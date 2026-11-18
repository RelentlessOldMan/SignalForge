using Xunit;

namespace SignalForge.Tests;

/// <summary>Vibrato (ADR 0271).</summary>
public class VibratoTests
{
    [Fact]
    public void HalfSampleDelayAverages()
    {
        double[] y = Dsp.Vibrato([2.0, 4.0, -2.0], 0.5, 0.0, 1.0, 8.0);
        Assert.Equal([1.0, 3.0, 1.0], y);
    }

    [Fact]
    public void RejectsDepthAboveDelay() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Vibrato([1.0], 1.0, 2.0, 1.0, 8.0));
}
