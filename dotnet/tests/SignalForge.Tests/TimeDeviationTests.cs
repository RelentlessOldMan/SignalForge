using Xunit;

namespace SignalForge.Tests;

/// <summary>Time deviation (ADR 0331).</summary>
public class TimeDeviationTests
{
    [Fact]
    public void AlternatingSamplesByHand()
    {
        AllanDeviation t = Measurements.TimeDeviation([1.0, -1.0, 1.0, -1.0, 1.0, -1.0], 2, [1]);
        Assert.Equal(2.0 * Math.Sqrt(2.0 / 3), t.Deviations[0], 1e-15);
    }

    [Fact]
    public void RejectsTooLargeAFactor() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TimeDeviation([0.0, 1.0, 2.0, 3.0], 1, [2]));
}
