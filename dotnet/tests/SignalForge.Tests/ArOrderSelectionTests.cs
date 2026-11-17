using Xunit;

namespace SignalForge.Tests;

/// <summary>AR order selection (conventions: AR order selection; ADR 0206).</summary>
public class ArOrderSelectionTests
{
    [Fact]
    public void PicksTheOrderOfAnAr2Process()
    {
        var rng = new Random(57);
        var x = new double[5000];
        for (int i = 2; i < x.Length; i++)
        {
            double u1 = 1.0 - rng.NextDouble(), u2 = rng.NextDouble();
            double w = Math.Sqrt(-2 * Math.Log(u1)) * Math.Cos(2 * Math.PI * u2);
            x[i] = (1.2 * x[i - 1]) - (0.6 * x[i - 2]) + w;
        }
        var s = Dsp.ArOrderSelection(x, 10);
        Assert.Equal(2, s.AicOrder);
        Assert.InRange(s.FpeOrder, 2, 4);
    }
}
