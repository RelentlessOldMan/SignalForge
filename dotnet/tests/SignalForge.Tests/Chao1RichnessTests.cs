using Xunit;

namespace SignalForge.Tests;

/// <summary>The Chao1 richness (ADR 0545).</summary>
public class Chao1RichnessTests
{
    [Fact]
    public void NoTwos() =>
        Assert.Equal(11.0, Measurements.Chao1Richness([1.0, 1.0, 1.0, 1.0, 0.0, 3.0]), 15);

    [Fact]
    public void ThreeOnes() =>
        Assert.Equal(5.5, Measurements.Chao1Richness([1.0, 1.0, 1.0, 2.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.Chao1Richness([0.0, 0.0]));
}
