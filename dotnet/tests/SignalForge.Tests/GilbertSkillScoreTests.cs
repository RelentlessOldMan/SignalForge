using Xunit;

namespace SignalForge.Tests;

/// <summary>The Gilbert skill score (ADR 0439).</summary>
public class GilbertSkillScoreTests
{
    [Fact]
    public void Square() =>
        Assert.Equal(3.0 / 7.0, Measurements.GilbertSkillScore([1, 1, 1, 1, 0, 0, 0, 0, 1, 0], [1, 1, 1, 1, 0, 0, 0, 0, 0, 1]), 15);

    [Fact]
    public void RejectsEqualConstantRecords() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.GilbertSkillScore([1.0, 1.0], [1.0, 1.0]));
}
