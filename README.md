# SpendLens - Intelligent Expense Categorizer

A Django monolith for the hackathon problem statement: upload receipt images, run OCR, extract merchant/amount/date, auto-categorize expenses, and show an interactive dashboard.

## Tech Stack

- Django templates for frontend
- Django views/models for backend
- SQLite database
- Python Tesseract OCR through `pytesseract`
- PDF text extraction through `pypdf`
- Chart.js for interactive charts
- Bootstrap for clean responsive UI

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000`.

## OCR Setup

Install the Tesseract engine:

```bash
brew install tesseract
```

If Tesseract or PDF extraction is not available, the app still supports demo flow through the fallback OCR text field on the upload page.

## Demo Receipt Text

```text
Domino's Pizza
Amount: ₹540.00
Date: 2026-01-28
```

## Main Files

- `expenses/ocr.py`: OCR extraction and parsing logic
- `expenses/categorizer.py`: merchant and keyword based category rules
- `expenses/views.py`: upload, review, dashboard, and delete operations
- `expenses/templates/expenses/`: frontend templates
