"""Writes vectors/cases/symmetric_extremal_dependence_index.json, stdlib only.

The symmetric extremal dependence index (conventions: the symmetric extremal dependence
index; ADR 0491): the 2x2 table counted directly, the logarithms in 40-digit decimals.

Run from the repo root: python vectors/generators/symmetric_extremal_dependence_index.py [--check]
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


def sedi(h, f):
    lf, lg, lh, lm = f.ln(), (1 - f).ln(), h.ln(), (1 - h).ln()
    return (lf - lh - lg + lm) / (lf + lh + lg + lm)


def add(cid, t, d, why):
    tp = sum(1 for a, b in zip(t, d) if a == 1 and b == 1)
    fn = sum(1 for a, b in zip(t, d) if a == 1 and b == 0)
    fp = sum(1 for a, b in zip(t, d) if a == 0 and b == 1)
    tn = len(t) - tp - fn - fp
    assert tp + fn + fp + tn == len(t)
    q = sedi(D(tp) / (tp + fn), D(fp) / (fp + tn))
    cases.append(
        {
            "id": f"symmetric_extremal_dependence_index.{cid}",
            "op": "symmetric_extremal_dependence_index",
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
    "square",
    [1.0] * 4 + [0.0] * 4 + [1.0] + [0.0],
    [1.0] * 4 + [0.0] * 4 + [0.0] + [1.0],
    "H 4/5, F 1/5: 2 ln(1/4) / 2 ln(4/25)",
)
assert close(got, (D(1) / 4).ln() / (D(4) / 25).ln())
got = add(
    "uneven",
    [1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    "H 2/3, F 3/4: ln(3/2)/ln(1/24), below 0",
)
assert close(got, (D(3) / 2).ln() / (D(1) / 24).ln())
got = add(
    "skew",
    [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 1.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "H 3/4, F 1/3: ln(1/6)/ln(1/24)",
)
assert close(got, (D(1) / 6).ln() / (D(1) / 24).ln())
got = add(
    "flipped",
    [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
    [0.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0],
    "skew with both records complemented: H 2/3, F 1/4, the same ln(1/6)/ln(1/24)",
)
assert close(got, (D(1) / 6).ln() / (D(1) / 24).ln())
got = add(
    "independent", [1.0, 1.0, 0.0, 0.0], [1.0, 0.0, 1.0, 0.0], "H = F = 1/2: the numerator is 0"
)
assert got == 0
got = add(
    "opposite_lean",
    [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 1.0, 1.0, 0.0],
    "H 1/3, F 2/3: ln 4 / ln(4/81), below 0",
)
assert close(got, D(4).ln() / (D(4) / 81).ln())
rng = random.Random(491)
t = [float(rng.random() < 0.5) for _ in range(40)]
d = [v if rng.random() < 0.7 else 1.0 - v for v in t]
add("random", t, d, "40 bits from random.Random(491), about three in ten flipped")


def err(cid, why, **args):
    base = {"truth": [1.0, 0.0, 1.0], "decision": [1.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"symmetric_extremal_dependence_index.{cid}",
            "op": "symmetric_extremal_dependence_index",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "the records need an item", truth=[], decision=[])
err("lengths", "the records must match", decision=[1.0, 1.0])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.5, 0.0])
err(
    "truth_all_zero", "truth has no 1: TP = FN = 0", truth=[0.0, 0.0, 0.0], decision=[1.0, 0.0, 1.0]
)
err("truth_all_one", "truth has no 0: FP = TN = 0", truth=[1.0, 1.0, 1.0], decision=[1.0, 0.0, 1.0])
err("no_tp", "opposite records: TP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[0.0, 1.0, 0.0, 1.0])
err("no_fp", "equal records: FP = 0", truth=[1.0, 0.0, 1.0, 0.0], decision=[1.0, 0.0, 1.0, 0.0])
err(
    "no_fn",
    "every truth 1 caught: FN = 0",
    truth=[1.0, 0.0, 1.0, 0.0],
    decision=[1.0, 1.0, 1.0, 0.0],
)
err(
    "decision_all_one",
    "the decision has no 0: TN = 0",
    truth=[1.0, 0.0, 1.0],
    decision=[1.0, 1.0, 1.0],
)


doc = {
    "schema": 1,
    "suite": "symmetric_extremal_dependence_index",
    "description": "The symmetric extremal dependence index (conventions: the symmetric"
    " extremal dependence index; ADR 0491).",
    "cases": cases,
}
out = (
    pathlib.Path(__file__).resolve().parents[1]
    / "cases"
    / "symmetric_extremal_dependence_index.json"
)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/symmetric_extremal_dependence_index.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
