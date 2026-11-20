using Xunit;

namespace SignalForge.Tests;

/// <summary>Stiles' coefficient (ADR 0451).</summary>
public class StilesCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Log10(1.6), Measurements.StilesCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsACrossDifferenceOfHalfN() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.StilesCoefficient([1.0, 0.0, 0.0, 0.0], [1.0, 1.0, 0.0, 0.0]));
}
