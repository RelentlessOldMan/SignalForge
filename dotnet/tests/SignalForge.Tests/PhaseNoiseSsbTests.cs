using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Single-sideband phase noise L(f) (conventions: Phase noise measurement; ADR 0108).</summary>
public class PhaseNoiseSsbTests
{
    private const double A0 = 0.35875, A1 = 0.48829, A2 = 0.14128, A3 = 0.01168;

    // ENBW of the periodic 4-term Blackman-Harris window, in bins
    private const double Enbw = (A0 * A0 + (A1 * A1 + A2 * A2 + A3 * A3) / 2) / (A0 * A0);

    private static double LorentzianDb(double f, double linewidth, double fs)
    {
        // Wiener phase noise: autocorrelation rho^|k|, rho = exp(-sigma^2/2), sigma^2 = 2 pi dv/fs
        double rho = Math.Exp(-Math.PI * linewidth / fs);
        double w = 2 * Math.PI * f / fs;
        return 10 * Math.Log10((1 - rho * rho) / (1 - 2 * rho * Math.Cos(w) + rho * rho) / fs);
    }

    [Fact]
    public void WienerPhaseNoiseFollowsTheLorentzian()
    {
        const double fs = 1e4, dv = 10.0;
        var ones = Enumerable.Repeat(Complex.One, 1 << 18).ToArray();
        Complex[] x = Channel.PhaseNoise(ones, dv, fs, seed: 7);
        double[] offsets = [200.0, 500.0, 1000.0, 2000.0];
        PhaseNoise r = Measurements.PhaseNoiseSsb(x, fs, offsets, nperseg: 1024);
        for (int i = 0; i < offsets.Length; i++)
        {
            // L is the sideband density over the carrier group's power; the density itself is S(f)
            double got = r.LDbcHz[i] + 10 * Math.Log10(r.CarrierPower);
            double want = LorentzianDb(offsets[i], dv, fs);
            Assert.True(Math.Abs(got - want) < 0.5, $"{offsets[i]} Hz: {got} vs {want}");
        }
        Assert.True(Math.Abs(r.CarrierFrequency) < 2.0);
        Assert.InRange(r.CarrierPower, 0.5, 1.0); // the group holds the Lorentzian's core, not its tails
    }

    [Fact]
    public void TheTwoSidebandsAreAveraged()
    {
        // carrier 1 plus a line b at +k bins only: L = (b^2/ENBW)/2, 3 dB below one sideband
        const int n = 1024, k = 40;
        const double b = 1e-2;
        Complex[] x = [.. Enumerable.Range(0, n).Select(t => 1 + b * Complex.FromPolarCoordinates(1, 2 * Math.PI * k * t / n))];
        PhaseNoise r = Measurements.PhaseNoiseSsb(x, n, [k]);
        Assert.Equal(10 * Math.Log10(b * b / Enbw / 2), r.LDbcHz[0], 9);
        Assert.Equal(1.0, r.CarrierPower, 12);
    }

    [Fact]
    public void SmallPhaseModulationIsHalfThePhaseSpectrum()
    {
        // L ~ S_phi/2: a phase line m sin(w_m n) has S_phi power m^2/2, L power (m/2)^2 per sideband
        const int n = 1024, km = 50;
        const double m = 1e-3;
        double[] x = [.. Enumerable.Range(0, n).Select(t => Math.Cos(2 * Math.PI * 200 * t / n + m * Math.Sin(2 * Math.PI * km * t / n)))];
        PhaseNoise r = Measurements.PhaseNoiseSsb(x, n, [km]);
        Assert.True(Math.Abs(r.LDbcHz[0] - 10 * Math.Log10(m / 2 * (m / 2) / Enbw)) < 1e-5);
        Assert.Equal(200.0, r.CarrierFrequency, 9);
    }

    [Fact]
    public void ComplexUpperEdgeIsExclusive()
    {
        // the two-sided bins run -fs/2 ... fs/2 - df, so fc + o = fs/2 has no bin of its own
        var x = Enumerable.Repeat(Complex.One, 64).ToArray();
        Measurements.PhaseNoiseSsb(x, 64, [31.0]);
        Assert.Throws<ArgumentException>(() => Measurements.PhaseNoiseSsb(x, 64, [32.0]));
    }

    [Fact]
    public void NanOffsetIsRejected() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PhaseNoiseSsb(Enumerable.Repeat(Complex.One, 64).ToArray(), 64, [double.NaN]));
}
