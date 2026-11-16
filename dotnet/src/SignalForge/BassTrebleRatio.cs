namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Beranek's bass ratio <c>(T125 + T250)/(T500 + T1000)</c> (conventions: Bass and
    /// treble ratio; ADR 0180).</summary>
    /// <param name="times">The six octave-band reverberation times in seconds at 125, 250, 500,
    /// 1000, 2000 and 4000 Hz, finite and positive.</param>
    /// <returns>The ratio.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double BassRatio(ReadOnlySpan<double> times)
    {
        CheckBandTimes(times);
        return (times[0] + times[1]) / (times[2] + times[3]);
    }

    /// <summary>Beranek's treble ratio <c>(T2000 + T4000)/(T500 + T1000)</c> (conventions: Bass
    /// and treble ratio; ADR 0180).</summary>
    /// <param name="times">The six octave-band reverberation times in seconds at 125, 250, 500,
    /// 1000, 2000 and 4000 Hz, finite and positive.</param>
    /// <returns>The ratio.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double TrebleRatio(ReadOnlySpan<double> times)
    {
        CheckBandTimes(times);
        return (times[4] + times[5]) / (times[2] + times[3]);
    }

    private static void CheckBandTimes(ReadOnlySpan<double> times)
    {
        if (times.Length != 6)
            throw new ArgumentException("times must be six reverberation times (125 Hz to 4 kHz)", nameof(times));
        foreach (double t in times)
        {
            if (!(double.IsFinite(t) && t > 0))
                throw new ArgumentException("times must be finite and positive", nameof(times));
        }
    }
}
