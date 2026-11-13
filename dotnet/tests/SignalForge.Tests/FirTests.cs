using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>FIR design and the streaming FIR filter (conventions: FIR filters).</summary>
public class FirTests
{
    private static double[] Linspace(double a, double b, int n) =>
        [.. Enumerable.Range(0, n).Select(i => a + (b - a) * i / (n - 1))];

    [Fact]
    public void KaiserDesignMeetsItsSpec()
    {
        // 60 dB, 50 Hz transition centered on 200 Hz at fs = 1000 (3 dB margin for the formula).
        var (n, beta) = Dsp.KaiserParameters(60, 50, 1000);
        double[] h = Dsp.FirLowpass(n, 200, 1000, WindowType.Kaiser, beta);
        double delta = Math.Pow(10, -57.0 / 20);
        Assert.All(Dsp.FirResponse(h, Linspace(0, 175, 200), 1000), z => Assert.True(Math.Abs(z.Magnitude - 1) < delta));
        Assert.All(Dsp.FirResponse(h, Linspace(225, 500, 300), 1000), z => Assert.True(z.Magnitude < delta));
    }

    [Fact]
    public void DesignsAreSymmetric()
    {
        foreach (double[] h in new[]
        {
            Dsp.FirLowpass(31, 100, 1000),
            Dsp.FirHighpass(31, 100, 1000, WindowType.Hann),
            Dsp.FirBandpass(30, 100, 200, 1000, WindowType.Blackman),
        })
            for (int i = 0; i < h.Length; i++)
                Assert.Equal(h[i], h[^(i + 1)], 1e-15);
    }

    [Fact]
    public void ReferenceGainsAreOne()
    {
        Assert.Equal(1, Dsp.FirResponse(Dsp.FirLowpass(25, 80, 1000), [0], 1000)[0].Real, 1e-14);
        Assert.Equal(1, Dsp.FirResponse(Dsp.FirHighpass(25, 80, 1000), [500], 1000)[0].Magnitude, 1e-14);
        Assert.Equal(1, Dsp.FirResponse(Dsp.FirBandpass(25, 80, 300, 1000), [190], 1000)[0].Magnitude, 1e-14);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void AnySplitMatchesConvolution(bool complexInput)
    {
        var rng = new Random(3);
        double[] h = Dsp.FirLowpass(17, 120, 1000);
        Complex[] x = [.. Enumerable.Range(0, 500).Select(_ => new Complex(rng.NextDouble() - 0.5, complexInput ? rng.NextDouble() - 0.5 : 0))];
        Complex[] want = Dsp.Convolve(x, h)[..x.Length];
        for (int trial = 0; trial < 5; trial++)
        {
            int[] cuts = [0, .. Enumerable.Range(0, 12).Select(_ => rng.Next(x.Length + 1)).Order(), x.Length];
            var f = new FirFilter(h);
            var y = new List<Complex>();
            for (int i = 0; i + 1 < cuts.Length; i++)
            {
                if (complexInput)
                    y.AddRange(f.Process(x.AsSpan(cuts[i], cuts[i + 1] - cuts[i])));
                else
                    y.AddRange(f.Process([.. x[cuts[i]..cuts[i + 1]].Select(z => z.Real)]).Select(r => new Complex(r, 0)));
            }
            Assert.Equal(want.Length, y.Count);
            for (int i = 0; i < want.Length; i++)
                Assert.True((y[i] - want[i]).Magnitude < 1e-13, $"sample {i}");
        }
    }

    [Fact]
    public void ResetAndKind()
    {
        var f = new FirFilter([1.0, 1.0]);
        Assert.Empty(f.Process(ReadOnlySpan<double>.Empty));
        Assert.Equal([1.0, 3.0], f.Process([1.0, 2.0]));
        Assert.Throws<ArgumentException>(() => f.Process([Complex.ImaginaryOne]));
        Assert.Empty(f.Process(ReadOnlySpan<Complex>.Empty)); // empty chunks never throw
        f.Reset();
        Assert.Equal([Complex.ImaginaryOne], f.Process([Complex.ImaginaryOne])); // no memory of the real samples
    }

    [Fact]
    public void TapsAreCopied()
    {
        double[] taps = [1.0, 2.0];
        var f = new FirFilter(taps);
        taps[0] = 9;
        f.Taps[1] = 9;
        Assert.Equal([1.0, 2.0], f.Taps);
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.Throws<ArgumentException>(() => new FirFilter([]));
        Assert.Throws<ArgumentException>(() => new FirFilter([double.PositiveInfinity]));
        Assert.Throws<ArgumentOutOfRangeException>(() => Dsp.FirHighpass(-3, 100, 1000));
        Assert.Throws<ArgumentOutOfRangeException>(() => Dsp.KaiserParameters(double.NaN, 10, 100));
        Assert.Throws<ArgumentOutOfRangeException>(() => Dsp.KaiserParameters(60, 1e-300, 100));
    }
}
