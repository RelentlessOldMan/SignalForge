using Xunit;

namespace SignalForge.Tests;

/// <summary>The negative likelihood ratio (ADR 0483).</summary>
public class NegativeLikelihoodRatioTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.25, Measurements.NegativeLikelihoodRatio([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsADecisionWithNoTrueNegative() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.NegativeLikelihoodRatio([1.0, 0.0], [0.0, 1.0]));
}
