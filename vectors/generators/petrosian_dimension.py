"""Writes vectors/cases/petrosian_dimension.json, stdlib only.

Petrosian fractal dimension (conventions: Petrosian fractal dimension; ADR 0335): n = N, the
integer count N_delta of sign changes of the first difference (exact in rationals), then
D = log10 n / (log10 n + log10(n / (n + 0.4 N_delta))) in float.

Run from the repo root: python vectors/generators/petrosian_dimension.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def sign(v):
    return (v > 0) - (v < 0)


def petrosian(x):
    q = [Fr(v) for v in x]
    n = len(q)
    d = [q[i + 1] - q[i] for i in range(n - 1)]
    changes = sum(1 for i in range(n - 2) if sign(d[i]) * sign(d[i + 1]) < 0)
    return math.log10(n) / (math.log10(n) + math.log10(n / (n + 0.4 * changes))), changes


def add(cid, x, why):
    v, changes = petrosian(x)
    cases.append({"id": f"petrosian_dimension.{cid}", "op": "petrosian_dimension",
                  "args": {"samples": x}, "expected": v, "tol": TOL, "source": why})
    return v, changes


v, c = add("monotonic", [0.0, 1.0, 1.0, 2.5, 3.0, 7.0], "never turns (a flat step is no "
           "change): N_delta = 0, D = 1")
assert v == 1.0 and c == 0, (v, c)
v, c = add("alternating", [1.0, -1.0] * 5, "+-1 alternating, n = 10: N_delta = 8")
assert c == 8, c
add("flat_between", [0.0, 1.0, 1.0, 0.0, 0.0, 1.0], "a flat step between a rise and a fall is "
    "no change: N_delta = 0")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0, 1.5, -0.75, 2.0], "sixteen arbitrary samples")
add("tiny", [0.0, 1e-300, 0.0], "steps of 1e-300: the signs change once though the product "
    "of the steps underflows")


def err(cid, why, samples):
    cases.append({"id": f"petrosian_dimension.{cid}", "op": "petrosian_dimension",
                  "args": {"samples": samples}, "error": "invalid_argument", "source": why})


err("two", "at least 3 samples", [0.0, 1.0])
err("nan", "samples must be finite", [0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "petrosian_dimension",
    "description": "Petrosian fractal dimension (conventions: Petrosian fractal dimension; "
                   "ADR 0335).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "petrosian_dimension.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/petrosian_dimension.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
