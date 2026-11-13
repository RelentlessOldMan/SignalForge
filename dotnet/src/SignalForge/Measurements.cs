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
        Check(samples.Length, width, numHarmonics, fundamental);
        return Tone(Spectral.WelchPsd(samples, sampleRate, window: window, beta: beta), window, beta, width, numHarmonics, fundamental);
    }

    /// <summary>
    /// SNR, SINAD, THD and ENOB of the strongest tone in complex samples (or the one at
    /// <paramref name="fundamental"/>), from a two-sided spectrum; otherwise as for real samples.
    /// </summary>
    public static ToneMetrics ToneMetrics(ReadOnlySpan<Complex> samples, double sampleRate,
        WindowType window = WindowType.BlackmanHarris, double? beta = null, int? width = null,
        int numHarmonics = 5, double? fundamental = null)
    {
        Check(samples.Length, width, numHarmonics, fundamental);
        return Tone(Spectral.WelchPsd(samples, sampleRate, window: window, beta: beta), window, beta, width, numHarmonics, fundamental);
    }

    private static void Check(int samples, int? width, int numHarmonics, double? fundamental)
    {
        if (samples < 2)
            throw new ArgumentException("tone metrics need at least two samples", nameof(samples));
        ArgumentOutOfRangeException.ThrowIfNegative(numHarmonics);
        if (width is < 0)
            throw new ArgumentOutOfRangeException(nameof(width), "width must be non-negative");
        if (fundamental is { } f && !double.IsFinite(f))
            throw new ArgumentException("fundamental must be finite", nameof(fundamental));
    }

    private static ToneMetrics Tone(SpectralDensity d, WindowType window, double? beta, int? width,
        int numHarmonics, double? fundamental)
    {
        double fs = d.SampleRate;
        if (fundamental is { } given && !(Math.Abs(given) <= fs / 2 && (given >= 0 || !d.OneSided)))
            throw new ArgumentException("fundamental must satisfy |f| <= sample_rate/2 (and f >= 0 for real input)", nameof(fundamental));
        int w = width ?? HalfWidth(window, beta);
        int m = d.Psd.Length;
        var p = new double[m];
        for (int k = 0; k < m; k++)
            p[k] = d.Psd[k] * d.BinWidth;
        double[] f = d.Frequencies;
        var claimed = new bool[m];

        int Nearest(double freq) => (int)Math.Clamp(Math.Floor((freq - f[0]) / d.BinWidth + 0.5), 0, m - 1);

        List<int> Group(int c)
        {
            var idx = new List<int>();
            for (int k = Math.Max(c - w, 0); k <= Math.Min(c + w, m - 1); k++)
            {
                if (!claimed[k])
                {
                    claimed[k] = true;
                    idx.Add(k);
                }
            }
            return idx;
        }

        double Sum(List<int> idx)
        {
            double s = 0;
            foreach (int k in idx)
                s += p[k];
            return s;
        }

        var dc = Group(Nearest(0.0));
        int center;
        if (fundamental is { } at)
        {
            center = Nearest(at);
            if (claimed[center])
                throw new ArgumentException("the fundamental falls in the DC group", nameof(fundamental));
        }
        else
        {
            center = -1;
            for (int k = 0; k < m; k++)
                if (!claimed[k] && (center < 0 || p[k] > p[center]))
                    center = k;
            if (center < 0)
                throw new ArgumentException("no bins are left for the fundamental after the DC group", nameof(width));
        }
        var fund = Group(center);
        double signal = Sum(fund);
        if (!(signal > 0))
            throw new ArgumentException("no signal power at the fundamental", nameof(fundamental));
        double moment = 0;
        foreach (int k in fund)
            moment += p[k] * f[k];
        double f1 = moment / signal;
        double harmonic = 0;
        for (int h = 2; h <= numHarmonics + 1; h++)
        {
            double g;
            if (d.OneSided)
            {
                g = FlooredMod(h * f1, fs);
                if (g > fs / 2)
                    g = fs - g;
            }
            else
            {
                g = FlooredMod(h * f1 + fs / 2, fs) - fs / 2;
            }
            harmonic += Sum(Group(Nearest(g)));
        }
        double noise = 0;
        for (int k = 0; k < m; k++)
            if (!claimed[k])
                noise += p[k];
        double sinad = Db(signal, noise + harmonic);
        return new ToneMetrics(f1, signal, harmonic, noise, Sum(dc), Db(signal, noise), sinad,
            -Db(signal, harmonic), (sinad - 10 * Math.Log10(1.5)) / (20 * Math.Log10(2)));
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
