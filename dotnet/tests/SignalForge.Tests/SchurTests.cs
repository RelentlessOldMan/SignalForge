using Xunit;

namespace SignalForge.Tests;

/// <summary>Schur recursion (ADR 0221).</summary>
public class SchurTests
{
    [Fact]
    public void MatchesLevinson()
    {
        double[] r = Dsp.LpcToAutocorrelation(Dsp.ReflectionToLpc([0.4, -0.3, 0.2, 0.1, -0.35]), 0.7, 7);
        for (int order = 1; order <= 7; order++)
        {
            var s = Dsp.Schur(r, order);
            var fit = Dsp.Levinson(r, order);
            for (int j = 0; j < order; j++)
                Assert.Equal(fit.Reflection[j], s.Reflection[j], 1e-12);
            Assert.Equal(fit.Error, s.Error, 1e-12);
        }
    }
}
