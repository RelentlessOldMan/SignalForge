using Xunit;

namespace SignalForge.Tests;

/// <summary>Pielou's index of non-randomness (ADR 0619).</summary>
public class PielouNonrandomnessTests
{
    [Fact]
    public void Unit() =>
        Assert.Equal(Math.PI, Measurements.PielouNonrandomness([1.0], 1.0), 14);

    [Fact]
    public void MeanSquare() =>
        Assert.Equal(2.5 * Math.PI, Measurements.PielouNonrandomness([1.0, 3.0], 0.5), 14);

    [Fact]
    public void Coincident() =>
        Assert.Equal(0.0, Measurements.PielouNonrandomness([0.0, 0.0], 3.0));

    [Fact]
    public void RejectsZeroDensity() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PielouNonrandomness([1.0], 0.0));

    [Fact]
    public void RejectsOverflow() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.PielouNonrandomness([1e150, 1e150], 1e10));
}
