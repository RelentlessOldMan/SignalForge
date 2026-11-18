using Xunit;

namespace SignalForge.Tests;

/// <summary>Tremolo (ADR 0261).</summary>
public class TremoloTests
{
    [Fact]
    public void QuarterRateGains()
    {
        double[] y = Dsp.Tremolo([1.0, 1.0, 1.0, 1.0], 250.0, 0.5, 1000.0);
        double[] want = [1.0, 0.75, 0.5, 0.75];
        for (int n = 0; n < want.Length; n++)
            Assert.Equal(want[n], y[n], 1e-15);
    }

    [Fact]
    public void RejectsDepthAboveOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Tremolo([1.0], 5.0, 1.5, 1000.0));
}
