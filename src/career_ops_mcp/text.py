import re
from typing import Iterator


def slugify(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


def split_h2_sections(markdown: str) -> dict[str, str]:
    """Return {slug: body} for every H2 section in a markdown document."""
    sections: dict[str, str] = {}
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = slugify(line[3:].strip())
            current_lines = []
        else:
            if current_heading is not None:
                current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def extract_bullets(text: str) -> list[str]:
    """Return bare text of markdown bullet lines (- or *)."""
    bullets = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullets.append(stripped[2:].strip())
    return bullets


def chunk_text(text: str, max_chars: int = 512) -> Iterator[str]:
    """Split text into overlapping chunks at paragraph boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    buf: list[str] = []
    buf_len = 0
    for para in paragraphs:
        if buf_len + len(para) > max_chars and buf:
            yield "\n\n".join(buf)
            buf = []
            buf_len = 0
        buf.append(para)
        buf_len += len(para)
    if buf:
        yield "\n\n".join(buf)
