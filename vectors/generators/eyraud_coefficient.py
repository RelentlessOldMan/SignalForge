"""Writes vectors/cases/eyraud_coefficient.json, stdlib only.

Eyraud's coefficient (conventions: Eyraud's coefficient; ADR 0450): the 2x2 table counted
directly, the value formed in rationals from the shares as
(TP/n - pA pB) / (pA pB (1 - pA)(1 - pB)).

Run from the repo root: python vectors/generators/eyraud_coefficient.py [--check]
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
    q = (Fr(tp, len(t)) - pa * pb) / (pa * pb * (1 - pa) * (1 - pb))
    cases.append(
        {
            "id": f"eyraud_coefficient.{cid}",
            "op": "eyraud_coefficient",
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
    "n 4, TP 2, |A| = |B| = 2: 16 (8 - 4)/(4 4) = 4",
)
assert got == 4
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, TP 0, |A| = |B| = 2: 16 (0 - 4)/(4 4) = -4",
)
assert got == -4
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "n 4, TP 1, |A| = |B| = 2: 16 (4 - 4)/16 = 0",
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "n 5, TP 1, |A| = |B| = 2: 25 (5 - 4)/(4 9) = 25/36",
)
assert got == Fr(25, 36)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, TP 4, |A| = |B| = 5: 100 (40 - 25)/(25 25) = 12/5",
)
assert got == Fr(12, 5)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "n 6, TP 2, |A| 3, |B| 2: 36 (12 - 6)/(6 12) = 3",
)
assert got == 3
got = add(
    "far_below",
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0],
    "n 4, TP 0, |A| 1, |B| 3: 16 (0 - 3)/(3 3) = -16/3",
)
assert got == Fr(-16, 3)
rng = random.Random(450)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(450), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"eyraud_coefficient.{cid}",
            "op": "eyraud_coefficient",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_decision_one", "decision all 0: |B| = 0", decision=[0.0, 0.0, 0.0])
err("all_one", "truth all 1: n - |A| = 0", truth=[1.0, 1.0, 1.0])

doc = {
    "schema": 1,
    "suite": "eyraud_coefficient",
    "description": "Eyraud's coefficient (conventions: Eyraud's coefficient; ADR 0450).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "eyraud_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/eyraud_coefficient.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
