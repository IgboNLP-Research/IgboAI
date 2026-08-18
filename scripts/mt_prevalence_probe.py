#!/usr/bin/env python3
"""
mt_prevalence_probe.py — estimate machine-translation contamination in a corpus.

Motivated by dump-2026-08-18, where mid-corpus articles such as
"Obiọma Notre Dame de Lourdes" contain untranslated English clauses interleaved
with Igbo ("I work with Lourdes n'oge isi njem njem").

WHAT THIS MEASURES, AND WHAT IT DOES NOT
This is a LEXICAL PROXY, not MT detection. It counts English function words that
survive in the text. That signal:
  * under-counts fluent MT, which leaves no English behind at all;
  * over-counts articles that legitimately quote or cite English;
  * says nothing about translation quality where translation did occur.
Treat the corpus-wide figure as a lower bound on visible MT residue, and use the
stratified sample it writes for human annotation to get a defensible number.

    python scripts/mt_prevalence_probe.py corpus/raw/wikipedia_ig/dump-YYYY-MM-DD

Writes:
    mt_probe_summary.json     distribution and per-bucket counts
    mt_probe_sample.tsv       stratified sample, one row per doc, for annotation
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

# Function words that are unambiguously English and not Igbo. Short ambiguous
# tokens (a, i, na, no, so, be, ka) are excluded: "na" and "ka" are Igbo, and
# single letters appear in initials. Length >= 3 throughout.
EN_FUNCTION = {
    "the", "and", "for", "with", "from", "that", "this", "these", "those",
    "was", "were", "have", "has", "had", "been", "being", "will", "would",
    "could", "should", "which", "their", "they", "them", "there", "then",
    "than", "when", "where", "what", "who", "whom", "whose", "also", "other",
    "others", "more", "most", "some", "such", "only", "over", "under", "while",
    "both", "each", "many", "much", "first", "used", "using", "including",
    "however", "although", "because", "between", "during", "before", "after",
    "into", "through", "about", "against", "among", "within", "without",
    "his", "her", "its", "our", "your", "not", "but", "are", "you", "she",
    "him", "how", "all", "any", "can", "may", "one", "two", "new", "now",
}

# Repeated-character garble, e.g. "ọ ọọọ" seen in the Lourdes article.
GARBLE = re.compile(r"([^\W\d_])\1{3,}")
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

# Buckets on English-function-word ratio. Thresholds are provisional and should
# be recalibrated against the annotated sample.
BUCKETS = [
    ("clean", 0.000, 0.002),
    ("trace", 0.002, 0.010),
    ("moderate", 0.010, 0.030),
    ("heavy", 0.030, 1.001),
]


def bucket_of(ratio: float) -> str:
    for name, lo, hi in BUCKETS:
        if lo <= ratio < hi:
            return name
    return "heavy"


def score(text: str) -> tuple[float, int, int]:
    words = [w.lower() for w in WORD.findall(text)]
    if not words:
        return 0.0, 0, 0
    en = sum(1 for w in words if w in EN_FUNCTION)
    garble = len(GARBLE.findall(text))
    return en / len(words), en, garble


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("shard_dir", type=Path)
    ap.add_argument("--sample-per-bucket", type=int, default=25)
    ap.add_argument("--seed", type=int, default=20260818)
    args = ap.parse_args()

    shards = sorted(args.shard_dir.glob("shard-*.jsonl.gz"))
    if not shards:
        print(f"no shards under {args.shard_dir}", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    counts: Counter[str] = Counter()
    garbled_docs = 0
    total = 0
    # Reservoir per bucket so the sample is unbiased across the whole corpus.
    reservoir: dict[str, list] = {name: [] for name, _, _ in BUCKETS}
    seen: Counter[str] = Counter()

    for path in shards:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                ratio, en, garble = score(d["text"])
                b = bucket_of(ratio)
                counts[b] += 1
                total += 1
                if garble:
                    garbled_docs += 1

                seen[b] += 1
                row = (d["id"], d["title"], round(ratio, 5), en, garble,
                       d["text"][:300].replace("\t", " ").replace("\n", " "))
                res = reservoir[b]
                if len(res) < args.sample_per_bucket:
                    res.append(row)
                else:
                    j = rng.randrange(seen[b])
                    if j < args.sample_per_bucket:
                        res[j] = row
        print(f"  scanned {path.name} ({total:,} docs)", file=sys.stderr)

    summary = {
        "shard_dir": str(args.shard_dir),
        "documents": total,
        "buckets": {name: {"count": counts[name],
                           "share": round(counts[name] / max(total, 1), 4),
                           "en_ratio_range": [lo, hi]}
                    for name, lo, hi in BUCKETS},
        "docs_with_repeated_char_garble": garbled_docs,
        "garble_share": round(garbled_docs / max(total, 1), 4),
        "method": "lexical proxy: English function-word ratio; see module docstring",
        "caveat": "lower bound on visible MT residue; fluent MT leaves no trace",
    }
    Path("mt_probe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2))

    with open("mt_probe_sample.tsv", "w", encoding="utf-8") as fh:
        fh.write("bucket\tid\ttitle\ten_ratio\ten_words\tgarble\tannotation\texcerpt\n")
        for name, _, _ in BUCKETS:
            for r in reservoir[name]:
                fh.write(f"{name}\t{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t\t{r[5]}\n")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\nAnnotate the 'annotation' column in mt_probe_sample.tsv "
          "(e.g. mt / human / unclear), then recompute precision per bucket.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())