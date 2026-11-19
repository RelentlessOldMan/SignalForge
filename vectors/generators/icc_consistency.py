"""Writes vectors/cases/icc_consistency.json, stdlib only.

ICC(3,1) (conventions: ICC(3,1); ADR 0381): the means and sums of squares exact in rationals.

Run from the repo root: python vectors/generators/icc_consistency.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def add(cid, rows, why):
    x = [[Fr(v) for v in r] for r in rows]
    k, n = len(x), len(x[0])
    grand = sum(sum(r) for r in x) / (k * n)
    rm = [sum(r) / n for r in x]
    cm = [sum(x[i][j] for i in range(k)) / k for j in range(n)]
    ms_s = k * sum((c - grand) ** 2 for c in cm) / (n - 1)
    ss_e = sum((x[i][j] - rm[i] - cm[j] + grand) ** 2 for i in range(k) for j in range(n))
    ms_e = ss_e / ((n - 1) * (k - 1))
    icc = (ms_s - ms_e) / (ms_s + (k - 1) * ms_e)
    cases.append({"id": f"icc_consistency.{cid}", "op": "icc_consistency",
                  "args": {"ratings": rows}, "expected": float(icc), "tol": TOL,
                  "source": why})
    return icc


got = add("offset_raters", [[1.0, 2.0, 3.0], [2.0, 3.0, 4.0]],
          "the second rater is the first plus 1: no residual, ICC = 1")
assert got == 1
got = add("opposed", [[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]],
          "the column means are all 2, so MS_S = 0; residuals -1, 0, 1, 1, 0, -1 give "
          "MS_E = 4/2 = 2: (0 - 2)/(0 + 2) = -1")
assert got == -1
# Shrout and Fleiss (1979), Table 2: six subjects (columns here) rated by four judges (rows).
sf_table = [[9.0, 6.0, 8.0, 7.0, 10.0, 6.0], [2.0, 1.0, 4.0, 1.0, 5.0, 2.0],
            [5.0, 3.0, 6.0, 2.0, 6.0, 4.0], [8.0, 2.0, 8.0, 6.0, 9.0, 7.0]]
got = add("shrout_fleiss", sf_table,
          "the example of Shrout and Fleiss (1979), 4 judges by 6 targets; their published "
          "ICC(3,1) is 0.71: MS_S = 11.24, MS_E = 1.02")
assert round(float(got), 2) == 0.71
rng = random.Random(381)
base = [rng.randint(0, 40) / 4 for _ in range(15)]
rows = [[b + o + rng.randint(-6, 6) / 4 for b in base] for o in (0.0, 1.5, -2.0, 0.25, 3.0)]
add("five_raters", rows, "5 raters of 15 subjects from random.Random(381): a common score "
    "in quarters, a fixed offset per rater and independent quarters")


def err(cid, why, ratings):
    cases.append({"id": f"icc_consistency.{cid}", "op": "icc_consistency",
                  "args": {"ratings": ratings}, "error": "invalid_argument", "source": why})


err("one_rater", "k must be at least 2", [[1.0, 2.0, 3.0]])
err("one_subject", "n must be at least 2", [[1.0], [2.0]])
err("no_spread", "every column is the same once the rater offsets are removed",
    [[1.0, 1.0, 1.0], [4.0, 4.0, 4.0]])
err("nan", "ratings must be finite", [[1.0, 2.0, 3.0], [1.0, "nan", 3.0]])

doc = {
    "schema": 1,
    "suite": "icc_consistency",
    "description": "ICC(3,1) (conventions: ICC(3,1); ADR 0381).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "icc_consistency.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/icc_consistency.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
