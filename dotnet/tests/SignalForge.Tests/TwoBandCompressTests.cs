using Xunit;

namespace SignalForge.Tests;

/// <summary>Two-band compressor (ADR 0287).</summary>
public class TwoBandCompressTests
{
    [Fact]
    public void MatchesCompressOfTheBands()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        Bands b = Dsp.CrossoverSplit(x, 4, 0.1, 1.0);
        double[] lo = Dsp.Compress(b.Low, -6.0, 3.0, 0.3, 0.9);
        double[] hi = Dsp.Compress(b.High, -3.0, 2.0, 0.3, 0.9);
        double[] want = [.. lo.Zip(hi, (u, v) => u + v)];
        Assert.Equal(want, Dsp.TwoBandCompress(x, 4, 0.1, 1.0, -6.0, 3.0, -3.0, 2.0, 0.3, 0.9));
    }

    [Fact]
    public void RejectsOddOrder() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.TwoBandCompress([1.0], 3, 1.0, 8.0, 0.0, 2.0, 0.0, 2.0, 0.5, 0.5));
}
