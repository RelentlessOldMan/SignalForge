using Xunit;

namespace SignalForge.Tests;

/// <summary>Tsallis entropy (ADR 0356).</summary>
public class TsallisEntropyTests
{
    [Fact]
    public void Q2ByHand() =>
        Assert.Equal(0.375, Measurements.TsallisEntropy([0.0, 0.0, 0.0, 1.0], 2, 2), 1e-15);

    [Fact]
    public void Q0CountsTheOccupiedBins() =>
        Assert.Equal(2.0, Measurements.TsallisEntropy([0.0, 0.0, 0.0, 0.25, 1.0], 0, 8), 1e-15);

    [Fact]
    public void Q1IsShannon() =>
        Assert.Equal(Math.Log(4), Measurements.TsallisEntropy([0.0, 1.0, 2.0, 3.0], 1, 4), 1e-15);

    [Fact]
    public void RejectsANegativeOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TsallisEntropy([0.0, 1.0], -1));
}
