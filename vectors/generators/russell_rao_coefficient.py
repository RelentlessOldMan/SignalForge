"""Writes vectors/cases/russell_rao_coefficient.json, stdlib only.

The Russell-Rao coefficient (conventions: Russell-Rao coefficient; ADR 0426): the shared 1s
counted directly.

Run from the repo root: python vectors/generators/russell_rao_coefficient.py [--check]
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
    v = Fr(sum(1 for a, b in zip(t, d) if a == 1 and b == 1), len(t))
    cases.append(
        {
            "id": f"russell_rao_coefficient.{cid}",
            "op": "russell_rao_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(v),
            "tol": TOL,
            "source": why,
        }
    )
    return v


got = add("all_ones", [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], "both all 1: 1")
assert got == 1
got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "the same record, half 1: 1/2 (shared 0s do not count)",
)
assert got == Fr(1, 2)
got = add("all_zero", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "no 1 at all: 0")
assert got == 0
got = add(
    "partial", [1.0, 1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0, 1.0], "both 1 at items 0 and 4: 2/5"
)
assert got == Fr(2, 5)
rng = random.Random(426)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [float(rng.random() < 0.5) for _ in range(40)]
add("random", t, d, "40 items each from random.Random(426)")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"russell_rao_coefficient.{cid}",
            "op": "russell_rao_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", truth=[1.0, 2.0, 0.0])

doc = {
    "schema": 1,
    "suite": "russell_rao_coefficient",
    "description": "The Russell-Rao coefficient (conventions: Russell-Rao coefficient; ADR 0426).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "russell_rao_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/russell_rao_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
