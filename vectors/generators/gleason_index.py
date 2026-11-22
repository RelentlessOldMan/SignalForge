"""Writes vectors/cases/gleason_index.json, stdlib only.

Gleason's index (conventions: Gleason's index; ADR 0543): the total of dyadic values
formed exactly, the logarithm in 50-digit decimal.

Run from the repo root: python vectors/generators/gleason_index.py [--check]
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
    q = D(sum(1 for a in v if a > 0)) / dec(total).ln()
    cases.append(
        {
            "id": f"gleason_index.{cid}",
            "op": "gleason_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def near(q, want):
    return abs(q - want) < D("1e-40")


assert near(add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "k = 1, N = 4: 1/ln 4"), 1 / D(4).ln())
assert near(add("equal", [2.0] * 4, "k = 4, N = 8: 4/ln 8"), 4 / D(8).ln())
assert near(add("two", [3.0, 1.0], "k = 2, N = 4: 2/ln 4 = 1/ln 2"), 1 / D(2).ln())
assert near(add("halves", [0.5, 0.25, 0.25, 1.0], "k = 4, N = 2: 4/ln 2"), 4 / D(2).ln())
assert near(add("ones", [1.0] * 9, "k = 9, N = 9: 9/ln 9"), 9 / D(9).ln())
assert near(add("one_zero", [0.0, 2.0, 2.0, 2.0], "k = 3, N = 6: 3/ln 6"), 3 / D(6).ln())
assert near(add("four_to_one", [16.0, 4.0], "k = 2, N = 20: 2/ln 20"), 2 / D(20).ln())
add("ramp", [4.0, 1.0, 3.0, 2.0], "k = 4, N = 10")
add("near_one", [0.5, 0.5, 0.125], "k = 3, N = 9/8")
rng = random.Random(543)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(543).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"gleason_index.{cid}",
            "op": "gleason_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be above 1", samples=[0.0, 0.0, 0.0])
err("total_one", "the total must be above 1", samples=[0.5, 0.5])
err("single_one", "the total must be above 1", samples=[1.0])

doc = {
    "schema": 1,
    "suite": "gleason_index",
    "description": "Gleason's index (conventions: Gleason's index; ADR 0543).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gleason_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/gleason_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
