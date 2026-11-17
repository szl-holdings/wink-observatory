"""Read-only ENA *C. elegans* sequencing accession discovery.

Provider: EMBL-EBI European Nucleotide Archive Portal API. Taxonomy is fixed to
NCBI 6239. Returns only public catalog metadata (no FASTQ, lab records,
genotypes, participant data, trainable labels, or direct assay measurements).
A bounded catalog sample must never be advertised as the global census,
fresh experimental acquisition, licensing approval, or biological model proof.

Docs: https://ena-docs.readthedocs.io/en/latest/retrieval/programmatic-access/taxon-based-search.html
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from threading import Lock
import time
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener

HOST = "www.ebi.ac.uk"
PATH = "/ena/portal/api/search"
TAXON = 6239
LIMIT = 6
MAX_BYTES = 131072
_CACHE_SECONDS = 600
_RUN = re.compile(r"(?:SRR|ERR|DRR)[0-9]{3,15}\Z")
_STUDY = re.compile(r"(?:SRP|ERP|DRP|PRJNA|PRJEB|PRJDB)[0-9]{2,15}\Z")
_ALLOWED_FIELDS = ("run_accession", "study_accession", "sample_accession",
                   "scientific_name", "instrument_platform", "first_public")
_cache: dict = {}
_lock = Lock()


class ENAUnavailable(ValueError):
    """Unknown or incomplete public catalog response, never an empty study."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ENAUnavailable("REDIRECT_REFUSED")


def _pairs(items):
    output = {}
    for key, value in items:
        if key in output:
            raise ENAUnavailable("DUPLICATE_CATALOG_KEY")
        output[key] = value
    return output


def _nonfinite(_):
    raise ENAUnavailable("NONFINITE_NUMBER")


def url() -> str:
    return "https://" + HOST + PATH + "?" + urlencode({
        "result": "read_run", "query": f"tax_eq({TAXON})",
        "fields": ",".join(_ALLOWED_FIELDS),
        "format": "json", "limit": str(LIMIT),
    })


def _get(request_url: str):
    """No user-chosen URL; no redirects, cookies, token, proxies or raw-read downloads."""
    if request_url != url():
        raise ENAUnavailable("SOURCE_URL_NOT_CANONICAL")
    parts = urlsplit(request_url)
    if (parts.scheme != "https" or parts.hostname != HOST or parts.port not in (None, 443)
            or parts.path != PATH or parts.username or parts.password or parts.fragment):
        raise ENAUnavailable("SOURCE_HOST_INVALID")
    opener = build_opener(ProxyHandler({}), NoRedirect())
    request = Request(request_url, headers={"Accept": "application/json",
                                            "User-Agent": "SZL-WINK-ENA-Research/1",
                                            "Cache-Control": "no-cache"})
    try:
        with opener.open(request, timeout=8) as response:
            if response.status != 200 or response.geturl() != request_url:
                raise ENAUnavailable("CATALOG_HTTP_INVALID")
            raw = response.read(MAX_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ENAUnavailable("CATALOG_SOURCE_UNAVAILABLE") from exc
    if not raw or len(raw) > MAX_BYTES:
        raise ENAUnavailable("CATALOG_RESPONSE_BUDGET")
    try:
        rows = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=_nonfinite)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ENAUnavailable("CATALOG_INVALID_JSON") from exc
    if not isinstance(rows, list) or len(rows) > LIMIT:
        raise ENAUnavailable("CATALOG_RESULT_SHAPE")
    return rows


def _validate(rows: list[dict]) -> list[dict]:
    if not isinstance(rows, list) or not rows or len(rows) > LIMIT:
        raise ENAUnavailable("CATALOG_EMPTY_OR_INCOMPLETE")
    clean = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not set(row).issubset(_ALLOWED_FIELDS):
            raise ENAUnavailable("CATALOG_UNEXPECTED_FIELDS")
        run = row.get("run_accession")
        if not isinstance(run, str) or not _RUN.fullmatch(run) or run in seen:
            raise ENAUnavailable("CATALOG_RUN_IDENTITY_INVALID")
        seen.add(run)
        study = row.get("study_accession")
        if not isinstance(study, str) or not _STUDY.fullmatch(study):
            raise ENAUnavailable("CATALOG_STUDY_IDENTITY_INVALID")
        organism = row.get("scientific_name")
        if organism != "Caenorhabditis elegans":
            # Taxonomy query alone must not be interpreted as validated taxon coverage.
            raise ENAUnavailable("CATALOG_TAXON_MISMATCH")
        data = {}
        for key in _ALLOWED_FIELDS:
            value = row.get(key)
            if value is not None and (not isinstance(value, str) or len(value) > 140
                                      or any(ord(c) < 32 for c in value)):
                raise ENAUnavailable("CATALOG_FIELD_UNSAFE")
            data[key] = value
        clean.append(data)
    return clean


def _read_live() -> dict:
    rows = _validate(_get(url()))
    return {
        "state": "LIVE_PUBLIC_ARCHIVE_CATALOG",
        "source_kind": "ENA_PUBLIC_ACCESSION_METADATA",
        "provider": "EMBL-EBI European Nucleotide Archive",
        "taxon_id": TAXON,
        "query": f"tax_eq({TAXON})",
        "sample_limit": LIMIT,
        "catalog_completeness": "BOUNDED_SAMPLE_NOT_CENSUS",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "records": rows,
        "raw_sequences_downloaded": False,
        "live_lab_instrument_connected": False,
        "labeled_training_data_verified": False,
        "licensing_approved_for_training": False,
        "independent_scientific_validation": False,
        "source_url": url(),
    }


def sample(*, force: bool = False) -> dict:
    """Unknown ENA state is not an observed zero or laboratory negative result."""
    with _lock:
        now = time.monotonic()
        if not force and "data" in _cache and now - _cache["time"] < _CACHE_SECONDS:
            return {**_cache["data"], "state": "CACHED_PUBLIC_ARCHIVE_CATALOG",
                    "cache_age_seconds": round(now - _cache["time"], 1)}
        try:
            result = _read_live()
        except (ENAUnavailable, KeyError, ValueError, TypeError, OSError):
            return {
                "state": "PUBLIC_ARCHIVE_UNAVAILABLE",
                "source_kind": "ENA_PUBLIC_ACCESSION_METADATA",
                "provider": "EMBL-EBI European Nucleotide Archive",
                "taxon_id": TAXON,
                "retrieved_at": None,
                "catalog_completeness": "UNKNOWN",
                "records": [],
                "observed_zero_runs": False,
                "raw_sequences_downloaded": False,
                "live_lab_instrument_connected": False,
                "labeled_training_data_verified": False,
                "licensing_approved_for_training": False,
                "independent_scientific_validation": False,
            }
        _cache.update(time=now, data=result)
        return result
