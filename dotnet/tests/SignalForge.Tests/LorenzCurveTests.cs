using Xunit;

namespace SignalForge.Tests;

/// <summary>The Lorenz curve (ADR 0517).</summary>
public class LorenzCurveTests
{
    [Fact]
    public void Ramp() =>
        Assert.Equal([0.0, 0.1, 0.3, 0.6, 1.0], Measurements.LorenzCurve([4.0, 1.0, 3.0, 2.0]));

    [Fact]
    public void OneValue() =>
        Assert.Equal([0.0, 1.0], Measurements.LorenzCurve([5.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LorenzCurve([0.0, 0.0]));
}
