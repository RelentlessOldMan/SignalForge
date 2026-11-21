namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Cohen's h of two binary records of 0 and 1, the decision as the exposure: the
    /// difference of 2 asin(sqrt(share)) for the share of truth 1s where the decision is 1 and
    /// where it is 0, from -pi to pi (conventions: Cohen's h; ADR 0506).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>Cohen's h, from -pi to pi.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double CohenH(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long tn = truth.Length - tp - fn - fp;
        if (tp + fp == 0 || fn + tn == 0)
            throw new ArgumentException("the decision must hold both 0 and 1", nameof(decision));
        double ha = Math.Atan2(Math.Sqrt(tp), Math.Sqrt(fp));
        double hb = Math.Atan2(Math.Sqrt(fn), Math.Sqrt(tn));
        return 2.0 * (ha - hb);
    }
}
