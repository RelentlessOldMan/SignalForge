namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The log loss of the forecast <paramref name="probability"/> of a binary event
    /// against the <paramref name="outcome"/>, 0 or 1: the negative mean natural log-likelihood,
    /// in nats (conventions: Log loss; ADR 0392).</summary>
    /// <param name="outcome">The outcomes, 0 or 1; at least 1.</param>
    /// <param name="probability">The forecast probabilities of the event, in [0, 1]; the same
    /// length as <paramref name="outcome"/>.</param>
    /// <returns>The loss, at least 0.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or a certain forecast
    /// was wrong.</exception>
    public static double LogLoss(ReadOnlySpan<double> outcome, ReadOnlySpan<double> probability)
    {
        if (outcome.Length != probability.Length)
            throw new ArgumentException("outcome and probability must be the same length", nameof(probability));
        if (outcome.Length < 1)
            throw new ArgumentException("outcome and probability must not be empty", nameof(outcome));
        for (int i = 0; i < outcome.Length; i++)
        {
            if (outcome[i] is not (0 or 1))
                throw new ArgumentException("outcome must hold only 0 and 1", nameof(outcome));
            if (!(probability[i] >= 0 && probability[i] <= 1))
                throw new ArgumentException("probability must be in [0, 1]", nameof(probability));
        }
        double total = 0;
        for (int i = 0; i < outcome.Length; i++)
        {
            double q = outcome[i] == 1 ? probability[i] : 1.0 - probability[i];
            if (q == 0)
                throw new ArgumentException("a forecast of certainty was wrong: the loss is infinite", nameof(probability));
            total += Math.Log(q);
        }
        return -total / outcome.Length;
    }
}
