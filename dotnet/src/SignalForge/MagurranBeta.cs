namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Magurran's beta of the records <paramref name="x"/> and <paramref name="y"/>
    /// of values at least 0, each with a value above 0: (2a + b + c)(1 - a/(a + b + c)) on
    /// the kinds above 0, from 0 to twice the record length (conventions: Magurran's beta;
    /// ADR 0592).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>Magurran's beta, from 0 to twice the record length.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MagurranBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
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
        long unshared = onlyX + onlyY;
        return (double)((2L * both + unshared) * unshared) / (both + unshared);
    }
}
