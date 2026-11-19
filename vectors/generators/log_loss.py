"""Writes vectors/cases/log_loss.json, stdlib only.

The log loss (conventions: Log loss; ADR 0392): each term from math.log, summed with
math.fsum; the hand cases are multiples of ln 2.

Run from the repo root: python vectors/generators/log_loss.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys

TOL = {"abs": 1e-15, "rel": 1e-13}
cases = []


def add(cid, outcome, probability, why):
    terms = [math.log(p if y == 1 else 1.0 - p) for y, p in zip(outcome, probability)]
    ll = 0.0 - math.fsum(terms) / len(outcome)
    cases.append(
        {
            "id": f"log_loss.{cid}",
            "op": "log_loss",
            "args": {"outcome": outcome, "probability": probability},
            "expected": ll,
            "tol": TOL,
            "source": why,
        }
    )
    return ll


got = add("perfect", [1.0, 0.0, 1.0], [1.0, 0.0, 1.0], "every forecast certain and right: 0")
assert got == 0
got = add("coin", [1.0, 0.0, 0.0, 1.0], [0.5, 0.5, 0.5, 0.5], "always 1/2: ln 2 per item")
assert abs(got - math.log(2)) < 1e-16
got = add(
    "hand",
    [1.0, 0.0, 1.0, 0.0],
    [0.25, 0.75, 0.5, 0.5],
    "terms ln 1/4, ln 1/4, ln 1/2, ln 1/2: 6 ln 2 over 4 = 1.5 ln 2",
)
assert abs(got - 1.5 * math.log(2)) < 1e-15
got = add("one_certain_right", [1.0, 0.0], [1.0, 0.5], "terms 0 and ln 1/2: ln 2 / 2")
assert abs(got - math.log(2) / 2) < 1e-16
rng = random.Random(392)
prob = [0.01 + 0.98 * rng.random() for _ in range(300)]
outc = [1.0 if rng.random() < p else 0.0 for p in prob]
add(
    "calibrated",
    outc,
    prob,
    "300 forecasts in [0.01, 0.99] from random.Random(392), each "
    "outcome drawn with its forecast probability",
)


def err(cid, why, **args):
    base = {"outcome": [1.0, 0.0, 1.0], "probability": [0.9, 0.2, 0.6]}
    base.update(args)
    cases.append(
        {
            "id": f"log_loss.{cid}",
            "op": "log_loss",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "outcome and probability must be the same length", probability=[0.5])
err("empty", "N must be at least 1", outcome=[], probability=[])
err("outcome_not_binary", "outcomes must be 0 or 1", outcome=[1.0, 0.5, 1.0])
err("probability_above_one", "probabilities must be at most 1", probability=[0.9, 1.25, 0.6])
err("certain_and_wrong_positive", "p = 0 with y = 1: infinite loss", probability=[0.0, 0.2, 0.6])
err("certain_and_wrong_negative", "p = 1 with y = 0: infinite loss", probability=[0.9, 1.0, 0.6])

doc = {
    "schema": 1,
    "suite": "log_loss",
    "description": "The log loss (conventions: Log loss; ADR 0392).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "log_loss.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/log_loss.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
