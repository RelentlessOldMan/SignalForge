"""Writes vectors/cases/markedness.json, stdlib only.

Markedness (conventions: Markedness; ADR 0395): the table counted in integers, the precision
and the negative predictive value summed exactly in rationals.

Run from the repo root: python vectors/generators/markedness.py [--check]
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
    mk = Fr(tp, tp + fp) + Fr(tn, tn + fn) - 1
    cases.append(
        {
            "id": f"markedness.{cid}",
            "op": "markedness",
            "args": {"truth": truth, "decision": decision},
            "expected": float(mk),
            "tol": TOL,
            "source": why,
        }
    )
    return mk


got = add("perfect", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "PPV = NPV = 1: 1")
assert got == 1
got = add("inverted", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "PPV = NPV = 0: -1")
assert got == -1
got = add("chance", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "PPV = NPV = 1/2: 0")
assert got == 0
got = add(
    "hand",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    "TP 2, FP 1, TN 3, FN 1: PPV 2/3, NPV 3/4, 2/3 + 3/4 - 1 = 5/12",
)
assert got == Fr(5, 12)
rng = random.Random(395)
truth = [1.0 if rng.random() < 0.3 else 0.0 for _ in range(300)]
decision = [t if rng.random() < 0.8 else 1.0 - t for t in truth]
add(
    "noisy_detector",
    truth,
    decision,
    "300 items from random.Random(395), 30% positive, each decision flipped with probability 0.2",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 1.0, 0.0, 0.0], "decision": [1.0, 0.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"markedness.{cid}",
            "op": "markedness",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and decision must be the same length", decision=[1.0, 0.0])
err("empty", "N must be at least 1", truth=[], decision=[])
err("not_binary", "values must be 0 or 1", truth=[1.0, 1.0, 0.0, -1.0])
err("no_decided_positive", "the precision is undefined", decision=[0.0, 0.0, 0.0, 0.0])
err("no_decided_negative", "the NPV is undefined", decision=[1.0, 1.0, 1.0, 1.0])

doc = {
    "schema": 1,
    "suite": "markedness",
    "description": "Markedness (conventions: Markedness; ADR 0395).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "markedness.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/markedness.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
