#!/usr/bin/env python3
"""Verify a retained four-file archive and prepare an index-only rollback plan.

Read-only: no credentials, provider writes, SDK change or authority inference.
An operator must review this plan and use the protected release environment.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from scripts.wink_rollback_snapshot import (
    FILES, MAX_BYTES, MAX_TOTAL, SHA40, SOURCE, SPACE, fetch, parse_json, require,
)


def bounded_file(path: Path) -> bytes:
    require(not path.is_symlink() and path.is_file(), "ARCHIVE_FILE_NOT_REGULAR")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(0 < len(raw) <= MAX_BYTES, "ARCHIVE_FILE_BUDGET")
    return raw


def plan(directory: Path, manifest_sha256: str, expected_current: str, *, read=fetch) -> dict:
    require(SHA40.fullmatch(expected_current) is not None, "CURRENT_REVISION_INVALID")
    require(not directory.is_symlink() and directory.is_dir(), "ARCHIVE_DIRECTORY_INVALID")
    require({p.name for p in directory.iterdir()} == set(FILES) | {"manifest.json"},
            "ARCHIVE_TREE_NOT_EXACT")
    raw = bounded_file(directory / "manifest.json")
    require(sha256(raw).hexdigest() == manifest_sha256, "ARCHIVE_MANIFEST_DIGEST_MISMATCH")
    manifest = parse_json(raw)
    require(isinstance(manifest, dict) and
            manifest.get("schema") == "wink.public-static-rollback-readback/v1" and
            manifest.get("hf_repo") == SPACE and manifest.get("source_repo") == SOURCE and
            manifest.get("hf_sdk") == "static" and manifest.get("complete_hf_tree") is True and
            manifest.get("public_repo_only") is True, "ARCHIVE_IDENTITY_INVALID")
    old = manifest.get("hf_expected_revision")
    require(isinstance(old, str) and SHA40.fullmatch(old) is not None, "ARCHIVE_REVISION_INVALID")
    require(old != expected_current, "ROLLBACK_ALREADY_AT_ARCHIVE_REVISION")
    hashes, sizes = manifest.get("sha256"), manifest.get("sizes")
    require(isinstance(hashes, dict) and set(hashes) == set(FILES) and
            isinstance(sizes, dict) and set(sizes) == set(FILES), "ARCHIVE_MANIFEST_FILES_INVALID")
    blobs = {name: bounded_file(directory / name) for name in FILES}
    require(sum(map(len, blobs.values())) <= MAX_TOTAL, "ARCHIVE_TOTAL_BUDGET")
    for name, blob in blobs.items():
        require(type(sizes[name]) is int and len(blob) == sizes[name] and
                sha256(blob).hexdigest() == hashes[name], "ARCHIVE_BYTES_MISMATCH:" + name)
        require(blob == read(f"https://huggingface.co/spaces/{SPACE}/raw/{old}/{name}"),
                "IMMUTABLE_ARCHIVE_READBACK_MISMATCH:" + name)
    info = parse_json(read(f"https://huggingface.co/api/spaces/{SPACE}"))
    require(isinstance(info, dict) and info.get("id") == SPACE and info.get("private") is False
            and info.get("sha") == expected_current and
            isinstance(info.get("cardData"), dict) and info["cardData"].get("sdk") == "static",
            "CURRENT_SPACE_MOVED_PRIVATE_OR_NONSTATIC")
    tree = parse_json(read(f"https://huggingface.co/api/spaces/{SPACE}/tree/{expected_current}?recursive=true"))
    require(isinstance(tree, list) and len(tree) == len(FILES) and
            all(isinstance(row, dict) and row.get("type") == "file" and not row.get("lfs")
                for row in tree) and {row.get("path") for row in tree} == set(FILES),
            "CURRENT_SPACE_TREE_CHANGED")
    for name in FILES:
        if name != "index.html":
            require(read(f"https://huggingface.co/spaces/{SPACE}/raw/{expected_current}/{name}") == blobs[name],
                    "NON_HTML_FILE_CHANGED:" + name)
    return {
        "schema": "wink.static-rollback-plan/v1", "state": "REVIEW_REQUIRED_NOT_EXECUTED",
        "repo_id": SPACE, "repo_type": "space", "revision": "main",
        "parent_commit": expected_current, "archive_revision": old,
        "path_in_repo": "index.html", "restore_sha256": hashes["index.html"],
        "manifest_sha256": manifest_sha256, "provider_writes": False,
        "owner_approval_verified": False, "live_restore_tested": False,
        "limitations": ["Recheck provider identity immediately before effect; enforce parent_commit at upload",
                        "Protected environment and explicit owner approval remain required",
                        "After write verify all four immutable files and independent public runtime"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--expected-current", required=True)
    args = parser.parse_args()
    print(json.dumps(plan(args.archive, args.manifest_sha256, args.expected_current), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
