using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Gardner timing recovery against its definition and the linear loop model (conventions:
/// Synchronization, Tracking loops).</summary>
public class TimingLoopTests
{
    private const int Sps = 4;

    private static (byte[] Bits, Complex[] Tx, double[] H) Shaped(int nsym)
    {
        byte[] bits = Waveforms.Prbs(15, 2 * nsym);
        double[] h = Dsp.RrcTaps(0.35, Sps, 10);
        Complex[] tx = [.. Dsp.PulseShape(Modulation.QpskMap(bits), h, Sps), .. new Complex[64]];
        return (bits, tx, h);
    }

    // QPSK through a raised-cosine pulse (roll-off 0.5) written out analytically, symbol k peaking at
    // first + k·Sps·(1 + drift): a transmitter whose clock runs slow by drift.
    private static Complex[] RaisedCosineBurst(int nsym, double drift, double first)
    {
        var rng = new Random(2);
        var y = new Complex[(int)(first + nsym * Sps * (1 + drift)) + 48];
        for (int k = 0; k < nsym; k++)
        {
            var a = new Complex(rng.Next(2) * 2 - 1, rng.Next(2) * 2 - 1) / Math.Sqrt(2);
            double centre = first + k * Sps * (1 + drift);
            for (int n = Math.Max(0, (int)(centre - 48)); n < Math.Min(y.Length, (int)(centre + 49)); n++)
            {
                double x = (n - centre) / Sps;
                if (Math.Abs(x) >= 12)
                    continue;
                double p = Math.Abs(Math.Abs(x) - 1) < 1e-12 ? Math.PI / 4 * Sinc(1)
                    : Sinc(x) * Math.Cos(Math.PI * 0.5 * x) / (1 - x * x);
                y[n] += a * p;
            }
        }
        return y;
    }

    private static double Sinc(double x) => x == 0 ? 1 : Math.Sin(Math.PI * x) / (Math.PI * x);

    private static double MeanError(Complex[] y, double start, int nsym) =>
        Sync.GardnerTiming(y, Sps, 0, 0, start).Errors[1..nsym].Average();

    // The S-curve's slope at lock, from the open loop a tenth of a sample either side.
    private static double DetectorGain(Complex[] y, double first, int nsym) =>
        (MeanError(y, first + 0.1, nsym) - MeanError(y, first - 0.1, nsym)) / 0.2;

    [Fact]
    public void OpenLoopReadsLikeFractionalDelay()
    {
        var (_, tx, h) = Shaped(200);
        Complex[] y = Dsp.Convolve(tx, h);
        TimingRecovery r = Sync.GardnerTiming(y, Sps, 0, 0, start: 1.25);
        Complex[] want = Channel.FractionalDelay(y, -1.25, 8);
        for (int k = 0; k < r.Symbols.Length; k++)
        {
            Assert.True(Complex.Abs(r.Symbols[k] - want[k * Sps]) < 1e-14, $"symbol {k}");
            Assert.Equal(1.25 + Sps * k, r.Positions[k]);
        }
        Assert.Equal(0, r.Errors[0]);
    }

    [Theory]
    [InlineData(0.1)]
    [InlineData(0.3)]
    [InlineData(0.6)]
    public void SCurveIsOddAndPositiveLate(double eps)
    {
        var (_, tx, h) = Shaped(1500);
        Complex[] y = Dsp.Convolve(tx, h);
        double first = h.Length - 1;
        double late = MeanError(y, first + eps, 1400), early = MeanError(y, first - eps, 1400);
        Assert.True(late > 0 && early < 0, $"{late} {early}");
        Assert.True(Math.Abs(late + early) < 0.05 * late);
    }

    [Fact]
    public void LocksToAFractionalOffsetInNoise()
    {
        const int nsym = 6000;
        var (bits, tx, h) = Shaped(nsym);
        double first = h.Length - 1;
        var (kp, ki) = Sync.PiLoopGains(0.005, 1 / Math.Sqrt(2), DetectorGain(Dsp.Convolve(tx, h), first, 1500));
        double esN0Db = 2.0 + 10 * Math.Log10(2);
        Complex[] rx = Dsp.Convolve(Channel.Awgn(Channel.FractionalDelay(tx, 2.3), esN0Db, Sps, seed: 6, signalPower: 1.0 / Sps), h);
        TimingRecovery r = Sync.GardnerTiming(rx, Sps, kp, ki, start: first + 2); // starts 0.3 samples early
        double[] err = [.. r.Positions.Select((p, k) => p - (first + 2.3 + Sps * k))];
        Assert.Equal(-0.3, err[0], 1e-12);
        // noise-free the loop sits within 0.01 samples; in noise it jitters by about 0.15 rms and
        // wanders slowly (about 56 independent stretches here), so the mean has a spread of about 0.02
        double[] locked = err[400..nsym];
        Assert.True(Math.Abs(locked.Average()) < 0.06, $"mean {locked.Average()}");
        Assert.True(Math.Sqrt(locked.Average(e => e * e)) < 0.25);
        double ber = Metrics.BitErrors(bits.AsSpan(800, 2 * nsym - 800), Modulation.QpskDemapHard(r.Symbols.AsSpan(400, nsym - 400))).Rate;
        double theory = Metrics.QpskBerTheory(2.0);
        // 11 200 bits, about 420 errors: 3 sigma is about 15 %; the loop's jitter costs a little
        Assert.True(Math.Abs(ber - theory) / theory < 0.2, $"ber {ber} vs theory {theory}");
    }

    [Fact]
    public void DriftLagFollowsTheLinearModel()
    {
        const int nsym = 1500;
        const double drift = 1e-3, first = 48;
        double kd = DetectorGain(RaisedCosineBurst(nsym, 0, first), first, nsym - 10);
        Complex[] y = RaisedCosineBurst(nsym, drift, first);
        var (kp, ki) = Sync.PiLoopGains(0.02, 1 / Math.Sqrt(2), kd);
        double Lag(double[] positions) =>
            Enumerable.Range(300, nsym - 310).Average(k => positions[k] - (first + Sps * (1 + drift) * k));
        double lag = Lag(Sync.GardnerTiming(y, Sps, kp, 0, first).Positions);
        double model = -Sps * drift / (kp * kd);
        Assert.True(Math.Abs(lag / model - 1) < 0.25, $"lag {lag} vs model {model}");
        Assert.True(Math.Abs(Lag(Sync.GardnerTiming(y, Sps, kp, ki, first).Positions)) < 0.01);
    }

    [Fact]
    public void PiLoopGainsByHand()
    {
        var (kp, ki) = Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), 1);
        double theta = 0.01 / (1 / Math.Sqrt(2) + Math.Sqrt(2) / 4);
        double d = 1 + Math.Sqrt(2) * theta + theta * theta;
        Assert.Equal(2 * Math.Sqrt(2) * theta / d, kp, 1e-15);
        Assert.Equal(4 * theta * theta / d, ki, 1e-17);
        Assert.Equal(kp / 2, Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), 2).Kp, 1e-17);
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Complex[] one = [1];
        Assert.ThrowsAny<ArgumentException>(() => Sync.GardnerTiming(one, 1, 0.1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.GardnerTiming(one, 2, double.PositiveInfinity, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.GardnerTiming(one, 2, 0.1, -1e-3));
        Assert.ThrowsAny<ArgumentException>(() => Sync.GardnerTiming(one, 2, 0.1, 0, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Sync.GardnerTiming([double.NaN], 2, 0.1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.GardnerTiming(one, 2, 0.1, 0, 0, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.PiLoopGains(0.01, double.PositiveInfinity, 1));
        Assert.ThrowsAny<ArgumentException>(() => Sync.PiLoopGains(0.01, 1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.PiLoopGains(double.NaN, 1, 1));
    }
}
