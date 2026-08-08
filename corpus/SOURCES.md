# Corpus sources and storage policy

> **Licensing:** This file is the licensing and storage policy of record for all material under `corpus/`; it governs reuse as well as collection. For general repo licensing, see [Licensing](../README.md#licensing).

Each source class is handled according to what its licensing permits in a public repository. This file is the policy of record; the pipeline enforces it.

| Source class | Example | What we store publicly | License basis |
|---|---|---|---|
| Wikipedia/Wikisource | ig.wikipedia.org | Full text (`corpus/raw/`) with per-document URL attribution | CC BY-SA 4.0 |
| News | BBC Igbo RSS | URL manifests only (`corpus/manifests/`) - never article text | Copyrighted; manifests enable local, non-redistributed rebuilds |
| HF / Masakhane datasets | MasakhaNER, MAFAND-MT | Catalog metadata only (`corpus/catalog/`) - data stays on the Hub under its own license | Per-dataset |
| Religious parallel text | Igbo Bible translations | Nothing yet - each text requires individual license/public-domain verification before ingestion (JW300's withdrawal is the cautionary precedent) | Per-text, verify first |

## Quality flagging policy (adopted 2026-08-07, from PR #4 review)

Raw documents carry a `flags` field applied heuristically at fetch time: `archaic_register` (Union-Igbo era orthography, e.g. Bible-derived prose) and `mt_suspect_orthography` (non-Igbo characters such as ɔ/ɛ indicating machine translation or wrong-language leakage). Flagged text is retained, not deleted: archaic register is linguistically valuable when labelled; MT-suspect text is excluded from MT training uses at derivation time. News manifests store URLs and dates only; headline text is not retained (privacy and skew, PR #4 F7).

Human review gates every addition: nothing reaches `main` except by merged PR. Quality flags and per-source documentation live in `corpus/cards/`.

Adding a source = adding it to `scripts/corpus_fetch.py` (or a new fetcher) AND a row here AND a license note. All three or it doesn't ship.
