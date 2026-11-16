using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>The phase noise spur finder (conventions: Phase noise spur finder; ADR 0116).</summary>
public class PhaseNoiseSpurFinderTests
{
    private const double Fs = 1.0e6;
    private const int N = 1 << 16;
    private const double SpurAt = 1600 * Fs / N; // coherent: 100 bins of a 4096 segment from the carrier

    private static Complex[] CarrierWithNoise(double linewidth, int seed)
    {
        Complex[] x = [.. Enumerable.Range(0, N).Select(t => Complex.FromPolarCoordinates(1, 2 * Math.PI * 125_000.0 * t / Fs))];
        return Channel.PhaseNoise(x, linewidth, Fs, seed);
    }

    private static Complex[] WithSpur(Complex[] x, double dbc) =>
        [.. x.Select((v, t) => v + Complex.FromPolarCoordinates(Math.Pow(10, dbc / 20), 2 * Math.PI * (125_000.0 + SpurAt) * t / Fs))];

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    public void NoiseAloneHasNoSpurs(int seed)
    {
        PhaseNoiseSpurs r = Measurements.PhaseNoiseSpurs(CarrierWithNoise(20.0, seed), Fs, 3_000.0, 50_000.0, nperseg: 4096);
        Assert.Empty(r.Offsets);
        Assert.Empty(r.LevelsDbc);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    public void ASpurIsFoundAtItsOffsetAndLevel(int seed)
    {
        PhaseNoiseSpurs r = Measurements.PhaseNoiseSpurs(WithSpur(CarrierWithNoise(20.0, seed), -20.0), Fs, 3_000.0, 50_000.0, nperseg: 4096);
        Assert.Single(r.Offsets);
        Assert.Equal(SpurAt, r.Offsets[0], Fs / 4096 / 2); // the bin; the noisy carrier's centroid wanders
        Assert.Equal(-20.0, r.LevelsDbc[0], 0.2);
    }

    [Fact]
    public void FoundOffsetsRemoveTheSpur()
    {
        Complex[] clean = CarrierWithNoise(20.0, 4), dirty = WithSpur(clean, -20.0);
        PhaseNoiseSpurs r = Measurements.PhaseNoiseSpurs(dirty, Fs, 3_000.0, 50_000.0, nperseg: 4096);
        IntegratedPhaseNoise b = Measurements.IntegratedPhaseNoise(clean, Fs, 1_000.0, 50_000.0, nperseg: 4096);
        IntegratedPhaseNoise gone = Measurements.IntegratedPhaseNoise(dirty, Fs, 1_000.0, 50_000.0, nperseg: 4096,
            spurOffsets: [.. r.Offsets.Select(Math.Abs)]);
        Assert.Equal(b.IntegratedDbc, gone.IntegratedDbc, 0.05);
    }

    [Fact]
    public void RealInputFindsBothSides()
    {
        double[] x = [.. Enumerable.Range(0, 1024).Select(t => Math.Cos(2 * Math.PI * 200 * t / 1024 + 0.01 * Math.Sin(2 * Math.PI * 40 * t / 1024)))];
        PhaseNoiseSpurs r = Measurements.PhaseNoiseSpurs(x, 1024.0, 20.0, 60.0);
        Assert.Equal(2, r.Offsets.Length);
        Assert.Equal(-40.0, r.Offsets[0], 1e-9);
        Assert.Equal(40.0, r.Offsets[1], 1e-9);
        foreach (double l in r.LevelsDbc)
            Assert.Equal(20 * Math.Log10(0.01 / 2), l, 1e-3);
    }

    [Theory]
    [InlineData(0.0)]
    [InlineData(-3.0)]
    [InlineData(double.NaN)]
    [InlineData(double.PositiveInfinity)]
    public void BadThresholdThrows(double t)
    {
        Complex[] x = CarrierWithNoise(50.0, 6);
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PhaseNoiseSpurs(x, Fs, 3_000.0, 20_000.0, thresholdDb: t));
    }

    [Theory]
    [InlineData(20_000.0, 3_000.0)]
    [InlineData(0.0, 1_000.0)]
    [InlineData(100.0, 20_000.0)]
    public void BadBandThrows(double lo, double hi)
    {
        Complex[] x = CarrierWithNoise(50.0, 7);
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PhaseNoiseSpurs(x, Fs, lo, hi, nperseg: 4096));
    }
}
