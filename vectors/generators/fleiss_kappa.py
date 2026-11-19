"""Writes vectors/cases/fleiss_kappa.json, stdlib only.

Fleiss' kappa (conventions: Fleiss' kappa; ADR 0382): the agreement and chance terms exact in
rationals.

Run from the repo root: python vectors/generators/fleiss_kappa.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, rows, why):
    big_n, n = len(rows), int(sum(rows[0]))
    p = [Fr(int(sum(col)), big_n * n) for col in zip(*rows)]
    pe = sum(v * v for v in p)
    pbar = sum(Fr(int(sum(v * v for v in r)) - n, n * (n - 1)) for r in rows) / big_n
    kappa = (pbar - pe) / (1 - pe)
    cases.append({"id": f"fleiss_kappa.{cid}", "op": "fleiss_kappa", "args": {"counts": rows},
                  "expected": float(kappa), "tol": TOL, "source": why})
    return pbar, pe, kappa


got = add("full_agreement", [[3.0, 0.0], [0.0, 3.0]],
          "3 raters agree on each subject, half the ratings in each category: "
          "P = 1, Pe = 1/2, kappa = 1")
assert got == (1, Fr(1, 2), 1)
got = add("split", [[1.0, 1.0], [1.0, 1.0]],
          "2 raters disagree on both subjects: P = 0, Pe = 1/2, kappa = -1")
assert got == (0, Fr(1, 2), -1)
# Fleiss (1971): 10 subjects, 14 raters, 5 categories.
table = [[0, 0, 0, 0, 14], [0, 2, 6, 4, 2], [0, 0, 3, 5, 6], [0, 3, 9, 2, 0], [2, 2, 8, 1, 1],
         [7, 7, 0, 0, 0], [3, 2, 6, 3, 0], [2, 5, 3, 2, 2], [6, 5, 2, 1, 0], [0, 2, 2, 3, 7]]
got = add("fleiss_example", [[float(v) for v in r] for r in table],
          "the worked example of 10 subjects, 14 raters and 5 categories after Fleiss "
          "(1971), whose kappa is given as 0.210")
assert round(float(got[2]), 3) == 0.210
rng = random.Random(382)
rows = []
for _ in range(30):
    r = [0.0, 0.0, 0.0, 0.0]
    for _ in range(6):
        r[min(3, int(rng.random() ** 2 * 4))] += 1
    rows.append(r)
add("random_ratings", rows, "30 subjects of 6 ratings in 4 unevenly used categories from "
    "random.Random(382)")


def err(cid, why, counts):
    cases.append({"id": f"fleiss_kappa.{cid}", "op": "fleiss_kappa", "args": {"counts": counts},
                  "error": "invalid_argument", "source": why})


err("one_category", "q must be at least 2", [[3.0], [3.0]])
err("unequal_raters", "every row must sum to the same n", [[2.0, 1.0], [1.0, 1.0]])
err("one_rater", "n must be at least 2", [[1.0, 0.0], [0.0, 1.0]])
err("fraction", "counts must be whole numbers", [[1.5, 1.5], [2.0, 1.0]])
err("negative", "counts must not be negative", [[4.0, -1.0], [2.0, 1.0]])
err("one_category_used", "Pe = 1 when every rating is in the same category",
    [[3.0, 0.0], [3.0, 0.0]])

doc = {
    "schema": 1,
    "suite": "fleiss_kappa",
    "description": "Fleiss' kappa (conventions: Fleiss' kappa; ADR 0382).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fleiss_kappa.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/fleiss_kappa.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
