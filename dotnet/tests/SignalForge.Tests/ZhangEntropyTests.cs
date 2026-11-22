using Xunit;

namespace SignalForge.Tests;

/// <summary>Zhang's entropy (ADR 0561).</summary>
public class ZhangEntropyTests
{
    [Fact]
    public void TwoOnes() =>
        Assert.Equal(1.0, Measurements.ZhangEntropy([1.0, 1.0]), 14);

    [Fact]
    public void TwoTwos() =>
        Assert.Equal(5.0 / 6.0, Measurements.ZhangEntropy([2.0, 2.0]), 14);

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ZhangEntropy([1.0]));
}
