"""Writes vectors/cases/welch.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. Each segment is detrended by the conventions' formulas
(the line fitted by solving the 2x2 normal equations directly), windowed, and transformed by the
DFT summed term by term; the powers are averaged by the mean or by the median divided by b(K), the
expected median of K unit-mean exponential values. b(K) is checked against a numerical integral
of the order-statistic densities. Windows are the periodic cosine sums.

Run from the repo root: python vectors/generators/welch.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import statistics
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
COSINE_SUMS = {"rectangular": [1.0], "hann": [0.5, 0.5], "blackman": [0.42, 0.5, 0.08]}


def window(name, n):
    a = COSINE_SUMS[name]
    return [math.fsum((-1) ** k * c * math.cos(2 * math.pi * k * i / n) for k, c in enumerate(a))
            for i in range(n)]  # fmt: skip


def detrended(seg, how):
    n = len(seg)
    if how == "none":
        return seg
    if how == "constant":
        m = sum(seg) / n
        return [v - m for v in seg]
    # The line p + q*i minimizing sum |x[i] - p - q*i|^2: the 2x2 normal equations, solved by
    # Cramer's rule (the conventions centre the abscissa instead; the line is the same).
    s0, s1, s2 = n, sum(range(n)), sum(i * i for i in range(n))
    y0, y1 = sum(seg), sum(i * v for i, v in enumerate(seg))
    det = s0 * s2 - s1 * s1
    if det == 0:
        p, q = y0 / s0, 0
    else:
        p, q = (y0 * s2 - y1 * s1) / det, (s0 * y1 - s1 * y0) / det
    return [v - p - q * i for i, v in enumerate(seg)]


def exp_median_by_integral(k):
    """E[median of k unit exponentials] from the order-statistic densities, by Simpson's rule."""

    def order_mean(r):
        c = math.factorial(k) / (math.factorial(r - 1) * math.factorial(k - r))

        def f(x):
            e = math.exp(-x)
            return x * c * (1 - e) ** (r - 1) * e ** (k - r) * e

        n, hi = 40000, 60.0
        h = hi / n
        s = f(0) + f(hi) + 4 * math.fsum(f((i + 0.5) * h) for i in range(n))
        s += 2 * math.fsum(f(i * h) for i in range(1, n))
        return s * h / 6

    if k % 2 == 1:
        return order_mean(k // 2 + 1)
    return (order_mean(k // 2) + order_mean(k // 2 + 1)) / 2


def bias(k):
    b = math.fsum(1 / i for i in range(k // 2 + 1, k + 1))
    return b + 1 / k if k % 2 == 0 else b


for _k in range(1, 9):
    assert abs(bias(_k) - exp_median_by_integral(_k)) < 1e-10, _k


def rows(x, fs, n, noverlap, name, detrend):
    overlap = n // 2 if noverlap is None else noverlap
    step = n - overlap
    count = (len(x) - n) // step + 1
    w = window(name, n)
    scale = 1 / (fs * math.fsum(v * v for v in w))
    out = []
    for s in range(count):
        seg = detrended(list(x[s * step : s * step + n]), detrend)
        seg = [w[i] * seg[i] for i in range(n)]
        out.append([abs(sum(seg[i] * cmath.exp(-2j * math.pi * k * i / n) for i in range(n))) ** 2
                    * scale for k in range(n)])  # fmt: skip
    return out, step, w


def fold(p, n, one_sided):
    if one_sided:
        m = n // 2 + 1
        last = m - 1 if n % 2 == 0 else m
        return [p[k] * (2 if 1 <= k < last else 1) for k in range(m)]
    return [p[(i - n // 2) % n] for i in range(n)]


def freqs(n, fs, one_sided):
    if one_sided:
        return [k * fs / n for k in range(n // 2 + 1)]
    return [(i - n // 2) * fs / n for i in range(n)]


def welch(x, fs, n, noverlap=None, window="hann", one_sided=None, detrend="none", average="mean"):
    if one_sided is None:
        one_sided = not any(isinstance(v, complex) for v in x)
    r, _, w = rows(x, fs, n, noverlap, window, detrend)
    if average == "mean":
        p = [math.fsum(row[k] for row in r) / len(r) for k in range(n)]
    else:
        p = [statistics.median(row[k] for row in r) / bias(len(r)) for k in range(n)]
    s1, s2 = math.fsum(w), math.fsum(v * v for v in w)
    return {
        "frequencies": freqs(n, fs, one_sided),
        "psd": fold(p, n, one_sided),
        "sample_rate": fs,
        "nperseg": n,
        "num_segments": len(r),
        "one_sided": one_sided,
        "bin_width": fs / n,
        "enbw_hz": n * s2 / s1**2 * fs / n,
    }


def spectrogram(x, fs, n, noverlap=None, name="hann", detrend="none"):
    r, step, w = rows(x, fs, n, noverlap, name, detrend)
    s1, s2 = math.fsum(w), math.fsum(v * v for v in w)
    return {
        "frequencies": freqs(n, fs, True),
        "times": [(s * step + n / 2) / fs for s in range(len(r))],
        "psd": [fold(row, n, True) for row in r],
        "num_segments": len(r),
        "enbw_hz": n * s2 / s1**2 * fs / n,
    }


def cplx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


SRC = (
    "vectors/generators/welch.py (stdlib only): detrend by the normal equations, the DFT summed "
    "term by term, mean or median / b(K) with b(K) checked by integrating order-statistic densities"
)


def gen(case_id, x, fs, n, **kw):
    args = {"samples": cplx(x) if any(isinstance(v, complex) for v in x) else x,
            "sample_rate": fs, "nperseg": n, **kw}  # fmt: skip
    return {"id": case_id, "op": "welch_psd", "args": args,
            "expected": welch(x, fs, n, **kw), "tol": TOL, "source": SRC}  # fmt: skip


def hand(case_id, args, psd, why, op="welch_psd"):
    return {"id": case_id, "op": op, "args": args, "expected": {"psd": psd},
            "tol": TOL, "source": "by hand: " + why}  # fmt: skip


def err(case_id, args, why, op="welch_psd"):
    base = {"samples": [1.0, 2.0, 3.0, 4.0], "sample_rate": 1.0, "nperseg": 2}
    return {"id": case_id, "op": op, "args": {**base, **args}, "error": "invalid_argument",
            "source": why}  # fmt: skip


noisy = [math.sin(0.9 * i) + 0.4 * math.cos(2.3 * i * i % 7) + 0.05 * i for i in range(40)]
burst = [math.cos(2 * math.pi * 0.125 * i) + (6.0 if 17 <= i < 20 else 0.0) for i in range(48)]
chirp = [cmath.exp(1j * (0.4 * i + 0.03 * i * i)) + 0.2 + 0.01j * i for i in range(30)]
rect = {"window": "rectangular", "noverlap": 0}

cases = [
    hand("welch_psd.constant_detrend_removes_dc", {"samples": [3.0] * 8, "sample_rate": 1.0,
         "nperseg": 4, "detrend": "constant", **rect}, [0, 0, 0],
         "a constant minus its mean is zero in every segment"),
    hand("welch_psd.linear_detrend_removes_ramp", {"samples": [2.0 + 0.5 * i for i in range(8)],
         "sample_rate": 1.0, "nperseg": 4, "detrend": "linear"}, [0, 0, 0],
         "a line minus its least-squares line is zero in every segment"),
    hand("welch_psd.median_of_three", {"samples": [1.0, 1.0, 2.0, 2.0, 5.0, 5.0],
         "sample_rate": 1.0, "nperseg": 2, "average": "median", **rect}, [9.6, 0],
         "segments [1,1], [2,2], [5,5]: |X0|^2/(fs*sum w^2) = 4/2, 16/2, 100/2; the median 8 over "
         "b(3) = 1/2 + 1/3 = 5/6 is 9.6 (the mean would be 20); Nyquist is 0"),
    hand("welch_psd.median_of_two_is_the_mean", {"samples": [1.0, 1.0, 3.0, 3.0],
         "sample_rate": 1.0, "nperseg": 2, "average": "median", **rect}, [10, 0],
         "two segments: the median is the mean of 2 and 18, and b(2) = 1/2 + 1/2 = 1"),
    hand("welch_psd.median_of_four", {"samples": [1.0, 1.0, 2.0, 2.0, 3.0, 3.0, 10.0, 10.0],
         "sample_rate": 1.0, "nperseg": 2, "average": "median", **rect}, [15.6, 0],
         "DC powers 2, 8, 18, 200: the median (8 + 18)/2 = 13 over b(4) = 1/3 + 1/4 + 1/4 = 5/6"),
    gen("welch_psd.detrend_constant_hann", noisy, 100.0, 16, detrend="constant"),
    gen("welch_psd.detrend_linear_hann", noisy, 100.0, 16, detrend="linear"),
    gen("welch_psd.detrend_linear_odd_blackman", noisy, 1.0, 9, noverlap=3, window="blackman",
        detrend="linear"),
    gen("welch_psd.detrend_linear_one_sample", noisy[:5], 1.0, 1, noverlap=0, window="rectangular",
        detrend="linear"),
    gen("welch_psd.median_burst", burst, 8.0, 8, noverlap=0, average="median"),
    gen("welch_psd.median_overlap_even_count", burst, 8.0, 10, noverlap=5, average="median"),
    gen("welch_psd.median_and_detrend_two_sided", noisy, 2.0, 10, one_sided=False,
        detrend="constant", average="median"),
    gen("welch_psd.complex_detrend_linear", chirp, 1e3, 8, detrend="linear"),
    gen("welch_psd.complex_median", chirp, 1e3, 7, noverlap=2, window="blackman", average="median"),
    gen("welch_psd.mean_is_the_default", noisy, 1.0, 8, average="mean", detrend="none"),
    {"id": "spectrogram.detrend_linear", "op": "spectrogram",
     "args": {"samples": noisy, "sample_rate": 10.0, "nperseg": 10, "detrend": "linear"},
     "expected": spectrogram(noisy, 10.0, 10, detrend="linear"), "tol": TOL, "source": SRC},
    {"id": "spectrogram.detrend_constant_rect", "op": "spectrogram",
     "args": {"samples": noisy, "sample_rate": 1.0, "nperseg": 7, "noverlap": 2,
              "window": "rectangular", "detrend": "constant"},
     "expected": spectrogram(noisy, 1.0, 7, 2, "rectangular", "constant"), "tol": TOL,
     "source": SRC},
    err("welch_psd.unknown_detrend", {"detrend": "quadratic"}, "detrend is none, constant, linear"),
    err("welch_psd.unknown_average", {"average": "max"}, "average is mean or median"),
    err("spectrogram.unknown_detrend", {"detrend": "cubic"}, "detrend is none, constant, linear",
        op="spectrogram"),
]  # fmt: skip

# The hand values are also what the generator's sums give.
for c in cases[:5]:
    a = c["args"]
    got = welch(a["samples"], a["sample_rate"], a["nperseg"], a.get("noverlap"),
                a.get("window", "hann"), None, a.get("detrend", "none"), a.get("average", "mean"))  # fmt: skip
    assert all(abs(x - y) < 1e-12 for x, y in zip(got["psd"], c["expected"]["psd"], strict=True))

doc = {
    "schema": 1,
    "suite": "welch",
    "description": "Welch options: per-segment detrending and median averaging (conventions: "
    "Spectra, PSD and Spectrogram).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "welch.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/welch.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
