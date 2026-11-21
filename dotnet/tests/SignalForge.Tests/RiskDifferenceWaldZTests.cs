using Xunit;

namespace SignalForge.Tests;

/// <summary>The Wald z of the risk difference (ADR 0503).</summary>
public class RiskDifferenceWaldZTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(3.0 * Math.Sqrt(10.0) / 4.0, Measurements.RiskDifferenceWaldZ([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsEqualRecords() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RiskDifferenceWaldZ([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0]));
}
