"""Writes vectors/cases/fir.json from first principles, using only the Python standard library.

It does not import NumPy or SignalForge. The ideal impulse responses come from numerically
integrating the brick-wall spectrum (composite Simpson's rule), not from the sinc closed form the
library uses, so the two meet only if both are right. The windows are evaluated straight from the
cosine-sum and Kaiser definitions in docs/conventions.md, with I0 from its power series.

Run from the repo root: python vectors/generators/fir.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import json
import math
import pathlib
import sys

PANELS = 40000  # Simpson panels per band; the integration error is far below the 1e-12 tolerance

COSINE_SUMS = {
    "rectangular": [1.0],
    "hann": [0.5, 0.5],
    "hamming": [0.54, 0.46],
    "blackman": [0.42, 0.5, 0.08],
}


def simpson(f, a, b, n=PANELS):
    h = (b - a) / n
    terms = [f(a), f(b)]
    terms += [(4 if i % 2 else 2) * f(a + i * h) for i in range(1, n)]
    return math.fsum(terms) * h / 3


def ideal(bands, t):
    """Inverse DTFT of a real, even, unit-height response over the bands (normalized freq.):
    d[t] = 2 * integral of cos(2 pi nu t) over each band (lo, hi) on the positive axis."""
    return math.fsum(
        2 * simpson(lambda nu: math.cos(2 * math.pi * nu * t), lo, hi) for lo, hi in bands
    )


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
        return [
            bessel_i0(beta * math.sqrt(1 - (2 * i / d - 1) ** 2)) / bessel_i0(beta)
            for i in range(n)
        ]
    a = COSINE_SUMS[name]
    return [
        math.fsum((-1) ** k * a[k] * math.cos(2 * math.pi * k * i / d) for k in range(len(a)))
        for i in range(n)
    ]


def design(n, bands, reference, name, beta=None):
    w = window(name, n, beta)
    ts = [i - (n - 1) / 2 for i in range(n)]
    h = [ideal(bands, t) * wi for t, wi in zip(ts, w)]
    gain = math.fsum(hi * math.cos(2 * math.pi * reference * t) for hi, t in zip(h, ts))
    return [x / gain for x in h]


SOURCE = (
    "vectors/generators/fir.py (stdlib only): ideal response by Simpson integration of the "
    "brick-wall spectrum, times the symmetric {w} window from its definition, scaled to unit "
    "zero-phase gain at {ref}"
)
TOL = {"abs": 1e-12, "rel": 0}


def designed(case_id, op, args, bands, reference, ref_text):
    w = args.get("window", "hamming")
    taps = design(args["num_taps"], bands, reference, w, args.get("beta"))
    return {
        "id": case_id,
        "op": op,
        "args": args,
        "expected": taps,
        "tol": TOL,
        "source": SOURCE.format(w=w, ref=ref_text),
    }


def kaiser(case_id, a, df, fs, beta_text):
    dw = 2 * math.pi * df / fs
    beta = (
        0.1102 * (a - 8.7)
        if a > 50
        else 0.5842 * (a - 21) ** 0.4 + 0.07886 * (a - 21)
        if a >= 21
        else 0.0
    )
    m = max(0, math.ceil((a - 8) / (2.285 * dw)))
    return {
        "id": case_id,
        "op": "kaiser_parameters",
        "args": {"attenuation_db": a, "transition_width": df, "sample_rate": fs},
        "expected": [m + 1, beta],
        "tol": {"abs": 1e-12, "rel": 1e-12},
        "source": f"Kaiser's formulas (Oppenheim and Schafer): {beta_text}; "
        f"M = ceil(({a} - 8)/(2.285*2pi*{df}/{fs})) = {m}",
    }


def err(case_id, op, args, why):
    return {"id": case_id, "op": op, "args": args, "error": "invalid_argument", "source": why}


inv_pi = 1 / math.pi
c3 = [inv_pi, 0.5, inv_pi]
g3 = 0.5 + 2 * inv_pi

cases = [
    designed(
        "fir_lowpass.hamming_21",
        "fir_lowpass",
        {"num_taps": 21, "cutoff": 100, "sample_rate": 1000},
        [(0, 0.1)],
        0,
        "DC",
    ),
    designed(
        "fir_lowpass.even_8_hann",
        "fir_lowpass",
        {"num_taps": 8, "cutoff": 125, "sample_rate": 1000, "window": "hann"},
        [(0, 0.125)],
        0,
        "DC",
    ),
    designed(
        "fir_lowpass.kaiser_15",
        "fir_lowpass",
        {"num_taps": 15, "cutoff": 0.2, "sample_rate": 1, "window": "kaiser", "beta": 5.0},
        [(0, 0.2)],
        0,
        "DC",
    ),
    {
        "id": "fir_lowpass.rect_3_quarter",
        "op": "fir_lowpass",
        "args": {"num_taps": 3, "cutoff": 250, "sample_rate": 1000, "window": "rectangular"},
        "expected": [x / g3 for x in c3],
        "tol": TOL,
        "source": "by hand: d = 0.5 sinc(0.5 t) at t = -1, 0, 1 is [1/pi, 1/2, 1/pi]; divided by its sum 1/2 + 2/pi",
    },
    {
        "id": "fir_lowpass.single_tap",
        "op": "fir_lowpass",
        "args": {"num_taps": 1, "cutoff": 100, "sample_rate": 1000},
        "expected": [1.0],
        "tol": TOL,
        "source": "one tap scaled to unit gain at DC is [1]",
    },
    designed(
        "fir_highpass.hamming_21",
        "fir_highpass",
        {"num_taps": 21, "cutoff": 300, "sample_rate": 1000},
        [(0.3, 0.5)],
        0.5,
        "fs/2",
    ),
    designed(
        "fir_highpass.blackman_31",
        "fir_highpass",
        {"num_taps": 31, "cutoff": 2000, "sample_rate": 48000, "window": "blackman"},
        [(2000 / 48000, 0.5)],
        0.5,
        "fs/2",
    ),
    {
        "id": "fir_highpass.rect_3_quarter",
        "op": "fir_highpass",
        "args": {"num_taps": 3, "cutoff": 250, "sample_rate": 1000, "window": "rectangular"},
        "expected": [
            -inv_pi / (0.5 + 2 * inv_pi),
            0.5 / (0.5 + 2 * inv_pi),
            -inv_pi / (0.5 + 2 * inv_pi),
        ],
        "tol": TOL,
        "source": "by hand: d = sinc(t) - 0.5 sinc(0.5 t) = [-1/pi, 1/2, -1/pi]; gain at fs/2 is "
        "1/2 + 2/pi (cos(pi t) = -1 at t = +-1)",
    },
    designed(
        "fir_bandpass.hamming_41",
        "fir_bandpass",
        {"num_taps": 41, "low": 100, "high": 200, "sample_rate": 1000},
        [(0.1, 0.2)],
        0.15,
        "the band center 150 Hz",
    ),
    designed(
        "fir_bandpass.kaiser_33",
        "fir_bandpass",
        {
            "num_taps": 33,
            "low": 0.05,
            "high": 0.3,
            "sample_rate": 1,
            "window": "kaiser",
            "beta": 8.6,
        },
        [(0.05, 0.3)],
        0.175,
        "the band center 0.175",
    ),
    kaiser("kaiser_parameters.a60", 60, 50, 1000, "A > 50, beta = 0.1102*(60 - 8.7)"),
    kaiser(
        "kaiser_parameters.a30", 30, 100, 1000, "21 <= A <= 50, beta = 0.5842*9^0.4 + 0.07886*9"
    ),
    kaiser(
        "kaiser_parameters.a50",
        50,
        2,
        48,
        "A = 50 is in the middle band: 0.5842*29^0.4 + 0.07886*29",
    ),
    kaiser("kaiser_parameters.a21", 21, 10, 100, "A = 21: beta = 0.5842*0^0.4 + 0 = 0"),
    kaiser("kaiser_parameters.a15", 15, 10, 100, "A < 21, beta = 0"),
    kaiser("kaiser_parameters.a5_order0", 5, 10, 100, "A < 8 makes the order negative, so M = 0"),
    {
        "id": "fir_response.pair",
        "op": "fir_response",
        "args": {"taps": [1, 1], "frequencies": [0, 250, 500, -250], "sample_rate": 1000},
        "expected": {"re": [2, 1, 0, 1], "im": [0, -1, 0, 1]},
        "tol": TOL,
        "source": "by hand: 1 + e^(-j2 pi f/fs) is 2, 1 - j, 0, 1 + j",
    },
    {
        "id": "fir_response.three",
        "op": "fir_response",
        "args": {"taps": [1, 2, 3], "frequencies": [0, 0.5, 1], "sample_rate": 1},
        "expected": {"re": [6, 2, 6], "im": [0, 0, 0]},
        "tol": TOL,
        "source": "by hand: H(0) = 1+2+3; H(fs/2) = 1-2+3; H(fs) = H(0)",
    },
    {
        "id": "fir_response.empty_freqs",
        "op": "fir_response",
        "args": {"taps": [1], "frequencies": [], "sample_rate": 1},
        "expected": {"re": [], "im": []},
        "source": "no frequencies, no values",
    },
    {
        "id": "fir_filter.chunks",
        "op": "fir_filter",
        "args": {"taps": [1, 2, 3], "samples": [1, 0, 0, 1, 1], "chunks": [2, 0, 3]},
        "expected": [1, 2, 3, 1, 3],
        "tol": TOL,
        "source": "by hand: y[n] = x[n] + 2x[n-1] + 3x[n-2], state carried across the chunks",
    },
    {
        "id": "fir_filter.one_chunk",
        "op": "fir_filter",
        "args": {"taps": [1, 2, 3], "samples": [1, 0, 0, 1, 1], "chunks": [5]},
        "expected": [1, 2, 3, 1, 3],
        "tol": TOL,
        "source": "the same as fir_filter.chunks in one chunk",
    },
    {
        "id": "fir_filter.complex",
        "op": "fir_filter",
        "args": {
            "taps": [1, -1],
            "samples": {"re": [0, 1, 1], "im": [1, 0, 1]},
            "chunks": [1, 1, 1],
        },
        "expected": {"re": [0, 1, 0], "im": [1, -1, 1]},
        "tol": TOL,
        "source": "by hand: y[n] = x[n] - x[n-1] for x = [j, 1, 1+j] is [j, 1-j, j]",
    },
    {
        "id": "fir_filter.short_chunks_long_taps",
        "op": "fir_filter",
        "args": {"taps": [0, 0, 0, 1], "samples": [5, 6, 7, 8, 9], "chunks": [1, 1, 3]},
        "expected": [0, 0, 0, 5, 6],
        "tol": TOL,
        "source": "a pure 3-sample delay, chunks shorter than the state",
    },
    err(
        "fir_lowpass.cutoff_zero",
        "fir_lowpass",
        {"num_taps": 5, "cutoff": 0, "sample_rate": 1000},
        "0 < cutoff required",
    ),
    err(
        "fir_lowpass.cutoff_nyquist",
        "fir_lowpass",
        {"num_taps": 5, "cutoff": 500, "sample_rate": 1000},
        "cutoff < fs/2 required",
    ),
    err(
        "fir_lowpass.zero_taps",
        "fir_lowpass",
        {"num_taps": 0, "cutoff": 100, "sample_rate": 1000},
        "num_taps >= 1 required",
    ),
    err(
        "fir_lowpass.bad_rate",
        "fir_lowpass",
        {"num_taps": 5, "cutoff": 100, "sample_rate": 0},
        "sample_rate must be positive",
    ),
    err(
        "fir_lowpass.kaiser_no_beta",
        "fir_lowpass",
        {"num_taps": 5, "cutoff": 100, "sample_rate": 1000, "window": "kaiser"},
        "kaiser needs beta",
    ),
    err(
        "fir_lowpass.beta_not_kaiser",
        "fir_lowpass",
        {"num_taps": 5, "cutoff": 100, "sample_rate": 1000, "beta": 3},
        "beta is only allowed for kaiser",
    ),
    err(
        "fir_lowpass.zero_window",
        "fir_lowpass",
        {"num_taps": 2, "cutoff": 100, "sample_rate": 1000, "window": "hann"},
        "the symmetric Hann window of length 2 is [0, 0], so the taps have no gain to scale",
    ),
    err(
        "fir_highpass.even_taps",
        "fir_highpass",
        {"num_taps": 8, "cutoff": 100, "sample_rate": 1000},
        "a high-pass needs an odd num_taps",
    ),
    err(
        "fir_bandpass.reversed",
        "fir_bandpass",
        {"num_taps": 11, "low": 200, "high": 100, "sample_rate": 1000},
        "low < high required",
    ),
    err(
        "fir_bandpass.equal",
        "fir_bandpass",
        {"num_taps": 11, "low": 100, "high": 100, "sample_rate": 1000},
        "low < high required",
    ),
    err(
        "kaiser_parameters.zero_attenuation",
        "kaiser_parameters",
        {"attenuation_db": 0, "transition_width": 10, "sample_rate": 100},
        "A > 0 required",
    ),
    err(
        "kaiser_parameters.width_nyquist",
        "kaiser_parameters",
        {"attenuation_db": 40, "transition_width": 50, "sample_rate": 100},
        "transition_width < fs/2 required",
    ),
    err(
        "fir_response.empty_taps",
        "fir_response",
        {"taps": [], "frequencies": [0], "sample_rate": 1},
        "taps must be non-empty",
    ),
    err(
        "fir_filter.empty_taps",
        "fir_filter",
        {"taps": [], "samples": [1], "chunks": [1]},
        "taps must be non-empty",
    ),
    err(
        "fir_filter.nan_tap",
        "fir_filter",
        {"taps": [1, "nan"], "samples": [1], "chunks": [1]},
        "taps must be finite",
    ),
]

doc = {
    "schema": 1,
    "suite": "fir",
    "description": "FIR design (windowed sinc, Kaiser parameters), frequency response and the "
    "streaming FIR filter (conventions: FIR filters).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "fir.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]


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
        sys.exit(f"{out} is out of date: run python vectors/generators/fir.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")


# Self-check against the closed form (which this script otherwise never uses).
def sinc(x):
    return 1.0 if x == 0 else math.sin(math.pi * x) / (math.pi * x)


worst = max(
    abs(ideal([(0.05, 0.3)], t) - (0.6 * sinc(0.6 * t) - 0.1 * sinc(0.1 * t)))
    for t in range(-20, 21)
)
print(f"wrote {out} ({len(cases)} cases); Simpson vs closed form, worst {worst:.1e}")
