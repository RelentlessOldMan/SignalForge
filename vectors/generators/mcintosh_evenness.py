"""Writes vectors/cases/mcintosh_evenness.json, stdlib only.

The McIntosh evenness (conventions: the McIntosh evenness; ADR 0540): the sums of dyadic
values formed exactly, the square roots in 50-digit decimal.

Run from the repo root: python vectors/generators/mcintosh_evenness.py [--check]
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
    q = (dec(total) - dec(sq).sqrt()) / (dec(total) - dec(total) / D(len(v)).sqrt())
    cases.append(
        {
            "id": f"mcintosh_evenness.{cid}",
            "op": "mcintosh_evenness",
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
assert near(add("equal", [2.0] * 4, "N = 8, U = 4 = N/sqrt 4: 1"), 1)
assert near(add("equal_small", [0.5] * 6, "every value equal: 1"), 1)
assert near(
    add("two", [3.0, 1.0], "N = 4, U = sqrt 10: (4 - sqrt 10)/(4 - 4/sqrt 2)"),
    (D(4) - D(10).sqrt()) / (D(4) - D(4) / D(2).sqrt()),
)
assert near(
    add("halves", [0.5, 0.25, 0.25, 1.0], "N = 2, sum of squares 11/8: (2 - sqrt(11/8))/(2 - 1)"),
    D(2) - (D(11) / D(8)).sqrt(),
)
assert near(
    add("one_zero", [0.0, 2.0, 2.0, 2.0], "N = 6, U = sqrt 12: (6 - 2 sqrt 3)/(6 - 3)"),
    (D(6) - 2 * D(3).sqrt()) / 3,
)
add("ramp", [4.0, 1.0, 3.0, 2.0], "N = 10, sum of squares 30")
add("dominant", [100.0, 1.0, 1.0], "N = 102, sum of squares 10002")
rng = random.Random(540)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(540).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"mcintosh_evenness.{cid}",
            "op": "mcintosh_evenness",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs at least 2 values", samples=[])
err("single", "the record needs at least 2 values", samples=[5.0])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "mcintosh_evenness",
    "description": "The McIntosh evenness (conventions: the McIntosh evenness; ADR 0540).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mcintosh_evenness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mcintosh_evenness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
