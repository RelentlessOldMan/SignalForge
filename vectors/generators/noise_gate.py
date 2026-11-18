"""Writes vectors/cases/noise_gate.json, stdlib only.

Noise gate (conventions: Noise gate; ADR 0255). The expected values come from the counter
definition (c from hold + 1; |x| > threshold resets it to 0, otherwise it rises, capped at
hold + 1; pass x while c <= hold), exact since each output is x or 0. Complex cases use 3-4-5
magnitudes.

Run from the repo root: python vectors/generators/noise_gate.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def gate(mags, th, hold):
    keep, c = [], hold + 1
    for m in mags:
        c = 0 if m > th else min(c + 1, hold + 1)
        keep.append(c <= hold)
    return keep


def add(cid, x, th, why, hold=None):
    k = gate([abs(v) for v in x], th, hold or 0)
    args = {"samples": x, "threshold": th}
    if hold is not None:
        args["hold"] = hold
    y = [v if kk else 0.0 for v, kk in zip(x, k)]
    cases.append({"id": f"noise_gate.{cid}", "op": "noise_gate", "args": args, "expected": y,
                  "tol": TOL, "source": why})
    return y


y = add("no_hold", [0.25, 1.5, -0.5, -2.0, 1.0, 0.75, 3.0], 1.0,
        "hold 0: only samples above 1 pass; 1.0 itself does not")
assert y == [0.0, 1.5, 0.0, -2.0, 0.0, 0.0, 3.0]
y = add("hold_bridges", [2.0, 0.5, 0.25, 0.125, 3.0, 0.5, 0.25, 0.125, 0.0625], 1.0,
        "hold 2: two quiet samples pass after each loud one, the third is cut", hold=2)
assert y == [2.0, 0.5, 0.25, 0.0, 3.0, 0.5, 0.25, 0.0, 0.0]
y = add("starts_closed", [0.5, 0.5, 1.5, 0.5], 1.0, "hold 3: closed until the first loud sample",
        hold=3)
assert y == [0.0, 0.0, 1.5, 0.5]
add("threshold_zero", [0.0, -0.0, 0.125, 0.0, 0.0], 0.0, "threshold 0: any nonzero opens",
    hold=1)

re = [0.375, 3.0, 0.0, -0.375, 0.375]
im = [0.5, 4.0, 0.5, 0.5, -0.5]
mags = [0.625, 5.0, 0.5, 0.625, 0.625]
k = gate(mags, 1.0, 1)
assert k == [False, True, True, False, False]
cases.append({"id": "noise_gate.complex", "op": "noise_gate",
              "args": {"samples": {"re": re, "im": im}, "threshold": 1.0, "hold": 1},
              "expected": {"re": [v if kk else 0.0 for v, kk in zip(re, k)],
                           "im": [v if kk else 0.0 for v, kk in zip(im, k)]},
              "tol": TOL,
              "source": "complex by magnitude: |x| = 5/8, 5, 1/2, 5/8, 5/8 against 1, hold 1"})


def err(cid, why, **args):
    cases.append({"id": f"noise_gate.{cid}", "op": "noise_gate", "args": args,
                  "error": "invalid_argument", "source": why})


err("threshold_negative", "threshold must be at least 0", samples=[1.0], threshold=-1.0)
err("hold_negative", "hold must be at least 0", samples=[1.0], threshold=0.5, hold=-1)
err("empty", "samples must not be empty", samples=[], threshold=0.5)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], threshold=0.5)

doc = {
    "schema": 1,
    "suite": "noise_gate",
    "description": "Noise gate (conventions: Noise gate; ADR 0255).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "noise_gate.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/noise_gate.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
