using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Bessel design (conventions: IIR filters, Bessel design); the shared vectors hold the
/// exact sections, these check the design's properties.</summary>
public class BesselTests
{
    private static double[][] Design(bool high, int order, double cutoff, double fs) =>
        high ? Dsp.BesselHighpass(order, cutoff, fs) : Dsp.BesselLowpass(order, cutoff, fs);

    public static TheoryData<bool, int> Orders()
    {
        var data = new TheoryData<bool, int>();
        foreach (bool high in new[] { false, true })
        {
            for (int n = 1; n <= 10; n++)
                data.Add(high, n);
        }
        return data;
    }

    [Theory]
    [MemberData(nameof(Orders))]
    public void Is3DbAtTheCutoffAndMonotonic(bool high, int order)
    {
        double[][] sos = Design(high, order, 0.15, 1);
        Assert.Equal(0.5, Math.Pow(Dsp.SosResponse(sos, [0.15], 1)[0].Magnitude, 2), 1e-12);
        Assert.Equal(1, Dsp.SosResponse(sos, [high ? 0.5 : 0], 1)[0].Magnitude, 1e-13);
        double[] f = [.. Enumerable.Range(0, 501).Select(i => i / 1000.0)];
        double[] h = [.. Dsp.SosResponse(sos, f, 1).Select(z => z.Magnitude)];
        for (int i = 1; i < h.Length; i++)
            Assert.True(high ? h[i] > h[i - 1] : h[i] < h[i - 1]);
    }

    public static TheoryData<bool, int> BandOrders() => Orders();

    [Theory]
    [MemberData(nameof(BandOrders))]
    public void BandIsTheLowPassAtTheTransformedFrequency(bool stop, int order)
    {
        // A low-pass at fs/4 has K = 1, so its gain at fs/pi atan(|x|) is the prototype's at |x|.
        double low = 0.12, high = 0.3;
        double[][] sos = stop ? Dsp.BesselBandstop(order, low, high, 1) : Dsp.BesselBandpass(order, low, high, 1);
        double[][] lp = Dsp.BesselLowpass(order, 0.25, 1);
        double lo = Math.Tan(Math.PI * low), hi = Math.Tan(Math.PI * high);
        double[] f = [.. Enumerable.Range(0, 199).Select(i => 0.005 + i * 0.0025)];
        double[] x = [.. f.Select(v =>
        {
            double t = Math.Tan(Math.PI * v);
            return stop ? (hi - lo) * t / Math.Abs(lo * hi - t * t) : Math.Abs(t * t - lo * hi) / ((hi - lo) * t);
        })];
        Complex[] got = Dsp.SosResponse(sos, f, 1);
        Complex[] want = Dsp.SosResponse(lp, [.. x.Select(v => Math.Atan(v) / Math.PI)], 1);
        for (int i = 0; i < f.Length; i++)
            Assert.True(Math.Abs(got[i].Magnitude - want[i].Magnitude) <= 1e-12 + 1e-9 * want[i].Magnitude, $"{f[i]}");
        foreach (Complex h in Dsp.SosResponse(sos, [low, high], 1))
            Assert.Equal(0.5, h.Magnitude * h.Magnitude, 1e-12);
        Assert.Equal(order, sos.Length);
    }

    [Fact]
    public void BandOrder1IsButterworth()
    {
        double[][][] pairs = [Dsp.BesselBandpass(1, 100, 300, 1000), Dsp.ButterworthBandpass(1, 100, 300, 1000),
            Dsp.BesselBandstop(1, 100, 300, 1000), Dsp.ButterworthBandstop(1, 100, 300, 1000)];
        for (int p = 0; p < 4; p += 2)
        {
            for (int j = 0; j < 6; j++)
                Assert.Equal(pairs[p + 1][0][j], pairs[p][0][j], 1e-15);
        }
    }

    [Theory]
    [InlineData(0, 0.1, 0.2, 1)]
    [InlineData(11, 0.1, 0.2, 1)]
    [InlineData(3, 0.2, 0.1, 1)]
    [InlineData(3, 0.1, 0.5, 1)]
    public void BandRejectsBadArguments(int order, double low, double high, double fs)
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.BesselBandpass(order, low, high, fs));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.BesselBandstop(order, low, high, fs));
    }

    [Fact]
    public void Order1IsButterworth()
    {
        double[] b = Dsp.BesselLowpass(1, 100, 1000)[0], w = Dsp.ButterworthLowpass(1, 100, 1000)[0];
        double[] bh = Dsp.BesselHighpass(1, 100, 1000)[0], wh = Dsp.ButterworthHighpass(1, 100, 1000)[0];
        for (int j = 0; j < 6; j++)
        {
            Assert.Equal(w[j], b[j], 1e-15);
            Assert.Equal(wh[j], bh[j], 1e-15);
        }
    }

    private static double[] GroupDelay(double[][] sos, double[] f)
    {
        const double df = 1e-6;
        Complex[] hi = Dsp.SosResponse(sos, [.. f.Select(x => x + df)], 1), lo = Dsp.SosResponse(sos, [.. f.Select(x => x - df)], 1);
        return [.. hi.Zip(lo, (a, b) => -(a / b).Phase / (2 * Math.PI * 2 * df))];
    }

    [Fact]
    public void DelayIsFlatWhereButterworthsIsNot()
    {
        // At a cutoff well below fs/2 the bilinear transform keeps the analog delay's shape.
        double[] f = [.. Enumerable.Range(0, 40).Select(i => 0.0005 + 0.0095 * i / 39)];
        foreach (int order in new[] { 4, 6, 10 })
        {
            double[] gd = GroupDelay(Dsp.BesselLowpass(order, 0.02, 1), f);
            Assert.True((gd.Max() - gd.Min()) / gd.Average() < 0.005);
            double[] gb = GroupDelay(Dsp.ButterworthLowpass(order, 0.02, 1), f);
            Assert.True((gb.Max() - gb.Min()) / gb.Average() > 0.05);
        }
    }

    [Fact]
    public void Order2DelayAtDc()
    {
        // θ₂(ω₀s) has delay ω₀·a₁/a₀ = ω₀ at DC; the bilinear map adds a factor 1/(2K).
        double k = Math.Tan(Math.PI * 0.02), w0 = Math.Sqrt(3 * (Math.Sqrt(5) - 1) / 2);
        double gd = GroupDelay(Dsp.BesselLowpass(2, 0.02, 1), [1e-5])[0];
        Assert.Equal(1, gd / (w0 / (2 * k)), 1e-6);
    }

    [Theory]
    [InlineData(0, 0.1, 1.0)]
    [InlineData(11, 0.1, 1.0)]
    [InlineData(-1, 0.1, 1.0)]
    [InlineData(4, 0.5, 1.0)]
    [InlineData(4, 0.0, 1.0)]
    [InlineData(4, double.NaN, 1.0)]
    [InlineData(4, 0.1, double.PositiveInfinity)]
    [InlineData(4, 0.1, 0.0)]
    public void RejectsBadArguments(int order, double cutoff, double fs)
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.BesselLowpass(order, cutoff, fs));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.BesselHighpass(order, cutoff, fs));
    }
}
