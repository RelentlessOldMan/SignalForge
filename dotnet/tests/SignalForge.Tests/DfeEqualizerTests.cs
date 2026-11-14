using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>The decision-feedback equalizer (conventions: Synchronization, Decision-feedback
/// equalizer; ADR 0069).</summary>
public sealed class DfeEqualizerTests
{
    private const double H1 = 0.95; // the channel 1 + 0.95 z^-1 has a notch 26 dB deep at half the symbol rate
    private const double N0 = 0.01;

    private static (Complex[] A, Complex[] X) DeepNull(int seed, int n = 20000)
    {
        var rng = new Random(seed);
        var bits = new byte[2 * n];
        for (int i = 0; i < bits.Length; i++)
            bits[i] = (byte)rng.Next(2);
        Complex[] a = Modulation.QpskMap(bits);
        var x = new Complex[n];
        double s = Math.Sqrt(N0 / 2);
        for (int i = 0; i < n; i++)
            x[i] = a[i] + (i > 0 ? H1 * a[i - 1] : Complex.Zero) + s * new Complex(Gauss(rng), Gauss(rng));
        return (a, x);
    }

    private static double Gauss(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    // The MMSE linear and decision-feedback equalizers' MSE for 1 + h z^-1 at N0, from the folded
    // spectrum: with A = 1 + h^2 + N0 and B = 2h, N0/sqrt(A^2 - B^2) and 2 N0/(A + sqrt(A^2 - B^2)).
    private static (double Le, double Dfe) Bounds()
    {
        double a = 1 + H1 * H1 + N0, b = 2 * H1, r = Math.Sqrt(a * a - b * b);
        return (N0 / r, 2 * N0 / (a + r));
    }

    private static double Mse(Complex[] y, Complex[] a, int from)
    {
        double s = 0;
        for (int i = from; i < a.Length; i++)
            s += (y[i] - a[i]).Magnitude * (y[i] - a[i]).Magnitude;
        return s / (a.Length - from);
    }

    [Fact]
    public void NoFeedbackIsTheLmsEqualizerExactly()
    {
        var (a, x) = DeepNull(3, 500);
        var lms = Sync.LmsEqualizer(x, a.AsSpan(0, 100), 7, 0.3, 1, 2, "qpsk");
        var dfe = Sync.DfeEqualizer(x, a.AsSpan(0, 100), 7, 0, 0.3, 1, 2, "qpsk");
        Assert.Equal(lms.Symbols, dfe.Symbols);
        Assert.Equal(lms.Errors, dfe.Errors);
        Assert.Equal(lms.Taps, dfe.Taps);
        Assert.Empty(dfe.FeedbackTaps);
    }

    [Fact]
    public void FeedbackBeatsAnyLinearEqualizerOnADeepNull()
    {
        var (a, x) = DeepNull(1);
        var (le, dfeBound) = Bounds();
        var lms = Sync.LmsEqualizer(x, a.AsSpan(0, 2000), 21, 0.02, 1, 0, "qpsk");
        var dfe = Sync.DfeEqualizer(x, a.AsSpan(0, 2000), 3, 2, 0.02, 1, 0, "qpsk");
        Assert.True(Mse(lms.Symbols, a, 10000) > 0.95 * le); // no linear filter does better than the MMSE one
        // the MMSE-DFE bound, with a test allowance for misadjustment and a finite forward filter
        Assert.InRange(Mse(dfe.Symbols, a, 10000), 0.95 * dfeBound, 1.3 * dfeBound);
    }

    [Fact]
    public void APosterioriErrorIsZeroAtStepOne()
    {
        // with step 1 the updated taps give the reference exactly on the regressor they were updated
        // on: the last output's forward samples and the references before it
        var (a, x) = DeepNull(5, 50);
        foreach (int k in new[] { 1, 2, 5, 30 })
        {
            var r = Sync.DfeEqualizer(x.AsSpan(0, k), a.AsSpan(0, k), 4, 3, 1.0, 1, 1);
            Complex y = Complex.Zero;
            for (int i = 0; i < 4; i++)
                y += r.Taps[i] * (k - i >= 0 && k - i < k ? x[k - i] : Complex.Zero);
            for (int j = 1; j <= 3; j++)
                y += r.FeedbackTaps[j - 1] * (k - 1 - j >= 0 ? a[k - 1 - j] : Complex.Zero);
            Assert.Equal(0, (y - a[k - 1]).Magnitude, 1e-12);
        }
    }

    [Theory]
    [InlineData(3, -1, 0.5, "qpsk")]
    [InlineData(3, 2, 0.5, null)]
    [InlineData(3, 2, 2.5, "qpsk")]
    [InlineData(0, 2, 0.5, "qpsk")]
    public void Rejects(int taps, int feedback, double step, string? decision)
    {
        Complex[] x = [1, Complex.ImaginaryOne, -1, -Complex.ImaginaryOne];
        Assert.ThrowsAny<ArgumentException>(() => Sync.DfeEqualizer(x, [Complex.One], taps, feedback, step, 1, null, decision));
    }
}
