using Xunit;

namespace SignalForge.Tests;

/// <summary>Time weighting (conventions: Time weighting; ADR 0166).</summary>
public class TimeWeightingTests
{
    [Fact]
    public void ASteadyToneSettlesToItsMeanSquare()
    {
        const double fs = 8000;
        var x = new double[16000];
        for (int n = 0; n < x.Length; n++)
            x[n] = Math.Sqrt(2) * Math.Sin(2 * Math.PI * 1000 * n / fs);
        double[] y = Measurements.TimeWeighting(x, fs, 0.125);
        Assert.Equal(1.0, y[^1], 1e-3);
        Assert.All(y, v => Assert.True(v >= 0));
    }

    [Fact]
    public void OneTimeConstantReachesOneMinusOneOverE()
    {
        double[] y = Measurements.TimeWeighting(Enumerable.Repeat(1.0, 6000).ToArray(), 48000, 0.125);
        Assert.Equal(1 - Math.Exp(-1), y[^1], 1e-12);
    }
}
