"""Writes vectors/cases/sens_slope.json, stdlib only.

Sen's slope (conventions: Sen's slope; ADR 0365): every pairwise slope of dyadic samples and
their median exact in rationals.

Run from the repo root: python vectors/generators/sens_slope.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, why):
    q = [Fr(v) for v in x]
    s = sorted((q[j] - q[i]) / (j - i) for i in range(len(q)) for j in range(i + 1, len(q)))
    k = len(s)
    v = s[k // 2] if k % 2 else (s[k // 2 - 1] + s[k // 2]) / 2
    cases.append({"id": f"sens_slope.{cid}", "op": "sens_slope", "args": {"samples": x},
                  "expected": float(v), "tol": TOL, "source": why})
    return v


v = add("two_samples", [1.0, 4.0], "one slope of 3")
assert v == 3
v = add("outlier_by_hand", [0.0, 1.0, 2.0, 30.0],
        "slopes 1, 1, 10, 1, 29/2, 28: sorted 1, 1, 1, 10, 29/2, 28; median (1 + 10)/2 = 11/2")
assert v == Fr(11, 2)
v = add("line_with_outlier", [0.5 * t for t in range(10)] + [100.0],
        "a line of slope 1/2 with one wild sample: 45 slopes are exactly 1/2 of 55, so 1/2")
assert v == Fr(1, 2)
v = add("odd_count", [3.0, 1.0, 2.0],
        "slopes -2, -1/2, 1: median -1/2")
assert v == Fr(-1, 2)
rng = random.Random(365)
add("trend_in_noise", [t / 16 + rng.randint(-30, 30) / 8 for t in range(120)],
    "a ramp of 1/16 per sample plus random eighths from random.Random(365)")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5]}
    base.update(args)
    cases.append({"id": f"sens_slope.{cid}", "op": "sens_slope", "args": base,
                  "error": "invalid_argument", "source": why})


err("one_sample", "N must be at least 2", samples=[1.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "sens_slope",
    "description": "Sen's slope (conventions: Sen's slope; ADR 0365).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "sens_slope.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/sens_slope.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
