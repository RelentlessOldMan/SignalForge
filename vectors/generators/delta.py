"""Writes vectors/cases/delta.json, stdlib only.

HTK delta coefficients (conventions: Delta coefficients; ADR 0158), computed exactly with
fractions.Fraction from d_t = sum_n n (c[t+n] - c[t-n]) / (2 sum n^2), indices clamped to the
first and last frames. The generator checks the hand-worked ramp values.

Run from the repo root: python vectors/generators/delta.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from fractions import Fraction as F

TOL = {"abs": 1e-14, "rel": 1e-14}
cases = []


def delta(frames, width):
    c = [[F(v) for v in row] for row in frames]
    last = len(c) - 1
    norm = 2 * sum(n * n for n in range(1, width + 1))
    return [[sum(n * (c[min(t + n, last)][j] - c[max(t - n, 0)][j]) for n in range(1, width + 1))
             / norm for j in range(len(c[0]))] for t in range(len(c))]


def case(cid, frames, width, why, hand=None):
    out = delta(frames, width)
    if hand is not None:
        assert out == [[F(v) for v in row] for row in hand], (cid, out)
    args = {"frames": frames}
    if width != 2:
        args["width"] = width
    cases.append({"id": f"delta.{cid}", "op": "delta", "args": args,
                  "expected": [[float(v) for v in row] for row in out], "tol": TOL,
                  "source": why})


RAMP = [[float(t), 2.0 * t + 1] for t in range(6)]
case("ramp_width1", RAMP, 1,
     "c_t = (t, 2t+1), W = 1: (c[t+1] - c[t-1])/2 = slope inside, half slope at each end",
     [[F(1, 2), 1], [1, 2], [1, 2], [1, 2], [1, 2], [F(1, 2), 1]])
case("ramp_width2", RAMP, 2,
     "W = 2, norm 10: interior slope; t = 0 gives (1*1 + 2*2)/10 = 1/2, t = 1 gives "
     "(1*2 + 2*3)/10 = 4/5 for the first column",
     [[F(1, 2), 1], [F(4, 5), F(8, 5)], [1, 2], [1, 2], [F(4, 5), F(8, 5)], [F(1, 2), 1]])
case("single_frame", [[3.0, -1.0, 7.0]], 2, "one frame: every clamped difference is 0",
     [[0, 0, 0]])
case("wide", [[0.0], [1.0], [4.0]], 5,
     "W = 5 over 3 frames, norm 110: every index beyond the ends clamps; exact fractions")
case("alternating", [[1.0], [-1.0], [1.0], [-1.0], [1.0]], 1,
     "an alternating sequence with W = 1: c[t+1] = c[t-1] inside, so 0; the ends are -1 and 1",
     [[-1], [0], [0], [0], [1]])


def err(cid, args, why):
    cases.append({"id": f"delta.{cid}", "op": "delta", "args": args, "error": "invalid_argument",
                  "source": why})


err("no_frames", {"frames": []}, "needs at least one frame")
err("empty_frame", {"frames": [[]]}, "needs at least one value per frame")
err("nan", {"frames": [[1.0], ["nan"]]}, "values must be finite")
err("zero_width", {"frames": [[1.0], [2.0]], "width": 0}, "width must be at least 1")

doc = {
    "schema": 1,
    "suite": "delta",
    "description": "HTK delta coefficients (conventions: Delta coefficients; ADR 0158).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "delta.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/delta.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
