using Xunit;

namespace SignalForge.Tests;

/// <summary>Wavefolder (ADR 0252).</summary>
public class WavefoldTests
{
    [Fact]
    public void ReflectsAboutTheLimits()
    {
        double[] y = Dsp.Wavefold([0.5, 1.25, 3.0, -1.75, 4.0], 1.0);
        double[] want = [0.5, 0.75, -1.0, -0.25, 0.0];
        Assert.Equal(want, y);
    }

    [Fact]
    public void RejectsZeroLimit() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Wavefold([1.0], 0.0));
}
