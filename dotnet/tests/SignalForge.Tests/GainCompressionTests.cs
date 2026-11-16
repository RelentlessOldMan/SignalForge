using Xunit;

namespace SignalForge.Tests;

/// <summary>Gain compression and P1dB from a drive sweep (conventions: Gain compression;
/// ADR 0112).</summary>
public class GainCompressionTests
{
    private static (double[] X, double[] Y) CubicSweep(double a1, double a3, double stepDb)
    {
        double start = -60 + 20 * Math.Log10(Math.Sqrt(Math.Abs(a1 / a3)));
        int n = (int)Math.Round(60 / stepDb) + 1;
        double[] x = [.. Enumerable.Range(0, n).Select(i => start + i * stepDb)];
        double[] y = [.. x.Select(d =>
        {
            double amp = Math.Pow(10, d / 20);
            return 20 * Math.Log10(Math.Abs(a1 * amp + 0.75 * a3 * amp * amp * amp));
        })];
        return (x, y);
    }

    [Theory]
    [InlineData(1.0, -0.1)]
    [InlineData(10.0, -1.0)]
    [InlineData(0.5, -3.0)]
    public void AFineCubicSweepFindsTheTextbookPoint(double a1, double a3)
    {
        // 1 + (3/4)(a3/a1) A^2 = 10^(-1/20)  =>  A^2 = (4/3)(1 - 10^(-1/20)) |a1/a3|
        var (x, y) = CubicSweep(a1, a3, 0.01);
        GainCompression r = Measurements.GainCompression(x, y);
        double a1Db = 10 * Math.Log10(4.0 / 3 * (1 - Math.Pow(10, -1.0 / 20)) * Math.Abs(a1 / a3));
        Assert.Equal(20 * Math.Log10(a1), r.SmallSignalGainDb, 1e-5);
        Assert.Equal(a1Db, r.InputPointDb, 1e-4);
        Assert.Equal(a1Db + 20 * Math.Log10(a1) - 1, r.OutputPointDb, 1e-4);
    }

    [Theory]
    [InlineData(-37.0)]
    [InlineData(120.0)]
    public void ShiftingTheOutputsMovesTheGainNotTheInputPoint(double shift)
    {
        var (x, y) = CubicSweep(10.0, -1.0, 0.5);
        GainCompression r0 = Measurements.GainCompression(x, y);
        GainCompression r = Measurements.GainCompression(x, [.. y.Select(v => v + shift)]);
        Assert.Equal(r0.SmallSignalGainDb + shift, r.SmallSignalGainDb, 1e-9);
        Assert.Equal(r0.InputPointDb, r.InputPointDb, 1e-9);
        Assert.Equal(r0.OutputPointDb + shift, r.OutputPointDb, 1e-9);
    }

    [Fact]
    public void ALinearSweepNeverCompresses()
    {
        double[] x = [.. Enumerable.Range(0, 11).Select(i => -40.0 + 5 * i)];
        GainCompression r = Measurements.GainCompression(x, [.. x.Select(v => v + 12)], 0.1);
        Assert.True(double.IsNaN(r.InputPointDb) && double.IsNaN(r.OutputPointDb));
        Assert.Equal(22.0, r.SaturatedOutputDb);
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GainCompression([0.0, 1.0], [0.0]));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GainCompression([1.0, 0.0], [0.0, 0.0]));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GainCompression([0.0, 1.0], [0.0, 0.0], -1));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GainCompression([0.0, 1.0], [0.0, 0.0], double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GainCompression([0.0, 1.0], [0.0, 0.0], 1, 3));
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GainCompression([0.0, 1.0], [0.0, 0.0], 1, 0));
    }
}
