"""Writes vectors/cases/group_delay.json from the definitions, using only the Python standard library.

It does not import NumPy or SignalForge. Each generated case starts from chosen roots: the taps (or
a section's coefficients) are the expanded product g * z^-d * prod (1 - q z^-1), and the expected
delay is d plus the sum over the roots of the closed-form delay of one first-order factor,
Re(-q e^(-jw) / (1 - q e^(-jw))) (each zero on the unit circle gives 1/2 away from its angle). That is
a different formula from the conventions' Re(R/P) on the expanded polynomial, which the library
uses. The other cases are by hand.

Run from the repo root: python vectors/generators/group_delay.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write (numbers
within 1e-14, since C math libraries can differ in the last bit).
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-9, "rel": 1e-9}


def expand(roots, gain=1.0, delay=0):
    """Real coefficients of gain * z^-delay * prod (1 - q z^-1), roots in conjugate pairs."""
    c = [complex(gain)]
    for q in roots:
        c = [a - q * b for a, b in zip([*c, 0], [0, *c], strict=True)]
    assert all(abs(v.imag) < 1e-12 for v in c)
    return [0.0] * delay + [v.real for v in c]


def root_delay(q, nu):
    e = cmath.exp(-2j * math.pi * nu)
    return (-q * e / (1 - q * e)).real


def delay_from_roots(roots, delay, nu):
    return delay + math.fsum(root_delay(q, nu) for q in roots)


def pair(r, angle):
    return [cmath.rect(r, angle), cmath.rect(r, -angle)]


SRC = (
    "vectors/generators/group_delay.py (stdlib only): taps expanded from chosen roots; expected is "
    "the sum over the roots of each first-order factor's closed-form delay"
)


def fir_case(case_id, roots, gain, delay, freqs, fs):
    taps = expand(roots, gain, delay)
    tau = [delay_from_roots(roots, delay, f / fs) for f in freqs]
    return {"id": case_id, "op": "fir_group_delay",
            "args": {"taps": taps, "frequencies": freqs, "sample_rate": fs},
            "expected": tau, "tol": TOL, "source": SRC}  # fmt: skip


def section(zeros, poles, gain):
    b = expand(zeros, gain)
    a = expand(poles)
    return [*b, 0.0, 0.0][:3] + [*a, 0.0, 0.0][:3]


def sos_case(case_id, sections, freqs, fs):
    """sections: (zeros, poles, gain) with at most two of each."""
    sos = [section(z, p, g) for z, p, g in sections]
    tau = [
        math.fsum(
            delay_from_roots(z, 0, f / fs) - delay_from_roots(p, 0, f / fs) for z, p, _ in sections
        )
        for f in freqs
    ]
    return {"id": case_id, "op": "sos_group_delay",
            "args": {"sos": sos, "frequencies": freqs, "sample_rate": fs},
            "expected": tau, "tol": TOL, "source": SRC + "; zeros minus poles per section"}  # fmt: skip


def hand(case_id, op, args, expected, why):
    return {"id": case_id, "op": op, "args": args, "expected": expected, "tol": TOL,
            "source": "by hand: " + why}  # fmt: skip


def err(case_id, op, args, why):
    return {"id": case_id, "op": op, "args": args, "error": "invalid_argument", "source": why}


grid = [i / 20 for i in range(11)]  # 0 ... 0.5
hz = [i * 400.0 for i in range(11)]  # 0 ... 4000 Hz at 8000 Hz
p = 0.5

cases = [
    hand("fir_group_delay.pure_delay", "fir_group_delay",
         {"taps": [0, 0, 0, 1], "frequencies": [0, 0.1, 0.37], "sample_rate": 1}, [3, 3, 3],
         "H = e^(-j3w), phase -3w, delay 3"),
    hand("fir_group_delay.symmetric", "fir_group_delay",
         {"taps": [1, 2, 3, 2, 1], "frequencies": [0, 0.1, 0.25, 0.45], "sample_rate": 1},
         [2, 2, 2, 2], "symmetric taps are linear phase, (N - 1)/2 = 2 wherever H != 0"),
    hand("fir_group_delay.zero_on_circle_nan", "fir_group_delay",
         {"taps": [1, 2, 3, 2, 1], "frequencies": [1, 0.3], "sample_rate": 3}, ["nan", 2],
         "1 + 2z + 3z^2 + 2z^3 + z^4 = (1 + z + z^2)^2 has zeros at e^(+-j2pi/3), so H(fs/3) = 0 "
         "(to rounding) and the conventions give NaN; elsewhere 2"),
    hand("fir_group_delay.two_taps_nyquist", "fir_group_delay",
         {"taps": [1, 1], "frequencies": [0.2, 0.5], "sample_rate": 1}, [0.5, "nan"],
         "1 + e^(-jw) = 2 cos(w/2) e^(-jw/2): delay 1/2, and H(fs/2) = 0 is NaN"),
    hand("fir_group_delay.first_order", "fir_group_delay",
         {"taps": [1, 0.5], "frequencies": [0, 0.25, 0.5], "sample_rate": 1}, [1 / 3, 0.2, -1],
         "P = 1 + a e^(-jw), Re(R/P) = (a cos w + a^2)/(1 + 2a cos w + a^2), a = 0.5: "
         "0.75/2.25, 0.25/1.25, -0.25/0.25"),
    fir_case("fir_group_delay.minimum_phase_hz", [*pair(0.9, 0.7), 0.5, -0.3, *pair(0.8, 2.0)],
             2.0, 1, hz, 8000.0),
    fir_case("fir_group_delay.maximum_phase_roots", [*pair(1.6, 1.1), 0.4, *pair(0.3, 2.9)],
             -0.7, 0, grid, 1.0),
    err("fir_group_delay.empty_taps", "fir_group_delay",
        {"taps": [], "frequencies": [0], "sample_rate": 1}, "taps must be non-empty"),
    err("fir_group_delay.nan_frequency", "fir_group_delay",
        {"taps": [1], "frequencies": ["nan"], "sample_rate": 1}, "frequencies must be finite"),
    err("fir_group_delay.zero_rate", "fir_group_delay",
        {"taps": [1], "frequencies": [0], "sample_rate": 0}, "sample_rate must be > 0"),
    hand("sos_group_delay.one_pole", "sos_group_delay",
         {"sos": [[1, 0, 0, 1, -p, 0]], "frequencies": [0, 0.25, 0.5], "sample_rate": 1},
         [1, -0.2, -1 / 3],
         "1/(1 - p z^-1): -Re(-p e^(-jw)/(1 - p e^(-jw))) = (p cos w - p^2)/(1 - 2p cos w + p^2), "
         "p = 0.5: 0.25/0.25, -0.25/1.25, -0.75/2.25"),
    hand("sos_group_delay.a0_scaled", "sos_group_delay",
         {"sos": [[2, 0, 0, 2, -1, 0]], "frequencies": [0, 0.5], "sample_rate": 1},
         [1, -1 / 3], "the one_pole section times 2: dividing by a0 leaves the delay unchanged"),
    hand("sos_group_delay.unit_delay", "sos_group_delay",
         {"sos": [[0, 1, 0, 1, 0, 0]], "frequencies": [0, 0.3], "sample_rate": 1}, [1, 1],
         "H = z^-1"),
    hand("sos_group_delay.allpass", "sos_group_delay",
         {"sos": [[-p, 1, 0, 1, -p, 0]], "frequencies": [0, 0.25, 0.5], "sample_rate": 1},
         [3, 0.6, 1 / 3],
         "(-p + z^-1)/(1 - p z^-1): numerator (1 - p cos w)/(1 - 2p cos w + p^2) minus denominator "
         "(p^2 - p cos w)/(same) = (1 - p^2)/(1 - 2p cos w + p^2), p = 0.5: 0.75/0.25, 0.75/1.25, "
         "0.75/2.25"),
    hand("sos_group_delay.zero_on_circle", "sos_group_delay",
         {"sos": [[1, 1, 0, 1, 0, 0]], "frequencies": [0.2, 0.5], "sample_rate": 1}, [0.5, "nan"],
         "as fir_group_delay.two_taps_nyquist"),
    sos_case("sos_group_delay.two_sections_hz",
             [(pair(1.0, 2.5), pair(0.9, 0.5), 0.3), (pair(0.7, 1.5), [0.6, -0.2], 1.0)],
             hz, 8000.0),
    sos_case("sos_group_delay.first_order_sections",
             [([-0.98], [0.75], 0.125), ([0.2], [-0.4], 2.0), ([], pair(0.95, 1.2), 1.0)], grid, 1.0),
    err("sos_group_delay.a0_zero", "sos_group_delay",
        {"sos": [[1, 0, 0, 0, 1, 0]], "frequencies": [0], "sample_rate": 1},
        "every section needs a0 != 0"),
    err("sos_group_delay.five_columns", "sos_group_delay",
        {"sos": [[1, 0, 0, 1, 0]], "frequencies": [0], "sample_rate": 1}, "sections have 6 values"),
    err("sos_group_delay.inf_frequency", "sos_group_delay",
        {"sos": [[1, 0, 0, 1, 0, 0]], "frequencies": ["inf"], "sample_rate": 1},
        "frequencies must be finite"),
]  # fmt: skip

# The hand values, checked against the root formula where they have roots.
for want, got in [
    ([1, -0.2, -1 / 3], [-delay_from_roots([p], 0, nu) for nu in (0, 0.25, 0.5)]),
    ([3, 0.6, 1 / 3], [delay_from_roots([1 / p], 0, nu) - delay_from_roots([p], 0, nu)
                       for nu in (0, 0.25, 0.5)]),
    ([1 / 3, 0.2, -1], [delay_from_roots([-0.5], 0, nu) for nu in (0, 0.25, 0.5)]),
]:  # fmt: skip
    assert all(abs(a - b) < 1e-15 for a, b in zip(want, got, strict=True)), (want, got)

doc = {
    "schema": 1,
    "suite": "group_delay",
    "description": "Group delay in samples of FIR taps and of second-order sections, NaN at a zero "
    "on the unit circle (conventions: FIR filters and IIR filters, Group delay).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "group_delay.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/group_delay.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
