using Xunit;

namespace SignalForge.Tests;

/// <summary>Autocorrelation of an AR model (ADR 0214).</summary>
public class ReflectionToAutocorrelationTests
{
    [Fact]
    public void LevinsonInvertsIt()
    {
        double[] k = [0.4, -0.3, 0.2, 0.1, -0.35, 0.25];
        double[] r = Dsp.ReflectionToAutocorrelation(k, 2.5, k.Length);
        var fit = Dsp.Levinson(r, k.Length);
        for (int j = 0; j < k.Length; j++)
            Assert.Equal(k[j], fit.Reflection[j], 1e-12);
    }
}
