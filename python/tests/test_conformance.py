"""Every case in vectors/cases must pass."""

import pytest

from signalforge import conformance

CASES = list(conformance.iter_cases(conformance.find_vectors_dir()))


@pytest.mark.parametrize(("file", "case"), CASES, ids=[f"{f}:{c['id']}" for f, c in CASES])
def test_vector(file, case):
    result = conformance.run_case(file, case)
    assert result.passed, "; ".join(result.messages)


def test_every_case_has_a_source():
    missing = [c["id"] for _, c in CASES if not c.get("source")]
    assert not missing


def test_ids_unique_per_file():
    seen = set()
    for f, c in CASES:
        assert (f, c["id"]) not in seen
        seen.add((f, c["id"]))


def test_comparison_catches_a_wrong_value():
    case = {"id": "x", "op": "lin_to_db", "args": {"x": 10}, "expected": 10.001, "source": "t"}
    assert not conformance.run_case("t.json", case).passed


def test_main_writes_report(tmp_path):
    report = tmp_path / "r.json"
    assert conformance.main([str(conformance.find_vectors_dir()), "--report", str(report)]) == 0
    assert '"implementation": "python"' in report.read_text()
