using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Hard clipper (ADR 0251).</summary>
public class HardClipTests
{
    [Fact]
    public void RealClamps()
    {
        double[] y = Dsp.HardClip([-3.0, 0.25, 2.0], 1.0);
        double[] want = [-1.0, 0.25, 1.0];
        Assert.Equal(want, y);
    }

    [Fact]
    public void ComplexKeepsPhase()
    {
        Complex[] y = Dsp.HardClip([new Complex(3, 4), new Complex(0.3, 0.4)], 2.0);
        Assert.Equal(1.2, y[0].Real, 1e-15);
        Assert.Equal(1.6, y[0].Imaginary, 1e-15);
        Assert.Equal(new Complex(0.3, 0.4), y[1]);
    }
}
