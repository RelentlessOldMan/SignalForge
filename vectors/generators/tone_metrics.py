"""Writes vectors/cases/tone_metrics.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge, and it takes no spectrum: every input is a sum of tones at
bin centers, so each group's power is known in closed form (conventions: Tone metrics). A real
tone `A cos(2 pi k n/N + phi)` off DC and Nyquist has power A^2/2, at Nyquist A^2 cos^2(phi), a
complex tone `A e^(j...)` |A|^2, a DC offset d its |d|^2. With the rectangular window an on-bin
tone sits in its own bin; with the periodic Hann window it fills bins k-1, k, k+1 in the ratio
1/6 : 2/3 : 1/6 (the DFT of the window is N/2 at 0 and -N/4 at +-1). The dB figures follow from
the powers by the formulas in the conventions.

Run from the repo root: python vectors/generators/tone_metrics.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-9, "rel": 1e-9}


def real_tones(n, dc, tones):
    """dc + sum of A cos(2 pi k i/n + phi) for (k, A, phi) in tones."""
    return [dc + math.fsum(a * math.cos(2 * math.pi * k * i / n + ph) for k, a, ph in tones)
            for i in range(n)]


def complex_tones(n, dc, tones):
    """dc + sum of A e^(j(2 pi k i/n + phi)) for (k, A, phi) in tones."""
    return [dc + sum(a * cmath.exp(1j * (2 * math.pi * k * i / n + ph)) for k, a, ph in tones)
            for i in range(n)]


def cplx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


def figures(f1, s, h, noise, dc):
    def db(num, den):
        return "inf" if den == 0 else 10 * math.log10(num / den)

    sinad = db(s, noise + h)
    return {
        "fundamental_frequency": f1,
        "signal_power": s,
        "harmonic_power": h,
        "noise_power": noise,
        "dc_power": dc,
        "snr_db": db(s, noise),
        "sinad_db": sinad,
        "thd_db": "-inf" if h == 0 else 10 * math.log10(h / s),
        "enob": "inf" if sinad == "inf" else (sinad - 10 * math.log10(1.5)) / (20 * math.log10(2)),
    }


def case(case_id, x, fs, expected, src, **kw):
    args = {"samples": cplx(x) if any(isinstance(v, complex) for v in x) else x,
            "sample_rate": fs} | kw
    return {"id": case_id, "op": "tone_metrics", "args": args, "expected": expected, "tol": TOL,
            "source": src}


def err(case_id, args, why, op="tone_metrics"):
    return {"id": case_id, "op": op, "args": args, "error": "invalid_argument", "source": why}


def spurs(case_id, x, fs, carrier, found, src, **kw):
    """An sfdr case: carrier and each found spur as (frequency, power)."""
    dbc = [10 * math.log10(p / carrier[1]) for _, p in found]
    expected = {"carrier_frequency": carrier[0], "carrier_power": carrier[1],
                "sfdr_db": -dbc[0] if found else "inf",
                "spur_frequencies": [f for f, _ in found], "spur_powers": [p for _, p in found],
                "spur_dbc": dbc}
    c = case(case_id, x, fs, expected, src, **kw)
    c["op"] = "sfdr"
    return c


# Real, rectangular, N = fs = 64 (1 Hz bins), half-width 1. Groups: DC 0-1, fundamental 4-6,
# harmonics at 10, 15, 20, 25, 30 (+-1). Noise tones at 13 and 28, and at Nyquist (32).
rect = real_tones(64, 0.25, [(5, 1.0, 0.3), (10, 0.1, 0.0), (15, 0.05, 1.0), (13, 0.02, 0.4),
                             (28, 0.01, 2.0)])
rect = [v + 0.003 * (-1) ** i for i, v in enumerate(rect)]
rect_noise = 0.02**2 / 2 + 0.01**2 / 2 + 0.003**2

# Real, Hann, N = 128 at 1 kHz (7.8125 Hz bins), half-width 2. Fundamental at bin 10, harmonics
# at 20 and 30, noise tones at bins 25 and 55, DC 0.1; every tone's three bins sit inside its group.
hann = real_tones(128, 0.1, [(10, 0.7, 0.2), (20, 0.07, 1.1), (30, 0.007, 0.5), (25, 0.003, 0.0),
                             (55, 0.001, 2.5)])

# Complex, Hann, N = fs = 64, fundamental at 20 Hz: harmonic 2 aliases to -24 Hz, 3 to -4 Hz
# (the DC group takes -2 … 2, so that group is -6 … -3), 4 to 16 Hz (14 … 17, as 18 is the
# fundamental's), 5 to -28, 6 to -8. Noise tones at 10 and -15 Hz, DC 0.1 + 0.05j.
cx = complex_tones(64, 0.1 + 0.05j, [(20, 0.8, 0.0), (-24, 0.05, 0.7), (-4, 0.02, -1.0),
                                     (10, 0.004, 0.3), (-15, 0.002, 1.9)])

# Real, rectangular, N = fs = 32: a weak fundamental at 3 Hz named by the caller, a strong spur at
# 12 Hz that the default would have taken, a harmonic at 6 Hz; two harmonics (groups 5-7, 8-10).
named = real_tones(32, 0.0, [(3, 0.1, 0.0), (12, 0.5, 0.5), (6, 0.01, 0.0)])

# Real, Hann, N = fs = 64, half-width 0: each group is one bin, so the fundamental (bin 8) and its
# harmonic (bin 16) keep 2/3 of their power and the outer thirds go to noise, with a tone at 25.
narrow = real_tones(64, 0.0, [(8, 1.0, 0.0), (16, 0.1, 0.0), (25, 0.01, 0.0)])

cases = [
    case("tone_metrics.real_rectangular", rect, 64.0,
         figures(5.0, 0.5, 0.1**2 / 2 + 0.05**2 / 2, rect_noise, 0.25**2),
         "closed form: on-bin tones, rectangular window; S = 1/2, H = (0.1^2 + 0.05^2)/2, "
         "N = 0.02^2/2 + 0.01^2/2 + 0.003^2 (Nyquist), DC 0.25^2",
         window="rectangular"),
    case("tone_metrics.real_rectangular_no_harmonics", rect, 64.0,
         figures(5.0, 0.5, 0.0, rect_noise + 0.1**2 / 2 + 0.05**2 / 2, 0.25**2),
         "closed form: as real_rectangular, with num_harmonics 0 the harmonics are noise and "
         "THD is -inf", window="rectangular", num_harmonics=0),
    case("tone_metrics.real_rectangular_width_0", rect, 64.0,
         figures(5.0, 0.5, 0.1**2 / 2 + 0.05**2 / 2, rect_noise, 0.25**2),
         "closed form: on-bin tones with the rectangular window fill one bin, so half-width 0 "
         "changes nothing", window="rectangular", width=0),
    case("tone_metrics.real_hann", hann, 1000.0,
         figures(10 * 1000 / 128, 0.7**2 / 2, 0.07**2 / 2 + 0.007**2 / 2,
                 0.003**2 / 2 + 0.001**2 / 2, 0.1**2),
         "closed form: on-bin tones, Hann fills k-1 … k+1, all inside the +-2 groups; centroid "
         "of the symmetric group is bin 10 = 78.125 Hz", window="hann"),
    case("tone_metrics.complex_hann_aliased", cx, 64.0,
         figures(20.0, 0.8**2, 0.05**2 + 0.02**2, 0.004**2 + 0.002**2, 0.1**2 + 0.05**2),
         "closed form: complex on-bin tones, power |A|^2; harmonics 2 and 3 of 20 Hz alias to "
         "-24 and -4 Hz", window="hann"),
    case("tone_metrics.named_fundamental", named, 32.0,
         figures(3.0, 0.1**2 / 2, 0.01**2 / 2, 0.5**2 / 2, 0.0),
         "closed form: the fundamental named at 3 Hz; the 12 Hz spur is noise, so SNR is "
         "10 log10(0.005/0.125)", window="rectangular", num_harmonics=2, fundamental=3.0),
    case("tone_metrics.hann_width_0", narrow, 64.0,
         figures(8.0, 2 / 3 * 0.5, 2 / 3 * 0.005, (0.5 + 0.005) / 3 + 0.01**2 / 2, 0.0),
         "closed form: Hann puts 2/3 of an on-bin tone in its own bin and 1/6 in each neighbour; "
         "with half-width 0 the neighbours are noise", window="hann", width=0, num_harmonics=1),
    err("tone_metrics.one_sample", {"samples": [1.0], "sample_rate": 1.0},
        "at least two samples required"),
    err("tone_metrics.sample_nan", {"samples": [1.0, "nan", 0.0, 1.0], "sample_rate": 4.0},
        "samples must be finite"),
    err("tone_metrics.rate_zero", {"samples": rect, "sample_rate": 0.0},
        "sample_rate must be positive"),
    err("tone_metrics.harmonics_negative", {"samples": rect, "sample_rate": 64.0,
                                            "num_harmonics": -1}, "num_harmonics >= 0 required"),
    err("tone_metrics.width_negative", {"samples": rect, "sample_rate": 64.0, "width": -1},
        "width >= 0 required"),
    err("tone_metrics.fundamental_in_dc", {"samples": rect, "sample_rate": 64.0,
                                           "window": "rectangular", "fundamental": 1.0},
        "the bin nearest 1 Hz is in the DC group (bins 0 and 1)"),
    err("tone_metrics.fundamental_above_nyquist", {"samples": rect, "sample_rate": 64.0,
                                                   "fundamental": 33.0},
        "|fundamental| <= sample_rate/2 required"),
    err("tone_metrics.fundamental_negative_real", {"samples": rect, "sample_rate": 64.0,
                                                   "fundamental": -5.0},
        "a real input's fundamental must be >= 0"),
    err("tone_metrics.fundamental_nan", {"samples": rect, "sample_rate": 64.0,
                                         "fundamental": "nan"}, "the fundamental must be finite"),
    err("tone_metrics.no_signal", {"samples": [0.0] * 16, "sample_rate": 16.0},
        "all zeros: no signal power at the fundamental"),
    spurs("sfdr.real_rectangular", rect, 64.0, (5.0, 0.5),
          [(10.0, 0.1**2 / 2), (15.0, 0.05**2 / 2), (13.0, 0.02**2 / 2), (28.0, 0.01**2 / 2)],
          "closed form: the tone_metrics real_rectangular input; spurs strongest first, the "
          "harmonics at 10 and 15 Hz among them", window="rectangular", num_spurs=4),
    spurs("sfdr.complex_hann", cx, 64.0, (20.0, 0.8**2),
          [(-24.0, 0.05**2), (-4.0, 0.02**2), (10.0, 0.004**2)],
          "closed form: the tone_metrics complex_hann_aliased input; each spur's three Hann bins "
          "lie in its group, so its centroid is its bin", window="hann", num_spurs=3),
    spurs("sfdr.named_carrier_below_spur", named, 32.0, (3.0, 0.1**2 / 2), [(12.0, 0.5**2 / 2)],
          "closed form: the carrier named at 3 Hz is 14 dB below the 12 Hz spur, so SFDR is "
          "negative", window="rectangular", fundamental=3.0),
    spurs("sfdr.no_bins_left", real_tones(8, 0.0, [(3, 1.0, 0.0)]), 8.0, (3.0, 0.5), [],
          "by hand: 5 one-sided bins; with half-width 1 DC takes bins 0-1 and the 3 Hz carrier "
          "2-4, so no bin is left for a spur", window="rectangular", width=1, num_spurs=2),
    err("sfdr.no_spurs_asked", {"samples": rect, "sample_rate": 64.0, "num_spurs": 0},
        "num_spurs >= 1 required", op="sfdr"),
    err("sfdr.fundamental_in_dc", {"samples": rect, "sample_rate": 64.0, "window": "rectangular",
                                   "fundamental": 0.0}, "the fundamental is in the DC group",
        op="sfdr"),
    err("sfdr.one_sample", {"samples": [1.0], "sample_rate": 1.0},
        "at least two samples required", op="sfdr"),
    err("tone_metrics.kaiser_without_beta", {"samples": rect, "sample_rate": 64.0,
                                             "window": "kaiser"}, "the kaiser window needs beta"),
]

doc = {
    "schema": 1,
    "suite": "tone_metrics",
    "description": "SNR, SINAD, THD and ENOB of a tone, and SFDR with its spurs, from one windowed "
    "spectrum (conventions: Tone metrics, Spurs and SFDR).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "tone_metrics.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/tone_metrics.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
