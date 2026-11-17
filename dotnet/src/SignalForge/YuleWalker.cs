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
        var f = (Complex[])x.Clone();
        var b = (Complex[])x.Clone();
        var a = new Complex[order + 1];
        a[0] = 1;
        double error = 0;
        foreach (Complex v in x)
            error += (v.Real * v.Real) + (v.Imaginary * v.Imaginary);
        error /= n;
        for (int stage = 1; stage <= order; stage++)
        {
            int len = n - stage;
            Complex cross = Complex.Zero;
            double energy = 0;
            for (int i = 0; i < len; i++)
            {
                Complex fw = f[i + 1], bw = b[i];
                cross += fw * Complex.Conjugate(bw);
                energy += (fw.Real * fw.Real) + (fw.Imaginary * fw.Imaginary) + (bw.Real * bw.Real) + (bw.Imaginary * bw.Imaginary);
            }
            if (!(energy > 0))
                throw new ArgumentException("the prediction errors vanish: the record is perfectly predictable", nameof(x));
            Complex k = -2.0 * cross / energy;
            if (!(Complex.Abs(k) < 1))
                throw new ArgumentException("a reflection coefficient has |k| >= 1: the record is predictable", nameof(x));
            for (int i = 0; i < len; i++)
            {
                Complex fw = f[i + 1], bw = b[i];
                f[i] = fw + (k * bw);
                b[i] = bw + (Complex.Conjugate(k) * fw);
            }
            var next = new Complex[stage + 1];
            for (int j = 0; j <= stage; j++)
                next[j] = a[j] + (k * Complex.Conjugate(a[stage - j]));
            Array.Copy(next, a, stage + 1);
            error *= 1 - (k.Real * k.Real) - (k.Imaginary * k.Imaginary);
        }
        var buf = new Complex[m];
        Array.Copy(a, buf, order + 1);
        Transform(buf);
        var two = new double[m];
        for (int i = 0; i < m; i++)
            two[i] = error / (sampleRate * ((buf[i].Real * buf[i].Real) + (buf[i].Imaginary * buf[i].Imaginary)));
        var g = new Segments(n, n, 1, [], sampleRate, 1.0, Detrend.None, m);
        return new SpectralDensity(g.Frequencies(oneSided), g.Fold(two, 1.0, oneSided), sampleRate,
            n, 1, oneSided, sampleRate / m, sampleRate / n, m);
    }
}
