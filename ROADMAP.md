# IgboAI roadmap

The plan of record. Phases overlap; the ordering states dependency, not a
strict schedule. Automation principle throughout: deterministic fetch and
compute, LLM curation and documentation, human judgment at every merge.

## Phase 0: Infrastructure (done)
Public repo under IgboNLP-Research; branch protection on main; least-privilege
credentials (repo secret, app scoped to this repo, spend cap); two-layer
workflow pattern established.

## Phase 1: Literature tracking (live, nightly 05:00 UTC)
arXiv + OpenAlex + HF sweeps; monthly logs plus entries.jsonl; relevance
policy in CLAUDE.md; discard audit trail in PR bodies. Ongoing tuning:
precision/recall of the relevance bar.

## Phase 2: Corpus ingestion (live, weekly Sun 04:00 UTC)
Wikipedia full text (CC BY-SA, backfill in progress); news URL manifests
(no text stored); HF catalog (metadata only). Per-document quality flags
(archaic_register, mt_suspect_orthography) applied at fetch time; data cards
maintained per source; policy of record in corpus/SOURCES.md.

## Phase 3: Source expansion
- GitHub repo catalog (metadata + license only; authenticated via the
  workflow's built-in token; unlicensed repos flagged "verify before use").
- Religious/parallel text: per-text public-domain or license verification
  before any ingestion (policy: SOURCES.md).
- Additional Wikipedia languages (yo, ha, pcm) as deliberate additions.
- Speech data cataloguing (Common Voice Igbo and successors).

## Phase 4: Derivation and evaluation
- corpus/raw -> derived training sets: dedup/near-dup detection, flag-aware
  filtering (e.g. exclude mt_suspect from MT training), per-document language
  ID, splits with provenance. Derivation scripts are versioned; derived sets
  are reproducible from raw + script + config.
- Benchmark harness: standard Igbo test sets (NER, MT, sentiment, ASR as
  available), scheduled evaluation of new models from the tracked catalog,
  leaderboard table in the repo with committed run logs. Compute budget caps
  and pinned dataset versions for comparability.

## Phase 5: Models
Baseline adaptation experiments (AfriBERTa/AfroXLMR-class, NLLB-class MT,
speech models) trained/fine-tuned on derived sets; released via the org with
model cards mirroring the data-card discipline.

## Continuous: The IgboAI paper (versioned)
A living resource/infrastructure paper in paper/ (LaTeX):
aims and design of the project; the automation architecture and its
human-review economics; challenges of low-resource ingestion (licensing,
MT pollution, orthographic variation) with evidence from the pipeline's own
review records; corpus analysis; benchmark results as they arrive.
- Auto-generated stats (paper/stats.tex) rebuilt from entries.jsonl, data
  cards, and corpus stats at build time; prose is human-written.
- PDF built by CI; versions tagged as GitHub Releases; DOIs per version via
  Zenodo integration; CITATION.cff in the repo root.
- Trajectory: repo v0.x drafts -> arXiv preprint -> venue snapshot
  (LREC / COLING resource track / AfricaNLP workshop).

## Continuous: Community
CONTRIBUTING.md, issue templates, repo topics, and a landing README pass;
@claude issue triage so contributors' issues get elaborated automatically;
public leaderboard and data cards as the community-facing surface.
