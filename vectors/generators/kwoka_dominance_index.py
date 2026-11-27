"""Writes vectors/cases/kwoka_dominance_index.json, stdlib only.

The Kwoka dominance index (conventions: the Kwoka dominance index; ADR 0526): dyadic shares
ranked from the largest, the squared neighbouring gaps summed exactly in rationals.

Run from the repo root: python vectors/generators/kwoka_dominance_index.py [--check]
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
    v = sorted((Fr(a) for a in x), reverse=True)
    total = sum(v)
    q = sum(((a - b) / total) ** 2 for a, b in zip(v, v[1:]))
    cases.append(
        {
            "id": f"kwoka_dominance_index.{cid}",
            "op": "kwoka_dominance_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [2.0, 2.0, 2.0, 2.0], "four equal shares: 0")
assert got == 0
got = add("single", [5.0], "one value, no pairs: 0")
assert got == 0
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "the largest holds the total: 1")
assert got == 1
got = add("two", [3.0, 1.0], "shares 3/4, 1/4: (1/2)^2 = 1/4")
assert got == Fr(1, 4)
got = add("ramp", [4.0, 1.0, 3.0, 2.0], "shares 4, 3, 2, 1 tenths: 3 (1/10)^2 = 3/100")
assert got == Fr(3, 100)
got = add("three", [3.0, 0.0, 1.0], "shares 3/4, 1/4, 0: 1/4 + 1/16 = 5/16")
assert got == Fr(5, 16)
got = add("halves", [0.5, 0.25, 0.25, 1.0], "shares 1/2, 1/4, 1/8, 1/8: 1/16 + 1/64 + 0 = 5/64")
assert got == Fr(5, 64)
rng = random.Random(526)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(526).randint(0, 64)")
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
            "id": f"kwoka_dominance_index.{cid}",
            "op": "kwoka_dominance_index",
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
    "suite": "kwoka_dominance_index",
    "description": "The Kwoka dominance index (conventions: the Kwoka dominance index; ADR 0526).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "kwoka_dominance_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/kwoka_dominance_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
