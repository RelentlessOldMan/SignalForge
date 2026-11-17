using Xunit;

namespace SignalForge.Tests;

/// <summary>Cross-correlation (conventions: Cross-correlation; ADR 0190).</summary>
public class CrossCorrelationTests
{
    [Fact]
    public void LagsFromZeroAreTheUnscaledAutocorrelation()
    {
        var rng = new Random(36);
        var x = new double[12];
        for (int n = 0; n < x.Length; n++)
            x[n] = rng.NextDouble() - 0.5;
        var r = Dsp.CrossCorrelation(x, x);
        var a = Dsp.Autocorrelation(x, null, CorrelationScaling.None);
        for (int k = 0; k < a.Length; k++)
            Assert.Equal(a[k], r[k + 11], 1e-14);
    }
}
