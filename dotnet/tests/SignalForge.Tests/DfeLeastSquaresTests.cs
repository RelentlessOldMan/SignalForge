using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Least-squares equalizer taps and the equalizers' given start (conventions:
/// Synchronization, Least-squares equalizer taps; ADR 0072).</summary>
public sealed class DfeLeastSquaresTests
{
    private static readonly Complex[] H =
        [0.1, 0.9, new(0.3, 0.2), new(-0.1, 0.15), 0.05, new(0.2, -0.1)];

    private static Complex[] Symbols(Random rng, int n, bool qam16)
    {
        var bits = new byte[(qam16 ? 4 : 2) * n];
        for (int i = 0; i < bits.Length; i++)
            bits[i] = (byte)rng.Next(2);
        return qam16 ? Modulation.Qam16Map(bits) : Modulation.QpskMap(bits);
    }

    private static double Gauss(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    private static Complex[] Channel(Complex[] a, Complex[] h, int sps, double sigma, Random rng)
    {
        var x = new Complex[a.Length * sps];
        for (int n = 0; n < x.Length; n++)
        {
            for (int j = 0; j < h.Length; j++)
                if (n - j >= 0 && (n - j) % sps == 0)
                    x[n] += h[j] * a[(n - j) / sps];
            x[n] += sigma * new Complex(Gauss(rng), Gauss(rng));
        }
        return x;
    }

    [Fact]
    public void SatisfiesTheNormalEquations()
    {
        var rng = new Random(3);
        Complex[] a = Symbols(rng, 300, true);
        Complex[] x = Channel(a, H, 2, 0.05, rng);
        const int L = 9, M = 3, T = 200, C = 4;
        DfeTaps r = Sync.DfeLeastSquares(x, a.AsSpan(0, T), L, M, 2);
        // the residual is orthogonal to every regressor
        var res = new Complex[L + M];
        double scale = 0;
        for (int n = 0; n < T; n++)
        {
            var v = new Complex[L + M];
            for (int i = 0; i < L; i++)
                v[i] = 2 * n + C - i is int s && s >= 0 && s < x.Length ? x[s] : Complex.Zero;
            for (int j = 1; j <= M; j++)
                v[L + j - 1] = n - j >= 0 ? a[n - j] : Complex.Zero;
            Complex y = Complex.Zero;
            for (int i = 0; i < L; i++)
                y += r.Taps[i] * v[i];
            for (int j = 0; j < M; j++)
                y += r.FeedbackTaps[j] * v[L + j];
            for (int k = 0; k < L + M; k++)
            {
                res[k] += Complex.Conjugate(v[k]) * (a[n] - y);
                scale += v[k].Magnitude * v[k].Magnitude;
            }
        }
        foreach (Complex z in res)
            Assert.True(z.Magnitude < 1e-11 * scale);
    }

    [Fact]
    public void NoiselessPostCursorChannelIsSolvedExactly()
    {
        Complex[] a = Symbols(new Random(5), 50, false);
        Complex[] h = [new(0.8, -0.3), 0.4, new(0, -0.2)];
        DfeTaps r = Sync.DfeLeastSquares(Channel(a, h, 1, 0, new Random(0)), a, 1, 2);
        Assert.True((r.Taps[0] - 1 / h[0]).Magnitude < 1e-13);
        for (int j = 0; j < 2; j++)
            Assert.True((r.FeedbackTaps[j] + h[j + 1] / h[0]).Magnitude < 1e-13);
    }

    [Fact]
    public void StartIsAlreadyConverged()
    {
        var rng = new Random(7);
        const int N = 400, T = 60;
        Complex[] a = Symbols(rng, N, false);
        Complex[] x = Channel(a, H, 2, 0.03, rng);
        DfeTaps s = Sync.DfeLeastSquares(x, a.AsSpan(0, T), 11, 2, 2);
        Complex[] ls = Sync.DfeEqualizer(x, a.AsSpan(0, T), 11, 2, 0.05, 2, null, "qpsk", s.Taps, s.FeedbackTaps).Symbols;
        Complex[] imp = Sync.DfeEqualizer(x, a.AsSpan(0, T), 11, 2, 0.05, 2, null, "qpsk").Symbols;
        double Mse(Complex[] y)
        {
            double e = 0;
            for (int n = T; n < N; n++)
                e += Math.Pow((y[n] - a[n]).Magnitude, 2);
            return e / (N - T);
        }
        Assert.True(Mse(ls) < 0.01);
        Assert.True(Mse(imp) > 0.01);
    }

    [Fact]
    public void StepZeroKeepsTheGivenStart()
    {
        var x = new Complex[8];
        for (int k = 0; k < 8; k++)
            x[k] = Complex.FromPolarCoordinates(1, k);
        Complex[] w0 = [0.3, new(1, -0.2), new(0, 0.1)];
        Complex[] b0 = [new(0.5, 0.5)];
        Equalization r = Sync.LmsEqualizer(x, x.AsSpan(0, 3), 3, 0, initialTaps: w0);
        DfeEqualization d = Sync.DfeEqualizer(x, x, 3, 1, 0, initialTaps: w0, initialFeedback: b0);
        for (int n = 0; n < 8; n++)
        {
            Complex y = Complex.Zero;
            for (int i = 0; i < 3; i++)
                if (n + 1 - i is int s && s >= 0 && s < 8)
                    y += w0[i] * x[s];
            Assert.True((r.Symbols[n] - y).Magnitude < 1e-15);
            Complex yd = y + (n > 0 ? b0[0] * x[n - 1] : Complex.Zero);
            Assert.True((d.Symbols[n] - yd).Magnitude < 1e-15);
        }
        Assert.Equal(w0, r.Taps);
        Assert.Equal(b0, d.FeedbackTaps);
        Assert.NotSame(w0, r.Taps);
    }

    [Fact]
    public void Rejects()
    {
        Complex[] x = [1, Complex.ImaginaryOne, -1, -Complex.ImaginaryOne, 0.5, new(0, 0.25)];
        Complex[] t = [1, -1, Complex.ImaginaryOne, -Complex.ImaginaryOne, 1];
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeLeastSquares(x, t.AsSpan(0, 3), 3, 1));
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeLeastSquares(new Complex[6], t, 3, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeLeastSquares(x, t, 3, -1));
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeLeastSquares(x, new Complex[7], 3, 1));
        Complex[] ones = [1, 1, 1, 1];
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(ones, ones, 3, 1, 0.5, initialTaps: [1, 1]));
        Assert.ThrowsAny<ArgumentException>(() =>
            Sync.DfeEqualizer(ones, ones, 3, 1, 0.5, initialTaps: [0, double.PositiveInfinity, 0]));
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(ones, ones, 3, 1, 0.5, initialFeedback: [1, 1]));
    }

    private static readonly int[] Delays = [0, 4];
    private static readonly double[][] Gains = [[1, 0], [0.9, 0]];

    private static QpskLinkConfig Link16() => new()
    {
        Modulation = "qam16",
        NumSymbols = 6000,
        PreambleSymbols = 100,
        EbN0Db = 14,
        FrequencyOffsetHz = 5,
        EqualizerTaps = 11,
        EqualizerFeedback = 2,
        EqualizerStart = "least_squares",
        Seed = 80,
        MultipathDelays = Delays,
        MultipathGains = Gains,
    };

    [Fact]
    public void LinkShortPreambleNeedsTheLeastSquaresStart()
    {
        // measured in ADR 0072 (Python, seed 80): 0.0023 against 0.37 from the impulse
        Assert.True(SignalForge.Link.QpskLink(Link16()).BitErrors.Rate < 0.01);
        Assert.True(SignalForge.Link.QpskLink(Link16() with { EqualizerStart = "impulse" }).BitErrors.Rate > 0.1);
    }

    [Fact]
    public void LinkRejects()
    {
        Assert.ThrowsAny<ArgumentException>(() => SignalForge.Link.QpskLink(Link16() with { EqualizerStart = "zeros" }));
        Assert.ThrowsAny<ArgumentException>(() => SignalForge.Link.QpskLink(Link16() with
        {
            EqualizerTaps = null,
            EqualizerFeedback = 0,
            MultipathDelays = null,
            MultipathGains = null,
        }));
        Assert.ThrowsAny<ArgumentException>(() => SignalForge.Link.QpskLink(Link16() with { PreambleSymbols = 12 }));
    }
}
