"""Source and production browser must not invent a missing node metric."""
from __future__ import annotations

import unittest

from scripts.wink_browser_smoke import node_count_admission
from scripts import wink_public_runtime_watch as w


class NodeMetricAdmissionTests(unittest.TestCase):
    def test_local_html_requires_explicit_nonzero_bounded_node_count(self):
        for value in (None, 0, False, True, "", "17", 257, -1, 1.5, [], {}):
            with self.subTest(value=repr(value)):
                self.assertEqual(node_count_admission("local", value), (False, False))
        self.assertEqual(node_count_admission("local", 17), (True, True))
        self.assertEqual(node_count_admission("local", 256), (True, True))

    def test_existing_published_public_client_without_dom_node_count_is_unknown(self):
        self.assertEqual(node_count_admission("public", None), (True, False))
        # A real zero is a denied observation, not an absence.
        for value in (0, -1, 257, False, True, "17", [], {}):
            with self.subTest(value=repr(value)):
                self.assertEqual(node_count_admission("public", value), (False, False))

    def test_new_public_build_with_instrumented_17_nodes_is_verified(self):
        self.assertEqual(node_count_admission("public", 17), (True, True))

    def test_forbidden_target_rejected(self):
        with self.assertRaisesRegex(ValueError, "UNAPPROVED_BROWSER_TARGET"):
            node_count_admission("other", None)

    def test_public_witness_never_fabricates_itemized_count(self):
        t = {
            "github_main_sha": "b" * 40,
            "hf_space_revision": "a" * 40,
            "hf_sdk": "static",
            "static_http_get_statuses": {
                "/index.html": "200",
                "/style.css": "200",
            },
        }
        b = {
            "url": w.STATIC_URL,
            "state": "SOURCE_AND_3D_CLIENT_BOOT_VERIFIED",
            "actual_browser_render_verified": True,
            "http": 200,
            "feed_badge": "STALE SNAPSHOT",
            "webgl_draw_calls_before": 512,
            "webgl_draw_calls_after": 5440,
            "canvas_pixel_change_observed": True,
            "navigation_click_active": True,
            "protocol_panel_rendered": True,
            "has_webgl": True,
            "js_exceptions": [],
            "provider_writes": False,
            "training_started": False,
            "independent_scientific_validation": False,
            "itemized_worm_nodes": None,
            "itemized_node_count_verified": False,
            "itemized_node_count_state": "NOT_EXPOSED_BY_LEGACY_PUBLIC_HTML",
        }
        result = w.classify(b, t)
        self.assertEqual(result["deployment_observation"], "PUBLIC_STATIC_CLIENT_BOOT_OBSERVED")
        self.assertIsNone(result["public_itemized_node_count"])
        self.assertFalse(result["public_itemized_node_count_verified"])
        self.assertEqual(result["public_itemized_node_count_state"],
                         "NOT_EXPOSED_BY_LEGACY_PUBLIC_HTML")
        self.assertEqual(result["release_admission"], "HOLD")


if __name__ == "__main__":
    unittest.main()
