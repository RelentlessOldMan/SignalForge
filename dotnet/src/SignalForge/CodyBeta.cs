namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Cody's beta of the records <paramref name="x"/> and <paramref name="y"/> of
    /// values at least 0, each with a value above 0: (b + c)/2 on the kinds above 0, the mean
    /// of the kinds gained and lost, from 0 to the record length (conventions: Cody's beta;
    /// ADR 0590).</summary>
    /// <param name="x">The first record, finite, at least 0, with a value above 0.</param>
    /// <param name="y">The second record, finite, at least 0, with a value above 0, the same
    /// length as x.</param>
    /// <returns>Cody's beta, from 0 to the record length.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CodyBeta(ReadOnlySpan<double> x, ReadOnlySpan<double> y)
    {
        PiankaTop(x, nameof(x));
        PiankaTop(y, nameof(y));
        if (x.Length != y.Length)
            throw new ArgumentException("x and y must have the same length", nameof(y));
        int onlyX = 0, onlyY = 0;
        for (int i = 0; i < x.Length; i++)
        {
            if (x[i] > 0 && y[i] > 0)
                continue;
            if (x[i] > 0)
                onlyX++;
            else if (y[i] > 0)
                onlyY++;
        }
        return (onlyX + onlyY) / 2.0;
    }
}
