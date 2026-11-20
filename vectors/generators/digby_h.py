"""Writes vectors/cases/digby_h.json, stdlib only.

Digby's H (conventions: Digby's H; ADR 0444): the 2x2 table counted directly, the powers 3/4
taken as square roots in 40-digit decimals.

Run from the repo root: python vectors/generators/digby_h.py [--check]
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
    px, py = sx * sx.sqrt(), sy * sy.sqrt()
    q = (px - py) / (px + py)
    cases.append(
        {
            "id": f"digby_h.{cid}",
            "op": "digby_h",
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
    "TP 2, TN 2, no mismatch: y = 0 gives 1",
)
assert got == 1
got = add(
    "opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "FN 2, FP 2, no match: x = 0 gives -1"
)
assert got == -1
got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "one of each cell: x = y = 1 gives 0"
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 1, FN 1, FP 1, TN 2: x 2, y 1: (2^(3/4) - 1)/(2^(3/4) + 1)",
)
assert close(got, (D(8).sqrt().sqrt() - 1) / (D(8).sqrt().sqrt() + 1))
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: x 16, y 1: (8 - 1)/(8 + 1) = 7/9",
)
assert close(got, D(7) / 9)
got = add(
    "fourth_powers",
    [1.0] * 9 + [0.0] * 9 + [1.0] + [0.0],
    [1.0] * 9 + [0.0] * 9 + [0.0] + [1.0],
    "TP 9, TN 9, FN 1, FP 1: x 81, y 1: (27 - 1)/(27 + 1) = 13/14",
)
assert close(got, D(13) / 14)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 1, FN 2, FP 0, TN 2: FP empty, y = 0 gives 1",
)
assert got == 1
rng = random.Random(444)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(444), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"digby_h.{cid}",
            "op": "digby_h",
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
    "suite": "digby_h",
    "description": "Digby's H (conventions: Digby's H; ADR 0444).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "digby_h.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/digby_h.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
