"""Writes vectors/cases/coherence_confidence_interval.json, stdlib only.

Coherence confidence interval (conventions: Coherence confidence interval; ADR 0202): Fisher
transform of gamma = sqrt(coherence), s = z / sqrt(2K - 2), lower = max(0, tanh(atanh g - s))^2,
upper = tanh(atanh g + s)^2. z comes from statistics.NormalDist().inv_cdf, independent of
SignalForge's chi-squared quantile.

Run from the repo root: python vectors/generators/coherence_confidence_interval.py [--check]
With --check it writes nothing and exits 1 unless the file matches what it would write.
"""

import json
import math
import pathlib
import statistics
import sys

TOL = {"abs": 1e-13, "rel": 1e-11}
cases = []


def limits(g2, k, c):
    if g2 == 1.0:
        return 1.0, 1.0
    s = statistics.NormalDist().inv_cdf((1 + c) / 2) / math.sqrt(2 * k - 2)
    t = math.atanh(math.sqrt(g2))
    return max(0.0, math.tanh(t - s)) ** 2, math.tanh(t + s) ** 2


def add(cid, coh, k, c, why, give_c=True):
    lo_hi = [limits(g, k, c) for g in coh]
    args = {"coherence": coh, "num_segments": k}
    if give_c:
        args["confidence"] = c
    cases.append({"id": f"coherence_confidence_interval.{cid}", "op": "coherence_confidence_interval",
                  "args": args,
                  "expected": {"lower": [v[0] for v in lo_hi], "upper": [v[1] for v in lo_hi]},
                  "tol": TOL, "source": why})


assert limits(0.0, 8, 0.95)[0] == 0.0
add("mixed", [0.25, 0.81, 0.0, 1.0], 8, 0.95,
    "K = 8, c = 0.95: s = z(0.975)/sqrt(14); coherence 0 clips the lower limit at 0, 1 gives [1, 1]")
add("default_level", [0.5], 2, 0.95, "confidence defaults to 0.95; K = 2: s = z(0.975)/sqrt(2)",
    give_c=False)
add("many_segments", [0.5, 0.9, 0.04], 50, 0.5, "K = 50, c = 0.5: s = z(0.75)/sqrt(98)")
add("wide", [0.64], 4, 0.99, "K = 4, c = 0.99: s = z(0.995)/sqrt(6)")


def err(cid, why, **args):
    cases.append({"id": f"coherence_confidence_interval.{cid}", "op": "coherence_confidence_interval",
                  "args": args, "error": "invalid_argument", "source": why})


err("above_one", "coherence must be at most 1", coherence=[0.5, 1.5], num_segments=4)
err("negative", "coherence must be at least 0", coherence=[-0.1], num_segments=4)
err("nan", "coherence must be finite", coherence=["nan"], num_segments=4)
err("one_segment", "num_segments must be at least 2", coherence=[0.5], num_segments=1)
err("confidence_zero", "confidence must be above 0", coherence=[0.5], num_segments=4, confidence=0.0)
err("confidence_one", "confidence must be below 1", coherence=[0.5], num_segments=4, confidence=1.0)

doc = {
    "schema": 1,
    "suite": "coherence_confidence_interval",
    "description": "Coherence confidence interval (conventions: Coherence confidence interval; "
    "ADR 0202).",
    "cases": cases,
}
out = pathlib.Path(__file__).resolve().parents[1] / "cases" / "coherence_confidence_interval.json"
lines = ",\n".join("    " + json.dumps(c) for c in cases)
head = json.dumps({k: v for k, v in doc.items() if k != "cases"}, indent=2)[:-2]
text = head + ',\n  "cases": [\n' + lines + "\n  ]\n}\n"
if "--check" in sys.argv[1:]:
    if json.loads(out.read_text(encoding="utf-8")) != json.loads(text):
        sys.exit(f"{out} is out of date: run python vectors/generators/coherence_confidence_interval.py")
    print(f"{out} is up to date")
    sys.exit(0)
out.write_text(text, encoding="utf-8", newline="\n")
print(f"wrote {out} ({len(cases)} cases)")
