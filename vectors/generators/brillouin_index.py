"""Writes vectors/cases/brillouin_index.json, stdlib only.

The Brillouin index (conventions: the Brillouin index; ADR 0546): the multinomial
coefficient formed exactly, its logarithm in 50-digit decimal.

Run from the repo root: python vectors/generators/brillouin_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import math
import pathlib
import random
import sys
from decimal import Decimal as D

decimal.getcontext().prec = 50
TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def add(cid, x, why):
    v = [int(a) for a in x]
    assert all(a == b for a, b in zip(v, x))
    total = sum(v)
    m = math.factorial(total)
    for a in v:
        m //= math.factorial(a)
    q = D(m).ln() / total
    cases.append(
        {
            "id": f"brillouin_index.{cid}",
            "op": "brillouin_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("two_ones", [1.0, 1.0], "N = 2, 2!/(1! 1!) = 2: ln 2 / 2") == D(2).ln() / 2
assert add("one_holds_all", [0.0, 4.0], "one kind: ln 1 / 4 = 0") == 0
assert add("single", [2.0], "one kind: 0") == 0
assert add("four_ones", [1.0] * 4, "4! = 24: ln 24 / 4") == D(24).ln() / 4
assert add("two_twos", [2.0, 2.0], "4!/(2! 2!) = 6: ln 6 / 4") == D(6).ln() / 4
assert add("two", [3.0, 1.0], "4!/3! = 4: ln 4 / 4") == D(4).ln() / 4
assert add("ramp", [1.0, 2.0, 3.0], "6!/(1! 2! 3!) = 60: ln 60 / 6") == D(60).ln() / 6
add("larger", [40.0, 25.0, 0.0, 10.0, 25.0], "100!/(40! 25! 10! 25!) exactly")
rng = random.Random(546)
x = [float(rng.randint(0, 20)) for _ in range(30)]
add("random", x, "30 whole values from random.Random(546).randint(0, 20)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"brillouin_index.{cid}",
            "op": "brillouin_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("fraction", "values must be whole numbers", samples=[1.5, 2.0])
err("too_large", "the total must be at most 10 000 000", samples=[10000000.0, 1.0])

doc = {
    "schema": 1,
    "suite": "brillouin_index",
    "description": "The Brillouin index (conventions: the Brillouin index; ADR 0546).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "brillouin_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/brillouin_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
