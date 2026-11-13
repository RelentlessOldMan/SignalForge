import re
from pathlib import Path

import signalforge


def test_version_matches_repo_version_file() -> None:
    # VERSION at the repo root is the source of truth; build.ps1 stamps __version__ from it.
    root = next(d for d in Path(__file__).resolve().parents if (d / "VERSION").is_file())
    assert signalforge.__version__ == (root / "VERSION").read_text(encoding="ascii").strip()


def test_version_is_date_based_without_leading_zeros() -> None:
    assert re.fullmatch(r"[1-9]\d{3}\.[1-9]\d?\.[1-9]\d?\.(0|[1-9]\d*)", signalforge.__version__)
