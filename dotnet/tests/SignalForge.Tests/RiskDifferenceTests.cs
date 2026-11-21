using Xunit;

namespace SignalForge.Tests;

/// <summary>The risk difference (ADR 0501).</summary>
public class RiskDifferenceTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.6, Measurements.RiskDifference([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsADecisionWithNoZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RiskDifference([1.0, 0.0, 1.0], [1.0, 1.0, 1.0]));
}
