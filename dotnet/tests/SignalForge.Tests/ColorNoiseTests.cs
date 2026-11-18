using Xunit;

namespace SignalForge.Tests;

/// <summary>Colored noise (ADR 0318).</summary>
public class ColorNoiseTests
{
    [Fact]
    public void ExponentZeroRemovesTheMean()
    {
        double[] x = [1, 2, 3, 6];
        double[] y = Channel.ColorNoise(x, 0);
        for (int i = 0; i < x.Length; i++)
            Assert.Equal(x[i] - 3, y[i], 1e-14);
    }

    [Fact]
    public void BrownScalesEachBinsPowerByOneOverKSquared()
    {
        var rng = new Random(5);
        var x = new double[64];
        for (int i = 0; i < x.Length; i++)
            x[i] = rng.NextDouble() - 0.5;
        var px = Spectral.Fft(x);
        var py = Spectral.Fft(Channel.ColorNoise(x, 2));
        for (int k = 1; k <= 32; k++)
            Assert.Equal(1.0 / (k * k), py[k].Magnitude * py[k].Magnitude / (px[k].Magnitude * px[k].Magnitude), 1e-10);
    }

    [Fact]
    public void RejectsANonFiniteSample() =>
        Assert.ThrowsAny<ArgumentException>(() => Channel.ColorNoise([1, double.NaN], 1));
}
