"""Offline tests for the reviewed public HF rollback source admission."""
from __future__ import annotations

from copy import deepcopy
import json
import tempfile
import unittest
from unittest.mock import patch

from scripts import wink_rollback_snapshot as r

SOURCE = "b" * 40
HF_SHA = "a" * 40


class RollbackSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.blobs = {
            ".gitattributes": b"*.bin filter=lfs\n",
            "README.md": b"---\nsdk: static\n---\n",
            "index.html": b"<!doctype html>\n<html>evidence</html>\n",
            "style.css": b"body {color: white}\n",
        }
        self.info = {"id": r.SPACE, "sha": HF_SHA, "private": False,
                     "cardData": {"sdk": "static"}}
        self.tree = [{"path": x, "type": "file", "size": len(y)}
                     for x, y in self.blobs.items()]
        self.calls = []

    def serve(self, url):
        self.calls.append(url)
        prefix = "https://huggingface.co"
        if url == prefix + "/api/spaces/" + r.SPACE:
            return json.dumps(self.info).encode("utf-8")
        if url == prefix + "/api/spaces/" + r.SPACE + "/tree/" + HF_SHA + "?recursive=true":
            return json.dumps(self.tree).encode("utf-8")
        for name, data in self.blobs.items():
            if url == f"{prefix}/spaces/{r.SPACE}/raw/{HF_SHA}/{name}":
                return data
        raise AssertionError("unreviewed source URL " + url)

    def observe(self):
        return r.capture(HF_SHA, SOURCE, read=self.serve,
                         mirror=lambda commit: self.blobs["index.html"])

    def test_complete_static_tree_and_git_blob_are_real_bytes(self):
        manifest, data = self.observe()
        self.assertEqual(set(data), set(r.FILES))
        self.assertEqual(manifest["raw_source_count"], 4)
        self.assertTrue(manifest["complete_hf_tree"])
        self.assertTrue(manifest["github_index_hf_byte_parity"])
        self.assertEqual(manifest["hf_expected_revision"], HF_SHA)
        self.assertEqual(manifest["source_main_revision"], SOURCE)
        self.assertFalse(manifest["provider_writes"])
        self.assertFalse(manifest["rollback_executed"])
        self.assertFalse(manifest["owner_authority_verified"])
        self.assertFalse(manifest["independent_runtime_verified"])
        self.assertFalse(manifest["training_started"])
        self.assertEqual(len(self.calls), 6)
        self.assertTrue(all(x.startswith("https://huggingface.co/") for x in self.calls))

    def test_windows_crlf_checkout_is_not_git_blob_parity(self):
        raw=self.blobs["index.html"]
        altered=raw.replace(b"\n", b"\r\n")
        with self.assertRaisesRegex(r.SnapshotUnavailable, "MIRROR_NOT_BYTE_PARITY"):
            r.capture(HF_SHA, SOURCE, read=self.serve, mirror=lambda commit: altered)

    def test_source_revision_change_fail_closed(self):
        self.info["sha"]="c"*40
        with self.assertRaisesRegex(r.SnapshotUnavailable, "REVISION_MOVED"):
            self.observe()

    def test_private_or_wrong_space_denied(self):
        self.info["private"]=True
        with self.assertRaisesRegex(r.SnapshotUnavailable, "PRIVATE"):
            self.observe()
        self.info["private"]=False
        self.info["id"]="someone/else"
        with self.assertRaises(r.SnapshotUnavailable):
            self.observe()

    def test_sdk_would_have_changed_and_must_require_review(self):
        self.info["cardData"]["sdk"]="docker"
        with self.assertRaisesRegex(r.SnapshotUnavailable, "STATIC_SDK"):
            self.observe()

    def test_unexpected_new_repo_file_refuses_incomplete_backup(self):
        self.tree.append({"path":"new-private-note.txt","type":"file","size":3})
        with self.assertRaisesRegex(r.SnapshotUnavailable, "UNREVIEWED_FILE"):
            self.observe()

    def test_missing_css_rejects_rollback_completeness(self):
        self.tree=[row for row in self.tree if row["path"]!="style.css"]
        with self.assertRaisesRegex(r.SnapshotUnavailable, "INCOMPLETE"):
            self.observe()

    def test_lfs_entry_and_size_mismatch_not_trusted(self):
        self.tree[0]["lfs"]={"oid":"a"*64,"size":12}
        with self.assertRaisesRegex(r.SnapshotUnavailable, "LFS"):
            self.observe()
        self.tree[0].pop("lfs")
        self.tree[0]["size"]+=1
        with self.assertRaisesRegex(r.SnapshotUnavailable, "SIZE_MISMATCH"):
            self.observe()

    def test_nested_symlinks_or_directories_refused(self):
        self.tree[0]["type"]="directory"
        with self.assertRaisesRegex(r.SnapshotUnavailable, "UNEXPECTED_ENTRY"):
            self.observe()

    def test_invalid_sha_and_missing_source_blob_refused(self):
        for hf,source in (("main",SOURCE),(HF_SHA,"notasha"),(HF_SHA,"g"*40)):
            with self.subTest(hf=hf,source=source), self.assertRaises(r.SnapshotUnavailable):
                r.capture(hf,source,read=self.serve,mirror=lambda _: self.blobs["index.html"])
        with self.assertRaisesRegex(r.SnapshotUnavailable, "MIRROR_NOT_BYTE_PARITY"):
            r.capture(HF_SHA,SOURCE,read=self.serve,mirror=lambda _: b"")

    def test_duplicate_json_and_nonfinite_refused(self):
        with self.assertRaisesRegex(r.SnapshotUnavailable, "DUPLICATE_JSON"):
            r.parse_json(b'{"sdk":"static","sdk":"docker"}')
        with self.assertRaisesRegex(r.SnapshotUnavailable, "NONFINITE"):
            r.parse_json(b'{"size":NaN}')

    def test_no_arbitrary_host_or_tokened_url(self):
        with self.assertRaisesRegex(r.SnapshotUnavailable, "SOURCE_HOST"):
            r.fetch("http://127.0.0.1:8000/admin")


if __name__ == "__main__":
    unittest.main()
