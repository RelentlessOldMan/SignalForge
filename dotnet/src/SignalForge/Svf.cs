using System.Numerics;

namespace SignalForge;

/// <summary>Which response <see cref="Dsp.Svf(ReadOnlySpan{double}, double, double, double, SvfOutput)"/>
/// returns (conventions: State-variable filter; ADR 0279).</summary>
public enum SvfOutput
{
    /// <summary><c>1/(s² + k·s + 1)</c>.</summary>
    Lowpass,

    /// <summary><c>s/(s² + k·s + 1)</c>, peak gain <c>q</c>.</summary>
    Bandpass,

    /// <summary><c>s²/(s² + k·s + 1)</c>.</summary>
    Highpass,

    /// <summary><c>(s² + 1)/(s² + k·s + 1)</c>.</summary>
    Notch,
}

public static partial class Dsp
{
    /// <summary>Trapezoidal state-variable filter on real samples (conventions: State-variable
    /// filter; ADR 0279).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="cutoff">The cutoff, Hz, above 0 and below half the sample rate.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="output">Which response to return.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Svf(ReadOnlySpan<double> samples, double cutoff, double q, double sampleRate, SvfOutput output = SvfOutput.Lowpass)
    {
        (double g, double k) = SvfCoefficients(samples.Length, cutoff, q, sampleRate, output);
        var v = new double[samples.Length];
        for (int n = 0; n < v.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            v[n] = samples[n];
        }
        return SvfRun(v, g, k, output);
    }

    /// <summary>Trapezoidal state-variable filter on complex samples, part by part
    /// (conventions: State-variable filter; ADR 0279).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="cutoff">The cutoff, Hz, above 0 and below half the sample rate.</param>
    /// <param name="q">The quality factor, finite and positive.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="output">Which response to return.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] Svf(ReadOnlySpan<Complex> samples, double cutoff, double q, double sampleRate, SvfOutput output = SvfOutput.Lowpass)
    {
        (double g, double k) = SvfCoefficients(samples.Length, cutoff, q, sampleRate, output);
        var re = new double[samples.Length];
        var im = new double[samples.Length];
        for (int n = 0; n < re.Length; n++)
        {
            if (!double.IsFinite(samples[n].Real) || !double.IsFinite(samples[n].Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            re[n] = samples[n].Real;
            im[n] = samples[n].Imaginary;
        }
        double[] yr = SvfRun(re, g, k, output), yi = SvfRun(im, g, k, output);
        var y = new Complex[re.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = new Complex(yr[n], yi[n]);
        return y;
    }

    private static (double G, double K) SvfCoefficients(int length, double cutoff, double q, double sampleRate, SvfOutput output)
    {
        if (!double.IsFinite(sampleRate) || sampleRate <= 0)
            throw new ArgumentOutOfRangeException(nameof(sampleRate), "sampleRate must be positive");
        if (!double.IsFinite(cutoff) || !(cutoff > 0 && cutoff < sampleRate / 2))
            throw new ArgumentOutOfRangeException(nameof(cutoff), "cutoff must be in (0, sampleRate / 2)");
        if (!double.IsFinite(q) || !(q > 0))
            throw new ArgumentOutOfRangeException(nameof(q), "q must be positive");
        if (output is not (SvfOutput.Lowpass or SvfOutput.Bandpass or SvfOutput.Highpass or SvfOutput.Notch))
            throw new ArgumentOutOfRangeException(nameof(output), "output must be Lowpass, Bandpass, Highpass or Notch");
        if (length == 0)
            throw new ArgumentException("samples must not be empty", nameof(length));
        return (Math.Tan(Math.PI * cutoff / sampleRate), 1 / q);
    }

    private static double[] SvfRun(double[] v, double g, double k, SvfOutput output)
    {
        double a1 = 1 / (1 + g * (g + k));
        double a2 = g * a1;
        double a3 = g * a2;
        double ic1 = 0, ic2 = 0;
        var y = new double[v.Length];
        for (int n = 0; n < v.Length; n++)
        {
            double x = v[n];
            double v3 = x - ic2;
            double v1 = a1 * ic1 + a2 * v3;
            double v2 = ic2 + a2 * ic1 + a3 * v3;
            ic1 = 2 * v1 - ic1;
            ic2 = 2 * v2 - ic2;
            y[n] = output switch
            {
                SvfOutput.Lowpass => v2,
                SvfOutput.Bandpass => v1,
                SvfOutput.Highpass => x - k * v1 - v2,
                _ => x - k * v1,
            };
        }
        return y;
    }
}
