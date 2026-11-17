"""Provider SDK gating: SpaceCardData is mapping-like, not a built-in dict.

No external network, credentials or resource mutation in this suite.
"""
from __future__ import annotations

import unittest
from scripts.hf_sdk_card_gate import observed_sdk


class SpaceCardDataLike:
    """Mimic the actual Hugging Face Hub SpaceCardData interface."""
    def __init__(self, sdk):
        self.sdk = sdk
    def get(self, key, default=None):
        return self.sdk if key == "sdk" else default


class BrokenCard:
    def get(self, key):
        raise ValueError("unavailable")


class SDKGateTests(unittest.TestCase):
    def test_actual_provider_card_shape_is_not_dict(self):
        card = SpaceCardDataLike("static")
        self.assertFalse(isinstance(card, dict))
        self.assertEqual(observed_sdk(card), "static")
        self.assertEqual(observed_sdk(SpaceCardDataLike("docker")), "docker")

    def test_dict_compatibility_not_removed(self):
        self.assertEqual(observed_sdk({"sdk": "static"}), "static")
        self.assertEqual(observed_sdk({"sdk": "docker"}), "docker")

    def test_unknown_provider_sdk_stays_denied(self):
        for value in (None, "", "main", "gradio", "legacy", 0, True, 2, ["docker"]):
            with self.subTest(value=value):
                self.assertIsNone(observed_sdk(SpaceCardDataLike(value)))

    def test_missing_and_bad_cards_fail_closed(self):
        for value in (None, object(), {}, [], BrokenCard(), {"not_sdk": "docker"}):
            with self.subTest(kind=type(value).__name__):
                self.assertIsNone(observed_sdk(value))


if __name__ == "__main__":
    unittest.main()
