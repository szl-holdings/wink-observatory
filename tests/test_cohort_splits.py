"""Identity-leakage barriers for future C. elegans cohort evaluation."""
from __future__ import annotations

import copy
import unittest

from training.cohort_splits import CohortUnavailable, propose


class CohortTests(unittest.TestCase):
    @staticmethod
    def independent(n=140):
        return [{"sample_id":f"sample{i:04d}",
                 "animal_id":f"worm{i:04d}",
                 "plate_id":f"plate{i:04d}",
                 "batch_id":f"batch{i:04d}",
                 "session_id":f"session{i:04d}"} for i in range(n)]

    def test_reproducible_on_identical_content_even_if_input_order_changes(self):
        rows=self.independent()
        a=propose("a"*64,rows)
        b=propose("a"*64,list(reversed(rows)))
        self.assertEqual(a,b)
        self.assertEqual(a["state"],"REHEARSAL_GROUP_DISJOINT")
        self.assertEqual(sum(a["split_counts"].values()),len(rows))
        self.assertTrue(a["all_identity_groups_disjoint"])
        self.assertFalse(a["trainable"])
        self.assertFalse(a["partner_consent_verified"])
        self.assertFalse(a["records_observed_from_lab"])
        self.assertFalse(a["raw_ids_exported"])

    def test_shared_animal_plate_batch_session_identity_cannot_cross_folds(self):
        rows=self.independent(20)
        # Transitive chain across all four namespaces binds four records.
        rows[1]["animal_id"]=rows[0]["animal_id"]
        rows[2]["plate_id"]=rows[1]["plate_id"]
        rows[3]["batch_id"]=rows[2]["batch_id"]
        rows[4]["session_id"]=rows[3]["session_id"]
        report=propose("b"*64,rows)
        self.assertEqual(report["independent_identity_components"],16)
        self.assertTrue(report["all_identity_groups_disjoint"])

    def test_one_shared_plate_blocks_all_three_holdouts(self):
        rows=self.independent(20)
        for row in rows:
            row["plate_id"]="same_plate"
        report=propose("c"*64,rows)
        self.assertEqual(report["independent_identity_components"],1)
        self.assertEqual(report["state"],"HOLD_INSUFFICIENT_INDEPENDENT_COMPONENTS")
        self.assertEqual(sum(x>0 for x in report["split_counts"].values()),1)
        self.assertFalse(report["trainable"])

    def test_missing_identity_or_unpinned_dataset_denies(self):
        for sha in ("", "main", "z"*64):
            with self.subTest(sha=sha),self.assertRaises(CohortUnavailable):
                propose(sha,self.independent())
        rows=self.independent()
        del rows[0]["animal_id"]
        with self.assertRaisesRegex(CohortUnavailable,"SCHEMA"):
            propose("f"*64,rows)

    def test_duplicate_sample_and_embedded_control_characters_denied(self):
        rows=self.independent()
        rows[1]["sample_id"]=rows[0]["sample_id"]
        with self.assertRaisesRegex(CohortUnavailable,"DUPLICATE"):
            propose("a"*64,rows)
        rows=self.independent()
        rows[0]["sample_id"]="secret\ntext"
        with self.assertRaisesRegex(CohortUnavailable,"ID_INVALID"):
            propose("a"*64,rows)

    def test_no_data_never_becomes_a_trained_model(self):
        with self.assertRaisesRegex(CohortUnavailable,"SIZE"):
            propose("a"*64,[])
        with self.assertRaisesRegex(CohortUnavailable,"SIZE"):
            propose("a"*64,[self.independent()[0]])

if __name__=="__main__":
    unittest.main()
