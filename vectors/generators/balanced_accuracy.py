"""Writes vectors/cases/balanced_accuracy.json, stdlib only.

The balanced accuracy (conventions: Balanced accuracy; ADR 0396): the table counted in
integers, the sensitivity and specificity averaged exactly in rationals.

Run from the repo root: python vectors/generators/balanced_accuracy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, truth, decision, why):
    pairs = list(zip(truth, decision))
    tp, tn = pairs.count((1.0, 1.0)), pairs.count((0.0, 0.0))
    fp, fn = pairs.count((0.0, 1.0)), pairs.count((1.0, 0.0))
    ba = (Fr(tp, tp + fn) + Fr(tn, tn + fp)) / 2
    cases.append(
        {
            "id": f"balanced_accuracy.{cid}",
            "op": "balanced_accuracy",
            "args": {"truth": truth, "decision": decision},
            "expected": float(ba),
            "tol": TOL,
            "source": why,
        }
    )
    return ba


got = add("perfect", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "both rates 1: 1")
assert got == 1
got = add("inverted", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "both rates 0: 0")
assert got == 0
got = add(
    "always_negative",
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [0.0] * 10,
    "accuracy 9/10 but sensitivity 0, specificity 1: 1/2",
)
assert got == Fr(1, 2)
got = add(
    "hand",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    "sensitivity 2/3, specificity 3/4: 17/24",
)
assert got == Fr(17, 24)
rng = random.Random(396)
truth = [1.0 if rng.random() < 0.15 else 0.0 for _ in range(300)]
decision = [t if rng.random() < 0.8 else 1.0 - t for t in truth]
add(
    "noisy_detector",
    truth,
    decision,
    "300 items from random.Random(396), 15% positive, each decision flipped with probability 0.2",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 1.0, 0.0, 0.0], "decision": [1.0, 0.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"balanced_accuracy.{cid}",
            "op": "balanced_accuracy",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and decision must be the same length", decision=[1.0, 0.0])
err("empty", "N must be at least 1", truth=[], decision=[])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.0, 1.0, 0.5])
err("no_positive", "the sensitivity is undefined", truth=[0.0, 0.0, 0.0, 0.0])
err("no_negative", "the specificity is undefined", truth=[1.0, 1.0, 1.0, 1.0])

doc = {
    "schema": 1,
    "suite": "balanced_accuracy",
    "description": "The balanced accuracy (conventions: Balanced accuracy; ADR 0396).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "balanced_accuracy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/balanced_accuracy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
