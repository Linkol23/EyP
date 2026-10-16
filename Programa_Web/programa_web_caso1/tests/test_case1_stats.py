import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from case1_stats import (  # noqa: E402
    DATASET,
    INTERVALS,
    conditional_probability,
    complete_analysis,
    describe,
    frequency_distribution,
    probability_analysis,
    quantile_linear,
    simulation,
    stopping_rule,
)


class Case1StatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = [row["time_a"] for row in DATASET]
        cls.b = [row["time_b"] for row in DATASET]

    def test_dataset_has_24_paired_records(self):
        self.assertEqual(len(DATASET), 24)
        self.assertEqual([r["scenario"] for r in DATASET], list(range(1, 25)))

    def test_interval_boundaries_are_unique(self):
        boundaries = [20, 60, 61, 100, 101, 140, 141, 180, 181, 220]
        for value in boundaries:
            matches = sum(lower <= value <= upper for lower, upper in INTERVALS)
            self.assertEqual(matches, 1, msg=f"Frontera problemática: {value}")

    def test_frequencies_match_report(self):
        self.assertEqual([r["fi"] for r in frequency_distribution(self.a)], [21, 0, 1, 1, 1])
        self.assertEqual([r["fi"] for r in frequency_distribution(self.b)], [0, 24, 0, 0, 0])

    def test_descriptive_statistics_match_report(self):
        a = describe(self.a)
        b = describe(self.b)
        self.assertAlmostEqual(a["mean"], 59.9166666667)
        self.assertAlmostEqual(b["mean"], 71.1666666667)
        self.assertAlmostEqual(a["p90"], 104.9)
        self.assertAlmostEqual(b["p90"], 76.0)
        self.assertAlmostEqual(a["sample_variance"], 1666.7753623188)
        self.assertAlmostEqual(b["sample_sd"], 3.3965028903)

    def test_all_modes_are_returned(self):
        self.assertEqual(describe(self.a)["modes"], [40, 42, 45, 47])
        self.assertEqual(describe(self.b)["modes"], [68, 69, 70, 72])

    def test_d9_and_p90_are_identical(self):
        self.assertEqual(quantile_linear(self.a, .9), describe(self.a)["d9"])
        self.assertEqual(describe(self.a)["d9"], describe(self.a)["p90"])

    def test_rules_recommend_b(self):
        analysis = complete_analysis()
        self.assertFalse(analysis["rules"]["A"]["complies"])
        self.assertTrue(analysis["rules"]["B"]["complies"])
        self.assertEqual(analysis["decision"]["recommended_version"], "B")

    def test_probability_table_and_independence(self):
        result = probability_analysis()
        self.assertEqual(result["contingency"]["F_H"], 2)
        self.assertEqual(result["contingency"]["F_not_H"], 1)
        self.assertAlmostEqual(result["probabilities"]["P_F_given_H"], .25)
        self.assertFalse(result["mutually_exclusive"])
        self.assertFalse(result["independent"])

    def test_conditional_probabilities_document_counts_and_scenarios(self):
        result = probability_analysis()["conditionals"]
        self.assertEqual(result["P_F_given_H"]["numerator"], 2)
        self.assertEqual(result["P_F_given_H"]["denominator"], 8)
        self.assertEqual(result["P_F_given_H"]["numerator_scenarios"], [21, 24])
        self.assertEqual(result["P_H_given_F"]["denominator_scenarios"], [21, 23, 24])

    def test_conditional_probability_handles_zero_denominator(self):
        self.assertIsNone(conditional_probability(0, 0))
        with self.assertRaises(ValueError):
            conditional_probability(2, 1)

    def test_additional_information_preserves_all_records(self):
        additional = complete_analysis()["additional_information"]
        self.assertAlmostEqual(additional["first_20"]["mean"], 45.3)
        self.assertAlmostEqual(additional["first_20"]["p90"], 51.4)
        self.assertAlmostEqual(additional["all_24"]["p90"], 104.9)

    def test_stopping_rule_stops_at_three(self):
        result = stopping_rule()
        self.assertEqual(result["stop_revision"], 3)
        self.assertEqual(result["final_balance"], 330)
        self.assertEqual(len(result["rows"]), 3)

    def test_official_simulation_is_reproducible(self):
        result = simulation(321)
        self.assertEqual(result["generator"], "PCG64")
        self.assertEqual([row["count_F"] for row in result["rows"]], [14, 70, 128])
        self.assertEqual([round(row["relative_frequency"], 4) for row in result["rows"]], [.14, .14, .128])

    def test_all_internal_validations_pass(self):
        self.assertTrue(complete_analysis()["validation"]["all_passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

