using Xunit;

namespace SignalForge.Tests;

/// <summary>The jackknife Shannon entropy (ADR 0558).</summary>
public class JackknifeEntropyTests
{
    [Fact]
    public void TwoOnes() =>
        Assert.Equal(2.0 * Math.Log(2.0), Measurements.JackknifeEntropy([1.0, 1.0]), 14);

    [Fact]
    public void TwoTwos() =>
        Assert.Equal(3.0 * Math.Log(4.0 / 3.0), Measurements.JackknifeEntropy([2.0, 2.0]), 14);

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.JackknifeEntropy([1.0]));
}
