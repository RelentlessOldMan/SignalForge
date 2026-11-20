"""Writes vectors/cases/extremal_dependence_index.json, stdlib only.

The extremal dependence index (conventions: the extremal dependence index; ADR 0490): the
2x2 table counted directly, (ln F - ln H) / (ln F + ln H) with the logarithms in 40-digit
decimals.

Run from the repo root: python vectors/generators/extremal_dependence_index.py [--check]
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
    lf = (D(fp) / (fp + tn)).ln()
    lh = (D(tp) / (tp + fn)).ln()
    q = (lf - lh) / (lf + lh)
    cases.append(
        {
            "id": f"extremal_dependence_index.{cid}",
            "op": "extremal_dependence_index",
            "args": {"truth": t, "decision": d},
            "expected": float(q),
            "tol": TOL,
            "source": why,
        }
    )
    return q


def close(a, b):
    return abs(a - b) < D(10) ** -35


def edi(h, f):
    return ((f).ln() - (h).ln()) / ((f).ln() + (h).ln())


got = add(
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "H 4/5, F 1/5: ln(1/4)/ln(4/25)",
)
assert close(got, (D(1) / 4).ln() / (D(4) / 25).ln())
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "H 2/3, F 3/4: ln(9/8)/ln(1/2), below 0",
)
assert close(got, (D(9) / 8).ln() / (D(1) / 2).ln())
got = add(
    "skew",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "H 3/4, F 1/3: ln(4/9)/ln(1/4)",
)
assert close(got, edi(D(3) / 4, D(1) / 3))
got = add("equal_rates", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "H = F = 1/2: 0")
assert got == 0
got = add(
    "all_hits",
    [1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 0.0, 0.0],
    "H 1, F 1/3: ln(1/3)/ln(1/3) = 1, the greatest value",
)
assert got == 1
got = add(
    "all_alarms",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 1.0],
    "H 1/2, F 1: -ln(1/2)/ln(1/2) = -1, the least value",
)
assert got == -1
rng = random.Random(490)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(490), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"extremal_dependence_index.{cid}",
            "op": "extremal_dependence_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err("truth_all_zero", "truth has no 1: |A| = 0", truth=[0.0, 0.0, 0.0], decision=[1.0, 0.0, 1.0])
err("truth_all_one", "truth has no 0: n - |A| = 0", truth=[1.0, 1.0, 1.0], decision=[1.0, 0.0, 1.0])
err("no_tp", "opposite records: TP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[0.0, 1.0, 0.0, 1.0])
err("no_fp", "equal records: FP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[1.0, 0.0, 1.0, 0.0])
err(
    "decision_all_one",
    "the decision has no 0: H = F = 1",
    truth=[1.0, 0.0, 1.0],
    decision=[1.0, 1.0, 1.0],
)


doc = {
    "schema": 1,
    "suite": "extremal_dependence_index",
    "description": "The extremal dependence index (conventions: the extremal dependence"
    " index; ADR 0490).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "extremal_dependence_index.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/extremal_dependence_index.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
