namespace SignalForge;

/// <summary>The recurrence rate, determinism and longest diagonal line of a recurrence plot
/// (conventions: Recurrence quantification; ADR 0350).</summary>
/// <param name="Rate">Recurrent points over the points outside the Theiler window.</param>
/// <param name="Determinism">Recurrent points on diagonal lines of at least the minimum length,
/// over recurrent points.</param>
/// <param name="Longest">The longest diagonal line, or 0 if there are none.</param>
public sealed record RecurrenceQuantification(double Rate, double Determinism, int Longest);

public static partial class Measurements
{
    /// <summary>Zbilut and Webber's recurrence quantification: the recurrence rate, determinism
    /// and longest diagonal line of the Chebyshev recurrence plot (conventions: Recurrence
    /// quantification; ADR 0350).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="m">The embedding dimension, at least 1.</param>
    /// <param name="radius">Points closer than this recur. Finite and positive.</param>
    /// <param name="delay">The embedding delay in samples, at least 1.</param>
    /// <param name="minLine">The shortest diagonal line that counts for determinism, at least 1.</param>
    /// <param name="theiler">The Theiler window: points need <c>j − i</c> above it. At least 0.</param>
    /// <returns>The recurrence rate, determinism and longest diagonal line.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, there is no point
    /// outside the Theiler window, or no point recurs.</exception>
    public static RecurrenceQuantification RecurrenceQuantification(ReadOnlySpan<double> samples, int m, double radius, int delay = 1, int minLine = 2, int theiler = 0)
    {
        if (m < 1)
            throw new ArgumentOutOfRangeException(nameof(m), m, "must be at least 1");
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), delay, "must be at least 1");
        if (minLine < 1)
            throw new ArgumentOutOfRangeException(nameof(minLine), minLine, "must be at least 1");
        if (theiler < 0)
            throw new ArgumentOutOfRangeException(nameof(theiler), theiler, "must be at least 0");
        if (!double.IsFinite(radius) || !(radius > 0))
            throw new ArgumentOutOfRangeException(nameof(radius), radius, "must be finite and positive");
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        long windows = samples.Length - ((long)(m - 1) * delay);
        if (windows - theiler < 2)
            throw new ArgumentException("there must be at least one point outside the Theiler window", nameof(samples));
        int w = (int)windows;
        long points = 0, recurrent = 0, onLines = 0;
        int longest = 0;
        for (int s = theiler + 1; s < w; s++)
        {
            int run = 0;
            for (int i = 0; i <= w - s; i++)
            {
                bool hit = false;
                if (i < w - s)
                {
                    points++;
                    double dist = 0;
                    for (int l = 0; l < m; l++)
                        dist = Math.Max(dist, Math.Abs(samples[i + s + (l * delay)] - samples[i + (l * delay)]));
                    hit = dist < radius;
                }
                if (hit)
                {
                    run++;
                    continue;
                }
                if (run > 0)
                {
                    recurrent += run;
                    if (run >= minLine)
                        onLines += run;
                    longest = Math.Max(longest, run);
                    run = 0;
                }
            }
        }
        if (recurrent == 0)
            throw new ArgumentException("there are no recurrent points at this radius", nameof(radius));
        return new RecurrenceQuantification((double)recurrent / points, (double)onLines / recurrent, longest);
    }
}
