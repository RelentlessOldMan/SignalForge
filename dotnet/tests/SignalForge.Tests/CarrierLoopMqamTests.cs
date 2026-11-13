using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>8-PSK and 16-QAM carrier loops: closed forms and tracking (conventions:
/// Synchronization, Tracking loops).</summary>
public class CarrierLoopMqamTests
{
    private static (byte[] Bits, Complex[] Z, double[] Theta) Rotated(bool psk8, int nsym, double theta0, double omega)
    {
        byte[] bits = Waveforms.Prbs(15, (psk8 ? 3 : 4) * nsym);
        Complex[] a = psk8 ? Modulation.Psk8Map(bits) : Modulation.Qam16Map(bits);
        double[] theta = [.. Enumerable.Range(0, nsym).Select(k => theta0 + omega * k)];
        return (bits, [.. a.Select((s, k) => s * Complex.FromPolarCoordinates(1, theta[k]))], theta);
    }

    private static CarrierRecovery Run(bool psk8, Complex[] z, double kp, double ki, double phase = 0) =>
        psk8 ? Sync.Psk8CarrierTracking(z, kp, ki, phase) : Sync.Qam16CarrierTracking(z, kp, ki, phase);

    [Fact]
    public void Psk8ProportionalLagIsExact()
    {
        const double omega = 0.01, kp = 0.1;
        var (_, z, theta) = Rotated(true, 1000, 0.1, omega);
        CarrierRecovery r = Sync.Psk8CarrierTracking(z, kp, 0);
        // e = sin(θ − φ) for unit symbols, so the step kp·e = ω at the lag
        for (int k = 500; k < 1000; k++)
            Assert.Equal(Math.Asin(omega / kp), theta[k] - r.Phases[k], 1e-9);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void IntegratorRemovesTheLag(bool psk8)
    {
        const double omega = 0.004;
        var (kp, ki) = Sync.PiLoopGains(0.02, 1 / Math.Sqrt(2), 1);
        var (_, z, theta) = Rotated(psk8, 4000, 0.1, omega);
        CarrierRecovery r = Run(psk8, z, kp, ki);
        for (int k = 3000; k < 4000; k++)
        {
            Assert.Equal(0, theta[k] - r.Phases[k], 1e-8);
            if (k > 3000)
                Assert.Equal(omega, r.Phases[k] - r.Phases[k - 1], 1e-8);
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void TracksThroughNoiseWithoutErrors(bool psk8)
    {
        // at Es/N0 22 dB both have a symbol error rate below 1e-7 with perfect phase
        const int nsym = 3000;
        int k = psk8 ? 3 : 4;
        var (bits, z, _) = Rotated(psk8, nsym, 0.15, 0.003);
        Complex[] y = Channel.Awgn(z, 22, 1, 7);
        var (kp, ki) = Sync.PiLoopGains(0.02, 1 / Math.Sqrt(2), 1);
        Complex[] s = Run(psk8, y, kp, ki).Symbols[300..];
        byte[] got = psk8 ? Modulation.Psk8DemapHard(s) : Modulation.Qam16DemapHard(s);
        Assert.Equal(0, Metrics.BitErrors(bits.AsSpan(k * 300), got).Errors);
    }

    [Fact]
    public void Psk8LocksToAMultipleOfPiOver4()
    {
        var (_, z, _) = Rotated(true, 400, Math.PI / 4 + 0.05, 0);
        Assert.Equal(0.05, Sync.Psk8CarrierTracking(z, 0.1, 0).Phases[^1], 1e-9);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void BadArgumentsThrow(bool psk8)
    {
        Complex[] ok = [1, Complex.ImaginaryOne];
        Assert.ThrowsAny<ArgumentException>(() => Run(psk8, ok, -0.1, 0.01));
        Assert.ThrowsAny<ArgumentException>(() => Run(psk8, ok, 0.1, double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Run(psk8, ok, 0.1, 0.01, double.PositiveInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Run(psk8, [1, new Complex(double.NaN, 0)], 0.1, 0.01));
    }
}
