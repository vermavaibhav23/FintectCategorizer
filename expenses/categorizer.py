from decimal import Decimal, InvalidOperation


CATEGORY_RULES = {
    "Food": [
        "domino",
        "pizza",
        "restaurant",
        "swiggy",
        "zomato",
        "cafe",
        "coffee",
        "burger",
        "kfc",
        "mcdonald",
    ],
    "Travel": ["uber", "ola", "taxi", "metro", "flight", "train", "bus", "railway", "cab"],
    "Shopping": ["amazon", "flipkart", "myntra", "store", "mall", "fashion", "retail"],
    "Bills": ["electricity", "wifi", "mobile", "recharge", "broadband", "bill", "postpaid"],
    "Medical": ["pharmacy", "hospital", "clinic", "medicine", "apollo", "health"],
    "Groceries": ["grocery", "dmart", "bigbasket", "blinkit", "zepto", "mart", "supermarket"],
    "Entertainment": ["movie", "cinema", "bookmyshow", "netflix", "spotify", "game"],
}


def categorize_expense(text, merchant="", amount=None):
    haystack = f"{merchant} {text}".lower()

    merchant_category_overrides = {
        "bookmyshow": "Entertainment",
        "apollo pharmacy": "Medical",
        "uber": "Travel",
    }
    for keyword, category in merchant_category_overrides.items():
        if keyword in haystack:
            return category

    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in haystack for keyword in keywords):
            return category

    try:
        parsed_amount = Decimal(str(amount or "0"))
    except (InvalidOperation, TypeError):
        parsed_amount = Decimal("0")

    if parsed_amount > Decimal("10000"):
        return "Shopping"

    return "Other"


def category_palette():
    return {
        "Food": "#2563eb",
        "Travel": "#0891b2",
        "Shopping": "#7c3aed",
        "Bills": "#dc2626",
        "Medical": "#16a34a",
        "Groceries": "#ea580c",
        "Entertainment": "#db2777",
        "Other": "#64748b",
    }
