"""No-network adversarial tests for GitHub/HF/public-WINK release identity."""
from __future__ import annotations

import copy
import json
import unittest

from scripts import wink_release_probe as w


class IndependentReleaseProbeTests(unittest.TestCase):
    GIT = "b" * 40
    SPACE = "a" * 40
    OTHER = "c" * 40

    def fake(self, *, root=200, sdk="docker", stage="RUNNING",
             ready=200, producer="FRESH", build_sha=None, space_sha=None,
             science=True, gone=()):
        gh = {"ref": "refs/heads/main", "object": {"sha": self.GIT, "type": "commit"}}
        hf = {"id": w.SPACE, "private": False, "sha": space_sha or self.SPACE,
              "cardData": {"sdk": sdk}, "runtime": {"stage": stage}}
        results = {
            w.MAIN_URL: w.Readback(200, gh),
            w.SPACE_URL: w.Readback(200, hf),
            w.APP_URL + "/": w.Readback(root),
            w.APP_URL + "/healthz": w.Readback(200, {"process": "SERVING"}),
            w.APP_URL + "/readyz": w.Readback(ready, {"scientific_ready": False}),
            w.APP_URL + "/api/v1/build-info": w.Readback(
                200, {"declared_source_revision": build_sha or self.GIT,
                      "independent_runtime_verified": False}),
            w.APP_URL + "/api/v1/observatory": w.Readback(
                200, {"producer_telemetry_state": producer, "source_state": "PUBLIC_DATASET_READBACK"}),
            w.APP_URL + "/api/v1/acceptance-audit": w.Readback(
                200, {"overall_admission": "HOLD", "independent_evaluation_verified": False}
                if science else {"overall_admission": "PASS"}),
        }
        for url in gone:
            results[url] = w.Readback(404)
        def lookup(url):
            self.assertIn(url, w.FIXED)
            return copy.deepcopy(results[url])
        return lookup

    def test_actual_successful_transport_still_not_production_admission(self):
        result = w.observe(self.fake())
        self.assertEqual(result["github_main_sha"], self.GIT)
        self.assertEqual(result["hf_space_revision"], self.SPACE)
        self.assertEqual(result["deployment_state"], "HTTP_REACHABLE_UNADMITTED")
        self.assertEqual(result["release_admission"], "HOLD")
        self.assertEqual(result["scientific_admission"], "HOLD")
        self.assertTrue(result["declared_source_matches_current_main"])
        self.assertFalse(result["source_byte_parity_independently_verified"])
        self.assertFalse(result["independent_runtime_verified"])
        self.assertFalse(result["owner_countersignatures_verified"])

    def test_public_static_space_404_is_release_hold_even_when_provider_running(self):
        result = w.observe(self.fake(root=404, sdk="static", ready=404))
        self.assertEqual(result["http_get_statuses"]["/"], "404")
        self.assertIn("PUBLIC_ROOT_NOT_HTTP_200", result["blockers"])
        self.assertIn("HF_DOCKER_SDK_NOT_DEPLOYED", result["blockers"])
        self.assertEqual(result["deployment_state"], "HOLD")

    def test_main_mismatch_cannot_be_recast_as_green_pr_head(self):
        result = w.observe(self.fake(build_sha=self.OTHER))
        self.assertFalse(result["declared_source_matches_current_main"])
        self.assertIn("DEPLOYED_BUILD_SOURCE_NOT_EQUAL_MAIN", result["blockers"])
        self.assertEqual(result["deployment_state"], "HOLD")

    def test_hf_revision_and_service_source_are_different_identities(self):
        result = w.observe(self.fake(space_sha=self.OTHER))
        self.assertEqual(result["hf_space_revision"], self.OTHER)
        self.assertEqual(result["github_main_sha"], self.GIT)
        self.assertTrue(result["declared_source_matches_current_main"])
        self.assertFalse(result["source_byte_parity_independently_verified"])

    def test_healthy_app_cannot_make_stale_producer_fresh(self):
        result = w.observe(self.fake(producer="STALE", ready=503))
        self.assertEqual(result["http_get_statuses"]["/"], "200")
        self.assertEqual(result["producer_telemetry_state"], "STALE")
        self.assertIn("UPSTREAM_PRODUCER_NOT_FRESH", result["blockers"])
        self.assertEqual(result["telemetry_readiness"], "STALE_OR_UNAVAILABLE")
        # The Python UI is still publicly routable even when science data are stale.
        self.assertEqual(result["deployment_state"], "HTTP_REACHABLE_UNADMITTED")
        self.assertEqual(result["release_admission"], "HOLD")

    def test_no_scientific_audit_is_not_a_qualified_model(self):
        result = w.observe(self.fake(science=False))
        self.assertFalse(result["scientific_acceptance_report_present"])
        self.assertIn("SCIENTIFIC_GATE_REPORT_UNAVAILABLE", result["blockers"])
        self.assertEqual(result["scientific_admission"], "HOLD")

    def test_unknown_http_is_distinct_from_404(self):
        lookup = self.fake()
        def unavailable(url):
            if url == w.APP_URL + "/":
                return w.Readback(None)
            return lookup(url)
        result = w.observe(unavailable)
        self.assertEqual(result["http_get_statuses"]["/"], "UNAVAILABLE")
        self.assertEqual(result["deployment_state"], "HOLD")

    def test_private_hf_space_is_unavailable_not_current(self):
        lookup = self.fake()
        def private(url):
            if url == w.SPACE_URL:
                return w.Readback(200, {"id": w.SPACE, "private": True, "sha": self.SPACE})
            return lookup(url)
        result = w.observe(private)
        self.assertIsNone(result["hf_space_revision"])
        self.assertIn("HF_SPACE_REVISION_UNAVAILABLE", result["blockers"])

    def test_missing_main_or_malformed_sha_fails_closed(self):
        lookup = self.fake()
        def not_main(url):
            if url == w.MAIN_URL:
                return w.Readback(200, {"ref": "refs/heads/feature",
                                        "object": {"sha": self.GIT}})
            return lookup(url)
        result = w.observe(not_main)
        self.assertIsNone(result["github_main_sha"])
        self.assertEqual(result["release_admission"], "HOLD")

    def test_public_http_allowlist_refuses_arbitrary_private_urls(self):
        with self.assertRaises(w.Unavailable):
            w.get("http://127.0.0.1:8080/secret")
        with self.assertRaises(w.Unavailable):
            w.get("https://huggingface.co/api/whoami-v2")
        with self.assertRaises(w.Unavailable):
            w.get(w.APP_URL + "/admin")

    def test_secret_shape_or_duplicate_keys_cannot_be_accepted(self):
        with self.assertRaises(w.Unavailable):
            json.loads('{"state":"CURRENT","state":"HOLD"}',
                       object_pairs_hook=w._pairs)
        with self.assertRaises(w.Unavailable):
            json.loads('{"number":NaN}', parse_constant=w._nonfinite)

    def test_identities_and_state_are_json_serializable(self):
        result = w.observe(self.fake())
        value = json.loads(json.dumps(result))
        self.assertEqual(value["schema"], "wink.deployment-independent-readback/v1")
        self.assertEqual(value["owner_countersignatures_verified"], False)


if __name__ == "__main__":
    unittest.main()
