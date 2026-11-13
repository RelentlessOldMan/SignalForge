using System.Numerics;
using Xunit;

namespace SignalForge.Tests;

/// <summary>Fractional delay: tones come through delayed as theory says, whole-sample delays are
/// exact shifts (conventions: Channel, Fractional delay).</summary>
public class FractionalDelayTests
{
    [Theory]
    [InlineData(0.05, 5e-5)]
    [InlineData(0.25, 5e-5)]
    [InlineData(0.4, 3e-4)]
    public void AToneIsDelayed(double freq, double bound)
    {
        Complex[] x = [.. Enumerable.Range(0, 400).Select(n => Complex.FromPolarCoordinates(1, 2 * Math.PI * freq * n))];
        foreach (double d in new[] { 0.37, 3.5, -2.8 })
        {
            Complex[] y = Channel.FractionalDelay(x, d);
            for (int n = 50; n < 350; n++)
                Assert.True(Complex.Abs(y[n] - Complex.FromPolarCoordinates(1, 2 * Math.PI * freq * (n - d))) < bound, $"{d} at {n}");
        }
    }

    [Fact]
    public void WholeSampleDelaysAreExact()
    {
        var rng = new Random(5);
        Complex[] x = [.. Enumerable.Range(0, 64).Select(_ => new Complex(rng.NextDouble() - 0.5, rng.NextDouble() - 0.5))];
        foreach (int d in new[] { 0, 1, 7, -3 })
        {
            Complex[] y = Channel.FractionalDelay(x, d, 5);
            for (int n = 0; n < 64; n++)
                Assert.Equal(n - d >= 0 && n - d < 64 ? x[n - d] : Complex.Zero, y[n]);
        }
    }

    [Fact]
    public void BadArgumentsThrow()
    {
        Assert.ThrowsAny<ArgumentException>(() => Channel.FractionalDelay([Complex.One], double.NaN));
        Assert.ThrowsAny<ArgumentException>(() => Channel.FractionalDelay([Complex.One], double.NegativeInfinity));
        Assert.ThrowsAny<ArgumentException>(() => Channel.FractionalDelay([Complex.One], 0.5, 0));
    }
}
