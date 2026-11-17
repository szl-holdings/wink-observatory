# WINK release admission and rollback — HOLD until independently verified

## Immutable identity map

- GitHub canonical source: szl-holdings/wink-observatory protected main SHA.
- HF destination: SZLHOLDINGS/wink-observatory, last observed public revision
  01e1021e7e1d80a0d4754fa01ca84282cb854c85 (as of 2026-11-17 04:58 UTC).
- Current HF SDK: static. Proposed target: Docker + FastAPI/Gradio Python,
  port 7860. This SDK migration is a provider cost/capability decision.
- Public data source: SZLHOLDINGS/wink-observatory-data, exact revision sampled
  independently on each request; file readback uses pinned git revision.
- GPU authority: szl-holdings/szl-gpu-bridge existing signed queue (not WINK).
- Lab evidence: WINK v1.1 draft, Part D witnesses not started, A9/A10 open.

## Owner-controlled deployment preconditions

1. Confirm HF organization permits Docker SDK and its compute charges; no implicit
   paid hardware change or automatic training is allowed.
2. Review the true existing static HF Space, preserve its immutable revision,
   repository sources, README/index.html/style.css and rollback controls. The
   new publisher **adds/replaces files without deleting old source files**.
3. Merge this reviewed Python change under normal GitHub protections, run native
   exact-main Python CI and data validation, and verify owner/release authorization.
4. Configure a dedicated fine-grained HF_TOKEN in GitHub Actions (value never
   logged), plus protection and required reviewers on the hf-wink-production
   GitHub environment. The environment name itself is not a review.
5. Manually dispatch the sole publisher against exact protected main with:
   expected_main_sha, expected_hf_sha, open_deploy_window=true,
   sdk_migration_approved=true, and rollback_ready=true. It must stop on any
   identity movement, missing approval, unavailable state or closed window.
6. Read back the new HF git revision and SDK, then validate actual public GET /
   (200), /healthz (200), /readyz (200 only on current public data), /api/v1/observatory
   (200 with dataset SHA) and /api/v1/build-info. If any fail, HOLD the release
   and restore the pinned prior Space revision through the owner publisher.
7. Independently repeat the source/module hash parity and source/Space/boot
   identity verification; source files, HTTP reachability and runtime authority
   are three different evidence states. A signed dataset/lab receipt is another.

## Go/no-go contract

Process reachability != source parity != evidence validity != owner authority
!= deployed revision != independent runtime witness. Missing any required field
gives HOLD, not green. Never merge or publish merely because PR-head CI passed.
Training is separately denied until it has rights, labels, animal/session-disjoint
split, reviewed A9/A10 criteria, signed job and explicitly bounded GPU budget.

### Known current holds

- Direct wet-lab instrument acquisition: NOT CONNECTED.
- Independent co-signatures / A3 observer / protocol freeze: NOT VERIFIED.
- Part D records: 0; no genesis record should be fabricated.
- C. elegans locomotion video/labels: NOT PROVIDED.
- Signed HPC compute/owner budget in this WINK route: NOT ADMITTED.
- HF static-to-Docker eligibility: NOT VERIFIED.
- Production source-HF runtime parity: NOT VERIFIED.

Avoid inventing performance metrics for investors. Do not use patient records,
unlicensed scientific datasets, or confidential lab footage in public Spaces.

## November 17 source/Space admission hardening

**Direct bounded readback, 2026-11-17 06:34 UTC (not a deployed-Python claim):**

- GitHub source main: bd9742da5d73a9c9f71f3d88e848b8cdbdc0fac8.
- Public HF Space SZLHOLDINGS/wink-observatory repo revision:
  01e1021e7e1d80a0d4754fa01ca84282cb854c85; SDK static, provider stage
  RUNNING, visibility public. The public Space origin returned GET / HTTP 404;
  /index.html, /readyz, /api/v1/observatory and /api/v1/acceptance-audit also
  returned HTTP 404. The source repository file at the immutable Hugging Face
  resolve/main/index.html separately returned HTTP 200. A repository HTML
  file is NOT proof of an operational frontend.
- The Python application is in GitHub main, NOT in the static HF runtime.
  No main-to-HF module byte parity or independent runtime proof exists.
- Fleet-data producer's last observed UTC snapshot is 2026-11-17 03:15 and
  is STALE. Reading its dataset with HTTP 200 does not refresh the producer.

**Actual GitHub governance gates, read back after modifications:**

- Main is protected with enforced required checks: gate, source-contracts,
  python-service, and public-source-readback. Strict base freshness, checks
  applied to administrators, zero peer-review approval minimum for the
  authorized solo build, no force-push, no branch deletion, and linear
  history. The zero peer-review count does NOT waive the required checks.
- Environment hf-wink-production exists and restricts deployments to
  protected branches; one named owner reviewer must approve deployments.
  This is separate from the pull-request review-count setting. It is NOT
  automatic approval to modify the provider.
- No HF billing, compute allocation or SDK migration was performed. Official
  HF Hub documentation currently says Gradio and Docker compute Spaces
  require a paid plan (Team/Enterprise for organizations). CPU Basic has zero
  hourly cost but provider plan eligibility is a separate owner gate.
  Confirm both eligibility and billing before any deployment.

### Read-only release admission instrument

scripts/wink_release_probe.py issues only bounded anonymous GETs to the
GitHub main ref, public HF Space metadata and six exact public Space routes.
It preserves separate states for HTTP transport, deployed revision, source
declaration, SDK, telemetry freshness, evidence, owner authority and scientific
validity. Unknown and HTTP 404 are HOLD, not successful deployments.

Local observation:

    python scripts/wink_release_probe.py --output wink-readback.json

release-readback.yml retains the JSON report, scheduled and on main changes,
without provider mutation or e-mail. A green *observation workflow* certifies
only successful observation, NEVER a successful release. In contrast,
publish-hf-python.yml will run the --strict-transport check AFTER authorized
publication and refuse to claim serving Python routes until actual HTTP and
current-main source declaration align.

Strict HTTP transport deliberately does NOT require scientific telemetry to
be fresh: an operational visualization must be allowed to report STALE
honestly. Release_admission is held until independent module byte comparison,
runtime boot witness, and owner and scientific evidence all qualify.

Source SHA, HF repo revision, raw HTML existence, app HTTP GET, telemetry age,
owner authority, signed evidence, GPU execution and scientific validity are
different observables; never substitute a PR-head green check for any of them.

### Current owner credential / provider plan readback (2026-11-17)

The authenticated Hugging Face connection reports SZLHOLDINGS as a **Team**
organization with administrator membership. This satisfies the broad
organization-plan classification for Docker compute Spaces; it does **not**
authorize an SDK migration, compute allocation, subscription change, or a
specific deployment window. Do not advertise a released Python HF runtime.

A read-only GitHub Actions secret-*name* inventory found **no HF_TOKEN
configured** at the repository level or in the protected
hf-wink-production environment. No credential value was read, copied,
logged, rotated or supplied. The existing manual source-owned publisher
will stop at HF_TOKEN_NOT_CONFIGURED until the owner provisions an
appropriately scoped credential through an approved GitHub environment
secret channel. Never paste a token into a chat or commit it to GitHub.
The repository environment reviewer must separately approve deployment;
a registered secret is never itself permission to deploy.
