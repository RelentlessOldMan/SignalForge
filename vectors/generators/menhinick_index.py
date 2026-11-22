"""Writes vectors/cases/menhinick_index.json, stdlib only.

Menhinick's index (conventions: Menhinick's index; ADR 0541): the total of dyadic values
formed exactly, the square root in 50-digit decimal.

Run from the repo root: python vectors/generators/menhinick_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from decimal import Decimal as D
from fractions import Fraction as Fr

decimal.getcontext().prec = 50
TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, why):
    v = [Fr(a) for a in x]
    total = sum(v)
    q = D(sum(1 for a in v if a > 0)) / dec(total).sqrt()
    cases.append(
        {
            "id": f"menhinick_index.{cid}",
            "op": "menhinick_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def near(q, want):
    return abs(q - want) < D("1e-40")


assert near(add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "k = 1, N = 4: 1/2"), D(1) / 2)
assert near(add("equal", [2.0] * 4, "k = 4, N = 8: 4/sqrt 8 = sqrt 2"), D(2).sqrt())
assert near(add("two", [3.0, 1.0], "k = 2, N = 4: 1"), 1)
assert near(add("halves", [0.5, 0.25, 0.25, 1.0], "k = 4, N = 2: 2 sqrt 2"), 2 * D(2).sqrt())
assert near(add("ones", [1.0] * 9, "k = 9, N = 9: 3"), 3)
assert near(add("one_zero", [0.0, 2.0, 2.0, 2.0], "k = 3, N = 6: 3/sqrt 6"), 3 / D(6).sqrt())
assert near(add("single", [5.0], "k = 1, N = 5: 1/sqrt 5"), 1 / D(5).sqrt())
add("ramp", [4.0, 1.0, 3.0, 2.0], "k = 4, N = 10")
rng = random.Random(541)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(541).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"menhinick_index.{cid}",
            "op": "menhinick_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "menhinick_index",
    "description": "Menhinick's index (conventions: Menhinick's index; ADR 0541).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "menhinick_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/menhinick_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
