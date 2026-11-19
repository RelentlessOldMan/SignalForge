"""Writes vectors/cases/roc_auc.json, stdlib only.

The ROC AUC (conventions: ROC AUC; ADR 0393): every positive-negative pair counted, a win 2
and a tie 1, over twice the number of pairs, exact in rationals.

Run from the repo root: python vectors/generators/roc_auc.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, truth, score, why):
    pos = [s for t, s in zip(truth, score) if t == 1]
    neg = [s for t, s in zip(truth, score) if t == 0]
    half = sum(2 if p > q else 1 if p == q else 0 for p in pos for q in neg)
    auc = Fr(half, 2 * len(pos) * len(neg))
    cases.append(
        {
            "id": f"roc_auc.{cid}",
            "op": "roc_auc",
            "args": {"truth": truth, "score": score},
            "expected": float(auc),
            "tol": TOL,
            "source": why,
        }
    )
    return auc


got = add(
    "perfect", [0.0, 0.0, 1.0, 1.0], [0.1, 0.2, 0.7, 0.9], "every positive above every negative: 1"
)
assert got == 1
got = add("reversed", [1.0, 1.0, 0.0, 0.0], [0.1, 0.2, 0.7, 0.9], "every positive below: 0")
assert got == 0
got = add(
    "hand",
    [0.0, 0.0, 1.0, 1.0],
    [0.1, 0.4, 0.35, 0.8],
    "pairs (0.35 v 0.1 win, 0.35 v 0.4 loss, 0.8 wins both): 3 of 4 = 3/4",
)
assert got == Fr(3, 4)
got = add("all_tied", [1.0, 0.0, 1.0, 0.0, 0.0], [2.0, 2.0, 2.0, 2.0, 2.0], "every pair tied: 1/2")
assert got == Fr(1, 2)
got = add(
    "some_ties",
    [1.0, 0.0, 1.0, 0.0, 1.0],
    [3.0, 3.0, 1.0, 0.0, 5.0],
    "positives 3, 1, 5 against negatives 3, 0: 1/2 + 1 + 0 + 1 + 1 + 1 = 4.5 of 6 = 3/4",
)
assert got == Fr(3, 4)
rng = random.Random(393)
truth = [1.0 if rng.random() < 0.35 else 0.0 for _ in range(200)]
score = [round(rng.gauss(t, 1.0), 1) for t in truth]
add(
    "noisy_scores",
    truth,
    score,
    "200 items from random.Random(393), 35% positive, score a "
    "unit Gaussian about the class rounded to 0.1, so with ties",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "score": [0.9, 0.2, 0.6]}
    base.update(args)
    cases.append(
        {
            "id": f"roc_auc.{cid}",
            "op": "roc_auc",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and score must be the same length", score=[0.5])
err("empty", "no positive and no negative", truth=[], score=[])
err("truth_not_binary", "truth must be 0 or 1", truth=[1.0, 0.5, 1.0])
err("no_negative", "the AUC needs a negative", truth=[1.0, 1.0, 1.0])
err("no_positive", "the AUC needs a positive", truth=[0.0, 0.0, 0.0])
err("score_infinite", "scores must be finite", score=[0.9, "inf", 0.6])

doc = {
    "schema": 1,
    "suite": "roc_auc",
    "description": "The ROC AUC (conventions: ROC AUC; ADR 0393).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "roc_auc.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/roc_auc.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
