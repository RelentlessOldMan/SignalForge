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
}
