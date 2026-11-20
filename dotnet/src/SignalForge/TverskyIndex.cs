namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Tversky index of two binary records of 0 and 1: the items both mark 1
    /// over those plus <paramref name="alpha"/> times the items only <paramref name="truth"/>
    /// marks and <paramref name="beta"/> times the items only <paramref name="decision"/>
    /// marks (conventions: Tversky index; ADR 0423).</summary>
    /// <param name="truth">The first record, 0 or 1; at least 1.</param>
    /// <param name="decision">The second record, 0 or 1; the same length as
    /// <paramref name="truth"/>.</param>
    /// <param name="alpha">The weight on items only truth marks, finite and at least 0.</param>
    /// <param name="beta">The weight on items only decision marks, finite and at least
    /// 0.</param>
    /// <returns>The index, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the denominator
    /// is zero.</exception>
    public static double TverskyIndex(ReadOnlySpan<double> truth, ReadOnlySpan<double> decision, double alpha, double beta)
    {
        if (!double.IsFinite(alpha) || !(alpha >= 0))
            throw new ArgumentOutOfRangeException(nameof(alpha), alpha, "must be finite and at least 0");
        if (!double.IsFinite(beta) || !(beta >= 0))
            throw new ArgumentOutOfRangeException(nameof(beta), beta, "must be finite and at least 0");
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
        double den = (tp + (alpha * fn)) + (beta * fp);
        if (den == 0)
            throw new ArgumentException("the denominator TP + alpha*FN + beta*FP is zero", nameof(truth));
        return tp / den;
    }
}
