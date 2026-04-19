import re
from dataclasses import dataclass
from pathlib import Path

_SCORE_RE = re.compile(r"(\d+(?:\.\d+)?)/5")
_NUM_RE = re.compile(r"#(\d+)")


@dataclass
class PipelineEntry:
    url: str
    company: str
    title: str
    evaluated_num: int | None = None
    score: float | None = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "company": self.company,
            "title": self.title,
            "evaluated_num": self.evaluated_num,
            "score": self.score,
        }


def _parse_checked_line(parts: list[str]) -> PipelineEntry | None:
    # Format: #NUM | url | company | title | SCORE/5 | PDF emoji
    # parts already stripped
    if len(parts) < 4:
        return None
    num_match = _NUM_RE.search(parts[0])
    num = int(num_match.group(1)) if num_match else None
    url = parts[1].strip()
    company = parts[2].strip()
    title = parts[3].strip()
    score = None
    if len(parts) >= 5:
        m = _SCORE_RE.search(parts[4])
        score = float(m.group(1)) if m else None
    return PipelineEntry(url=url, company=company, title=title, evaluated_num=num, score=score)


def _parse_unchecked_line(parts: list[str]) -> PipelineEntry | None:
    # Format: url | company | title
    if len(parts) < 3:
        return None
    return PipelineEntry(url=parts[0].strip(), company=parts[1].strip(), title=parts[2].strip())


def parse(path: Path) -> dict[str, list[PipelineEntry]]:
    """Return {'pending': [...], 'processed': [...], 'pendientes': [...]}."""
    buckets: dict[str, list[PipelineEntry]] = {"pending": [], "processed": [], "pendientes": []}
    current_bucket: str | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            if heading == "pending":
                current_bucket = "pending"
            elif heading == "processed":
                current_bucket = "processed"
            elif heading in ("pendientes", "pendiente"):
                current_bucket = "pendientes"
            else:
                current_bucket = None
            continue

        if current_bucket is None:
            continue

        if stripped.startswith("- [x]"):
            content = stripped[5:].strip()
            parts = [p.strip() for p in content.split("|")]
            entry = _parse_checked_line(parts)
            if entry:
                buckets[current_bucket].append(entry)
        elif stripped.startswith("- [ ]"):
            content = stripped[5:].strip()
            parts = [p.strip() for p in content.split("|")]
            entry = _parse_unchecked_line(parts)
            if entry:
                buckets[current_bucket].append(entry)

    return buckets
