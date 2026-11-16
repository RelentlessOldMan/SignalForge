using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Temporal centroid and spread (conventions: Temporal centroid; ADR 0147).</summary>
public class TemporalCentroidTests
{
    private static double[] Pulse()
    {
        var rng = new Random(147);
        return [.. Enumerable.Range(0, 64).Select(n => (rng.NextDouble() - 0.5) * Math.Sin(Math.PI * n / 63))];
    }

    [Fact]
    public void DelayShiftsTheCentroidOnly()
    {
        double[] x = Pulse();
        var a = Measurements.TemporalCentroid(x, 1000);
        var b = Measurements.TemporalCentroid([.. new double[10], .. x], 1000);
        Assert.Equal(a.Centroid + 0.01, b.Centroid, 1e-12 * b.Centroid);
        Assert.Equal(a.Spread, b.Spread, 1e-12 * a.Spread);
    }

    [Fact]
    public void ScalingLeavesItUnchanged()
    {
        double[] x = Pulse();
        var a = Measurements.TemporalCentroid(x, 1000);
        var b = Measurements.TemporalCentroid([.. x.Select(v => new Complex(2, -3) * v)], 1000);
        Assert.Equal(a.Centroid, b.Centroid, 1e-12 * a.Centroid);
        Assert.Equal(a.Spread, b.Spread, 1e-12 * a.Spread);
    }
}
