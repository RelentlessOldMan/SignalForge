using Xunit;

namespace SignalForge.Tests;

/// <summary>The Tversky index (ADR 0423).</summary>
public class TverskyIndexTests
{
    private static readonly double[] Truth = [1.0, 1.0, 1.0, 0.0, 0.0, 1.0];
    private static readonly double[] Decision = [1.0, 1.0, 0.0, 1.0, 1.0, 0.0];

    [Fact]
    public void UnitWeightsGiveTheJaccardIndex() =>
        Assert.Equal(Measurements.JaccardIndex(Truth, Decision), Measurements.TverskyIndex(Truth, Decision, 1.0, 1.0), 15);

    [Fact]
    public void RejectsAZeroDenominator() =>
        Assert.ThrowsAny<ArgumentException>(() => Measurements.TverskyIndex([1.0, 0.0], [0.0, 1.0], 0.0, 0.0));
}
