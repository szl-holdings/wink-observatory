"""Guard the sole HF publisher and independent read-only release witness."""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / ".github/workflows/publish-hf-python.yml"
READBACK = ROOT / ".github/workflows/release-readback.yml"
PUB = ROOT / "scripts/publish_hf_python.py"
PROBE = ROOT / "scripts/wink_release_probe.py"


class ReleaseTopologyTests(unittest.TestCase):
    def test_publisher_is_manual_main_only_with_independent_owner_environment(self):
        workflow = OWNER.read_text(encoding="utf-8")
        header = workflow.split("permissions:")[0]
        self.assertIn("workflow_dispatch:", header)
        self.assertNotIn("schedule:", header)
        self.assertNotIn("push:", header)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("name: hf-wink-production", workflow)
        self.assertIn('expected_main_sha:', workflow)
        self.assertIn('expected_hf_sha:', workflow)
        for name in ("open_deploy_window", "sdk_migration_approved", "rollback_ready"):
            self.assertIn(name + ":", workflow)
            self.assertIn(name.upper() if name.upper() in workflow else name, workflow)
        self.assertIn("python -I -B scripts/publish_hf_python.py", workflow)
        self.assertIn("python -I -B scripts/wink_release_probe.py", workflow)
        self.assertIn("--strict-transport", workflow)

    def test_before_publisher_has_complete_immutable_static_rollback_archive(self):
        workflow = OWNER.read_text(encoding="utf-8")
        preflight = workflow.index("scripts/wink_rollback_snapshot.py")
        archive = workflow.index("name: wink-public-static-rollback-")
        publisher = workflow.index("python -I -B scripts/publish_hf_python.py")
        self.assertLess(preflight, archive)
        self.assertLess(archive, publisher)
        self.assertIn("if-no-files-found: error", workflow)
        self.assertIn("include-hidden-files: true", workflow)
        self.assertIn("--source-sha", workflow)
        self.assertIn("--hf-sha", workflow)
        source = (ROOT / "scripts/wink_rollback_snapshot.py").read_text(encoding="utf-8")
        self.assertNotIn("HF_TOKEN", source)
        self.assertNotIn("upload_folder", source)
        self.assertNotIn("request_hardware", source)
        self.assertIn("PUBLIC_HF_TREE_INCOMPLETE_OR_UNREVIEWED", source)
        self.assertIn("GITHUB_STATIC_MIRROR_NOT_BYTE_PARITY", source)

    def test_publisher_enforces_provider_cas_main_lease_and_no_direct_gpu_action(self):
        source = PUB.read_text(encoding="utf-8")
        self.assertIn("EXPECTED_MAIN_SHA", source)
        self.assertIn("EXPECTED_HF_SHA", source)
        self.assertIn("parent_commit=expected_hf", source)
        self.assertIn("MAIN_MOVED_BEFORE_PROVIDER_COMMIT", source)
        self.assertIn("PROTECTED_MAIN_MOVED_OR_UNAVAILABLE", source)
        self.assertNotIn("delete_patterns", source.split("result=api.upload_folder(", 1)[1])
        self.assertNotIn("request_hardware", source)
        self.assertNotIn("run_job", source)
        self.assertNotIn("HF_TOKEN", PROBE.read_text(encoding="utf-8"))

    def test_scheduled_release_witness_is_read_only_no_deploy_or_mail(self):
        source = READBACK.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("schedule:", source)
        self.assertIn("branches: [main]", source)
        self.assertIn("permissions:\n  contents: read", source)
        self.assertIn("scripts/wink_release_probe.py --output", source)
        self.assertNotIn("HF_TOKEN", source)
        self.assertNotIn("secrets.", source)
        self.assertNotIn("scripts/publish_hf_python.py", source)
        self.assertNotIn("upload_folder", source)
        self.assertNotIn("gh issue create", source)
        self.assertNotIn("gh workflow run", source)

    def test_static_html_repair_is_owner_manual_single_writer_and_old_source_pinned(self):
        static = (ROOT / ".github/workflows/publish-hf-static-repair.yml").read_text(encoding="utf-8")
        docker = OWNER.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", static)
        self.assertNotIn("schedule:", static)
        self.assertNotIn("\n  push:", static)
        self.assertIn("name: hf-wink-production", static)
        self.assertIn("name: hf-wink-production", docker)
        self.assertIn("group: wink-hf-single-writer", static)
        self.assertIn("group: wink-hf-single-writer", docker)
        self.assertIn("fetch-depth: 0", static)
        self.assertIn("fetch-depth: 0", docker)
        self.assertIn("github.ref == 'refs/heads/main'", static)
        self.assertIn("expected_main_sha:", static)
        self.assertIn("expected_hf_sha:", static)
        self.assertIn("approved_maintenance_window:", static)
        self.assertIn("static_repair_approved:", static)
        self.assertIn("rollback_ready:", static)
        self.assertIn("b118d2dc9246df478ba5d5a96cfc6c4b783eb148", static)
        self.assertIn("41d90e0646b84f282e9461279eb54325d5897cf7", static)
        self.assertIn("include-hidden-files: true", static)
        self.assertIn("if-no-files-found: error", static)
        archived = static.index("name: wink-original-public-static-rollback-")
        write = static.index("python -I -B scripts/publish_hf_static.py")
        self.assertLess(archived, write)
        self.assertIn("HF_TOKEN: ${{ secrets.HF_TOKEN }}", static)
        self.assertIn("playwright==1.64.0", static)
        self.assertIn("python -B scripts/wink_browser_smoke.py --target public", static)
        self.assertLess(static.index("python -I -B scripts/publish_hf_static.py"),
                        static.index("python -B scripts/wink_browser_smoke.py --target public"))
        self.assertIn("permissions:\n  contents: read", static)
        self.assertNotIn("upload_folder", static)
        self.assertNotIn("request_hardware", static)

    def test_static_publisher_writes_only_index_and_requires_hf_parent_lease(self):
        source = (ROOT / "scripts/publish_hf_static.py").read_text(encoding="utf-8")
        self.assertIn('path_in_repo="index.html"', source)
        self.assertIn("parent_commit=old_hf", source)
        self.assertIn('observed_sdk(original.card_data) == "static"', source)
        self.assertIn('old_hf == ORIGINAL_HF', source)
        self.assertIn('STATIC_REPAIR_APPROVED', source)
        self.assertIn('APPROVED_WINDOW', source)
        self.assertIn('ROLLBACK_READY', source)
        self.assertNotIn("delete_patterns", source.split("result = api.upload_file(", 1)[1])
        self.assertNotIn("request_hardware", source)
        self.assertNotIn("upload_folder", source)
        self.assertNotIn("run_job", source)

    def test_existing_source_validation_still_guards_main_and_prs(self):
        source = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request", source)
        self.assertIn("backend/validate.py", source)
        fullstack = (ROOT / ".github/workflows/python-fullstack.yml").read_text(encoding="utf-8")
        self.assertIn("test_*.py", fullstack)
        self.assertIn("client.get(\"/\", follow_redirects=False)", fullstack)
        self.assertIn("public-source-readback:", fullstack)
        self.assertIn("container-smoke:", fullstack)
        self.assertIn("docker build --pull", fullstack)
        self.assertIn("DOCKER_CANDIDATE_ROOT_HTTP_200", fullstack)
        self.assertIn("NO_HF_DEPLOYMENT_NO_SCIENTIFIC_OR_INDEPENDENT_RUNTIME_ADMISSION", fullstack)


if __name__ == "__main__":
    unittest.main()
