"""Writes vectors/cases/cross_entropy.json, stdlib only.

The cross-entropy (conventions: cross-entropy; ADR 0415): the distributions exact in
rationals, the logarithms in 40-digit decimal.

Run from the repo root: python vectors/generators/cross_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-13}
decimal.getcontext().prec = 40
D = decimal.Decimal
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def add(cid, p, q, why):
    sp, sq = sum(Fr(v) for v in p), sum(Fr(v) for v in q)
    h = D(0)
    for a, b in zip(p, q):
        if a != 0:
            h -= dec(Fr(a) / sp) * dec(Fr(b) / sq).ln()
    cases.append(
        {
            "id": f"cross_entropy.{cid}",
            "op": "cross_entropy",
            "args": {"p": p, "q": q},
            "expected": float(h),
            "tol": TOL,
            "source": why,
        }
    )
    return h


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add("point", [1.0, 0.0], [2.0, 0.0], "a point mass coded for itself: 0")
assert close(got, D(0))
got = add("fair", [1.0, 1.0], [1.0, 1.0], "a fair coin coded for itself: its entropy, ln 2")
assert close(got, D(2).ln())
got = add(
    "biased_under_fair", [3.0, 1.0], [1.0, 1.0], "any P coded for a fair coin: ln 2 whatever P is"
)
assert close(got, D(2).ln())
got = add(
    "fair_under_biased",
    [1.0, 1.0],
    [3.0, 1.0],
    "a fair coin coded for (3/4, 1/4): (1/2) ln(4/3) + (1/2) ln 4 = (1/2) ln(16/3)",
)
assert close(got, (D(16) / 3).ln() / 2)
got = add(
    "p_zero",
    [0.0, 1.0, 1.0],
    [2.0, 1.0, 1.0],
    "p zero at index 0, dropped: Q = (1/2, 1/4, 1/4), so ln 4",
)
assert close(got, D(4).ln())
rng = random.Random(415)
p = [rng.randint(0, 6) * 1.0 for _ in range(16)]
q = [rng.randint(1, 6) * 1.0 for _ in range(16)]
assert 0.0 in p
add("counts", p, q, "16 counts each from random.Random(415), with zeros in p")


def err(cid, why, **args):
    base = {"p": [1.0, 2.0, 3.0], "q": [2.0, 1.0, 1.0]}
    base.update(args)
    cases.append(
        {
            "id": f"cross_entropy.{cid}",
            "op": "cross_entropy",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "p needs a value", p=[], q=[])
err("lengths", "p and q must match", q=[1.0, 1.0])
err("negative", "values must be non-negative", p=[1.0, -0.5, 3.0])
err("not_finite", "values must be finite", q=[1.0, "nan", 1.0])
err("zero_sum", "p must have a positive sum", p=[0.0, 0.0, 0.0])
err("infinite", "q is zero where p is not", q=[1.0, 0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "cross_entropy",
    "description": "The cross-entropy (conventions: cross-entropy; ADR 0415).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cross_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cross_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
