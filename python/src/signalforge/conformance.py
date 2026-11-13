"""Run the shared test vectors in ``vectors/cases``. Format described in vectors/README.md.

Usage: ``python -m signalforge.conformance [VECTORS_DIR] [--report FILE]``. Exit 0 when every case
passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from . import channel, dsp, measurements, metrics, modulation, spectral, units, waveforms

DEFAULT_TOL = {"abs": 1e-12, "rel": 1e-12}

OPS: dict[str, Callable[..., Any]] = {
    "lin_to_db": units.lin_to_db,
    "db_to_lin": units.db_to_lin,
    "amp_to_db": units.amp_to_db,
    "db_to_amp": units.db_to_amp,
    "w_to_dbm": units.w_to_dbm,
    "dbm_to_w": units.dbm_to_w,
    "vrms_to_dbm": units.vrms_to_dbm,
    "dbm_to_vrms": units.dbm_to_vrms,
    "tone": waveforms.tone,
    "prbs": waveforms.prbs,
    "power_stats": measurements.power_stats,
    "qpsk_map": modulation.qpsk_map,
    "qpsk_demap_hard": modulation.qpsk_demap_hard,
    "bit_errors": metrics.bit_errors,
    "fft": spectral.fft,
    "ifft": spectral.ifft,
    "fft_frequencies": spectral.fft_frequencies,
    "window": spectral.window,
    "window_stats": spectral.window_stats,
    "welch_psd": spectral.welch_psd,
    "occupied_bandwidth": spectral.occupied_bandwidth,
    "channel_power": spectral.channel_power,
    "convolve": dsp.convolve,
    "upsample": dsp.upsample,
    "rrc_taps": dsp.rrc_taps,
    "pulse_shape": dsp.pulse_shape,
    "frequency_offset": channel.frequency_offset,
    "evm": metrics.evm,
    "qpsk_ber_theory": metrics.qpsk_ber_theory,
}


class BadCase(Exception):
    """A vector case that is malformed (as opposed to one the library fails)."""


def decode(v: Any) -> Any:
    """JSON vector value to a Python value: complex objects, special floats, arrays."""
    if isinstance(v, str) and v in ("inf", "-inf", "nan"):
        return float(v)
    if isinstance(v, dict):
        if set(v) == {"re", "im"}:
            re, im = v["re"], v["im"]
            if isinstance(re, list):
                if not isinstance(im, list) or len(im) != len(re):
                    raise BadCase("re and im must be arrays of the same length")
                return np.asarray([decode(r) for r in re]) + 1j * np.asarray(
                    [decode(i) for i in im]
                )
            return complex(decode(re), decode(im))
        return {k: decode(x) for k, x in v.items()}
    if isinstance(v, list):
        return np.asarray([decode(x) for x in v])
    return v


def encode(v: Any) -> Any:
    """Python result to the JSON vector form (for reports)."""
    if dataclasses.is_dataclass(v) and not isinstance(v, type):
        return {f.name: encode(getattr(v, f.name)) for f in dataclasses.fields(v)}
    if isinstance(v, dict):
        return {k: encode(x) for k, x in v.items()}
    if isinstance(v, np.ndarray):
        if np.iscomplexobj(v):
            return {
                "re": [encode(float(x)) for x in v.real],
                "im": [encode(float(x)) for x in v.imag],
            }
        return [encode(x.item()) for x in v]
    if isinstance(v, complex | np.complexfloating):
        return {"re": encode(float(v.real)), "im": encode(float(v.imag))}
    if isinstance(v, np.generic):
        v = v.item()
    if isinstance(v, float) and not math.isfinite(v):
        return "nan" if math.isnan(v) else ("inf" if v > 0 else "-inf")
    return v


def _close(actual: complex | float, expected: complex | float, tol: dict[str, float]) -> bool:
    if isinstance(expected, float) and math.isnan(expected):
        return isinstance(actual, float | np.floating) and math.isnan(actual)
    if isinstance(expected, float) and math.isinf(expected):
        return bool(actual == expected)
    return bool(abs(actual - expected) <= tol["abs"] + tol["rel"] * abs(expected))


def _kind(v: Any) -> str:
    """The vector type of a value: bool, real, complex, array, or other."""
    if isinstance(v, bool | np.bool_):
        return "bool"
    if isinstance(v, np.ndarray):
        return "complex array" if np.iscomplexobj(v) else "real array"
    if isinstance(v, complex | np.complexfloating):
        return "complex"
    if isinstance(v, int | float | np.integer | np.floating):
        return "real"
    return type(v).__name__


def compare(actual: Any, expected: Any, tol: dict[str, float], path: str = "") -> list[str]:
    """Differences between an actual result and a decoded expected value, as messages.

    Types must match exactly (a real array is not a complex array, a scalar is not a one-element
    array); booleans compare exactly, numbers within ``tol``.
    """
    where = path or "value"
    if dataclasses.is_dataclass(actual) and not isinstance(actual, type):
        actual = {f.name: getattr(actual, f.name) for f in dataclasses.fields(actual)}
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{where}: expected a record, got {type(actual).__name__}"]
        out: list[str] = []
        for k, e in expected.items():
            p = f"{path}.{k}" if path else k
            out += compare(actual[k], e, tol, p) if k in actual else [f"{p}: missing"]
        return out
    if isinstance(actual, np.ndarray) and not np.iscomplexobj(actual) and actual.dtype != np.bool_:
        actual = np.asarray(actual, dtype=np.float64)  # uint8 bits and int arrays are real arrays
    ka, ke = _kind(actual), _kind(expected)
    if ka != ke:
        return [f"{where}: type {ka} does not match expected {ke}"]
    if ke == "bool":
        return (
            [] if bool(actual) == bool(expected) else [f"{where}: {actual} != expected {expected}"]
        )
    if isinstance(expected, np.ndarray):
        if actual.shape != expected.shape:
            return [f"{where}: shape {actual.shape} != expected {expected.shape}"]
        bad = [i for i in range(expected.size) if not _close(actual[i], expected[i], tol)]
        if bad:
            i = bad[0]
            return [f"{where}[{i}]: {actual[i]!r} != expected {expected[i]!r} ({len(bad)} differ)"]
        return []
    if not _close(actual, expected, tol):
        return [f"{where}: {actual!r} != expected {expected!r}"]
    return []


@dataclass
class CaseResult:
    file: str
    id: str
    passed: bool
    messages: list[str]
    actual: Any = None


def find_vectors_dir(start: Path | None = None) -> Path:
    """The repository's ``vectors/cases`` directory, searched upward from ``start``."""
    here = (start or Path(__file__)).resolve()
    for d in [here, *here.parents]:
        cand = d / "vectors" / "cases"
        if cand.is_dir():
            return cand
    raise FileNotFoundError("vectors/cases not found above " + str(here))


def iter_cases(vectors_dir: Path) -> Iterator[tuple[str, dict[str, Any]]]:
    for path in sorted(vectors_dir.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("schema") != 1:
            raise ValueError(f"{path.name}: unsupported schema {doc.get('schema')!r}")
        for case in doc["cases"]:
            yield path.name, case


def run_case(file: str, case: dict[str, Any]) -> CaseResult:
    cid = case["id"]
    op = OPS.get(case["op"])
    if op is None:
        return CaseResult(file, cid, False, [f"unknown op {case['op']!r}"])
    try:
        args = {k: decode(v) for k, v in case.get("args", {}).items()}
        expected = decode(case["expected"]) if "expected" in case else None
    except BadCase as e:
        return CaseResult(file, cid, False, [f"bad case: {e}"])
    tol = {**DEFAULT_TOL, **case.get("tol", {})}
    want_error = case.get("error")
    try:
        actual = op(**args)
    except TypeError as e:  # an unknown or missing argument: the case itself is wrong
        return CaseResult(file, cid, False, [f"bad case: {e}"])
    except ValueError as e:
        if want_error == "invalid_argument":
            return CaseResult(file, cid, True, [])
        return CaseResult(file, cid, False, [f"raised ValueError: {e}"])
    if want_error:
        return CaseResult(file, cid, False, [f"expected error {want_error!r}"], encode(actual))
    if "expected" not in case:
        return CaseResult(file, cid, False, ["bad case: no expected value or error"])
    msgs = compare(actual, expected, tol)
    return CaseResult(file, cid, not msgs, msgs, encode(actual))


def run_all(vectors_dir: Path) -> list[CaseResult]:
    return [run_case(f, c) for f, c in iter_cases(vectors_dir)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m signalforge.conformance")
    ap.add_argument("vectors", nargs="?", type=Path, help="vectors/cases directory")
    ap.add_argument("--report", type=Path, help="write a JSON report here")
    ns = ap.parse_args(argv)
    results = run_all(ns.vectors or find_vectors_dir(Path.cwd()))
    failed = [r for r in results if not r.passed]
    for r in failed:
        print(f"FAIL {r.file} {r.id}: {'; '.join(r.messages)}")
    print(f"{len(results) - len(failed)}/{len(results)} cases passed")
    if ns.report:
        ns.report.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "implementation": "python",
            "passed": len(results) - len(failed),
            "failed": len(failed),
            "cases": [dataclasses.asdict(r) for r in results],
        }
        ns.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
