"""Offline CAS-plan and archive tamper regressions; never restores a provider."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import wink_static_rollback_plan as r
from scripts.wink_rollback_snapshot import SnapshotUnavailable


class RollbackPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.old, self.current = 'a' * 40, 'b' * 40
        self.blobs = {n: (n + '\n').encode() for n in r.FILES}
        self.manifest = dict(schema='wink.public-static-rollback-readback/v1',
                             hf_repo=r.SPACE, source_repo=r.SOURCE, hf_sdk='static',
                             complete_hf_tree=True, public_repo_only=True,
                             hf_expected_revision=self.old,
                             sha256={n: sha256(b).hexdigest() for n,b in self.blobs.items()},
                             sizes={n: len(b) for n,b in self.blobs.items()})
        for n,b in self.blobs.items(): (self.root / n).write_bytes(b)
        self.write_manifest()
        self.info = dict(id=r.SPACE, private=False, sha=self.current, cardData={'sdk':'static'})
        self.tree = [dict(type='file', path=n) for n in r.FILES]
        self.changed = None

    def write_manifest(self):
        raw = json.dumps(self.manifest).encode()
        (self.root / 'manifest.json').write_bytes(raw)
        self.digest = sha256(raw).hexdigest()

    def read(self, url):
        if '/api/spaces/' in url:
            return json.dumps(self.tree if '/tree/' in url else self.info).encode()
        name = url.rsplit('/',1)[-1]
        if f'/raw/{self.current}/' in url and name == self.changed: return b'changed'
        return self.blobs[name]

    def plan(self): return r.plan(self.root, self.digest, self.current, read=self.read)

    def test_valid_plan_binds_cas_and_has_no_effect_authority(self):
        p = self.plan()
        self.assertEqual(p['parent_commit'], self.current)
        self.assertEqual(p['path_in_repo'], 'index.html')
        self.assertFalse(p['provider_writes'])
        self.assertFalse(p['owner_approval_verified'])
        self.assertFalse(p['live_restore_tested'])

    def test_tampered_manifest(self):
        (self.root/'manifest.json').write_bytes(b'{}')
        with self.assertRaisesRegex(SnapshotUnavailable, 'DIGEST'): self.plan()

    def test_tampered_blob(self):
        (self.root/'style.css').write_bytes(b'changed')
        with self.assertRaisesRegex(SnapshotUnavailable, 'BYTES_MISMATCH'): self.plan()

    def test_moved_parent(self):
        self.info['sha']='c'*40
        with self.assertRaisesRegex(SnapshotUnavailable, 'MOVED'): self.plan()

    def test_sdk_or_privacy_change(self):
        for key,value in [('private',True),('cardData',{'sdk':'docker'})]:
            original=self.info[key]; self.info[key]=value
            with self.assertRaises(SnapshotUnavailable): self.plan()
            self.info[key]=original

    def test_extra_tree_entry(self):
        self.tree.append(dict(type='file',path='extra.txt'))
        with self.assertRaisesRegex(SnapshotUnavailable, 'TREE_CHANGED'): self.plan()

    def test_duplicate_tree_entry(self):
        self.tree[-1]=self.tree[0]
        with self.assertRaisesRegex(SnapshotUnavailable, 'TREE_CHANGED'): self.plan()

    def test_non_html_drift(self):
        self.changed='README.md'
        with self.assertRaisesRegex(SnapshotUnavailable, 'NON_HTML'): self.plan()

    def test_extra_local_file(self):
        (self.root/'extra').write_text('x')
        with self.assertRaisesRegex(SnapshotUnavailable, 'TREE_NOT_EXACT'): self.plan()

    def test_symlink_file(self):
        f=self.root/'style.css'; f.unlink()
        try:
            f.symlink_to(self.root/'index.html')
        except OSError as exc:
            if getattr(exc, 'winerror', None) == 1314:
                self.skipTest('Windows account lacks symlink privilege; rejection tested separately')
            raise
        with self.assertRaisesRegex(SnapshotUnavailable, 'NOT_REGULAR'): self.plan()

    def test_symlink_rejection_without_os_privilege(self):
        with patch.object(Path, 'is_symlink', return_value=True):
            with self.assertRaisesRegex(SnapshotUnavailable, 'NOT_REGULAR'):
                r.bounded_file(self.root/'style.css')

    def test_bool_size(self):
        self.manifest['sizes']['index.html']=True; self.write_manifest()
        with self.assertRaisesRegex(SnapshotUnavailable, 'BYTES_MISMATCH'): self.plan()

    def test_same_revision(self):
        self.current=self.old
        with self.assertRaisesRegex(SnapshotUnavailable, 'ALREADY'): self.plan()

    def test_immutable_readback_mismatch(self):
        self.blobs['style.css']=b'wrong provider bytes'
        with self.assertRaisesRegex(SnapshotUnavailable, 'READBACK_MISMATCH'): self.plan()

if __name__ == '__main__': unittest.main()
