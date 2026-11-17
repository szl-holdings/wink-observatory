"""Source-only A10 presentation overlay, with historical inputs preserved."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from backend.falsifiability import audit

ROOT = Path(__file__).resolve().parents[1]

class A10ConsumerTests(unittest.TestCase):
    def test_backend_reports_correction_without_mutating_receipt(self):
        held = json.loads((ROOT / 'data/receipts/v5-heldout.json').read_text())
        original = copy.deepcopy(held)
        result = audit(held)
        self.assertEqual(held, original)
        self.assertEqual(result['overall_admission'], 'HOLD')
        self.assertEqual(result['a10_interpretation_scope'], 'SOURCE_REVIEW_NOT_NEW_MEASUREMENT')
        self.assertIn('supersession-20261117', result['a10_interpretation_source'])
        self.assertIn('low-score cause unknown', ' '.join(result['warnings']))
        self.assertNotIn('measures letter-format, not accuracy', ' '.join(result['warnings']))

    def test_public_render_overlay_preserves_source(self):
        if not shutil.which('node'):
            self.skipTest('Node unavailable')
        html = (ROOT / 'frontend/index.html').read_text()
        module = html[html.index('var PUBLIC_DATASET ='):html.index('var lastApproved =')]
        paths = ['fleet/snapshot.json', 'witness/records.json', 'protocol/status.json',
                 'receipts/v5-heldout.json', 'receipts/v5-bench.json', 'receipts/a10-diagnosis.json']
        docs = [json.loads((ROOT / 'data' / p).read_text()) for p in paths]
        js = 'const assert = require("assert");\n' + 'const docs = '+json.dumps(docs)+';\n'
        js += 'var nodeMeshes = docs[0].groups; function sourceTime(x){return Date.parse(x);}\n' + module
        js += '''
const original = JSON.stringify(docs);
const out = validatedPublic({id: PUBLIC_DATASET, private:false, sha:'a'.repeat(40)}, docs);
assert.strictEqual(JSON.stringify(docs), original);
assert(out.protocol.open_szl['4'].includes('OPEN'));
const neutral = out.heldout.criteria.find(x => x.id === 'criterion_4_neutral');
assert(neutral.audit.txt.includes('low-score cause unknown'));
assert(neutral.audit.txt.includes('UNINTERPRETABLE'));
assert(!neutral.audit.txt.includes('not correctness'));
assert.strictEqual(out.sourceSha, 'a'.repeat(40));
'''
        result = subprocess.run(['node', '-e', js], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_baseline_and_readme_do_not_repeat_retracted_claim(self):
        for path in ('frontend/index.html', 'README.md', 'backend/falsifiability.py'):
            text = (ROOT / path).read_text()
            self.assertNotIn('letter-format, not correctness', text)
            self.assertNotIn('letter-format compliance, not correctness', text)
            self.assertIn('low-score cause unknown', text)
