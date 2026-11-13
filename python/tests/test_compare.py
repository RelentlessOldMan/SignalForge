"""The cross-language compare tool."""

from __future__ import annotations

import copy
import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from signalforge import QpskLinkConfig, conformance, qpsk_link
from signalforge import compare as cmp

VECTORS = conformance.find_vectors_dir()


@pytest.fixture(scope="module")
def report() -> dict[str, Any]:
    results = conformance.run_all(VECTORS)
    rep = {"implementation": "python", "cases": [dataclasses.asdict(r) for r in results]}
    out: dict[str, Any] = json.loads(json.dumps(rep))  # as written to a file and read back
    return out


def _case(rep: dict[str, Any], cid: str) -> dict[str, Any]:
    return next(c for c in rep["cases"] if c["id"] == cid)


def test_a_report_agrees_with_itself(report: dict[str, Any]) -> None:
    assert cmp.compare_reports(report, copy.deepcopy(report), VECTORS) == []


def test_reports_differing_beyond_the_case_tolerance(report: dict[str, Any]) -> None:
    other = copy.deepcopy(report)
    other["implementation"] = "dotnet"
    _case(other, "lin_to_db.1000")["actual"] += 1e-9
    _case(other, "lin_to_db.2")["actual"] += 1e-13  # inside the default tolerance
    diffs = cmp.compare_reports(report, other, VECTORS)
    assert len(diffs) == 1
    assert diffs[0].startswith("units.json lin_to_db.1000: python vs dotnet")


def test_reports_missing_and_failing_cases(report: dict[str, Any]) -> None:
    other = copy.deepcopy(report)
    other["implementation"] = "dotnet"
    gone = other["cases"].pop(0)
    _case(other, "lin_to_db.1000")["passed"] = False
    diffs = cmp.compare_reports(report, other, VECTORS)
    assert f"{gone['file']} {gone['id']}: only in python" in diffs
    assert "units.json lin_to_db.1000: passes in python, fails in dotnet" in diffs


def test_a_case_not_in_the_vectors(report: dict[str, Any]) -> None:
    extra = {**report, "cases": [*report["cases"], {**report["cases"][0], "id": "made.up"}]}
    diffs = cmp.compare_reports(extra, copy.deepcopy(extra), VECTORS)
    assert diffs == [f"{report['cases'][0]['file']} made.up: not in the vectors"]


def _link(**kw: Any) -> dict[str, Any]:
    d: dict[str, Any] = json.loads(qpsk_link(QpskLinkConfig(**kw)).to_json())
    return d


NOISY = {"num_symbols": 20_000, "eb_n0_db": 6.0, "frequency_offset_hz": 20.0, "phase": 1.0}


def test_noisy_links_with_different_noise_agree() -> None:
    a, b = _link(**NOISY, seed=1), _link(**NOISY, seed=2)
    assert a["bit_errors"]["errors"] != b["bit_errors"]["errors"]
    b["config"]["seed"] = 1  # the other language's stream differs the same way
    assert cmp.compare_link_reports(a, b) == []


def test_noisy_links_that_disagree() -> None:
    a = _link(**NOISY, seed=1)
    b = copy.deepcopy(a)
    b["bit_errors"]["errors"] *= 2  # about 100 against 200: some 8 standard deviations
    b["evm"]["rms"] *= 1.1  # 21% in power over 20000 symbols: about 20 standard deviations
    diffs = cmp.compare_link_reports(a, b)
    assert [d.split(":")[0] for d in diffs] == ["bit_errors", "evm.rms"]
    c = copy.deepcopy(a)
    c["frame_start"] += 1
    assert cmp.compare_link_reports(a, c) == [
        f"frame_start: {a['frame_start']} != {c['frame_start']}"
    ]


def test_links_of_different_configs() -> None:
    a, b = _link(num_symbols=50), _link(num_symbols=50, phase=0.1)
    assert cmp.compare_link_reports(a, b)[0].startswith("config: phase")


def test_noiseless_links_compare_every_field() -> None:
    a = _link(num_symbols=300, frequency_offset_hz=-45.0, phase=-1.2, delay_samples=5)
    b = copy.deepcopy(a)
    assert cmp.compare_link_reports(a, b) == []
    b["frequency_offset_hz"] += 1e-6
    assert cmp.compare_link_reports(a, b)[0].startswith("frequency_offset_hz")


def test_command_line(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cfg = tmp_path / "cfg.json"
    cfg.write_text(json.dumps({"num_symbols": 64, "eb_n0_db": 8.0}), encoding="utf-8")
    assert cmp.main(["run-link", str(cfg)]) == 0
    out = tmp_path / "r.json"
    out.write_text(capsys.readouterr().out, encoding="utf-8")
    assert cmp.main(["link", str(out), str(out)]) == 0
    assert capsys.readouterr().out.strip() == "agree"
    cfg.write_text(json.dumps({"num_symbols": 64, "bogus": 1}), encoding="utf-8")
    assert cmp.main(["run-link", str(cfg)]) == 2
    assert cmp.main(["link", str(out), str(tmp_path / "missing.json")]) == 2


def test_a_field_on_one_side_only(report: dict[str, Any]) -> None:
    other = copy.deepcopy(report)
    rec = next(c for c in other["cases"] if isinstance(c["actual"], dict) and "rms" in c["actual"])
    rec["actual"]["extra"] = 1.0
    diffs = cmp.compare_reports(report, other, VECTORS)
    assert diffs == [f"{rec['file']} {rec['id']}: python vs python: extra: only in the second"]
    a = _link(num_symbols=50)
    b = copy.deepcopy(a)
    del b["evm"]["peak"]
    assert cmp.compare_link_reports(a, b) == ["evm.peak: only in the first"]


def test_noisy_links_must_share_the_theoretical_ber() -> None:
    a = _link(**NOISY, seed=1)
    b = copy.deepcopy(a)
    b["ber_theory"] *= 1.01
    assert cmp.compare_link_reports(a, b)[0].startswith("ber_theory")
