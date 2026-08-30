# Data card - Igbo Wikipedia (`wikipedia_ig`)

## Source and method of collection

- **Source:** `ig.wikipedia.org`, main namespace (namespace 0) only.
- **Method, phase 1 (2026-08-07 through 2026-08-15): MediaWiki Action API**
  via `scripts/corpus_fetch.py`.
  - Title discovery: `list=allpages` walked alphabetically with an
    `apcontinue` cursor in `corpus/state.json` (backfill phase); once the
    backfill completes, the fetcher switches to `list=recentchanges` from a
    stored `rc_ts` watermark.
  - Text extraction: `prop=extracts&explaintext=1`, 20 titles per request.
  - Documents whose extract is under 50 characters are dropped as stubs.
  - **This phase's batches have been relocated to `corpus/pilot/` and no
    longer count toward the cumulative totals below** (see flag 21). Files
    there: `2026-08-07.jsonl.gz`, `2026-08-13.jsonl.gz`, `2026-08-15.jsonl.gz`.
- **Method, phase 2 (from 2026-08-18): one-shot XML dump ingest**, via the
  new `scripts/corpus_dump_ingest.py`, which replaced the `allpages` walk.
  Rationale given in the script's own docstring: at ~0.7s/request the API
  walk would have taken roughly six months of weekly runs to cover Igbo
  Wikipedia's ~58k titles; a dump is one download.
  - Streams `https://dumps.wikimedia.org/igwiki/latest/igwiki-latest-pages-articles.xml.bz2`
    and decompresses incrementally (uncompressed XML never touches disk).
  - Keeps namespace-0, non-redirect pages only; drops empty bodies.
  - Cleans wikitext with `mwparserfromhell.strip_code(normalize=True,
    collapse=True)`, then strips leading media-caption fragments and
    `[citation needed]` markers.
  - Drops the page entirely if under 300 characters after cleaning
    (`MIN_CHARS`, raised from phase 1's 50-character stub threshold) or if
    residue markers (`data-mw=`, `typeof="mw:`, `{{`, `Templeeti:`) survive
    the clean, i.e. `strip_code` failed to resolve the markup.
  - Shards output at 5,000 kept documents per file so no single commit blob
    is huge; records the dump's SHA-256 and `Last-Modified` in
    `corpus/state.json` for reproducibility from a named snapshot (something
    the API walk could never offer).
  - Once the dump completes, `corpus_fetch.py`'s `recentchanges` path takes
    over from the dump's `rc_ts` watermark, so incremental updates continue
    on top of the snapshot.
- **Storage:** `corpus/raw/wikipedia_ig/<YYYY-MM-DD>.jsonl.gz` for
  incremental-fetch days; `corpus/raw/wikipedia_ig/dump-<YYYY-MM-DD>/shard-
  NNN.jsonl.gz` for the one-shot dump. Fields differ slightly by phase: dump
  documents carry `id`, `title`, `url`, `lang_claimed`, `text`, `source:
  "dump"`, `dump_modified`; incremental documents additionally carry `flags`
  (see flag 22, a gap specific to the dump path).
- **No text normalisation beyond each phase's own cleaning step is applied.**
  Markup leakage and orthographic inconsistency that survive cleaning are
  documented as quality flags below, not fixed.

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
`workflow_dispatch`. The dump ingest (phase 2 above) is not on this cadence:
it is a manual, occasional `scripts/corpus_dump_ingest.py` invocation, run
once so far (2026-08-18) to replace the slow `allpages` backfill. The weekly
workflow now drives `recentchanges` increments on top of that snapshot.

## Cumulative size

Figures below are **derived from source each run**, not accumulated from
prior cards (see flag 21 for why the pre-2026-08-18 rows no longer apply to
`corpus/raw/`).

| As of | Documents | Whitespace tokens | Characters | Source |
|---|---|---|---|---|
| 2026-08-07 – 2026-08-15 | 19 → 65 | 10,922 → 32,469 | 58,848 → 178,148 | phase-1 API walk; **now archived to `corpus/pilot/`, not `corpus/raw/`** |
| 2026-08-19, dump (corrected date, see flag 28) | **50,623** | not recoverable this run (flag 23) | not recoverable this run (flag 23) | one-shot XML dump, 11 shards |
| 2026-08-18, incremental | 21 | 22,827 | 130,182 | `recentchanges`, diacritic ratio 0.06522, this file read directly and in full |
| 2026-08-23, incremental (raw file) | 21 | 22,845 | 130,231 | `recentchanges`, diacritic ratio 0.06545, this file read directly and in full |
| 2026-08-23, incremental (deduplicated by title vs 2026-08-18) | **21 unique titles total, 0 net-new** | n/a | n/a | 20 of 21 documents byte-identical to 2026-08-18's; see flag 27 |
| 2026-08-30, incremental (raw file) | 22 | 15,245 | 88,876 | `recentchanges`, diacritic ratio 0.06793, this file read directly and in full; matches `corpus_run_summary.json` exactly |
| 2026-08-30, incremental (deduplicated by title vs 2026-08-23) | **22 net-new titles, 0 overlap** | n/a | n/a | see flag 30 — the flag-27 stagnation bug appears fixed this run |

The 50,623 figure is not from a file I opened; it is read from
`mt_probe_summary.json` (`scripts/mt_prevalence_probe.py`, committed at repo
root), which itself streamed all 11 shards. I did not decompress the 47 MB
of dump shards directly, per this run's turn-budget instruction. The 21/
22,827/130,182 figures for the incremental file **were** derived directly,
from a full single-pass read of the one file this run actually added
(`corpus/raw/wikipedia_ig/2026-08-18.jsonl.gz`, matching
`corpus_run_summary.json` exactly, confirming there is nothing else this run
produced in that file).

**Practical corpus size as of 2026-08-30: on the order of 50,666 unique
documents** (50,623 dump + 21 unique incremental pages from 2026-08-18/23 +
22 net-new incremental pages from this run, see flag 30), up from the
50,644 figure that held flat across 2026-08-18 and 2026-08-23 (flag 27).
Raw storage under `corpus/raw/wikipedia_ig/` now holds 64 incremental
records across three dated files for those 43 distinct pages, so document
counts read directly off the raw files still overstate corpus growth unless
deduplicated by title. Token/character/diacritic aggregates for the dump
portion are currently unknown corpus-wide (flag 23); do not quote a
corpus-wide `diacritic_char_ratio` until that is fixed.

**Backfill status: DONE**, via the dump (`backfill_done: true`,
`backfill_method: "dump"` in `corpus/state.json`), not via the `allpages`
walk described as in-progress in earlier versions of this card. The
`allpages`-specific observations in flags 6 and 11 below describe the
now-archived `corpus/pilot/` files, not the current `corpus/raw/` corpus.

## Known limitations and quality flags

Flags dated **2026-08-07** are from the first run
(now `corpus/pilot/2026-08-07.jsonl.gz`); flags dated **2026-08-13**
are from direct inspection of the 20 documents in
`corpus/pilot/2026-08-13.jsonl.gz`; flags dated **2026-08-15
(run 1)** are from direct inspection of the first 4 documents in
`corpus/pilot/2026-08-15.jsonl.gz`; flags dated **2026-08-15
(run 2)** are from direct inspection of the 22 documents a second same-day
run appended to that file (indices 4–25). Flags dated **2026-08-18** are
from the dump ingest and this run's 21-document incremental batch; see each
flag for which. Flags dated **2026-08-23** are from this run's 21-document
incremental batch, read in full and compared directly, document by document,
against the 2026-08-18 file. Flags dated **2026-08-30** are from this run's
22-document incremental batch, read in full and compared directly, title by
title, against the 2026-08-23 file.

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

### 7. 2026-08-13 — Non-Igbo script leakage: a full Ethiopic (Ge'ez) word mid-sentence

*2007 Nhọrọ Senate nke Naijiria na Ekiti Steeti* reads:

> Sylvester Ayodele Arise na- **ይምረጡ** anya Ekiti North, Adefemi Kila na-
> anya anya Ekiti Central na Sola Akinyede na- anya anya Ekiti South niile
> n'elu ikpo okwu nke Peoples Democratic Party

`ይምረጡ` is four Ethiopic syllabary characters (U+12ED, U+121D, U+1228,
U+1321 — "yä", "mə", "rä", "ṭu"), not a rendering glitch on Latin script.
This is a more severe version of the flag-5 pattern from 2026-08-07 (Yoruba/
IPA open-o characters signalling MT): here an MT/templating pipeline
substituted a wrong-script token for the verb slot entirely.

### 8. 2026-08-13 — Same templated verb slot renders inconsistently across a whole article category

This run's 20 documents include **8 formulaic Nigerian election-result
stubs** (Senate/governor/state-assembly, 2003–2019), all built from what is
evidently one shared template with a "represents constituency X" verb slot.
That slot renders differently — sometimes wrongly — in every instance:

- `na-ele anya Bauchi North` / `na- anya anya Bauchi Central` (word dropped,
  leaving a bare repeated `anya anya`)
- `na-amị anya Adamawa Central` (`amị` is not a standard Igbo verb form here)
- `na- ይምረጡ anya Ekiti North` (flag 7, wrong script entirely)
- `Olusola Adeyeye na- ndị Osun Central` (verb dropped completely)

Four distinct renderings of what should be one consistent phrase, within a
single 20-document batch. This points to a systematic generation defect
(bot-authored or MT-assisted template) affecting an entire Wikipedia article
category, not isolated typos. These 8 stubs are 3,394 of this run's 49,313
characters (6.9%) but the category is large — Nigeria has 36 states across
many election years and types — so the backfill should be expected to
surface hundreds more.

### 9. 2026-08-13 — Batch is heavily skewed toward violent-crime narratives, by volume

5 of this run's 20 documents concern killings or sexual assault (*2014
Ikpe ndina n'ike nke ndị òtù Birbhum* — gang rape; *2019 ndina n'ike na igbu
ọchụ na Ampang* — rape and murder; *2020 Patna-Bhabua Intercity Express
ndina n'ike* — rape; *2022 University of Idaho Massacre*; *2024 Ogbugbu
Ottawa* — mass killing). By document count that is 25%, but these are
disproportionately the batch's *longest* articles: together they account for
**33,327 of 49,313 characters (67.6%)** of this run's text. Combined with
the equivalent skew already flagged in the BBC Igbo manifest headlines (see
[bbc_igbo.md](bbc_igbo.md)), this is a second, independent signal that
readily available Igbo text sources over-represent violent-crime content
relative to general prose. Relevant for anyone drawing sentiment-label
priors or generative fine-tuning data from either source without rebalancing.

### 10. 2026-08-13 — Diacritic ratio remains volatile at this batch size, not a reliable per-run signal

This run's reported `diacritic_char_ratio` is 0.0764 (character-weighted),
but per-document ratios in the same batch range from 0.0063 to 0.1033
(unweighted mean 0.0602). The 8 election stubs (flag 8) average lower
(0.069 combined) than the batch as a whole but are not the zero-diacritic
extreme seen in last run's date stubs — under-marking severity varies by
template, not just by document length. Confirms last run's caution: do not
read the headline ratio as a corpus-health metric until batch sizes are much
larger.

### 11. 2026-08-15 — First run out of the date-stub range: no zero-diacritic stubs this batch, but n is tiny

This run's 4 documents (*2Baba*, *A-One (graffiti artist)*, *ABii National*,
*ART Holdings*) all have per-document diacritic ratios between 0.044 and
0.099 — none show the near-zero ratio or the empty-section templated-stub
shape of flag 6. This is consistent with the `allpages` cursor having moved
past the numeric/date-title range, but 4 documents is far too small a
sample to call the stub problem resolved; treat as a hypothesis for the next
several runs to confirm or refute, not a conclusion.

### 12. 2026-08-15 — Object replacement characters (U+FFFC) inline in running text (`2Baba`)

`2Baba` contains two U+FFFC OBJECT REPLACEMENT CHARACTER glyphs (`￼￼`)
embedded directly in a sentence: `Ọ bụkwa onye nnọchi anya akara maka
￼￼"National Agency for Food and Drug And Administration and Control"`. This
is the extractor's placeholder for a stripped inline image/icon (a common
MediaWiki pattern for flag or logo templates) that survived into
`explaintext` output rather than being removed. Same failure family as the
markup leakage in flag 3, different manifestation.

### 13. 2026-08-15 — Non-Igbo Unicode letter and a split-word artifact, same document

Also in `2Baba`: `Ȯra Benue` uses U+022E LATIN CAPITAL LETTER O WITH DOT
ABOVE — not an Igbo character (Igbo's dot diacritics are dot-*below*,
ọ/Ọ U+1ECD/U+1ECC); likely OCR- or copy-paste-origin corruption from a
source that used dot-above Yoruba/Africanist orthography, echoing the
wrong-orthography-letter pattern in flag 5. Separately, `"The Unstop
pable"` appears with a stray space mid-word (correct elsewhere in the same
document as `The Unstoppable`) — an extraction-side line-wrap artifact, not
a spelling variant.

### 14. 2026-08-15 — Grave-accent tone marking inconsistent within one document (`A-One (graffiti artist)`)

`màkà` (grave accent on both vowels) appears twice, alongside unmarked
`maka` used with the same meaning elsewhere in the batch (e.g. throughout
`ABii National`, `ART Holdings`). Grave accent for low tone is a legitimate
Igbo tone-marking convention, but its sporadic, document-local use next to
otherwise-unmarked text is the same inconsistent-marking pattern flagged at
batch level in flag 10 — here confirmed at the single-document level. Useful
as another positive example for tone-restoration research (see Intended
uses), but a caution against assuming any one document's tone marking is
complete or consistent.

### 15. 2026-08-15 (run 2) — Ethiopic-script substitution recurs outside the election-template category (flag 7 was not isolated)

`Abena Takyiwa` reads:

> Abena Takyiwa ( **ከውጭ** 25 Disemba 1958) bụ onye ike ụzọ Ghana...

`ከውጭ` is three Ethiopic (Amharic) syllable characters (U+12A8, U+12CD,
U+132D — "ka", "we", "che"), standing in for what should be a birth-date
marker word (compare `amụrụ`/`a mụrụ` used in this same batch's other
biographies, e.g. `Abby Chin`, `Abba Musa Rimi`). Flag 7 (2026-08-13) found
the same wrong-script substitution in an election-result template's verb
slot; here it appears in an unrelated birth-parenthetical construction in a
different document type. Two independent occurrences across two runs and two
template families point to a systematic defect somewhere upstream (MT
pipeline or template engine) that occasionally emits Ethiopic script for a
missing token, rather than a one-off glitch.

### 16. 2026-08-15 (run 2) — Literal arrow glyph (U+21B5) leaks into running text as a paragraph-break placeholder

`Abdul Yahaya`: `"...kacha baa uru na asọmpi ahụ.↵Na February 2019, Yahaya
bịanyere aka..."`. U+21B5 DOWNWARDS ARROW WITH CORNER LEFTWARDS appears
mid-sentence where a paragraph or line break should be. Same failure family
as the U+FFFC object-replacement-character leakage in flag 12 (an
extractor/serialisation placeholder surviving into `explaintext` output) but
a different specific glyph and a different underlying markup construct.

### 17. 2026-08-15 (run 2) — Title spelling absent from body; three inconsistent spellings of the same place name in one document

The document titled `Abakaléké` (URL-encoded `Abakal%C3%A9k%C3%A9`) never
once uses that spelling in its body text. Instead the body alternates
between `Abakaliki` (2 occurrences) and `Abakeleke` (5 occurrences) for the
same Ebonyi State city, e.g. `Abakaliki bụ isi obodo nke Ebonyi Steeti...`
opening the article, then `Aha Abakeleke pụtara 'Aba Nkaleke'...` two
sentences later. Three distinct spellings of one place name, none matching
the canonical title, within a single short document. Likely a
redirect/alternate-title artifact in the source wiki rather than an
extraction bug, but it means naive title-body consistency checks or
title-based entity linking will fail on this document.

### 18. 2026-08-15 (run 2) — Same markup-leakage family as flag 3, in a biography infobox pronunciation widget

`Abdulmumin Jibrin` opens: `". Abdulmumin Jibrin pronunciation ⓘ</link> (
mmalite 9 September 1976) bụ onye ike ọchịchị Naijiria..."` — a stray
leading period, the English word "pronunciation", an ⓘ info-icon glyph, and
an unclosed `</link>` tag all survive from what was presumably an audio
pronunciation template. Same defect class as flag 3 (Parsoid/MediaWiki
markup not stripped by `explaintext`), different template.

### 19. 2026-08-15 (run 2) — Open-o (U+0254) recurs a third time, in unrelated prose

`Aay Preston-Myint`: `"Emere akwụkwọ ngosi nka nke Chicago kwa afɔ 2017..."`
— `afɔ` for `afọ` ("year"), using the Yoruba/IPA open-o (U+0254) instead of
Igbo's `ọ` (U+1ECD). Flag 5 (2026-08-07) and flag 10's election stubs
(2026-08-13) already documented this substitution; this is a third,
unrelated document, reinforcing that it is a low-level recurring
character-substitution error spread across the corpus rather than isolated
to one article or template.

### 20. 2026-08-15 (run 2) — Dropped leading pronoun, same defect family as flag 8 but outside a template

`Abdul-Karim Gharaybeh`: the "Oge ọ malitere" section begins `" mụrụ
Gharaybeh na Irbid na 20 June 1923."` — missing the expected leading `Ọ`/`A`
subject pronoun before the verb (compare `A mụrụ Salih na Wad Madani...` in
the same run's `Abdin Mohamed Ali Salih`, correctly formed). Flag 8
attributed this dropped-word pattern to a specific election-result template;
seeing it in ordinary narrative prose here suggests the dropped-token defect
is broader than that one template category.

### 21. 2026-08-18 — The corpus regime changed: a one-shot dump ingest replaced the incremental backfill, 780x the document count in one step

`scripts/corpus_dump_ingest.py` (new this run) streamed the full `igwiki`
XML dump and kept 50,623 documents across 11 shards under
`corpus/raw/wikipedia_ig/dump-2026-08-18/`, per `mt_probe_summary.json`'s
document count. This landed already-committed by the time this triage pass
started; it is documented here for the first time. The phase-1 API batches
this card previously tracked (19 → 65 documents across three dates) have
been relocated to `corpus/pilot/` and are superseded, not additive. Treat
every flag below dated before 2026-08-18 as describing `corpus/pilot/`
content, still useful as documented failure modes but no longer describing
what is live in `corpus/raw/`.

### 22. 2026-08-18 — None of the 50,623 dump documents carry the `flags` heuristic that incremental documents carry

`corpus/SOURCES.md`'s quality-flagging policy describes a `flags` field
(`archaic_register`, `mt_suspect_orthography`) applied "at fetch time."
Reading `scripts/corpus_dump_ingest.py` directly: its per-document `doc`
dict has keys `id`, `title`, `url`, `lang_claimed`, `text`, `source`,
`dump_modified`, and calls neither `quality_flags()` nor writes a `flags`
key. `scripts/corpus_fetch.py` (the incremental path) does call
`quality_flags()` and does write `flags`. **Every one of the 50,623 dump
documents is unflagged for archaic-register or MT-suspect orthography
regardless of content**, while the 21 documents added by today's
incremental run are flagged normally. Any downstream filtering that trusts
the `flags` field will silently pass 99.96% of the corpus through
unscreened for these two heuristics. This is not a new heuristic proposal;
it is the existing heuristics simply not being run on the dump path.

### 23. 2026-08-18 — The dump ingest's own run summary was overwritten before any triage pass read it, and is not reconstructable within this run's budget

Both `scripts/corpus_dump_ingest.py` and `scripts/corpus_fetch.py` call
`SUMMARY_PATH.write_text(...)` unconditionally on `corpus_run_summary.json`
(`corpus_fetch.py`'s own header comment even calls the file "uncommitted",
i.e. meant to be consumed once per run, not persisted). The dump ingest
would have written its own summary (`pages_seen`, `non_mainspace`,
`redirects`, `empty`, `skipped_short`, `skipped_residue`, `kept`,
`keep_rate`, `tokens_ws`, `chars`, `diacritic_char_ratio` for all 50,623
documents) but that file was overwritten by the subsequent incremental
`corpus_fetch.py` run (this run, `mode: "all"`) before a curation pass ever
read it. What survives: the document count (50,623, via the independent
`mt_probe_summary.json` scan, flag 21) and dump provenance in
`corpus/state.json` (`dump_sha256`, `dump_modified`). Token counts, character
counts, corpus-wide diacritic ratio, and the pipeline's own skip-reason
breakdown for the dump are gone. Recomputing them requires decompressing
all 11 shards (~47 MB), which this run's turn budget explicitly rules out.
**Recommend to the reviewer:** either have the dump script write its
summary somewhere durable (not the single shared `corpus_run_summary.json`
slot), or run a dedicated stats pass over the dump shards outside the
per-PR triage budget.

### 24. 2026-08-18 — Independent MT-residue probe over the full dump: at least 36% of documents show detectable English residue, one concrete example cited in the probe script itself

`mt_probe_summary.json` (from `scripts/mt_prevalence_probe.py`, run over all
11 dump shards) buckets all 50,623 documents by English-function-word ratio:
**clean 32.14% (16,271), trace 31.58% (15,989), moderate 28.40% (14,375),
heavy 7.88% (3,988)**; separately, 178 documents (0.35%) contain
repeated-character garble (regex `([^\W\d_])\1{3,}`). The script's own
docstring names the motivating case: *"Obiọma Notre Dame de Lourdes"
contains untranslated English clauses interleaved with Igbo ("I work with
Lourdes n'oge isi njem njem")* — i.e. raw MT output left mid-sentence, a more
severe version of the wrong-script/MT patterns already flagged at 5, 7, 15,
19. The method is an explicit lower bound (the script's own caveat: fluent
MT leaves no English behind and would score "clean"; legitimate English
quotation would be over-counted), so 36% "trace or worse" is a floor, not an
estimate of true MT prevalence. **The recommended follow-up did not happen:**
the script writes a stratified `mt_probe_sample.tsv` for human annotation of
each bucket, but no such file exists anywhere in this repository or working
tree; the annotation step needed to turn these buckets into a "defensible
number" (the script's phrase) is still outstanding.

### 25. 2026-08-18 — Markup-leakage family (flags 3, 18) recurs in this run's incremental batch

`Karin Lochte` embeds a raw, unclosed citation tag: `(2008-05-08) "Karin
Lochte, director, Alfred Wegener Institute for Polar and Marine Research,
Bremerhaven, Germany". Nature 453 (254): 254. DOI:10.1038/nj7192-254a.
</ref>`. `Yenagoa` embeds a raw HTML anchor mid-sentence:
`nhazi \n2" href="./Local_government_area" id="mwHg" rel="mw:WikiLink"
title="Local government area">LGA nwere mpaghara...`. Both are
`explaintext`-extraction failures on citation/wikilink templates, same
defect family as previously flagged, confirming the API extraction path
still leaks markup on this run's small batch even though it is a different
extraction method (`prop=extracts`) from the dump's `mwparserfromhell`
cleaning (flag 22's path, which has its own residue filter instead).

### 26. 2026-08-18 — A third diacritic convention: ogonek vowels, in an incoherent, folkloric-register biography

`Nnamdi Azikiwe` has this run's lowest diacritic ratio (0.0103) and reads as
incoherent, proverb-inflected commentary rather than an encyclopedic
biography: *"Zik na agho aghugho dika mbe. Nya melu na mu afuro ya na anya
nke ųkwų. Mana Zik bu oyili dike egwu, gaa gaa n'ogwu, anu kpolunku na eju
onu."* ("Zik is deceitful like a tortoise" is a folk simile, not
encyclopedic register; several clauses do not parse as standard Igbo.) It
also uses **U+0173 (ų) and U+01EB (ǫ), ogonek-marked vowels**, in `ųkwų` and
`ǫlųrų`. This is a third distinct diacritic convention in this card, next to
modern Ọnwụ dot-below (ọ/ụ, U+1ECD/U+1ECC) and the Union-Igbo combining
up-tack of flag 2 (U+0355); ogonek marking is characteristic of older
missionary-era transcription. Worth tracking as its own pattern rather than
folding into flag 2's "archaic register," since the underlying Unicode
characters and apparent source register both differ.

### 27. 2026-08-23 — The incremental fetch is not actually advancing: today's batch is 20/21 documents byte-identical to 2026-08-18's

Read directly, in full, both `corpus/raw/wikipedia_ig/2026-08-18.jsonl.gz` and
`corpus/raw/wikipedia_ig/2026-08-23.jsonl.gz` (21 documents each). Same 21
titles, same order, in both files. **20 of 21 documents have byte-identical
`text` across the two files.** The one exception, `Chimamanda Ngozi Adichie`,
differs only by a genuine small live edit (`na Enugu` → `na obodo Enugu`,
`O gara` → `Ọ gara`, +49 characters) — evidence this really is the same
underlying `recentchanges` query re-run, not a coincidence.

`corpus/state.json`'s `rc_ts` explains why: **before this run it still read
`2026-08-04T19:55:40Z`**, identical to `dump_modified`, meaning the
2026-08-18 incremental run's `recentchanges` query never advanced the
watermark it read from, despite that run reporting 21 "new" documents. This
run advanced `rc_ts` to `2026-08-10T01:59:45Z` — a 6-day step, still 13 days
behind today (2026-08-23) — and that was not enough to avoid re-surfacing
almost the same page set.

**Practical effect: the wikipedia_ig corpus has not grown since 2026-08-18**
despite two incremental runs each logging 21 documents. `corpus/raw/
wikipedia_ig/` now holds 42 records across the two dated files for only 21
distinct pages (see the corrected cumulative-size table above).

**Recommend to the reviewer:** verify `scripts/corpus_fetch.py` persists the
`rc_ts` it actually used (not a stale default) after every run, not just
this one; and consider deduplicating `corpus/raw/wikipedia_ig/*.jsonl.gz` by
title/id before counting documents or drawing training data — this is the
pilot's near-duplicate-stub problem (flag 6) recurring at whole-batch scale
instead of within one batch.

### 28. 2026-08-23 — Correction: the dump directory is `dump-2026-08-19`, not `dump-2026-08-18` as flags 21–23 state

Confirmed directly against the repository tree
(`corpus/raw/wikipedia_ig/dump-2026-08-19/`, 11 shards, already present
before this run started) and `corpus/state.json`'s
`ingested_at: 2026-08-19T10:01:36Z`. Flags 21–23 above, and the cumulative-
size table's "dump" row, described the same one-shot ingest under the wrong
date label ("2026-08-18"). `dump_modified` (2026-08-04T19:55:40Z) is the
*source dump's own* timestamp, not the ingest date, and is not where the
"2026-08-18" label came from either — it is simply wrong. Flags 21–23's
prose is left as originally written, since the events they describe are
otherwise accurate; the cumulative-size table above is corrected to
"2026-08-19, dump".

### 29. 2026-08-23 — Zero of the 21 incremental documents carry either heuristic flag, though at least two should

Checked directly: every document in both `2026-08-18.jsonl.gz` and
`2026-08-23.jsonl.gz` has `"flags": []`. Yet this same 21-document batch
contains documents this card already flags as clear quality issues:

- `Nnamdi Azikiwe` (flag 26) — this batch's lowest diacritic ratio (0.0103),
  incoherent proverb-register prose ("Zik na agho aghugho dika mbe"), and
  legacy ogonek diacritics (ų, ǫ) not used in modern Ọnwụ orthography. This
  is close to the textbook definition of `archaic_register`, by the flag's
  own name, and it is not caught.
- `Karin Lochte` and `Yenagoa` (flag 25) — raw, unclosed markup surviving
  extraction (`</ref>`, an `href="./Local_government_area"` HTML anchor).
  Neither existing flag name (`archaic_register`, `mt_suspect_orthography`)
  obviously covers markup leakage, which suggests it needs its own heuristic
  rather than being folded into `mt_suspect_orthography`.

**Proposed heuristic patterns, for the reviewer to evaluate against a larger
sample before wiring in:**

1. `archaic_register`: flag when `diacritic_char_ratio < 0.02` for a
   document over some minimum length (to avoid penalizing short, legitimately
   diacritic-light stubs) **and** the text contains at least one of the
   legacy-orthography markers already catalogued in this card — U+0355
   (combining up-tack, flag 2), U+0173/U+01EB (ogonek ų/ǫ, flag 26), or the
   lexical markers `nile`, `we je`, `ulo uku` (flag 2).
2. A new flag, e.g. `markup_leakage` (distinct from `mt_suspect_orthography`):
   trigger on residual-markup regexes that have now recurred across four
   separate documents in this card (flags 3, 18, 22, 25) —
   `</ref>`, `href="\./`, `data-mw=`, `typeof="mw:`, literal `Templeeti:`.
   This defect is specific to the `prop=extracts` incremental path (flag 22
   already notes the dump path has its own, different residue filter), so
   scoping the heuristic to incremental documents only would reduce false
   positives.

Not fixed here — this card's author does quality triage, not pipeline edits
(see the hf_catalog card's flag 2 for the same division of labour applied
there).

### 30. 2026-08-30 — The flag-27 stagnation bug appears fixed: this run's 22 documents are all net-new, zero overlap with 2026-08-23

Read both `corpus/raw/wikipedia_ig/2026-08-30.jsonl.gz` (22 documents) and
`corpus/raw/wikipedia_ig/2026-08-23.jsonl.gz` (21 documents) directly and
compared titles: **zero title overlap**, all 22 of this run's documents are
new. `corpus/state.json`'s `rc_ts` advanced from `2026-08-10T01:59:45Z` to
`2026-08-30T09:01:23Z` — a 20-day jump, versus the 6-day step that still
left the fetch stuck last run. This is consistent with flag 27's fix
recommendation (persist the actually-used `rc_ts`) having taken effect, but
one clean run is not proof the watermark-persistence logic is now correct
in general; worth another confirming check next run before closing flag 27
out for good.

### 31. 2026-08-30 — Markup-leakage family (flags 3, 18, 22, 25) recurs in 5 of 22 documents (23%) this run

`</ref>` residue in `Abby Jane Morrell` (×2), `Aize Obayan`, `Akpụkpọ anụ a
na-atụfu`, and `Alaide Gualberta Beccari` (×4); an unexpanded `Templeeti:`
token in `100% eneji emeghariri ọhụrụ`. Same `prop=extracts` extraction
failure on citation templates as previously documented, but the highest
per-batch incidence rate seen yet for this defect family. Reinforces the
`markup_leakage` heuristic proposed in flag 29 — with 23% incidence in a
22-document batch, this is no longer a rare edge case on the incremental
path.

### 32. 2026-08-30 — `mt_suspect_orthography` fires on `Achille Mbembe`, but the trigger is a legitimate IPA pronunciation guide, not MT residue

The flagged character is U+025B (ɛ) inside `/ əmˈbɛmbeɪ/`, an English-style
IPA pronunciation gloss for the name "Mbembe" — standard practice on
Wikipedia biographies, not a translation artifact. This is a false positive
for the *reason* the heuristic exists (catching Yoruba/IPA-adjacent
character substitution as an MT signal, flags 5, 19), even though the
character match is correct. Consistent with `mt_prevalence.md`'s finding
that `mt_suspect_orthography` has 100% precision on only a single document
(n=1) in the annotated sample — this run's one hit suggests that precision
figure was already an overestimate, not just a small sample. Worth
excluding IPA-slash-delimited spans (`/…/` or `[…]` immediately after a
proper noun) from the heuristic before trusting its precision further.

## Intended uses

- **Suitable:** language-model pre-training (after dedup, MT-residue
  filtering per flag 24, and the flags-coverage gap in flag 22), vocabulary/
  tokeniser construction, orthography and diacritic-restoration research
  (the corpus now contains modern Ọnwụ, Union-Igbo combining-tack, and
  ogonek conventions side by side, per flags 2 and 26), Igbo NER seed data
  (Nigerian political and biblical entities are well represented).
- **Use with care:** anything sensitive to orthographic uniformity (TTS front
  ends, grapheme-to-phoneme, tone modelling) — flags 2, 6, and 26 will bite.
- **Not suitable:** MT training without filtering. At least 36% of the dump
  shows detectable English MT residue (flag 24, a lower bound), and a
  substantial share of Igbo Wikipedia is itself machine-translated from
  English (flag 5); training MT on this corpus risks laundering MT output
  back into the model.
- **Not suitable as a fluency reference** for evaluation sets without human
  vetting of each item.
- **Not yet suitable for anything that depends on the `flags` heuristic**
  (e.g. "exclude archaic_register" or "exclude mt_suspect_orthography" as a
  filter step) over the dump portion of the corpus, until flag 22 is fixed:
  that filter currently passes the entire dump through as if unflagged.
