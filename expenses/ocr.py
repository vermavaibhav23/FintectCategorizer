import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


AMOUNT_PATTERNS = [
    r"(?:total\s+paid|amount\s+charged|trip\s+fare|fare)\s*(?:of)?\s*[:\-]?\s*(?:rs\.?|inr|₹|%)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
    r"(?:amount|total|grand total|paid|balance)\s*(?:of)?\s*[:\-]?\s*(?:rs\.?|inr|₹|%)?\s*([0-9,]+(?:\.[0-9]{1,2})?)",
    r"(?:rs\.?|inr|₹)\s*([0-9,]+(?:\.[0-9]{1,2})?)",
]

DATE_PATTERNS = [
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4})",
    r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
    r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})",
]


def extract_text_from_receipt(file_path):
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    return extract_text_from_image(file_path)


def extract_text_from_pdf(pdf_path):
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", "Install pypdf to extract text from PDF receipts."

    try:
        reader = PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        return "", f"PDF extraction unavailable: {exc}"

    if not text:
        return "", "No selectable text found in this PDF. Try an image receipt or paste fallback text."
    return text, "PDF text extracted successfully."


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
    joined = "\n".join(lines[:12]).lower()
    if "uber" in joined:
        return "Uber"

    ignored = (
        "amount",
        "total",
        "date",
        "invoice",
        "receipt",
        "tax",
        "gst",
        "bill",
        "thanks",
        "payment",
    )
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

    if not amounts:
        return Decimal("0.00")

    preferred = _extract_preferred_amount(lowered)
    if preferred is not None:
        return preferred

    return max(amounts)


def _extract_preferred_amount(lowered_text):
    preferred_labels = ("total paid", "amount charged", "grand total", "total")
    for label in preferred_labels:
        pattern = rf"{label}\s*(?:of)?\s*[:\-]?\s*(?:rs\.?|inr|₹|%)?\s*([0-9,]+(?:\.[0-9]{{1,2}})?)"
        match = re.search(pattern, lowered_text, re.IGNORECASE)
        if match:
            try:
                return Decimal(match.group(1).replace(",", ""))
            except InvalidOperation:
                return None
    return None


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
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %d %Y",
        "%B %d %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None
