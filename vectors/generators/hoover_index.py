"""Writes vectors/cases/hoover_index.json, stdlib only.

The Hoover index (conventions: the Hoover index; ADR 0512): the absolute deviations of dyadic
values from their mean summed exactly in rationals, over twice the total.

Run from the repo root: python vectors/generators/hoover_index.py [--check]
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
    mean = sum(v) / n
    q = sum(abs(a - mean) for a in v) / (2 * sum(v))
    cases.append(
        {
            "id": f"hoover_index.{cid}",
            "op": "hoover_index",
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
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "mean 1: (1 + 1 + 1 + 3)/8 = 3/4")
assert got == Fr(3, 4)
got = add("two", [1.0, 3.0], "mean 2: (1 + 1)/8 = 1/4")
assert got == Fr(1, 4)
got = add("ramp", [1.0, 2.0, 3.0, 4.0], "mean 5/2: (3/2 + 1/2 + 1/2 + 3/2)/20 = 1/5")
assert got == Fr(1, 5)
got = add("unsorted", [3.0, 0.0, 1.0], "mean 4/3: (5/3 + 4/3 + 1/3)/8 = 5/12")
assert got == Fr(5, 12)
got = add("halves", [0.5, 0.25, 0.25, 1.0], "mean 1/2: (0 + 1/4 + 1/4 + 1/2)/4 = 1/4")
assert got == Fr(1, 4)
rng = random.Random(512)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(512).randint(0, 64)")
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
            "id": f"hoover_index.{cid}",
            "op": "hoover_index",
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
    "suite": "hoover_index",
    "description": "The Hoover index (conventions: the Hoover index; ADR 0512).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hoover_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hoover_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
