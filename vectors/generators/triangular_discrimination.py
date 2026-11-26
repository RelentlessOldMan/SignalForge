"""Writes vectors/cases/triangular_discrimination.json, stdlib only.

The triangular discrimination (conventions: triangular discrimination; ADR 0416): exact in
rationals.

Run from the repo root: python vectors/generators/triangular_discrimination.py [--check]
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
    t = Fr(0)
    for a, b in zip(p, q):
        if a == 0 and b == 0:
            continue
        pi, qi = Fr(a) / sp, Fr(b) / sq
        t += (pi - qi) ** 2 / (pi + qi)
    cases.append(
        {
            "id": f"triangular_discrimination.{cid}",
            "op": "triangular_discrimination",
            "args": {"p": p, "q": q},
            "expected": float(t),
            "tol": TOL,
            "source": why,
        }
    )
    return t


got = add("same", [1.0, 2.0, 3.0], [2.0, 4.0, 6.0], "the same distribution after scaling: 0")
assert got == 0
got = add("disjoint", [1.0, 0.0, 0.0], [0.0, 2.0, 1.0], "no shared support: P + Q summed, 2")
assert got == 2
got = add(
    "half",
    [1.0, 0.0],
    [1.0, 1.0],
    "P = (1, 0), Q = (1/2, 1/2): (1/4)/(3/2) + (1/4)/(1/2) = 1/6 + 1/2 = 2/3",
)
assert got == Fr(2, 3)
got = add(
    "coin",
    [3.0, 1.0],
    [1.0, 1.0],
    "P = (3/4, 1/4) against a fair coin: (1/16)/(5/4) + (1/16)/(3/4) = 2/15",
)
assert got == Fr(2, 15)
got = add(
    "shared_zero",
    [3.0, 0.0, 1.0],
    [1.0, 0.0, 1.0],
    "the coin case with an index zero in both, dropped: 2/15",
)
assert got == Fr(2, 15)
rng = random.Random(416)
p = [rng.randint(0, 6) * 1.0 for _ in range(16)]
q = [rng.randint(0, 6) * 1.0 for _ in range(16)]
assert 0.0 in p + q
add("counts", p, q, "16 counts each from random.Random(416), 0 to 6, with zeros")
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
            "id": f"triangular_discrimination.{cid}",
            "op": "triangular_discrimination",
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

doc = {
    "schema": 1,
    "suite": "triangular_discrimination",
    "description": "The triangular discrimination (conventions: triangular discrimination; "
    "ADR 0416).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "triangular_discrimination.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/triangular_discrimination.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
