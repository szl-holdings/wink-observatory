"""Deterministic leakage-barrier rehearsal for future worm-behavior datasets.

No source data is read, modified or sent anywhere. The output is a zero-effect
engineering split proposal, NOT lab authorization or trainable science.
Merging shared animal, plate, batch and session identities into connected
components prevents any of those groups crossing train/validation/test.
Input order and hidden filesystem state cannot influence the partition.

Real biological records, labels and licenses are NOT present in this repo.
"""
from __future__ import annotations

import hashlib
import json
import re

SHA256 = re.compile(r"[a-f0-9]{64}\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}\Z")
FIELDS = ("animal_id", "plate_id", "batch_id", "session_id")
MAX_ROWS = 10000
DEFAULT_RANGES = ((7000, "train"), (8500, "validation"), (10000, "test"))


class CohortUnavailable(ValueError):
    """Invalid or incomplete split proof must not turn into training admission."""


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise CohortUnavailable(reason)


def propose(dataset_sha256: str, rows: list[dict]) -> dict:
    require(isinstance(dataset_sha256, str) and SHA256.fullmatch(dataset_sha256) is not None,
            "DATASET_CONTENT_IDENTITY_REQUIRED")
    require(type(rows) is list and 3 <= len(rows) <= MAX_ROWS, "COHORT_SIZE_UNSUPPORTED")
    samples = set()
    parsed = []
    for row in rows:
        require(type(row) is dict and set(row) == {"sample_id", *FIELDS},
                "COHORT_SCHEMA_INCOMPLETE")
        require(all(type(row[k]) is str and IDENTIFIER.fullmatch(row[k]) is not None
                    for k in ("sample_id", *FIELDS)), "COHORT_ID_INVALID")
        sid = row["sample_id"]
        require(sid not in samples, "DUPLICATE_SAMPLE_ID")
        samples.add(sid)
        parsed.append(row)
    parsed.sort(key=lambda r: r["sample_id"])
    n = len(parsed)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)

    # Closure is critical: two independent plates can still share one worm ID
    # or acquisition batch and therefore must be on the same side of the split.
    first_seen = {}
    for i, row in enumerate(parsed):
        for field in FIELDS:
            key = (field, row[field])
            if key in first_seen:
                union(i, first_seen[key])
            else:
                first_seen[key] = i
    components: dict[int, list[int]] = {}
    for i in range(n):
        components.setdefault(find(i), []).append(i)
    assignments = {}
    for component in components.values():
        members = tuple(parsed[i]["sample_id"] for i in component)
        ident = dataset_sha256 + "|" + "|".join(members)
        slot = int.from_bytes(hashlib.sha256(ident.encode()).digest()[:8], "big") % 10000
        split = next(name for upper, name in DEFAULT_RANGES if slot < upper)
        for i in component:
            assignments[parsed[i]["sample_id"]] = split

    # Defense in depth: a future changed union heuristic cannot silently
    # scatter the same animal/plate/batch/session across evaluation folds.
    scopes: dict[tuple[str, str], str] = {}
    for row in parsed:
        current = assignments[row["sample_id"]]
        for field in FIELDS:
            key = (field, row[field])
            require(key not in scopes or scopes[key] == current, "GROUP_LEAKAGE_DETECTED")
            scopes[key] = current

    sizes = {x: sum(1 for split in assignments.values() if split == x)
             for x in ("train", "validation", "test")}
    all_present = all(x > 0 for x in sizes.values())
    canonical = json.dumps(assignments, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema": "wink.cohort-split-rehearsal/v1",
        "state": "REHEARSAL_GROUP_DISJOINT" if all_present
                 else "HOLD_INSUFFICIENT_INDEPENDENT_COMPONENTS",
        "dataset_sha256": dataset_sha256,
        "records_observed_from_lab": False,
        "records": n,
        "independent_identity_components": len(components),
        "split_counts": sizes,
        "split_digest_sha3_256": hashlib.sha3_256(canonical).hexdigest(),
        "all_identity_groups_disjoint": True,
        "trainable": False,
        "license_verified": False,
        "partner_consent_verified": False,
        "heldout_model_quality_verified": False,
        "raw_ids_exported": False,
        "note": "Deterministic synthetic/owner-supplied identity preflight only; not an approved study split",
    }
