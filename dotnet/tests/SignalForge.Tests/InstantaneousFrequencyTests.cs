using Xunit;

namespace SignalForge.Tests;

/// <summary>Instantaneous frequency (conventions: Instantaneous frequency; ADR 0187).</summary>
public class InstantaneousFrequencyTests
{
    [Fact]
    public void AnFmToneFollowsItsModulation()
    {
        const double fs = 512, fc = 100, dev = 20, fm = 4;
        var x = new double[512];
        for (int n = 0; n < x.Length; n++)
            x[n] = Math.Cos(2 * Math.PI * fc * n / fs + dev / fm * Math.Sin(2 * Math.PI * fm * n / fs));
        var f = Spectral.InstantaneousFrequency(x, fs);
        for (int n = 0; n < f.Length; n++)
            Assert.Equal(fc + dev * Math.Cos(2 * Math.PI * fm * (n + 0.5) / fs), f[n], 0.05);
    }
}
