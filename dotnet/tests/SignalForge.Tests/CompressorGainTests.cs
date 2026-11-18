using Xunit;

namespace SignalForge.Tests;

/// <summary>Compressor gain computer (ADR 0254).</summary>
public class CompressorGainTests
{
    [Fact]
    public void HardKneeFollowsTheRatio()
    {
        double[] g = Dsp.CompressorGain([-40.0, -20.0, -19.0, 0.0], -20.0, 4.0);
        double[] want = [0.0, 0.0, -0.75, -15.0];
        Assert.Equal(want, g);
    }

    [Fact]
    public void KneeCentreIsAnEighthOfTheWidthTimesSlope()
    {
        double[] g = Dsp.CompressorGain([-20.0], -20.0, 4.0, 8.0);
        Assert.Equal(-0.75, g[0]);
    }

    [Fact]
    public void RejectsRatioBelowOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.CompressorGain([0.0], -10.0, 0.5));
}
