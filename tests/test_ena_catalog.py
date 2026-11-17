"""No-network ENA scientific discovery contract and negative controls."""
from __future__ import annotations
import unittest
from unittest.mock import patch

from backend import ena_catalog as ena

class ENACatalogTests(unittest.TestCase):
    def setUp(self):
        ena._cache.clear()

    def sample_rows(self):
        return [
            {"run_accession": "ERR123456", "study_accession": "ERP123456",
             "sample_accession": "ERS123456", "scientific_name": "Caenorhabditis elegans",
             "instrument_platform": "ILLUMINA", "first_public": "2026-10-01"},
            {"run_accession": "SRR654321", "study_accession": "SRP123456",
             "sample_accession": "SRS654321", "scientific_name": "Caenorhabditis elegans",
             "instrument_platform": "OXFORD_NANOPORE", "first_public": "2026-09-01"},
        ]

    def test_sample_is_not_a_census_or_a_lab_experiment_stream(self):
        with patch.object(ena, "_get", return_value=self.sample_rows()):
            result = ena.sample(force=True)
        self.assertEqual(result["state"], "LIVE_PUBLIC_ARCHIVE_CATALOG")
        self.assertEqual(result["catalog_completeness"], "BOUNDED_SAMPLE_NOT_CENSUS")
        self.assertEqual(result["taxon_id"], 6239)
        self.assertEqual(len(result["records"]), 2)
        self.assertFalse(result["raw_sequences_downloaded"])
        self.assertFalse(result["live_lab_instrument_connected"])
        self.assertFalse(result["labeled_training_data_verified"])
        self.assertFalse(result["licensing_approved_for_training"])

    def test_same_sample_is_cached_but_cache_is_labeled(self):
        with patch.object(ena, "_get", return_value=self.sample_rows()) as get:
            a = ena.sample()
            b = ena.sample()
        self.assertEqual(get.call_count, 1)
        self.assertEqual(a["state"], "LIVE_PUBLIC_ARCHIVE_CATALOG")
        self.assertEqual(b["state"], "CACHED_PUBLIC_ARCHIVE_CATALOG")

    def test_empty_is_unavailable_not_a_negative_science_result(self):
        with patch.object(ena, "_get", return_value=[]):
            result=ena.sample(force=True)
        self.assertEqual(result["state"], "PUBLIC_ARCHIVE_UNAVAILABLE")
        self.assertEqual(result["records"], [])
        self.assertFalse(result["observed_zero_runs"])

    def test_duplicate_run_ids_hold(self):
        repeated=self.sample_rows()[0]
        rows=[repeated,repeated.copy()]
        with self.assertRaisesRegex(ena.ENAUnavailable,"RUN_IDENTITY"):
            ena._validate(rows)

    def test_taxonomy_mismatch_holds_without_promoting_other_species(self):
        rows=self.sample_rows()
        rows[0]["scientific_name"]="Caenorhabditis briggsae"
        with self.assertRaisesRegex(ena.ENAUnavailable,"TAXON_MISMATCH"):
            ena._validate(rows)

    def test_changed_source_url_and_raw_read_paths_denied(self):
        with self.assertRaisesRegex(ena.ENAUnavailable, "NOT_CANONICAL"):
            ena._get("https://www.ebi.ac.uk/ena/browser/api/fasta/ERR123456")
        self.assertEqual("read_run", dict(
            __import__("urllib.parse",fromlist=["parse_qsl"]).parse_qsl(
                __import__("urllib.parse",fromlist=["urlsplit"]).urlsplit(ena.url()).query))["result"])
        self.assertTrue("tax_eq%286239%29" in ena.url())

    def test_missing_accessions_or_extra_files_hold(self):
        rows=self.sample_rows()
        del rows[0]["study_accession"]
        with self.assertRaisesRegex(ena.ENAUnavailable,"STUDY_IDENTITY"):
            ena._validate(rows)
        rows=self.sample_rows()
        rows[0]["fastq_ftp"]="not copied"
        with self.assertRaisesRegex(ena.ENAUnavailable,"UNEXPECTED_FIELDS"):
            ena._validate(rows)

    def test_more_than_bounded_count_refused(self):
        rows=self.sample_rows()*(ena.LIMIT+1)
        with self.assertRaisesRegex(ena.ENAUnavailable,"EMPTY_OR_INCOMPLETE"):
            ena._validate(rows)

if __name__ == "__main__":
    unittest.main()
