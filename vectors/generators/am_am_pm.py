"""Writes vectors/cases/am_am_pm.json by hand arithmetic, using only the Python standard library.

It does not import NumPy or SignalForge. The Saleh model A(r) = aa r / (1 + ba r^2),
Phi(r) = ap r^2 / (1 + bp r^2) is applied to samples whose amplitude is the same within each bin,
at several phases, so each bin's ratio y/x is A(r)/r e^{j Phi(r)} and reads 20 log10(A(r)/r) dB and
Phi(r) in degrees (conventions: AM/AM and AM/PM; ADR 0113).

Run from the repo root: python vectors/generators/am_am_pm.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import cmath
import json
import math
import pathlib
import sys

TOL = {"abs": 1e-12, "rel": 1e-12}

AA, BA, AP, BP = 2.1587, 1.1517, 4.0033, 9.1040  # Saleh's fitted travelling-wave tube values


def cx(values):
    return {"re": [v.real for v in values], "im": [v.imag for v in values]}


def case(case_id, args, levels, counts, gain, phase, src):
    return {"id": case_id, "op": "am_am_pm", "args": args,
            "expected": {"levels_db": levels, "counts": counts, "gain_db": gain,
                         "phase_deg": phase},
            "tol": TOL, "source": src}


def err(case_id, args, why):
    return {"id": case_id, "op": "am_am_pm", "args": args, "error": "invalid_argument",
            "source": why}


# Bins [-30, -20), [-20, -10), [-10, -5), [-5, 0), [0, 5]; five samples each at -25, -15, -2.5
# and 2.5 dB, none in [-10, -5); one sample at 0 amplitude and one at -40 dB, neither counted.
edges = [-30.0, -20.0, -10.0, -5.0, 0.0, 5.0]
x, y = [], []
for d in (-25.0, -15.0, -2.5, 2.5):
    r = 10 ** (d / 20)
    for k in range(5):
        th = 2 * math.pi * k / 5 + 0.3
        x.append(cmath.rect(r, th))
        y.append(cmath.rect(AA * r / (1 + BA * r * r), th + AP * r * r / (1 + BP * r * r)))
x += [0j, cmath.rect(0.01, 1.0)]
y += [0.5 + 0.5j, cmath.rect(0.03, 1.2)]


def gain_db(d):
    r = 10 ** (d / 20)
    return 20 * math.log10(AA / (1 + BA * r * r))


def phase_deg(d):
    r = 10 ** (d / 20)
    return AP * r * r / (1 + BP * r * r) * 180 / math.pi


# A phase wrap: at x = 1 (0 dB, the last bin's upper edge, counted), ratios e^{+-j(pi - 0.1)}
# average to cos(pi - 0.1), real and negative: 180 degrees, not 0.
t = math.pi - 0.1
wrap_y = [complex(math.cos(t), math.sin(t)), complex(math.cos(t), -math.sin(t))]

cases = [
    case("am_am_pm.saleh", {"input": cx(x), "output": cx(y), "edges_db": edges},
         [-25.0, -15.0, -7.5, -2.5, 2.5], [5, 5, 0, 5, 5],
         [gain_db(-25.0), gain_db(-15.0), "nan", gain_db(-2.5), gain_db(2.5)],
         [phase_deg(-25.0), phase_deg(-15.0), "nan", phase_deg(-2.5), phase_deg(2.5)],
         "by hand: each bin's samples share r, so y/x = A(r)/r e^{j Phi(r)}: gain "
         "20 log10(aa/(1 + ba r^2)), phase ap r^2/(1 + bp r^2) in degrees; [-10, -5) is empty "
         "(NaN, 0); the zero sample and the one at -40 dB are outside every bin"),
    case("am_am_pm.phase_wrap_on_the_top_edge", {"input": cx([1 + 0j, 1 + 0j]),
                                                 "output": cx(wrap_y),
                                                 "edges_db": [-10.0, 0.0]},
         [-5.0], [2], [20 * math.log10(-math.cos(t))], [180.0],
         "by hand: x = 1 is 0 dB, the last edge, which the last bin includes; e^{j(pi - 0.1)} "
         "and e^{-j(pi - 0.1)} average to cos(pi - 0.1) < 0, so the phase is 180 degrees and "
         "the gain 20 log10 cos(0.1)"),
    case("am_am_pm.ratios_cancel", {"input": cx([0.5 + 0j, 0.5j]),
                                    "output": cx([1 + 0j, -1j]),
                                    "edges_db": [-12.0, 0.0]},
         [-6.0], [2], ["-inf"], [0.0],
         "by hand: both inputs are -6.02 dB; the ratios 2 and -2 average to 0, so the gain is "
         "-inf and the phase 0"),
    err("am_am_pm.lengths_differ", {"input": cx([1 + 0j, 1j]), "output": cx([1 + 0j]),
                                    "edges_db": [-10.0, 10.0]},
        "input and output need the same length"),
    err("am_am_pm.empty", {"input": cx([]), "output": cx([]), "edges_db": [-10.0, 10.0]},
        "at least one sample required"),
    err("am_am_pm.one_edge", {"input": cx([1 + 0j]), "output": cx([1 + 0j]),
                              "edges_db": [0.0]},
        "at least two edges required"),
    err("am_am_pm.edges_not_ascending", {"input": cx([1 + 0j]), "output": cx([1 + 0j]),
                                         "edges_db": [0.0, -10.0]},
        "edges must be strictly ascending"),
    err("am_am_pm.edge_nan", {"input": cx([1 + 0j]), "output": cx([1 + 0j]),
                              "edges_db": [-10.0, "nan"]},
        "edges must be finite"),
    err("am_am_pm.output_inf", {"input": cx([1 + 0j]),
                                "output": {"re": ["inf"], "im": [0.0]},
                                "edges_db": [-10.0, 10.0]},
        "output must be finite"),
]

doc = {
    "schema": 1,
    "suite": "am_am_pm",
    "description": "AM/AM and AM/PM by input-level bin (conventions: AM/AM and AM/PM; "
                   "ADR 0113).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "am_am_pm.json"


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
        sys.exit(f"{out} is out of date: run python vectors/generators/am_am_pm.py")
    print(f"{out} is up to date")
    sys.exit(0)
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
out.write_text(head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n", encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
