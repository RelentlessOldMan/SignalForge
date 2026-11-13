using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Sample clock offset against a tone and the timing loop (conventions: Channel, Sample
/// clock offset).</summary>
public class ClockOffsetTests
{
    [Theory]
    [InlineData(-1e5)]
    [InlineData(-300.0)]
    [InlineData(25.0)]
    [InlineData(2e4)]
    [InlineData(1e5)]
    public void ToneIsReadAtTheNewRate(double ppm)
    {
        double r = 1 + ppm / 1e6;
        Complex[] x = [.. Enumerable.Range(0, 400).Select(n => Complex.FromPolarCoordinates(1, 2 * Math.PI * 0.05 * n))];
        Complex[] y = Channel.ClockOffset(x, ppm);
        Assert.Equal((int)Math.Floor(399 / r) + 1, y.Length);
        for (int n = 0; n < y.Length; n++)
        {
            double t = n * r;
            if (t > 16 && t < 399 - 16) // the default kernel's error floor is about 2e-5 here
                Assert.True(Complex.Abs(y[n] - Complex.FromPolarCoordinates(1, 2 * Math.PI * 0.05 * t)) < 5e-5, $"n {n}");
        }
    }

    [Fact]
    public void ZeroPpmReturnsTheInput()
    {
        Complex[] x = [new(1, 2), new(0, -0.5), 3, new(0.25, -1)];
        Assert.Equal(x, Channel.ClockOffset(x, 0));
        Assert.Empty(Channel.ClockOffset([], 30));
    }

    [Fact]
    public void TimingLoopFollowsTheClock()
    {
        const int sps = 4, nsym = 6000;
        const double ppm = 200;
        byte[] bits = Waveforms.Prbs(15, 2 * nsym);
        double[] h = Dsp.RrcTaps(0.35, sps, 10);
        Complex[] tx = [.. Dsp.PulseShape(Modulation.QpskMap(bits), h, sps), .. new Complex[64]];
        double first = h.Length - 1;
        Complex[] clean = Dsp.Convolve(tx, h);
        double late = Sync.GardnerTiming(clean, sps, 0, 0, first + 0.1).Errors[1..1500].Average();
        double early = Sync.GardnerTiming(clean, sps, 0, 0, first - 0.1).Errors[1..1500].Average();
        var (kp, ki) = Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), (late - early) / 0.2);
        double r = 1 + ppm / 1e6;
        TimingRecovery got = Sync.GardnerTiming(Dsp.Convolve(Channel.ClockOffset(tx, ppm), h), sps, kp, ki, Math.Round(first / r));
        // symbol k peaks at (first + k·sps)/r: 4.8 samples of drift by the end, over a symbol
        double[] err = [.. Enumerable.Range(500, nsym - 500).Select(k => got.Positions[k] - (first + sps * k) / r)];
        // the loop sits about 0.017 samples off even without an offset (the detector's bias on this
        // pulse); following the clock adds little to that, and nothing grows along the burst
        double[] still = Sync.GardnerTiming(clean, sps, kp, ki, first).Positions;
        double bias = Enumerable.Range(500, nsym - 500).Average(k => still[k] - (first + sps * k));
        Assert.True(Math.Abs(err.Average() - bias) < 0.01, $"mean {err.Average()} bias {bias}");
        Assert.True(Math.Abs(err[..2750].Average() - err[2750..].Average()) < 0.01);
        Assert.True(err.Max(Math.Abs) < 0.15);
        Assert.Equal(0, Metrics.BitErrors(bits.AsSpan(1000), Modulation.QpskDemapHard(got.Symbols.AsSpan(500, nsym - 500))).Errors);
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Complex[] one = [1];
        Assert.ThrowsAny<ArgumentException>(() => Channel.ClockOffset(one, 1.5e5));
        Assert.ThrowsAny<ArgumentException>(() => Channel.ClockOffset(one, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Channel.ClockOffset(one, 1, 0));
    }
}
