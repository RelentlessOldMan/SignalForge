using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Integrated phase noise and RMS jitter (conventions: Integrated phase noise; ADR 0109).</summary>
public class IntegratedPhaseNoiseTests
{
    private static double LorentzianBand(double fLo, double fHi, double linewidth, double fs)
    {
        // Wiener phase noise: S(f) = (1/fs)(1 - rho^2)/(1 - 2 rho cos w + rho^2), rho = exp(-pi dv/fs);
        // its integral is (1/pi) arctan(((1 + rho)/(1 - rho)) tan(pi f/fs))
        double rho = Math.Exp(-Math.PI * linewidth / fs), a = (1 + rho) / (1 - rho);
        double Prim(double f) => Math.Atan(a * Math.Tan(Math.PI * f / fs)) / Math.PI;
        return Prim(fHi) - Prim(fLo);
    }

    [Fact]
    public void WienerPhaseNoiseIntegratesToTheLorentzian()
    {
        const double fs = 1e4, dv = 10.0;
        const int seg = 1024;
        double df = fs / seg;
        Complex[] x = Channel.PhaseNoise(Enumerable.Repeat(Complex.One, 1 << 18).ToArray(), dv, fs, seed: 11);
        double lo = 10.5 * df, hi = 200.5 * df; // edges between bins, so the whole bins are the band
        IntegratedPhaseNoise r = Measurements.IntegratedPhaseNoise(x, fs, lo, hi, nperseg: seg);
        double want = 2 * LorentzianBand(lo, hi, dv, fs) / r.CarrierPower; // both sides
        Assert.InRange(r.PhaseRms * r.PhaseRms / want, 0.95, 1.05);
        Assert.True(Math.Abs(r.IntegratedDbc - 10 * Math.Log10(want)) < 0.2);
    }

    [Fact]
    public void SmallSineModulationIsMOverRootTwo()
    {
        // the RMS of m sin(w_m n) is m/sqrt(2); jitter divides by 2 pi f_c
        const int n = 1024, kc = 300, km = 40;
        const double m = 1e-3;
        double[] x = [.. Enumerable.Range(0, n).Select(t => Math.Cos(2 * Math.PI * kc * t / n + m * Math.Sin(2 * Math.PI * km * t / n)))];
        IntegratedPhaseNoise r = Measurements.IntegratedPhaseNoise(x, n, 20.5, 60.5);
        Assert.True(Math.Abs(r.PhaseRms / (m / Math.Sqrt(2)) - 1) < 1e-6);
        Assert.True(Math.Abs(r.JitterRms / (r.PhaseRms / (2 * Math.PI * kc)) - 1) < 1e-12);
        Assert.Equal((20.5, 60.5), (r.FLo, r.FHi));
    }

    [Fact]
    public void AnEmptyBandGivesNoPhaseError()
    {
        // a coherent tone leaves only rounding outside its seven bins
        const int n = 1024;
        double[] x = [.. Enumerable.Range(0, n).Select(t => Math.Cos(2 * Math.PI * 100 * t / n))];
        IntegratedPhaseNoise r = Measurements.IntegratedPhaseNoise(x, n, 10.5, 50.5);
        Assert.True(r.PhaseRms < 1e-6);
        Assert.True(r.IntegratedDbc < -120);
    }

    [Fact]
    public void AZeroCarrierFrequencyHasInfiniteJitter()
    {
        const int n = 64;
        Complex[] x = [.. Enumerable.Range(0, n).Select(t => 1 + 1e-3 * Complex.FromPolarCoordinates(1, 2 * Math.PI * 10 * t / n))];
        // a one-bin group (width 0) makes the centroid exactly the 0 Hz bin, not a rounding residue
        IntegratedPhaseNoise r = Measurements.IntegratedPhaseNoise(x, n, 5.5, 20.5, width: 0);
        Assert.Equal(0.0, r.CarrierFrequency);
        Assert.Equal(double.PositiveInfinity, r.JitterRms);
    }

    [Theory]
    [InlineData(double.NaN, 8.0)]
    [InlineData(8.0, double.NaN)]
    [InlineData(-1.0, 8.0)]
    public void BadBand(double lo, double hi) =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.IntegratedPhaseNoise(Enumerable.Repeat(Complex.One, 64).ToArray(), 64, lo, hi));
}
