#!/usr/bin/env python3
"""Bounded public WINK deployment witness: read-only, independent of PR-head CI.

This observer never deploys, signs, authorizes, retries mutating calls, or reads
tokens. GitHub protected-main identity, HF repository revision, provider SDK,
actual HTTP application routing, declared source and experimental evidence are
different assertions. Every unknown or mismatch is an explicit HOLD.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

REPO = "szl-holdings/wink-observatory"
SPACE = "SZLHOLDINGS/wink-observatory"
MAIN_URL = "https://api.github.com/repos/" + REPO + "/git/ref/heads/main"
SPACE_URL = "https://huggingface.co/api/spaces/" + SPACE
APP_URL = "https://szlholdings-wink-observatory.hf.space"
ROUTES = ("/", "/healthz", "/readyz", "/api/v1/build-info",
          "/api/v1/observatory", "/api/v1/acceptance-audit")
SHA40 = re.compile(r"[a-f0-9]{40}\Z")
MAX_BODY = 131072
FIXED = {MAIN_URL, SPACE_URL, *(APP_URL + p for p in ROUTES)}
JSON_ROUTES = {MAIN_URL, SPACE_URL, *(APP_URL + p for p in ROUTES if p != "/")}


class Unavailable(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Unavailable("REDIRECT_DENIED")


@dataclass(frozen=True)
class Readback:
    http: int | None
    payload: dict | None = None
    sha256: str | None = None


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise Unavailable("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _nonfinite(_):
    raise Unavailable("NONFINITE_JSON")


def get(url: str) -> Readback:
    """Public, allowlisted HTTPS GET only. No proxy, auth, cookies or redirects."""
    if url not in FIXED:
        raise Unavailable("UNAPPROVED_ENDPOINT")
    opener = build_opener(ProxyHandler({}), NoRedirect())
    req = Request(url, headers={"Accept": "application/json, text/html",
                                "User-Agent": "SZL-WINK-Release-Readback/1",
                                "Cache-Control": "no-cache, no-store"}, method="GET")
    try:
        with opener.open(req, timeout=8) as resp:
            if resp.geturl() != url:
                raise Unavailable("HTTP_REDIRECT_REFUSED")
            status = int(resp.status)
            raw = resp.read(MAX_BODY + 1)
    except HTTPError as exc:
        code = int(exc.code)
        exc.close()
        return Readback(code)
    except (URLError, TimeoutError, OSError, Unavailable):
        return Readback(None)
    if len(raw) > MAX_BODY:
        return Readback(None)
    digest = sha256(raw).hexdigest()
    if status != 200:
        return Readback(status, sha256=digest)
    if url in JSON_ROUTES:
        try:
            body = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                              parse_constant=_nonfinite)
        except (UnicodeError, ValueError, RecursionError):
            return Readback(200, sha256=digest)
        if not isinstance(body, dict):
            return Readback(200, sha256=digest)
        return Readback(200, payload=body, sha256=digest)
    return Readback(200, sha256=digest)


def _valid_sha(x: Any) -> bool:
    return isinstance(x, str) and SHA40.fullmatch(x) is not None


def _http_status(value: Readback) -> str:
    return "UNAVAILABLE" if value.http is None else str(value.http)


def observe(fetch=get) -> dict:
    """A transport/source readback is not an approval, signature, or scientific pass."""
    checks = [MAIN_URL, SPACE_URL, *(APP_URL + p for p in ROUTES)]
    data = {}
    for url in checks:
        try:
            observation = fetch(url)
            if not isinstance(observation, Readback):
                observation = Readback(None)
        except (OSError, ValueError, TypeError, TimeoutError):
            observation = Readback(None)
        data[url] = observation
    gh = data[MAIN_URL]
    hf = data[SPACE_URL]
    main = None
    if gh.http == 200 and isinstance(gh.payload, dict):
        ref = gh.payload
        sha = (ref.get("object") or {}).get("sha") if isinstance(ref.get("object"), dict) else None
        if ref.get("ref") == "refs/heads/main" and _valid_sha(sha):
            main = sha
    space_sha, sdk, stage = None, None, None
    if hf.http == 200 and isinstance(hf.payload, dict) and hf.payload.get("id") == SPACE \
            and hf.payload.get("private") is False:
        obj = hf.payload
        space_sha = obj.get("sha") if _valid_sha(obj.get("sha")) else None
        card = obj.get("cardData")
        runtime = obj.get("runtime")
        sdk = card.get("sdk") if isinstance(card, dict) else None
        stage = runtime.get("stage") if isinstance(runtime, dict) else None
    routes = {path: _http_status(data[APP_URL + path]) for path in ROUTES}
    build = data[APP_URL + "/api/v1/build-info"]
    declared = build.payload.get("declared_source_revision") if isinstance(build.payload, dict) else None
    telemetry = data[APP_URL + "/api/v1/observatory"]
    ev = telemetry.payload if isinstance(telemetry.payload, dict) else None
    audit = data[APP_URL + "/api/v1/acceptance-audit"]
    science = audit.payload if isinstance(audit.payload, dict) else None
    declared_source_match = bool(_valid_sha(main) and declared == main)
    producer_state = ev.get("producer_telemetry_state") if ev else None
    http_root = routes["/"] == "200"
    route_statuses = [routes[p] for p in ROUTES if p != "/readyz"]
    all_http = http_root and all(code == "200" for code in route_statuses)
    ready_status = routes["/readyz"]
    provider_running = (sdk == "docker" and stage == "RUNNING")
    code_valid = (science is not None and science.get("overall_admission") == "HOLD"
                  and science.get("independent_evaluation_verified") is False)
    parity_declared = all_http and declared_source_match
    upstream_fresh = producer_state == "FRESH"
    # The HTML/UI can be reachable even while a producer is stale. Those are
    # different readiness dimensions and must not be collapsed to one green bit.
    app_transport_ok = provider_running and all_http and parity_declared and code_valid
    telemetry_ready = upstream_fresh and ready_status == "200"
    blockers = []
    if main is None: blockers.append("GITHUB_PROTECTED_MAIN_UNAVAILABLE")
    if space_sha is None: blockers.append("HF_SPACE_REVISION_UNAVAILABLE")
    if sdk != "docker": blockers.append("HF_DOCKER_SDK_NOT_DEPLOYED")
    if stage != "RUNNING": blockers.append("HF_RUNTIME_NOT_RUNNING")
    if not http_root: blockers.append("PUBLIC_ROOT_NOT_HTTP_200")
    for p in ROUTES[1:]:
        if routes[p] != "200":
            blockers.append("ROUTE_UNAVAILABLE:" + p + ":HTTP_" + routes[p])
    if not declared_source_match: blockers.append("DEPLOYED_BUILD_SOURCE_NOT_EQUAL_MAIN")
    if not code_valid: blockers.append("SCIENTIFIC_GATE_REPORT_UNAVAILABLE")
    if not upstream_fresh: blockers.append("UPSTREAM_PRODUCER_NOT_FRESH")
    # No self-reported build flag or GitHub CI check can establish the independent
    # deployment witness or authorize experiments. A second issuer is required.
    return {
        "schema": "wink.deployment-independent-readback/v1",
        "source": REPO, "space": SPACE,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "github_main_sha": main,
        "hf_space_revision": space_sha,
        "hf_sdk": sdk, "hf_provider_runtime_stage": stage,
        "http_get_statuses": routes,
        "http_root_reachable": http_root,
        "all_non_readiness_routes_http_200": all_http,
        "readyz_http_status": ready_status,
        "app_transport_state": "HTTP_REACHABLE_SOURCE_DECLARATION_MATCH"
        if app_transport_ok else "HOLD",
        "telemetry_readiness": "CURRENT_PRODUCER" if telemetry_ready else "STALE_OR_UNAVAILABLE",
        "declared_runtime_source_sha": declared if _valid_sha(declared) else None,
        "declared_source_matches_current_main": declared_source_match,
        "source_byte_parity_independently_verified": False,
        "source_identity_state": "DECLARED_MATCH_NOT_INDEPENDENT_PARITY"
        if parity_declared else "UNVERIFIED_OR_MISMATCH",
        "producer_telemetry_state": producer_state or "UNAVAILABLE",
        "scientific_acceptance_report_present": code_valid,
        "scientific_admission": "HOLD",
        "partner_data_rights_verified": False,
        "owner_countersignatures_verified": False,
        "gpu_training_active_verified": False,
        "environment_reviewers_verified": False,
        "independent_runtime_verified": False,
        "deployment_state": "HTTP_REACHABLE_UNADMITTED"
        if app_transport_ok else "HOLD",
        "release_admission": "HOLD",
        "blockers": blockers or ["INDEPENDENT_RUNTIME_AND_OWNER_ATTESTATION_MISSING"],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, help="Write public evidence report, not deployment")
    p.add_argument("--strict-transport", action="store_true",
                   help="Fail when public app routes, Docker SDK or source declaration are absent; telemetry may remain stale")
    args = p.parse_args()
    report = observe()
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding="utf-8", newline="\n")
    print(raw, end="")
    if args.strict_transport and report["deployment_state"] != "HTTP_REACHABLE_UNADMITTED":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
