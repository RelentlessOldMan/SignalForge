using Xunit;

namespace SignalForge.Tests;

/// <summary>The extremal dependence index (ADR 0490).</summary>
public class ExtremalDependenceIndexTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(Math.Log(0.25) / Math.Log(0.16), Measurements.ExtremalDependenceIndex([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 14);

    [Fact]
    public void RejectsADecisionOfAllOnes() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.ExtremalDependenceIndex([1.0, 0.0], [1.0, 1.0]));
}
