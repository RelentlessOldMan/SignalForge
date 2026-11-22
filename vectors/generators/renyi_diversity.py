"""Writes vectors/cases/renyi_diversity.json, stdlib only.

The Renyi diversity of counts (conventions: the Renyi diversity of counts; ADR 0566): exact
shares and ln(sum p^q)/(1-q) in 60-digit decimal.

Run from the repo root: python vectors/generators/renyi_diversity.py [--check]
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
        v = D(len(shares)).ln()
    elif q == 1:
        v = -sum(p * p.ln() for p in shares)
    else:
        s = sum(((qq * p.ln()).exp() for p in shares), D(0))
        v = s.ln() / (1 - qq)
    cases.append(
        {
            "id": f"renyi_diversity.{cid}",
            "op": "renyi_diversity",
            "args": {"samples": x, "order": q},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert near(add("even_pair", [1.0, 1.0], 2.0, "two equal shares: ln 2 at any order"), D(2).ln())
assert near(add("richness", [0.0, 3.0, 5.0], 0.0, "q = 0: ln K = ln 2"), D(2).ln())
assert near(
    add("inverse_simpson", [1.0, 1.0, 2.0], 2.0, "shares 1/4, 1/4, 1/2: ln(8/3)"), (D(8) / 3).ln()
)
assert near(
    add("shannon", [1.0, 1.0, 2.0], 1.0, "ln 4/2 + ln 2/2 = (3/2) ln 2"), D("1.5") * D(2).ln()
)
assert near(
    add("cubic", [1.0, 1.0, 2.0], 3.0, "ln((10/64)^(-1/2)) = ln 8 - ln(10)/2"),
    3 * D(2).ln() - D(10).ln() / 2,
)
assert near(add("half", [1.0, 3.0], 0.5, "ln(1 + sqrt(3)/2)"), (1 + D(3).sqrt() / 2).ln())
assert add("one_kind", [0.0, 4.0], 2.0, "one kind: 0") == 0
add("near_one", [2.0, 0.5, 3.25, 1.0], 1.000001, "q just above 1: the expm1 form")
add("below_one", [2.0, 0.5, 3.25, 1.0], 0.9, "q = 0.9")
add("edge", [2.0, 0.5, 3.25, 1.0], 1.5, "q = 1.5: the max form")
add("large", [2.0, 0.5, 3.25, 1.0, 0.0], 250.0, "q = 250: near 1/max p = 6.75/3.25")
add("small_order", [2.0, 0.5, 3.25, 1.0], 0.1, "q = 0.1")
rng = random.Random(566)
x = [round(rng.uniform(0, 5), 3) for _ in range(30)]
add("random", x, 2.5, "30 values from random.Random(566).uniform(0, 5), 3 places, q = 2.5")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "order": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"renyi_diversity.{cid}",
            "op": "renyi_diversity",
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
    "suite": "renyi_diversity",
    "description": "The Renyi diversity of counts (conventions: the Renyi diversity of counts; ADR 0566).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "renyi_diversity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/renyi_diversity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
