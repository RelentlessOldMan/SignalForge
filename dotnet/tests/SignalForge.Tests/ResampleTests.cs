using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Resampling: analytic tones, DC level, gcd reduction, errors (conventions: Resampling).</summary>
public class ResampleTests
{
    [Theory]
    [InlineData(3, 2)]
    [InlineData(2, 3)]
    [InlineData(4, 1)]
    [InlineData(1, 4)]
    [InlineData(5, 3)]
    public void ToneMatchesAnalyticToneInInterior(int up, int down)
    {
        const double f = 0.02;
        double[] x = [.. Enumerable.Range(0, 4000).Select(n => Math.Cos(2 * Math.PI * f * n + 0.4))];
        double[] y = Dsp.Resample(x, up, down);
        Assert.Equal((x.Length * up + down - 1) / down, y.Length);
        for (int m = 300; m < y.Length - 300; m++)
            Assert.True(Math.Abs(y[m] - Math.Cos(2 * Math.PI * f * m * down / up + 0.4)) < 5e-3);
    }

    [Fact]
    public void ComplexToneKeepsPhase()
    {
        Complex[] x = [.. Enumerable.Range(0, 2000).Select(n => Complex.FromPolarCoordinates(1, 0.1 * n))];
        Complex[] y = Dsp.Resample(x, 2, 1);
        for (int m = 200; m < y.Length - 200; m++)
            Assert.True((y[m] - Complex.FromPolarCoordinates(1, 0.1 * m / 2)).Magnitude < 5e-3);
    }

    [Fact]
    public void DcLevelIsKept()
    {
        double[] y = Dsp.Interpolate(Enumerable.Repeat(2.0, 300).ToArray(), 3);
        for (int m = 100; m < y.Length - 100; m++)
            Assert.True(Math.Abs(y[m] - 2) < 1e-2);
    }

    [Fact]
    public void GcdReduction()
    {
        double[] x = [.. Enumerable.Range(0, 50).Select(n => Math.Sin(0.3 * n))];
        Assert.Equal(Dsp.Resample(x, 3, 2), Dsp.Resample(x, 6, 4));
        Assert.Equal(Dsp.ResampleTaps(3, 2), Dsp.ResampleTaps(6, 4));
    }

    [Fact]
    public void DefaultTapsAreTheDocumentedLowpass() =>
        Assert.Equal(Dsp.FirLowpass(61, 1.0 / 6, 1), Dsp.ResampleTaps(3, 2));

    [Fact]
    public void IdentityReturnsCopy()
    {
        double[] x = [1, 2];
        double[] y = Dsp.Resample(x, 2, 2);
        Assert.Equal(x, y);
        Assert.NotSame(x, y);
    }

    [Fact]
    public void Wrappers()
    {
        double[] x = [.. Enumerable.Range(0, 20).Select(n => (double)n)];
        Assert.Equal(Dsp.Resample(x, 3, 1), Dsp.Interpolate(x, 3));
        Assert.Equal(Dsp.Resample(x, 1, 3), Dsp.Decimate(x, 3));
    }

    [Fact]
    public void BadArguments()
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Resample([1.0], 0, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Resample([1.0], 1, -1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Resample(ReadOnlySpan<double>.Empty, 2, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Resample([1.0], 2, 1, [0.5, 0.5]));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Resample([1.0], 2, 1, []));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Resample([1.0], 2, 1, [1, double.PositiveInfinity, 1]));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.ResampleTaps(3, 3));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Decimate([Complex.One], 0));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Interpolate([1.0], 0));
    }

    [Theory]
    [InlineData(3, 2)]
    [InlineData(2, 3)]
    [InlineData(1, 4)]
    [InlineData(5, 1)]
    [InlineData(4, 6)]
    public void ResamplerIsResampleWithDelayedTaps(int up, int down)
    {
        var rng = new Random(7);
        double[] x = [.. Enumerable.Range(0, 301).Select(_ => rng.NextDouble() - 0.5)];
        var r = new Resampler(up, down);
        var y = new List<double>();
        int at = 0;
        foreach (int n in new[] { 0, 1, 17, 3, 0, 120, 60, 100 })
        {
            y.AddRange(r.Process(x.AsSpan(at, n)));
            at += n;
        }
        double[] h = [.. new double[r.Taps.Length - 1], .. r.Taps];
        double[] whole = Dsp.Resample(x, up, down, h);
        Assert.Equal(whole.Length, y.Count);
        for (int i = 0; i < whole.Length; i++)
            Assert.True(Math.Abs(y[i] - whole[i]) < 1e-12);
    }

    [Fact]
    public void ResamplerComplexEvenTapsAndReset()
    {
        Complex[] x = [.. Enumerable.Range(0, 50).Select(n => Complex.FromPolarCoordinates(1, 0.3 * n))];
        double[] taps = [0.2, 0.5, 0.3, -0.1];
        var r = new Resampler(7, 3, taps);
        Complex[] first = [.. r.Process(x.AsSpan(0, 13)), .. r.Process(ReadOnlySpan<Complex>.Empty), .. r.Process(x.AsSpan(13))];
        r.Reset();
        Assert.Equal(first, r.Process(x));
        Complex[] whole = Dsp.Resample(x, 7, 3, [0, 0, 0, .. taps]);
        Assert.Equal(whole.Length, first.Length);
        for (int i = 0; i < whole.Length; i++)
            Assert.True(Complex.Abs(first[i] - whole[i]) < 1e-12);
    }

    [Fact]
    public void ResamplerOneOneCopiesAndKindIsFixedUntilReset()
    {
        var copy = new Resampler(2, 2);
        Assert.Equal([1.0], copy.Taps);
        Assert.Empty(copy.Process(ReadOnlySpan<double>.Empty));
        Assert.Equal([1.0, 2.0], copy.Process([1.0, 2.0]));
        var r = new Resampler(3, 2);
        r.Process([1.0]);
        Assert.Throws<ArgumentException>(() => r.Process([Complex.ImaginaryOne]));
        r.Reset();
        Assert.Equal(2, r.Process([Complex.ImaginaryOne]).Length);
    }

    [Fact]
    public void ResamplerBadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => new Resampler(0, 1));
        Assert.ThrowsAny<ArgumentException>(() => new Resampler(1, 0));
        Assert.ThrowsAny<ArgumentException>(() => new Resampler(2, 1, []));
        Assert.ThrowsAny<ArgumentException>(() => new Resampler(2, 1, [1.0, double.NaN]));
    }
}
