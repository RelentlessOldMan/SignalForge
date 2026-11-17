"""Writes vectors/cases/sample_and_hold.json, stdlib only.

Sample-and-hold (conventions: Sample-and-hold; ADR 0245). The expected values are written out by
hand from the index rule y[n] = x[offset + P floor((n - offset) / P)], zero before offset; they
are exact copies, so the tolerance is zero.

Run from the repo root: python vectors/generators/sample_and_hold.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 0.0, "rel": 0.0}
cases = []


def add(cid, x, period, expected, why, offset=None, im=None, expected_im=None):
    args = {"samples": x if im is None else {"re": x, "im": im}, "period": period}
    if offset is not None:
        args["offset"] = offset
    exp = expected if im is None else {"re": expected, "im": expected_im}
    cases.append({"id": f"sample_and_hold.{cid}", "op": "sample_and_hold", "args": args,
                  "expected": exp, "tol": TOL, "source": why})


add("period_three", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 3,
    [1.0, 1.0, 1.0, 4.0, 4.0, 4.0, 7.0, 7.0], "P = 3: x[0], x[3], x[6] each held 3 samples")
add("offset", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], 3,
    [0.0, 0.0, 3.0, 3.0, 3.0, 6.0, 6.0, 6.0], "P = 3, offset 2: zeros, then x[2], x[5]", offset=2)
add("period_one", [1.5, -2.0, 0.25], 1, [1.5, -2.0, 0.25], "P = 1: the input itself")
add("long_period", [-1.0, 2.0, 3.0, 4.0], 10, [-1.0, -1.0, -1.0, -1.0],
    "period longer than the input: x[0] throughout")
add("complex", [1.0, 2.0, 3.0, 4.0, 5.0], 2, [0.0, 2.0, 2.0, 4.0, 4.0], "complex, P = 2, offset 1",
    offset=1, im=[-1.0, -2.0, -3.0, -4.0, -5.0], expected_im=[0.0, -2.0, -2.0, -4.0, -4.0])


def err(cid, why, **args):
    cases.append({"id": f"sample_and_hold.{cid}", "op": "sample_and_hold", "args": args,
                  "error": "invalid_argument", "source": why})


err("period_zero", "period must be at least 1", samples=[1.0], period=0)
err("offset_too_large", "offset must be below period", samples=[1.0], period=2, offset=2)
err("offset_negative", "offset must be at least 0", samples=[1.0], period=2, offset=-1)
err("empty", "samples must not be empty", samples=[], period=2)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], period=2)

doc = {
    "schema": 1,
    "suite": "sample_and_hold",
    "description": "Sample-and-hold (conventions: Sample-and-hold; ADR 0245).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "sample_and_hold.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/sample_and_hold.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
