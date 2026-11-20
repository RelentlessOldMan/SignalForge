namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Rogot-Goldberg coefficient of two binary records of 0 and 1: the mean
    /// of the Dice coefficients of the 1s and of the 0s, from 0 to 1 (conventions: the
    /// Rogot-Goldberg coefficient; ADR 0467).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double RogotGoldbergCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        long ones = (2 * tp) + fn + fp, zeros = (2 * tn) + fn + fp;
        if (ones == 0 || zeros == 0)
            throw new ArgumentException("truth and decision must not both be all 0 or both all 1", nameof(truth));
        return ((double)tp / ones) + ((double)tn / zeros);
    }
}
