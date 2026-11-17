"""WINK all-Python FastAPI + Gradio serving stack. All GET endpoints are read-only."""
from __future__ import annotations

import os
from pathlib import Path
import re
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import gradio as gr

from backend.live_data import fresh, producer_fresh, research, snapshot, summary
from backend.admission import compute_status, training_decision
from backend.live_sources import status as public_space_status
from backend.ena_catalog import sample as ena_sample
from backend.falsifiability import public_audit
from backend.ui import build_ui

api=FastAPI(title="WINK Observatory",version="1.0.0",
            description="Source-revision-pinned public evidence, not wet-lab instrumentation.")
_SHA=re.compile(r"[a-f0-9]{40}\Z")

@api.middleware("http")
async def headers(request, call_next):
    response=await call_next(request)
    response.headers["Cache-Control"]="no-store, max-age=0"
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="no-referrer"
    return response

@api.get("/healthz")
def healthz():
    return {"process":"SERVING", "public_feed":"UNVERIFIED_UNTIL_READBACK",
            "scientific_ready":False}

@api.get("/readyz")
def readyz():
    s=snapshot()
    ok=fresh(s) and producer_fresh(s) and bool(s.get("dataset_revision"))
    return JSONResponse(status_code=200 if ok else 503,
                        content={"public_dataset":"READABLE" if ok else "UNAVAILABLE",
                                 "source_state":s["source_state"],"producer_telemetry_state":summary(s)["producer_telemetry_state"],"scientific_ready":False,
                                 "wetlab_instrument":"NOT_CONNECTED"})

@api.get("/api/v1/observatory")
def observatory():
    return {"schema":"wink.observatory.public-evidence/v1",**summary(snapshot())}

@api.get("/api/v1/acceptance-audit")
def acceptance_audit():
    """Exact rate-threshold arithmetic; retains scientific HOLD."""
    return public_audit(snapshot())


@api.get("/api/v1/sequence-catalog")
def sequence_catalog():
    """Six accession metadata rows maximum. No FASTQ, study-wide census or lab data."""
    result = ena_sample()
    status = 200 if result["state"] in ("LIVE_PUBLIC_ARCHIVE_CATALOG", "CACHED_PUBLIC_ARCHIVE_CATALOG") else 503
    return JSONResponse(status_code=status, content=result)


@api.get("/api/v1/research")
def literature():
    return research()

@api.get("/api/v1/training")
def training():
    return training_decision(snapshot())

@api.get("/api/v1/compute")
def compute():
    return compute_status()

@api.get("/api/v1/public-space")
def public_space():
    return public_space_status()

@api.get("/api/v1/build-info")
def build_info():
    source=os.getenv("WINK_GITHUB_SHA","")
    if not _SHA.fullmatch(source):
        try:
            source=Path(__file__).resolve().parents[1].joinpath("SOURCE_REVISION").read_text().strip()
        except OSError:
            source=""
    return {"github_repo":"szl-holdings/wink-observatory",
            "declared_source_revision":source if _SHA.fullmatch(source) else None,
            "source_authority":"PUBLISHER_DECLARATION_ONLY" if _SHA.fullmatch(source) else "UNKNOWN",
            "deployed_hf_revision":None,"independent_runtime_verified":False,
            "signature_verified":False,"gpu_training_started":False}

app=gr.mount_gradio_app(api,build_ui(),path="/")
