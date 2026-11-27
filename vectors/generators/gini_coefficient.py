"""Writes vectors/cases/gini_coefficient.json, stdlib only.

The Gini coefficient (conventions: the Gini coefficient; ADR 0510): the defining sum of
|x_i - x_j| over every ordered pair of dyadic values, over 2 n^2 mean, exact in rationals.

Run from the repo root: python vectors/generators/gini_coefficient.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, x, why):
    v = [Fr(a) for a in x]
    n = len(v)
    q = sum(abs(a - b) for a in v for b in v) / (2 * n * sum(v))
    cases.append(
        {
            "id": f"gini_coefficient.{cid}",
            "op": "gini_coefficient",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [2.0, 2.0, 2.0], "every value equal: 0")
assert got == 0
got = add("single", [5.0], "one value: 1 - 1/1 = 0")
assert got == 0
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one of four holds the total: 1 - 1/4")
assert got == Fr(3, 4)
got = add("two", [1.0, 3.0], "pair sum 2 2 = 4, over 2 4 2 = 16: 1/4")
assert got == Fr(1, 4)
got = add("ramp", [1.0, 2.0, 3.0, 4.0], "pair sum 2 10 = 20, over 2 16 5/2 = 80: 1/4")
assert got == Fr(1, 4)
got = add("unsorted", [3.0, 0.0, 1.0], "pair sum 2 6 = 12, over 2 9 4/3 = 24: 1/2")
assert got == Fr(1, 2)
got = add(
    "halves",
    [0.5, 0.25, 0.25, 1.0],
    "pair sum 2 (1/4 + 1/4 + 1/2 + 0 + 3/4 + 3/4) = 5, over 2 4 2 = 16: 5/16",
)
assert got == Fr(5, 16)
rng = random.Random(510)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(510).randint(0, 64)")
add(
    "huge",
    [1e308, 9e307, 1e300],
    "values whose sum overflows a double: the result is that of the values scaled down",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"gini_coefficient.{cid}",
            "op": "gini_coefficient",
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
    "suite": "gini_coefficient",
    "description": "The Gini coefficient (conventions: the Gini coefficient; ADR 0510).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gini_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/gini_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
