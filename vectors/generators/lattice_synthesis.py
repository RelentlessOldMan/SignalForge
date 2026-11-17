"""Writes vectors/cases/lattice_synthesis.json, stdlib only.

Lattice synthesis filter (conventions: Lattice synthesis filter; ADR 0212). Each case runs the
all-pole lattice with plain lists from zero state, and is cross-checked against the direct
recursion y[n] = e[n] - sum_{j>=1} a_j y[n-j] with the step-up filter a, and against the
analysis lattice, which must give e back.

Run from the repo root: python vectors/generators/lattice_synthesis.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def synth(e, k):
    p = len(k)
    st = [0j] * p
    y = []
    for v in e:
        f = complex(v)
        for m in range(p, 0, -1):
            f = f - k[m - 1] * st[m - 1]
            if m < p:
                st[m] = st[m - 1] + complex(k[m - 1]).conjugate() * f
        st[0] = f
        y.append(f)
    return y


def stepup(k):
    a = [1 + 0j]
    for km in k:
        a = a + [0j]
        a = [a[j] + km * a[len(a) - 1 - j].conjugate() for j in range(len(a))]
    return a


def allpole(e, k):
    a = stepup(k)
    y = []
    for n, v in enumerate(e):
        y.append(v - sum(a[j] * y[n - j] for j in range(1, len(a)) if n - j >= 0))
    return y


def analysis(x, k):
    f = list(x)
    b = list(f)
    for km in k:
        d = [0j] + b[:-1]
        f, b = ([u + km * v for u, v in zip(f, d)],
                [v + complex(km).conjugate() * u for u, v in zip(f, d)])
    return f


def enc(vs, as_complex):
    if as_complex:
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [complex(v).real for v in vs]


def add(cid, e, k, why):
    cx = any(isinstance(v, complex) for v in list(e) + list(k))
    y = synth(e, k)
    assert all(abs(u - v) < 1e-12 for u, v in zip(y, allpole(e, k)))
    assert all(abs(u - v) < 1e-12 for u, v in zip(analysis(y, k), e))
    cases.append({"id": f"lattice_synthesis.{cid}", "op": "lattice_synthesis",
                  "args": {"excitation": enc(e, any(isinstance(v, complex) for v in e)),
                           "reflection": enc(k, any(isinstance(v, complex) for v in k))},
                  "expected": enc(y, cx), "tol": TOL, "source": why})


add("impulse_order_one", [1.0, 0.0, 0.0, 0.0], [0.5],
    "1/(1 + 0.5 z^-1): an impulse gives (-0.5)^n = 1, -0.5, 0.25, -0.125")
add("impulse_order_two", [1.0, 0.0, 0.0, 0.0, 0.0], [0.5, -0.3],
    "1/A with a = [1, 0.35, -0.3]: y[n] = e[n] - 0.35 y[n-1] + 0.3 y[n-2]")
add("ramp_order_three", [1.0, 2.0, 3.0, 4.0, 5.0], [0.5, -1 / 3, 0.25],
    "the lattice on a ramp; equals the direct all-pole recursion")
add("burg_inverse", [1.0, 2.0 - 144 / 85, 3 - 288 / 85 + 77 / 85], [-8 / 9, 77 / 85],
    "ADR 0205's x = [1, 2, 3] residual through its Burg lattice gives x back")
add("large_k", [1.0, 0.0, 0.0], [1.5], "|k| > 1 is allowed (unstable): 1, -1.5, 2.25")
add("complex", [1 + 1j, -0.5j, 2.0 + 0j, 0.5 - 0.5j], [0.3 + 0.4j, -0.2 + 0.1j],
    "complex excitation and k: conj(k) on the backward path")
add("complex_k_real_excitation", [1.0, 0.0, -1.0], [0.5j], "real excitation, complex k")


def err(cid, why, **args):
    cases.append({"id": f"lattice_synthesis.{cid}", "op": "lattice_synthesis", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty_excitation", "excitation must not be empty", excitation=[], reflection=[0.5])
err("empty_reflection", "reflection must not be empty", excitation=[1.0], reflection=[])
err("nan_excitation", "excitation must be finite", excitation=[1.0, "nan"], reflection=[0.5])
err("nan_k", "reflection must be finite", excitation=[1.0, 2.0], reflection=["nan"])

doc = {
    "schema": 1,
    "suite": "lattice_synthesis",
    "description": "Lattice synthesis filter (conventions: Lattice synthesis filter; ADR 0212).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lattice_synthesis.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lattice_synthesis.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
