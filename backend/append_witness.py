#!/usr/bin/env python3
"""Append a Part D witness record. Stdlib only. Fail-closed.

Records are SHA3-256 digest-chained over canonical JSON, each record carrying
the previous record's digest. The chain is verified before appending; a broken
chain refuses to write. Nothing is deleted; the series is append-only.
"""
import datetime
import hashlib
import json
import pathlib
import sys

REC = pathlib.Path(__file__).resolve().parents[1] / "data" / "witness" / "records.json"


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_of(record):
    body = {k: v for k, v in record.items() if k != "digest"}
    return hashlib.sha3_256(canon(body).encode("utf-8")).hexdigest()


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: append_witness.py '<json payload with observer and observation>'")
    try:
        payload = json.loads(sys.argv[1])
    except Exception as exc:
        sys.exit("payload is not JSON: " + str(exc))
    if not isinstance(payload, dict) or "observer" not in payload or "observation" not in payload:
        sys.exit("payload requires 'observer' and 'observation'")

    doc = json.loads(REC.read_text(encoding="utf-8"))
    recs = doc.get("records", [])
    for i, r in enumerate(recs):
        if digest_of(r) != r.get("digest"):
            sys.exit("digest chain broken at record " + str(i) + " - refusing to append")

    prev = recs[-1]["digest"] if recs else None
    body = dict(payload)
    body["sequence"] = len(recs)
    body["recorded_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    body["prev_digest"] = prev
    body["digest"] = hashlib.sha3_256(canon(body).encode("utf-8")).hexdigest()
    recs.append(body)
    doc["records"] = recs
    REC.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print("appended sequence", body["sequence"], "digest", body["digest"])


if __name__ == "__main__":
    main()
