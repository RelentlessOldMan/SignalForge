using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Soft demapping: the sign is the hard decision, QPSK's closed form, the bound against the
/// exact log-sum LLR, and scaling with the noise variance (conventions: Bits and symbols, Soft
/// demapping).</summary>
public class SoftDemapTests
{
    private static Complex[] Map(int k, byte[] b) => k switch
    {
        2 => Modulation.QpskMap(b),
        3 => Modulation.Psk8Map(b),
        _ => Modulation.Qam16Map(b),
    };

    private static byte[] Hard(int k, Complex[] y) => k switch
    {
        2 => Modulation.QpskDemapHard(y),
        3 => Modulation.Psk8DemapHard(y),
        _ => Modulation.Qam16DemapHard(y),
    };

    private static double[] Soft(int k, Complex[] y, double n0) => k switch
    {
        2 => Modulation.QpskDemapLlr(y, n0),
        3 => Modulation.Psk8DemapLlr(y, n0),
        _ => Modulation.Qam16DemapLlr(y, n0),
    };

    private static Complex[] Noisy(int k, double n0, int seed) =>
        Channel.Awgn(Map(k, Waveforms.Prbs(11, k * 2047)), 10 * Math.Log10(1 / n0), 1, seed, 1.0);

    [Theory]
    [InlineData(2)]
    [InlineData(3)]
    [InlineData(4)]
    public void SignIsTheHardDecision(int k)
    {
        Complex[] y = Noisy(k, 0.2, 1);
        double[] llr = Soft(k, y, 0.2);
        byte[] hard = Hard(k, y);
        Assert.Equal(k * y.Length, llr.Length);
        for (int i = 0; i < llr.Length; i++)
            if (Math.Abs(llr[i]) > 1e-9)
                Assert.Equal(llr[i] < 0 ? 1 : 0, hard[i]);
    }

    private static double LogSumExp(IEnumerable<double> v)
    {
        double[] a = [.. v];
        double top = a.Max();
        return top + Math.Log(a.Sum(x => Math.Exp(x - top)));
    }

    [Theory]
    [InlineData(2)]
    [InlineData(3)]
    [InlineData(4)]
    public void WithinTheBoundOfTheExactLlr(int k)
    {
        const double n0 = 0.3;
        int m = 1 << k;
        var labels = new byte[k * m];
        for (int p = 0; p < m; p++)
            for (int i = 0; i < k; i++)
                labels[p * k + i] = (byte)((p >> (k - 1 - i)) & 1);
        Complex[] points = Map(k, labels), y = Noisy(k, n0, 2);
        double[] llr = Soft(k, y, n0);
        double worst = 0;
        for (int n = 0; n < y.Length; n++)
            for (int i = 0; i < k; i++)
            {
                int bit = i;
                IEnumerable<double> Metric(int b) => Enumerable.Range(0, m)
                    .Where(p => ((p >> (k - 1 - bit)) & 1) == b)
                    .Select(p => -Math.Pow(Complex.Abs(y[n] - points[p]), 2) / n0);
                double exact = LogSumExp(Metric(0)) - LogSumExp(Metric(1));
                worst = Math.Max(worst, Math.Abs(llr[n * k + i] - exact));
            }
        Assert.True(worst <= Math.Log(m / 2.0) + 1e-9, $"{worst}");
        if (k == 2)
            Assert.True(worst < 1e-9, $"{worst}");
    }

    [Fact]
    public void QpskClosedFormAndScaling()
    {
        var rng = new Random(4);
        Complex[] y = [.. Enumerable.Range(0, 100).Select(_ => new Complex(rng.NextDouble() * 4 - 2, rng.NextDouble() * 4 - 2))];
        double[] llr = Modulation.QpskDemapLlr(y, 0.7);
        for (int n = 0; n < y.Length; n++)
        {
            Assert.Equal(2 * Math.Sqrt(2) * y[n].Real / 0.7, llr[2 * n], 1e-12);
            Assert.Equal(2 * Math.Sqrt(2) * y[n].Imaginary / 0.7, llr[2 * n + 1], 1e-12);
        }
        foreach (int k in new[] { 3, 4 })
        {
            double[] one = Soft(k, y, 1), two = Soft(k, y, 2);
            for (int i = 0; i < one.Length; i++)
                Assert.Equal(one[i] / 2, two[i], 1e-14);
        }
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Psk8DemapLlr([Complex.One], -1));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.QpskDemapLlr([Complex.One], double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Modulation.Qam16DemapLlr([new Complex(double.PositiveInfinity, 0)], 1));
    }
}
