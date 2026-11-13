"""Cross-language checks: diff two conformance reports, or two QPSK link reports.

Command line (exit code 0 when they agree, 1 when they do not, 2 for bad input)::

    python -m signalforge.compare reports A.json B.json [--vectors DIR]
    python -m signalforge.compare link A.json B.json
    python -m signalforge.compare run-link CONFIG.json [--out PATH]

``reports`` takes the files written by ``python -m signalforge.conformance --report`` and by the C#
``SignalForge.Conformance --report``. ``link`` takes two ``qpsk_link`` JSON reports of the same
config, from either language; ``run-link`` writes the Python one. The rules are in
``docs/testing.md`` (Cross-language checks).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from . import link
from .conformance import DEFAULT_TOL, compare, decode, find_vectors_dir, iter_cases

# Noiseless link reports come from the same arithmetic in a different order.
NOISELESS_TOL = {"abs": 1e-9, "rel": 1e-9}


def _fields(a: Any, b: Any, path: str = "") -> list[str]:
    """Record fields present on one side only, at any depth (``compare`` checks only one side's)."""
    if not (isinstance(a, dict) and isinstance(b, dict)) or {"re", "im"} == set(a) == set(b):
        return []
    out = [f"{path}{k}: only in the first" for k in sorted(a.keys() - b.keys())]
    out += [f"{path}{k}: only in the second" for k in sorted(b.keys() - a.keys())]
    for k in sorted(a.keys() & b.keys()):
        out += _fields(a[k], b[k], f"{path}{k}.")
    return out


def compare_reports(a: dict[str, Any], b: dict[str, Any], vectors_dir: Path) -> list[str]:
    """Differences between two conformance reports.

    Every case must be in both, pass or fail in both, and give actuals with the same fields that
    agree within the case's own tolerance. Cases the reports have but the vectors do not are listed
    too.
    """
    na, nb = a.get("implementation", "a"), b.get("implementation", "b")
    tols = {(f, c["id"]): {**DEFAULT_TOL, **c.get("tol", {})} for f, c in iter_cases(vectors_dir)}
    ca = {(c["file"], c["id"]): c for c in a["cases"]}
    cb = {(c["file"], c["id"]): c for c in b["cases"]}
    out = [f"{f} {i}: only in {na}" for f, i in ca.keys() - cb.keys()]
    out += [f"{f} {i}: only in {nb}" for f, i in cb.keys() - ca.keys()]
    for key in sorted(ca.keys() & cb.keys()):
        f, i = key
        x, y = ca[key], cb[key]
        if key not in tols:
            out.append(f"{f} {i}: not in the vectors")
            continue
        if x["passed"] != y["passed"]:
            state = {True: "passes", False: "fails"}
            out.append(f"{f} {i}: {state[x['passed']]} in {na}, {state[y['passed']]} in {nb}")
            continue
        if x.get("actual") is None or y.get("actual") is None:
            if (x.get("actual") is None) != (y.get("actual") is None):
                out.append(f"{f} {i}: a result in only one of {na} and {nb}")
            continue
        msgs = _fields(x["actual"], y["actual"])
        msgs = msgs or compare(decode(x["actual"]), decode(y["actual"]), tols[key])
        out += [f"{f} {i}: {na} vs {nb}: {m}" for m in msgs]
    return sorted(out)


def compare_link_reports(a: dict[str, Any], b: dict[str, Any], z_max: float = 4.0) -> list[str]:
    """Differences between two ``qpsk_link`` reports of the same config.

    Without noise both runs are deterministic and every field must agree within
    ``NOISELESS_TOL``. With noise the random streams differ, so the counts must match, the frame
    must start at the same symbol, and the bit error rate and the mean squared EVM must agree
    within ``z_max`` standard deviations (two-sample tests; docs/testing.md). The theoretical BER
    depends only on the config and must agree as closely as a noiseless field.
    """
    out = _fields(a, b)
    if out:
        return out
    out = compare(decode(a["config"]), decode(b["config"]), NOISELESS_TOL)
    if out:
        return ["config: " + m for m in out]
    if a["config"]["eb_n0_db"] is None:
        return compare(decode(a), decode(b), NOISELESS_TOL)
    out = compare(decode(a["ber_theory"]), decode(b["ber_theory"]), NOISELESS_TOL, "ber_theory")
    ea, eb = a["bit_errors"], b["bit_errors"]
    for k, x, y in [
        ("frame_start", a["frame_start"], b["frame_start"]),
        ("bit_errors.compared", ea["compared"], eb["compared"]),
        ("evm.num_symbols", a["evm"]["num_symbols"], b["evm"]["num_symbols"]),
    ]:
        if x != y:
            out.append(f"{k}: {x} != {y}")
    if out:
        return out
    n = ea["compared"]
    p = (ea["errors"] + eb["errors"]) / (2 * n)
    sd = math.sqrt(2 * n * p * (1 - p))
    d = abs(ea["errors"] - eb["errors"])
    if d > 0 and d / sd > z_max:  # d > 0 means 0 < p < 1, so sd > 0
        out.append(f"bit_errors: {ea['errors']} vs {eb['errors']} of {n} ({d / sd:.1f} sd)")
    # |e|^2 of complex Gaussian error is exponential: its standard deviation equals its mean
    m = a["evm"]["num_symbols"]
    sa, sb = float(a["evm"]["rms"]) ** 2, float(b["evm"]["rms"]) ** 2
    sd = (sa + sb) / 2 * math.sqrt(2 / m)
    if sd > 0 and abs(sa - sb) / sd > z_max:
        out.append(f"evm.rms: {a['evm']['rms']} vs {b['evm']['rms']} ({abs(sa - sb) / sd:.1f} sd)")
    return out


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m signalforge.compare")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("reports", help="diff two conformance reports")
    r.add_argument("a", type=Path)
    r.add_argument("b", type=Path)
    r.add_argument("--vectors", type=Path, help="vectors/cases directory")
    lk = sub.add_parser("link", help="compare two qpsk_link reports of one config")
    lk.add_argument("a", type=Path)
    lk.add_argument("b", type=Path)
    run = sub.add_parser("run-link", help="run qpsk_link on a JSON config, print its report")
    run.add_argument("config", type=Path)
    run.add_argument("--out", type=Path, help="write the report here instead of printing it")
    ns = ap.parse_args(argv)
    try:
        if ns.cmd == "run-link":
            text = link.qpsk_link(link.QpskLinkConfig(**_load(ns.config))).to_json()
            if ns.out:
                ns.out.parent.mkdir(parents=True, exist_ok=True)
                ns.out.write_text(text + "\n", encoding="utf-8", newline="\n")
            else:
                print(text)
            return 0
        if ns.cmd == "reports":
            vectors = ns.vectors or find_vectors_dir(Path.cwd())
            diffs = compare_reports(_load(ns.a), _load(ns.b), vectors)
        else:
            diffs = compare_link_reports(_load(ns.a), _load(ns.b))
    except (OSError, ValueError, TypeError, KeyError) as e:
        print(f"error: {e!r}", file=sys.stderr)
        return 2
    for d in diffs:
        print(d)
    print("agree" if not diffs else f"{len(diffs)} differences")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
