using Xunit;

namespace SignalForge.Tests;

/// <summary>Least-squares FIR design: optimality, against equiripple, type II, errors
/// (conventions: FIR filters, Least-squares design).</summary>
public class LeastSquaresTests
{
    private static readonly double[] Bands = [0.0, 0.1, 0.15, 0.5];
    private static readonly double[] Desired = [1.0, 1.0, 0.0, 0.0];

    /// <summary>The zero-phase gain of symmetric taps at ν = f/fs.</summary>
    private static double Gain(double[] h, double nu)
    {
        double c = (h.Length - 1) / 2.0, s = 0;
        for (int n = 0; n < h.Length; n++)
            s += h[n] * Math.Cos(2 * Math.PI * nu * (n - c));
        return s;
    }

    /// <summary>The weighted integral squared error by the trapezoid rule on 4001 points per band.</summary>
    private static double Energy(double[] h, double[] bands, double[] desired, double[] weights)
    {
        double total = 0;
        for (int j = 0; j < weights.Length; j++)
        {
            double lo = bands[2 * j], hi = bands[2 * j + 1], step = (hi - lo) / 4000;
            double sum = 0;
            for (int i = 0; i <= 4000; i++)
            {
                double nu = lo + i * step;
                double d = desired[2 * j] + (desired[2 * j + 1] - desired[2 * j]) * (nu - lo) / (hi - lo);
                double e = Math.Pow(Gain(h, nu) - d, 2);
                sum += i == 0 || i == 4000 ? e / 2 : e;
            }
            total += weights[j] * sum * step;
        }
        return total;
    }

    [Theory]
    [InlineData(31)]
    [InlineData(30)]
    public void SymmetricPerturbationsOnlyRaiseTheError(int n)
    {
        double[] h = Dsp.FirLeastSquares(n, Bands, Desired, 1, [1, 4]);
        for (int i = 0; i < n; i++)
            Assert.Equal(h[i], h[n - 1 - i]);
        double best = Energy(h, Bands, Desired, [1, 4]);
        var rng = new Random(5);
        for (int trial = 0; trial < 5; trial++)
        {
            double[] d = [.. Enumerable.Range(0, n).Select(_ => rng.NextDouble() - 0.5)];
            double[] moved = [.. Enumerable.Range(0, n).Select(i => h[i] + 1e-3 * (d[i] + d[n - 1 - i]))];
            Assert.True(Energy(moved, Bands, Desired, [1, 4]) > best);
        }
    }

    [Fact]
    public void LowerErrorEnergyThanEquiripple()
    {
        double[] ls = Dsp.FirLeastSquares(41, Bands, Desired, 1);
        double[] eq = Dsp.FirEquiripple(41, Bands, [1.0, 0.0], 1);
        Assert.True(Energy(ls, Bands, Desired, [1, 1]) < Energy(eq, Bands, Desired, [1, 1]));
    }

    [Fact]
    public void EvenTapsHaveAZeroAtNyquist()
    {
        double[] h = Dsp.FirLeastSquares(16, [0, 0.2, 0.3, 0.5], [0, 0, 1, 1], 1);
        Assert.True(Dsp.FirResponse(h, [0.5], 1)[0].Magnitude < 1e-12);
    }

    [Fact]
    public void SlopedBandIsFollowed()
    {
        double[] h = Dsp.FirLeastSquares(61, [0, 0.4], [0, 0.8], 1);
        for (double nu = 0.05; nu < 0.36; nu += 0.05)
            Assert.True(Math.Abs(Gain(h, nu) - 2 * nu) < 1e-3);
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(0, Bands, Desired, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(1002, Bands, Desired, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, Bands, [1.0, 0.0], 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, [0, 0.2, 0.3], Desired, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, [0, 0.2, 0.2, 0.5], Desired, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, [0, 0.2, 0.3, 0.6], Desired, 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, Bands, Desired, 1, [1.0, 0.0]));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, Bands, Desired, 1, [1.0]));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, Bands, [1, double.NaN, 0, 0], 1));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, Bands, Desired, 0));
    }
}
