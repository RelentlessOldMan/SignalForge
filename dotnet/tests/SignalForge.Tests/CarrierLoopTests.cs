using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Decision-directed QPSK carrier tracking against its definition and the loop model
/// (conventions: Synchronization, Tracking loops).</summary>
public class CarrierLoopTests
{
    private const int Sps = 4;

    private static (Complex[] Z, double[] Theta) Rotated(int nsym, double theta0, double omega)
    {
        Complex[] points = Modulation.QpskMap(Waveforms.Prbs(15, 2 * nsym));
        double[] theta = [.. Enumerable.Range(0, nsym).Select(k => theta0 + omega * k)];
        return ([.. points.Select((p, k) => p * Complex.FromPolarCoordinates(1, theta[k]))], theta);
    }

    [Fact]
    public void ProportionalLagIsExact()
    {
        const double omega = 0.01, kp = 0.1;
        var (z, theta) = Rotated(1000, 0.4, omega);
        CarrierRecovery r = Sync.QpskCarrierTracking(z, kp, 0);
        double want = Math.Asin(omega / (Math.Sqrt(2) * kp));
        for (int k = 500; k < z.Length; k++)
            Assert.True(Math.Abs(theta[k] - r.Phases[k] - want) < 1e-9, $"k {k}");
    }

    [Fact]
    public void IntegratorRemovesTheLag()
    {
        const double omega = 0.01;
        var (kp, ki) = Sync.PiLoopGains(0.02, 1 / Math.Sqrt(2), Math.Sqrt(2));
        var (z, theta) = Rotated(3000, 0.4, omega);
        CarrierRecovery r = Sync.QpskCarrierTracking(z, kp, ki);
        for (int k = 2000; k < z.Length - 1; k++)
        {
            Assert.True(Math.Abs(theta[k] - r.Phases[k]) < 1e-9, $"k {k}");
            Assert.True(Math.Abs(r.Phases[k + 1] - r.Phases[k] - omega) < 1e-11);
        }
    }

    [Fact]
    public void LocksWithAStartPhaseAndReportsIt()
    {
        var (z, _) = Rotated(50, 0.2, 0);
        CarrierRecovery r = Sync.QpskCarrierTracking(z, 0.3, 0, 0.2);
        for (int k = 0; k < z.Length; k++)
        {
            Assert.True(Math.Abs(r.Errors[k]) < 1e-14);
            Assert.True(Math.Abs(r.Phases[k] - 0.2) < 1e-14);
            Assert.True(Complex.Abs(r.Symbols[k] - z[k] * Complex.FromPolarCoordinates(1, -0.2)) < 1e-15);
        }
    }

    [Fact]
    public void FullLinkAfterTimingRecovery()
    {
        const int nsym = 8000;
        const double offset = 1e-4; // carrier offset in cycles per sample
        byte[] bits = Waveforms.Prbs(15, 2 * nsym);
        double[] h = Dsp.RrcTaps(0.35, Sps, 10);
        Complex[] tx = [.. Dsp.PulseShape(Modulation.QpskMap(bits), h, Sps), .. new Complex[64]];
        double first = h.Length - 1;
        Complex[] clean = Dsp.Convolve(tx, h);
        double late = Sync.GardnerTiming(clean, Sps, 0, 0, first + 0.1).Errors[1..1500].Average();
        double early = Sync.GardnerTiming(clean, Sps, 0, 0, first - 0.1).Errors[1..1500].Average();
        var (tkp, tki) = Sync.PiLoopGains(0.005, 1 / Math.Sqrt(2), (late - early) / 0.2);
        Complex[] moved = Channel.FrequencyOffset(Channel.FractionalDelay(tx, 2.3), offset, 1.0, 0.3);
        double esN0Db = 4.0 + 10 * Math.Log10(2);
        Complex[] rx = Dsp.Convolve(Channel.Awgn(moved, esN0Db, Sps, seed: 4, signalPower: 1.0 / Sps), h);
        TimingRecovery timed = Sync.GardnerTiming(rx, Sps, tkp, tki, first + 2);
        var (ckp, cki) = Sync.PiLoopGains(0.01, 1 / Math.Sqrt(2), Math.Sqrt(2));
        CarrierRecovery r = Sync.QpskCarrierTracking(timed.Symbols.AsSpan(0, nsym), ckp, cki);
        // the integrator settles on the offset per symbol: least-squares slope of the phase
        double mk = (1000 + nsym - 1) / 2.0, mp = r.Phases[1000..].Average();
        double num = 0, den = 0;
        for (int k = 1000; k < nsym; k++)
        {
            num += (k - mk) * (r.Phases[k] - mp);
            den += (k - mk) * (k - mk);
        }
        double want = 2 * Math.PI * offset * Sps;
        Assert.True(Math.Abs(num / den / want - 1) < 0.05, $"slope {num / den} vs {want}");
        double ber = Metrics.BitErrors(bits.AsSpan(2000), Modulation.QpskDemapHard(r.Symbols.AsSpan(1000))).Rate;
        double theory = Metrics.QpskBerTheory(4.0);
        // 14 000 bits, about 175 errors: 3 sigma is about 23 %; both loops' jitter costs a little
        Assert.True(Math.Abs(ber - theory) / theory < 0.3, $"ber {ber} vs theory {theory}");
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Complex[] one = [1];
        Assert.ThrowsAny<ArgumentException>(() => Sync.QpskCarrierTracking(one, -0.1, 0));
        Assert.ThrowsAny<ArgumentException>(() => Sync.QpskCarrierTracking(one, 0.1, double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Sync.QpskCarrierTracking(one, 0.1, 0, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Sync.QpskCarrierTracking([new Complex(1, double.PositiveInfinity)], 0.1, 0));
    }
}
