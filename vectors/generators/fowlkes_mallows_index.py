"""Writes vectors/cases/fowlkes_mallows_index.json, stdlib only.

The Fowlkes-Mallows index (conventions: Fowlkes-Mallows index; ADR 0389): the table counted in
integers, one correctly rounded root of the exact product.

Run from the repo root: python vectors/generators/fowlkes_mallows_index.py [--check]
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
    tp = pairs.count((1.0, 1.0))
    fp, fn = pairs.count((0.0, 1.0)), pairs.count((1.0, 0.0))
    fm = tp / math.sqrt((tp + fp) * (tp + fn))
    cases.append(
        {
            "id": f"fowlkes_mallows_index.{cid}",
            "op": "fowlkes_mallows_index",
            "args": {"truth": truth, "decision": decision},
            "expected": fm,
            "tol": TOL,
            "source": why,
        }
    )
    return tp, (tp + fp) * (tp + fn)


got = add(
    "perfect", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "precision = recall = 1: 2/sqrt(2*2) = 1"
)
assert got == (2, 4)
got = add(
    "half_and_two_thirds",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 1.0, 1.0],
    "TP 2, decided 4, actual 3: precision 1/2, recall 2/3, sqrt(1/3) = 2/sqrt(12)",
)
assert got == (2, 12)
got = add(
    "quarter",
    [1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 1.0],
    "TP 1, decided 4, actual 1: 1/sqrt(4) = 1/2",
)
assert got == (1, 4)
got = add("no_hit", [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], "TP 0: FM = 0")
assert got == (0, 1)
rng = random.Random(389)
truth = [1.0 if rng.random() < 0.2 else 0.0 for _ in range(250)]
decision = [t if rng.random() < 0.85 else 1.0 - t for t in truth]
add(
    "noisy_detector",
    truth,
    decision,
    "250 items from random.Random(389), 20% positive, each decision flipped with probability 0.15",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0, 0.0], "decision": [1.0, 0.0, 0.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"fowlkes_mallows_index.{cid}",
            "op": "fowlkes_mallows_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and decision must be the same length", decision=[1.0, 0.0])
err("empty", "N must be at least 1", truth=[], decision=[])
err("not_binary", "values must be 0 or 1", truth=[1.0, 0.0, 1.0, 0.25])
err(
    "no_decided_positive",
    "precision is undefined with no 1 in decision",
    decision=[0.0, 0.0, 0.0, 0.0],
)
err("no_true_positive_class", "recall is undefined with no 1 in truth", truth=[0.0, 0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "fowlkes_mallows_index",
    "description": "The Fowlkes-Mallows index (conventions: Fowlkes-Mallows index; ADR 0389).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fowlkes_mallows_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/fowlkes_mallows_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
