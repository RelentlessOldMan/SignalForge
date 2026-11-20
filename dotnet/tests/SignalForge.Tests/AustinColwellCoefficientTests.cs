using Xunit;

namespace SignalForge.Tests;

/// <summary>The Austin-Colwell coefficient (ADR 0448).</summary>
public class AustinColwellCoefficientTests
{
    [Fact]
    public void Quarter() =>
        Assert.Equal(1.0 / 3.0, Measurements.AustinColwellCoefficient([1, 1, 0, 0], [1, 0, 1, 1]), 14);

    [Fact]
    public void RejectsRecordsOfDifferentLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AustinColwellCoefficient([0.0, 1.0], [0.0]));
}
