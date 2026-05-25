import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


AMOUNT_PATTERNS = [
    r"(?:amount|total|grand total|paid|balance)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
    r"(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]{1,2})?)",
]

DATE_PATTERNS = [
    r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
    r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})",
]


def extract_text_from_image(image_path):
    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return "", "Install pillow and pytesseract for automatic OCR."

    try:
        return pytesseract.image_to_string(Image.open(image_path)), "OCR extracted with Tesseract."
    except Exception as exc:
        return "", f"OCR unavailable: {exc}"


def parse_receipt_text(text):
    clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
    merchant = _extract_merchant(clean_lines)
    amount = _extract_amount(text)
    transaction_date = _extract_date(text)

    return {
        "merchant": merchant,
        "amount": amount,
        "transaction_date": transaction_date,
    }


def _extract_merchant(lines):
    ignored = ("amount", "total", "date", "invoice", "receipt", "tax", "gst", "bill")
    for line in lines[:8]:
        lowered = line.lower()
        if not any(word in lowered for word in ignored) and len(line) > 2:
            return line[:120]
    return ""


def _extract_amount(text):
    lowered = text.lower()
    candidates = []

    for pattern in AMOUNT_PATTERNS:
        for match in re.finditer(pattern, lowered, re.IGNORECASE):
            candidates.append(match.group(1))

    if not candidates:
        candidates = re.findall(r"\b([0-9,]+\.[0-9]{2})\b", text)

    amounts = []
    for candidate in candidates:
        try:
            amounts.append(Decimal(candidate.replace(",", "")))
        except InvalidOperation:
            continue

    return max(amounts) if amounts else Decimal("0.00")


def _extract_date(text):
    lowered = text.lower()
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, lowered, re.IGNORECASE)
        if not match:
            continue

        parsed = _parse_date(match.group(1))
        if parsed:
            return parsed

    return None


def _parse_date(value):
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d-%m-%y",
        "%d/%m/%y",
        "%d %b %Y",
        "%d %B %Y",
        "%d %b %y",
        "%d %B %y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
