import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Application:
    num: int
    date: str
    company: str
    role: str
    score: float | None
    status: str
    pdf: bool
    report_path: str | None
    report_num: str | None
    notes: str

    def to_dict(self) -> dict:
        return {
            "num": self.num,
            "date": self.date,
            "company": self.company,
            "role": self.role,
            "score": self.score,
            "status": self.status,
            "pdf": self.pdf,
            "report_path": self.report_path,
            "report_num": self.report_num,
            "notes": self.notes,
        }


_REPORT_LINK_RE = re.compile(r"\[(\d+)\]\(([^)]+)\)")
_SCORE_RE = re.compile(r"(\d+(?:\.\d+)?)/5")


def _parse_cell(s: str) -> str:
    return s.strip()


def _parse_score(s: str) -> float | None:
    m = _SCORE_RE.search(s)
    return float(m.group(1)) if m else None


def _parse_pdf(s: str) -> bool:
    return "✅" in s


def _parse_report(s: str) -> tuple[str | None, str | None]:
    m = _REPORT_LINK_RE.search(s)
    if m:
        return m.group(1), m.group(2)
    return None, None


def _split_row(line: str) -> list[str]:
    # strip leading/trailing | then split
    stripped = line.strip().strip("|")
    return [c for c in stripped.split("|")]


def parse(path: Path) -> list[Application]:
    text = path.read_text(encoding="utf-8")
    apps: list[Application] = []
    in_table = False

    for line in text.splitlines():
        line_s = line.strip()
        if not line_s.startswith("|"):
            continue
        cells = _split_row(line_s)
        if len(cells) < 9:
            continue
        # skip header and separator rows
        first = cells[0].strip()
        if first == "#" or set(first.replace("-", "").replace(" ", "")) == set():
            in_table = True
            continue
        if not in_table:
            continue
        try:
            num = int(first)
        except ValueError:
            continue

        report_num, report_path = _parse_report(cells[7])
        apps.append(
            Application(
                num=num,
                date=_parse_cell(cells[1]),
                company=_parse_cell(cells[2]),
                role=_parse_cell(cells[3]),
                score=_parse_score(cells[4]),
                status=_parse_cell(cells[5]),
                pdf=_parse_pdf(cells[6]),
                report_num=report_num,
                report_path=_parse_cell(cells[7]) if not report_num else report_path,
                notes=_parse_cell(cells[8]),
            )
        )
    return apps
