using Xunit;

namespace SignalForge.Tests;

/// <summary>Modulation transfer function (conventions: Modulation transfer function; ADR 0176).</summary>
public class ModulationTransferTests
{
    [Fact]
    public void ALongDecayMatchesSchroedersContinuousForm()
    {
        const double fs = 8000, t60 = 1;
        double r = Math.Pow(10, -3 / (t60 * fs));
        var ir = new double[(int)(3 * fs)];
        for (int n = 0; n < ir.Length; n++)
            ir[n] = Math.Pow(r, n);
        double[] f = [0.63, 2, 8];
        double[] m = Measurements.ModulationTransfer(ir, fs, f);
        for (int k = 0; k < f.Length; k++)
        {
            double expected = 1 / Math.Sqrt(1 + Math.Pow(2 * Math.PI * f[k] * t60 / (6 * Math.Log(10)), 2));
            Assert.True(Math.Abs(m[k] / expected - 1) < 1e-3, $"F = {f[k]}: {m[k]} vs {expected}");
        }
    }
}
