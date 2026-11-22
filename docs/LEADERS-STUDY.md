# Domain Leader Study — wink-observatory (live 3D instrument, receipts-native)

OUROBOROS phase-3, cohort-02 tranche-1, Kimi ruling W26-C2T1-KIMI-20261123-ASK (GO). PROPOSE-ONLY study card: documentation only, no implementation in this PR.

## Current state (repo inspection 2026-11-23)
Python repo; description: live 3D instrument for the SZL x Vidal-Gadea Lab evaluation protocol: witness records, receipts. Topics: live-telemetry, observatory, szl-estate, szl-holdings, threejs, vidal-gadea.

## Domain leaders studied
| Leader | What they have | Key sources |
| --- | --- | --- |
| uPlot (leeoniya) | The reference small fast time-series chart library with published benchmark methodology and machine-readable bench results (bench/results.json in-repo) — the leader answer for live telemetry strips that must stay smooth at high frequency | github.com/leeoniya/uPlot + bench results.json (accessed 2026-11-23) |
| uPlot performance documentation | Documented perf envelope (2-pass canvas rendering, data-oriented memory layout) honored by published measurements, not claims | leeoniya/uPlot performance docs (accessed 2026-11-23) |

## What the leaders do better
- Performance claims ship as in-repo machine-readable benchmark artifacts — anyone can rerun the leader's numbers. That is the receipts-first culture the estate wants, applied to viz itself.
- A dedicated telemetry surface (the chart strip) is kept separate from the heavy 3D scene, so instrument smoothness does not compete with the 3D render loop for frame budget.
- Data-oriented layout means streaming updates touch less memory per frame — the leader version of live-data discipline.

## Gaps
- Witness-record/receipt surface exists (description-measured), but no documented frame-budget or chart-perf receipt was found for the instrument's own rendering: the observatory measures everything except its own smoothness.

## Ranked #1 absorb proposal (NOT implemented in this PR)
Adopt the leader's benchmark-receipt culture for the instrument itself: publish a machine-readable perf receipt (render ms + telemetry points/sec at fixed dataset size) per release, uPlot-style. Expected benefit: instrument quality becomes measured and comparable across releases; regressions visible before user complaints. Cost/risk: low; benchmark harness + receipt file, no runtime change. Validation: receipt generation in CI on a fixed synthetic telemetry stream. Rollback: harness removal only.

## Sources
- uPlot repo: https://github.com/leeoniya/uPlot (accessed 2026-11-23)
- uPlot bench results: https://github.com/leeoniya/uPlot/blob/master/bench/results.json (accessed 2026-11-23)
