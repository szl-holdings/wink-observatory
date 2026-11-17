"""Live, unauthenticated provider readback for the exact public WINK HF Space.

This reads Hugging Face repository and runtime *metadata*, not lab instruments,
Docker process health, scientific validation, GPU state, or release authority.
"""
from __future__ import annotations
from datetime import datetime, timezone
import re
from threading import Lock
import time

from backend.live_data import SourceUnavailable, get_json

SPACE = "SZLHOLDINGS/wink-observatory"
API = "https://huggingface.co/api/spaces/" + SPACE
SHA = re.compile(r"[0-9a-f]{40}\Z")
_lock = Lock()
_cache: dict = {}
TTL = 45.0

def read_now() -> dict:
    info = get_json(API)
    if info.get("id") != SPACE or info.get("private") is not False:
        raise SourceUnavailable("PUBLIC_SPACE_IDENTITY_UNAVAILABLE")
    rev = info.get("sha")
    if not isinstance(rev, str) or not SHA.fullmatch(rev):
        raise SourceUnavailable("PUBLIC_SPACE_REVISION_UNAVAILABLE")
    card = info.get("cardData")
    runtime = info.get("runtime")
    if not isinstance(card, dict) or not isinstance(runtime, dict):
        raise SourceUnavailable("PUBLIC_SPACE_METADATA_INCOMPLETE")
    sdk = card.get("sdk")
    stage = runtime.get("stage")
    if sdk not in ("static", "docker", "gradio") or not isinstance(stage, str) or len(stage) > 40:
        raise SourceUnavailable("PUBLIC_SPACE_SDK_OR_STAGE_INVALID")
    return {"state": "LIVE_PUBLIC_HF_METADATA",
            "space_id": SPACE,
            "space_repository_revision": rev,
            "space_sdk": sdk,
            "provider_runtime_stage": stage,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "metadata_observed_live": True,
            "http_root_verified": False,
            "app_source_parity_verified": False,
            "independent_runtime_verified": False,
            "lab_instrument_verified": False,
            "note": "Hugging Face provider metadata only, not direct HTTP root or wet-lab measurements"}

def status(*, force: bool = False) -> dict:
    with _lock:
        now = time.monotonic()
        if not force and _cache.get("data") and now - _cache["time"] < TTL:
            result = dict(_cache["data"])
            result["state"] = "CACHED_PUBLIC_HF_METADATA"
            result["metadata_observed_live"] = False
            result["cache_age_seconds"] = round(now - _cache["time"], 1)
            return result
        try:
            result = read_now()
        except (SourceUnavailable, OSError, KeyError, TypeError, ValueError):
            return {"state": "PUBLIC_HF_METADATA_UNAVAILABLE",
                    "space_id": SPACE,
                    "space_repository_revision": None,
                    "space_sdk": None,
                    "provider_runtime_stage": "UNKNOWN",
                    "retrieved_at": None,
                    "metadata_observed_live": False,
                    "http_root_verified": False,
                    "app_source_parity_verified": False,
                    "independent_runtime_verified": False,
                    "lab_instrument_verified": False}
        _cache.update(data=dict(result), time=now)
        return result
