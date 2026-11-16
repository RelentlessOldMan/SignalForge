"""Writes vectors/cases/noise_figure.json by hand, using only the Python standard library.

Each case is the Y-factor formula worked by hand (conventions: Noise figure; ADR 0105):
T_h = T0*(1 + ENR), T_e = (T_h - Y*T_c)/(Y - 1), F = 1 + T_e/T0 with T0 = 290 K. That is the
definition of the noise temperature, not the rearranged form the code uses.

Run from the repo root: python vectors/generators/noise_figure.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys
from fractions import Fraction

OP = "noise_figure_y_factor"
T0 = 290
cases = []


def expected(y, enr, tc):
    """y, enr and tc exact (Fraction) where they can be; enr may be a float from a dB value."""
    th = T0 * (1 + enr)
    te = (th - y * tc) / (y - 1)
    f = 1 + te / T0
    return {"y_factor": float(y), "noise_factor": float(f),
            "noise_figure_db": 10 * math.log10(float(f)), "noise_temperature": float(te)}


F = Fraction
for cid, args, y, enr, why in (
    ("textbook_enr15_y10", {"hot_power": 10.0, "cold_power": 1.0, "enr_db": 15.0}, F(10),
     10 ** 1.5, "textbook: ENR 15 dB, Y 10 dB, T_c = T0: F = 10^1.5/9, NF about 5.46 dB"),
    ("ideal_y2_enr0", {"hot_power": 2.0, "cold_power": 1.0, "enr_db": 0.0}, F(2), F(1),
     "by hand: ENR 1, Y 2, T_c = T0: T_e = (580 - 580)/1 = 0, F = 1, NF 0 dB"),
    ("enr10_y3", {"hot_power": 6.0, "cold_power": 2.0, "enr_db": 10.0}, F(3), F(10),
     "by hand: ENR 10, Y 3: T_e = (3190 - 870)/2 = 1160 K, F = 5"),
    ("cold_half_t0", {"hot_power": 8.0, "cold_power": 2.0, "enr_db": 10.0,
                      "cold_temperature": 145.0}, F(4), F(10),
     "by hand: ENR 10, Y 4, T_c = 145 K: T_e = (3190 - 580)/3 = 870 K, F = 4"),
    ("cold_twice_t0", {"hot_power": 3.0, "cold_power": 1.5, "enr_db": 10.0,
                       "cold_temperature": 580.0}, F(2), F(10),
     "by hand: ENR 10, Y 2, T_c = 580 K: T_e = (3190 - 1160)/1 = 2030 K, F = 8"),
    ("liquid_nitrogen", {"hot_power": 3.2, "cold_power": 1.0, "enr_db": 5.0,
                         "cold_temperature": 77.0}, F(16, 5), 10 ** 0.5,
     "by hand: ENR 10^0.5, Y 3.2, T_c = 77 K, T_e = (290(1 + ENR) - 3.2*77)/2.2"),
    ("negative_enr_db", {"hot_power": 1.25, "cold_power": 1.0, "enr_db": -3.0}, F(5, 4),
     10 ** -0.3, "by hand: ENR 10^-0.3, Y 1.25, T_c = T0: F = ENR/0.25"),
    ("picowatts", {"hot_power": 4e-12, "cold_power": 1e-12, "enr_db": 10.0}, F(4), F(10),
     "by hand: only the ratio counts, Y 4 (to rounding), ENR 10: F = 10/3"),
    ("below_one", {"hot_power": 12.0, "cold_power": 1.0, "enr_db": 10.0}, F(12), F(10),
     "by hand: ENR 10, Y 12: F = 10/11 < 1, a negative T_e = -290/11 K, returned as it is"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": args, "expected": expected(y, enr, F(
        int(args.get("cold_temperature", T0)))), "tol": {"abs": 1e-12, "rel": 1e-12},
        "source": why})
base = {"hot_power": 10.0, "cold_power": 1.0, "enr_db": 15.0}
for cid, change, why in (
    ("y_one", {"hot_power": 1.0}, "Y must be above 1"),
    ("hot_below_cold", {"hot_power": 0.5}, "Y must be above 1"),
    ("cold_zero", {"cold_power": 0.0}, "cold_power must be positive"),
    ("cold_negative", {"cold_power": -1.0, "hot_power": 1.0}, "cold_power must be positive"),
    ("hot_nan", {"hot_power": "nan"}, "hot_power must be finite"),
    ("hot_inf", {"hot_power": "inf"}, "hot_power must be finite"),
    ("enr_inf", {"enr_db": "inf"}, "enr_db must be finite"),
    ("enr_overflows", {"enr_db": 4000.0}, "ENR = 10^400 overflows, so F is not finite"),
    ("y_overflows", {"hot_power": 1e300, "cold_power": 1e-300}, "Y overflows, so F is not finite"),
    ("cold_temperature_zero", {"cold_temperature": 0.0}, "cold_temperature must be positive"),
    ("cold_temperature_nan", {"cold_temperature": "nan"}, "cold_temperature must be finite"),
    ("negative_noise_factor", {"hot_power": 2.0, "enr_db": 0.0, "cold_temperature": 580.0},
     "by hand: ENR 1, Y 2, T_c = 2 T0: F = (1 - 2)/1 = -1"),
    ("zero_noise_factor", {"hot_power": 2.0, "enr_db": 0.0, "cold_temperature": 435.0},
     "by hand: ENR 1, Y 2, T_c = 1.5 T0: F = (1 - 1)/1 = 0"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": base | change,
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "noise_figure",
    "description": "Noise figure by the Y-factor method (conventions: Noise figure; ADR 0105).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "noise_figure.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/noise_figure.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
