"""Writes vectors/cases/tversky_index.json, stdlib only.

The Tversky index (conventions: Tversky index; ADR 0423): the sets counted directly, the
index formed in rationals.

Run from the repo root: python vectors/generators/tversky_index.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, t, d, alpha, beta, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    v = Fr(tp) / (tp + Fr(alpha) * fn + Fr(beta) * fp)
    cases.append(
        {
            "id": f"tversky_index.{cid}",
            "op": "tversky_index",
            "args": {"truth": t, "decision": d, "alpha": alpha, "beta": beta},
            "expected": float(v),
            "tol": TOL,
            "source": why,
        }
    )
    return v


T = [1.0, 1.0, 1.0, 0.0, 0.0, 1.0]
D = [1.0, 1.0, 0.0, 1.0, 1.0, 0.0]
# TP = 2, FN = 2, FP = 2.
got = add("jaccard", T, D, 1.0, 1.0, "alpha = beta = 1 is Jaccard: 2/(2 + 2 + 2) = 1/3")
assert got == Fr(1, 3)
got = add("dice", T, D, 0.5, 0.5, "alpha = beta = 1/2 is Dice: 2/(2 + 1 + 1) = 1/2")
assert got == Fr(1, 2)
got = add("misses_only", T, D, 1.0, 0.0, "FP ignored: 2/(2 + 2) = 1/2, the recall")
assert got == Fr(1, 2)
got = add(
    "uneven",
    [1.0, 1.0, 1.0, 1.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    0.25,
    2.0,
    "TP 1, FN 3, FP 1: 1/(1 + 3/4 + 2) = 4/15",
)
assert got == Fr(4, 15)
got = add("no_hit", [1.0, 0.0], [0.0, 1.0], 1.0, 1.0, "no shared item: 0")
assert got == 0
got = add(
    "zero_weights", [1.0, 0.0, 1.0], [1.0, 1.0, 0.0], 0.0, 0.0, "both weights 0 and TP 1: 1/1 = 1"
)
assert got == 1
rng = random.Random(423)
t = [float(rng.random() < 0.4) for _ in range(40)]
d = [float(rng.random() < 0.5) for _ in range(40)]
add("random", t, d, 0.3, 0.7, "40 items each from random.Random(423), alpha 0.3, beta 0.7")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0], "alpha": 1.0, "beta": 1.0}
    base.update(args)
    cases.append(
        {
            "id": f"tversky_index.{cid}",
            "op": "tversky_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("negative_alpha", "alpha must be at least 0", alpha=-0.5)
err("negative_beta", "beta must be at least 0", beta=-1.0)
err("infinite_alpha", "alpha must be finite", alpha="inf")
err("nan_beta", "beta must be finite", beta="nan")
err(
    "no_ones",
    "no 1 in either record: the denominator is 0",
    truth=[0.0, 0.0, 0.0],
    decision=[0.0, 0.0, 0.0],
)
err(
    "zero_denominator",
    "TP 0 and both weights 0: the denominator is 0",
    truth=[1.0, 0.0],
    decision=[0.0, 1.0],
    alpha=0.0,
    beta=0.0,
)

doc = {
    "schema": 1,
    "suite": "tversky_index",
    "description": "The Tversky index (conventions: Tversky index; ADR 0423).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tversky_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tversky_index.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
