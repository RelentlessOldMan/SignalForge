using Xunit;

namespace SignalForge.Tests;

/// <summary>The Miller-Madow entropy (ADR 0555).</summary>
public class MillerMadowEntropyTests
{
    [Fact]
    public void TwoTwos() =>
        Assert.Equal(Math.Log(2.0) + 0.125, Measurements.MillerMadowEntropy([2.0, 2.0]), 14);

    [Fact]
    public void OneKind() =>
        Assert.Equal(0.0, Measurements.MillerMadowEntropy([0.0, 4.0]), 15);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MillerMadowEntropy([0.0, 0.0]));
}
