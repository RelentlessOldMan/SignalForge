"""Writes vectors/cases/bubble_entropy.json, stdlib only.

Bubble entropy (conventions: Bubble entropy; ADR 0345): each window's swap count by running an
ascending bubble sort on it (equal values not swapped); sum p^2 exact in rationals; then
H = -ln sum p^2 and (H_{m+1} - H_m) / ln((m + 1)/(m - 1)) in float.

Run from the repo root: python vectors/generators/bubble_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from collections import Counter
from fractions import Fraction as Fr

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def bubble_swaps(w):
    w = list(w)
    swaps = 0
    for end in range(len(w) - 1, 0, -1):
        for j in range(end):
            if w[j] > w[j + 1]:
                w[j], w[j + 1] = w[j + 1], w[j]
                swaps += 1
    assert w == sorted(w)
    return swaps


def renyi(x, k):
    windows = len(x) - k + 1
    counts = Counter(bubble_swaps(x[i:i + k]) for i in range(windows))
    return -math.log(sum((Fr(c, windows) ** 2 for c in counts.values()), Fr(0)))


def add(cid, x, m, why):
    v = (renyi(x, m + 1) - renyi(x, m)) / math.log((m + 1) / (m - 1))
    cases.append({"id": f"bubble_entropy.{cid}", "op": "bubble_entropy",
                  "args": {"samples": x, "m": m}, "expected": v, "tol": TOL, "source": why})
    return v


v = add("ramp", [float(i) for i in range(10)], 2, "a ramp: every window has 0 swaps, so 0")
assert v == 0.0
v = add("alternating", [0.0, 1.0] * 5, 2, "0, 1 alternating: m = 2 swaps 0, 1 in turn; m = 3 "
        "windows (0,1,0) and (1,0,1) both have one swap")
assert abs(v - math.log(Fr(41, 81)) / math.log(3)) < 1e-15, v
add("ties", [1.0, 1.0, 2.0, 1.0, 1.0, 0.5, 0.5, 3.0, 1.0, 2.0], 3, "ties are not swapped")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75, 0.1,
              1.5, -0.75, 2.0, 0.5, -1.0], 4, "eighteen arbitrary samples, m = 4")
rng = random.Random(345)
add("noise", [rng.randint(-50, 50) / 8 for _ in range(150)], 10, "150 random eighths from "
    "random.Random(345), m = 10")
add("shortest", [3.0, 1.0, 2.0], 2, "three samples, m = 2: windows of 3 are one")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0, 1.5], "m": 2}
    base.update(args)
    cases.append({"id": f"bubble_entropy.{cid}", "op": "bubble_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("m_one", "m must be at least 2", m=1)
err("m_65", "m must be at most 64", m=65)
err("too_short", "samples must be at least m + 1 long", m=5)
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "bubble_entropy",
    "description": "Bubble entropy (conventions: Bubble entropy; ADR 0345).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "bubble_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/bubble_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
