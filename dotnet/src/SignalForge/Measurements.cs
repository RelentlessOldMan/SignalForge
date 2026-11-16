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
