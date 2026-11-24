using Xunit;

namespace SignalForge.Tests;

/// <summary>Lloyd's index of patchiness (ADR 0610).</summary>
public class LloydPatchinessTests
{
    [Fact]
    public void Mixed() =>
        Assert.Equal(2.0 / 3.0, Measurements.LloydPatchiness([1.0, 2.0, 3.0]), 14);

    [Fact]
    public void Singles() =>
        Assert.Equal(0.0, Measurements.LloydPatchiness([1.0, 1.0, 0.0]));

    [Fact]
    public void Clumped() =>
        Assert.Equal(2.5, Measurements.LloydPatchiness([0.0, 0.0, 6.0]), 14);

    [Fact]
    public void RejectsFraction() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LloydPatchiness([1.5, 2.0]));

    [Fact]
    public void RejectsAllZero() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.LloydPatchiness([0.0, 0.0]));
}
