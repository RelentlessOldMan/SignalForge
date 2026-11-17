using Xunit;

namespace SignalForge.Tests;

/// <summary>Lattice analysis filter (conventions: Lattice analysis filter; ADR 0211).</summary>
public class LatticeFilterTests
{
    [Fact]
    public void MatchesTheDirectFormFilter()
    {
        var rng = new Random(62);
        var x = new double[200];
        for (int i = 0; i < x.Length; i++)
            x[i] = rng.NextDouble() - 0.5;
        double[] k = [0.4, -0.3, 0.2, 0.1, -0.35];
        double[] a = Dsp.ReflectionToLpc(k);
        double[] y = Dsp.LatticeFilter(x, k);
        for (int n = 0; n < x.Length; n++)
        {
            double acc = 0;
            for (int j = 0; j < a.Length && j <= n; j++)
                acc += a[j] * x[n - j];
            Assert.Equal(acc, y[n], 1e-12);
        }
    }
}
