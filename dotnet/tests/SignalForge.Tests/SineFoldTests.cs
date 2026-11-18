using Xunit;

namespace SignalForge.Tests;

/// <summary>Sine wavefolder (ADR 0323).</summary>
public class SineFoldTests
{
    [Fact]
    public void UnitDriveMapsOneToOne() => Assert.Equal([-1.0, 0.0, 1.0], Dsp.SineFold([-1.0, 0.0, 1.0], 1));

    [Fact]
    public void DriveTwoFoldsOneBackToZero() => Assert.Equal(0.0, Dsp.SineFold([1.0], 2)[0], 1e-15);

    [Fact]
    public void RejectsAZeroDrive() =>
        Assert.ThrowsAny<ArgumentException>(() => Dsp.SineFold([0.5], 0));
}
