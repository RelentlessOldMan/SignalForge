namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The prevalence threshold of a binary decision against a binary truth,
    /// records of 0 and 1: (sqrt(TPR FPR) - FPR) / (TPR - FPR), from 0 to 1 (conventions: the
    /// prevalence threshold; ADR 0487).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The threshold, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double PrevalenceThreshold(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long a = tp + fn, b = truth.Length - a;
        if (a == 0 || b == 0)
            throw new ArgumentException("truth must hold both 0 and 1", nameof(truth));
        long den = (tp * b) - (fp * a);
        if (den == 0)
            throw new ArgumentException("the true and false positive rates must differ", nameof(decision));
        return (Math.Sqrt((double)(tp * fp) * (double)(a * b)) - (double)(fp * a)) / den;
    }
}
