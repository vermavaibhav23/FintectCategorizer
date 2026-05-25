from decimal import Decimal

from django.test import SimpleTestCase

from .categorizer import categorize_expense
from .ocr import parse_receipt_text


class ReceiptParsingTests(SimpleTestCase):
    def test_parses_uber_receipt_text(self):
        text = """
        Uber
        March 10, 2025
        Thanks for riding, Vaibhav
        Total paid ₹298.45
        Trip fare ₹260.00
        Payments
        Cash ₹298.45
        """

        parsed = parse_receipt_text(text)

        self.assertEqual(parsed["merchant"], "Uber")
        self.assertEqual(parsed["amount"], Decimal("298.45"))
        self.assertEqual(str(parsed["transaction_date"]), "2025-03-10")
        self.assertEqual(categorize_expense(text, parsed["merchant"], parsed["amount"]), "Travel")

    def test_prefers_total_paid_over_smaller_line_items(self):
        text = """
        Uber
        Total paid INR 540.50
        Base fare INR 280.00
        Taxes INR 18.20
        """

        parsed = parse_receipt_text(text)

        self.assertEqual(parsed["amount"], Decimal("540.50"))

    def test_handles_ocr_noise_in_uber_total(self):
        text = """
        Uber March 10, 2025
        Thanks for tipping, Nisha
        Total %311.93
        Trip Charge 261.93
        Subtotal 261.93
        Tip 50.00
        """

        parsed = parse_receipt_text(text)

        self.assertEqual(parsed["merchant"], "Uber")
        self.assertEqual(parsed["amount"], Decimal("311.93"))
        self.assertEqual(str(parsed["transaction_date"]), "2025-03-10")
