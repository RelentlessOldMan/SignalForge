using Xunit;

namespace SignalForge.Tests;

/// <summary>Centre time and the early decay time (conventions: Centre time; ADR 0173).</summary>
public class CentreTimeTests
{
    private static double[] Decay()
    {
        var ir = new double[40000];
        for (int n = 0; n < ir.Length; n++)
            ir[n] = Math.Pow(0.999, n);
        return ir;
    }

    [Fact]
    public void ALongGeometricDecayHasCentreQOverOneMinusQ()
    {
        const double q = 0.999 * 0.999;
        Assert.Equal(q / (1 - q) / 1000, Measurements.CentreTime(Decay(), 1000), 1e-9);
    }

    [Fact]
    public void TheEarlyDecayTimeIsTheZeroToMinusTenFit() =>
        Assert.Equal(60 / (-20 * Math.Log10(0.999) * 1000), Measurements.ReverberationTime(Decay(), 1000, 0, -10), 1e-8);
}
