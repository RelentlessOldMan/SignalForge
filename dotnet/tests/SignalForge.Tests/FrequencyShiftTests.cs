using Xunit;

namespace SignalForge.Tests;

/// <summary>Frequency shifter (ADR 0301).</summary>
public class FrequencyShiftTests
{
    [Fact]
    public void ShiftsACosineUp()
    {
        double[] x = new double[64];
        for (int n = 0; n < x.Length; n++)
            x[n] = Math.Cos(2 * Math.PI * 5 * n / 64);
        double[] y = Spectral.FrequencyShift(x, 3.0, 64.0);
        for (int n = 0; n < y.Length; n++)
            Assert.Equal(Math.Cos(2 * Math.PI * 8 * n / 64), y[n], 1e-12);
    }

    [Fact]
    public void RejectsInfiniteShift() =>
        Assert.ThrowsAny<ArgumentException>(() => Spectral.FrequencyShift([1.0, 2.0], double.PositiveInfinity, 8.0));
}
