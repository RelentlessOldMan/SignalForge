"""Writes vectors/cases/average_precision.json, stdlib only.

The average precision (conventions: Average precision; ADR 0394): the step sum over the
distinct scores from the highest down, exact in rationals.

Run from the repo root: python vectors/generators/average_precision.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, truth, score, why):
    n1 = truth.count(1.0)
    ap = Fr(0)
    for tau in sorted(set(score), reverse=True):
        above = [t for t, s in zip(truth, score) if s >= tau]
        k = sum(1 for t, s in zip(truth, score) if s == tau and t == 1)
        ap += Fr(k * above.count(1.0), len(above))
    ap /= n1
    cases.append(
        {
            "id": f"average_precision.{cid}",
            "op": "average_precision",
            "args": {"truth": truth, "score": score},
            "expected": float(ap),
            "tol": TOL,
            "source": why,
        }
    )
    return ap


got = add("perfect", [0.0, 0.0, 1.0, 1.0], [0.1, 0.2, 0.7, 0.9], "positives on top: 1")
assert got == 1
got = add(
    "hand",
    [1.0, 0.0, 1.0, 0.0, 1.0],
    [0.9, 0.8, 0.7, 0.6, 0.5],
    "positives at ranks 1, 3, 5: (1 + 2/3 + 3/5)/3 = 34/45",
)
assert got == Fr(34, 45)
got = add(
    "tied_pair",
    [1.0, 0.0, 1.0],
    [0.5, 0.5, 0.2],
    "threshold 0.5: 1 of 2 positive, k = 1; 0.2: 2 of 3, k = 1: (1/2 + 2/3)/2 = 7/12",
)
assert got == Fr(7, 12)
got = add("all_positive", [1.0, 1.0], [0.3, 0.1], "no negatives: every precision 1")
assert got == 1
got = add("worst", [0.0, 0.0, 1.0], [0.9, 0.8, 0.1], "the one positive last: 1/3")
assert got == Fr(1, 3)
rng = random.Random(394)
truth = [1.0 if rng.random() < 0.2 else 0.0 for _ in range(200)]
score = [round(rng.gauss(t, 1.0), 1) for t in truth]
add(
    "noisy_scores",
    truth,
    score,
    "200 items from random.Random(394), 20% positive, score a "
    "unit Gaussian about the class rounded to 0.1, so with ties",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "score": [0.9, 0.2, 0.6]}
    base.update(args)
    cases.append(
        {
            "id": f"average_precision.{cid}",
            "op": "average_precision",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and score must be the same length", score=[0.5])
err("empty", "no positive", truth=[], score=[])
err("truth_not_binary", "truth must be 0 or 1", truth=[1.0, 2.0, 1.0])
err("no_positive", "the average is over the positives", truth=[0.0, 0.0, 0.0])
err("score_nan", "scores must be finite", score=[0.9, "nan", 0.6])

doc = {
    "schema": 1,
    "suite": "average_precision",
    "description": "The average precision (conventions: Average precision; ADR 0394).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "average_precision.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/average_precision.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
