using Xunit;

namespace SignalForge.Tests;

/// <summary>Lattice synthesis filter (conventions: Lattice synthesis filter; ADR 0212).</summary>
public class LatticeSynthesisTests
{
    [Fact]
    public void InvertsTheAnalysisLattice()
    {
        var rng = new Random(64);
        var x = new double[300];
        for (int i = 0; i < x.Length; i++)
            x[i] = rng.NextDouble() - 0.5;
        double[] k = [0.4, -0.3, 0.2, 0.1, -0.35, 0.25];
        double[] y = Dsp.LatticeSynthesis(Dsp.LatticeFilter(x, k), k);
        for (int n = 0; n < x.Length; n++)
            Assert.Equal(x[n], y[n], 1e-10);
    }
}
