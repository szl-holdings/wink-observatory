# Domain Leader Study — wink-observatory (live 3D instrument, receipts-native)

OUROBOROS phase-3, cohort-02 tranche-1, Kimi ruling W26-C2T1-KIMI-20261123-ASK (GO). PROPOSE-ONLY study card: documentation only, no implementation in this PR.

## Current state (repo inspection 2026-11-22)
Python repo; description: live 3D instrument for the SZL x Vidal-Gadea Lab evaluation protocol: witness records, receipts. Topics: live-telemetry, observatory, szl-estate, szl-holdings, threejs, vidal-gadea.

## Domain leaders studied
| Leader | What they have | Key sources |
| --- | --- | --- |
| uPlot (leeoniya) | The reference small fast time-series chart library with published benchmark methodology and machine-readable bench results (bench/results.json in-repo) — the leader answer for live telemetry strips that must stay smooth at high frequency | uPlot repo @ commit a8b48ee3a2ec53700194155fbfd8db71e0ca9fef (accessed 2026-11-22) |
| uPlot performance documentation | Published Canvas 2D benchmark results across browsers and data scales, shipped as an in-repo machine-readable artifact rather than marketing prose | uPlot bench/results.json @ commit a8b48ee3a2ec53700194155fbfd8db71e0ca9fef (accessed 2026-11-22) |

## What the leaders do better
- Performance claims ship as in-repo machine-readable benchmark artifacts pinned to a revision — anyone can rerun or audit the leader's numbers against exactly the code that produced them. That is the receipts-first culture the estate wants, applied to viz itself.
- A dedicated telemetry surface (the chart strip) is kept separate from the heavy 3D scene, so instrument smoothness does not compete with the 3D render loop for frame budget.
- Leader benchmark numbers are published per browser and data scale, so perf claims carry their measurement environment with them instead of posing as universal truths.

## Gaps
- Witness-record/receipt surface exists (description-measured), but no documented frame-budget or chart-perf receipt was found for the instrument's own rendering: the observatory measures everything except its own smoothness.

## Ranked #1 absorb proposal (NOT implemented in this PR)
Adopt the leader's benchmark-receipt culture for the instrument itself: publish a machine-readable perf receipt per release recording render ms and telemetry points/sec, plus the full measurement environment (browser + version, device/GPU profile, viewport, canvas size, fixed synthetic stream definition and dataset size), and pin the commit SHA the receipt was produced from. Comparisons are valid only within the same recorded environment; cross-environment numbers are labeled incomparable. Expected benefit: instrument quality becomes measured and comparable across releases; regressions visible before user complaints. Cost/risk: low; benchmark harness + receipt file, no runtime change. Validation: receipt generation in CI on a fixed synthetic telemetry stream in a pinned CI environment. Rollback: harness removal only.

## Sources (accessed 2026-11-22; pinned revision a8b48ee3a2ec53700194155fbfd8db71e0ca9fef, master HEAD at access time)
- uPlot repo @ pinned commit: https://github.com/leeoniya/uPlot/tree/a8b48ee3a2ec53700194155fbfd8db71e0ca9fef
- uPlot bench results @ pinned commit: https://github.com/leeoniya/uPlot/blob/a8b48ee3a2ec53700194155fbfd8db71e0ca9fef/bench/results.json
