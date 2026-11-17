using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Teager-Kaiser energy (conventions: Teager-Kaiser energy; ADR 0188).</summary>
public class TeagerEnergyTests
{
    [Fact]
    public void RealAndComplexFormsAgreeOnRealInput()
    {
        var rng = new Random(34);
        var x = new double[50];
        var c = new Complex[50];
        for (int n = 0; n < x.Length; n++)
            c[n] = x[n] = rng.NextDouble() - 0.5;
        var r = Measurements.TeagerEnergy(x);
        var z = Measurements.TeagerEnergy(c);
        for (int n = 0; n < r.Length; n++)
            Assert.Equal(r[n], z[n], 1e-15);
    }
}
