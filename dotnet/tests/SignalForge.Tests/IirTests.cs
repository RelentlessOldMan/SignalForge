using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

public class IirTests
{
    private static double[][] Design(bool high, int order, double cutoff, double fs) =>
        high ? Dsp.ButterworthHighpass(order, cutoff, fs) : Dsp.ButterworthLowpass(order, cutoff, fs);

    [Theory]
    [InlineData(false, 1, 0.003)]
    [InlineData(false, 4, 0.1)]
    [InlineData(false, 9, 0.37)]
    [InlineData(false, 16, 0.499)]
    [InlineData(true, 1, 0.37)]
    [InlineData(true, 6, 0.003)]
    [InlineData(true, 9, 0.1)]
    [InlineData(true, 16, 0.25)]
    public void ButterworthMagnitudeHasTheClosedForm(bool high, int order, double cutoff)
    {
        double[][] sos = Design(high, order, cutoff * 48000, 48000);
        Assert.Equal((order + 1) / 2, sos.Length);
        Assert.All(sos, r => Assert.Equal(1.0, r[3]));
        double k = Math.Tan(Math.PI * cutoff);
        double[] f = [.. Enumerable.Range(0, 301).Select(i => (-0.4999 + 0.9998 * i / 300) * 48000)];
        Complex[] h = Dsp.SosResponse(sos, f, 48000);
        for (int i = 0; i < f.Length; i++)
        {
            double t = Math.Abs(Math.Tan(Math.PI * f[i] / 48000));
            double r = high ? k / t : t / k;
            double expected = 1 / (1 + Math.Pow(r, 2 * order));
            double got = h[i].Magnitude * h[i].Magnitude;
            Assert.True(Math.Abs(got - expected) <= 1e-12 + 1e-9 * expected, $"f = {f[i]}: {got} vs {expected}");
        }
        Assert.Equal(0.5, Math.Pow(Dsp.SosResponse(sos, [cutoff * 48000], 48000)[0].Magnitude, 2), 1e-9);
    }

    [Theory]
    [InlineData(false, 1)]
    [InlineData(false, 7)]
    [InlineData(true, 4)]
    [InlineData(true, 7)]
    public void ButterworthSectionsAreStableWithUnitGain(bool high, int order)
    {
        double[][] sos = Design(high, order, 1500, 8000);
        double reference = high ? 4000 : 0;
        foreach (double[] row in sos)
        {
            // Both poles inside the unit circle: |a2| < 1 and |a1| < 1 + a2.
            Assert.True(Math.Abs(row[5]) < 1 && Math.Abs(row[4]) < 1 + row[5]);
            Assert.Equal(1.0, Dsp.SosResponse([row], [reference], 8000)[0].Magnitude, 1e-14);
        }
        double[] a2 = [.. sos.Skip(order % 2).Select(r => r[5])];
        for (int i = 1; i < a2.Length; i++)
            Assert.True(a2[i] >= a2[i - 1], "the sharpest section is last");
    }

    [Fact]
    public void ImpulseResponseSpectrumMatchesSosResponse()
    {
        double[][] sos = Dsp.ButterworthLowpass(5, 900, 8000);
        var impulse = new double[4096];
        impulse[0] = 1;
        double[] h = new IirFilter(sos).Process(impulse);
        Complex[] spectrum = Spectral.Fft([.. h.Select(v => new Complex(v, 0))]);
        int[] bins = [.. Enumerable.Range(0, 56).Select(i => 37 * i)];
        Complex[] expected = Dsp.SosResponse(sos, [.. bins.Select(k => k * 8000.0 / 4096)], 8000);
        for (int i = 0; i < bins.Length; i++)
            Assert.True(Complex.Abs(spectrum[bins[i]] - expected[i]) <= 1e-12, $"bin {bins[i]}");
    }

    [Fact]
    public void ChunksConcatenateToOnePass()
    {
        var rng = new Random(3);
        double[] x = [.. Enumerable.Range(0, 301).Select(_ => rng.NextDouble() - 0.5)];
        Complex[] z = [.. x.Select(v => new Complex(v, rng.NextDouble() - 0.5))];
        var f = new IirFilter(Dsp.ButterworthHighpass(6, 0.2, 1));
        double[] whole = f.Process(x);
        f.Reset();
        double[] parts = [.. f.Process(x.AsSpan(0, 1)), .. f.Process(x.AsSpan(1, 0)), .. f.Process(x.AsSpan(1, 119)), .. f.Process(x.AsSpan(120))];
        Assert.Equal(whole, parts);
        f.Reset();
        Complex[] wholeZ = f.Process(z);
        f.Reset();
        Complex[] partsZ = [.. f.Process(z.AsSpan(0, 150)), .. f.Process(z.AsSpan(150))];
        Assert.Equal(wholeZ, partsZ);
    }

    [Fact]
    public void RealOrComplexUntilReset()
    {
        var f = new IirFilter([[1, 0, 0, 1, -0.5, 0]]);
        Assert.Empty(f.Process(ReadOnlySpan<double>.Empty));
        f.Process([1.0]);
        Assert.Throws<ArgumentException>(() => f.Process([Complex.ImaginaryOne]));
        f.Reset();
        Assert.Equal(Complex.ImaginaryOne, f.Process([Complex.ImaginaryOne])[0]);
        Assert.Throws<ArgumentException>(() => f.Process([1.0]));
    }

    [Fact]
    public void SectionsAreANormalizedCopy()
    {
        double[][] sos = [[2, 4, 2, 2, 1, 0.5]];
        var f = new IirFilter(sos);
        sos[0][0] = 99;
        double[][] s = f.Sections;
        Assert.Equal([1.0, 2, 1, 1, 0.5, 0.25], s[0]);
        s[0][0] = 99;
        Assert.Equal(1.0, f.Sections[0][0]);
    }

    public static TheoryData<double[][]> BadSections => new()
    {
        Array.Empty<double[]>(),
        new[] { new double[] { 1, 0, 0, 1, 0 } },
        new[] { new double[] { 1, 0, 0, 0, 0, 0 } },
        new[] { new double[] { 1, 0, 0, 1, double.NaN, 0 } },
        new[] { new double[] { 1, 0, 0, 1, double.PositiveInfinity, 0 } },
        new double[][] { null! },
    };

    [Theory]
    [MemberData(nameof(BadSections))]
    public void BadSectionsThrow(double[][] sos)
    {
        Assert.ThrowsAny<ArgumentException>(() => new IirFilter(sos));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SosResponse(sos, [0.0], 1));
    }

    [Theory]
    [InlineData(0, 1.0, 8.0)]
    [InlineData(-1, 1.0, 8.0)]
    [InlineData(2, double.NaN, 8.0)]
    [InlineData(2, -1.0, 8.0)]
    [InlineData(2, 4.0, 8.0)]
    [InlineData(2, 1.0, double.PositiveInfinity)]
    [InlineData(2, 1.0, -8.0)]
    public void BadDesignArgumentsThrow(int order, double cutoff, double rate)
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.ButterworthLowpass(order, cutoff, rate));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.ButterworthHighpass(order, cutoff, rate));
    }

    [Fact]
    public void SosResponseRejectsBadArguments()
    {
        Assert.Throws<ArgumentNullException>(() => Dsp.SosResponse(null!, [0.0], 1));
        Assert.Throws<ArgumentException>(() => Dsp.SosResponse([[1, 0, 0, 1, 0, 0]], [double.NaN], 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SosResponse([[1, 0, 0, 1, 0, 0]], [0.0], 0));
    }

    [Theory]
    [InlineData(false, 1, 0.001, 0.002)]
    [InlineData(false, 3, 0.1, 0.11)]
    [InlineData(false, 6, 0.05, 0.45)]
    [InlineData(false, 9, 0.3, 0.4999)]
    [InlineData(true, 1, 0.3, 0.4999)]
    [InlineData(true, 2, 0.001, 0.002)]
    [InlineData(true, 6, 0.1, 0.11)]
    [InlineData(true, 9, 0.05, 0.45)]
    public void ButterworthBandMagnitudeHasTheClosedForm(bool stop, int order, double low, double high)
    {
        double[][] sos = stop ? Dsp.ButterworthBandstop(order, low * 1000, high * 1000, 1000)
            : Dsp.ButterworthBandpass(order, low * 1000, high * 1000, 1000);
        Assert.Equal(order, sos.Length);
        Assert.All(sos, r => Assert.Equal(1.0, r[3]));
        double lo = Math.Tan(Math.PI * low), hi = Math.Tan(Math.PI * high);
        double[] f = [.. Enumerable.Range(0, 301).Select(i => (-0.4999 + 0.9998 * i / 300) * 1000)];
        Complex[] h = Dsp.SosResponse(sos, f, 1000);
        for (int i = 0; i < f.Length; i++)
        {
            double t = Math.Abs(Math.Tan(Math.PI * f[i] / 1000));
            double x2 = Math.Pow((t * t - lo * hi) / ((hi - lo) * t), 2 * order);
            double expected = stop ? (double.IsInfinity(x2) ? 1 : x2 / (1 + x2)) : 1 / (1 + x2);
            double got = h[i].Magnitude * h[i].Magnitude;
            Assert.True(Math.Abs(got - expected) <= 1e-11 + 1e-9 * expected, $"f = {f[i]}: {got} vs {expected}");
        }
        foreach (Complex e in Dsp.SosResponse(sos, [low * 1000, high * 1000], 1000))
            Assert.Equal(0.5, e.Magnitude * e.Magnitude, 1e-9);
    }

    [Fact]
    public void ButterworthBandRejectsBadArguments()
    {
        foreach (var design in new Func<int, double, double, double, double[][]>[] { Dsp.ButterworthBandpass, Dsp.ButterworthBandstop })
        {
            Assert.Throws<ArgumentOutOfRangeException>(() => design(0, 1, 2, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 2, 1, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 1, 1, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 0, 1, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 1, 4, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 1, double.NaN, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 1, 2, 0));
        }
    }
}
