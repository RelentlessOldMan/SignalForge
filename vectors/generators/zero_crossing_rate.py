"""Writes vectors/cases/zero_crossing_rate.json, stdlib only.

Each case's crossings are counted by hand (conventions: Zero-crossing rate; ADR 0146): a sample
is positive when `x >= 0`, and the rate is the number of sign changes over `N - 1`. The
generator checks each hand count against that rule.

Run from the repo root: python vectors/generators/zero_crossing_rate.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def case(cid, samples, crossings, why):
    signs = [x >= 0 for x in samples]
    assert sum(a != b for a, b in zip(signs, signs[1:])) == crossings, cid
    cases.append({"id": f"zero_crossing_rate.{cid}", "op": "zero_crossing_rate",
                  "args": {"samples": samples},
                  "expected": float(F(crossings, len(samples) - 1)), "tol": TOL,
                  "source": why})


def err(cid, samples, why):
    cases.append({"id": f"zero_crossing_rate.{cid}", "op": "zero_crossing_rate",
                  "args": {"samples": samples}, "error": "invalid_argument", "source": why})


case("alternating", [1.0, -1.0, 1.0, -1.0], 3, "every pair changes sign: 3 of 3")
case("constant_sign", [1.0, 2.0, 3.0], 0, "no pair changes sign: 0 of 2")
case("zero_after_positive", [1.0, 0.0, -1.0], 1,
     "0 counts as positive, so only (0, -1) crosses: 1 of 2")
case("touch_from_below", [-1.0, 0.0, -1.0], 2,
     "0 counts as positive, so touching it from below crosses twice: 2 of 2")
case("touch_from_above", [1.0, 0.0, 1.0], 0, "0 counts as positive: no crossing")
case("negative_zero", [-0.0, -1.0], 1, "-0.0 >= 0, so it counts as positive: 1 of 1")
case("mixed", [3.0, -2.0, -5.0, 4.0, 4.0], 2, "crossings at (3, -2) and (-5, 4): 2 of 4")

err("one_sample", [1.0], "needs at least two samples")
err("empty", [], "needs at least two samples")
err("nan", [1.0, "nan"], "samples must be finite")
err("inf", ["inf", 1.0], "samples must be finite")

doc = {
    "schema": 1,
    "suite": "zero_crossing_rate",
    "description": "Zero-crossing rate (conventions: Zero-crossing rate; ADR 0146).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "zero_crossing_rate.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/zero_crossing_rate.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
