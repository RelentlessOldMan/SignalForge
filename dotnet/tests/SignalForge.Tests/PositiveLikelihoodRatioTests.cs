using Xunit;

namespace SignalForge.Tests;

/// <summary>The positive likelihood ratio (ADR 0482).</summary>
public class PositiveLikelihoodRatioTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(4.0, Measurements.PositiveLikelihoodRatio([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsADecisionWithNoFalsePositive() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PositiveLikelihoodRatio([1.0, 0.0], [1.0, 0.0]));
}
