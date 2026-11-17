# WINK scientific method and source boundaries (research proposal)

Status: **engineering source candidate; public HF runtime still static; no
laboratory instrument, signed scientific witness, or trained biological model**.
This document does not claim the proposed research method is novel or validated.
All proposed biological conclusions remain falsifiable hypotheses.

## Four different clocks and evidence domains

| Source | Actual content | What its HTTP 200 establishes | What it does NOT establish |
| --- | --- | --- | --- |
| Hugging Face WINK dataset | Public fleet report, draft protocol, held-out receipt, zero Part D records | Source revision and serialized bytes read at one pinned SHA | Timestamp freshness, a real microscopy feed, lab approval |
| EMBL-EBI ENA Portal API | Public sequencing-run, sample, study accessions for NCBI taxon 6239 | Bounded public archive catalog readback | New live assay readings, data rights or annotated video |
| Europe PMC REST | Current literature catalog metadata | Availability and IDs/titles of indexed articles | A new replication result or wet-lab discovery |
| SZL GPU bridge public GitHub receipts | Historical immutable public execution events and denial evidence | Versioned evidence/report claims in repository | A live GPU heartbeat or verified active training |

Implementations: backend/live_data.py, backend/ena_catalog.py,
backend/gpu_receipts.py and backend/live_sources.py. These planes NEVER share
implicit source authority. No secret is needed for any public catalog request.

### ENA accession sampling

Fixed read-only endpoint: ENA Portal API, result=read_run, tax_eq(6239),
format=json, limit=6. One request, no redirects, proxies, private metadata,
raw FASTQ, URLs controlled by users, or pagination beyond the six-record bound.
Run, study, sample, taxonomy, release date and platform are catalog metadata.
No citation of six returned rows as a complete representative cohort, and no
conversion of a public record into a training-license permission.

Official source: https://ena-docs.readthedocs.io/en/latest/retrieval/programmatic-access/taxon-based-search.html

## Independent A9/A10 falsifiability arithmetic

A rate threshold is auditable only if **at least one valid possible binary
outcome** can falsify it. backend/falsifiability.py reconstructs exact
finite-sample failure counts using integer enumeration. It does not infer
statistical power, population generalization or independent validation.

For 40 trials and an upper contamination bound <= 0.10, at least **5** events
are needed to fail. For 15 trials and an invented-ID bound <= 0.80, at least
**13** events are needed to fail, making that threshold permissive of many
failures. For a 20-item neutral 'accuracy' requirement of >=
base(0.05) - tolerance(0.10) = **-0.05**, no nonnegative accuracy can fail
the rule. Furthermore the actual source says the probe measures
*letter-format compliance*, not answer correctness: A10=UNINTERPRETABLE.

The neutral receipt omits a structured tolerance field: the arithmetic
permits the value 0.10 ONLY with the exact reviewed public rule literal.
An edited literal or unrecognized criterion returns UNAVAILABLE and HOLD.
Every result remains scientific-admission HOLD regardless of raw recorded
pass flags. Neither the test suite nor a dashboard makes the underlying
criterion adequate.

## Leakage-resistant cross-experiment partition rehearsal

training/cohort_splits.py groups records by the transitive connected
components of shared animal, plate, batch and session identifiers. Each
connected component is deterministically assigned to one fold from
a digest of a pinned dataset SHA-256 plus the component's sample IDs.
No component may cross train / validation / test. If the source data is
too correlated to produce all three folds, the method returns HOLD;
it **never** splits related animals or batches just to fill a quota.

It is an in-memory engineering rehearsal, with synthetic unit tests.
No real lab records have been ingested, reviewed or split. A stable
source-derived digest is NOT an authentication signature, and this
partition is not independent experimental replication.

## Leader methods to benchmark, not appropriate or copy blindly

- [Tierpsy Tracker](https://github.com/Tierpsy/tierpsy-tracker) — worm
  skeletons, tracking and interpretable phenotyping feature baselines.
- [SLEAP](https://docs.sleap.ai/) — multi-animal pose and active-learning
  annotation, including modern PyTorch training paths.
- [DeepLabCut](https://github.com/DeepLabCut/DeepLabCut) — animal keypoint
  estimation and documented markerless tracking baselines.
- [Worm-PostureNet (2026)](https://doi.org/10.1016/j.rineng.2026.110616)
  — end-to-end C. elegans landmark, tracking and behavioral profiling
  approach. Compare methods only after reviewing datasets, protocols
  and licensing, and without unsupported superiority claims.

**Proposed, unmeasured idea:** use governance/evidence constraints as part
of behavioral ML acceptance: a body-pose model's output is valid only if
its specimen-level split, negative controls, calibration, uncertainty and
method provenance are independently checkable. The algorithms named above
are established research; WINK has not reproduced or surpassed their
performance.

## Five separate gates for future GPU-backed research

1. **Rights and scope:** explicit owner/lab decision, dataset copyright
   and animal/video label permission. Non-public lab data stays in the lab's
   approved perimeter; public Hugging Face metadata cannot authorize transfer.
2. **Experiment contract:** exact source dataset revision, acquisition
   protocol, timestamps, animal/session identifiers, label ontology and
   drift of annotation guidelines. Missing is UNAVAILABLE, not empty.
3. **Experimental design:** connected-component group-disjoint holdout,
   negative controls that *could fail*, interpretation of neutral scoring,
   uncertainty/power and blinded replicates.
4. **Compute owner admission:** exact signed existing szl-gpu-bridge job
   spec, time/replica/budget cap, approved GPU node, no raw anonymous
   inference ports or ungoverned tunnels.
5. **Post-run evidence:** preserved training seed/environment, complete
   failure cases, explicit no-training outcomes, independent readback,
   model-card claim review and co-signatures before public promotion.

No GPU dispatch, model training, generated biological observations,
model-card publication, Space SDK migration or external actuation is
authorized by the presence of this document or source.
