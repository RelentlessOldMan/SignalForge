using Xunit;

namespace SignalForge.Tests;

/// <summary>Biweight midcorrelation (ADR 0373).</summary>
public class BiweightMidcorrelationTests
{
    [Fact]
    public void ByHand() =>
        Assert.Equal(-0.5, Measurements.BiweightMidcorrelation([-1.0, 0.0, 1.0], [0.0, 1.0, -1.0]), 1e-15);

    [Fact]
    public void OutlierCutOff() =>
        Assert.Equal(1.0, Measurements.BiweightMidcorrelation([1.0, 2.0, 3.0, 4.0, 5.0, 100.0], [1.0, 2.0, 3.0, 4.0, 5.0, 200.0]), 1e-15);

    [Fact]
    public void RejectsAZeroMad() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.BiweightMidcorrelation([1.0, 1.0, 2.0], [1.0, 2.0, 3.0]));
}
