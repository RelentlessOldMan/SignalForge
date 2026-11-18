using Xunit;

namespace SignalForge.Tests;

/// <summary>State-variable filter (ADR 0279).</summary>
public class SvfTests
{
    [Fact]
    public void NotchIsLowPlusHigh()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6, 0.5, 1.3];
        double[] lo = Dsp.Svf(x, 0.1, 2.0, 1.0, SvfOutput.Lowpass);
        double[] hp = Dsp.Svf(x, 0.1, 2.0, 1.0, SvfOutput.Highpass);
        double[] no = Dsp.Svf(x, 0.1, 2.0, 1.0, SvfOutput.Notch);
        for (int n = 0; n < x.Length; n++)
            Assert.Equal(lo[n] + hp[n], no[n], 1e-12);
    }

    [Fact]
    public void RejectsZeroQ() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Svf([1.0], 1.0, 0.0, 8.0));
}
