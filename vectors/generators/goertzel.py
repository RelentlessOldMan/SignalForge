"""Writes vectors/cases/goertzel.json, stdlib only.

Goertzel (conventions: Goertzel; ADR 0224). The expected values are the direct DTFT sums
X(f) = sum x[n] exp(-2 pi i f n / fs), without the recursion, cross-checked against closed forms:
the geometric series for all ones, exp(-i w n0) for an impulse, N/2 for a cosine on a bin.

Run from the repo root: python vectors/generators/goertzel.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def dtft(x, fs, f):
    return sum(v * cmath.exp(-2j * math.pi * f * n / fs) for n, v in enumerate(x))


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, x, fs, freqs, why):
    out = [complex(dtft(x, fs, f)) for f in freqs]
    cases.append({"id": f"goertzel.{cid}", "op": "goertzel",
                  "args": {"samples": enc(x), "sample_rate": fs, "frequencies": freqs},
                  "expected": {"re": [v.real for v in out], "im": [v.imag for v in out]},
                  "tol": TOL, "source": why})
    return out


ones = [1.0] * 8
freqs = [0.0, 1.0, 2.5, -1.3, 3.7]
out = add("ones", ones, 8.0, freqs, "all ones: (1 - e^(-i w N)) / (1 - e^(-i w)), 8 at DC, 0 on bins")
for f, v in zip(freqs, out):
    w = 2 * math.pi * f / 8.0
    closed = 8.0 if f == 0 else (1 - cmath.exp(-1j * w * 8)) / (1 - cmath.exp(-1j * w))
    assert abs(v - closed) < 1e-12, (f, v, closed)
imp = [0.0, 0.0, 1.0, 0.0, 0.0]
freqs = [0.3, 1.1, -0.7]
out = add("impulse", imp, 2.0, freqs, "impulse at n = 2: e^(-2 i w)")
for f, v in zip(freqs, out):
    assert abs(v - cmath.exp(-2j * math.pi * f / 2.0 * 2)) < 1e-15
cosine = [math.cos(2 * math.pi * 3 * n / 16) for n in range(16)]
out = add("cosine_on_bin", cosine, 16.0, [3.0, 13.0, 5.0], "cos on bin 3 of 16: 8, 8, 0")
assert abs(out[0] - 8) < 1e-12 and abs(out[1] - 8) < 1e-12 and abs(out[2]) < 1e-12
add("off_bin", [0.5, -1.0, 2.0, 0.25, -0.75, 1.5, 0.0], 1000.0, [12.5, 140.0, 333.3, 499.0, 777.0],
    "off-bin frequencies, two past fs/2")
add("single_sample", [2.5], 1.0, [0.1, 0.4], "N = 1: X = x[0]")
add("complex", [1 + 1j, -0.5j, 0.25 - 0.5j, 2.0 + 0j], 4.0, [0.0, 1.0, -1.0, 0.6],
    "complex samples: positive and negative frequencies differ")


def err(cid, why, **args):
    cases.append({"id": f"goertzel.{cid}", "op": "goertzel", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", "samples must not be empty", samples=[], sample_rate=1.0, frequencies=[0.1])
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], sample_rate=1.0,
    frequencies=[0.1])
err("zero_rate", "sample_rate must be positive", samples=[1.0], sample_rate=0.0,
    frequencies=[0.1])
err("no_frequencies", "frequencies must not be empty", samples=[1.0], sample_rate=1.0,
    frequencies=[])
err("nan_frequency", "frequencies must be finite", samples=[1.0], sample_rate=1.0,
    frequencies=["nan"])

doc = {
    "schema": 1,
    "suite": "goertzel",
    "description": "Goertzel (conventions: Goertzel; ADR 0224).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "goertzel.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/goertzel.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
