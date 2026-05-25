import shutil

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check whether local OCR dependencies are available."

    def handle(self, *args, **options):
        checks = [
            ("tesseract command", bool(shutil.which("tesseract"))),
            ("Pillow Python package", self._can_import("PIL")),
            ("pytesseract Python package", self._can_import("pytesseract")),
            ("pypdf Python package", self._can_import("pypdf")),
        ]

        for label, ok in checks:
            marker = "OK" if ok else "MISSING"
            self.stdout.write(f"{marker}: {label}")

        if not checks[0][1]:
            self.stdout.write("")
            self.stdout.write("Install Tesseract engine:")
            self.stdout.write("  macOS: brew install tesseract")
            self.stdout.write("  Ubuntu: sudo apt install tesseract-ocr")
            self.stdout.write("  Windows: install Tesseract and add it to PATH")

        if not all(ok for _, ok in checks[1:]):
            self.stdout.write("")
            self.stdout.write("Install Python packages inside your active virtualenv:")
            self.stdout.write("  pip install -r requirements.txt")

    def _can_import(self, module_name):
        try:
            __import__(module_name)
        except ImportError:
            return False
        return True
