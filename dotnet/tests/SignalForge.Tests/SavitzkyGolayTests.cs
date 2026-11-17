using Xunit;

namespace SignalForge.Tests;

/// <summary>Savitzky–Golay (ADR 0233).</summary>
public class SavitzkyGolayTests
{
    [Fact]
    public void ReproducesACubicAndItsDerivative()
    {
        double[] x = [.. Enumerable.Range(0, 40).Select(k => 0.01 * k * k * k - 0.3 * k * k + 2 * k - 1)];
        double[] y = Dsp.SavgolFilter(x, 9, 3);
        double[] dy = Dsp.SavgolFilter(x, 9, 3, 1);
        for (int k = 0; k < 40; k++)
        {
            Assert.True(Math.Abs(y[k] - x[k]) < 1e-9, $"value {k}");
            Assert.True(Math.Abs(dy[k] - (0.03 * k * k - 0.6 * k + 2)) < 1e-9, $"slope {k}");
        }
    }
}
