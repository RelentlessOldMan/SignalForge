"""Writes vectors/cases/reflection_conversion.json, stdlib only.

Reflection coefficients and prediction filters (conventions: Reflection coefficients and
prediction filters; ADR 0210). The filters are the hand expansions
  order 2: a = [1, k1 + k2 conj k1, k2]
  order 3: a = [1, a1 + k3 conj a2, a2 + k3 conj a1, k3]
evaluated in exact fractions (real) or with complex (complex); each pair is used both ways.

Run from the repo root: python vectors/generators/reflection_conversion.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def conj(v):
    return v.conjugate() if isinstance(v, complex) else v


def hand(k):
    if len(k) == 1:
        return [1, k[0]]
    a1, a2 = k[0] + k[1] * conj(k[0]), k[1]
    if len(k) == 2:
        return [1, a1, a2]
    return [1, a1 + k[2] * conj(a2), a2 + k[2] * conj(a1), k[2]]


def enc(vs):
    if any(isinstance(v, complex) for v in vs):
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [float(v) for v in vs]


def pair(cid, k, why):
    a = hand(k)
    cases.append({"id": f"reflection_to_lpc.{cid}", "op": "reflection_to_lpc",
                  "args": {"reflection": enc(k)}, "expected": enc(a), "tol": TOL, "source": why})
    cases.append({"id": f"lpc_to_reflection.{cid}", "op": "lpc_to_reflection",
                  "args": {"coefficients": enc(a)}, "expected": enc(k), "tol": TOL,
                  "source": why + "; the step-down recovers k"})


pair("order_one", [Fr(-1, 2)], "k = -1/2: a = [1, -1/2]")
pair("order_two", [Fr(1, 2), Fr(-3, 10)], "a = [1, 1/2 + (-3/10)(1/2), -3/10] = [1, 7/20, -3/10]")
pair("burg_three_samples", [Fr(-8, 9), Fr(77, 85)],
     "ADR 0205's x = [1, 2, 3]: k = -8/9, 77/85 and a = [1, -144/85, 77/85]")
pair("order_three", [Fr(1, 2), Fr(-1, 3), Fr(1, 4)],
     "order 3 by the hand expansion in exact fractions")
pair("complex_order_two", [0.3 + 0.4j, -0.2 + 0.1j], "complex: a1 = k1 + k2 conj k1")
pair("complex_order_three", [0.5j, 0.1 - 0.6j, -0.3 + 0.2j],
     "complex order 3: a1 + k3 conj a2, a2 + k3 conj a1")
assert hand([Fr(-8, 9), Fr(77, 85)]) == [1, Fr(-144, 85), Fr(77, 85)]


def err(op, cid, why, **args):
    cases.append({"id": f"{op}.{cid}", "op": op, "args": args, "error": "invalid_argument",
                  "source": why})


err("reflection_to_lpc", "unit_k", "every |k| < 1", reflection=[0.5, 1.0])
err("reflection_to_lpc", "empty", "reflection must not be empty", reflection=[])
err("reflection_to_lpc", "nan", "reflection must be finite", reflection=[0.5, "nan"])
err("lpc_to_reflection", "a0_not_one", "coefficients[0] must be 1", coefficients=[2.0, 0.5])
err("lpc_to_reflection", "order_zero", "the filter must have order at least 1",
    coefficients=[1.0])
err("lpc_to_reflection", "not_minimum_phase", "a = [1, 0, 1]: k2 = 1", coefficients=[1.0, 0.0, 1.0])
err("lpc_to_reflection", "nan", "coefficients must be finite", coefficients=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "reflection_conversion",
    "description": "Reflection coefficients and prediction filters (conventions: Reflection"
    " coefficients and prediction filters; ADR 0210).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "reflection_conversion.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/reflection_conversion.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
