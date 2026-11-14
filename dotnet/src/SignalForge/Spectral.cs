using System.Numerics;

namespace SignalForge;

/// <summary>What each Welch segment loses before the window (conventions: Spectra, PSD).</summary>
public enum Detrend
{
    /// <summary>The segment as it is.</summary>
    None,

    /// <summary>The segment minus its mean.</summary>
    Constant,

    /// <summary>The segment minus its least-squares line.</summary>
    Linear,
}

/// <summary>How Welch's segment powers are combined per bin (conventions: Spectra, PSD).</summary>
public enum WelchAverage
{
    /// <summary>The mean over segments.</summary>
    Mean,

    /// <summary>The median over segments divided by its expected value for exponential power.</summary>
    Median,
}

/// <summary>How <see cref="Spectral.LombScargle"/> scales its result (conventions: Spectra, Lomb-Scargle).</summary>
public enum LombScargleNormalization
{
    /// <summary><c>2P / Σy²</c>: the fraction of the data's sum of squares the sinusoid explains, 0 to 1.</summary>
    Standard,

    /// <summary>Scargle's <c>P</c>, in value units squared.</summary>
    Power,
}

/// <summary>Named windows. Formulas in docs/conventions.md (Spectra).</summary>
public enum WindowType
{
    /// <summary>All ones.</summary>
    Rectangular,

    /// <summary>Cosine sum 0.5, 0.5.</summary>
    Hann,

    /// <summary>Cosine sum 0.54, 0.46.</summary>
    Hamming,

    /// <summary>Cosine sum 0.42, 0.5, 0.08.</summary>
    Blackman,

    /// <summary>Four-term Blackman-Harris: 0.35875, 0.48829, 0.14128, 0.01168.</summary>
    BlackmanHarris,

    /// <summary>Five-term flat-top: 0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368.</summary>
    Flattop,

    /// <summary>Kaiser window; needs a shape parameter β ≥ 0.</summary>
    Kaiser,
}

/// <summary>Coherent gain Σw/N and equivalent noise bandwidth in bins N·Σw²/(Σw)² of a window.</summary>
/// <param name="CoherentGain">Σw / N: the reading of a unit tone at a bin center.</param>
/// <param name="EnbwBins">N·Σw² / (Σw)²: the noise bandwidth in bins.</param>
public sealed record WindowStats(double CoherentGain, double EnbwBins);

/// <summary>A power spectral density in sample-units²/Hz; see docs/conventions.md (Spectra).</summary>
/// <param name="Frequencies">Bin frequencies in Hz, ascending.</param>
/// <param name="Psd">Density at each bin, in sample-units²/Hz.</param>
/// <param name="SampleRate">Sample rate in Hz.</param>
/// <param name="Nperseg">Segment length.</param>
/// <param name="NumSegments">Number of segments averaged.</param>
/// <param name="OneSided">True for a one-sided PSD of real input.</param>
/// <param name="BinWidth">fs / nfft, the bin spacing in Hz.</param>
/// <param name="EnbwHz">The window's equivalent noise bandwidth in Hz (resolution bandwidth).</param>
/// <param name="Nfft">Transform length: nperseg plus the zero padding.</param>
public sealed record SpectralDensity(
    double[] Frequencies,
    double[] Psd,
    double SampleRate,
    int Nperseg,
    int NumSegments,
    bool OneSided,
    double BinWidth,
    double EnbwHz,
    int Nfft)
{
    /// <summary>
    /// (0, fs/2) for a one-sided PSD, whose DC and Nyquist bins are half bins; null for two-sided. Pass
    /// it to <see cref="Spectral.OccupiedBandwidth"/> and <see cref="Spectral.ChannelPower"/>.
    /// </summary>
    public (double Low, double High)? Span => OneSided ? (0.0, SampleRate / 2) : null;
}

/// <summary>
/// A spectrogram: Welch's segments kept, one PSD row per segment, in sample-units²/Hz
/// (conventions: Spectra, Spectrogram).
/// </summary>
/// <param name="Frequencies">Bin frequencies in Hz, as for <see cref="SpectralDensity"/>.</param>
/// <param name="Times">Each segment's center, in seconds from the first sample.</param>
/// <param name="Psd">One row per segment, each <c>Frequencies.Length</c> bins.</param>
/// <param name="SampleRate">Sample rate in Hz.</param>
/// <param name="Nperseg">Segment length.</param>
/// <param name="NumSegments">Number of segments (rows).</param>
/// <param name="OneSided">True for one-sided rows of real input.</param>
/// <param name="BinWidth">fs / nfft, the bin spacing in Hz.</param>
/// <param name="EnbwHz">The window's equivalent noise bandwidth in Hz (resolution bandwidth).</param>
/// <param name="Nfft">Transform length: nperseg plus the zero padding.</param>
public sealed record Spectrogram(
    double[] Frequencies,
    double[] Times,
    double[][] Psd,
    double SampleRate,
    int Nperseg,
    int NumSegments,
    bool OneSided,
    double BinWidth,
    double EnbwHz,
    int Nfft)
{
    /// <summary>(0, fs/2) for one-sided rows, whose DC and Nyquist bins are half bins; null for two-sided.</summary>
    public (double Low, double High)? Span => OneSided ? (0.0, SampleRate / 2) : null;
}

/// <summary>Occupied bandwidth by the β/2 method, in the PSD's frequency axis.</summary>
/// <param name="Bandwidth">Upper minus lower, in Hz.</param>
/// <param name="Lower">Lower band edge in Hz.</param>
/// <param name="Upper">Upper band edge in Hz.</param>
/// <param name="TotalPower">Total power of the PSD, in sample-units².</param>
/// <param name="Fraction">Fraction of the power inside the band.</param>
public sealed record OccupiedBandwidth(double Bandwidth, double Lower, double Upper, double TotalPower, double Fraction);

/// <summary>Adjacent channel power ratio: power in each adjacent channel relative to the main one.</summary>
/// <param name="MainPower">Power in the main channel, in the PSD's power units.</param>
/// <param name="LowerPower">Power in the lower channel at each offset, in the order given.</param>
/// <param name="UpperPower">Power in the upper channel at each offset.</param>
/// <param name="LowerDbc">10·log10(lower / main) per offset; −∞ for an empty channel.</param>
/// <param name="UpperDbc">10·log10(upper / main) per offset; −∞ for an empty channel.</param>
public sealed record Acpr(double MainPower, double[] LowerPower, double[] UpperPower, double[] LowerDbc, double[] UpperDbc);

/// <summary>
/// FFT, frequency axes, windows, Welch PSD, occupied bandwidth and channel power. Definitions in
/// docs/conventions.md (Spectra) and docs/adr/0006-fft-windows-spectra.md.
/// </summary>
public static class Spectral
{
    /// <summary>Largest Kaiser β: I₀(β) overflows a double just above 713.</summary>
    public const double KaiserMaxBeta = 700.0;

    private static readonly Dictionary<WindowType, double[]> CosineSums = new()
    {
        [WindowType.Rectangular] = [1.0],
        [WindowType.Hann] = [0.5, 0.5],
        [WindowType.Hamming] = [0.54, 0.46],
        [WindowType.Blackman] = [0.42, 0.5, 0.08],
        [WindowType.BlackmanHarris] = [0.35875, 0.48829, 0.14128, 0.01168],
        [WindowType.Flattop] = [0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368],
    };

    /// <summary>Number of terms of a cosine-sum window; 0 for Kaiser.</summary>
    internal static int CosineTerms(WindowType type) => CosineSums.TryGetValue(type, out var a) ? a.Length : 0;

    /// <summary>Forward DFT, unnormalized: X[k] = Σ x[n]·e^{−j2πkn/N}. Any length N ≥ 1.</summary>
    public static Complex[] Fft(ReadOnlySpan<Complex> samples)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("fft needs at least one sample", nameof(samples));
        var x = samples.ToArray();
        Transform(x);
        return x;
    }

    /// <summary>Forward DFT of real samples; see <see cref="Fft(ReadOnlySpan{Complex})"/>.</summary>
    public static Complex[] Fft(ReadOnlySpan<double> samples) => Fft(ToComplex(samples));

    /// <summary>Inverse DFT, scaled by 1/N. Any length N ≥ 1.</summary>
    public static Complex[] Ifft(ReadOnlySpan<Complex> spectrum)
    {
        if (spectrum.IsEmpty)
            throw new ArgumentException("ifft needs at least one bin", nameof(spectrum));
        var x = new Complex[spectrum.Length];
        for (int i = 0; i < x.Length; i++)
            x[i] = Complex.Conjugate(spectrum[i]);
        Transform(x);
        double scale = 1.0 / x.Length;
        for (int i = 0; i < x.Length; i++)
            x[i] = Complex.Conjugate(x[i]) * scale;
        return x;
    }

    /// <summary>
    /// Bin frequencies of an n-point FFT: unshifted (NumPy fftfreq order) or shifted (fftshift order,
    /// ascending from −fs/2).
    /// </summary>
    public static double[] FftFrequencies(int n, double sampleRate, bool shifted = false)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(n);
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        var f = new double[n];
        double df = sampleRate / n;
        for (int i = 0; i < n; i++)
        {
            int k = shifted ? i - n / 2 : (i <= (n - 1) / 2 ? i : i - n);
            f[i] = k * df;
        }
        return f;
    }

    /// <summary>
    /// A window of length <paramref name="n"/>, periodic unless <paramref name="symmetric"/>.
    /// <paramref name="beta"/> is required for <see cref="WindowType.Kaiser"/> and not allowed otherwise.
    /// </summary>
    public static double[] Window(WindowType type, int n, bool symmetric = false, double? beta = null)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(n);
        if (type == WindowType.Kaiser)
        {
            if (beta is not (>= 0 and <= KaiserMaxBeta))
                throw new ArgumentException($"kaiser needs 0 <= beta <= {KaiserMaxBeta}", nameof(beta));
        }
        else if (!CosineSums.ContainsKey(type))
            throw new ArgumentException($"unknown window {type}", nameof(type));
        else if (beta is not null)
            throw new ArgumentException("beta applies to the kaiser window only", nameof(beta));
        if (n <= 1)
            return n == 0 ? [] : [1.0];

        var w = new double[n];
        double d = symmetric ? n - 1 : n;
        if (type == WindowType.Kaiser)
        {
            double b = beta!.Value, norm = BesselI0(b);
            for (int i = 0; i < n; i++)
            {
                double r = 2.0 * i / d - 1.0;
                w[i] = BesselI0(b * Math.Sqrt(Math.Max(1.0 - r * r, 0.0))) / norm;
            }
            return w;
        }
        double[] a = CosineSums[type];
        for (int k = 0; k < a.Length; k++)
        {
            double sign = k % 2 == 0 ? 1.0 : -1.0;
            for (int i = 0; i < n; i++)
                w[i] += sign * a[k] * Math.Cos(2.0 * Math.PI * k * i / d);
        }
        return w;
    }

    /// <summary>Coherent gain and ENBW (in bins) of a window. The window must not sum to zero.</summary>
    public static WindowStats WindowStats(ReadOnlySpan<double> window)
    {
        if (window.IsEmpty)
            throw new ArgumentException("window must not be empty", nameof(window));
        double s = 0, s2 = 0;
        foreach (double v in window)
        {
            s += v;
            s2 += v * v;
        }
        if (s == 0)
            throw new ArgumentException("window sums to zero", nameof(window));
        int n = window.Length;
        return new WindowStats(s / n, n * s2 / (s * s));
    }

    /// <summary>
    /// Welch PSD of complex samples: two-sided, in shifted (ascending) order. Segment length defaults
    /// to the whole input, overlap to half a segment. <paramref name="beta"/> is the Kaiser β;
    /// <paramref name="detrend"/> acts on each segment, <paramref name="average"/> combines them.
    /// </summary>
    public static SpectralDensity WelchPsd(ReadOnlySpan<Complex> samples, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, WelchAverage average = WelchAverage.Mean, int? nfft = null) =>
        Welch(samples, sampleRate, nperseg, noverlap, window, beta, oneSided: false, detrend, average, nfft);

    /// <summary>
    /// Welch PSD of real samples: one-sided (bins 0 … ⌊N/2⌋, all but DC and Nyquist doubled) unless
    /// <paramref name="oneSided"/> is false, which gives the two-sided shifted PSD.
    /// <paramref name="beta"/> is the Kaiser β; <paramref name="detrend"/> acts on each segment,
    /// <paramref name="average"/> combines them.
    /// </summary>
    public static SpectralDensity WelchPsd(ReadOnlySpan<double> samples, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, bool oneSided = true,
        double? beta = null, Detrend detrend = Detrend.None, WelchAverage average = WelchAverage.Mean,
        int? nfft = null) =>
        Welch(ToComplex(samples), sampleRate, nperseg, noverlap, window, beta, oneSided, detrend, average, nfft);

    private static SpectralDensity Welch(ReadOnlySpan<Complex> x, double sampleRate, int? nperseg,
        int? noverlap, WindowType window, double? beta, bool oneSided, Detrend detrend, WelchAverage average,
        int? nfft)
    {
        if (average is not (WelchAverage.Mean or WelchAverage.Median))
            throw new ArgumentException($"unknown average {average}", nameof(average));
        var g = Prepare(x, sampleRate, nperseg, noverlap, window, beta, detrend, nfft);
        var buf = new Complex[g.Nfft];
        var acc = new double[g.Nfft];
        double scale = g.Scale / g.Count;
        if (average == WelchAverage.Mean)
        {
            for (int s = 0; s < g.Count; s++)
                g.AddPower(x, s, buf, acc);
        }
        else
        {
            var rows = new double[g.Count][];
            for (int s = 0; s < g.Count; s++)
                g.AddPower(x, s, buf, rows[s] = new double[g.Nfft]);
            var col = new double[g.Count];
            int mid = g.Count / 2;
            for (int k = 0; k < g.Nfft; k++)
            {
                for (int s = 0; s < g.Count; s++)
                    col[s] = rows[s][k];
                Array.Sort(col);
                acc[k] = g.Count % 2 == 1 ? col[mid] : (col[mid - 1] + col[mid]) / 2;
            }
            scale = g.Scale / MedianBias(g.Count);
        }
        return new SpectralDensity(g.Frequencies(oneSided), g.Fold(acc, scale, oneSided), sampleRate,
            g.N, g.Count, oneSided, sampleRate / g.Nfft, WindowStats(g.W).EnbwBins * sampleRate / g.N, g.Nfft);
    }

    /// <summary>
    /// Spectrogram of complex samples: Welch's segments kept one per row, each a two-sided shifted
    /// PSD (conventions: Spectra, Spectrogram). <paramref name="beta"/> is the Kaiser β.
    /// </summary>
    public static Spectrogram Spectrogram(ReadOnlySpan<Complex> samples, double sampleRate, int nperseg,
        int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        Frames(samples, sampleRate, nperseg, noverlap, window, beta, oneSided: false, detrend, nfft);

    /// <summary>
    /// Spectrogram of real samples: one-sided rows unless <paramref name="oneSided"/> is false, which
    /// gives two-sided shifted rows. <paramref name="beta"/> is the Kaiser β.
    /// </summary>
    public static Spectrogram Spectrogram(ReadOnlySpan<double> samples, double sampleRate, int nperseg,
        int? noverlap = null, WindowType window = WindowType.Hann, bool oneSided = true, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        Frames(ToComplex(samples), sampleRate, nperseg, noverlap, window, beta, oneSided, detrend, nfft);

    private static Spectrogram Frames(ReadOnlySpan<Complex> x, double sampleRate, int nperseg,
        int? noverlap, WindowType window, double? beta, bool oneSided, Detrend detrend, int? nfft)
    {
        var g = Prepare(x, sampleRate, nperseg, noverlap, window, beta, detrend, nfft);
        var rows = new double[g.Count][];
        var times = new double[g.Count];
        var buf = new Complex[g.Nfft];
        for (int s = 0; s < g.Count; s++)
        {
            var p = new double[g.Nfft];
            g.AddPower(x, s, buf, p);
            rows[s] = g.Fold(p, g.Scale, oneSided);
            times[s] = (s * (double)g.Step + g.N / 2.0) / sampleRate;
        }
        return new Spectrogram(g.Frequencies(oneSided), times, rows, sampleRate, g.N, g.Count, oneSided,
            sampleRate / g.Nfft, WindowStats(g.W).EnbwBins * sampleRate / g.N, g.Nfft);
    }

    private static Segments Prepare(ReadOnlySpan<Complex> x, double sampleRate, int? nperseg, int? noverlap,
        WindowType window, double? beta, Detrend detrend, int? nfft)
    {
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (detrend is not (Detrend.None or Detrend.Constant or Detrend.Linear))
            throw new ArgumentException($"unknown detrend {detrend}", nameof(detrend));
        int n = nperseg ?? x.Length;
        if (n < 1)
            throw new ArgumentException("nperseg must be at least 1", nameof(nperseg));
        if (x.Length < n)
            throw new ArgumentException("fewer samples than nperseg", nameof(nperseg));
        int overlap = noverlap ?? n / 2;
        if (overlap < 0 || overlap >= n)
            throw new ArgumentException("noverlap must satisfy 0 <= noverlap < nperseg", nameof(noverlap));
        int step = n - overlap;
        int m = nfft ?? n;
        if (m < n)
            throw new ArgumentException("nfft must be at least nperseg", nameof(nfft));
        double[] w = Window(window, n, beta: beta);
        if (w.All(v => v == 0))
            throw new ArgumentException($"{window} window of length {n} is all zeros", nameof(window));
        return new Segments(n, step, (x.Length - n) / step + 1, w, sampleRate, 1.0 / (sampleRate * w.Sum(v => v * v)),
            detrend, m);
    }

    /// <summary>
    /// Lomb-Scargle periodogram of real <paramref name="values"/> taken at <paramref name="times"/>, one
    /// value per frequency (conventions: Spectra, Lomb-Scargle; ADR 0059).
    /// </summary>
    /// <param name="times">Sample times, finite, in any order; at least two.</param>
    /// <param name="values">Finite values, one per time.</param>
    /// <param name="frequencies">Trial frequencies in Hz, finite and positive; may be empty.</param>
    /// <param name="center">Subtract the mean of the values first.</param>
    /// <param name="normalization">Scargle's power or the standard <c>2P / Σy²</c>.</param>
    /// <returns>The periodogram at each frequency, in their order.</returns>
    public static double[] LombScargle(ReadOnlySpan<double> times, ReadOnlySpan<double> values, ReadOnlySpan<double> frequencies,
        bool center = true, LombScargleNormalization normalization = LombScargleNormalization.Standard)
    {
        int n = times.Length;
        if (values.Length != n || n < 2)
            throw new ArgumentException("times and values must have the same length, at least 2", nameof(values));
        foreach (double v in times)
            if (!double.IsFinite(v)) throw new ArgumentException("times must be finite", nameof(times));
        foreach (double v in values)
            if (!double.IsFinite(v)) throw new ArgumentException("values must be finite", nameof(values));
        foreach (double v in frequencies)
            if (!(double.IsFinite(v) && v > 0)) throw new ArgumentException("frequencies must be finite and positive", nameof(frequencies));
        if (normalization is not (LombScargleNormalization.Standard or LombScargleNormalization.Power))
            throw new ArgumentException($"unknown normalization {normalization}", nameof(normalization));
        double mean = 0;
        if (center)
        {
            foreach (double v in values) mean += v;
            mean /= n;
        }
        var y = new double[n];
        double total = 0;
        for (int i = 0; i < n; i++)
        {
            y[i] = values[i] - mean;
            total += y[i] * y[i];
        }
        if (normalization == LombScargleNormalization.Standard && !(total > 0))
            throw new ArgumentException("the standard normalization needs values that are not all equal", nameof(values));
        var out_ = new double[frequencies.Length];
        double small = 1e-12 * n;
        for (int k = 0; k < out_.Length; k++)
        {
            double w = 2 * Math.PI * frequencies[k];
            double s2 = 0, c2 = 0;
            foreach (double t in times)
            {
                s2 += Math.Sin(2 * w * t);
                c2 += Math.Cos(2 * w * t);
            }
            double tau = Math.Atan2(s2, c2) / (2 * w);
            double yc = 0, ys = 0, cc = 0, ss = 0;
            for (int i = 0; i < n; i++)
            {
                double c = Math.Cos(w * (times[i] - tau)), s = Math.Sin(w * (times[i] - tau));
                yc += y[i] * c;
                ys += y[i] * s;
                cc += c * c;
                ss += s * s;
            }
            double p = (cc >= small ? yc * yc / cc : 0) + (ss >= small ? ys * ys / ss : 0);
            out_[k] = normalization == LombScargleNormalization.Standard ? p / total : p / 2;
        }
        return out_;
    }

    /// <summary>Chance that white Gaussian noise gives a standard Lomb-Scargle value above <paramref name="power"/>
    /// at any of <paramref name="numFrequencies"/> independent frequencies (conventions: Spectra; ADR 0062).</summary>
    /// <param name="power">A value of the standard normalization, in [0, 1].</param>
    /// <param name="numSamples">The number of samples the periodogram was computed from.</param>
    /// <param name="numFrequencies">The number of independent frequencies searched, at least 1.</param>
    /// <param name="center">Whether the periodogram subtracted the mean, as <see cref="LombScargle"/>'s <c>center</c>.</param>
    /// <returns><c>1 − (1 − P₁)^M</c> with <c>P₁ = (1 − z)^((N − d)/2)</c>, <c>d</c> 3 centered and 2 not.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double LombScargleFalseAlarm(double power, int numSamples, int numFrequencies = 1, bool center = true)
    {
        int d = center ? 3 : 2;
        if (!(power >= 0 && power <= 1))
            throw new ArgumentOutOfRangeException(nameof(power), power, "must be between 0 and 1 (the standard normalization)");
        if (numSamples < d + 1)
            throw new ArgumentOutOfRangeException(nameof(numSamples), numSamples, $"must be at least {d + 1}");
        ArgumentOutOfRangeException.ThrowIfLessThan(numFrequencies, 1);
        double p1 = Math.Pow(1 - power, (numSamples - d) / 2.0);
        return p1 == 1 ? 1.0 : -ExpM1(numFrequencies * LogP1(-p1));
    }

    /// <summary>Frequency grid <c>k / (oversampling·T)</c>, <c>k = 1, 2, …</c> up to <paramref name="maxFrequency"/>,
    /// for <see cref="LombScargle"/> (conventions: Spectra; ADR 0062).</summary>
    /// <param name="times">The sample times, finite, at least 2 and not all equal; <c>T</c> is their span.</param>
    /// <param name="oversampling">Grid points per <c>1/T</c>, positive and finite.</param>
    /// <param name="maxFrequency">The highest frequency, positive and finite; null for <c>N/(2T)</c>.</param>
    /// <returns>The frequencies in Hz, ascending; empty when the first would be above the maximum.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the grid would exceed 10⁷ frequencies.</exception>
    public static double[] LombScargleFrequencies(ReadOnlySpan<double> times, double oversampling = 5.0, double? maxFrequency = null)
    {
        if (times.Length < 2)
            throw new ArgumentException("times must have at least 2 values", nameof(times));
        double lo = double.PositiveInfinity, hi = double.NegativeInfinity;
        foreach (double t in times)
        {
            if (!double.IsFinite(t)) throw new ArgumentException("times must be finite", nameof(times));
            lo = Math.Min(lo, t);
            hi = Math.Max(hi, t);
        }
        double span = hi - lo;
        if (!(span > 0))
            throw new ArgumentException("times must not all be equal", nameof(times));
        Check.PositiveFinite(oversampling, nameof(oversampling));
        double fmax = maxFrequency is { } m ? Check.PositiveFinite(m, nameof(maxFrequency)) : times.Length / (2 * span);
        double df = 1 / (oversampling * span);
        double ratio = fmax / df + 1e-9;
        if (!(ratio < 1e7 + 1))
            throw new ArgumentException("the grid would have more than 10^7 frequencies", nameof(oversampling));
        var out_ = new double[(int)Math.Floor(ratio)];
        for (int k = 0; k < out_.Length; k++)
            out_[k] = (k + 1) * df;
        return out_;
    }

    /// <summary>log(1 + x), accurate for small x (Kahan's form).</summary>
    private static double LogP1(double x)
    {
        double u = 1 + x;
        return u == 1 ? x : Math.Log(u) * x / (u - 1);
    }

    /// <summary>exp(x) − 1, accurate for small x (Kahan's form).</summary>
    private static double ExpM1(double x)
    {
        double u = Math.Exp(x);
        if (u == 1) return x;
        double um1 = u - 1;
        return um1 == -1 ? -1 : um1 * x / Math.Log(u);
    }

    /// <summary>The expected median of <paramref name="k"/> independent unit-mean exponential values
    /// (conventions: Spectra, PSD).</summary>
    private static double MedianBias(int k)
    {
        double b = 0;
        for (int i = k / 2 + 1; i <= k; i++)
            b += 1.0 / i;
        return k % 2 == 0 ? b + 1.0 / k : b;
    }

    /// <summary>Welch's segmentation: length, step, count, window, the scale 1/(fs·Σw²), detrending.</summary>
    private sealed record Segments(int N, int Step, int Count, double[] W, double SampleRate, double Scale,
        Detrend Detrend, int Nfft)
    {
        /// <summary>Adds |FFT(w·detrended segment s)|², unscaled and in FFT order, to <paramref name="acc"/>.</summary>
        public void AddPower(ReadOnlySpan<Complex> x, int s, Complex[] buf, double[] acc)
        {
            var seg = x.Slice(s * Step, N);
            Complex mean = Complex.Zero, slope = Complex.Zero;
            double c = (N - 1) / 2.0;
            if (Detrend != Detrend.None)
            {
                for (int i = 0; i < N; i++)
                    mean += seg[i];
                mean /= N;
            }
            if (Detrend == Detrend.Linear && N > 1)
            {
                double tt = 0;
                for (int i = 0; i < N; i++)
                {
                    slope += (i - c) * seg[i];
                    tt += (i - c) * (i - c);
                }
                slope /= tt;
            }
            for (int i = 0; i < N; i++)
                buf[i] = (seg[i] - mean - slope * (i - c)) * W[i];
            Array.Clear(buf, N, Nfft - N);
            Transform(buf);
            for (int i = 0; i < Nfft; i++)
                acc[i] += buf[i].Real * buf[i].Real + buf[i].Imaginary * buf[i].Imaginary;
        }

        /// <summary>FFT-order power times <paramref name="scale"/>, as one-sided (doubled) or shifted bins.</summary>
        public double[] Fold(double[] p, double scale, bool oneSided)
        {
            if (oneSided)
            {
                int m = Nfft / 2 + 1, last = Nfft % 2 == 0 ? m - 1 : m;
                var one = new double[m];
                for (int k = 0; k < m; k++)
                    one[k] = p[k] * scale * (k >= 1 && k < last ? 2.0 : 1.0);
                return one;
            }
            var two = new double[Nfft];
            for (int i = 0; i < Nfft; i++)
                two[i] = p[(i + (Nfft + 1) / 2) % Nfft] * scale; // fftshift: index i holds bin i − ⌊n/2⌋
            return two;
        }

        public double[] Frequencies(bool oneSided) => oneSided
            ? [.. Enumerable.Range(0, Nfft / 2 + 1).Select(k => k * (SampleRate / Nfft))]
            : FftFrequencies(Nfft, SampleRate, shifted: true);
    }

    /// <summary>
    /// Occupied bandwidth by the ITU-R SM.328 β/2 method: the band with (1 − fraction)/2 of the power
    /// left out on each side. Bins are rectangles of the bin spacing, clipped to
    /// <paramref name="span"/> if given (for a one-sided PSD pass <see cref="SpectralDensity.Span"/>);
    /// edges interpolate within a bin.
    /// </summary>
    public static OccupiedBandwidth OccupiedBandwidth(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        double fraction = 0.99, (double Low, double High)? span = null)
    {
        if (!(fraction > 0 && fraction <= 1))
            throw new ArgumentException("fraction must be in (0, 1]", nameof(fraction));
        var (power, left, right) = Bins(frequencies, psd, span);
        int n = power.Length;
        var cum = new double[n + 1]; // cum[k] = power before bin k
        for (int k = 0; k < n; k++)
            cum[k + 1] = cum[k] + power[k];
        double total = cum[n];
        if (!(total > 0))
            throw new ArgumentException("total power must be positive", nameof(psd));
        double loTarget = (1 - fraction) / 2 * total, hiTarget = (1 + fraction) / 2 * total;

        int kLo = 0;
        while (!(cum[kLo + 1] > loTarget))
            kLo++;
        int kHi = n - 1;
        while (!(cum[kHi] < hiTarget))
            kHi--;
        double lower = left[kLo] + (loTarget - cum[kLo]) / power[kLo] * (right[kLo] - left[kLo]);
        double upper = left[kHi] + (hiTarget - cum[kHi]) / power[kHi] * (right[kHi] - left[kHi]);
        return new OccupiedBandwidth(upper - lower, lower, upper, total, fraction);
    }

    /// <summary>
    /// The PSD integrated over [low, high]; bins count by the part of their width inside. Bins are
    /// clipped to <paramref name="span"/> as for <see cref="OccupiedBandwidth"/>.
    /// </summary>
    public static double ChannelPower(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double low, double high,
        (double Low, double High)? span = null)
    {
        if (!(double.IsFinite(low) && double.IsFinite(high) && low < high))
            throw new ArgumentException("need finite low < high", nameof(low));
        var (power, left, right) = Bins(frequencies, psd, span);
        double sum = 0;
        for (int k = 0; k < power.Length; k++)
        {
            double overlap = Math.Max(Math.Min(right[k], high) - Math.Max(left[k], low), 0.0);
            sum += power[k] * overlap / (right[k] - left[k]);
        }
        return sum;
    }

    /// <summary>
    /// Power in the main channel and in the lower and upper channels at each center-to-center
    /// offset, by the <see cref="ChannelPower"/> rule (conventions: Spectra, ACPR).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="center">Main channel center in Hz.</param>
    /// <param name="bandwidth">Main channel width in Hz, positive.</param>
    /// <param name="offsets">Center-to-center offsets in Hz, at least one, each positive.</param>
    /// <param name="adjacentBandwidth">Adjacent channel width in Hz; default <paramref name="bandwidth"/>.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <exception cref="ArgumentException">A channel leaves the spectrum, or the main channel has no power.</exception>
    public static Acpr Acpr(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double center, double bandwidth,
        ReadOnlySpan<double> offsets, double? adjacentBandwidth = null, (double Low, double High)? span = null)
    {
        Check.Finite(center, nameof(center));
        double b = Check.PositiveFinite(bandwidth, nameof(bandwidth));
        double ba = adjacentBandwidth is { } a ? Check.PositiveFinite(a, nameof(adjacentBandwidth)) : b;
        if (offsets.IsEmpty)
            throw new ArgumentException("at least one offset required", nameof(offsets));
        foreach (double o in offsets)
            Check.PositiveFinite(o, nameof(offsets));
        var (power, left, right) = Bins(frequencies, psd, span);
        double slack = 0; // rounding in center ± offset ± width/2
        for (int k = 0; k < power.Length; k++)
            slack = Math.Max(slack, 1e-9 * (right[k] - left[k]));

        double Channel(double low, double high, string param)
        {
            if (low < left[0] - slack || high > right[^1] + slack)
                throw new ArgumentException($"channel [{low}, {high}] leaves the spectrum [{left[0]}, {right[^1]}]", param);
            double sum = 0;
            for (int k = 0; k < power.Length; k++)
                sum += power[k] * Math.Max(Math.Min(right[k], high) - Math.Max(left[k], low), 0.0) / (right[k] - left[k]);
            return sum;
        }

        double main = Channel(center - b / 2, center + b / 2, nameof(center));
        if (!(main > 0))
            throw new ArgumentException("the main channel has no power", nameof(psd));
        int n = offsets.Length;
        double[] lower = new double[n], upper = new double[n], lowerDbc = new double[n], upperDbc = new double[n];
        for (int i = 0; i < n; i++)
        {
            lower[i] = Channel(center - offsets[i] - ba / 2, center - offsets[i] + ba / 2, nameof(offsets));
            upper[i] = Channel(center + offsets[i] - ba / 2, center + offsets[i] + ba / 2, nameof(offsets));
            lowerDbc[i] = 10 * (Math.Log10(lower[i]) - Math.Log10(main)); // the ratio itself could underflow
            upperDbc[i] = 10 * (Math.Log10(upper[i]) - Math.Log10(main));
        }
        return new Acpr(main, lower, upper, lowerDbc, upperDbc);
    }

    /// <summary>Validates a PSD's bins; returns each bin's power PSD·Δ and its edges, clipped to the span.</summary>
    private static (double[] Power, double[] Left, double[] Right) Bins(ReadOnlySpan<double> f, ReadOnlySpan<double> psd,
        (double Low, double High)? span)
    {
        if (f.Length != psd.Length)
            throw new ArgumentException("frequencies and psd must have the same length", nameof(psd));
        if (f.Length < 2)
            throw new ArgumentException("need at least two bins", nameof(f));
        foreach (double v in f)
            if (!double.IsFinite(v))
                throw new ArgumentException("frequencies must be finite", nameof(f));
        foreach (double p in psd)
            if (!(double.IsFinite(p) && p >= 0))
                throw new ArgumentException("psd must be finite and non-negative", nameof(psd));
        double delta = (f[^1] - f[0]) / (f.Length - 1);
        bool even = double.IsFinite(delta) && delta > 0;
        for (int i = 1; even && i < f.Length; i++)
            even = Math.Abs(f[i] - f[i - 1] - delta) <= 1e-6 * delta;
        if (!even)
            throw new ArgumentException("frequencies must be ascending, evenly spaced, with a finite spacing", nameof(f));
        double lo = double.NegativeInfinity, hi = double.PositiveInfinity;
        if (span is { } s)
        {
            if (!(s.Low <= f[0] && s.High >= f[^1]))
                throw new ArgumentException("span must be (low, high) covering every bin center", nameof(span));
            (lo, hi) = s;
        }
        int n = f.Length;
        var power = new double[n];
        var left = new double[n];
        var right = new double[n];
        for (int k = 0; k < n; k++)
        {
            power[k] = psd[k] * delta;
            left[k] = Math.Max(f[k] - delta / 2, lo);
            right[k] = Math.Min(f[k] + delta / 2, hi);
            if (!(right[k] > left[k]))
                throw new ArgumentException("half a bin rounds to nothing at these frequencies", nameof(f));
        }
        double total = 0;
        foreach (double p in power)
            total += p;
        if (!double.IsFinite(total))
            throw new ArgumentException("psd too large: the bin powers or their sum overflow", nameof(psd));
        return (power, left, right);
    }

    private static Complex[] ToComplex(ReadOnlySpan<double> x)
    {
        var c = new Complex[x.Length];
        for (int i = 0; i < x.Length; i++)
            c[i] = new Complex(x[i], 0);
        return c;
    }

    /// <summary>In-place forward DFT of any length ≥ 1.</summary>
    private static void Transform(Complex[] x)
    {
        int n = x.Length;
        if (n == 1)
            return;
        if (BitOperations.IsPow2(n))
            Radix2(x);
        else
            Bluestein(x);
    }

    /// <summary>Iterative radix-2 decimation-in-time FFT; length must be a power of two.</summary>
    private static void Radix2(Complex[] x)
    {
        int n = x.Length;
        for (int i = 1, j = 0; i < n; i++)
        {
            int bit = n >> 1;
            for (; (j & bit) != 0; bit >>= 1)
                j ^= bit;
            j ^= bit;
            if (i < j)
                (x[i], x[j]) = (x[j], x[i]);
        }
        var tw = new Complex[n / 2]; // tw[k] = e^{−j2πk/n}, each computed directly for accuracy
        for (int k = 0; k < tw.Length; k++)
        {
            var (sin, cos) = Math.SinCos(-2.0 * Math.PI * k / n);
            tw[k] = new Complex(cos, sin);
        }
        for (int len = 2; len <= n; len <<= 1)
        {
            int half = len >> 1, stride = n / len;
            for (int start = 0; start < n; start += len)
            {
                for (int k = 0; k < half; k++)
                {
                    Complex t = tw[k * stride] * x[start + k + half];
                    Complex u = x[start + k];
                    x[start + k] = u + t;
                    x[start + k + half] = u - t;
                }
            }
        }
    }

    /// <summary>Bluestein's chirp-z FFT for any length, via a power-of-two circular convolution.</summary>
    private static void Bluestein(Complex[] x)
    {
        int n = x.Length;
        int m = (int)BitOperations.RoundUpToPowerOf2((uint)(2 * n - 1));
        var chirp = new Complex[n]; // e^{−jπk²/n}, with k² reduced mod 2n so the angle stays small
        long twoN = 2L * n;
        for (int k = 0; k < n; k++)
        {
            long k2 = (long)k * k % twoN;
            var (sin, cos) = Math.SinCos(-Math.PI * k2 / n);
            chirp[k] = new Complex(cos, sin);
        }
        var a = new Complex[m];
        var b = new Complex[m];
        for (int k = 0; k < n; k++)
            a[k] = x[k] * chirp[k];
        b[0] = Complex.Conjugate(chirp[0]);
        for (int k = 1; k < n; k++)
            b[k] = b[m - k] = Complex.Conjugate(chirp[k]);
        Radix2(a);
        Radix2(b);
        for (int i = 0; i < m; i++)
            a[i] = Complex.Conjugate(a[i] * b[i]);
        Radix2(a); // inverse via conjugation: conv = conj(FFT(conj(A·B))) / m
        for (int k = 0; k < n; k++)
            x[k] = Complex.Conjugate(a[k]) / m * chirp[k];
    }

    /// <summary>Modified Bessel function of the first kind, order 0, by its power series.</summary>
    internal static double BesselI0(double x)
    {
        double q = x * x / 4, term = 1, sum = 1;
        for (int k = 1; k < 500; k++)
        {
            term *= q / ((double)k * k);
            sum += term;
            if (term <= sum * 1e-17)
                break;
        }
        return sum;
    }
}
