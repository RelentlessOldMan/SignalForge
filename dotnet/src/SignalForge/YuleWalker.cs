using System.Numerics;

namespace SignalForge;

public static partial class Spectral
{
    /// <summary>The Yule-Walker AR PSD <c>σ²/(fs·|A|²)</c> of real samples from the biased
    /// autocorrelation and Levinson-Durbin: one-sided unless <paramref name="oneSided"/> is false
    /// (conventions: Yule-Walker AR PSD; ADR 0203).</summary>
    /// <param name="samples">Finite samples, not all zero, more than <paramref name="order"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="order">The AR order <c>p</c>, at least 1 and below the input length.</param>
    /// <param name="nfft">Number of frequency bins, at least <c>order + 1</c>; null for the input length.</param>
    /// <param name="oneSided">Fold to bins 0 … ⌊nfft/2⌋, as Welch.</param>
    /// <returns>The density, with <c>NumSegments = 1</c> and <c>EnbwHz = fs/N</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static SpectralDensity YuleWalkerPsd(ReadOnlySpan<double> samples, double sampleRate, int order,
        int? nfft = null, bool oneSided = true) =>
        YuleWalker(ToComplex(samples), sampleRate, order, nfft, oneSided);

    /// <summary>The two-sided, shifted Yule-Walker AR PSD <c>σ²/(fs·|A|²)</c> of complex samples
    /// (conventions: Yule-Walker AR PSD; ADR 0203).</summary>
    /// <param name="samples">Finite samples, not all zero, more than <paramref name="order"/>.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="order">The AR order <c>p</c>, at least 1 and below the input length.</param>
    /// <param name="nfft">Number of frequency bins, at least <c>order + 1</c>; null for the input length.</param>
    /// <returns>The density, with <c>NumSegments = 1</c> and <c>EnbwHz = fs/N</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static SpectralDensity YuleWalkerPsd(ReadOnlySpan<Complex> samples, double sampleRate, int order,
        int? nfft = null) =>
        YuleWalker(samples.ToArray(), sampleRate, order, nfft, oneSided: false);

    private static SpectralDensity YuleWalker(Complex[] x, double sampleRate, int order, int? nfft, bool oneSided)
    {
        foreach (Complex v in x)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(x));
        }
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        int n = x.Length;
        if (order < 1)
            throw new ArgumentOutOfRangeException(nameof(order), "order must be at least 1");
        if (order >= n)
            throw new ArgumentException("order must be below the input length", nameof(order));
        int m = nfft ?? n;
        if (m < order + 1)
            throw new ArgumentException("nfft must be at least order + 1", nameof(nfft));
        ComplexLevinson fit = Dsp.Levinson(Dsp.Autocorrelation(x, order), order);
        var buf = new Complex[m];
        Array.Copy(fit.Coefficients, buf, order + 1);
        Transform(buf);
        var two = new double[m];
        for (int k = 0; k < m; k++)
            two[k] = fit.Error / (sampleRate * ((buf[k].Real * buf[k].Real) + (buf[k].Imaginary * buf[k].Imaginary)));
        var g = new Segments(n, n, 1, [], sampleRate, 1.0, Detrend.None, m);
        return new SpectralDensity(g.Frequencies(oneSided), g.Fold(two, 1.0, oneSided), sampleRate,
            n, 1, oneSided, sampleRate / m, sampleRate / n, m);
    }

    /// <summary>The PSD <c>σ²/(fs·|A|²)</c> of a given real AR model on <paramref name="nfft"/>
    /// bins: one-sided unless <paramref name="oneSided"/> is false (conventions: AR model PSD;
    /// ADR 0223).</summary>
    /// <param name="coefficients">The prediction-error filter, finite, <c>a[0] = 1</c>, not zero on any bin.</param>
    /// <param name="error">The prediction error <c>σ²</c>, positive and finite.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nfft">Number of frequency bins, at least <c>order + 1</c>.</param>
    /// <param name="oneSided">Fold to bins 0 … ⌊nfft/2⌋, as Welch.</param>
    /// <returns>The density, with <c>Nperseg = nfft</c>, <c>NumSegments = 1</c> and <c>EnbwHz = fs/nfft</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static SpectralDensity ArPsd(ReadOnlySpan<double> coefficients, double error, double sampleRate, int nfft,
        bool oneSided = true) =>
        ArModel(ToComplex(coefficients), error, sampleRate, nfft, oneSided);

    /// <summary>The two-sided, shifted PSD <c>σ²/(fs·|A|²)</c> of a given complex AR model on
    /// <paramref name="nfft"/> bins (conventions: AR model PSD; ADR 0223).</summary>
    /// <param name="coefficients">The prediction-error filter, finite, <c>a[0] = 1</c>, not zero on any bin.</param>
    /// <param name="error">The prediction error <c>σ²</c>, positive and finite.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="nfft">Number of frequency bins, at least <c>order + 1</c>.</param>
    /// <returns>The density, with <c>Nperseg = nfft</c>, <c>NumSegments = 1</c> and <c>EnbwHz = fs/nfft</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static SpectralDensity ArPsd(ReadOnlySpan<Complex> coefficients, double error, double sampleRate, int nfft) =>
        ArModel(coefficients.ToArray(), error, sampleRate, nfft, oneSided: false);

    private static SpectralDensity ArModel(Complex[] a, double error, double sampleRate, int nfft, bool oneSided)
    {
        if (a.Length == 0)
            throw new ArgumentException("coefficients must not be empty", nameof(a));
        foreach (Complex v in a)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("coefficients must be finite", nameof(a));
        }
        if (a[0] != Complex.One)
            throw new ArgumentException("coefficients[0] must be 1", nameof(a));
        Check.PositiveFinite(error, nameof(error));
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        if (nfft < a.Length)
            throw new ArgumentException("nfft must be at least order + 1", nameof(nfft));
        var buf = new Complex[nfft];
        Array.Copy(a, buf, a.Length);
        Transform(buf);
        var two = new double[nfft];
        for (int k = 0; k < nfft; k++)
        {
            double den = (buf[k].Real * buf[k].Real) + (buf[k].Imaginary * buf[k].Imaginary);
            if (den == 0)
                throw new ArgumentException("the filter must not vanish on a frequency bin", nameof(a));
            two[k] = error / (sampleRate * den);
        }
        var g = new Segments(nfft, nfft, 1, [], sampleRate, 1.0, Detrend.None, nfft);
        return new SpectralDensity(g.Frequencies(oneSided), g.Fold(two, 1.0, oneSided), sampleRate,
            nfft, 1, oneSided, sampleRate / nfft, sampleRate / nfft, nfft);
    }

    /// <summary>Burg's AR PSD <c>σ²/(fs·|A|²)</c> of real samples, the reflection coefficients fitted
    /// to the forward and backward errors: one-sided unless <paramref name="oneSided"/> is false
    /// (conventions: Burg AR PSD; ADR 0204).</summary>
    /// <param name="samples">Finite samples, more than <paramref name="order"/>, not perfectly predictable.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="order">The AR order <c>p</c>, at least 1 and below the input length.</param>
    /// <param name="nfft">Number of frequency bins, at least <c>order + 1</c>; null for the input length.</param>
    /// <param name="oneSided">Fold to bins 0 … ⌊nfft/2⌋, as Welch.</param>
    /// <returns>The density, with <c>NumSegments = 1</c> and <c>EnbwHz = fs/N</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static SpectralDensity BurgPsd(ReadOnlySpan<double> samples, double sampleRate, int order,
        int? nfft = null, bool oneSided = true) =>
        Burg(ToComplex(samples), sampleRate, order, nfft, oneSided);

    /// <summary>The two-sided, shifted Burg AR PSD <c>σ²/(fs·|A|²)</c> of complex samples
    /// (conventions: Burg AR PSD; ADR 0204).</summary>
    /// <param name="samples">Finite samples, more than <paramref name="order"/>, not perfectly predictable.</param>
    /// <param name="sampleRate">Sample rate in Hz, positive and finite.</param>
    /// <param name="order">The AR order <c>p</c>, at least 1 and below the input length.</param>
    /// <param name="nfft">Number of frequency bins, at least <c>order + 1</c>; null for the input length.</param>
    /// <returns>The density, with <c>NumSegments = 1</c> and <c>EnbwHz = fs/N</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static SpectralDensity BurgPsd(ReadOnlySpan<Complex> samples, double sampleRate, int order,
        int? nfft = null) =>
        Burg(samples.ToArray(), sampleRate, order, nfft, oneSided: false);

    private static SpectralDensity Burg(Complex[] x, double sampleRate, int order, int? nfft, bool oneSided)
    {
        foreach (Complex v in x)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(x));
        }
        Check.PositiveFinite(sampleRate, nameof(sampleRate));
        int n = x.Length;
        if (order < 1)
            throw new ArgumentOutOfRangeException(nameof(order), "order must be at least 1");
        if (order >= n)
            throw new ArgumentException("order must be below the input length", nameof(order));
        int m = nfft ?? n;
        if (m < order + 1)
            throw new ArgumentException("nfft must be at least order + 1", nameof(nfft));
        ComplexLevinson fit = Dsp.Burg(x, order);
        var buf = new Complex[m];
        Array.Copy(fit.Coefficients, buf, order + 1);
        Transform(buf);
        var two = new double[m];
        for (int i = 0; i < m; i++)
            two[i] = fit.Error / (sampleRate * ((buf[i].Real * buf[i].Real) + (buf[i].Imaginary * buf[i].Imaginary)));
        var g = new Segments(n, n, 1, [], sampleRate, 1.0, Detrend.None, m);
        return new SpectralDensity(g.Frequencies(oneSided), g.Fold(two, 1.0, oneSided), sampleRate,
            n, 1, oneSided, sampleRate / m, sampleRate / n, m);
    }
}
