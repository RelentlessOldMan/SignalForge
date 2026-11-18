"""Writes vectors/cases/rectify.json, stdlib only.

Rectifier (conventions: Rectifier; ADR 0253). The expected values come from the definition
(full wave |x|, half wave x if x > 0 else 0), exact.

Run from the repo root: python vectors/generators/rectify.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 0.0, "rel": 0.0}
cases = []
X = [-2.5, -1.0, -0.125, 0.0, 0.375, 1.0, 3.25]


def add(cid, x, full, why):
    y = [abs(v) if full is not False else (v if v > 0 else 0.0) for v in x]
    args = {"samples": x}
    if full is not None:
        args["full"] = full
    cases.append({"id": f"rectify.{cid}", "op": "rectify", "args": args,
                  "expected": [v + 0.0 for v in y], "tol": TOL, "source": why})
    return y


y = add("default_full", X, None, "default: full wave |x|")
assert y == [2.5, 1.0, 0.125, 0.0, 0.375, 1.0, 3.25]
add("full", X, True, "full wave |x|")
y = add("half", X, False, "half wave: x if x > 0 else 0")
assert y == [0.0, 0.0, 0.0, 0.0, 0.375, 1.0, 3.25]


def err(cid, why, **args):
    cases.append({"id": f"rectify.{cid}", "op": "rectify", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty", "samples must not be empty", samples=[])
err("nan_sample", "samples must be finite", samples=[1.0, "nan"])

doc = {
    "schema": 1,
    "suite": "rectify",
    "description": "Rectifier (conventions: Rectifier; ADR 0253).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "rectify.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/rectify.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
