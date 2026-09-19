import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from invoice_tool.generator import generate_invoices, load_invoices


class InvoiceToolTests(unittest.TestCase):
    def test_sample_data_totals(self):
        invoices = load_invoices(Path("data/sample_orders.csv"))
        self.assertEqual(len(invoices), 3)
        self.assertEqual(invoices[0].invoice_number, "INV-1001")
        self.assertEqual(invoices[0].subtotal, Decimal("735.00"))
        self.assertEqual(invoices[0].tax_amount, Decimal("58.80"))
        self.assertEqual(invoices[0].total, Decimal("793.80"))

    def test_generation_creates_pdf_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            invoices = generate_invoices("data/sample_orders.csv", tmp)
            self.assertEqual(len(invoices), 3)
            self.assertTrue((Path(tmp) / "invoice_INV-1001.pdf").exists())
            self.assertTrue((Path(tmp) / "invoice_summary.csv").exists())

    def test_missing_column_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["invoice_number", "customer_name"])
                writer.writerow(["INV-X", "Test"])

            with self.assertRaises(ValueError):
                load_invoices(path)


if __name__ == "__main__":
    unittest.main()
