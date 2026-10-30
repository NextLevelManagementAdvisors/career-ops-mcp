from pathlib import Path

import pytest

from career_ops_mcp import server, tools


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("CAREER_OPS_OWNER_NAME", raising=False)
    monkeypatch.delenv("CAREER_OPS_ARCHETYPES", raising=False)


def test_prompt_uses_configured_owner_and_archetypes(monkeypatch):
    monkeypatch.setenv("CAREER_OPS_OWNER_NAME", "Sam Lee")
    monkeypatch.setenv("CAREER_OPS_ARCHETYPES", "Founder, Advisor")
    text = server.evaluate_fit("Some JD text")
    assert "Sam Lee's AI job search advisor" in text
    assert "target archetypes: Founder, Advisor" in text
    assert "Forward Deployed Engineer" not in text


def test_prompt_without_profile_is_generic(monkeypatch, tmp_path):
    monkeypatch.setattr("career_ops_mcp.profile.PROFILE_FILE", tmp_path / "none.yml")
    text = server.evaluate_fit("Some JD text")
    assert "the user's AI job search advisor" in text
    assert "No archetypes are configured" in text


def test_tool_text_has_no_author_name():
    for fn in (server.match_cv_to_jd, server.get_cv, server.get_cv_section, server.evaluate_fit):
        assert "Eric" not in (fn.__doc__ or "")


def test_get_application_error_includes_path(monkeypatch, tmp_path):
    missing = Path(tmp_path) / "data" / "applications.md"
    monkeypatch.setattr(tools, "APPLICATIONS_FILE", missing)
    result = tools.get_application("Acme")
    assert str(missing) in result["error"]
