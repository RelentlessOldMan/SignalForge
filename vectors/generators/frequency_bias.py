"""Writes vectors/cases/frequency_bias.json, stdlib only.

The frequency bias (conventions: the frequency bias; ADR 0488): the 2x2 table counted
directly, the value formed in rationals.

Run from the repo root: python vectors/generators/frequency_bias.py [--check]
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
    q = Fr(tp + fp, tp + fn)
    cases.append(
        {
            "id": f"frequency_bias.{cid}",
            "op": "frequency_bias",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "|B| 2, |A| 2: 1")
assert got == 1
got = add(
    "opposite", [1.0, 0.0, 1.0, 0.0], [0.0, 1.0, 0.0, 1.0], "|B| 2, |A| 2: 1, with no 1 in common"
)
assert got == 1
got = add("none_flagged", [1.0, 0.0, 0.0], [0.0, 0.0, 0.0], "|B| 0, |A| 1: 0, the least value")
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "|B| 5, |A| 3: 5/3",
)
assert got == Fr(5, 3)
got = add(
    "skew",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "|B| 4, |A| 4: 1",
)
assert got == 1
got = add("under", [1.0, 1.0, 1.0, 1.0, 0.0], [1.0, 0.0, 0.0, 0.0, 0.0], "|B| 1, |A| 4: 1/4")
assert got == Fr(1, 4)
got = add("all_flagged", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "|B| 3, |A| 1: 3")
assert got == 3
rng = random.Random(488)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(488), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"frequency_bias.{cid}",
            "op": "frequency_bias",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("truth_all_zero", "truth has no 1: |A| = 0", truth=[0.0, 0.0, 0.0], decision=[1.0, 0.0, 1.0])


doc = {
    "schema": 1,
    "suite": "frequency_bias",
    "description": "The frequency bias (conventions: the frequency bias; ADR 0488).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "frequency_bias.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/frequency_bias.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
