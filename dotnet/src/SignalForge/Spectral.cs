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

/// <summary>The scale <see cref="Spectral.InterpolatePeak"/> fits its parabola on (conventions: Spectra, Peak interpolation).</summary>
public enum PeakScale
{
    /// <summary><c>10 log10</c> of the PSD; exact for a Gaussian peak.</summary>
    Decibel,

    /// <summary>The PSD as it is; exact for a parabolic peak.</summary>
    Linear,
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

/// <summary>
/// DPSS (Slepian) tapers, one per row, and the fraction of each one's energy in [−W, W]
/// (conventions: Spectra, DPSS tapers; ADR 0078).
/// </summary>
/// <param name="Tapers">K rows of N values, each of unit norm, most concentrated first.</param>
/// <param name="Concentrations">The fraction of each taper's energy inside [−W, W], W = NW/N.</param>
public sealed record TaperSet(double[][] Tapers, double[] Concentrations);

/// <summary>
/// Thomson's harmonic F-test per bin (conventions: Spectra, Harmonic F-test; ADR 0080).
/// </summary>
/// <param name="Frequencies">Bin frequencies in Hz: 0 … fs/2 for real input, the two-sided axis for complex.</param>
/// <param name="Amplitudes">The complex amplitude μ of a line μ·e^{2πi f n/fs} at each bin.</param>
/// <param name="FStatistic">F with 2 and 2K − 2 degrees of freedom.</param>
/// <param name="PValues">The F(2, 2K − 2) upper tail at each F.</param>
/// <param name="NumTapers">K, the number of tapers.</param>
public sealed record HarmonicFTestResult(double[] Frequencies, Complex[] Amplitudes, double[] FStatistic,
    double[] PValues, int NumTapers);

/// <summary>
/// Lines found by the harmonic F-test and the multitaper PSD left once they are removed
/// (conventions: Spectra, Multitaper line removal; ADR 0083).
/// </summary>
/// <typeparam name="T">The sample type: <see cref="double"/> for real input, <see cref="Complex"/> for complex.</typeparam>
/// <param name="Spectrum">The multitaper PSD of the residual.</param>
/// <param name="LineFrequencies">The lines' bin frequencies in Hz, in the F-test's order.</param>
/// <param name="LineAmplitudes">Each line's μ, the amplitude of μ·e^{2πi f n/fs}.</param>
/// <param name="Residual">The samples with the lines removed.</param>
public sealed record LineRemovalResult<T>(SpectralDensity Spectrum, double[] LineFrequencies, Complex[] LineAmplitudes,
    T[] Residual);

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

/// <summary>Loaded and notch power densities and their ratio (conventions: Spectra, Noise power
/// ratio; ADR 0118).</summary>
/// <param name="LoadedDensity">Mean PSD of the band outside the notch, in the PSD's units.</param>
/// <param name="NotchDensity">Mean PSD inside the notch.</param>
/// <param name="NprDb">10·log10(loaded) − 10·log10(notch); +∞ for an empty notch.</param>
public sealed record NoisePowerRatio(double LoadedDensity, double NotchDensity, double NprDb);

/// <summary>Geometric and arithmetic mean of the PSD over a band, and their ratio (conventions:
/// Spectra, Spectral flatness; ADR 0120).</summary>
/// <param name="GeometricMean">exp of the width-weighted mean of ln PSD, in the PSD's units.</param>
/// <param name="ArithmeticMean">Width-weighted mean PSD.</param>
/// <param name="Flatness">GeometricMean / ArithmeticMean, in [0, 1].</param>
/// <param name="FlatnessDb">10·log10(Flatness); −∞ when a weighted bin is zero.</param>
public sealed record SpectralFlatness(double GeometricMean, double ArithmeticMean, double Flatness, double FlatnessDb);

/// <summary>Peak and mean of a PSD over a band, and their ratio (conventions: Spectra, Spectral
/// crest factor; ADR 0125).</summary>
/// <param name="Peak">Largest PSD among the bins that overlap the band.</param>
/// <param name="Mean">Width-weighted mean PSD.</param>
/// <param name="Crest">Peak / Mean, at least 1.</param>
/// <param name="CrestDb">10·log10(Peak) − 10·log10(Mean).</param>
public sealed record SpectralCrest(double Peak, double Mean, double Crest, double CrestDb);

/// <summary>Power, centroid and RMS bandwidth of a PSD over a band (conventions: Spectra, Spectral
/// centroid and RMS bandwidth; ADR 0121).</summary>
/// <param name="Power">Integral of the step density over the band.</param>
/// <param name="Centroid">Power-weighted mean frequency, in the PSD's axis.</param>
/// <param name="RmsBandwidth">Power-weighted RMS spread about the centroid.</param>
public sealed record SpectralMoments(double Power, double Centroid, double RmsBandwidth);

/// <summary>Skewness and kurtosis of a PSD over a band (conventions: Spectra, Spectral skewness and
/// kurtosis; ADR 0126).</summary>
/// <param name="Skewness">m3 / m2^(3/2) about the centroid.</param>
/// <param name="Kurtosis">m4 / m2², not the excess: a flat band gives 9/5.</param>
public sealed record SpectralShape(double Skewness, double Kurtosis);

/// <summary>The least-squares line through a PSD over a band (conventions: Spectra, Spectral slope;
/// ADR 0127).</summary>
/// <param name="Center">The band's centre in Hz, where <paramref name="Level"/> is given.</param>
/// <param name="Level">The line's value at the centre: the band's mean PSD (or mean dB).</param>
/// <param name="Slope">The line's slope, in the PSD's units (or dB) per Hz.</param>
public sealed record SpectralSlope(double Center, double Level, double Slope);

/// <summary>A peak's width at a level below its top (conventions: Spectra, Peak widths; ADR 0138).</summary>
/// <param name="Index">The peak's bin.</param>
/// <param name="Level">The level the width is measured at, height − relHeight·prominence.</param>
/// <param name="Left">The left crossing in Hz.</param>
/// <param name="Right">The right crossing in Hz.</param>
/// <param name="Width">Right − Left, in Hz.</param>
public sealed record PeakWidth(int Index, double Level, double Left, double Right, double Width);

/// <summary>A tone found in a PSD (conventions: Spectra, Find tones; ADR 0137).</summary>
/// <param name="Index">The peak's bin.</param>
/// <param name="Frequency">The interpolated frequency in Hz, or the peak's where the fit is undefined.</param>
/// <param name="Height">The interpolated height in PSD units, or the peak's where the fit is undefined.</param>
/// <param name="Prominence">The peak's prominence.</param>
public sealed record Tone(int Index, double Frequency, double Height, double Prominence);

/// <summary>A peak's vertex from a parabola through three bins (conventions: Spectra, Peak interpolation; ADR 0136).</summary>
/// <param name="Frequency">The vertex's frequency in Hz.</param>
/// <param name="Height">The vertex's height in PSD units.</param>
/// <param name="Offset">The vertex's offset from the peak bin, in bins, within ±1/2.</param>
public sealed record PeakEstimate(double Frequency, double Height, double Offset);

/// <summary>A local maximum of a PSD (conventions: Spectra, Spectral peaks; ADR 0135).</summary>
/// <param name="Index">The middle bin of the peak's run, ⌊(i + j)/2⌋.</param>
/// <param name="Frequency">The run's middle in Hz, (f_i + f_j)/2.</param>
/// <param name="Height">The run's PSD value.</param>
/// <param name="Prominence">Height above the higher of the two bases.</param>
public sealed record SpectralPeak(int Index, double Frequency, double Height, double Prominence);

/// <summary>The power above and below a split frequency (conventions: Spectra, Band energy ratio;
/// ADR 0134).</summary>
/// <param name="Low">Power from the band's low edge to the split.</param>
/// <param name="High">Power from the split to the band's high edge.</param>
/// <param name="Ratio">High / Low: +∞ when Low is 0, 0 when High is 0.</param>
/// <param name="RatioDb">10 log10(Ratio).</param>
public sealed record BandEnergyRatio(double Low, double High, double Ratio, double RatioDb);

/// <summary>The loudest and quietest parts of a band (conventions: Spectra, Spectral contrast; ADR
/// 0133).</summary>
/// <param name="Peak">Mean density over the top fraction of the band's width.</param>
/// <param name="Valley">Mean density over the bottom fraction of the band's width.</param>
/// <param name="ContrastDb">10 log10(Peak / Valley), +∞ when Valley is 0.</param>
public sealed record SpectralContrast(double Peak, double Valley, double ContrastDb);

/// <summary>Differential entropy of a band's normalized PSD (conventions: Spectra, Spectral entropy;
/// ADR 0128).</summary>
/// <param name="Entropy">−∫ p ln p df of the unit-power step density, in nats.</param>
/// <param name="EntropyBandwidth">exp(Entropy), in Hz.</param>
/// <param name="Normalized">EntropyBandwidth over the band's width, in (0, 1].</param>
public sealed record SpectralEntropy(double Entropy, double EntropyBandwidth, double Normalized);

/// <summary>Where the PSD falls a given number of dB below its peak (conventions: Spectra, x dB
/// bandwidth; ADR 0122).</summary>
/// <param name="PeakFrequency">The peak bin's center, in the PSD's axis.</param>
/// <param name="PeakPsd">The peak bin's PSD.</param>
/// <param name="Lower">The lower edge, interpolated linearly in power.</param>
/// <param name="Upper">The upper edge, interpolated linearly in power.</param>
/// <param name="Bandwidth">Upper − Lower.</param>
public sealed record DbBandwidth(double PeakFrequency, double PeakPsd, double Lower, double Upper, double Bandwidth);

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

    /// <summary>
    /// The <paramref name="numTapers"/> discrete prolate spheroidal sequences of
    /// <paramref name="length"/> samples most concentrated in [−W, W], W =
    /// <paramref name="halfBandwidth"/>/<paramref name="length"/> (conventions: Spectra, DPSS tapers;
    /// ADR 0078).
    /// </summary>
    /// <param name="length">N, at least 1.</param>
    /// <param name="halfBandwidth">NW, the time–half-bandwidth product: above 0 and below N/2.</param>
    /// <param name="numTapers">K, 1 … N; null for max(1, ⌊2NW⌋ − 1).</param>
    public static TaperSet DpssTapers(int length, double halfBandwidth, int? numTapers = null)
    {
        if (length < 1)
            throw new ArgumentOutOfRangeException(nameof(length), length, "must be at least 1");
        var (nw, k) = TaperArgs(length, halfBandwidth, numTapers);
        double[][] tapers = Dpss(length, nw / length, k);
        return new TaperSet(tapers, Concentrations(tapers, nw / length));
    }

    private static double[] Concentrations(double[][] tapers, double w)
    {
        var conc = new double[tapers.Length];
        for (int j = 0; j < tapers.Length; j++)
        {
            // the autocorrelation r_d by an FFT of length 2N, exact up to rounding
            double[] v = tapers[j];
            int n = v.Length;
            var buf = new Complex[2 * n];
            for (int i = 0; i < n; i++)
                buf[i] = v[i];
            Transform(buf);
            for (int i = 0; i < buf.Length; i++)
                buf[i] = (buf[i].Real * buf[i].Real) + (buf[i].Imaginary * buf[i].Imaginary);
            Complex[] r = Ifft(buf);
            double lam = 2 * w * r[0].Real;
            for (int lag = 1; lag < n; lag++)
                lam += 2 * (Math.Sin(2 * Math.PI * w * lag) / (Math.PI * lag)) * r[lag].Real;
            conc[j] = lam;
        }
        return conc;
    }

    /// <summary>
    /// Thomson's multitaper PSD of complex samples: the mean of the periodograms of the whole input
    /// under the DPSS tapers, two-sided in shifted order (conventions: Spectra, Multitaper PSD; ADR
    /// 0078).
    /// </summary>
    /// <param name="samples">At least one sample.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="halfBandwidth">NW: above 0 and below the input length over 2.</param>
    /// <param name="numTapers">K, 1 … N; null for max(1, ⌊2NW⌋ − 1).</param>
    /// <param name="nfft">Transform length, at least the input length; null for the input length.</param>
    /// <param name="adaptive">Thomson's adaptive weights instead of the plain mean (ADR 0079).</param>
    public static SpectralDensity MultitaperPsd(ReadOnlySpan<Complex> samples, double sampleRate,
        double halfBandwidth, int? numTapers = null, int? nfft = null, bool adaptive = false) =>
        Multitaper(samples, sampleRate, halfBandwidth, numTapers, oneSided: false, nfft, adaptive);

    /// <summary>
    /// Thomson's multitaper PSD of real samples: one-sided unless <paramref name="oneSided"/> is
    /// false, which gives the two-sided shifted PSD (conventions: Spectra, Multitaper PSD; ADR 0078).
    /// </summary>
    /// <param name="samples">At least one sample.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="halfBandwidth">NW: above 0 and below the input length over 2.</param>
    /// <param name="numTapers">K, 1 … N; null for max(1, ⌊2NW⌋ − 1).</param>
    /// <param name="oneSided">Fold to bins 0 … ⌊nfft/2⌋, as Welch.</param>
    /// <param name="nfft">Transform length, at least the input length; null for the input length.</param>
    /// <param name="adaptive">Thomson's adaptive weights instead of the plain mean (ADR 0079).</param>
    public static SpectralDensity MultitaperPsd(ReadOnlySpan<double> samples, double sampleRate,
        double halfBandwidth, int? numTapers = null, bool oneSided = true, int? nfft = null, bool adaptive = false) =>
        Multitaper(ToComplex(samples), sampleRate, halfBandwidth, numTapers, oneSided, nfft, adaptive);

    private static SpectralDensity Multitaper(ReadOnlySpan<Complex> x, double sampleRate, double halfBandwidth,
        int? numTapers, bool oneSided, int? nfft, bool adaptive)
    {
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        int n = x.Length;
        if (n < 1)
            throw new ArgumentException("samples needs at least 1", nameof(x));
        int m = nfft ?? n;
        if (m < n)
            throw new ArgumentException("nfft must be at least the input length", nameof(nfft));
        var (nw, k) = TaperArgs(n, halfBandwidth, numTapers);
        double[][] tapers = Dpss(n, nw / n, k);
        var buf = new Complex[m];
        var eigen = new double[k][];
        for (int j = 0; j < k; j++)
        {
            for (int i = 0; i < n; i++)
                buf[i] = x[i] * tapers[j][i];
            Array.Clear(buf, n, m - n);
            Transform(buf);
            eigen[j] = new double[m];
            for (int i = 0; i < m; i++)
                eigen[j][i] = (buf[i].Real * buf[i].Real + buf[i].Imaginary * buf[i].Imaginary) / sampleRate;
        }
        var two = new double[m];
        if (adaptive)
        {
            double power = 0;
            for (int i = 0; i < n; i++)
                power += (x[i].Real * x[i].Real) + (x[i].Imaginary * x[i].Imaginary);
            Adaptive(eigen, Concentrations(tapers, nw / n), power / n / sampleRate, two);
        }
        else
        {
            for (int i = 0; i < m; i++)
            {
                double s = 0;
                for (int j = 0; j < k; j++)
                    s += eigen[j][i];
                two[i] = s / k;
            }
        }
        var g = new Segments(n, n, 1, tapers[0], sampleRate, 1.0, Detrend.None, m);
        return new SpectralDensity(g.Frequencies(oneSided), g.Fold(two, 1.0, oneSided), sampleRate,
            n, k, oneSided, sampleRate / m, 2 * nw / n * sampleRate, m);
    }

    /// <summary>
    /// Thomson's F-test for a line μ·e^{2πi f n/fs} at each bin of a real input, bins 0 … ⌊M/2⌋
    /// (conventions: Spectra, Harmonic F-test; ADR 0080).
    /// </summary>
    /// <param name="samples">The input, at least one sample.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="halfBandwidth">NW, in (0, N/2).</param>
    /// <param name="numTapers">K, at least 2; null for max(1, ⌊2NW⌋ − 1), which must then be at least 2.</param>
    /// <param name="nfft">Transform length, at least the input length; null for the input length.</param>
    public static HarmonicFTestResult HarmonicFTest(ReadOnlySpan<double> samples, double sampleRate,
        double halfBandwidth, int? numTapers = null, int? nfft = null) =>
        FTest(ToComplex(samples), sampleRate, halfBandwidth, numTapers, nfft, oneSided: true);

    /// <summary>
    /// Thomson's F-test for a line μ·e^{2πi f n/fs} at each bin of a complex input, on the two-sided
    /// axis (conventions: Spectra, Harmonic F-test; ADR 0080).
    /// </summary>
    /// <param name="samples">The input, at least one sample.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="halfBandwidth">NW, in (0, N/2).</param>
    /// <param name="numTapers">K, at least 2; null for max(1, ⌊2NW⌋ − 1), which must then be at least 2.</param>
    /// <param name="nfft">Transform length, at least the input length; null for the input length.</param>
    public static HarmonicFTestResult HarmonicFTest(ReadOnlySpan<Complex> samples, double sampleRate,
        double halfBandwidth, int? numTapers = null, int? nfft = null) =>
        FTest(samples, sampleRate, halfBandwidth, numTapers, nfft, oneSided: false);

    private static HarmonicFTestResult FTest(ReadOnlySpan<Complex> x, double sampleRate, double halfBandwidth,
        int? numTapers, int? nfft, bool oneSided)
    {
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        int n = x.Length;
        if (n < 1)
            throw new ArgumentException("samples needs at least 1", nameof(x));
        int m = nfft ?? n;
        if (m < n)
            throw new ArgumentException("nfft must be at least the input length", nameof(nfft));
        var (nw, k) = TaperArgs(n, halfBandwidth, numTapers);
        if (k < 2)
            throw new ArgumentException("the F-test needs at least 2 tapers", nameof(numTapers));
        double[][] tapers = Dpss(n, nw / n, k);
        var xs = new Complex[k][];
        var u = new double[k];
        double uu = 0;
        for (int j = 0; j < k; j++)
        {
            xs[j] = new Complex[m];
            for (int i = 0; i < n; i++)
            {
                xs[j][i] = x[i] * tapers[j][i];
                u[j] += tapers[j][i];
            }
            Transform(xs[j]);
            uu += u[j] * u[j];
        }
        var mu = new Complex[m];
        var f = new double[m];
        var p = new double[m];
        for (int b = 0; b < m; b++)
        {
            Complex s = Complex.Zero;
            for (int j = 0; j < k; j++)
                s += u[j] * xs[j][b];
            mu[b] = s / uu;
            double resid = 0;
            for (int j = 0; j < k; j++)
            {
                Complex r = xs[j][b] - (mu[b] * u[j]);
                resid += (r.Real * r.Real) + (r.Imaginary * r.Imaginary);
            }
            double mag = (mu[b].Real * mu[b].Real) + (mu[b].Imaginary * mu[b].Imaginary);
            double num = (k - 1) * mag * uu;
            f[b] = resid > 0 ? num / resid : num > 0 ? double.PositiveInfinity : 0.0;
            p[b] = double.IsPositiveInfinity(f[b]) ? 0.0 : Math.Pow(1 + (f[b] / (k - 1)), -(k - 1));
        }
        var g = new Segments(n, n, 1, tapers[0], sampleRate, 1.0, Detrend.None, m);
        int count = oneSided ? (m / 2) + 1 : m;
        int Bin(int i) => oneSided ? i : (i + ((m + 1) / 2)) % m; // two-sided index i holds bin i − ⌊m/2⌋
        return new HarmonicFTestResult(g.Frequencies(oneSided),
            [.. Enumerable.Range(0, count).Select(i => mu[Bin(i)])],
            [.. Enumerable.Range(0, count).Select(i => f[Bin(i)])],
            [.. Enumerable.Range(0, count).Select(i => p[Bin(i)])], k);
    }

    /// <summary>
    /// Thomson's line removal on a real input: subtract the lines the harmonic F-test finds, then the
    /// multitaper PSD of what remains (conventions: Spectra, Multitaper line removal; ADR 0083).
    /// </summary>
    /// <param name="samples">The input, at least one sample.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="halfBandwidth">NW, in (0, N/2).</param>
    /// <param name="probability">A bin is a line when its p-value is below this, in (0, 1]; null for 1/N.</param>
    /// <param name="numTapers">K, at least 2; null for max(1, ⌊2NW⌋ − 1), which must then be at least 2.</param>
    /// <param name="oneSided">Whether the spectrum is one-sided.</param>
    /// <param name="nfft">Transform length, at least the input length; null for the input length.</param>
    /// <param name="adaptive">Whether the spectrum uses Thomson's adaptive weights.</param>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LineRemovalResult<double> MultitaperLineRemoval(ReadOnlySpan<double> samples, double sampleRate,
        double halfBandwidth, double? probability = null, int? numTapers = null, bool oneSided = true, int? nfft = null,
        bool adaptive = false)
    {
        var (freqs, amps, residual) = RemoveLines(ToComplex(samples), sampleRate, halfBandwidth, probability, numTapers, nfft, real: true);
        double[] r = [.. residual.Select(z => z.Real)];
        return new LineRemovalResult<double>(MultitaperPsd(r, sampleRate, halfBandwidth, numTapers, oneSided, nfft, adaptive),
            freqs, amps, r);
    }

    /// <summary>
    /// Thomson's line removal on a complex input: subtract the lines the harmonic F-test finds, then the
    /// two-sided multitaper PSD of what remains (conventions: Spectra, Multitaper line removal; ADR 0083).
    /// </summary>
    /// <param name="samples">The input, at least one sample.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="halfBandwidth">NW, in (0, N/2).</param>
    /// <param name="probability">A bin is a line when its p-value is below this, in (0, 1]; null for 1/N.</param>
    /// <param name="numTapers">K, at least 2; null for max(1, ⌊2NW⌋ − 1), which must then be at least 2.</param>
    /// <param name="nfft">Transform length, at least the input length; null for the input length.</param>
    /// <param name="adaptive">Whether the spectrum uses Thomson's adaptive weights.</param>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LineRemovalResult<Complex> MultitaperLineRemoval(ReadOnlySpan<Complex> samples, double sampleRate,
        double halfBandwidth, double? probability = null, int? numTapers = null, int? nfft = null, bool adaptive = false)
    {
        var (freqs, amps, residual) = RemoveLines(samples, sampleRate, halfBandwidth, probability, numTapers, nfft, real: false);
        return new LineRemovalResult<Complex>(MultitaperPsd(residual, sampleRate, halfBandwidth, numTapers, nfft, adaptive),
            freqs, amps, residual);
    }

    private static (double[] Frequencies, Complex[] Amplitudes, Complex[] Residual) RemoveLines(ReadOnlySpan<Complex> x,
        double sampleRate, double halfBandwidth, double? probability, int? numTapers, int? nfft, bool real)
    {
        HarmonicFTestResult test = FTest(x, sampleRate, halfBandwidth, numTapers, nfft, oneSided: real);
        int n = x.Length, m = nfft ?? n;
        double alpha = probability ?? 1.0 / n;
        if (!(alpha > 0 && alpha <= 1))
            throw new ArgumentOutOfRangeException(nameof(probability), probability, "must be in (0, 1]");
        var (nw, _) = TaperArgs(n, halfBandwidth, numTapers);
        int r = (int)Math.Floor(nw * m / n);
        int Pos(int b)
        {
            b = ((b % m) + m) % m;
            return real ? (b <= m / 2 ? b : m - b) : (b + (m / 2)) % m;
        }
        int BinOf(int j) => real ? j : (((j - (m / 2)) % m) + m) % m;
        double[] f = test.FStatistic;
        var lines = new List<int>();
        for (int j = 0; j < f.Length; j++)
        {
            if (!(test.PValues[j] < alpha))
                continue;
            int b = BinOf(j);
            bool peak = true;
            for (int d = -r; d <= r && peak; d++)
            {
                int i = Pos(b + d);
                if (d != 0 && i != j)
                    peak = i < j ? f[j] > f[i] : f[j] >= f[i];
            }
            if (peak)
                lines.Add(j);
        }
        var residual = x.ToArray();
        foreach (int j in lines)
        {
            int b = BinOf(j);
            Complex mu = test.Amplitudes[j];
            for (int t = 0; t < n; t++)
            {
                Complex e = Complex.FromPolarCoordinates(1, 2 * Math.PI * (int)((long)b * t % m) / m);
                residual[t] -= real
                    ? (b == 0 || 2 * b == m ? mu.Real * e.Real : 2 * (mu * e).Real)
                    : mu * e;
            }
        }
        return ([.. lines.Select(j => test.Frequencies[j])], [.. lines.Select(j => test.Amplitudes[j])], residual);
    }

    /// <summary>Thomson's adaptive combination, each bin iterated on its own (ADR 0079).</summary>
    private static void Adaptive(double[][] eigen, double[] lam, double noise, double[] s)
    {
        int k = lam.Length;
        for (int i = 0; i < s.Length; i++)
        {
            double cur = k == 1 ? eigen[0][i] : (eigen[0][i] + eigen[1][i]) / 2;
            if (k > 1 && noise != 0)
            {
                for (int it = 0; it < 1000 && cur > 0; it++)
                {
                    double num = 0, den = 0;
                    for (int j = 0; j < k; j++)
                    {
                        double a = (lam[j] * cur) + ((1 - lam[j]) * noise);
                        double w = lam[j] / (a * a);
                        num += w * eigen[j][i];
                        den += w;
                    }
                    double next = num / den;
                    bool done = Math.Abs(next - cur) <= 1e-10 * next;
                    cur = next;
                    if (done)
                        break;
                }
            }
            s[i] = cur;
        }
    }

    private static (double Nw, int K) TaperArgs(int n, double halfBandwidth, int? numTapers)
    {
        if (!(halfBandwidth > 0 && halfBandwidth < n / 2.0))
            throw new ArgumentOutOfRangeException(nameof(halfBandwidth), halfBandwidth, "must be above 0 and below length/2");
        int k = numTapers ?? Math.Max(1, (int)Math.Floor(2 * halfBandwidth) - 1);
        if (k < 1 || k > n)
            throw new ArgumentOutOfRangeException(nameof(numTapers), k, "must be between 1 and length");
        return (halfBandwidth, k);
    }

    /// <summary>The tapers: Sturm bisection for each eigenvalue of the commuting tridiagonal matrix,
    /// then inverse iteration (conventions: Spectra, DPSS tapers).</summary>
    private static double[][] Dpss(int n, double w, int k)
    {
        double cw = Math.Cos(2 * Math.PI * w);
        var d = new double[n];
        var e = new double[n]; // e[i] couples i − 1 and i; e[0] = 0
        for (int i = 0; i < n; i++)
        {
            d[i] = ((n - 1) / 2.0 - i) * ((n - 1) / 2.0 - i) * cw;
            e[i] = i == 0 ? 0 : i * (double)(n - i) / 2;
        }
        var rows = new double[k][];
        for (int j = 0; j < k; j++)
            rows[j] = InverseIteration(d, e, TridiagonalEigenvalue(d, e, n - 1 - j), j, rows.AsSpan(0, j));
        return rows;
    }

    /// <summary>How many eigenvalues of the tridiagonal matrix are below <paramref name="x"/>.</summary>
    private static int Sturm(double[] d, double[] e, double x)
    {
        int below = 0;
        double q = 1.0;
        for (int i = 0; i < d.Length; i++)
        {
            q = d[i] - x - (i > 0 ? e[i] * e[i] / q : 0.0);
            if (q == 0.0)
                q = -1e-300;
            if (q < 0)
                below++;
        }
        return below;
    }

    /// <summary>The <paramref name="index"/>-th smallest eigenvalue (from 0), by bisection on the Sturm count.</summary>
    private static double TridiagonalEigenvalue(double[] d, double[] e, int index)
    {
        int n = d.Length;
        double lo = double.PositiveInfinity, hi = double.NegativeInfinity;
        for (int i = 0; i < n; i++)
        {
            double r = Math.Abs(e[i]) + (i + 1 < n ? Math.Abs(e[i + 1]) : 0.0);
            lo = Math.Min(lo, d[i] - r);
            hi = Math.Max(hi, d[i] + r);
        }
        for (int it = 0; it < 200; it++)
        {
            double mid = 0.5 * (lo + hi);
            if (mid == lo || mid == hi)
                break;
            if (Sturm(d, e, mid) > index)
                hi = mid;
            else
                lo = mid;
        }
        return 0.5 * (lo + hi);
    }

    /// <summary>The unit eigenvector for <paramref name="theta"/>, with the sign rule for taper <paramref name="k"/>.</summary>
    private static double[] InverseIteration(double[] d, double[] e, double theta, int k, ReadOnlySpan<double[]> earlier)
    {
        int n = d.Length;
        double mid = (n - 1) / 2.0;
        var v = new double[n];
        for (int i = 0; i < n; i++)
            v[i] = k % 2 == 0 ? 1.0 : mid - i;
        double scale = 1.0;
        for (int i = 0; i < n; i++)
            scale = Math.Max(scale, Math.Max(Math.Abs(d[i]), Math.Abs(e[i])));
        for (int it = 0; it < 4; it++)
        {
            v = ShiftedSolve(d, e, theta, v, scale);
            foreach (double[] u in earlier) // against rounding drift toward a neighbor
            {
                double dot = 0;
                for (int i = 0; i < n; i++)
                    dot += u[i] * v[i];
                for (int i = 0; i < n; i++)
                    v[i] -= dot * u[i];
            }
            double norm = 0;
            for (int i = 0; i < n; i++)
                norm += v[i] * v[i];
            norm = Math.Sqrt(norm);
            for (int i = 0; i < n; i++)
                v[i] /= norm;
        }
        double sign = 0;
        for (int i = 0; i < n; i++)
            sign += k % 2 == 0 ? v[i] : (mid - i) * v[i];
        if (sign < 0)
        {
            for (int i = 0; i < n; i++)
                v[i] = -v[i];
        }
        return v;
    }

    /// <summary>(T − θI)x = b by Gaussian elimination with partial pivoting (as LAPACK's gttrf); a
    /// zero pivot is replaced by a tiny one, as inverse iteration wants.</summary>
    private static double[] ShiftedSolve(double[] d, double[] e, double theta, double[] b, double scale)
    {
        int n = d.Length;
        double eps = Math.Pow(2, -52) * scale;
        var dd = new double[n];
        var du = new double[n]; // row i, column i + 1
        var dl = new double[n]; // row i + 1, column i
        var du2 = new double[n]; // row i, column i + 2, after a swap
        var y = (double[])b.Clone();
        for (int i = 0; i < n; i++)
        {
            dd[i] = d[i] - theta;
            du[i] = i + 1 < n ? e[i + 1] : 0.0;
            dl[i] = i + 1 < n ? e[i + 1] : 0.0;
        }
        for (int i = 0; i < n - 1; i++)
        {
            if (Math.Abs(dd[i]) >= Math.Abs(dl[i]))
            {
                if (dd[i] == 0.0)
                    dd[i] = eps;
                double f = dl[i] / dd[i];
                dd[i + 1] -= f * du[i];
                y[i + 1] -= f * y[i];
            }
            else
            {
                double f = dd[i] / dl[i];
                dd[i] = dl[i];
                double t = du[i];
                du[i] = dd[i + 1];
                dd[i + 1] = t - (f * dd[i + 1]);
                du2[i] = du[i + 1];
                du[i + 1] = -f * du[i + 1];
                (y[i], y[i + 1]) = (y[i + 1], y[i] - (f * y[i + 1]));
            }
        }
        if (dd[n - 1] == 0.0)
            dd[n - 1] = eps;
        var x = new double[n];
        for (int i = n - 1; i >= 0; i--)
        {
            double s = y[i];
            if (i + 1 < n)
                s -= du[i] * x[i + 1];
            if (i + 2 < n)
                s -= du2[i] * x[i + 2];
            x[i] = s / dd[i];
        }
        return x;
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

    /// <summary>
    /// Zechmeister-Kürster generalized Lomb-Scargle periodogram: the weighted fit of
    /// <c>a cos ωt + b sin ωt + c</c> at each frequency (conventions: Spectra, Generalized Lomb-Scargle;
    /// ADR 0081).
    /// </summary>
    /// <param name="times">Sample times, finite, in any order; at least two.</param>
    /// <param name="values">Finite values, one per time.</param>
    /// <param name="frequencies">Trial frequencies in Hz, finite and positive; may be empty.</param>
    /// <param name="uncertainties">σ per sample, finite and positive; null for all 1.</param>
    /// <param name="normalization">Standard <c>(χ²₀ − χ²)/χ²₀</c>, or power <c>(χ²₀ − χ²)/2</c>.</param>
    /// <returns>The periodogram at each frequency, in their order.</returns>
    public static double[] GeneralizedLombScargle(ReadOnlySpan<double> times, ReadOnlySpan<double> values,
        ReadOnlySpan<double> frequencies, double[]? uncertainties = null,
        LombScargleNormalization normalization = LombScargleNormalization.Standard)
    {
        int n = times.Length;
        if (values.Length != n || n < 2)
            throw new ArgumentException("times and values must have the same length, at least 2", nameof(values));
        foreach (double v in times)
            if (!double.IsFinite(v)) throw new ArgumentException("times must be finite", nameof(times));
        foreach (double v in values)
            if (!double.IsFinite(v)) throw new ArgumentException("values must be finite", nameof(values));
        var w = new double[n];
        for (int i = 0; i < n; i++)
            w[i] = 1;
        if (uncertainties is not null)
        {
            if (uncertainties.Length != n)
                throw new ArgumentException("uncertainties must have one value per sample", nameof(uncertainties));
            for (int i = 0; i < n; i++)
            {
                double s = uncertainties[i];
                if (!(double.IsFinite(s) && s > 0))
                    throw new ArgumentException("uncertainties must be finite and positive", nameof(uncertainties));
                w[i] = 1 / (s * s);
            }
        }
        foreach (double v in frequencies)
            if (!(double.IsFinite(v) && v > 0)) throw new ArgumentException("frequencies must be finite and positive", nameof(frequencies));
        if (normalization is not (LombScargleNormalization.Standard or LombScargleNormalization.Power))
            throw new ArgumentException($"unknown normalization {normalization}", nameof(normalization));
        double bigW = 0;
        foreach (double v in w)
            bigW += v;
        for (int i = 0; i < n; i++)
            w[i] /= bigW;
        var y = values.ToArray();
        double yy = Cov(w, y, y);
        if (normalization == LombScargleNormalization.Standard && !(yy > 0))
            throw new ArgumentException("the standard normalization needs values that are not all equal", nameof(values));
        var out_ = new double[frequencies.Length];
        var c = new double[n];
        var s_ = new double[n];
        for (int k = 0; k < out_.Length; k++)
        {
            double om = 2 * Math.PI * frequencies[k];
            for (int i = 0; i < n; i++)
            {
                c[i] = Math.Cos(om * times[i]);
                s_[i] = Math.Sin(om * times[i]);
            }
            double tau = Math.Atan2(2 * Cov(w, c, s_), Cov(w, c, c) - Cov(w, s_, s_)) / (2 * om);
            for (int i = 0; i < n; i++)
            {
                c[i] = Math.Cos(om * (times[i] - tau));
                s_[i] = Math.Sin(om * (times[i] - tau));
            }
            double cc = Cov(w, c, c), ss = Cov(w, s_, s_);
            double p = 0;
            if (cc >= 1e-12)
                p += Cov(w, y, c) * Cov(w, y, c) / cc;
            if (ss >= 1e-12)
                p += Cov(w, y, s_) * Cov(w, y, s_) / ss;
            out_[k] = normalization == LombScargleNormalization.Standard ? p / yy : bigW * p / 2;
        }
        return out_;
    }

    /// <summary>
    /// Multiterm Lomb-Scargle periodogram: the weighted fit of a constant and <paramref name="terms"/>
    /// harmonics <c>aₖ cos kωt + bₖ sin kωt</c> at each frequency (conventions: Spectra, Multiterm
    /// Lomb-Scargle; ADR 0103).
    /// </summary>
    /// <param name="times">Sample times, finite, in any order; at least two.</param>
    /// <param name="values">Finite values, one per time.</param>
    /// <param name="frequencies">Trial frequencies in Hz, finite and positive; may be empty.</param>
    /// <param name="terms">The number of harmonics, at least 1.</param>
    /// <param name="uncertainties">σ per sample, finite and positive; null for all 1.</param>
    /// <param name="normalization">Standard <c>(χ²₀ − χ²)/χ²₀</c>, or power <c>(χ²₀ − χ²)/2</c>.</param>
    /// <returns>The periodogram at each frequency, in their order.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] LombScargleMultiterm(ReadOnlySpan<double> times, ReadOnlySpan<double> values,
        ReadOnlySpan<double> frequencies, int terms, double[]? uncertainties = null,
        LombScargleNormalization normalization = LombScargleNormalization.Standard)
    {
        int n = times.Length;
        if (values.Length != n || n < 2)
            throw new ArgumentException("times and values must have the same length, at least 2", nameof(values));
        foreach (double v in times)
            if (!double.IsFinite(v)) throw new ArgumentException("times must be finite", nameof(times));
        foreach (double v in values)
            if (!double.IsFinite(v)) throw new ArgumentException("values must be finite", nameof(values));
        ArgumentOutOfRangeException.ThrowIfLessThan(terms, 1);
        var w = new double[n];
        for (int i = 0; i < n; i++)
            w[i] = 1;
        if (uncertainties is not null)
        {
            if (uncertainties.Length != n)
                throw new ArgumentException("uncertainties must have one value per sample", nameof(uncertainties));
            for (int i = 0; i < n; i++)
            {
                double s = uncertainties[i];
                if (!(double.IsFinite(s) && s > 0))
                    throw new ArgumentException("uncertainties must be finite and positive", nameof(uncertainties));
                w[i] = 1 / (s * s);
            }
        }
        foreach (double v in frequencies)
            if (!(double.IsFinite(v) && v > 0)) throw new ArgumentException("frequencies must be finite and positive", nameof(frequencies));
        if (normalization is not (LombScargleNormalization.Standard or LombScargleNormalization.Power))
            throw new ArgumentException($"unknown normalization {normalization}", nameof(normalization));
        double bigW = 0;
        foreach (double v in w)
            bigW += v;
        for (int i = 0; i < n; i++)
            w[i] /= bigW;
        var yc = new double[n];
        double mean = Dot(w, values.ToArray());
        for (int i = 0; i < n; i++)
            yc[i] = values[i] - mean;
        double yy = Dot3(w, yc, yc);
        // the weights need not sum to exactly 1, so equal values can leave a tiny yy
        if (normalization == LombScargleNormalization.Standard && (!values.ContainsAnyExcept(values[0]) || !(yy > 0)))
            throw new ArgumentException("the standard normalization needs values that are not all equal", nameof(values));
        var out_ = new double[frequencies.Length];
        for (int j = 0; j < out_.Length; j++)
        {
            double om = 2 * Math.PI * frequencies[j];
            var kept = new List<(double[] Q, double QQ)>();
            double explained = 0;
            for (int k = 1; k <= terms; k++)
            {
                for (int part = 0; part < 2; part++)
                {
                    var q = new double[n];
                    for (int i = 0; i < n; i++)
                    {
                        double arg = om * k * times[i];
                        q[i] = part == 0 ? Math.Cos(arg) : Math.Sin(arg);
                    }
                    double m = Dot(w, q);
                    for (int i = 0; i < n; i++)
                        q[i] -= m;
                    foreach (var (b, bb) in kept)
                    {
                        double c = Dot3(w, q, b) / bb;
                        for (int i = 0; i < n; i++)
                            q[i] -= c * b[i];
                    }
                    double qq = Dot3(w, q, q);
                    if (qq < 1e-12)
                        continue;
                    kept.Add((q, qq));
                    double yq = Dot3(w, yc, q);
                    explained += yq * yq / qq;
                }
            }
            out_[j] = normalization == LombScargleNormalization.Standard ? explained / yy : bigW * explained / 2;
        }
        return out_;
    }

    /// <summary>Σ w a.</summary>
    private static double Dot(double[] w, double[] a)
    {
        double s = 0;
        for (int i = 0; i < w.Length; i++)
            s += w[i] * a[i];
        return s;
    }

    /// <summary>Σ w a b.</summary>
    private static double Dot3(double[] w, double[] a, double[] b)
    {
        double s = 0;
        for (int i = 0; i < w.Length; i++)
            s += w[i] * a[i] * b[i];
        return s;
    }

    /// <summary>The weighted centered sum Σ w a b − (Σ w a)(Σ w b), weights summing to 1.</summary>
    private static double Cov(double[] w, double[] a, double[] b)
    {
        double ab = 0, sa = 0, sb = 0;
        for (int i = 0; i < w.Length; i++)
        {
            ab += w[i] * a[i] * b[i];
            sa += w[i] * a[i];
            sb += w[i] * b[i];
        }
        return ab - (sa * sb);
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

    /// <summary>The standard Lomb-Scargle value that white Gaussian noise exceeds with chance <paramref name="probability"/>
    /// over <paramref name="numFrequencies"/> independent frequencies: the inverse of <see cref="LombScargleFalseAlarm"/>
    /// (conventions: Spectra; ADR 0082).</summary>
    /// <param name="probability">The false-alarm probability, in [0, 1].</param>
    /// <param name="numSamples">The number of samples the periodogram was computed from.</param>
    /// <param name="numFrequencies">The number of independent frequencies searched, at least 1.</param>
    /// <param name="center">Whether the periodogram subtracted the mean, as <see cref="LombScargle"/>'s <c>center</c>;
    /// true also for <see cref="GeneralizedLombScargle"/>.</param>
    /// <returns><c>1 − P₁^(2/(N − d))</c> with <c>P₁ = 1 − (1 − p)^(1/M)</c>, <c>d</c> 3 centered and 2 not.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double LombScargleFalseAlarmLevel(double probability, int numSamples, int numFrequencies = 1, bool center = true)
    {
        int d = center ? 3 : 2;
        if (!(probability >= 0 && probability <= 1))
            throw new ArgumentOutOfRangeException(nameof(probability), probability, "must be between 0 and 1");
        if (numSamples < d + 1)
            throw new ArgumentOutOfRangeException(nameof(numSamples), numSamples, $"must be at least {d + 1}");
        ArgumentOutOfRangeException.ThrowIfLessThan(numFrequencies, 1);
        if (probability == 0)
            return 1.0;
        double p1 = probability < 1 ? -ExpM1(LogP1(-probability) / numFrequencies) : 1.0;
        return -ExpM1(2 * Math.Log(p1) / (numSamples - d));
    }

    /// <summary>Baluev's alias-free estimate of the chance that white Gaussian noise gives a standard Lomb-Scargle
    /// value above <paramref name="power"/> anywhere up to <paramref name="maxFrequency"/> for these sample times
    /// (conventions: Spectra; ADR 0098).</summary>
    /// <param name="power">A value of the standard normalization, in [0, 1].</param>
    /// <param name="times">The sample times, finite and not all equal, at least 4 centered and 3 not.</param>
    /// <param name="maxFrequency">The highest frequency searched, positive and finite.</param>
    /// <param name="center">Whether the periodogram subtracted the mean, as <see cref="LombScargle"/>'s <c>center</c>;
    /// true also for <see cref="GeneralizedLombScargle"/>.</param>
    /// <returns><c>1 − (1 − P₁)·e^(−τ)</c>, with <c>τ</c> Baluev's expected number of upcrossings.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double LombScargleFalseAlarmBaluev(double power, ReadOnlySpan<double> times, double maxFrequency,
        bool center = true)
    {
        if (!(power >= 0 && power <= 1))
            throw new ArgumentOutOfRangeException(nameof(power), power, "must be between 0 and 1 (the standard normalization)");
        var (nk, nh, scale) = BaluevSetup(times, maxFrequency, center);
        return Baluev(power, nk, nh, scale);
    }

    /// <summary>The highest standard Lomb-Scargle value over <paramref name="frequencies"/> for each of
    /// <paramref name="draws"/> resamplings of <paramref name="values"/> with replacement at the same times, in draw order
    /// (conventions: Spectra; ADR 0101).</summary>
    /// <param name="times">The sample times, as for <see cref="LombScargle"/>.</param>
    /// <param name="values">The values, as for <see cref="LombScargle"/> in the standard normalization.</param>
    /// <param name="frequencies">The search grid in Hz, not empty.</param>
    /// <param name="draws">The number of resamplings, at least 1.</param>
    /// <param name="seed">The seed of the generator.</param>
    /// <param name="center">Whether to subtract each draw's mean, as for <see cref="LombScargle"/>.</param>
    /// <returns>One peak per draw; 0 for a draw that cannot be normalized.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] LombScargleBootstrap(ReadOnlySpan<double> times, ReadOnlySpan<double> values,
        ReadOnlySpan<double> frequencies, int draws, int seed, bool center = true) =>
        LombScargleBootstrap(times, values, frequencies, draws, new Random(seed), center);

    /// <summary>The highest standard Lomb-Scargle value over <paramref name="frequencies"/> for each of
    /// <paramref name="draws"/> resamplings of <paramref name="values"/> with replacement at the same times, in draw order
    /// (conventions: Spectra; ADR 0101).</summary>
    /// <param name="times">The sample times, as for <see cref="LombScargle"/>.</param>
    /// <param name="values">The values, as for <see cref="LombScargle"/> in the standard normalization.</param>
    /// <param name="frequencies">The search grid in Hz, not empty.</param>
    /// <param name="draws">The number of resamplings, at least 1.</param>
    /// <param name="rng">The generator the indices are drawn from.</param>
    /// <param name="center">Whether to subtract each draw's mean, as for <see cref="LombScargle"/>.</param>
    /// <returns>One peak per draw; 0 for a draw that cannot be normalized.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] LombScargleBootstrap(ReadOnlySpan<double> times, ReadOnlySpan<double> values,
        ReadOnlySpan<double> frequencies, int draws, Random rng, bool center = true)
    {
        ArgumentNullException.ThrowIfNull(rng);
        LombScargle(times, values, frequencies, center); // checks everything else
        if (frequencies.IsEmpty)
            throw new ArgumentException("must not be empty", nameof(frequencies));
        ArgumentOutOfRangeException.ThrowIfLessThan(draws, 1);
        int n = values.Length;
        var peaks = new double[draws];
        var drawn = new double[n];
        for (int i = 0; i < draws; i++)
        {
            bool same = true, zero = true;
            for (int k = 0; k < n; k++)
            {
                drawn[k] = values[rng.Next(n)];
                same &= drawn[k] == drawn[0];
                zero &= drawn[k] == 0;
            }
            if (center ? same : zero)
                continue; // nothing to normalize: the peak is 0
            peaks[i] = LombScargle(times, drawn, frequencies, center).Max();
        }
        return peaks;
    }

    /// <summary>The standard Lomb-Scargle value that white Gaussian noise exceeds with chance <paramref name="probability"/>
    /// anywhere up to <paramref name="maxFrequency"/>: the inverse of <see cref="LombScargleFalseAlarmBaluev"/>, by
    /// bisection (conventions: Spectra; ADR 0099).</summary>
    /// <param name="probability">The false-alarm probability, in [0, 1].</param>
    /// <param name="times">The sample times, finite and not all equal, at least 4 centered and 3 not.</param>
    /// <param name="maxFrequency">The highest frequency searched, positive and finite.</param>
    /// <param name="center">Whether the periodogram subtracted the mean, as <see cref="LombScargle"/>'s <c>center</c>;
    /// true also for <see cref="GeneralizedLombScargle"/>.</param>
    /// <returns>The smallest value bisection finds whose Baluev probability is at most <paramref name="probability"/>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double LombScargleFalseAlarmLevelBaluev(double probability, ReadOnlySpan<double> times, double maxFrequency,
        bool center = true)
    {
        if (!(probability >= 0 && probability <= 1))
            throw new ArgumentOutOfRangeException(nameof(probability), probability, "must be between 0 and 1");
        var (nk, nh, scale) = BaluevSetup(times, maxFrequency, center);
        if (probability == 1)
            return 0; // F(0) = 1 is not above 1
        double lo = 0, hi = 1;
        while (true)
        {
            double m = lo + (hi - lo) / 2;
            if (m == lo || m == hi)
                return hi;
            if (Baluev(m, nk, nh, scale) > probability)
                lo = m;
            else
                hi = m;
        }
    }

    /// <summary>Checks the times and <c>f_max</c>; returns <c>N_K</c>, <c>N_H</c> and <c>f_max·√(4πD)·γ</c>.</summary>
    private static (int Nk, int Nh, double Scale) BaluevSetup(ReadOnlySpan<double> times, double maxFrequency, bool center)
    {
        var (d, h) = center ? (3, 1) : (2, 0);
        int n = times.Length;
        if (n < d + 1)
            throw new ArgumentException($"times must have at least {d + 1} values", nameof(times));
        double lo = double.PositiveInfinity, hi = double.NegativeInfinity, sum = 0;
        foreach (double t in times)
        {
            if (!double.IsFinite(t)) throw new ArgumentException("times must be finite", nameof(times));
            lo = Math.Min(lo, t);
            hi = Math.Max(hi, t);
            sum += t;
        }
        if (!(hi - lo > 0))
            throw new ArgumentException("times must not all be equal", nameof(times));
        Check.PositiveFinite(maxFrequency, nameof(maxFrequency));
        int nk = n - d, nh = n - h;
        double mean = sum / n, ss = 0;
        foreach (double t in times)
            ss += (t - mean) * (t - mean);
        double var = ss / n;
        var (k, r) = nh % 2 == 0 ? (2, 1 / Math.Sqrt(Math.PI)) : (3, Math.Sqrt(Math.PI) / 2);
        for (; k < nh; k += 2)
            r = r * k / (k - 1);
        double gamma = Math.Sqrt(2.0 / nh) * r;
        return (nk, nh, maxFrequency * Math.Sqrt(4 * Math.PI * var) * gamma);
    }

    /// <summary>The Baluev value at <paramref name="z"/> for the numbers from <see cref="BaluevSetup"/>.</summary>
    private static double Baluev(double z, int nk, int nh, double scale)
    {
        double p1 = Math.Pow(1 - z, nk / 2.0);
        if (p1 == 1)
            return 1.0;
        double tau = scale * Math.Pow(1 - z, (nk - 1) / 2.0);
        tau *= Math.Sqrt(nh * z / 2);
        return -ExpM1(LogP1(-p1) - tau);
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
    internal static double LogP1(double x)
    {
        double u = 1 + x;
        return u == 1 ? x : Math.Log(u) * x / (u - 1);
    }

    /// <summary>exp(x) − 1, accurate for small x (Kahan's form).</summary>
    internal static double ExpM1(double x)
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

    /// <summary>
    /// Mean PSD of the loaded <paramref name="band"/> outside the <paramref name="notch"/> over the
    /// mean PSD in the notch, each by the <see cref="ChannelPower"/> rule (conventions: Spectra,
    /// Noise power ratio; ADR 0118).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The loaded band's edges in Hz.</param>
    /// <param name="notch">The notch's edges in Hz, strictly inside the band.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The two densities and the ratio.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum, or the loaded band has no power.</exception>
    public static NoisePowerRatio NoisePowerRatio(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High) band, (double Low, double High) notch, (double Low, double High)? span = null)
    {
        if (!(double.IsFinite(band.Low) && double.IsFinite(band.High) && double.IsFinite(notch.Low) && double.IsFinite(notch.High)))
            throw new ArgumentException("band and notch edges must be finite", nameof(band));
        if (!(band.Low < notch.Low && notch.Low < notch.High && notch.High < band.High))
            throw new ArgumentException("need band low < notch low < notch high < band high", nameof(notch));
        var (power, left, right) = Bins(frequencies, psd, span);
        double slack = 0; // as for Acpr
        for (int k = 0; k < power.Length; k++)
            slack = Math.Max(slack, 1e-9 * (right[k] - left[k]));
        if (band.Low < left[0] - slack || band.High > right[^1] + slack)
            throw new ArgumentException($"band [{band.Low}, {band.High}] leaves the spectrum [{left[0]}, {right[^1]}]", nameof(band));

        double Channel(double low, double high)
        {
            double sum = 0;
            for (int k = 0; k < power.Length; k++)
                sum += power[k] * Math.Max(Math.Min(right[k], high) - Math.Max(left[k], low), 0.0) / (right[k] - left[k]);
            return sum;
        }

        double loaded = (Channel(band.Low, notch.Low) + Channel(notch.High, band.High))
            / ((notch.Low - band.Low) + (band.High - notch.High));
        if (!(loaded > 0))
            throw new ArgumentException("the loaded band has no power", nameof(psd));
        double inside = Channel(notch.Low, notch.High) / (notch.High - notch.Low);
        double npr = inside == 0 ? double.PositiveInfinity : 10 * (Math.Log10(loaded) - Math.Log10(inside));
        return new NoisePowerRatio(loaded, inside, npr);
    }

    /// <summary>
    /// The span between the first points either side of the peak where the PSD has fallen
    /// <paramref name="dropDb"/> below it, interpolated linearly in power between bins
    /// (conventions: Spectra, x dB bandwidth; ADR 0122).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="dropDb">How far below the peak, in dB; finite and positive.</param>
    /// <param name="band">Only bins whose centers lie in it take part; null for all.</param>
    /// <returns>The peak and the two edges.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, the band has no bin or no power, or the PSD does not fall that far on a side.</exception>
    public static DbBandwidth DbBandwidth(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double dropDb,
        (double Low, double High)? band = null)
    {
        if (!(double.IsFinite(dropDb) && dropDb > 0))
            throw new ArgumentOutOfRangeException(nameof(dropDb), "drop_db must be finite and positive");
        Bins(frequencies, psd, null);
        int first = 0, last = frequencies.Length - 1;
        if (band is { } b)
        {
            if (!(double.IsFinite(b.Low) && double.IsFinite(b.High)))
                throw new ArgumentException("band must be (low, high) with finite edges", nameof(band));
            if (!(b.Low < b.High))
                throw new ArgumentException("band low must be below band high", nameof(band));
            first = -1;
            for (int i = 0; i < frequencies.Length; i++)
            {
                if (frequencies[i] >= b.Low && frequencies[i] <= b.High)
                {
                    if (first < 0)
                        first = i;
                    last = i;
                }
            }
            if (first < 0)
                throw new ArgumentException("no bin lies in the band", nameof(band));
        }
        int k = first;
        for (int i = first + 1; i <= last; i++)
        {
            if (psd[i] > psd[k])
                k = i;
        }
        double peak = psd[k];
        if (!(peak > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        double t = peak * Math.Pow(10, -dropDb / 10);
        double delta = (frequencies[^1] - frequencies[0]) / (frequencies.Length - 1);

        double Edge(ReadOnlySpan<double> f, ReadOnlySpan<double> p, int step)
        {
            for (int i = k + step; i >= first && i <= last; i += step)
            {
                if (p[i] <= t)
                {
                    int j = i - step; // the neighbour towards the peak, above t
                    return f[i] - step * ((t - p[i]) / (p[j] - p[i])) * delta;
                }
            }
            throw new ArgumentException($"the PSD does not fall {dropDb} dB below the peak within the band", nameof(psd));
        }

        double lower = Edge(frequencies, psd, -1), upper = Edge(frequencies, psd, +1);
        return new DbBandwidth(frequencies[k], peak, lower, upper, upper - lower);
    }

    /// <summary>The band's edges, checked as for ACPR's channels; the whole spectrum when null.</summary>
    private static (double Low, double High) BandEdges((double Low, double High)? band, double[] left, double[] right)
    {
        if (band is not { } b)
            return (left[0], right[^1]);
        if (!(double.IsFinite(b.Low) && double.IsFinite(b.High)))
            throw new ArgumentException("band must be (low, high) with finite edges", nameof(band));
        if (!(b.Low < b.High))
            throw new ArgumentException("band low must be below band high", nameof(band));
        double slack = 0; // as for Acpr
        for (int k = 0; k < left.Length; k++)
            slack = Math.Max(slack, 1e-9 * (right[k] - left[k]));
        if (b.Low < left[0] - slack || b.High > right[^1] + slack)
            throw new ArgumentException($"band [{b.Low}, {b.High}] leaves the spectrum [{left[0]}, {right[^1]}]", nameof(band));
        return b;
    }

    /// <summary>
    /// Power, centroid and RMS bandwidth of the PSD taken as constant over each bin, integrated
    /// exactly over <paramref name="band"/> (the whole spectrum when null) (conventions: Spectra,
    /// Spectral centroid and RMS bandwidth; ADR 0121).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The power, the centroid and the RMS bandwidth.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum, or the band has no power.</exception>
    public static SpectralMoments SpectralMoments(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        int n = power.Length;
        double[] a = new double[n], b = new double[n], d = new double[n];
        double total = 0, first = 0;
        for (int k = 0; k < n; k++)
        {
            a[k] = Math.Max(left[k], lo);
            b[k] = Math.Min(right[k], hi);
            if (!(b[k] > a[k]))
                continue;
            d[k] = power[k] / (right[k] - left[k]);
            total += d[k] * (b[k] - a[k]);
            first += d[k] * (b[k] - a[k]) * (a[k] + b[k]) / 2;
        }
        if (!(total > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        double c = first / total, second = 0;
        for (int k = 0; k < n; k++)
        {
            if (b[k] > a[k])
                second += d[k] * (Math.Pow(b[k] - c, 3) - Math.Pow(a[k] - c, 3)) / 3;
        }
        return new SpectralMoments(total, c, Math.Sqrt(Math.Max(second / total, 0)));
    }

    /// <summary>
    /// The frequency below which <paramref name="fraction"/> of the band's power lies, the PSD
    /// taken as constant over each bin (conventions: Spectra, Spectral rolloff; ADR 0124).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="fraction">The share of the band's power, finite, in (0, 1].</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The rolloff frequency in Hz.</returns>
    /// <exception cref="ArgumentException">The fraction is out of range, an edge is out of order or not finite, the band leaves the spectrum, or the band has no power.</exception>
    public static double SpectralRolloff(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double fraction,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        if (!(double.IsFinite(fraction) && fraction > 0 && fraction <= 1))
            throw new ArgumentOutOfRangeException(nameof(fraction), "fraction must be in (0, 1]");
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        int n = power.Length;
        double[] a = new double[n], b = new double[n], d = new double[n], piece = new double[n];
        double total = 0;
        for (int k = 0; k < n; k++)
        {
            a[k] = Math.Max(left[k], lo);
            b[k] = Math.Min(right[k], hi);
            if (!(b[k] > a[k]))
                continue;
            d[k] = power[k] / (right[k] - left[k]);
            piece[k] = d[k] * (b[k] - a[k]);
            total += piece[k];
        }
        if (!(total > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        double target = fraction * total, running = 0;
        int last = -1;
        for (int k = 0; k < n; k++)
        {
            if (!(b[k] > a[k]))
                continue;
            if (piece[k] > 0)
                last = k;
            double after = running + piece[k];
            if (after >= target)
                return Math.Min(Math.Max(a[k] + (target - running) / d[k], a[k]), b[k]);
            running = after;
        }
        return b[last]; // rounding left the running sum short of 1·power
    }

    /// <summary>
    /// Skewness and kurtosis of the PSD taken as constant over each bin, integrated exactly about
    /// the centroid over <paramref name="band"/> (the whole spectrum when null) (conventions:
    /// Spectra, Spectral skewness and kurtosis; ADR 0126).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The skewness and the kurtosis.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum, or the band has no power or no spread.</exception>
    public static SpectralShape SpectralShape(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        int n = power.Length;
        double[] a = new double[n], b = new double[n], d = new double[n];
        double total = 0, first = 0;
        for (int k = 0; k < n; k++)
        {
            a[k] = Math.Max(left[k], lo);
            b[k] = Math.Min(right[k], hi);
            if (!(b[k] > a[k]))
                continue;
            d[k] = power[k] / (right[k] - left[k]);
            total += d[k] * (b[k] - a[k]);
            first += d[k] * (b[k] - a[k]) * (a[k] + b[k]) / 2;
        }
        if (!(total > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        double c = first / total, m2 = 0, m3 = 0, m4 = 0;
        for (int k = 0; k < n; k++)
        {
            if (!(b[k] > a[k]))
                continue;
            double u = b[k] - c, v = a[k] - c;
            m2 += d[k] * (Math.Pow(u, 3) - Math.Pow(v, 3)) / 3;
            m3 += d[k] * (Math.Pow(u, 4) - Math.Pow(v, 4)) / 4;
            m4 += d[k] * (Math.Pow(u, 5) - Math.Pow(v, 5)) / 5;
        }
        m2 /= total;
        m3 /= total;
        m4 /= total;
        if (!(m2 > 0))
            throw new ArgumentException("the band has no spread", nameof(psd));
        return new SpectralShape(m3 / Math.Pow(m2, 1.5), m4 / (m2 * m2));
    }

    /// <summary>
    /// The continuous least-squares line through the PSD, taken as constant over each bin (in dB
    /// with <paramref name="db"/>), over <paramref name="band"/> (the whole spectrum when null)
    /// (conventions: Spectra, Spectral slope; ADR 0127).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <param name="db">Fit 10·log10 of the PSD instead of the PSD.</param>
    /// <returns>The band's centre, the line's level there and its slope.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum, the band has no power, or with <paramref name="db"/> a bin in the band is zero.</exception>
    public static SpectralSlope SpectralSlope(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null, bool db = false)
    {
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        double center = (lo + hi) / 2, width = hi - lo, total = 0, sum = 0, moment = 0;
        bool zero = false;
        for (int k = 0; k < power.Length; k++)
        {
            double a = Math.Max(left[k], lo), b = Math.Min(right[k], hi);
            if (!(b > a))
                continue;
            double d = power[k] / (right[k] - left[k]);
            total += d * (b - a);
            if (d == 0)
                zero = true;
            double y = db ? 10 * Math.Log10(d) : d;
            sum += y * (b - a);
            moment += y * ((b - center) * (b - center) - (a - center) * (a - center)) / 2;
        }
        if (!(total > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        if (db && zero)
            throw new ArgumentException("with db, every bin in the band must have a positive PSD", nameof(psd));
        return new SpectralSlope(center, sum / width, moment / (width * width * width / 12));
    }

    /// <summary>
    /// How fast the PSD falls from the band's first bin: each later piece's change in density
    /// over its distance in bins, weighted by width, over the later pieces' power (conventions:
    /// Spectra, Spectral decrease; ADR 0130).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The decrease, dimensionless: 0 for a flat PSD, negative for a falling one.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum or holds fewer than two bins, or it has no power after its first bin.</exception>
    public static double SpectralDecrease(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        double step = frequencies[1] - frequencies[0];
        var pieces = new List<(double W, double M, double D)>();
        for (int k = 0; k < power.Length; k++)
        {
            double a = Math.Max(left[k], lo), b = Math.Min(right[k], hi);
            if (b > a)
                pieces.Add((b - a, (a + b) / 2, power[k] / (right[k] - left[k])));
        }
        if (pieces.Count < 2)
            throw new ArgumentException("the band must hold at least two bins", nameof(band));
        var first = pieces[0];
        double rest = 0, sum = 0;
        for (int k = 1; k < pieces.Count; k++)
        {
            var (w, m, d) = pieces[k];
            rest += d * w;
            sum += (d - first.D) * w * step / (m - first.M);
        }
        if (!(rest > 0))
            throw new ArgumentException("the band has no power after its first bin", nameof(psd));
        return sum / rest;
    }

    /// <summary>
    /// The vertex of the parabola through the peak bin <paramref name="index"/> and its two
    /// neighbours (conventions: Spectra, Peak interpolation; ADR 0136).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="index">The peak bin, 1 to n − 2, not lower than either neighbour.</param>
    /// <param name="scale">The scale the parabola is fitted on.</param>
    /// <returns>The vertex's frequency, height and offset.</returns>
    /// <exception cref="ArgumentException">The arrays are invalid, the bin is at an edge, lower than a neighbour or flat with both, a dB value is not positive, or <paramref name="scale"/> is unknown.</exception>
    public static PeakEstimate InterpolatePeak(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, int index, PeakScale scale = PeakScale.Decibel)
    {
        if (scale is not (PeakScale.Decibel or PeakScale.Linear))
            throw new ArgumentOutOfRangeException(nameof(scale), "unknown scale");
        Bins(frequencies, psd, null);
        int n = psd.Length;
        if (index < 1 || index > n - 2)
            throw new ArgumentOutOfRangeException(nameof(index), "index must be an interior bin, 1 <= index <= n - 2");
        if (psd[index] < psd[index - 1] || psd[index] < psd[index + 1])
            throw new ArgumentException("the bin at index must not be lower than its neighbours", nameof(index));
        if (scale == PeakScale.Decibel && !(Math.Min(psd[index - 1], Math.Min(psd[index], psd[index + 1])) > 0))
            throw new ArgumentException("the three bins must be positive on the dB scale", nameof(psd));
        return Vertex(frequencies, psd, index, scale)
            ?? throw new ArgumentException("the three bins are flat", nameof(psd));
    }

    /// <summary>The parabola's vertex through bins <c>k − 1, k, k + 1</c>, or null where it is undefined.</summary>
    private static PeakEstimate? Vertex(ReadOnlySpan<double> f, ReadOnlySpan<double> psd, int k, PeakScale scale)
    {
        double a = psd[k - 1], b = psd[k], c = psd[k + 1];
        if (scale == PeakScale.Decibel)
        {
            if (!(Math.Min(a, Math.Min(b, c)) > 0))
                return null;
            a = 10 * Math.Log10(a);
            b = 10 * Math.Log10(b);
            c = 10 * Math.Log10(c);
        }
        double curve = a - 2 * b + c;
        if (!(curve < 0))
            return null;
        double offset = (a - c) / (2 * curve);
        double vertex = b - (a - c) * offset / 4;
        double delta = (f[^1] - f[0]) / (f.Length - 1);
        double height = scale == PeakScale.Decibel ? Math.Pow(10, vertex / 10) : vertex;
        return new PeakEstimate(f[k] + offset * delta, height, offset);
    }

    /// <summary>
    /// Each spectral peak's width where the PSD crosses height − relHeight·prominence,
    /// interpolated linearly between bins; in order of frequency (conventions: Spectra, Peak
    /// widths; ADR 0138).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="relHeight">How far down the prominence the width is taken, in (0, 1].</param>
    /// <param name="minProminence">The least prominence kept, finite and non-negative.</param>
    /// <returns>One width per peak, lowest frequency first.</returns>
    /// <exception cref="ArgumentException">The arrays are invalid, <paramref name="relHeight"/> is outside (0, 1], or <paramref name="minProminence"/> is negative or not finite.</exception>
    public static IReadOnlyList<PeakWidth> PeakWidths(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double relHeight = 0.5, double minProminence = 0)
    {
        if (!(relHeight > 0 && relHeight <= 1))
            throw new ArgumentOutOfRangeException(nameof(relHeight), "relHeight must be in (0, 1]");
        var peaks = SpectralPeaks(frequencies, psd, minProminence);
        int n = psd.Length;
        double delta = (frequencies[n - 1] - frequencies[0]) / (n - 1);
        var widths = new List<PeakWidth>();
        foreach (var p in peaks)
        {
            double level = p.Height - relHeight * p.Prominence;
            int i = p.Index, j = p.Index;
            while (psd[i - 1] == p.Height)
                i--;
            while (psd[j + 1] == p.Height)
                j++;
            int k = i;
            while (k > 0 && psd[k] > level)
                k--;
            double lo = psd[k] <= level ? k + (level - psd[k]) / (psd[k + 1] - psd[k]) : k;
            k = j;
            while (k < n - 1 && psd[k] > level)
                k++;
            double hi = psd[k] <= level ? k - (level - psd[k]) / (psd[k - 1] - psd[k]) : k;
            double left = frequencies[0] + lo * delta, right = frequencies[0] + hi * delta;
            widths.Add(new PeakWidth(p.Index, level, left, right, right - left));
        }
        return widths;
    }

    /// <summary>
    /// The <paramref name="count"/> most prominent spectral peaks, each with its frequency and
    /// height interpolated on <paramref name="scale"/>; most prominent first, ties to the lower
    /// frequency (conventions: Spectra, Find tones; ADR 0137).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="count">How many tones at most, at least 1.</param>
    /// <param name="minProminence">The least prominence kept, finite and non-negative.</param>
    /// <param name="scale">The scale each peak's parabola is fitted on.</param>
    /// <returns>The tones, most prominent first.</returns>
    /// <exception cref="ArgumentException">The arrays are invalid, <paramref name="count"/> is below 1, <paramref name="minProminence"/> is negative or not finite, or <paramref name="scale"/> is unknown.</exception>
    public static IReadOnlyList<Tone> FindTones(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, int count, double minProminence = 0, PeakScale scale = PeakScale.Decibel)
    {
        if (scale is not (PeakScale.Decibel or PeakScale.Linear))
            throw new ArgumentOutOfRangeException(nameof(scale), "unknown scale");
        ArgumentOutOfRangeException.ThrowIfLessThan(count, 1);
        var ranked = SpectralPeaks(frequencies, psd, minProminence).OrderByDescending(p => p.Prominence).Take(count);
        var tones = new List<Tone>();
        foreach (var p in ranked)
        {
            var v = Vertex(frequencies, psd, p.Index, scale);
            tones.Add(v is null
                ? new Tone(p.Index, p.Frequency, p.Height, p.Prominence)
                : new Tone(p.Index, v.Frequency, v.Height, p.Prominence));
        }
        return tones;
    }

    /// <summary>
    /// The PSD's local maxima with their prominence, in order of frequency; a plateau is one
    /// peak, and the first and last bins are never peaks (conventions: Spectra, Spectral peaks;
    /// ADR 0135).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="minProminence">The least prominence kept, finite and non-negative.</param>
    /// <returns>The peaks, lowest frequency first.</returns>
    /// <exception cref="ArgumentException">The arrays are invalid, or <paramref name="minProminence"/> is negative or not finite.</exception>
    public static IReadOnlyList<SpectralPeak> SpectralPeaks(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double minProminence = 0)
    {
        if (!(double.IsFinite(minProminence) && minProminence >= 0))
            throw new ArgumentOutOfRangeException(nameof(minProminence), "minProminence must be finite and >= 0");
        Bins(frequencies, psd, null);
        int n = psd.Length;
        var peaks = new List<SpectralPeak>();
        int i = 1;
        while (i < n - 1)
        {
            int j = i;
            while (j + 1 < n && psd[j + 1] == psd[i])
                j++;
            double h = psd[i];
            if (psd[i - 1] < h && j < n - 1 && psd[j + 1] < h)
            {
                double left = h, right = h;
                for (int k = i; k >= 0 && psd[k] <= h; k--)
                    left = Math.Min(left, psd[k]);
                for (int k = j; k < n && psd[k] <= h; k++)
                    right = Math.Min(right, psd[k]);
                double prominence = h - Math.Max(left, right);
                if (prominence >= minProminence)
                    peaks.Add(new SpectralPeak((i + j) / 2, (frequencies[i] + frequencies[j]) / 2, h, prominence));
            }
            i = j + 1;
        }
        return peaks;
    }

    /// <summary>
    /// The PSD's power above <paramref name="split"/> over its power below, the PSD taken as
    /// constant over each bin, over <paramref name="band"/> (the whole spectrum when null)
    /// (conventions: Spectra, Band energy ratio; ADR 0134).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="split">The split frequency in Hz, strictly inside the band.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The low and high powers, their ratio and its dB.</returns>
    /// <exception cref="ArgumentException">The split is not finite or not inside the band, an edge is out of order or not finite, the band leaves the spectrum, or it has no power.</exception>
    public static BandEnergyRatio BandEnergyRatio(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double split,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        if (!double.IsFinite(split))
            throw new ArgumentOutOfRangeException(nameof(split), "split must be a finite number");
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        if (!(lo < split && split < hi))
            throw new ArgumentOutOfRangeException(nameof(split), "split must be strictly inside the band");
        double low = 0, high = 0;
        for (int k = 0; k < power.Length; k++)
        {
            double d = power[k] / (right[k] - left[k]);
            low += d * Math.Max(Math.Min(right[k], split) - Math.Max(left[k], lo), 0);
            high += d * Math.Max(Math.Min(right[k], hi) - Math.Max(left[k], split), 0);
        }
        if (!(low + high > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        if (low == 0)
            return new BandEnergyRatio(low, high, double.PositiveInfinity, double.PositiveInfinity);
        if (high == 0)
            return new BandEnergyRatio(low, high, 0, double.NegativeInfinity);
        return new BandEnergyRatio(low, high, high / low, 10 * Math.Log10(high / low));
    }

    /// <summary>
    /// The mean PSD over the loudest and the quietest <paramref name="fraction"/> of the band's
    /// width, and their ratio in dB, the PSD taken as constant over each bin, over
    /// <paramref name="band"/> (the whole spectrum when null) (conventions: Spectra, Spectral
    /// contrast; ADR 0133).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <param name="fraction">The share of the band's width for the peak and for the valley, in (0, 1/2].</param>
    /// <returns>The peak, the valley and the contrast in dB.</returns>
    /// <exception cref="ArgumentException">The fraction is out of range, an edge is out of order or not finite, the band leaves the spectrum, or it has no power.</exception>
    public static SpectralContrast SpectralContrast(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null, double fraction = 0.2)
    {
        if (!(double.IsFinite(fraction) && fraction > 0 && fraction <= 0.5))
            throw new ArgumentOutOfRangeException(nameof(fraction), "fraction must be in (0, 1/2]");
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        var pieces = new List<(double W, double D)>();
        double total = 0, sum = 0;
        for (int k = 0; k < power.Length; k++)
        {
            double a = Math.Max(left[k], lo), b = Math.Min(right[k], hi);
            if (!(b > a))
                continue;
            double d = power[k] / (right[k] - left[k]);
            pieces.Add((b - a, d));
            total += d * (b - a);
            sum += b - a;
        }
        if (!(total > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        double width = fraction * sum;
        var up = pieces.Select((p, i) => (p, i)).OrderBy(t => t.p.D).ThenBy(t => t.i).Select(t => t.p).ToList();
        var down = Enumerable.Range(0, up.Count).Select(i => up[up.Count - 1 - i]);
        double peak = Fill(down, width), valley = Fill(up, width);
        double db = valley == 0 ? double.PositiveInfinity : 10 * Math.Log10(peak / valley);
        return new SpectralContrast(peak, valley, db);
    }

    private static double Fill(IEnumerable<(double W, double D)> pieces, double width)
    {
        double taken = 0, acc = 0;
        foreach (var (w, d) in pieces)
        {
            double t = Math.Min(w, width - taken);
            if (!(t > 0))
                break;
            acc += t * d;
            taken += t;
        }
        return acc / width;
    }

    /// <summary>
    /// The differential entropy of the PSD, taken as constant over each bin and normalized to
    /// unit power, over <paramref name="band"/> (the whole spectrum when null) (conventions:
    /// Spectra, Spectral entropy; ADR 0128).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The entropy, the entropy bandwidth and its share of the band.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum, or the band has no power.</exception>
    public static SpectralEntropy SpectralEntropy(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        int n = power.Length;
        double[] a = new double[n], b = new double[n], d = new double[n];
        double total = 0;
        for (int k = 0; k < n; k++)
        {
            a[k] = Math.Max(left[k], lo);
            b[k] = Math.Min(right[k], hi);
            if (!(b[k] > a[k]))
                continue;
            d[k] = power[k] / (right[k] - left[k]);
            total += d[k] * (b[k] - a[k]);
        }
        if (!(total > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        double h = 0;
        for (int k = 0; k < n; k++)
        {
            if (!(b[k] > a[k] && d[k] > 0))
                continue;
            double p = d[k] / total;
            h -= p * (b[k] - a[k]) * Math.Log(p);
        }
        double width = Math.Exp(h);
        return new SpectralEntropy(h, width, width / (hi - lo));
    }

    /// <summary>
    /// The L2 distance between two PSD frames taken as constant over each bin, over
    /// <paramref name="band"/> (the whole spectrum when null); each frame scaled to unit power
    /// with <paramref name="normalize"/>, only rises counted with <paramref name="rectify"/>
    /// (conventions: Spectra, Spectral flux; ADR 0129).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="previous">The earlier frame's PSD per bin, finite and non-negative.</param>
    /// <param name="current">The later frame's PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <param name="normalize">Scale each frame to unit power over the band first.</param>
    /// <param name="rectify">Count only the bins where the PSD rose.</param>
    /// <returns>sqrt(∫ Δ² df) over the band.</returns>
    /// <exception cref="ArgumentException">A frame is invalid, an edge is out of order or not finite, the band leaves the spectrum, or with <paramref name="normalize"/> a frame has no power in the band.</exception>
    public static double SpectralFlux(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> previous, ReadOnlySpan<double> current,
        (double Low, double High)? band = null, (double Low, double High)? span = null, bool normalize = true, bool rectify = true)
    {
        var (p0, left, right) = Bins(frequencies, previous, span);
        var (p1, _, _) = Bins(frequencies, current, span);
        var (lo, hi) = BandEdges(band, left, right);
        int n = p0.Length;
        double total0 = 0, total1 = 0;
        for (int k = 0; k < n; k++)
        {
            double a = Math.Max(left[k], lo), b = Math.Min(right[k], hi);
            if (!(b > a))
                continue;
            double width = right[k] - left[k];
            total0 += p0[k] / width * (b - a);
            total1 += p1[k] / width * (b - a);
        }
        if (normalize && !(total0 > 0 && total1 > 0))
            throw new ArgumentException("with normalize, each frame needs power in the band", nameof(previous));
        double s0 = normalize ? total0 : 1, s1 = normalize ? total1 : 1, sum = 0;
        for (int k = 0; k < n; k++)
        {
            double a = Math.Max(left[k], lo), b = Math.Min(right[k], hi);
            if (!(b > a))
                continue;
            double width = right[k] - left[k];
            double delta = p1[k] / width / s1 - p0[k] / width / s0;
            if (rectify)
                delta = Math.Max(delta, 0);
            sum += delta * delta * (b - a);
        }
        return Math.Sqrt(sum);
    }

    /// <summary>
    /// One minus the normalized correlation of two PSD frames taken as constant over each bin,
    /// over <paramref name="band"/> (the whole spectrum when null) (conventions: Spectra,
    /// Spectral variation; ADR 0131).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="previous">The earlier frame's PSD per bin, finite and non-negative.</param>
    /// <param name="current">The later frame's PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The variation, in [0, 1]: 0 for the same shape, 1 for frames sharing no band.</returns>
    /// <exception cref="ArgumentException">A frame is invalid or has no power in the band, an edge is out of order or not finite, or the band leaves the spectrum.</exception>
    public static double SpectralVariation(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> previous, ReadOnlySpan<double> current,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        var (p0, left, right) = Bins(frequencies, previous, span);
        var (p1, _, _) = Bins(frequencies, current, span);
        var (lo, hi) = BandEdges(band, left, right);
        double total0 = 0, total1 = 0, cross = 0, sq0 = 0, sq1 = 0;
        for (int k = 0; k < p0.Length; k++)
        {
            double a = Math.Max(left[k], lo), b = Math.Min(right[k], hi);
            if (!(b > a))
                continue;
            double w = b - a, d0 = p0[k] / (right[k] - left[k]), d1 = p1[k] / (right[k] - left[k]);
            total0 += d0 * w;
            total1 += d1 * w;
            cross += d0 * d1 * w;
            sq0 += d0 * d0 * w;
            sq1 += d1 * d1 * w;
        }
        if (!(total0 > 0 && total1 > 0))
            throw new ArgumentException("each frame needs power in the band", nameof(previous));
        return 1 - cross / Math.Sqrt(sq0 * sq1);
    }

    /// <summary>
    /// How jagged the PSD is from bin to bin: the squared jumps between neighbouring pieces, each
    /// weighted by the two pieces' mean width, over the PSD's squared norm, over
    /// <paramref name="band"/> (the whole spectrum when null) (conventions: Spectra, Spectral
    /// irregularity; ADR 0132).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The irregularity, dimensionless: 0 for a flat PSD.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum or holds fewer than two bins, or it has no power.</exception>
    public static double SpectralIrregularity(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        var pieces = new List<(double W, double D)>();
        for (int k = 0; k < power.Length; k++)
        {
            double a = Math.Max(left[k], lo), b = Math.Min(right[k], hi);
            if (b > a)
                pieces.Add((b - a, power[k] / (right[k] - left[k])));
        }
        if (pieces.Count < 2)
            throw new ArgumentException("the band must hold at least two bins", nameof(band));
        double total = 0, norm = 0, jumps = 0;
        for (int k = 0; k < pieces.Count; k++)
        {
            var (w, d) = pieces[k];
            total += d * w;
            norm += d * d * w;
            if (k + 1 < pieces.Count)
            {
                double step = pieces[k + 1].D - d;
                jumps += step * step * (w + pieces[k + 1].W) / 2;
            }
        }
        if (!(total > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        return jumps / norm;
    }

    /// <summary>
    /// The PSD's geometric mean over its arithmetic mean across <paramref name="band"/> (the whole
    /// spectrum when null), each bin weighted by its overlap with the band (conventions: Spectra,
    /// Spectral flatness; ADR 0120).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The two means, the flatness and the flatness in dB.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum, or the band has no power.</exception>
    public static SpectralFlatness SpectralFlatness(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        double total = 0, sum = 0, logSum = 0;
        bool zero = false;
        for (int k = 0; k < power.Length; k++)
        {
            double w = Math.Max(Math.Min(right[k], hi) - Math.Max(left[k], lo), 0.0);
            if (!(w > 0))
                continue;
            double d = power[k] / (right[k] - left[k]);
            total += w;
            sum += w * d;
            if (d == 0)
                zero = true;
            else
                logSum += w * Math.Log(d);
        }
        double arith = sum / total;
        if (!(arith > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        if (zero)
            return new SpectralFlatness(0, arith, 0, double.NegativeInfinity);
        double geo = Math.Exp(logSum / total);
        return new SpectralFlatness(geo, arith, geo / arith, 10 * (Math.Log10(geo) - Math.Log10(arith)));
    }

    /// <summary>
    /// The PSD's peak over its mean across <paramref name="band"/> (the whole spectrum when null),
    /// the mean weighted by each bin's overlap with the band (conventions: Spectra, Spectral crest
    /// factor; ADR 0125).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="band">The band's edges in Hz, or null for the whole spectrum.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <returns>The peak, the mean, the crest and the crest in dB.</returns>
    /// <exception cref="ArgumentException">An edge is out of order or not finite, the band leaves the spectrum, or the band has no power.</exception>
    public static SpectralCrest SpectralCrest(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd,
        (double Low, double High)? band = null, (double Low, double High)? span = null)
    {
        var (power, left, right) = Bins(frequencies, psd, span);
        var (lo, hi) = BandEdges(band, left, right);
        double total = 0, sum = 0, peak = 0;
        for (int k = 0; k < power.Length; k++)
        {
            double w = Math.Max(Math.Min(right[k], hi) - Math.Max(left[k], lo), 0.0);
            if (!(w > 0))
                continue;
            double d = power[k] / (right[k] - left[k]);
            total += w;
            sum += w * d;
            peak = Math.Max(peak, d);
        }
        double mean = sum / total;
        if (!(mean > 0))
            throw new ArgumentException("the band has no power", nameof(psd));
        return new SpectralCrest(peak, mean, peak / mean, 10 * (Math.Log10(peak) - Math.Log10(mean)));
    }

    /// <summary>
    /// ACPR with every channel weighted by a root-raised-cosine filter's |H(f)|² (peak 1, roll-off
    /// <paramref name="alpha"/>, at <paramref name="symbolRate"/>), each bin's power weighted at
    /// its center (conventions: Spectra, ACPR; ADR 0111).
    /// </summary>
    /// <param name="frequencies">Bin centers in Hz, ascending and evenly spaced.</param>
    /// <param name="psd">PSD per bin, finite and non-negative.</param>
    /// <param name="center">Main channel center in Hz.</param>
    /// <param name="symbolRate">The filter's symbol rate in Hz, positive.</param>
    /// <param name="alpha">The filter's roll-off, in (0, 1].</param>
    /// <param name="offsets">Center-to-center offsets in Hz, at least one, each positive.</param>
    /// <param name="span">Clips the outer bins, as for <see cref="OccupiedBandwidth"/>.</param>
    /// <exception cref="ArgumentException">A channel leaves the spectrum, or the main channel has no power.</exception>
    public static Acpr AcprRrc(ReadOnlySpan<double> frequencies, ReadOnlySpan<double> psd, double center, double symbolRate,
        double alpha, ReadOnlySpan<double> offsets, (double Low, double High)? span = null)
    {
        Check.Finite(center, nameof(center));
        double rs = Check.PositiveFinite(symbolRate, nameof(symbolRate));
        if (!(alpha > 0 && alpha <= 1))
            throw new ArgumentOutOfRangeException(nameof(alpha), alpha, "alpha must be in (0, 1]");
        if (offsets.IsEmpty)
            throw new ArgumentException("at least one offset required", nameof(offsets));
        foreach (double o in offsets)
            Check.PositiveFinite(o, nameof(offsets));
        var (power, left, right) = Bins(frequencies, psd, span);
        double[] f = frequencies.ToArray();
        double slack = 0; // rounding in center ± offset ± support
        for (int k = 0; k < power.Length; k++)
            slack = Math.Max(slack, 1e-9 * (right[k] - left[k]));
        double flat = (1 - alpha) * rs / 2, edge = (1 + alpha) * rs / 2;

        double Channel(double at, string param)
        {
            if (at - edge < left[0] - slack || at + edge > right[^1] + slack)
                throw new ArgumentException($"channel [{at - edge}, {at + edge}] leaves the spectrum [{left[0]}, {right[^1]}]", param);
            double sum = 0;
            for (int k = 0; k < power.Length; k++)
            {
                double x = Math.Abs(f[k] - at);
                double g = x <= flat ? 1 : x < edge ? 0.5 * (1 + Math.Cos(Math.PI * (x - flat) / (alpha * rs))) : 0;
                sum += power[k] * g;
            }
            return sum;
        }

        double main = Channel(center, nameof(center));
        if (!(main > 0))
            throw new ArgumentException("the main channel has no power", nameof(psd));
        int n = offsets.Length;
        double[] lower = new double[n], upper = new double[n], lowerDbc = new double[n], upperDbc = new double[n];
        for (int i = 0; i < n; i++)
        {
            lower[i] = Channel(center - offsets[i], nameof(offsets));
            upper[i] = Channel(center + offsets[i], nameof(offsets));
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
