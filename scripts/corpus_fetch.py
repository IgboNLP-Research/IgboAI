#!/usr/bin/env python3
"""Corpus ingestion fetch layer for IgboAI. Stdlib only.

Source classes and their storage strategies (licensing-aware):
  wikipedia  -> full text committed (CC BY-SA 4.0; attribution via per-doc URL)
                corpus/raw/wikipedia_<lang>/<date>.jsonl.gz
  hf         -> catalog metadata only (datasets stay on the Hub under their
                own licenses); corpus/catalog/hf_datasets.json
  news       -> URL manifests only (article text is copyrighted and must NOT
                be committed to a public repo); corpus/manifests/<feed>.jsonl

State (resume cursors, backfill progress): corpus/state.json
A per-run summary for the LLM triage step:   corpus_run_summary.json (uncommitted)

Usage: python scripts/corpus_fetch.py <wikipedia|hf|news|all> [max_pages]
"""

import gzip
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MODE = sys.argv[1] if len(sys.argv) > 1 else "all"
MAX_PAGES = int(sys.argv[2]) if len(sys.argv) > 2 else 500  # per language per run

WIKI_LANGS = ["ig"]  # Igbo. Add e.g. "yo", "ha", "pcm" deliberately, per data plan.
HF_TERMS = [
    "igbo", "yoruba", "hausa", "naija", "pidgin nigerian",
    "masakhane", "african languages",
]
NEWS_FEEDS = {
    # name -> RSS URL. Manifests only; no article text is stored.
    "bbc_igbo": "https://feeds.bbci.co.uk/igbo/rss.xml",
}

STATE_PATH = Path("corpus/state.json")
SUMMARY_PATH = Path("corpus_run_summary.json")
UA = {"User-Agent": "IgboAI-corpus/1.0 (research corpus builder; contact via repo)"}
TODAY = datetime.now(timezone.utc).date().isoformat()

IGBO_DIACRITICS = set("ịọụṅỊỌỤṄ")


def http_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def http_text(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def text_stats(docs: list[dict]) -> dict:
    toks = sum(len(d["text"].split()) for d in docs)
    chars = sum(len(d["text"]) for d in docs)
    dia = sum(sum(c in IGBO_DIACRITICS for c in d["text"]) for d in docs)
    return {
        "documents": len(docs),
        "tokens_ws": toks,
        "chars": chars,
        "diacritic_char_ratio": round(dia / chars, 5) if chars else 0.0,
    }


# --------------------------- Wikipedia (full text) ---------------------------

def fetch_wikipedia(state: dict) -> dict:
    """Incremental-with-backfill: walks allpages via a cursor in state, then on
    later runs also picks up recent changes. Bounded by MAX_PAGES per run, so
    the backfill drains across runs the same way the literature backlog did."""
    report = {}
    for lang in WIKI_LANGS:
        api = f"https://{lang}.wikipedia.org/w/api.php"
        skey = f"wikipedia_{lang}"
        st = state.setdefault(skey, {"backfill_done": False, "apcontinue": "", "rc_ts": ""})
        titles: list[str] = []

        if not st["backfill_done"]:
            params = {
                "action": "query", "list": "allpages", "apnamespace": 0,
                "aplimit": min(MAX_PAGES, 500), "format": "json",
            }
            if st["apcontinue"]:
                params["apcontinue"] = st["apcontinue"]
            data = http_json(api + "?" + urllib.parse.urlencode(params))
            titles = [p["title"] for p in data.get("query", {}).get("allpages", [])]
            cont = data.get("continue", {}).get("apcontinue")
            if cont:
                st["apcontinue"] = cont
            else:
                st["backfill_done"] = True
                st["rc_ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            params = {
                "action": "query", "list": "recentchanges", "rcnamespace": 0,
                "rclimit": min(MAX_PAGES, 500), "rcprop": "title|timestamp",
                "rcdir": "newer", "format": "json",
            }
            if st["rc_ts"]:
                params["rcstart"] = st["rc_ts"]
            data = http_json(api + "?" + urllib.parse.urlencode(params))
            changes = data.get("query", {}).get("recentchanges", [])
            titles = sorted({c["title"] for c in changes})
            if changes:
                st["rc_ts"] = max(c["timestamp"] for c in changes)

        docs = []
        for i in range(0, len(titles), 20):  # extracts allows 20 titles/request
            params = {
                "action": "query", "prop": "extracts|info", "inprop": "url",
                "explaintext": 1, "titles": "|".join(titles[i:i + 20]),
                "format": "json",
            }
            data = http_json(api + "?" + urllib.parse.urlencode(params))
            for page in data.get("query", {}).get("pages", {}).values():
                text = (page.get("extract") or "").strip()
                if len(text) < 50:  # skip stubs/empties
                    continue
                docs.append({
                    "id": f"wiki:{lang}:{page.get('pageid')}",
                    "title": page.get("title", ""),
                    "url": page.get("fullurl", ""),
                    "lang_claimed": lang,
                    "text": text,
                    "fetched": TODAY,
                    "license": "CC BY-SA 4.0",
                    "provenance": f"{lang}.wikipedia.org API extracts",
                })

        out = {}
        if docs:
            out_dir = Path(f"corpus/raw/wikipedia_{lang}")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{TODAY}.jsonl.gz"
            with gzip.open(out_path, "at", encoding="utf-8") as f:
                for d in docs:
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
            out = {"output": str(out_path), **text_stats(docs)}
            # small sample for LLM triage (uncommitted, via summary file)
            out["samples"] = [
                {"title": d["title"], "url": d["url"], "excerpt": d["text"][:600]}
                for d in docs[:: max(1, len(docs) // 8)][:8]
            ]
        out["backfill_done"] = st["backfill_done"]
        report[skey] = out
    return report


# ------------------------- HF Hub (catalog only) -----------------------------

def fetch_hf_catalog(state: dict) -> dict:
    seen_ids = set()
    entries = []
    for term in HF_TERMS:
        url = (
            "https://huggingface.co/api/datasets?"
            + urllib.parse.urlencode({"search": term, "limit": 50, "full": "true"})
        )
        try:
            data = http_json(url)
        except Exception as e:
            print(f"[warn] HF search failed ({term}): {e}", file=sys.stderr)
            continue
        for d in data:
            did = d.get("id", "")
            if not did or did in seen_ids:
                continue
            seen_ids.add(did)
            card = d.get("cardData") or {}
            entries.append({
                "id": did,
                "url": f"https://huggingface.co/datasets/{did}",
                "license": card.get("license") or d.get("license") or "UNKNOWN",
                "languages": card.get("language") or [],
                "tags": (d.get("tags") or [])[:15],
                "downloads": d.get("downloads", 0),
                "last_modified": d.get("lastModified", ""),
                "matched_term": term,
            })
    entries.sort(key=lambda e: -e["downloads"])
    out_path = Path("corpus/catalog/hf_datasets.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    prev_ids = set()
    if out_path.exists():
        prev_ids = {e["id"] for e in json.loads(out_path.read_text())}
    out_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
    new = [e for e in entries if e["id"] not in prev_ids]
    return {
        "output": str(out_path),
        "total": len(entries),
        "new_since_last_run": [
            {k: e[k] for k in ("id", "url", "license", "languages")} for e in new[:40]
        ],
    }


# -------------------------- News (manifests only) ----------------------------

def fetch_news_manifests(state: dict) -> dict:
    import xml.etree.ElementTree as ET
    report = {}
    for name, feed_url in NEWS_FEEDS.items():
        try:
            root = ET.fromstring(http_text(feed_url))
        except Exception as e:
            print(f"[warn] feed failed ({name}): {e}", file=sys.stderr)
            continue
        out_path = Path(f"corpus/manifests/{name}.jsonl")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        existing = set()
        if out_path.exists():
            for line in out_path.read_text().splitlines():
                try:
                    existing.add(json.loads(line)["url_sha1"])
                except Exception:
                    pass
        added = 0
        with out_path.open("a", encoding="utf-8") as f:
            for item in root.iter("item"):
                link = (item.findtext("link") or "").strip()
                if not link:
                    continue
                h = hashlib.sha1(link.encode()).hexdigest()
                if h in existing:
                    continue
                f.write(json.dumps({
                    "url": link,
                    "url_sha1": h,
                    "title": (item.findtext("title") or "").strip(),
                    "published": (item.findtext("pubDate") or "").strip(),
                    "recorded": TODAY,
                    "note": "manifest only; text not stored (copyright)",
                }, ensure_ascii=False) + "\n")
                existing.add(h)
                added += 1
        report[name] = {"output": str(out_path), "new_urls": added}
    return report


def main() -> None:
    state = load_state()
    summary = {"run_date": TODAY, "mode": MODE}
    if MODE in ("wikipedia", "all"):
        summary["wikipedia"] = fetch_wikipedia(state)
    if MODE in ("hf", "all"):
        summary["hf_catalog"] = fetch_hf_catalog(state)
    if MODE in ("news", "all"):
        summary["news"] = fetch_news_manifests(state)
    save_state(state)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in summary.items() if k != "wikipedia"} |
                     {"wikipedia_keys": list(summary.get("wikipedia", {}))}, indent=2))


if __name__ == "__main__":
    main()
