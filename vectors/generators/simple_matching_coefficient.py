"""Writes vectors/cases/simple_matching_coefficient.json, stdlib only.

The simple matching coefficient (conventions: simple matching coefficient; ADR 0424): the
agreements counted directly.

Run from the repo root: python vectors/generators/simple_matching_coefficient.py [--check]
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
    v = Fr(sum(1 for a, b in zip(t, d) if a == b), len(t))
    cases.append(
        {
            "id": f"simple_matching_coefficient.{cid}",
            "op": "simple_matching_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(v),
            "tol": TOL,
            "source": why,
        }
    )
    return v


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "the same record: 1")
assert got == 1
got = add(
    "all_zero",
    [0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0],
    "shared absences count: 1 (the Jaccard index is undefined here)",
)
assert got == 1
got = add("opposite", [1.0, 0.0, 1.0], [0.0, 1.0, 0.0], "every item differs: 0")
assert got == 0
got = add(
    "partial", [1.0, 1.0, 0.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0, 1.0], "agree at items 0, 2, 4: 3/5"
)
assert got == Fr(3, 5)
rng = random.Random(424)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.9 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(424), about a tenth flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"simple_matching_coefficient.{cid}",
            "op": "simple_matching_coefficient",
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
    "suite": "simple_matching_coefficient",
    "description": "The simple matching coefficient (conventions: simple matching coefficient;"
    " ADR 0424).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "simple_matching_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/simple_matching_coefficient.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
