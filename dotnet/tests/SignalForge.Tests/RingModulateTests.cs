using Xunit;

namespace SignalForge.Tests;

/// <summary>Ring modulator (ADR 0260).</summary>
public class RingModulateTests
{
    [Fact]
    public void QuarterRateCarrier()
    {
        double[] y = Dsp.RingModulate([1.0, 2.0, 3.0, 4.0], 250.0, 1000.0);
        double[] want = [1.0, 0.0, -3.0, 0.0];
        for (int n = 0; n < want.Length; n++)
            Assert.Equal(want[n], y[n], 1e-14);
    }

    [Fact]
    public void RejectsZeroSampleRate() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.RingModulate([1.0], 100.0, 0.0));
}
