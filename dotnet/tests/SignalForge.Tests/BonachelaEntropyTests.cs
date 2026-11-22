using Xunit;

namespace SignalForge.Tests;

/// <summary>The Bonachela entropy (ADR 0560).</summary>
public class BonachelaEntropyTests
{
    [Fact]
    public void TwoOnes() =>
        Assert.Equal(7.0 / 12.0, Measurements.BonachelaEntropy([1.0, 1.0]), 14);

    [Fact]
    public void TwoTwos() =>
        Assert.Equal(37.0 / 60.0, Measurements.BonachelaEntropy([2.0, 2.0]), 14);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BonachelaEntropy([0.0, 0.0]));
}
