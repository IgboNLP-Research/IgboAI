# Data card — BBC News Igbo (`bbc_igbo`)

## Source and method of collection

- **Source:** BBC News Igbo RSS feed, `https://feeds.bbci.co.uk/igbo/rss.xml`.
- **Method:** `scripts/corpus_fetch.py` parses the feed and appends one
  record per *previously unseen* article URL to
  `corpus/manifests/bbc_igbo.jsonl`. Deduplication is by SHA-1 of the URL.
- **What is stored:** `url`, `url_sha1`, `published`, `recorded`, and a
  fixed `note`. **Article body text is never fetched or stored.**
- **What is not stored:** article text, images, author bylines, comments,
  and — contrary to this card's previous description — **no `title`
  field**. Checked directly against `corpus/manifests/bbc_igbo.jsonl` on
  2026-08-15: every one of the 15 records to date has exactly the five
  fields above; none has a `title` key. The card previously described a
  stored headline field and reasoned about its narrowness as an
  attribution/privacy question. That description did not match the data
  on disk. Corrected here; if a `title` field is added to the fetcher in
  future, the license/attribution reasoning below about headline
  quotation would need to be revisited at that point, not before.

## License and attribution

- **License: none granted. BBC article text is copyrighted**, and the BBC
  Terms of Use do not permit redistribution.
- This is exactly why the pipeline stores **URL manifests only** (see
  `corpus/SOURCES.md`). The manifest is a pointer list; it enables a
  researcher to rebuild the text **locally**, for their own analysis, without
  this repository ever redistributing it.
- **Obligations on anyone using this manifest:** fetching the listed URLs is
  your own act under your own jurisdiction's text-and-data-mining exception
  (e.g. EU DSM Art. 3/4, UK TDM for non-commercial research). Do not
  redistribute the rebuilt text. Do not commit rebuilt text to this repo.
- **Attribution if quoting:** "BBC News Igbo", with the article URL.

## Update cadence

Weekly, alongside the rest of the ingestion workflow (Sundays 04:00 UTC).

**Coverage caveat:** an RSS feed is a *sliding window* — typically the most
recent ~10–20 items. A weekly poll of a feed this size will silently miss
articles if BBC Igbo publishes faster than the window drains between runs.
This run recorded 11 URLs spanning **2026-07-21 to 2026-08-06** (17 days),
which suggests the window currently holds more than a week of output and the
weekly cadence is adequate *for now*. This should be re-checked as volume
changes; a gap in `published` dates between consecutive runs is the symptom.

**2026-08-15 update:** runs are in practice landing every 2-8 days, not
weekly (2026-08-07, 2026-08-13, 2026-08-15 so far), so the sliding-window
risk above is being tested more often than the nominal cadence implies.
The three batches' `published` ranges are 2026-07-21 to 2026-08-06,
2026-08-07 to 2026-08-11, and 2026-08-15 (a single item) respectively — the
first two are contiguous, but there is a **4-day silence, 2026-08-12 to
2026-08-14, with zero recorded items** between the second and third batch.
At the batch-1 long-run rate (11 items / 17 days ≈ 0.65/day) a 4-day gap
with nothing published is plausible on its own, so this is flagged as an
observation to watch, not a confirmed miss — but it is exactly the symptom
the caveat above says to watch for, and it should be rechecked against the
live feed if it recurs or lengthens.

## Cumulative size

| As of | New URLs this run | Cumulative URLs |
|---|---|---|
| 2026-08-07 | 11 | 11 |
| 2026-08-13 | 3 | 14 |
| 2026-08-15 | 1 | 15 |
| 2026-08-18 | 2 | 17 |
| 2026-08-23 | 0 | 17 |
| 2026-08-30 | 6 | 23 |
| 2026-09-13 | 8 | 31 |
| 2026-09-20 | 8 | 39 |
| 2026-09-27 | 7 | 46 |
| 2026-10-18 | 10 | 56 |

Cumulative figure derived directly by grouping all 56 lines in
`corpus/manifests/bbc_igbo.jsonl` by `recorded` date (9 distinct dates:
2026-08-07, 08-13, 08-15, 08-18, 08-30, 09-13, 09-20, 09-27, 10-18 — note
2026-08-23 contributed 0 new and so has no group of its own), not
accumulated from the prior card.

**2026-10-18 correction: the previous table skipped two entire runs
(2026-09-13 and 2026-09-20, 8 new items each) and understated 2026-09-27's
count.** Grouping every line directly, rather than trusting the previous
card's running total, finds `recorded: "2026-09-13"` (8 lines) and
`recorded: "2026-09-20"` (8 lines) between 2026-08-30 and 2026-09-27 —
neither previously appeared in this table at all. `recorded: "2026-09-27"`
itself has **7** lines, not 8. Old cumulative value after 2026-09-27: 31.
New value: 46 (23 + 8 + 8 + 7). This is a different and more mundane
failure than the 2026-09-06 case below: these two runs' commits plainly
exist in the manifest (unlike 2026-09-06, which left no trace anywhere),
so this was a card-maintenance gap — two triage passes were skipped or
under-counted — not a lost or reverted commit. The matching gap also
exists in `wikipedia_ig.md` (see flag 42 there): `corpus/raw/wikipedia_ig/`
holds `2026-09-13.jsonl.gz` and `2026-09-20.jsonl.gz` that no prior version
of that card ever counted either, which rules out this being
manifest-specific and points at the triage step generally.

**2026-09-27 correction: the "2026-09-06" row this table previously
showed (5 new, cumulative 28) does not exist in the manifest.** Grouping
every line by `recorded` date finds exactly seven distinct dates —
2026-08-07, 08-13, 08-15, 08-18, 08-23, 08-30, 2026-09-27 — with zero lines
recorded 2026-09-06. This run's 8 new lines bring the file from 23 to 31,
not from a prior 28 to 33. The previous card's 28/2026-09-06 figures, and
the matching flags 33–36 in `wikipedia_ig.md` (which describe a same-dated
Wikipedia run "read directly, in full"), describe a run that left no trace
in any of this run's three source files (this manifest, the HF catalog,
or the Wikipedia raw files — see the equivalent correction in
`wikipedia_ig.md`'s cumulative-size section and flag 37 there). Old value:
28. New value: 31 (23 verified real + 8 this run). Recommend to the
reviewer: check whether a 2026-09-06 commit was made and later reverted,
or whether that prior card update was written without a matching data
commit.

**2026-08-18 gap check:** the two new items are published 2026-08-17 and
2026-08-18, a 2-3 day gap since the last recorded item (2026-08-15). This is
back to the normal cadence the coverage caveat above expects, unlike the
4-day silent gap flagged on 2026-08-15.

**2026-08-23 gap check:** zero new items this run. The most recent recorded
`published` date is still 2026-08-18, so this is a **5-day silence
(2026-08-19 through 2026-08-23) with nothing recorded** — longer than the
4-day gap flagged on 2026-08-15 and, at the batch-1 long-run rate
(≈0.65 items/day), enough that a couple of items would statistically be
expected in that window. Flagged as an observation to check against the live
feed, not a confirmed miss (RSS feeds do have quiet news days), but this is
now the second gap of this shape and worth checking whether the sliding
20-item window is starting to drop items between the weekly-ish runs.

**2026-08-30 gap check:** the 6 new items are published 2026-08-24 through
2026-08-29 (checked directly against `corpus/manifests/bbc_igbo.jsonl`),
resuming immediately after the previous run's last recorded date
(2026-08-18). **The 2026-08-23 flag's suspected gap (2026-08-19 through
2026-08-23) is not covered by any item in this run either** — this run's
earliest new `published` date is 2026-08-24, not 2026-08-19. Since this
poll ran after the RSS window would have long since slid past that date
range, that 5-day span is now unrecoverable from this feed. Read together
with flag 2026-08-15's window-adequacy caveat, this is evidence (not proof)
that the sliding-window risk is real rather than hypothetical: a
weekly-ish cadence can permanently lose days of coverage, not just delay
them.

**2026-09-06 gap check — retracted, see the cumulative-size correction
above.** This entry described a run and a manifest state that do not
exist in `corpus/manifests/bbc_igbo.jsonl`; left here struck through in
spirit (not deleted, per this project's policy of correcting in place with
old/new values) rather than silently removed.

**2026-09-27 gap check — retracted, 2026-10-18: the "~25-day gap" was an
artifact of the same missing-runs bug the cumulative-size correction above
describes, not a real feed gap.** This entry was written against a
cumulative table that skipped the 2026-09-13 and 2026-09-20 runs entirely,
so it compared 2026-09-27's items against 2026-08-30's as if they were
adjacent. They were not: `recorded: "2026-09-13"` items are published
2026-09-04 to 2026-09-12, and `recorded: "2026-09-20"` items are published
2026-09-15 to 2026-09-19 — both checked directly against
`corpus/manifests/bbc_igbo.jsonl`. The real sequence is contiguous:
08-30 batch ends 2026-08-29 -> 09-13 batch runs 09-04 to 09-12 (6-day gap,
unremarkable) -> 09-20 batch runs 09-15 to 09-19 (3-day gap) -> 09-27 batch
runs 09-23 to 09-27 (4-day gap). There was no 25-day silence; coverage in
this window looks healthy. Left here struck through in spirit rather than
deleted, per this card's correction policy — the lesson (verify the
cumulative table against a fresh group-by before trusting a gap
calculation built on it) is worth keeping even though the specific alarm
was false.

**2026-10-18 gap check: an ~18-day gap, smaller than the retracted
2026-09-27 claim but real this time.** This run's 10 new items are
published 2026-10-15 10:14 UTC through 2026-10-18 07:50 UTC; the previous
batch (`recorded: "2026-09-27"`) tops out at 2026-09-27 07:24 UTC. That
leaves **2026-09-27 through 2026-10-15, about 18 days, with zero recorded
items** — verified directly against the manifest, with no missing-run
explanation found this time (the manifest's 9 `recorded` dates are
contiguous with this run's). Unlike the retracted 25-day claim, this gap
survives a direct check. It is also harder to dismiss than the shorter
early gaps: this run's 10 items span only 3 days (10-15 to 10-18, ≈3.3
items/day), well above the batch-1 long-run rate of ≈0.65/day used in
earlier gap assessments — if that faster rate held during the silent
window, a 10-20 item sliding RSS window could already have fully cycled
past whatever published in the first half of the gap, meaning some of this
loss may be permanent and unrecoverable from the feed, similar in kind to
the concern the (retracted) 2026-09-27 entry raised, just smaller in
degree. **Recommend to the reviewer:** check whether the ingestion workflow
actually ran on its stated cadence between 2026-09-27 and 2026-10-18 (a
21-day span between runs would itself explain most of this gap regardless
of feed-window size), and re-verify this card's running cumulative table
against a direct group-by every time, given the two-run undercount just
found above.

## Known limitations and quality flags

Flags dated **2026-08-07** unless noted. The topical-skew and register
observations below were made against the live RSS feed at fetch time; they
are **not reproducible from the manifest alone**, since (see above) no
`title` field is actually persisted to `corpus/manifests/bbc_igbo.jsonl`.

- **Manifest only — zero tokens.** This source contributes nothing to corpus
  size until someone rebuilds it locally. It is a *pointer* asset.
- **Topical skew.** Of the 11 headlines recorded, 6 concern violent crime or
  death (killings, a collapsed building, sexual assault, bodies found). This
  is normal news-cycle composition, but a corpus built from BBC Igbo will
  carry a strong negative-event and named-victim skew. Relevant for sentiment
  work (label priors will be badly unbalanced) and for anyone fine-tuning a
  generative model on it.
- **Privacy: named private individuals.** Several headlines name
  non-public-figure victims of crime. Anyone rebuilding the text should treat
  it as containing personal data about identifiable people and handle it
  accordingly — this is a stronger constraint than the copyright one for EU/UK
  researchers, and it does not expire when copyright arguments do.
- **Register.** BBC Igbo is edited, standard-orthography, journalistic Igbo
  with consistent diacritic marking — from the headlines, notably higher
  orthographic quality than the Wikipedia batch (see
  [wikipedia_ig.md](wikipedia_ig.md)). Valuable as a *reference register*
  precisely for that reason.
- **Not verified:** whether BBC Igbo articles are human-written or partly
  translated from BBC English. Worth establishing before treating this as
  gold-standard native Igbo.
- **2026-08-15 — no headline field is actually stored.** See the corrected
  "Source and method" section above. Practical effect: nothing in
  `bbc_igbo.jsonl` itself supports topic filtering, keyword search, or the
  kind of per-item skew check performed for this card at fetch time (the
  topical-skew and register flags above). A reviewer or future card author
  working from the manifest alone, without also capturing feed content at
  fetch time, cannot repeat that check — only `url` and `published` are
  available for any such analysis going forward.

## Intended uses

- **Suitable:** building a locally-rebuilt monolingual news corpus for LM
  adaptation; NER (dense in Nigerian person, place, and organisation names);
  topic classification; a high-quality orthographic reference for
  diacritic-restoration evaluation.
- **Suitable:** longitudinal tracking of Igbo news vocabulary, using the
  manifest alone as a URL index.
- **Not permitted:** committing rebuilt article text to this repository, or
  redistributing it in any dataset release.
- **Use with care:** sentiment and safety work, given the topical skew above.
