using Xunit;

namespace SignalForge.Tests;

/// <summary>Dispersion entropy (ADR 0341).</summary>
public class DispersionEntropyTests
{
    [Fact]
    public void TwoLevelsGiveOne() =>
        Assert.Equal(1.0, Measurements.DispersionEntropy([1.0, -1.0, 1.0, -1.0, 1.0, -1.0], 1, 2), 1e-15);

    [Fact]
    public void OnePatternGivesZero() =>
        Assert.Equal(0.0, Measurements.DispersionEntropy([0.3, -0.7, 1.1], 3, 3), 1e-15);

    [Fact]
    public void RejectsOneClass() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DispersionEntropy([0.0, 1.0, 2.0], 1, 1));
}
