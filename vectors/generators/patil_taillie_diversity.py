"""Writes vectors/cases/patil_taillie_diversity.json, stdlib only.

The Patil-Taillie diversity (conventions: the Patil-Taillie diversity; ADR 0565): exact
shares and (1 - sum p^(beta+1))/beta in 60-digit decimal.

Run from the repo root: python vectors/generators/patil_taillie_diversity.py [--check]
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


def add(cid, x, q, why):
    xs = [Fr(a) for a in x]
    total = sum(xs, Fr(0))
    shares = [dec(a / total) for a in xs if a > 0]
    qq = dec(Fr(q))
    if q == 0:
        v = -sum(p * p.ln() for p in shares)
    else:
        v = (1 - sum((((qq + 1) * p.ln()).exp() for p in shares), D(0))) / qq
    cases.append(
        {
            "id": f"patil_taillie_diversity.{cid}",
            "op": "patil_taillie_diversity",
            "args": {"samples": x, "beta": q},
            "expected": float(v),
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert near(add("simpson", [1.0, 1.0, 2.0], 1.0, "beta = 1: 1 - 3/8 = 5/8"), D(5) / 8)
assert near(add("even_pair", [1.0, 1.0], 1.0, "two equal shares, beta = 1: 1/2"), D(1) / 2)
assert near(add("richness", [0.0, 3.0, 5.0], -1.0, "beta = -1: K - 1 = 1"), 1)
assert near(add("shannon", [1.0, 1.0], 0.0, "beta = 0: ln 2"), D(2).ln())
assert near(add("square", [1.0, 1.0, 2.0], 2.0, "beta = 2: (1 - 10/64)/2 = 27/64"), D(27) / 64)
assert near(
    add("minus_half", [1.0, 3.0], -0.5, "beta = -1/2: (1 - (1 + sqrt 3)/2)/(-1/2)"), D(3).sqrt() - 1
)
assert add("one_kind", [0.0, 4.0], 1.0, "one kind: 0") == 0
add("near_zero", [2.0, 0.5, 3.25, 1.0], 1e-7, "beta just above 0: the expm1 form")
add("negative_beta", [2.0, 0.5, 3.25, 1.0], -0.9, "beta = -0.9")
add("large", [2.0, 0.5, 3.25, 1.0, 0.0], 40.0, "beta = 40")
rng = random.Random(565)
x = [round(rng.uniform(0, 5), 3) for _ in range(30)]
add("random", x, 0.75, "30 values from random.Random(565).uniform(0, 5), 3 places, beta = 0.75")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "beta": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"patil_taillie_diversity.{cid}",
            "op": "patil_taillie_diversity",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("beta_below", "beta must be at least -1", beta=-1.5)

doc = {
    "schema": 1,
    "suite": "patil_taillie_diversity",
    "description": "The Patil-Taillie diversity (conventions: the Patil-Taillie diversity; ADR 0565).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "patil_taillie_diversity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/patil_taillie_diversity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
