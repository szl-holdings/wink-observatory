"""A9/A10 exact finite-sample falsifiability witnesses and negative controls."""
from __future__ import annotations
import copy
import json
import unittest

from backend import falsifiability as a
from backend.live_data import ROOT

class FalsifiabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((ROOT/"data/receipts/v5-heldout.json").read_text(encoding="utf-8"))

    def test_actual_four_recorded_passes_do_not_clear_science(self):
        report = a.audit(self.receipt)
        self.assertEqual(report["overall_admission"], "HOLD")
        self.assertEqual(report["evaluated_criteria"], 4)
        self.assertFalse(report["scientific_model_qualified"])
        self.assertTrue(all(x["recorded_pass"] for x in report["findings"]))
        self.assertTrue(all(not x["independent_science_pass"] for x in report["findings"]))

    def test_neutral_rule_cannot_trip_due_to_negative_accuracy_floor(self):
        r=a.audit(self.receipt)
        item=next(x for x in r["findings"] if x["criterion"]=="criterion_4_neutral")
        self.assertLess(item["threshold"],0)
        self.assertFalse(item["valid_binary_measurement_can_fail"])
        self.assertEqual(item["review_state"],"UNINTERPRETABLE")
        self.assertIsNone(item["mathematical_failure_witness"]["maximum_failing_success_count"])

    def test_invented_identifier_rule_requires_catastrophic_failure_count(self):
        r=a.audit(self.receipt)
        item=next(x for x in r["findings"] if x["criterion"]=="criterion_5_invented_id")
        self.assertEqual(item["mathematical_failure_witness"]["minimum_fail_events"],13)
        self.assertAlmostEqual(item["mathematical_failure_witness"]["minimum_fail_fraction"],13/15,places=5)
        self.assertEqual(item["review_state"],"THRESHOLD_TRIPS_ONLY_IN_CATASTROPHIC_RANGE")

    def test_contamination_failure_requires_five_of_forty(self):
        r=a.audit(self.receipt)
        item=next(x for x in r["findings"] if x["criterion"]=="criterion_2_contamination")
        self.assertEqual(item["mathematical_failure_witness"]["minimum_fail_events"],5)

    def test_unknown_criterion_invalidates_whole_battery(self):
        fake=copy.deepcopy(self.receipt)
        fake["criteria"][0]["id"]="criterion_999_not_reviewed"
        with self.assertRaisesRegex(a.EvaluationUnavailable,"UNSUPPORTED"):
            a.audit(fake)

    def test_no_outcome_is_not_a_clean_zero(self):
        fake=copy.deepcopy(self.receipt)
        fake["criteria"][0]["n"]=0
        with self.assertRaisesRegex(a.EvaluationUnavailable,"COUNT_NOT_POSITIVE"):
            a.audit(fake)

    def test_boolean_count_is_rejected(self):
        fake=copy.deepcopy(self.receipt)
        fake["criteria"][0]["n"]=True
        with self.assertRaises(a.EvaluationUnavailable):
            a.audit(fake)

    def test_unreachable_upper_bound_is_not_passed(self):
        fake=copy.deepcopy(self.receipt)
        fake["criteria"][0]["threshold"]=1.0
        result=a.audit(fake)
        item=result["findings"][0]
        self.assertFalse(item["valid_binary_measurement_can_fail"])
        self.assertEqual(item["review_state"],"CANNOT_TRIP")

    def test_missing_evidence_fails_closed(self):
        self.assertEqual(a.public_audit({"docs":{}})["overall_admission"],"HOLD")
        self.assertEqual(a.public_audit({"docs":{}})["state"],"UNAVAILABLE")

if __name__ == "__main__":
    unittest.main()
