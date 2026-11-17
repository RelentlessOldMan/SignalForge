using Xunit;

namespace SignalForge.Tests;

/// <summary>Burg AR PSD (conventions: Burg AR PSD; ADR 0204).</summary>
public class BurgPsdTests
{
    [Fact]
    public void ToneInNoisePeaksAtItsFrequency()
    {
        var rng = new Random(52);
        var x = new double[128];
        for (int i = 0; i < x.Length; i++)
            x[i] = Math.Cos(2 * Math.PI * 0.12 * i) + (0.05 * (rng.NextDouble() - 0.5));
        var d = Spectral.BurgPsd(x, 1.0, 6, nfft: 1000);
        int best = Array.IndexOf(d.Psd, d.Psd.Max());
        Assert.Equal(0.12, d.Frequencies[best], 0.005);
    }
}
