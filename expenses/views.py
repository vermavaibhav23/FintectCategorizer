import json
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .categorizer import categorize_expense, category_palette
from .forms import ExpenseEditForm, ReceiptUploadForm
from .models import Expense
from .ocr import extract_text_from_image, parse_receipt_text


def dashboard(request):
    expenses = Expense.objects.all()
    selected_category = request.GET.get("category", "")

    if selected_category:
        expenses = expenses.filter(category=selected_category)

    category_totals = (
        Expense.objects.values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )
    total_spend = Expense.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    receipt_count = Expense.objects.count()
    biggest_category = category_totals[0] if category_totals else None
    latest_expense = Expense.objects.order_by("-created_at").first()

    chart_labels = [item["category"] for item in category_totals]
    chart_values = [float(item["total"] or 0) for item in category_totals]
    palette = category_palette()
    chart_colors = [palette.get(label, "#64748b") for label in chart_labels]

    context = {
        "expenses": expenses,
        "category_totals": category_totals,
        "total_spend": total_spend,
        "receipt_count": receipt_count,
        "biggest_category": biggest_category,
        "latest_expense": latest_expense,
        "selected_category": selected_category,
        "category_choices": Expense.CATEGORY_CHOICES,
        "chart_labels": json.dumps(chart_labels),
        "chart_values": json.dumps(chart_values),
        "chart_colors": json.dumps(chart_colors),
    }
    return render(request, "expenses/dashboard.html", context)


def upload_receipt(request):
    if request.method == "POST":
        form = ReceiptUploadForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.save()

            ocr_text, confidence_note = extract_text_from_image(expense.receipt_image.path)
            manual_text = form.cleaned_data.get("manual_ocr_text", "").strip()
            final_text = ocr_text.strip() or manual_text

            parsed = parse_receipt_text(final_text)
            expense.ocr_text = final_text
            expense.confidence_note = confidence_note
            expense.merchant = parsed["merchant"]
            expense.amount = parsed["amount"]
            expense.transaction_date = parsed["transaction_date"]
            expense.category = categorize_expense(final_text, expense.merchant, expense.amount)
            expense.save()

            if not ocr_text and manual_text:
                messages.warning(
                    request,
                    "Automatic OCR was unavailable, so the app used your fallback text.",
                )
            else:
                messages.success(request, "Receipt uploaded and categorized successfully.")

            return redirect(f"{reverse('edit_expense', args=[expense.id])}?fresh=1")
    else:
        form = ReceiptUploadForm()

    return render(request, "expenses/upload.html", {"form": form})


def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    if request.method == "POST":
        form = ExpenseEditForm(request.POST, instance=expense)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.category = categorize_expense(updated.ocr_text, updated.merchant, updated.amount)
            if "category" in form.changed_data:
                updated.category = form.cleaned_data["category"]
            updated.save()
            messages.success(request, "Expense details updated.")
            return redirect("dashboard")
    else:
        form = ExpenseEditForm(instance=expense)

    return render(
        request,
        "expenses/edit.html",
        {
            "expense": expense,
            "form": form,
            "is_fresh": request.GET.get("fresh") == "1",
        },
    )


@require_POST
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id)
    expense.delete()
    messages.success(request, "Expense deleted.")
    return redirect("dashboard")
