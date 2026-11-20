"""Writes vectors/cases/gilbert_skill_score.json, stdlib only.

The Gilbert skill score (conventions: Gilbert skill score; ADR 0439): the 2x2 table counted
directly, the value formed in rationals from the chance hits R = |A||B|/n.

Run from the repo root: python vectors/generators/gilbert_skill_score.py [--check]
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
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = sum(1 for a, b in zip(t, d) if a == 0 and b == 0)
    chance = Fr((tp + fn) * (tp + fp), len(t))
    q = (tp - chance) / (tp + fn + fp - chance)
    cases.append(
        {
            "id": f"gilbert_skill_score.{cid}",
            "op": "gilbert_skill_score",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "TP 2, TN 2, R 1: (2 - 1)/(2 - 1) = 1"
)
assert got == 1
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "FN 2, FP 2, R 1: (0 - 1)/(4 - 1) = -1/3, the least value",
)
assert got == Fr(-1, 3)
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell, R 1: (1 - 1)/(3 - 1) = 0",
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 1, FN 1, FP 1, TN 2, R 4/5: (1/5)/(11/5) = 1/11",
)
assert got == Fr(1, 11)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1, R 5/2: (3/2)/(7/2) = 3/7",
)
assert got == Fr(3, 7)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 1, FN 2, FP 0, TN 2, R 3/5: (2/5)/(12/5) = 1/6",
)
assert got == Fr(1, 6)
rng = random.Random(439)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(439), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"gilbert_skill_score.{cid}",
            "op": "gilbert_skill_score",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "all_one",
    "both all 1: R = n = TP, so the denominator is 0",
    truth=[1.0, 1.0, 1.0],
    decision=[1.0, 1.0, 1.0],
)
err(
    "all_zero",
    "both all 0: TP, FN, FP and R are 0",
    truth=[0.0, 0.0, 0.0],
    decision=[0.0, 0.0, 0.0],
)

doc = {
    "schema": 1,
    "suite": "gilbert_skill_score",
    "description": "The Gilbert skill score (conventions: Gilbert skill score; ADR 0439).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gilbert_skill_score.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/gilbert_skill_score.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
