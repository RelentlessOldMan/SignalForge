using Xunit;

namespace SignalForge.Tests;

/// <summary>Cubic soft clipper (ADR 0250).</summary>
public class SoftClipTests
{
    [Fact]
    public void HeldAtTwoThirdsBeyondOne()
    {
        double[] y = Dsp.SoftClip([-5.0, -1.0, 0.5, 1.0, 2.0]);
        Assert.Equal(-2.0 / 3.0, y[0]);
        Assert.Equal(-2.0 / 3.0, y[1]);
        Assert.Equal(11.0 / 24.0, y[2], 3e-16);
        Assert.Equal(2.0 / 3.0, y[3]);
        Assert.Equal(2.0 / 3.0, y[4]);
    }

    [Fact]
    public void RejectsEmpty() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SoftClip([]));
}
