from decimal import Decimal

from django.db import models


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ("Food", "Food"),
        ("Travel", "Travel"),
        ("Shopping", "Shopping"),
        ("Bills", "Bills"),
        ("Medical", "Medical"),
        ("Groceries", "Groceries"),
        ("Entertainment", "Entertainment"),
        ("Other", "Other"),
    ]

    receipt_image = models.FileField(upload_to="receipts/")
    merchant = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    transaction_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="Other")
    ocr_text = models.TextField(blank=True)
    confidence_note = models.CharField(max_length=140, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]

    def __str__(self):
        label = self.merchant or "Unknown merchant"
        return f"{label} - {self.category} - Rs {self.amount}"

    @property
    def is_pdf(self):
        return self.receipt_image.name.lower().endswith(".pdf")
