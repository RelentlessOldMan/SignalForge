using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Phase noise with spurs removed (conventions: Phase noise with spurs removed; ADR 0115).</summary>
public class PhaseNoiseSpursTests
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
    public void RemovalRecoversTheIntegralWithoutTheSpur(int seed)
    {
        Complex[] clean = CarrierWithNoise(20.0, seed), dirty = WithSpur(clean, -20.0);
        IntegratedPhaseNoise b = Measurements.IntegratedPhaseNoise(clean, Fs, 1_000.0, 50_000.0, nperseg: 4096);
        IntegratedPhaseNoise kept = Measurements.IntegratedPhaseNoise(dirty, Fs, 1_000.0, 50_000.0, nperseg: 4096);
        IntegratedPhaseNoise gone = Measurements.IntegratedPhaseNoise(dirty, Fs, 1_000.0, 50_000.0, nperseg: 4096, spurOffsets: [SpurAt]);
        double added = Math.Pow(10, kept.IntegratedDbc / 10) - Math.Pow(10, b.IntegratedDbc / 10);
        Assert.Equal(1e-2, added, 5e-4);
        Assert.Equal(b.IntegratedDbc, gone.IntegratedDbc, 0.05);
    }

    [Fact]
    public void LAtTheSpurReadsTheNoiseAroundIt()
    {
        Complex[] clean = CarrierWithNoise(20.0, 3), dirty = WithSpur(clean, -20.0);
        double b = Measurements.PhaseNoiseSsb(clean, Fs, [SpurAt], nperseg: 4096).LDbcHz[0];
        double kept = Measurements.PhaseNoiseSsb(dirty, Fs, [SpurAt], nperseg: 4096).LDbcHz[0];
        double gone = Measurements.PhaseNoiseSsb(dirty, Fs, [SpurAt], nperseg: 4096, spurOffsets: [SpurAt]).LDbcHz[0];
        Assert.True(kept > b + 15);
        Assert.Equal(b, gone, 1.5);
    }

    [Fact]
    public void NoSpursChangesNothing()
    {
        Complex[] x = CarrierWithNoise(50.0, 4);
        IntegratedPhaseNoise a = Measurements.IntegratedPhaseNoise(x, Fs, 3_000.0, 20_000.0, nperseg: 2048);
        IntegratedPhaseNoise e = Measurements.IntegratedPhaseNoise(x, Fs, 3_000.0, 20_000.0, nperseg: 2048, spurOffsets: []);
        Assert.Equal(a.IntegratedDbc, e.IntegratedDbc);
        IntegratedPhaseNoise far = Measurements.IntegratedPhaseNoise(x, Fs, 3_000.0, 20_000.0, nperseg: 2048, spurOffsets: [100_000.0]);
        Assert.Equal(a.IntegratedDbc, far.IntegratedDbc);
    }

    [Theory]
    [InlineData(0.0)]
    [InlineData(-5.0)]
    [InlineData(double.NaN)]
    [InlineData(double.PositiveInfinity)]
    public void BadSpurOffsetsThrow(double o)
    {
        Complex[] x = CarrierWithNoise(50.0, 6);
        Assert.ThrowsAny<ArgumentException>(() => Measurements.IntegratedPhaseNoise(x, Fs, 3_000.0, 20_000.0, spurOffsets: [o]));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PhaseNoiseSsb(x, Fs, [5_000.0], spurOffsets: [o]));
    }
}
