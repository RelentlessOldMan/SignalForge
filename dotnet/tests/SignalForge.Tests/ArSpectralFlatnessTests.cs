using Xunit;

namespace SignalForge.Tests;

/// <summary>Spectral flatness of an AR model (ADR 0213).</summary>
public class ArSpectralFlatnessTests
{
    [Fact]
    public void IsTheRatioOfModelErrorToPower()
    {
        // sigma^2 / r[0] of a Burg fit is the product, by the Levinson error recursion.
        var rng = new Random(65);
        var x = new double[500];
        for (int i = 1; i < x.Length; i++)
            x[i] = (0.8 * x[i - 1]) + rng.NextDouble() - 0.5;
        var fit = Dsp.Burg(x, 4);
        double r0 = x.Sum(v => v * v) / x.Length;
        double product = 1;
        foreach (double k in fit.Reflection)
            product *= 1 - (k * k);
        Assert.Equal(product, Dsp.ArSpectralFlatness(fit.Reflection), 1e-14);
        Assert.Equal(fit.Error / r0, Dsp.ArSpectralFlatness(fit.Reflection), 1e-12);
    }
}
