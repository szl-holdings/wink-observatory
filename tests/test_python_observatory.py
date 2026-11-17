"""No network, secrets, GPU or lab instruments. Source and scientific-state regressions."""
from __future__ import annotations
import copy
import hashlib
import json
import unittest
from unittest.mock import patch

from backend import live_data as live
from backend.admission import compute_status, training_decision

class PublicEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs={k:json.loads((live.ROOT/"data"/p).read_text(encoding="utf-8"))
                  for k,p in live.FILES.items()}
    def setUp(self):
        live._cache.clear()

    def test_local_mirror_cannot_claim_live_instrument(self):
        s=live.mirror()
        self.assertEqual(s["source_state"],"OFFLINE_PACKAGED_MIRROR")
        self.assertFalse(live.fresh(s))
        self.assertFalse(s["signature_verified"])
        self.assertFalse(s["independent_lab_verified"])
        self.assertEqual(s["wetlab_instrument_state"],"NOT_CONNECTED")

    def test_full_public_dataset_revision_pins_each_file_read(self):
        sha="a"*40
        observed=[]
        def getter(url):
            observed.append(url)
            if url.endswith("/api/datasets/"+live.DATASET):
                return {"id":live.DATASET,"private":False,"sha":sha}
            for key,path in live.FILES.items():
                if url.endswith("/raw/"+sha+"/"+path):
                    return copy.deepcopy(self.docs[key])
            self.fail("unapproved URL: "+url)
        with patch.object(live,"get_json",side_effect=getter):
            result=live.fetch_public()
        self.assertEqual(result["dataset_revision"],sha)
        self.assertEqual(result["source_state"],"PUBLIC_DATASET_READBACK")
        self.assertEqual(len(observed),len(live.FILES)+1)
        self.assertFalse(result["independent_lab_verified"])

    def test_wrong_private_or_mutable_metadata_fails_closed(self):
        for body in ({"id":live.DATASET,"private":True,"sha":"b"*40},
                     {"id":live.DATASET,"private":False,"sha":"main"},
                     {"id":"other/dataset","private":False,"sha":"b"*40}):
            with self.subTest(body=body):
                with patch.object(live,"get_json",return_value=body):
                    with self.assertRaises(live.SourceUnavailable):
                        live.fetch_public()

    def test_ledger_pointer_and_hash_are_both_checked(self):
        docs=copy.deepcopy(self.docs)
        record={"observer":"TEST_ONLY","observation":"synthetic negative control",
                "sequence":0,"recorded_at":"2026-11-17T04:00:00Z","prev_digest":None}
        record["digest"]=hashlib.sha3_256(json.dumps(record,sort_keys=True,separators=(",",":"),
                                                     ensure_ascii=False).encode()).hexdigest()
        docs["witness"]["records"]=[record]
        live.validate(docs)
        wrong=copy.deepcopy(docs)
        wrong["witness"]["records"][0]["prev_digest"]="f"*64
        with self.assertRaisesRegex(live.SourceUnavailable,"CHAIN_IDENTITY"):
            live.validate(wrong)
        wrong=copy.deepcopy(docs)
        wrong["witness"]["records"][0]["digest"]="f"*64
        with self.assertRaisesRegex(live.SourceUnavailable,"DIGEST_MISMATCH"):
            live.validate(wrong)

    def test_json_duplicate_and_nan_are_rejected(self):
        with self.assertRaises(live.SourceUnavailable):
            json.loads('{"id":1,"id":2}',object_pairs_hook=live.pairs)
        with self.assertRaises(live.SourceUnavailable):
            json.loads('{"id":NaN}',parse_constant=live.nonfinite)

    def test_network_denial_degrades_to_mirror(self):
        with patch.object(live,"fetch_public",side_effect=live.SourceUnavailable("DOWN")):
            snapshot=live.snapshot(force=True)
        self.assertEqual(snapshot["source_state"],"OFFLINE_PACKAGED_MIRROR")
        self.assertFalse(live.fresh(snapshot))

    def test_untrippable_bench_cannot_train_biology(self):
        decision=training_decision(live.mirror())
        self.assertEqual(decision["decision"],"HOLD")
        self.assertFalse(decision["accelerator_allocated"])
        self.assertFalse(decision["model_trained"])
        self.assertEqual(decision["witness_records"],0)
        self.assertTrue(any(x["state"]=="HOLD" for x in decision["gates"]))

    def test_unconfigured_hpc_not_claimed(self):
        with patch.dict("os.environ",{},clear=True):
            self.assertEqual(compute_status()["state"],"UNCONFIGURED")
        with patch.dict("os.environ",{"WINK_COMPUTE_STATUS_URL":"http://127.0.0.1/admin",
                                     "WINK_COMPUTE_TRUSTED_HOST":"127.0.0.1"},clear=True):
            self.assertEqual(compute_status()["state"],"CONFIG_REJECTED")

    def test_live_http_does_not_grant_signature_or_lab_authority(self):
        s={"source_state":"PUBLIC_DATASET_READBACK","source_kind":"PUBLIC_REPOSITORY",
           "dataset_revision":"f"*40,"retrieved_at":"2026-11-17T04:00:00Z",
           "docs":copy.deepcopy(self.docs)}
        result=live.summary(s)
        self.assertFalse(result["signature_verified"])
        self.assertFalse(result["independent_lab_verified"])
        self.assertFalse(result["protocol_frozen"])
        self.assertEqual(result["wetlab_instrument_state"],"NOT_CONNECTED")

    def test_external_research_host_is_strictly_allowlisted(self):
        for bad in ("http://huggingface.co/api/datasets/"+live.DATASET,
                    "https://evil.example/api/datasets/"+live.DATASET,
                    "https://huggingface.co/private/"):
            with self.subTest(bad=bad), self.assertRaises(live.SourceUnavailable):
                live.get_json(bad)

if __name__=="__main__":
    unittest.main()
