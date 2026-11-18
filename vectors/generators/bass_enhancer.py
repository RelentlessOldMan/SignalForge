"""Writes vectors/cases/bass_enhancer.json, stdlib only.

Bass enhancer (conventions: Bass enhancer; ADR 0290). Both Linkwitz-Riley bands are the stdlib
Butterworth biquads of vectors/generators/crossover_split.py run in exact rationals and rounded
once; the cubic soft clipper of ADR 0250 (u - u^3/3 inside [-1, 1], +-2/3 beyond) and the sum
are stdlib floats.

Run from the repo root: python vectors/generators/bass_enhancer.py [--check]
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


def lr(order, fc, fs):
    n = order // 2
    lo, hi = butterworth(n, fc, fs, False), butterworth(n, fc, fs, True)
    high = [list(r) for r in hi + hi]
    if n % 2:
        high[0][:3] = [-v for v in high[0][:3]]
    return lo + lo, high


def add(cid, x, order, fc, fs, drive, mix, why):
    low, high = lr(order, fc, fs)
    c = [clip(drive * v) / drive for v in run(low, x)]
    h = run(high, c)
    y = [v + mix * w for v, w in zip(x, h)]
    cases.append({"id": f"bass_enhancer.{cid}", "op": "bass_enhancer",
                  "args": {"samples": x, "order": order, "cutoff": fc, "sample_rate": fs,
                           "drive": drive, "mix": mix},
                  "expected": y, "tol": TOL, "source": why})


S = [0.9 * math.sin(2 * math.pi * n / 16) for n in range(16)]
M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05]
add("sine", S, 4, 0.1, 1.0, 2.0, 1.0, "sine at fs/16, LR4 at 0.1 fs, drive 2, fully added")
add("mixed", M, 4, 0.15, 1.0, 4.0, 0.5, "LR4 at 0.15 fs, drive 4: low band partly held")
add("lr2_hz", M, 2, 120.0, 8000.0, 1.0, 0.3, "LR2 at 120 Hz, fs 8 kHz: high band inverted")
add("mix_zero", M, 4, 0.15, 1.0, 4.0, 0.0, "mix 0: the input")
assert cases[-1]["expected"] == M


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "order": 4, "cutoff": 1.0, "sample_rate": 8.0,
            "drive": 1.0, "mix": 0.5}
    base.update(args)
    cases.append({"id": f"bass_enhancer.{cid}", "op": "bass_enhancer", "args": base,
                  "error": "invalid_argument", "source": why})


err("drive_negative", "drive must be positive", drive=-1.0)
err("mix_high", "mix must be at most 1", mix=2.0)
err("cutoff_zero", "cutoff must be positive", cutoff=0.0)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "bass_enhancer",
    "description": "Bass enhancer (conventions: Bass enhancer; ADR 0290).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bass_enhancer.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bass_enhancer.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
