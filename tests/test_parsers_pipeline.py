from pathlib import Path
from career_ops_mcp.parsers.pipeline import parse


def test_pending_bucket(pipeline_file: Path) -> None:
    buckets = parse(pipeline_file)
    assert len(buckets["pending"]) == 3


def test_processed_bucket(pipeline_file: Path) -> None:
    buckets = parse(pipeline_file)
    assert len(buckets["processed"]) == 1
    entry = buckets["processed"][0]
    assert entry.evaluated_num == 1
    assert entry.score == 3.2
    assert "OldCo" in entry.company


def test_pendientes_bucket(pipeline_file: Path) -> None:
    buckets = parse(pipeline_file)
    assert len(buckets["pendientes"]) == 1
    assert "Empresa SA" in buckets["pendientes"][0].company


def test_unchecked_has_no_num(pipeline_file: Path) -> None:
    buckets = parse(pipeline_file)
    for entry in buckets["pending"]:
        assert entry.evaluated_num is None
        assert entry.score is None


def test_url_parsed(pipeline_file: Path) -> None:
    entry = parse(pipeline_file)["pending"][0]
    assert entry.url.startswith("https://")
