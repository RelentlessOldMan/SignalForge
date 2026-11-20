namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The extreme dependency score of a binary decision against a binary truth,
    /// records of 0 and 1: 2 ln(|A|/n) / ln(TP/n) - 1, from -1 to 1 (conventions: the extreme
    /// dependency score; ADR 0489).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The score, from -1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ExtremeDependencyScore(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, fn = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t == 1 && d == 1)
                tp++;
            else if (t == 1)
                fn++;
        }
        if (tp == 0)
            throw new ArgumentException("truth and decision must share a 1", nameof(decision));
        if (tp == truth.Length)
            throw new ArgumentException("truth and decision must not be all 1", nameof(decision));
        double n = truth.Length;
        return (2.0 * Math.Log((tp + fn) / n) / Math.Log(tp / n)) - 1.0;
    }
}
