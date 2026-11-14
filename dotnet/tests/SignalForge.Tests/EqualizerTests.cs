using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>LMS equalizer (conventions: Synchronization, LMS equalizer; ADR 0066).</summary>
public sealed class EqualizerTests
{
    private static readonly Complex[] H = [1, new(0.35, -0.2), new(-0.1, 0.05)];

    private static Complex[] Qpsk(int n, int seed)
    {
        var rng = new Random(seed);
        var bits = new byte[2 * n];
        for (int i = 0; i < bits.Length; i++)
            bits[i] = (byte)rng.Next(2);
        return Modulation.QpskMap(bits);
    }

    // the first x.Length samples of x through the taps h
    private static Complex[] Filter(Complex[] x, Complex[] h)
    {
        var y = new Complex[x.Length];
        for (int n = 0; n < x.Length; n++)
            for (int j = 0; j < h.Length && j <= n; j++)
                y[n] += h[j] * x[n - j];
        return y;
    }

    private static double Mse(Complex[] y, Complex[] a, int from, int to)
    {
        double s = 0;
        for (int i = from; i < to; i++)
            s += Complex.Abs(y[i] - a[i]) * Complex.Abs(y[i] - a[i]);
        return s / (to - from);
    }

    [Fact]
    public void LearnsAMultipathChannel()
    {
        Complex[] a = Qpsk(2000, 0);
        var r = Sync.LmsEqualizer(Filter(a, H), a.AsSpan(0, 300), 11, 0.2, center: 2, decision: "qpsk");
        Assert.Equal((a.Length, a.Length, 11), (r.Symbols.Length, r.Errors.Length, r.Taps.Length));
        Assert.True(Mse(r.Symbols, a, a.Length - 500, a.Length) < 1e-4); // an 11-tap inverse of a minimum-phase channel
        Assert.Equal(Modulation.QpskDemapHard(a.AsSpan(300)), Modulation.QpskDemapHard(r.Symbols.AsSpan(300)));
        // the taps approximate the channel's inverse: equalizer * channel is near a delayed impulse
        var combined = new Complex[r.Taps.Length + H.Length - 1];
        for (int i = 0; i < r.Taps.Length; i++)
            for (int j = 0; j < H.Length; j++)
                combined[i + j] += r.Taps[i] * H[j];
        Assert.True(Complex.Abs(combined[2] - 1) < 0.01);
        Assert.True(combined.Where((_, i) => i != 2).Max(Complex.Abs) < 0.01);
    }

    [Fact]
    public void FractionalSpacingTakesAHalfSampleOffset()
    {
        // two samples per symbol, the symbol energy on the odd samples: a symbol-spaced reader at
        // n*sps would see only zeros; the fractionally spaced taps move the center
        Complex[] a = Qpsk(1500, 1);
        var up = new Complex[2 * a.Length];
        for (int i = 0; i < a.Length; i++)
            up[2 * i + 1] = a[i];
        var r = Sync.LmsEqualizer(Filter(up, [0.5, 1.0, 0.5]), a.AsSpan(0, 400), 8, 0.3, samplesPerSymbol: 2, decision: "qpsk");
        // the last symbol's pulse is cut off by the end of the samples
        Assert.True(Mse(r.Symbols, a, a.Length - 300, a.Length - 1) < 1e-6);
    }

    [Fact]
    public void WithoutDecisionTheTapsHoldAfterTraining()
    {
        Complex[] a = Qpsk(200, 2), x = Filter(a, H);
        var held = Sync.LmsEqualizer(x, a.AsSpan(0, 100), 5, 0.5);
        var trained = Sync.LmsEqualizer(x.AsSpan(0, 100), a.AsSpan(0, 100), 5, 0.5);
        Assert.All(held.Errors.Skip(100), e => Assert.Equal(Complex.Zero, e));
        Assert.Equal(trained.Symbols.Take(98), held.Symbols.Take(98));
    }

    [Theory]
    [InlineData("qpsk", 2)]
    [InlineData("psk8", 3)]
    [InlineData("qam16", 4)]
    [InlineData("qam64", 6)]
    public void DecisionsFollowTheDemappers(string decision, int bps)
    {
        var rng = new Random(3);
        var bits = new byte[bps * 50];
        for (int i = 0; i < bits.Length; i++)
            bits[i] = (byte)rng.Next(2);
        Complex[] a = decision switch
        {
            "qpsk" => Modulation.QpskMap(bits),
            "psk8" => Modulation.Psk8Map(bits),
            "qam16" => Modulation.Qam16Map(bits),
            _ => Modulation.Qam64Map(bits),
        };
        Complex[] y = [.. a.Select(s => s * new Complex(1, 0.01))]; // near the points, so each decides its own
        var r = Sync.LmsEqualizer(y, [], 1, 0, decision: decision);
        for (int i = 0; i < a.Length; i++)
            Assert.True(Complex.Abs(r.Errors[i] - (a[i] - y[i])) < 1e-15);
    }

    [Fact]
    public void InputIsNotChanged()
    {
        Complex[] x = Qpsk(20, 0), before = [.. x];
        Sync.LmsEqualizer(x, x.AsSpan(0, 5), 3, 1, decision: "qpsk");
        Assert.Equal(before, x);
    }
}
