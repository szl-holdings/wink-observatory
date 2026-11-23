#!/usr/bin/env python3
"""WINK Observatory schema gate. Stdlib only. Fail-closed.

Exit 0 = all data files valid. Any violation exits 1 with a reason.
Runs on every push and PR (.github/workflows/validate.yml).
"""
import hashlib
import json
import math
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parents[1] / "data"
STATUSES = {"running", "parked", "complete", "degraded", "stopped", "not-found"}
SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)salad[-_]?api[-_]?key"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_.\-]{20,}"),
    re.compile(r"(?i)private[_-]?key"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def fail(msg):
    print("FAIL:", msg)
    sys.exit(1)



def _unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _reject_nonfinite(_value):
    raise ValueError("NONFINITE_JSON_NUMBER")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("NONFINITE_JSON_NUMBER")
    return number


def load(name):
    path = BASE / name
    if not path.exists():
        fail("missing " + name)
    raw = path.read_text(encoding="utf-8")
    for pat in SECRET_PATTERNS:
        if pat.search(raw):
            fail("secret-shaped content in " + name)
    try:
        return json.loads(raw, object_pairs_hook=_unique_pairs,
                          parse_constant=_reject_nonfinite, parse_float=_finite_float)
    except Exception as exc:
        fail("invalid JSON in " + name + ": " + str(exc))


def main():
    fleet = load("fleet/snapshot.json")
    for g in fleet.get("groups", []):
        if g.get("status") not in STATUSES:
            fail("fleet group " + str(g.get("name")) + " has status not in " + str(sorted(STATUSES)))
    totals = fleet.get("totals", {})
    if totals.get("itemized_here", 0) > totals.get("groups", 0):
        fail("fleet itemized_here exceeds provider group total")
    if totals.get("active", 0) > totals.get("groups", 0):
        fail("fleet active exceeds provider group total")

    witness = load("witness/records.json")
    recs = witness.get("records", [])
    if not isinstance(recs, list):
        fail("witness records must be a list")
    for i, r in enumerate(recs):
        if "digest" not in r or "recorded_at" not in r:
            fail("witness record " + str(i) + " missing digest/recorded_at")
        body = {k: v for k, v in r.items() if k != "digest"}
        canon = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if hashlib.sha3_256(canon.encode("utf-8")).hexdigest() != r["digest"]:
            fail("witness digest chain broken at record " + str(i))

    heldout = load("receipts/v5-heldout.json")
    for c in heldout.get("criteria", []):
        if not isinstance(c, dict) or "id" not in c:
            fail("heldout criterion missing id")
        if "trippability_audit" not in c:
            fail("criterion " + c["id"] + " has no trippability_audit (A9)")
        if c.get("a10_status") == "UNINTERPRETABLE" and c.get("recorded_pass") is True and "a10_note" not in c:
            fail("criterion " + c["id"] + " passed while UNINTERPRETABLE without an A10 note")

    bench = load("receipts/v5-bench.json")
    for ck in bench.get("checkpoints", []):
        if not isinstance(ck.get("eval_loss"), (int, float)):
            fail("bench checkpoint missing numeric eval_loss")

    proto = load("protocol/status.json")
    freeze = proto.get("freeze", {})
    if freeze.get("frozen") and not freeze.get("freeze_date"):
        fail("protocol claims frozen without a freeze date")
    if not isinstance(proto.get("open_szl", {}), dict):
        fail("protocol open_szl must be an object")

    print("OK: all observatory data files valid; no secret-shaped content")
    sys.exit(0)


if __name__ == "__main__":
    main()
