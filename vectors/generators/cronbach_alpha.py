"""Writes vectors/cases/cronbach_alpha.json, stdlib only.

Cronbach's alpha (conventions: Cronbach's alpha; ADR 0380): the row variances and the
variance of the column totals exact in rationals.

Run from the repo root: python vectors/generators/cronbach_alpha.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def var(v):
    v = [Fr(u) for u in v]
    mean = sum(v) / len(v)
    return sum((u - mean) ** 2 for u in v) / (len(v) - 1)


def add(cid, rows, why):
    k = len(rows)
    items = sum(var(r) for r in rows)
    total = var([sum(col) for col in zip(*[[Fr(u) for u in r] for r in rows])])
    alpha = Fr(k, k - 1) * (1 - items / total)
    cases.append({"id": f"cronbach_alpha.{cid}", "op": "cronbach_alpha",
                  "args": {"scores": rows}, "expected": float(alpha), "tol": TOL,
                  "source": why})
    return items, total, alpha


got = add("offset_rows", [[1.0, 2.0, 3.0], [2.0, 3.0, 4.0]],
          "both rows have variance 1, the totals 3, 5, 7 variance 4: 2(1 - 2/4) = 1")
assert got == (2, 4, 1)
got = add("three_items", [[1.0, 2.0, 3.0, 4.0], [2.0, 1.0, 4.0, 3.0], [1.0, 3.0, 2.0, 4.0]],
          "each row is 1..4 in some order, variance 5/3; totals 4, 6, 9, 11, variance 29/3: "
          "1.5(1 - 5/(29/3)) = 21/29")
assert got == (5, Fr(29, 3), Fr(21, 29))
got = add("negative", [[1.0, 2.0, 3.0], [3.0, 1.0, 1.0]],
          "the rows disagree: variances 1 and 4/3, totals 4, 3, 4 variance 1/3: "
          "2(1 - 7) = -12")
assert got == (Fr(7, 3), Fr(1, 3), -12)
rng = random.Random(380)
base = [rng.randint(0, 40) / 4 for _ in range(25)]
rows = [[b + rng.randint(-12, 12) / 4 for b in base] for _ in range(6)]
add("six_items", rows, "6 items of 25 subjects from random.Random(380): a common score in "
    "quarters plus independent quarters")


def err(cid, why, scores):
    cases.append({"id": f"cronbach_alpha.{cid}", "op": "cronbach_alpha",
                  "args": {"scores": scores}, "error": "invalid_argument", "source": why})


err("one_item", "k must be at least 2", [[1.0, 2.0, 3.0]])
err("one_subject", "N must be at least 2", [[1.0], [2.0]])
err("equal_totals", "the totals 4, 4, 4 have no variance", [[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]])
err("nan", "scores must be finite", [[1.0, 2.0, 3.0], [1.0, "nan", 3.0]])

doc = {
    "schema": 1,
    "suite": "cronbach_alpha",
    "description": "Cronbach's alpha (conventions: Cronbach's alpha; ADR 0380).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "cronbach_alpha.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/cronbach_alpha.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
