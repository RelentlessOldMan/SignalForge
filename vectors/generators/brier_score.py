"""Writes vectors/cases/brier_score.json, stdlib only.

The Brier score (conventions: Brier score; ADR 0391): the squares summed exactly in rationals
from the binary values of the probabilities, rounded once.

Run from the repo root: python vectors/generators/brier_score.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-13}
cases = []


def add(cid, outcome, probability, why):
    bs = sum((Fr(p) - Fr(y)) ** 2 for y, p in zip(outcome, probability)) / len(outcome)
    cases.append(
        {
            "id": f"brier_score.{cid}",
            "op": "brier_score",
            "args": {"outcome": outcome, "probability": probability},
            "expected": float(bs),
            "tol": TOL,
            "source": why,
        }
    )
    return bs


got = add("perfect", [1.0, 0.0, 1.0], [1.0, 0.0, 1.0], "every forecast certain and right: 0")
assert got == 0
got = add("always_wrong", [1.0, 0.0], [0.0, 1.0], "every forecast certain and wrong: 1")
assert got == 1
got = add("coin", [1.0, 0.0, 0.0, 1.0], [0.5, 0.5, 0.5, 0.5], "always 1/2: each square 1/4")
assert got == Fr(1, 4)
got = add(
    "hand",
    [1.0, 0.0, 1.0, 0.0],
    [0.75, 0.25, 0.5, 1.0],
    "squares 1/16, 1/16, 1/4, 1: sum 11/8 over 4 = 11/32",
)
assert got == Fr(11, 32)
rng = random.Random(391)
prob = [rng.random() for _ in range(300)]
outc = [1.0 if rng.random() < p else 0.0 for p in prob]
add(
    "calibrated",
    outc,
    prob,
    "300 forecasts from random.Random(391), each outcome drawn with its forecast probability",
)


def err(cid, why, **args):
    base = {"outcome": [1.0, 0.0, 1.0], "probability": [0.9, 0.2, 0.6]}
    base.update(args)
    cases.append(
        {
            "id": f"brier_score.{cid}",
            "op": "brier_score",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "outcome and probability must be the same length", probability=[0.5])
err("empty", "N must be at least 1", outcome=[], probability=[])
err("outcome_not_binary", "outcomes must be 0 or 1", outcome=[1.0, 0.5, 1.0])
err("probability_above_one", "probabilities must be at most 1", probability=[0.9, 1.25, 0.6])
err("probability_negative", "probabilities must be at least 0", probability=[0.9, -0.1, 0.6])

doc = {
    "schema": 1,
    "suite": "brier_score",
    "description": "The Brier score (conventions: Brier score; ADR 0391).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "brier_score.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/brier_score.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
