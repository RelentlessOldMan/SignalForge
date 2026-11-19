using Xunit;

namespace SignalForge.Tests;

/// <summary>The average precision (ADR 0394).</summary>
public class AveragePrecisionTests
{
    [Fact]
    public void Hand() =>
        Assert.Equal(34.0 / 45, Measurements.AveragePrecision([1.0, 0.0, 1.0, 0.0, 1.0], [0.9, 0.8, 0.7, 0.6, 0.5]), 1e-15);

    [Fact]
    public void TiedPair() =>
        Assert.Equal(7.0 / 12, Measurements.AveragePrecision([1.0, 0.0, 1.0], [0.5, 0.5, 0.2]), 1e-15);

    [Fact]
    public void RejectsNoPositive() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.AveragePrecision([0.0, 0.0], [0.2, 0.4]));
}
