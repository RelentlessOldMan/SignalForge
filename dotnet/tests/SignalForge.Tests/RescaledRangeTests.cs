using Xunit;

namespace SignalForge.Tests;

/// <summary>Rescaled range and the Hurst exponent (ADR 0340).</summary>
public class RescaledRangeTests
{
    [Fact]
    public void RampByHand()
    {
        // s = 4: y = −1.5, −0.5, 0.5, 1.5; Z = −1.5, −2, −1.5, 0; R = 2, S = √(5/4).
        RescaledRange r = Measurements.RescaledRange([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0], [4, 8]);
        Assert.Equal(2 / Math.Sqrt(1.25), r.Values[0], 1e-15);
        Assert.Equal([4, 8], r.Scales);
    }

    [Fact]
    public void AlternatingHasHurstZero()
    {
        double[] x = new double[16];
        for (int i = 0; i < x.Length; i++)
            x[i] = i % 2 == 0 ? 1 : -1;
        Assert.Equal(0.0, Measurements.RescaledRange(x, [4, 8, 16]).Hurst, 1e-15);
    }

    [Fact]
    public void RejectsAConstantBox() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.RescaledRange([2.0, 2.0, 2.0, 2.0, 1.0, 3.0, 0.0, 1.0], [4, 8]));
}
