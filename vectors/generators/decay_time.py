"""Writes vectors/cases/decay_time.json, stdlib only.

Decay time from a curve (conventions: Decay time from a curve; ADR 0184): n1, n2 the first
samples at or below start_db and stop_db, the least-squares slope m (dB/s) over n1 <= n < n2,
-60/m. Lines give -60/slope exactly; other curves have their slopes worked in fractions.

Run from the repo root: python vectors/generators/decay_time.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def slope_time(d, fs, a, b):
    d = [F(v) if v != "-inf" else None for v in d]
    n1 = next(i for i, v in enumerate(d) if v is None or v <= a)
    n2 = next(i for i, v in enumerate(d) if v is None or v <= b)
    ns = range(n1, n2)
    mn = F(sum(ns), len(ns))
    my = sum(d[n] for n in ns) / len(ns)
    m = sum((n - mn) * (d[n] - my) for n in ns) / sum((n - mn) ** 2 for n in ns) * F(fs)
    return -60 / m


def add(cid, d, fs, why, a=None, b=None):
    args = {"decay": d, "sample_rate": fs}
    if a is not None:
        args["start_db"] = a
    if b is not None:
        args["stop_db"] = b
    t = slope_time(d, fs, -5 if a is None else a, -25 if b is None else b)
    cases.append({"id": f"decay_time.{cid}", "op": "decay_time", "args": args,
                  "expected": float(t), "tol": TOL, "source": why})


LINE = [-0.5 * n for n in range(80)]
add("line", LINE, 100.0, "-0.5 dB per sample at 100 Hz: -50 dB/s, so -60/-50 = 1.2 s; "
    "fit over samples 10..49")
add("line_t30", LINE, 100.0, "the same line from -5 to -35 dB: 1.2 s", b=-35.0)
add("offset", [-2.25 - 0.5 * n for n in range(80)], 100.0,
    "the line shifted down 2.25 dB (not starting at 0): same slope, 1.2 s")
add("hand", [0.0, -6.0, -11.0, -14.0, -20.0, -27.0, -30.0], 10.0,
    "start 0, stop -20 (EDT-like, wider): n1 = 0, n2 = 4; points (0, 0), (1, -6), (2, -11), "
    "(3, -14): slope -4.7 dB/sample, -47 dB/s at 10 Hz, T = 60/47", a=0.0, b=-20.0)
add("ends_in_minus_inf", [0.0, -3.0, -6.0, -9.0, "-inf", "-inf"], 1000.0,
    "-3 dB per sample to -9, then -inf: n1 = 2 (first at or below -5), n2 = 4 (-inf is below "
    "-25); fit over samples 2 and 3: -3 dB per sample, -3000 dB/s at 1 kHz, T = 0.02 s")
add("non_monotonic", [0.0, -6.0, -4.0, -10.0, -26.0], 1.0,
    "n1 = 1 (first at or below -5), n2 = 4; points (1, -6), (2, -4), (3, -10): slope -2 dB/s at "
    "1 Hz, T = 30 s")


def err(cid, d, fs, why, a=None, b=None):
    args = {"decay": d, "sample_rate": fs}
    if a is not None:
        args["start_db"] = a
    if b is not None:
        args["stop_db"] = b
    cases.append({"id": f"decay_time.{cid}", "op": "decay_time", "args": args,
                  "error": "invalid_argument", "source": why})


err("never_reaches", [-0.5 * n for n in range(20)], 100.0, "ends at -9.5 dB, never -25")
err("too_few", [0.0, -10.0, -30.0], 100.0, "n1 = 1, n2 = 2: one sample in the fit")
err("rising", [0.0, -6.0, -5.5, -5.2, -30.0], 100.0,
    "n1 = 1, n2 = 4; points -6, -5.5, -5.2 rise: positive slope")
err("nan", [0.0, "nan", -30.0], 100.0, "NaN in the curve")
err("plus_inf", [0.0, "inf", -30.0], 100.0, "+inf in the curve")
err("empty", [], 100.0, "empty curve")
err("zero_rate", LINE, 0.0, "sample_rate must be positive")
err("levels", LINE, 100.0, "stop_db must be below start_db", a=-25.0, b=-5.0)
err("start_above_zero", LINE, 100.0, "start_db must be at most 0", a=1.0)

doc = {
    "schema": 1,
    "suite": "decay_time",
    "description": "Decay time from a curve (conventions: Decay time from a curve; ADR 0184).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "decay_time.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/decay_time.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
