using Xunit;

namespace SignalForge.Tests;

/// <summary>Clarity and definition (conventions: Clarity and definition; ADR 0172).</summary>
public class ClarityTests
{
    [Fact]
    public void ClarityAndDefinitionAgree()
    {
        var rng = new Random(10);
        var ir = new double[4000];
        for (int n = 0; n < ir.Length; n++)
            ir[n] = (rng.NextDouble() - 0.5) * Math.Pow(0.999, n);
        double d = Measurements.Definition(ir, 8000);
        Assert.Equal(10 * Math.Log10(d / (1 - d)), Measurements.Clarity(ir, 8000, 0.05), 1e-10);
    }
}
