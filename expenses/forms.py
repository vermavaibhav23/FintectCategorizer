from django import forms

from .models import Expense


class ReceiptUploadForm(forms.ModelForm):
    manual_ocr_text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "placeholder": "Optional fallback: paste receipt text if OCR is unavailable.",
            }
        ),
        label="Fallback OCR text",
        help_text="Useful when OCR/PDF extraction is unavailable on the demo machine.",
    )

    class Meta:
        model = Expense
        fields = ["receipt_image", "manual_ocr_text"]
        widgets = {
            "receipt_image": forms.FileInput(attrs={"accept": "image/*,.pdf,application/pdf"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["receipt_image"].widget.attrs.update({"class": "form-control"})
        self.fields["manual_ocr_text"].widget.attrs.update({"class": "form-control"})


class ExpenseEditForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["merchant", "amount", "transaction_date", "category", "ocr_text"]
        widgets = {
            "transaction_date": forms.DateInput(attrs={"type": "date"}),
            "ocr_text": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})
        self.fields["category"].widget.attrs.update({"class": "form-select"})
