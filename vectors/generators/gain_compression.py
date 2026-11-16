"""Writes vectors/cases/gain_compression.json by hand arithmetic, using only the Python standard
library.

It does not import NumPy or SignalForge. The piecewise sweeps are chosen so every gain,
compression and interpolated point is a round number written out below. The cubic sweep's levels
come from the fundamental of y = a1 x + a3 x^3 on a tone, a1 A + (3/4) a3 A^3, and its points
follow ADR 0112's rule step by step.

Run from the repo root: python vectors/generators/gain_compression.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}


def case(case_id, args, gss, gain, comp, point, out_point, sat, src):
    return {"id": case_id, "op": "gain_compression", "args": args,
            "expected": {"small_signal_gain_db": gss, "gain_db": gain, "compression": comp,
                         "input_point_db": point, "output_point_db": out_point,
                         "saturated_output_db": sat},
            "tol": TOL, "source": src}


def err(case_id, args, why):
    return {"id": case_id, "op": "gain_compression", "args": args, "error": "invalid_argument",
            "source": why}


# Gain 10 dB up to -20 dBm in, then 9.5, 9, 7, 4: compression 0, 0, 0, 0.5, 1, 3, 6.
x = [-30.0, -25.0, -20.0, -15.0, -10.0, -5.0, 0.0]
y = [-20.0, -15.0, -10.0, -5.5, -1.0, 2.0, 4.0]
g = [10.0, 10.0, 10.0, 9.5, 9.0, 7.0, 4.0]
c = [0.0, 0.0, 0.0, 0.5, 1.0, 3.0, 6.0]

# A noisy small-signal reading: gains 10.25, 9.75, 10 average to 10.
xn = [-30.0, -20.0, -10.0, 0.0]
yn = [-19.75, -10.25, 0.0, 8.0]
gn = [10.25, 9.75, 10.0, 8.0]
cn = [10.0 - v for v in gn]

# The cubic: a1 = 10, a3 = -1, drive amplitudes 10^(d/20) for d = -20, -18, ..., 4.
a1, a3 = 10.0, -1.0
xc = [float(d) for d in range(-20, 6, 2)]
yc = []
for d in xc:
    amp = 10 ** (d / 20)
    yc.append(20 * math.log10(a1 * amp + 0.75 * a3 * amp**3))
gc = [yv - xv for xv, yv in zip(xc, yc)]
cc = [gc[0] - v for v in gc]
k = next(i for i, v in enumerate(cc) if v >= 1.0)
pc = xc[k - 1] + (1.0 - cc[k - 1]) / (cc[k] - cc[k - 1]) * (xc[k] - xc[k - 1])

cases = [
    case("gain_compression.p1db", {"input_db": x, "output_db": y},
         10.0, g, c, -10.0, -1.0, 4.0,
         "by hand: compression first reaches 1 dB at -10 dBm in, exactly a step; output "
         "-10 + 10 - 1 = -1; the largest output is 4"),
    case("gain_compression.p2db_between_steps", {"input_db": x, "output_db": y,
                                                  "compression_db": 2.0},
         10.0, g, c, -7.5, 0.5, 4.0,
         "by hand: 2 dB lies between 1 at -10 and 3 at -5, halfway: -7.5 in, output "
         "-7.5 + 10 - 2 = 0.5"),
    case("gain_compression.p05db_from_the_first_rise", {"input_db": x, "output_db": y,
                                                         "compression_db": 0.25},
         10.0, g, c, -17.5, -7.75, 4.0,
         "by hand: 0.25 dB lies halfway between 0 at -20 and 0.5 at -15: -17.5 in, output "
         "-17.5 + 10 - 0.25 = -7.75"),
    case("gain_compression.not_reached", {"input_db": x, "output_db": y,
                                          "compression_db": 7.0},
         10.0, g, c, "nan", "nan", 4.0,
         "by hand: the compression never reaches 7 dB (6 at most), so both points are NaN"),
    case("gain_compression.averaged_small_signal", {"input_db": xn, "output_db": yn,
                                                    "linear_points": 3},
         10.0, gn, cn, -5.0, 4.0, 8.0,
         "by hand: the first three gains 10.25, 9.75, 10 average to 10, so the compressions "
         "are -0.25, 0.25, 0, 2; 1 dB lies halfway between 0 at -10 and 2 at 0: -5 in, output "
         "-5 + 10 - 1 = 4"),
    case("gain_compression.reached_at_the_first_step", {"input_db": [-20.0, -10.0, 0.0],
                                                        "output_db": [-11.0, 1.0, 10.0],
                                                        "linear_points": 2},
         10.0, [9.0, 11.0, 10.0], [1.0, -1.0, 0.0], -20.0, -11.0, 10.0,
         "by hand: gains 9 and 11 average to 10, so the first step is already 1 dB down: the "
         "point is the first input, -20, output -20 + 10 - 1 = -11"),
    case("gain_compression.cubic", {"input_db": xc, "output_db": yc},
         gc[0], gc, cc, pc, pc + gc[0] - 1.0, max(yc),
         "by hand: levels from a1 A + (3/4) a3 A^3 with a1 = 10, a3 = -1, A = 10^(d/20); the "
         "point interpolates linearly in dB between the steps either side of 1 dB"),
    err("gain_compression.lengths_differ", {"input_db": x, "output_db": y[:-1]},
        "input_db and output_db need the same length"),
    err("gain_compression.one_step", {"input_db": [0.0], "output_db": [10.0]},
        "at least two steps required"),
    err("gain_compression.not_ascending", {"input_db": [-10.0, -10.0, 0.0],
                                           "output_db": [0.0, 0.0, 9.0]},
        "input_db must be strictly ascending"),
    err("gain_compression.nan_output", {"input_db": [-10.0, 0.0], "output_db": [0.0, "nan"]},
        "levels must be finite"),
    err("gain_compression.compression_zero", {"input_db": x, "output_db": y,
                                              "compression_db": 0.0},
        "compression_db > 0 required"),
    err("gain_compression.linear_points_zero", {"input_db": x, "output_db": y,
                                                "linear_points": 0},
        "linear_points must be at least 1"),
    err("gain_compression.linear_points_too_many", {"input_db": x, "output_db": y,
                                                    "linear_points": 8},
        "linear_points must not exceed the number of steps (7)"),
]

doc = {
    "schema": 1,
    "suite": "gain_compression",
    "description": "Gain compression and the 1 dB point from a drive sweep (conventions: Gain "
                   "compression; ADR 0112).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "gain_compression.json"


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, int | float) and isinstance(b, int | float) and not isinstance(a, bool):
        return abs(a - b) <= 1e-14 * max(1.0, abs(b))
    return a == b


if "--check" in sys.argv[1:]:
    if not same(json.loads(out.read_text(encoding="utf-8")), json.loads(json.dumps(doc))):
        sys.exit(f"{out} is out of date: run python vectors/generators/gain_compression.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
