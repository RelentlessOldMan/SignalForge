"""Writes vectors/cases/permutation_entropy.json, stdlib only.

Permutation entropy (conventions: Permutation entropy; ADR 0325): each window
x[i], x[i + delay], ... of order samples is reduced to its stable ascending sort order
(Python's sorted, so ties keep index order); the patterns are counted exactly and
H = -sum p ln p / ln(order!) taken in float.

Run from the repo root: python vectors/generators/permutation_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from collections import Counter

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def entropy(x, order, delay):
    windows = len(x) - (order - 1) * delay
    pats = Counter()
    for i in range(windows):
        v = [x[i + j * delay] for j in range(order)]
        pats[tuple(sorted(range(order), key=lambda j: v[j]))] += 1
    h = -sum((c / windows) * math.log(c / windows) for c in pats.values())
    return h / math.log(math.factorial(order))


def add(cid, x, order, why, delay=None):
    args = {"samples": x, "order": order}
    if delay is not None:
        args["delay"] = delay
    h = entropy(x, order, 1 if delay is None else delay)
    cases.append({"id": f"permutation_entropy.{cid}", "op": "permutation_entropy", "args": args,
                  "expected": h, "tol": TOL, "source": why})
    return h


h = add("rising", [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], 3, "a rising ramp: one pattern, H = 0")
assert h == 0.0, h
h = add("zigzag", [0.0, 1.0, 0.0, 1.0, 0.0], 2, "order 2 on 0,1,0,1,0: two rises, two falls, so "
        "H = ln 2 / ln 2 = 1")
assert h == 1.0, h
h = add("ties", [1.0, 1.0, 1.0, 2.0, 1.0], 2, "equal neighbours count as rising: 3 rises and "
        "1 fall, H = -(3/4 ln 3/4 + 1/4 ln 1/4) / ln 2")
assert abs(h - (-(0.75 * math.log(0.75) + 0.25 * math.log(0.25)) / math.log(2))) < 1e-15, h
add("order3", [4.0, 7.0, 9.0, 10.0, 6.0, 11.0, 3.0], 3, "the Bandt-Pompe example series, order "
    "3: 5 windows, patterns 012, 012, 201, 102, 201")
add("delay", [0.3, -1.2, 2.0, 0.7, -0.4, 1.1, 0.0, -2.5, 0.9, 1.6, -0.8, 0.2], 3,
    "twelve arbitrary samples, order 3, delay 2", delay=2)
add("order4", [math.sin(1.7 * n) + 0.1 * n for n in range(30)], 4,
    "30 samples of sin(1.7 n) + n/10, order 4")
add("one_window", [3.0, 1.0, 2.0], 3, "exactly one window: H = 0")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.5, 2.0], "order": 2}
    base.update(args)
    cases.append({"id": f"permutation_entropy.{cid}", "op": "permutation_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("order_one", "order must be at least 2", order=1)
err("order_nine", "order must be at most 8", order=9, samples=[float(n % 5) for n in range(20)])
err("delay_zero", "delay must be at least 1", delay=0)
err("too_short", "4 samples hold no window of order 3, delay 2", order=3, delay=2)
err("inf", "samples must be finite", samples=[0.0, "inf", 1.0])

doc = {
    "schema": 1,
    "suite": "permutation_entropy",
    "description": "Permutation entropy (conventions: Permutation entropy; ADR 0325).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "permutation_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/permutation_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
