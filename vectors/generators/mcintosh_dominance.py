"""Writes vectors/cases/mcintosh_dominance.json, stdlib only.

The McIntosh dominance (conventions: the McIntosh dominance; ADR 0539): the sums of dyadic
values formed exactly, the square roots in 50-digit decimal.

Run from the repo root: python vectors/generators/mcintosh_dominance.py [--check]
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
TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, x, why):
    v = [Fr(a) for a in x]
    total = sum(v)
    sq = sum(a * a for a in v)
    q = (dec(total) - dec(sq).sqrt()) / (dec(total) - dec(total).sqrt())
    cases.append(
        {
            "id": f"mcintosh_dominance.{cid}",
            "op": "mcintosh_dominance",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def near(q, want):
    return abs(q - want) < D("1e-40")


assert near(add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "U = N = 4: 0"), 0)
assert near(
    add("equal", [2.0] * 4, "N = 8, U = 4: 4/(8 - 2 sqrt 2)"), D(4) / (D(8) - 2 * D(2).sqrt())
)
assert near(
    add("two", [3.0, 1.0], "N = 4, U = sqrt 10: (4 - sqrt 10)/2"), (D(4) - D(10).sqrt()) / 2
)
assert near(
    add(
        "halves",
        [0.5, 0.25, 0.25, 1.0],
        "N = 2, sum of squares 11/8: (2 - sqrt(11/8))/(2 - sqrt 2)",
    ),
    (D(2) - (D(11) / D(8)).sqrt()) / (D(2) - D(2).sqrt()),
)
assert near(add("ones", [1.0] * 9, "N = 9, U = 3: (9 - 3)/(9 - 3) = 1"), 1)
add("ramp", [4.0, 1.0, 3.0, 2.0], "N = 10, sum of squares 30")
add("dominant", [100.0, 1.0, 1.0], "N = 102, sum of squares 10002")
add("small_values", [0.5] * 6, "N = 3 < n = 6, above 1")
rng = random.Random(539)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(539).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"mcintosh_dominance.{cid}",
            "op": "mcintosh_dominance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be above 1", samples=[0.0, 0.0, 0.0])
err("total_one", "the total must be above 1", samples=[0.5, 0.5])
err("total_small", "the total must be above 1", samples=[0.25, 0.5])

doc = {
    "schema": 1,
    "suite": "mcintosh_dominance",
    "description": "The McIntosh dominance (conventions: the McIntosh dominance; ADR 0539).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mcintosh_dominance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mcintosh_dominance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
