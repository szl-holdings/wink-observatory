"""Zero-effect exact HF publishing admission tests, including SpaceCardData.

Runs without huggingface_hub, real tokens or network; the module under test
receives a fake Hugging Face API injected before import.
"""
from __future__ import annotations

import importlib.util
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/publish_hf_python.py"
SOURCE="b"*40
HF="a"*40
PUBLISHED="c"*40


class SpaceCardData:
    def __init__(self, sdk):
        self._sdk=sdk

    def get(self, field, default=None):
        return self._sdk if field == "sdk" else default


class FakeHub:
    instances=[]

    def __init__(self, token):
        assert token == "TEST_ONLY_NOT_A_REAL_CREDENTIAL"
        self.latest=HF
        self.before=SpaceCardData("static")
        self.call=None
        self.info_count=0
        self.__class__.instances.append(self)

    def space_info(self, repo):
        assert repo == "SZLHOLDINGS/wink-observatory"
        self.info_count+=1
        return SimpleNamespace(sha=self.latest, private=False,
                               card_data=self.before)

    def upload_folder(self, **kwargs):
        self.call=kwargs
        assert kwargs["parent_commit"]==HF
        assert kwargs["repo_type"]=="space"
        assert kwargs["revision"]=="main"
        assert kwargs["repo_id"]=="SZLHOLDINGS/wink-observatory"
        assert kwargs["folder_path"]=="dist/hf-space"
        assert not any(key in kwargs for key in ("delete_patterns","force"))
        self.latest=PUBLISHED
        return SimpleNamespace(oid=PUBLISHED)


def load():
    """No real Hugging Face client is importable or used by this test."""
    with patch.dict(sys.modules, {"huggingface_hub": SimpleNamespace(HfApi=FakeHub)}):
        spec=importlib.util.spec_from_file_location("_publisher_under_test",SCRIPT)
        assert spec and spec.loader
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class PublisherAdmissionTests(unittest.TestCase):
    def setUp(self):
        FakeHub.instances.clear()
        self.module=load()
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old=os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(lambda: os.chdir(self.old))
        folder=Path("dist/hf-space")
        folder.mkdir(parents=True)
        (folder/"Dockerfile").write_text("FROM scratch\n",encoding="utf-8")
        (folder/"SOURCE_REVISION").write_text(SOURCE+"\n",encoding="utf-8")
        self.env={
            "GITHUB_SHA":SOURCE,"EXPECTED_MAIN_SHA":SOURCE,
            "EXPECTED_HF_SHA":HF,"APPROVED_WINDOW":"true",
            "SDK_MIGRATION_APPROVED":"true","ROLLBACK_READY":"true",
            "HF_TOKEN":"TEST_ONLY_NOT_A_REAL_CREDENTIAL",
        }

    def permitted(self, **overrides):
        values={**self.env,**overrides}
        fake_ls=SimpleNamespace(returncode=0,
                                stdout=(SOURCE+"\trefs/heads/main\n").encode())
        with patch.dict(os.environ,values,clear=True), \
             patch.object(self.module.subprocess,"run",return_value=fake_ls) as command:
            return self.module.main()

    def test_real_space_card_data_shape_does_not_block_approved_publisher(self):
        # Keep synthetic publication notices out of the real CI release log.
        output=StringIO()
        with redirect_stdout(output):
            result=self.permitted()
        self.assertEqual(result,0)
        self.assertIn("PUBLISHED_UNVERIFIED_RUNTIME", output.getvalue())
        instance=FakeHub.instances[0]
        self.assertEqual(instance.call["parent_commit"],HF)
        self.assertEqual(instance.latest,PUBLISHED)
        self.assertEqual(instance.info_count,2)

    def test_owner_window_and_rollback_are_hard_holds(self):
        for change in ({"APPROVED_WINDOW":"false"},
                       {"SDK_MIGRATION_APPROVED":"false"},
                       {"ROLLBACK_READY":"false"},
                       {"HF_TOKEN":""},
                       {"EXPECTED_HF_SHA":"main"},
                       {"EXPECTED_MAIN_SHA":"d"*40}):
            with self.subTest(change=change):
                FakeHub.instances.clear()
                with self.assertRaises(SystemExit):
                    self.permitted(**change)
                self.assertEqual(FakeHub.instances,[])

    def test_malformed_or_missing_sdk_fails_without_provider_write(self):
        for sdk in ("legacy","",None,True):
            with self.subTest(sdk=sdk):
                FakeHub.instances.clear()
                original=FakeHub.space_info
                def changed(obj,repo):
                    info=original(obj,repo)
                    info.card_data=SpaceCardData(sdk)
                    return info
                with patch.object(FakeHub,"space_info",changed):
                    with self.assertRaisesRegex(SystemExit,"HF_SPACE_SDK_UNEXPECTED"):
                        self.permitted()
                self.assertIsNone(FakeHub.instances[0].call)

    def test_source_move_before_publication_holds(self):
        FakeHub.instances.clear()
        fake_ls=SimpleNamespace(returncode=0,
                                stdout=("d"*40+"\trefs/heads/main\n").encode())
        with patch.dict(os.environ,self.env,clear=True), \
             patch.object(self.module.subprocess,"run",return_value=fake_ls):
            with self.assertRaisesRegex(SystemExit,"PROTECTED_MAIN_MOVED"):
                self.module.main()
        self.assertEqual(FakeHub.instances,[])

    def test_hash_readback_mismatch_holds(self):
        old=FakeHub.space_info
        def after_wrong(obj,repo):
            info=old(obj,repo)
            if obj.info_count>1:
                info.sha="d"*40
            return info
        with patch.object(FakeHub,"space_info",after_wrong):
            with self.assertRaisesRegex(SystemExit,"HF_COMMIT_READBACK_MISMATCH"):
                self.permitted()


if __name__=="__main__":
    unittest.main()
