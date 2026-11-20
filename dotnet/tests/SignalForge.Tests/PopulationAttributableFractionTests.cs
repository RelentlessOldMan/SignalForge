using Xunit;

namespace SignalForge.Tests;

/// <summary>The population attributable fraction (ADR 0486).</summary>
public class PopulationAttributableFractionTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.6, Measurements.PopulationAttributableFraction([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsADecisionWithNoZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PopulationAttributableFraction([1.0, 0.0], [1.0, 1.0]));
}
