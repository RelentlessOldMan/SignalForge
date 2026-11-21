using Xunit;

namespace SignalForge.Tests;

/// <summary>The mean log deviation (ADR 0514).</summary>
public class MeanLogDeviationTests
{
    [Fact]
    public void Halves() =>
        Assert.Equal(Math.Log(2.0) / 4.0, Measurements.MeanLogDeviation([0.5, 0.25, 0.25, 1.0]), 15);

    [Fact]
    public void Equal() =>
        Assert.Equal(0.0, Measurements.MeanLogDeviation([2.0, 2.0, 2.0]), 15);

    [Fact]
    public void RejectsAZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MeanLogDeviation([1.0, 0.0]));
}
