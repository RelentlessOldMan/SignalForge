using Xunit;

namespace SignalForge.Tests;

/// <summary>Auto-wah (ADR 0280).</summary>
public class AutoWahTests
{
    [Fact]
    public void FixedCutoffIsTheUnityBandPass()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        double[] y = Dsp.AutoWah(x, 0.1, 0.1, 2.0, 0.5, 0.5, 1.0, 1.0);
        double[] bp = Dsp.Svf(x, 0.1, 2.0, 1.0, SvfOutput.Bandpass);
        for (int n = 0; n < x.Length; n++)
            Assert.Equal(bp[n] / 2, y[n], 1e-12);
    }

    [Fact]
    public void RejectsLowAboveHigh() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AutoWah([1.0], 3.0, 2.0, 1.0, 0.5, 0.5, 8.0, 0.5));
}
