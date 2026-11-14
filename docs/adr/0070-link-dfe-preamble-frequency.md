# ADR 0070: Decision feedback and a preamble frequency in the link

Status: accepted, 2026-11-13

## Context

ADR 0069 built a decision-feedback equalizer. In the link (ADR 0067) a channel with a strong echo
one symbol late (`1 + 0.9·z⁻¹` at the symbol rate, a notch 20 dB deep) defeats the linear
equalizer: at 30 dB QPSK, 11 taps leave a BER of 0.57 (the inverse decays as `0.9ᵏ` and the taps
cannot span it). With two feedback taps there are no errors. At 8 dB both fail for another
reason: through that interference the QPSK estimate `f` (steps 2–6) is about 1 Hz off. Over a
one-second preamble the channel the equalizer sees then turns a full cycle while it trains, so
it never converges.

## Decision

- Config `equalizer_feedback` [0]: an integer `≥ 0`, nonzero only with `equalizer_taps`. Step 7
  then runs `dfe_equalizer` with that many feedback taps (at the symbol rate, on the training and
  then the decisions) in place of `lms_equalizer`; with 0 it is `lms_equalizer` exactly.
- **With the equalizer, the frequency comes from the preamble**, data-aided, before step 7: with
  `n_b = ⌊P/B⌋ ≥ 2` full blocks of the preamble, `q_b` the correlation of block `b` with the known
  symbols on the coarsely derotated samples at `k₀`, the frequency is the coarse `f₁` plus the
  least-squares slope of the blocks' phases (unwrapped by the phase step between neighbours) over
  time. The known symbols take the modulation's data out, so the interference adds far less error
  than it gives the blind estimators. With fewer than two full blocks, `f` from step 6 stays.
- A least-squares line rather than the mean phase step `arg(Σ q_b·conj(q_{b−1}))`: that sum
  telescopes towards the first and last blocks, so only their errors count; the line weighs them
  all. On the echo below it cut the error 3 to 7 times.
- Its range is `±R/(2B)` around `f₁` (±15.6 Hz at 1 kHz and `B = 32`). The phase (step 6) is
  still reported; the equalizer does not use it, as it learns any fixed phase in training.

## Consequences

- Equalizer runs report a different `frequency_offset_hz` from the chain without the equalizer;
  timing, frame start and phase are unchanged. Equalizer runs with noise change their results.
- Measured on `1 + 0.9·z⁻¹` (delays 0 and 4 at 4 samples per symbol): at QPSK 8 dB the
  preamble estimate is within 0.03 Hz in five seeds (the old one 1 Hz off). With two feedback
  taps the BER is 0.0002–0.0007 in three seeds (the linear equalizer 0.015); 16-QAM at 14 dB goes
  from 0.34 to under 0.0002. Noiseless, 64-QAM needs a 2000-symbol preamble to start without
  errors (1000 leave 18, all just after training). The estimate keeps a small bias from the echo's cross
  terms with the known preamble (noiseless, 0.02 Hz for QPSK and 0.008 Hz for 16-QAM there); the
  decision-directed taps follow it.
- The matched-filter bound (`ber_theory`) is unchanged and far below these: error propagation
  and the forward filter's noise come on top, and no closed form gives them. Tests bracket the
  BER between the bound and the linear equalizer's.
- **8-PSK through that echo is not solved**: its blind estimate (8th power) is about 50 Hz off,
  outside the preamble estimate's range. A data-aided coarse search is later work.
