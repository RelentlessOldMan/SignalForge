namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The G statistic of the 2x2 table of two binary records of 0 and 1: 2n times
    /// their mutual information in nats, at least 0 (conventions: the G statistic of two
    /// binary records; ADR 0481).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The statistic, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BinaryGStatistic(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long n = truth.Length, tn = n - tp - fn - fp, na = tp + fn, nb = tp + fp;
        double total = 0.0;
        total += BinaryGStatisticTerm(tp, na, nb, n);
        total += BinaryGStatisticTerm(fn, na, n - nb, n);
        total += BinaryGStatisticTerm(fp, n - na, nb, n);
        total += BinaryGStatisticTerm(tn, n - na, n - nb, n);
        return 2.0 * total;
    }

    private static double BinaryGStatisticTerm(long c, long ra, long kb, long n) =>
        c == 0 ? 0.0 : c * Math.Log((double)(n * c) / (double)(ra * kb));
}
