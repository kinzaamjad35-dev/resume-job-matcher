"""Text extraction from PDF, DOCX and plain-text files."""
from __future__ import annotations

import io
import re


def extract_text(data: bytes, filename: str) -> str:
    """Return the plain text of an uploaded file based on its extension."""
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif name.endswith(".docx"):
        import docx

        from docx.table import Table
        from docx.text.paragraph import Paragraph

        document = docx.Document(io.BytesIO(data))
        # Walk the body in document order so a table under EXPERIENCE stays under EXPERIENCE
        # (python-docx lists paragraphs and tables separately, which moved tables to the end).
        parts = []
        for el in document.element.body.iterchildren():
            tag = el.tag.rsplit("}", 1)[-1]
            if tag == "p":
                parts.append(Paragraph(el, document).text)
            elif tag == "tbl":
                for row in Table(el, document).rows:
                    cells = []
                    for cell in row.cells:  # merged cells repeat; keep each once
                        if not cells or cell.text != cells[-1]:
                            cells.append(cell.text)
                    parts.append(" | ".join(cells))
        text = "\n".join(parts)
    elif name.endswith((".txt", ".md")):
        text = data.decode("utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {filename}. Use PDF, DOCX or TXT.")
    return clean_text(text)


def clean_text(text: str) -> str:
    text = text.replace("\r", "\n").replace("\u2022", "-").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
