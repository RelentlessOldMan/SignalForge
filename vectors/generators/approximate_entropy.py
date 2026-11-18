"""Writes vectors/cases/approximate_entropy.json, stdlib only.

Approximate entropy (conventions: Approximate entropy; ADR 0333): Phi_m - Phi_{m+1}, Phi_k the
mean of ln(C_i / n_k) with C_i the templates of k samples (self included) within r by the
Chebyshev distance. Dyadic samples and r, so the counts are exact (rationals); logs in float.

Run from the repo root: python vectors/generators/approximate_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def phi(q, k, r):
    n = len(q) - k + 1
    logs = []
    for i in range(n):
        c = sum(1 for j in range(n) if max(abs(q[j + l] - q[i + l]) for l in range(k)) <= r)
        logs.append(math.log(Fr(c, n)))
    return math.fsum(logs) / n


def add(cid, x, m, r, why):
    q, rr = [Fr(v) for v in x], Fr(r)
    v = phi(q, m, rr) - phi(q, m + 1, rr)
    cases.append({"id": f"approximate_entropy.{cid}", "op": "approximate_entropy",
                  "args": {"samples": x, "m": m, "r": r}, "expected": v, "tol": TOL,
                  "source": why})
    return v


v = add("alternating", [1.0, -1.0] * 3, 1, 0.5, "+-1 alternating, N = 6: Phi_1 = ln(1/2); "
        "Phi_2 = (3 ln(3/5) + 2 ln(2/5))/5")
assert abs(v - (math.log(0.5) - (3 * math.log(0.6) + 2 * math.log(0.4)) / 5)) < 1e-15, v
v = add("constant", [1.5] * 7, 2, 0.0, "a constant: every template matches, 0")
assert v == 0.0, v
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0,
              1.5, -0.75, 2.0, 0.5, -1.0, 1.25, 0.625], 2, 1.25, "twenty arbitrary dyadic "
    "samples, m = 2, r = 1.25")
add("ties", [0.0, 1.0, 2.0, 1.0, 0.0, 1.0, 2.0, 3.0, 2.0, 1.0, 0.0, 1.0], 1, 1.0,
    "distances exactly at r = 1 count as matches")
add("tight", [0.0, 0.5, 0.25], 1, 0.25, "the shortest record, N = m + 2")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "m": 1, "r": 0.5}
    base.update(args)
    cases.append({"id": f"approximate_entropy.{cid}", "op": "approximate_entropy",
                  "args": base, "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("r_negative", "r must be at least 0", r=-0.25)
err("too_short", "samples must be at least m + 2 long", m=4)
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "approximate_entropy",
    "description": "Approximate entropy (conventions: Approximate entropy; ADR 0333).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "approximate_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/approximate_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
