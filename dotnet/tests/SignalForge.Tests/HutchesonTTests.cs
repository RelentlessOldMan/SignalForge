using Xunit;

namespace SignalForge.Tests;

/// <summary>Hutcheson's t (ADR 0557).</summary>
public class HutchesonTTests
{
    [Fact]
    public void EvenAgainstOneKind() =>
        Assert.Equal(4.0 * Math.Sqrt(2.0) * Math.Log(2.0), Measurements.HutchesonT([2.0, 2.0], [4.0]), 13);

    [Fact]
    public void ChangesSignOnSwap() =>
        Assert.Equal(
            -Measurements.HutchesonT([1.0, 2.0, 3.0], [5.0, 1.0, 1.0]),
            Measurements.HutchesonT([5.0, 1.0, 1.0], [1.0, 2.0, 3.0]),
            15);

    [Fact]
    public void RejectsBothOneKind() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.HutchesonT([4.0], [0.0, 3.0]));
}
