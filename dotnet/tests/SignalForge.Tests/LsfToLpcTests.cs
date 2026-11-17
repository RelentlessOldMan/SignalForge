using Xunit;

namespace SignalForge.Tests;

/// <summary>LSF to prediction filter (conventions: LSF to prediction filter; ADR 0209).</summary>
public class LsfToLpcTests
{
    [Fact]
    public void RoundTripsABurgFit()
    {
        var rng = new Random(60);
        var x = new double[500];
        for (int i = 0; i < x.Length; i++)
            x[i] = rng.NextDouble() - 0.5;
        foreach (int order in new[] { 1, 2, 7, 12 })
        {
            double[] a = Dsp.Burg(x, order).Coefficients;
            double[] back = Dsp.LsfToLpc(Dsp.LineSpectralFrequencies(a));
            Assert.Equal(a.Length, back.Length);
            for (int j = 0; j < a.Length; j++)
                Assert.Equal(a[j], back[j], 1e-10);
        }
    }
}
