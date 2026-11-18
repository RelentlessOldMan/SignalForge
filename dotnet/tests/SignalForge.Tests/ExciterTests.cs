using Xunit;

namespace SignalForge.Tests;

/// <summary>Harmonic exciter (ADR 0288).</summary>
public class ExciterTests
{
    [Fact]
    public void MixZeroIsTheInput()
    {
        double[] x = [0.3, -0.7, 1.1, 0.4, -0.9, 0.2, 0.8, -0.6];
        Assert.Equal(x, Dsp.Exciter(x, 4, 0.2, 1.0, 3.0, 0.0));
    }

    [Fact]
    public void RejectsInfiniteDrive() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.Exciter([1.0], 4, 1.0, 8.0, double.PositiveInfinity, 0.5));
}
