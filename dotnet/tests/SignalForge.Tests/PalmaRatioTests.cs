using Xunit;

namespace SignalForge.Tests;

/// <summary>The Palma ratio (ADR 0518).</summary>
public class PalmaRatioTests
{
    [Fact]
    public void Three() =>
        Assert.Equal(9.0 / 14.0, Measurements.PalmaRatio([3.0, 1.0, 2.0]), 15);

    [Fact]
    public void Equal() =>
        Assert.Equal(0.25, Measurements.PalmaRatio([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]), 15);

    [Fact]
    public void RejectsAnEmptyBottom() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PalmaRatio([0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]));
}
