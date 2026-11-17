using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Yule-Walker AR PSD (conventions: Yule-Walker AR PSD; ADR 0203).</summary>
public class YuleWalkerPsdTests
{
    [Fact]
    public void DensityIntegratesToTheMeanPower()
    {
        var rng = new Random(50);
        var x = new double[200];
        var z = new Complex[200];
        double power = 0, complexPower = 0;
        for (int i = 0; i < x.Length; i++)
        {
            x[i] = rng.NextDouble() - 0.5;
            z[i] = new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5);
            power += x[i] * x[i];
            complexPower += z[i].Real * z[i].Real + z[i].Imaginary * z[i].Imaginary;
        }
        var d = Spectral.YuleWalkerPsd(x, 3.0, 4, nfft: 8192);
        Assert.Equal(power / x.Length, d.Psd.Sum() * d.BinWidth, 1e-9);
        var c = Spectral.YuleWalkerPsd(z, 3.0, 4, nfft: 8192);
        Assert.Equal(complexPower / z.Length, c.Psd.Sum() * c.BinWidth, 1e-9);
    }
}
