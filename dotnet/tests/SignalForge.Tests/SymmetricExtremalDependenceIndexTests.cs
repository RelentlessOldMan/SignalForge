using Xunit;

namespace SignalForge.Tests;

/// <summary>The symmetric extremal dependence index (ADR 0491).</summary>
public class SymmetricExtremalDependenceIndexTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Log(0.25) / Math.Log(0.16), Measurements.SymmetricExtremalDependenceIndex([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsATableWithAZeroCell() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.SymmetricExtremalDependenceIndex([1.0, 0.0, 1.0, 0.0], [1.0, 1.0, 1.0, 0.0]));
}
