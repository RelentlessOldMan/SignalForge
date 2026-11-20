namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Tarwid's coefficient of two binary records of 0 and 1: the shared 1s against
    /// chance as a difference over a sum, from −1 to below 1 (conventions: Tarwid's
    /// coefficient; ADR 0453).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TarwidCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long n = truth.Length, nt = tp + fn, nd = tp + fp;
        if (nt == 0 || nd == 0)
            throw new ArgumentException("truth and decision must each hold a 1", nameof(truth));
        return (double)((n * tp) - (nt * nd)) / (double)((n * tp) + (nt * nd));
    }
}
