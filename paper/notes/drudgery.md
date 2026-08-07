# Field notes for the Challenges section (raw; prose later)

Braindump ledger. Add dated entries as things happen; harvest into
paper Section "Challenges of Low-Resource Ingestion".

## 2026-08 - Getting to the first green run (the failure ladder)
- Run 1: OIDC token permission missing (id-token: write). Lesson: agent
  actions have auth requirements beyond classic workflow permissions.
- Run 2: GitHub App not installed on the org; app vs API key are two
  separate credential systems (GitHub operations vs model access). Install
  flow confusingly detours through vendor account-linking pages.
- Run 3: turn-limit exceeded; ceiling was calibrated for nightly increments,
  not a 30-day backfill. Lesson: bound the WORK (item caps) not just the
  agent (turn caps); make limits dispatch inputs, keep tight cron defaults.
- Run 3.5: input plumbing half-applied (expression referenced an input that
  was never declared); silent fallback to default masked it.
- Run 4: green. Pattern adopted everywhere after: incremental batching,
  commit-as-you-go, PR opened after first batch, graceful degradation notes.

## 2026-08 - Robot-found bugs (evidence that LLM triage pays)
- Literature PR: agent independently diagnosed the arXiv version-suffix
  dedup mismatch (seen.json stored ...v1; fixed fetcher emits bare IDs) and
  wrote a reviewer note proposing normalisation. Bug root cause: raw-string
  vs escaped-string regex confusion introduced via a shell-generation layer.
- Corpus PR #4 (F1-F7): inspected committed data, not just stats;
  reproduced HF 429 from the runner; identified silent-failure +
  unconditional-overwrite + gate-logic interaction that could wipe the
  catalog; refused to commit an empty catalog; declined to patch pipeline
  code as out-of-lane. Findings became fixes + policy same week.

## 2026-08 - Rate limits and shared infrastructure
- Wikimedia 429 on first corpus run: CI runners share egress IPs; politeness
  (pacing + Retry-After backoff) is mandatory, not optional. Same later for
  HF API. OpenAlex mailto polite-pool as the cooperative model.

## 2026-08 - Licensing triage per source class (the minefield)
- Wikipedia: CC BY-SA, full text storable with per-doc URL attribution.
- News: copyrighted; public repo stores URL manifests only (OSCAR/C4-style
  rebuildability). Later dropped headline text from manifests too
  (privacy + skew).
- HF datasets: catalog metadata only; data stays on the Hub under its own
  license; UNKNOWN licenses flagged "verify before use".
- Religious parallel text: deferred entirely pending per-text verification;
  JW300 withdrawal as the cautionary precedent.
- GitHub repos (planned): huge share have NO license file = all rights
  reserved; catalog-only with per-repo human verification.

## 2026-08 - Igbo Wikipedia quality (what "raw" really contains)
- Alphabetical backfill skew: first batches dominated by numeric/date stubs
  and election lists; corpus quality improves as cursor advances. Reviewer
  impressions of early batches are not representative.
- Observed: markup leakage (data-mw, unexpanded Templeeti:), MT-suspect
  orthography (non-Igbo open vowels), archaic Union-Igbo register in
  Bible-derived prose, diacritic-poor informal text.
- Policy adopted: filter markup damage and stubs at fetch; tag (never
  delete) archaic_register and mt_suspect_orthography; flag-aware filtering
  deferred to derivation time. Rationale: raw is staging, derivation is
  where destiny is decided; tags preserve linguistic value (archaic
  register is data, not dirt).

## 2026-08 - Human-review economics
- Asymmetry principle: false keeps are cheap (visible, prunable at review);
  false discards were invisible and irreversible until the discard audit
  trail was added to PR bodies. Design so the cheap error is the likely one.
- Merge boundary as the single control point; everything else automated.
- Morning review cost so far: minutes/day. Track this; it is the number
  that decides how much automation a solo researcher can govern.

## To capture next
- First unattended cron run behaviour; discard-list quality post-loosening.
- Sunday corpus run with F1 fix + flags: flag rates, card quality.
- Actual monthly spend vs the estimate.
