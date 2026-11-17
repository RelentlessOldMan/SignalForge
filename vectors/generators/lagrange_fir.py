"""Writes vectors/cases/lagrange_fir.json, stdlib only.

Lagrange fractional-delay FIR (conventions: Lagrange fractional-delay FIR; ADR 0225).
h[k] = prod_{m != k} (D - m) / (k - m) in exact fractions; each case is checked against the moment
identity sum_k h[k] k^q = D^q for q <= order (exact for polynomials up to the order).

Run from the repo root: python vectors/generators/lagrange_fir.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def taps(d, n):
    h = []
    for k in range(n + 1):
        v = Fr(1)
        for m in range(n + 1):
            if m != k:
                v *= (d - m) / Fr(k - m)
        h.append(v)
    for q in range(n + 1):
        assert sum(hk * Fr(k) ** q for k, hk in enumerate(h)) == d**q, (d, n, q)
    return h


def add(cid, d, n, why):
    h = taps(d, n)
    cases.append({"id": f"lagrange_fir.{cid}", "op": "lagrange_fir",
                  "args": {"delay": float(d), "order": n}, "expected": [float(v) for v in h],
                  "tol": TOL, "source": why})
    return h


assert add("linear", Fr(3, 10), 1, "order 1: [1 - D, D] = [7/10, 3/10]") == [Fr(7, 10), Fr(3, 10)]
assert add("quadratic_half", Fr(1, 2), 2, "order 2, D = 1/2: [3/8, 3/4, -1/8]") == [
    Fr(3, 8), Fr(3, 4), Fr(-1, 8)]
assert add("cubic_center", Fr(3, 2), 3, "order 3, D = 3/2: [-1/16, 9/16, 9/16, -1/16]") == [
    Fr(-1, 16), Fr(9, 16), Fr(9, 16), Fr(-1, 16)]
assert add("integer_delay", Fr(2), 4, "D = 2 of order 4: the impulse at 2") == [0, 0, 1, 0, 0]
add("order_five", Fr(37, 16), 5, "order 5, D = 37/16")
add("extrapolate", Fr(-1, 2), 2, "D = -1/2, outside 0 ... N: allowed")
add("order_eight", Fr(41, 10), 8, "order 8, D = 4.1")


def err(cid, why, **args):
    cases.append({"id": f"lagrange_fir.{cid}", "op": "lagrange_fir", "args": args,
                  "error": "invalid_argument", "source": why})


err("order_zero", "order must be at least 1", delay=0.5, order=0)
err("nan_delay", "delay must be finite", delay="nan", order=3)
err("inf_delay", "delay must be finite", delay="inf", order=3)

doc = {
    "schema": 1,
    "suite": "lagrange_fir",
    "description": "Lagrange fractional-delay FIR (conventions: Lagrange fractional-delay FIR;"
    " ADR 0225).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lagrange_fir.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lagrange_fir.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
