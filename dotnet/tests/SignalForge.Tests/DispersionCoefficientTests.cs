using Xunit;

namespace SignalForge.Tests;

/// <summary>The dispersion coefficient (ADR 0471).</summary>
public class DispersionCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(0.15, Measurements.DispersionCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsUnequalLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DispersionCoefficient([0.0, 1.0], [1.0]));
}
