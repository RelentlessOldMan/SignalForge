"""Writes vectors/cases/normalize_peak.json, stdlib only.

Peak normalization (conventions: Peak normalization; ADR 0268). g = peak / max |x|, y = x g, in
exact rationals; complex magnitudes are 3-4-5 binary fractions, so |x| is exact.

Run from the repo root: python vectors/generators/normalize_peak.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 1e-15, "rel": 1e-15}
cases = []


def add(cid, x, why, peak=None):
    g = Fr(peak if peak is not None else 1.0) / max(abs(Fr(v)) for v in x)
    y = [Fr(v) * g for v in x]
    args = {"samples": x}
    if peak is not None:
        args["peak"] = peak
    cases.append({"id": f"normalize_peak.{cid}", "op": "normalize_peak", "args": args,
                  "expected": [float(v) for v in y], "tol": TOL, "source": why})
    return y


y = add("unit", [0.5, -0.25, 0.125, 0.0], "peak 1: largest 0.5 scaled by 2")
assert y == [1, Fr(-1, 2), Fr(1, 4), 0]
y = add("negative_peak_sample", [0.5, -4.0, 2.0], "largest magnitude is negative: -1 after",
        peak=1.0)
assert y[1] == -1
add("half", [3.0, -1.5, 0.75], "peak 1/2", peak=0.5)
add("third", [1.0, 2.0, -3.0], "peak 1, gain 1/3: products round once", peak=1.0)
add("up", [0.001, -0.002], "small input scaled up to peak 8", peak=8.0)

re_, im_ = [0.375, 0.0, -0.1875], [0.5, 0.25, 0.25]
# |x| = 5/8, 1/4, 5/16; gain 1/(5/8) = 8/5
g = Fr(1) / Fr(5, 8)
cases.append({"id": "normalize_peak.complex", "op": "normalize_peak",
              "args": {"samples": {"re": re_, "im": im_}},
              "expected": {"re": [float(Fr(v) * g) for v in re_],
                           "im": [float(Fr(v) * g) for v in im_]},
              "tol": TOL, "source": "complex, largest |x| = 5/8 (3-4-5): first sample 0.6 + 0.8i"})


def err(cid, why, **args):
    base = {"samples": [1.0, -2.0], "peak": 1.0}
    base.update(args)
    cases.append({"id": f"normalize_peak.{cid}", "op": "normalize_peak", "args": base,
                  "error": "invalid_argument", "source": why})


err("peak_zero", "peak must be positive", peak=0.0)
err("peak_nan", "peak must be finite", peak="nan")
err("all_zero", "samples must not all be zero", samples=[0.0, 0.0])
err("empty", "samples must not be empty", samples=[])
err("inf_sample", "samples must be finite", samples=[1.0, "inf"])

doc = {
    "schema": 1,
    "suite": "normalize_peak",
    "description": "Peak normalization (conventions: Peak normalization; ADR 0268).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "normalize_peak.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/normalize_peak.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
