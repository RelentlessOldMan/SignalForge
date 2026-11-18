"""Writes vectors/cases/hjorth_parameters.json, stdlib only.

Hjorth parameters (conventions: Hjorth parameters; ADR 0324): the population variances of x, of
d[n] = x[n+1] - x[n] and of dd[n] = d[n+1] - d[n], exact in rationals; activity = var(x),
mobility = sqrt(var(d)/var(x)), complexity = sqrt(var(dd)/var(d)) / mobility, the square roots
taken once in float.

Run from the repo root: python vectors/generators/hjorth_parameters.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def var(v):
    mean = sum(v, Fr(0)) / len(v)
    return sum(((e - mean) ** 2 for e in v), Fr(0)) / len(v)


def diff(v):
    return [v[n + 1] - v[n] for n in range(len(v) - 1)]


def add(cid, x, why):
    q = [Fr(v) for v in x]
    d = diff(q)
    v0, v1, v2 = var(q), var(d), var(diff(d))
    mobility = math.sqrt(v1 / v0)
    expected = {"activity": float(v0), "mobility": mobility,
                "complexity": math.sqrt(v2 / v1) / mobility}
    cases.append({"id": f"hjorth_parameters.{cid}", "op": "hjorth_parameters",
                  "args": {"samples": x}, "expected": expected, "tol": TOL, "source": why})
    return expected


e = add("alternating", [1.0, -1.0, 1.0, -1.0, 1.0, -1.0],
        "+-1 at Nyquist: var 1; d = (-2, 2, -2, 2, -2), mean -2/5, var 96/25; dd = +-4, var 16; "
        "mobility sqrt(96/25), complexity 4 / (96/25) = 25/24")
assert e["activity"] == 1.0 and abs(e["mobility"] - math.sqrt(3.84)) < 1e-15, e
assert abs(e["complexity"] - 25 / 24) < 1e-15, e
add("short", [0.0, 1.0, 0.0], "three samples: var 2/9, d = (1, -1) var 1, dd = (-2) var 0")
add("square", [1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0],
    "a square wave of period 4")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25],
    "eight arbitrary dyadic samples")


def err(cid, x, why):
    cases.append({"id": f"hjorth_parameters.{cid}", "op": "hjorth_parameters",
                  "args": {"samples": x}, "error": "invalid_argument", "source": why})


err("too_short", [1.0, 2.0], "needs at least 3 samples")
err("ramp", [1.0, 2.0, 3.0, 4.0], "a straight ramp: var(d) = 0")
err("constant", [2.0, 2.0, 2.0], "a constant: var(x) = 0")
err("nan", [1.0, "nan", 0.0], "samples must be finite")

doc = {
    "schema": 1,
    "suite": "hjorth_parameters",
    "description": "Hjorth parameters (conventions: Hjorth parameters; ADR 0324).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hjorth_parameters.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hjorth_parameters.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
