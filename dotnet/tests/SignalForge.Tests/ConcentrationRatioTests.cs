using Xunit;

namespace SignalForge.Tests;

/// <summary>The concentration ratio (ADR 0524).</summary>
public class ConcentrationRatioTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal(0.7, Measurements.ConcentrationRatio([4.0, 1.0, 3.0, 2.0], 2), 15);

    [Fact]
    public void Halves() =>
        Assert.Equal(0.875, Measurements.ConcentrationRatio([0.5, 0.25, 0.25, 1.0], 3), 15);

    [Fact]
    public void RejectsTooManyValues() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ConcentrationRatio([1.0, 2.0], 3));
}
