"""Writes vectors/cases/sliding_dft.json, stdlib only.

Sliding DFT (conventions: Sliding DFT; ADR 0231). The expected values are direct DFT sums over
each window, S_n = sum_m x[n - N + 1 + m] exp(-2 pi i k m / N), x zero before 0, without the
recursion; cross-checked against closed forms: a constant at k = 0 gives the running count, and
a complex exponential on bin k gives N exp(2 pi i k (n - N + 1) / N) once the window is full.

Run from the repo root: python vectors/generators/sliding_dft.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def direct(x, n, k):
    out = []
    for i in range(len(x)):
        s = 0j
        for m in range(n):
            j = i - n + 1 + m
            if j >= 0:
                s += x[j] * cmath.exp(-2j * math.pi * k * m / n)
        out.append(s)
    return out


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, x, n, k, why):
    out = direct(x, n, k)
    cases.append({"id": f"sliding_dft.{cid}", "op": "sliding_dft",
                  "args": {"samples": enc(x), "length": n, "k": k},
                  "expected": {"re": [v.real for v in out], "im": [v.imag for v in out]},
                  "tol": TOL, "source": why})
    return out


out = add("constant_dc", [2.0] * 7, 4, 0, "constant 2 at k = 0: 2, 4, 6, 8, 8, 8, 8")
assert all(abs(v - c) < 1e-15 for v, c in zip(out, [2, 4, 6, 8, 8, 8, 8]))
tone = [cmath.exp(2j * math.pi * 3 * i / 8) for i in range(20)]
out = add("on_bin", tone, 8, 3, "e^(2 pi i 3 n / 8) at k = 3: 8 e^(2 pi i 3 (n - 7) / 8) when full")
for i in range(7, 20):
    assert abs(out[i] - 8 * cmath.exp(2j * math.pi * 3 * (i - 7) / 8)) < 1e-12
add("real_mixed", [0.5, -1.0, 2.0, 0.25, -0.75, 1.5, 0.0, 3.0, -2.0, 1.0, 0.5], 5, 2,
    "real samples, N = 5, k = 2")
add("length_one", [1.5, -2.0, 0.25], 1, 0, "N = 1: the samples themselves")
add("long_window", [1.0, 2.0, 3.0], 6, 5, "window longer than the input: zero-padded")
add("complex", [1 + 1j, -0.5j, 0.25 - 0.5j, 2.0 + 0j, -1 + 0.5j, 0.75j], 3, 1, "complex samples")


def err(cid, why, **args):
    cases.append({"id": f"sliding_dft.{cid}", "op": "sliding_dft", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", "samples must not be empty", samples=[], length=4, k=0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], length=2, k=0)
err("length_zero", "length must be at least 1", samples=[1.0], length=0, k=0)
err("k_too_big", "k must be below length", samples=[1.0], length=4, k=4)
err("k_negative", "k must be at least 0", samples=[1.0], length=4, k=-1)

doc = {
    "schema": 1,
    "suite": "sliding_dft",
    "description": "Sliding DFT (conventions: Sliding DFT; ADR 0231).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "sliding_dft.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/sliding_dft.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
