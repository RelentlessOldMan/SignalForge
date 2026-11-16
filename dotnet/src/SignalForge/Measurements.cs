using System.Numerics;

namespace SignalForge;

/// <summary>
/// Power statistics of a sample sequence, in sample units (squared for powers). <see cref="Dc"/> is
/// the mean sample. <see cref="PeakIndex"/> is the first sample with the largest |x|². PAPR is
/// 10·log10(peak / mean) in dB, NaN when the mean power is zero.
/// </summary>
/// <param name="NumSamples">Number of samples measured.</param>
/// <param name="MeanPower">Mean of |x|².</param>
/// <param name="Rms">Square root of the mean power.</param>
/// <param name="PeakPower">Largest |x|².</param>
/// <param name="PeakAmplitude">Largest |x|.</param>
/// <param name="PeakIndex">First index of the largest |x|².</param>
/// <param name="PaprDb">Peak-to-average power ratio in dB.</param>
/// <param name="Dc">Mean sample (complex mean; imaginary part 0 for real input).</param>
public sealed record PowerStats(
    int NumSamples,
    double MeanPower,
    double Rms,
    double PeakPower,
    double PeakAmplitude,
    int PeakIndex,
    double PaprDb,
    Complex Dc);

/// <summary>
/// SNR, SINAD, THD and ENOB of one tone (conventions: Tone metrics). Powers are in sample units²,
/// summed over bin groups of one windowed spectrum.
/// </summary>
/// <param name="FundamentalFrequency">Power-weighted centroid of the fundamental's group, in Hz.</param>
/// <param name="SignalPower">Power of the fundamental's group.</param>
/// <param name="HarmonicPower">Power of all the harmonic groups.</param>
/// <param name="NoisePower">Power of every bin in no group.</param>
/// <param name="DcPower">Power of the DC group.</param>
/// <param name="SnrDb">10·log10(signal / noise); +∞ for no noise.</param>
/// <param name="SinadDb">10·log10(signal / (noise + harmonics)); +∞ when both are zero.</param>
/// <param name="ThdDb">10·log10(harmonics / signal); −∞ for no harmonics.</param>
/// <param name="Enob">(SINAD − 10·log10 1.5) / (20·log10 2), in bits.</param>
public sealed record ToneMetrics(
    double FundamentalFrequency,
    double SignalPower,
    double HarmonicPower,
    double NoisePower,
    double DcPower,
    double SnrDb,
    double SinadDb,
    double ThdDb,
    double Enob);

/// <summary>
/// Spurious-free dynamic range and the strongest spurs (conventions: Spurs and SFDR). The carrier is
/// the tone metrics' fundamental group; spurs are the next strongest groups, DC excluded, strongest
/// peak bin first.
/// </summary>
/// <param name="CarrierFrequency">Power-weighted centroid of the carrier's group, in Hz.</param>
/// <param name="CarrierPower">Power of the carrier's group, in sample units².</param>
/// <param name="SfdrDb">Minus the first spur's dBc; +∞ when there is no spur.</param>
/// <param name="SpurFrequencies">Each spur's power centroid, in Hz.</param>
/// <param name="SpurPowers">Each spur's group power, in sample units².</param>
/// <param name="SpurDbc">Each spur relative to the carrier: 10·log10(spur / carrier).</param>
public sealed record Sfdr(
    double CarrierFrequency,
    double CarrierPower,
    double SfdrDb,
    double[] SpurFrequencies,
    double[] SpurPowers,
    double[] SpurDbc);

/// <summary>
/// Third-order intermodulation of two tones (conventions: Two-tone intermodulation; ADR 0107).
/// Tones and products come lower first; powers in sample units².
/// </summary>
/// <param name="ToneFrequencies">The two tones' power centroids, in Hz.</param>
/// <param name="TonePowers">The two tones' group powers.</param>
/// <param name="ImdFrequencies">2f₁ − f₂ and 2f₂ − f₁, aliased into the spectrum, in Hz.</param>
/// <param name="ImdPowers">The two products' group powers.</param>
/// <param name="ImdDbc">Each product relative to the mean tone power; −∞ for no power.</param>
/// <param name="WorstImdDbc">The larger of <paramref name="ImdDbc"/>.</param>
/// <param name="Ip3Db">10·log10(mean tone power) − <paramref name="WorstImdDbc"/>/2.</param>
public sealed record TwoToneImd(
    double[] ToneFrequencies,
    double[] TonePowers,
    double[] ImdFrequencies,
    double[] ImdPowers,
    double[] ImdDbc,
    double WorstImdDbc,
    double Ip3Db);

/// <summary>Single-sideband phase noise of a carrier (conventions: Phase noise measurement;
/// ADR 0108).</summary>
/// <param name="CarrierFrequency">The carrier group's power centroid, in Hz.</param>
/// <param name="CarrierPower">The carrier group's power, in sample units².</param>
/// <param name="Offsets">The offsets from the carrier, in Hz.</param>
/// <param name="LDbcHz">L at each offset: the two sidebands' mean PSD over the carrier power, in dBc/Hz.</param>
public sealed record PhaseNoise(double CarrierFrequency, double CarrierPower, double[] Offsets, double[] LDbcHz);

/// <summary>Phase noise integrated over an offset band (conventions: Integrated phase noise;
/// ADR 0109).</summary>
/// <param name="CarrierFrequency">The carrier group's power centroid, in Hz.</param>
/// <param name="CarrierPower">The carrier group's power, in sample units².</param>
/// <param name="FLo">The band's lower offset, in Hz.</param>
/// <param name="FHi">The band's upper offset, in Hz.</param>
/// <param name="IntegratedDbc">The band's power on both sides over the carrier power, in dBc.</param>
/// <param name="PhaseRms">The RMS phase error, in radians.</param>
/// <param name="JitterRms">The RMS jitter, PhaseRms/(2π|CarrierFrequency|), in seconds.</param>
public sealed record IntegratedPhaseNoise(double CarrierFrequency, double CarrierPower, double FLo, double FHi,
    double IntegratedDbc, double PhaseRms, double JitterRms);

/// <summary>A Y-factor noise figure measurement (conventions: Noise figure; ADR 0105).</summary>
/// <param name="YFactor">Hot over cold output power.</param>
/// <param name="NoiseFactor">The linear noise factor F.</param>
/// <param name="NoiseFigureDb">10·log10 F.</param>
/// <param name="NoiseTemperature">290·(F − 1), in kelvin.</param>
public sealed record NoiseFigure(double YFactor, double NoiseFactor, double NoiseFigureDb, double NoiseTemperature);

/// <summary>The noise figure of matched stages in a chain (conventions: Noise figure, Cascade;
/// ADR 0106).</summary>
/// <param name="NoiseFactor">The chain's linear noise factor F.</param>
/// <param name="NoiseFigureDb">10·log10 F.</param>
/// <param name="NoiseTemperature">290·(F − 1), in kelvin.</param>
/// <param name="GainDb">The stages' gains summed, in dB.</param>
/// <param name="Contributions">Each stage's term of Friis' sum, in chain order.</param>
public sealed record CascadeNoiseFigure(double NoiseFactor, double NoiseFigureDb, double NoiseTemperature, double GainDb, double[] Contributions);

/// <summary>Power measurements and tone metrics. Definitions in docs/conventions.md.</summary>
public static class Measurements
{
    /// <summary>Mean power, RMS, peak, PAPR and DC of complex samples (at least one).</summary>
    public static PowerStats PowerStats(ReadOnlySpan<Complex> samples)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("needs at least one sample", nameof(samples));
        double sum = 0, peak = -1;
        int peakIndex = 0;
        Complex dc = Complex.Zero;
        for (int i = 0; i < samples.Length; i++)
        {
            Complex x = samples[i];
            if (!(double.IsFinite(x.Real) && double.IsFinite(x.Imaginary)))
                throw new ArgumentException("samples must be finite", nameof(samples));
            double p = x.Real * x.Real + x.Imaginary * x.Imaginary;
            sum += p;
            dc += x;
            if (p > peak)
            {
                peak = p;
                peakIndex = i;
            }
        }
        return Build(samples.Length, sum, peak, peakIndex, dc);
    }

    /// <summary>Mean power, RMS, peak, PAPR and DC of real samples (at least one).</summary>
    public static PowerStats PowerStats(ReadOnlySpan<double> samples)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("needs at least one sample", nameof(samples));
        double sum = 0, peak = -1, dc = 0;
        int peakIndex = 0;
        for (int i = 0; i < samples.Length; i++)
        {
            double x = samples[i];
            if (!double.IsFinite(x))
                throw new ArgumentException("samples must be finite", nameof(samples));
            double p = x * x;
            sum += p;
            dc += x;
            if (p > peak)
            {
                peak = p;
                peakIndex = i;
            }
        }
        return Build(samples.Length, sum, peak, peakIndex, dc);
    }

    private static PowerStats Build(int n, double sum, double peak, int peakIndex, Complex dcSum)
    {
        double mean = sum / n;
        double papr = mean > 0 ? 10.0 * Math.Log10(peak / mean) : double.NaN;
        return new PowerStats(n, mean, Math.Sqrt(mean), peak, Math.Sqrt(peak), peakIndex, papr, dcSum / n);
    }

    /// <summary>
    /// SNR, SINAD, THD and ENOB of the strongest tone in real samples (or the one at
    /// <paramref name="fundamental"/>), from a one-sided spectrum. <paramref name="width"/> is the
    /// half-width of each bin group, by default set by the window; harmonics 2 …
    /// <paramref name="numHarmonics"/> + 1 are found at multiples of the fundamental, aliased.
    /// </summary>
    public static ToneMetrics ToneMetrics(ReadOnlySpan<double> samples, double sampleRate,
        WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null,
        int numHarmonics = 5, double? fundamental = null)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(numHarmonics);
        Check(samples.Length, width, fundamental);
        return Tone(new ToneGroups(Spectral.WelchPsd(samples, sampleRate, window: window, beta: beta), window, beta, width, fundamental), numHarmonics);
    }

    /// <summary>
    /// SNR, SINAD, THD and ENOB of the strongest tone in complex samples (or the one at
    /// <paramref name="fundamental"/>), from a two-sided spectrum; otherwise as for real samples.
    /// </summary>
    public static ToneMetrics ToneMetrics(ReadOnlySpan<Complex> samples, double sampleRate,
        WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null,
        int numHarmonics = 5, double? fundamental = null)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(numHarmonics);
        Check(samples.Length, width, fundamental);
        return Tone(new ToneGroups(Spectral.WelchPsd(samples, sampleRate, window: window, beta: beta), window, beta, width, fundamental), numHarmonics);
    }

    /// <summary>
    /// SFDR of the strongest tone in real samples (or the one at <paramref name="fundamental"/>) and up
    /// to <paramref name="numSpurs"/> spurs. Groups are formed as for <see cref="ToneMetrics(ReadOnlySpan{double}, double, WindowType, double?, int?, int, double?)"/>;
    /// after DC and the carrier, each spur is the group around the strongest bin left, until
    /// <paramref name="numSpurs"/> are found or no bin with power is left.
    /// </summary>
    public static Sfdr Sfdr(ReadOnlySpan<double> samples, double sampleRate,
        WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null,
        double? fundamental = null, int numSpurs = 1)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(numSpurs, 1);
        Check(samples.Length, width, fundamental);
        return Spurs(new ToneGroups(Spectral.WelchPsd(samples, sampleRate, window: window, beta: beta), window, beta, width, fundamental), numSpurs);
    }

    /// <summary>
    /// SFDR of the strongest tone in complex samples (or the one at <paramref name="fundamental"/>)
    /// and up to <paramref name="numSpurs"/> spurs, from a two-sided spectrum; otherwise as for real
    /// samples.
    /// </summary>
    public static Sfdr Sfdr(ReadOnlySpan<Complex> samples, double sampleRate,
        WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null,
        double? fundamental = null, int numSpurs = 1)
    {
        ArgumentOutOfRangeException.ThrowIfLessThan(numSpurs, 1);
        Check(samples.Length, width, fundamental);
        return Spurs(new ToneGroups(Spectral.WelchPsd(samples, sampleRate, window: window, beta: beta), window, beta, width, fundamental), numSpurs);
    }

    /// <summary>Noise figure from the output powers with a noise source hot and cold:
    /// F = (ENR − Y·(T_c/T₀ − 1))/(Y − 1), T₀ = 290 K (conventions: Noise figure; ADR 0105).</summary>
    /// <param name="hotPower">Output power with the source on, linear, above <paramref name="coldPower"/>.</param>
    /// <param name="coldPower">Output power with the source off, linear, positive, same unit.</param>
    /// <param name="enrDb">The source's excess noise ratio in dB, finite.</param>
    /// <param name="coldTemperature">The cold source's temperature in kelvin, positive.</param>
    /// <returns>Y, F, the noise figure in dB and the noise temperature.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or F is not finite and positive.</exception>
    public static NoiseFigure NoiseFigureYFactor(double hotPower, double coldPower, double enrDb, double coldTemperature = 290)
    {
        const double t0 = 290;
        if (!(coldPower > 0) || !double.IsFinite(coldPower))
            throw new ArgumentOutOfRangeException(nameof(coldPower), coldPower, "must be finite and positive");
        if (!double.IsFinite(hotPower) || !(hotPower > coldPower))
            throw new ArgumentOutOfRangeException(nameof(hotPower), hotPower, "must be finite and greater than coldPower");
        if (!double.IsFinite(enrDb))
            throw new ArgumentOutOfRangeException(nameof(enrDb), enrDb, "must be finite");
        if (!(coldTemperature > 0) || !double.IsFinite(coldTemperature))
            throw new ArgumentOutOfRangeException(nameof(coldTemperature), coldTemperature, "must be finite and positive");
        double y = hotPower / coldPower;
        double f = (Math.Pow(10, enrDb / 10) - y * (coldTemperature / t0 - 1)) / (y - 1);
        if (!(f > 0) || !double.IsFinite(f))
            throw new ArgumentException("the measurement gives no finite positive noise factor", nameof(hotPower));
        return new NoiseFigure(y, f, 10 * Math.Log10(f), t0 * (f - 1));
    }

    /// <summary>Friis' noise factor of matched stages in chain order:
    /// F = F₁ + (F₂ − 1)/G₁ + (F₃ − 1)/(G₁G₂) + … (conventions: Noise figure, Cascade; ADR 0106).</summary>
    /// <param name="noiseFiguresDb">Each stage's noise figure in dB, finite, not negative.</param>
    /// <param name="gainsDb">Each stage's gain in dB, finite; negative for a loss.</param>
    /// <returns>F, the noise figure in dB, the noise temperature, the total gain and each stage's term.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or F is not finite.</exception>
    public static CascadeNoiseFigure NoiseFigureCascade(ReadOnlySpan<double> noiseFiguresDb, ReadOnlySpan<double> gainsDb)
    {
        if (noiseFiguresDb.IsEmpty || noiseFiguresDb.Length != gainsDb.Length)
            throw new ArgumentException("noise figures and gains need the same number of stages, at least 1", nameof(gainsDb));
        for (int i = 0; i < noiseFiguresDb.Length; i++)
        {
            if (!double.IsFinite(noiseFiguresDb[i]) || !double.IsFinite(gainsDb[i]))
                throw new ArgumentException("noise figures and gains must be finite", nameof(noiseFiguresDb));
            if (noiseFiguresDb[i] < 0)
                throw new ArgumentOutOfRangeException(nameof(noiseFiguresDb), noiseFiguresDb[i], "must not be negative");
        }
        var c = new double[noiseFiguresDb.Length];
        double before = 1, total = 0, gainDb = 0;
        for (int i = 0; i < c.Length; i++)
        {
            double f = Math.Pow(10, noiseFiguresDb[i] / 10);
            c[i] = i == 0 ? f : (f - 1) / before;
            total += c[i];
            before *= Math.Pow(10, gainsDb[i] / 10);
            gainDb += gainsDb[i];
        }
        if (!double.IsFinite(total))
            throw new ArgumentException("the gains before a noisy stage underflow: no finite noise factor", nameof(gainsDb));
        return new CascadeNoiseFigure(total, 10 * Math.Log10(total), 290 * (total - 1), gainDb, c);
    }

    /// <summary>
    /// The tones at <paramref name="f1"/> &lt; <paramref name="f2"/> in real samples and their
    /// third-order products 2f₁ − f₂ and 2f₂ − f₁, grouped as for the tone metrics (conventions:
    /// Two-tone intermodulation; ADR 0107).
    /// </summary>
    /// <param name="samples">Real samples, at least two.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="f1">The lower tone's frequency in Hz.</param>
    /// <param name="f2">The upper tone's frequency in Hz.</param>
    /// <param name="window">Window of the one-segment spectrum.</param>
    /// <param name="beta">Kaiser β, for the Kaiser window only.</param>
    /// <param name="width">Half-width of each bin group; by default set by the window.</param>
    /// <returns>The tones, the products, their dBc and the intercept.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a group would overlap another.</exception>
    public static TwoToneImd TwoToneImd(ReadOnlySpan<double> samples, double sampleRate, double f1, double f2,
        WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null)
    {
        CheckTones(samples.Length, width, f1, f2);
        return Imd(new ToneGroups(Spectral.WelchPsd(samples, sampleRate, window: window, beta: beta), window, beta, width, f1), f1, f2);
    }

    /// <summary>As for real samples, from the two-sided spectrum of complex samples.</summary>
    /// <param name="samples">Complex samples, at least two.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="f1">The lower tone's frequency in Hz.</param>
    /// <param name="f2">The upper tone's frequency in Hz.</param>
    /// <param name="window">Window of the one-segment spectrum.</param>
    /// <param name="beta">Kaiser β, for the Kaiser window only.</param>
    /// <param name="width">Half-width of each bin group; by default set by the window.</param>
    /// <returns>The tones, the products, their dBc and the intercept.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a group would overlap another.</exception>
    public static TwoToneImd TwoToneImd(ReadOnlySpan<Complex> samples, double sampleRate, double f1, double f2,
        WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null)
    {
        CheckTones(samples.Length, width, f1, f2);
        return Imd(new ToneGroups(Spectral.WelchPsd(samples, sampleRate, window: window, beta: beta), window, beta, width, f1), f1, f2);
    }

    /// <summary>L(f) in dBc/Hz of real samples at each offset from the strongest bin (or the one
    /// at <paramref name="carrier"/>), from a Welch PSD (conventions: Phase noise measurement;
    /// ADR 0108).</summary>
    /// <param name="samples">Real samples, at least two.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="offsets">Offsets from the carrier in Hz, finite and positive.</param>
    /// <param name="carrier">The carrier's frequency; by default the strongest bin.</param>
    /// <param name="nperseg">Welch segment length; by default the whole input.</param>
    /// <param name="window">Window of the Welch segments.</param>
    /// <param name="beta">Kaiser β, for the Kaiser window only.</param>
    /// <param name="width">Half-width of the carrier group; by default set by the window.</param>
    /// <returns>The carrier and L at each offset.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or an offset falls in the carrier group or past the spectrum.</exception>
    public static PhaseNoise PhaseNoiseSsb(ReadOnlySpan<double> samples, double sampleRate, ReadOnlySpan<double> offsets,
        double? carrier = null, int? nperseg = null, WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null)
    {
        CheckOffsets(samples.Length, offsets, width, carrier);
        return Ssb(FindCarrier(Spectral.WelchPsd(samples, sampleRate, nperseg, window: window, beta: beta), carrier, window, beta, width), offsets);
    }

    /// <summary>As for real samples, from the two-sided spectrum of complex samples.</summary>
    /// <param name="samples">Complex samples, at least two.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="offsets">Offsets from the carrier in Hz, finite and positive.</param>
    /// <param name="carrier">The carrier's frequency; by default the strongest bin.</param>
    /// <param name="nperseg">Welch segment length; by default the whole input.</param>
    /// <param name="window">Window of the Welch segments.</param>
    /// <param name="beta">Kaiser β, for the Kaiser window only.</param>
    /// <param name="width">Half-width of the carrier group; by default set by the window.</param>
    /// <returns>The carrier and L at each offset.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or an offset falls in the carrier group or past the spectrum.</exception>
    public static PhaseNoise PhaseNoiseSsb(ReadOnlySpan<Complex> samples, double sampleRate, ReadOnlySpan<double> offsets,
        double? carrier = null, int? nperseg = null, WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null)
    {
        CheckOffsets(samples.Length, offsets, width, carrier);
        return Ssb(FindCarrier(Spectral.WelchPsd(samples, sampleRate, nperseg, window: window, beta: beta), carrier, window, beta, width), offsets);
    }

    /// <summary>RMS phase error and jitter of real samples from the PSD over offsets
    /// <paramref name="fLo"/> … <paramref name="fHi"/> on both sides of the carrier, whole bins only
    /// (conventions: Integrated phase noise; ADR 0109).</summary>
    /// <param name="samples">Real samples, at least two.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="fLo">The band's lower offset in Hz, positive.</param>
    /// <param name="fHi">The band's upper offset in Hz, above <paramref name="fLo"/> and finite.</param>
    /// <param name="carrier">The carrier's frequency; by default the strongest bin.</param>
    /// <param name="nperseg">Welch segment length; by default the whole input.</param>
    /// <param name="window">Window of the Welch segments.</param>
    /// <param name="beta">Kaiser β, for the Kaiser window only.</param>
    /// <param name="width">Half-width of the carrier group; by default set by the window.</param>
    /// <returns>The carrier, the integrated power, the RMS phase and the RMS jitter.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the band reaches into the carrier group or past the spectrum.</exception>
    public static IntegratedPhaseNoise IntegratedPhaseNoise(ReadOnlySpan<double> samples, double sampleRate, double fLo, double fHi,
        double? carrier = null, int? nperseg = null, WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null)
    {
        CheckBand(fLo, fHi);
        CheckCarrierArgs(samples.Length, width, carrier);
        return Integrate(FindCarrier(Spectral.WelchPsd(samples, sampleRate, nperseg, window: window, beta: beta), carrier, window, beta, width), fLo, fHi);
    }

    /// <summary>As for real samples, from the two-sided spectrum of complex samples.</summary>
    /// <param name="samples">Complex samples, at least two.</param>
    /// <param name="sampleRate">Sample rate in Hz.</param>
    /// <param name="fLo">The band's lower offset in Hz, positive.</param>
    /// <param name="fHi">The band's upper offset in Hz, above <paramref name="fLo"/> and finite.</param>
    /// <param name="carrier">The carrier's frequency; by default the strongest bin.</param>
    /// <param name="nperseg">Welch segment length; by default the whole input.</param>
    /// <param name="window">Window of the Welch segments.</param>
    /// <param name="beta">Kaiser β, for the Kaiser window only.</param>
    /// <param name="width">Half-width of the carrier group; by default set by the window.</param>
    /// <returns>The carrier, the integrated power, the RMS phase and the RMS jitter.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the band reaches into the carrier group or past the spectrum.</exception>
    public static IntegratedPhaseNoise IntegratedPhaseNoise(ReadOnlySpan<Complex> samples, double sampleRate, double fLo, double fHi,
        double? carrier = null, int? nperseg = null, WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null)
    {
        CheckBand(fLo, fHi);
        CheckCarrierArgs(samples.Length, width, carrier);
        return Integrate(FindCarrier(Spectral.WelchPsd(samples, sampleRate, nperseg, window: window, beta: beta), carrier, window, beta, width), fLo, fHi);
    }

    private static void CheckBand(double fLo, double fHi)
    {
        if (!(fLo > 0 && fLo < fHi && fHi < double.PositiveInfinity))
            throw new ArgumentException("the band needs 0 < f_lo < f_hi, finite", nameof(fLo));
    }

    private static void CheckOffsets(int samples, ReadOnlySpan<double> offsets, int? width, double? carrier)
    {
        if (offsets.IsEmpty)
            throw new ArgumentException("offsets must not be empty", nameof(offsets));
        foreach (double o in offsets)
            if (!(o > 0) || !double.IsFinite(o))
                throw new ArgumentOutOfRangeException(nameof(offsets), o, "offsets must be finite and positive");
        CheckCarrierArgs(samples, width, carrier);
    }

    private static void CheckCarrierArgs(int samples, int? width, double? carrier)
    {
        if (samples < 2)
            throw new ArgumentException("phase noise needs at least two samples", nameof(samples));
        if (width is < 0)
            throw new ArgumentOutOfRangeException(nameof(width), "width must be non-negative");
        if (carrier is { } f && !double.IsFinite(f))
            throw new ArgumentException("carrier must be finite", nameof(carrier));
    }

    /// <summary>A Welch PSD with its carrier bin <c>C</c>, group half-width <c>W</c>, group power and centroid.</summary>
    private readonly record struct PnCarrier(SpectralDensity D, int C, int W, double Pc, double Fc)
    {
        public int Nearest(double x) => (int)Math.Clamp(Math.Floor((x - D.Frequencies[0]) / D.BinWidth + 0.5), 0, D.Psd.Length - 1);

        public void CheckReach(double o, string what)
        {
            double fs = D.SampleRate, lo = D.OneSided ? 0 : -fs / 2;
            if (!(Fc - o >= lo && (D.OneSided ? Fc + o <= fs / 2 : Fc + o < fs / 2)))
                throw new ArgumentException($"{what} reaches past the spectrum", nameof(o));
        }
    }

    private static PnCarrier FindCarrier(SpectralDensity d, double? carrier, WindowType window, double? beta, int? width)
    {
        double fs = d.SampleRate, df = d.BinWidth;
        double[] psd = d.Psd;
        int n = psd.Length;
        double total = 0;
        foreach (double v in psd)
            total += v * df;
        if (!double.IsFinite(total))
            throw new ArgumentException("samples must be finite and small enough for a finite spectrum", nameof(d));
        int w = Math.Min(width ?? HalfWidth(window, beta), n);
        int c = 0;
        if (carrier is { } given)
        {
            if (!(Math.Abs(given) <= fs / 2 && (given >= 0 || !d.OneSided)))
                throw new ArgumentException("carrier must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)", nameof(carrier));
            c = new PnCarrier(d, 0, 0, 0, 0).Nearest(d.OneSided ? given : FlooredMod(given + fs / 2, fs) - fs / 2);
        }
        else
        {
            for (int k = 1; k < n; k++)
                if (psd[k] > psd[c])
                    c = k;
        }
        double pc = 0, moment = 0;
        for (int k = Math.Max(c - w, 0); k <= Math.Min(c + w, n - 1); k++)
        {
            pc += psd[k] * df;
            moment += psd[k] * df * d.Frequencies[k];
        }
        if (!(pc > 0))
            throw new ArgumentException("no power at the carrier", nameof(carrier));
        return new PnCarrier(d, c, w, pc, moment / pc);
    }

    private static PhaseNoise Ssb(PnCarrier k, ReadOnlySpan<double> offsets)
    {
        double[] psd = k.D.Psd;
        var l = new double[offsets.Length];
        for (int i = 0; i < l.Length; i++)
        {
            double o = offsets[i];
            k.CheckReach(o, "an offset");
            int ka = k.Nearest(k.Fc - o), kb = k.Nearest(k.Fc + o);
            if (Math.Abs(ka - k.C) <= k.W || Math.Abs(kb - k.C) <= k.W)
                throw new ArgumentException("an offset falls in the carrier group", nameof(offsets));
            double s = (psd[ka] + psd[kb]) / 2;
            l[i] = s > 0 ? 10 * Math.Log10(s / k.Pc) : double.NegativeInfinity;
        }
        return new PhaseNoise(k.Fc, k.Pc, offsets.ToArray(), l);
    }

    private static IntegratedPhaseNoise Integrate(PnCarrier k, double fLo, double fHi)
    {
        k.CheckReach(fHi, "the band");
        double sum = 0;
        for (int i = 0; i < k.D.Psd.Length; i++)
        {
            double off = Math.Abs(k.D.Frequencies[i] - k.Fc);
            if (off < fLo || off > fHi)
                continue;
            if (Math.Abs(i - k.C) <= k.W)
                throw new ArgumentException("the band reaches into the carrier group", nameof(fLo));
            sum += k.D.Psd[i];
        }
        double ratio = sum * k.D.BinWidth / k.Pc;
        double rms = Math.Sqrt(ratio);
        double jitter = k.Fc != 0 ? rms / (2 * Math.PI * Math.Abs(k.Fc)) : rms > 0 ? double.PositiveInfinity : 0;
        return new IntegratedPhaseNoise(k.Fc, k.Pc, fLo, fHi, ratio > 0 ? 10 * Math.Log10(ratio) : double.NegativeInfinity, rms, jitter);
    }

    private static void CheckTones(int samples, int? width, double f1, double f2)
    {
        Check(samples, width, f1);
        if (!double.IsFinite(f2))
            throw new ArgumentException("f2 must be finite", nameof(f2));
        if (!(f1 < f2))
            throw new ArgumentException("f1 must be below f2", nameof(f1));
    }

    private static TwoToneImd Imd(ToneGroups g, double f1, double f2)
    {
        double fs = g.D.SampleRate;
        if (!(Math.Abs(f2) <= fs / 2 && (f2 >= 0 || !g.D.OneSided)))
            throw new ArgumentException("f2 must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)", nameof(f2));
        int c = g.Nearest(g.Alias(f2));
        if (g.Claimed[c])
            throw new ArgumentException("f2 falls in the DC group or the f1 group", nameof(f2));
        var idx = g.Group(c);
        double p2 = g.Power(idx);
        if (!(p2 > 0))
            throw new ArgumentException("no signal power at f2", nameof(f2));
        double[] imdF = [g.Alias(2 * f1 - f2), g.Alias(2 * f2 - f1)];
        var imdP = new double[2];
        for (int i = 0; i < 2; i++)
        {
            int k = g.Nearest(imdF[i]);
            if (g.Claimed[k])
                throw new ArgumentException("an intermodulation product falls on DC, a tone or the other product", nameof(f2));
            imdP[i] = g.Power(g.Group(k));
        }
        double pt = (g.Signal + p2) / 2;
        double[] dbc = [.. imdP.Select(p => p > 0 ? 10 * Math.Log10(p / pt) : double.NegativeInfinity)];
        double worst = Math.Max(dbc[0], dbc[1]);
        return new TwoToneImd([g.F1, g.Centroid(idx, p2)], [g.Signal, p2], imdF, imdP, dbc, worst, 10 * Math.Log10(pt) - worst / 2);
    }

    private static void Check(int samples, int? width, double? fundamental)
    {
        if (samples < 2)
            throw new ArgumentException("tone metrics need at least two samples", nameof(samples));
        if (width is < 0)
            throw new ArgumentOutOfRangeException(nameof(width), "width must be non-negative");
        if (fundamental is { } f && !double.IsFinite(f))
            throw new ArgumentException("fundamental must be finite", nameof(fundamental));
    }

    private static ToneMetrics Tone(ToneGroups g, int numHarmonics)
    {
        double fs = g.D.SampleRate;
        double harmonic = 0;
        for (int h = 2; h <= numHarmonics + 1; h++)
        {
            double x;
            if (g.D.OneSided)
            {
                x = FlooredMod(h * g.F1, fs);
                if (x > fs / 2)
                    x = fs - x;
            }
            else
            {
                x = FlooredMod(h * g.F1 + fs / 2, fs) - fs / 2;
            }
            harmonic += g.Power(g.Group(g.Nearest(x)));
        }
        double noise = 0;
        for (int k = 0; k < g.P.Length; k++)
            if (!g.Claimed[k])
                noise += g.P[k];
        double sinad = Db(g.Signal, noise + harmonic);
        return new ToneMetrics(g.F1, g.Signal, harmonic, noise, g.Power(g.Dc), Db(g.Signal, noise), sinad,
            -Db(g.Signal, harmonic), (sinad - 10 * Math.Log10(1.5)) / (20 * Math.Log10(2)));
    }

    private static Sfdr Spurs(ToneGroups g, int numSpurs)
    {
        var freqs = new List<double>();
        var powers = new List<double>();
        while (powers.Count < numSpurs)
        {
            int c = g.Strongest();
            if (c < 0 || !(g.P[c] > 0))
                break;
            var idx = g.Group(c);
            double power = g.Power(idx);
            freqs.Add(g.Centroid(idx, power));
            powers.Add(power);
        }
        double[] dbc = [.. powers.Select(v => 10 * Math.Log10(v / g.Signal))];
        return new Sfdr(g.F1, g.Signal, dbc.Length > 0 ? -dbc[0] : double.PositiveInfinity,
            [.. freqs], [.. powers], dbc);
    }

    /// <summary>
    /// One windowed spectrum's bins, claimed group by group: DC, then the fundamental (conventions:
    /// Tone metrics). Later groups are claimed by the caller.
    /// </summary>
    private sealed class ToneGroups
    {
        /// <summary>Bins at or below this fraction of the total power are rounding error: zero.</summary>
        private const double Floor = 1e-20;

        private readonly int _w;

        public ToneGroups(SpectralDensity d, WindowType window, double? beta, int? width, double? fundamental)
        {
            double fs = d.SampleRate;
            if (fundamental is { } given && !(Math.Abs(given) <= fs / 2 && (given >= 0 || !d.OneSided)))
                throw new ArgumentException("fundamental must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)", nameof(fundamental));
            if (fundamental is { } f && !d.OneSided)
                fundamental = FlooredMod(f + fs / 2, fs) - fs / 2; // +fs/2 is the bin at −fs/2
            D = d;
            P = new double[d.Psd.Length];
            _w = Math.Min(width ?? HalfWidth(window, beta), P.Length); // wider changes nothing
            double total = 0;
            for (int k = 0; k < P.Length; k++)
            {
                P[k] = d.Psd[k] * d.BinWidth;
                total += P[k];
            }
            if (!double.IsFinite(total))
                throw new ArgumentException("samples must be finite and small enough for a finite spectrum", nameof(d));
            for (int k = 0; k < P.Length; k++)
                if (P[k] <= Floor * total)
                    P[k] = 0; // rounding error
            Claimed = new bool[P.Length];
            Dc = Group(Nearest(0.0));
            int c;
            if (fundamental is { } at)
            {
                c = Nearest(at);
                if (Claimed[c])
                    throw new ArgumentException("the fundamental falls in the DC group", nameof(fundamental));
            }
            else
            {
                c = Strongest();
                if (c < 0)
                    throw new ArgumentException("no bins are left for the fundamental after the DC group", nameof(width));
            }
            var fund = Group(c);
            Signal = Power(fund);
            if (!(Signal > 0))
                throw new ArgumentException("no signal power at the fundamental", nameof(fundamental));
            F1 = Centroid(fund, Signal);
        }

        public SpectralDensity D { get; }

        /// <summary>Bin powers, PSD · bin width.</summary>
        public double[] P { get; }

        public bool[] Claimed { get; }

        public List<int> Dc { get; }

        public double Signal { get; }

        public double F1 { get; }

        /// <summary><paramref name="freq"/> in the spectrum's range: folded for real input, wrapped for complex.</summary>
        public double Alias(double freq)
        {
            double fs = D.SampleRate;
            if (D.OneSided)
            {
                double x = FlooredMod(freq, fs);
                return x > fs / 2 ? fs - x : x;
            }
            return FlooredMod(freq + fs / 2, fs) - fs / 2;
        }

        /// <summary>Index of the bin nearest <paramref name="freq"/>, clipped to the spectrum.</summary>
        public int Nearest(double freq) =>
            (int)Math.Clamp(Math.Floor((freq - D.Frequencies[0]) / D.BinWidth + 0.5), 0, P.Length - 1);

        /// <summary>The first unclaimed bin with the largest power, or −1 when none is left.</summary>
        public int Strongest()
        {
            int c = -1;
            for (int k = 0; k < P.Length; k++)
                if (!Claimed[k] && (c < 0 || P[k] > P[c]))
                    c = k;
            return c;
        }

        /// <summary>Claims and returns the unclaimed bins within the half-width of bin <paramref name="c"/>.</summary>
        public List<int> Group(int c)
        {
            var idx = new List<int>();
            for (int k = Math.Max(c - _w, 0); k <= Math.Min(c + _w, P.Length - 1); k++)
            {
                if (!Claimed[k])
                {
                    Claimed[k] = true;
                    idx.Add(k);
                }
            }
            return idx;
        }

        public double Power(List<int> idx)
        {
            double s = 0;
            foreach (int k in idx)
                s += P[k];
            return s;
        }

        public double Centroid(List<int> idx, double power)
        {
            double moment = 0;
            foreach (int k in idx)
                moment += P[k] * D.Frequencies[k];
            return moment / power;
        }
    }

    private static int HalfWidth(WindowType window, double? beta)
    {
        int terms = Spectral.CosineTerms(window);
        if (terms > 0)
            return terms;
        double b = beta ?? throw new ArgumentException("the kaiser window needs beta", nameof(beta));
        return (int)Math.Ceiling(Math.Sqrt(1 + (b / Math.PI) * (b / Math.PI)));
    }

    /// <summary>x mod y with the sign of y, as Python's float %.</summary>
    private static double FlooredMod(double x, double y)
    {
        double r = x % y;
        return r != 0 && (r < 0) != (y < 0) ? r + y : r;
    }

    /// <summary>10·log10(num / den) for num &gt; 0; +∞ when den is zero.</summary>
    private static double Db(double num, double den) => den == 0 ? double.PositiveInfinity : 10 * Math.Log10(num / den);
}
