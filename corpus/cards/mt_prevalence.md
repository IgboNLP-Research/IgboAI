### MT prevalence (measured 2026-08-29)

A stratified sample of 100 documents was drawn across the four
English-residue buckets of `scripts/mt_prevalence_probe.py` and annotated
by one Igbo-speaking annotator (mt / human / unclear). Labels are in
`mt_probe_annotated.tsv`.

**60 of 100 documents were judged machine-translated**; 22 human-authored,
18 unclear.

Neither existing signal detects this (n=82, excluding unclear):

| signal | result |
| --- | --- |
| English function-word ratio (probe buckets) | per-bucket precision 76 / 56 / 52 / 56% from `clean` to `heavy`; non-monotonic, `clean` highest. Does not track MT. |
| `mt_suspect_orthography` | fired on 1 of 82 documents. Recall 1.67% (1 of 60), precision 100% on n=1. |
| `archaic_register` | fired zero times; untestable on this sample. |

Any filtering that relies on `mt_suspect_orthography` currently passes
~98% of machine-translated content unflagged.

Limitations: single annotator, no inter-annotator agreement statistic, and
18% of the sample resisted classification, so the mt/human boundary is
itself uncertain. The 60% figure should be read as one annotator's
judgment on 100 documents, not a settled corpus statistic.