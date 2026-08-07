# Data card — BBC News Igbo (`bbc_igbo`)

## Source and method of collection

- **Source:** BBC News Igbo RSS feed, `https://feeds.bbci.co.uk/igbo/rss.xml`.
- **Method:** `scripts/corpus_fetch.py` parses the feed and appends one
  record per *previously unseen* article URL to
  `corpus/manifests/bbc_igbo.jsonl`. Deduplication is by SHA-1 of the URL.
- **What is stored:** `url`, `url_sha1`, `title`, `published`, `recorded`,
  and a fixed `note`. **Article body text is never fetched or stored.**
- **What is not stored:** article text, images, author bylines, comments.

The stored `title` field is the headline as it appears in the RSS feed. This
is the one piece of BBC-authored prose the manifest retains; it is kept
because it is the only human-readable handle on an entry, and headline-length
quotation for indexing purposes is a narrow use. If a reviewer judges even
this too much, the field can be dropped without affecting rebuild ability
(`url` alone is sufficient).

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

## Cumulative size

| As of | New URLs this run | Cumulative URLs |
|---|---|---|
| 2026-08-07 | 11 | 11 |

No token or character counts apply — no text is stored.

## Known limitations and quality flags

Flags dated **2026-08-07**.

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
