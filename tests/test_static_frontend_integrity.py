"""Static WINK 3D boot contract: syntax, provenance and safe display.

This test caught the 2026-11-17 historical HF HTML truncated at 'for ('
with no closing module script, body or html. An HTTP 200 alone proves
nothing about whether a Three.js app actually initialized.

No external JavaScript, browser, internet or partner data is required here.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "frontend" / "index.html"


class StaticFrontendIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML.read_text(encoding="utf-8")
        open_script = '<script type="module">'
        assert cls.html.count(open_script) == 1
        cls.module = cls.html.split(open_script, 1)[1].split("</script>", 1)[0]

    def test_full_document_contains_closed_module_body_and_html(self):
        self.assertTrue(self.html.lstrip().startswith("<!DOCTYPE html>"))
        self.assertTrue(self.html.rstrip().endswith("</html>"))
        self.assertEqual(self.html.count("</script>"), 2)
        self.assertEqual(self.html.count("</body>"), 1)
        self.assertEqual(self.html.count("</html>"), 1)
        self.assertNotIn("    for (\n</script>", self.html)

    def test_es_module_parses_as_actual_javascript(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js not installed; HTML structural checks still apply")
        result = subprocess.run(
            [node, "--check", "--input-type=module"],
            input=self.module, text=True,
            capture_output=True, timeout=15, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr[:1400])

    def test_render_loop_and_dom_status_are_initialized_not_boot_forever(self):
        for term in ("requestAnimationFrame(renderFrame)",
                     "refreshPublic();",
                     "setInterval(refreshPublic, 5 * 60 * 1000)",
                     "reportFeed('VERIFYING'",
                     "function applyLive()",
                     "controls.update()",
                     "renderer.render(scene, camera)",
                     "addEventListener('resize'"):
            with self.subTest(term=term):
                self.assertIn(term, self.module)
        self.assertNotIn("LIVE INSTRUMENT", self.html)

    def test_immutable_dataset_revision_is_used_never_mutable_main(self):
        self.assertIn("metadata.sha", self.module)
        self.assertIn("/raw/' + metadata.sha + '/'", self.module)
        self.assertIn("PUBLIC_DATASET_REVISION_UNAVAILABLE", self.module)
        self.assertNotIn("var BASE =", self.html)
        self.assertIn("cache: 'no-store'", self.module)
        self.assertIn("credentials: 'omit'", self.module)
        self.assertIn("redirect: 'error'", self.module)

    def test_bounded_finite_source_shapes_and_explicit_a9_a10_holds(self):
        for term in ("PUBLIC_FLEET_SCHEMA_OR_DENOMINATOR_INVALID",
                     "WITNESS_CHAIN_UNVERIFIED_OR_OBSERVATION_STARTED",
                     "HELDOUT_BATTERY_INCOMPLETE",
                     "A9_EVIDENCE_INVALID",
                     "A10_UNINTERPRETABLE_STATUS_MISSING",
                     "BENCH_SNAPSHOT_INVALID",
                     "STALE SNAPSHOT",
                     "OFFLINE BASELINE",
                     "CACHED SNAPSHOT",
                     "NOT a live wet-lab instrument"):
            with self.subTest(term=term):
                self.assertIn(term, self.module)
        self.assertIn("wink/diagnosis/v0.1", self.module)

    def test_remote_source_strings_are_html_escaped(self):
        for term in ("escapeHtml(d.name)", "escapeHtml(d.detail)",
                     "escapeHtml(p.open_szl[keys[i]])",
                     "escapeHtml(c.label)", "escapeHtml(a.txt)"):
            with self.subTest(term=term):
                self.assertIn(term, self.module)
        self.assertIn("function escapeHtml(", self.module)

    def test_real_chromium_source_canary_proves_draw_commands_and_moving_pixels(self):
        browser = (ROOT / "scripts/wink_browser_smoke.py").read_text(encoding="utf-8")
        ci = (ROOT / ".github/workflows/static-browser-canary.yml").read_text(encoding="utf-8")
        for token in ("GL_DRAW_WITNESS", "drawElements", "drawArrays",
                      "webgl_draw_calls_before", "webgl_draw_calls_after",
                      "canvas_png_size_bytes", "canvas_pixel_change_observed",
                      "sha256(before_png).digest() != sha256(after_png).digest()"):
            with self.subTest(token=token):
                self.assertIn(token, browser)
        self.assertIn("playwright==1.64.0", ci)
        self.assertIn("python -B scripts/wink_browser_smoke.py --target local", ci)
        self.assertIn("SOURCE_AND_3D_CLIENT_BOOT_VERIFIED", ci)
        self.assertIn("independent_scientific_validation", ci)
        self.assertIn("contents: read", ci)
        self.assertNotIn("secrets.", ci)
        self.assertNotIn("upload_folder", ci)
        self.assertNotIn("request_hardware", ci)
        self.assertNotIn("publish_hf_static.py", ci)

    def test_public_3d_uses_proposed_stylized_not_verified_biology(self):
        self.assertIn("STYLIZED, NOT ANATOMICAL", self.html)
        self.assertIn("PROTOCOL v1.1 (NOT FROZEN)", self.html)
        self.assertIn("SCIENCE QUALIFICATION HOLD", self.module)
        self.assertIn("WITNESS STATE UNKNOWN", self.module)


if __name__ == "__main__":
    unittest.main()
