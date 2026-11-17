"""Writes vectors/cases/median_filter.json, stdlib only.

Running median filter (conventions: Running median filter; ADR 0234). Each expected output is
the middle element of the sorted window x[n - w ... n + w], w = min(h, n, L - 1 - n): exact,
since it is one of the inputs.

Run from the repo root: python vectors/generators/median_filter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

cases = []


def med(x, length):
    h = (length - 1) // 2
    n = len(x)
    out = []
    for i in range(n):
        w = min(h, i, n - 1 - i)
        out.append(sorted(x[i - w : i + w + 1])[w])
    return out


def add(cid, x, length, why):
    y = med(x, length)
    cases.append({"id": f"median_filter.{cid}", "op": "median_filter",
                  "args": {"samples": x, "length": length}, "expected": y,
                  "tol": {"abs": 0.0, "rel": 0.0}, "source": why})
    return y


y = add("spike", [1.0, 1.0, 9.0, 1.0, 1.0, 1.0], 3, "a lone spike is removed")
assert y == [1.0] * 6
y = add("step", [0.0, 0.0, 0.0, 5.0, 5.0, 5.0], 5, "a step edge is kept sharp")
assert y == [0.0, 0.0, 0.0, 5.0, 5.0, 5.0]
add("mixed", [3.0, -1.0, 4.0, 1.0, -5.0, 9.0, 2.0, -6.0, 5.0, 3.0, -5.0, 8.0], 5,
    "length 5 on mixed data: shrinking windows at the ends")
add("long_window", [2.0, 7.0, 1.0, 8.0], 9, "window longer than the data")
y = add("length_one", [0.5, -0.25, 3.0], 1, "length 1: the samples themselves")
assert y == [0.5, -0.25, 3.0]
add("single_sample", [4.0], 7, "one sample")
add("ties", [1.0, 2.0, 2.0, 2.0, 1.0, 1.0, 3.0], 3, "repeated values")


def err(cid, why, **args):
    cases.append({"id": f"median_filter.{cid}", "op": "median_filter", "args": args,
                  "error": "invalid_argument", "source": why})


err("even_length", "length must be odd", samples=[1.0, 2.0], length=4)
err("zero_length", "length must be at least 1", samples=[1.0], length=0)
err("empty", "samples must not be empty", samples=[], length=3)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], length=3)

doc = {
    "schema": 1,
    "suite": "median_filter",
    "description": "Running median filter (conventions: Running median filter; ADR 0234).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "median_filter.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/median_filter.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
