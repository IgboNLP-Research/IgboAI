#!/usr/bin/env python3
"""Fetch new papers and models relevant to Igbo / African NLP + speech + LLMs.

Sources:
  - arXiv API (preprints)
  - OpenAlex API (venue-published work: ACL Anthology venues incl. TACL,
    ACL/EMNLP/EACL/COLING/LREC and their workshops, plus journals) -- no key needed
  - Hugging Face Hub (models and datasets)

Deterministic fetch layer: this script only gathers and filters candidates.
Summarization, relevance ranking, and PR writing are handled by Claude Code
in the GitHub Actions workflow, keeping LLM behavior auditable and cheap.

Outputs: candidates.json in the repo root (consumed by the workflow).
Stdlib only -- no dependencies to install on the runner.
"""

import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

LOOKBACK_DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 2  # cron cadence + margin
SEEN_PATH = Path(".github/tracking/seen.json")
OUT_PATH = Path("candidates.json")

ARXIV_QUERIES = [
    'all:"Igbo"',
    'all:"African NLP" OR all:"African languages" AND cat:cs.CL',
    'all:"low-resource" AND all:"machine translation" AND cat:cs.CL',
    '(all:"speech recognition" OR all:"text-to-speech" OR all:"ASR") AND (all:"African" OR all:"low-resource" OR all:"tonal")',
    'all:"tone" AND all:"tonal languages" AND (cat:eess.AS OR cat:cs.CL)',
    '(all:"multilingual" AND all:"large language model") AND (all:"African" OR all:"Nigerian")',
]
HF_SEARCH_TERMS = [
    "igbo", "african nlp", "afriberta", "afroxlmr", "nllb igbo",
    "igbo asr", "igbo tts", "african speech", "naija", "african llm",
]
# OpenAlex full-text search strings (covers ACL Anthology venues, LREC, TACL,
# workshops, and journals that arXiv misses). Plain phrases, not fielded syntax.
OPENALEX_QUERIES = [
    '"Igbo"',
    '"African languages" NLP',
    '"low-resource" "machine translation"',
    '"African" "speech recognition"',
    '"tonal language" speech',
    '"African" "large language model"',
]
OPENALEX_MAILTO = "i.ezeani@lancaster.ac.uk"  # set to a real address (polite pool = faster, no key needed)

ATOM = "{http://www.w3.org/2005/Atom}"
UA = {"User-Agent": "IgboAI-tracker/1.0 (research literature monitor)"}


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_arxiv(cutoff: datetime) -> list[dict]:
    items = []
    for q in ARXIV_QUERIES:
        url = (
            "http://export.arxiv.org/api/query?"
            + urllib.parse.urlencode(
                {
                    "search_query": q,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                    "max_results": 40 if LOOKBACK_DAYS <= 7 else 250,
                }
            )
        )
        try:
            root = ET.fromstring(http_get(url))
        except Exception as e:  # network hiccups shouldn't kill the whole run
            print(f"[warn] arXiv query failed ({q}): {e}", file=sys.stderr)
            continue
        for entry in root.findall(f"{ATOM}entry"):
            published = entry.findtext(f"{ATOM}published") or ""
            try:
                pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except ValueError:
                continue
            if pub_dt < cutoff:
                continue
            arxiv_id = (entry.findtext(f"{ATOM}id") or "").rsplit("/", 1)[-1]
            items.append(
                {
                    "source": "arxiv",
                    "id": f"arxiv:{re.sub(r'v\d+$', '', arxiv_id)}",
                    "title": " ".join((entry.findtext(f"{ATOM}title") or "").split()),
                    "abstract": " ".join((entry.findtext(f"{ATOM}summary") or "").split()),
                    "authors": [
                        a.findtext(f"{ATOM}name")
                        for a in entry.findall(f"{ATOM}author")
                    ][:12],
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "published": published,
                    "matched_query": q,
                }
            )
    return items


def fetch_hf(cutoff: datetime) -> list[dict]:
    items = []
    for kind in ("models", "datasets"):
        for term in HF_SEARCH_TERMS:
            url = (
                f"https://huggingface.co/api/{kind}?"
                + urllib.parse.urlencode(
                    {"search": term, "sort": "lastModified", "direction": -1, "limit": 25}
                )
            )
            try:
                data = json.loads(http_get(url))
            except Exception as e:
                print(f"[warn] HF query failed ({kind}/{term}): {e}", file=sys.stderr)
                continue
            for it in data:
                last_mod = it.get("lastModified") or it.get("createdAt") or ""
                try:
                    mod_dt = datetime.fromisoformat(last_mod.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if mod_dt < cutoff:
                    continue
                repo_id = it.get("id") or it.get("modelId", "")
                items.append(
                    {
                        "source": f"hf-{kind}",
                        "id": f"hf:{kind}:{repo_id}",
                        "title": repo_id,
                        "tags": it.get("tags", [])[:20],
                        "url": f"https://huggingface.co/"
                        + ("datasets/" if kind == "datasets" else "")
                        + repo_id,
                        "downloads": it.get("downloads", 0),
                        "last_modified": last_mod,
                        "matched_query": term,
                    }
                )
    return items


def _deinvert_abstract(inv: dict | None) -> str:
    """OpenAlex stores abstracts as {word: [positions]}; rebuild plain text."""
    if not inv:
        return ""
    slots: dict[int, str] = {}
    for word, positions in inv.items():
        for pos in positions:
            slots[pos] = word
    return " ".join(slots[i] for i in sorted(slots))[:2000]


def fetch_openalex(cutoff: datetime) -> list[dict]:
    items = []
    for q in OPENALEX_QUERIES:
        cursor = "*"
        for _ in range(5):  # max 5 pages x 100 = 500/query; plenty even for backfills
            url = (
                "https://api.openalex.org/works?"
                + urllib.parse.urlencode(
                    {
                        "search": q,
                        "filter": f"from_publication_date:{cutoff.date().isoformat()}",
                        "sort": "publication_date:desc",
                        "per-page": 100,
                        "cursor": cursor,
                        "mailto": OPENALEX_MAILTO,
                    }
                )
            )
            try:
                data = json.loads(http_get(url))
            except Exception as e:
                print(f"[warn] OpenAlex query failed ({q}): {e}", file=sys.stderr)
                break
            for w in data.get("results", []):
                # Skip arXiv-hosted versions: fetch_arxiv already covers those,
                # and this avoids preprint/published near-duplicates in one run.
                venue = (
                    (w.get("primary_location") or {}).get("source") or {}
                ).get("display_name") or ""
                if "arxiv" in venue.lower():
                    continue
                wid = (w.get("id") or "").rsplit("/", 1)[-1]  # e.g. W4321...
                if not wid:
                    continue
                items.append(
                    {
                        "source": "openalex",
                        "id": f"openalex:{wid}",
                        "title": w.get("display_name") or "",
                        "abstract": _deinvert_abstract(w.get("abstract_inverted_index")),
                        "authors": [
                            (a.get("author") or {}).get("display_name")
                            for a in (w.get("authorships") or [])
                        ][:12],
                        "venue": venue,
                        "url": w.get("doi") or (w.get("id") or ""),
                        "published": w.get("publication_date") or "",
                        "matched_query": q,
                    }
                )
            cursor = (data.get("meta") or {}).get("next_cursor")
            if not cursor:
                break
    return items


def main() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    seen: set[str] = set()
    if SEEN_PATH.exists():
        seen = set(json.loads(SEEN_PATH.read_text()))

    candidates = fetch_arxiv(cutoff) + fetch_openalex(cutoff) + fetch_hf(cutoff)

    # dedupe within-run and against history
    fresh, ids = [], set()
    for c in candidates:
        if c["id"] in seen or c["id"] in ids:
            continue
        ids.add(c["id"])
        fresh.append(c)

    MAX_ITEMS_PER_RUN = 40
    fresh.sort(key=lambda c: c.get("published") or c.get("last_modified") or "", reverse=True)
    fresh = fresh[:MAX_ITEMS_PER_RUN]

    OUT_PATH.write_text(json.dumps(fresh, indent=2, ensure_ascii=False))
    print(f"{len(fresh)} new candidates (of {len(candidates)} fetched)")

if __name__ == "__main__":
    main()
