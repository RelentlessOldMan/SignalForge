namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Brier score of the forecast <paramref name="probability"/> of a binary event
    /// against the <paramref name="outcome"/>, 0 or 1: the mean squared difference, from 0 to 1
    /// (conventions: Brier score; ADR 0391).</summary>
    /// <param name="outcome">The outcomes, 0 or 1; at least 1.</param>
    /// <param name="probability">The forecast probabilities of the event, in [0, 1]; the same
    /// length as <paramref name="outcome"/>.</param>
    /// <returns>The score, from 0 to 1.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BrierScore(ReadOnlySpan<double> outcome, ReadOnlySpan<double> probability)
    {
        if (outcome.Length != probability.Length)
            throw new ArgumentException("outcome and probability must be the same length", nameof(probability));
        if (outcome.Length < 1)
            throw new ArgumentException("outcome and probability must not be empty", nameof(outcome));
        double total = 0;
        for (int i = 0; i < outcome.Length; i++)
        {
            double y = outcome[i], p = probability[i];
            if (y is not (0 or 1))
                throw new ArgumentException("outcome must hold only 0 and 1", nameof(outcome));
            if (!(p >= 0 && p <= 1))
                throw new ArgumentException("probability must be in [0, 1]", nameof(probability));
            total += (p - y) * (p - y);
        }
        return total / outcome.Length;
    }
}
