#!/usr/bin/env python3
"""Capture the complete, *public* old WINK static Space before SDK conversion.

No provider writes, credentials, GPU calls or laboratory data. The expected
HF revision is checked against current repo metadata; the entire pinned
tree is enumerated and compared to a strict reviewed allowlist so a missing
file cannot silently become a purported rollback. Index.html is compared
to the exact protected Git *blob* (not CRLF-translated Windows worktree).

Producing this archive proves backup-byte completeness only. It NEVER grants
maintenance-window, owner approval, deploy or independent science authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import pathlib
import re
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

SPACE = "SZLHOLDINGS/wink-observatory"
SOURCE = "szl-holdings/wink-observatory"
SHA40 = re.compile(r"[a-f0-9]{40}\Z")
FILES = (".gitattributes", "README.md", "index.html", "style.css")
MAX_BYTES = 131072
MAX_TOTAL = 262144


class SnapshotUnavailable(ValueError):
    """Incomplete or unexpected public source: stop before any upload."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SnapshotUnavailable("REDIRECT_REFUSED")


def require(test: bool, reason: str) -> None:
    if not test:
        raise SnapshotUnavailable(reason)


def parse_json(raw: bytes):
    def pairs(items):
        val = {}
        for key, value in items:
            require(key not in val, "DUPLICATE_JSON_KEY")
            val[key] = value
        return val

    def nonfinite(_):
        raise SnapshotUnavailable("NONFINITE_JSON")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=nonfinite)
    except SnapshotUnavailable:
        # Keep the exact fail-closed rejection class for audit evidence.
        raise
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SnapshotUnavailable("UNREADABLE_PUBLIC_METADATA") from exc


def fetch(url: str) -> bytes:
    # Supplied URLs are created only from reviewed constant hosts and exact SHA.
    require(url.startswith("https://huggingface.co/"), "SOURCE_HOST_NOT_APPROVED")
    opener = build_opener(ProxyHandler({}), NoRedirect())
    req = Request(url, headers={"Accept": "application/json, text/plain",
                                "Cache-Control": "no-store",
                                "User-Agent": "SZL-WINK-Rollback-Readback/1"},
                  method="GET")
    try:
        with opener.open(req, timeout=12) as response:
            require(response.geturl() == url and response.status == 200,
                    "PUBLIC_HF_FETCH_NOT_EXACT")
            data = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SnapshotUnavailable("PUBLIC_HF_FETCH_UNAVAILABLE") from exc
    require(bool(data) and len(data) <= MAX_BYTES, "PUBLIC_HF_FILE_BUDGET")
    return data


def git_blob(source_sha: str) -> bytes:
    require(SHA40.fullmatch(source_sha) is not None, "SOURCE_SHA_INVALID")
    try:
        result = subprocess.run(
            ["git", "show", f"{source_sha}:frontend/index.html"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False, timeout=12,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise SnapshotUnavailable("PROTECTED_SOURCE_BLOB_UNAVAILABLE") from exc
    require(result.returncode == 0 and 0 < len(result.stdout) <= MAX_BYTES,
            "PROTECTED_SOURCE_BLOB_UNAVAILABLE")
    return result.stdout


def capture(hf_sha: str, source_sha: str, *, read=fetch, mirror=git_blob) -> tuple[dict, dict[str, bytes]]:
    require(isinstance(hf_sha, str) and SHA40.fullmatch(hf_sha) is not None,
            "HF_EXPECTED_SHA_INVALID")
    require(isinstance(source_sha, str) and SHA40.fullmatch(source_sha) is not None,
            "GITHUB_EXPECTED_SHA_INVALID")

    base = "https://huggingface.co"
    info = parse_json(read(base + "/api/spaces/" + SPACE))
    require(isinstance(info, dict) and info.get("id") == SPACE
            and info.get("private") is False and info.get("sha") == hf_sha,
            "PUBLIC_HF_REVISION_MOVED_OR_PRIVATE")
    card = info.get("cardData")
    require(isinstance(card, dict) and card.get("sdk") == "static",
            "ROLLBACK_STATIC_SDK_IDENTITY_MISMATCH")

    rows = parse_json(read(base + "/api/spaces/" + SPACE + "/tree/" +
                           hf_sha + "?recursive=true"))
    require(isinstance(rows, list), "PUBLIC_HF_TREE_UNAVAILABLE")
    names = set()
    sizes = {}
    for row in rows:
        require(isinstance(row, dict) and row.get("type") == "file",
                "PUBLIC_HF_TREE_UNEXPECTED_ENTRY")
        name, n = row.get("path"), row.get("size")
        require(isinstance(name, str) and name in FILES and name not in names,
                "PUBLIC_HF_TREE_UNREVIEWED_FILE")
        require(type(n) is int and 0 < n <= MAX_BYTES, "PUBLIC_HF_TREE_FILE_SIZE_INVALID")
        require(not row.get("lfs"), "PUBLIC_HF_TREE_LFS_NOT_REVIEWED")
        names.add(name)
        sizes[name] = n
    require(names == set(FILES), "PUBLIC_HF_TREE_INCOMPLETE_OR_UNREVIEWED")
    require(sum(sizes.values()) <= MAX_TOTAL, "ROLLBACK_TOTAL_SIZE_BUDGET")

    blobs = {}
    for name in FILES:
        url = f"{base}/spaces/{SPACE}/raw/{hf_sha}/{name}"
        raw = read(url)
        require(len(raw) == sizes[name], "HF_RAW_FILE_SIZE_MISMATCH:" + name)
        blobs[name] = raw
    source_bytes = mirror(source_sha)
    require(blobs["index.html"] == source_bytes, "GITHUB_STATIC_MIRROR_NOT_BYTE_PARITY")
    digest = sha256(source_bytes).hexdigest()
    manifest = {
        "schema": "wink.public-static-rollback-readback/v1",
        "state": "COMPLETE_PUBLIC_STATIC_BYTES_NOT_DEPLOYMENT_AUTHORITY",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "hf_repo": SPACE,
        "hf_expected_revision": hf_sha,
        "source_repo": SOURCE,
        "source_main_revision": source_sha,
        "hf_sdk": "static",
        "complete_hf_tree": True,
        "public_repo_only": True,
        "raw_source_count": len(blobs),
        "sha256": {name: sha256(blobs[name]).hexdigest() for name in FILES},
        "sizes": sizes,
        "github_mirror_index_sha256": digest,
        "github_index_hf_byte_parity": True,
        "source_signed": False,
        "rollback_executed": False,
        "owner_authority_verified": False,
        "provider_writes": False,
        "training_started": False,
        "independent_runtime_verified": False,
    }
    return manifest, blobs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--hf-sha", required=True)
    parser.add_argument("--out-dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    manifest, blobs = capture(args.hf_sha, args.source_sha)
    dest = args.out_dir
    require(not dest.exists(), "ROLLBACK_DESTINATION_MUST_BE_NEW")
    dest.mkdir(parents=True, exist_ok=False)
    for name in FILES:
        (dest / name).write_bytes(blobs[name])
    (dest / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        newline="\n",
    )
    # Emit only public identities and content digests, not uncontrolled HTML.
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
