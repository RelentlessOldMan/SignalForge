"""Writes vectors/cases/mcnemar_statistic.json, stdlib only.

McNemar's statistic (conventions: McNemar's statistic; ADR 0479): the 2x2 table counted
directly, the value formed in rationals.

Run from the repo root: python vectors/generators/mcnemar_statistic.py [--check]
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
    assert tp + fn + fp + tn == len(t)
    q = Fr((fn - fp) ** 2, fn + fp)
    cases.append(
        {
            "id": f"mcnemar_statistic.{cid}",
            "op": "mcnemar_statistic",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "balanced", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 1.0, 0.0], "FN 1, FP 1: 0/2 = 0, the least value"
)
assert got == 0
got = add("opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "FN 2, FP 2: 0")
assert got == 0
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "FN 2, FP 0: 4/2 = 2 = FN + FP",
)
assert got == 2
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0, 1.0, 1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0, 0.0, 0.0] + [1.0],
    "FN 3, FP 1: 4/4 = 1",
)
assert got == 1
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "FN 1, FP 3: 4/4 = 1",
)
assert got == 1
got = add(
    "lopsided",
    [1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0],
    "FN 4, FP 1: 9/5",
)
assert got == Fr(9, 5)
got = add(
    "one_way", [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], "FP 3, FN 0: 9/3 = 3 = n, the greatest value"
)
assert got == 3
rng = random.Random(479)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(479), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"mcnemar_statistic.{cid}",
            "op": "mcnemar_statistic",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("agree", "equal records: FN + FP = 0", truth=[1.0, 0.0, 1.0], decision=[1.0, 0.0, 1.0])

doc = {
    "schema": 1,
    "suite": "mcnemar_statistic",
    "description": "McNemar's statistic (conventions: McNemar's statistic; ADR 0479).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mcnemar_statistic.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mcnemar_statistic.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
