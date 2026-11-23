---
license: apache-2.0
szl:
  source_repo: szl-holdings/wink-observatory
  proof_url: https://github.com/szl-holdings/wink-observatory
---
<!-- szl:header v1 -->
# WINK Observatory

**A 3D research evidence instrument for the proposed SZL Holdings and Vidal-Gadea Lab evaluation protocol (v1.1, not frozen).**

Open it: **[WINK Observatory Space](https://huggingface.co/spaces/SZLHOLDINGS/wink-observatory)** ·
**Release admission (Nov 17):** The [public static HF frontend](https://szlholdings-wink-observatory.static.hf.space/index.html) now has the complete source-verified 3D JavaScript at HF commit `41d90e0` (first owner-approved HTML-only release). However, its **real public browser still falls back to OFFLINE BASELINE**, because the live public dataset grew from 7 to 17 itemized fleet groups and introduced legitimate `not-found` states. The next GitHub candidate dynamically renders all admitted groups and displays true producer freshness; a local real Chromium check confirmed **17 itemized 3D nodes** and `STALE SNAPSHOT` (A9/A10 remain open). This second repair is **not public until a new separately owner-approved, source-bound static-only release**. The Python/Docker backend and live wet-lab model remain separate HOLDs.

Live data: **[wink-observatory-data](https://huggingface.co/datasets/SZLHOLDINGS/wink-observatory-data)** ·
Lab: **[Vidal-Gadea Lab](https://agvg75.github.io/lab/)**

## What it is

Three stations, rendered in WebGL from public repository snapshots (freshness is separate and may be STALE):

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
| Neutral-accuracy 0.05 figure | Parsed-option correctness conflates answer and formatting; low-score cause unknown, arms not established independent. Historical diagnosis superseded: [correction](docs/A10_SUPERSESSION_20261117.md) |
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

## Python full-stack candidate (November 17, 2026)

This repository now includes an all-Python Gradio + FastAPI serving candidate,
3D Plotly observability, revision-scoped Hugging Face public dataset readback,
a separate Europe PMC literature feed, evidence-preserving source fallbacks,
developer JSON GET routes, and explicit GPU/training HOLD gates.

**Deployment is not admitted.** The existing public Hugging Face Space remains a
static-SDK runtime until an owner-controlled, reviewer-authorized publication
converts it. A RUNNING page, literature metadata, or provider-reported fleet
count must not be described as live Vidal-Gadea Lab instrumentation.

The WINK v1.1 protocol is draft and not frozen. Public Part D records are empty;
the A9/A10 science findings are open. No mutual countersignature, wet-lab
instrument feed, biological training, independent runtime verification, GPU
allocation, or lab-data transfer is asserted here.

### Python developer quickstart

    python -m pip install -r requirements.txt
    python -m unittest discover -s tests -p 'test_python_observatory.py' -v
    python backend/validate.py
    python -m training.readiness   # exits 3 while scientific training is HOLD
    uvicorn app:app --host 127.0.0.1 --port 7860

Read-only HTTP API: /healthz, /readyz, /api/v1/observatory,
/api/v1/research, /api/v1/training, /api/v1/compute, /api/v1/build-info, /docs.

The existing [szl-gpu-bridge](https://github.com/szl-holdings/szl-gpu-bridge)
owns the signed and reviewed GPU queue. WINK will not become a second dispatcher.
The current public dataset contains receipts, not licensed/labeled worm videos.
Biological training requires lab authorization, an animal-disjoint holdout,
reviewed acceptance criteria, signer pins and a bounded GPU budget.

See [release and rollback](docs/RELEASE.md) and
[the Python container manifest](deploy/hf/README.md). Source-revision alignment,
deployment, owner approval and independent scientific evidence stay separate.

## Public sequencing science and reproducible acceptance arithmetic (source candidate)

The Python research platform now includes the fixed-taxonomy **EMBL-EBI ENA
public sequencing accession catalog**. It samples at most six `C. elegans`
run/study/sample metadata rows (NCBI taxon 6239); it neither downloads FASTQ
files nor claims a current laboratory assay. `GET /api/v1/sequence-catalog`
returns HTTP 503 when the archive is unavailable, not an invented zero.

`GET /api/v1/acceptance-audit` evaluates the exact public v5 receipt's A9/A10
threshold arithmetic. Four recorded pass flags **do not** clear scientific
admission: one neutral threshold is mathematically impossible to trip and
its underlying metric is marked UNINTERPRETABLE. A bound of 0.80 on invented
identifiers requires 13/15 errors to fail. No performance conclusion is claimed.

`training/cohort_splits.py` rehearses group-disjoint holdout partitions with
animal/plate/batch/session connectivity and pinned dataset hashes. It does not
read laboratory records or start training. See
[scientific methods and leader baselines](docs/SCIENTIFIC_METHOD.md) for
references, limitations and release gates.

**Release state:** Python source and tests in GitHub do not imply the
public Hugging Face Space has migrated away from its existing static SDK.
