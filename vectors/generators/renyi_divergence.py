"""Writes vectors/cases/renyi_divergence.json, stdlib only.

The Rényi divergence (conventions: Rényi divergence; ADR 0413): the distributions exact in
rationals, the powers and the logarithm in 40-digit decimal.

Run from the repo root: python vectors/generators/renyi_divergence.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import decimal
import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-12}
decimal.getcontext().prec = 40
D = decimal.Decimal
cases = []


def dec(f):
    return D(f.numerator) / D(f.denominator)


def pw(f, e):
    return (D(e) * dec(f).ln()).exp()


def add(cid, p, q, alpha, why):
    sp, sq = sum(Fr(v) for v in p), sum(Fr(v) for v in q)
    s = sum(
        pw(Fr(a) / sp, alpha) * pw(Fr(b) / sq, 1 - alpha) for a, b in zip(p, q) if a != 0 and b != 0
    )
    r = s.ln() / (D(alpha) - 1)
    r = max(r, D(0))
    cases.append(
        {
            "id": f"renyi_divergence.{cid}",
            "op": "renyi_divergence",
            "args": {"p": p, "q": q, "alpha": alpha},
            "expected": float(r),
            "tol": TOL,
            "source": why,
        }
    )
    return r


def close(a, b):
    return abs(a - b) < D(10) ** -30


got = add("same", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], 2.0, "the same distribution after scaling: 0")
assert close(got, D(0))
got = add(
    "order_2",
    [3.0, 1.0],
    [1.0, 1.0],
    2.0,
    "P = (3/4, 1/4) from a fair coin, order 2: ln(1 + chi-square) = ln(5/4)",
)
assert close(got, D("1.25").ln())
got = add(
    "order_3",
    [3.0, 1.0],
    [1.0, 1.0],
    3.0,
    "order 3: sum P^3/Q^2 = (27/64 + 1/64)·4 = 7/4, so ln(7/4)/2",
)
assert close(got, D("1.75").ln() / 2)
got = add(
    "order_half",
    [1.0, 0.0],
    [1.0, 1.0],
    0.5,
    "P = (1, 0), Q = (1/2, 1/2), order 1/2: -2 ln(1/sqrt 2) = ln 2",
)
assert close(got, D(2).ln())
got = add(
    "q_zero_low",
    [1.0, 1.0],
    [1.0, 0.0],
    0.5,
    "order 1/2 with q zero under p: sum sqrt(1/2 · 1) = 1/sqrt 2, so ln 2",
)
assert close(got, D(2).ln())
rng = random.Random(413)
p = [rng.randint(0, 6) * 1.0 for _ in range(16)]
q = [rng.randint(1, 6) * 1.0 for _ in range(16)]
assert 0.0 in p
add("counts", p, q, 1.5, "16 counts each from random.Random(413), order 1.5")
add("counts_low", p, q, 0.25, "the same counts, order 0.25")


def err(cid, why, **args):
    base = {"p": [1.0, 2.0, 3.0], "q": [2.0, 1.0, 1.0], "alpha": 2.0}
    base.update(args)
    cases.append(
        {
            "id": f"renyi_divergence.{cid}",
            "op": "renyi_divergence",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("alpha_one", "alpha must not be 1", alpha=1.0)
err("alpha_zero", "alpha must be above 0", alpha=0.0)
err("alpha_nan", "alpha must be finite", alpha="nan")
err("empty", "p needs a value", p=[], q=[])
err("lengths", "p and q must match", q=[1.0, 1.0])
err("negative", "values must be non-negative", q=[1.0, -0.5, 3.0])
err("zero_sum", "p must have a positive sum", p=[0.0, 0.0, 0.0])
err("infinite", "order 2 with q zero where p is not", q=[1.0, 0.0, 1.0])
err("disjoint", "order 1/2 with no shared support", p=[1.0, 0.0, 0.0], q=[0.0, 1.0, 1.0], alpha=0.5)

doc = {
    "schema": 1,
    "suite": "renyi_divergence",
    "description": "The Rényi divergence (conventions: Rényi divergence; ADR 0413).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "renyi_divergence.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/renyi_divergence.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
