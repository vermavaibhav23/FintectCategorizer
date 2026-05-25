import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


CURRENCY_PATTERN = r"(?:rs\.?|inr|\u20b9|â‚¹|€|\$|£)"
AMOUNT_PATTERNS = [
    rf"(?:total\s+paid|amount\s+charged|trip\s+fare|fare)\s*(?:of)?\s*[:\-]?\s*(?:{CURRENCY_PATTERN}|%)?\s*([0-9,]+(?:\.[0-9]{{1,2}})?)",
    rf"(?:amount|total|grand total|paid|balance)\s*(?:of)?\s*[:\-]?\s*(?:{CURRENCY_PATTERN}|%)?\s*([0-9,]+(?:\.[0-9]{{1,2}})?)",
    rf"{CURRENCY_PATTERN}\s*([0-9,]+(?:\.[0-9]{{1,2}})?)",
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

        _configure_tesseract(pytesseract)
        image = _prepare_image_for_ocr(Image.open(image_path))
        text = pytesseract.image_to_string(image, config="--psm 6")
        return text, "OCR extracted with Tesseract."
    except Exception as exc:
        tesseract_note = _format_tesseract_error(exc)

    text, note = _extract_text_with_claude_vision(image_path)
    if text:
        return text, note
    return "", f"{tesseract_note} {note}".strip()


def _configure_tesseract(pytesseract):
    import os

    configured_cmd = os.environ.get("TESSERACT_CMD")
    if configured_cmd:
        pytesseract.pytesseract.tesseract_cmd = configured_cmd
        return

    candidates = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return


def _prepare_image_for_ocr(image):
    image = image.convert("L")
    width, height = image.size
    if width < 1200:
        scale = 1200 / width
        image = image.resize((1200, int(height * scale)))
    return image


def _format_tesseract_error(exc):
    try:
        from pytesseract.pytesseract import TesseractNotFoundError
    except Exception:
        TesseractNotFoundError = None

    if TesseractNotFoundError and isinstance(exc, TesseractNotFoundError):
        return (
            "Tesseract OCR is not installed or not in PATH. Install Tesseract, "
            "or set TESSERACT_CMD to the tesseract.exe path."
        )
    return f"Tesseract OCR unavailable: {exc}"


def _get_api_key():
    import os

    return os.environ.get("ANTHROPIC_API_KEY")


def _extract_text_with_claude_vision(image_path):
    import base64

    api_key = _get_api_key()
    if not api_key:
        return "", "Claude Vision unavailable: set ANTHROPIC_API_KEY to enable the API fallback."

    try:
        import anthropic

        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        suffix = Path(image_path).suffix.lower()
        media_type = media_type_map.get(suffix, "image/jpeg")

        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Extract all text from this receipt image exactly as it appears. "
                                "Return only the raw text content, preserving line breaks and layout."
                            ),
                        },
                    ],
                }
            ],
        )
        return response.content[0].text, "OCR extracted with Claude Vision."
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
    if "bookmyshow" in joined:
        return "BookMyShow"
    if "apollo pharmacy" in joined:
        return "Apollo Pharmacy"

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
    preferred_labels = (
        r"total\s+paid",
        r"amount\s+charged",
        r"grand\s+total",
        r"total",
    )
    for label in preferred_labels:
        pattern = rf"(?<![a-z]){label}\s*(?:of)?\s*[:\-]?\s*(?:{CURRENCY_PATTERN}|%)?\s*([0-9,]+(?:\.[0-9]{{1,2}})?)"
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
