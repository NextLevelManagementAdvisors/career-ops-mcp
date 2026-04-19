from pathlib import Path
from career_ops_mcp.parsers.cv import parse


def test_parse_name(cv_file: Path) -> None:
    cv = parse(cv_file)
    assert cv.name == "Test User"


def test_sections_present(cv_file: Path) -> None:
    cv = parse(cv_file)
    slugs = {s.slug for s in cv.sections}
    assert "professional-summary" in slugs
    assert "professional-experience" in slugs
    assert "technical-skills" in slugs
    assert "education" in slugs
    assert "academic-research" in slugs


def test_section_lookup(cv_file: Path) -> None:
    cv = parse(cv_file)
    sec = cv.section("technical-skills")
    assert sec is not None
    assert "Python" in sec.body


def test_bullets_extracted(cv_file: Path) -> None:
    cv = parse(cv_file)
    exp = cv.section("professional-experience")
    assert exp is not None
    assert len(exp.bullets) >= 3
    assert any("pipeline" in b.lower() for b in exp.bullets)


def test_full_text(cv_file: Path) -> None:
    cv = parse(cv_file)
    text = cv.full_text()
    assert "Test User" in text
    assert "Professional Experience" in text


def test_missing_section_returns_none(cv_file: Path) -> None:
    cv = parse(cv_file)
    assert cv.section("nonexistent-section") is None
