"""Writes vectors/cases/binary_chi_square.json, stdlib only.

The chi-square statistic of two binary records (conventions: the chi-square statistic of
two binary records; ADR 0478): the 2x2 table counted directly, the value formed in
rationals.

Run from the repo root: python vectors/generators/binary_chi_square.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    na, nb, n = tp + fn, tp + fp, len(t)
    q = Fr(n * (tp * tn - fn * fp) ** 2, na * nb * (n - na) * (n - nb))
    cases.append(
        {
            "id": f"binary_chi_square.{cid}",
            "op": "binary_chi_square",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 2, TN 2, all margins 2: 4 16/16 = 4 = n",
)
assert got == 4
got = add("opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "FN 2, FP 2: 4 16/16 = 4 = n")
assert got == 4
got = add("independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: k 0, 0")
assert got == 0
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1, all margins 5: 10 15^2/625 = 18/5",
)
assert got == Fr(18, 5)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 2, FN 1, TN 3, |A| 3, |B| 2: 6 36/(6 12) = 3",
)
assert got == 3
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "TP 2, FN 1, FP 3, TN 1, |A| 3, |B| 5: 7 1/(15 8) = 7/120",
)
assert got == Fr(7, 120)
got = add(
    "lone", [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], "n 4, TP 1, TN 3, |A| = |B| = 1: 4 9/9 = 4"
)
assert got == 4
rng = random.Random(478)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(478), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"binary_chi_square.{cid}",
            "op": "binary_chi_square",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_decision_one", "decision all 0: |B| = 0", decision=[0.0, 0.0, 0.0])
err("all_one", "truth all 1: n - |A| = 0", truth=[1.0, 1.0, 1.0])

doc = {
    "schema": 1,
    "suite": "binary_chi_square",
    "description": "The chi-square statistic of two binary records (conventions: the"
    " chi-square statistic of two binary records; ADR 0478).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "binary_chi_square.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/binary_chi_square.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
