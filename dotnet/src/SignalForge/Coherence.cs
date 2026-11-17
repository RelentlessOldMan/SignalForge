using System.Numerics;

namespace SignalForge;

/// <summary>Magnitude-squared coherence per one-sided bin (conventions: Coherence; ADR 0192).</summary>
/// <param name="Frequencies">Bin frequencies <c>k·fs/M</c>, <c>k = 0 … ⌊M/2⌋</c>.</param>
/// <param name="Values">The coherence in [0, 1] per bin; NaN where an auto-spectrum is 0.</param>
/// <param name="NumSegments">How many segments were averaged.</param>
public sealed record Coherence(double[] Frequencies, double[] Values, int NumSegments);

/// <summary>Welch cross-spectral density per one-sided bin (conventions: Cross-spectral density;
/// ADR 0194).</summary>
/// <param name="Frequencies">Bin frequencies <c>k·fs/M</c>, <c>k = 0 … ⌊M/2⌋</c>.</param>
/// <param name="Csd">The cross-spectral density <c>Pxy</c>, units²/Hz.</param>
/// <param name="NumSegments">How many segments were averaged.</param>
public sealed record CrossSpectralDensity(double[] Frequencies, Complex[] Csd, int NumSegments);

/// <summary>H1 frequency-response estimate per one-sided bin (conventions: Transfer function (H1);
/// ADR 0193).</summary>
/// <param name="Frequencies">Bin frequencies <c>k·fs/M</c>, <c>k = 0 … ⌊M/2⌋</c>.</param>
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
        Detrend detrend = Detrend.None, int? nfft = null)
    {
        var (g, sxy, sxx, syy) = CrossSegments(x, y, sampleRate, nperseg, noverlap, window, beta, detrend, nfft);
        int m = sxx.Length;
        var values = new double[m];
        for (int k = 0; k < m; k++)
        {
            double d = sxx[k] * syy[k];
            double num = sxy[k].Real * sxy[k].Real + sxy[k].Imaginary * sxy[k].Imaginary;
            values[k] = d > 0 ? Math.Min(1.0, num / d) : double.NaN;
        }
        return new Coherence(g.Frequencies(true), values, g.Count);
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
        Detrend detrend = Detrend.None, int? nfft = null)
    {
        var (g, sxy, sxx, _) = CrossSegments(x, y, sampleRate, nperseg, noverlap, window, beta, detrend, nfft);
        var response = new Complex[sxx.Length];
        for (int k = 0; k < response.Length; k++)
            response[k] = sxx[k] > 0 ? sxy[k] / sxx[k] : new Complex(double.NaN, double.NaN);
        return new TransferFunction(g.Frequencies(true), response, g.Count);
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
    /// <returns>The frequencies, the cross-spectral density and the segment count.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static CrossSpectralDensity CrossSpectralDensity(ReadOnlySpan<double> x, ReadOnlySpan<double> y, double sampleRate,
        int? nperseg = null, int? noverlap = null, WindowType window = WindowType.Hann, double? beta = null,
        Detrend detrend = Detrend.None, int? nfft = null)
    {
        var (g, sxy, _, _) = CrossSegments(x, y, sampleRate, nperseg, noverlap, window, beta, detrend, nfft);
        int m = sxy.Length, last = g.Nfft % 2 == 0 ? m - 1 : m;
        double scale = g.Scale / g.Count;
        var csd = new Complex[m];
        for (int k = 0; k < m; k++)
            csd[k] = sxy[k] * scale * (k >= 1 && k < last ? 2.0 : 1.0);
        return new CrossSpectralDensity(g.Frequencies(true), csd, g.Count);
    }

    private static (Segments G, Complex[] Sxy, double[] Sxx, double[] Syy) CrossSegments(ReadOnlySpan<double> x,
        ReadOnlySpan<double> y, double sampleRate, int? nperseg, int? noverlap, WindowType window, double? beta,
        Detrend detrend, int? nfft)
    {
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        foreach (double v in x)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("x must be finite", nameof(x));
        }
        foreach (double v in y)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("y must be finite", nameof(y));
        }
        Complex[] xc = ToComplex(x), yc = ToComplex(y);
        var g = Prepare(xc, sampleRate, nperseg, noverlap, window, beta, detrend, nfft);
        int m = g.Nfft / 2 + 1;
        var sxy = new Complex[m];
        var sxx = new double[m];
        var syy = new double[m];
        var bx = new Complex[g.Nfft];
        var by = new Complex[g.Nfft];
        for (int s = 0; s < g.Count; s++)
        {
            g.Spectrum(xc, s, bx);
            g.Spectrum(yc, s, by);
            for (int k = 0; k < m; k++)
            {
                sxy[k] += Complex.Conjugate(bx[k]) * by[k];
                sxx[k] += bx[k].Real * bx[k].Real + bx[k].Imaginary * bx[k].Imaginary;
                syy[k] += by[k].Real * by[k].Real + by[k].Imaginary * by[k].Imaginary;
            }
        }
        return (g, sxy, sxx, syy);
    }
}
