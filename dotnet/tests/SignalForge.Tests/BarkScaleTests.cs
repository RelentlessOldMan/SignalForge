using Xunit;

namespace SignalForge.Tests;

/// <summary>Bark scale (conventions: Bark scale; ADR 0163).</summary>
public class BarkScaleTests
{
    [Fact]
    public void RoundTripAndIncreasingOverTheAudioBand()
    {
        double previous = double.NegativeInfinity;
        for (int i = 0; i <= 400; i++)
        {
            double f = i == 0 ? 0 : Math.Pow(10, 6.0 * (i - 1) / 399);
            double z = Units.HzToBark(f);
            Assert.True(z > previous);
            previous = z;
            Assert.Equal(f, Units.BarkToHz(z), 1e-9 + 1e-11 * f);
        }
    }

    [Fact]
    public void ContinuousAtBothBranchEdges()
    {
        foreach (double edge in new[] { 1960 * 2.53 / 24.28, 1960 * 20.63 / 6.18 })
            Assert.Equal(Units.HzToBark(edge * (1 - 1e-12)), Units.HzToBark(edge * (1 + 1e-12)), 1e-9);
    }

    [Fact]
    public void ZeroRoundTripsToExactlyZero() => Assert.Equal(0.0, Units.BarkToHz(Units.HzToBark(0)));
}
