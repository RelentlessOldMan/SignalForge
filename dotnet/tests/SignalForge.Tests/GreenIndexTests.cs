using Xunit;

namespace SignalForge.Tests;

/// <summary>Green's index of dispersion (ADR 0611).</summary>
public class GreenIndexTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(-0.1, Measurements.GreenIndex([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void Uneven() =>
        Assert.Equal(17.0 / 112.0, Measurements.GreenIndex([4.0, 0.0, 1.0, 0.0, 3.0]), 14);

    [Fact]
    public void Clumped() =>
        Assert.Equal(1.0, Measurements.GreenIndex([0.0, 0.0, 6.0]), 14);

    [Fact]
    public void RejectsOneUnit() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GreenIndex([5.0]));

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GreenIndex([1.0, 0.0]));
}
