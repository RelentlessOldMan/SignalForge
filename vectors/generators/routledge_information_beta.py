"""Writes vectors/cases/routledge_information_beta.json, stdlib only.

Routledge's information beta (conventions: Routledge's information beta; ADR 0595):
presence counts and ln n - (2a ln 2 + p ln p + q ln q)/n with 60-digit decimal logarithms;
each hand case is also checked against its closed form.

Run from the repo root: python vectors/generators/routledge_information_beta.py [--check]
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
TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, x, y, why):
    xs = [Fr(a) for a in x]
    ys = [Fr(b) for b in y]
    both = sum(1 for a, b in zip(xs, ys) if a > 0 and b > 0)
    only_x = sum(1 for a, b in zip(xs, ys) if a > 0 and b == 0)
    only_y = sum(1 for a, b in zip(xs, ys) if a == 0 and b > 0)
    p = both + only_x
    q = both + only_y
    n = p + q
    v = D(n).ln() - (2 * both * D(2).ln() + D(p) * D(p).ln() + D(q) * D(q).ln()) / n
    cases.append(
        {
            "id": f"routledge_information_beta.{cid}",
            "op": "routledge_information_beta",
            "args": {"x": x, "y": y},
            "expected": float(v) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return v


def near(a, b):
    return abs(a - b) < D(10) ** -50


L2, L3, L5, L7 = D(2).ln(), D(3).ln(), D(5).ln(), D(7).ln()
assert near(add("same", [1.0, 2.0, 3.0], [5.0, 0.5, 1.0], "the same kinds: 0"), 0)
assert near(add("disjoint", [1.0, 0.0], [0.0, 1.0], "a = 0, b = c = 1: ln 2"), L2)
assert near(
    add("subset", [1.0, 1.0], [1.0, 0.0], "a = 1, b = 1, c = 0: ln 3 - (4/3) ln 2"), L3 - 4 * L2 / 3
)
assert near(
    add("crossed", [1.0, 2.0, 0.0, 4.0], [0.0, 3.0, 5.0, 1.0], "a = 2, b = c = 1: (1/3) ln 2"),
    L2 / 3,
)
assert near(
    add("nested", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "a = 1, b = 0, c = 2: (3/2) ln 2 - (3/4) ln 3"),
    3 * L2 / 2 - 3 * L3 / 4,
)
assert near(
    add(
        "swap", [1.0, 1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 1.0, 1.0], "a = 1, b = c = 2: (2/3) ln 2"
    ),
    2 * L2 / 3,
)
assert near(
    add(
        "uneven",
        [1.0, 1.0, 0.0, 1.0, 1.0, 1.0],
        [1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        "a = 1, b = 4, c = 1: ln 7 - (4/7) ln 2 - (5/7) ln 5",
    ),
    L7 - 4 * L2 / 7 - 5 * L5 / 7,
)
assert near(
    add(
        "lopsided",
        [1.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 1.0, 1.0, 1.0],
        "a = 0, b = 1, c = 4: ln 5 - (8/5) ln 2",
    ),
    L5 - 8 * L2 / 5,
)
assert near(
    add(
        "tiny",
        [5e-324, 0.0, 1.0],
        [0.0, 1e-300, 1.0],
        "the smallest double counts as present: a = b = c = 1: (1/2) ln 2",
    ),
    L2 / 2,
)
rng = random.Random(595)
x = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
y = [rng.choice([0.0, 0.0, 1.0, 2.5]) for _ in range(25)]
add("random", x, y, "x then y, 25 values each from random.Random(595).choice([0, 0, 1, 2.5])")


def err(cid, why, **args):
    base = {"x": [1.0, 2.0, 3.0], "y": [3.0, 1.0, 2.0]}
    base.update(args)
    cases.append(
        {
            "id": f"routledge_information_beta.{cid}",
            "op": "routledge_information_beta",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "a record needs a value", x=[], y=[])
err("negative", "values must be at least 0", y=[1.0, -0.5, 2.0])
err("all_zero", "each record needs a value above 0", x=[0.0, 0.0, 0.0])
err("lengths", "the records must have the same length", y=[1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "routledge_information_beta",
    "description": "Routledge's information beta of two presence records (conventions: Routledge's information beta; ADR 0595).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "routledge_information_beta.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/routledge_information_beta.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
