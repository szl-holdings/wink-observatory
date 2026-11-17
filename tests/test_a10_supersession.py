"""Offline regression checks of the exact archived neutral scorer excerpt.

These are deterministic scorer semantics checks, not a model/GPU rerun.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / 'data' / 'receipts'

class A10SupersessionTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((RECEIPTS / 'a10-diagnosis-supersession-20261117.json').read_text())

    def score(self, output, answer=0):
        namespace = {'re': re, 'NEUTRAL_QA': [('Question', ['First', 'Second', 'Third', 'Fourth'], answer)],
                     'generate': lambda model, tok, body, limit: output}
        exec(compile(self.record['evidence']['neutral_acc_source_excerpt'], '<archived neutral_acc>', 'exec'), namespace)
        return namespace['neutral_acc'](None, None)

    def test_original_diagnosis_is_preserved_byte_exact(self):
        self.assertEqual(hashlib.sha256((RECEIPTS / 'a10-diagnosis.json').read_bytes()).hexdigest(), self.record['supersedes']['sha256'])

    def test_historical_receipt_checkout_preserves_exact_bytes_cross_platform(self):
        # Without explicit eol=lf, core.autocrlf converts LF to CRLF on Windows,
        # making this byte-exact historical receipt appear corrupted.
        lines = (ROOT / '.gitattributes').read_text(encoding='utf-8').splitlines()
        self.assertIn('data/receipts/a10-diagnosis.json text eol=lf', lines)
        self.assertIn('data/receipts/a10-diagnosis-supersession-20261117.json text eol=lf', lines)

    def test_lowercase_correct_option_scores(self):
        self.assertEqual(self.score('a'), (1.0, 1))

    def test_well_formatted_wrong_option_fails(self):
        self.assertEqual(self.score('B'), (0.0, 0))

    def test_verbose_correct_option_can_score(self):
        self.assertEqual(self.score('Answer: a'), (1.0, 1))

    def test_content_without_option_does_not_score(self):
        self.assertEqual(self.score('First'), (0.0, 0))

    def test_first_standalone_option_wins(self):
        self.assertEqual(self.score('B then A'), (0.0, 0))

    def test_no_causal_or_runtime_upgrade(self):
        self.assertEqual(self.record['replacement']['cause_of_low_observation'], 'UNKNOWN_WITHOUT_PER_ITEM_OUTPUTS')
        self.assertEqual(self.record['replacement']['preservation_verdict'], 'UNINTERPRETABLE')
        self.assertTrue(all(value is False for value in self.record['limits'].values()))

    def test_neutral_floor_cannot_fail(self):
        floor = self.record['replacement']['criterion_floor']
        self.assertEqual(floor, 0.05 - 0.10)
        self.assertTrue(all(k / 20 >= floor for k in range(21)))

if __name__ == '__main__':
    unittest.main()
