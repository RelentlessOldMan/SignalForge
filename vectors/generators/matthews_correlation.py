"""Writes vectors/cases/matthews_correlation.json, stdlib only.

The Matthews correlation coefficient (conventions: Matthews correlation; ADR 0385): the 2 x 2
table counted in integers, one correctly rounded root of the exact product.

Run from the repo root: python vectors/generators/matthews_correlation.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, truth, decision, why):
    pairs = list(zip(truth, decision))
    tp, tn = pairs.count((1.0, 1.0)), pairs.count((0.0, 0.0))
    fp, fn = pairs.count((0.0, 1.0)), pairs.count((1.0, 0.0))
    num = tp * tn - fp * fn
    product = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
    mcc = num / math.sqrt(product)
    cases.append(
        {
            "id": f"matthews_correlation.{cid}",
            "op": "matthews_correlation",
            "args": {"truth": truth, "decision": decision},
            "expected": mcc,
            "tol": TOL,
            "source": why,
        }
    )
    return num, product


got = add("perfect", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "TP = TN = 2: 4/sqrt(2*2*2*2) = 1")
assert got == (4, 16)
got = add("inverted", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "FP = FN = 2: -4/sqrt(16) = -1")
assert got == (-4, 16)
got = add(
    "one_miss",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0],
    "TP 1, FN 1, TN 2, FP 0: 2/sqrt(1*2*2*3) = 1/sqrt(3)",
)
assert got == (2, 12)
got = add(
    "chance", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: (1 - 1)/sqrt(16) = 0"
)
assert got == (0, 16)
rng = random.Random(385)
truth = [1.0 if rng.random() < 0.1 else 0.0 for _ in range(300)]
decision = [t if rng.random() < 0.9 else 1.0 - t for t in truth]
add(
    "rare_class",
    truth,
    decision,
    "300 items from random.Random(385), 10% positive, each decision flipped with probability 0.1",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0, 0.0], "decision": [1.0, 0.0, 0.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"matthews_correlation.{cid}",
            "op": "matthews_correlation",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and decision must be the same length", decision=[1.0, 0.0])
err("empty", "N must be at least 1", truth=[], decision=[])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.0, 2.0, 0.0])
err(
    "no_positive_decision",
    "TP + FP = 0 when no item is decided positive",
    decision=[0.0, 0.0, 0.0, 0.0],
)
err("no_negative_truth", "TN + FP = 0 when every true class is 1", truth=[1.0, 1.0, 1.0, 1.0])
err("nan", "nan is not 0 or 1", truth=[1.0, "nan", 1.0, 0.0])

doc = {
    "schema": 1,
    "suite": "matthews_correlation",
    "description": "The Matthews correlation coefficient (conventions: Matthews correlation; "
    "ADR 0385).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "matthews_correlation.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/matthews_correlation.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
