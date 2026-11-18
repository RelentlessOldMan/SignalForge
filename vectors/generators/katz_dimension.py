"""Writes vectors/cases/katz_dimension.json, stdlib only.

Katz fractal dimension (conventions: Katz fractal dimension; ADR 0334): points (i, x[i]),
n = N - 1, L = fsum of hypot(1, step), d = max hypot(i, x[i] - x[0]),
D = log10 n / (log10 n + log10(d / L)), in float with math.hypot and math.fsum.

Run from the repo root: python vectors/generators/katz_dimension.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def katz(x):
    n = len(x) - 1
    length = math.fsum(math.hypot(1.0, x[i + 1] - x[i]) for i in range(n))
    extent = max(math.hypot(i, x[i] - x[0]) for i in range(n + 1))
    return math.log10(n) / (math.log10(n) + math.log10(extent / length))


def add(cid, x, why):
    v = katz(x)
    cases.append({"id": f"katz_dimension.{cid}", "op": "katz_dimension",
                  "args": {"samples": x}, "expected": v, "tol": TOL, "source": why})
    return v


v = add("line", [0.75 * i - 1.0 for i in range(12)], "a straight line: d = L, so D = 1")
assert abs(v - 1) < 1e-15, v
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0, 1.5, -0.75, 2.0], "sixteen arbitrary samples")
add("sawtooth", [float(i % 4) for i in range(17)], "a sawtooth of period 4")
add("three", [0.0, 1.0, 0.5], "the shortest record")


def err(cid, why, samples):
    cases.append({"id": f"katz_dimension.{cid}", "op": "katz_dimension",
                  "args": {"samples": samples}, "error": "invalid_argument", "source": why})


err("two", "at least 3 samples", [0.0, 1.0])
err("zero_denominator", "0, 3, 0: L = 2 sqrt 10 = 2 d, so log10 2 + log10(1/2) = 0",
    [0.0, 3.0, 0.0])
err("inf", "samples must be finite", [0.0, "inf", 1.0])

doc = {
    "schema": 1,
    "suite": "katz_dimension",
    "description": "Katz fractal dimension (conventions: Katz fractal dimension; ADR 0334).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "katz_dimension.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/katz_dimension.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
