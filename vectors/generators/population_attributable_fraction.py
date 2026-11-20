"""Writes vectors/cases/population_attributable_fraction.json, stdlib only.

The population attributable fraction (conventions: the population attributable fraction;
ADR 0486): the 2x2 table counted directly, the value formed in rationals.

Run from the repo root: python vectors/generators/population_attributable_fraction.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    q = 1 - Fr(len(t) * fn, (tp + fn) * (fn + tn))
    cases.append(
        {
            "id": f"population_attributable_fraction.{cid}",
            "op": "population_attributable_fraction",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, |A| 2, FN 1, FN + TN 2: 1 - 4/4 = 0",
)
assert got == 0
got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "FN 0: 1, the greatest value")
assert got == 1
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, |A| 5, FN 1, FN + TN 5: 1 - 10/25 = 3/5",
)
assert got == Fr(3, 5)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "n 7, |A| 3, FN 1, FN + TN 2: 1 - 7/6 = -1/6",
)
assert got == Fr(-1, 6)
got = add(
    "skew",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "n 7, |A| 4, FN 1, FN + TN 3: 1 - 7/12 = 5/12",
)
assert got == Fr(5, 12)
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, |A| 2, FN 2, FN + TN 2: 1 - 8/4 = -1, no error for TP = 0",
)
assert got == -1
got = add(
    "truth_all_one", [1.0, 1.0, 1.0], [1.0, 0.0, 1.0], "n 3, |A| 3, FN 1, FN + TN 1: 1 - 3/3 = 0"
)
assert got == 0
rng = random.Random(486)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(486), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"population_attributable_fraction.{cid}",
            "op": "population_attributable_fraction",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_truth_one", "truth has no 1: |A| = 0", truth=[0.0, 0.0, 0.0], decision=[1.0, 0.0, 1.0])
err(
    "decision_all_one",
    "the decision has no 0: FN + TN = 0",
    truth=[1.0, 0.0, 1.0],
    decision=[1.0, 1.0, 1.0],
)


doc = {
    "schema": 1,
    "suite": "population_attributable_fraction",
    "description": "The population attributable fraction (conventions: the population"
    " attributable fraction; ADR 0486).",
    "cases": cases,
}
out = (
    pathlib.Path(__file__).resolve().parents[1] / "cases" / "population_attributable_fraction.json"
)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/population_attributable_fraction.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
