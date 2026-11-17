using Xunit;

namespace SignalForge.Tests;

/// <summary>Magnitude-squared coherence (conventions: Coherence; ADR 0192).</summary>
public class CoherenceTests
{
    [Fact]
    public void FilteredNoiseIsCoherentAndIndependentNoiseIsNot()
    {
        var rng = new Random(39);
        var x = new double[8192];
        var z = new double[8192];
        for (int n = 0; n < x.Length; n++)
        {
            x[n] = rng.NextDouble() - 0.5;
            z[n] = rng.NextDouble() - 0.5;
        }
        var y = new double[x.Length];
        for (int n = 0; n < y.Length; n++)
            y[n] = 0.5 * x[n] + (n >= 1 ? 0.3 * x[n - 1] : 0) + (n >= 2 ? 0.1 * x[n - 2] : 0);
        Assert.All(Spectral.Coherence(x, y, 1, nperseg: 256).Values, v => Assert.True(v > 0.98));
        Assert.True(Spectral.Coherence(x, z, 1, nperseg: 256).Values.Average() < 0.05);
    }
}
