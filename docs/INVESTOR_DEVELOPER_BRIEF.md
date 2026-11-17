# WINK Observatory — investor and developer brief

**Source:** szl-holdings/wink-observatory
**Distribution target:** https://huggingface.co/spaces/SZLHOLDINGS/wink-observatory
**Evidence feed:** https://huggingface.co/datasets/SZLHOLDINGS/wink-observatory-data

## The proposition

Research organizations lose confidence when a beautiful dashboard quietly
promotes a fresh HTTP 200 or a recorded pass to a validated experiment.
WINK visualizes the **evidence gap** rather than suppressing it. Its Python
backend tracks immutable publication revisions, data-contract failures,
replayable records, evaluation trippability, and independent approval holds.
Its Python frontend explains those states to scientists, developers and
decision-makers through a live 3D observational metaphor and accessible views.

## Already implemented as a GitHub release candidate

- Gradio UI + Plotly 3D view, entirely authored in Python.
- FastAPI read-only OpenAPI interface with no-store and independent readiness.
- Revision-pinned public HF dataset: fleet metadata, protocol status, Part D
  witness state, benchmark and held-out receipts including A9/A10 problems.
- Bounded public Europe PMC literature metadata from C. elegans research.
- GitHub GPU bridge read-only public evidence adapter: source-bound attempts and
  historical effects, explicitly NOT live GPU process measurement.
- Strict checksum/chain validation and native GitHub Actions tests.
- Non-root Docker candidate and a manual, expected-revision HF publisher.

**Do not present the candidate as the presently deployed Python Space.**
The public Space was last observed RUNNING on static SDK. Docker admission,
an HF organization plan/SDK transition, owner-reviewed rollback and independent
public build readback are separate gates.

## What is not claimed

No deployed gene-editing capability, live microscope stream, clinical diagnosis,
AI biological-discovery model, trained wet-lab model, authenticated partner
countersignature, signed Part D record, paper acceptance, attributable revenue,
running GPU job, provider authorization, or independently verified release.

The visible public v5 receipt records open issues: untrippable/low-power
acceptance rules and an uninterpretable neutral-accuracy metric. The protocol
v1.1 instrument is draft, not frozen. Those states are preserved verbatim.

## Why the design may be defensible (hypotheses, not proven advantages)

1. A source-revision-pinned, receipt-aware observation graph where negative
   controls and unavailable-data states remain first-class.
2. One shared Python codebase for data adapters, API, UI, QA and release controls.
3. Reuse of SZL's existing **signed GPU-bridge queue** rather than adding
   an ungoverned supercomputer execution path.
4. An extensible path to consented assays, acquisition hardware and governed
   model evaluation once data rights, lab validation and owner gates exist.

No market-size estimate, cost savings, performance superiority, or commercial
pricing is asserted without a measured basis.

## Developer surfaces

    GET /healthz              # process reachability, not scientific readiness
    GET /readyz               # 503 if current provider data is unavailable/stale
    GET /api/v1/observatory   # named-source identities and provenance states
    GET /api/v1/research      # Europe PMC metadata, not lab experiments
    GET /api/v1/training      # explicit HOLD and required evidence
    GET /api/v1/compute       # only public bridge receipts, not direct host
    GET /api/v1/build-info    # declared revision, not independent runtime proof
    GET /docs                 # OpenAPI user/developer interface

No POST service accepts lab data, model training commands, authorization
claims or private material. Public observations are advisory, not a source
of action authority.

## Next evidence needed

- Lab-approved data-ingress and subject-consent/license agreement, plus source
  of fresh measurement and authoritative UTC timestamps.
- C. elegans behavior dataset with licensed labeled videos and animal-disjoint
  holdout; controls with statistical power; independently witnessed A9/A10.
- Authorized Massed Compute/Salad training budget and exact signed gpu-bridge
  job spec; no direct tunnels or unpinned HPC dispatch.
- Protected GitHub source review, HF SDK eligibility, deployment window,
  rollback path, exact Space boot and module-byte witness.
- Explicit partner attribution and contribution table before public coauthor
  or co-signed claims.

The platform prioritizes scientific credibility over decorative "green."
