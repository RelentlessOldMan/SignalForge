using Xunit;

namespace SignalForge.Tests;

/// <summary>Fisher's alpha (ADR 0550).</summary>
public class FisherAlphaTests
{
    [Fact]
    public void SolvesTheLogSeries()
    {
        double a = Measurements.FisherAlpha([5.0, 1.0, 1.0, 0.0, 2.0]);
        Assert.Equal(4.0, a * Math.Log(1.0 + (9.0 / a)), 12);
    }

    [Fact]
    public void DependsOnlyOnTheCounts() =>
        Assert.Equal(Measurements.FisherAlpha([3.0, 1.0]), Measurements.FisherAlpha([2.0, 2.0]));

    [Fact]
    public void RejectsAllOnes() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FisherAlpha([1.0, 1.0]));
}
