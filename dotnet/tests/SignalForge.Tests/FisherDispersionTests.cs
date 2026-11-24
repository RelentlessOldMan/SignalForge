using Xunit;

namespace SignalForge.Tests;

/// <summary>Fisher's index of dispersion statistic (ADR 0615).</summary>
public class FisherDispersionTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(1.0, Measurements.FisherDispersion([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void Uneven() =>
        Assert.Equal(8.25, Measurements.FisherDispersion([4.0, 0.0, 1.0, 0.0, 3.0]), 13);

    [Fact]
    public void Even() =>
        Assert.Equal(0.0, Measurements.FisherDispersion([2.0, 2.0, 2.0]));

    [Fact]
    public void RejectsOneUnit() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FisherDispersion([5.0]));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.FisherDispersion([1e308, 0.0, 0.0]));
}
