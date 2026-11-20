"""Writes vectors/cases/negative_likelihood_ratio.json, stdlib only.

The negative likelihood ratio (conventions: the negative likelihood ratio; ADR 0483): the
2x2 table counted directly, the value formed in rationals.

Run from the repo root: python vectors/generators/negative_likelihood_ratio.py [--check]
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
    q = Fr(fn * (fp + tn), (tp + fn) * tn)
    cases.append(
        {
            "id": f"negative_likelihood_ratio.{cid}",
            "op": "negative_likelihood_ratio",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: 1 2/(2 1) = 1"
)
assert got == 1
got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "FN 0, TN 2: 0, the least value")
assert got == 0
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: 1 5/(5 4) = 1/4",
)
assert got == Fr(1, 4)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1: 1 4/(3 1) = 4/3",
)
assert got == Fr(4, 3)
got = add(
    "skew",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "TP 3, FN 1, FP 1, TN 2: 1 3/(4 2) = 3/8",
)
assert got == Fr(3, 8)
got = add(
    "none_flagged", [1.0, 0.0, 0.0], [0.0, 0.0, 0.0], "FN 1, FP 0, TN 2, |A| 1: 1 2/(1 2) = 1"
)
assert got == 1
rng = random.Random(483)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(483), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"negative_likelihood_ratio.{cid}",
            "op": "negative_likelihood_ratio",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_truth_one", "truth has no 1: |A| = 0", truth=[0.0, 0.0, 0.0], decision=[1.0, 0.0, 1.0])
err("no_tn", "opposite records: TN = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[0.0, 1.0, 0.0, 1.0])
err("truth_all_one", "truth has no 0: TN = 0", truth=[1.0, 1.0, 1.0], decision=[1.0, 0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "negative_likelihood_ratio",
    "description": "The negative likelihood ratio (conventions: the negative likelihood"
    " ratio; ADR 0483).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "negative_likelihood_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/negative_likelihood_ratio.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
