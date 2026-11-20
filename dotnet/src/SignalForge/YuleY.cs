namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Yule's Y of two binary records of 0 and 1: the coefficient of colligation,
    /// from −1 to 1 (conventions: Yule's Y; ADR 0431).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>Y, from −1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or TP·TN + FN·FP is
    /// zero.</exception>
    public static double YuleY(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long tp = 0, fn = 0, fp = 0, tn = 0;
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
            else
                tn++;
        }
        long x = tp * tn, y = fn * fp;
        if (x + y == 0)
            throw new ArgumentException("TP*TN + FN*FP must not be zero", nameof(truth));
        double sx = Math.Sqrt((double)x), sy = Math.Sqrt((double)y);
        return (sx - sy) / (sx + sy);
    }
}
