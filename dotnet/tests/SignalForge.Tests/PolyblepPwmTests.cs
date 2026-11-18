using Xunit;

namespace SignalForge.Tests;

/// <summary>PolyBLEP pulse-width modulation (ADR 0313).</summary>
public class PolyblepPwmTests
{
    [Fact]
    public void AConstantDutyIsThePolyblepSquare()
    {
        double[] d = new double[200];
        Array.Fill(d, 0.3);
        Assert.Equal(Waveforms.PolyblepSquare(8000, 200, 123, 0.3, 0.7, 0.2),
            Waveforms.PolyblepPwm(d, 8000, 123, 0.7, 0.2));
    }

    [Fact]
    public void RejectsAFrequencyAboveNyquist() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PolyblepPwm([0.5], 8000, 4001));

    [Fact]
    public void RejectsADutyOutsideZeroToOne() =>
        Assert.ThrowsAny<ArgumentException>(() => Waveforms.PolyblepPwm([0.5, 1.5], 8000, 1000));
}
