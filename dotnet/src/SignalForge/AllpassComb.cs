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

    /// <summary>Schroeder reverberator: the mean of parallel feedback combs through series
    /// all-passes, blended with the dry signal (conventions: Schroeder reverberator;
    /// ADR 0295).</summary>
    /// <param name="samples">Real, finite samples, at least one.</param>
    /// <param name="combs">The comb delays in samples: 1 to 64, each at least 1.</param>
    /// <param name="combGains">One feedback gain per comb, each with <c>|g| &lt; 1</c>.</param>
    /// <param name="allpasses">The all-pass delays in samples: 0 to 64, each at least 1.</param>
    /// <param name="allpassGain">The all-passes' gain, with <c>|g| &lt; 1</c>.</param>
    /// <param name="mix">The wet fraction, in [0, 1].</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] SchroederReverb(ReadOnlySpan<double> samples, ReadOnlySpan<int> combs, ReadOnlySpan<double> combGains, ReadOnlySpan<int> allpasses, double allpassGain, double mix)
    {
        if (combs.Length < 1 || combs.Length > 64)
            throw new ArgumentException("combs must hold 1 to 64 delays", nameof(combs));
        if (combGains.Length != combs.Length)
            throw new ArgumentException("combGains must hold one gain per comb", nameof(combGains));
        if (allpasses.Length > 64)
            throw new ArgumentException("allpasses must hold at most 64 delays", nameof(allpasses));
        CheckMix(mix);
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        double[] w = new double[samples.Length];
        for (int k = 0; k < combs.Length; k++)
        {
            double[] c = CombFilter(samples, combs[k], combGains[k], feedback: true);
            for (int n = 0; n < w.Length; n++)
                w[n] += c[n];
        }
        for (int n = 0; n < w.Length; n++)
            w[n] /= combs.Length;
        foreach (int d in allpasses)
            w = AllpassComb(w, d, allpassGain);
        double[] y = new double[w.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = samples[n] * (1 - mix) + w[n] * mix;
        return y;
    }
}
