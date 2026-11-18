"""Writes vectors/cases/sample_entropy.json, stdlib only.

Sample entropy (conventions: Sample entropy; ADR 0326): L = N - m template starts; pairs i < l
match when max_j |x[i+j] - x[l+j]| <= r, counted exactly in rationals for lengths m (B) and
m + 1 (A); -ln(A/B) in float, +inf when A = 0. The samples are dyadic, so float differences
are exact too.

Run from the repo root: python vectors/generators/sample_entropy.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def counts(x, m, r):
    q = [Fr(v) for v in x]
    rr = Fr(r)
    starts = len(q) - m
    b = a = 0
    for i in range(starts - 1):
        for j in range(i + 1, starts):
            if max(abs(q[i + k] - q[j + k]) for k in range(m)) <= rr:
                b += 1
                if abs(q[i + m] - q[j + m]) <= rr:
                    a += 1
    return a, b


def add(cid, x, m, r, why):
    assert all(Fr(v).denominator & (Fr(v).denominator - 1) == 0 for v in x)
    a, b = counts(x, m, r)
    value = "inf" if a == 0 else -math.log(a / b)
    cases.append({"id": f"sample_entropy.{cid}", "op": "sample_entropy",
                  "args": {"samples": x, "m": m, "r": r}, "expected": value, "tol": TOL,
                  "source": why})
    return a, b


got = add("periodic", [0.0, 1.0] * 5, 2, 0.25, "a period-2 wave: every pair of equal phase "
          "matches at m and m+1; A = B, SampEn 0")
assert got[0] == got[1] == 12, got
got = add("by_hand", [1.0, 2.0, 1.0, 3.0, 1.0, 2.0], 1, 0.5,
          "m = 1, r = 1/2: starts 0..4 are 1,2,1,3,1; B = 3 pairs of 1s, of which A = 1 "
          "(0,4: next 2,2); SampEn ln 3")
assert got == (1, 3), got
got = add("at_r", [0.0, 0.5, 1.0, 0.0, 0.5, 1.5], 1, 0.5,
          "a distance exactly r = 1/2 matches")
add("no_extension", [0.0, 1.0, 0.0, 2.0, 0.0, 3.0], 1, 0.25,
    "the 0s match at m = 1 but their successors 1, 2 do not: A = 0, +inf")
add("mixed", [0.25, -1.5, 3.0, 2.75, -0.5, 0.125, 1.0, -2.25, 0.375, 2.5, -1.25, 0.75,
              0.0, 1.5, -0.75, 2.0, 0.5, -1.0, 1.25, 0.625], 2, 1.25,
    "twenty arbitrary dyadic samples, m = 2, r = 5/4")


def err(cid, why, **args):
    base = {"samples": [0.0, 1.0, 0.0, 1.0, 0.0], "m": 1, "r": 0.5}
    base.update(args)
    cases.append({"id": f"sample_entropy.{cid}", "op": "sample_entropy", "args": base,
                  "error": "invalid_argument", "source": why})


err("m_zero", "m must be at least 1", m=0)
err("r_negative", "r must be at least 0", r=-0.1)
err("too_short", "3 samples with m = 2 give one template", samples=[0.0, 1.0, 2.0], m=2)
err("no_match", "no two templates match at m: B = 0", samples=[0.0, 1.0, 2.0, 3.0], r=0.5)
err("nan", "samples must be finite", samples=[0.0, "nan", 1.0])

doc = {
    "schema": 1,
    "suite": "sample_entropy",
    "description": "Sample entropy (conventions: Sample entropy; ADR 0326).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "sample_entropy.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/sample_entropy.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
