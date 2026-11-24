"""Writes vectors/cases/johnson_rank_preference.json, stdlib only.

Johnson's rank preference index (conventions: Johnson's rank preference index; ADR 0608):
each value ranked from 1 for the largest by counting the values above it and the values
equal to it, and the rank of use less the rank of availability.

Run from the repo root: python vectors/generators/johnson_rank_preference.py [--check]
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
TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def rank(vs, i):
    above = sum(1 for v in vs if v > vs[i])
    tied = sum(1 for v in vs if v == vs[i])
    return above + Fr(tied + 1, 2)


def add(cid, x, available, why):
    f = [rank(x, i) - rank(available, i) for i in range(len(x))]
    cases.append(
        {
            "id": f"johnson_rank_preference.{cid}",
            "op": "johnson_rank_preference",
            "args": {"x": x, "available": available},
            "expected": [float(fi) + 0.0 for fi in f],
            "tol": TOL,
            "source": why,
        }
    )
    return f


assert add(
    "same_order", [3.0, 2.0, 1.0], [3.0, 2.0, 1.0], "use ranked as availability: 0 for each kind"
) == [0, 0, 0]
assert add(
    "reversed",
    [1.0, 2.0, 3.0],
    [3.0, 2.0, 1.0],
    "use ranks 3, 2, 1, availability ranks 1, 2, 3: 2, 0, -2",
) == [2, 0, -2]
assert add(
    "ties",
    [1.0, 1.0, 0.0],
    [1.0, 2.0, 3.0],
    "use ranks 1.5, 1.5, 3, availability ranks 3, 2, 1: -1.5, -0.5, 2",
) == [Fr(-3, 2), Fr(-1, 2), 2]
assert add("one_kind", [2.0], [5.0], "one kind: 0") == [0]
assert add(
    "tiny",
    [5e-324, 0.0, 1.0],
    [1.0, 1.0, 1.0],
    "the smallest double ranks above 0: use ranks 2, 3, 1, availability all 2: 0, 1, -1",
) == [0, 1, -1]
assert add(
    "huge",
    [1e308, 1e308, 1.0],
    [1.0, 2.0, 3.0],
    "use ranks 1.5, 1.5, 3, availability ranks 3, 2, 1: -1.5, -0.5, 2",
) == [Fr(-3, 2), Fr(-1, 2), 2]
assert add(
    "uneven",
    [2.0, 1.0, 1.0, 0.0],
    [1.0, 2.0, 1.0, 4.0],
    "use ranks 1, 2.5, 2.5, 4, availability ranks 3.5, 2, 3.5, 1: -2.5, 0.5, -1, 3",
) == [Fr(-5, 2), Fr(1, 2), -1, 3]
rng = random.Random(608)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
x[0] = 1.0
available = [rng.choice([0.5, 1.0, 2.5]) for _ in range(25)]
add(
    "random",
    x,
    available,
    "x then available, 25 values each from random.Random(608)"
    ".choice([0, 0, 1, 2.5]) with x[0] = 1, and .choice([0.5, 1, 2.5])",
)


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "available": [1.0, 1.0, 1.0]}
    base.update(args)
    cases.append(
        {
            "id": f"johnson_rank_preference.{cid}",
            "op": "johnson_rank_preference",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "a record needs a value", x=[], available=[])
err("negative", "values must be at least 0", x=[1.0, -0.5, 2.0])
err("all_zero", "a record needs a value above 0", x=[0.0, 0.0, 0.0])
err("lengths", "the records must have the same length", available=[1.0, 2.0])
err("unavailable", "available must be above 0 everywhere", available=[1.0, 0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "johnson_rank_preference",
    "description": "Johnson's rank preference index (conventions: Johnson's rank preference "
    "index; ADR 0608).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "johnson_rank_preference.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/johnson_rank_preference.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
