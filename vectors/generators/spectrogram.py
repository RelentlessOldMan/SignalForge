"""Writes vectors/cases/spectrogram.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. Each segment's spectrum is the DFT summed term by term,
X[k] = sum_n w[n] x[s*step + n] e^(-j 2 pi k n / N), scaled by 1/(fs * sum w^2) and folded to one
or two sides as conventions: Spectra (PSD, Spectrogram) says. Windows are the periodic cosine sums.

Run from the repo root: python vectors/generators/spectrogram.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
COSINE_SUMS = {"rectangular": [1.0], "hann": [0.5, 0.5], "blackman": [0.42, 0.5, 0.08]}


def window(name, n):
    a = COSINE_SUMS[name]
    return [math.fsum((-1) ** k * c * math.cos(2 * math.pi * k * i / n) for k, c in enumerate(a))
            for i in range(n)]


def spectrogram(x, fs, n, noverlap=None, name="hann", one_sided=None):
    is_complex = any(isinstance(v, complex) for v in x)
    if one_sided is None:
        one_sided = not is_complex
    overlap = n // 2 if noverlap is None else noverlap
    step = n - overlap
    count = (len(x) - n) // step + 1
    w = window(name, n)
    scale = 1 / (fs * math.fsum(v * v for v in w))
    rows = []
    for s in range(count):
        seg = [w[i] * x[s * step + i] for i in range(n)]
        p = [abs(sum(seg[i] * cmath.exp(-2j * math.pi * k * i / n) for i in range(n))) ** 2 * scale
             for k in range(n)]
        if one_sided:
            m = n // 2 + 1
            last = m - 1 if n % 2 == 0 else m
            rows.append([p[k] * (2 if 1 <= k < last else 1) for k in range(m)])
        else:
            rows.append([p[(i - n // 2) % n] for i in range(n)])
    if one_sided:
        freqs = [k * fs / n for k in range(n // 2 + 1)]
    else:
        freqs = [(i - n // 2) * fs / n for i in range(n)]
    s1, s2 = math.fsum(w), math.fsum(v * v for v in w)
    return {
        "frequencies": freqs,
        "times": [(s * step + n / 2) / fs for s in range(count)],
        "psd": rows,
        "sample_rate": fs,
        "nperseg": n,
        "num_segments": count,
        "one_sided": one_sided,
        "bin_width": fs / n,
        "enbw_hz": n * s2 / s1**2 * fs / n,
    }


def cplx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


SRC = (
    "vectors/generators/spectrogram.py (stdlib only): each segment's DFT summed term by term, "
    "scaled and folded per conventions: Spectra"
)


def gen(case_id, x, fs, n, src=SRC, psd=None, **kw):
    args = {"samples": cplx(x) if any(isinstance(v, complex) for v in x) else x, "sample_rate": fs,
            "nperseg": n}
    opts = {"noverlap": "noverlap", "name": "window", "one_sided": "one_sided"}
    args |= {opts[k]: v for k, v in kw.items()}
    expected = spectrogram(x, fs, n, **kw)
    if psd is not None:  # a hand derivation replaces the sums
        expected["psd"] = psd
    return {"id": case_id, "op": "spectrogram", "args": args, "expected": expected, "tol": TOL,
            "source": src}


def err(case_id, args, why):
    return {"id": case_id, "op": "spectrogram", "args": args, "error": "invalid_argument",
            "source": why}


ramp = [float(i % 5) - 2 + 0.25 * math.sin(0.7 * i) for i in range(24)]
chirp = [cmath.exp(1j * (0.3 * i + 0.02 * i * i)) * (1 + 0.1 * i) for i in range(20)]
tone = [cmath.exp(2j * math.pi * i / 4) for i in range(8)]

cases = [
    gen("spectrogram.real_hann", ramp, 1000.0, 8),
    gen("spectrogram.real_hann_odd", ramp, 1000.0, 7),
    gen("spectrogram.real_no_overlap", ramp, 2.0, 6, noverlap=0, name="rectangular"),
    gen("spectrogram.real_overlap_5", ramp, 1.0, 8, noverlap=5, name="blackman"),
    gen("spectrogram.real_two_sided", ramp, 1000.0, 8, one_sided=False),
    gen("spectrogram.real_whole", ramp[:9], 3.0, 9, name="rectangular"),
    gen("spectrogram.complex_hann", chirp, 1e6, 8),
    gen("spectrogram.complex_odd_rect", chirp, 1e6, 5, noverlap=1, name="rectangular"),
    gen("spectrogram.complex_tone_rect", tone, 4.0, 4, noverlap=0, name="rectangular",
        psd=[[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0]],
        src="by hand: e^(j pi n/2) is a unit tone at bin 1 of 4; each row has A^2*N/fs = 4/4 = 1 at "
        "+1 Hz (shifted index 3) and 0 elsewhere; segments centered at 0.5 s and 1.5 s"),
    err("spectrogram.nperseg_zero", {"samples": ramp, "sample_rate": 1.0, "nperseg": 0},
        "nperseg >= 1 required"),
    err("spectrogram.nperseg_too_long", {"samples": ramp, "sample_rate": 1.0, "nperseg": 25},
        "nperseg <= number of samples required"),
    err("spectrogram.noverlap_equal", {"samples": ramp, "sample_rate": 1.0, "nperseg": 8,
                                       "noverlap": 8}, "noverlap < nperseg required"),
    err("spectrogram.rate_zero", {"samples": ramp, "sample_rate": 0.0, "nperseg": 4},
        "sample_rate must be positive"),
    err("spectrogram.noverlap_negative", {"samples": ramp, "sample_rate": 1.0, "nperseg": 8,
                                          "noverlap": -1}, "noverlap >= 0 required"),
    err("spectrogram.rate_nan", {"samples": ramp, "sample_rate": "nan", "nperseg": 4},
        "sample_rate must be finite"),
]

doc = {
    "schema": 1,
    "suite": "spectrogram",
    "description": "Spectrograms: Welch segments kept one per row (conventions: Spectra, "
    "Spectrogram).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "spectrogram.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/spectrogram.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
