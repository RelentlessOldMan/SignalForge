using Xunit;

namespace SignalForge.Tests;

/// <summary>Autocorrelation of a prediction-error filter (ADR 0220).</summary>
public class LpcToAutocorrelationTests
{
    [Fact]
    public void LevinsonInvertsIt()
    {
        double[] a = Dsp.ReflectionToLpc([0.4, -0.3, 0.2, 0.1, -0.35]);
        double[] r = Dsp.LpcToAutocorrelation(a, 0.7, a.Length - 1);
        var fit = Dsp.Levinson(r, a.Length - 1);
        for (int j = 0; j < a.Length; j++)
            Assert.Equal(a[j], fit.Coefficients[j], 1e-12);
        Assert.Equal(0.7, fit.Error, 1e-12);
    }
}
