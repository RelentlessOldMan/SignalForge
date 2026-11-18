"""Writes vectors/cases/exciter.json, stdlib only.

Harmonic exciter (conventions: Harmonic exciter; ADR 0288). The Linkwitz-Riley high band is the
stdlib Butterworth biquads of vectors/generators/crossover_split.py run in exact rationals; the
cubic soft clipper of ADR 0250 (u - u^3/3 inside [-1, 1], +-2/3 beyond) and the sum are stdlib
floats.

Run from the repo root: python vectors/generators/exciter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-11}
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


def clip(u):
    if abs(u) < 1:
        return u - u * u * u / 3
    return math.copysign(2.0 / 3.0, u)


def add(cid, x, order, fc, fs, drive, mix, why):
    n = order // 2
    hi = butterworth(n, fc, fs, True)
    high = [list(r) for r in hi + hi]
    if n % 2:
        high[0][:3] = [-v for v in high[0][:3]]
    h = run(high, x)
    y = [v + mix * (clip(drive * w) / drive) for v, w in zip(x, h)]
    if mix == 0:
        assert y == x
    cases.append({"id": f"exciter.{cid}", "op": "exciter",
                  "args": {"samples": x, "order": order, "cutoff": fc, "sample_rate": fs,
                           "drive": drive, "mix": mix},
                  "expected": y, "tol": TOL, "source": why})


M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05]
add("gentle", M, 4, 0.2, 1.0, 0.5, 0.5, "LR4 at 0.2 fs, drive 1/2: mostly inside the clipper")
add("hard", M, 4, 0.2, 1.0, 8.0, 1.0, "LR4 at 0.2 fs, drive 8: the high band mostly held")
add("lr2_khz", M, 2, 3000.0, 48000.0, 2.0, 0.25, "LR2 at 3 kHz, fs 48 kHz: high band inverted")
add("mix_zero", M, 4, 0.2, 1.0, 2.0, 0.0, "mix 0: the input")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "order": 4, "cutoff": 1.0, "sample_rate": 8.0,
            "drive": 1.0, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"exciter.{cid}", "op": "exciter", "args": base,
                  "error": "invalid_argument", "source": why})


err("drive_zero", "drive must be positive", drive=0.0)
err("mix_high", "mix must be at most 1", mix=1.5)
err("order_odd", "order must be even", order=3)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "exciter",
    "description": "Harmonic exciter (conventions: Harmonic exciter; ADR 0288).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "exciter.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/exciter.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
