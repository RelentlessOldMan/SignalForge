using Xunit;

namespace SignalForge.Tests;

/// <summary>Decay curvature (conventions: Decay curvature; ADR 0182).</summary>
public class DecayCurvatureTests
{
    [Fact]
    public void ItIsTheRatioOfT30ToT20()
    {
        var rng = new Random(32);
        var h = new double[8000];
        for (int n = 0; n < h.Length; n++)
            h[n] = (rng.NextDouble() - 0.5) * Math.Pow(0.998, n);
        double t20 = Measurements.ReverberationTime(h, 8000);
        double t30 = Measurements.ReverberationTime(h, 8000, -5, -35);
        Assert.Equal(100 * (t30 / t20 - 1), Measurements.DecayCurvature(h, 8000), 1e-12);
    }
}
