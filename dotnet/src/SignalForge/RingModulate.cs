using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Multiplies real samples by the carrier <c>cos(2π·f·n/fs + phase)</c>
    /// (conventions: Ring modulator; ADR 0260).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="frequency">The carrier frequency in Hz, finite.</param>
    /// <param name="sampleRate">The sample rate in Hz, finite and positive.</param>
    /// <param name="phase">The carrier phase in radians, finite.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] RingModulate(ReadOnlySpan<double> samples, double frequency, double sampleRate, double phase = 0)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] c = RingCarrier(samples.Length, frequency, sampleRate, phase);
        for (int n = 0; n < c.Length; n++)
        {
            if (!double.IsFinite(samples[n]))
                throw new ArgumentException("samples must be finite", nameof(samples));
            c[n] = samples[n] * c[n];
        }
        return c;
    }

    /// <summary>Multiplies complex samples by the carrier <c>cos(2π·f·n/fs + phase)</c>
    /// (conventions: Ring modulator; ADR 0260).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="frequency">The carrier frequency in Hz, finite.</param>
    /// <param name="sampleRate">The sample rate in Hz, finite and positive.</param>
    /// <param name="phase">The carrier phase in radians, finite.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] RingModulate(ReadOnlySpan<Complex> samples, double frequency, double sampleRate, double phase = 0)
    {
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] c = RingCarrier(samples.Length, frequency, sampleRate, phase);
        var y = new Complex[c.Length];
        for (int n = 0; n < c.Length; n++)
        {
            Complex v = samples[n];
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
            y[n] = new Complex(v.Real * c[n], v.Imaginary * c[n]);
        }
        return y;
    }

    private static double[] RingCarrier(int length, double frequency, double sampleRate, double phase)
    {
        if (!double.IsFinite(frequency))
            throw new ArgumentOutOfRangeException(nameof(frequency), "frequency must be finite");
        if (!double.IsFinite(sampleRate) || !(sampleRate > 0))
            throw new ArgumentOutOfRangeException(nameof(sampleRate), "sample_rate must be positive");
        if (!double.IsFinite(phase))
            throw new ArgumentOutOfRangeException(nameof(phase), "phase must be finite");
        double w = 2.0 * Math.PI * frequency;
        var c = new double[length];
        for (int n = 0; n < length; n++)
            c[n] = Math.Cos(w * (n / sampleRate) + phase);
        return c;
    }
}
