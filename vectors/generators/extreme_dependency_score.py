"""Writes vectors/cases/extreme_dependency_score.json, stdlib only.

The extreme dependency score (conventions: the extreme dependency score; ADR 0489): the
2x2 table counted directly, 2 ln(|A|/n) / ln(TP/n) - 1 with the logarithms in 40-digit
decimals.

Run from the repo root: python vectors/generators/extreme_dependency_score.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 40

TOL = {"abs": 1e-13, "rel": 1e-13}
cases = []


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    n = len(t)
    q = 2 * (D(tp + fn) / n).ln() / (D(tp) / n).ln() - 1
    cases.append(
        {
            "id": f"extreme_dependency_score.{cid}",
            "op": "extreme_dependency_score",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


got = add(
    "identical",
    [1.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "|A| 2, TP 2, n 4: 2 ln(1/2)/ln(1/2) - 1 = 1, the greatest value",
)
assert got == 1
got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "|A| 5, TP 4, n 10: 2 ln(1/2)/ln(2/5) - 1",
)
assert close(got, 2 * (D(1) / 2).ln() / (D(2) / 5).ln() - 1)
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "|A| 3, TP 2, n 7: 2 ln(3/7)/ln(2/7) - 1",
)
assert close(got, 2 * (D(3) / 7).ln() / (D(2) / 7).ln() - 1)
got = add(
    "skew",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "|A| 4, TP 3, n 7: 2 ln(4/7)/ln(3/7) - 1",
)
assert close(got, 2 * (D(4) / 7).ln() / (D(3) / 7).ln() - 1)
got = add(
    "truth_all_one",
    [1.0, 1.0, 1.0],
    [1.0, 0.0, 1.0],
    "|A| 3, TP 2, n 3: 2 ln 1/ln(2/3) - 1 = -1, the least value",
)
assert got == -1
got = add(
    "lone",
    [1.0] + [0.0] * 9,
    [1.0, 1.0] + [0.0] * 8,
    "|A| 1, TP 1, n 10: 1, false alarms do not count",
)
assert got == 1
rng = random.Random(489)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(489), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"extreme_dependency_score.{cid}",
            "op": "extreme_dependency_score",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("no_tp", "opposite records: TP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[0.0, 1.0, 0.0, 1.0])
err("truth_all_zero", "truth has no 1: TP = 0", truth=[0.0, 0.0, 0.0], decision=[1.0, 0.0, 1.0])
err(
    "all_one",
    "both records all 1: TP = n, ln(TP/n) = 0",
    truth=[1.0, 1.0, 1.0],
    decision=[1.0, 1.0, 1.0],
)


doc = {
    "schema": 1,
    "suite": "extreme_dependency_score",
    "description": "The extreme dependency score (conventions: the extreme dependency"
    " score; ADR 0489).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "extreme_dependency_score.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/extreme_dependency_score.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
