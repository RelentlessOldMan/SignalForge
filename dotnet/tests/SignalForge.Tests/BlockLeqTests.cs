using Xunit;

namespace SignalForge.Tests;

/// <summary>Short Leq series and sound exposure (conventions: Short Leq series and sound
/// exposure; ADR 0170).</summary>
public class BlockLeqTests
{
    [Fact]
    public void BlockMeansAverageToTheExposureRate()
    {
        var rng = new Random(5);
        var x = new double[48000];
        for (int n = 0; n < x.Length; n++)
            x[n] = rng.NextDouble() - 0.5;
        double[] blocks = Measurements.BlockLeq(x, 48000, 0.1);
        Assert.Equal(10, blocks.Length);
        Assert.Equal(Measurements.SoundExposure(x, 48000), blocks.Average(), 1e-12);
    }
}
