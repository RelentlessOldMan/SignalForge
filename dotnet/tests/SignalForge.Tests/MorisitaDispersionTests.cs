using Xunit;

namespace SignalForge.Tests;

/// <summary>Morisita's index of dispersion (ADR 0612).</summary>
public class MorisitaDispersionTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(0.8, Measurements.MorisitaDispersion([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void Uneven() =>
        Assert.Equal(45.0 / 28.0, Measurements.MorisitaDispersion([4.0, 0.0, 1.0, 0.0, 3.0]), 14);

    [Fact]
    public void Clumped() =>
        Assert.Equal(3.0, Measurements.MorisitaDispersion([0.0, 0.0, 6.0]), 14);

    [Fact]
    public void RejectsOneUnit() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MorisitaDispersion([5.0]));

    [Fact]
    public void RejectsTotalOfOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.MorisitaDispersion([1.0, 0.0]));
}
