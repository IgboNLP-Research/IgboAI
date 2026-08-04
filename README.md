# IgboAI

Open research on AI for the Igbo language: self-updating literature tracking, corpora, and benchmarks spanning NLP, speech, and language models for a low-resource, tonal language.

> **Status:** early infrastructure stage. Literature tracking is live; corpora and benchmarks are planned. Nothing here should be treated as a stable resource or citable result yet.

## What lives here

- `RELATED_WORK.md` - a running, dated log of new papers, models, and datasets relevant to Igbo and closely transferable African/low-resource language work. Updated by automation, curated by a human at the PR stage.
- `scripts/fetch_candidates.py` - the deterministic fetch layer (see below).
- `.github/workflows/literature-tracking.yml` - the nightly automation.
- Corpora and benchmark suites will be added as the project grows.

## How the automation works

Every night, a scheduled GitHub Actions workflow keeps the literature log current. It is deliberately split into two layers:

**Deterministic fetch, LLM curation.** A stdlib-only Python script queries three sources - the arXiv API (preprints), OpenAlex (venue-published work: ACL Anthology venues such as ACL, EMNLP, EACL, COLING, LREC and TACL, plus workshops and journals), and the Hugging Face Hub (models and datasets). It filters by date, deduplicates against a history file (`.github/tracking/seen.json`), and writes the candidates to a scratch JSON file. Only then, and only if there is anything new, does Claude Code run: it judges relevance to Igbo specifically, writes researcher-oriented summaries into `RELATED_WORK.md`, and opens a pull request. Retrieval failures and summarization failures are therefore easy to tell apart, and days with nothing new cost nothing.

**Human-in-the-loop at the merge boundary.** The automation never pushes to `main`. Everything arrives as a pull request for human review; nothing auto-merges. The same principle will apply to future corpus and benchmark automation, where it matters even more - scraped "Igbo" text is often mislanguaged or machine-translated, and silently ingesting it would poison downstream training data.

**Tuning.** Recall is controlled by the query lists at the top of `scripts/fetch_candidates.py` (`ARXIV_QUERIES`, `OPENALEX_QUERIES`, `HF_SEARCH_TERMS`); precision is controlled by the relevance-filtering instructions in the workflow prompt. A repo-level `CLAUDE.md` describing the project's research focus sharpens the keep/discard judgments across all Claude-driven workflows.

**Known limitations.** OpenAlex indexes venue proceedings with a lag of days to weeks, so published versions surface a little after preprints. A paper tracked as an arXiv preprint may later reappear as its published version under a different identifier; these are reconciled at review time.

## License

Code is licensed under [Apache-2.0](LICENSE). Datasets added to this repository will carry their own licenses, documented per-dataset in data cards, respecting the licenses of source material.
