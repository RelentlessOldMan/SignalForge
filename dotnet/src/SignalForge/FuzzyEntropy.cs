namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Chen's fuzzy entropy <c>ln φ_m − ln φ_{m+1}</c>: baseline-removed templates,
    /// Chebyshev distance and the membership <c>exp(−dⁿ/r)</c> (conventions: Fuzzy entropy;
    /// ADR 0339).</summary>
    /// <param name="samples">Real samples, finite, at least <c>m + 2</c>.</param>
    /// <param name="m">The template length, at least 1.</param>
    /// <param name="r">The membership width, finite and positive.</param>
    /// <param name="n">The membership power, finite and at least 1.</param>
    /// <returns>The fuzzy entropy.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the memberships
    /// underflow to 0.</exception>
    public static double FuzzyEntropy(ReadOnlySpan<double> samples, int m, double r, double n = 2)
    {
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (!(double.IsFinite(r) && r > 0))
            throw new ArgumentOutOfRangeException(nameof(r), r, "must be finite and positive");
        if (!(double.IsFinite(n) && n >= 1))
            throw new ArgumentOutOfRangeException(nameof(n), n, "must be finite and at least 1");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int starts = samples.Length - m;
        if (starts < 2)
            throw new ArgumentException("samples must be at least m + 2 long", nameof(samples));
        double a = FuzzyEntropyPhi(samples, m, starts, r, n);
        double b = FuzzyEntropyPhi(samples, m + 1, starts, r, n);
        if (!(a > 0 && b > 0))
            throw new ArgumentException("the memberships underflowed to 0", nameof(samples));
        return Math.Log(a) - Math.Log(b);
    }

    private static double FuzzyEntropyPhi(ReadOnlySpan<double> samples, int length, int starts, double r, double n)
    {
        var t = new double[starts, length];
        for (int i = 0; i < starts; i++)
        {
            double mean = 0;
            for (int l = 0; l < length; l++)
                mean += samples[i + l];
            mean /= length;
            for (int l = 0; l < length; l++)
                t[i, l] = samples[i + l] - mean;
        }
        double total = 0;
        for (int i = 0; i < starts; i++)
        {
            for (int j = 0; j < starts; j++)
            {
                if (j == i)
                    continue;
                double d = 0;
                for (int l = 0; l < length; l++)
                    d = Math.Max(d, Math.Abs(t[i, l] - t[j, l]));
                total += Math.Exp(-Math.Pow(d, n) / r);
            }
        }
        return total / ((double)starts * (starts - 1));
    }
}
