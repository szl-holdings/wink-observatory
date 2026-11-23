"""WINK schema gate must reject ambiguous JSON before receipt admission."""
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from backend import validate as gate


class StrictSchemaJsonTests(unittest.TestCase):
    def load_sample(self, raw):
        with TemporaryDirectory() as directory:
            Path(directory, "sample.json").write_text(raw, encoding="utf-8")
            with patch.object(gate, "BASE", Path(directory)), redirect_stdout(io.StringIO()):
                return gate.load("sample.json")

    def test_duplicate_top_level_key_rejected(self):
        with self.assertRaises(SystemExit):
            self.load_sample('{"status":"running","status":"stopped"}')

    def test_duplicate_nested_key_rejected(self):
        with self.assertRaises(SystemExit):
            self.load_sample('{"group":{"active":1,"active":0}}')

    def test_nonstandard_constants_rejected(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token), self.assertRaises(SystemExit):
                self.load_sample('{"score":' + token + '}')

    def test_exponent_overflow_rejected(self):
        with self.assertRaises(SystemExit):
            self.load_sample('{"score":1e999}')

    def test_finite_control_accepted(self):
        self.assertEqual(self.load_sample('{"score":1.25,"group":{"active":2}}'),
                         {"score":1.25,"group":{"active":2}})


if __name__ == "__main__":
    unittest.main()
