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

    public static TheoryData<bool, int, double, double> Bands()
    {
        var data = new TheoryData<bool, int, double, double>();
        foreach (bool stop in new[] { false, true })
            foreach (int order in new[] { 1, 2, 3, 6, 9 })
                foreach (var (low, high) in new[] { (0.001, 0.002), (0.1, 0.11), (0.05, 0.45), (0.3, 0.4999) })
                    data.Add(stop, order, low, high);
        return data;
    }

    [Theory]
    [MemberData(nameof(Bands))]
    public void ButterworthBandMagnitudeHasTheClosedForm(bool stop, int order, double low, double high)
    {
        double[][] sos = stop ? Dsp.ButterworthBandstop(order, low * 1000, high * 1000, 1000)
            : Dsp.ButterworthBandpass(order, low * 1000, high * 1000, 1000);
        Assert.Equal(order, sos.Length);
        Assert.All(sos, r => Assert.Equal(1.0, r[3]));
        Assert.All(sos, r => Assert.True(Math.Abs(r[5]) < 1 && Math.Abs(r[4]) < 1 + r[5], "a pole outside the unit circle"));
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
    public void ButterworthBandpassPassesItsCenterAndBandstopNullsIt()
    {
        double f0 = 8000 / Math.PI * Math.Atan(Math.Sqrt(Math.Tan(Math.PI / 8) * Math.Tan(Math.PI / 4)));
        double[][] bp = Dsp.ButterworthBandpass(4, 1000, 2000, 8000), bs = Dsp.ButterworthBandstop(4, 1000, 2000, 8000);
        Assert.Equal(1.0, Dsp.SosResponse(bp, [f0], 8000)[0].Magnitude, 1e-12);
        Assert.True(Dsp.SosResponse(bs, [f0], 8000)[0].Magnitude < 1e-12);
        Assert.All(Dsp.SosResponse(bs, [0, 4000], 8000), h => Assert.Equal(1.0, h.Magnitude, 1e-12));
        double[] x = [.. Enumerable.Range(0, 4000).Select(n => Math.Cos(2 * Math.PI * f0 * n / 8000))];
        double[] y = new IirFilter(bp).Process(x);
        for (int n = 3000; n < 4000; n++)
            Assert.True(Math.Abs(y[n] - x[n]) < 1e-9, $"n = {n}"); // unit gain, zero phase at the center
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

    [Theory]
    [InlineData(200.0)]
    [InlineData(900.0)]
    [InlineData(1300.0)]
    public void ZeroPhaseFilterScalesAToneByHSquaredWithoutDelay(double f)
    {
        double[][] sos = Dsp.ButterworthLowpass(5, 1000, 8000);
        double[] x = [.. Enumerable.Range(0, 4000).Select(n => Math.Cos(2 * Math.PI * f * n / 8000 + 0.3))];
        double[] y = Dsp.ZeroPhaseFilter(sos, x);
        double h2 = Math.Pow(Dsp.SosResponse(sos, [f], 8000)[0].Magnitude, 2);
        for (int n = 1000; n < 3000; n++)
            Assert.True(Math.Abs(y[n] - h2 * x[n]) < 1e-9, $"n = {n}");
    }

    [Fact]
    public void ZeroPhaseFilterIsLinearAndRejectsBadArguments()
    {
        double[][] sos = Dsp.ButterworthBandpass(2, 0.1, 0.2, 1);
        var rng = new Random(3);
        double[] re = [.. Enumerable.Range(0, 200).Select(_ => rng.NextDouble() - 0.5)];
        double[] im = [.. Enumerable.Range(0, 200).Select(_ => rng.NextDouble() - 0.5)];
        double[] yr = Dsp.ZeroPhaseFilter(sos, re, 10), yi = Dsp.ZeroPhaseFilter(sos, im, 10);
        Complex[] z = Dsp.ZeroPhaseFilter(sos, [.. re.Zip(im, (a, b) => new Complex(a, b))], 10);
        for (int i = 0; i < z.Length; i++)
            Assert.True((z[i] - new Complex(yr[i], yi[i])).Magnitude < 1e-12);
        Assert.All(Dsp.ZeroPhaseFilter(sos, Enumerable.Repeat(2.0, 50).ToArray()), v => Assert.Equal(0, v, 1e-12));

        double[][] flat = [[1, 0, 0, 1, 0, 0]];
        double[] ones = [.. Enumerable.Repeat(1.0, 8)];
        Assert.Throws<ArgumentException>(() => Dsp.ZeroPhaseFilter([[1, 0, 0, 1, -1, 0]], ones, 0));
        Assert.Throws<ArgumentException>(() => Dsp.ZeroPhaseFilter(flat, ones, 8));
        Assert.Throws<ArgumentOutOfRangeException>(() => Dsp.ZeroPhaseFilter(flat, ones, -1));
        Assert.Throws<ArgumentException>(() => Dsp.ZeroPhaseFilter(flat, [.. Enumerable.Repeat(1.0, 9)]));
        Assert.Throws<ArgumentException>(() => Dsp.ZeroPhaseFilter(flat, ReadOnlySpan<double>.Empty, 0));
        Assert.Throws<ArgumentException>(() => Dsp.ZeroPhaseFilter(flat, [1.0, double.NaN, 1, 1], 0));
        Assert.Throws<ArgumentException>(() => Dsp.ZeroPhaseFilter(flat, [Complex.One, new Complex(1, double.PositiveInfinity), Complex.One], 0));
        Assert.Throws<ArgumentException>(() => Dsp.ZeroPhaseFilter([[2, 0, 0, 2, -2, 0]], ones, 0));
    }

    private static double ChebT(int n, double x) =>
        Math.Abs(x) <= 1 ? Math.Cos(n * Math.Acos(x)) : Math.Pow(Math.Sign(x), n) * Math.Cosh(n * Math.Acosh(Math.Abs(x)));

    public static TheoryData<bool, int, double, double> Chebyshevs()
    {
        var data = new TheoryData<bool, int, double, double>();
        foreach (bool high in new[] { false, true })
            foreach (int order in new[] { 1, 2, 3, 6, 9 })
                foreach (var (ripple, cutoff) in new[] { (0.1, 0.01), (1.0, 0.2), (3.0, 0.49), (0.5, 0.25) })
                    data.Add(high, order, ripple, cutoff);
        return data;
    }

    [Theory]
    [MemberData(nameof(Chebyshevs))]
    public void Chebyshev1MagnitudeHasTheClosedForm(bool high, int order, double ripple, double cutoff)
    {
        double[][] sos = high ? Dsp.Chebyshev1Highpass(order, ripple, cutoff * 1000, 1000)
            : Dsp.Chebyshev1Lowpass(order, ripple, cutoff * 1000, 1000);
        Assert.Equal((order + 1) / 2, sos.Length);
        Assert.All(sos, r => Assert.True(Math.Abs(r[5]) < 1 && Math.Abs(r[4]) < 1 + r[5], "a pole outside the unit circle"));
        double eps2 = Math.Pow(10, ripple / 10) - 1, k = Math.Tan(Math.PI * cutoff);
        double[] f = [.. Enumerable.Range(0, 301).Select(i => (0.0001 + 0.4998 * i / 300) * 1000)];
        Complex[] h = Dsp.SosResponse(sos, f, 1000);
        for (int i = 0; i < f.Length; i++)
        {
            double t = Math.Tan(Math.PI * f[i] / 1000);
            double expected = 1 / (1 + eps2 * Math.Pow(ChebT(order, high ? k / t : t / k), 2));
            double got = h[i].Magnitude * h[i].Magnitude;
            Assert.True(Math.Abs(got - expected) <= 1e-11 + 1e-9 * expected, $"f = {f[i]}: {got} vs {expected}");
        }
        double edge = Dsp.SosResponse(sos, [cutoff * 1000], 1000)[0].Magnitude;
        Assert.Equal(1 / (1 + eps2), edge * edge, 1e-9);
        double end = Dsp.SosResponse(sos, [high ? 500.0 : 0.0], 1000)[0].Magnitude;
        Assert.Equal(order % 2 == 1 ? 1.0 : Math.Pow(10, -ripple / 20), end, 1e-12);
    }

    [Fact]
    public void Chebyshev1RejectsBadArguments()
    {
        foreach (var design in new Func<int, double, double, double, double[][]>[] { Dsp.Chebyshev1Lowpass, Dsp.Chebyshev1Highpass })
        {
            Assert.Throws<ArgumentOutOfRangeException>(() => design(0, 1, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, 0, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, -1, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, double.NaN, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, double.PositiveInfinity, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, 200.5, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, 4000, 1, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 1, 0, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 1, 4, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 1, 1, 0));
        }
    }

    public static TheoryData<bool, int, double, double> InverseChebyshevs()
    {
        var data = new TheoryData<bool, int, double, double>();
        foreach (bool high in new[] { false, true })
            foreach (int order in new[] { 1, 2, 3, 6, 9 })
                foreach (var (atten, cutoff) in new[] { (20.0, 0.01), (40.0, 0.2), (60.0, 0.49), (100.0, 0.25) })
                    data.Add(high, order, atten, cutoff);
        return data;
    }

    [Theory]
    [MemberData(nameof(InverseChebyshevs))]
    public void Chebyshev2MagnitudeHasTheClosedForm(bool high, int order, double atten, double cutoff)
    {
        double[][] sos = high ? Dsp.Chebyshev2Highpass(order, atten, cutoff * 1000, 1000)
            : Dsp.Chebyshev2Lowpass(order, atten, cutoff * 1000, 1000);
        Assert.Equal((order + 1) / 2, sos.Length);
        Assert.All(sos, r => Assert.True(Math.Abs(r[5]) < 1 && Math.Abs(r[4]) < 1 + r[5], "a pole outside the unit circle"));
        double eps2 = 1 / (Math.Pow(10, atten / 10) - 1), k = Math.Tan(Math.PI * cutoff), floor = Math.Pow(10, -atten / 10);
        double[] f = [.. Enumerable.Range(0, 301).Select(i => (0.0001 + 0.4998 * i / 300) * 1000)];
        Complex[] h = Dsp.SosResponse(sos, f, 1000);
        for (int i = 0; i < f.Length; i++)
        {
            double t = Math.Tan(Math.PI * f[i] / 1000);
            double x = eps2 * Math.Pow(ChebT(order, high ? t / k : k / t), 2), expected = x / (1 + x);
            double got = h[i].Magnitude * h[i].Magnitude;
            Assert.True(Math.Abs(got - expected) <= 1e-11 + 1e-9 * expected, $"f = {f[i]}: {got} vs {expected}");
            if (high ? f[i] < cutoff * 1000 : f[i] > cutoff * 1000)
                Assert.True(got <= floor * (1 + 1e-9) + 1e-15, $"stop band at {f[i]}: {got}");
        }
        double edge = Dsp.SosResponse(sos, [cutoff * 1000], 1000)[0].Magnitude;
        Assert.Equal(1, edge * edge / floor, 1e-9);
        double end = Dsp.SosResponse(sos, [high ? 500.0 : 0.0], 1000)[0].Magnitude;
        Assert.Equal(1.0, end, 1e-12);
    }

    [Fact]
    public void Chebyshev2OrderOneHasItsZeroAtTheFarEnd()
    {
        Assert.True(Dsp.SosResponse(Dsp.Chebyshev2Lowpass(1, 30, 100, 1000), [500.0], 1000)[0].Magnitude < 1e-15);
        Assert.True(Dsp.SosResponse(Dsp.Chebyshev2Highpass(1, 30, 100, 1000), [0.0], 1000)[0].Magnitude < 1e-15);
    }

    [Fact]
    public void AttenuationAndRippleMayBe200Db()
    {
        Assert.Equal(2, Dsp.Chebyshev2Lowpass(4, 200, 100, 1000).Length);
        Assert.Equal(2, Dsp.Chebyshev1Highpass(4, 200, 100, 1000).Length);
    }

    [Fact]
    public void Chebyshev2RejectsBadArguments()
    {
        foreach (var design in new Func<int, double, double, double, double[][]>[] { Dsp.Chebyshev2Lowpass, Dsp.Chebyshev2Highpass })
        {
            Assert.Throws<ArgumentOutOfRangeException>(() => design(0, 40, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, 0, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, -1, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, double.NaN, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, double.PositiveInfinity, 1, 8));
            Assert.Throws<ArgumentOutOfRangeException>(() => design(2, 200.5, 1, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 40, 0, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 40, 4, 8));
            Assert.ThrowsAny<ArgumentException>(() => design(2, 40, 1, 0));
        }
    }

    [Fact]
    public void DesignsThatRoundOntoTheUnitCircleAreRejected()
    {
        Assert.Throws<ArgumentException>(() => Dsp.ButterworthLowpass(4, 1e-9, 1));
        Assert.Throws<ArgumentException>(() => Dsp.ButterworthHighpass(4, 0.499999999, 1));
        Assert.Throws<ArgumentException>(() => Dsp.ButterworthBandpass(4, 1e-9, 2e-9, 1));
        Assert.Throws<ArgumentException>(() => Dsp.Chebyshev1Lowpass(4, 1, 1e-9, 1));
        Assert.Throws<ArgumentException>(() => Dsp.Chebyshev2Lowpass(4, 40, 1e-9, 1));
        Assert.Throws<ArgumentException>(() => Dsp.Chebyshev2Highpass(4, 40, 0.499999999, 1));
        Assert.Throws<ArgumentOutOfRangeException>(() => Dsp.ButterworthLowpass(1001, 0.1, 1));
        Assert.Throws<ArgumentOutOfRangeException>(() => Dsp.ButterworthBandstop(int.MaxValue, 0.1, 0.2, 1));
    }

    [Fact]
    public void DesignsNearTheLimitAreStillStable()
    {
        Assert.Equal(1.0, Dsp.SosResponse(Dsp.ButterworthLowpass(4, 1e-6, 1), [0.0], 1)[0].Magnitude, 1e-9);
        Assert.Equal(1.0, Dsp.SosResponse(Dsp.Chebyshev2Lowpass(4, 40, 1e-6, 1), [0.0], 1)[0].Magnitude, 1e-9);
    }

    [Fact]
    public void TinyDbValuesKeepTheirDigits()
    {
        double ripple = 1e-9, want = ripple * Math.Log(10) / 10;
        double edge = Dsp.SosResponse(Dsp.Chebyshev1Lowpass(3, ripple, 100, 1000), [100.0], 1000)[0].Magnitude;
        Assert.True(Math.Abs((1 - edge * edge) / want - 1) < 1e-5, $"{1 - edge * edge} vs {want}");
        Assert.All(Dsp.Chebyshev2Lowpass(3, 1e-9, 100, 1000), r => Assert.True(Math.Abs(r[5]) < 1 && Math.Abs(r[4]) < 1 + r[5]));
    }

    private static double[][] BandChebyshev(int kind, bool stop, int order, double db, double low, double high, double fs) =>
        (kind, stop) switch
        {
            (1, false) => Dsp.Chebyshev1Bandpass(order, db, low, high, fs),
            (1, true) => Dsp.Chebyshev1Bandstop(order, db, low, high, fs),
            (2, false) => Dsp.Chebyshev2Bandpass(order, db, low, high, fs),
            _ => Dsp.Chebyshev2Bandstop(order, db, low, high, fs),
        };

    public static TheoryData<int, bool, int, double, double, double> BandChebyshevs()
    {
        var data = new TheoryData<int, bool, int, double, double, double>();
        foreach (int kind in new[] { 1, 2 })
            foreach (bool stop in new[] { false, true })
                foreach (int order in new[] { 1, 2, 3, 6 })
                    foreach (var (low, high, db) in new[] { (0.001, 0.002, 0.5), (0.1, 0.11, 3.0), (0.05, 0.45, 40.0), (0.3, 0.45, 80.0) })
                        data.Add(kind, stop, order, low, high, db);
        return data;
    }

    [Theory]
    [MemberData(nameof(BandChebyshevs))]
    public void ChebyshevBandMagnitudeHasTheClosedForm(int kind, bool stop, int order, double low, double high, double db)
    {
        double[][] sos = BandChebyshev(kind, stop, order, db, low * 1000, high * 1000, 1000);
        Assert.Equal(order, sos.Length);
        Assert.All(sos, r => Assert.True(Math.Abs(r[5]) < 1 && Math.Abs(r[4]) < 1 + r[5], "a pole outside the unit circle"));
        double lo = Math.Tan(Math.PI * low), hi = Math.Tan(Math.PI * high), w2 = lo * hi, bw = hi - lo;
        double ratio = Math.Pow(10, db / 10) - 1;
        double[] f = [.. Enumerable.Range(0, 301).Select(i => (-0.4999 + 0.9998 * i / 300) * 1000)];
        Complex[] h = Dsp.SosResponse(sos, f, 1000);
        for (int i = 0; i < f.Length; i++)
        {
            double t = Math.Abs(Math.Tan(Math.PI * f[i] / 1000));
            double x = stop ? bw * t / (w2 - t * t) : (t * t - w2) / (bw * t);
            double expected = kind == 1
                ? 1 / (1 + ratio * Math.Pow(ChebT(order, x), 2))
                : 1 / (1 + 1 / (Math.Pow(ChebT(order, 1 / x), 2) / ratio));
            double got = h[i].Magnitude * h[i].Magnitude;
            Assert.True(Math.Abs(got - expected) <= 1e-10 + 1e-8 * expected, $"f = {f[i]}: {got} vs {expected}");
        }
        foreach (Complex e in Dsp.SosResponse(sos, [low * 1000, high * 1000], 1000))
            Assert.True(Math.Abs(e.Magnitude * e.Magnitude * (1 + ratio) - 1) < 1e-8);
    }

    [Fact]
    public void ChebyshevBandReferenceGains()
    {
        double center = 1000 / Math.PI * Math.Atan(Math.Sqrt(Math.Tan(Math.PI * 0.1) * Math.Tan(Math.PI * 0.2)));
        foreach (var (order, want) in new[] { (3, 1.0), (4, Math.Pow(10, -1.0 / 20)) }) // even type I: the ripple's low point
        {
            Assert.Equal(want, Dsp.SosResponse(Dsp.Chebyshev1Bandpass(order, 1, 100, 200, 1000), [center], 1000)[0].Magnitude, 1e-9);
            Assert.All(Dsp.SosResponse(Dsp.Chebyshev1Bandstop(order, 1, 100, 200, 1000), [0.0, 500], 1000),
                h => Assert.Equal(want, h.Magnitude, 1e-9));
        }
        Assert.Equal(1.0, Dsp.SosResponse(Dsp.Chebyshev2Bandpass(4, 40, 100, 200, 1000), [center], 1000)[0].Magnitude, 1e-9);
        Assert.All(Dsp.SosResponse(Dsp.Chebyshev2Bandstop(4, 40, 100, 200, 1000), [0.0, 500], 1000),
            h => Assert.Equal(1.0, h.Magnitude, 1e-9));
    }

    [Fact]
    public void ChebyshevBandRejectsBadArguments()
    {
        foreach (int kind in new[] { 1, 2 })
            foreach (bool stop in new[] { false, true })
            {
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 0, 1, 0.1, 0.2, 1));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 1001, 1, 0.1, 0.2, 1));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 2, 0, 0.1, 0.2, 1));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 2, 250, 0.1, 0.2, 1));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 2, double.NaN, 0.1, 0.2, 1));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 2, 1, 0.2, 0.1, 1));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 2, 1, 0.1, 0.5, 1));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 2, 1, 0, 0.2, 1));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 2, 1, 0.1, 0.2, 0));
                Assert.ThrowsAny<ArgumentException>(() => BandChebyshev(kind, stop, 4, 1, 1e-9, 2e-9, 1));
            }
    }

    [Theory]
    [InlineData(false, 1, 1.0, 40.0, 0.1)]
    [InlineData(false, 2, 0.5, 20.0, 0.2)]
    [InlineData(false, 3, 0.1, 60.0, 0.05)]
    [InlineData(false, 5, 1.0, 80.0, 0.3)]
    [InlineData(false, 6, 3.0, 30.0, 0.25)]
    [InlineData(false, 9, 0.01, 120.0, 0.1)]
    [InlineData(false, 12, 0.5, 100.0, 0.4)]
    [InlineData(true, 1, 1.0, 40.0, 0.1)]
    [InlineData(true, 3, 0.1, 60.0, 0.05)]
    [InlineData(true, 6, 3.0, 30.0, 0.25)]
    [InlineData(true, 12, 0.5, 100.0, 0.4)]
    public void EllipticIsEquirippleInBothBands(bool high, int order, double ripple, double atten, double cutoff)
    {
        double[][] sos = high ? Dsp.EllipticHighpass(order, ripple, atten, cutoff, 1) : Dsp.EllipticLowpass(order, ripple, atten, cutoff, 1);
        Assert.Equal((order + 1) / 2, sos.Length);
        Assert.All(sos, r => Assert.True(Math.Abs(r[5]) < 1 && Math.Abs(r[4]) < 1 + r[5], "a pole outside the unit circle"));
        double passLo = Math.Pow(10, -ripple / 10), stopHi = Math.Pow(10, -atten / 10);
        // Frequencies from the pass band outwards.
        double[] f = [.. Enumerable.Range(0, 200001).Select(i => high ? 0.5 - 0.5 * i / 200000 : 0.5 * i / 200000)];
        double[] h2 = [.. Dsp.SosResponse(sos, f, 1).Select(h => h.Magnitude * h.Magnitude)];
        double passMax = 0;
        int first = -1;
        for (int i = 0; i < f.Length; i++)
        {
            if (high ? f[i] >= cutoff : f[i] <= cutoff)
            {
                Assert.True(h2[i] <= 1 + 1e-12 && h2[i] >= passLo * (1 - 1e-12), $"pass band at {f[i]}: {h2[i]}");
                passMax = Math.Max(passMax, h2[i]);
            }
            else if (first < 0 && h2[i] <= stopHi * (1 + 1e-9))
                first = i;
        }
        Assert.Equal(1.0, passMax, 1e-6);
        Complex edge = Dsp.SosResponse(sos, [cutoff], 1)[0];
        Assert.True(Math.Abs(edge.Magnitude * edge.Magnitude / passLo - 1) < 1e-10);
        double stopMax = h2[first..].Max();
        Assert.True(stopMax <= stopHi * (1 + 1e-6), $"stop band peak {stopMax}");
        if (order > 1)
            Assert.True(Math.Abs(stopMax / stopHi - 1) < 1e-3, $"stop band peak {stopMax} vs {stopHi}");
        double reference = Dsp.SosResponse(sos, [high ? 0.5 : 0.0], 1)[0].Magnitude;
        Assert.Equal(order % 2 == 1 ? 1.0 : Math.Pow(10, -ripple / 20), reference, 1e-12);
    }

    [Fact]
    public void EllipticOrder1IsChebyshev1()
    {
        double[] e = Dsp.EllipticLowpass(1, 1, 40, 100, 1000)[0], c = Dsp.Chebyshev1Lowpass(1, 1, 100, 1000)[0];
        for (int j = 0; j < 6; j++)
            Assert.Equal(c[j], e[j], 1e-13);
    }

    [Theory]
    [InlineData(0, 1.0, 40.0, 0.1, 1.0)]
    [InlineData(1001, 1.0, 40.0, 0.1, 1.0)]
    [InlineData(4, 0.0, 40.0, 0.1, 1.0)]
    [InlineData(4, 40.0, 40.0, 0.1, 1.0)]
    [InlineData(4, 50.0, 40.0, 0.1, 1.0)]
    [InlineData(4, 1.0, 250.0, 0.1, 1.0)]
    [InlineData(4, double.NaN, 40.0, 0.1, 1.0)]
    [InlineData(4, 1.0, double.PositiveInfinity, 0.1, 1.0)]
    [InlineData(4, 1.0, 40.0, 0.5, 1.0)]
    [InlineData(4, 1.0, 40.0, 0.0, 1.0)]
    [InlineData(1000, 1.0, 2.0, 0.1, 1.0)]
    public void EllipticRejectsBadArguments(int order, double ripple, double atten, double cutoff, double fs)
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.EllipticLowpass(order, ripple, atten, cutoff, fs));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.EllipticHighpass(order, ripple, atten, cutoff, fs));
    }

    [Theory]
    [InlineData(false, 1, 1.0, 40.0, 0.1, 0.2)]
    [InlineData(false, 2, 0.5, 30.0, 0.001, 0.002)]
    [InlineData(false, 3, 0.1, 60.0, 0.1, 0.11)]
    [InlineData(false, 4, 1.0, 80.0, 0.05, 0.45)]
    [InlineData(false, 7, 0.2, 100.0, 0.3, 0.45)]
    [InlineData(true, 1, 1.0, 40.0, 0.1, 0.2)]
    [InlineData(true, 2, 0.5, 30.0, 0.001, 0.002)]
    [InlineData(true, 3, 0.1, 60.0, 0.1, 0.11)]
    [InlineData(true, 4, 1.0, 80.0, 0.05, 0.45)]
    [InlineData(true, 7, 0.2, 100.0, 0.3, 0.45)]
    public void EllipticBandIsTheLowpassThroughTheBandMap(bool stop, int order, double ripple, double atten, double low, double high)
    {
        double[][] sos = stop ? Dsp.EllipticBandstop(order, ripple, atten, low * 1000, high * 1000, 1000)
            : Dsp.EllipticBandpass(order, ripple, atten, low * 1000, high * 1000, 1000);
        Assert.Equal(order, sos.Length);
        Assert.All(sos, r => Assert.True(Math.Abs(r[5]) < 1 && Math.Abs(r[4]) < 1 + r[5], "a pole outside the unit circle"));
        double lo = Math.Tan(Math.PI * low), hi = Math.Tan(Math.PI * high), w2 = lo * hi, bw = hi - lo;
        double[] f = [.. Enumerable.Range(0, 999).Select(i => 0.0005 + 0.0005 * i)];
        double[] mapped = [.. f.Select(v =>
        {
            double t = Math.Tan(Math.PI * v);
            return Math.Atan(Math.Abs(stop ? bw * t / (w2 - t * t) : (t * t - w2) / (bw * t))) / Math.PI;
        })];
        double[][] lowpass = Dsp.EllipticLowpass(order, ripple, atten, 0.25, 1); // prewarped edge 1
        Complex[] want = Dsp.SosResponse(lowpass, mapped, 1);
        Complex[] got = Dsp.SosResponse(sos, [.. f.Select(v => v * 1000)], 1000);
        for (int i = 0; i < f.Length; i++)
        {
            double w = want[i].Magnitude * want[i].Magnitude, g = got[i].Magnitude * got[i].Magnitude;
            Assert.True(Math.Abs(g - w) <= 1e-12 + 1e-8 * w, $"{f[i]}: {g} vs {w}");
        }
        foreach (Complex e in Dsp.SosResponse(sos, [low * 1000, high * 1000], 1000))
            Assert.True(Math.Abs(e.Magnitude * e.Magnitude / Math.Pow(10, -ripple / 10) - 1) < 1e-8);
    }

    [Fact]
    public void EllipticBandReferenceGains()
    {
        double center = 1000 / Math.PI * Math.Atan(Math.Sqrt(Math.Tan(Math.PI * 0.1) * Math.Tan(Math.PI * 0.2)));
        foreach (var (order, want) in new[] { (3, 1.0), (4, Math.Pow(10, -1 / 20.0)) }) // even: the ripple's low point
        {
            double[][] bp = Dsp.EllipticBandpass(order, 1, 50, 100, 200, 1000), bs = Dsp.EllipticBandstop(order, 1, 50, 100, 200, 1000);
            Assert.Equal(want, Dsp.SosResponse(bp, [center], 1000)[0].Magnitude, 1e-9);
            foreach (Complex h in Dsp.SosResponse(bs, [0.0, 500.0], 1000))
                Assert.Equal(want, h.Magnitude, 1e-9);
            // The band-stop's center is the prototype's infinity: a zero (odd) or the stop level.
            Assert.Equal(order % 2 == 1 ? 0.0 : Math.Pow(10, -50 / 20.0), Dsp.SosResponse(bs, [center], 1000)[0].Magnitude, 1e-12);
        }
    }

    [Theory]
    [InlineData(0, 1.0, 40.0, 0.1, 0.2, 1.0)]
    [InlineData(1001, 1.0, 40.0, 0.1, 0.2, 1.0)]
    [InlineData(2, 0.0, 40.0, 0.1, 0.2, 1.0)]
    [InlineData(2, 40.0, 40.0, 0.1, 0.2, 1.0)]
    [InlineData(2, 1.0, 250.0, 0.1, 0.2, 1.0)]
    [InlineData(2, double.NaN, 40.0, 0.1, 0.2, 1.0)]
    [InlineData(2, 1.0, 40.0, 0.2, 0.1, 1.0)]
    [InlineData(2, 1.0, 40.0, 0.1, 0.5, 1.0)]
    [InlineData(2, 1.0, 40.0, 0.0, 0.2, 1.0)]
    [InlineData(2, 1.0, 40.0, 0.1, 0.2, 0.0)]
    [InlineData(4, 1.0, 40.0, 1e-9, 2e-9, 1.0)]
    [InlineData(1000, 1.0, 2.0, 0.1, 0.2, 1.0)]
    public void EllipticBandRejectsBadArguments(int order, double ripple, double atten, double low, double high, double fs)
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.EllipticBandpass(order, ripple, atten, low, high, fs));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.EllipticBandstop(order, ripple, atten, low, high, fs));
    }
}
