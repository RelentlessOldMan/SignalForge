"""Writes vectors/cases/saturate.json, stdlib only.

Tanh saturator (conventions: Tanh saturator; ADR 0259). The expected values come from the
definition tanh(drive x) / tanh(drive) with the stdlib math.tanh, an independent implementation.

Run from the repo root: python vectors/generators/saturate.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-15, "rel": 1e-13}
cases = []
X = [-3.0, -1.0, -0.5, -0.125, 0.0, 0.25, 0.75, 1.0, 2.5]


def add(cid, x, d, why):
    y = [math.tanh(d * v) / math.tanh(d) for v in x]
    cases.append({"id": f"saturate.{cid}", "op": "saturate", "args": {"samples": x, "drive": d},
                  "expected": y, "tol": TOL, "source": why})
    return y


for d in (0.5, 2.0, 8.0):
    y = add(f"drive_{d:g}".replace(".", "_"), X, d, f"drive {d:g}: tanh(d x)/tanh(d)")
    assert abs(y[7] - 1) < 1e-15 and abs(y[1] + 1) < 1e-15
y = add("gentle", [-0.5, 0.25, 1.0], 1e-6, "drive 1e-6: y close to x")
assert all(abs(a - b) < 1e-11 for a, b in zip(y, [-0.5, 0.25, 1.0]))
y = add("hard", [-1.0, -0.5, 0.5, 4.0], 40.0, "drive 40: tanh(d) = 1 to double precision")
assert y == [-1.0, -1.0, 1.0, 1.0]


def err(cid, why, **args):
    cases.append({"id": f"saturate.{cid}", "op": "saturate", "args": args,
                  "error": "invalid_argument", "source": why})


err("drive_zero", "drive must be positive", samples=[1.0], drive=0.0)
err("drive_inf", "drive must be finite", samples=[1.0], drive="inf")
err("empty", "samples must not be empty", samples=[], drive=1.0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], drive=1.0)

doc = {
    "schema": 1,
    "suite": "saturate",
    "description": "Tanh saturator (conventions: Tanh saturator; ADR 0259).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "saturate.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/saturate.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
