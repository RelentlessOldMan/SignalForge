using Xunit;

namespace SignalForge.Tests;

/// <summary>The Wald z of Cohen's h (ADR 0508).</summary>
public class CohenHWaldZTests
{
    [Fact]
    public void ThreeQuarters() =>
        Assert.Equal(Math.PI * Math.Sqrt(2.0) / 3.0, Measurements.CohenHWaldZ([1, 1, 1, 0, 1, 0, 0, 0], [1, 1, 1, 1, 0, 0, 0, 0]), 14);

    [Fact]
    public void RejectsADecisionWithNoZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.CohenHWaldZ([1.0, 0.0, 1.0], [1.0, 1.0, 1.0]));
}
