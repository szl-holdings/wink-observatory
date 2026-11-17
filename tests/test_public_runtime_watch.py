"""Adversarial, no-network tests for public HF browser runtime evidence."""
from __future__ import annotations

import unittest
from unittest import mock
from types import ModuleType
from pathlib import Path
import json
import tempfile

from scripts import wink_public_runtime_watch as w
from scripts import wink_browser_smoke as smoke

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
    def test_redirected_browser_reports_observed_origin_not_requested_origin(self):
        # Exercise the actual browser adapter, not a prebuilt evidence dict.
        # No browser installation, network, or page JavaScript is needed.
        for final_url, response_url in (
            ("https://unexpected.example/index.html", "https://unexpected.example/index.html"),
            (smoke.PUBLIC, "https://unexpected.example/index.html"),
        ):
            with self.subTest(final_url=final_url, response_url=response_url):
                api = ModuleType("playwright.sync_api")
                api.TimeoutError = type("PlaywrightTimeoutError", (Exception,), {})
                manager = mock.MagicMock()
                api.sync_playwright = mock.Mock(return_value=manager)
                browser_instance = manager.__enter__.return_value.chromium.launch.return_value
                page = browser_instance.new_page.return_value
                page.url = final_url
                page.goto.return_value.status = 200
                page.goto.return_value.url = response_url
                with mock.patch.dict("sys.modules", {"playwright.sync_api": api}):
                    result = smoke.observe("public")
                self.assertEqual(result["state"], "UNEXPECTED_BROWSER_ORIGIN")
                self.assertEqual(result["url"], final_url)
                self.assertFalse(result["actual_browser_render_verified"])
                page.evaluate.assert_not_called()
                browser_instance.close.assert_called_once()
                self.assertFalse(w.classify(result, transport())["public_client_boot_verified"])

    def test_playwright_specific_error_retains_transport_and_failed_receipt(self):
        error = type("PlaywrightError", (Exception,), {})
        loader = mock.Mock(side_effect=[lambda: transport(),
                                       mock.Mock(side_effect=error("private diagnostic"))])
        with mock.patch.object(w, "_load", loader):
            result = w.observe()
        self.assertEqual(result["deployment_observation"], "INCOMPLETE_PUBLIC_OBSERVATION")
        self.assertEqual(result["github_main_sha"], MAIN)
        self.assertEqual(result["hf_revision"], HF)
        self.assertEqual(result["browser_failure_type"], "PlaywrightError")
        self.assertNotIn("private diagnostic", str(result))
        self.assertEqual(result["release_admission"], "HOLD")

        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "witness.json"
            with mock.patch.object(w, "observe", return_value=result), \
                 mock.patch("sys.argv", ["watch", "--output", str(dest)]), \
                 mock.patch("builtins.print"):
                self.assertEqual(w.main(), 2)
            self.assertEqual(json.loads(dest.read_text())["browser_failure_type"],
                             "PlaywrightError")

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
