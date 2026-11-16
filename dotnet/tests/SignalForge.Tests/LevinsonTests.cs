using Xunit;

namespace SignalForge.Tests;

/// <summary>Linear prediction by Levinson-Durbin (conventions: Pulse shaping, Linear prediction; ADR 0149).</summary>
public class LevinsonTests
{
    private static double[] Ar2(int n)
    {
        var rng = new Random(149);
        var x = new double[n];
        for (int i = 2; i < n; i++)
        {
            double w = Math.Sqrt(-2 * Math.Log(1 - rng.NextDouble())) * Math.Cos(2 * Math.PI * rng.NextDouble());
            x[i] = 0.75 * x[i - 1] - 0.5 * x[i - 2] + w;
        }
        return x;
    }

    [Fact]
    public void RecoversAnAr2Process()
    {
        var lev = Dsp.Levinson(Dsp.Autocorrelation(Ar2(100_000), 2), 2);
        Assert.Equal(1.0, lev.Coefficients[0]);
        Assert.Equal(-0.75, lev.Coefficients[1], 0.02);
        Assert.Equal(0.5, lev.Coefficients[2], 0.02);
        Assert.Equal(1.0, lev.Error, 0.03);
    }

    [Fact]
    public void ErrorIsTheResidualMeanSquare()
    {
        double[] x = Ar2(500);
        var lev = Dsp.Levinson(Dsp.Autocorrelation(x, 4), 4);
        double[] residual = Dsp.Convolve(x, lev.Coefficients);
        double meanSquare = residual.Sum(v => v * v) / x.Length;
        Assert.Equal(meanSquare, lev.Error, 1e-10 * meanSquare);
    }
}
