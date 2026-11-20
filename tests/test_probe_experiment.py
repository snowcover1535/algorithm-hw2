import unittest

from experiments.probe_experiment import experiment_rows, measure_probes


class ProbeExperimentTests(unittest.TestCase):
    def test_empty_table_has_zero_probes(self):
        self.assertEqual(measure_probes(8, 0), (0.0, 0.0))

    def test_experiment_covers_requested_load_factor_range(self):
        rows = experiment_rows(capacity=32)
        self.assertEqual(len(rows), 16)
        self.assertEqual(rows[0]["load_factor"], 0.25)
        self.assertEqual(rows[-1]["load_factor"], 4.0)
        for row in rows:
            with self.subTest(load_factor=row["load_factor"]):
                self.assertGreaterEqual(row["successful_measured"], 1.0)
                self.assertGreaterEqual(row["unsuccessful_measured"], 0.0)

    def test_rejects_invalid_experiment_sizes(self):
        with self.assertRaises(ValueError):
            measure_probes(0, 1)
        with self.assertRaises(ValueError):
            measure_probes(8, -1)


if __name__ == "__main__":
    unittest.main()
