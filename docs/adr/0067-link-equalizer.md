# ADR 0067: The LMS equalizer in the single-carrier link

Status: accepted, 2026-11-13

## Context

ADR 0064 put a static multipath channel in the link for OFDM only, because the single-carrier
chains (QPSK, 8-PSK, 16-QAM, 64-QAM) had no equalizer. ADR 0066 built one. This puts it in the
chains: where it sits, how it is fed and trained, and what `ber_theory` means once a channel with
inter-symbol interference is in the way, where no closed form gives a linear equalizer's BER.

## Decision

- Config: `equalizer_taps` [none] (an integer `≥ 1`) and `equalizer_step` [0.1] (normalized step,
  `[0, 2]`). With `equalizer_taps` the chains accept `multipath_delays` and `multipath_gains`;
  without it they still reject them. `"ofdm"` and FSK reject `equalizer_taps`.
- The equalizer replaces step 7 (the derotated symbol-spaced samples, or the carrier loop): it
  runs **fractionally spaced at 2 samples per symbol** on the matched-filter output, so
  `samples_per_symbol` must be even. It takes the samples from the symbol at the frame start
  (`round(τ) mod sps + k₀·sps`) on, derotated by the estimated frequency, trains on the preamble
  and then decides with the chain's own demapper. Its center tap starts on the sample the chain
  would have taken, so the estimates before it (timing, frame start, frequency) are unchanged.
- With the equalizer, EVM and bit errors are measured **from symbol P on**: the preamble is its
  training, and its outputs there are from taps still converging (noiseless, every error of a
  run falls in the first few hundred symbols), so the preamble must be shorter than the frame.
  Without it the preamble still counts.
- `timing_loop_gains` and `carrier_loop_gains` are rejected with the equalizer: it follows a
  slowly moving phase itself, and two loops on one error would fight.
- With multipath the transmit signal gets `max(multipath_delays)` zeros after it (room for the
  last echo) and the channel runs `multipath` first, as for OFDM.
- `ber_theory` with multipath is the **matched-filter bound**: the chain's theory at
  `Eb/N₀ + 10·log10 E_h`, with `E_h = Σᵢ Σⱼ gᵢ·conj(gⱼ)·ρ((dⱼ − dᵢ)/sps)` the energy the paths
  give one pulse, `ρ` the raised-cosine pulse (the autocorrelation of the root-raised-cosine
  pulse) at a time in symbols. It is a lower bound on the BER of any symbol-by-symbol receiver,
  not a prediction: the linear equalizer's noise enhancement and its misadjustment come on top.
  Without multipath it is unchanged.

## Consequences

- A test brackets the BER between the bound and a fixed allowance, and the link compare skips the
  EVM with multipath as it already does.
- The equalizer is trained once, on the preamble. Fed at 2 samples per symbol, a
  root-raised-cosine signal leaves part of the band empty, so the input's eigenvalue spread is
  large and normalized LMS converges slowly: measured on a three-path channel, 11 taps at step 0.1
  take about 2000 symbols to reach the least-squares error. Configs use preambles of hundreds of
  symbols and let the decisions finish the job.
- A long preamble makes the frame search (step 3, coherent over the preamble) sensitive to the
  coarse frequency error: the QPSK estimate is off by about 0.7 Hz rms on a flat 1 kHz link at
  6 dB, and about twice that through strong inter-symbol interference, which over a one-second
  preamble turns the correlation through a full cycle and can pick the wrong start. The tests
  use a moderate channel; [ADR 0068](0068-block-frame-search.md) then made the search work in blocks.
- Measured on a moderate channel (delays 0, 2, 5; gains 1, 0.3 + 0.2j, −0.1) at step 0.1, the
  BER is 0.2–0.4 dB from the bound for QPSK at 6 dB and 16-QAM at 12 dB; the tests allow 1 dB.
- Decision feedback, a training-free (blind) start and a step schedule are later work.
