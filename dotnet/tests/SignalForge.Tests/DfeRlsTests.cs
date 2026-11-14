using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>RLS training for the decision-feedback equalizer and the link (conventions:
/// Synchronization, Decision-feedback equalizer; ADR 0077).</summary>
public sealed class DfeRlsTests
{
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

    [Fact]
    public void ForwardOnlyIsTheRlsEqualizer()
    {
        var (a, x) = Hard(1, 300);
        DfeEqualization d = Sync.DfeEqualizer(x, a.AsSpan(0, 50), 9, 0, 0.5, center: 2, decision: "qpsk", forgetting: 0.99);
        Equalization r = Sync.RlsEqualizer(x, a.AsSpan(0, 50), 9, 0.99, center: 2, decision: "qpsk");
        for (int k = 0; k < 300; k++)
            Assert.True((d.Symbols[k] - r.Symbols[k]).Magnitude < 1e-12);
        for (int i = 0; i < 9; i++)
            Assert.True((d.Taps[i] - r.Taps[i]).Magnitude < 1e-12);
    }

    [Fact]
    public void StepIsNotUsed()
    {
        var (a, x) = Hard(2, 200);
        DfeEqualization p = Sync.DfeEqualizer(x, a.AsSpan(0, 40), 7, 2, 0.0, decision: "qpsk", phaseLoopGains: (0.02, 0), forgetting: 0.995);
        DfeEqualization q = Sync.DfeEqualizer(x, a.AsSpan(0, 40), 7, 2, 1.5, decision: "qpsk", phaseLoopGains: (0.02, 0), forgetting: 0.995);
        Assert.Equal(p.Symbols, q.Symbols);
    }

    [Fact]
    public void TapsAreTheLeastSquaresSolution()
    {
        // training covers every output, so the feedback regressor is the known symbols; the
        // regularized normal equations solved by Gaussian elimination with partial pivoting
        var (a, x) = Hard(3, 60);
        const int taps = 5, m = 2, c = 1, k = taps + m;
        DfeEqualization r = Sync.DfeEqualizer(x, a, taps, m, 0.5, center: c, forgetting: 1.0, delta: 0.01);
        var big = new Complex[k, k];
        var rhs = new Complex[k];
        for (int i = 0; i < k; i++)
            big[i, i] = 0.01;
        rhs[c] = 0.01;
        var z = new Complex[k];
        for (int n = 0; n < 60; n++)
        {
            for (int i = 0; i < taps; i++)
                z[i] = n + c - i >= 0 && n + c - i < x.Length ? x[n + c - i] : Complex.Zero;
            for (int j = 1; j <= m; j++)
                z[taps + j - 1] = n - j >= 0 ? a[n - j] : Complex.Zero;
            for (int i = 0; i < k; i++)
            {
                rhs[i] += Complex.Conjugate(z[i]) * a[n];
                for (int j = 0; j < k; j++)
                    big[i, j] += Complex.Conjugate(z[i]) * z[j];
            }
        }
        for (int col = 0; col < k; col++)
        {
            int piv = col;
            for (int i = col + 1; i < k; i++)
                if (big[i, col].Magnitude > big[piv, col].Magnitude)
                    piv = i;
            for (int j = 0; j < k; j++)
                (big[col, j], big[piv, j]) = (big[piv, j], big[col, j]);
            (rhs[col], rhs[piv]) = (rhs[piv], rhs[col]);
            for (int i = col + 1; i < k; i++)
            {
                Complex f = big[i, col] / big[col, col];
                for (int j = col; j < k; j++)
                    big[i, j] -= f * big[col, j];
                rhs[i] -= f * rhs[col];
            }
        }
        var w = new Complex[k];
        for (int i = k - 1; i >= 0; i--)
        {
            Complex s = rhs[i];
            for (int j = i + 1; j < k; j++)
                s -= big[i, j] * w[j];
            w[i] = s / big[i, i];
        }
        Complex[] got = [.. r.Taps, .. r.FeedbackTaps];
        for (int i = 0; i < k; i++)
            Assert.True((got[i] - w[i]).Magnitude < 1e-9);
    }

    private static QpskLinkConfig Short(string mod, int seed, double? forgetting) => new()
    {
        Modulation = mod,
        NumSymbols = 2000,
        PreambleSymbols = 100,
        EbN0Db = mod == "qam16" ? 14 : 12,
        FrequencyOffsetHz = 5,
        MultipathDelays = [0, 4],
        MultipathGains = [[1.0, 0.0], [0.9, 0.0]],
        EqualizerTaps = 11,
        EqualizerFeedback = 2,
        EqualizerLoopGains = [0.02, 0.0001],
        EqualizerForgetting = forgetting,
        Seed = seed,
    };

    [Theory]
    [InlineData("qam16")]
    [InlineData("psk8")]
    public void LinkShortPreambleFromTheImpulse(string mod)
    {
        // measured in ADR 0077 (Python's noise): LMS from the impulse fails on every seed, RLS at
        // most 0.0027
        double[] rls = [.. Enumerable.Range(80, 4).Select(s => Link.QpskLink(Short(mod, s, 0.999)).BitErrors.Rate)];
        double[] lms = [.. Enumerable.Range(80, 4).Select(s => Link.QpskLink(Short(mod, s, null)).BitErrors.Rate)];
        Assert.True(rls.Max() < 0.005, string.Join(", ", rls));
        Assert.True(lms.Min() > 0.2, string.Join(", ", lms));
    }

    [Fact]
    public void LinkRejects()
    {
        QpskLinkConfig c = Short("qpsk", 80, 0.999);
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { EqualizerForgetting = 0 }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { EqualizerForgetting = 1.5 }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { EqualizerForgetting = double.NaN }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(c with { EqualizerTaps = null, EqualizerFeedback = 0, EqualizerLoopGains = null }));
    }

    [Fact]
    public void Rejects()
    {
        Complex[] x = [1, Complex.ImaginaryOne, -1, -Complex.ImaginaryOne];
        Complex[] t = [1];
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(x, t, 3, 2, 0.5, decision: "qpsk", forgetting: 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(x, t, 3, 2, 0.5, decision: "qpsk", forgetting: 1.5));
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(x, t, 3, 2, 0.5, decision: "qpsk", forgetting: 0.99, delta: 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(x, t, 3, 2, 2.5, decision: "qpsk", forgetting: 0.99));
    }
}
