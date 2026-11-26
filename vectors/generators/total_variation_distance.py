"""Writes vectors/cases/total_variation_distance.json, stdlib only.

The total variation distance (conventions: total variation distance; ADR 0411): exact in
rationals.

Run from the repo root: python vectors/generators/total_variation_distance.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, p, q, why):
    sp, sq = sum(Fr(v) for v in p), sum(Fr(v) for v in q)
    tv = sum(abs(Fr(a) / sp - Fr(b) / sq) for a, b in zip(p, q)) / 2
    cases.append(
        {
            "id": f"total_variation_distance.{cid}",
            "op": "total_variation_distance",
            "args": {"p": p, "q": q},
            "expected": float(tv),
            "tol": TOL,
            "source": why,
        }
    )
    return tv


got = add("same", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "the same distribution after scaling: 0")
assert got == 0
got = add("disjoint", [1.0, 0.0], [0.0, 3.0], "no common support: 1")
assert got == 1
got = add("half", [1.0, 0.0], [1.0, 1.0], "P = (1, 0), Q = (1/2, 1/2): (1/2 + 1/2)/2 = 1/2")
assert got == Fr(1, 2)
got = add(
    "event",
    [3.0, 1.0, 1.0, 5.0],
    [1.0, 1.0, 3.0, 5.0],
    "P = (3, 1, 1, 5)/10, Q = (1, 1, 3, 5)/10: the event {0} differs most, by 2/10",
)
assert got == Fr(1, 5)
rng = random.Random(411)
p = [rng.randint(0, 6) * 1.0 for _ in range(16)]
q = [rng.randint(0, 6) * 1.0 for _ in range(16)]
assert 0.0 in p + q
add("counts", p, q, "16 counts each from random.Random(411), 0 to 6, with zeros")
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
            "id": f"total_variation_distance.{cid}",
            "op": "total_variation_distance",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "p needs a value", p=[], q=[])
err("lengths", "p and q must match", q=[1.0, 1.0])
err("negative", "values must be non-negative", p=[1.0, -0.5, 3.0])
err("not_finite", "values must be finite", q=[1.0, "-inf", 1.0])
err("zero_sum", "q must have a positive sum", q=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "total_variation_distance",
    "description": "The total variation distance (conventions: total variation distance; "
    "ADR 0411).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "total_variation_distance.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/total_variation_distance.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
