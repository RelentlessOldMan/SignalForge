using Xunit;

namespace SignalForge.Tests;

/// <summary>Hurlbert's PIE (ADR 0548).</summary>
public class HurlbertPieTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(11.0 / 15.0, Measurements.HurlbertPie([1.0, 2.0, 3.0]), 15);

    [Fact]
    public void TwoOnes() =>
        Assert.Equal(1.0, Measurements.HurlbertPie([1.0, 1.0]), 15);

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HurlbertPie([0.5, 0.5]));
}
