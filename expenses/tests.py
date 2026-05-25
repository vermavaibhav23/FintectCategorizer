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

    def test_merchant_rules_take_priority_over_broad_keywords(self):
        self.assertEqual(
            categorize_expense("BookMyShow ticket at mall", "BookMyShow", "450.00"),
            "Entertainment",
        )
        self.assertEqual(
            categorize_expense("Apollo Pharmacy retail bill", "Apollo Pharmacy", "320.00"),
            "Medical",
        )
        self.assertEqual(
            categorize_expense(
                "Apollo Health & Lifestyle Ltd. pharmacy bill",
                "APOLLO PHARMACY",
                "255.00",
            ),
            "Medical",
        )

    def test_known_indian_merchant_mappings(self):
        examples = [
            ("Swiggy", "Food"),
            ("IndiGo", "Travel"),
            ("Myntra", "Shopping"),
            ("Airtel Postpaid", "Bills"),
            ("PharmEasy", "Medical"),
            ("D Mart", "Groceries"),
            ("PVR Cinemas", "Entertainment"),
        ]

        for merchant, expected_category in examples:
            with self.subTest(merchant=merchant):
                self.assertEqual(
                    categorize_expense(f"{merchant} receipt", merchant, "500.00"),
                    expected_category,
                )


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

    def test_dashboard_filters_processed_receipts_by_category(self):
        Expense.objects.create(
            merchant="Uber",
            amount="311.93",
            category="Travel",
            ocr_text="Uber receipt",
        )
        Expense.objects.create(
            merchant="Apollo Pharmacy",
            amount="255.00",
            category="Medical",
            ocr_text="Apollo receipt",
        )

        response = self.client.get(reverse("dashboard"), {"category": "Medical"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["expenses"].values_list("merchant", flat=True)), ["Apollo Pharmacy"])
        self.assertEqual(response.context["selected_category"], "Medical")
