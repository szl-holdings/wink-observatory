"""Read-only public GitHub evidence-plane adapter for the existing SZL GPU bridge.

A released GitHub receipt is NOT a live GPU process, a trained model or a
cryptographic verification. No host addresses, credentials, polling agent or
provider effector are accessed here.
"""
from __future__ import annotations
import base64
from datetime import datetime, timezone
import hashlib
import json
import re
from threading import Lock
import time
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

REPO="szl-holdings/szl-gpu-bridge"
BASE="https://api.github.com/repos/"+REPO
PATTERN=re.compile(r"job-2026-nemo-v3-governed-attempt-([1-9][0-9]{0,3})\.json\Z")
SHA=re.compile(r"[a-f0-9]{40}\Z")
BUDGET=262144
_lock=Lock()
_cache={}

class BridgeUnavailable(ValueError):
    pass

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise BridgeUnavailable("REDIRECT_REFUSED")

def pairs(items):
    d={}
    for k,v in items:
        if k in d:
            raise BridgeUnavailable("DUPLICATE_GITHUB_JSON_KEY")
        d[k]=v
    return d

def github_get(path,revision=None):
    if not isinstance(path,str) or ".." in path or not path.startswith("/"):
        raise BridgeUnavailable("INVALID_GITHUB_PATH")
    if revision is not None and (not isinstance(revision,str) or not SHA.fullmatch(revision)):
        raise BridgeUnavailable("INVALID_GITHUB_REVISION")
    url=BASE+path+("?ref="+revision if revision is not None else "")
    p=urlsplit(url)
    if p.scheme!="https" or p.netloc!="api.github.com" or not p.path.startswith("/repos/"+REPO+"/"):
        raise BridgeUnavailable("GITHUB_URL_NOT_ALLOWLISTED")
    request=Request(url,headers={"Accept":"application/vnd.github+json",
                                 "User-Agent":"SZL-WINK-GPU-Receipt-Readback/1"})
    try:
        with build_opener(ProxyHandler({}),NoRedirect()).open(request,timeout=7) as r:
            if r.status!=200 or r.geturl()!=url:
                raise BridgeUnavailable("GITHUB_HTTP_UNAVAILABLE")
            raw=r.read(BUDGET+1)
    except (URLError,HTTPError,OSError,TimeoutError) as exc:
        raise BridgeUnavailable("GITHUB_UNAVAILABLE") from exc
    if not raw or len(raw)>BUDGET:
        raise BridgeUnavailable("GITHUB_RESPONSE_BUDGET")
    try:
        return json.loads(raw.decode(),object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(BridgeUnavailable("NONFINITE_JSON")))
    except (UnicodeError,ValueError,RecursionError) as exc:
        raise BridgeUnavailable("INVALID_GITHUB_JSON") from exc

def latest_receipt():
    ref=github_get("/git/ref/heads/main")
    if not isinstance(ref,dict):
        raise BridgeUnavailable("MAIN_REF_INVALID")
    sha=(ref.get("object") or {}).get("sha")
    if not isinstance(sha,str) or not SHA.fullmatch(sha):
        raise BridgeUnavailable("MAIN_REVISION_INVALID")
    entries=github_get("/contents/queue/evidence",sha)
    if not isinstance(entries,list) or not entries or len(entries)>=100:
        raise BridgeUnavailable("EVIDENCE_INCOMPLETE")
    numbered=[]
    for item in entries:
        if not isinstance(item,dict) or item.get("type")!="file":
            raise BridgeUnavailable("EVIDENCE_ITEM_INVALID")
        match=PATTERN.fullmatch(str(item.get("name","")))
        if match:
            numbered.append((int(match.group(1)),item["name"]))
    if not numbered:
        raise BridgeUnavailable("NO_OWNED_RECEIPT")
    index,name=max(numbered)
    rel="queue/evidence/"+name
    entry=github_get("/contents/"+rel,sha)
    if (not isinstance(entry,dict) or entry.get("path")!=rel or
            entry.get("type")!="file" or entry.get("encoding")!="base64"
            or not isinstance(entry.get("content"),str) or
            not isinstance(entry.get("sha"),str) or not SHA.fullmatch(entry["sha"])):
        raise BridgeUnavailable("RECEIPT_BLOB_METADATA_INVALID")
    try:
        raw=base64.b64decode(entry["content"],validate=False)
    except (ValueError,TypeError) as exc:
        raise BridgeUnavailable("RECEIPT_BASE64_INVALID") from exc
    if not raw or len(raw)>65536 or hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()!=entry["sha"]:
        raise BridgeUnavailable("RECEIPT_GIT_BLOB_MISMATCH")
    try:
        receipt=json.loads(raw.decode(),object_pairs_hook=pairs)
    except (UnicodeError,ValueError,RecursionError) as exc:
        raise BridgeUnavailable("RECEIPT_JSON_INVALID") from exc
    if (not isinstance(receipt,dict) or receipt.get("kind")!="szl-nemo-v3-pre-dispatch-evidence"
            or receipt.get("v")!=1 or receipt.get("jobId")!=name.removesuffix(".json")):
        raise BridgeUnavailable("RECEIPT_SCHEMA_OR_JOB_INVALID")
    details=receipt.get("preDispatchEvidence")
    if not isinstance(details,dict):
        raise BridgeUnavailable("RECEIPT_PHASE_MISSING")
    fields=("eventCreated","workflowRunCreated","claimCreated","trainingStarted",
            "receiptUploaded","adapterUploaded","deployed","promoted")
    if any(type(details.get(field)) is not bool for field in fields):
        raise BridgeUnavailable("RECEIPT_EFFECTS_INCOMPLETE")
    return {"state":"PUBLIC_GITHUB_RECEIPT_READBACK",
            "bridge_repository":REPO,"protected_bridge_main_sha":sha,
            "latest_attempt":index,"job_id":receipt["jobId"],
            "failure_phase":str(details.get("failurePhase","UNKNOWN"))[:90],
            "reported_training_started":details["trainingStarted"],
            "reported_deployed":details["deployed"],
            "reported_promoted":details["promoted"],
            "signed_receipt_verified":False,
            "live_gpu_runtime_verified":False,
            "evidence_url":"https://github.com/"+REPO+"/blob/"+sha+"/"+rel,
            "retrieved_at":datetime.now(timezone.utc).isoformat(),
            "note":"Public repository record, not an active-node or signature witness"}

def readback():
    """Bounded cache avoids unauthenticated GitHub public API quota exhaustion."""
    with _lock:
        now=time.monotonic()
        if _cache.get("data") and now-_cache["at"]<120:
            result=dict(_cache["data"])
            result["state"]="CACHED_PUBLIC_GITHUB_RECEIPT"
            result["cached_seconds"]=round(now-_cache["at"],1)
            return result
        try:
            result=latest_receipt()
        except (BridgeUnavailable,KeyError,TypeError,ValueError,OSError):
            return {"state":"PUBLIC_GPU_EVIDENCE_UNAVAILABLE","live_gpu_runtime_verified":False,
                    "signed_receipt_verified":False,"reported_training_started":None}
        _cache.update(at=now,data=dict(result))
        return result
