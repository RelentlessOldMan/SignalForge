"""Writes vectors/cases/attention_entropy.json, stdlib only.

Attention entropy (conventions: Attention entropy; ADR 0346): strict interior local maxima and
minima by a plain loop; the four interval sets (max-max, min-min, each max to the next min,
each min to the next max) by direct search; exact counts, then the mean of the four
-sum p ln p in float.

Run from the repo root: python vectors/generators/attention_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import random
import sys
from collections import Counter

TOL = {"abs": 1e-14, "rel": 1e-13}
cases = []


def shannon(gaps):
    n = len(gaps)
    return -math.fsum(c / n * math.log(c / n) for c in Counter(gaps).values())


def add(cid, x, why):
    peaks = [i for i in range(1, len(x) - 1) if x[i] > x[i - 1] and x[i] > x[i + 1]]
    troughs = [i for i in range(1, len(x) - 1) if x[i] < x[i - 1] and x[i] < x[i + 1]]
    sets = [
        [b - a for a, b in zip(peaks, peaks[1:])],
        [b - a for a, b in zip(troughs, troughs[1:])],
        [min(t for t in troughs if t > p) - p for p in peaks if any(t > p for t in troughs)],
        [min(p for p in peaks if p > t) - t for t in troughs if any(p > t for p in peaks)],
    ]
    assert all(sets), sets
    v = math.fsum(shannon(s) for s in sets) / 4
    cases.append({"id": f"attention_entropy.{cid}", "op": "attention_entropy",
                  "args": {"samples": x}, "expected": v, "tol": TOL, "source": why})
    return sets, v


sets, v = add("zigzag", [0.0, 1.0] * 6, "0, 1 alternating: every interval is 2 or 1, one "
              "length per set, so 0")
assert v == 0.0
sets, v = add("two_lengths", [0.0, 2.0, 1.0, 3.0, 0.0, 0.0, 4.0, 1.0, 5.0, 0.0], "maxima at "
              "1, 3, 6, 8 and minima at 2, 7 (the plateau at 4, 5 is neither)")
assert sets[0] == [2, 3, 2] and sets[1] == [5], sets
add("plateaus", [1.0, 1.0, 3.0, 2.0, 2.0, 0.0, 4.0, 4.0, 1.0, 5.0, 0.5, 2.0, -1.0, 3.0],
    "plateaus at peaks and troughs are not key points")
rng = random.Random(346)
add("noise", [rng.randint(-20, 20) / 4 for _ in range(200)], "200 random quarters from "
    "random.Random(346)")


def err(cid, why, samples):
    cases.append({"id": f"attention_entropy.{cid}", "op": "attention_entropy",
                  "args": {"samples": samples}, "error": "invalid_argument", "source": why})


err("ramp", "a ramp has no key points", [0.0, 1.0, 2.0, 3.0, 4.0])
err("one_peak", "one maximum gives no max-to-max interval", [0.0, 2.0, 1.0, 3.0, 4.0])
err("short", "two samples have no interior", [0.0, 1.0])
err("inf", "samples must be finite", [0.0, "inf", 1.0, 2.0])

doc = {
    "schema": 1,
    "suite": "attention_entropy",
    "description": "Attention entropy (conventions: Attention entropy; ADR 0346).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "attention_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/attention_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
