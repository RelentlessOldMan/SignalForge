using Xunit;

namespace SignalForge.Tests;

/// <summary>Tristimulus (conventions: Spectra, Tristimulus; ADR 0142).</summary>
public class TristimulusTests
{
    private static readonly double[] Heights = [5, 3, 2, 1, 0.5, 0.25, 7];
    private static readonly int[] Orders = [1, 2, 3, 4, 5, 9, 0];

    [Fact]
    public void ScalingHeightsLeavesItUnchanged()
    {
        var a = Spectral.Tristimulus(Heights, Orders);
        var b = Spectral.Tristimulus([.. Heights.Select(h => 6 * h)], Orders);
        Assert.Equal(a.First, b.First, 1e-12);
        Assert.Equal(a.Second, b.Second, 1e-12);
        Assert.Equal(a.Third, b.Third, 1e-12);
    }

    [Fact]
    public void SharesSumToOne()
    {
        var a = Spectral.Tristimulus(Heights, Orders);
        Assert.Equal(1.0, a.First + a.Second + a.Third, 1e-15);
    }

    [Fact]
    public void Sawtooth()
    {
        int[] m = [.. Enumerable.Range(1, 10)];
        var got = Spectral.Tristimulus([.. m.Select(k => 1.0 / (k * k))], m);
        double total = m.Sum(k => 1.0 / k);
        Assert.Equal(1 / total, got.First, 1e-12);
        Assert.Equal((1 / 2.0 + 1 / 3.0 + 1 / 4.0) / total, got.Second, 1e-12);
        Assert.Equal(m.Where(k => k >= 5).Sum(k => 1.0 / k) / total, got.Third, 1e-12);
    }
}
