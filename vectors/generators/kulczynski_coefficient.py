"""Writes vectors/cases/kulczynski_coefficient.json, stdlib only.

The Kulczynski coefficient (conventions: Kulczynski coefficient; ADR 0428): the sets
counted directly, the value formed in rationals.

Run from the repo root: python vectors/generators/kulczynski_coefficient.py [--check]
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
    c = (Fr(len(a & b), len(a)) + Fr(len(a & b), len(b))) / 2
    cases.append(
        {
            "id": f"kulczynski_coefficient.{cid}",
            "op": "kulczynski_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(c),
            "tol": TOL,
            "source": why,
        }
    )
    return c


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "the same set: 1")
assert got == 1
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 0.0],
    "recall 1/3, precision 1: (1/3 + 1)/2 = 2/3",
)
assert got == Fr(2, 3)
got = add("disjoint", [1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], "no shared item: 0")
assert got == 0
got = add(
    "partial",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0, 1.0],
    "A = {0, 1, 2}, B = {1, 2, 3, 4}: (2/3 + 2/4)/2 = 7/12",
)
assert got == Fr(7, 12)
rng = random.Random(428)
t = [float(rng.random() < 0.4) for _ in range(40)]
d = [float(rng.random() < 0.5) for _ in range(40)]
add("random", t, d, "40 items each from random.Random(428)")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"kulczynski_coefficient.{cid}",
            "op": "kulczynski_coefficient",
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
    "suite": "kulczynski_coefficient",
    "description": "The Kulczynski coefficient (conventions: Kulczynski coefficient; ADR 0428).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "kulczynski_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/kulczynski_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
