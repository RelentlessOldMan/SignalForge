"""Writes vectors/cases/hill_evenness.json, stdlib only.

Hill evenness (conventions: Hill evenness; ADR 0564): exact shares and
(sum p^q)^(1/(1-q))/K in 60-digit decimal.

Run from the repo root: python vectors/generators/hill_evenness.py [--check]
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
        v = D(len(shares))
    elif q == 1:
        v = (-sum(p * p.ln() for p in shares)).exp()
    else:
        s = sum(((qq * p.ln()).exp() for p in shares), D(0))
        v = (s.ln() / (1 - qq)).exp()
    v /= len(shares)
    cases.append(
        {
            "id": f"hill_evenness.{cid}",
            "op": "hill_evenness",
            "args": {"samples": x, "order": q},
            "expected": float(v),
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert near(add("even_pair", [1.0, 1.0], 2.0, "two equal shares: 1 at any order"), 1)
assert add("richness", [0.0, 3.0, 5.0], 0.0, "q = 0: K/K = 1") == 1
assert near(add("inverse_simpson", [1.0, 1.0, 2.0], 2.0, "D2 = 8/3 over 3 kinds: 8/9"), D(8) / 9)
assert near(add("shannon", [1.0, 1.0, 2.0], 1.0, "D1 = 2^(3/2) over 3 kinds"), D(2) ** D("1.5") / 3)
assert near(
    add("half", [1.0, 3.0], 0.5, "D = 1 + sqrt(3)/2 over 2 kinds"), (1 + D(3).sqrt() / 2) / 2
)
add("near_one", [2.0, 0.5, 3.25, 1.0], 1.000001, "q just above 1")
add("edge", [2.0, 0.5, 3.25, 1.0], 1.5, "q = 1.5")
add("large", [2.0, 0.5, 3.25, 1.0, 0.0], 250.0, "q = 250: near (6.75/3.25)/4")
add("small_order", [2.0, 0.5, 3.25, 1.0, 0.0], 0.1, "q = 0.1, a zero value left out of K")
rng = random.Random(563)
x = [round(rng.uniform(0, 5), 3) for _ in range(30)]
add("random", x, 2.5, "30 values from random.Random(563).uniform(0, 5), 3 places, q = 2.5")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "order": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"hill_evenness.{cid}",
            "op": "hill_evenness",
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
    "suite": "hill_evenness",
    "description": "Hill evenness (conventions: Hill evenness; ADR 0564).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hill_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hill_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
