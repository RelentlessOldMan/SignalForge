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
