#!/usr/bin/env python3
"""
backfill_entries_jsonl.py — reconstruct missing entries.jsonl records.

Entries logged before the 2026-08-04 migration ("docs(related-work): split log
into monthly files") have prose write-ups in related-work/<month>.md but no
machine-readable record, so anything computing over entries.jsonl sees fewer
entries than the log shows.

TWO FORMATS EXIST IN THE LOG:

  pre-migration (single line, metadata in parentheses):
    - **Title** (Hugging Face model, 2026-08-04) - prose ... <URL>

  current (metadata line, then summary, then a relevance line):
    - **Title** - type: dataset · Hugging Face · 2026-08-23 · tags: [...] · languages: [...]
      summary
      *Igbo relevance:* ... <URL>

The old format carries no tags, no languages, and no separate Igbo-relevance
sentence: relevance is woven into the prose. Those fields are therefore left
EMPTY rather than invented, and the whole prose goes into `summary`. Every
record is marked "backfilled": true so reconstructed entries stay
distinguishable from those written at log time.

Candidates go to a review file, not straight into entries.jsonl.

    python scripts/backfill_entries_jsonl.py
    # review, then:
    # cat related-work/entries_backfill_review.jsonl >> related-work/entries.jsonl
"""

from __future__ import annotations

import json
import re
from pathlib import Path

MD = Path("related-work/2026-08.md")
JSONL = Path("related-work/entries.jsonl")
OUT = Path("related-work/entries_backfill_review.jsonl")

ENTRY_START = re.compile(r"^- \*\*(.+?)\*\*", re.M)
# Angle-bracket autolinks are used throughout, so stop at '>' as well as ')' ']'.
URL = re.compile(r"https?://[^\s)\]>]+")
# Pre-migration metadata: (Hugging Face model, 2026-08-04)
OLD_META = re.compile(r"\((.+?),\s*(\d{4}-\d{2}-\d{2})\)\s*[-–]\s*")

TYPE_WORDS = {"model": "model", "dataset": "dataset", "preprint": "paper",
              "paper": "paper", "article": "paper", "journal": "paper"}


def derive_id(url: str, title: str) -> str:
    if m := re.search(r"arxiv\.org/abs/([\d.]+)", url):
        return f"arxiv:{m.group(1)}"
    if m := re.search(r"huggingface\.co/datasets/([\w\-./]+)", url):
        return f"hf:datasets:{m.group(1).rstrip('/')}"
    if m := re.search(r"huggingface\.co/([\w\-./]+)", url):
        return f"hf:models:{m.group(1).rstrip('/')}"
    if m := re.search(r"openalex\.org/(W\d+)", url):
        return f"openalex:{m.group(1)}"
    if m := re.search(r"doi\.org/(\S+)", url):
        return f"doi:{m.group(1)}"
    return f"UNKNOWN:{title[:40]}"


def parse_old(title: str, body: str) -> tuple[dict, list[str]]:
    """Pre-migration single-line entry."""
    problems: list[str] = []
    urls = URL.findall(body)
    url = urls[-1] if urls else ""          # the link sits at the end
    if not url:
        problems.append("no URL found")

    typ, source, date = "", "", ""
    if m := OLD_META.search(body):
        blurb, date = m.group(1).strip(), m.group(2)
        low = blurb.lower()
        for word, mapped in TYPE_WORDS.items():
            if word in low:
                typ = mapped
                source = re.sub(rf"\s*{word}\s*$", "", blurb, flags=re.I).strip()
                break
        if not typ and re.match(r"^(arxiv|doi):", derive_id(url, title)):
            typ = "paper"
        if not typ:
            source = blurb
            problems.append(f"could not infer type from {blurb!r}")
        prose = body[m.end():]
    else:
        problems.append("no (source type, date) parenthetical")
        prose = body

    prose = URL.sub("", prose).replace("<", "").replace(">", "")
    summary = " ".join(prose.split())
    if not summary:
        problems.append("no summary text")

    rec = {"id": derive_id(url, title), "title": title, "type": typ, "url": url,
           "source": source, "date": date, "tags": [], "languages": [],
           "summary": summary, "igbo_relevance": "", "backfilled": True,
           "format": "pre-migration"}
    if rec["id"].startswith("UNKNOWN"):
        problems.append("could not derive id from URL")
    return rec, problems


def parse_new(title: str, body: str) -> tuple[dict, list[str]]:
    """Current format. Present for completeness; normally nothing hits this."""
    problems: list[str] = []
    urls = URL.findall(body)
    url = urls[-1] if urls else ""
    if not url:
        problems.append("no URL found")

    def grab(pat: str, label: str, required: bool = True) -> str:
        m = re.search(pat, body, re.I)
        if not m:
            if required:
                problems.append(f"no {label}")
            return ""
        return m.group(1).strip()

    typ = grab(r"type:\s*([A-Za-z]+)", "type")
    source = grab(r"type:\s*[A-Za-z]+\s*·\s*([^·]+)·", "source", required=False)
    date = grab(r"(\d{4}-\d{2}-\d{2})", "date", required=False)
    tags = grab(r"tags:\s*\[([^\]]*)\]", "tags", required=False)
    langs = grab(r"languages:\s*\[([^\]]*)\]", "languages", required=False)

    rel = ""
    if m := re.search(r"\*Igbo relevance:\*\s*(.+?)(?:\n\s*\n|\Z)", body, re.S | re.I):
        rel = " ".join(URL.sub("", m.group(1)).replace("<", "").replace(">", "").split())
    else:
        problems.append("no *Igbo relevance:* line")

    lines = [l.strip() for l in body.split("\n")[1:]
             if l.strip() and not l.strip().startswith("*Igbo relevance:*")]
    summary = " ".join(" ".join(lines).split())

    rec = {"id": derive_id(url, title), "title": title, "type": typ.lower(),
           "url": url, "source": source.strip(" ·"), "date": date,
           "tags": [t.strip() for t in re.split(r"[,|]", tags) if t.strip()],
           "languages": [l.strip() for l in re.split(r"[,|]", langs) if l.strip()],
           "summary": summary, "igbo_relevance": rel, "backfilled": True,
           "format": "current"}
    if rec["id"].startswith("UNKNOWN"):
        problems.append("could not derive id from URL")
    return rec, problems


def main() -> int:
    text = MD.read_text(encoding="utf-8")

    have_ids, have_urls = set(), set()
    for l in JSONL.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            have_ids.add(r["id"])
            if r.get("url"):
                have_urls.add(r["url"].rstrip("/"))

    # have_ids = {json.loads(l)["id"]
    #             for l in JSONL.read_text(encoding="utf-8").splitlines() if l.strip()}

    starts = [(m.start(), m.group(1)) for m in ENTRY_START.finditer(text)]
    records, flagged, skipped = [], 0, 0

    for i, (pos, title) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        body = text[pos:end]
        # Format detection: the current format puts "type:" on the title line.
        first_line = body.split("\n", 1)[0]
        rec, problems = (parse_new if "type:" in first_line else parse_old)(title, body)

        # Dedupe by id, not title: titles drift between the two files.
        if rec["id"] in have_ids or (rec["url"] and rec["url"].rstrip("/") in have_urls):
            skipped += 1
            continue

        records.append(rec)
        print(f"{'  !!' if problems else '    '} {rec['id']:<45} "
              f"[{rec['format']}] {title[:45]}")
        for p in problems:
            print(f"        - {p}")
            flagged += 1

    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                   encoding="utf-8")
    print(f"\n{skipped} already present (matched by id), {len(records)} candidates "
          f"written to {OUT}")
    print(f"{flagged} field-level problems flagged.")
    print("Old-format records have empty tags/languages/igbo_relevance by design: "
          "the pre-migration log did not record them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())