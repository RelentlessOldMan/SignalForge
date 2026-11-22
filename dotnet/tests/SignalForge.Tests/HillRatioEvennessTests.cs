using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hill ratio evenness (ADR 0536).</summary>
public class HillRatioEvennessTests
{
    [Fact]
    public void Two() =>
        Assert.Equal(0.4 * Math.Pow(3.0, 0.75), Measurements.HillRatioEvenness([3.0, 1.0]), 13);

    [Fact]
    public void EqualWithAZero() =>
        Assert.Equal(1.0, Measurements.HillRatioEvenness([0.0, 2.0, 2.0]), 13);

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HillRatioEvenness([0.0, 0.0]));
}
