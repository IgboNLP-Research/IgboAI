# Corpus sources and storage policy

Each source class is handled according to what its licensing permits in a
public repository. This file is the policy of record; the pipeline enforces it.

| Source class | Example | What we store publicly | License basis |
|---|---|---|---|
| Wikipedia/Wikisource | ig.wikipedia.org | Full text (`corpus/raw/`) with per-document URL attribution | CC BY-SA 4.0 |
| News | BBC Igbo RSS | URL manifests only (`corpus/manifests/`) — never article text | Copyrighted; manifests enable local, non-redistributed rebuilds |
| HF / Masakhane datasets | MasakhaNER, MAFAND-MT | Catalog metadata only (`corpus/catalog/`) — data stays on the Hub under its own license | Per-dataset |
| Religious parallel text | Igbo Bible translations | Nothing yet — each text requires individual license/public-domain verification before ingestion (JW300's withdrawal is the cautionary precedent) | Per-text, verify first |

Human review gates every addition: nothing reaches `main` except by merged PR.
Quality flags and per-source documentation live in `corpus/cards/`.

Adding a source = adding it to `scripts/corpus_fetch.py` (or a new fetcher)
AND a row here AND a license note. All three or it doesn't ship.
