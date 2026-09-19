from pathlib import Path
from pypdf import PdfReader


PDF_PATH = Path(__file__).resolve().parents[2] / "data" / "spotify_web_app_architecture.pdf"


def read_pdf():
    reader = PdfReader(PDF_PATH)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text