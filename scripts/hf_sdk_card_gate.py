"""Hugging Face Space SDK classification with strict metadata boundary.

huggingface_hub returns SpaceCardData, a mapping-like object that is NOT a
built-in dict. Do not reject that legitimate provider type, and do not
infer provider SDK from a default or app-level README text alone.
This helper never authenticates, writes, fetches, or changes provider state.
"""
from __future__ import annotations

from typing import Any


def observed_sdk(card_data: Any) -> str | None:
    """Only a recognized, explicitly reported provider card SDK is admissible."""
    get = getattr(card_data, "get", None)
    if not callable(get):
        return None
    try:
        value = get("sdk")
    except (TypeError, ValueError, KeyError, AttributeError):
        return None
    return value if type(value) is str and value in {"static", "docker"} else None
