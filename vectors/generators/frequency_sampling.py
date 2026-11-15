"""Writes vectors/cases/frequency_sampling.json from the definitions, using only the Python
standard library.

It does not import NumPy or SignalForge. For each design it interpolates the target onto the
grid, evaluates the conventions' closed form d(t) = (1/L)[G_0 + 2 sum G_k cos(2 pi k t/L) +
G_{K-1} cos(pi t)] by direct sums (math.fsum), and multiplies by its own symmetric windows. It
needs no FFT, because cos is even, so d(t) = d(-t) exactly; it still averages the windowed taps
with their reverse as the conventions do. The hand cases
are worked out in their sources and checked against the sums.

Run from the repo root: python vectors/generators/frequency_sampling.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 0}
SRC = ("conventions: Frequency-sampling design; the closed form by direct cosine sums over the "
       "grid, this generator's linear interpolation and symmetric windows")

COSINE_SUMS = {
    "rectangular": [1.0],
    "hann": [0.5, 0.5],
    "hamming": [0.54, 0.46],
    "blackman": [0.42, 0.5, 0.08],
}


def bessel_i0(x):
    term, total, k = 1.0, [1.0], 0
    while term > 1e-30 * math.fsum(total):
        k += 1
        term *= (x / (2 * k)) ** 2
        total.append(term)
    return math.fsum(total)


def window(name, n, beta=None):
    if n == 1:
        return [1.0]
    d = n - 1  # symmetric
    if name == "kaiser":
        return [bessel_i0(beta * math.sqrt(max(0.0, 1 - (2 * i / d - 1) ** 2))) / bessel_i0(beta)
                for i in range(n)]
    a = COSINE_SUMS[name]
    return [math.fsum((-1) ** k * a[k] * math.cos(2 * math.pi * k * i / d) for k in range(len(a)))
            for i in range(n)]


def default_points(n):
    k = 1
    while k < max(n, 512):
        k *= 2
    return k + 1


def grid(freqs, gains, fs, k):
    big_l = 2 * (k - 1)
    nb = [f / fs for f in freqs]
    out = []
    for j in range(k):
        nu = j / big_l
        i = next(i for i in range(len(nb) - 1) if nb[i] <= nu <= nb[i + 1])
        out.append(gains[i] + (gains[i + 1] - gains[i]) * (nu - nb[i]) / (nb[i + 1] - nb[i]))
    return out


def design(n, freqs, gains, fs, name="hamming", beta=None, k=None):
    k = default_points(n) if k is None else k
    big_l = 2 * (k - 1)
    g = grid(freqs, gains, fs, k)
    w = window(name, n, beta)
    taps = []
    for i in range(n):
        t = i - (n - 1) / 2
        terms = [g[0], g[k - 1] * math.cos(math.pi * t)]
        terms += [2 * g[j] * math.cos(2 * math.pi * j * t / big_l) for j in range(1, k - 1)]
        taps.append(math.fsum(terms) / big_l * w[i])
    return [(a + b) / 2 for a, b in zip(taps, reversed(taps))]


def args_of(n, freqs, gains, fs, name, beta, k):
    a = {"num_taps": n, "frequencies": freqs, "gains": gains, "sample_rate": fs}
    if name != "hamming":
        a["window"] = name
    if beta is not None:
        a["beta"] = beta
    if k is not None:
        a["num_points"] = k
    return a


def gen(case_id, n, freqs, gains, fs, name="hamming", beta=None, k=None):
    return {"id": case_id, "op": "fir_frequency_sampling",
            "args": args_of(n, freqs, gains, fs, name, beta, k),
            "expected": design(n, freqs, gains, fs, name, beta, k), "tol": TOL, "source": SRC}


def hand(case_id, n, freqs, gains, fs, expected, why, name="hamming", beta=None, k=None):
    got = design(n, freqs, gains, fs, name, beta, k)
    assert all(abs(x - y) < 1e-14 for x, y in zip(got, expected, strict=True)), (case_id, got)
    return {"id": case_id, "op": "fir_frequency_sampling",
            "args": args_of(n, freqs, gains, fs, name, beta, k), "expected": expected, "tol": TOL,
            "source": "by hand: " + why}


def err(case_id, args, why):
    base = {"num_taps": 11, "frequencies": [0, 0.2, 0.3, 0.5], "gains": [1, 1, 0, 0],
            "sample_rate": 1}
    return {"id": case_id, "op": "fir_frequency_sampling", "args": {**base, **args},
            "error": "invalid_argument", "source": why}


cases = [
    hand("fir_frequency_sampling.flat_is_impulse", 7, [0, 0.5], [2, 2], 1.0,
         [0, 0, 0, 2, 0, 0, 0],
         "a flat gain 2 has sum_{k=0}^{L-1} e^{2 pi i k t/L} = L delta(t) at integer t, so d = 2 "
         "delta, and the symmetric Hamming window's centre is 1"),
    hand("fir_frequency_sampling.ramp_3", 3, [0, 0.5], [1, 0], 1.0, [0.25, 0.5, 0.25],
         "K = 3, L = 4: G = [1, 1/2, 0]; d(t) = (1/4)(1 + cos(pi t/2)) at t = -1, 0, 1",
         name="rectangular", k=3),
    hand("fir_frequency_sampling.even_2", 2, [0, 0.25, 0.5], [1, 1, 0], 1.0,
         [(1 + math.sqrt(2)) / 4] * 2,
         "K = 3, L = 4: G = [1, 1, 0]; d(+-1/2) = (1/4)(1 + 2 cos(pi/4))", name="rectangular", k=3),
    hand("fir_frequency_sampling.one_tap_two_points", 1, [0, 0.5], [1, 3], 1.0, [2.0],
         "K = 2, L = 2, N = 1: d(0) = (G_0 + G_1)/2", k=2),
    gen("fir_frequency_sampling.lowpass_31", 31, [0, 0.1, 0.15, 0.5], [1, 1, 0, 0], 1.0),
    gen("fir_frequency_sampling.lowpass_30_even_hz", 30, [0, 100, 150, 500], [1, 1, 0, 0], 1000.0,
        name="hann", k=257),
    gen("fir_frequency_sampling.bandpass_kaiser", 41, [0, 0.15, 0.2, 0.3, 0.35, 0.5],
        [0, 0, 1, 1, 0, 0], 1.0, name="kaiser", beta=6.0),
    gen("fir_frequency_sampling.arbitrary_tight_grid", 23, [0, 0.1, 0.3, 0.5],
        [0.5, 1.5, 0.2, 0.7], 1.0, name="rectangular", k=13),
    gen("fir_frequency_sampling.highpass_blackman", 21, [0, 0.2, 0.3, 0.5], [0, 0, 1, 1], 1.0,
        name="blackman"),
    gen("fir_frequency_sampling.odd_grid", 51, [0, 0.24, 0.4, 1.0], [1, 0.8, 0, 0], 2.0, k=100),
    gen("fir_frequency_sampling.long_255", 255, [0, 0.2, 0.22, 0.5], [1, 1, 0, 0], 1.0),
    err("fir_frequency_sampling.zero_taps", {"num_taps": 0}, "num_taps >= 1"),
    err("fir_frequency_sampling.one_frequency", {"frequencies": [0], "gains": [1]},
        "at least two frequencies"),
    err("fir_frequency_sampling.not_from_zero", {"frequencies": [0.01, 0.2, 0.3, 0.5]},
        "the first frequency must be 0"),
    err("fir_frequency_sampling.not_to_nyquist", {"frequencies": [0, 0.2, 0.3, 0.45]},
        "the last frequency must be sample_rate/2"),
    err("fir_frequency_sampling.duplicate_frequency", {"frequencies": [0, 0.2, 0.2, 0.5]},
        "frequencies must increase strictly"),
    err("fir_frequency_sampling.gains_length", {"gains": [1, 1, 0]}, "one gain per frequency"),
    err("fir_frequency_sampling.nan_gain", {"gains": [1, "nan", 0, 0]}, "gains must be finite"),
    err("fir_frequency_sampling.even_nyquist_gain", {"num_taps": 10, "gains": [0, 0, 1, 1]},
        "an even num_taps needs zero gain at sample_rate/2"),
    err("fir_frequency_sampling.one_point", {"num_points": 1}, "num_points >= 2"),
    err("fir_frequency_sampling.points_too_many", {"num_points": 2**20 + 2},
        "num_points <= 2^20 + 1"),
    err("fir_frequency_sampling.grid_too_short", {"num_points": 5}, "2(num_points - 1) >= num_taps"),
    err("fir_frequency_sampling.kaiser_no_beta", {"window": "kaiser"}, "the Kaiser window needs beta"),
    err("fir_frequency_sampling.beta_without_kaiser", {"beta": 5.0}, "beta only with kaiser"),
    err("fir_frequency_sampling.zero_rate", {"sample_rate": 0, "frequencies": [0, 0]},
        "sample_rate must be > 0"),
]  # fmt: skip

doc = {
    "schema": 1,
    "suite": "frequency_sampling",
    "description": "Frequency-sampling FIR design: a piecewise-linear gain sampled from 0 to fs/2, "
    "inverse DFT with linear phase, symmetric window (conventions: FIR filters, "
    "Frequency-sampling design).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "frequency_sampling.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/frequency_sampling.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
