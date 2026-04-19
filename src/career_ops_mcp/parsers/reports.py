import re
from dataclasses import dataclass
from pathlib import Path


_REPORT_FILENAME_RE = re.compile(r"^(\d{3})-(.+)-(\d{4}-\d{2}-\d{2})\.md$")


@dataclass
class ReportMeta:
    num: str          # zero-padded, e.g. "012"
    slug: str
    date: str
    path: Path

    def to_dict(self) -> dict:
        return {"num": self.num, "slug": self.slug, "date": self.date}


def list_reports(reports_dir: Path) -> list[ReportMeta]:
    if not reports_dir.exists():
        return []
    results = []
    for p in sorted(reports_dir.glob("*.md")):
        m = _REPORT_FILENAME_RE.match(p.name)
        if m:
            results.append(ReportMeta(num=m.group(1), slug=m.group(2), date=m.group(3), path=p))
    return results


def find_report(reports_dir: Path, num: str) -> Path | None:
    padded = num.zfill(3)
    for p in reports_dir.glob(f"{padded}-*.md"):
        return p
    return None


def read_report(reports_dir: Path, num: str) -> str | None:
    p = find_report(reports_dir, num)
    if p and p.exists():
        return p.read_text(encoding="utf-8")
    return None
