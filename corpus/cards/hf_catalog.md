# Data card — Hugging Face dataset catalog (`hf_catalog`)

## Source and method of collection

- **Source:** Hugging Face Hub datasets API,
  `https://huggingface.co/api/datasets?search=<term>&limit=50&full=true`.
- **Search terms:** `igbo`, `yoruba`, `hausa`, `naija`, `pidgin nigerian`,
  `masakhane`, `african languages`.
- **Method:** `scripts/corpus_fetch.py` queries each term, deduplicates by
  dataset id, and records `id`, `url`, `license`, `languages`, `tags`,
  `downloads`, `last_modified`, `matched_term`, sorted by download count.
- **What is stored:** `corpus/catalog/hf_datasets.json` — **metadata only**.
  No dataset content is downloaded or committed. Datasets remain on the Hub
  under their own licenses (see `corpus/SOURCES.md`).

## License and attribution

The catalog file itself is factual metadata. **Each listed dataset carries
its own license**, which governs any actual use of its data. A dataset
appearing in this catalog is *not* an endorsement that it is usable — it is
a pointer to be license-checked before ingestion.

Datasets whose license field resolves to `UNKNOWN` must be treated as
**"verify before use"**: unlicensed, not permissively licensed. The Hub's
license field is self-declared by uploaders and is frequently absent, wrong,
or inapplicable to re-uploaded third-party data.

## Update cadence

Weekly, with the rest of the ingestion workflow (Sundays 04:00 UTC). The
catalog is rebuilt in full each run; `new_since_last_run` diffs against the
previous file.

## Cumulative size

| As of | Datasets catalogued | New this run |
|---|---|---|
| 2026-08-07 | **0 (fetch failed — see below)** | 0 |
| 2026-08-15 | 278 | 0 |
| 2026-08-18 | 278 | 0 |
| 2026-08-23 | 286 | 8 |
| 2026-08-30 | 290 | 4 |

**2026-08-18:** verified directly by diffing dataset ids between this run's
`corpus/catalog/hf_datasets.json` and the prior commit's: identical 278-id
set, zero additions, zero removals. The file still shows as fully changed
in `git diff` because the catalog is rebuilt from scratch each run (per-
dataset fields like `downloads` and `last_modified` refresh even when the
member set doesn't change) — a byte-level diff is not evidence of new
datasets; `new_since_last_run` is the field to trust, and it agrees with the
id-set check here.

**Provenance gap:** the fetch recovered from the 2026-08-07 rate-limit
failure at some point before this run (the committed
`corpus/catalog/hf_datasets.json` already held 278 entries at the start of
this run, and `new_since_last_run` is empty), but no card update recorded
that recovery or an intermediate count. The table above cannot show when the
catalog actually filled in; treat the 278 figure as "current as of
2026-08-15" rather than as a stable long-run trend point.

## Notable datasets (first full listing — populated 2026-08-15)

This section was never filled in previously because every prior run either
failed (2026-08-07) or landed without a card update. With 278 entries now on
file and `new_since_last_run` empty, this is a survey of the current catalog
rather than a diff. By search term: `igbo` 50, `yoruba` 51, `hausa` 51,
`naija` 47, `masakhane` 46, `african languages` 22, `pidgin nigerian` 11
(terms overlap; totals don't sum to 278).

- **`HausaNLP/NaijaSenti-Twitter`, `HausaNLP/AfriSenti-Twitter`** — CC-BY-NC-
  SA-4.0, multi-way sentiment over Hausa/Igbo/Yoruba/Pidgin (and, for
  AfriSenti, a dozen more African languages) Twitter text. Directly relevant
  to Igbo sentiment work; non-commercial license restricts downstream use.
- **`Davlan/masakhanerV1`, `BlakBot/masakhaner`** — MasakhaNER, the standard
  African-language NER benchmark, includes Igbo. License field is `UNKNOWN`
  on both listings despite the underlying MasakhaNER release being CC-BY-
  4.0-ish in its paper/repo — **verify against the original MasakhaNER
  release before treating the Hub license field as authoritative.**
- **`Davlan/NaijaRC`** — CC-BY-NC-4.0 reading-comprehension set covering
  Igbo, Yoruba, and Hausa. Non-commercial.
- **`HausaNLP/Naija-Lex`, `HausaNLP/Naija-Stopwords`** — CC-BY-NC-SA-4.0
  lexicon/stopword resources spanning Igbo, Hausa, Yoruba.
- **`ccibeekeoc42/TinyStories_igbo`, `ccibeekeoc42/DollyHHRLHF_igbo`,
  `ccibeekeoc42/english_to_igbo`** — Apache-2.0/MIT Igbo instruction- and
  story-style parallel data, apparently machine-translated from the English
  originals (TinyStories, Dolly). Permissively licensed but MT provenance
  means the same MT-laundering caution as this card's Wikipedia sibling
  applies if used for MT training.
- **`Tommy0201/JW300_Igbo_To_Eng`** — built from JW300, a dataset whose
  withdrawal is already flagged as a standing precedent in
  `corpus/SOURCES.md`; this re-upload's `UNKNOWN` license needs verification
  regardless of the parent corpus's own history.
- **Long tail of `UNKNOWN`-license, low-download re-uploads**, notably the
  `michsethowusu/igbo-<lang>_sentence-pairs` series (Igbo paired with Shona,
  Tumbuka, Xhosa, Pedi, Yoruba, Kikuyu, etc.) — plausible bitext but
  unverified license and unverified sentence-alignment quality; "verify
  before use" per the license policy below.

## 2026-08-23 — 8 new datasets

All 8 arrived via the `african languages` / `yoruba` search terms rather than
a direct `igbo` match; one (`0xnu/igbo`) is Igbo-specific by id, the rest are
multi-language African-language bundles or catalogs that list `ig` among
many other language codes (or list no `languages` at all).

- **`0xnu/igbo`** — Apache-2.0, tagged `ig` directly. Worth a closer look on
  its own merits, not just as part of a bundle.
- **`rufatronics/african-languages-hplt-filtered`, `VelkroLM/african-
  languages-corpus`** — CC0-1.0 (public-domain-equivalent), both list `ig`
  alongside ten-plus other African languages (ha, yo, pcm-adjacent kr, ff,
  am, so, ti, wo, ln, lg, sn). Permissive license; worth checking how much of
  the bundle is actually Igbo before committing to ingest.
- **`rufatronics/african-languages-filtered`, `VelkroLM/african-languages-
  filtered`** — license `other` (not a standard SPDX identifier on the Hub);
  treat like an unclear license, i.e. read the dataset card before use, even
  though this is a step above `UNKNOWN`.
- **`VelkroLM/african-languages-catalog`** — license `UNKNOWN`, no
  `languages` field populated. **Verify before use.**
- **`VelkroLM/african-languages-speech`** — CC-BY-4.0 but no `languages`
  field populated; unclear from the catalog alone whether it actually
  contains Igbo speech data or just matched the `african languages` search
  term.
- **`michsethowusu/kikuyu-yoruba_sentence-pairs`** — license `UNKNOWN`, and
  not an Igbo pair (Kikuyu-Yoruba); listed here only because it matched a
  search term. Same `michsethowusu/*_sentence-pairs` family already flagged
  in the notable-datasets list below for its Igbo-paired siblings.

## 2026-08-30 — 4 new datasets

- **`michsethowusu/Code-170k-igbo`** — Apache-2.0, tagged `ig` only. By id
  this reads as ~170k code-generation/instruction examples with Igbo-
  language text, likely translated (machine or otherwise) from an English
  code-instruction corpus into the `michsethowusu` uploader's usual
  translated-pairs style (compare the `*_sentence-pairs` family already
  flagged in this card). Permissive license; worth a closer look at
  translation quality before use, same MT-provenance caution as the
  `ccibeekeoc42` entries above — code-instruction text machine-translated
  into Igbo is a plausible but unverified source of unnatural or
  code-switched Igbo.
- **`McGill-NLP/NaijaS2ST`** — license `UNKNOWN`, audio+text, speech-to-
  speech translation across English/Hausa/Igbo/Yoruba/Naija-Pidgin
  (10K-100K scale, per its size-category tag). If the license clears, this
  is directly relevant to Igbo ASR/TTS and speech-translation work, and is
  one of the few catalogued datasets pairing Igbo *speech* rather than text
  alone. **Verify before use.**
- **`CLEAR-Global/Hausa-Synthetic-ASR-Dataset-XTTS`** (CC-BY-4.0) and
  **`CLEAR-Global/TWB-voice-TTS-Hausa-1.0-sampleset`** (license `other`) —
  both Hausa-only (no Igbo tag), synthetic/TTS-derived ASR data from CLEAR
  Global (Translators without Borders). In scope per this project's
  Nigerian-language relevance policy, and the XTTS synthetic-ASR generation
  method is a technique that could transfer to bootstrapping Igbo ASR data
  where recorded speech is scarcer than text; worth reading the method even
  though the data itself is Hausa-only.

## Known limitations and quality flags

### 1. 2026-08-07 — all seven Hub queries failed; catalog written as `[]`

`corpus/catalog/hf_datasets.json` contains `[]` and the run summary reports
`"total": 0`. Verified directly from this runner:

```
GET https://huggingface.co/api/datasets?search=igbo&limit=3&full=true
  -> HTTP Error 429: Too Many Requests
```

The search terms include `igbo` and `masakhane`, which on a healthy run
should match well-known resources (MasakhaNER, MasakhaNEWS, MAFAND-MT,
Lacuna/IgboNLP releases, FLORES-200 derivatives). Zero results for all seven
terms is only consistent with total request failure — shared GitHub Actions
runner IPs are rate-limited by the Hub.

`fetch_hf_catalog` catches per-term exceptions and only warns to stderr, so
the run reported success. **Treat this run as producing no HF catalog data.**

### 2. Failure is silent *and* destructive — needs a pipeline fix

Two coupled defects, flagged for the reviewer (not fixed here; this card's
author does quality triage, not pipeline edits):

- **Unconditional overwrite.** `fetch_hf_catalog` writes `entries` to
  `hf_datasets.json` whether or not any query succeeded
  (`scripts/corpus_fetch.py:218`). This run was harmless — there was no
  prior catalog. On any *future* run, a transient 429 will overwrite an
  accumulated catalog with `[]`, silently losing it.
- **The loss then masquerades as novelty.** After such a wipe, the next
  successful run diffs against an empty `prev_ids` and reports **every**
  dataset as `new_since_last_run` — producing a large fake "new datasets"
  section in that run's PR.
- **The workflow gate can suppress triage.** `.github/workflows/corpus-ingestion.yml`
  counts `len(new_since_last_run)` toward the "did we fetch anything" gate.
  A wipe contributes 0, so an HF-only failure run could skip the triage step
  entirely and leave the wipe undocumented.

Suggested remedy for the reviewer to consider: track per-term success, and
skip the write (or merge into the existing catalog rather than replacing it)
when any term failed; surface a `failed_terms` list in the run summary.

### 3. Metadata-quality caveats that will apply once the fetch works

- `license` is read from `cardData.license` with a fallback, defaulting to
  the literal string `UNKNOWN`. Absent ≠ permissive. **As of 2026-08-30,
  163 of the 290 catalogued datasets (56.2%) carry `UNKNOWN`** — counted
  directly from `corpus/catalog/hf_datasets.json` (was 162/286, 56.6%, on
  2026-08-23) — so this is the majority case, not an edge case, and it is
  not shrinking; do not filter or sort on license without first routing
  `UNKNOWN` entries to manual review.
- `languages` comes from self-declared card metadata and is often missing or
  wrong on African-language datasets; do not filter on it alone.
- `search` matches names and descriptions, so `naija` and `african languages`
  will pull in false positives, and datasets with no matching keyword in
  their card will be missed entirely regardless of relevance.
- The catalog captures a **snapshot**. Hub datasets are mutable and can be
  gated or withdrawn — JW300's withdrawal is the standing cautionary
  precedent (`corpus/SOURCES.md`). Re-verify license and availability at the
  moment of actual use, not from this file.

## Intended uses

- **Suitable:** discovery and triage — finding candidate Igbo and related
  Nigerian/African-language datasets worth a human license review.
- **Suitable:** tracking the ecosystem over time (what appears, what
  disappears, what gets re-licensed).
- **Not suitable:** as a license source of record. Always confirm on the Hub
  and in the dataset's own documentation before ingesting anything.
