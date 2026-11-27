using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The sound strength <c>10·log10(Σ |h|² / Σ |h_ref|²)</c> in dB against the
    /// free-field response at 10 m (conventions: Sound strength; ADR 0178).</summary>
    /// <param name="impulseResponse">The complex response, finite, not empty.</param>
    /// <param name="reference">The complex free-field response at 10 m, at the same sample rate,
    /// finite, not empty, not all zero.</param>
    /// <returns>G in dB; <c>−∞</c> for a silent response.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SoundStrength(ReadOnlySpan<Complex> impulseResponse, ReadOnlySpan<Complex> reference)
    {
        int e = PowerOf2Exponent(Math.Max(LargestMagnitude(impulseResponse), LargestMagnitude(reference)));
        return StrengthDb(Sum(ResponsePowers(impulseResponse, e)), StrengthReference(reference, e));
    }

    /// <summary>The sound strength <c>10·log10(Σ h² / Σ h_ref²)</c> in dB against the free-field
    /// response at 10 m (conventions: Sound strength; ADR 0178).</summary>
    /// <param name="impulseResponse">The real response, finite, not empty.</param>
    /// <param name="reference">The real free-field response at 10 m, at the same sample rate,
    /// finite, not empty, not all zero.</param>
    /// <returns>G in dB; <c>−∞</c> for a silent response.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SoundStrength(ReadOnlySpan<double> impulseResponse, ReadOnlySpan<double> reference)
    {
        int e = PowerOf2Exponent(Math.Max(LargestMagnitude(impulseResponse), LargestMagnitude(reference)));
        return StrengthDb(Sum(ResponsePowers(impulseResponse, e)), StrengthReference(reference, e));
    }

    private static double StrengthReference(ReadOnlySpan<Complex> reference, int exponent)
    {
        if (reference.IsEmpty)
            throw new ArgumentException("reference must not be empty", nameof(reference));
        double e = 0;
        foreach (Complex v in reference)
        {
            if (!(double.IsFinite(v.Real) && double.IsFinite(v.Imaginary)))
                throw new ArgumentException("reference must be finite", nameof(reference));
            double re = Math.ScaleB(v.Real, -exponent), im = Math.ScaleB(v.Imaginary, -exponent);
            e += re * re + im * im;
        }
        return e > 0 ? e : throw new ArgumentException("reference must not be all zero", nameof(reference));
    }

    private static double StrengthReference(ReadOnlySpan<double> reference, int exponent)
    {
        if (reference.IsEmpty)
            throw new ArgumentException("reference must not be empty", nameof(reference));
        double e = 0;
        foreach (double v in reference)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("reference must be finite", nameof(reference));
            double u = Math.ScaleB(v, -exponent);
            e += u * u;
        }
        return e > 0 ? e : throw new ArgumentException("reference must not be all zero", nameof(reference));
    }

    private static double Sum(double[] p)
    {
        double s = 0;
        foreach (double v in p)
            s += v;
        return s;
    }

    private static double StrengthDb(double energy, double reference) =>
        energy == 0 ? double.NegativeInfinity : 10 * Math.Log10(energy / reference);
}
