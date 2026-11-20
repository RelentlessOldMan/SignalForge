"""Writes vectors/cases/anderberg_d.json, stdlib only.

Anderberg's D (conventions: Anderberg's D; ADR 0446): the 2x2 table counted directly, the
value formed in rationals from the cell shares as the row and column maxima less the margin
maxima, halved.

Run from the repo root: python vectors/generators/anderberg_d.py [--check]
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
    a, b, c, e = (Fr(k, len(t)) for k in (tp, fn, fp, tn))
    rows = [[a, b], [c, e]]
    cols = [[a, c], [b, e]]
    gain = sum(max(x) for x in rows) + sum(max(x) for x in cols)
    q = (gain - max(sum(x) for x in rows) - max(sum(x) for x in cols)) / 2
    cases.append(
        {
            "id": f"anderberg_d.{cid}",
            "op": "anderberg_d",
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
    "TP 2, TN 2: sigma 8, sigma' 4: (8 - 4)/8 = 1/2, the most",
)
assert got == Fr(1, 2)
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "FN 2, FP 2: sigma 8, sigma' 4: 1/2, disagreement predicts as well",
)
assert got == Fr(1, 2)
got = add(
    "independent",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell: sigma 4, sigma' 4: 0",
)
assert got == 0
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 0.0, 1.0],
    "TP 1, FN 1, FP 1, TN 2: sigma 6, sigma' 3 + 3: 0, associated but no gain",
)
assert got == 0
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "TP 4, TN 4, FN 1, FP 1: sigma 16, sigma' 10: 6/20 = 3/10",
)
assert got == Fr(3, 10)
got = add(
    "subset",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0, 0.0, 0.0],
    "TP 2, FN 1, FP 0, TN 3: sigma 2 + 3 + 2 + 3 = 10, sigma' 3 + 4: 3/12 = 1/4",
)
assert got == Fr(1, 4)
got = add(
    "far_below",
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 1.0, 1.0],
    "TP 0, FN 1, FP 3, TN 0: sigma 1 + 3 + 3 + 1 = 8, sigma' 3 + 3: 2/8 = 1/4",
)
assert got == Fr(1, 4)
got = add(
    "constant",
    [1.0, 1.0, 1.0],
    [1.0, 0.0, 1.0],
    "truth all 1, TP 2, FN 1: sigma 5, sigma' 3 + 2: 0, no error",
)
assert got == 0
rng = random.Random(446)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(446), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"anderberg_d.{cid}",
            "op": "anderberg_d",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])

doc = {
    "schema": 1,
    "suite": "anderberg_d",
    "description": "Anderberg's D (conventions: Anderberg's D; ADR 0446).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "anderberg_d.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/anderberg_d.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
