using Xunit;

namespace SignalForge.Tests;

/// <summary>ERB scale (conventions: ERB scale; ADR 0160).</summary>
public class ErbScaleTests
{
    [Theory]
    [InlineData(0.0)]
    [InlineData(250.0)]
    [InlineData(4000.0)]
    [InlineData(20000.0)]
    public void RoundTrip(double hz) => Assert.Equal(hz, Units.ErbRateToHz(Units.HzToErbRate(hz)), 1e-9);

    [Theory]
    [InlineData(100.0)]
    [InlineData(1000.0)]
    [InlineData(5000.0)]
    public void RateSlopeTimesBandwidthIsTheConstantRatio(double hz)
    {
        const double H = 1e-3;
        double slope = (Units.HzToErbRate(hz + H) - Units.HzToErbRate(hz - H)) / (2 * H);
        double ratio = 21.4 * 24.7 * 4.37 / (1000 * Math.Log(10)); // about 1.0032 (ADR 0160)
        Assert.Equal(ratio, slope * Units.ErbBandwidth(hz), 1e-7);
    }
}
