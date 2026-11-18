"""Writes vectors/cases/mtie.json, stdlib only.

Maximum time interval error (conventions: Maximum time interval error; ADR 0337): for each n,
tau = n tau0 and MTIE = max over k of (max - min of x[k..k+n]), the extremes exact in
rationals and the difference rounded once to float.

Run from the repo root: python vectors/generators/mtie.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as Fr

TOL = {"abs": 0.0, "rel": 1e-15}
cases = []


def add(cid, x, tau0, sizes, why):
    q = [Fr(v) for v in x]
    values = []
    for n in sizes:
        values.append(float(max(max(q[k:k + n + 1]) - min(q[k:k + n + 1])
                                for k in range(len(q) - n))))
    expected = {"taus": [float(n * Fr(tau0)) for n in sizes], "values": values}
    cases.append({"id": f"mtie.{cid}", "op": "mtie",
                  "args": {"time_error": x, "sample_interval": tau0, "window_sizes": sizes},
                  "expected": expected, "tol": TOL, "source": why})
    return expected


e = add("ramp", [0.5 * i for i in range(10)], 1.0, [1, 4, 9], "a ramp of 0.5 per sample: "
        "MTIE = 0.5 n")
assert e["values"] == [0.5, 2.0, 4.5], e
e = add("step", [0.0] * 5 + [3.0] * 5, 0.25, [1, 3], "a step of 3: every window that holds "
        "it sees 3")
assert e["values"] == [3.0, 3.0], e
add("ns_wander", [v * 2**-30 for v in (0, 3, 1, -4, 2, 7, 5, -1, 0, 6, -3, 2)], 0.0625,
    [2, 5, 1, 11], "nanosecond-scale wander, sizes out of order")
add("spike", [0.0, 0.0, 0.0, 5.0, 0.0, 0.0, -1.0, 0.0], 1e-3, [1, 2, 3], "a single spike "
    "and a dip three samples later")


def err(cid, why, **args):
    base = {"time_error": [0.0, 1.0, 0.5, 2.0], "sample_interval": 1.0, "window_sizes": [1]}
    base.update(args)
    cases.append({"id": f"mtie.{cid}", "op": "mtie", "args": base,
                  "error": "invalid_argument", "source": why})


err("size_zero", "each window size must be at least 1", window_sizes=[0])
err("size_too_big", "each window size must be at most N - 1", window_sizes=[4])
err("no_sizes", "window_sizes must not be empty", window_sizes=[])
err("interval_negative", "sample_interval must be positive", sample_interval=-1.0)
err("one_sample", "at least 2 samples", time_error=[1.0])

doc = {
    "schema": 1,
    "suite": "mtie",
    "description": "Maximum time interval error (conventions: Maximum time interval error; "
                   "ADR 0337).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "mtie.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/mtie.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
