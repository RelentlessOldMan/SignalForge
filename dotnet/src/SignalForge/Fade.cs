using System.Numerics;

namespace SignalForge;

/// <summary>The shape of a fade ramp (conventions: Fades; ADR 0262).</summary>
public enum FadeShape
{
    /// <summary><c>r(t) = t</c>.</summary>
    Linear,

    /// <summary><c>r(t) = (1 − cos(π·t))/2</c>, flat at both ends.</summary>
    Cosine,
}

public static partial class Dsp
{
    /// <summary>Ramps the gain of real samples up over the first <paramref name="fadeIn"/>
    /// samples and down over the last <paramref name="fadeOut"/> (conventions: Fades;
    /// ADR 0262).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="fadeIn">Samples in the fade-in ramp, from 0 to the number of samples.</param>
    /// <param name="fadeOut">Samples in the fade-out ramp, from 0 to the number of samples.</param>
    /// <param name="shape">The ramp shape.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Fade(ReadOnlySpan<double> samples, int fadeIn, int fadeOut, FadeShape shape = FadeShape.Linear)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] g = FadeGain(samples.Length, fadeIn, fadeOut, shape);
        for (int n = 0; n < g.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            g[n] = samples[n] * g[n];
        }
        return g;
    }

    /// <summary>Ramps the gain of complex samples up over the first <paramref name="fadeIn"/>
    /// samples and down over the last <paramref name="fadeOut"/> (conventions: Fades;
    /// ADR 0262).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="fadeIn">Samples in the fade-in ramp, from 0 to the number of samples.</param>
    /// <param name="fadeOut">Samples in the fade-out ramp, from 0 to the number of samples.</param>
    /// <param name="shape">The ramp shape.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Fade(ReadOnlySpan<Complex> samples, int fadeIn, int fadeOut, FadeShape shape = FadeShape.Linear)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] g = FadeGain(samples.Length, fadeIn, fadeOut, shape);
        var y = new Complex[g.Length];
        for (int n = 0; n < g.Length; n++)
        {
            Complex v = samples[n];
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = new Complex(v.Real * g[n], v.Imaginary * g[n]);
        }
        return y;
    }

    private static double[] FadeGain(int length, int fadeIn, int fadeOut, FadeShape shape)
    {
        if (fadeIn < 0 || fadeIn > length)
            throw new ArgumentOutOfRangeException(nameof(fadeIn), "fade_in must be from 0 to the number of samples");
        if (fadeOut < 0 || fadeOut > length)
            throw new ArgumentOutOfRangeException(nameof(fadeOut), "fade_out must be from 0 to the number of samples");
        if (!Enum.IsDefined(shape))
            throw new ArgumentOutOfRangeException(nameof(shape), "shape must be Linear or Cosine");
        var g = new double[length];
        Array.Fill(g, 1.0);
        for (int n = 0; n < fadeIn; n++)
            g[n] *= FadeRamp((double)n / fadeIn, shape);
        for (int k = 0; k < fadeOut; k++)
            g[length - 1 - k] *= FadeRamp((double)k / fadeOut, shape);
        return g;
    }

    private static double FadeRamp(double t, FadeShape shape) =>
        shape == FadeShape.Linear ? t : (1 - Math.Cos(Math.PI * t)) / 2;

    /// <summary>Joins real <paramref name="a"/> and <paramref name="b"/> over
    /// <paramref name="overlap"/> shared samples with complementary ramps (conventions:
    /// Crossfade; ADR 0263).</summary>
    /// <param name="a">The first input, finite, at least one sample.</param>
    /// <param name="b">The second input, finite, at least one sample.</param>
    /// <param name="overlap">Shared samples, from 0 to the length of each input.</param>
    /// <param name="shape">The ramp shape.</param>
    /// <returns><c>a.Length + b.Length − overlap</c> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Crossfade(ReadOnlySpan<double> a, ReadOnlySpan<double> b, int overlap, FadeShape shape = FadeShape.Linear)
    {
        double[] w = CrossfadeWeights(a.Length, b.Length, overlap, shape);
        foreach (double v in a)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("a must be finite", nameof(a));
        }
        foreach (double v in b)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("b must be finite", nameof(b));
        }
        int head = a.Length - overlap;
        var y = new double[head + b.Length];
        a[..head].CopyTo(y);
        for (int k = 0; k < overlap; k++)
            y[head + k] = a[head + k] * (1 - w[k]) + b[k] * w[k];
        b[overlap..].CopyTo(y.AsSpan(a.Length));
        return y;
    }

    /// <summary>Joins complex <paramref name="a"/> and <paramref name="b"/> over
    /// <paramref name="overlap"/> shared samples with complementary ramps (conventions:
    /// Crossfade; ADR 0263).</summary>
    /// <param name="a">The first input, finite, at least one sample.</param>
    /// <param name="b">The second input, finite, at least one sample.</param>
    /// <param name="overlap">Shared samples, from 0 to the length of each input.</param>
    /// <param name="shape">The ramp shape.</param>
    /// <returns><c>a.Length + b.Length − overlap</c> samples.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Crossfade(ReadOnlySpan<Complex> a, ReadOnlySpan<Complex> b, int overlap, FadeShape shape = FadeShape.Linear)
    {
        double[] w = CrossfadeWeights(a.Length, b.Length, overlap, shape);
        foreach (Complex v in a)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("a must be finite", nameof(a));
        }
        foreach (Complex v in b)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("b must be finite", nameof(b));
        }
        int head = a.Length - overlap;
        var y = new Complex[head + b.Length];
        a[..head].CopyTo(y);
        for (int k = 0; k < overlap; k++)
        {
            Complex p = a[head + k], q = b[k];
            double u = 1 - w[k];
            y[head + k] = new Complex(p.Real * u + q.Real * w[k], p.Imaginary * u + q.Imaginary * w[k]);
        }
        b[overlap..].CopyTo(y.AsSpan(a.Length));
        return y;
    }

    private static double[] CrossfadeWeights(int lengthA, int lengthB, int overlap, FadeShape shape)
    {
        if (lengthA == 0)
            throw new ArgumentException("a must not be empty", nameof(lengthA));
        if (lengthB == 0)
            throw new ArgumentException("b must not be empty", nameof(lengthB));
        if (overlap < 0 || overlap > Math.Min(lengthA, lengthB))
            throw new ArgumentOutOfRangeException(nameof(overlap), "overlap must be from 0 to the length of each input");
        if (!Enum.IsDefined(shape))
            throw new ArgumentOutOfRangeException(nameof(shape), "shape must be Linear or Cosine");
        var w = new double[overlap];
        for (int k = 0; k < overlap; k++)
            w[k] = FadeRamp((double)(k + 1) / (overlap + 1), shape);
        return w;
    }
}
