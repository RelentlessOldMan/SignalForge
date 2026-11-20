namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Mountford's coefficient of two binary records of 0 and 1: twice the shared
    /// 1s over the products of the counts, at least 0 (conventions: Mountford's coefficient;
    /// ADR 0452).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double MountfordCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long den = (tp * fn) + (tp * fp) + (2 * fn * fp);
        if (den == 0)
            throw new ArgumentException("TP FN + TP FP + 2 FN FP must not be zero", nameof(truth));
        return (double)(2 * tp) / (double)den;
    }
}
