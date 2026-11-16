using Xunit;

namespace SignalForge.Tests;

/// <summary>Early decay time (conventions: Early decay time; ADR 0181).</summary>
public class EarlyDecayTimeTests
{
    [Fact]
    public void ItIsReverberationTimeFromZeroToMinusTen()
    {
        var rng = new Random(31);
        var h = new double[6000];
        for (int n = 0; n < h.Length; n++)
            h[n] = (rng.NextDouble() - 0.5) * Math.Pow(0.998, n);
        Assert.Equal(Measurements.ReverberationTime(h, 8000, 0, -10), Measurements.EarlyDecayTime(h, 8000));
    }
}
