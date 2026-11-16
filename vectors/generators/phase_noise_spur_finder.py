"""Writes vectors/cases/phase_noise_spur_finder.json by hand, using only the Python standard library.

The inputs are carriers with pure sinusoidal phase modulation, e^{j(w_c n + m sin(w_m n))}
(Jacobi-Anger lines of amplitude J_k(m) at w_c + k w_m), plus added spur tones, all coherent with
the Welch segment. The periodic 4-term Blackman-Harris window puts a line of power P in seven bins:
P c_d^2 / (a0^2 + (a1^2 + a2^2 + a3^2)/2) at offset d, c_0 = a0 and c_{+-d} = a_d/2. This generator
builds that bin spectrum by hand and applies the finder's test (conventions: Phase noise spur
finder; ADR 0116) to it.

Run from the repo root: python vectors/generators/phase_noise_spur_finder.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import sys

A = (0.35875, 0.48829, 0.14128, 0.01168)
D = A[0] ** 2 + (A[1] ** 2 + A[2] ** 2 + A[3] ** 2) / 2
FRAC = {d: (A[abs(d)] if d == 0 else A[abs(d)] / 2) ** 2 / D for d in range(-3, 4)}
W = 4  # the Blackman-Harris carrier group's half-width
TOL = {"abs": 1e-12, "rel": 1e-9}
cases = []


def bessel_j(k, m):
    k_abs = abs(k)
    v = sum((-1) ** s * (m / 2) ** (2 * s + k_abs) / (math.factorial(s) * math.factorial(s + k_abs))
            for s in range(40))
    return v * (-1) ** k_abs if k < 0 else v


class Spectrum:
    """Bin powers of coherent lines; complex input is two-sided (bins -N/2 .. N/2-1), real input
    one-sided (bins 0 .. N/2)."""

    def __init__(self, n, fs, complex_):
        self.n, self.fs, self.complex_ = n, fs, complex_
        self.df = fs / n
        self.first = -n // 2 if complex_ else 0
        self.p = [0.0] * (n if complex_ else n // 2 + 1)

    def line(self, k, power):
        for d, f in FRAC.items():
            self.p[k + d - self.first] += power * f

    def psd(self):
        return [v / self.df for v in self.p]


def signal(n, kc, km, m, spurs, complex_):
    out_re, out_im = [], []
    for i in range(n):
        th = 2 * math.pi * kc * i / n + m * math.sin(2 * math.pi * km * i / n)
        re, im = math.cos(th), math.sin(th)
        for ks, amp in spurs:
            re += amp * math.cos(2 * math.pi * ks * i / n)
            im += amp * math.sin(2 * math.pi * ks * i / n)
        out_re.append(re)
        out_im.append(im)
    return {"re": out_re, "im": out_im} if complex_ else out_re


def spectrum(n, fs, kc, km, m, spurs, complex_, orders):
    s = Spectrum(n, fs, complex_)
    for k in orders:
        j = bessel_j(k, m)
        s.line(kc + k * km, j * j if complex_ else j * j / 2)
    for ks, amp in spurs:
        s.line(ks, amp * amp if complex_ else amp * amp / 2)
    return s


def find(s, kc, band, threshold_db):
    """The test in ADR 0116, on the hand bin powers."""
    p = list(s.p)
    n = len(p)
    ci = kc - s.first
    found = []
    for i in range(n):
        if not (band[0] <= abs(i - ci) <= band[1]):
            continue
        assert abs(i - ci) > 2 * W + 1
        a, b = i - W - 1, i + W + 1
        if a < 0 or b >= n:
            continue
        if not (all(p[i] > p[q] for q in range(i - W, i))
                and all(p[i] >= p[q] for q in range(i + 1, i + W + 1))):
            continue
        g = sum(p[a + 1:b])
        line = (2 * W + 1) * (p[a] + p[b]) / 2
        ratio_db = 10 * math.log10(g / line) if line > 0 else math.inf
        if g > line * 10 ** (threshold_db / 10):
            # keep the vectors clear of the threshold: both languages must agree on the test
            assert ratio_db > threshold_db + 1, ratio_db
            found.append((i - ci, g - line))
        elif g > 0:
            assert ratio_db < threshold_db - 1, ratio_db
    return found


def case(cid, *, n, fs, kc, km, m, spurs, complex_, orders, band, threshold_db, why):
    s = spectrum(n, fs, kc, km, m, spurs, complex_, orders)
    pc = sum(s.p[kc + d - s.first] for d in range(-W, W + 1))
    found = find(s, kc, band, threshold_db)
    args = {"samples": signal(n, kc, km, m, spurs, complex_), "sample_rate": fs,
            "f_lo": band[0] * s.df, "f_hi": band[1] * s.df}
    if threshold_db != 10.0:
        args["threshold_db"] = threshold_db
    exp = {"carrier_frequency": kc * s.df, "carrier_power": pc,
           "offsets": [o * s.df for o, _ in found],
           "levels_dbc": [10 * math.log10(v / pc) for _, v in found]}
    cases.append({"id": f"phase_noise_spurs.{cid}", "op": "phase_noise_spurs", "args": args,
                  "expected": exp, "tol": TOL, "source": why})


PM = {"n": 1024, "fs": 1024.0, "kc": -200, "km": 16, "m": 0.3, "spurs": [(-176, 0.03)],
      "complex_": True, "orders": range(-12, 13)}
case("pm_lines_and_a_spur", **PM, band=(9.5, 40.5), threshold_db=10.0,
     why="by hand: Jacobi-Anger lines every 16 bins from -200 Hz, m = 0.3, plus a spur of "
     "amplitude 0.03 at +24 bins; the band holds lines k = +-1, +-2 and the spur, each the peak "
     "of its group over a line between edge bins on the neighbours' skirts or empty")
case("peak_just_outside_the_band", **PM, band=(41.5, 47.5), threshold_db=10.0,
     why="by hand: as pm_lines_and_a_spur; the band holds the k = +-3 lines' lower skirts but "
     "not their peaks at 48 bins, so nothing is found")
REAL = {"n": 1024, "fs": 10240.0, "kc": 256, "km": 20, "m": 0.01, "spurs": [(268, 0.003)],
        "complex_": False, "orders": range(-6, 7)}
case("real_spur_on_a_line_skirt", **REAL, band=(10.5, 50.5), threshold_db=10.0,
     why="by hand: a real cosine at 256 bins, m = 0.01 at 20 bins, a spur at +12 bins; the "
     "spur's upper edge is on the k = 1 line's skirt and the line's lower edge on the spur's")
case("threshold_drops_the_weaker_ratio", **REAL, band=(10.5, 50.5), threshold_db=32.0,
     why="by hand: as real_spur_on_a_line_skirt with a 32 dB threshold, which the spur's group "
     "over its line misses and the k = 1 line's passes")
case("edge_past_the_spectrum_not_tested", n=1024, fs=1024.0, kc=470, km=1000, m=0.0,
     spurs=[(500, 0.001), (508, 0.01)], complex_=False, orders=[0], band=(25.5, 41.5),
     threshold_db=10.0,
     why="by hand: a real carrier at 470 Hz, tones at 500 and 508 Hz; the 508 bin's upper edge "
     "is past fs/2, so it is not tested; the 500 bin's edge is on the 508 tone's skirt")

M = 128


def tone(k):
    return [math.cos(2 * math.pi * k * i / M) for i in range(M)]


for cid, extra, why in (
    ("band_within_2w_plus_1", {"f_lo": 9.0, "f_hi": 30.0}, "9 bins is within 2w + 1 of the carrier"),
    ("band_reversed", {"f_lo": 30.0, "f_hi": 12.0}, "the band needs f_lo < f_hi"),
    ("band_past_the_spectrum", {"f_lo": 12.0, "f_hi": 40.0}, "32 + 40 Hz is past fs/2"),
    ("threshold_zero", {"f_lo": 12.0, "f_hi": 30.0, "threshold_db": 0.0},
     "threshold_db must be positive"),
    ("threshold_negative", {"f_lo": 12.0, "f_hi": 30.0, "threshold_db": -3.0},
     "threshold_db must be positive"),
    ("threshold_nan", {"f_lo": 12.0, "f_hi": 30.0, "threshold_db": "nan"},
     "threshold_db must be finite"),
    ("threshold_inf", {"f_lo": 12.0, "f_hi": 30.0, "threshold_db": "inf"},
     "threshold_db must be finite"),
):
    cases.append({"id": f"phase_noise_spurs.{cid}", "op": "phase_noise_spurs",
                  "args": {"samples": tone(32), "sample_rate": float(M), **extra},
                  "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "phase_noise_spur_finder",
    "description": "The phase noise spur finder (conventions: Phase noise spur finder; ADR 0116).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "phase_noise_spur_finder.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/phase_noise_spur_finder.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
