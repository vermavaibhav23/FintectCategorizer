from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("merchant", "amount", "transaction_date", "category", "created_at")
    list_filter = ("category", "transaction_date")
    search_fields = ("merchant", "ocr_text")
