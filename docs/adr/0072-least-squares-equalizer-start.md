# ADR 0072: A least-squares start for the equalizer

Status: accepted, 2026-11-13

## Context

The LMS and decision-feedback equalizers (ADRs 0066, 0069) start from a unit impulse and learn
on the training. Normalized LMS at step 0.1 needs about 2000 symbols to converge through a
strong echo (ADR 0067), so the link needs a long preamble. With the preamble's symbols known, the
taps that minimize the training error can be solved for directly instead.

Measured in the link on `1 + 0.9·z⁻¹` (11 forward and 2 feedback taps, 6000 symbols, three
seeds), with the taps solved for on the preamble and then adapted as before:

| | QPSK 8 dB, P = 100 | P = 200 | 16-QAM 14 dB, P = 100 | P = 200 |
|---|---|---|---|---|
| unit impulse | 0.46–0.61 | 0.0001–0.001 | 0.37–0.46 | 0.03–0.45 |
| least squares | 0.01–0.55 | 0.0001–0.0003 | 0.002–0.007 | 0.008–0.06 |

The rest of the failures come from the frequency: with a short preamble the estimate is 0.05 to
0.6 Hz off, and over 6 s the constellation turns through part of a cycle that the taps do not
follow. That is the next ADR's (a phase loop in the equalizer); with both, every run above has a
BER of 0.0011 or less.

## Decision

- `dfe_least_squares(samples, training, num_taps, num_feedback, *, samples_per_symbol=1,
  center=None)` returns `DfeTaps(taps, feedback_taps)`: the forward and feedback taps that
  minimize `Σ_{n<T} |t_n − y_n|²` over the training, with the DFE's regressors (the feedback on
  the training symbols). It solves the normal equations by Gaussian elimination with partial
  pivoting, written out in the conventions so both languages do the same arithmetic. It needs
  `T ≥ L + M` training symbols; a zero pivot (the training does not determine the taps) is a bad
  argument.
- `lms_equalizer` gains `initial_taps` and `dfe_equalizer` gains `initial_taps` and
  `initial_feedback` (keyword, default the unit impulse and zeros). Given, they replace the start
  and nothing else changes.
- The link gains `equalizer_start`: `"impulse"` [default] or `"least_squares"`, which solves on
  the preamble and starts step 7's equalizer there. It still adapts on the preamble afterwards.
- No regularization: on the link's fractionally spaced taps the normal matrix's condition is
  about 10⁶ (noiseless) and the taps stay small, so plain elimination keeps about ten digits.
  A badly conditioned training would give large taps; the equalizer's adaptation then follows.
- Not a separate solver module: the elimination is small and private to this use, as
  Equiripple's and LeastSquares' are.

## Consequences

- With `equalizer_start = "least_squares"` a preamble of a few times `L + M` symbols starts the
  taps converged; adaptation from there only has to follow the channel.
- The solve costs `T·(L+M)²` for the matrix and `(L+M)³/3` for the elimination, small beside the
  equalizer's run.
- Runs near the frequency's edge are not binomial: 16-QAM at 14 dB with `P = 100` gave 54
  errors in Python and 1 in C# on the same config, 7 sd apart, as one stream's frequency error
  turned the constellation further. Its link config waits for the phase loop; the one added is
  QPSK at 8 dB with `P = 200`, which every seed decodes with 0–3 errors.
