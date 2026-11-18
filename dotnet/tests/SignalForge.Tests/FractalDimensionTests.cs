using Xunit;

namespace SignalForge.Tests;

/// <summary>Katz and Petrosian fractal dimensions (ADRs 0334, 0335).</summary>
public class FractalDimensionTests
{
    [Fact]
    public void KatzOfALineIsOne()
    {
        double[] x = new double[30];
        for (int i = 0; i < x.Length; i++)
            x[i] = 2 - (0.5 * i);
        Assert.Equal(1.0, Measurements.KatzDimension(x), 1e-14);
    }

    [Fact]
    public void KatzRejectsAZeroDenominator() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.KatzDimension([0.0, 3.0, 0.0]));

    [Fact]
    public void PetrosianByHand()
    {
        // 0, 2, 1, 3: steps +, −, +: two changes.
        double expected = Math.Log10(4) / (Math.Log10(4) + Math.Log10(4 / 4.8));
        Assert.Equal(expected, Measurements.PetrosianDimension([0.0, 2.0, 1.0, 3.0]), 1e-15);
    }

    [Fact]
    public void PetrosianOfAMonotonicSeriesIsOne() =>
        Assert.Equal(1.0, Measurements.PetrosianDimension([0.0, 1.0, 1.0, 4.0]));
}
