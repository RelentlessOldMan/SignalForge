using Xunit;

namespace SignalForge.Tests;

/// <summary>Higuchi fractal dimension (ADR 0330).</summary>
public class HiguchiDimensionTests
{
    [Fact]
    public void ALineHasDimensionOne()
    {
        double[] x = new double[40];
        for (int i = 0; i < x.Length; i++)
            x[i] = 3 - (0.25 * i);
        Assert.Equal(1.0, Measurements.HiguchiDimension(x, 10), 1e-13);
    }

    [Fact]
    public void ShortZigzagByHand()
    {
        // 1, −1, 1, −1: L(1) = 6·3/3 = 6; at k = 2 each start is flat, so L(2) = 0 is rejected.
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HiguchiDimension([1.0, -1.0, 1.0, -1.0], 2));
    }

    [Fact]
    public void RejectsKMaxAboveHalf() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HiguchiDimension([0.0, 1.0, 3.0, 2.0, 5.0], 3));
}
