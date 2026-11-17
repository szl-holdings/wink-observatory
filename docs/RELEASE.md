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
  RUNNING, visibility public. An early check incorrectly used the
  Docker/Gradio-form host szlholdings-wink-observatory.hf.space and observed
  GET / and Python API HTTP 404. That proved only the Docker origin was
  unavailable, NOT that the static site was broken. The Space's own
  huggingface.co page names the real static origin:
  https://szlholdings-wink-observatory.static.hf.space. Direct independent
  HTTP checks verified GET / responds 302 -> /index.html, with /index.html
  HTTP 200 and /style.css HTTP 200. The static HTML served at its origin
  has host-added bytes and must NOT be presented as raw immutable Git
  blob parity. The static frontend is publicly reachable while the
  Python Docker backend is not deployed.
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

Read-only GitHub Actions metadata shows **no repository- or
hf-wink-production-environment-local HF_TOKEN secret**. An additional
organization-level metadata inspection on 2026-11-17 found that
**both HF_TOKEN and HF_ORG_TOKEN are already defined for szl-holdings with
visibility=all**. A repo-local absence therefore DOES NOT establish the
publisher lacks an inherited credential: the existing secrets.HF_TOKEN
expression may resolve to the organization-scoped secret. The secret value,
expiry, Hugging Face write permissions, selected issuer and functional upload
authority were NOT accessed or verified; do not claim this means deployability.
Prior source notes that called the credential missing are superseded.

An organization secret with visibility=all also creates a broad potential
blast radius across workflows. The safer reviewable route is a dedicated
least-privilege, write-scoped token admitted to the production environment
after owner review, with rotation/scope evidence, without breaking other
repos that currently consume the shared organization credential. Never copy
a token into source, logs or chat. Do NOT alter secret visibility, rotate
secrets, dispatch publication or treat inherited secret availability as
maintenance-window, environment-reviewer or billing authorization.

### HF publisher SDK preflight repair (source-only)

A fresh anonymous Python Hugging Face Hub `space_info` inspection on November
17, 2026 observed that `SZLHOLDINGS/wink-observatory` reports SDK `static`
through `huggingface_hub.SpaceCardData`. That object is mapping-like but
**is not a built-in dict**. The first source-owned Python HF publisher
incorrectly required `isinstance(card_data, dict)` and therefore would
always stop at `HF_SPACE_SDK_UNEXPECTED` on the actual provider return type,
even with a legitimate approved deployment window.

The repair uses only the observed `card_data.get("sdk")` protocol and accepts
the explicit provider values `static` and `docker`. Missing, malformed,
unrecognized or erroring card metadata continues to HOLD without a provider
write. The `python -I -B` launcher still runs in isolated mode, loading the
reviewed helper by its fixed sibling filesystem path (not PYTHONPATH or a
dynamic URL). Both authorized fake-provider tests and refusal cases run
entirely offline; no real token, Space write or GPU command is involved.

This removes a verified **future publication preflight code defect**, NOT
the unverified permissions/scope of the inherited organization-level
HF_TOKEN, environment reviewer approval, SDK migration window, stale
producer snapshot, or missing independent runtime witness. No upgrade is
represented as performed by this source-only repair.

### Exact HF Docker-bundle smoke qualification (prepublication only)

The python-fullstack.yml workflow now includes a separate container-smoke
job. It builds the exact dist/hf-space tree emitted by the existing sole
publisher: Python backend, public-only data mirror, ASGI entrypoint,
requirements, Dockerfile, source-owned HF card, and a SOURCE_REVISION
containing the CI head SHA. The job does NOT upload any HF files.

A nonroot container starts locally on the GitHub runner at 127.0.0.1:17860.
Bounded HTTP GETs must verify that / returns HTML and /healthz reports
SERVING. /api/v1/build-info must explicitly declare the source checkout SHA,
remain PUBLISHER_DECLARATION_ONLY, state
independent_runtime_verified=false and gpu_training_started=false,
and the container must run as uid 1000. The container is destroyed at job end.
No credentials, lab private data or GPU hardware are passed to the container.

A passing container smoke test establishes that the candidate can boot on
Linux as packaged. It is not an actual Hugging Face deployment, its source
declaration is not a signed runtime attestation, and it does not clear
production/environment owner or scientific admission HOLDs. A separate
HF canonical revision and live public HTTP witness is still mandatory.

### Provable complete static rollback source (before future SDK migration)

The original public WINK static Space at HF commit
01e1021e7e1d80a0d4754fa01ca84282cb854c85 contains **exactly four
reviewed tracked files**. A source-only independent readback on 2026-11-17
at 07:48 UTC verified the immutable provider tree, sizes, and raw bytes.
The entire public source snapshot (README, HTML, CSS and .gitattributes)
is retained locally on the owner computer under
C:\Users\steph\szl-cto\wink-public-rollback-20261117-raw, with
manifest.json. This does NOT constitute a provider rollback or
a production deployment.

| Historical file | Bytes | SHA-256 |
| --- | ---: | --- |
| .gitattributes | 1,519 | 11ad7efa24975ee4b0c3c3a38ed18737f0658a5f75a0a96787b576a78a023361 |
| README.md | 2,074 | ad920ec66340e578934e2c5aef3d534dcb5b4ba4c7bdbabb88f3889e523ea4f1 |
| index.html | 19,994 | 9f4f5350fc223d0bed88bd017ff35fecf44f3410c1c5e55e802928d70f6e4a52 |
| style.css | 388 | 789bfd541c9f06658ac410d968e9c39fa8c63a48a08643b36071b984c699a9f4 |

The canonical GitHub SOURCE COMMIT
190488e0c15e2c69cfe04681f23697e53b337b45 stores exactly the same
19,994-byte blob for frontend/index.html as HF index.html. A Windows
checkout may display 20,305 bytes because of CRLF translation; the
source of truth is the exact immutable Git blob, not the working tree.
This avoids false source-parity rejection from platform line endings.

New source-owned prepublication gate:
scripts/wink_rollback_snapshot.py confirms the expected current public
HF revision and static SDK, enumerates the full pinned tree and refuses
unexpected/missing files, checks each exact byte-length and SHA-256,
compares HF index bytes with the pinned GitHub main blob, and only then
stages the entire original static source plus JSON manifest.

The sole manual publisher uploads that public, SHA-bound rollback archive
to protected GitHub Actions artifacts **before any HF mutation**. The
artifact uploader explicitly includes hidden files so the public
.gitattributes file cannot be silently omitted. The publisher must fail
before any provider commit if this archive cannot be independently
materialized and uploaded. The archive is source evidence: it does NOT
grant a valid owner maintenance window, authorize bills or training,
automatically restore the old Space, or independently verify a running
Python application. A rollback itself must still be a separate
operator-authorized, exact-revision action.

Once an HF Space switches to Docker, its file tree is no longer this
static four-file baseline. The static rollback gate is intentionally
one-time for the first SDK conversion; future Docker-to-Docker updates
need a separately reviewed rollback contract rather than bypassing this
strict static source identity.

## November 17: WebGL browser-boot defect discovered and repaired in source

A public HTTP 200 for the canonical static origin did **not** prove the
Three.js application executed. A fresh, independent headless Chromium 156
inspection on BETTERWITHAGE loaded the current deployed
https://szlholdings-wink-observatory.static.hf.space/index.html and observed:

- HTTP status 200 and a canvas element, with WebGL context available.
- Feed badge stuck at BOOT; timestamp stuck at "starting...".
- Protocol and receipt panels stuck at "loading...".
- No 3D state, no live source application rendering and no source validation.
- The immutable Hugging Face index.html file at
  01e1021e7e1d80a0d4754fa01ca84282cb854c85 matches the old 19,994-byte
  GitHub frontend/index.html blob exactly but **ends with an incomplete
  JavaScript expression "for ("**, with no closing module script, body or HTML
  document. A browser HTML parser cannot execute that unfinished module.

The earlier "public 3D frontend operational" phrasing was incorrect.
Transport: PUBLIC_STATIC_HTTP_200; client JavaScript: BOOT_INCOMPLETE;
scientific validity: HOLD. This is a real functional failure, not a missing
Docker backend. The Docker-form origin is a separate, correctly unlaunched
Python runtime and still returns 404.

### Source repair, bounded scientific data, and actual browser check

The repaired frontend/index.html now closes the module/document, enables
requestAnimationFrame rendering, camera navigation, responsive resize and
reduced-motion handling. A bounded, anonymous browser loader resolves the
public WINK HF dataset commit once, pins every JSON read to that exact
40-character immutable SHA, validates the published scientific status,
allows only expected schema/criteria, sanitizes all dataset-sourced HTML and
tooltips, and does not invent witness records or model quality.

A second independent Chromium instance loaded the **local GitHub candidate**
through localhost with full Three.js CDN/WebGL and the real pinned public
HF dataset. The resulting browser state was:

- GET repaired local HTML: 200; WebGL canvas created; 3D render loop running.
- Badge: STALE SNAPSHOT; dataset observed SHA prefix 1bbb219da73c;
  producer observation about 391 minutes old at that readback.
- Protocol showed NOT FROZEN and open operator questions.
- Receipt battery showed named A9/A10 low-power, uninformative and invalid
  acceptance findings. Part D: NOT STARTED; no created witnesses.
- JavaScript exceptions: none; reported HTTP errors: none; failed requests:
  none. Browser availability is an interactive source-candidate check,
  **not** an HF deployment or independent scientific validity.
- Offline Python/Node contracts also reject a truncated module. Stale public
  data is correctly labeled stale rather than promoted to LIVE.

### Separate static-only owner-reviewed release path

The new manual workflow publish-hf-static-repair.yml is strictly limited to
a one-time repair of the public static Space index.html. It shares the
wink-hf-single-writer concurrency group and owner-protected
hf-wink-production environment with the existing Docker publisher. It has
no push or schedule trigger, does not change README, CSS, Space SDK, hardware,
billing, app dependencies, GPU or lab data.

Its exact initial provider predecessor MUST be
01e1021e7e1d80a0d4754fa01ca84282cb854c85. The complete immutable
four-file static rollback is independently verified and archived BEFORE
an HF upload_file call. For that historical rollback it uses the exact
old GitHub frontend mirror at
190488e0c15e2c69cfe04681f23697e53b337b45. The GitHub checkout uses
fetch-depth 0 so this historical source blob really exists in CI; the
existing Docker publisher also receives this correction.

Only once the owner environment reviewer, maintenance window, static repair
scope, rollback and exact current-main/HF revision checks are satisfied,
the workflow may replace index.html with the **exact protected GitHub blob**.
The HF upload is guarded with parent_commit compare-and-swap and independently
read back by hash. The provider's current static SDK must remain unchanged.
A successful source upload is NOT a certified JavaScript browser render, nor
a release of the separate Python/Docker app.

**The static repair has NOT been dispatched or deployed by source changes
alone.** Nothing here grants a lab countersignature, biological model quality
claim, training license, GPU allocation, or science admission. Do not mark
the public 3D visualization functional until the owner-approved publisher
completes and a real browser verifies the new deployed HF revision.

### Reproducible real-browser check (operator/CI development host)

Independent client-side boot must be checked, not inferred from GET 200 or
a valid JavaScript parse. The source provides scripts/wink_browser_smoke.py,
a fixed-origin, manual-only Playwright/Chromium observer. The observer never
sends credentials or POSTs, changes provider state, consumes training GPU,
signs scientific records or contacts collaborators.

On a development machine with Python 3.12 and Playwright 1.64.0:

    python -m pip install playwright==1.64.0
    python -m playwright install chromium
    # In a separate shell from the repository root:
    python -m http.server 18760 --bind 127.0.0.1
    # In the repository root:
    python scripts/wink_browser_smoke.py --target local

A success means the real browser executed WebGL/Three.js, read a single pinned
public dataset revision, populated the A9/A10/protocol panels, and responded
to a navigation click with no uncaught JS exceptions. STALE SNAPSHOT can
still be a correct result; a hypothetical fresh HTTP fetch cannot rewrite
the producer's historical timestamp. Browser rendering does NOT clear
scientific admission or lab agreement requirements.

After owner-approved static-only publication, run:

    python scripts/wink_browser_smoke.py --target public

The current original deployed static revision must fail that client-boot
test because the incomplete old module remains at BOOT. A working local
candidate is not a deployed runtime. Publish only through the existing
protected and serialized, owner-reviewed static repair workflow. A public
browser verification is still independent of the publisher's returned SHA.

The manual static HTML-only publishing workflow also invokes that same
Playwright 1.64.0/Chromium client boot check AFTER committing the exact HF
source revision and verifying the provider's raw HTML bytes. It performs
bounded source propagation retries and fails the workflow with explicit
STATIC_BROWSER_BOOT_UNVERIFIED_AFTER_PROVIDER_COMMIT if the public deployed
HTML remains stuck at BOOT or cannot load/validate its public data. Failure
does not pretend to undo the provider write; the complete old static rollback
artifact is retained for a separately authorized recovery. A successful
browser boot still never qualifies the lab's scientific method or starts
the separate Python/Docker backend.

### Source-only real 3D graphics canary (after PR #10)

The HTML static source passed a developer-local Chromium smoke test, but
that alone did not preserve repeatable proof in CI. The source-owned
static-browser-canary.yml now exercises exactly the reviewed source in an
ephemeral Chromium 156+ browser as part of changes to the HTML or its
real-browser harness. It starts a localhost HTTP server bound to 127.0.0.1,
does not request or use Hugging Face credentials, and tears down the
server before job exit. Its browser dependency is pinned.

The browser harness now instruments the actual WebGL drawArrays/drawElements
(and instanced variants) BEFORE page modules execute, counts real GPU/CPU
driver draw calls, captures the actual canvas PNG, and checks that the
compressed scene is nontrivial, that further draw calls occur during
navigation, and that camera motion changes the canvas pixels. It also
requires the public dataset source to be at an immutable SHA and the
protocol and A9/A10 panels to be populated and explicitly UNINTERPRETABLE
where necessary. It still reports the historical producer clock as STALE.
A source canary success is strictly **not** a deployed HF browser witness,
and has no authority to unlock protected deployment or wet-lab training.

The GitHub Actions job produces a bounded JSON receipt (source only)
and explicitly notes no provider writes, no lab model training and no
independent scientific validation. This converts a previously one-off
developer browser check into an auditable, reproducible 3D graphics gate
without fabricating biology or confusing screenshots with measurements.

### Protected-main static 3D canary coverage

A browser canary restricted to HTML-only PR paths can pass when modified but
**cannot** be made a GitHub required status check: a docs-only or backend-only
PR would not trigger it, leaving the protected-main check pending forever.

The required-check admission upgrade therefore makes the read-only
static-browser-canary.yml run on **all** pull requests and protected-main
pushes, even when only documentation changes. This adds real Chromium
runtime minutes but ensures the source-level visual 3D failure cannot be
skipped by changing an adjacent file. The pinned 1.64.0 Playwright browser
test is additive to existing WINK source-contracts, Python service, public
readback and Docker bundle checks.

This requirement applies to GitHub source admission only. Passing source
Chromium must NEVER automatically approve the HF environment reviewer,
maintenance window, provider token, HF SDK migration, lab signatures,
labeled biological data or GPU training.
