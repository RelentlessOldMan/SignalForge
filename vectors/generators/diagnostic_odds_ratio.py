"""Writes vectors/cases/diagnostic_odds_ratio.json, stdlib only.

The diagnostic odds ratio (conventions: Diagnostic odds ratio; ADR 0390): the table counted in
integers, the ratio exact in rationals.

Run from the repo root: python vectors/generators/diagnostic_odds_ratio.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, truth, decision, why):
    pairs = list(zip(truth, decision))
    tp, tn = pairs.count((1.0, 1.0)), pairs.count((0.0, 0.0))
    fp, fn = pairs.count((0.0, 1.0)), pairs.count((1.0, 0.0))
    # The odds of a positive decision among the positives over that among the negatives.
    dor = Fr(tp, fn) / Fr(fp, tn) if tn else None
    assert dor is None or dor == Fr(tp * tn, fp * fn)
    dor = Fr(tp * tn, fp * fn)
    cases.append(
        {
            "id": f"diagnostic_odds_ratio.{cid}",
            "op": "diagnostic_odds_ratio",
            "args": {"truth": truth, "decision": decision},
            "expected": float(dor),
            "tol": TOL,
            "source": why,
        }
    )
    return dor


got = add(
    "chance",
    [1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    "one of each cell: odds 1 among positives and negatives, DOR = 1",
)
assert got == 1
got = add(
    "good_test",
    [1.0] * 10 + [0.0] * 10,
    [1.0] * 8 + [0.0] * 2 + [1.0] * 1 + [0.0] * 9,
    "TP 8, FN 2, FP 1, TN 9: odds 4 over odds 1/9, DOR = 36",
)
assert got == 36
got = add(
    "inverted",
    [1.0, 1.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 0.0, 1.0, 1.0],
    "TP 1, FN 2, FP 2, TN 0: DOR = 0",
)
assert got == 0
got = add(
    "thirds",
    [1.0] * 4 + [0.0] * 5,
    [1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0],
    "TP 1, FN 3, FP 3, TN 2: DOR = 2/9",
)
assert got == Fr(2, 9)
rng = random.Random(390)
truth = [1.0 if rng.random() < 0.3 else 0.0 for _ in range(400)]
decision = [t if rng.random() < 0.8 else 1.0 - t for t in truth]
add(
    "noisy_detector",
    truth,
    decision,
    "400 items from random.Random(390), 30% positive, each decision flipped with probability 0.2",
)


def err(cid, why, **args):
    base = {"truth": [1.0, 1.0, 0.0, 0.0], "decision": [1.0, 0.0, 1.0, 0.0]}
    base.update(args)
    cases.append(
        {
            "id": f"diagnostic_odds_ratio.{cid}",
            "op": "diagnostic_odds_ratio",
            "args": base,
            "error": "invalid_argument",
            "source": why,
        }
    )


err("lengths_differ", "truth and decision must be the same length", decision=[1.0, 0.0])
err("empty", "N must be at least 1", truth=[], decision=[])
err("not_binary", "values must be 0 or 1", decision=[1.0, 0.0, 1.0, 7.0])
err("no_false_positive", "FP = 0 makes the ratio infinite", decision=[1.0, 0.0, 0.0, 0.0])
err("no_false_negative", "FN = 0 makes the ratio infinite", decision=[1.0, 1.0, 1.0, 0.0])

doc = {
    "schema": 1,
    "suite": "diagnostic_odds_ratio",
    "description": "The diagnostic odds ratio (conventions: Diagnostic odds ratio; ADR 0390).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "diagnostic_odds_ratio.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/diagnostic_odds_ratio.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
