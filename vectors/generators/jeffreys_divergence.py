"""Writes vectors/cases/jeffreys_divergence.json, stdlib only.

The Jeffreys divergence (conventions: Jeffreys divergence; ADR 0414): the distributions exact
in rationals, the logarithms in 40-digit decimal.

Run from the repo root: python vectors/generators/jeffreys_divergence.py [--check]
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
    j = D(0)
    for a, b in zip(p, q):
        if a == 0 and b == 0:
            continue
        pi, qi = Fr(a) / sp, Fr(b) / sq
        j += dec(pi - qi) * dec(pi / qi).ln()
    cases.append(
        {
            "id": f"jeffreys_divergence.{cid}",
            "op": "jeffreys_divergence",
            "args": {"p": p, "q": q},
            "expected": float(j),
            "tol": TOL,
            "source": why,
        }
    )
    return j


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add("same", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "the same distribution after scaling: 0")
assert close(got, D(0))
got = add(
    "coin",
    [3.0, 1.0],
    [1.0, 1.0],
    "P = (3/4, 1/4) against a fair coin: (1/4) ln(3/2) + (1/4) ln 2 = (1/4) ln 3",
)
assert close(got, D(3).ln() / 4)
got = add(
    "swap", [1.0, 2.0], [2.0, 1.0], "P = (1/3, 2/3), Q = (2/3, 1/3): (1/3) ln 2 twice = (2/3) ln 2"
)
assert close(got, D(2).ln() * 2 / 3)
got = add(
    "shared_zero",
    [3.0, 0.0, 1.0],
    [1.0, 0.0, 1.0],
    "the coin case with an index zero in both, dropped: (1/4) ln 3",
)
assert close(got, D(3).ln() / 4)
rng = random.Random(414)
p = [rng.randint(1, 50) * 1.0 for _ in range(16)]
q = [rng.randint(1, 50) * 1.0 for _ in range(16)]
add("counts", p, q, "16 counts each from random.Random(414), 1 to 50")
add(
    "huge_p",
    [1e308, 9e307, 1e300],
    [1.0, 2.0, 3.0],
    "p sums past the largest double: the result is that of p scaled down",
)
add(
    "huge_q",
    [1.0, 2.0, 3.0],
    [1.5e308, 1e308, 2e307],
    "q sums past the largest double: the result is that of q scaled down",
)


def err(cid, why, **args):
    base = {"p": [1.0, 2.0, 3.0], "q": [2.0, 1.0, 1.0]}
    base.update(args)
    cases.append(
        {
            "id": f"jeffreys_divergence.{cid}",
            "op": "jeffreys_divergence",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "p needs a value", p=[], q=[])
err("lengths", "p and q must match", q=[1.0, 1.0])
err("negative", "values must be non-negative", q=[1.0, -0.5, 3.0])
err("not_finite", "values must be finite", p=[1.0, "inf", 1.0])
err("zero_sum", "q must have a positive sum", q=[0.0, 0.0, 0.0])
err("p_zero", "p zero where q is not", p=[1.0, 0.0, 3.0])
err("q_zero", "q zero where p is not", q=[1.0, 0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "jeffreys_divergence",
    "description": "The Jeffreys divergence (conventions: Jeffreys divergence; ADR 0414).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "jeffreys_divergence.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/jeffreys_divergence.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
