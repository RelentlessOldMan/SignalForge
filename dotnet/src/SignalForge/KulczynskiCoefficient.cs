namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Kulczynski coefficient of two binary records of 0 and 1: the mean of
    /// the shares of each record's 1s that the other also marks (conventions: Kulczynski
    /// coefficient; ADR 0428).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a record holds
    /// no 1.</exception>
    public static double KulczynskiCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
    {
        if (truth.Length != decision.Length)
            throw new ArgumentException("truth and decision must be the same length", nameof(decision));
        if (truth.Length < 1)
            throw new ArgumentException("truth and decision must not be empty", nameof(truth));
        long both = 0, nt = 0, nd = 0;
        for (int i = 0; i < truth.Length; i++)
        {
            double t = truth[i], d = decision[i];
            if (t is not (0 or 1))
                throw new ArgumentException("truth must hold only 0 and 1", nameof(truth));
            if (d is not (0 or 1))
                throw new ArgumentException("decision must hold only 0 and 1", nameof(decision));
            if (t == 1)
                nt++;
            if (d == 1)
                nd++;
            if (t == 1 && d == 1)
                both++;
        }
        if (nt == 0 || nd == 0)
            throw new ArgumentException("truth and decision must each hold at least one 1", nameof(truth));
        return (((double)both / nt) + ((double)both / nd)) / 2;
    }
}
