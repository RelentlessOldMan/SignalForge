using Xunit;

namespace SignalForge.Tests;

/// <summary>Distance correlation (ADR 0372).</summary>
public class DistanceCorrelationTests
{
    [Fact]
    public void TwoPoints() =>
        Assert.Equal(1.0, Measurements.DistanceCorrelation([0.0, 1.0], [5.0, 3.0]), 1e-15);

    [Fact]
    public void Parabola()
    {
        double d = Measurements.DistanceCorrelation([-2.0, -1.0, 0.0, 1.0, 2.0], [4.0, 1.0, 0.0, 1.0, 4.0]);
        Assert.InRange(d, 0.1, 0.99);
    }

    [Fact]
    public void RejectsAConstantRecord() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.DistanceCorrelation([1.0, 2.0], [3.0, 3.0]));
}
