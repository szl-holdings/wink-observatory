"""Public Space revision/SDK truth states; no provider writes or laboratory claims."""
from __future__ import annotations
import unittest
from unittest.mock import patch

from backend import live_sources as live

class PublicSpaceMetadataTests(unittest.TestCase):
    def setUp(self):
        live._cache.clear()

    def test_static_runtime_metadata_never_claims_science_or_source_parity(self):
        provider={"id":live.SPACE,"private":False,"sha":"c"*40,
                  "cardData":{"sdk":"static"},
                  "runtime":{"stage":"RUNNING"}}
        with patch.object(live,"get_json",return_value=provider) as getter:
            outcome=live.read_now()
        getter.assert_called_once_with(live.API)
        self.assertEqual(outcome["space_repository_revision"],"c"*40)
        self.assertEqual(outcome["space_sdk"],"static")
        self.assertEqual(outcome["provider_runtime_stage"],"RUNNING")
        self.assertFalse(outcome["independent_runtime_verified"])
        self.assertFalse(outcome["lab_instrument_verified"])
        self.assertFalse(outcome["app_source_parity_verified"])
        self.assertFalse(outcome["http_root_verified"])

    def test_cache_is_explicitly_not_another_live_read(self):
        provider={"id":live.SPACE,"private":False,"sha":"d"*40,
                  "cardData":{"sdk":"docker"}, "runtime":{"stage":"RUNNING"}}
        with patch.object(live,"get_json",return_value=provider) as getter:
            first=live.status()
            cached=live.status()
        self.assertEqual(getter.call_count,1)
        self.assertEqual(first["state"],"LIVE_PUBLIC_HF_METADATA")
        self.assertEqual(cached["state"],"CACHED_PUBLIC_HF_METADATA")
        self.assertFalse(cached["metadata_observed_live"])

    def test_moved_or_private_space_is_unavailable(self):
        for invalid in (
            {"id":live.SPACE,"private":True,"sha":"a"*40},
            {"id":"another/space","private":False,"sha":"a"*40},
            {"id":live.SPACE,"private":False,"sha":"main"},
            {"id":live.SPACE,"private":False,"sha":"a"*40,
             "cardData":{"sdk":"static"}}
        ):
            with self.subTest(invalid=invalid):
                with patch.object(live,"get_json",return_value=invalid):
                    result=live.status(force=True)
                self.assertEqual(result["state"],"PUBLIC_HF_METADATA_UNAVAILABLE")
                self.assertFalse(result["independent_runtime_verified"])
                live._cache.clear()

if __name__=="__main__":
    unittest.main()
