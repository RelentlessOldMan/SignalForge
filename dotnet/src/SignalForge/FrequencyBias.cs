namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The frequency bias of a binary decision against a binary truth, records of 0
    /// and 1: the decision's 1s over the truth's, at least 0 (conventions: the frequency bias;
    /// ADR 0488).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The bias, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double FrequencyBias(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, fn = 0, fp = 0;
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
            else if (d == 1)
                fp++;
        }
        if (tp + fn == 0)
            throw new ArgumentException("truth must hold a 1", nameof(truth));
        return (double)(tp + fp) / (tp + fn);
    }
}
