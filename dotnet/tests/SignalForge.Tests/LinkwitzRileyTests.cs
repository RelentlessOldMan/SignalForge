using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Linkwitz-Riley crossover (ADR 0284).</summary>
public class LinkwitzRileyTests
{
    [Theory]
    [InlineData(2)]
    [InlineData(6)]
    public void BandsSumToAnAllPass(int order)
    {
        Crossover x = Dsp.LinkwitzRiley(order, 1200.0, 48000.0);
        double[] f = [100.0, 1200.0, 5000.0, 20000.0];
        Complex[] lo = Dsp.SosResponse(x.Low, f, 48000.0), hi = Dsp.SosResponse(x.High, f, 48000.0);
        for (int i = 0; i < f.Length; i++)
            Assert.Equal(1.0, (lo[i] + hi[i]).Magnitude, 1e-10);
        Assert.Equal(0.5, lo[1].Magnitude, 1e-12);
    }

    [Fact]
    public void RejectsOddOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.LinkwitzRiley(3, 1.0, 8.0));
}
