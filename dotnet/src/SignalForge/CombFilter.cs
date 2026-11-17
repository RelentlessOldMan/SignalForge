using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Feedforward <c>y[n] = x[n] + g·x[n − D]</c> or feedback
    /// <c>y[n] = x[n] + g·y[n − D]</c> comb of real samples, zero before the start (conventions:
    /// Comb filter; ADR 0237).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The delay <c>D</c> in samples, at least 1.</param>
    /// <param name="gain">The gain <c>g</c>; <c>|g| &lt; 1</c> for feedback.</param>
    /// <param name="feedback">True for the feedback form.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] CombFilter(ReadOnlySpan<double> samples, int delay, double gain, bool feedback = false) =>
        [.. CombFilter((ReadOnlySpan<Complex>)ToComplexArray(samples), delay, gain, feedback).Select(v => v.Real)];

    /// <summary>Feedforward <c>y[n] = x[n] + g·x[n − D]</c> or feedback
    /// <c>y[n] = x[n] + g·y[n − D]</c> comb of complex samples, zero before the start
    /// (conventions: Comb filter; ADR 0237).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="delay">The delay <c>D</c> in samples, at least 1.</param>
    /// <param name="gain">The gain <c>g</c>; <c>|g| &lt; 1</c> for feedback.</param>
    /// <param name="feedback">True for the feedback form.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] CombFilter(ReadOnlySpan<Complex> samples, int delay, double gain, bool feedback = false)
    {
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), "delay must be at least 1");
        if (!double.IsFinite(gain))
            throw new ArgumentOutOfRangeException(nameof(gain), "gain must be finite");
        if (feedback && !(Math.Abs(gain) < 1))
            throw new ArgumentOutOfRangeException(nameof(gain), "a feedback comb needs |gain| < 1");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        Complex[] y = samples.ToArray();
        for (int n = delay; n < y.Length; n++)
            y[n] = samples[n] + gain * (feedback ? y[n - delay] : samples[n - delay]);
        return y;
    }
}
