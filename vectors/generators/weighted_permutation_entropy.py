"""Writes vectors/cases/weighted_permutation_entropy.json, stdlib only.

Weighted permutation entropy (conventions: Weighted permutation entropy; ADR 0343): each
window's pattern by sorting (value, index) pairs, its population variance and the pattern
probabilities exact in rationals, then -sum p ln p / ln(order!) in float.

Run from the repo root: python vectors/generators/weighted_permutation_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def add(cid, x, m, tau, why):
    q = [Fr(v) for v in x]
    windows = len(q) - (m - 1) * tau
    sums = {}
    for i in range(windows):
        w = [q[i + l * tau] for l in range(m)]
        mean = sum(w, Fr(0)) / m
        weight = sum(((v - mean) ** 2 for v in w), Fr(0)) / m
        pattern = tuple(l for _, l in sorted((v, l) for l, v in enumerate(w)))
        sums[pattern] = sums.get(pattern, Fr(0)) + weight
    total = sum(sums.values(), Fr(0))
    p = [s / total for s in sums.values() if s > 0]
    v = -math.fsum(float(u) * math.log(u) for u in p) / math.log(math.factorial(m))
    args = {"samples": x, "order": m}
    if tau != 1:
        args["delay"] = tau
    cases.append({"id": f"weighted_permutation_entropy.{cid}",
                  "op": "weighted_permutation_entropy", "args": args, "expected": v,
                  "tol": TOL, "source": why})
    return v


v = add("ramp", [float(i) for i in range(10)], 3, 1, "a ramp: one pattern, so 0")
assert v == 0.0
v = add("two_patterns", [0.0, 1.0, 0.0, 3.0, 0.0], 2, 1, "windows (0,1), (1,0), (0,3), (3,0): "
        "weights 1/4, 1/4, 9/4, 9/4, so p = 1/2 each and the value is 1")
assert v == 1.0, v
v = add("weights_matter", [0.0, 1.0, 0.0, 5.0], 2, 1, "rising windows weigh 1/4 + 25/4, the "
        "falling one 1/4: p = 26/27 and 1/27")
assert abs(v - -(26 / 27 * math.log(26 / 27) + 1 / 27 * math.log(1 / 27)) / math.log(2)) < 1e-15
add("ties", [1.0, 1.0, 2.0, 1.0, 1.0, 0.5, 0.5, 3.0, 1.0], 3, 1, "ties broken by index")
rng = random.Random(343)
add("noise", [rng.randint(-40, 40) / 8 for _ in range(120)], 4, 2,
    "120 random eighths from random.Random(343), order 4, delay 2")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "order": 2}
    base.update(args)
    cases.append({"id": f"weighted_permutation_entropy.{cid}",
                  "op": "weighted_permutation_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("order_one", "order must be at least 2", order=1)
err("order_nine", "order must be at most 8", order=9)
err("delay_zero", "delay must be at least 1", delay=0)
err("too_short", "no window fits", order=3, delay=3)
err("constant", "no window varies", samples=[2.0, 2.0, 2.0, 2.0])
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "weighted_permutation_entropy",
    "description": "Weighted permutation entropy (conventions: Weighted permutation entropy; "
                   "ADR 0343).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "weighted_permutation_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/weighted_permutation_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
