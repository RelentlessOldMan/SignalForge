using Xunit;

namespace SignalForge.Tests;

/// <summary>The standard error of the log odds ratio (ADR 0493).</summary>
public class LogOddsRatioStandardErrorTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Sqrt(2.5), Measurements.LogOddsRatioStandardError([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsATableWithAZeroCell() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LogOddsRatioStandardError([1.0, 0.0, 1.0, 0.0], [1.0, 0.0, 1.0, 0.0]));
}
