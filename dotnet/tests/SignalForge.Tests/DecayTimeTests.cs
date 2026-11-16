using Xunit;

namespace SignalForge.Tests;

/// <summary>Decay time from a curve (conventions: Decay time from a curve; ADR 0184).</summary>
public class DecayTimeTests
{
    [Fact]
    public void ReverberationTimeIsTheDecayTimeOfTheSchroederDecay()
    {
        var rng = new Random(34);
        var h = new double[6000];
        for (int n = 0; n < h.Length; n++)
            h[n] = (rng.NextDouble() - 0.5) * Math.Pow(0.998, n);
        Assert.Equal(Measurements.ReverberationTime(h, 8000), Measurements.DecayTime(Measurements.SchroederDecay(h), 8000));
    }
}
