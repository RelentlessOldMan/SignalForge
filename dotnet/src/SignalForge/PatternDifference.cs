namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The pattern difference of two binary records of 0 and 1: four times the
    /// product of the shares of the two kinds of disagreement, from 0 to 1 (conventions: the
    /// pattern difference; ADR 0474).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The difference, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PatternDifference(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long fn = 0, fp = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t != d)
            {
                if (t == 1)
                    fn++;
                else
                    fp++;
            }
        }
        long n = truth.Length;
        return (double)(4 * fn * fp) / (n * n);
    }
}
