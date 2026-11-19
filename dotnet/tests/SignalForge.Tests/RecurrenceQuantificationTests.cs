using Xunit;

namespace SignalForge.Tests;

/// <summary>Recurrence quantification (ADR 0350).</summary>
public class RecurrenceQuantificationTests
{
    [Fact]
    public void PeriodThreeByHand()
    {
        // Twelve samples of period 3: the diagonals 3, 6 and 9 recur, 18 of 66 points, each
        // one line, the longest 9.
        double[] x = [0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 0.0, 1.0, 2.0, 0.0, 1.0, 2.0];
        var got = Measurements.RecurrenceQuantification(x, 1, 0.5);
        Assert.Equal(18.0 / 66, got.Rate, 1e-15);
        Assert.Equal(1.0, got.Determinism);
        Assert.Equal(9, got.Longest);
    }

    [Fact]
    public void AnIsolatedPointIsNotDeterministic()
    {
        var got = Measurements.RecurrenceQuantification([0.0, 4.0, 1.0, 5.0, 0.25], 1, 0.5);
        Assert.Equal(0.1, got.Rate, 1e-15);
        Assert.Equal(0.0, got.Determinism);
        Assert.Equal(1, got.Longest);
    }

    [Fact]
    public void RejectsNoRecurrence() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RecurrenceQuantification([0.0, 1.0, 2.0], 1, 0.5));
}
