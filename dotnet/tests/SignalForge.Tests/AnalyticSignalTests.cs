using Xunit;

namespace SignalForge.Tests;

/// <summary>Analytic signal (conventions: Analytic signal; ADR 0185).</summary>
public class AnalyticSignalTests
{
    [Fact]
    public void AnAmToneHasItsEnvelope()
    {
        var x = new double[256];
        var env = new double[256];
        for (int n = 0; n < 256; n++)
        {
            env[n] = 1 + 0.5 * Math.Cos(2 * Math.PI * 2 * n / 256);
            x[n] = env[n] * Math.Cos(2 * Math.PI * 40 * n / 256);
        }
        var z = Spectral.AnalyticSignal(x);
        for (int n = 0; n < 256; n++)
        {
            Assert.Equal(env[n], z[n].Magnitude, 1e-12);
            Assert.Equal(x[n], z[n].Real, 1e-12);
        }
    }
}
