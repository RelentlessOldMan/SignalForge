using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>PowerFrequencyOffset on 16-QAM and 8-PSK, where the lag-1 fourth-power estimator
/// fails (conventions: Synchronization; ADR 0049).</summary>
public class PowerFrequencyOffsetTests
{
    private const double Rs = 1000;

    private static double Normal(Random rng) =>
        Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());

    /// <summary>Errors of the new estimator and of the lag-1 one over 20 random offsets and phases.</summary>
    private static (double[] New, double[] Old) Errors(bool psk8, int n, double? esN0Db, int power)
    {
        var rng = new Random(5);
        var fresh = new double[20];
        var old = new double[20];
        double limit = Rs / (2 * power);
        for (int t = 0; t < 20; t++)
        {
            byte[] bits = [.. Enumerable.Range(0, (psk8 ? 3 : 4) * n).Select(_ => (byte)rng.Next(2))];
            Complex[] a = psk8 ? Modulation.Psk8Map(bits) : Modulation.Qam16Map(bits);
            double f = (rng.NextDouble() * 1.6 - 0.8) * limit;
            Complex[] z = Channel.FrequencyOffset(a, f, Rs, rng.NextDouble() * 6 - 3);
            if (esN0Db is { } es)
            {
                double sigma = Math.Sqrt(Math.Pow(10, -es / 10) / 2);
                for (int k = 0; k < n; k++)
                    z[k] += new Complex(sigma * Normal(rng), sigma * Normal(rng));
            }
            fresh[t] = Math.Abs(Sync.PowerFrequencyOffset(z, Rs, power) - f);
            old[t] = Math.Abs(Sync.QpskFrequencyOffset(z, Rs) - f);
        }
        return (fresh, old);
    }

    [Fact]
    public void NoiselessQam16WhereLag1Fails()
    {
        var (fresh, old) = Errors(false, 400, null, 4);
        Assert.True(fresh.Max() < 0.1, $"max {fresh.Max()}");
        double rms = Math.Sqrt(old.Average(e => e * e));
        Assert.True(rms > 3, $"lag-1 rms {rms}"); // the reason for this estimator (ADR 0049)
    }

    [Fact]
    public void Qam16ThroughNoise()
    {
        var (fresh, _) = Errors(false, 2000, 14.0, 4); // Eb/N0 8 dB
        Assert.True(fresh.Max() < 0.05, $"max {fresh.Max()}");
    }

    [Fact]
    public void Psk8EighthPower()
    {
        var (fresh, _) = Errors(true, 1000, 16.0, 8);
        Assert.True(fresh.Max() < 0.1, $"max {fresh.Max()}");
    }

    [Fact]
    public void InRange()
    {
        var rng = new Random(2);
        foreach (int p in new[] { 1, 2, 4, 8, 16 })
        {
            for (int t = 0; t < 10; t++)
            {
                Complex[] z = [.. Enumerable.Range(0, 37).Select(_ => new Complex(Normal(rng), Normal(rng)))];
                double f = Sync.PowerFrequencyOffset(z, Rs, p);
                Assert.InRange(f, -Rs / (2 * p) + 1e-12, Rs / (2 * p));
            }
        }
    }

    [Fact]
    public void Rejects()
    {
        Complex[] two = [Complex.One, Complex.ImaginaryOne];
        Assert.ThrowsAny<ArgumentException>(() => Sync.PowerFrequencyOffset(two, Rs, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.PowerFrequencyOffset(two, Rs, 17));
        Assert.ThrowsAny<ArgumentException>(() => Sync.PowerFrequencyOffset(two, double.PositiveInfinity, 4));
        Assert.ThrowsAny<ArgumentException>(() => Sync.PowerFrequencyOffset([Complex.One, new Complex(double.NaN, 0)], Rs, 4));
        Assert.ThrowsAny<ArgumentException>(() => Sync.PowerFrequencyOffset([Complex.One], Rs, 4));
    }
}
