"""Read-only compute and training admission. Does not launch GPU jobs."""
from __future__ import annotations

import os
from urllib.parse import urlsplit
from backend.live_data import fresh, summary

def compute_status() -> dict:
    """Trust is not granted merely because an endpoint URL was configured.

    The reviewed gpu-bridge output schema, signer pin, source SHA and runtime
    freshness must be admitted separately. No private IPs, secrets or actions.
    """
    if os.getenv("WINK_BRIDGE_PUBLIC_RECEIPTS", "0") == "1":
        from backend.gpu_receipts import readback
        receipt=readback()
        return {**receipt, "gpu_job_launched": False,
                "verified_runtime": False,
                "note": "Published signed-queue evidence only; no direct GPU/host connection."}
    url = os.getenv("WINK_COMPUTE_STATUS_URL", "")
    host = os.getenv("WINK_COMPUTE_TRUSTED_HOST", "")
    if not url or not host:
        return {"state": "UNCONFIGURED", "verified_runtime": False,
                "gpu_job_launched": False, "source": None}
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname != host or
            not host.endswith(".a-11-oy.com") or
            p.port not in (None, 443) or p.username or p.password or
            p.query or p.fragment or not p.path.startswith("/api/") or len(url) > 250):
        return {"state": "CONFIG_REJECTED", "verified_runtime": False,
                "gpu_job_launched": False, "source": None}
    return {"state": "OWNER_ADAPTER_REVIEW_REQUIRED", "verified_runtime": False,
            "gpu_job_launched": False, "source": url,
            "note": "Do not claim GPU connectivity without a signed status contract and independent runtime readback."}

def training_decision(s: dict) -> dict:
    """A public receipt dataset is not a labeled biological training dataset."""
    ev = summary(s)
    doc = s.get("docs") or {}
    protocol = doc.get("protocol") or {}
    witness = doc.get("witness") or {}
    gates = [
        {"id": "public_feed_revision", "state": "PASS" if fresh(s) and
         s.get("dataset_revision") else "HOLD",
         "scope": "Current public dataset readback, not lab instrumentation"},
        {"id": "protocol_and_countersignatures", "state": "HOLD",
         "scope": "Authenticated mutual lab agreement and observer pins not verified"},
        {"id": "licensed_labeled_training_dataset", "state": "HOLD",
         "scope": "No C. elegans animal/session video and expert annotation set supplied"},
        {"id": "subject_disjoint_holdout", "state": "HOLD",
         "scope": "A9 trippability and A10 neutral scoring remain open"},
        {"id": "hpc_budget_and_owner_authority", "state": "HOLD",
         "scope": "GPU route, run manifest, budget and owner approval not independently verified"},
        {"id": "rollback_and_independent_witness", "state": "HOLD",
         "scope": "Release signature, runtime attestation and rollback remain separate"},
    ]
    return {"decision": "HOLD", "training_started": False,
            "model_trained": False, "accelerator_allocated": False,
            "scientific_model_qualified": False, "source_revision": ev["dataset_revision"],
            "protocol_frozen": (protocol.get("freeze") or {}).get("frozen"),
            "witness_records": len(witness.get("records") or []),
            "gates": gates,
            "next_action": "Obtain a licensed and annotated biological dataset, animal-disjoint holdout, explicit GPU budget, owner pins, and reviewed A9/A10 criteria."}
