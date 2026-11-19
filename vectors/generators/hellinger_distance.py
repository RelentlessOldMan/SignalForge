"""Writes vectors/cases/hellinger_distance.json, stdlib only.

The Hellinger distance (conventions: Hellinger distance; ADR 0409): the distributions exact in
rationals, the roots in 40-digit decimal.

Run from the repo root: python vectors/generators/hellinger_distance.py [--check]
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
    ss = sum((dec(Fr(a) / sp).sqrt() - dec(Fr(b) / sq).sqrt()) ** 2 for a, b in zip(p, q))
    h = (ss / 2).sqrt()
    cases.append(
        {
            "id": f"hellinger_distance.{cid}",
            "op": "hellinger_distance",
            "args": {"p": p, "q": q},
            "expected": float(h),
            "tol": TOL,
            "source": why,
        }
    )
    return h


got = add("same", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "the same distribution after scaling: 0")
assert got == 0
got = add("disjoint", [1.0, 0.0], [0.0, 3.0], "no common support: 1")
assert got == 1
got = add(
    "half",
    [1.0, 0.0],
    [1.0, 1.0],
    "P = (1, 0), Q = (1/2, 1/2): 1 - sum sqrt(PQ) = 1 - 1/sqrt 2, so H = sqrt(1 - 1/sqrt 2)",
)
assert abs(got - (1 - 1 / D(2).sqrt()).sqrt()) < D(10) ** -35
got = add(
    "quarter",
    [1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 1.0],
    "P a point, Q uniform on 4: sum sqrt(PQ) = 1/2, H = sqrt(1/2)",
)
assert abs(got - D("0.5").sqrt()) < D(10) ** -35
rng = random.Random(409)
p = [rng.randint(0, 6) * 1.0 for _ in range(16)]
q = [rng.randint(0, 6) * 1.0 for _ in range(16)]
assert 0.0 in p + q
add("counts", p, q, "16 counts each from random.Random(409), 0 to 6, with zeros")


def err(cid, why, **args):
    base = {"p": [1.0, 2.0, 3.0], "q": [2.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"hellinger_distance.{cid}",
            "op": "hellinger_distance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "p needs a value", p=[], q=[])
err("lengths", "p and q must match", q=[1.0, 1.0])
err("negative", "values must be non-negative", p=[1.0, -0.5, 3.0])
err("not_finite", "values must be finite", q=[1.0, "inf", 1.0])
err("zero_sum", "p must have a positive sum", p=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "hellinger_distance",
    "description": "The Hellinger distance (conventions: Hellinger distance; ADR 0409).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hellinger_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hellinger_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
