"""Writes vectors/cases/integrated_phase_noise.json by hand, using only the Python standard library.

The inputs are carriers with pure sinusoidal phase modulation, e^{j(w_c n + m sin(w_m n))}. By
the Jacobi-Anger expansion it has lines of amplitude J_k(m) at w_c + k w_m (half that, mirrored,
for a real cosine). The rates are coherent with the Welch segments and the periodic 4-term
Blackman-Harris window puts each line's whole power in seven bins, so with band edges between
the lines the band holds sum J_k^2 over its lines, both signs of k, against the carrier's J_0^2:
ratio = sum J_k^2 / J_0^2 exactly (conventions: Integrated phase noise; ADR 0109). J_k is summed
from its power series.

Run from the repo root: python vectors/generators/integrated_phase_noise.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

OP = "integrated_phase_noise"
cases = []


def bessel_j(k, m):
    return sum((-1) ** s * (m / 2) ** (2 * s + k) / (math.factorial(s) * math.factorial(s + k))
               for s in range(40))


def pm(n, kc, km, m, period, complex_):
    th = [2 * math.pi * (kc * i / period) + m * math.sin(2 * math.pi * km * i / period)
          for i in range(n)]
    if complex_:
        return {"re": [math.cos(t) for t in th], "im": [math.sin(t) for t in th]}
    return [math.cos(t) for t in th]


def case(cid, *, n, seg, fs, kc, km, m, band, orders, complex_, why):
    df = fs / seg
    j0 = bessel_j(0, m)
    ratio = sum(2 * bessel_j(k, m) ** 2 for k in orders) / j0**2
    args = {"samples": pm(n, kc, km, m, seg, complex_), "sample_rate": fs,
            "f_lo": band[0] * df, "f_hi": band[1] * df}
    if seg != n:
        args["nperseg"] = seg
    rms = math.sqrt(ratio)
    exp = {"carrier_frequency": kc * df, "carrier_power": j0**2 if complex_ else j0**2 / 2,
           "f_lo": args["f_lo"], "f_hi": args["f_hi"], "integrated_dbc": 10 * math.log10(ratio),
           "phase_rms": rms, "jitter_rms": rms / (2 * math.pi * abs(kc * df))}
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": args, "expected": exp,
                  "tol": {"abs": 1e-12, "rel": 1e-9}, "source": why})


case("complex_two_lines", n=1024, seg=1024, fs=1024.0, kc=-200, km=16, m=0.3, band=(8.5, 40.5),
     orders=[1, 2], complex_=True,
     why="by hand: Jacobi-Anger, m = 0.3 at 16 Hz on -200 Hz; band 8.5-40.5 Hz holds k = +-1, +-2")
case("real_one_line", n=1024, seg=1024, fs=10240.0, kc=256, km=20, m=0.01, band=(5.5, 30.5),
     orders=[1], complex_=False,
     why="by hand: Jacobi-Anger on a real cosine at 2560 Hz, m = 0.01 at 200 Hz; k = +-1 only")
case("real_band_skips_first_line", n=4096, seg=1024, fs=4096.0, kc=256, km=32, m=1.0,
     band=(40.5, 111.5), orders=[2, 3], complex_=False,
     why="by hand: Jacobi-Anger, m = 1 at 128 Hz; band 162-446 Hz holds k = +-2, +-3; Welch "
     "segments of identical spectra")

M = 128


def tone(k, n=M):
    return [math.cos(2 * math.pi * k * i / M) for i in range(n)]


for cid, x, lo, hi, why in (
    ("zero_f_lo", tone(32), 0.0, 8.0, "f_lo must be positive"),
    ("f_hi_not_above_f_lo", tone(32), 8.0, 8.0, "f_lo < f_hi"),
    ("infinite_f_hi", tone(32), 8.0, "inf", "f_hi must be finite"),
    ("band_in_carrier_group", tone(32), 2.0, 8.0, "bins 2-4 from the carrier are in its group"),
    ("band_past_nyquist", tone(32), 8.0, 40.0, "32 + 40 is past fs/2 = 64"),
    ("no_carrier_power", [0.0] * M, 8.0, 16.0, "a zero carrier has no power"),
    ("one_sample", [1.0], 0.1, 0.2, "the spectrum needs at least two samples"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": x, "sample_rate": float(M) if len(x) > 1 else 1.0,
                           "f_lo": lo, "f_hi": hi},
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Integrated phase noise and RMS jitter over an offset band (conventions: "
    "Integrated phase noise; ADR 0109).",
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
