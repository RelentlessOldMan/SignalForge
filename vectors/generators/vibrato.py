"""Writes vectors/cases/vibrato.json, stdlib only.

Vibrato (conventions: Vibrato; ADR 0271): a delay delay + depth cos((2 pi rate)(n / fs))
samples read with linear interpolation from rest. Constant-delay cases are exact; modulated
cases are a stdlib transcription with math.cos and math.floor.

Run from the repo root: python vectors/generators/vibrato.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def run(x, delay, depth, rate, fs):
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


def add(cid, x, delay, depth, rate, fs, why):
    y = run(x, delay, depth, rate, fs)
    cases.append({"id": f"vibrato.{cid}", "op": "vibrato",
                  "args": {"samples": x, "delay": delay, "depth": depth, "rate": rate,
                           "sample_rate": fs},
                  "expected": y, "tol": TOL, "source": why})
    return y


X = [1.0, -0.5, 0.25, 2.0, -1.0, 0.75, 0.5, -0.25]
y = add("whole_delay", X, 2.0, 0.0, 1.0, 8.0, "depth 0, delay 2: a shift by 2 from rest")
assert y == [0.0, 0.0] + X[:-2]
y = add("half_delay", X, 0.5, 0.0, 1.0, 8.0, "depth 0, delay 1/2: neighbours averaged")
assert y == [0.5] + [(a + b) / 2 for a, b in zip(X, X[1:])]
y = add("zero_delay", X, 0.0, 0.0, 3.0, 8.0, "delay 0: unchanged")
assert y == X
add("quarter_rate", X, 2.0, 1.0, 2.0, 8.0,
    "delay 2 + cos(pi n/2): delays 3, 2, 1, 2, ... (whole samples)")
add("modulated", [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3, -0.1, 0.05],
    3.25, 1.5, 0.7, 10.0, "delay 3.25, depth 1.5, rate 0.7 Hz at 10 Hz")

cre, cim = [1.0, 0.0, -2.0, 0.5], [0.0, 1.0, 0.5, -1.0]
yc = run([complex(r, i) for r, i in zip(cre, cim)], 1.5, 0.0, 1.0, 4.0)
cases.append({"id": "vibrato.complex", "op": "vibrato",
              "args": {"samples": {"re": cre, "im": cim}, "delay": 1.5, "depth": 0.0,
                       "rate": 1.0, "sample_rate": 4.0},
              "expected": {"re": [complex(v).real for v in yc], "im": [complex(v).imag for v in yc]},
              "tol": TOL, "source": "complex, delay 3/2: x[n-2] and x[n-1] averaged"})


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "delay": 2.0, "depth": 1.0, "rate": 1.0, "sample_rate": 8.0}
    base.update(args)
    cases.append({"id": f"vibrato.{cid}", "op": "vibrato", "args": base,
                  "error": "invalid_argument", "source": why})


err("delay_negative", "delay must be at least 0", delay=-1.0)
err("depth_above_delay", "depth must be at most delay", depth=2.5)
err("depth_negative", "depth must be at least 0", depth=-0.5)
err("rate_inf", "rate must be finite", rate="inf")
err("fs_negative", "sample_rate must be positive", sample_rate=-8.0)
err("empty", "samples must not be empty", samples=[])
err("nan_sample", "samples must be finite", samples=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "vibrato",
    "description": "Vibrato (conventions: Vibrato; ADR 0271).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "vibrato.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/vibrato.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
