using Xunit;

namespace SignalForge.Tests;

/// <summary>David and Moore's index of clumping (ADR 0613).</summary>
public class DavidMooreClumpingTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(-0.5, Measurements.DavidMooreClumping([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void Uneven() =>
        Assert.Equal(17.0 / 16.0, Measurements.DavidMooreClumping([4.0, 0.0, 1.0, 0.0, 3.0]), 14);

    [Fact]
    public void OneIndividual() =>
        Assert.Equal(0.0, Measurements.DavidMooreClumping([1.0, 0.0]), 14);

    [Fact]
    public void RejectsOneUnit() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DavidMooreClumping([5.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DavidMooreClumping([0.0, 0.0]));
}
