"""Writes vectors/cases/concentration_ratio.json, stdlib only.

The concentration ratio (conventions: the concentration ratio; ADR 0524): the k largest of
dyadic values summed exactly in rationals, over the total.

Run from the repo root: python vectors/generators/concentration_ratio.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, x, k, why):
    v = sorted((Fr(a) for a in x), reverse=True)
    q = sum(v[:k]) / sum(v)
    cases.append(
        {
            "id": f"concentration_ratio.{cid}",
            "op": "concentration_ratio",
            "args": {"samples": x, "k": k},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [2.0, 2.0, 2.0, 2.0], 1, "one of four equal values: 1/4")
assert got == Fr(1, 4)
got = add("all", [1.0, 2.0, 3.0], 3, "k = n: 1")
assert got == 1
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], 1, "the largest holds the total: 1")
assert got == 1
got = add("ramp", [4.0, 1.0, 3.0, 2.0], 2, "(4 + 3)/10 = 7/10")
assert got == Fr(7, 10)
got = add("three", [3.0, 0.0, 1.0], 1, "3/4")
assert got == Fr(3, 4)
got = add("halves", [0.5, 0.25, 0.25, 1.0], 3, "(1 + 1/2 + 1/4)/2 = 7/8")
assert got == Fr(7, 8)
rng = random.Random(524)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, 6, "30 values k/8, k from random.Random(524).randint(0, 64); the 6 largest")
add(
    "huge",
    [1e308, 9e307, 1e300],
    1,
    "values whose sum overflows a double: the result is that of the values scaled down",
)


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0], "k": 1}
    base.update(args)
    cases.append(
        {
            "id": f"concentration_ratio.{cid}",
            "op": "concentration_ratio",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the record needs a value", samples=[])
err("negative", "values must be at least 0", samples=[1.0, -0.5, 2.0])
err("all_zero", "the total must be positive", samples=[0.0, 0.0, 0.0])
err("k_zero", "k must be at least 1", k=0)
err("k_too_big", "k must be at most n", k=4)

doc = {
    "schema": 1,
    "suite": "concentration_ratio",
    "description": "The concentration ratio (conventions: the concentration ratio; ADR 0524).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "concentration_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/concentration_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
