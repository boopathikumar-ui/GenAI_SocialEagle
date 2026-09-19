from pathlib import Path
from pypdf import PdfReader

PDF_PATH = Path("data/spotify_web_app_architecture.pdf")


def read_pdf():
    reader = PdfReader(PDF_PATH)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


if __name__ == "__main__":
    pdf_text = read_pdf()

    print("PDF loaded successfully!")
    print(f"Number of characters: {len(pdf_text)}")
    print("\nFirst 1000 characters:\n")
    print(pdf_text[:1000])