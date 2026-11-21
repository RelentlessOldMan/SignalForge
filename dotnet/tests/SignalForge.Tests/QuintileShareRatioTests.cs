using Xunit;

namespace SignalForge.Tests;

/// <summary>The quintile share ratio (ADR 0519).</summary>
public class QuintileShareRatioTests
{
    [Fact]
    public void Three() =>
        Assert.Equal(3.0, Measurements.QuintileShareRatio([3.0, 1.0, 2.0]), 14);

    [Fact]
    public void RampTen() =>
        Assert.Equal(19.0 / 3.0, Measurements.QuintileShareRatio([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]), 14);

    [Fact]
    public void RejectsAnEmptyBottom() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.QuintileShareRatio([0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]));
}
