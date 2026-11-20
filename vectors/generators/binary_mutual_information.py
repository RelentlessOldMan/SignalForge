"""Writes vectors/cases/binary_mutual_information.json, stdlib only.

Binary mutual information (conventions: binary mutual information; ADR 0464): the 2x2
table counted directly, the four terms (c/n) ln(n c / (r k)) summed in 40-digit decimals,
each logarithm correctly rounded there.

Run from the repo root: python vectors/generators/binary_mutual_information.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 40
TOL = {"abs": 1e-15, "rel": 1e-13}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    n = len(t)
    tn = n - tp - fn - fp
    na, nb = tp + fn, tp + fp
    q = D(0)
    for c, ra, kb in ((tp, na, nb), (fn, na, n - nb), (fp, n - na, nb), (tn, n - na, n - nb)):
        if c > 0:
            q += D(c) / D(n) * (D(n * c) / D(ra * kb)).ln()
    cases.append(
        {
            "id": f"binary_mutual_information.{cid}",
            "op": "binary_mutual_information",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


LN2, LN3, LN5 = D(2).ln(), D(3).ln(), D(5).ln()
got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 2, TN 2, all margins 2: 2 (1/2) ln 2 = ln 2, the entropy of either",
)
assert close(got, LN2)
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell, all margins 2: every log ln 1, 0",
)
assert got == 0
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, FN 2, FP 2, all margins 2: ln 2, as for identical records",
)
assert close(got, LN2)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, TP = TN = 4, FN = FP = 1, margins 5: 0.8 ln(8/5) + 0.2 ln(2/5) = 2.6 ln 2 - ln 5",
)
assert close(got, D("2.6") * LN2 - LN5)
got = add(
    "subset",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0],
    "n 4, TP 1, FN 1, TN 2, |A| 2, |B| 1: (1/4) ln 2 + (1/4) ln(2/3) + (1/2) ln(4/3)"
    " = 1.5 ln 2 - 0.75 ln 3",
)
assert close(got, D("1.5") * LN2 - D("0.75") * LN3)
got = add("constant", [1.0, 1.0, 1.0], [1.0, 0.0, 1.0], "truth all 1: every log ln 1, 0, no error")
assert got == 0
got = add("all_zero", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "both all 0: TN 3, ln(9/9) = 0, no error")
assert got == 0
rng = random.Random(464)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(464), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"binary_mutual_information.{cid}",
            "op": "binary_mutual_information",
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
    "suite": "binary_mutual_information",
    "description": "Binary mutual information (conventions: binary mutual information; ADR 0464).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "binary_mutual_information.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/binary_mutual_information.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
