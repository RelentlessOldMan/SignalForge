using Xunit;

namespace SignalForge.Tests;

/// <summary>The Gower-Legendre coefficient (ADR 0455).</summary>
public class GowerLegendreCoefficientTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(8.0 / 9.0, Measurements.GowerLegendreCoefficient([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsRecordsOfDifferentLengths() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GowerLegendreCoefficient([1.0, 0.0], [1.0]));
}
