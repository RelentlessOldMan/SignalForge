"""Writes vectors/cases/stutter.json, stdlib only.

Stutter (conventions: Stutter; ADR 0299), transcribed from the rule:
y[n] = x[start + (n - start) mod length] for start <= n < start + repeats length, x[n] elsewhere.

Run from the repo root: python vectors/generators/stutter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def add(cid, x, start, length, repeats, why):
    y = [x[start + (n - start) % length] if start <= n < start + repeats * length else x[n]
         for n in range(len(x))]
    cases.append({"id": f"stutter.{cid}", "op": "stutter",
                  "args": {"samples": x, "start": start, "length": length, "repeats": repeats},
                  "expected": y, "tol": TOL, "source": why})
    return y


X = [float(n + 1) for n in range(16)]
y = add("three", X, 2, 3, 3, "slice 3..5 three times from n = 2, then the input resumes")
assert y == [1.0, 2.0, 3.0, 4.0, 5.0, 3.0, 4.0, 5.0, 3.0, 4.0, 5.0] + X[11:]
add("past_end", X, 12, 3, 4, "the repeats run past the end and are cut off")
assert add("once", X, 4, 5, 1, "one repeat: the input") == X
assert add("none", X, 4, 5, 0, "no repeats: the input") == X
add("single_sample", X, 7, 1, 6, "a one-sample slice held for six samples")
add("start_past_end", X, 20, 2, 3, "a start past the end: the input")


def err(cid, why, **args):
    base = {"samples": [1.0, 2.0], "start": 0, "length": 1, "repeats": 2}
    base.update(args)
    cases.append({"id": f"stutter.{cid}", "op": "stutter", "args": base,
                  "error": "invalid_argument", "source": why})


err("length_zero", "length must be at least 1", length=0)
err("start_negative", "start must be at least 0", start=-1)
err("repeats_negative", "repeats must be at least 0", repeats=-1)
err("empty", "samples must not be empty", samples=[])

doc = {
    "schema": 1,
    "suite": "stutter",
    "description": "Stutter (conventions: Stutter; ADR 0299).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "stutter.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/stutter.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
