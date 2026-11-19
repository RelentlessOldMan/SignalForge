using Xunit;

namespace SignalForge.Tests;

/// <summary>Rényi entropy (ADR 0353).</summary>
public class RenyiEntropyTests
{
    [Theory]
    [InlineData(0.0)]
    [InlineData(0.5)]
    [InlineData(1.0)]
    [InlineData(2.0)]
    public void AUniformHistogramIsLnKAtEveryOrder(double alpha) =>
        Assert.Equal(Math.Log(4), Measurements.RenyiEntropy([0.0, 1.0, 2.0, 3.0], alpha, 4), 1e-15);

    [Fact]
    public void CollisionByHand() =>
        Assert.Equal(Math.Log(8.0 / 5), Measurements.RenyiEntropy([0.0, 0.0, 0.0, 1.0], 2, 2), 1e-15);

    [Fact]
    public void RejectsANegativeOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RenyiEntropy([0.0, 1.0], -1));
}
