"""Writes vectors/cases/sine_fold.json, stdlib only.

Sine wavefolder (conventions: Sine wavefolder; ADR 0323): k = (pi / 2) drive, y = sin(k x),
with math.sin.

Run from the repo root: python vectors/generators/sine_fold.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
cases = []


def add(cid, x, drive, why):
    k = (math.pi / 2) * drive
    y = [math.sin(k * v) for v in x]
    cases.append({"id": f"sine_fold.{cid}", "op": "sine_fold",
                  "args": {"samples": x, "drive": drive}, "expected": y, "tol": TOL,
                  "source": why})
    return y


y = add("unit", [-1.0, -0.5, 0.0, 0.5, 1.0], 1.0, "drive 1: +-1 to +-1, +-1/2 to +-sqrt(2)/2")
assert y[0] == -1.0 and y[-1] == 1.0 and abs(y[3] - math.sqrt(0.5)) < 1e-15, y
y = add("one_fold", [0.25, 0.5, 0.75, 1.0], 2.0, "drive 2: the peak at 1/2, folded back to 0 "
        "at 1")
assert y[1] == 1.0 and abs(y[3]) < 1e-15, y
add("hot", [-0.9, -0.3, 0.1, 0.45, 0.8], 5.5, "drive 5.5: several folds")
add("gentle", [-2.0, 0.3, 1.7], 0.25, "drive 1/4: inputs beyond 1, still unfolded")


def err(cid, why, **args):
    base = {"samples": [0.5, -0.5], "drive": 1.0}
    base.update(args)
    cases.append({"id": f"sine_fold.{cid}", "op": "sine_fold", "args": base,
                  "error": "invalid_argument", "source": why})


err("drive_zero", "drive must be positive", drive=0.0)
err("no_samples", "samples must not be empty", samples=[])
err("sample_inf", "samples must be finite", samples=[0.5, "inf"])

doc = {
    "schema": 1,
    "suite": "sine_fold",
    "description": "Sine wavefolder (conventions: Sine wavefolder; ADR 0323).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "sine_fold.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/sine_fold.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
