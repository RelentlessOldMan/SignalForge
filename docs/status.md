# Status

Updated with every chunk of work. Dates are absolute.

## Next

1. **Gardner timing recovery**: a closed loop (Gardner detector, PI loop filter, interpolation by
   the `fractional_delay` kernel) with its conventions, ADR and vectors; checks: lock to a
   static and a slowly drifting offset, and loop bandwidth against the linear model.

## Built

- 2026-11-12: repo, license (MIT), README, this brain (`CLAUDE.md`, `docs/status.md`), CI.
- 2026-11-12: research and architecture docs: conventions, architecture, testing, dependencies with
  license verification, ADRs 0001–0005 (0006 below).
- 2026-11-12: Python package `signalforge` and C# library `SignalForge` (then 0.1.0), each with:
  `Signal` with metadata; units (dB, dBm, Vrms at an impedance); complex and real tones; PRBS
  (O.150 polynomials, orders 7–31); power stats (mean, RMS, peak, PAPR, DC); QPSK Gray map and hard
  demap; bit error count.
- 2026-11-12: NumPy approved as the Python runtime dependency; its bundled GCC Fortran runtime
  (GCC runtime exception) puts no obligation on our code. ADR 0004.
- 2026-11-12: PSF-2.0 approved, MPL-2.0 allowed for dev-only tools (ADR 0005); mypy strict added to
  the Python checks and CI, tests annotated.
- 2026-11-12: shared vectors, 46 cases across units, waveforms, PRBS, measurements and modulation.
  Python 79 passed, 2 skipped (PRBS 23 and 31 full-period checks, too slow); .NET 77 passed.
- 2026-11-13: spectral module in both languages (ADR 0006): FFT (Python `numpy.fft`; C# its own
  radix-2 plus Bluestein, no dependency), frequency axes, seven windows with coherent gain and ENBW,
  Welch PSD (one- and two-sided), occupied bandwidth (β/2), channel power. 59 new vectors (105 in
  all). Python 153 passed, 2 skipped (CI: Python 3.10 and 3.13); .NET 148 passed.
- 2026-11-13: date-based versioning (`YYYY.M.D.N`, docs/versioning.md): `VERSION` at the root is the
  one source; .NET reads it at build time, `build.ps1` bumps it and stamps Python's `__version__`;
  tests in both languages check they agree. Was 0.1.0; first build 2026.11.13.0. Python 155 passed,
  2 skipped; .NET 149 passed.
- 2026-11-13: review and fixes across both languages:
  - **Bugs fixed:** occupied bandwidth could return `inf` at fraction 1 when trailing bins were zero
    (the total and the running sum differed in the last bit); a one-sided PSD undercounted DC and
    Nyquist power. New `span` argument for OBW and channel power, and `SpectralDensity.span`
    `(0, fs/2)` for one-sided PSDs (conventions: Bins as rectangles).
  - **Stricter arguments:** Kaiser β limited to 0…700 (I₀ overflows above 713); Welch takes `beta`;
    sample rates and impedances must be finite; `power_stats` and PSD frequencies reject NaN and
    infinity; QPSK bits must be exactly 0 or 1; Python counts must be integers (`3.0` is
    rejected). New conventions section: Arguments.
  - **Conformance runners:** the C# runner passed some broken cases (an argument it didn't read,
    a decoding error counted as the expected `invalid_argument`, truncated `re`/`im` pairs,
    approximate window names). Both runners now reject unknown arguments and compare types
    strictly. `vectors/selftest/must_fail.json` holds 11 wrong cases both runners must fail; it
    found one more crash in the C# runner.
  - 26 new vectors (131 in all): span cases, the fraction-1 regression, Kaiser and Welch β,
    non-finite inputs, PRBS 11/15/20/23/31 prefixes and a PRBS7 run past its period.
  - Docs and tooling: build.ps1 refuses a missing or malformed `VERSION`; CI actions updated to the
    current node24 majors; NumPy floor raised to 2.2 (the oldest version CI tests); README in the
    REPO-SETUP form; NuGet metadata. Two license questions are open for the user (dependencies.md):
    libquadmath (LGPL) in NumPy's Linux wheels, and NumPy's vendored permissive parts.
  - Python 207 passed, 2 skipped; .NET 189 passed.
- 2026-11-13: QPSK link building blocks in both languages (ADR 0007): modules `dsp` (convolution,
  upsampling, unit-energy RRC taps, pulse shaping) and `channel` (seeded AWGN at Es/N0, frequency
  offset); in `metrics`, EVM (RMS, %, dB, peak) and QPSK BER theory, with C#'s own erfc. 49 new
  vectors (180 in all); RRC expected values come from the inverse Fourier transform of the
  root-raised-cosine spectrum (Gauss–Legendre), not the closed form. Unit tests check AWGN
  statistics, the matched filter's Nyquist property, and a shaped QPSK link's BER against theory
  at 4 dB Eb/N0 in both languages. Python 278 passed, 2 skipped; .NET 259 passed.
- 2026-11-13: review of the link blocks. Python raised `OverflowError` (not `ValueError`) for an
  extreme Es/N0 or Eb/N0, where C# quietly returned infinity: AWGN now rejects an Es/N0 so low the
  noise variance overflows (both languages), and BER theory returns 0 above about 3080 dB. CI's
  Python 3.10 mypy (NumPy 2.2 stubs) failed on two annotations; fixed and checked locally on 3.10.
  2 new vectors (182). Python 283 passed, 2 skipped (also on 3.10); .NET 261 passed.
- 2026-11-13: block synchronization ([ADR 0008](adr/0008-block-synchronization.md)), new module
  `sync` in both languages: Oerder–Meyr symbol timing (`timing_offset`), fourth-power QPSK carrier
  frequency (`qpsk_frequency_offset`) and phase (`qpsk_phase_offset`), each a feed-forward block
  estimate; correction reuses `frequency_offset`. 24 new vectors (206), built from clean signals
  where each estimator is exact. Unit tests run a shaped QPSK link with delay, carrier offset, phase
  and noise, recover it, and check BER against theory at 6 dB. Python 312 passed, 2 skipped; .NET
  290 passed.
- 2026-11-13: review of `sync`. The estimators are scale-invariant, but `z⁴` underflowed to 0 for
  symbols near 1e-90 (estimate 0) and overflowed near 1e80 (NaN). Both languages now scale each block
  by a power of two first, which is exact, so earlier results are bit-identical. 6 new vectors
  (212); five of them fail on the old code. Python 318 passed, 2 skipped; .NET 296 passed.
- 2026-11-13: end-to-end QPSK link ([ADR 0009](adr/0009-qpsk-link-report.md)), new module `link`
  in both languages: `qpsk_link(QpskLinkConfig)` runs PRBS bits through RRC shaping, delay, carrier
  offset and AWGN, recovers timing, frame start (preamble search), frequency and phase, and returns
  `QpskLinkReport` with EVM, bit errors and theory BER, writing the same JSON in both languages.
  The coarse fourth-power frequency estimate alone left BER 200 times theory at 6 dB, so the
  receiver adds `sync.qpsk_block_phases` (new) and a line fit through the block phases for fine
  frequency and phase. 24 new vectors (236): exact block phases, and noiseless links checked against
  the channel's own delay, offset and phase. Unit tests check BER against theory at 6 dB with three
  offsets, and the JSON field names (the same list in both languages). Python 354 passed, 2
  skipped; .NET 327 passed.
- 2026-11-13: review of `link`. In Python a NumPy integer in the config made `to_json` raise
  (`dataclasses.asdict` keeps `np.int64`), and NumPy floats or an integer Eb/N0 were rejected. The
  link now accepts any real number (not bool) and stores the config in the report as plain `int`
  and `float`. Python 355 passed, 2 skipped; .NET 327 passed.
- 2026-11-13: cross-language checks. A C# console tool (`dotnet/tools/SignalForge.Conformance`,
  built from the tests' own runner) writes the same conformance report as Python, and runs a
  `qpsk_link` config. `python -m signalforge.compare` diffs the two reports (every field of every
  result, at the case's tolerance) and compares two link reports (noiseless: every field; noisy:
  bit errors and mean squared EVM by two-sample tests). `vectors/links/` holds one noisy and one
  noiseless config; `build.ps1` and a new CI job run all of it. Vectors may now give `null`. The
  first diff found a real gap: Python's runner ignored properties, so `SpectralDensity.span` was
  never compared. Python 367 passed, 2 skipped; .NET 330 passed; vectors 237/237; reports agree.
- 2026-11-13: review of the compare tool. Both diffs compared only the fields on one side, so a
  field the other side alone had went unseen; they now check both sides' field names first. A
  noisy link compare also checks the theoretical BER (it depends only on the config). The C# tool
  printed a stack trace on a bad config or argument and now exits 2 with a message, as the Python
  one does. Python 369 passed, 2 skipped; .NET 330 passed.
- 2026-11-13: FIR filters in both languages (ADR 0010): windowed-sinc low-pass, high-pass (odd
  length) and band-pass design scaled to unit gain at DC, fs/2 or the band center; Kaiser's
  length and beta formulas; the complex frequency response; and `FirFilter`, the first operation
  with state across chunks (any split of a signal gives the same output as one call). The 38
  vectors come from `vectors/generators/fir.py`, standard library only, which integrates the
  ideal spectrum numerically rather than using the sinc formula; CI checks the file still
  matches it. The Python runner now treats a tuple result as a real array, as C# already did.
  A design whose taps have no gain to scale (a length-2 Hann window) raises instead of returning
  NaN. `link._finite` moved to `_checks.real` for reuse. A unit test caught Python's `FirFilter`
  keeping the caller's array instead of a copy. Python 422 passed, 2 skipped; .NET 376 passed;
  vectors 275/275; reports and links agree.
- 2026-11-13: Resampling in both languages (ADR 0011): `resample(x, up, down, taps)` by a
  rational factor reduced by its gcd, with the filter delay removed so output `m` sits at input
  time `m·down/up`; `interpolate` and `decimate` are its two special cases; default taps
  `resample_taps` are a Hamming low-pass of 20·R + 1 taps. C# runs a polyphase loop that skips the
  zero products; Python convolves the zero-stuffed signal. The 20 vectors come from
  `vectors/generators/resample.py` (standard library, brute-force sum) and hand derivations.
  Review fix: integer arguments now reject bools in Python (`True` used to pass as 1), as reals
  already did.
- 2026-11-13: signal files in both languages (ADR 0012): `encode_samples` / `decode_samples` for
  the 18 SigMF datatypes (real and complex; f64, f32, i32, i16, i8; little and big endian), with
  integers scaled to full scale 1.0, rounded half to even, and out-of-range values rejected; and
  `write_sigmf` / `read_sigmf` for a `.sigmf-meta` + `.sigmf-data` pair carrying every `Signal`
  field (the extras in a `signalforge` extension namespace). Written from the format description;
  nothing copied from the spec or sigmf-python. 81 vectors from `vectors/generators/files.py`
  (standard library `struct`), with 16 recordings in `vectors/files/`, including foreign-written and
  malformed ones. New cross-language check: each language writes a recording per datatype, both
  read all of them, and `compare files` checks the reads match exactly and the two writers agree
  within one quantization step (`build.ps1`, CI). Review fixes found on the way: the runners turned
  a complex value with an infinite part into NaN (Python) or failed to match it (C#); C# read JSON
  integers as doubles (a ternary promoted `long` to `double`).
  Python 585 passed, 2 skipped (3.10 too); .NET 515 passed; conformance 376/376 in both.
- 2026-11-13: spectrogram in both languages (ADR 0013): Welch's segments kept one per row, same
  windowing, scaling and sidedness, rows timed at segment centers; Welch now shares the segment
  code. 13 vectors from `vectors/generators/spectrogram.py` (standard library, DFT summed term by
  term) and a hand-derived tone; both runners now read and compare 2-D results.
  Python 604 passed, 2 skipped (3.10 too); .NET 533 passed; conformance 389/389 in both.
- 2026-11-13: IIR filters in both languages (ADR 0014): second-order sections, Butterworth
  low-pass and high-pass by the prewarped bilinear transform with a fixed section order and unit
  gain per section, `sos_response`, and a streaming `IirFilter` shaped like `FirFilter`. 26 vectors
  from `vectors/generators/iir.py` (real biquad formulas, a different route from the library's
  pole mapping) plus hand cases; unit tests check every design against the closed-form magnitude.
  The runners share one chunked-filter op. Python 713 passed, 2 skipped (3.10 too); .NET 589
  passed; conformance 415/415 in both.
- 2026-11-13: `build.ps1` runs every vector generator's `--check`, as CI already did, so a stale
  vector file fails locally before a push.
- 2026-11-13: more waveforms in both languages: `multitone` (chosen phases, or `newman_phases`),
  linear `chirp` (reaches `stop` at N/fs) and `pulse_train` (whole samples, floored modulo, any
  delay). `tone` now rejects non-finite frequency, amplitude and phase in both. 29 vectors from
  `vectors/generators/stimuli.py` (standard library, formulas sample by sample) plus hand cases.
  Unit tests: Newman phases cut a 32-tone crest factor below 0.4 of √32, chirp instantaneous
  frequency is linear and two chirps join without a jump. Python 779 passed, 2 skipped (3.10
  too); .NET 627 passed; conformance 444/444 in both.
- 2026-11-13: review of the signal files, spectrogram and IIR slices (no wrong numbers found):
  the two languages now apply one set of JSON limits to SigMF meta (int64 integers, finite floats,
  valid Unicode, 64 levels, `null` captures or metadata rejected), and Python checks everything
  before writing either file, as C# did. Python `write_sigmf` accepts NumPy scalars in the signal,
  `decode_samples` counts a memoryview's bytes, and a huge JSON integer or a bool sample rate is a
  `ValueError`. 24 new vectors, 23 of them errors (files, IIR, spectrogram); the C# runner reads an empty `sos`.
  Python 809 passed, 2 skipped (3.10 too); .NET 655 passed; conformance 468/468 in both.
- 2026-11-13: tone metrics in both languages (ADR 0015): `tone_metrics` / `Measurements.ToneMetrics`
  gives SNR, SINAD, THD and ENOB of the strongest (or a named) tone from one windowed spectrum of
  the whole input. Bins are grouped DC, fundamental, aliased harmonics, noise, each bin once, with
  a half-width set by the window; the fundamental's frequency is its group's power centroid.
  18 vectors (`generators/tone_metrics.py`) built from on-bin tones whose group powers are known
  in closed form, including aliased harmonics of a complex tone and the Hann 1/6 : 2/3 : 1/6 split.
  Python 839 passed, 2 skipped (3.10 too); .NET 681 passed; conformance 486/486 in both.
- 2026-11-13: SFDR in both languages: `sfdr` / `Measurements.Sfdr` gives the carrier and up to
  `num_spurs` spurs (group power, power centroid, dBc), strongest peak bin first, DC never a spur,
  from the same groups as the tone metrics; both languages now share one grouping helper. 7 more
  closed-form vectors in `tone_metrics.json`, among them a named carrier below its spur (negative
  SFDR) and a spectrum with no bin left for a spur.
  Python 851 passed, 2 skipped (3.10 too); .NET 689 passed; conformance 493/493 in both.
- 2026-11-13: band-pass and band-stop Butterworth in both languages (`butterworth_bandpass`,
  `butterworth_bandstop`; ADR 0016): the low-pass prototype transformed to the band, one section
  per band pole pair, scaled by the analog factors so the cascade's gain is exactly the closed form.
  16 more `iir.json` cases (two by hand, seven designs the generator checks against the closed-form
  magnitude before writing, responses, a filter run, six errors).
  Python 926 passed, 2 skipped (3.10 too); .NET 716 passed; conformance 511/511 in both.
- 2026-11-13: zero-phase filtering in both languages (`zero_phase_filter` /
  `Dsp.ZeroPhaseFilter`, ADR 0017): forward then backward over an odd extension, each pass from
  the sections' steady state. 12 more `iir.json` cases (two by hand, a constant that must come back
  exactly, five from a direct form I implementation, five errors).
  Python 949 passed, 2 skipped (3.10 too); .NET 732 passed; conformance 523/523 in both.
- 2026-11-13: review fixes for tone metrics, SFDR, band Butterworth and zero-phase filtering.
  Tone metrics: bins at or below 1e-20 of the total power are zeroed (rounding error had picked
  fundamentals and spurs that differed between languages); a non-finite spectrum is an error; the
  C# half-width is clamped (it overflowed near `int.MaxValue`); a complex fundamental of +fs/2
  means the -fs/2 bin. Zero-phase filtering rejects non-finite samples. The band generator now
  checks stability and the denominator product against a polynomial expansion of the analog
  prototype, independent of the pole algorithm. The C# runner rejects `2.0` for an integer
  argument. 26 more vectors (tone 9, iir 17); C# band tests match Python's 40 cases.
  Python 981 passed, 2 skipped (3.10 too); .NET 793 passed; conformance 549/549 in both.
- 2026-11-13: Chebyshev type I low-pass and high-pass in both languages (`chebyshev1_lowpass`,
  `chebyshev1_highpass` / `Dsp.Chebyshev1Lowpass`, `Chebyshev1Highpass`, ADR 0018): pass-band
  ripple in dB, the cutoff the pass-band edge, sections shared with Butterworth's builder (a test
  annotation fixed for NumPy on Python 3.10 in the next build). 20 more
  `iir.json` cases (two designs by hand, eight checked against the closed form, a response, a
  filter run, eight errors).
  Python 1061 passed, 2 skipped (3.10 too); .NET 854 passed; conformance 569/569 in both.
- 2026-11-13: ACPR in both languages (`acpr` / `Spectral.Acpr`, ADR 0019): main channel and lower
  and upper channels at each center-to-center offset, by the channel power rule, in dBc; a channel
  that leaves the spectrum is an error. New `vectors/generators/acpr.py` writes `acpr.json`
  (15 cases, the powers summed from piecewise-constant bins by hand). Tests: on-bin tones through
  Welch (-20 and -40 dBc), flat noise (the bandwidth ratio), bad arguments.
  Python 1086 passed, 2 skipped (3.10 too); .NET 877 passed; conformance 584/584 in both.
- 2026-11-13: Chebyshev type II low-pass and high-pass in both languages (`chebyshev2_lowpass`,
  `chebyshev2_highpass` / `Dsp.Chebyshev2Lowpass`, `Chebyshev2Highpass`, ADR 0020): flat pass
  band, stop-band peaks at `-attenuation_db`, the cutoff the stop-band edge; the shared cascade
  builder now takes zeros on the unit circle. Fix found while designing it: a type I ripple above
  about 3080 dB raised OverflowError in Python, not ValueError, and past ~200 dB the poles sit on
  the unit circle to rounding, so ripple and attenuation are now limited to (0, 200] dB. 20 more
  `iir.json` cases (two designs by hand, eight computed from the analog quadratics and checked
  against the closed form, a response, nine errors incl. two type I ones).
  Python 1176 passed, 2 skipped (3.10 too); .NET 940 passed; conformance 604/604 in both.
- 2026-11-13: review pass over the spectral measurements and the IIR designs, fixes in both
  languages. IIR: a cutoff or band edge within ~1e-8·fs of 0 or fs/2 rounded a pole onto the unit
  circle (Butterworth gain 0, a pole at z = 1; Chebyshev II raised ZeroDivisionError in Python and
  gave NaN in C#); every design now checks its sections are finite and strictly stable and
  rejects the rest. The Chebyshev II reference gain uses the exact denominators. dB values enter
  as `expm1` (C#: a series below 1e-5), so a 1e-17 dB ripple no longer divides by zero. Order is
  capped at 1000. Python `sos_response` rejects complex and bool frequencies. Spectral: an
  overflowing bin power or total gave NaN (Python) or IndexOutOfRangeException (C#); an infinite
  bin spacing passed in Python; bins whose half-width rounds away are rejected; a channel past the
  spectrum by rounding (`0.3 − 0.1 − 0.2`) is accepted within 1e-9 of a bin; dBc is a difference
  of logs, so a 1e-400 ratio is −4000 dBc, not −∞; Python `channel_power` validates its edges
  (no TypeError/OverflowError); C# names `center` when the main channel leaves the spectrum.
  Conventions updated; 8 more `iir.json` and 5 more spectral/ACPR cases.
  Known weakness, not fixed: the band-form vectors come from a generator that follows the same
  pole-pair construction as the code; an independent root-finding check would be stronger.
  Python 1208 passed, 2 skipped (3.10 too); .NET 959 passed; conformance 617/617 in both.
- 2026-11-13: band-pass and band-stop Chebyshev types I and II ([ADR 0021](adr/0021-band-chebyshev.md)):
  `chebyshev1_bandpass`, `chebyshev1_bandstop`, `chebyshev2_bandpass`, `chebyshev2_bandstop`
  (`Chebyshev1Bandpass` ... in C#), on the shared band transform that Butterworth band designs now
  also use. Conventions give the prototype frequency maps, the closed-form |H|², the type II
  zero images and the section gains. 21 new `iir.json` cases: four by-hand order-1 designs, ten
  computed designs (orders 2-5), seven rejections. The generator builds the sections from their
  own analog quadratics and checks them against the closed-form |H|² and edge values, section
  stability, and the product of the denominators against the prototype expanded by polynomial
  substitution (independent of the pole-pair split). Python 1334 passed, 2 skipped; .NET 1046
  passed; conformance 638/638 in both.
- 2026-11-13: review of the band Chebyshevs. A sweep of 1568 designs (orders 1-1000, dB 1e-9 to
  200, bands from 1e-12·fs wide to near Nyquist): each design either raises `ValueError` or
  matches the closed-form |H|² to 1e-6, except where second-order-section coefficients can't hold
  the poles (a 1e-12·fs band; 200 dB ripple). Both languages were run on the same grid and on
  800 random designs (a temporary check, not vectors). They accept and reject the same designs
  and agree to 1e-12 on random designs, 1e-6 at the extremes. No code defects found; the
  conventions now state the bandwidth and dB conditioning limits.
- 2026-11-13: elliptic (Cauer) low-pass and high-pass ([ADR 0022](adr/0022-elliptic.md)):
  `elliptic_lowpass`, `elliptic_highpass` (`EllipticLowpass`, `EllipticHighpass`), with ripple and
  attenuation in dB. Elliptic functions by the descending Landen ladder, the degree equation by
  the nome q-product, `v0` by the ladder; conventions give every step. Designs with `k' < 1e-6`
  are rejected. 17 new `iir.json` cases: three by hand (order 1 and the order-2 design with
  ε = 1 in closed form, low-pass and high-pass), eight computed (orders 3-8), six rejections
  (including the transition limit). The generator is independent of the library: it builds the rational
  function R_N from theta functions and the AGM, finds the poles as roots of D² + ε²N² (polished
  by Newton on the product form), and checks the equiripple bounds, |H|² against the closed form
  to 1e-12, and stability. A temporary sweep of 600 random designs (orders 1-1000) agreed in both
  languages to 1e-10, accepting and rejecting the same ones. Python 1388 passed, 2 skipped; .NET
  1086 passed; conformance 655/655 in both.
- 2026-11-13: review of the elliptic low/high-pass. Against the generator's independent R_N
  (theta series), 2310 designs (orders 1-30, ripple 1e-6 to 199 dB, A − R 1e-3 to 200 dB,
  cutoffs 1e-4 to 0.4999·fs) match the closed-form |H|² to 4e-9 at mid-band cutoffs and 7e-7 at
  the extreme ones. Orders 1 and 2 are never rejected; rejections are the `k' ≥ 1e-6` limit and
  the pole check. Both languages ran a 9204-design grid (orders to 1000, cutoffs to 1e-6·fs):
  they agree to 1e-7 except at cutoffs 1e-6·fs and 0.4999·fs (ill-conditioned rows, agreeing
  to about 1e-5), and accept/reject the same designs except three with 150-200 dB ripple whose
  poles sit one rounding step (2e-16) from the unit circle. No code defects; the conventions'
  conditioning note now names the elliptic ripple limit.
- 2026-11-13: band-pass and band-stop elliptic ([ADR 0023](adr/0023-band-elliptic.md)):
  `elliptic_bandpass`, `elliptic_bandstop` (`EllipticBandpass`, `EllipticBandstop`): the elliptic
  prototype (now a shared helper) through the ADR 0021 band builder unchanged, with the type I
  even-order gain. 14 new `iir.json` cases: two by hand (order 1, ε = 1, W = 1, B = 2), seven
  computed (orders 2-6, narrow and wide bands), five rejections. The generator puts its own
  theta-series prototype through the band transform and checks the closed-form |H|², the edges,
  the band-stop center, stability and the denominator product by polynomial substitution; the
  library matches it to 2e-15. A temporary sweep of 800 random band designs agreed in both
  languages to 1e-10. Python 1437 passed, 2 skipped; .NET 1123 passed; conformance 669/669 in
  both.
- 2026-11-13: review of the band elliptics. Against the generator's theta-series R_N, 1005
  designs (orders 1-30, ripple 1e-6 to 199 dB, bands from 1e-9·fs wide and edges from 1e-6·fs
  to 0.4999·fs) match the closed-form |H|² to 3e-9 for ordinary bands; the worst errors (2e-2,
  3e-2) need two limits at once (100 dB ripple in a 1e-9·fs band, order 30 with edges at
  1e-6·fs), and order 1, which is Chebyshev I, shows the same loss, so it is the band transform's
  conditioning already in the conventions. Both languages ran a 4032-design grid (orders to
  1000, the same bands, ripple from 1e-9 dB): all agree to 1e-7 and accept and reject the same
  designs. No defects found.

- 2026-11-13: equiripple FIR design ([ADR 0024](adr/0024-equiripple-fir.md)):
  `fir_equiripple(num_taps, bands, desired, sample_rate, weights=None, grid_density=16)`
  (`FirEquiripple`), symmetric type I and II, piecewise-constant bands with weights. The grid,
  the Remez exchange's tie rules and the stop rule are in the conventions, so the result is the
  unique discrete optimum on a defined grid. Two numerical traps found and fixed on the way: an
  optimum with an extra ripple makes the exchange swap between two equally good sets forever
  (now also stopped by the gap between the largest error and δ), and rebuilding the taps by
  sampling the interpolant on a uniform grid magnifies rounding in the transition gaps (a 41-tap
  design measured 2e-8 instead of 3e-11; now a direct solve at the final set). The returned taps
  are verified on the grid. Near the precision limit (ripple about 1e-13) the languages may
  differ in whether a design raises, so that is a unit-test property, not a vector. New
  generator `vectors/generators/equiripple.py`: 50-digit Remez by cosine-basis solves and
  Clenshaw evaluation, each result certified by alternation; 33 cases (seven by hand, nine
  certified, 17 rejections). The library matches to 1e-14, except 2e-11 on a design with
  δ = 3e-9 whose taps are ill-determined in double. Python 1480 passed, 2 skipped; .NET 1166
  passed; conformance 702/702 in both.

- 2026-11-13: equiripple review. A random sweep against the generator's 50-digit solver (300
  designs to 70 taps) and Python against C# (481 designs to 400 taps) found two defects, both
  fixed in both languages and the conventions: (1) a first extremal set lying only in bands whose
  desired value is 0 gives `δ = 0` and too few extrema, and rounding at the set's last point
  could flip a sign, which raised on ordinary designs: the old set's points now always count in
  the exchange, with their exact error `±δ`; (2) the final tap check's 1e-6 margin rejected usable
  designs whose coefficients are large (wide gaps between bands), where rounding alone exceeds
  it: now 0.1%, which still catches the failures it is for. False rejections in the sweep fell
  from 205 to 158 of 481 (most of the rest are beyond double precision). Python no longer warns
  on an IEEE division by zero at the precision limit. New vector `zero_delta_start` (34 cases),
  a regression test per language. Python 1482 passed, 2 skipped; .NET 1168 passed; conformance 703/703 in both.
- 2026-11-13: Bessel IIR design, `bessel_lowpass` and `bessel_highpass` (`BesselLowpass`,
  `BesselHighpass`), ADR 0025: maximally flat delay, normalized to −3 dB at the cutoff, order 1 to
  10 (the reverse Bessel polynomial's roots lose digits fast beyond), poles by Aberth's iteration
  on the recurrence, through the existing cascade. Vectors: order 1 and 2 by hand, the rest from
  50-digit roots of the exact integer coefficients and a 50-digit `ω₀`, each checked against the
  closed-form `|H|²`; tests check −3 dB, monotonic magnitude, the flat delay against
  Butterworth's and the order-2 delay at DC (`ω₀/(2K)`).
- 2026-11-13: equiripple start by reference scaling (conventions, ADR 0024): above 16 cosine
  terms the design with half as many is solved first and its final set stretched along the bands
  to start the exchange. On the 481-design random sweep Python's raises fell from 158 to 136
  (C# 147); the rest are at the precision limit (relative ripple near 1e-13 or below, or taps so
  large that their cancellation leaves no digits). Where both languages design, ordinary ripples
  agree to 4 digits or better; taps differ only in designs whose taps reach 1e3 to 1e10, where
  they are determined only to rounding times their size.
- 2026-11-13: Hilbert transformers and differentiators (conventions: Equiripple design,
  ADR 0026): `fir_equiripple(..., kind="hilbert" | "differentiator")`, C# `EquirippleKind`.
  Antisymmetric taps (types III and IV) through the same exchange with `Q = sin(2πν)` or
  `sin(πν)`; `desired` 1 is the ideal (Hilbert `H = −j`, differentiator the derivative per
  sample), a differentiator's error relative to the slope where `desired ≠ 0`; a target that
  cannot be met where `Q = 0` raises. Vectors: three hand designs with `L = 1`, nine certified by
  the 50-digit generator (extended to types III and IV), five errors. Tests: a Hilbert
  transformer turns cos into sin, a differentiator gives the derivative, taps exactly
  antisymmetric.
- 2026-11-13: streaming resampling (conventions: Resampling, ADR 0027): `Resampler(up, down,
  taps=None)` with `process`, `reset` and `taps`, like `FirFilter`. Its causal stream
  `z[m] = L·Σ h[k]·u[mM − k]` is `resample` with the taps delayed by `N − 1`; after `n` inputs
  exactly `⌈nL/M⌉` outputs have come out, however the input was split. Taps of any length (even
  too); the default is `resample_taps`, or `[1]` at 1/1. Polyphase, `⌈N/L⌉` taps per phase.
  Vectors: one by hand, seven from the generator's term-by-term causal sum (cross-checked there
  against its delayed-taps `resample`), three errors. Tests: the identity with `resample` over
  random splits, complex input with even taps, reset, the real/complex kind fixed until reset.
- 2026-11-13: group delay (conventions: FIR filters and IIR filters, Group delay; ADR 0028):
  `fir_group_delay(taps, frequencies, sample_rate)` and `sos_group_delay(sos, ...)`, in samples,
  closed form per polynomial (`Re(R/P)`, sections add as numerator minus denominator), NaN where a
  polynomial is within rounding of 0 (a zero on the unit circle). Vectors: nine by hand (pure
  delay, linear phase, the NaN points, first-order and all-pass sections, `a0` scaling), four from
  a stdlib generator that expands chosen roots into taps and sums each root's own closed-form
  delay, six errors. Tests: both agree with a numerical phase derivative, sections add, linear
  phase taps give `(N − 1)/2`, and the Bessel low-pass delay is flat to 1% up to half the cutoff
  where the Butterworth's varies by 30% and more.
- 2026-11-13: least-squares FIR design (conventions: FIR filters, Least-squares design; ADR 0029):
  `fir_least_squares(num_taps, bands, desired, sample_rate, weights=None)`, symmetric taps (odd
  or even) minimizing the exact weighted integral squared error, `desired` given at both edges of
  each band and linear between. The normal equations are built from closed-form integrals and
  solved directly. Vectors: five by hand (orthogonal cosines over `[0, fs/2]`), seven from a
  stdlib generator that checks the integrals by Simpson quadrature and solves exactly in
  rational arithmetic (up to 101 taps), nine errors. Tests: symmetric perturbations only raise the
  error, lower error energy than the equiripple design, type II zero at `fs/2`, a sloped band
  followed.
- 2026-11-13: Welch options (conventions: Spectra, PSD; ADR 0030): `detrend` ("none",
  "constant", "linear") per segment before the window, in `welch_psd` and `spectrogram`, and
  `average="median"` in `welch_psd`, the per-bin median divided by `b(K)`, the exact expected
  median of `K` unit-mean exponentials (odd and even `K`). C#: `Detrend`, `WelchAverage`. Vectors
  (`welch.json`): five by hand, twelve from a stdlib generator that detrends by the uncentred
  normal equations and checks `b(K)` by integrating the order-statistic densities, three errors.
  Tests: detrending ignores an added constant or line (real and complex), the median is unbiased
  for white noise (odd and even `K`), resists a burst, and reads a steady tone `1/b(K)` high.
- 2026-11-13: zero padding (conventions: Spectra, PSD; ADR 0031): `nfft >= nperseg` on
  `welch_psd` and `spectrogram`, zeros after the windowed segment, the scale `1/(fs·Σw²)`
  unchanged so power sums keep their meaning; `bin_width = fs/nfft`, `enbw_hz` still
  `ENBW·fs/nperseg`; both results gain `nfft` (C#: `Nfft`, the last record member). Vectors in
  `welch.json`: one by hand, six generated, two errors. Tests: every `nfft/nperseg`-th padded bin
  is the unpadded bin (one- and two-sided), total power kept for odd and even `nfft`.
- 2026-11-13: Bessel band-pass and band-stop (conventions: IIR filters; ADR 0032): the Bessel
  prototype's poles through the shared band transform with the type I Chebyshev gains, −3 dB at
  `low` and `high`, `1 ≤ order ≤ 10`. Vectors in `iir.json`: two order-1 cases by hand, eight from
  the 50-digit roots (checked against the closed-form `|H|²` and the substituted denominator),
  four errors; orders 9 and 10 at 1e-11, the roots' double-precision accuracy. Tests: every order
  equals the low-pass at `fs/4` read at `atan(|x|)`, order 1 is the band Butterworth.
- 2026-11-13: all-pass sections (conventions: IIR filters, All-pass sections; ADR 0033):
  `allpass_first_order(cutoff, sample_rate)` (phase `−π/2` at the cutoff) and
  `allpass_second_order(center, bandwidth, sample_rate)` (`−π` at the center, the `−π/2` and
  `−3π/2` points exactly `bandwidth` apart), one section each. Vectors in `iir.json`: four by
  hand, five checked at `H = −j, −1, j` with the edges from their closed form, five errors.
  Tests: unit magnitude, monotone phase, the group delay integrating to the total phase, power
  kept through `IirFilter`. The planned "mixing" slice was dropped: `frequency_offset` already
  is it.
- 2026-11-13: IQ imbalance and DC offset (conventions: Channel; ADR 0034):
  `iq_imbalance(samples, gain_db, phase)` with the error on the Q branch
  (`y = I + j·g·(Q·cos φ + I·sin φ)`), `iq_image_rejection_db(gain_db, phase)` and
  `dc_offset(samples, offset)`. 17 vectors in `channel.json`: by hand, and from the widely
  linear form `μx + νx̄` (independent of the branch form). Tests: a tone's DFT image matches the
  image rejection, the Q branch is `g·sin(θ + φ)`, no other bin is touched.
- 2026-11-13: 8-PSK and 16-QAM (conventions: Bits and symbols; ADR 0035): `psk8_map`,
  `psk8_demap_hard` (point `p` at `e^{jπp/4}`, label `p ⊕ (p >> 1)`), `qam16_map`,
  `qam16_demap_hard` (two Gray 4-PAM axes, first bit 0 positive, over `√10`, thresholds 0 and
  `2/√10`). 12 vectors by hand in `modulation.json`. Tests: round trips, unit energy, every
  nearest-neighbor pair differs in one bit, noise under the decision margin changes nothing. Review: a NaN symbol
  is `invalid_argument` in both demappers (Python cast it to an arbitrary integer sector).
- 2026-11-13: phase noise (conventions: Channel; ADR 0036): `phase_noise(samples, linewidth_hz,
  sample_rate, *, seed)`, a Wiener walk from `φ[0] = 0` with Gaussian steps of variance
  `2π·linewidth/fs`. Five vectors (zero linewidth, one sample, three errors); the random part is
  checked in each language against theory: the step variance, the variance over a lag, and
  `E[e^{jφ[n]}] = e^{−nσ²/2}` over 4000 runs.
- 2026-11-13: error-rate theory (conventions: EVM and BER; ADR 0037): `qam16_ber_theory`,
  `qam16_ser_theory` (closed forms), `psk8_ser_theory` and `psk8_ber_theory` (Pawula's phase-tail
  integral by Simpson, 4096 panels), all exact for our Gray labelings; the 8-PSK BER is
  `⅔·(T(π/8) + T(3π/8))`, not the `Ps/3` approximation the plan named. 36 vectors from
  `vectors/generators/error_rates.py`, which checks the 16-QAM forms against integrating the
  Gaussian over the decision intervals and gets 8-PSK from the phase density instead. Tests:
  limits, monotone, the high-SNR approximations, and Monte-Carlo runs through map, AWGN and
  demap at 8 dB (within 6 %). Python 1895 passed, 2 skipped; .NET 1519 passed.
- 2026-11-13: static multipath (conventions: Channel; ADR 0038): `multipath(samples, delays,
  gains)`, a tapped delay line with integer delays and complex gains, output as long as the input
  (tail dropped), gains not normalized. 12 vectors by hand in `channel.json`; tests against a
  dense convolution. Python 1919 passed, 2 skipped; .NET 1533 passed.
- 2026-11-13: soft demapping (conventions: Bits and symbols; ADR 0039): `qpsk_demap_llr`,
  `psk8_demap_llr`, `qam16_demap_llr` `(symbols, noise_variance)`, max-log LLRs by a search over
  the points, positive for bit 0, `noise_variance = N0`. 22 vectors (4 by hand, the rest empty
  input and errors); tests: the sign is the hard decision, QPSK equals `2√2·Re(y)/N0` exactly,
  within `ln(M/2)` of the exact log-sum LLR, scaling with `N0`. Python 1952 passed, 2 skipped;
  .NET 1563 passed.
- 2026-11-13: fractional delay (conventions: Channel; ADR 0040): `fractional_delay(samples, delay,
  *, half_width=16)`, a Kaiser-windowed sinc (β = 8) evaluated per output sample, exact shifts for
  whole-sample delays, zero outside the input. Fractional multipath is a sum of these, so
  `multipath` keeps integer delays. 15 vectors from `vectors/generators/fractional_delay.py` (the
  sum over every input sample, its own I0 series); tests: tones up to 0.25·fs within 5e-5
  (measured floor about 2e-5), exact integer shifts. Python 1976 passed, 2 skipped; .NET 1583
  passed.
- 2026-11-13: LLR statistics through the receive chain (tests only): QPSK through RRC shaping,
  AWGN, the matched filter and sampling at Es/N0 = 7 dB gives signed LLRs with mean `2·Es/N0`
  and variance twice that, within 1.5 % and 2 % (measured within 0.3 %), in both link suites.
  Python 1977 passed, 2 skipped; .NET 1584 passed.
- 2026-11-13: block fading (conventions: Channel; ADR 0041): `rician_fading(samples, k_factor,
  block_length, *, seed)`, one gain `√(K/(K+1)) + √(1/(K+1))·CN(0, 1)` per block, Rayleigh at
  K = 0, no fading at K = ∞. 6 deterministic vectors in channel.json (K = ∞, empty, bad
  arguments); tests: mean power, mean, per-axis variance for K = 0, 1, 3, 10, the Rayleigh power
  CDF, one gain per block with a short last block, seeding. Python 1998 passed, 2 skipped;
  .NET 1598 passed.
- 2026-11-13: QPSK in Rayleigh fading (conventions: EVM and BER; ADR 0042):
  `qpsk_ber_rayleigh_theory(eb_n0_db)`, `½(1 − √(γ/(1+γ)))` in a form without cancellation. 9
  vectors added to `error_rates.py`, checked there against the AWGN curve averaged over the
  exponential |g|² density; tests: limits, `1/(4γ)` asymptote, above the AWGN curve, and
  Monte-Carlo through `rician_fading` (K = 0) with coherent detection at 0, 5 and 10 dB within
  6 % (measured within 2 %). Python 2011 passed, 2 skipped; .NET 1611 passed.
- 2026-11-13: fractional timing end to end (tests): a shaped QPSK burst delayed by 0.3 … 3.9
  samples through `fractional_delay`; `timing_offset` finds it within 0.05 samples (measured
  within 0.014), undoing the fraction gives the AWGN BER within 10 %, and sampling half a sample
  or more off is over 1.3 times worse. `fractional_delay` now evaluates its kernel once per
  distinct fraction in both languages (same arithmetic, about 9 times faster on long inputs).
  Python 2015 passed, 2 skipped; .NET 1615 passed.

## Not built

Everything else in the brief: IIR designs beyond Butterworth, Chebyshev I/II, elliptic, Bessel and all-pass sections (all-pass design to a delay target), FIR design beyond windowed sinc, equiripple and least squares (arbitrary-magnitude bands, frequency sampling), spectral estimators beyond Welch and the spectrogram
(multitaper, Lomb-Scargle), the rest of modulation (PSK/QAM
beyond QPSK, 8-PSK and 16-QAM, FSK, OFDM, analog), impairments beyond AWGN, frequency offset, IQ imbalance, DC offset, Wiener phase noise and static multipath, fractional delay and block fading, tracking loops (timing, carrier), RF measurements (ACPR channel filtering,
phase noise, NF), standards waveforms, file formats beyond SigMF (WAV, NumPy, streaming reads and writes, multi-channel and
multi-capture recordings, SigMF annotations, unsigned sample types), plotting, CLI,
packaging and publishing.

## Lessons

- 2026-11-13: Before putting a feature in Next, grep for it: "mixing" was planned while
  `frequency_offset` already multiplied by `e^(j(2π f n/fs + φ))` in both languages.
- 2026-11-12: The test for any dependency is whether it could ever force our code under the GPL or
  limit commercial shipping. A GPL label on a compiler runtime with the GCC exception does not.
- 2026-11-12: Check build tools' licenses too: hatchling and mypy both pull in pathspec (MPL-2.0).
  flit_core is clean. Whether a tool is shipped decides which licenses it may use (ADR 0005).
- 2026-11-12: NumPy's type stubs differ by version: Python 3.10 gets NumPy 2.2, which rejects a bare
  `np.ndarray` under strict mypy. Annotate with `NDArray[dtype]` and run mypy on both Pythons.
- 2026-11-12: Binary wheels can bundle libraries under other licenses; read the wheel's own
  `LICENSE.txt`, not just the project's top-level license.
- 2026-11-12: The `dotnet new xunit` template is xunit v2; there is no `xunit3` template in the SDK.
- 2026-11-12: Avoid long bash heredocs with quotes in JSON or C#; write such files directly.
- 2026-11-13: Windows PowerShell 5.1 splits a splatted `-m:1` into `- m : 1` for native commands;
  pass MSBuild switches as `/m:1`. Git Bash does the opposite: it turns `/m:1` into a path, so
  type `-m:1` there.
- 2026-11-13: Git Bash mangles backslash paths passed through `cmd /c`; run cmd invocations from
  the PowerShell tool instead.
- 2026-11-13: A conformance runner needs its own tests. Hand-written wrong cases
  (`vectors/selftest`) caught a C# runner that passed cases it never really ran.
- 2026-11-13: NumPy wheels bundle different native libraries per platform (Linux ships
  libquadmath, Windows doesn't). Check the wheels for every platform CI or users install, not
  only the local one.
- 2026-11-13: For a special function, check relative error over the whole range against the C
  library before trusting it. The naive `exp(-x*x)` in erfc costs about 1e-13 near x = 25 from
  the rounding of x²; splitting x into a short `z` plus a remainder fixes it. Below about 1e-308
  results are subnormal and relative error stops meaning anything.
- 2026-11-13: Test an estimator inside the whole chain, at the SNR it will be used at, before
  trusting it. The fourth-power frequency estimate looked fine at 20 dB and on clean vectors, but
  at 6 dB its error (0.1 to 0.5 Hz at Rs = 1000) turned a long frame by whole turns. A link test
  that skips a step when its parameter is zero (no frequency correction at 0 Hz) hides exactly this.
- 2026-11-13: Diff the two languages' full results, not just each against a partial expected
  value. A vector checks only the fields it lists, so a field one runner never sees (a Python
  property, where C# reflection sees every property) passes everywhere until the results are
  compared with each other.
- 2026-11-13: `np.asarray` returns the caller's own array when it already has the right dtype,
  so an object that keeps an argument (filter taps) must copy it with `np.array`. C# copies
  with `ToArray()` by habit; Python needs the same care, and a test that mutates the input.
