"""Writes vectors/cases/kulczynski_i.json, stdlib only.

The first Kulczynski coefficient (conventions: the first Kulczynski coefficient;
ADR 0462): the 2x2 table counted directly, the value formed in rationals as
TP / (FN + FP).

Run from the repo root: python vectors/generators/kulczynski_i.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    q = Fr(tp, fn + fp)
    cases.append(
        {
            "id": f"kulczynski_i.{cid}",
            "op": "kulczynski_i",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "TP 0, FN 2, FP 2: 0/4 = 0, the least value",
)
assert got == 0
got = add("independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: 1/2")
assert got == Fr(1, 2)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: 4/2 = 2",
)
assert got == 2
got = add(
    "subset",
    [1.0, 1.0, 1.0, 1.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 0.0],
    "TP 3, FN 1, FP 0, TN 1: 3/1 = 3",
)
assert got == 3
got = add(
    "far_below", [1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 1.0, 1.0], "TP 0, FN 1, FP 3, TN 0: 0/4 = 0"
)
assert got == 0
got = add(
    "shared_zeros",
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    "TP 1, FN 1, FP 2, TN 3: 1/3; shared 0s do not count",
)
assert got == Fr(1, 3)
got = add(
    "constant", [1.0, 1.0, 1.0], [1.0, 0.0, 1.0], "truth all 1, TP 2, FN 1: 2/1 = 2, no error"
)
assert got == 2
rng = random.Random(462)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(462), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"kulczynski_i.{cid}",
            "op": "kulczynski_i",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "identical",
    "FN + FP = 0: the records agree everywhere",
    truth=[1.0, 0.0, 1.0],
    decision=[1.0, 0.0, 1.0],
)

doc = {
    "schema": 1,
    "suite": "kulczynski_i",
    "description": "The first Kulczynski coefficient (conventions: the first Kulczynski"
    " coefficient; ADR 0462).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "kulczynski_i.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/kulczynski_i.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
