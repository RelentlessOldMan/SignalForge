"""Writes vectors/cases/stimuli.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. Multitones, Newman phases, linear chirps and pulse trains
(conventions: Tones) are evaluated sample by sample from their formulas with math and cmath.

Run from the repo root: python vectors/generators/stimuli.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}
SRC = "vectors/generators/stimuli.py (stdlib only): "


def multitone(fs, n, freqs, amps, phases, cplx_out):
    out = []
    for i in range(n):
        t = i / fs
        args = [2 * math.pi * f * t + p for f, p in zip(freqs, phases)]
        if cplx_out:
            out.append(sum(a * cmath.exp(1j * x) for a, x in zip(amps, args)))
        else:
            out.append(math.fsum(a * math.cos(x) for a, x in zip(amps, args)))
    return out


def chirp(fs, n, f0, f1, amp, phase, cplx_out):
    duration = n / fs
    out = []
    for i in range(n):
        t = i / fs
        theta = 2 * math.pi * (f0 * t + (f1 - f0) * t * t / (2 * duration)) + phase
        out.append(amp * cmath.exp(1j * theta) if cplx_out else amp * math.cos(theta))
    return out


def cplx(z):
    return {"re": [v.real for v in z], "im": [v.imag for v in z]}


def mt(case_id, fs, n, freqs, amps=None, phases=None, cplx_out=True, expected=None, src=None):
    args = {"sample_rate": fs, "num_samples": n, "frequencies": freqs}
    if amps is not None:
        args["amplitudes"] = amps
    if phases is not None:
        args["phases"] = phases
    if not cplx_out:
        args["complex"] = False
    y = expected if expected is not None else multitone(
        fs, n, freqs, amps or [1.0] * len(freqs), phases or [0.0] * len(freqs), cplx_out)
    return {"id": case_id, "op": "multitone", "args": args, "expected": cplx(y) if cplx_out else y,
            "tol": TOL, "source": src or SRC + "each tone's cos/exp summed sample by sample"}


def ch(case_id, fs, n, f0, f1, amp=None, phase=None, cplx_out=True, expected=None, src=None):
    args = {"sample_rate": fs, "num_samples": n, "start": f0, "stop": f1}
    if amp is not None:
        args["amplitude"] = amp
    if phase is not None:
        args["phase"] = phase
    if not cplx_out:
        args["complex"] = False
    y = expected if expected is not None else chirp(
        fs, n, f0, f1, 1.0 if amp is None else amp, 0.0 if phase is None else phase, cplx_out)
    return {"id": case_id, "op": "chirp", "args": args, "expected": cplx(y) if cplx_out else y,
            "tol": TOL, "source": src or SRC + "theta = 2 pi (f0 t + (f1 - f0) t^2 / 2T) + phase"}


def err(case_id, op, args, why):
    return {"id": case_id, "op": op, "args": args, "error": "invalid_argument", "source": why}


h = math.sqrt(0.5)
cases = [
    mt("multitone.dc_and_nyquist_real", 4.0, 4, [0.0, 2.0], cplx_out=False,
       expected=[2.0, 0.0, 2.0, 0.0], src="by hand: 1 + cos(pi n) = 2, 0, 2, 0"),
    mt("multitone.two_bins_complex", 8.0, 8, [1.0, -2.0], [1.0, 0.5], [0.0, math.pi / 2],
       expected=[cmath.exp(1j * math.pi * k / 4) + 0.5j * cmath.exp(-1j * math.pi * k / 2)
                 for k in range(8)],
       src="by hand: e^(j pi n/4) + 0.5 j e^(-j pi n/2), the 45- and 90-degree samples"),
    mt("multitone.five_tones_newman", 48000.0, 40,
       [1000.0 * (k + 1) for k in range(5)], None, [math.pi * k * k / 5 for k in range(5)]),
    mt("multitone.three_tones_real", 1000.0, 33, [50.0, 123.4, 377.0], [1.0, 0.25, 2.0],
       [0.3, -1.0, 2.5], cplx_out=False),
    mt("multitone.empty", 10.0, 0, [1.0], expected=[], src="zero samples"),
    err("multitone.no_frequencies", "multitone",
        {"sample_rate": 1.0, "num_samples": 4, "frequencies": []}, "at least one frequency"),
    err("multitone.amplitudes_length", "multitone",
        {"sample_rate": 1.0, "num_samples": 4, "frequencies": [0.1, 0.2], "amplitudes": [1.0]},
        "one amplitude per frequency"),
    err("multitone.phases_length", "multitone",
        {"sample_rate": 1.0, "num_samples": 4, "frequencies": [0.1], "phases": [0.0, 1.0]},
        "one phase per frequency"),
    err("multitone.rate_zero", "multitone",
        {"sample_rate": 0.0, "num_samples": 4, "frequencies": [0.1]}, "sample_rate > 0"),
    {"id": "newman_phases.four", "op": "newman_phases", "args": {"count": 4},
     "expected": [0.0, math.pi / 4, math.pi, 9 * math.pi / 4], "tol": TOL,
     "source": "by hand: pi k^2 / 4 for k = 0..3"},
    {"id": "newman_phases.one", "op": "newman_phases", "args": {"count": 1}, "expected": [0.0],
     "tol": TOL, "source": "by hand: pi * 0 / 1"},
    {"id": "newman_phases.seven", "op": "newman_phases", "args": {"count": 7},
     "expected": [math.pi * k * k / 7 for k in range(7)], "tol": TOL,
     "source": SRC + "pi k^2 / 7"},
    err("newman_phases.zero", "newman_phases", {"count": 0}, "count >= 1"),
    ch("chirp.quarter_turns", 4.0, 4, 0.0, 4.0,
       expected=[1 + 0j, complex(h, h), -1 + 0j, complex(h, h)],
       src="by hand: T = 1 s, theta = 4 pi t^2 at t = 0, 1/4, 1/2, 3/4 is 0, pi/4, pi, 9pi/4"),
    ch("chirp.down_real", 4.0, 4, 4.0, 0.0, 2.0, cplx_out=False,
       expected=[2.0, 2 * h, -2.0, 2 * h],
       src="by hand: T = 1 s, theta = 2 pi (4t - 2t^2) at t = 0, 1/4, 1/2, 3/4 is 0, 7pi/4, 3pi, "
       "15pi/4; 2 cos theta = 2, sqrt 2, -2, sqrt 2"),
    ch("chirp.up_complex", 1e6, 64, -2e5, 3e5, 0.5, 1.0),
    ch("chirp.constant_is_a_tone", 1000.0, 16, 125.0, 125.0, cplx_out=False,
       expected=[math.cos(math.pi * k / 4) for k in range(16)],
       src="by hand: start = stop is the tone cos(2 pi 125 n/1000) = cos(pi n/4)"),
    ch("chirp.real_phase", 8000.0, 50, 100.0, 3900.0, 1.5, -0.7, cplx_out=False),
    ch("chirp.empty", 1.0, 0, 0.0, 0.5, expected=[], src="zero samples"),
    err("chirp.rate_zero", "chirp",
        {"sample_rate": 0.0, "num_samples": 4, "start": 0.0, "stop": 1.0}, "sample_rate > 0"),
    err("chirp.negative_samples", "chirp",
        {"sample_rate": 1.0, "num_samples": -1, "start": 0.0, "stop": 1.0}, "num_samples >= 0"),
    {"id": "pulse_train.basic", "op": "pulse_train",
     "args": {"num_samples": 10, "period": 4, "width": 1},
     "expected": [1.0, 0, 0, 0, 1, 0, 0, 0, 1, 0], "tol": TOL,
     "source": "by hand: n mod 4 < 1 at n = 0, 4, 8"},
    {"id": "pulse_train.delay_width_amplitude", "op": "pulse_train",
     "args": {"num_samples": 10, "period": 4, "width": 3, "amplitude": 2.0, "delay": 5},
     "expected": [0.0, 2, 2, 2, 0, 2, 2, 2, 0, 2], "tol": TOL,
     "source": "by hand: (n - 5) mod 4 < 3; n = 0 gives -5 mod 4 = 3, n = 1 gives 0"},
    {"id": "pulse_train.negative_delay", "op": "pulse_train",
     "args": {"num_samples": 8, "period": 4, "width": 1, "delay": -1},
     "expected": [0.0, 0, 0, 1, 0, 0, 0, 1], "tol": TOL,
     "source": "by hand: (n + 1) mod 4 < 1 at n = 3, 7"},
    {"id": "pulse_train.full_width", "op": "pulse_train",
     "args": {"num_samples": 3, "period": 2, "width": 2, "amplitude": -0.5},
     "expected": [-0.5, -0.5, -0.5], "tol": TOL, "source": "by hand: width = period is always on"},
    {"id": "pulse_train.zero_width", "op": "pulse_train",
     "args": {"num_samples": 3, "period": 2, "width": 0},
     "expected": [0.0, 0.0, 0.0], "tol": TOL, "source": "by hand: width 0 is never on"},
    err("pulse_train.period_zero", "pulse_train",
        {"num_samples": 4, "period": 0, "width": 0}, "period >= 1"),
    err("pulse_train.width_over_period", "pulse_train",
        {"num_samples": 4, "period": 2, "width": 3}, "width <= period"),
    err("pulse_train.width_negative", "pulse_train",
        {"num_samples": 4, "period": 2, "width": -1}, "width >= 0"),
]

doc = {
    "schema": 1,
    "suite": "stimuli",
    "description": "Multitones, Newman phases, linear chirps and pulse trains (conventions: Tones).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "stimuli.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/stimuli.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
