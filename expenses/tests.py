from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from .categorizer import categorize_expense
from .models import Expense
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

    def test_parses_bookmyshow_receipt_text(self):
        text = """
        BookMyShow
        PVR Cinemas, Phoenix Mall
        bookmyshow.com
        Date: 2026-02-01
        Booking ID: BMS-990213
        Movie: Pushpa 3
        2x Tickets (Gold) \u20b9440
        Convenience fee \u20b960
        GST \u20b922
        TOTAL \u20b9522
        Payment: UPI
        """

        parsed = parse_receipt_text(text)

        self.assertEqual(parsed["merchant"], "BookMyShow")
        self.assertEqual(parsed["amount"], Decimal("522"))
        self.assertEqual(str(parsed["transaction_date"]), "2026-02-01")
        self.assertEqual(categorize_expense(text, parsed["merchant"], parsed["amount"]), "Entertainment")

    def test_parses_ocr_currency_confusion(self):
        text = """
        BookMyShow
        Date: 2026-02-01
        TOTAL €522
        """

        parsed = parse_receipt_text(text)

        self.assertEqual(parsed["amount"], Decimal("522"))

    def test_parses_apollo_receipt_text(self):
        text = """
        Apollo Pharmacy
        JP Nagar, Bengaluru
        Date: 2026-01-31
        Bill #: APH-55932
        Crocin 500mg x10 \u20b932
        Cetrizine 10mg x10 \u20b928
        Subtotal \u20b9370
        Apollo discount -\u20b937
        TOTAL \u20b9333
        Payment: Cash
        """

        parsed = parse_receipt_text(text)

        self.assertEqual(parsed["merchant"], "Apollo Pharmacy")
        self.assertEqual(parsed["amount"], Decimal("333"))
        self.assertEqual(str(parsed["transaction_date"]), "2026-01-31")
        self.assertEqual(categorize_expense(text, parsed["merchant"], parsed["amount"]), "Medical")


class ReceiptUploadFlowTests(TestCase):
    def test_upload_review_does_not_save_until_user_confirms(self):
        receipt = SimpleUploadedFile(
            "uber.png",
            b"not-a-real-image",
            content_type="image/png",
        )

        response = self.client.post(
            reverse("upload_receipt"),
            {
                "receipt_image": receipt,
                "manual_ocr_text": "Uber\nTotal %311.93\nMarch 10, 2025",
            },
        )

        self.assertRedirects(response, reverse("review_pending_expense"))
        self.assertEqual(Expense.objects.count(), 0)

        response = self.client.post(
            reverse("review_pending_expense"),
            {
                "merchant": "Uber",
                "amount": "311.93",
                "transaction_date": "2025-03-10",
                "category": "Travel",
                "ocr_text": "Uber\nTotal %311.93\nMarch 10, 2025",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(Expense.objects.count(), 1)
