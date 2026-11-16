"""Writes vectors/cases/phase_noise_ssb.json by hand, using only the Python standard library.

The inputs are carriers with pure sinusoidal phase modulation, e^{j(w_c n + m sin(w_m n))}. By
the Jacobi-Anger expansion it has lines of amplitude J_k(m) at w_c + k w_m (half that, mirrored,
for a real cosine). The rates are coherent with the Welch segments and the periodic 4-term
Blackman-Harris window leaks only three bins, so each line sits alone: the carrier group holds
J_0^2 (J_0^2/2 for real input) and the PSD at a sideband bin is that line's power over the window's
ENBW, ENBW = (fs/N)(a0^2 + (a1^2 + a2^2 + a3^2)/2)/a0^2. So L(k f_m) = J_k^2/(J_0^2 ENBW) exactly
(conventions: Phase noise measurement; ADR 0108). J_k is summed from its power series.

Run from the repo root: python vectors/generators/phase_noise_ssb.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

OP = "phase_noise_ssb"
BH = (0.35875, 0.48829, 0.14128, 0.01168)
cases = []


def bessel_j(k, m):
    return sum((-1) ** s * (m / 2) ** (2 * s + k) / (math.factorial(s) * math.factorial(s + k))
               for s in range(40))


def enbw_hz(fs, n):
    a0, a1, a2, a3 = BH
    return fs / n * (a0**2 + (a1**2 + a2**2 + a3**2) / 2) / a0**2


def pm(n, kc, km, m, period, complex_):
    th = [2 * math.pi * (kc * i / period) + m * math.sin(2 * math.pi * km * i / period)
          for i in range(n)]
    if complex_:
        return {"re": [math.cos(t) for t in th], "im": [math.sin(t) for t in th]}
    return [math.cos(t) for t in th]


def case(cid, *, n, seg, fs, kc, km, m, orders, complex_, carrier=None, why):
    df = fs / seg
    x = pm(n, kc, km, m, seg, complex_)
    j0 = bessel_j(0, m)
    args = {"samples": x, "sample_rate": fs, "offsets": [k * km * df for k in orders]}
    if seg != n:
        args["nperseg"] = seg
    if carrier is not None:
        args["carrier"] = carrier
    exp = {"carrier_frequency": kc * df, "carrier_power": j0**2 if complex_ else j0**2 / 2,
           "offsets": args["offsets"],
           "l_dbc_hz": [10 * math.log10(bessel_j(k, m) ** 2 / (j0**2 * enbw_hz(fs, seg)))
                        for k in orders]}
    cases.append({"id": f"{OP}.{cid}", "op": OP, "args": args, "expected": exp,
                  "tol": {"abs": 1e-9, "rel": 1e-9}, "source": why})


case("complex_baseband_small_m", n=1024, seg=1024, fs=10240.0, kc=0, km=16, m=0.05,
     orders=[1, 2, 3], complex_=True,
     why="by hand: Jacobi-Anger, m = 0.05 at 160 Hz on a 0 Hz carrier; L = J_k^2/(J_0^2 ENBW)")
case("complex_offset_carrier", n=1024, seg=1024, fs=1024.0, kc=-200, km=20, m=0.5,
     orders=[1, 2], complex_=True,
     why="by hand: Jacobi-Anger, m = 0.5 at 20 Hz on a -200 Hz carrier")
case("real_carrier", n=1024, seg=1024, fs=1024.0, kc=256, km=16, m=0.2, orders=[1, 2, 4],
     complex_=False,
     why="by hand: Jacobi-Anger on a real cosine at 256 Hz, m = 0.2 at 16 Hz; one-sided PSD")
case("real_large_index_segments", n=4096, seg=1024, fs=4096.0, kc=256, km=32, m=1.0,
     orders=[1, 2, 3], complex_=False,
     why="by hand: Jacobi-Anger, m = 1 at 128 Hz; four-plus Welch segments of identical spectra")
case("given_carrier", n=1024, seg=1024, fs=1024.0, kc=300, km=24, m=0.1, orders=[1],
     complex_=False, carrier=301.0,
     why="by hand: Jacobi-Anger at 300 Hz; the carrier given as 301 Hz picks bin 301, whose group still holds the whole line")

M = 128


def tone(k, n=M):
    return [math.cos(2 * math.pi * k * i / M) for i in range(n)]


for cid, x, offsets, extra, why in (
    ("empty_offsets", tone(32), [], {}, "offsets must not be empty"),
    ("zero_offset", tone(32), [0.0], {}, "offsets must be positive"),
    ("negative_offset", tone(32), [-8.0], {}, "offsets must be positive"),
    ("infinite_offset", tone(32), ["inf"], {}, "offsets must be finite"),
    ("offset_in_carrier_group", tone(32), [3.0], {}, "3 bins is inside the half-width 4"),
    ("offset_past_nyquist", tone(32), [40.0], {}, "32 + 40 is past fs/2 = 64"),
    ("offset_below_zero", tone(32), [40.0, 8.0], {}, "32 - 40 is below 0 for real input"),
    ("no_carrier_power", [0.0] * M, [8.0], {}, "a zero carrier has no power"),
    ("carrier_above_nyquist", tone(32), [8.0], {"carrier": 70.0}, "|carrier| <= fs/2"),
    ("real_negative_carrier", tone(32), [8.0], {"carrier": -32.0}, "real input needs f >= 0"),
    ("one_sample", [1.0], [0.25], {}, "the spectrum needs at least two samples"),
):
    cases.append({"id": f"{OP}.{cid}", "op": OP,
                  "args": {"samples": x, "sample_rate": float(M) if len(x) > 1 else 1.0,
                           "offsets": offsets, **extra},
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": OP,
    "description": "Single-sideband phase noise L(f) in dBc/Hz (conventions: Phase noise "
    "measurement; ADR 0108).",
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
