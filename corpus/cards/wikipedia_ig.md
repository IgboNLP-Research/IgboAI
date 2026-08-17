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
| 2026-08-13 | 39 | 20,125 | 108,161 |
| 2026-08-15 (run 1) | 43 | 22,012 | 118,610 |
| 2026-08-15 (run 2) | 65 | 32,469 | 178,148 |

*(2026-08-15 run 1 added 4 documents, 1,887 whitespace tokens, 10,449
characters. A second run landed later the same day — hence "run 1"/"run 2" —
adding a further 22 documents, 10,457 whitespace tokens, 59,538 characters,
per-document diacritic ratios ranging 0.0070–0.1135.)*

**Backfill status: IN PROGRESS.** `backfill_done: false`; the `allpages`
cursor advanced `24_Julaị` → `A_Child_Is_Born` (run 1) → `Abiodun_Essiet`
(run 2). The walk is now fully into ordinary alphabetical biography/topic
titles ("Ab-" surnames), well past the numeric/date-title range. Run 2's 22
documents contain **no zero-diacritic date stubs and no empty-section
templated stubs** (the flag 6 pattern) — every document is a genuine
biography or topic article. This confirms, with a much larger sample than
run 1's 4 documents, the hypothesis in flag 11 below: the stub-heavy pattern
was specific to the date/numeric-title range the walk has now left. The
MT-suspect and markup-leakage patterns (flags 3, 5, 7, 8), however, persist
at similar or higher rates in ordinary articles — see flags 15–20.

## Known limitations and quality flags

Flags dated **2026-08-07** are from the first run
(`corpus/raw/wikipedia_ig/2026-08-07.jsonl.gz`); flags dated **2026-08-13**
are from direct inspection of the 20 documents in
`corpus/raw/wikipedia_ig/2026-08-13.jsonl.gz`; flags dated **2026-08-15
(run 1)** are from direct inspection of the first 4 documents in
`corpus/raw/wikipedia_ig/2026-08-15.jsonl.gz`; flags dated **2026-08-15
(run 2)** are from direct inspection of the 22 documents a second same-day
run appended to that file (indices 4–25).

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
