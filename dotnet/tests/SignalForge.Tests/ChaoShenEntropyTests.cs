using Xunit;

namespace SignalForge.Tests;

/// <summary>The Chao-Shen entropy (ADR 0554).</summary>
public class ChaoShenEntropyTests
{
    [Fact]
    public void TwoTwos() =>
        Assert.Equal(16.0 / 15.0 * Math.Log(2.0), Measurements.ChaoShenEntropy([2.0, 2.0]), 14);

    [Fact]
    public void TwoOnes() =>
        Assert.Equal(16.0 / 7.0 * Math.Log(2.0), Measurements.ChaoShenEntropy([1.0, 1.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ChaoShenEntropy([0.0, 0.0]));
}
