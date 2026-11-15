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

    /// <summary>The integral squared error of antisymmetric taps, A = Σ h[n]·sin(2πν(n − c)), trapezoid on 4001 points.</summary>
    private static double AntiEnergy(double[] h, double[] bands, double[] target, bool differentiator)
    {
        double c = (h.Length - 1) / 2.0, total = 0;
        for (int j = 0; j < bands.Length / 2; j++)
        {
            double lo = bands[2 * j], hi = bands[2 * j + 1], step = (hi - lo) / 4000, sum = 0;
            for (int i = 0; i <= 4000; i++)
            {
                double nu = lo + (i * step), a = 0;
                for (int n = 0; n < h.Length; n++)
                    a += h[n] * Math.Sin(2 * Math.PI * nu * (n - c));
                double d = target[2 * j] + ((target[2 * j + 1] - target[2 * j]) * (nu - lo) / (hi - lo));
                if (differentiator)
                    d *= -2 * Math.PI * nu;
                double e = (a - d) * (a - d);
                sum += i == 0 || i == 4000 ? e / 2 : e;
            }
            total += sum * step;
        }
        return total;
    }

    [Theory]
    [InlineData(9, FirKind.Hilbert)]
    [InlineData(10, FirKind.Hilbert)]
    [InlineData(9, FirKind.Differentiator)]
    [InlineData(10, FirKind.Differentiator)]
    public void AntisymmetricPerturbationsOnlyRaiseTheError(int n, FirKind kind)
    {
        bool diff = kind == FirKind.Differentiator;
        double[] bands = diff ? [0, 0.3, 0.35, 0.5] : [0.04, 0.46], target = diff ? [1, 1, 0, 0] : [1, 1];
        double[] h = Dsp.FirLeastSquares(n, bands, target, 1, kind: kind);
        Assert.Equal(h, h.Reverse().Select(v => -v));
        double best = AntiEnergy(h, bands, target, diff);
        var rng = new Random(5);
        for (int trial = 0; trial < 5; trial++)
        {
            double[] d = [.. Enumerable.Range(0, n).Select(_ => rng.NextDouble() - 0.5)];
            foreach (int sign in new[] { 1, -1 })
            {
                double[] moved = [.. Enumerable.Range(0, n).Select(i => h[i] + (sign * 1e-3 * (d[i] - d[n - 1 - i])))];
                Assert.True(AntiEnergy(moved, bands, target, diff) > best);
            }
        }
    }

    [Fact]
    public void DifferentiatorFollowsTheSlope()
    {
        double[] h = Dsp.FirLeastSquares(41, [0, 0.3, 0.4, 0.5], [1, 1, 0, 0], 1, [1, 1], FirKind.Differentiator);
        Assert.Equal(0.0, h[20]);
        for (int i = 0; i < 40; i++)
        {
            double nu = 0.01 + (0.27 * i / 39), a = 0;
            for (int n = 0; n < 41; n++)
                a += h[n] * Math.Sin(2 * Math.PI * nu * (n - 20));
            Assert.True(Math.Abs(a + (2 * Math.PI * nu)) < 1e-3);
        }
    }

    [Fact]
    public void AntisymmetricBadArguments()
    {
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(11, Bands, Desired, 1, kind: (FirKind)9));
        Assert.ThrowsAny<ArgumentException>(() => Dsp.FirLeastSquares(1, Bands, Desired, 1, kind: FirKind.Hilbert));
    }
}
