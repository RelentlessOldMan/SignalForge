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

    /// <summary>Feedback comb whose loop runs through a one-pole low-pass, so treble decays
    /// faster (conventions: Damped feedback comb; ADR 0297).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="delay">The loop delay in samples, at least 1.</param>
    /// <param name="feedback">The loop gain, with <c>|g| &lt; 1</c>.</param>
    /// <param name="damping">The low-pass pole, in [0, 1).</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] LowpassFeedbackComb(ReadOnlySpan<double> samples, int delay, double feedback, double damping)
    {
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), "delay must be at least 1");
        if (!(Math.Abs(feedback) < 1))
            throw new ArgumentOutOfRangeException(nameof(feedback), "feedback must satisfy |feedback| < 1");
        if (!(damping >= 0 && damping < 1))
            throw new ArgumentOutOfRangeException(nameof(damping), "damping must be in [0, 1)");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] y = new double[samples.Length];
        double f = 0;
        for (int n = 0; n < y.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            f = (1 - damping) * (n >= delay ? y[n - delay] : 0.0) + damping * f;
            y[n] = v + feedback * f;
        }
        return y;
    }
}
