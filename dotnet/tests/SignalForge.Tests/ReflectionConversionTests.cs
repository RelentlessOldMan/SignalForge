using Xunit;

namespace SignalForge.Tests;

/// <summary>Reflection coefficients and prediction filters (ADR 0210).</summary>
public class ReflectionConversionTests
{
    [Fact]
    public void RoundTripsABurgFit()
    {
        var rng = new Random(61);
        var x = new double[300];
        for (int i = 0; i < x.Length; i++)
            x[i] = rng.NextDouble() - 0.5;
        var fit = Dsp.Burg(x, 9);
        double[] a = Dsp.ReflectionToLpc(fit.Reflection);
        double[] k = Dsp.LpcToReflection(fit.Coefficients);
        for (int j = 0; j < a.Length; j++)
            Assert.Equal(fit.Coefficients[j], a[j], 1e-12);
        for (int j = 0; j < k.Length; j++)
            Assert.Equal(fit.Reflection[j], k[j], 1e-12);
    }
}
