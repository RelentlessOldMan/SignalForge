"""Writes vectors/cases/hampel_filter.json, stdlib only.

Hampel filter (conventions: Hampel filter; ADR 0235). Medians and MADs are the middle elements
of sorted windows (exact); kappa = 1 / inv_cdf(3/4) comes from statistics.NormalDist and is
checked against the constant in the conventions. Threshold boundaries are kept far from
equality.

Run from the repo root: python vectors/generators/hampel_filter.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import pathlib
import sys
from statistics import NormalDist

KAPPA = 1 / NormalDist().inv_cdf(0.75)
assert KAPPA == 1.482602218505602
cases = []


def hampel(x, length, t):
    h = (length - 1) // 2
    n = len(x)
    out = []
    for i in range(n):
        w = min(h, i, n - 1 - i)
        win = x[i - w : i + w + 1]
        med = sorted(win)[w]
        mad = sorted(abs(v - med) for v in win)[w]
        lim = t * KAPPA * mad
        dev = abs(x[i] - med)
        assert dev == lim == 0 or abs(dev - lim) > 1e-6 * max(1.0, lim), (i, dev, lim)
        out.append(med if dev > lim else x[i])
    return out


def add(cid, x, length, why, t=None):
    y = hampel(x, length, 3.0 if t is None else t)
    args = {"samples": x, "length": length}
    if t is not None:
        args["threshold"] = t
    cases.append({"id": f"hampel_filter.{cid}", "op": "hampel_filter", "args": args,
                  "expected": y, "tol": {"abs": 0.0, "rel": 0.0}, "source": why})
    return y


base = [1.0, 1.25, 0.75, 1.5, 1.0, 0.5, 1.25, 1.0, 0.75, 1.5, 1.0]
spiky = base[:]
spiky[4] = 20.0
y = add("spike", spiky, 5, "one spike replaced by its window median, the rest kept")
assert y[4] != 20.0 and all(y[i] == spiky[i] for i in range(11) if i != 4)
y = add("clean", base, 5, "no outliers at threshold 3: unchanged")
assert y == base
add("zero_threshold", [3.0, -1.0, 4.0, 1.0, -5.0, 9.0, 2.0, -6.0, 5.0], 3,
    "threshold 0: the running median wherever a sample differs from it", t=0.0)
y = add("flat_mad_zero", [2.0, 2.0, 2.0, 7.0, 2.0, 2.0, 2.0], 5, "MAD 0: the 7 is replaced")
assert y == [2.0] * 7
add("low_threshold", [0.0, 1.0, 0.25, 2.0, 0.5, -1.0, 0.75, 3.0, 0.0], 5,
    "threshold 1 on mixed data", t=1.0)
add("single_sample", [4.0], 3, "one sample: kept")


def err(cid, why, **args):
    cases.append({"id": f"hampel_filter.{cid}", "op": "hampel_filter", "args": args,
                  "error": "invalid_argument", "source": why})


err("even_length", "length must be odd", samples=[1.0, 2.0], length=2)
err("negative_threshold", "threshold must be non-negative", samples=[1.0], length=3,
    threshold=-1.0)
err("empty", "samples must not be empty", samples=[], length=3)
err("nan_sample", "samples must be finite", samples=[1.0, "nan"], length=3)

doc = {
    "schema": 1,
    "suite": "hampel_filter",
    "description": "Hampel filter (conventions: Hampel filter; ADR 0235).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "hampel_filter.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/hampel_filter.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
