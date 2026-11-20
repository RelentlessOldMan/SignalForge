namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Austin-Colwell coefficient of two binary records of 0 and 1: the
    /// arcsine-transformed simple matching coefficient, from 0 to 1 (conventions: the
    /// Austin-Colwell coefficient; ADR 0448).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The coefficient, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double AustinColwellCoefficient(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        double p = (double)(tp + tn) / (double)(tp + fn + fp + tn);
        return Math.Asin(Math.Sqrt(p)) * 2.0 / Math.PI;
    }
}
