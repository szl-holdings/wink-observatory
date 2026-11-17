"""Revision-pinned, bounded public scientific data readback. No secrets or lab PII.

Reading a public repository is not reading a live experiment. The release
controller must separately verify Space runtime identity and witness authority.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from threading import RLock
import time
from urllib.parse import urlencode, urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
DATASET = "SZLHOLDINGS/wink-observatory-data"
FILES = {"fleet": "fleet/snapshot.json", "protocol": "protocol/status.json",
         "witness": "witness/records.json", "heldout": "receipts/v5-heldout.json",
         "bench": "receipts/v5-bench.json", "diagnosis": "receipts/a10-diagnosis.json"}
SHA = re.compile(r"[a-f0-9]{40}\Z")
MAX_BYTES = 262144
TTL = 60.0
_lock = RLock()
_cache: dict = {}

class SourceUnavailable(ValueError):
    """Inadequate source evidence, not an empty observation."""

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SourceUnavailable("REDIRECT_REFUSED")

def pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise SourceUnavailable("DUPLICATE_JSON_KEY")
        out[key] = value
    return out

def nonfinite(_):
    raise SourceUnavailable("NONFINITE_NUMBER")

def finite_float(value: str) -> float:
    number=float(value)
    if not math.isfinite(number):
        raise SourceUnavailable("NONFINITE_NUMBER")
    return number

def get_json(url: str) -> dict:
    p = urlsplit(url)
    allowed = (
        (p.netloc == "huggingface.co" and not p.query and
         (p.path == "/api/datasets/" + DATASET or
          p.path.startswith("/datasets/" + DATASET + "/raw/")))
        or (p.netloc == "www.ebi.ac.uk" and
            p.path == "/europepmc/webservices/rest/search")
    )
    if p.scheme != "https" or p.username or p.password or p.fragment or not allowed:
        raise SourceUnavailable("SOURCE_URL_NOT_ALLOWLISTED")
    request = Request(url, headers={"Accept": "application/json",
                                   "User-Agent": "SZL-WINK-Observatory/1",
                                   "Cache-Control": "no-cache"})
    opener = build_opener(ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=7) as response:
            if response.status != 200 or response.geturl() != url:
                raise SourceUnavailable("UNEXPECTED_HTTP")
            raw = response.read(MAX_BYTES + 1)
    except (OSError, URLError, HTTPError, TimeoutError) as exc:
        raise SourceUnavailable("PUBLIC_SOURCE_UNAVAILABLE") from exc
    if not raw or len(raw) > MAX_BYTES:
        raise SourceUnavailable("SOURCE_BYTE_BUDGET")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise SourceUnavailable("SOURCE_INVALID_JSON") from exc
    if not isinstance(value, dict):
        raise SourceUnavailable("SOURCE_NOT_OBJECT")
    return value

def utc(value: str) -> datetime:
    if not isinstance(value, str) or len(value) > 42:
        raise SourceUnavailable("SOURCE_TIMESTAMP_INVALID")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SourceUnavailable("SOURCE_TIMESTAMP_INVALID") from exc
    if d.tzinfo is None or d.utcoffset().total_seconds() != 0:
        raise SourceUnavailable("SOURCE_TIMESTAMP_NOT_UTC")
    return d

def validate(docs: dict) -> None:
    schemas = {"fleet": "wink/fleet-snapshot/v0.1",
               "protocol": "wink/protocol-status/v0.1",
               "witness": "wink/witness/v0.1-draft",
               "heldout": "wink/receipt-heldout/v0.1",
               "bench": "wink/receipt-bench/v0.1"}
    for key, schema in schemas.items():
        if docs.get(key, {}).get("schema_version") != schema:
            raise SourceUnavailable("SOURCE_SCHEMA_MISMATCH_" + key)
    fleet = docs["fleet"]
    groups, totals = fleet.get("groups"), fleet.get("totals")
    if not isinstance(groups, list) or not isinstance(totals, dict) or len(groups) > 250:
        raise SourceUnavailable("FLEET_INCOMPLETE")
    if any(not isinstance(row, dict) or row.get("status") not in
           {"running", "parked", "complete", "degraded", "stopped"} for row in groups):
        raise SourceUnavailable("FLEET_STATUS_INVALID")
    n, itemized, active = (totals.get(k) for k in ("groups", "itemized_here", "active"))
    if (any(type(v) is not int or v < 0 for v in (n, itemized, active))
            or itemized != len(groups) or itemized > n or active > n):
        raise SourceUnavailable("FLEET_TOTALS_CONTRADICT")
    utc(fleet.get("captured_at"))
    records = docs["witness"].get("records")
    if not isinstance(records, list) or len(records) > 5000:
        raise SourceUnavailable("WITNESS_INCOMPLETE")
    prev = None
    for i, row in enumerate(records):
        if not isinstance(row, dict) or row.get("sequence") != i or row.get("prev_digest") != prev:
            raise SourceUnavailable("WITNESS_CHAIN_IDENTITY_MISMATCH")
        utc(row.get("recorded_at"))
        body = {k: v for k, v in row.items() if k != "digest"}
        raw = json.dumps(body, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode()
        digest = hashlib.sha3_256(raw).hexdigest()
        if row.get("digest") != digest:
            raise SourceUnavailable("WITNESS_DIGEST_MISMATCH")
        prev = digest
    freeze = docs["protocol"].get("freeze")
    if not isinstance(freeze, dict) or type(freeze.get("frozen")) is not bool:
        raise SourceUnavailable("PROTOCOL_FREEZE_UNKNOWN")
    if freeze["frozen"] and not freeze.get("freeze_date"):
        raise SourceUnavailable("UNSUPPORTED_FROZEN_CLAIM")
    criteria = docs["heldout"].get("criteria")
    if not isinstance(criteria, list) or not criteria:
        raise SourceUnavailable("HELDOUT_EVIDENCE_MISSING")
    if any(not isinstance(c, dict) or not isinstance(c.get("trippability_audit"), dict)
           for c in criteria):
        raise SourceUnavailable("A9_TRIPPABILITY_EVIDENCE_MISSING")

def fetch_public() -> dict:
    info = get_json("https://huggingface.co/api/datasets/" + DATASET)
    sha = info.get("sha")
    if (info.get("id") != DATASET or info.get("private") is not False
            or not isinstance(sha, str) or not SHA.fullmatch(sha)):
        raise SourceUnavailable("DATASET_REVISION_UNAVAILABLE")
    docs = {key: get_json(f"https://huggingface.co/datasets/{DATASET}/raw/{sha}/{path}")
            for key, path in FILES.items()}
    validate(docs)
    return {"source_state": "PUBLIC_DATASET_READBACK", "source_kind": "PUBLIC_REPOSITORY",
            "dataset_revision": sha, "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "signature_verified": False, "independent_lab_verified": False,
            "wetlab_instrument_state": "NOT_CONNECTED", "docs": docs}

def mirror() -> dict:
    docs = {}
    for key, path in FILES.items():
        file = ROOT / "data" / path
        if not file.is_file() or file.stat().st_size > MAX_BYTES:
            raise SourceUnavailable("PACKAGED_MIRROR_MISSING")
        docs[key] = json.loads(file.read_text(encoding="utf-8"),
                               object_pairs_hook=pairs, parse_constant=nonfinite)
    validate(docs)
    return {"source_state": "OFFLINE_PACKAGED_MIRROR", "source_kind": "PACKAGED_REPOSITORY",
            "dataset_revision": None, "retrieved_at": None,
            "signature_verified": False, "independent_lab_verified": False,
            "wetlab_instrument_state": "NOT_CONNECTED", "docs": docs}

def snapshot(*, force: bool = False) -> dict:
    with _lock:
        now = time.monotonic()
        if not force and _cache.get("ok") and now - _cache["time"] < TTL:
            result = copy.deepcopy(_cache["ok"])
            result["source_state"] = "RECENT_READBACK_CACHE"
            result["cache_age_seconds"] = round(now - _cache["time"], 1)
            return result
        try:
            result = fetch_public()
        except (SourceUnavailable, OSError, TypeError, KeyError, ValueError):
            if _cache.get("ok"):
                result = copy.deepcopy(_cache["ok"])
                result["source_state"] = "STALE_LAST_SUCCESS"
                result["cache_age_seconds"] = round(now - _cache["time"], 1)
            else:
                try:
                    result = mirror()
                except (SourceUnavailable, OSError, ValueError, KeyError, TypeError):
                    result = {"source_state": "UNAVAILABLE", "source_kind": "UNKNOWN",
                              "dataset_revision": None, "retrieved_at": None,
                              "signature_verified": False, "independent_lab_verified": False,
                              "wetlab_instrument_state": "NOT_CONNECTED", "docs": {}}
        else:
            _cache.update(time=now, ok=copy.deepcopy(result))
        return result

def research() -> dict:
    """Public Europe PMC paper metadata; never presented as instrument telemetry."""
    query = urlencode({"query": '("Caenorhabditis elegans" OR "C. elegans")',
                       "format": "json", "pageSize": "6", "sort": "FIRST_PDATE_D desc"})
    try:
        data = get_json("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + query)
        rows = data.get("resultList", {}).get("result")
        if not isinstance(rows, list) or len(rows) > 6:
            raise SourceUnavailable("LITERATURE_RESPONSE_INVALID")
        clean = []
        for row in rows:
            if not isinstance(row, dict):
                raise SourceUnavailable("LITERATURE_RESPONSE_INVALID")
            clean.append({key: str(row.get(key) or "")[:240]
                          for key in ("id", "title", "authorString", "pubYear", "doi")})
        return {"state": "LIVE_PUBLIC_METADATA", "provider": "Europe PMC",
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "papers": clean}
    except (SourceUnavailable, OSError, KeyError, TypeError, ValueError):
        return {"state": "UNAVAILABLE", "provider": "Europe PMC",
                "retrieved_at": None, "papers": []}

def summary(s: dict) -> dict:
    docs = s.get("docs") or {}
    fleet, protocol = docs.get("fleet") or {}, docs.get("protocol") or {}
    witness, heldout = docs.get("witness") or {}, docs.get("heldout") or {}
    return {"source_state": s["source_state"], "source_kind": s["source_kind"],
            "dataset_id": DATASET, "dataset_revision": s["dataset_revision"],
            "readback_at": s["retrieved_at"],
            "source_snapshot_at": fleet.get("captured_at"),
            "provider_reported_groups": (fleet.get("totals") or {}).get("groups"),
            "provider_reported_active": (fleet.get("totals") or {}).get("active"),
            "operator_itemized": len(fleet.get("groups") or []),
            "witness_records": len(witness.get("records") or []),
            "protocol_frozen": (protocol.get("freeze") or {}).get("frozen"),
            "heldout_verdict": heldout.get("overall_verdict", "UNAVAILABLE"),
            "wetlab_instrument_state": "NOT_CONNECTED", "signature_verified": False,
            "independent_lab_verified": False,
            "claim": "Public source readback, not experimental measurements"}

def fresh(s: dict) -> bool:
    return s.get("source_state") in {"PUBLIC_DATASET_READBACK", "RECENT_READBACK_CACHE"}
