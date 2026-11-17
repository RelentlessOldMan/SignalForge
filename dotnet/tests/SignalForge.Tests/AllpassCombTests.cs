using Xunit;

namespace SignalForge.Tests;

/// <summary>Schroeder allpass section (ADR 0240).</summary>
public class AllpassCombTests
{
    [Fact]
    public void ImpulseResponseMatchesClosedForm()
    {
        var x = new double[40];
        x[0] = 1;
        double g = 0.7;
        double[] h = Dsp.AllpassComb(x, 5, g);
        for (int n = 0; n < 40; n++)
        {
            double want = n == 0 ? -g : n % 5 == 0 ? (1 - g * g) * Math.Pow(g, n / 5 - 1) : 0;
            Assert.Equal(want, h[n], 1e-14);
        }
    }

    [Fact]
    public void RejectsUnitGain() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.AllpassComb([1.0], 1, 1.0));
}
