"""Writes vectors/cases/youden_j.json, stdlib only.

Youden's J (conventions: Youden's J; ADR 0387): the 2 x 2 table counted in integers.

Run from the repo root: python vectors/generators/youden_j.py [--check]
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
    j = Fr(tp, tp + fn) + Fr(tn, tn + fp) - 1
    assert j == Fr(tp * tn - fp * fn, (tp + fn) * (tn + fp))
    cases.append(
        {
            "id": f"youden_j.{cid}",
            "op": "youden_j",
            "args": {"truth": truth, "decision": decision},
            "expected": float(j),
            "tol": TOL,
            "source": why,
        }
    )
    return j


got = add(
    "perfect", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "sensitivity = specificity = 1: J = 1"
)
assert got == 1
got = add(
    "inverted", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "sensitivity = specificity = 0: J = -1"
)
assert got == -1
got = add(
    "always_positive",
    [1.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 1.0, 1.0, 1.0, 1.0],
    "deciding positive always: sensitivity 1, specificity 0, J = 0",
)
assert got == 0
got = add(
    "mixed",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    "sensitivity 2/3, specificity 3/4: J = 2/3 + 3/4 - 1 = 5/12",
)
assert got == Fr(5, 12)
rng = random.Random(387)
truth = [1.0 if rng.random() < 0.15 else 0.0 for _ in range(300)]
decision = [t if rng.random() < 0.8 else 1.0 - t for t in truth]
add(
    "noisy_detector",
    truth,
    decision,
    "300 items from random.Random(387), 15% positive, each decision flipped with probability 0.2",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0, 0.0], "decision": [1.0, 0.0, 0.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"youden_j.{cid}",
            "op": "youden_j",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and decision must be the same length", decision=[1.0, 0.0])
err("empty", "N must be at least 1", truth=[], decision=[])
err("not_binary", "values must be 0 or 1", decision=[1.0, -1.0, 1.0, 0.0])
err("no_true_positive_class", "TP + FN = 0 when the truth has no 1", truth=[0.0, 0.0, 0.0, 0.0])
err("no_true_negative_class", "TN + FP = 0 when the truth has no 0", truth=[1.0, 1.0, 1.0, 1.0])

doc = {
    "schema": 1,
    "suite": "youden_j",
    "description": "Youden's J (conventions: Youden's J; ADR 0387).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "youden_j.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/youden_j.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
