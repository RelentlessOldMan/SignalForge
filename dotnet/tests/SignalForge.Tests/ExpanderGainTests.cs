using Xunit;

namespace SignalForge.Tests;

/// <summary>Downward-expander gain computer (ADR 0256).</summary>
public class ExpanderGainTests
{
    [Fact]
    public void HardKneeBelowThreshold()
    {
        double[] g = Dsp.ExpanderGain([0.0, -40.0, -41.0, -60.0], -40.0, 2.0);
        double[] want = [0.0, 0.0, -1.0, -20.0];
        Assert.Equal(want, g);
    }

    [Fact]
    public void RejectsNegativeKnee() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.ExpanderGain([0.0], -10.0, 2.0, -1.0));
}
