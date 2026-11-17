"""Writes vectors/cases/bandwidth_expansion.json, stdlib only.

Bandwidth expansion (conventions: Bandwidth expansion; ADR 0219). a_j -> a_j g^j in exact
fractions; an order-1 filter [1, -p] becomes [1, -g p], its pole moving from p to g p.

Run from the repo root: python vectors/generators/bandwidth_expansion.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def add(cid, a, g, why):
    out = [c * g**j for j, c in enumerate(a)]
    cases.append({"id": f"bandwidth_expansion.{cid}", "op": "bandwidth_expansion",
                  "args": {"coefficients": enc(a), "factor": float(g)}, "expected": enc(out),
                  "tol": TOL, "source": why})
    return out


out = add("order_three", [1, Fr(1, 2), Fr(-1, 3), Fr(1, 4)], Fr(9, 10),
          "g = 9/10: [1, 9/20, -27/100, 729/4000]")
assert out == [1, Fr(9, 20), Fr(-27, 100), Fr(729, 4000)]
out = add("order_one_pole", [1, Fr(-4, 5)], Fr(1, 2), "pole 4/5 moves to 2/5: [1, -2/5]")
assert out == [1, Fr(-2, 5)]
add("identity", [1, Fr(-1, 6), Fr(-1, 6)], Fr(1), "g = 1 leaves the filter unchanged")
add("any_a0", [Fr(2), Fr(1), Fr(1, 2)], Fr(1, 2), "a_0 = 2 is allowed: [2, 1/2, 1/8]")
add("single_tap", [Fr(1)], Fr(3, 4), "[1] stays [1]")
add("complex", [1, 0.5j, -0.25 + 0j], 0.5, "complex: [1, 0.25j, -0.0625]")


def err(cid, why, **args):
    cases.append({"id": f"bandwidth_expansion.{cid}", "op": "bandwidth_expansion", "args": args,
                  "error": "invalid_argument", "source": why})


err("zero_factor", "factor must be in (0, 1]", coefficients=[1.0, 0.5], factor=0.0)
err("factor_above_one", "factor must be in (0, 1]", coefficients=[1.0, 0.5], factor=1.5)
err("nan_factor", "factor must be in (0, 1]", coefficients=[1.0, 0.5], factor="nan")
err("empty", "coefficients must not be empty", coefficients=[], factor=0.9)
err("nan_coefficient", "coefficients must be finite", coefficients=[1.0, "nan"], factor=0.9)

doc = {
    "schema": 1,
    "suite": "bandwidth_expansion",
    "description": "Bandwidth expansion (conventions: Bandwidth expansion; ADR 0219).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bandwidth_expansion.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bandwidth_expansion.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
