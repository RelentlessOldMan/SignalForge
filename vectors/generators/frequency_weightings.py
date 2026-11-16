"""Writes vectors/cases/frequency_weightings.json, stdlib only.

The IEC 61672-1 A and C weightings (conventions: Frequency weightings; ADR 0164), from the
standard's pole frequencies, each minus its own value at 1000 Hz, in 50-digit decimal. As
independent checks it asserts the standard's rounded normalization constants (A1000 = -2.000 dB,
C1000 = -0.062 dB) and its nominal design values at base-10 frequencies, to their 0.1 dB rounding.

Run from the repo root: python vectors/generators/frequency_weightings.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from decimal import Decimal as D
from decimal import getcontext

getcontext().prec = 50
TOL = {"abs": 1e-11, "rel": 1e-12}
cases = []
F1, F2, F3, F4 = D("20.598997"), D("107.65265"), D("737.86223"), D("12194.217")


def a_raw(f):
    f2 = f * f
    return 20 * (F4**2 * f2**2 / ((f2 + F1**2) * ((f2 + F2**2) * (f2 + F3**2)).sqrt() * (f2 + F4**2))).log10()


def c_raw(f):
    f2 = f * f
    return 20 * (F4**2 * f2 / ((f2 + F1**2) * (f2 + F4**2))).log10()


A1000, C1000 = a_raw(D(1000)), c_raw(D(1000))
assert round(A1000, 3) == D("-2.000") and round(C1000, 3) == D("-0.062"), (A1000, C1000)

NOMINAL = {  # k: (A, C) at 1000 10^(k/10) Hz, IEC 61672-1 design goals rounded to 0.1 dB
    -20: ("-70.4", "-14.3"), -17: ("-50.5", "-6.2"), -15: ("-39.4", "-3.0"),
    -12: ("-26.2", "-0.8"), -10: ("-19.1", "-0.3"), -9: ("-16.1", "-0.2"), -6: ("-8.6", "0.0"),
    -3: ("-3.2", "0.0"), 3: ("1.2", "-0.2"), 6: ("1.0", "-0.8"), 9: ("-1.1", "-3.0"),
    10: ("-2.5", "-4.4"), 12: ("-6.6", "-8.5"), 13: ("-9.3", "-11.2"),
}
for k, (a, c) in NOMINAL.items():
    f = 1000 * D(10) ** (D(k) / 10)
    assert abs(a_raw(f) - A1000 - D(a)) <= D("0.05"), (k, a_raw(f) - A1000)
    assert abs(c_raw(f) - C1000 - D(c)) <= D("0.05"), (k, c_raw(f) - C1000)

for op, raw, ref in (("a_weighting", a_raw, A1000), ("c_weighting", c_raw, C1000)):
    cases.append({"id": f"{op}.zero", "op": op, "args": {"frequency": 0.0}, "expected": "-inf",
                  "source": "log10 of 0 at f = 0"})
    cases.append({"id": f"{op}.f_1000", "op": op, "args": {"frequency": 1000.0}, "expected": 0.0,
                  "tol": TOL, "source": "normalized by its own value at 1 kHz: exactly 0"})
    for cid, f in (("f_10", 10.0), ("f_100", 100.0), ("f_1995", 1000 * 10**0.3),
                   ("f_10000", 10000.0), ("f_20000", 20000.0), ("f_1e6", 1e6)):
        cases.append({"id": f"{op}.{cid}", "op": op, "args": {"frequency": f},
                      "expected": float(raw(D(f)) - ref), "tol": TOL,
                      "source": "IEC 61672-1 closed form in 50-digit decimal, minus the 1 kHz value"})
    for cid, v, why in (("negative", -1.0, "frequency must be non-negative"),
                        ("nan", "nan", "frequency must be finite"),
                        ("inf", "inf", "frequency must be finite")):
        cases.append({"id": f"{op}.{cid}", "op": op, "args": {"frequency": v},
                      "error": "invalid_argument", "source": why})

doc = {
    "schema": 1,
    "suite": "frequency_weightings",
    "description": "IEC 61672-1 A and C weightings (conventions: Frequency weightings; ADR 0164).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "frequency_weightings.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/frequency_weightings.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
