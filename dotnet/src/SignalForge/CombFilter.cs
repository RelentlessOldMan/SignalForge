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

    /// <summary>Plays each <paramref name="block"/>-sample stretch backwards one block late,
    /// blended with the dry signal (conventions: Reverse delay; ADR 0298).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="block">The block length in samples, at least 1.</param>
    /// <param name="mix">The wet fraction, in [0, 1].</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] ReverseDelay(ReadOnlySpan<double> samples, int block, double mix)
    {
        if (block < 1)
            throw new ArgumentOutOfRangeException(nameof(block), "block must be at least 1");
        CheckMix(mix);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        double[] y = new double[samples.Length];
        for (int n = 0; n < y.Length; n++)
        {
            int q = n / block, r = n % block;
            double wet = q >= 1 ? samples[((q - 1) * block) + (block - 1 - r)] : 0.0;
            y[n] = samples[n] * (1 - mix) + wet * mix;
        }
        return y;
    }

    /// <summary>Plays the <paramref name="length"/>-sample slice at <paramref name="start"/>
    /// <paramref name="repeats"/> times in a row over the input (conventions: Stutter;
    /// ADR 0299).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="start">The first sample of the slice, at least 0.</param>
    /// <param name="length">The slice length in samples, at least 1.</param>
    /// <param name="repeats">How many times the slice plays, at least 0.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] Stutter(ReadOnlySpan<double> samples, int start, int length, int repeats)
    {
        if (start < 0)
            throw new ArgumentOutOfRangeException(nameof(start), "start must be at least 0");
        if (length < 1)
            throw new ArgumentOutOfRangeException(nameof(length), "length must be at least 1");
        if (repeats < 0)
            throw new ArgumentOutOfRangeException(nameof(repeats), "repeats must be at least 0");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        long end = start + ((long)repeats * length);
        double[] y = samples.ToArray();
        for (int n = start; n < y.Length && n < end; n++)
            y[n] = samples[start + ((n - start) % length)];
        return y;
    }

    /// <summary>The input plus echoes <c>gains[k]·x[n − delays[k]]</c>, added in list order
    /// (conventions: Multi-tap delay; ADR 0300).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="delays">The tap delays in samples: 1 to 64, each at least 1.</param>
    /// <param name="gains">One finite gain per delay.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] MultitapDelay(ReadOnlySpan<double> samples, ReadOnlySpan<int> delays, ReadOnlySpan<double> gains)
    {
        if (delays.Length < 1 || delays.Length > 64)
            throw new ArgumentException("delays must hold 1 to 64 taps", nameof(delays));
        if (gains.Length != delays.Length)
            throw new ArgumentException("gains must hold one gain per delay", nameof(gains));
        for (int k = 0; k < delays.Length; k++)
        {
            if (delays[k] < 1)
                throw new ArgumentOutOfRangeException(nameof(delays), "delays must be at least 1");
            if (!double.IsFinite(gains[k]))
                throw new ArgumentException("gains must be finite", nameof(gains));
        }
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        double[] y = samples.ToArray();
        for (int k = 0; k < delays.Length; k++)
        {
            for (int n = delays[k]; n < y.Length; n++)
                y[n] += gains[k] * samples[n - delays[k]];
        }
        return y;
    }
}
