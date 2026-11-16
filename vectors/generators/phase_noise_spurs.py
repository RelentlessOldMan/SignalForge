"""Writes vectors/cases/phase_noise_spurs.json by hand, using only the Python standard library.

The inputs are carriers with pure sinusoidal phase modulation, e^{j(w_c n + m sin(w_m n))}
(Jacobi-Anger lines of amplitude J_k(m) at w_c + k w_m), plus added spur tones, all coherent with
the Welch segment, with no two lines' skirts sharing a bin. The periodic 4-term Blackman-Harris
window puts a line of power P in seven bins: P c_d^2 / (a0^2 + (a1^2 + a2^2 + a3^2)/2) at offset d,
c_0 = a0 and c_{+-d} = a_d/2. This generator builds that bin spectrum by hand, applies the removal
rule (conventions: Phase noise with spurs removed; ADR 0115) and reads L(f) or the band sum from it.

Run from the repo root: python vectors/generators/phase_noise_spurs.py [--check]
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


def remove(s, psd, c, spur_bins):
    """The rule in ADR 0115, on bin indices; ``spur_bins`` are offsets in bins, in order."""
    n = len(psd)
    hi = (s.n // 2) if not s.complex_ else s.n // 2 - 1
    for o in spur_bins:
        for b0 in (c - o, c + o):
            if not (s.first <= b0 <= hi):
                continue
            si = b0 - s.first
            ci = c - s.first
            assert abs(si - ci) > 2 * W + 1
            a, b = si - W - 1, si + W + 1
            va = psd[a] if a >= 0 else psd[b]
            vb = psd[b] if b < n else va
            for j in range(max(a + 1, 0), min(b - 1, n - 1) + 1):
                psd[j] = va + (vb - va) * (j - a) / (2 * W + 2)
    return psd


def ipn_case(cid, *, n, fs, kc, km, m, spurs, complex_, orders, band, spur_bins, why):
    s = spectrum(n, fs, kc, km, m, spurs, complex_, orders)
    psd = s.psd()
    if spur_bins is not None:
        psd = remove(s, psd, kc, spur_bins)
    pc = sum(s.p[kc + d - s.first] for d in range(-W, W + 1))
    total = sum(psd[i] for i in range(len(psd))
                if band[0] <= abs(i + s.first - kc) <= band[1])
    ratio = total * s.df / pc
    rms = math.sqrt(ratio)
    args = {"samples": signal(n, kc, km, m, spurs, complex_), "sample_rate": fs,
            "f_lo": band[0] * s.df, "f_hi": band[1] * s.df}
    if spur_bins is not None:
        args["spur_offsets"] = [o * s.df for o in spur_bins]
    exp = {"carrier_frequency": kc * s.df, "carrier_power": pc,
           "f_lo": args["f_lo"], "f_hi": args["f_hi"], "integrated_dbc": 10 * math.log10(ratio),
           "phase_rms": rms, "jitter_rms": rms / (2 * math.pi * abs(kc * s.df))}
    cases.append({"id": f"integrated_phase_noise.{cid}", "op": "integrated_phase_noise",
                  "args": args, "expected": exp, "tol": TOL, "source": why})


def ssb_case(cid, *, n, fs, kc, km, m, spurs, complex_, orders, offsets, spur_bins, why):
    s = spectrum(n, fs, kc, km, m, spurs, complex_, orders)
    psd = s.psd()
    if spur_bins is not None:
        psd = remove(s, psd, kc, spur_bins)
    pc = sum(s.p[kc + d - s.first] for d in range(-W, W + 1))
    ell = [10 * math.log10((psd[kc - o - s.first] + psd[kc + o - s.first]) / 2 / pc)
           for o in offsets]
    args = {"samples": signal(n, kc, km, m, spurs, complex_), "sample_rate": fs,
            "offsets": [o * s.df for o in offsets]}
    if spur_bins is not None:
        args["spur_offsets"] = [o * s.df for o in spur_bins]
    exp = {"carrier_frequency": kc * s.df, "carrier_power": pc, "offsets": args["offsets"],
           "l_dbc_hz": ell}
    cases.append({"id": f"phase_noise_ssb.{cid}", "op": "phase_noise_ssb", "args": args,
                  "expected": exp, "tol": TOL, "source": why})


PM = {"n": 1024, "fs": 1024.0, "kc": -200, "km": 16, "m": 0.3, "spurs": [(-176, 0.01)],
      "complex_": True, "orders": range(-12, 13)}
ipn_case("spur_kept", **PM, band=(8.5, 40.5), spur_bins=None,
         why="by hand: Jacobi-Anger lines every 16 bins from -200 Hz, m = 0.3, plus a spur of "
         "amplitude 0.01 at +24 bins; the band holds lines k = +-1, +-2 and the spur")
ipn_case("spur_removed", **PM, band=(8.5, 40.5), spur_bins=[24],
         why="by hand: as spur_kept, the spur's 9 bins on each side replaced by a line between "
         "the bins at +-5, each on a neighbouring line's skirt (ADR 0115)")
ipn_case("overlapping_spurs_in_order", **PM, band=(8.5, 40.5), spur_bins=[24, 26],
         why="by hand: as spur_removed, then 26 bins, whose lower edge is a bin already "
         "interpolated for the first")
ipn_case("real_spur_next_to_a_line", n=1024, fs=10240.0, kc=256, km=20, m=0.01,
         spurs=[(268, 0.003)], complex_=False, orders=range(-6, 7), band=(5.5, 30.5),
         spur_bins=[12],
         why="by hand: a real cosine at 256 bins, m = 0.01 at 20 bins, a spur at +12; the upper "
         "edge (+17) is on the k = 1 line's skirt")
ipn_case("edge_past_nyquist_and_a_side_skipped", n=1024, fs=1024.0, kc=470, km=1000, m=0.0,
         spurs=[(500, 0.001), (508, 0.01)], complex_=False, orders=[0], band=(25.5, 41.5),
         spur_bins=[38, 60],
         why="by hand: a real carrier at 470 Hz, tones at 500 and 508 Hz; the 508 group's upper "
         "edge is past fs/2 so the group takes the lower edge's value; 470 + 60 is past the "
         "spectrum, so that side is skipped")
ssb_case("spur_kept", **PM, offsets=[16, 24], spur_bins=None,
         why="by hand: as integrated_phase_noise.spur_kept; L at 24 bins reads the spur")
ssb_case("spur_removed", **PM, offsets=[16, 24], spur_bins=[24],
         why="by hand: L at 24 bins reads the middle of the interpolated line, the mean of the "
         "edges; at 16 bins the PM line, untouched")

M = 128


def tone(k, n=M):
    return [math.cos(2 * math.pi * k * i / M) for i in range(n)]


for op, extra in (("integrated_phase_noise", {"f_lo": 12.0, "f_hi": 30.0}),
                  ("phase_noise_ssb", {"offsets": [20.0]})):
    for cid, spur, why in (
        ("spur_too_near_the_carrier", [9.0], "9 bins is within 2w + 1 of the carrier"),
        ("spur_offset_zero", [0.0], "spur offsets must be positive"),
        ("spur_offset_negative", [-20.0], "spur offsets must be positive"),
        ("spur_offset_nan", ["nan"], "spur offsets must be finite"),
        ("spur_offset_inf", ["inf"], "spur offsets must be finite"),
    ):
        cases.append({"id": f"{op}.{cid}", "op": op,
                      "args": {"samples": tone(32), "sample_rate": float(M), **extra,
                               "spur_offsets": spur},
                      "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "phase_noise_spurs",
    "description": "Phase noise and integrated phase noise with spurs removed (conventions: "
    "Phase noise with spurs removed; ADR 0115).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "phase_noise_spurs.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/phase_noise_spurs.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
