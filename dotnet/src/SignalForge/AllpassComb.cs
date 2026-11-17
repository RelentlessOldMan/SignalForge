using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Schroeder allpass <c>y[n] = −g·x[n] + x[n − D] + g·y[n − D]</c> of real samples,
    /// zero before the start (conventions: Schroeder allpass section; ADR 0240).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The delay <c>D</c> in samples, at least 1.</param>
    /// <param name="gain">The gain <c>g</c>, with <c>|g| &lt; 1</c>.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] AllpassComb(ReadOnlySpan<double> samples, int delay, double gain) =>
        [.. AllpassComb((ReadOnlySpan<Complex>)ToComplexArray(samples), delay, gain).Select(v => v.Real)];

    /// <summary>Schroeder allpass <c>y[n] = −g·x[n] + x[n − D] + g·y[n − D]</c> of complex
    /// samples, zero before the start (conventions: Schroeder allpass section; ADR 0240).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The delay <c>D</c> in samples, at least 1.</param>
    /// <param name="gain">The gain <c>g</c>, with <c>|g| &lt; 1</c>.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] AllpassComb(ReadOnlySpan<Complex> samples, int delay, double gain)
    {
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), "delay must be at least 1");
        if (!double.IsFinite(gain) || !(Math.Abs(gain) < 1))
            throw new ArgumentOutOfRangeException(nameof(gain), "gain must satisfy |gain| < 1");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new Complex[samples.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = n >= delay ? -gain * samples[n] + samples[n - delay] + gain * y[n - delay] : -gain * samples[n];
        return y;
    }
}
