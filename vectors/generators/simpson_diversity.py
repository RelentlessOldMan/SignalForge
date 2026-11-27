"""Writes vectors/cases/simpson_diversity.json, stdlib only.

The Gini-Simpson index (conventions: the Gini-Simpson index; ADR 0529): one less the
squared shares of dyadic values, formed exactly in rationals.

Run from the repo root: python vectors/generators/simpson_diversity.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, x, why):
    v = [Fr(a) for a in x]
    total = sum(v)
    q = 1 - sum((a / total) ** 2 for a in v)
    cases.append(
        {
            "id": f"simpson_diversity.{cid}",
            "op": "simpson_diversity",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


assert add("equal", [2.0] * 4, "four equal shares: 1 - 4/16 = 3/4") == Fr(3, 4)
assert add("single", [5.0], "one value: 0") == 0
assert add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one share of 1: 0") == 0
assert add("two", [3.0, 1.0], "shares 3/4, 1/4: 1 - 10/16 = 3/8") == Fr(3, 8)
assert add("ramp", [4.0, 1.0, 3.0, 2.0], "shares 4, 1, 3, 2 tenths: 1 - 30/100 = 7/10") == Fr(7, 10)
assert add("three", [3.0, 0.0, 1.0], "shares 3/4, 0, 1/4: 1 - 10/16 = 3/8") == Fr(3, 8)
assert add("halves", [0.5, 0.25, 0.25, 1.0], "shares 1/4, 1/8, 1/8, 1/2: 1 - 22/64 = 21/32") == Fr(
    21, 32
)
rng = random.Random(529)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(529).randint(0, 64)")
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
            "id": f"simpson_diversity.{cid}",
            "op": "simpson_diversity",
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
    "suite": "simpson_diversity",
    "description": "The Gini-Simpson index (conventions: the Gini-Simpson index; ADR 0529).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "simpson_diversity.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/simpson_diversity.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
