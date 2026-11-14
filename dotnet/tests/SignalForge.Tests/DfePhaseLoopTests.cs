using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>The phase loop inside the decision-feedback equalizer (conventions: Synchronization,
/// Decision-feedback equalizer; ADR 0073).</summary>
public sealed class DfePhaseLoopTests
{
    private static readonly Complex[] H = [1, new(0.5, -0.25), new(-0.2, 0.15), 0.1];

    private static double Gauss(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    private static (Complex[] A, Complex[] X) Turning(int seed, int n, double rate, double sigma = 0)
    {
        var rng = new Random(seed);
        var bits = new byte[2 * n];
        for (int i = 0; i < bits.Length; i++)
            bits[i] = (byte)rng.Next(2);
        Complex[] a = Modulation.QpskMap(bits);
        var x = new Complex[n];
        for (int k = 0; k < n; k++)
        {
            Complex s = Complex.Zero;
            for (int j = 0; j < H.Length; j++)
                if (k - j >= 0)
                    s += H[j] * a[k - j];
            x[k] = s * Complex.FromPolarCoordinates(1, rate * k) + sigma * new Complex(Gauss(rng), Gauss(rng));
        }
        return (a, x);
    }

    private static double Mse(Complex[] y, Complex[] a, int from)
    {
        double e = 0;
        for (int k = from; k < a.Length; k++)
            e += Math.Pow((y[k] - a[k]).Magnitude, 2);
        return e / (a.Length - from);
    }

    [Fact]
    public void ZeroGainsAreNoLoopExactly()
    {
        var (a, x) = Turning(1, 300, 0.01);
        DfeEqualization plain = Sync.DfeEqualizer(x, a.AsSpan(0, 40), 5, 3, 0.1, decision: "qpsk");
        DfeEqualization zero = Sync.DfeEqualizer(x, a.AsSpan(0, 40), 5, 3, 0.1, decision: "qpsk", phaseLoopGains: (0, 0));
        Assert.Equal(plain.Symbols, zero.Symbols);
        Assert.Equal(plain.Taps, zero.Taps);
        Assert.Equal(plain.FeedbackTaps, zero.FeedbackTaps);
    }

    [Fact]
    public void FollowsAFrequencyTheTapsCannot()
    {
        var (a, x) = Turning(2, 3000, 0.01, 0.05);
        DfeEqualization plain = Sync.DfeEqualizer(x, a.AsSpan(0, 100), 5, 3, 0.1, decision: "qpsk");
        DfeEqualization loop = Sync.DfeEqualizer(x, a.AsSpan(0, 100), 5, 3, 0.1, decision: "qpsk", phaseLoopGains: (0.05, 0.001));
        Assert.True(Mse(loop.Symbols, a, 2000) < 0.02);
        Assert.True(Mse(plain.Symbols, a, 2000) > 0.1);
        Assert.True((loop.Taps[2] - 1).Magnitude < 0.2);
    }

    [Fact]
    public void ConstantPhaseIsTakenOutByTheLoopNotTheTaps()
    {
        var (a, x) = Turning(3, 2000, 0);
        for (int k = 0; k < x.Length; k++)
            x[k] *= Complex.FromPolarCoordinates(1, 0.6);
        DfeEqualization plain = Sync.DfeEqualizer(x, a, 5, 3, 0.1);
        DfeEqualization loop = Sync.DfeEqualizer(x, a, 5, 3, 0.1, phaseLoopGains: (0.05, 0.001));
        Assert.True(Mse(plain.Symbols, a, 1500) < 2e-3);
        Assert.True(Mse(loop.Symbols, a, 1500) < 2e-3);
        Assert.True(Math.Abs(plain.Taps[2].Phase + 0.6) < 0.05);
        Assert.True(Math.Abs(loop.Taps[2].Phase) < 0.05);
    }

    [Fact]
    public void Rejects()
    {
        Complex[] x = [1, 1, 1, 1];
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(x, x, 3, 1, 0.5, phaseLoopGains: (0.1, -0.01)));
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(x, x, 3, 1, 0.5, phaseLoopGains: (double.NaN, 0)));
    }

    private static readonly int[] Delays = [0, 4];
    private static readonly double[][] Gains = [[1, 0], [0.9, 0]];

    private static QpskLinkConfig Short(string modulation = "qpsk", double eb = 8) => new()
    {
        Modulation = modulation,
        NumSymbols = 6000,
        PreambleSymbols = 100,
        EbN0Db = eb,
        FrequencyOffsetHz = 5,
        EqualizerTaps = 11,
        EqualizerFeedback = 2,
        EqualizerStart = "least_squares",
        EqualizerLoopGains = [0.02, 0.0001],
        Seed = 80,
        MultipathDelays = Delays,
        MultipathGains = Gains,
    };

    [Theory]
    [InlineData("qpsk", 8.0)]
    [InlineData("qam16", 14.0)]
    [InlineData("psk8", 12.0)]
    public void LinkShortPreambleDecodesWithTheLoop(string modulation, double eb) =>
        Assert.True(Link.QpskLink(Short(modulation, eb)).BitErrors.Rate < 0.003);

    [Fact]
    public void LinkNoiselessShortPreambleNeedsTheLoop()
    {
        // no noise, so the same in every language: the frequency is about 0.1 Hz off
        QpskLinkConfig c = Short("qam16") with { EbN0Db = null };
        Assert.Equal(0, Link.QpskLink(c).BitErrors.Errors);
        Assert.True(Link.QpskLink(c with { EqualizerLoopGains = null }).BitErrors.Rate > 0.1);
    }

    [Fact]
    public void LinkRejects()
    {
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(Short() with { EqualizerLoopGains = [0.1, -1] }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(Short() with { EqualizerLoopGains = [0.1] }));
        Assert.ThrowsAny<ArgumentException>(() => Link.QpskLink(Short() with
        {
            EqualizerTaps = null,
            EqualizerFeedback = 0,
            EqualizerStart = "impulse",
            MultipathDelays = null,
            MultipathGains = null,
        }));
    }
}
