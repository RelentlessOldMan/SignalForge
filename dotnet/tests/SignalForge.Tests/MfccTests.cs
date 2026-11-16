using Xunit;

namespace SignalForge.Tests;

/// <summary>MFCC (conventions: MFCC; ADR 0157).</summary>
public class MfccTests
{
    [Fact]
    public void ScalingThePowerChangesOnlyC0()
    {
        double[][] w = Spectral.MelFilterbank(24, 512, 16000, 100, 7000);
        var rng = new Random(3);
        double[] p = Enumerable.Range(0, 257).Select(_ => 0.5 + 1.5 * rng.NextDouble()).ToArray();
        double[] a = Spectral.Mfcc(p, w, 13);
        double[] b = Spectral.Mfcc(p.Select(v => 9 * v).ToArray(), w, 13);
        Assert.Equal(Math.Sqrt(24) * Math.Log(9), b[0] - a[0], 1e-12);
        for (int i = 1; i < 13; i++)
            Assert.Equal(a[i], b[i], 1e-12);
    }

    [Fact]
    public void RejectsJaggedFilterbank()
    {
        double[][] w = [[1, 0], [1]];
        Assert.Throws<ArgumentException>(() => Spectral.Mfcc([1.0, 2.0], w, 1));
    }
}
