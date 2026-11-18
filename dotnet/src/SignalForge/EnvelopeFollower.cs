using System.Numerics;

namespace SignalForge;

public static partial class Dsp
{
    /// <summary>Peak envelope of <c>|x|</c> for real samples, with one-pole attack and release
    /// coefficients, from rest (conventions: Envelope follower; ADR 0238).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="attack">The coefficient while rising, in <c>[0, 1)</c>.</param>
    /// <param name="release">The coefficient otherwise, in <c>[0, 1)</c>.</param>
    /// <returns>One envelope value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] EnvelopeFollower(ReadOnlySpan<double> samples, double attack, double release) =>
        EnvelopeFollower((ReadOnlySpan<Complex>)ToComplexArray(samples), attack, release);

    /// <summary>Peak envelope of <c>|x|</c> for complex samples, with one-pole attack and release
    /// coefficients, from rest (conventions: Envelope follower; ADR 0238).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="attack">The coefficient while rising, in <c>[0, 1)</c>.</param>
    /// <param name="release">The coefficient otherwise, in <c>[0, 1)</c>.</param>
    /// <returns>One envelope value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] EnvelopeFollower(ReadOnlySpan<Complex> samples, double attack, double release)
    {
        if (!double.IsFinite(attack) || attack < 0 || attack >= 1)
            throw new ArgumentOutOfRangeException(nameof(attack), "attack must be in [0, 1)");
        if (!double.IsFinite(release) || release < 0 || release >= 1)
            throw new ArgumentOutOfRangeException(nameof(release), "release must be in [0, 1)");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var e = new double[samples.Length];
        double prev = 0;
        for (int n = 0; n < samples.Length; n++)
        {
            double r = Complex.Abs(samples[n]);
            double c = r > prev ? attack : release;
            prev = r + c * (prev - r);
            e[n] = prev;
        }
        return e;
    }

    /// <summary>Peak of <c>|x|</c> for real samples, held for <paramref name="hold"/> samples and
    /// then decaying by <paramref name="release"/> per sample, from rest (conventions: Peak hold;
    /// ADR 0243).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="hold">How many samples a peak is held after it arrives, at least 0.</param>
    /// <param name="release">The decay per sample after the hold, in <c>[0, 1)</c>.</param>
    /// <returns>One held value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] PeakHold(ReadOnlySpan<double> samples, int hold, double release) =>
        PeakHold((ReadOnlySpan<Complex>)ToComplexArray(samples), hold, release);

    /// <summary>Peak of <c>|x|</c> for complex samples, held for <paramref name="hold"/> samples
    /// and then decaying by <paramref name="release"/> per sample, from rest (conventions: Peak
    /// hold; ADR 0243).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="hold">How many samples a peak is held after it arrives, at least 0.</param>
    /// <param name="release">The decay per sample after the hold, in <c>[0, 1)</c>.</param>
    /// <returns>One held value per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] PeakHold(ReadOnlySpan<Complex> samples, int hold, double release)
    {
        if (hold < 0)
            throw new ArgumentOutOfRangeException(nameof(hold), "hold must be at least 0");
        if (!double.IsFinite(release) || release < 0 || release >= 1)
            throw new ArgumentOutOfRangeException(nameof(release), "release must be in [0, 1)");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (Complex v in samples)
        {
            if (!double.IsFinite(v.Real) || !double.IsFinite(v.Imaginary))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        var y = new double[samples.Length];
        double p = 0;
        int c = 0;
        for (int n = 0; n < samples.Length; n++)
        {
            double r = Complex.Abs(samples[n]);
            if (r >= p)
            {
                p = r;
                c = 0;
            }
            else if (c < hold)
            {
                c++;
            }
            else
            {
                p = release * p;
                if (p < r)
                    p = r;
            }
            y[n] = p;
        }
        return y;
    }

    /// <summary>Scales each real sample by the fast envelope over the slow one, to the power
    /// <paramref name="amount"/> (conventions: Transient shaper; ADR 0281).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="fast">The fast envelope's coefficient, rising and falling, in <c>[0, 1)</c>.</param>
    /// <param name="slow">The slow envelope's coefficient, rising and falling, in <c>[0, 1)</c>.</param>
    /// <param name="amount">The power on the ratio, finite; 0 returns the input.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double[] TransientShaper(ReadOnlySpan<double> samples, double fast, double slow, double amount)
    {
        CheckTransientShaper(fast, slow, amount);
        double[] g = TransientGains(EnvelopeFollower(samples, fast, fast), EnvelopeFollower(samples, slow, slow), amount);
        var y = new double[samples.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = samples[n] * g[n];
        return y;
    }

    /// <summary>Scales each complex sample, part by part, by the fast envelope over the slow
    /// one, to the power <paramref name="amount"/> (conventions: Transient shaper;
    /// ADR 0281).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="fast">The fast envelope's coefficient, rising and falling, in <c>[0, 1)</c>.</param>
    /// <param name="slow">The slow envelope's coefficient, rising and falling, in <c>[0, 1)</c>.</param>
    /// <param name="amount">The power on the ratio, finite; 0 returns the input.</param>
    /// <returns>One output per sample.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static Complex[] TransientShaper(ReadOnlySpan<Complex> samples, double fast, double slow, double amount)
    {
        CheckTransientShaper(fast, slow, amount);
        double[] g = TransientGains(EnvelopeFollower(samples, fast, fast), EnvelopeFollower(samples, slow, slow), amount);
        var y = new Complex[samples.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = new Complex(samples[n].Real * g[n], samples[n].Imaginary * g[n]);
        return y;
    }

    private static void CheckTransientShaper(double fast, double slow, double amount)
    {
        if (!double.IsFinite(fast) || fast < 0 || fast >= 1)
            throw new ArgumentOutOfRangeException(nameof(fast), "fast must be in [0, 1)");
        if (!double.IsFinite(slow) || slow < 0 || slow >= 1)
            throw new ArgumentOutOfRangeException(nameof(slow), "slow must be in [0, 1)");
        if (!double.IsFinite(amount))
            throw new ArgumentOutOfRangeException(nameof(amount), "amount must be finite");
    }

    private static double[] TransientGains(double[] ef, double[] es, double amount)
    {
        var g = new double[ef.Length];
        for (int n = 0; n < g.Length; n++)
            g[n] = ef[n] > 0 && es[n] > 0 ? Math.Pow(ef[n] / es[n], amount) : 1.0;
        return g;
    }
}
