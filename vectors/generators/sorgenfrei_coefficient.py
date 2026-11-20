"""Writes vectors/cases/sorgenfrei_coefficient.json, stdlib only.

The Sorgenfrei coefficient (conventions: Sorgenfrei coefficient; ADR 0434): the sets
counted directly, the value formed in rationals.

Run from the repo root: python vectors/generators/sorgenfrei_coefficient.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, t, d, why):
    a = {i for i, v in enumerate(t) if v == 1}
    b = {i for i, v in enumerate(d) if v == 1}
    c = Fr(len(a & b) ** 2, len(a) * len(b))
    cases.append(
        {
            "id": f"sorgenfrei_coefficient.{cid}",
            "op": "sorgenfrei_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(c),
            "tol": TOL,
            "source": why,
        }
    )
    return c


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "the same set: 1")
assert got == 1
got = add("subset", [1.0, 1.0, 1.0, 0.0], [0.0, 1.0, 0.0, 0.0], "|A| 3, |B| 1, TP 1: 1/3")
assert got == Fr(1, 3)
got = add("disjoint", [1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], "no shared item: 0")
assert got == 0
got = add(
    "partial",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0, 1.0],
    "A = {0, 1, 2}, B = {1, 2, 3, 4}: 4/12 = 1/3",
)
assert got == Fr(1, 3)
got = add(
    "square", [1.0, 1.0, 1.0, 1.0, 0.0], [1.0, 1.0, 0.0, 0.0, 0.0], "|A| 4, |B| 2, TP 2: 4/8 = 1/2"
)
assert got == Fr(1, 2)
got = add(
    "thirds",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0, 0.0, 0.0],
    "|A| 3, |B| 3, TP 2: 4/9",
)
assert got == Fr(4, 9)
rng = random.Random(434)
t = [float(rng.random() < 0.4) for _ in range(40)]
d = [float(rng.random() < 0.5) for _ in range(40)]
add("random", t, d, "40 items each from random.Random(434)")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"sorgenfrei_coefficient.{cid}",
            "op": "sorgenfrei_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_one", "the decision holds no 1", decision=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "sorgenfrei_coefficient",
    "description": "The Sorgenfrei coefficient (conventions: Sorgenfrei coefficient; ADR 0434).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "sorgenfrei_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/sorgenfrei_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
