"""Writes vectors/cases/kendall_w.json, stdlib only.

Kendall's W (conventions: Kendall's W; ADR 0379): mean ranks per rater, the rank sums and the
tie correction exact in rationals.

Run from the repo root: python vectors/generators/kendall_w.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-14}
cases = []


def ranks(v):
    return [sum(1 for u in v if u < w) + Fr(sum(1 for u in v if u == w) + 1, 2) for w in v]


def add(cid, rows, why):
    m, n = len(rows), len(rows[0])
    sums = [Fr(0)] * n
    ties = 0
    for row in rows:
        sums = [a + b for a, b in zip(sums, ranks(row))]
        for v in set(row):
            t = row.count(v)
            ties += t**3 - t
    s = sum((r - Fr(m * (n + 1), 2)) ** 2 for r in sums)
    w = 12 * s / (m * m * (n**3 - n) - m * ties)
    cases.append({"id": f"kendall_w.{cid}", "op": "kendall_w", "args": {"ratings": rows},
                  "expected": float(w), "tol": TOL, "source": why})
    return s, ties, w


got = add("full_agreement", [[1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0],
                             [0.1, 0.2, 0.3, 0.4]],
          "every rater ranks 1, 2, 3, 4: R = 3, 6, 9, 12, S = 2(4.5^2 + 1.5^2) = 45; "
          "12*45/(9*60) = 1")
assert got == (45, 0, 1)
got = add("opposed", [[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]],
          "the second rater reverses the first: R = 4, 4, 4, S = 0, W = 0")
assert got == (0, 0, 0)
got = add("ties", [[1.0, 2.0, 3.0, 4.0], [1.0, 1.0, 2.0, 3.0]],
          "ranks 1, 2, 3, 4 and 1.5, 1.5, 3, 4: R = 2.5, 3.5, 6, 8, S = 18.5; T = 6; "
          "12*18.5/(4*60 - 2*6) = 222/228 = 37/38")
assert got == (Fr(37, 2), 6, Fr(37, 38))
rng = random.Random(379)
base = [rng.randint(0, 12) for _ in range(9)]
rows = [[float(b + rng.randint(-3, 3)) for b in base] for _ in range(5)]
add("five_raters_with_ties", rows,
    "5 raters of 9 items from random.Random(379): a common score plus -3..3 each, ties "
    "within raters")
rows = [[rng.random() for _ in range(12)] for _ in range(4)]
add("independent", rows, "4 independent raters of 12 uniform values")


def err(cid, why, ratings):
    cases.append({"id": f"kendall_w.{cid}", "op": "kendall_w", "args": {"ratings": ratings},
                  "error": "invalid_argument", "source": why})


err("one_rater", "m must be at least 2", [[1.0, 2.0, 3.0]])
err("one_item", "n must be at least 2", [[1.0], [2.0]])
err("all_constant", "the denominator is 0 when every row is constant",
    [[1.0, 1.0, 1.0], [2.0, 2.0, 2.0]])
err("nan", "ratings must be finite", [[1.0, 2.0, 3.0], [1.0, "nan", 3.0]])

doc = {
    "schema": 1,
    "suite": "kendall_w",
    "description": "Kendall's W (conventions: Kendall's W; ADR 0379).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "kendall_w.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/kendall_w.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
