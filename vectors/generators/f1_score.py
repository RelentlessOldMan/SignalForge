"""Writes vectors/cases/f1_score.json, stdlib only.

The F1 score (conventions: F1 score; ADR 0386): the 2 x 2 table counted in integers.

Run from the repo root: python vectors/generators/f1_score.py [--check]
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
    tp = pairs.count((1.0, 1.0))
    fp, fn = pairs.count((0.0, 1.0)), pairs.count((1.0, 0.0))
    precision, recall = Fr(tp, tp + fp), Fr(tp, tp + fn)
    f1 = 2 * precision * recall / (precision + recall) if tp else Fr(0)
    assert f1 == Fr(2 * tp, 2 * tp + fp + fn)
    cases.append(
        {
            "id": f"f1_score.{cid}",
            "op": "f1_score",
            "args": {"truth": truth, "decision": decision},
            "expected": float(f1),
            "tol": TOL,
            "source": why,
        }
    )
    return f1


got = add("perfect", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "precision = recall = 1: F1 = 1")
assert got == 1
got = add(
    "half_and_two_thirds",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 1.0],
    "TP 2, FN 1, FP 2: precision 1/2, recall 2/3, harmonic mean 2(1/3)/(7/6) = 4/7",
)
assert got == Fr(4, 7)
got = add("no_hit", [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], "TP 0 with a miss and a false alarm: F1 = 0")
assert got == 0
rng = random.Random(386)
truth = [1.0 if rng.random() < 0.2 else 0.0 for _ in range(250)]
decision = [t if rng.random() < 0.85 else 1.0 - t for t in truth]
add(
    "noisy_detector",
    truth,
    decision,
    "250 items from random.Random(386), 20% positive, each decision flipped with probability 0.15",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0, 0.0], "decision": [1.0, 0.0, 0.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"f1_score.{cid}",
            "op": "f1_score",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and decision must be the same length", decision=[1.0, 0.0])
err("empty", "N must be at least 1", truth=[], decision=[])
err("not_binary", "values must be 0 or 1", truth=[1.0, 0.5, 1.0, 0.0])
err(
    "no_positive",
    "2TP + FP + FN = 0 when neither record has a 1",
    truth=[0.0, 0.0, 0.0, 0.0],
    decision=[0.0, 0.0, 0.0, 0.0],
)

doc = {
    "schema": 1,
    "suite": "f1_score",
    "description": "The F1 score (conventions: F1 score; ADR 0386).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "f1_score.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/f1_score.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
