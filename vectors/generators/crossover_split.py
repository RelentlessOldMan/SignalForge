"""Writes vectors/cases/crossover_split.json, stdlib only.

Two-band splitter (conventions: Two-band splitter; ADR 0285). The Linkwitz-Riley bands are the
stdlib Butterworth biquads of conventions: Butterworth design, twice over, with the first high
section's numerator negated when the Butterworth order is odd. Each section runs as its
difference equation, from rest, in exact rationals at the float coefficients.

Run from the repo root: python vectors/generators/crossover_split.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def butterworth(order, cutoff, fs, high):
    k = math.tan(math.pi * cutoff / fs)
    rows = []
    if order % 2:
        if high:
            rows.append([1 / (k + 1), -1 / (k + 1), 0.0, 1.0, (k - 1) / (k + 1), 0.0])
        else:
            rows.append([k / (k + 1), k / (k + 1), 0.0, 1.0, (k - 1) / (k + 1), 0.0])
    for i in range(order // 2 - 1, -1, -1):
        iq = 2 * math.sin(math.pi * (2 * i + 1) / (2 * order))
        d = k * k + k * iq + 1
        a = [1.0, 2 * (k * k - 1) / d, (k * k - k * iq + 1) / d]
        b = [1 / d, -2 / d, 1 / d] if high else [k * k / d, 2 * k * k / d, k * k / d]
        rows.append(b + a)
    return rows


def run(rows, x):
    y = [Fr(v) for v in x]
    for b0, b1, b2, a0, a1, a2 in rows:
        b0, b1, b2, a1, a2 = (Fr(v) for v in (b0, b1, b2, a1, a2))
        assert a0 == 1
        out = []
        for n in range(len(y)):
            acc = b0 * y[n]
            if n >= 1:
                acc += b1 * y[n - 1] - a1 * out[n - 1]
            if n >= 2:
                acc += b2 * y[n - 2] - a2 * out[n - 2]
            out.append(acc)
        y = out
    return [float(v) for v in y]


def add(cid, x, order, fc, fs, why):
    n = order // 2
    lo, hi = butterworth(n, fc, fs, False), butterworth(n, fc, fs, True)
    high = [list(r) for r in hi + hi]
    if n % 2:
        high[0][:3] = [-v for v in high[0][:3]]
    cases.append({"id": f"crossover_split.{cid}", "op": "crossover_split",
                  "args": {"samples": x, "order": order, "cutoff": fc, "sample_rate": fs},
                  "expected": {"low": run(lo + lo, x), "high": run(high, x)}, "tol": TOL,
                  "source": why})


IMP = [1.0] + [0.0] * 15
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05]
add("lr4_impulse", IMP, 4, 0.125, 1.0, "LR4 at fs/8: impulse responses of both bands")
add("lr2", M, 2, 1000.0, 8000.0, "LR2 at 1 kHz, fs 8 kHz: high band inverted")
add("lr6", M, 6, 0.3, 1.0, "LR6 at 0.3 fs: high band inverted")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "order": 4, "cutoff": 1.0, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"crossover_split.{cid}", "op": "crossover_split", "args": base,
                  "error": "invalid_argument", "source": why})


err("order_odd", "order must be even", order=3)
err("cutoff_nyquist", "cutoff must be below fs/2", cutoff=4.0)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "crossover_split",
    "description": "Two-band splitter (conventions: Two-band splitter; ADR 0285).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "crossover_split.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/crossover_split.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
