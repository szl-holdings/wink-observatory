<!-- szl:header v1 -->
# WINK Observatory

**A live 3D instrument for the co-signed SZL Holdings × Vidal-Gadea Lab evaluation protocol (v1.1, not frozen).**

Open it: **[WINK Observatory Space](https://huggingface.co/spaces/SZLHOLDINGS/wink-observatory)** ·
Live data: **[wink-observatory-data](https://huggingface.co/datasets/SZLHOLDINGS/wink-observatory-data)** ·
Lab: **[Vidal-Gadea Lab](https://agvg75.github.io/lab/)**

## What it is

Three stations, rendered live in WebGL:

1. **The Worm** — estate fleet telemetry as a stylized *C. elegans* (the lab's
   model organism). Named groups are nodes on the ventral cord, colored by
   live status. Stylized, not anatomical.
2. **Witness Helix** — the protocol Part D witness-record series. Empty by
   design: the first observation falls at co-signature (D2), and the helix
   says so out loud.
3. **Receipt Battery** — the v5 held-out receipt displayed **with its own open
   audit findings**: two criteria unable to trip (A9), one low-power, one
   UNINTERPRETABLE (A10). A public instrument that renders its failed
   falsifiability audit is the point.

## Architecture

| Layer | Where | Role |
|---|---|---|
| Front-end | frontend/index.html → HF Space (static SDK) | Three.js 3D scene; live fetch, fail-closed CACHED fallback |
| Data feed | HF dataset SZLHOLDINGS/wink-observatory-data | Witness records, fleet snapshots, receipts, protocol status |
| Back-end | backend/ | Stdlib-only validators + SHA3-256 digest-chained witness append |
| Gate | .github/workflows/validate.yml | Schema + secret-shape gate on every push/PR (fail-closed) |

## Honest status

| Claim | Status |
|---|---|
| Space deployed | YES — static SDK, no server, no secrets client-side |
| Witness series (Part D) | NOT STARTED — first observation falls at signature per D2 |
| v5 held-out receipt | PUBLISHED WITH OPEN FINDINGS — A9 trippability audit open, A10 UNINTERPRETABLE |
| Neutral-accuracy 0.05 figure | Measures letter-format compliance, not correctness — see data/receipts/a10-diagnosis.json |
| Protocol freeze | NONE — no deposit, no DOI, no freeze date asserted |

## Roadmap (proposed, not launched)

- **WINK-Scribe** — small fine-tuned assistant that drafts Part D witness
  records in protocol format; evaluated with trippable criteria per A9 before
  any claim is made.
- **Behavior-analysis model** — vision model for C. elegans locomotion
  scoring, trained with the lab, published with the same receipt discipline.
- **Witness automation** — estate pipelines append digest-chained records
  weekly via backend/append_witness.py; the Observatory renders them live.

## Contribute / verify

Every figure shown is checkable against the dataset. Nothing is deleted;
records are append-only. If the feed is unreachable the Observatory says
CACHED instead of guessing.

## Use limits

A running Space is not evidence of a capability. No protocol freeze is
asserted by this repository. Fleet totals are provider-reported; only
operator-verified groups are itemized. Trust never 100%.

---
<sub>SZL Holdings · Vidal-Gadea Lab · honest by design · fail-closed · license MIT (align to estate Apache-2.0 at owner discretion)</sub>
