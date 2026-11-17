using Xunit;

namespace SignalForge.Tests;

/// <summary>Coherent output power (conventions: Coherent output power; ADR 0198).</summary>
public class CoherentOutputPowerTests
{
    [Fact]
    public void PartsSumToTheOutputPsd()
    {
        var rng = new Random(47);
        var x = new double[8192];
        var y = new double[8192];
        for (int n = 0; n < x.Length; n++)
            x[n] = rng.NextDouble() - 0.5;
        for (int n = 0; n < y.Length; n++)
            y[n] = x[n] + (n >= 1 ? 0.5 * x[n - 1] : 0) + 0.3 * (rng.NextDouble() - 0.5);
        var r = Spectral.CoherentOutputPower(x, y, 2, nperseg: 256);
        var p = Spectral.WelchPsd(y, 2, nperseg: 256);
        for (int k = 0; k < p.Psd.Length; k++)
        {
            Assert.Equal(p.Psd[k], r.Coherent[k] + r.Noncoherent[k], 1e-12);
            Assert.True(r.Noncoherent[k] >= 0);
        }
    }
}
