"""Writes vectors/cases/yule_y.json, stdlib only.

Yule's Y (conventions: Yule's Y; ADR 0431): the 2x2 table counted directly, the roots taken
in 40-digit decimals.

Run from the repo root: python vectors/generators/yule_y.py [--check]
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
    tn = sum(1 for a, b in zip(t, d) if a == 0 and b == 0)
    sx, sy = D(tp * tn).sqrt(), D(fn * fp).sqrt()
    q = (sx - sy) / (sx + sy)
    cases.append(
        {
            "id": f"yule_y.{cid}",
            "op": "yule_y",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(v, want):
    return abs(v - want) < D("1e-35")


got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "TP 2, TN 2, no mismatch: (2 - 0)/(2 + 0) = 1",
)
assert got == 1
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "FN 2, FP 2, no match: (0 - 2)/(0 + 2) = -1",
)
assert got == -1
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell: (1 - 1)/(1 + 1) = 0",
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 1, FN 1, FP 1, TN 2: (sqrt 2 - 1)/(sqrt 2 + 1) = 3 - 2 sqrt 2",
)
assert close(got, 3 - 2 * D(2).sqrt())
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: (4 - 1)/(4 + 1) = 3/5",
)
assert close(got, D(3) / 5)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 1, FN 2, FP 0, TN 2: FP empty gives (sqrt 2 - 0)/(sqrt 2 + 0) = 1",
)
assert got == 1
rng = random.Random(431)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(431), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"yule_y.{cid}",
            "op": "yule_y",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "constant",
    "truth all 1: TN and FP are 0, so both products are 0",
    truth=[1.0, 1.0, 1.0],
    decision=[1.0, 0.0, 1.0],
)

doc = {
    "schema": 1,
    "suite": "yule_y",
    "description": "Yule's Y (conventions: Yule's Y; ADR 0431).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "yule_y.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/yule_y.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
