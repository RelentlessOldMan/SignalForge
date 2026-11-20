using Xunit;

namespace SignalForge.Tests;

/// <summary>The relative risk (ADR 0484).</summary>
public class RelativeRiskTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(4.0, Measurements.RelativeRisk([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsADecisionWithNoFalseNegative() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RelativeRisk([1.0, 0.0], [1.0, 0.0]));
}
