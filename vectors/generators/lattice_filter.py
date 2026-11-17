"""Writes vectors/cases/lattice_filter.json, stdlib only.

Lattice analysis filter (conventions: Lattice analysis filter; ADR 0211). Each case runs
f_m[n] = f_{m-1}[n] + k_m b_{m-1}[n-1], b_m[n] = b_{m-1}[n-1] + conj(k_m) f_{m-1}[n] with plain
lists from zero state, and is cross-checked against the direct-form convolution with the
step-up filter a (a <- pad(a) + k conj(reverse(pad(a)))) cut to N samples.

Run from the repo root: python vectors/generators/lattice_filter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys

TOL = {"abs": 1e-13, "rel": 1e-12}
cases = []


def lattice(x, k):
    f = [complex(v) for v in x]
    b = list(f)
    for km in k:
        d = [0j] + b[:-1]
        f, b = ([u + km * v for u, v in zip(f, d)],
                [v + complex(km).conjugate() * u for u, v in zip(f, d)])
    return f


def direct(x, k):
    a = [1 + 0j]
    for km in k:
        a = a + [0j]
        a = [a[j] + km * a[len(a) - 1 - j].conjugate() for j in range(len(a))]
    return [sum(a[j] * x[n - j] for j in range(len(a)) if n - j >= 0) for n in range(len(x))]


def enc(vs, as_complex):
    if as_complex:
        return {"re": [complex(v).real for v in vs], "im": [complex(v).imag for v in vs]}
    return [complex(v).real for v in vs]


def add(cid, x, k, why):
    cx = any(isinstance(v, complex) for v in list(x) + list(k))
    y = lattice(x, k)
    assert all(abs(u - v) < 1e-12 for u, v in zip(y, direct(x, k)))
    cases.append({"id": f"lattice_filter.{cid}", "op": "lattice_filter",
                  "args": {"samples": enc(x, any(isinstance(v, complex) for v in x)),
                           "reflection": enc(k, any(isinstance(v, complex) for v in k))},
                  "expected": enc(y, cx), "tol": TOL, "source": why})


add("impulse_order_one", [1.0, 0.0, 0.0], [0.5], "an impulse gives a = [1, 0.5] then 0")
add("impulse_order_two", [1.0, 0.0, 0.0, 0.0], [0.5, -0.3],
    "an impulse gives a = [1, 0.5 + (-0.3)(0.5), -0.3] = [1, 0.35, -0.3], then 0")
add("ramp_order_three", [1.0, 2.0, 3.0, 4.0, 5.0], [0.5, -1 / 3, 0.25],
    "the recursion on a ramp; equals the ramp convolved with the step-up filter")
add("burg_residual", [1.0, 2.0, 3.0], [-8 / 9, 77 / 85],
    "ADR 0205's x = [1, 2, 3] through its own Burg lattice: x * [1, -144/85, 77/85]")
add("large_k", [1.0, -1.0, 2.0], [1.5], "|k| > 1 is allowed: [1, -1 + 1.5, 2 - 1.5]")
add("complex_samples", [1 + 1j, -0.5j, 2.0 + 0j, 0.5 - 0.5j], [0.3 + 0.4j, -0.2 + 0.1j],
    "complex samples and k: conj(k) on the backward path")
add("complex_k_real_samples", [1.0, 0.0, -1.0], [0.5j], "real samples, complex k")


def err(cid, why, **args):
    cases.append({"id": f"lattice_filter.{cid}", "op": "lattice_filter", "args": args,
                  "error": "invalid_argument", "source": why})


err("empty_samples", "samples must not be empty", samples=[], reflection=[0.5])
err("empty_reflection", "reflection must not be empty", samples=[1.0], reflection=[])
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], reflection=[0.5])
err("nan_k", "reflection must be finite", samples=[1.0, 2.0], reflection=["nan"])

doc = {
    "schema": 1,
    "suite": "lattice_filter",
    "description": "Lattice analysis filter (conventions: Lattice analysis filter; ADR 0211).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "lattice_filter.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/lattice_filter.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
