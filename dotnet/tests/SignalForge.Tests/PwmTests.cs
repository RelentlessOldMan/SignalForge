using Xunit;

namespace SignalForge.Tests;

/// <summary>Pulse-width modulation (ADR 0312).</summary>
public class PwmTests
{
    [Fact]
    public void AConstantDutyIsTheNaiveSquare()
    {
        double[] d = new double[200];
        Array.Fill(d, 0.3);
        Assert.Equal(Waveforms.Square(8000, 200, 123, 0.3, 0.7, 0.2), Waveforms.Pwm(d, 8000, 123, 0.7, 0.2));
    }

    [Fact]
    public void AnEmptyDutyGivesAnEmptyOutput() => Assert.Empty(Waveforms.Pwm([], 8000, 1000));

    [Theory]
    [InlineData(double.NaN)]
    [InlineData(-0.5)]
    [InlineData(1.5)]
    public void RejectsADutyOutsideZeroToOne(double bad) =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.Pwm([0.5, bad], 8000, 1000));
}
