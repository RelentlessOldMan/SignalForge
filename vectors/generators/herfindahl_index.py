"""Writes vectors/cases/herfindahl_index.json, stdlib only.

The Herfindahl index (conventions: the Herfindahl index; ADR 0523): the squared shares of
dyadic values formed exactly in rationals.

Run from the repo root: python vectors/generators/herfindahl_index.py [--check]
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
    q = sum((a / total) ** 2 for a in v)
    cases.append(
        {
            "id": f"herfindahl_index.{cid}",
            "op": "herfindahl_index",
            "args": {"samples": x},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("equal", [2.0, 2.0, 2.0, 2.0], "four equal shares: 4 (1/4)^2 = 1/4")
assert got == Fr(1, 4)
got = add("single", [5.0], "one value: 1")
assert got == 1
got = add("one_holds_all", [0.0, 0.0, 0.0, 4.0], "one of four holds the total: 1")
assert got == 1
got = add("ramp", [4.0, 1.0, 3.0, 2.0], "(1 + 4 + 9 + 16)/100 = 3/10")
assert got == Fr(3, 10)
got = add("three", [3.0, 0.0, 1.0], "(9 + 0 + 1)/16 = 5/8")
assert got == Fr(5, 8)
got = add("halves", [0.5, 0.25, 0.25, 1.0], "(1/4 + 1/16 + 1/16 + 1)/4 = 11/32")
assert got == Fr(11, 32)
rng = random.Random(523)
x = [rng.randint(0, 64) / 8 for _ in range(30)]
add("random", x, "30 values k/8, k from random.Random(523).randint(0, 64)")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0, 3.0]}
    base.update(args)
    cases.append(
        {
            "id": f"herfindahl_index.{cid}",
            "op": "herfindahl_index",
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
    "suite": "herfindahl_index",
    "description": "The Herfindahl index (conventions: the Herfindahl index; ADR 0523).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "herfindahl_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/herfindahl_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
