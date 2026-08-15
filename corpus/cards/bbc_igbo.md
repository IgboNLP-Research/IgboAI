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

No token or character counts apply — no text is stored.

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
