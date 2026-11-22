"""Writes vectors/cases/sharma_mittal_diversity.json, stdlib only.

The Sharma-Mittal diversity of counts (conventions: the Sharma-Mittal diversity of counts;
ADR 0570): exact shares and ((sum p^q)^((1-r)/(1-q)) - 1)/(1 - r) in 60-digit decimal.

Run from the repo root: python vectors/generators/sharma_mittal_diversity.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D
from fractions import Fraction as Fr

decimal.getcontext().prec = 60
TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, q, deg, why):
    xs = [Fr(a) for a in x]
    total = sum(xs, Fr(0))
    shares = [dec(a / total) for a in xs if a > 0]
    qq = dec(Fr(q))
    rr = dec(Fr(deg))
    if q == 1:
        h = -sum(p * p.ln() for p in shares)
    else:
        h = sum(((qq * p.ln()).exp() for p in shares), D(0)).ln() / (1 - qq)
    v = h if deg == 1 else (((1 - rr) * h).exp() - 1) / (1 - rr)
    cases.append(
        {
            "id": f"sharma_mittal_diversity.{cid}",
            "op": "sharma_mittal_diversity",
            "args": {"samples": x, "order": q, "degree": deg},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert near(add("hill", [1.0, 1.0, 2.0], 2.0, 0.0, "r = 0: D_2 - 1 = 8/3 - 1 = 5/3"), D(5) / 3)
assert near(add("tsallis", [1.0, 1.0, 2.0], 2.0, 2.0, "r = q = 2: 1 - 3/8 = 5/8"), D(5) / 8)
assert near(add("renyi", [1.0, 1.0], 2.0, 1.0, "r = 1: ln 2"), D(2).ln())
assert near(
    add("shannon_exp", [1.0, 1.0, 2.0], 1.0, 0.0, "q = 1, r = 0: 2^1.5 - 1"), 2 * D(2).sqrt() - 1
)
assert near(add("richness", [0.0, 3.0, 5.0], 0.0, 0.0, "q = 0, r = 0: K - 1 = 1"), 1)
assert near(add("cube", [1.0, 1.0, 2.0], 2.0, 3.0, "((3/8)^2 - 1)/(-2) = 55/128"), D(55) / 128)
assert add("one_kind", [0.0, 4.0], 2.0, 0.5, "one kind: 0") == 0
add("near_one_degree", [2.0, 0.5, 3.25, 1.0], 1.5, 1.0000001, "r just above 1: the expm1 form")
add("near_one_order", [2.0, 0.5, 3.25, 1.0], 1.000001, 2.5, "q just above 1")
add("negative_degree", [2.0, 0.5, 3.25, 1.0, 0.0], 0.5, -3.0, "r = -3")
rng = random.Random(570)
x = [round(rng.uniform(0, 5), 3) for _ in range(30)]
add(
    "random",
    x,
    1.75,
    0.25,
    "30 values from random.Random(570).uniform(0, 5), 3 places, q = 1.75, r = 0.25",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "order": 2.0, "degree": 0.5}
    base.update(args)
    cases.append(
        {
            "id": f"sharma_mittal_diversity.{cid}",
            "op": "sharma_mittal_diversity",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("negative_order", "the order must be at least 0", order=-0.5)

doc = {
    "schema": 1,
    "suite": "sharma_mittal_diversity",
    "description": "The Sharma-Mittal diversity of counts (conventions: the Sharma-Mittal diversity of counts; ADR 0570).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "sharma_mittal_diversity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/sharma_mittal_diversity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
