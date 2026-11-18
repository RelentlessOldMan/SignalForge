"""Writes vectors/cases/fuzzy_entropy.json, stdlib only.

Fuzzy entropy (conventions: Fuzzy entropy; ADR 0339): M = N - m templates of k = m and m + 1
samples minus their own mean and the Chebyshev distances, exact in rationals from dyadic
samples; then D = exp(-d**n / r), phi_k = sum over i != j of D / (M (M - 1)) with math.fsum,
and ln phi_m - ln phi_{m+1}, in float.

Run from the repo root: python vectors/generators/fuzzy_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-11}
cases = []


def phi(q, k, starts, r, n):
    t = []
    for i in range(starts):
        w = q[i:i + k]
        mean = sum(w, Fr(0)) / k
        t.append([v - mean for v in w])
    terms = []
    for i in range(starts):
        for j in range(starts):
            if i != j:
                d = max(abs(a - b) for a, b in zip(t[i], t[j]))
                terms.append(math.exp(-(float(d) ** n) / r))
    return math.fsum(terms) / (starts * (starts - 1))


def add(cid, x, m, r, n, why):
    q = [Fr(v) for v in x]
    starts = len(q) - m
    v = math.log(phi(q, m, starts, r, n)) - math.log(phi(q, m + 1, starts, r, n))
    args = {"samples": x, "m": m, "r": r}
    if n != 2:
        args["n"] = n
    cases.append({"id": f"fuzzy_entropy.{cid}", "op": "fuzzy_entropy", "args": args,
                  "expected": v, "tol": TOL, "source": why})
    return v


v = add("line", [0.75 * i - 3.0 for i in range(12)], 2, 0.5, 2, "a straight line: every "
        "baseline-removed template is the same, so 0")
assert v == 0.0, v
add("alternating", [1.0, -1.0] * 5, 1, 0.5, 2, "+-1 alternating, m = 1")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.0,
              1.5, -0.75, 2.0, 0.5, -1.0], 2, 0.75, 2, "eighteen arbitrary dyadic samples")
add("power_three", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5], 1, 2.0, 3,
    "n = 3, r = 2")
add("power_one", [0.0, 1.0, 0.5, 2.0, 1.5, 3.0, 2.5], 2, 0.25, 1, "n = 1, r = 0.25")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "m": 1, "r": 0.5}
    base.update(args)
    cases.append({"id": f"fuzzy_entropy.{cid}", "op": "fuzzy_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("r_zero", "r must be positive", r=0.0)
err("n_half", "n must be at least 1: smaller powers are ill-conditioned at d = 0", n=0.5)
err("too_short", "samples must be at least m + 2 long", m=4)
err("inf", "samples must be finite", samples=[0.0, "inf", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "fuzzy_entropy",
    "description": "Fuzzy entropy (conventions: Fuzzy entropy; ADR 0339).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fuzzy_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/fuzzy_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
