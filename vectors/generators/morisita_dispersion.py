"""Writes vectors/cases/morisita_dispersion.json, stdlib only.

Morisita's index of dispersion (conventions: Morisita's index of dispersion; ADR 0612):
n sum(x (x - 1))/(sum(x) (sum(x) - 1)) with fractions, straight from the definition.

Run from the repo root: python vectors/generators/morisita_dispersion.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, counts, why):
    xs = [Fr(c) for c in counts]
    tot = sum(xs)
    f = len(xs) * sum(c * (c - 1) for c in xs) / (tot * (tot - 1))
    cases.append(
        {
            "id": f"morisita_dispersion.{cid}",
            "op": "morisita_dispersion",
            "args": {"counts": counts},
            "expected": float(f) + 0.0,
            "tol": TOL,
            "source": why,
        }
    )
    return f


assert add("even", [2.0, 2.0, 2.0], "3 * 6/(6 * 5) = 3/5") == Fr(3, 5)
assert add("clumped", [0.0, 0.0, 6.0], "all in one of 3 units: 3") == 3
assert add("two_units", [0.0, 3.0], "all in one of 2 units: 2") == 2
assert add("mixed", [1.0, 2.0, 3.0], "3 * 8/(6 * 5) = 4/5") == Fr(4, 5)
assert add("uneven", [4.0, 0.0, 1.0, 0.0, 3.0], "5 * 18/(8 * 7) = 45/28") == Fr(45, 28)
assert add("singles", [1.0, 1.0, 0.0, 0.0], "no two share a unit: 0") == 0
assert (
    add("huge", [1e308, 0.0], "the sums would overflow: all in one of 2 units, 2") == 2
)
assert add(
    "many_singles",
    [1.0] * 1000 + [3.0],
    "1000 ones and a 3: sum x(x - 1) 6, total 1003, n 1001: 1001 * 6/(1003 * 1002)",
) == Fr(1001 * 6, 1003 * 1002)
cases[-1]["tol"] = {
    "abs": 0.0,
    "rel": 1e-13,
}  # a small value: hold it to relative accuracy
rng = random.Random(612)
counts = [float(rng.choice([0, 0, 1, 2, 3, 7])) for _ in range(30)]
add("random", counts, "30 counts from random.Random(612).choice([0, 0, 1, 2, 3, 7])")


def err(cid, why, counts):
    cases.append(
        {
            "id": f"morisita_dispersion.{cid}",
            "op": "morisita_dispersion",
            "args": {"counts": counts},
            "error": "invalid_argument",
            "source": why,
        }
    )


err("empty", "there must be a unit", [])
err("one_unit", "there must be at least two units", [5.0])
err("total_one", "the total must be above 1", [1.0, 0.0])
err("negative", "counts must be at least 0", [1.0, -1.0, 2.0])
err("all_zero", "the total must be above 0", [0.0, 0.0])
err("not_whole", "counts must be whole numbers", [1.0, 2.5])

doc = {
    "schema": 1,
    "suite": "morisita_dispersion",
    "description": "Morisita's index of dispersion (conventions: Morisita's index of "
    "dispersion; ADR 0612).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "morisita_dispersion.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(
            f"{out} is out of date: run python vectors/generators/morisita_dispersion.py"
        )
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
