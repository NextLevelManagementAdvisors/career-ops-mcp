from pathlib import Path

import pytest

from career_ops_mcp import profile


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("CAREER_OPS_OWNER_NAME", raising=False)
    monkeypatch.delenv("CAREER_OPS_ARCHETYPES", raising=False)


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "profile.yml"
    p.write_text(text, encoding="utf-8")
    return p


def test_defaults_when_profile_missing(tmp_path):
    missing = tmp_path / "nope.yml"
    assert profile.owner_name(missing) == "the user"
    assert profile.target_archetypes(missing) == []


def test_reads_name_and_archetypes(tmp_path):
    p = _write(
        tmp_path,
        'candidate:\n  full_name: "Jane Smith"\n'
        "target_roles:\n  primary: [Senior AI Engineer]\n  archetypes:\n"
        '    - name: "AI/ML Engineer"\n      fit: primary\n'
        '    - name: "Solutions Architect"\n',
    )
    assert profile.owner_name(p) == "Jane Smith"
    assert profile.target_archetypes(p) == ["AI/ML Engineer", "Solutions Architect"]


def test_falls_back_to_primary_roles(tmp_path):
    p = _write(tmp_path, "target_roles:\n  primary: [Founder]\n")
    assert profile.target_archetypes(p) == ["Founder"]


def test_env_overrides_profile(tmp_path, monkeypatch):
    p = _write(tmp_path, 'candidate:\n  full_name: "Jane Smith"\n')
    monkeypatch.setenv("CAREER_OPS_OWNER_NAME", "Sam Lee")
    monkeypatch.setenv("CAREER_OPS_ARCHETYPES", "Founder, Advisor")
    assert profile.owner_name(p) == "Sam Lee"
    assert profile.target_archetypes(p) == ["Founder", "Advisor"]


def test_malformed_profile_is_ignored(tmp_path):
    p = _write(tmp_path, "candidate: [unclosed")
    assert profile.owner_name(p) == "the user"
    assert profile.target_archetypes(p) == []


def test_possessive():
    assert profile.possessive("Jane Smith") == "Jane Smith's"
    assert profile.possessive("Chris Jones") == "Chris Jones'"
