using Xunit;

namespace SignalForge.Tests;

/// <summary>The standard error of the risk difference (ADR 0502).</summary>
public class RiskDifferenceStandardErrorTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(2.0 * Math.Sqrt(10.0) / 25.0, Measurements.RiskDifferenceStandardError([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsADecisionWithNoOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RiskDifferenceStandardError([1.0, 0.0, 1.0], [0.0, 0.0, 0.0]));
}
