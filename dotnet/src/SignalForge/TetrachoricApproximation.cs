namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Pearson's cosine approximation to the tetrachoric correlation of two binary
    /// records of 0 and 1: cos(pi / (1 + sqrt(OR))) with OR the odds ratio, from -1 to 1
    /// (conventions: the tetrachoric approximation; ADR 0492).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <returns>The correlation, from -1 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TetrachoricApproximation(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision)
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
        if (fn * fp == 0)
            throw new ArgumentException("the records must disagree both ways", nameof(decision));
        return Math.Cos(Math.PI / (1.0 + Math.Sqrt((double)(tp * tn) / (double)(fn * fp))));
    }
}
