"""Writes vectors/cases/tsallis_diversity.json, stdlib only.

The Tsallis diversity of counts (conventions: the Tsallis diversity of counts; ADR 0568):
exact shares and (1 - sum p^q)/(q - 1) in 60-digit decimal.

Run from the repo root: python vectors/generators/tsallis_diversity.py [--check]
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
    if q == 1:
        v = -sum(p * p.ln() for p in shares)
    else:
        v = (1 - sum(((qq * p.ln()).exp() for p in shares), D(0))) / (qq - 1)
    cases.append(
        {
            "id": f"tsallis_diversity.{cid}",
            "op": "tsallis_diversity",
            "args": {"samples": x, "order": q},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


assert near(add("simpson", [1.0, 1.0, 2.0], 2.0, "q = 2: 1 - 3/8 = 5/8"), D(5) / 8)
assert near(add("even_pair", [1.0, 1.0], 2.0, "two equal shares, q = 2: 1/2"), D(1) / 2)
assert near(add("richness", [0.0, 3.0, 5.0], 0.0, "q = 0: K - 1 = 1"), 1)
assert near(add("shannon", [1.0, 1.0], 1.0, "q = 1: ln 2"), D(2).ln())
assert near(add("cubic", [1.0, 1.0, 2.0], 3.0, "q = 3: (1 - 10/64)/2 = 27/64"), D(27) / 64)
assert near(add("half", [1.0, 3.0], 0.5, "q = 1/2: (1 - (1 + sqrt 3)/2)/(-1/2)"), D(3).sqrt() - 1)
assert add("one_kind", [0.0, 4.0], 2.0, "one kind: 0") == 0
add("near_one", [2.0, 0.5, 3.25, 1.0], 1.0000001, "q just above 1: the expm1 form")
add("small_order", [2.0, 0.5, 3.25, 1.0], 0.1, "q = 0.1")
add("large", [2.0, 0.5, 3.25, 1.0, 0.0], 41.0, "q = 41")
rng = random.Random(568)
x = [round(rng.uniform(0, 5), 3) for _ in range(30)]
add("random", x, 1.75, "30 values from random.Random(568).uniform(0, 5), 3 places, q = 1.75")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "order": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"tsallis_diversity.{cid}",
            "op": "tsallis_diversity",
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
    "suite": "tsallis_diversity",
    "description": "The Tsallis diversity of counts (conventions: the Tsallis diversity of counts; ADR 0568).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tsallis_diversity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tsallis_diversity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
