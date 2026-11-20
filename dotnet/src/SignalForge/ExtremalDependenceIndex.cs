namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The extremal dependence index of a binary decision against a binary truth,
    /// records of 0 and 1: (ln F - ln H) / (ln F + ln H) with H the hit rate and F the false
    /// alarm rate, from -1 to 1 (conventions: the extremal dependence index; ADR 0490).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The index, from -1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ExtremalDependenceIndex(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        if (tp == 0)
            throw new ArgumentException("truth and decision must share a 1", nameof(decision));
        if (fp == 0)
            throw new ArgumentException("the decision must have a false positive", nameof(decision));
        if (tp == a && fp == b)
            throw new ArgumentException("decision must hold a 0", nameof(decision));
        double lf = Math.Log((double)fp / b), lh = Math.Log((double)tp / a);
        return (lf - lh) / (lf + lh);
    }
}
