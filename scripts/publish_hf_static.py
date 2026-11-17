#!/usr/bin/env python3
"""Revision-pinned, manually approved WINK static HTML repair — never Docker migration.

The only allowed effect is replacing index.html in the EXISTING public static
Space with exact GitHub protected-main bytes. No README, SDK, other files,
hardware, secrets, budgets or scientific records are modified.

This is a deliberately separate *scope* under the SAME serialized HF writer
concurrency group and the SAME protected owner-reviewed production environment
as the Docker publisher. It must not run automatically. The original static
source must first be preserved as a reviewed public rollback artifact.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import re
from runpy import run_path
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from huggingface_hub import HfApi

SPACE = "SZLHOLDINGS/wink-observatory"
SOURCE_REPO = "szl-holdings/wink-observatory"
# Every provider revision is owner-supplied, exact and independently read back.
SHA40 = re.compile(r"[a-f0-9]{40}\Z")
ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "frontend" / "index.html"
observed_sdk = run_path(str(Path(__file__).resolve().with_name("hf_sdk_card_gate.py")),
                        run_name="_wink_hf_card_gate")["observed_sdk"]
prior_git_blob = run_path(
    str(Path(__file__).resolve().with_name("wink_rollback_snapshot.py")),
    run_name="_wink_public_git_blob",
)["git_blob"]


class AdmissionHold(ValueError):
    pass


def require(valid: bool, reason: str) -> None:
    if not valid:
        raise AdmissionHold(reason)


def read_main_lease(expected: str) -> None:
    try:
        res = subprocess.run(["git", "ls-remote", "origin", "refs/heads/main"],
                             cwd=ROOT, capture_output=True, timeout=15, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        raise AdmissionHold("PROTECTED_MAIN_LEASE_UNAVAILABLE") from exc
    require(res.returncode == 0 and
            res.stdout.strip() == (expected + "\trefs/heads/main").encode("ascii"),
            "PROTECTED_MAIN_MOVED_OR_UNAVAILABLE")


def verify_previous_ancestor(previous: str, current: str) -> None:
    """The previous provider HTML must belong to protected Git history."""
    require(bool(SHA40.fullmatch(previous)) and bool(SHA40.fullmatch(current)),
            "STATIC_SOURCE_ANCESTRY_INVALID")
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", previous, current],
            cwd=ROOT, capture_output=True, timeout=15, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AdmissionHold("STATIC_SOURCE_HISTORY_UNAVAILABLE") from exc
    require(result.returncode == 0, "PREVIOUS_STATIC_SOURCE_NOT_PROTECTED_ANCESTOR")


def read_source_bytes(expected: str) -> bytes:
    require(isinstance(expected, str) and SHA40.fullmatch(expected) is not None,
            "SOURCE_SHA_UNAVAILABLE")
    require(FILE.is_file(), "FRONTEND_SOURCE_MISSING")
    worktree = FILE.read_bytes()
    try:
        source = subprocess.run(["git", "show", expected + ":frontend/index.html"],
                                cwd=ROOT, capture_output=True, check=False, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        raise AdmissionHold("GITHUB_BLOB_UNAVAILABLE") from exc
    require(source.returncode == 0, "GITHUB_BLOB_UNAVAILABLE")
    require(worktree == source.stdout and 25000 < len(worktree) < 120000,
            "WORKTREE_NOT_EXACT_REVIEWED_BLOB")
    require(worktree.rstrip().endswith(b"</html>") and
            worktree.count(b"</script>") == 2 and
            b"function refreshPublic()" in worktree and
            b"STALE SNAPSHOT" in worktree and
            b"SCIENCE QUALIFICATION HOLD" in worktree,
            "FRONTEND_BOOT_CONTRACT_UNAVAILABLE")
    return worktree


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AdmissionHold("PUBLIC_READBACK_REDIRECT_REFUSED")


def public_readback(sha: str) -> bytes:
    require(isinstance(sha, str) and SHA40.fullmatch(sha) is not None,
            "PROVIDER_SHA_UNAVAILABLE")
    url = f"https://huggingface.co/spaces/{SPACE}/raw/{sha}/index.html"
    req = Request(url, headers={"Accept": "text/plain",
                                "User-Agent": "SZL-WINK-Static-Public-Readback/1",
                                "Cache-Control": "no-cache"}, method="GET")
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=12) as r:
            require(r.geturl() == url and r.status == 200,
                    "PROVIDER_RAW_HTTP_IDENTITY_CHANGED")
            content = r.read(120001)
    except (HTTPError, URLError, OSError, TimeoutError) as exc:
        raise AdmissionHold("PROVIDER_RAW_READBACK_UNAVAILABLE") from exc
    require(15000 < len(content) <= 120000, "PROVIDER_RAW_BYTES_UNAVAILABLE")
    return content


def main() -> int:
    main_sha = os.environ.get("GITHUB_SHA", "")
    expected_main = os.environ.get("EXPECTED_MAIN_SHA", "")
    old_hf = os.environ.get("EXPECTED_HF_SHA", "")
    previous_source = os.environ.get("EXPECTED_DEPLOYED_SOURCE_SHA", "")
    require(isinstance(main_sha, str) and SHA40.fullmatch(main_sha) is not None and
            main_sha == expected_main, "SOURCE_SHA_NOT_EXACT_MAIN")
    require(isinstance(old_hf, str) and SHA40.fullmatch(old_hf) is not None,
            "EXACT_PUBLIC_HF_PREDECESSOR_REQUIRED")
    require(isinstance(previous_source, str) and
            SHA40.fullmatch(previous_source) is not None and previous_source != main_sha,
            "EXACT_PREVIOUS_GITHUB_SOURCE_REQUIRED")
    require(os.environ.get("APPROVED_WINDOW") == "true", "DEPLOYMENT_WINDOW_CLOSED")
    require(os.environ.get("STATIC_REPAIR_APPROVED") == "true",
            "STATIC_HTML_REPAIR_NOT_APPROVED")
    require(os.environ.get("ROLLBACK_READY") == "true", "ROLLBACK_ARTIFACT_NOT_APPROVED")
    token = os.environ.get("HF_TOKEN")
    require(bool(token), "PUBLISHER_CREDENTIAL_UNAVAILABLE")
    read_main_lease(main_sha)
    exact = read_source_bytes(main_sha)
    verify_previous_ancestor(previous_source, main_sha)
    predecessor_blob = prior_git_blob(previous_source)
    require(15000 < len(predecessor_blob) < 120000,
            "PREVIOUS_SOURCE_BYTES_INVALID")

    # Validate the exact immutable existing Space in the provider before effects.
    api = HfApi(token=token)
    original = api.space_info(SPACE)
    require(original.sha == old_hf and original.private is False,
            "HF_STATIC_SOURCE_MOVED_OR_PRIVATE")
    require(observed_sdk(original.card_data) == "static",
            "HF_SPACE_NOT_STATIC_OR_UNREVIEWED")
    # A human-reviewed backup must bind the *current* provider predecessor
    # to an actual ancestor of protected GitHub main, not an invented SHA.
    require(public_readback(old_hf) == predecessor_blob,
            "PUBLIC_HF_PREDECESSOR_NOT_EXACT_GITHUB_SOURCE")

    # The server enforces parent_commit as an optimistic concurrency lease.
    # A second GitHub lease is observed immediately before requesting the write.
    read_main_lease(main_sha)
    result = api.upload_file(
        path_or_fileobj=str(FILE), path_in_repo="index.html",
        repo_id=SPACE, repo_type="space", revision="main", parent_commit=old_hf,
        commit_message="fix(wink): restore source-verified 3D static HTML " + main_sha[:12],
    )
    new_hf = getattr(result, "oid", None)
    require(isinstance(new_hf, str) and SHA40.fullmatch(new_hf) is not None,
            "HF_COMMIT_UNATTESTED_AFTER_PROVIDER_WRITE")
    print(json.dumps({"state": "PROVIDER_COMMITTED_RUNTIME_UNVERIFIED",
                      "new_hf_revision": new_hf,
                      "old_hf_revision": old_hf, "main_sha": main_sha,
                      "static_html_only": True, "gpu_job_started": False,
                      "license_changed": False, "sdk_changed": False},
                     sort_keys=True))
    observed = api.space_info(SPACE)
    require(observed.sha == new_hf and observed_sdk(observed.card_data) == "static",
            "HF_PROVIDER_COMMIT_OR_SDK_READBACK_MISMATCH")
    served = public_readback(new_hf)
    require(served == exact, "HF_RAW_HTML_BYTES_NOT_EXACT_SOURCE")
    print(json.dumps({
        "state": "STATIC_HTML_SOURCE_BYTES_VERIFIED_RUNTIME_NOT_INDEPENDENTLY_PROVED",
        "old_hf_revision": old_hf, "new_hf_revision": new_hf,
        "source_main_sha": main_sha, "html_sha256": sha256(exact).hexdigest(),
        "hf_sdk": "static", "static_client_render_verified": False,
        "model_trained": False, "independent_science_verified": False,
        "environment_owner_authority_verified_by_script": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
