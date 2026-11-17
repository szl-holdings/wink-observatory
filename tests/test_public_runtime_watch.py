"""Adversarial, no-network tests for public HF browser runtime evidence."""
from __future__ import annotations

import unittest

from scripts import wink_public_runtime_watch as w

MAIN = "b" * 40
HF = "a" * 40


def transport(sdk="static", reachable=True):
    return {
        "github_main_sha": MAIN,
        "hf_space_revision": HF,
        "hf_sdk": sdk,
        "static_http_get_statuses": {
            "/index.html": "200" if reachable else "404",
            "/style.css": "200" if reachable else "404",
        },
        "blockers": ["HF_DOCKER_SDK_NOT_DEPLOYED"],
    }


def browser(verified=False):
    return {
        "url": w.STATIC_URL,
        "state": "SOURCE_AND_3D_CLIENT_BOOT_VERIFIED"
                 if verified else "HOLD_CLIENT_BOOT_OR_DATA_UNAVAILABLE",
        "actual_browser_render_verified": verified,
        "http": 200,
        "feed_badge": "STALE SNAPSHOT" if verified else "BOOT",
        "feed_detail": "Dataset historical · producer stale" if verified else "starting...",
        "webgl_draw_calls_before": 512 if verified else 0,
        "webgl_draw_calls_after": 5440 if verified else 0,
        "canvas_pixel_change_observed": verified,
        "navigation_click_active": verified,
        "protocol_panel_rendered": verified,
        "has_webgl": verified,
        "js_exceptions": [],
        "provider_writes": False,
        "training_started": False,
        "independent_scientific_validation": False,
    }


class PublicRuntimeMonitorTests(unittest.TestCase):
    def test_http_200_with_broken_javascript_is_observed_hold_not_green_production(self):
        record = w.classify(browser(), transport())
        self.assertTrue(record["public_static_http_reachable"])
        self.assertEqual(record["browser_badge"], "BOOT")
        self.assertEqual(record["deployment_observation"], "PUBLIC_STATIC_CLIENT_BOOT_HOLD")
        self.assertFalse(record["public_client_boot_verified"])
        self.assertFalse(record["source_byte_parity_independently_verified"])
        self.assertEqual(record["release_admission"], "HOLD")

    def test_genuine_browser_canary_still_never_authorizes_science_or_deployment(self):
        record = w.classify(browser(True), transport())
        self.assertEqual(record["deployment_observation"], "PUBLIC_STATIC_CLIENT_BOOT_OBSERVED")
        self.assertTrue(record["public_client_boot_verified"])
        self.assertEqual(record["browser_webgl_draws_after"], 5440)
        self.assertTrue(record["browser_canvas_pixel_change_observed"])
        self.assertFalse(record["verified_owner_release_approval"])
        self.assertFalse(record["independent_scientific_validation"])
        self.assertFalse(record["gpu_training_active_verified"])
        self.assertFalse(record["source_byte_parity_independently_verified"])
        self.assertEqual(record["release_admission"], "HOLD")

    def test_missing_public_static_http_cannot_pass_even_with_fake_browser_success(self):
        record = w.classify(browser(True), transport(reachable=False))
        self.assertEqual(record["deployment_observation"], "STATIC_HTTP_UNAVAILABLE")
        self.assertFalse(record["public_client_boot_verified"])

    def test_unknown_source_or_browser_is_incomplete_not_known_failure(self):
        for b,t in (({}, {}), ({"state": "BROWSER_UNAVAILABLE"}, transport()),
                    (None, transport()), (browser(), {"hf_sdk": "static"})):
            with self.subTest(browser=b, transport=t):
                record = w.classify(b, t)
                self.assertEqual(record["deployment_observation"],
                                 "INCOMPLETE_PUBLIC_OBSERVATION")
                self.assertEqual(record["release_admission"], "HOLD")

    def test_future_docker_migration_does_not_inherit_static_state(self):
        record = w.classify(browser(True), transport(sdk="docker"))
        self.assertEqual(record["deployment_observation"],
                         "STATIC_CLIENT_NOT_APPLICABLE_TO_CURRENT_SDK")
        self.assertFalse(record["public_client_boot_verified"])

    def test_wrong_browser_origin_or_self_reported_release_pass_is_denied(self):
        for field,value in (("url", "https://evil.example/"),
                            ("state", "HOLD_CLIENT_BOOT_OR_DATA_UNAVAILABLE"),
                            ("http", 404),
                            ("provider_writes", True),
                            ("training_started", True),
                            ("independent_scientific_validation", True),
                            ("has_webgl", False),
                            ("webgl_draw_calls_before", 0),
                            ("webgl_draw_calls_after", 12),
                            ("canvas_pixel_change_observed", False),
                            ("navigation_click_active", False),
                            ("protocol_panel_rendered", False),
                            ("js_exceptions", ["render crashed"]),
                            ("feed_badge", "BOOT"),
                            ("actual_browser_render_verified", False)):
            with self.subTest(field=field):
                b=browser(True)
                b[field]=value
                record=w.classify(b,transport())
                self.assertEqual(record["deployment_observation"],
                                 "PUBLIC_STATIC_CLIENT_BOOT_HOLD")
                self.assertFalse(record["public_client_boot_verified"])

    def test_metadata_only_http_200_does_not_prove_client(self):
        t=transport()
        b={"url":w.STATIC_URL, "http":200, "state":"SOURCE_AND_3D_CLIENT_BOOT_VERIFIED",
           "actual_browser_render_verified":False, "provider_writes":False,
           "training_started":False, "independent_scientific_validation":False}
        result=w.classify(b,t)
        self.assertEqual(result["deployment_observation"], "PUBLIC_STATIC_CLIENT_BOOT_HOLD")


if __name__ == "__main__":
    unittest.main()
