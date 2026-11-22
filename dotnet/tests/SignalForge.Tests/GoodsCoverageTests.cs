using Xunit;

namespace SignalForge.Tests;

/// <summary>Good's coverage (ADR 0544).</summary>
public class GoodsCoverageTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(7.0 / 9.0, Measurements.GoodsCoverage([5.0, 1.0, 1.0, 0.0, 2.0]), 15);

    [Fact]
    public void AllOnes() =>
        Assert.Equal(0.0, Measurements.GoodsCoverage([1.0, 1.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GoodsCoverage([0.0, 0.0]));
}
