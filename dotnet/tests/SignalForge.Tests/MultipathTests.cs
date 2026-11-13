using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Multipath: the tapped delay line against a direct convolution with the dense taps,
/// truncated to the input's length (conventions: Channel, Multipath).</summary>
public class MultipathTests
{
    [Fact]
    public void MatchesDenseConvolution()
    {
        var rng = new Random(3);
        Complex[] x = [.. Enumerable.Range(0, 200).Select(_ => new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5))];
        int[] delays = [0, 3, 3, 17, 250];
        Complex[] gains = [1, new(0.5, -0.25), new(0, 0.1), -0.3, 2];
        var dense = new Complex[delays.Max() + 1];
        for (int i = 0; i < delays.Length; i++)
            dense[delays[i]] += gains[i];
        Complex[] y = Channel.Multipath(x, delays, gains);
        Assert.Equal(x.Length, y.Length);
        for (int n = 0; n < x.Length; n++)
        {
            Complex want = 0;
            for (int k = 0; k <= Math.Min(n, dense.Length - 1); k++)
                want += dense[k] * x[n - k];
            Assert.True(Complex.Abs(y[n] - want) < 1e-13, $"{n}: {y[n]} vs {want}");
        }
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Channel.Multipath([Complex.One], [-1], [Complex.One]));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Multipath([Complex.One], [0, 1], [Complex.One]));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Multipath([Complex.One], [], []));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Multipath([Complex.One], [0], [new Complex(double.NaN, 0)]));
        Assert.ThrowsAny<ArgumentException>(() => Channel.Multipath([Complex.One], [0], [new Complex(0, double.PositiveInfinity)]));
    }
}
