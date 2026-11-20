"""Writes vectors/cases/doolittle_coefficient.json, stdlib only.

The Doolittle coefficient (conventions: the Doolittle coefficient; ADR 0466): the 2x2 table
counted directly, the value formed in rationals.

Run from the repo root: python vectors/generators/doolittle_coefficient.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    n, na, nb = len(t), tp + fn, tp + fp
    q = Fr((n * tp - na * nb) ** 2, na * nb * (n - na) * (n - nb))
    cases.append(
        {
            "id": f"doolittle_coefficient.{cid}",
            "op": "doolittle_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 2, all margins 2: (8 - 4)^2/(4 4) = 1",
)
assert got == 1
got = add("independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "n 4, TP 1, all margins 2: 0")
assert got == 0
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, TP 0, all margins 2: (-4)^2/16 = 1",
)
assert got == 1
got = add(
    "far_below",
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0],
    "n 4, TP 0, |A| 1, |B| 3: (-3)^2/(3 3) = 1, one record the other flipped",
)
assert got == 1
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "n 6, TP 2, |A| 3, |B| 2: 6^2/(6 12) = 1/2",
)
assert got == Fr(1, 2)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, TP 4, all margins 5: 15^2/(25 25) = 9/25",
)
assert got == Fr(9, 25)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "n 5, TP 1, |A| = |B| = 2: 1^2/(4 9) = 1/36",
)
assert got == Fr(1, 36)
rng = random.Random(466)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(466), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"doolittle_coefficient.{cid}",
            "op": "doolittle_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("all_one", "truth all 1: n - |A| is 0", truth=[1.0, 1.0, 1.0], decision=[1.0, 0.0, 1.0])
err("no_one", "decision has no 1: |B| is 0", truth=[1.0, 0.0, 1.0], decision=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "doolittle_coefficient",
    "description": "The Doolittle coefficient (conventions: the Doolittle coefficient; ADR 0466).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "doolittle_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/doolittle_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
