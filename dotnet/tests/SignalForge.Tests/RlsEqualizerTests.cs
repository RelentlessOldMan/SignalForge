using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>The recursive-least-squares equalizer (conventions: Synchronization, RLS equalizer;
/// ADR 0076).</summary>
public sealed class RlsEqualizerTests
{
    // a zero at radius 0.9: badly conditioned, so normalized LMS converges slowly (ADR 0076)
    private static readonly Complex[] H = [1, Complex.FromPolarCoordinates(0.9, 0.6)];

    private static double Gauss(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    private static (Complex[] A, Complex[] X) Hard(int seed, int n)
    {
        var rng = new Random(seed);
        var bits = new byte[2 * n];
        for (int i = 0; i < bits.Length; i++)
            bits[i] = (byte)rng.Next(2);
        Complex[] a = Modulation.QpskMap(bits);
        var x = new Complex[n];
        for (int k = 0; k < n; k++)
            x[k] = a[k] + (k > 0 ? H[1] * a[k - 1] : Complex.Zero) + new Complex(0.05 * Gauss(rng), 0.05 * Gauss(rng));
        return (a, x);
    }

    private static double Mse(Complex[] y, Complex[] a, int from, int to)
    {
        double e = 0;
        for (int k = from; k < to; k++)
            e += Math.Pow((y[k] - a[k]).Magnitude, 2);
        return e / (to - from);
    }

    [Fact]
    public void ConvergesWhereLmsIsSlow()
    {
        // measured in ADR 0076 (Python's noise): RLS 0.06 over symbols 25-49, LMS (step 0.5) 0.32;
        // after 400 symbols RLS about 0.03, LMS still 0.11
        double re = 0, me = 0, rl = 0, ml = 0;
        for (int seed = 0; seed < 10; seed++)
        {
            var (a, x) = Hard(seed, 400);
            Complex[] r = Sync.RlsEqualizer(x, a, 15, 1.0, center: 2).Symbols;
            Complex[] m = Sync.LmsEqualizer(x, a, 15, 0.5, center: 2).Symbols;
            re += Mse(r, a, 25, 50) / 10;
            me += Mse(m, a, 25, 50) / 10;
            rl += Mse(r, a, 300, 400) / 10;
            ml += Mse(m, a, 300, 400) / 10;
        }
        Assert.True(re < 0.1 && me > 0.2, $"{re} {me}");
        Assert.True(rl < 0.05 && ml > 0.08, $"{rl} {ml}");
    }

    // a z = b by Gaussian elimination with partial pivoting
    private static Complex[] Solve(Complex[,] a, Complex[] b)
    {
        int n = b.Length;
        for (int k = 0; k < n; k++)
        {
            int piv = k;
            for (int i = k + 1; i < n; i++)
                if (a[i, k].Magnitude > a[piv, k].Magnitude)
                    piv = i;
            for (int j = 0; j < n; j++)
                (a[k, j], a[piv, j]) = (a[piv, j], a[k, j]);
            (b[k], b[piv]) = (b[piv], b[k]);
            for (int i = k + 1; i < n; i++)
            {
                Complex f = a[i, k] / a[k, k];
                for (int j = k; j < n; j++)
                    a[i, j] -= f * a[k, j];
                b[i] -= f * b[k];
            }
        }
        var z = new Complex[n];
        for (int i = n - 1; i >= 0; i--)
        {
            Complex s = b[i];
            for (int j = i + 1; j < n; j++)
                s -= a[i, j] * z[j];
            z[i] = s / a[i, i];
        }
        return z;
    }

    [Theory]
    [InlineData(1.0, 0.01)]
    [InlineData(0.95, 0.3)]
    public void TapsAreTheWeightedLeastSquaresSolution(double lam, double delta)
    {
        var (a, x) = Hard(3, 60);
        const int taps = 6, c = 1;
        Equalization r = Sync.RlsEqualizer(x, a, taps, lam, delta, center: c);
        // the regressors as the conventions define them, solved directly
        var big = new Complex[taps, taps];
        var rhs = new Complex[taps];
        for (int i = 0; i < taps; i++)
            big[i, i] = Math.Pow(lam, 60) * delta;
        rhs[c] = Math.Pow(lam, 60) * delta;
        for (int n = 0; n < 60; n++)
        {
            double f = Math.Pow(lam, 59 - n);
            Complex U(int i) => n + c - i >= 0 && n + c - i < x.Length ? x[n + c - i] : Complex.Zero;
            for (int i = 0; i < taps; i++)
            {
                rhs[i] += f * Complex.Conjugate(U(i)) * a[n];
                for (int j = 0; j < taps; j++)
                    big[i, j] += f * Complex.Conjugate(U(i)) * U(j);
            }
        }
        Complex[] w = Solve(big, rhs);
        for (int i = 0; i < taps; i++)
            Assert.True((r.Taps[i] - w[i]).Magnitude < 1e-9);
    }

    [Fact]
    public void OneTapGainClosedForm()
    {
        Complex[] a = Modulation.QpskMap([0, 1, 1, 0, 1, 1, 0, 0]);
        Complex[] x = [.. a.Select(z => 2 * z)];
        Equalization r = Sync.RlsEqualizer(x, a, 1, 1.0, 0.5);
        for (int n = 0; n < 4; n++)
            Assert.True((r.Symbols[n] - (2 * a[n] * (0.5 + 2 * n) / (0.5 + 4 * n))).Magnitude < 1e-14);
    }

    [Fact]
    public void DecisionsCarryOnAfterAShortTraining()
    {
        var (a, x) = Hard(5, 600);
        Equalization r = Sync.RlsEqualizer(x, a.AsSpan(0, 40), 15, 0.995, center: 2, decision: "qpsk");
        Assert.True(Mse(r.Symbols, a, 300, 600) < 0.05);
        Equalization held = Sync.RlsEqualizer(x, a.AsSpan(0, 40), 15, 0.995, center: 2);
        Assert.All(held.Errors[40..], e => Assert.Equal(Complex.Zero, e));
    }

    [Fact]
    public void Rejects()
    {
        Complex[] x = [1, Complex.ImaginaryOne, -1, -Complex.ImaginaryOne];
        Complex[] t = [1];
        Assert.ThrowsAny<ArgumentException>(() => Sync.RlsEqualizer(x, t, 3, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.RlsEqualizer(x, t, 3, 1.5));
        Assert.ThrowsAny<ArgumentException>(() => Sync.RlsEqualizer(x, t, 3, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Sync.RlsEqualizer(x, t, 3, 0.99, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.RlsEqualizer(x, t, 3, 0.99, double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Sync.RlsEqualizer(x, t, 3, 0.99, decision: "bpsk"));
        Assert.ThrowsAny<ArgumentException>(() => Sync.RlsEqualizer(x, t, 3, 0.99, initialTaps: [1, 0]));
    }
}
