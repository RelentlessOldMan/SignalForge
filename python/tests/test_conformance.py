"""Every case in vectors/cases must pass."""

from pathlib import Path
from typing import Any

import pytest

from signalforge import conformance

CASES = list(conformance.iter_cases(conformance.find_vectors_dir()))


@pytest.mark.parametrize(("file", "case"), CASES, ids=[f"{f}:{c['id']}" for f, c in CASES])
def test_vector(file: str, case: dict[str, Any]) -> None:
    result = conformance.run_case(file, case)
    assert result.passed, "; ".join(result.messages)


def test_every_case_has_a_source() -> None:
    missing = [c["id"] for _, c in CASES if not c.get("source")]
    assert not missing


def test_ids_unique_per_file() -> None:
    seen = set()
    for f, c in CASES:
        assert (f, c["id"]) not in seen
        seen.add((f, c["id"]))


SELFTEST = list(conformance.iter_cases(conformance.find_vectors_dir().parent / "selftest"))


@pytest.mark.parametrize(("file", "case"), SELFTEST, ids=[c["id"] for _, c in SELFTEST])
def test_runner_fails_a_wrong_case(file: str, case: dict[str, Any]) -> None:
    assert not conformance.run_case(file, case).passed, case["why"]


def test_main_writes_report(tmp_path: Path) -> None:
    report = tmp_path / "r.json"
    assert conformance.main([str(conformance.find_vectors_dir()), "--report", str(report)]) == 0
    assert '"implementation": "python"' in report.read_text()
