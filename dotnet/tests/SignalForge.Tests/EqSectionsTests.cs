using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Shelving and peaking EQ sections (ADR 0282).</summary>
public class EqSectionsTests
{
    [Fact]
    public void HighShelfGainAtNyquist()
    {
        double[][] sos = Dsp.HighShelf(6000.0, 5.0, 0.7071, 48000.0);
        Complex[] h = Dsp.SosResponse(sos, [0.0, 24000.0], 48000.0);
        Assert.Equal(1.0, h[0].Magnitude, 1e-12);
        Assert.Equal(Math.Pow(10, 5.0 / 20), h[1].Magnitude, 1e-12);
    }

    [Fact]
    public void PeakingGainAtCentre()
    {
        double[][] sos = Dsp.PeakingEq(1000.0, -6.0, 3.0, 48000.0);
        Complex[] h = Dsp.SosResponse(sos, [1000.0], 48000.0);
        Assert.Equal(Math.Pow(10, -6.0 / 20), h[0].Magnitude, 1e-12);
    }

    [Fact]
    public void RejectsZeroQ() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.LowShelf(100.0, 3.0, 0.0, 8000.0));
}
