using Xunit;

namespace SignalForge.Tests;

/// <summary>The log odds ratio (ADR 0480).</summary>
public class LogOddsRatioTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(4 * Math.Log(2), Measurements.LogOddsRatio([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsAZeroCell() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LogOddsRatio([1.0, 0.0, 1.0], [1.0, 1.0, 0.0]));
}
