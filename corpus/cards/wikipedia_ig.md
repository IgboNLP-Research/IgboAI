# Data card - Igbo Wikipedia (`wikipedia_ig`)

## Source and method of collection

- **Source:** `ig.wikipedia.org`, main namespace (namespace 0) only.
- **Method:** MediaWiki Action API via `scripts/corpus_fetch.py`.
  - Title discovery: `list=allpages` walked alphabetically with an
    `apcontinue` cursor in `corpus/state.json` (backfill phase); once the
    backfill completes, the fetcher switches to `list=recentchanges` from a
    stored `rc_ts` watermark.
  - Text extraction: `prop=extracts&explaintext=1`, 20 titles per request.
  - Documents whose extract is under 50 characters are dropped as stubs.
- **Storage:** `corpus/raw/wikipedia_ig/<YYYY-MM-DD>.jsonl.gz`, one JSON
  object per line with fields `id`, `title`, `url`, `lang_claimed`, `text`,
  `fetched`, `license`, `provenance`.
- **No text normalisation is applied.** What is stored is what the API
  returned, including any markup leakage or orthographic inconsistency (see
  quality flags).

## License and attribution

- **License:** CC BY-SA 4.0 (Wikipedia text). A small amount of Wikipedia
  content is additionally GFDL-licensed; CC BY-SA 4.0 is the operative
  license for reuse here.
- **Attribution requirement:** every document carries its `url`, which is the
  attribution handle. Any derived corpus, model card, or publication that
  redistributes this text must credit Igbo Wikipedia and preserve
  share-alike terms on the redistributed text.
- **Share-alike caveat for downstream use:** CC BY-SA is copyleft on the
  *text*. Model weights trained on it are generally not treated as derivative
  works, but a released *dataset* that includes this text must stay BY-SA.
  Do not silently merge it into a permissively-licensed corpus release.

## Update cadence

Weekly — `.github/workflows/corpus-ingestion.yml`, Sundays 04:00 UTC, capped
at `max_pages` titles per language per run (default 500). Manual runs via
`workflow_dispatch`.

## Cumulative size

| As of | Documents | Whitespace tokens | Characters |
|---|---|---|---|
| 2026-08-07 | 19 | 10,922 | 58,848 |

*(First run of this source. Later runs add their batch to these totals.)*

**Backfill status: IN PROGRESS.** `backfill_done: false`; the `allpages`
cursor sits at `2000_Sacagawea_dollar_-_Washington_quarter_mule`, i.e. still
in the numeric/early-alphabet range. The batch composition below is therefore
*not* representative of Igbo Wikipedia as a whole — it is the head of an
alphabetical walk, which is why it is dominated by date and year stubs.

## Known limitations and quality flags

All flags dated **2026-08-07**, from direct inspection of
`corpus/raw/wikipedia_ig/2026-08-07.jsonl.gz`.

### 1. One document is 86% of the batch — batch-level statistics are meaningless

`1 Ndị Eze` (`wiki:ig:60346`) is 50,333 of 58,848 characters (85.5%) and
9,383 of 10,922 whitespace tokens (85.9%). The summary's headline
`diacritic_char_ratio` of **0.07866 is essentially that one article's ratio
(0.0834)**. The other 18 documents together average **0.0504**, and range
from 0.0000 to 0.1026. Do not quote per-run diacritic ratios as a corpus
health metric while batch sizes are this small and this skewed.

### 2. Mixed orthography *within* a single document (`1 Ndị Eze`)

The article interleaves modern standard (Ọnwụ) Igbo with archaic Union-Igbo
orthography, evidently because narrative sections were lifted from an old
Bible translation while the framing prose is modern:

> …bú onye-isi ndi-ob͕ū nke eze, ma-ọbu onye-nche-ya… **Netan bịakwutere
> Bat-sheba, bụ́ nne Sọlọmọn, gwa ya ihe na-emenụ.**

Two orthographies in adjacent sentences. Concretely:

- **25 occurrences of U+0355 COMBINING UP TACK BELOW** (`ob͕ū`, `Mb͕e`),
  spanning 63% of the document. This character is **not part of the modern
  Igbo character set**; it will not survive naive NFC/NFD normalisation
  cleanly and will fragment subword vocabularies.
- Archaic lexis/spelling: `ulo uku` (×9, modern `ụlọ ukwu`), `nile` (×10,
  modern `niile`), `we je`, `anēmeghi`, hyphenated compounds
  (`onye-isi-ọchi-agha`, `ugwọ-ọlu-nchu-àjà`).
- Inconsistent tone marking: `bụ́` with combining acute in modern sections,
  unmarked `bụ` elsewhere.

**Implication:** valuable as historical/religious-register Igbo, actively
harmful if mixed unlabelled into a modern-Igbo LM or a normalisation-
sensitive TTS front end. Recommend segment-level orthography tagging, or
excluding this document from modern-standard training splits.

### 3. Parsoid/MediaWiki markup leakage — `explaintext` did not clean 3 pages

- `!Kweiten-ta-ǀǀKen`: **466 of 1,039 characters (45%) are a raw markup
  blob** — `<San about="#mwt6" class="rt-commentedText nowrap"
  data-mw='{"akụkụ":[{"ụdị":{"target":{"wt":"IPAc-en"…` — embedded JSON
  template parameters, an unclosed HTML-ish tag, and `typeof="mw:Transclusion"`.
- Unexpanded template names survive as literal text: `Templeeti:` appears 3×
  — `Templeeti:Election results` at the end of *1979 Nhọrọ gọvanọ nke Cross
  River State*, and `Templeeti:First Book of KingsTempleeti:Second Book of
  Kings` at the end of *1 Ndị Eze*.

### 4. Encoding damage in `!Kweiten-ta-ǀǀKen`

The stored text begins `CæKweiten-ta-Ken` while the article title is
`!Kweiten-ta-ǀǀKen`. Both U+01C0 dental-click letters have been lost from the
body text and a spurious `Cæ` prefix introduced. Mojibake, not a legitimate
click transcription — the clicks in the *title* are correct, so this is
extraction-side damage.

### 5. Non-Igbo characters signalling machine translation

`1991 Nhọrọ gọvanọ nke Kaduna Steeti` contains:

> **Ɔ** James Bawa Magaji ka **ɔ** ga-eso ya.

U+0186/U+0254 (open O) belongs to Yoruba/Ewe/IPA orthography; Igbo uses
`Ọ/ọ` (U+1ECC/U+1ECD). `ɛ` also appears 2× in the batch. Combined with the
garbled date `mere na 14, 1991` (month dropped from "March 14, 1991") and
the incoherent `meri mbụ nke mbụ`, this document reads as unedited MT output.

Same pattern in `1979 Nhọrọ gọvanọ nke Cross River State`:
`Nhọpụta steeti steeti Kuros Riva` (duplicated noun), `meri Iran site na ihe
vootu kacha elu` ("Iran" is a mistranslation artifact), `ma merie nnukwu
mmegide na ike ahụ ahụ` (incoherent). Both documents also begin with stray
leading whitespace/periods (`.         Nhọpụta…`).

### 6. Template-generated near-duplicate stubs with empty sections

Nine of nineteen documents are formulaic date/year stubs with 90–224
characters of body text and 3–4 **empty** section headers each (`== Ihe mere
na 11 Disemba ==`, `== Onye amuru ==`, `== Onye wuru ==` with nothing
under them). `14 Febrụwarị` and `18 Febrụwarị` are **78.8% character-identical**.

These stubs also use **dotless, unmarked orthography** and carry untranslated
English residue — `11 Disemba` (diacritic ratio **0.0000**) reads:

> 11 Disemba bu ubochi nke 11th (nke iri na out) na onwa ana kpo Disemba. Na
> Gregorian calender, 11 Disemba bu ubochi nke 345th…

Note `bu`/`ubochi`/`onwa`/`afo`/`anyi` for `bụ`/`ụbọchị`/`ọnwa`/`afọ`/`anyị`;
English ordinals `11th`/`345th`; the misspelt English `Gregorian calender`;
and `nke iri na out` where `out` is a corruption of `otu`. This is the
explanation for the zero diacritic ratio — genuine orthographic
under-marking, not an encoding fault.

**Recommendation:** near-duplicate detection and downweighting before any LM
pre-training use; the alphabetical backfill will surface many hundreds more
of these.

## Intended uses

- **Suitable:** language-model pre-training (after dedup and the caveats
  above), vocabulary/tokeniser construction, orthography and diacritic-
  restoration research (this batch is a good natural testbed — it contains
  fully-marked, partially-marked, and unmarked text), Igbo NER seed data
  (Nigerian political and biblical entities are well represented).
- **Use with care:** anything sensitive to orthographic uniformity (TTS front
  ends, grapheme-to-phoneme, tone modelling) — flags 2 and 6 will bite.
- **Not suitable:** MT training without filtering. A substantial share of
  Igbo Wikipedia is itself machine-translated from English (flag 5), so
  training MT on it risks laundering MT output back into the model.
- **Not suitable as a fluency reference** for evaluation sets without human
  vetting of each item.
