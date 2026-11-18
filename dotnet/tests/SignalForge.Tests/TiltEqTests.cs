using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Tilt EQ (ADR 0283).</summary>
public class TiltEqTests
{
    [Fact]
    public void UnityAtThePivot()
    {
        double[][] sos = Dsp.TiltEq(800.0, 9.0, 48000.0);
        Complex[] h = Dsp.SosResponse(sos, [0.0, 800.0, 24000.0], 48000.0);
        Assert.Equal(Math.Pow(10, -4.5 / 20), h[0].Magnitude, 1e-12);
        Assert.Equal(1.0, h[1].Magnitude, 1e-12);
        Assert.Equal(Math.Pow(10, 4.5 / 20), h[2].Magnitude, 1e-12);
    }

    [Fact]
    public void RejectsZeroFrequency() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.TiltEq(0.0, 3.0, 8000.0));
}
