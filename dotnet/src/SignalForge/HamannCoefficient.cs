namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Hamann coefficient of two binary records of 0 and 1: the share of items
    /// they agree on minus the share they disagree on (conventions: Hamann coefficient;
    /// ADR 0432).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double HamannCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long u = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t != d)
                u++;
        }
        long n = truth.Length;
        return (double)(n - (2 * u)) / n;
    }
}
