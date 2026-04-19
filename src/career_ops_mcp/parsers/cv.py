from dataclasses import dataclass
from pathlib import Path

from career_ops_mcp.text import split_h2_sections, extract_bullets, slugify


@dataclass
class CVSection:
    slug: str
    heading: str
    body: str
    bullets: list[str]


@dataclass
class CV:
    name: str
    contact: str
    sections: list[CVSection]

    def section(self, slug: str) -> CVSection | None:
        for s in self.sections:
            if s.slug == slug:
                return s
        return None

    def full_text(self) -> str:
        parts = [self.name, self.contact]
        for s in self.sections:
            parts.append(f"## {s.heading}\n\n{s.body}")
        return "\n\n---\n\n".join(parts)


def _extract_heading_text(markdown: str) -> tuple[str, str]:
    """Return (name_line, contact_line) from the top of cv.md."""
    lines = markdown.splitlines()
    name = ""
    contact = ""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            name = stripped[2:].strip()
        elif name and stripped and not stripped.startswith("#") and not stripped.startswith("---"):
            contact = stripped
            break
    return name, contact


def parse(path: Path) -> CV:
    text = path.read_text(encoding="utf-8")
    name, contact = _extract_heading_text(text)
    raw_sections = split_h2_sections(text)

    sections = []
    # Preserve reading order by iterating the original text for H2 headings
    import re
    for m in re.finditer(r"^## (.+)$", text, re.MULTILINE):
        heading = m.group(1).strip()
        sl = slugify(heading)
        body = raw_sections.get(sl, "")
        sections.append(CVSection(slug=sl, heading=heading, body=body, bullets=extract_bullets(body)))

    return CV(name=name, contact=contact, sections=sections)
