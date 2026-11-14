# ADR 0077: RLS training for the decision-feedback equalizer and the link

Status: accepted, 2026-11-13

## Context

ADR 0076 added an RLS equalizer with forward taps only. Measured in the link (two-path echo
`1 + 0.9·z⁻⁴` at the symbol rate, 11 forward taps at 2 per symbol, 4000 symbols, seeds 80–85),
forward-only RLS barely helps: the link equalizer that works on this channel is the
decision-feedback one with its phase loop (ADRs 0069, 0073). With RLS training *that* equalizer,
over the combined regressor of the rotated forward samples and the past references, the short
preamble works from the plain impulse start. Bit error rates, 2 feedback taps, loop gains
`(0.02, 0.0001)`, 5 Hz offset, 100 preamble symbols:

| | LMS, impulse | LMS, least-squares start | RLS λ = 0.999, impulse |
|---|---|---|---|
| QPSK, 8 dB | 0.001–0.010 | 0.0004–0.0013 | 0–0.0012 |
| 16-QAM, 14 dB | 0.24–0.45 | 0–0.0004 | 0.0001–0.0010 |
| 8-PSK, 12 dB | 0.32 (every seed) | 0.0015–0.63 (4 of 6 fail) | 0–0.0027 |

Over 10 seeds at 6000 symbols, 8-PSK with RLS has about a third of the least-squares start's
errors on the seeds that do not slip; one seed in ten still slips either way, which the pilots
(ADR 0075) are for. At 40 or 60 preamble symbols every form fails on most seeds.

## Decision

- `dfe_equalizer` gains `forgetting=None` and `delta=0.01` (C# `forgetting`, `delta`). With
  `forgetting` given, the tap update is RLS (ADR 0076's recurrence) over
  `z = (u_0·r … u_{L−1}·r, p_1 … p_M)` and the coefficients `(w, b)`, where `r` is the loop's
  rotation (1 without the loop); `y = Σ θ_k·z_k` exactly as before, so the phase loop, pilots,
  training, decisions and starts are unchanged. `step` is still checked but not used.
- The update is skipped where the LMS one is (no reference, or zero power).
- The link gains `equalizer_forgetting` [none] (in `(0, 1]`, only with `equalizer_taps`), passed
  as `forgetting`; `delta` stays at its default.
- `rls_equalizer` stays as it is: the forward-only block.

## Consequences

- `O((L + M)²)` work per symbol instead of `O(L + M)`, in a pure-Python loop: about 4 times
  slower for the link's 13 coefficients. Fine for the link's sizes.
- The impulse start with RLS now matches or beats the least-squares start, so the two are
  alternatives; neither is the default, which stays LMS from the impulse.
