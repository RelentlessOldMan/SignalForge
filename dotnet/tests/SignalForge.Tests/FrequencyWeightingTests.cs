using Xunit;

namespace SignalForge.Tests;

/// <summary>A and C weightings (conventions: Frequency weightings; ADR 0164).</summary>
public class FrequencyWeightingTests
{
    [Fact]
    public void ExactlyZeroAt1KhzAndMinusInfAtDc()
    {
        Assert.Equal(0.0, Units.AWeighting(1000));
        Assert.Equal(0.0, Units.CWeighting(1000));
        Assert.Equal(double.NegativeInfinity, Units.AWeighting(0));
        Assert.Equal(double.NegativeInfinity, Units.CWeighting(0));
    }

    [Theory]
    [InlineData(-10, -19.1, -0.3)]
    [InlineData(3, 1.2, -0.2)]
    [InlineData(10, -2.5, -4.4)]
    public void StandardTableAtBaseTenFrequencies(int k, double a, double c)
    {
        double f = 1000 * Math.Pow(10, k / 10.0);
        Assert.Equal(a, Units.AWeighting(f), 0.05);
        Assert.Equal(c, Units.CWeighting(f), 0.05);
    }

    [Fact]
    public void NoOverflowAtHugeFrequencies()
    {
        Assert.True(double.IsFinite(Units.AWeighting(1e200)));
        Assert.True(double.IsFinite(Units.CWeighting(1e200)));
    }
}
