"""Writes vectors/cases/consonni_todeschini_coefficient.json, stdlib only.

The Consonni-Todeschini coefficient (conventions: the Consonni-Todeschini coefficient;
ADR 0457): the 2x2 table counted directly, ln(1 + TP + TN) and ln(1 + n) correctly rounded in
40-digit decimals, then their ratio.

Run from the repo root: python vectors/generators/consonni_todeschini_coefficient.py [--check]
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
    q = D(1 + tp + tn).ln() / D(1 + len(t)).ln()
    cases.append(
        {
            "id": f"consonni_todeschini_coefficient.{cid}",
            "op": "consonni_todeschini_coefficient",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add("identical", [1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0], "n 4, TP + TN 4: ln 5/ln 5 = 1")
assert got == 1
got = add(
    "opposite",
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    "n 4, TP + TN 0: ln 1/ln 5 = 0, the least value",
)
assert got == 0
got = add("independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "n 4, TP + TN 2: ln 3/ln 5")
assert 0.68 < got < 0.69
got = add(
    "uneven", [1.0, 1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0, 1.0], "n 5, TP 1, TN 2: ln 4/ln 6"
)
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "n 10, TP 4, TN 4: ln 9/ln 11",
)
got = add("half", [1.0, 0.0, 0.0], [1.0, 1.0, 1.0], "n 3, TP 1, TN 0: ln 2/ln 4 = 1/2")
assert close(got, D(1) / 2)
got = add("power", [1.0] + [0.0] * 7, [1.0] * 7 + [0.0], "n 8, TP 1, TN 1: ln 3/ln 9 = 1/2")
assert close(got, D(1) / 2)
got = add("cube", [1.0] + [0.0] * 62, [0.0] + [1.0] * 62, "n 63, TP + TN 0: ln 1/ln 64 = 0")
assert got == 0
got = add(
    "third",
    [1.0, 1.0, 1.0] + [0.0] * 60,
    [1.0, 0.0, 0.0] + [1.0] * 60,
    "n 63, TP 1, TN 0, FN 2, FP 60: ln 2/ln 64 = 1/6",
)
assert close(got, D(1) / 6)
got = add(
    "constant", [1.0, 1.0, 1.0], [1.0, 0.0, 1.0], "truth all 1, n 3, TP 2: ln 3/ln 4, no error"
)
got = add(
    "all_zero", [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "both all 0, n 3, TN 3: ln 4/ln 4 = 1, no error"
)
assert got == 1
rng = random.Random(457)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(457), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"consonni_todeschini_coefficient.{cid}",
            "op": "consonni_todeschini_coefficient",
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
    "suite": "consonni_todeschini_coefficient",
    "description": "The Consonni-Todeschini coefficient (conventions: the Consonni-Todeschini"
    " coefficient; ADR 0457).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "consonni_todeschini_coefficient.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/consonni_todeschini_coefficient.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
