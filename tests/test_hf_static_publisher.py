"""No-network, zero-secret tests of static WINK repair provider admission."""
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "b" * 40
PREVIOUS = "c" * 40
OLD = "01e1021e7e1d80a0d4754fa01ca84282cb854c85"
NEW = "a" * 40
FILE = b"<!doctype html>\n" + b"X" * 30000 + b"</html>\n"


class Card:
    def __init__(self, name):
        self.name = name

    def get(self, key):
        return self.name if key == "sdk" else None


class FakeHub:
    instances = []
    private = False
    stage_sdk = "static"
    start_sha = OLD
    result_sha = NEW

    def __init__(self, token):
        assert token == "NON_SECRET_TEST_SENTINEL"
        self.sha = self.start_sha
        self.call = None
        self.__class__.instances.append(self)

    def space_info(self, name):
        assert name == "SZLHOLDINGS/wink-observatory"
        return SimpleNamespace(sha=self.sha, card_data=Card(self.stage_sdk),
                               private=self.private)

    def upload_file(self, **kw):
        assert self.call is None
        self.call = kw
        self.sha = self.result_sha
        return SimpleNamespace(oid=self.result_sha)


def load():
    with patch.dict(sys.modules, {"huggingface_hub": SimpleNamespace(HfApi=FakeHub)}):
        spec = importlib.util.spec_from_file_location("_wink_static_publisher", ROOT / "scripts/publish_hf_static.py")
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


class StaticPublisherTests(unittest.TestCase):
    def setUp(self):
        FakeHub.instances.clear()
        FakeHub.private = False
        FakeHub.stage_sdk = "static"
        FakeHub.start_sha = OLD
        FakeHub.result_sha = NEW
        self.module = load()
        self.env = {
            "GITHUB_SHA": SOURCE,
            "EXPECTED_MAIN_SHA": SOURCE,
            "EXPECTED_HF_SHA": OLD,
            "EXPECTED_DEPLOYED_SOURCE_SHA": PREVIOUS,
            "APPROVED_WINDOW": "true",
            "STATIC_REPAIR_APPROVED": "true",
            "ROLLBACK_READY": "true",
            "HF_TOKEN": "NON_SECRET_TEST_SENTINEL",
        }

    def run_approved(self, extra=None, source=FILE, readback=FILE,
                     prior_git=FILE, prior_http=FILE):
        env = {**self.env, **(extra or {})}
        out = StringIO()
        def provider_readback(sha):
            return prior_http if sha == env["EXPECTED_HF_SHA"] else readback
        with patch.dict(os.environ, env, clear=True), \
             patch.object(self.module, "read_main_lease") as lease, \
             patch.object(self.module, "read_source_bytes", return_value=source), \
             patch.object(self.module, "verify_previous_ancestor") as ancestry, \
             patch.object(self.module, "prior_git_blob", return_value=prior_git), \
             patch.object(self.module, "public_readback", side_effect=provider_readback) as rd, \
             redirect_stdout(out):
            result = self.module.main()
        ancestry.assert_called_once_with(env["EXPECTED_DEPLOYED_SOURCE_SHA"], SOURCE)
        return result, out.getvalue(), lease, rd

    def test_approved_exact_html_repair_only_preserves_sdk_and_source(self):
        status, log, lease, rd = self.run_approved()
        self.assertEqual(status, 0)
        self.assertIn("STATIC_HTML_SOURCE_BYTES_VERIFIED_RUNTIME_NOT_INDEPENDENTLY_PROVED", log)
        self.assertEqual(lease.call_count, 2)
        self.assertEqual(rd.call_count, 2)
        rd.assert_any_call(OLD)
        rd.assert_any_call(NEW)
        api = FakeHub.instances[0]
        self.assertEqual(api.sha, NEW)
        self.assertEqual(api.call["repo_type"], "space")
        self.assertEqual(api.call["path_in_repo"], "index.html")
        self.assertEqual(api.call["parent_commit"], OLD)
        self.assertEqual(api.call["revision"], "main")
        self.assertNotIn("delete_patterns", api.call)
        self.assertNotIn("hardware", api.call)
        self.assertNotIn("README.md", str(api.call))

    def test_no_input_may_fake_a_maintenance_window_or_sdk_approval(self):
        cases = (
            {"APPROVED_WINDOW": "false"},
            {"STATIC_REPAIR_APPROVED": "false"},
            {"ROLLBACK_READY": "false"},
            {"HF_TOKEN": ""},
            {"EXPECTED_HF_SHA": "main"},
            {"EXPECTED_DEPLOYED_SOURCE_SHA": "main"},
            {"EXPECTED_DEPLOYED_SOURCE_SHA": SOURCE},
            {"EXPECTED_DEPLOYED_SOURCE_SHA": ""},
            {"EXPECTED_MAIN_SHA": "c" * 40},
        )
        for edit in cases:
            with self.subTest(edit=edit):
                FakeHub.instances.clear()
                with self.assertRaises(self.module.AdmissionHold):
                    self.run_approved(edit)
                self.assertEqual(FakeHub.instances, [])

    def test_private_or_moved_provider_source_is_not_published(self):
        for private, sdk, orig_sha in ((True, "static", OLD),
                                       (False, "docker", OLD),
                                       (False, "legacy", OLD),
                                       (False, "static", "d" * 40)):
            with self.subTest(private=private, sdk=sdk, sha=orig_sha):
                FakeHub.instances.clear()
                FakeHub.private = private
                FakeHub.stage_sdk = sdk
                FakeHub.start_sha = orig_sha
                with self.assertRaises(self.module.AdmissionHold):
                    self.run_approved()
                self.assertIsNone(FakeHub.instances[0].call)

    def test_postcommit_raw_bytes_mismatch_is_a_hard_failure(self):
        with self.assertRaisesRegex(self.module.AdmissionHold, "HF_RAW_HTML_BYTES_NOT_EXACT_SOURCE"):
            self.run_approved(readback=b"NOT_THE_EXPECTED_REPAIRED_HTML")
        # The file has already been committed; we preserve and report its SHA
        # rather than pretending the write was rolled back.
        self.assertIsNotNone(FakeHub.instances[0].call)

    def test_repeat_static_update_uses_actual_hf_and_previous_protected_source(self):
        # Production's first release successfully committed exact raw HTML at
        # HF 41d90e..., but failed its client boot due to evolving dataset.
        latest = "41d90e0646b84f282e9461279eb54325d5897cf7"
        previous = "b118d2dc9246df478ba5d5a96cfc6c4b783eb148"
        FakeHub.start_sha = latest
        status, out, leases, readback = self.run_approved({
            "EXPECTED_HF_SHA": latest,
            "EXPECTED_DEPLOYED_SOURCE_SHA": previous,
        })
        self.assertEqual(status, 0)
        self.assertEqual(FakeHub.instances[0].call["parent_commit"], latest)
        readback.assert_any_call(latest)
        readback.assert_any_call(NEW)
        self.assertEqual(leases.call_count, 2)

    def test_old_public_source_byte_mismatch_blocks_any_write(self):
        with self.assertRaisesRegex(
            self.module.AdmissionHold,
            "PUBLIC_HF_PREDECESSOR_NOT_EXACT_GITHUB_SOURCE",
        ):
            self.run_approved(prior_git=b"Y" * len(FILE), prior_http=FILE)
        self.assertIsNone(FakeHub.instances[0].call)

    def test_wrong_valid_hf_revision_still_blocks_provider_write(self):
        with self.assertRaisesRegex(
            self.module.AdmissionHold, "HF_STATIC_SOURCE_MOVED_OR_PRIVATE",
        ):
            self.run_approved({"EXPECTED_HF_SHA": "d" * 40})
        self.assertIsNone(FakeHub.instances[0].call)

    def test_protected_history_ancestry_is_not_bypassed(self):
        with patch.object(self.module.subprocess, "run",
                          return_value=SimpleNamespace(returncode=1)):
            with self.assertRaisesRegex(
                self.module.AdmissionHold, "PREVIOUS_STATIC_SOURCE_NOT_PROTECTED_ANCESTOR",
            ):
                self.module.verify_previous_ancestor(PREVIOUS, SOURCE)

    def test_no_arbitrary_client_revision_accepted(self):
        with self.assertRaisesRegex(self.module.AdmissionHold, "PROVIDER_SHA_UNAVAILABLE"):
            self.module.public_readback("main")
        with self.assertRaisesRegex(self.module.AdmissionHold, "PROVIDER_SHA_UNAVAILABLE"):
            self.module.public_readback("z" * 40)

    def test_release_has_two_discrete_git_leases_not_one(self):
        _, _, leases, _ = self.run_approved()
        self.assertEqual(leases.call_count, 2)
        self.assertEqual(leases.call_args.args[0], SOURCE)


if __name__ == "__main__":
    unittest.main()
