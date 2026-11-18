"""Writes vectors/cases/flanger.json, stdlib only.

Flanger (conventions: Flanger; ADR 0272): x (1 - mix) + v mix with v the vibrato (ADR 0271),
transcribed with the stdlib math.cos and math.floor.

Run from the repo root: python vectors/generators/flanger.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def wet(x, delay, depth, rate, fs):
    w = 2.0 * math.pi * rate
    v = []
    for n in range(len(x)):
        p = n - (delay + depth * math.cos(w * (n / fs)))
        i = math.floor(p)
        f = p - i
        lo = x[i] if i >= 0 else 0.0
        hi = x[i + 1] if i + 1 >= 0 and f > 0 else 0.0
        v.append((complex(lo), complex(hi), f))
    return v


def run(x, delay, depth, rate, fs, mix):
    y = []
    for xn, (lo, hi, f) in zip(x, wet(x, delay, depth, rate, fs)):
        xc = complex(xn)
        vr = lo.real * (1 - f) + hi.real * f
        vi = lo.imag * (1 - f) + hi.imag * f
        y.append(complex(xc.real * (1 - mix) + vr * mix, xc.imag * (1 - mix) + vi * mix))
    return y


def add(cid, x, delay, depth, rate, fs, mix, why):
    y = [v.real for v in run(x, delay, depth, rate, fs, mix)]
    cases.append({"id": f"flanger.{cid}", "op": "flanger",
                  "args": {"samples": x, "delay": delay, "depth": depth, "rate": rate,
                           "sample_rate": fs, "mix": mix},
                  "expected": y, "tol": TOL, "source": why})
    return y


X = [1.0, -0.5, 0.25, 2.0, -1.0, 0.75, 0.5, -0.25]
y = add("comb", X, 2.0, 0.0, 1.0, 8.0, 0.5, "depth 0, delay 2, mix 1/2: (x[n] + x[n-2])/2")
assert y == [(a + b) / 2 for a, b in zip(X, [0.0, 0.0] + X[:-2])]
y = add("dry", X, 3.0, 1.0, 1.0, 8.0, 0.0, "mix 0: the dry signal")
assert y == X
add("wet", X, 2.0, 1.0, 2.0, 8.0, 1.0, "mix 1: the vibrato alone")
add("modulated", [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05],
    3.25, 1.5, 0.7, 10.0, 0.3, "delay 3.25, depth 1.5, rate 0.7 Hz at 10 Hz, mix 0.3")

cre, cim = [1.0, 0.0, -2.0, 0.5], [0.0, 1.0, 0.5, -1.0]
yc = run([complex(r, i) for r, i in zip(cre, cim)], 1.0, 0.0, 1.0, 4.0, 0.5)
cases.append({"id": "flanger.complex", "op": "flanger",
              "args": {"samples": {"re": cre, "im": cim}, "delay": 1.0, "depth": 0.0,
                       "rate": 1.0, "sample_rate": 4.0, "mix": 0.5},
              "expected": {"re": [v.real for v in yc], "im": [v.imag for v in yc]},
              "tol": TOL, "source": "complex, delay 1, mix 1/2: (x[n] + x[n-1])/2"})


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "delay": 2.0, "depth": 1.0, "rate": 1.0, "sample_rate": 8.0,
            "mix": 0.5}
    base.update(args)
    cases.append({"id": f"flanger.{cid}", "op": "flanger", "args": base,
                  "error": "invalid_argument", "source": why})


err("mix_high", "mix must be at most 1", mix=1.5)
err("mix_negative", "mix must be at least 0", mix=-0.25)
err("depth_above_delay", "depth must be at most delay", depth=3.0)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "flanger",
    "description": "Flanger (conventions: Flanger; ADR 0272).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "flanger.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/flanger.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
