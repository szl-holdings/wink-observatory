"""Public, read-only GPU bridge receipt scope; never connects to the host."""
from __future__ import annotations
import base64
import hashlib
import json
import unittest
from unittest.mock import patch

from backend import gpu_receipts as g

class BridgeReadbackTests(unittest.TestCase):
    def setUp(self):
        g._cache.clear()

    def make_receipt(self):
        return {"kind":"szl-nemo-v3-pre-dispatch-evidence","v":1,
                "jobId":"job-2026-nemo-v3-governed-attempt-16",
                "preDispatchEvidence":{
                    "failurePhase":"PRE_DISPATCH_VALIDATOR_REJECTED",
                    "eventCreated":False,"workflowRunCreated":False,
                    "claimCreated":False,"trainingStarted":False,
                    "receiptUploaded":False,"adapterUploaded":False,
                    "deployed":False,"promoted":False}}

    def test_reads_latest_immutable_public_receipt_as_evidence_only(self):
        sha="b"*40
        doc=self.make_receipt()
        raw=json.dumps(doc,sort_keys=True).encode()
        blob=hashlib.sha1(f"blob {len(raw)}\0".encode()+raw).hexdigest()
        selected=[]
        def getter(path,revision=None):
            selected.append((path,revision))
            if path=="/git/ref/heads/main":
                return {"object":{"sha":sha}}
            if path=="/contents/queue/evidence":
                self.assertEqual(revision,sha)
                return [{"type":"file","name":"job-2026-nemo-v3-governed-attempt-15.json"},
                        {"type":"file","name":"job-2026-nemo-v3-governed-attempt-16.json"}]
            self.assertEqual(revision,sha)
            return {"path":"queue/evidence/job-2026-nemo-v3-governed-attempt-16.json",
                    "type":"file","encoding":"base64","content":base64.b64encode(raw).decode(),
                    "sha":blob}
        with patch.object(g,"github_get",side_effect=getter):
            r=g.latest_receipt()
        self.assertEqual(r["latest_attempt"],16)
        self.assertEqual(r["protected_bridge_main_sha"],sha)
        self.assertEqual(r["failure_phase"],"PRE_DISPATCH_VALIDATOR_REJECTED")
        self.assertFalse(r["reported_training_started"])
        self.assertFalse(r["live_gpu_runtime_verified"])
        self.assertFalse(r["signed_receipt_verified"])
        self.assertEqual(len(selected),3)

    def test_missing_or_corrupted_receipt_fails_closed(self):
        with patch.object(g,"github_get",return_value={"object":{"sha":"main"}}):
            self.assertEqual(g.readback()["state"],"PUBLIC_GPU_EVIDENCE_UNAVAILABLE")

    def test_github_api_host_and_commit_are_not_user_selectable(self):
        for bad in ("/../secrets","/contents/../tokens"):
            with self.subTest(bad=bad),self.assertRaises(g.BridgeUnavailable):
                g.github_get(bad)
        with self.assertRaises(g.BridgeUnavailable):
            g.github_get("/contents/queue/evidence","main")

if __name__=="__main__":
    unittest.main()
