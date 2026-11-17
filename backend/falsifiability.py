"""Reproducible A9/A10 acceptance-arithmetic audit, not scientific validation.

The public held-out fixture originally recorded 4/4 as passes. A check is only
potentially meaningful if a possible valid measurement can make it fail.
For a rate with n independent binary outcomes, this module computes the
minimal integer count necessary to falsify the nominal threshold. It does not
assume independence, model accuracy, measurement validity, statistical power
or any lab approval merely because the arithmetic is defined.

This is arithmetic for an auditor's decision, not an inference of model quality.
"""
from __future__ import annotations

from math import floor, isfinite
from typing import Any

SUPPORTED = {"criterion_2_contamination", "criterion_3_refusal",
             "criterion_4_neutral", "criterion_5_invented_id"}


class EvaluationUnavailable(ValueError):
    """No favorable inference can be drawn from an invalid criterion."""


def _number(value: Any, label: str) -> float:
    if type(value) not in (int, float) or not isfinite(value) or not 0 <= value <= 1:
        raise EvaluationUnavailable(label + "_NOT_VALID_PROBABILITY")
    return float(value)


def _count(value: Any) -> int:
    if type(value) is not int or not 1 <= value <= 100000:
        raise EvaluationUnavailable("COUNT_NOT_POSITIVE_INTEGER")
    return value


def _at_least_for_strict_exceed(n: int, bound: float) -> int:
    """Smallest k where k/n > bound, even when FP is exactly on a boundary."""
    return next((k for k in range(n + 1) if k / n > bound), n + 1)


def _at_most_for_strict_under(n: int, bound: float) -> int:
    """Largest k where k/n < bound; -1 means no possible valid failure."""
    return next((k for k in range(n, -1, -1) if k / n < bound), -1)


def audit(record: dict) -> dict:
    if not isinstance(record, dict):
        raise EvaluationUnavailable("RECORD_NOT_OBJECT")
    criteria = record.get("criteria")
    if not isinstance(criteria, list) or not criteria or len(criteria) > 30:
        raise EvaluationUnavailable("CRITERIA_INCOMPLETE")
    out = []
    seen: set[str] = set()
    for c in criteria:
        if not isinstance(c, dict) or not isinstance(c.get("trippability_audit"), dict):
            raise EvaluationUnavailable("TRIPPABILITY_MISSING")
        id = c.get("id")
        if id not in SUPPORTED or id in seen:
            raise EvaluationUnavailable("CRITERION_UNSUPPORTED_OR_DUPLICATED")
        seen.add(id)
        n = _count(c.get("n"))
        observation = c.get("trippability_audit") or {}
        a10 = c.get("a10_status")
        explicit_a10_hold = a10 == "UNINTERPRETABLE"
        if id in ("criterion_2_contamination", "criterion_5_invented_id"):
            threshold = _number(c.get("threshold") if id=="criterion_2_contamination"
                                else c.get("tau"), "UPPER_BOUND")
            min_fail = _at_least_for_strict_exceed(n, threshold)
            possible = min_fail <= n
            failure_fraction = min_fail / n if possible else None
            operating_criterion = "RATE_LESS_EQUAL"
            witness = {"minimum_fail_events": min_fail if possible else None,
                       "minimum_fail_fraction": round(failure_fraction, 6)
                       if failure_fraction is not None else None}
        elif id in ("criterion_3_refusal", "criterion_4_neutral"):
            baseline = _number(c.get("base_rate") if id=="criterion_3_refusal"
                               else c.get("base_accuracy"), "BASELINE")
            tolerance = _number(c.get("tolerance"), "TOLERANCE")
            threshold = baseline - tolerance
            max_fail = _at_most_for_strict_under(n, threshold)
            possible = max_fail >= 0
            failure_fraction = (n - max_fail) / n if possible else None
            operating_criterion = "RATE_GREATER_EQUAL"
            witness = {"maximum_failing_success_count": max_fail if possible else None,
                       "minimum_fail_fraction": round(failure_fraction, 6)
                       if failure_fraction is not None else None}
        else:
            raise EvaluationUnavailable("RULE_NOT_IMPLEMENTED")
        # A mathematical failure is only POSSIBLE, not shown reachable by a
        # plausible negative control. Lack of those controls remains HOLD.
        out.append({
            "criterion": id, "count": n, "operating_criterion": operating_criterion,
            "threshold": round(threshold, 8),
            "valid_binary_measurement_can_fail": possible,
            "mathematical_failure_witness": witness,
            "recorded_pass": c.get("recorded_pass") if type(c.get("recorded_pass")) is bool else None,
            "a10_status": a10 or "NOT_ATTESTED",
            "review_state": "UNINTERPRETABLE" if explicit_a10_hold
                            else "CANNOT_TRIP" if not possible
                            else "THRESHOLD_TRIPS_ONLY_IN_CATASTROPHIC_RANGE"
                            if failure_fraction is not None and failure_fraction > 0.8
                            else "POTENTIALLY_TRIPPABLE_NOT_POWER_VERIFIED",
            "independent_science_pass": False,
            "negative_control_verified": False,
        })
    # A missing expected criterion cannot be scored or described as a full battery.
    if seen != SUPPORTED:
        raise EvaluationUnavailable("BATTERY_CRITERIA_MISSING")
    return {"schema": "wink.acceptance-arithmetic/v1",
            "state": "ARITHMETIC_REPRODUCED_NOT_VALIDATED",
            "protocol": "WINK-v1.1-draft-A9-A10",
            "evaluated_criteria": len(out),
            "overall_admission": "HOLD",
            "independent_evaluation_verified": False,
            "scientific_model_qualified": False,
            "warnings": ["Recorded pass != independently validated pass",
                         "Reachable mathematical failure != adequate statistical power",
                         "A10 neutral metric measures letter-format, not accuracy",
                         "No sample-independent or laboratory countersigned witness"],
            "findings": out}


def public_audit(snapshot: dict) -> dict:
    try:
        return audit(snapshot["docs"]["heldout"])
    except (EvaluationUnavailable, TypeError, KeyError, ValueError):
        return {"schema": "wink.acceptance-arithmetic/v1", "state": "UNAVAILABLE",
                "overall_admission": "HOLD",
                "independent_evaluation_verified": False,
                "scientific_model_qualified": False,
                "findings": []}
