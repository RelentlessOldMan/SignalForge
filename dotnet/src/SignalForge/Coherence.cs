using System.Numerics;

namespace SignalForge;

/// <summary>Magnitude-squared coherence per bin, one-sided for real input, (conventions: Coherence; ADR 0192).</summary>
/// <param name="Frequencies">Bin frequencies <c>k·fs/M</c>, <c>k = 0 … ⌊M/2⌋</c>; for complex
/// input, all <c>M</c> bins in shifted order (ADR 0196, ADR 0197).</param>
/// <param name="Values">The coherence in [0, 1] per bin; NaN where an auto-spectrum is 0.</param>
/// <param name="NumSegments">How many segments were averaged.</param>
public sealed record Coherence(double[] Frequencies, double[] Values, int NumSegments);

/// <summary>The output PSD split by the coherence (conventions: Coherent output power; ADR 0198).</summary>
/// <param name="Frequencies">The <c>WelchPsd</c> bin frequencies of the output.</param>
/// <param name="Coherent"><c>γ²·Pyy</c>, units²/Hz.</param>
/// <param name="Noncoherent"><c>Pyy − Coherent</c>, units²/Hz.</param>
/// <param name="NumSegments">How many segments were averaged.</param>
public sealed record CoherentOutputPower(double[] Frequencies, double[] Coherent, double[] Noncoherent, int NumSegments);

/// <summary>Welch cross-spectral density per bin, one-sided for real input, (conventions: Cross-spectral density;
/// ADR 0194).</summary>
/// <param name="Frequencies">Bin frequencies <c>k·fs/M</c>, <c>k = 0 … ⌊M/2⌋</c>; for complex
/// input, all <c>M</c> bins in shifted order (ADR 0196, ADR 0197).</param>
/// <param name="Csd">The cross-spectral density <c>Pxy</c>, units²/Hz.</param>
/// <param name="NumSegments">How many segments were averaged.</param>
public sealed record CrossSpectralDensity(double[] Frequencies, Complex[] Csd, int NumSegments);

/// <summary>H1 frequency-response estimate per bin, one-sided for real input, (conventions: Transfer function (H1);
/// ADR 0193).</summary>
/// <param name="Frequencies">Bin frequencies <c>k·fs/M</c>, <c>k = 0 … ⌊M/2⌋</c>; for complex
/// input, all <c>M</c> bins in shifted order (ADR 0196, ADR 0197).</param>
/// <param name="Response">The complex response from input to output; NaN where the input has no
/// power.</param>
/// <param name="NumSegments">How many segments were averaged.</param>
public sealed record TransferFunction(double[] Frequencies, Complex[] Response, int NumSegments);

public static partial class Spectral
{
    /// <summary><c>min(1, |Sxy|²/(Sxx·Syy))</c> over Welch's segments of <paramref name="x"/> and
    /// <paramref name="y"/>, NaN where an auto-spectrum is 0 (conventions: Coherence; ADR 0192).</summary>
    /// <param name="x">Real samples, finite.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the coherence and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Coherence Coherence(ReadOnlySpan<double> x, ReadOnlySpan<double> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        CoherenceOf(ToComplex(x), ToComplex(y), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: true);

    /// <summary>The coherence, for complex samples: all bins in shifted order (ADR 0197).</summary>
    /// <param name="x">Complex input samples, finite.</param>
    /// <param name="y">Complex output samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the coherence and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Coherence Coherence(ReadOnlySpan<Complex> x, ReadOnlySpan<Complex> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        CoherenceOf(x.ToArray(), y.ToArray(), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: false);

    private static Coherence CoherenceOf(Complex[] x, Complex[] y, double sampleRate, int? nperseg, int? noverlap,
        WindowType window, double? beta, Detrend detrend, int? nfft, bool oneSided)
    {
        var (g, sxy, sxx, syy) = CrossSegments(x, y, sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided);
        int m = sxx.Length;
        var values = new double[m];
        for (int k = 0; k < m; k++)
        {
            double d = sxx[k] * syy[k];
            double num = sxy[k].Real * sxy[k].Real + sxy[k].Imaginary * sxy[k].Imaginary;
            values[k] = d > 0 ? Math.Min(1.0, num / d) : double.NaN;
        }
        return new Coherence(g.Frequencies(oneSided), values, g.Count);
    }

    /// <summary>H1 = <c>Σ conj X·Y / Σ|X|²</c> over Welch's segments, from input
    /// <paramref name="x"/> to output <paramref name="y"/>; NaN where the input has no power
    /// (conventions: Transfer function (H1); ADR 0193).</summary>
    /// <param name="x">Real input samples, finite.</param>
    /// <param name="y">Real output samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the response and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static TransferFunction TransferFunction(ReadOnlySpan<double> x, ReadOnlySpan<double> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        TransferFunctionOf(ToComplex(x), ToComplex(y), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: true);

    /// <summary>The H1 estimate, for complex samples: all bins in shifted order (ADR 0197).</summary>
    /// <param name="x">Complex input samples, finite.</param>
    /// <param name="y">Complex output samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the response and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static TransferFunction TransferFunction(ReadOnlySpan<Complex> x, ReadOnlySpan<Complex> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        TransferFunctionOf(x.ToArray(), y.ToArray(), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: false);

    private static TransferFunction TransferFunctionOf(Complex[] x, Complex[] y, double sampleRate, int? nperseg, int? noverlap,
        WindowType window, double? beta, Detrend detrend, int? nfft, bool oneSided)
    {
        var (g, sxy, sxx, _) = CrossSegments(x, y, sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided);
        var response = new Complex[sxx.Length];
        for (int k = 0; k < response.Length; k++)
            response[k] = sxx[k] > 0 ? sxy[k] / sxx[k] : new Complex(double.NaN, double.NaN);
        return new TransferFunction(g.Frequencies(oneSided), response, g.Count);
    }

    /// <summary><c>Pxy = d·Σ conj X·Y / (K·fs·Σw²)</c> over Welch's segments, one-sided, scaled
    /// like <c>WelchPsd</c>
    /// (conventions: Cross-spectral density; ADR 0194).</summary>
    /// <param name="x">Real samples, finite.</param>
    /// <param name="y">Real samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <param name="oneSided">One-sided (doubled) bins when true; two-sided shifted bins when false
    /// (ADR 0196).</param>
    /// <returns>The frequencies, the cross-spectral density and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static CrossSpectralDensity CrossSpectralDensity(ReadOnlySpan<double> x, ReadOnlySpan<double> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null, bool oneSided = true) =>
        Csd(ToComplex(x), ToComplex(y), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided);

    /// <summary><c>Pxy = Σ conj X·Y / (K·fs·Σw²)</c> over Welch's segments of complex samples,
    /// two-sided in shifted order (conventions: Cross-spectral density; ADR 0196).</summary>
    /// <param name="x">Complex samples, finite.</param>
    /// <param name="y">Complex samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the cross-spectral density and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static CrossSpectralDensity CrossSpectralDensity(ReadOnlySpan<Complex> x, ReadOnlySpan<Complex> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        Csd(x.ToArray(), y.ToArray(), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: false);

    private static CrossSpectralDensity Csd(Complex[] x, Complex[] y, double sampleRate, int? nperseg, int? noverlap,
        WindowType window, double? beta, Detrend detrend, int? nfft, bool oneSided)
    {
        var (g, sxy, _, _) = CrossSegments(x, y, sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided);
        double scale = g.Scale / g.Count;
        int m = sxy.Length, last = g.Nfft % 2 == 0 ? m - 1 : m;
        var csd = new Complex[m];
        for (int k = 0; k < m; k++)
            csd[k] = sxy[k] * scale * (oneSided && k >= 1 && k < last ? 2.0 : 1.0);
        return new CrossSpectralDensity(g.Frequencies(oneSided), csd, g.Count);
    }

    /// <summary>H2 = <c>Σ|Y|² / Σ conj Y·X</c> over Welch's segments, from input
    /// <paramref name="x"/> to output <paramref name="y"/>; NaN where the cross-spectrum is 0
    /// (conventions: Transfer function (H2); ADR 0195).</summary>
    /// <param name="x">Real input samples, finite.</param>
    /// <param name="y">Real output samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the response and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static TransferFunction TransferFunctionH2(ReadOnlySpan<double> x, ReadOnlySpan<double> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        TransferFunctionH2Of(ToComplex(x), ToComplex(y), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: true);

    /// <summary>The H2 estimate, for complex samples: all bins in shifted order (ADR 0197).</summary>
    /// <param name="x">Complex input samples, finite.</param>
    /// <param name="y">Complex output samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the response and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static TransferFunction TransferFunctionH2(ReadOnlySpan<Complex> x, ReadOnlySpan<Complex> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        TransferFunctionH2Of(x.ToArray(), y.ToArray(), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: false);

    private static TransferFunction TransferFunctionH2Of(Complex[] x, Complex[] y, double sampleRate, int? nperseg, int? noverlap,
        WindowType window, double? beta, Detrend detrend, int? nfft, bool oneSided)
    {
        var (g, sxy, _, syy) = CrossSegments(x, y, sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided);
        var response = new Complex[syy.Length];
        for (int k = 0; k < response.Length; k++)
        {
            Complex syx = Complex.Conjugate(sxy[k]);
            response[k] = syx != Complex.Zero ? new Complex(syy[k], 0) / syx : new Complex(double.NaN, double.NaN);
        }
        return new TransferFunction(g.Frequencies(oneSided), response, g.Count);
    }

    /// <summary><c>γ²·Pyy</c> and <c>(1 − γ²)·Pyy</c> on the <c>WelchPsd</c> bins of
    /// <paramref name="y"/>, with <c>γ²</c> taken as 0 where an auto-spectrum is 0 (conventions:
    /// Coherent output power; ADR 0198).</summary>
    /// <param name="x">Real input samples, finite.</param>
    /// <param name="y">Real output samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the two parts and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static CoherentOutputPower CoherentOutputPower(ReadOnlySpan<double> x, ReadOnlySpan<double> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        CoherentOutputPowerOf(ToComplex(x), ToComplex(y), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: true);

    /// <summary>The coherent output power for complex samples: all bins in shifted order (ADR 0197,
    /// ADR 0198).</summary>
    /// <param name="x">Complex input samples, finite.</param>
    /// <param name="y">Complex output samples, finite, as many as <paramref name="x"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nperseg">Segment length; the whole input when null.</param>
    /// <param name="noverlap">Overlap; half a segment when null.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <param name="detrend">Detrending of each segment.</param>
    /// <param name="nfft">Transform length, at least <paramref name="nperseg"/>; the segment length when null.</param>
    /// <returns>The frequencies, the two parts and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static CoherentOutputPower CoherentOutputPower(ReadOnlySpan<Complex> x, ReadOnlySpan<Complex> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null) =>
        CoherentOutputPowerOf(x.ToArray(), y.ToArray(), sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided: false);

    private static CoherentOutputPower CoherentOutputPowerOf(Complex[] x, Complex[] y, double sampleRate, int? nperseg,
        int? noverlap, WindowType window, double? beta, Detrend detrend, int? nfft, bool oneSided)
    {
        var (g, sxy, sxx, syy) = CrossSegments(x, y, sampleRate, nperseg, noverlap, window, beta, detrend, nfft, oneSided);
        int m = syy.Length, last = g.Nfft % 2 == 0 ? m - 1 : m;
        double scale = g.Scale / g.Count;
        var coherent = new double[m];
        var noncoherent = new double[m];
        for (int k = 0; k < m; k++)
        {
            double pyy = syy[k] * scale * (oneSided && k >= 1 && k < last ? 2.0 : 1.0);
            double d = sxx[k] * syy[k];
            double num = sxy[k].Real * sxy[k].Real + sxy[k].Imaginary * sxy[k].Imaginary;
            double gamma = d > 0 ? Math.Min(1.0, num / d) : 0.0;
            coherent[k] = gamma * pyy;
            noncoherent[k] = pyy - coherent[k];
        }
        return new CoherentOutputPower(g.Frequencies(oneSided), coherent, noncoherent, g.Count);
    }

    /// <summary>Welch's equivalent degrees of freedom <c>2K / (1 + 2 Σ (1 − l/K)·ρ(l)²)</c> of
    /// <c>K</c> overlapped segments (conventions: Welch degrees of freedom; ADR 0200).</summary>
    /// <param name="nperseg">Segment length, at least 1.</param>
    /// <param name="noverlap">Overlap, at least 0 and less than <paramref name="nperseg"/>.</param>
    /// <param name="numSegments">The number of segments <c>K</c>, at least 1.</param>
    /// <param name="window">The window applied to each segment.</param>
    /// <param name="beta">The Kaiser β, for the Kaiser window only.</param>
    /// <returns>The equivalent degrees of freedom, between 2 and <c>2K</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double WelchDof(int nperseg, int noverlap, int numSegments, WindowType window = WindowType.Hann,
        double? beta = null)
    {
        if (nperseg < 1)
            throw new ArgumentOutOfRangeException(nameof(nperseg), "nperseg must be at least 1");
        if (noverlap < 0 || noverlap >= nperseg)
            throw new ArgumentOutOfRangeException(nameof(noverlap), "noverlap must satisfy 0 <= noverlap < nperseg");
        if (numSegments < 1)
            throw new ArgumentOutOfRangeException(nameof(numSegments), "numSegments must be at least 1");
        double[] w = Window(window, nperseg, beta: beta);
        if (w.All(v => v == 0))
            throw new ArgumentException($"{window} window of length {nperseg} is all zeros", nameof(window));
        int step = nperseg - noverlap;
        double energy = w.Sum(v => v * v), total = 0;
        for (int lag = 1; lag < numSegments; lag++)
        {
            int shift = lag * step;
            if (shift >= nperseg)
                break;
            double c = 0;
            for (int i = 0; i + shift < nperseg; i++)
                c += w[i] * w[i + shift];
            double rho = c / energy;
            total += (1.0 - (double)lag / numSegments) * rho * rho;
        }
        return 2.0 * numSegments / (1.0 + 2.0 * total);
    }

    /// <summary><c>1 − alpha^(1/(K−1))</c>: the coherence that independent Gaussian signals exceed
    /// with probability <paramref name="alpha"/> over <c>K</c> independent segments; overlap is
    /// not corrected for (conventions: Coherence threshold; ADR 0199).</summary>
    /// <param name="numSegments">The number of independent segments <c>K</c>, at least 2.</param>
    /// <param name="alpha">The false-alarm probability, strictly between 0 and 1.</param>
    /// <returns>The threshold, in (0, 1).</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CoherenceThreshold(int numSegments, double alpha = 0.05)
    {
        if (numSegments < 2)
            throw new ArgumentOutOfRangeException(nameof(numSegments), "numSegments must be at least 2");
        if (!(alpha > 0 && alpha < 1))
            throw new ArgumentOutOfRangeException(nameof(alpha), "alpha must be strictly between 0 and 1");
        return 1 - Math.Pow(alpha, 1.0 / (numSegments - 1));
    }

    /// <summary>Welch's segments of x and y: (segments, Σ conj X·Y, Σ|X|², Σ|Y|²) on the one-sided
    /// bins, or all bins in fftshift order when not one-sided (ADR 0192, ADR 0197).</summary>
    private static (Segments G, Complex[] Sxy, double[] Sxx, double[] Syy) CrossSegments(Complex[] x, Complex[] y,
        double sampleRate, int? nperseg, int? noverlap, WindowType window, double? beta, Detrend detrend, int? nfft,
        bool oneSided)
    {
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        foreach (Complex v in x)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("x must be finite", nameof(x));
        }
        foreach (Complex v in y)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        var g = Prepare(x, sampleRate, nperseg, noverlap, window, beta, detrend, nfft);
        int n = g.Nfft;
        var sxy = new Complex[n];
        var sxx = new double[n];
        var syy = new double[n];
        var bx = new Complex[n];
        var by = new Complex[n];
        for (int s = 0; s < g.Count; s++)
        {
            g.Spectrum(x, s, bx);
            g.Spectrum(y, s, by);
            for (int k = 0; k < n; k++)
            {
                sxy[k] += Complex.Conjugate(bx[k]) * by[k];
                sxx[k] += bx[k].Real * bx[k].Real + bx[k].Imaginary * bx[k].Imaginary;
                syy[k] += by[k].Real * by[k].Real + by[k].Imaginary * by[k].Imaginary;
            }
        }
        if (oneSided)
        {
            int m = n / 2 + 1;
            return (g, sxy[..m], sxx[..m], syy[..m]);
        }
        return (g, Shift(sxy), Shift(sxx), Shift(syy));
    }

    private static T[] Shift<T>(T[] a)
    {
        var r = new T[a.Length];
        for (int i = 0; i < a.Length; i++)
            r[i] = a[(i + (a.Length + 1) / 2) % a.Length]; // fftshift
        return r;
    }
}
