"""Writes vectors/cases/chi_square_divergence.json, stdlib only.

The Pearson chi-square divergence (conventions: Pearson chi-square divergence; ADR 0412):
exact in rationals.

Run from the repo root: python vectors/generators/chi_square_divergence.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-13}
cases = []


def add(cid, p, q, why):
    sp, sq = sum(Fr(v) for v in p), sum(Fr(v) for v in q)
    c2 = sum((Fr(a) / sp - Fr(b) / sq) ** 2 / (Fr(b) / sq) for a, b in zip(p, q) if b != 0)
    cases.append(
        {
            "id": f"chi_square_divergence.{cid}",
            "op": "chi_square_divergence",
            "args": {"p": p, "q": q},
            "expected": float(c2),
            "tol": TOL,
            "source": why,
        }
    )
    return c2


got = add("same", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "the same distribution after scaling: 0")
assert got == 0
got = add("half", [1.0, 0.0], [1.0, 1.0], "P = (1, 0), Q = (1/2, 1/2): (1/4)/(1/2) twice = 1")
assert got == 1
got = add(
    "coin", [3.0, 1.0], [1.0, 1.0], "P = (3/4, 1/4) from a fair coin: (1/16)/(1/2) twice = 1/4"
)
assert got == Fr(1, 4)
got = add(
    "reverse",
    [1.0, 1.0],
    [3.0, 1.0],
    "P fair, Q = (3/4, 1/4): (1/16)/(3/4) + (1/16)/(1/4) = 1/12 + 1/4 = 1/3",
)
assert got == Fr(1, 3)
got = add(
    "shared_zero",
    [2.0, 0.0, 2.0],
    [1.0, 0.0, 3.0],
    "the middle index zero in both and dropped: (1/16)/(1/4) + (1/16)/(3/4) = 1/4 + 1/12 = 1/3",
)
assert got == Fr(1, 3)
rng = random.Random(412)
p = [rng.randint(1, 50) * 1.0 for _ in range(16)]
q = [rng.randint(1, 50) * 1.0 for _ in range(16)]
add("counts", p, q, "16 counts each from random.Random(412), 1 to 50")
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
            "id": f"chi_square_divergence.{cid}",
            "op": "chi_square_divergence",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "p needs a value", p=[], q=[])
err("lengths", "p and q must match", q=[1.0, 1.0])
err("negative", "values must be non-negative", q=[1.0, -0.5, 3.0])
err("not_finite", "values must be finite", p=[1.0, "inf", 1.0])
err("zero_sum", "p must have a positive sum", p=[0.0, 0.0, 0.0])
err("infinite", "q is zero where p is not", q=[1.0, 0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "chi_square_divergence",
    "description": "The Pearson chi-square divergence (conventions: Pearson chi-square "
    "divergence; ADR 0412).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "chi_square_divergence.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/chi_square_divergence.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
