using Xunit;

namespace SignalForge.Tests;

/// <summary>The Grassberger entropy (ADR 0559).</summary>
public class GrassbergerEntropyTests
{
    private const double Euler = 0.5772156649015329;

    [Fact]
    public void TwoOnes() =>
        Assert.Equal((2.0 * Math.Log(2.0)) + Euler, Measurements.GrassbergerEntropy([1.0, 1.0]), 14);

    [Fact]
    public void TwoTwos() =>
        Assert.Equal((3.0 * Math.Log(2.0)) + Euler - 2.0, Measurements.GrassbergerEntropy([2.0, 2.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GrassbergerEntropy([0.0, 0.0]));
}
