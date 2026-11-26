"""Writes vectors/cases/js_divergence.json, stdlib only.

The Jensen-Shannon divergence (conventions: Jensen-Shannon divergence; ADR 0408): the
distributions exact in rationals, the logarithms in 40-digit decimal.

Run from the repo root: python vectors/generators/js_divergence.py [--check]
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
    d = D(0)
    for a, b in zip(p, q):
        pi, qi = Fr(a) / sp, Fr(b) / sq
        mi = (pi + qi) / 2
        for w in (pi, qi):
            if w > 0:
                d += dec(w) * dec(w / mi).ln()
    d /= 2
    cases.append(
        {
            "id": f"js_divergence.{cid}",
            "op": "js_divergence",
            "args": {"p": p, "q": q},
            "expected": float(d),
            "tol": TOL,
            "source": why,
        }
    )
    return d


got = add("same", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "the same distribution after scaling: 0")
assert got == 0
got = add("disjoint", [1.0, 0.0], [0.0, 3.0], "no common support: the bound ln 2")
assert abs(got - D(2).ln()) < D(10) ** -35
got = add(
    "half",
    [1.0, 0.0],
    [1.0, 1.0],
    "P = (1, 0), Q = (1/2, 1/2), M = (3/4, 1/4): "
    "(1/2)[ln 4/3 + (1/2) ln 2/3 + (1/2) ln 2] = (3/2) ln 2 - (3/4) ln 3",
)
assert abs(got - (D(3) / 2 * D(2).ln() - D(3) / 4 * D(3).ln())) < D(10) ** -35
rng = random.Random(408)
p = [rng.randint(0, 6) * 1.0 for _ in range(16)]
q = [rng.randint(0, 6) * 1.0 for _ in range(16)]
assert 0.0 in p + q
add("counts", p, q, "16 counts each from random.Random(408), 0 to 6, with zeros")
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
    base = {"p": [1.0, 2.0, 3.0], "q": [2.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"js_divergence.{cid}",
            "op": "js_divergence",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "p needs a value", p=[], q=[])
err("lengths", "p and q must match", q=[1.0, 1.0])
err("negative", "values must be non-negative", q=[1.0, -0.5, 3.0])
err("not_finite", "values must be finite", p=[1.0, "nan", 1.0])
err("zero_sum", "q must have a positive sum", q=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "js_divergence",
    "description": "The Jensen-Shannon divergence (conventions: Jensen-Shannon divergence; "
    "ADR 0408).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "js_divergence.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/js_divergence.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
