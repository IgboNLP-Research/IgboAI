#!/usr/bin/env python3
"""
corpus_dump_ingest.py — full-corpus ingest from a Wikimedia XML dump.

Replaces the API `allpages` backfill in corpus_fetch.py, which walked one title
per request (the TextExtracts `exlimit` cap is 1 unless `exintro` is set, and
`exintro` returns lead sections only). At 0.7s/request, 58k titles was ~11 hours
of request time, or roughly six months of weekly runs. The dump is one download.

corpus_fetch.py keeps the incremental path: once this script sets
backfill_done=true and rc_ts to the dump timestamp, `recentchanges` picks up
edits made after the snapshot.

    python scripts/corpus_dump_ingest.py [lang] [--max-pages N] [--keep-dump]

Design notes:
  * Streams and decompresses incrementally. The uncompressed XML (several
    hundred MB) is never written to disk.
  * Shards output so no single blob dominates a git commit and diffs stay
    readable. One shard per SHARD_SIZE kept articles.
  * Records the dump's SHA-256 and Last-Modified in state.json. The corpus is
    then reproducible from a named snapshot, which the API walk never was.
  * Resumable in the weak sense: shards already flushed survive a crash. There
    is no mid-dump cursor; rerun from the start and overwrite.

Requires: pip install mwparserfromhell
"""

from __future__ import annotations

import argparse
import bz2
import gzip
import hashlib
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import mwparserfromhell as mw

sys.path.insert(0, str(Path(__file__).resolve().parent))
_argv = sys.argv
sys.argv = [_argv[0]]                     # corpus_fetch reads sys.argv at import time
try:
    from corpus_fetch import IGBO_DIACRITICS, text_stats   # noqa: E402  shared metrics; keeps cards comparable
finally:
    sys.argv = _argv

DUMP_URL = "https://dumps.wikimedia.org/{wiki}/latest/{wiki}-latest-pages-articles.xml.bz2"
UA = "IgboAI-corpus-bot/1.0 (https://github.com/IgboNLP-Research/IgboAI)"

MIN_CHARS = 300          # matches corpus_fetch.py; see card F6 before changing
SHARD_SIZE = 5000        # kept articles per shard file
CHUNK = 1 << 20          # 1 MiB network reads

RAW = Path("corpus/raw")
STATE_PATH = Path("corpus/state.json")
SUMMARY_PATH = Path("corpus_run_summary.json")

# strip_code leaves image-caption fragments and citation placeholders behind.
LEADING_MEDIA = re.compile(r"^\s*(?:thumb|right|left|center|upright|border|frameless|\d+px)\s*\|\s*",
                           re.IGNORECASE)
CITATION_NEEDED = re.compile(r"\[\s*citation needed\s*\]", re.IGNORECASE)
BLANK_RUNS = re.compile(r"\n{3,}")

# Residue that means strip_code did not fully resolve the page.
RESIDUE = ("data-mw=", 'typeof="mw:', "{{", "Templeeti:")


def clean(wikitext: str) -> str:
    text = mw.parse(wikitext).strip_code(normalize=True, collapse=True)
    # Media fragments can survive on several consecutive leading lines.
    lines = text.split("\n")
    while lines and LEADING_MEDIA.match(lines[0]):
        lines[0] = LEADING_MEDIA.sub("", lines[0])
        if not lines[0].strip():
            lines.pop(0)
        else:
            break
    text = "\n".join(lines)
    text = CITATION_NEEDED.sub("", text)
    return BLANK_RUNS.sub("\n\n", text).strip()

def stream_dump(url: str, sha: hashlib._Hash):
    """Yield decompressed XML bytes, hashing the compressed stream as it passes."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    dec = bz2.BZ2Decompressor()
    with urllib.request.urlopen(req) as resp:
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            sha.update(chunk)
            out = dec.decompress(chunk)
            if out:
                yield out

class _Reader:
    """Adapts the byte generator to the .read() interface iterparse expects."""

    def __init__(self, gen):
        self.gen, self.buf = gen, b""

    def read(self, n: int = -1) -> bytes:
        while n < 0 or len(self.buf) < n:
            try:
                self.buf += next(self.gen)
            except StopIteration:
                break
        if n < 0:
            out, self.buf = self.buf, b""
            return out
        out, self.buf = self.buf[:n], self.buf[n:]
        return out


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def ingest(lang: str, max_pages: int | None) -> dict:
    wiki = f"{lang}wiki"
    url = DUMP_URL.format(wiki=wiki)

    head = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
    with urllib.request.urlopen(head) as r:
        dump_modified = r.headers.get("Last-Modified", "")
        dump_bytes = int(r.headers.get("Content-Length", 0))
    print(f"dump: {url}\n  {dump_bytes:,} bytes, modified {dump_modified}", file=sys.stderr)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    outdir = RAW / f"wikipedia_{lang}" / f"dump-{stamp}"
    outdir.mkdir(parents=True, exist_ok=True)

    sha = hashlib.sha256()
    reader = _Reader(stream_dump(url, sha))

    counts = dict(pages_seen=0, non_mainspace=0, redirects=0, empty=0,
                  skipped_short=0, skipped_residue=0, kept=0)
    shards: list[str] = []
    buf: list[dict] = []
        
    stat_sample: list[dict] = []     # excerpts for the card; capped
    totals = dict(documents=0, tokens_ws=0, chars=0, diacritics=0)
    def flush() -> None:
        if not buf:
            return
        path = outdir / f"shard-{len(shards):03d}.jsonl.gz"
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            for d in buf:
                fh.write(json.dumps(d, ensure_ascii=False) + "\n")
        shards.append(str(path))
        print(f"  wrote {path} ({len(buf)} docs)", file=sys.stderr)
        buf.clear()

    for _, el in ET.iterparse(reader, events=("end",)):
        if local(el.tag) != "page":
            continue
        counts["pages_seen"] += 1

        ns = el.findtext("{*}ns")
        if ns != "0":
            counts["non_mainspace"] += 1
        elif el.find("{*}redirect") is not None:
            counts["redirects"] += 1
        else:
            title = html.unescape(el.findtext("{*}title") or "")
            pageid = el.findtext("{*}id") or ""
            body = el.findtext("{*}revision/{*}text") or ""
            if not body.strip():
                counts["empty"] += 1
            else:
                text = clean(html.unescape(body))
                if len(text) < MIN_CHARS:
                    counts["skipped_short"] += 1
                elif any(r in text for r in RESIDUE):
                    counts["skipped_residue"] += 1
                else:
                    doc = {
                        "id": f"wiki:{lang}:{pageid}",
                        "title": title,
                        "url": f"https://{lang}.wikipedia.org/wiki/"
                               + urllib.parse.quote(title.replace(" ", "_")),
                        "lang_claimed": lang,
                        "text": text,
                        "source": "dump",
                        "dump_modified": dump_modified,
                    }
                    buf.append(doc)
                    counts["kept"] += 1
                    totals["documents"] += 1
                    totals["tokens_ws"] += len(text.split())
                    totals["chars"] += len(text)
                    totals["diacritics"] += sum(c in IGBO_DIACRITICS for c in text)
                    if totals["documents"] % 250 == 1:
                        stat_sample.append(doc)
                    if len(buf) >= SHARD_SIZE:
                        flush()

        el.clear()   # release the parsed subtree; the dump does not fit in memory

        if counts["pages_seen"] % 10000 == 0:
            print(f"  {counts['pages_seen']:,} pages, {counts['kept']:,} kept",
                  file=sys.stderr)
        if max_pages and counts["pages_seen"] >= max_pages:
            print(f"  stopping at --max-pages {max_pages}", file=sys.stderr)
            break

    flush()

    out = {
        "output_dir": str(outdir),
        "shards": shards,
        "dump_url": url,
        "dump_modified": dump_modified,
        "dump_bytes": dump_bytes,
        "dump_sha256": sha.hexdigest() if not max_pages else "partial-run-not-hashed",
        "min_chars": MIN_CHARS,
        **counts,
        "documents": totals["documents"],
        "tokens_ws": totals["tokens_ws"],
        "chars": totals["chars"],
        "diacritic_char_ratio": round(totals["diacritics"] / max(totals["chars"], 1), 5),
        "samples": [{"title": d["title"], "url": d["url"], "excerpt": d["text"][:600]}
            for d in stat_sample[:: max(1, len(stat_sample) // 8)][:8]],
    }
    out["keep_rate"] = round(counts["kept"] / max(counts["pages_seen"], 1), 4)
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("lang", nargs="?", default="ig")
    ap.add_argument("--max-pages", type=int, default=None,
                    help="stop after N pages; for smoke tests. Skips the dump hash.")
    args = ap.parse_args()

    result = ingest(args.lang, args.max_pages)

    key = f"wikipedia_{args.lang}"
    summary = {"run_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
               "mode": "dump", "wikipedia": {key: result}}
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    if not args.max_pages:
        state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {}
        state[key] = {
            "backfill_done": True,
            "backfill_method": "dump",
            "dump_modified": result["dump_modified"],
            "dump_sha256": result["dump_sha256"],
            "ingested_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            # recentchanges resumes from the snapshot boundary.
            "rc_ts": datetime.strptime(
                result["dump_modified"], "%a, %d %b %Y %H:%M:%S %Z"
            ).strftime("%Y-%m-%dT%H:%M:%SZ") if result["dump_modified"] else "",
        }
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2))

    print(json.dumps({k: v for k, v in result.items() if k != "samples"},
                     ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())