from pathlib import Path
from career_ops_mcp.parsers.states import parse


def test_state_count(states_file: Path) -> None:
    idx = parse(states_file)
    assert len(idx.states) == 7


def test_normalize_canonical(states_file: Path) -> None:
    idx = parse(states_file)
    assert idx.normalize("evaluated") == "evaluated"
    assert idx.normalize("Evaluated") == "evaluated"
    assert idx.normalize("EVALUATED") == "evaluated"


def test_normalize_alias(states_file: Path) -> None:
    idx = parse(states_file)
    assert idx.normalize("aplicado") == "applied"
    assert idx.normalize("enviada") == "applied"
    assert idx.normalize("sent") == "applied"
    assert idx.normalize("entrevista") == "interview"
    assert idx.normalize("rechazado") == "rejected"


def test_normalize_unknown(states_file: Path) -> None:
    idx = parse(states_file)
    assert idx.normalize("gibberish") is None


def test_to_dict(states_file: Path) -> None:
    idx = parse(states_file)
    d = idx.states[0].to_dict()
    assert "id" in d
    assert "label" in d
    assert "aliases" in d
    assert "description" in d
