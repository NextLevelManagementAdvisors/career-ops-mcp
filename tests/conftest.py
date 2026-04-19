from pathlib import Path
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture()
def applications_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "applications.md"


@pytest.fixture()
def cv_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "cv.md"


@pytest.fixture()
def pipeline_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "pipeline.md"


@pytest.fixture()
def states_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "states.yml"


@pytest.fixture()
def portals_file(fixtures_dir: Path) -> Path:
    return fixtures_dir / "portals.yml"
