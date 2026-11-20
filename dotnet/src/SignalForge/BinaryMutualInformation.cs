namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The mutual information of two binary records of 0 and 1: that of their 2x2
    /// table, in nats, 0 at independence (conventions: binary mutual information;
    /// ADR 0464).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The mutual information in nats, at least 0 up to rounding.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BinaryMutualInformation(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        total += BinaryMutualInformationTerm(tp, na, nb, n);
        total += BinaryMutualInformationTerm(fn, na, n - nb, n);
        total += BinaryMutualInformationTerm(fp, n - na, nb, n);
        total += BinaryMutualInformationTerm(tn, n - na, n - nb, n);
        return total;
    }

    private static double BinaryMutualInformationTerm(long c, long ra, long kb, long n) =>
        c == 0 ? 0.0 : (double)c / n * Math.Log((double)(n * c) / (double)(ra * kb));
}
