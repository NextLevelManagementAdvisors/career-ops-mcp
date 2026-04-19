from pathlib import Path
from career_ops_mcp.parsers.applications import parse


def test_parse_row_count(applications_file: Path) -> None:
    apps = parse(applications_file)
    assert len(apps) == 4


def test_parse_first_row(applications_file: Path) -> None:
    app = parse(applications_file)[0]
    assert app.num == 1
    assert app.company == "Acme Corp"
    assert app.role == "Solutions Architect"
    assert app.score == 4.2
    assert app.status == "Evaluated"
    assert app.pdf is True
    assert app.report_num == "001"


def test_parse_no_report(applications_file: Path) -> None:
    apps = parse(applications_file)
    no_report = [a for a in apps if a.report_num is None]
    assert len(no_report) == 2


def test_status_preserved(applications_file: Path) -> None:
    apps = parse(applications_file)
    statuses = {a.status for a in apps}
    assert "Applied" in statuses
    assert "Interview" in statuses
    assert "Discarded" in statuses


def test_pdf_parsing(applications_file: Path) -> None:
    apps = parse(applications_file)
    pdf_true = [a for a in apps if a.pdf]
    pdf_false = [a for a in apps if not a.pdf]
    assert len(pdf_true) == 1
    assert len(pdf_false) == 3


def test_notes_parsed(applications_file: Path) -> None:
    app = parse(applications_file)[0]
    assert "Strong fit" in app.notes
