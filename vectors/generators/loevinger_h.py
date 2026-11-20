"""Writes vectors/cases/loevinger_h.json, stdlib only.

Loevinger's H (conventions: Loevinger's H; ADR 0441): the 2x2 table counted directly, the
value formed in rationals as (TP/n - pA pB)/(min(pA, pB) - pA pB).

Run from the repo root: python vectors/generators/loevinger_h.py [--check]
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
    pa, pb = Fr(tp + fn, len(t)), Fr(tp + fp, len(t))
    q = (Fr(tp, len(t)) - pa * pb) / (min(pa, pb) - pa * pb)
    cases.append(
        {
            "id": f"loevinger_h.{cid}",
            "op": "loevinger_h",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, |A| = |B| = TP = 2: (1/2 - 1/4)/(1/2 - 1/4) = 1",
)
assert got == 1
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, |A| = |B| = 2, TP 0: (0 - 1/4)/(1/4) = -1",
)
assert got == -1
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell: TP/n = pA pB = 1/4, 0",
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "n 5, |A| = |B| = 2, TP 1: (1/5 - 4/25)/(2/5 - 4/25) = 1/6",
)
assert got == Fr(1, 6)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, |A| = |B| = 5, TP 4: (2/5 - 1/4)/(1/2 - 1/4) = 3/5",
)
assert got == Fr(3, 5)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 0.0],
    "B inside A, n 5, |A| 3, |B| 1, TP 1: (1/5 - 3/25)/(1/5 - 3/25) = 1",
)
assert got == 1
got = add(
    "far_below",
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0],
    "n 4, |A| 1, |B| 3, TP 0: (0 - 3/16)/(1/4 - 3/16) = -3, below -1",
)
assert got == -3
rng = random.Random(441)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(441), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"loevinger_h.{cid}",
            "op": "loevinger_h",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "all_one",
    "truth all 1: pA = 1, so min(pA, pB) = pA pB",
    truth=[1.0, 1.0, 1.0],
    decision=[1.0, 0.0, 1.0],
)
err("all_zero", "decision all 0: pB = 0, so the denominator is 0", decision=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "loevinger_h",
    "description": "Loevinger's H (conventions: Loevinger's H; ADR 0441).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "loevinger_h.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/loevinger_h.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
