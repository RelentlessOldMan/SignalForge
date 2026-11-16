using Xunit;

namespace SignalForge.Tests;

/// <summary>Energy-time curve (conventions: Energy-time curve; ADR 0186).</summary>
public class EnergyTimeCurveTests
{
    [Fact]
    public void ThePeakIsZeroDb()
    {
        var rng = new Random(33);
        var h = new double[500];
        for (int n = 0; n < h.Length; n++)
            h[n] = (rng.NextDouble() - 0.5) * Math.Pow(0.99, n);
        Assert.Equal(0.0, Measurements.EnergyTimeCurve(h).Max());
    }
}
