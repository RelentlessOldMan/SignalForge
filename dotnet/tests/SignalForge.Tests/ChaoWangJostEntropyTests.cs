using Xunit;

namespace SignalForge.Tests;

/// <summary>The Chao-Wang-Jost entropy (ADR 0562).</summary>
public class ChaoWangJostEntropyTests
{
    [Fact]
    public void TwoOnes() =>
        Assert.Equal(3.0 * Math.Log(1.5), Measurements.ChaoWangJostEntropy([1.0, 1.0]), 13);

    [Fact]
    public void OneEach() =>
        Assert.Equal(4.0 * Math.Log(2.0) / 3.0, Measurements.ChaoWangJostEntropy([1.0, 2.0]), 13);

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ChaoWangJostEntropy([1.0]));
}
