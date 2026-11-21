using Xunit;

namespace SignalForge.Tests;

/// <summary>The Wald z of the log odds ratio (ADR 0498).</summary>
public class LogOddsRatioWaldZTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Log(16.0) * Math.Sqrt(0.4), Measurements.LogOddsRatioWaldZ([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsATableWithAZeroCell() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LogOddsRatioWaldZ([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0]));
}
