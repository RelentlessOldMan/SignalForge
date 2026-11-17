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
}
