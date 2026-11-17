"""Writes vectors/cases/schmitt_trigger.json, stdlib only.

Schmitt trigger (conventions: Schmitt trigger; ADR 0244). The expected states come from the
definition (state from 0; above high sets it, below low clears it, otherwise it is held, and a
sample exactly on a threshold holds it), with binary-fraction samples so every comparison is exact.

Run from the repo root: python vectors/generators/schmitt_trigger.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

cases = []


def run(x, lo, hi):
    out, state = [], 0
    for v in x:
        if v > hi:
            state = 1
        elif v < lo:
            state = 0
        out.append(state)
    return out


def add(cid, x, lo, hi, why):
    y = run(x, lo, hi)
    cases.append({"id": f"schmitt_trigger.{cid}", "op": "schmitt_trigger",
                  "args": {"samples": x, "low": lo, "high": hi}, "expected": y,
                  "tol": {"abs": 0.0, "rel": 0.0}, "source": why})
    return y


y = add("noisy_edge",
        [0.0, 0.375, 0.625, 0.4375, 0.5625, 1.25, 0.875, 0.4375, 0.625, -0.125, 0.25, -0.625, 0.25],
        -0.5, 0.5, "high at the first sample above 0.5, held through chatter until -0.625")
assert y == [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]
y = add("on_thresholds", [1.0, 2.0, 1.0, -1.0, 2.25, -1.0, -1.25, 2.0], -1.0, 2.0,
        "a sample exactly on a threshold holds the state")
assert y == [0, 0, 0, 0, 1, 1, 0, 0]
y = add("never_high", [0.25, -0.75, 0.5, 0.0], 0.0, 1.0, "never above high: all 0")
assert y == [0, 0, 0, 0]
add("square", [3.0, 3.0, -3.0, -3.0, 3.0, 0.0, -3.0, 0.0], -1.0, 1.0, "a square wave and its mid value")


def err(cid, why, **args):
    cases.append({"id": f"schmitt_trigger.{cid}", "op": "schmitt_trigger", "args": args,
                  "error": "invalid_argument", "source": why})


err("equal_thresholds", "low must be below high", samples=[1.0], low=0.5, high=0.5)
err("reversed", "low must be below high", samples=[1.0], low=1.0, high=0.0)
err("empty", "samples must not be empty", samples=[], low=0.0, high=1.0)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], low=0.0, high=1.0)

doc = {
    "schema": 1,
    "suite": "schmitt_trigger",
    "description": "Schmitt trigger (conventions: Schmitt trigger; ADR 0244).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "schmitt_trigger.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/schmitt_trigger.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
