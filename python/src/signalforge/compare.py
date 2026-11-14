"""Cross-language checks: diff two conformance reports, or two QPSK link reports.

Command line (exit code 0 when they agree, 1 when they do not, 2 for bad input)::

    python -m signalforge.compare reports A.json B.json [--vectors DIR]
    python -m signalforge.compare link A.json B.json
    python -m signalforge.compare run-link CONFIG.json [--out PATH]
    python -m signalforge.compare write-files DIR
    python -m signalforge.compare read-files DIR [--out PATH]
    python -m signalforge.compare files A.json B.json

``reports`` takes the files written by ``python -m signalforge.conformance --report`` and by the C#
``SignalForge.Conformance --report``. ``link`` takes two ``qpsk_link`` JSON reports of the same
config, from either language; ``run-link`` writes the Python one. ``write-files`` writes one
recording per datatype into DIR, ``read-files`` reads every recording in DIR into a report, and
``files`` checks two such reports of the same DIR (one from each language) agree. The rules are in
``docs/testing.md`` (Cross-language checks).
"""

from __future__ import annotations

import argparse
import cmath
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

from . import files, link
from .conformance import DEFAULT_TOL, compare, decode, find_vectors_dir, iter_cases
from .core import Signal

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
    depends only on the config and must agree as closely as a noiseless field. FSK reports have no
    EVM (``null``); both must agree on that.
    """
    out = _fields(a, b)
    if out:
        return out
    out = compare(decode(a["config"]), decode(b["config"]), NOISELESS_TOL)
    if out:
        return ["config: " + m for m in out]
    if a["config"]["eb_n0_db"] is None:
        da, db = decode(a), decode(b)
        if all(isinstance(v, dict) and v["rms"] <= 1e-9 for v in (da["evm"], db["evm"])):
            # an exact recovery (OFDM): the error is rounding, its dB and peak index are noise
            for v in (da["evm"], db["evm"]):
                del v["rms_db"], v["peak_index"]
        return compare(da, db, NOISELESS_TOL)
    out = compare(decode(a["ber_theory"]), decode(b["ber_theory"]), NOISELESS_TOL, "ber_theory")
    ea, eb = a["bit_errors"], b["bit_errors"]
    va, vb = a["evm"], b["evm"]
    if (va is None) != (vb is None):
        return [*out, f"evm: {va} != {vb}"]
    for k, x, y in [
        ("frame_start", a["frame_start"], b["frame_start"]),
        ("bit_errors.compared", ea["compared"], eb["compared"]),
        ("evm.num_symbols", va and va["num_symbols"], vb and vb["num_symbols"]),
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
    if va is None or a["config"].get("multipath_delays") is not None:
        # over multipath the EVM is a mean of unequal parts, led by the weakest subcarriers'
        # estimates (OFDM) or by the equalizer's adaptation noise (single carrier): no per-symbol
        # standard deviation fits it (docs/testing.md)
        return out
    # |e|^2 of complex Gaussian error is exponential: its standard deviation equals its mean
    m = va["num_symbols"]
    sa, sb = float(va["rms"]) ** 2, float(vb["rms"]) ** 2
    sd = (sa + sb) / 2 * math.sqrt(2 / m)
    if sd > 0 and abs(sa - sb) / sd > z_max:
        out.append(f"evm.rms: {va['rms']} vs {vb['rms']} ({abs(sa - sb) / sd:.1f} sd)")
    return out


EXCHANGE_DATATYPES = [
    f"{k}{t}{o}"
    for k in "cr"
    for t, orders in [
        ("f64", "lb"),
        ("f32", "lb"),
        ("i32", "lb"),
        ("i16", "lb"),
        ("i8", ""),
        ("u32", "lb"),
        ("u16", "lb"),
        ("u8", ""),
    ]
    for o in ([f"_{c}e" for c in orders] or [""])
]


def exchange_signal(datatype: str, writer: str) -> Signal:
    """The recording both languages write for one datatype (conventions: Signal files)."""
    n = range(64)
    amp = [0.45 * (1 + math.cos(2 * math.pi * k / 64)) for k in n]
    z = [a * cmath.exp(2j * math.pi * 0.05 * k) for a, k in zip(amp, n, strict=True)]
    is_complex = datatype[0] == "c"
    return Signal(
        np.array(z) if is_complex else np.array([v.real for v in z]),
        48000.0,
        center_frequency=915e6 if is_complex else 0.0,
        time_origin=-0.25,
        units="V",
        impedance=50.0,
        metadata={
            "writer": writer,
            "run": 7,
            "gains": [1, 2.5],
            "core:author": "signalforge",
            "core:annotations": [
                {"core:sample_start": 8, "core:sample_count": 16, "core:label": "burst"},
                {"core:sample_start": 40, "core:comment": "marker"},
            ],
        },
    )


def write_exchange_files(directory: Path, writer: str = "python") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for dt in EXCHANGE_DATATYPES:
        files.write_sigmf(directory / f"{writer}-{dt}", exchange_signal(dt, writer), dt)


def read_files_report(directory: Path) -> dict[str, Any]:
    """Every recording in ``directory``, decoded: the report ``files`` compares."""
    out: dict[str, Any] = {}
    for meta in sorted(directory.glob("*.sigmf-meta")):
        s = files.read_sigmf(meta)
        x = np.asarray(s.samples)
        out[meta.name.removesuffix(".sigmf-meta")] = {
            "re": x.real.tolist(),
            "im": x.imag.tolist() if np.iscomplexobj(x) else None,
            "sample_rate": s.sample_rate,
            "center_frequency": s.center_frequency,
            "time_origin": s.time_origin,
            "units": s.units,
            "impedance": s.impedance,
            "metadata": dict(s.metadata),
        }
    return {"files": out}


def _diff(a: Any, b: Any, path: str = "") -> list[str]:
    """Every difference between two JSON values, exactly (numbers compare by value)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = [f"{path}{k}: on one side only" for k in sorted(a.keys() ^ b.keys())]
        return out + [
            d for k in sorted(a.keys() & b.keys()) for d in _diff(a[k], b[k], f"{path}{k}.")
        ]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        pairs = enumerate(zip(a, b, strict=True))
        return [d for i, (x, y) in pairs for d in _diff(x, y, f"{path}{i}.")]
    same = type(a) is type(b) or {type(a), type(b)} <= {int, float}
    return [] if same and a == b else [f"{path.rstrip('.') or 'value'}: {a!r} != {b!r}"]


def _step(datatype: str) -> float:
    t = datatype[1:4].rstrip("_")
    bits = {"f64": 0, "f32": 24, "32": 31, "16": 15, "8": 7}[t if t[0] == "f" else t[1:]]
    return 2.0**-bits if bits else 0.0


def compare_file_reports(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """Both languages read the same files identically, and each language's recording of a datatype
    matches the other's to within one quantization step (they come from the same formula)."""
    fa, fb = a["files"], b["files"]
    out = [f"{n}: read by only one side" for n in sorted(set(fa) ^ set(fb))]
    out += [f"{n}: {d}" for n in sorted(set(fa) & set(fb)) for d in _diff(fa[n], fb[n])]
    for dt in EXCHANGE_DATATYPES:
        pairs = [fa.get(f"{w}-{dt}") for w in ("python", "dotnet")]
        if pairs[0] is None or pairs[1] is None:
            out.append(f"{dt}: a recording is missing from one writer")
            continue
        p, d = ({k: v for k, v in r.items() if k not in ("re", "im", "metadata")} for r in pairs)
        out += [f"{dt} python vs dotnet: {x}" for x in _diff(p, d)]
        mp, md = ({k: v for k, v in r["metadata"].items() if k != "writer"} for r in pairs)
        out += [f"{dt} python vs dotnet metadata: {x}" for x in _diff(mp, md)]
        tol = _step(dt) + 1e-12
        for part in ("re", "im"):
            xp, xd = pairs[0][part], pairs[1][part]
            if (xp is None) != (xd is None) or (xp is not None and len(xp) != len(xd)):
                out.append(f"{dt} python vs dotnet: {part} shapes differ")
            elif (
                xp is not None
                and (err := max((abs(u - v) for u, v in zip(xp, xd, strict=True)), default=0)) > tol
            ):
                out.append(f"{dt} python vs dotnet: {part} differs by {err:.3g} (> {tol:.3g})")
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
    wf = sub.add_parser("write-files", help="write the exchange recordings into DIR")
    wf.add_argument("dir", type=Path)
    rf = sub.add_parser("read-files", help="read every recording in DIR, print the report")
    rf.add_argument("dir", type=Path)
    rf.add_argument("--out", type=Path, help="write the report here instead of printing it")
    fc = sub.add_parser("files", help="compare two read-files reports of one DIR")
    fc.add_argument("a", type=Path)
    fc.add_argument("b", type=Path)
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
        if ns.cmd == "write-files":
            write_exchange_files(ns.dir)
            return 0
        if ns.cmd == "read-files":
            text = json.dumps(read_files_report(ns.dir), indent=1)
            if ns.out:
                ns.out.parent.mkdir(parents=True, exist_ok=True)
                ns.out.write_text(text + "\n", encoding="utf-8", newline="\n")
            else:
                print(text)
            return 0
        if ns.cmd == "files":
            diffs = compare_file_reports(_load(ns.a), _load(ns.b))
        elif ns.cmd == "reports":
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
