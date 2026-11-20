"""Writes vectors/cases/baroni_urbani_buser_ii.json, stdlib only.

The second Baroni-Urbani-Buser coefficient (conventions: the second Baroni-Urbani-Buser
coefficient; ADR 0468): the 2x2 table counted directly, sqrt(TP TN) correctly rounded in
40-digit decimals and the value formed there.

Run from the repo root: python vectors/generators/baroni_urbani_buser_ii.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 40
TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    root = D(tp * tn).sqrt()
    q = (root + (tp - fn - fp)) / (root + (tp + fn + fp))
    cases.append(
        {
            "id": f"baroni_urbani_buser_ii.{cid}",
            "op": "baroni_urbani_buser_ii",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add(
    "identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "TP 2, TN 2: r 2, (2 + 2)/(2 + 2) = 1"
)
assert got == 1
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "TP 0, TN 0, FN 2, FP 2: (0 - 4)/(0 + 4) = -1",
)
assert got == -1
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell: r 1, (1 + 1 - 2)/(1 + 3) = 0",
)
assert got == 0
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: r 4, (4 + 2)/(4 + 6) = 3/5",
)
assert close(got, D(3) / 5)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 2, FN 1, TN 3: (sqrt 6 + 1)/(sqrt 6 + 3)",
)
assert close(got * (D(6).sqrt() + 3), D(6).sqrt() + 1)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 1, FN 1, FP 1, TN 2: (sqrt 2 - 1)/(sqrt 2 + 3)",
)
assert close(got * (D(2).sqrt() + 3), D(2).sqrt() - 1)
got = add("all_one", [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], "both all 1, TP 3, TN 0: 3/3 = 1, no error")
assert got == 1
rng = random.Random(468)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(468), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"baroni_urbani_buser_ii.{cid}",
            "op": "baroni_urbani_buser_ii",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("all_zero", "both all 0: the denominator is 0", truth=[0.0, 0.0, 0.0], decision=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "baroni_urbani_buser_ii",
    "description": "The second Baroni-Urbani-Buser coefficient (conventions: the second"
    " Baroni-Urbani-Buser coefficient; ADR 0468).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "baroni_urbani_buser_ii.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/baroni_urbani_buser_ii.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
