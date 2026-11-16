using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Single-tone frequency by Kay's estimator (conventions: Single-tone frequency (Kay);
/// ADR 0123).</summary>
public class KayFrequencyTests
{
    private static double Gauss(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    private static Complex[] Tone(int n, double f, double amp, double phase) =>
        [.. Enumerable.Range(0, n).Select(k => amp * Complex.Exp(new Complex(0, 2 * Math.PI * f * k + phase)))];

    [Theory]
    [InlineData(-0.43)]
    [InlineData(-0.2)]
    [InlineData(-0.01)]
    [InlineData(0.0)]
    [InlineData(0.001)]
    [InlineData(0.17)]
    [InlineData(0.3333)]
    [InlineData(0.49)]
    public void NoiselessTonesAreExact(double f) =>
        Assert.Equal(f, Measurements.KayFrequency(Tone(40, f, 2.5, 0.7), 1.0), 1e-13);

    [Theory]
    [InlineData(1e-6, 0.0)]
    [InlineData(1.0, 2.0)]
    [InlineData(1e6, -3.0)]
    public void AmplitudeAndPhaseChangeNothing(double amp, double phase) =>
        Assert.Equal(1.23, Measurements.KayFrequency(Tone(25, 0.0123, amp, phase), 100.0), 1e-11);

    [Fact]
    public void VarianceIsNearTheCrlbAtHighSnr()
    {
        const int N = 24, Trials = 4000;
        const double Snr = 1000;
        double sigma = Math.Sqrt(1 / Snr / 2);
        var rng = new Random(123);
        Complex[] tone = Tone(N, 0.1, 1, 0);
        var est = new double[Trials];
        var x = new Complex[N];
        for (int t = 0; t < Trials; t++)
        {
            for (int i = 0; i < N; i++)
                x[i] = tone[i] + sigma * new Complex(Gauss(rng), Gauss(rng));
            est[t] = Measurements.KayFrequency(x, 1.0);
        }
        double crlb = 6 / (Math.Pow(2 * Math.PI, 2) * Snr * N * ((double)N * N - 1));
        double mean = est.Average(), variance = est.Sum(v => (v - mean) * (v - mean)) / Trials;
        Assert.Equal(0.1, mean, 5 * Math.Sqrt(crlb / Trials) + 1e-12);
        Assert.Equal(1.0, variance / crlb, 0.15);
    }

    [Fact]
    public void ZeroSampleIsRejected() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KayFrequency([Complex.One, Complex.Zero], 1.0));
}
