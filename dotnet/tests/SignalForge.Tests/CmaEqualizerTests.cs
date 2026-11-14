using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>The blind constant-modulus equalizer (conventions: Synchronization, Constant-modulus
/// equalizer; ADR 0074).</summary>
public sealed class CmaEqualizerTests
{
    private static readonly Complex[] H = [1, new(0.35, -0.2), new(-0.1, 0.05)];

    private static (Complex[] A, Complex[] X) Channel(int seed, int n, int bitsPerSymbol, double turn)
    {
        var rng = new Random(seed);
        var bits = new byte[bitsPerSymbol * n];
        for (int i = 0; i < bits.Length; i++)
            bits[i] = (byte)rng.Next(2);
        Complex[] a = bitsPerSymbol == 2 ? Modulation.QpskMap(bits) : Modulation.Qam16Map(bits);
        var x = new Complex[n];
        for (int k = 0; k < n; k++)
        {
            Complex s = Complex.Zero;
            for (int j = 0; j < H.Length; j++)
                if (k - j >= 0)
                    s += H[j] * a[k - j];
            x[k] = s * Complex.FromPolarCoordinates(1, turn);
        }
        return (a, x);
    }

    // the blind output keeps the channel's phase: compare after the best single rotation
    private static double RotatedMse(Complex[] y, Complex[] a, int from)
    {
        Complex s = Complex.Zero;
        for (int k = from; k < a.Length; k++)
            s += a[k] * Complex.Conjugate(y[k]);
        Complex turn = Complex.FromPolarCoordinates(1, s.Phase);
        double e = 0;
        for (int k = from; k < a.Length; k++)
            e += Math.Pow((y[k] * turn - a[k]).Magnitude, 2);
        return e / (a.Length - from);
    }

    private static double Mse(Complex[] y, Complex[] a, int from)
    {
        double e = 0;
        for (int k = from; k < a.Length; k++)
            e += Math.Pow((y[k] - a[k]).Magnitude, 2);
        return e / (a.Length - from);
    }

    [Theory]
    [InlineData(2, 1.0, 0.012)]
    [InlineData(4, 1.32, 0.025)]
    public void OpensTheEyeWithNoTraining(int bitsPerSymbol, double modulus, double limit)
    {
        var (a, x) = Channel(2, 3000, bitsPerSymbol, 0.7);
        Equalization r = Sync.CmaEqualizer(x, 7, 0.03, modulus: modulus);
        Assert.True(RotatedMse(r.Symbols, a, 2000) < limit);
        Assert.True(RotatedMse(x, a, 2000) > limit);
    }

    [Fact]
    public void OneTapScalarGain()
    {
        Complex g = 1.7 * new Complex(0.6, -0.8);
        var x = new Complex[20];
        for (int k = 0; k < x.Length; k++)
            x[k] = g * Complex.FromPolarCoordinates(1, Math.PI / 4 * ((2 * k) + 1));
        Equalization r = Sync.CmaEqualizer(x, 1, 0.5);
        Complex w = 1;
        for (int k = 0; k < x.Length; k++)
            w *= 1 + (0.5 * (1 - Math.Pow((w * g).Magnitude, 2)));
        Assert.True((r.Taps[0] - w).Magnitude < 1e-13);
        Assert.True(Math.Abs(r.Taps[0].Magnitude - (1 / 1.7)) < 1e-9);
    }

    [Fact]
    public void ItsTapsStartADecisionDirectedLms()
    {
        var (a, x) = Channel(4, 3000, 2, 0.3);
        Equalization blind = Sync.CmaEqualizer(x, 7, 0.03);
        // the blind output's pi/2 ambiguity is resolved here with the known symbols, as a preamble would
        Complex s = Complex.Zero;
        for (int k = 0; k < a.Length; k++)
            s += a[k] * Complex.Conjugate(blind.Symbols[k]);
        Complex turn = Complex.FromPolarCoordinates(1, Math.PI / 2 * Math.Round(s.Phase / (Math.PI / 2)));
        Complex[] start = [.. blind.Taps.Select(t => t * turn)];
        Equalization r = Sync.LmsEqualizer(x, [], 7, 0.05, decision: "qpsk", initialTaps: start);
        Equalization trained = Sync.LmsEqualizer(x, a, 7, 0.05);
        // as good as training on every symbol: 7 taps leave about 0.007 on this channel either way
        Assert.True(Mse(r.Symbols, a, 2000) < 1.1 * Mse(trained.Symbols, a, 2000));
        Assert.True(Mse(trained.Symbols, a, 2000) < 0.01);
    }

    [Fact]
    public void Rejects()
    {
        Complex[] x = [1, Complex.ImaginaryOne, -1];
        Assert.ThrowsAny<ArgumentException>(() => Sync.CmaEqualizer(x, 3, 0.5, modulus: 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.CmaEqualizer(x, 3, 0.5, modulus: double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Sync.CmaEqualizer(x, 3, 2.5));
        Assert.ThrowsAny<ArgumentException>(() => Sync.CmaEqualizer(x, 3, 0.5, initialTaps: [1, 0]));
    }
}
