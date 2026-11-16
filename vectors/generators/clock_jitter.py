"""Writes vectors/cases/clock_jitter.json by hand, using only the Python standard library.

The random streams differ between languages, so the only shared cases are those that do not
depend on the seed (conventions: Channel, Sample clock jitter; ADR 0104): with rms = 0 every read
is on the grid, where the kernel gives the sample itself, and the rejected arguments. The
statistics of real jitter are checked by the tests in both languages.

Run from the repo root: python vectors/generators/clock_jitter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

cases = []
OP = "clock_jitter"


def C(xs):
    return {"re": [complex(z).real for z in xs], "im": [complex(z).imag for z in xs]}


X = [complex(math.cos(0.7 * n) + 0.1 * n, math.sin(0.3 * n * n) - 0.5) for n in range(12)]
ON_GRID = "by hand: rms = 0 reads every sample on the grid, where the kernel gives the sample"
for cid, args, want in (
    ("zero_rms_seed1", {"samples": C(X), "rms": 0.0, "seed": 1}, X),
    ("zero_rms_seed7_narrow", {"samples": C(X), "rms": 0.0, "seed": 7, "half_width": 3}, X),
    ("one_sample", {"samples": C([2 - 1j]), "rms": 0.0, "seed": 3}, [2 - 1j]),
    ("empty", {"samples": C([]), "rms": 0.25, "seed": 1}, []),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": args, "expected": C(want),
                  "tol": {"abs": 0, "rel": 0},
                  "source": ON_GRID if want else "by hand: no samples in, none out"})
for cid, change, why in (
    ("negative_rms", {"rms": -0.01}, "rms must not be negative"),
    ("rms_over_half", {"rms": 0.5000001}, "rms must be at most 0.5"),
    ("nan_rms", {"rms": "nan"}, "rms must be finite"),
    ("zero_half_width", {"half_width": 0}, "half_width must be at least 1"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": C(X[:4]), "rms": 0.1, "seed": 1} | change,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Sample clock jitter, the seed-independent cases (conventions: Channel, "
    "Sample clock jitter; ADR 0104).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / f"{OP}.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/{OP}.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
