using Xunit;

namespace SignalForge.Tests;

/// <summary>Sen's slope (ADR 0365).</summary>
public class SensSlopeTests
{
    [Fact]
    public void OutlierByHand()
    {
        // Slopes 1, 1, 1, 10, 29/2, 28: the middle two average to 11/2.
        Assert.Equal(5.5, Measurements.SensSlope([0.0, 1.0, 2.0, 30.0]));
    }

    [Fact]
    public void OddCount() =>
        Assert.Equal(-0.5, Measurements.SensSlope([3.0, 1.0, 2.0]));

    [Fact]
    public void RejectsOneSample() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SensSlope([1.0]));
}
