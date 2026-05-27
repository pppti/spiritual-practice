import os

ALLOWED_EXTENSIONS = {'.txt', '.docx', '.pdf', '.mobi', '.md'}
MAX_SIZE = 20 * 1024 * 1024  # 20MB


def parse_txt(content: bytes) -> str:
    for enc in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode('utf-8', errors='replace')


def parse_docx(content: bytes) -> str:
    from io import BytesIO
    from docx import Document
    doc = Document(BytesIO(content))
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())


def parse_pdf(content: bytes) -> str:
    from io import BytesIO
    from PyPDF2 import PdfReader
    reader = PdfReader(BytesIO(content))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return '\n'.join(parts)


def parse_md(content: bytes) -> str:
    return content.decode('utf-8', errors='replace')


def parse_mobi(content: bytes) -> str:
    # Basic MOBI parsing: extract text content by stripping binary headers
    # Full MOBI parsing requires complex libraries, this is a best-effort approach
    try:
        text = content.decode('utf-8', errors='replace')
        # Try to find readable text segments
        import re
        # Remove non-printable chars except newlines and Chinese chars
        text = re.sub(r'[^\x20-\x7e一-鿿　-〿＀-￯\n\r]', '', text)
        # Keep only lines that seem like text (>10 chars)
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 10]
        return '\n'.join(lines[:5000])  # Limit to 5000 lines
    except Exception:
        return ''


def parse_file(filename: str, content: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}")

    if len(content) > MAX_SIZE:
        raise ValueError(f"File too large (max {MAX_SIZE // 1024 // 1024}MB)")

    parsers = {
        '.txt': parse_txt,
        '.md': parse_md,
        '.docx': parse_docx,
        '.pdf': parse_pdf,
        '.mobi': parse_mobi,
    }
    return parsers[ext](content)
