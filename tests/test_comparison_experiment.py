import tempfile
import unittest
from pathlib import Path

from experiments.compare_tables import experiment_rows, measure_key_set, write_csv, write_pdf, write_svg


class TableComparisonExperimentTests(unittest.TestCase):
    def test_compares_both_tables_across_requested_load_factors(self):
        rows = experiment_rows(capacity=100)
        self.assertEqual(len(rows), 9)
        self.assertEqual(rows[0]["load_factor"], 0.1)
        self.assertEqual(rows[-1]["load_factor"], 0.9)
        for row in rows:
            with self.subTest(load_factor=row["load_factor"]):
                self.assertGreaterEqual(row["linear_failure_measured"], 1.0)
                self.assertGreaterEqual(row["chaining_success_measured"], 1.0)

    def test_counts_actual_collision_and_empty_slot(self):
        self.assertEqual(measure_key_set(["g", "o"], 8, ["w", "b"]), (1.5, 1.0, 1.5, 2.0))

    def test_writes_comparison_table_graph_and_single_page_pdf(self):
        rows = experiment_rows(capacity=100)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            csv_path = output / "comparison.csv"
            svg_path = output / "comparison.svg"
            pdf_path = output / "comparison.pdf"
            write_csv(rows, csv_path)
            write_svg(rows, svg_path)
            write_pdf(rows, pdf_path)

            self.assertEqual(len(csv_path.read_text().splitlines()), 10)
            self.assertIn("<svg", svg_path.read_text())
            pdf = pdf_path.read_bytes()
            self.assertTrue(pdf.startswith(b"%PDF-1.4"))
            self.assertIn(b"/Count 1", pdf)


if __name__ == "__main__":
    unittest.main()
