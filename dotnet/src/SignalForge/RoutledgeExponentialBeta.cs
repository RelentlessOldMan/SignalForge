namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Routledge's exponential beta of the records <paramref name="x"/> and
    /// <paramref name="y"/> of values at least 0, each with a value above 0: exp(beta_I) - 1,
    /// with beta_I Routledge's information beta; from 0 to 1 (conventions: Routledge's
    /// exponential beta; ADR 0596).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>Routledge's exponential beta, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double RoutledgeExponentialBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        PiankaTop(x, nameof(x));
        PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        int both = 0, onlyX = 0, onlyY = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (x[i] > 0 && y[i] > 0)
                both++;
            else if (x[i] > 0)
                onlyX++;
            else if (y[i] > 0)
                onlyY++;
        }
        double p = both + onlyX;
        double q = both + onlyY;
        double n = p + q;
        double total = 2.0 * both * Math.Log(2.0) + (p * Math.Log(p) + q * Math.Log(q));
        return Math.Exp(Math.Max(0.0, Math.Log(n) - total / n)) - 1.0;
    }
}
