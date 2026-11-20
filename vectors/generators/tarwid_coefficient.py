"""Writes vectors/cases/tarwid_coefficient.json, stdlib only.

Tarwid's coefficient (conventions: Tarwid's coefficient; ADR 0453): the 2x2 table counted
directly, the value formed in rationals from the shares as (TP/n - pA pB) / (TP/n + pA pB).

Run from the repo root: python vectors/generators/tarwid_coefficient.py [--check]
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
    pa, pb = Fr(tp + fn, len(t)), Fr(tp + fp, len(t))
    q = (Fr(tp, len(t)) - pa * pb) / (Fr(tp, len(t)) + pa * pb)
    cases.append(
        {
            "id": f"tarwid_coefficient.{cid}",
            "op": "tarwid_coefficient",
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
    "n 4, TP 2, |A| = |B| = 2: (8 - 4)/(8 + 4) = 1/3",
)
assert got == Fr(1, 3)
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, TP 0, |A| = |B| = 2: (0 - 4)/(0 + 4) = -1, the least",
)
assert got == -1
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 1, |A| = |B| = 2: (4 - 4)/(4 + 4) = 0",
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "n 5, TP 1, |A| = |B| = 2: (5 - 4)/(5 + 4) = 1/9",
)
assert got == Fr(1, 9)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, TP 4, |A| = |B| = 5: (40 - 25)/(40 + 25) = 3/13",
)
assert got == Fr(3, 13)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "n 6, TP 2, |A| 3, |B| 2: (12 - 6)/(12 + 6) = 1/3",
)
assert got == Fr(1, 3)
got = add(
    "far_below",
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0],
    "n 4, TP 0, |A| 1, |B| 3: (0 - 3)/(0 + 3) = -1",
)
assert got == -1
got = add(
    "constant",
    [1.0, 1.0, 1.0],
    [1.0, 0.0, 1.0],
    "truth all 1, n 3, TP 2, |B| 2: (6 - 6)/(6 + 6) = 0, no error",
)
assert got == 0
got = add(
    "rare",
    [1.0] + [0.0] * 9,
    [1.0] + [0.0] * 9,
    "n 10, TP 1, |A| = |B| = 1: (10 - 1)/(10 + 1) = 9/11, near 1",
)
assert got == Fr(9, 11)
rng = random.Random(453)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(453), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"tarwid_coefficient.{cid}",
            "op": "tarwid_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_decision_one", "decision all 0: |B| = 0", decision=[0.0, 0.0, 0.0])
err("no_truth_one", "truth all 0: TP and |A| are 0", truth=[0.0, 0.0, 0.0])

doc = {
    "schema": 1,
    "suite": "tarwid_coefficient",
    "description": "Tarwid's coefficient (conventions: Tarwid's coefficient; ADR 0453).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tarwid_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/tarwid_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
