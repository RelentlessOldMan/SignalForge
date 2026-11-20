"""Writes vectors/cases/gower_legendre_coefficient.json, stdlib only.

The Gower-Legendre coefficient (conventions: the Gower-Legendre coefficient; ADR 0455): the
2x2 table counted directly, the value formed in rationals as (TP + TN) / (TP + TN + (FN + FP)/2).

Run from the repo root: python vectors/generators/gower_legendre_coefficient.py [--check]
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
    q = (tp + tn) / (tp + tn + Fr(fn + fp, 2))
    cases.append(
        {
            "id": f"gower_legendre_coefficient.{cid}",
            "op": "gower_legendre_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "TP 2, TN 2: 4/(4 + 0) = 1")
assert got == 1
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "FN 2, FP 2: 0/(0 + 2) = 0, the least value",
)
assert got == 0
got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: 2/(2 + 1) = 2/3"
)
assert got == Fr(2, 3)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 1, FN 1, FP 1, TN 2: 3/(3 + 1) = 3/4",
)
assert got == Fr(3, 4)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: 8/(8 + 1) = 8/9",
)
assert got == Fr(8, 9)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 1, FN 2, FP 0, TN 2: 3/(3 + 1) = 3/4",
)
assert got == Fr(3, 4)
got = add(
    "far_below", [1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 1.0, 1.0], "TP 0, FN 1, FP 3, TN 0: 0/(0 + 2) = 0"
)
assert got == 0
got = add(
    "constant",
    [1.0, 1.0, 1.0],
    [1.0, 0.0, 1.0],
    "truth all 1, TP 2, FN 1: 2/(2 + 1/2) = 4/5, no error",
)
assert got == Fr(4, 5)
got = add("all_zero", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "both all 0, TN 3: 3/(3 + 0) = 1, no error")
assert got == 1
rng = random.Random(455)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(455), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"gower_legendre_coefficient.{cid}",
            "op": "gower_legendre_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])

doc = {
    "schema": 1,
    "suite": "gower_legendre_coefficient",
    "description": "The Gower-Legendre coefficient (conventions: the Gower-Legendre"
    " coefficient; ADR 0455).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gower_legendre_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/gower_legendre_coefficient.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
