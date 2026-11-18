"""Writes vectors/cases/rotary.json, stdlib only.

Rotary-speaker effect (conventions: Rotary-speaker effect; ADR 0292). The Linkwitz-Riley bands
are the stdlib Butterworth biquads of vectors/generators/crossover_split.py in exact rationals,
each rounded once; the vibrato read (vectors/generators/vibrato.py) and the tremolo gains
(vectors/generators/tremolo.py) are stdlib floats.

Run from the repo root: python vectors/generators/rotary.py [--check]
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


def filt(rows, x):
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


def vib(x, delay, depth, rate, fs):
    w = 2.0 * math.pi * rate
    y = []
    for n in range(len(x)):
        p = n - (delay + depth * math.cos(w * (n / fs)))
        i = math.floor(p)
        f = p - i
        lo = x[i] if i >= 0 else 0.0
        hi = x[i + 1] if i + 1 >= 0 and f > 0 else 0.0
        if isinstance(lo, complex) or isinstance(hi, complex):
            lo, hi = complex(lo), complex(hi)
            y.append(complex(lo.real * (1 - f) + hi.real * f, lo.imag * (1 - f) + hi.imag * f))
        else:
            y.append(lo * (1 - f) + hi * f)
    return y


def gains(size, rate, depth, fs):
    out = []
    for n in range(size):
        c = math.cos(2.0 * math.pi * rate * (n / fs))
        out.append(1 - depth * (1 - c) / 2)
    return out


def add(cid, x, order, fc, hr, dr, delay, depth, td, fs, why):
    n = order // 2
    lo, hi = butterworth(n, fc, fs, False), butterworth(n, fc, fs, True)
    high = [list(r) for r in hi + hi]
    if n % 2:
        high[0][:3] = [-v for v in high[0][:3]]
    low_b, high_b = filt(lo + lo, x), filt(high, x)
    horn = [v * g for v, g in zip(vib(high_b, delay, depth, hr, fs), gains(len(x), hr, td, fs))]
    drum = [v * g for v, g in zip(low_b, gains(len(x), dr, td, fs))]
    cases.append({"id": f"rotary.{cid}", "op": "rotary",
                  "args": {"samples": x, "order": order, "cutoff": fc, "horn_rate": hr,
                           "drum_rate": dr, "delay": delay, "depth": depth,
                           "tremolo_depth": td, "sample_rate": fs},
                  "expected": [u + v for u, v in zip(horn, drum)], "tol": TOL, "source": why})


M = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05, 0.9, -0.4, 0.6, -1.0]
add("still", M, 4, 0.2, 0.0, 0.0, 2.0, 0.0, 0.5, 1.0,
    "rates 0: the bands summed with the high band delayed by 2 samples")
add("spinning", M, 4, 0.2, 0.05, 0.01, 3.0, 2.5, 0.4, 1.0,
    "LR4 at 0.2 fs, horn 0.05 fs, drum 0.01 fs, delay 3 +- 2.5 samples")
add("lr2_hz", M, 2, 800.0, 6.7, 5.8, 4.0, 1.5, 0.3, 8000.0,
    "LR2 at 800 Hz, fs 8 kHz, fast speed: horn 6.7 Hz, drum 5.8 Hz")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "order": 4, "cutoff": 1.0, "horn_rate": 0.1,
            "drum_rate": 0.1, "delay": 2.0, "depth": 1.0, "tremolo_depth": 0.5,
            "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"rotary.{cid}", "op": "rotary", "args": base,
                  "error": "invalid_argument", "source": why})


err("depth_over_delay", "depth must be at most delay", depth=3.0)
err("tremolo_depth_high", "tremolo_depth must be at most 1", tremolo_depth=1.5)
err("order_odd", "order must be even", order=1)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "rotary",
    "description": "Rotary-speaker effect (conventions: Rotary-speaker effect; ADR 0292).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "rotary.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/rotary.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
