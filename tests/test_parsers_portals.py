from pathlib import Path
from career_ops_mcp.parsers.portals import parse


def test_parse_count(portals_file: Path) -> None:
    portals = parse(portals_file)
    assert len(portals) == 3


def test_enabled_filter(portals_file: Path) -> None:
    portals = parse(portals_file)
    enabled = [p for p in portals if p.enabled]
    assert len(enabled) == 2


def test_first_portal(portals_file: Path) -> None:
    p = parse(portals_file)[0]
    assert p.name == "Acme Corp"
    assert "acme.example.com" in p.careers_url
    assert p.api is not None
    assert p.enabled is True


def test_to_dict_keys(portals_file: Path) -> None:
    p = parse(portals_file)[0]
    d = p.to_dict()
    assert "name" in d
    assert "careers_url" in d
    assert "enabled" in d
