using Xunit;

namespace SignalForge.Tests;

/// <summary>The Hill number (ADR 0563).</summary>
public class HillNumberTests
{
    [Fact]
    public void InverseSimpson() =>
        Assert.Equal(8.0 / 3.0, Measurements.HillNumber([1.0, 1.0, 2.0], 2.0), 13);

    [Fact]
    public void Shannon() =>
        Assert.Equal(Math.Pow(2.0, 1.5), Measurements.HillNumber([1.0, 1.0, 2.0], 1.0), 13);

    [Fact]
    public void ContinuousAtOne() =>
        Assert.Equal(
            Measurements.HillNumber([2.0, 0.5, 3.25, 1.0], 1.0),
            Measurements.HillNumber([2.0, 0.5, 3.25, 1.0], 1.0 + 1e-9),
            7);

    [Fact]
    public void RejectsNegativeOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HillNumber([1.0], -1.0));
}
