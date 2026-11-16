namespace SignalForge;

public static partial class Measurements
{
    private static readonly double[] StiAlpha = [0.085, 0.127, 0.230, 0.233, 0.309, 0.224, 0.173];
    private static readonly double[] StiBeta = [0.085, 0.078, 0.065, 0.011, 0.047, 0.095];

    /// <summary>The speech transmission index of a 7-band MTF matrix with the IEC 60268-16:2020
    /// male weights, without level, masking or threshold corrections (conventions: Speech
    /// transmission index; ADR 0177).</summary>
    /// <param name="mtf">7 rows (octave bands 125 Hz to 8 kHz) of equal length, at least 1,
    /// finite; values outside [0, 1] clip.</param>
    /// <returns>The STI.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double SpeechTransmissionIndex(double[][] mtf)
    {
        ArgumentNullException.ThrowIfNull(mtf);
        if (mtf.Length != 7)
            throw new ArgumentException("mtf must have 7 rows", nameof(mtf));
        int columns = mtf[0]?.Length ?? 0;
        if (columns == 0)
            throw new ArgumentException("mtf must have at least one column", nameof(mtf));
        var mti = new double[7];
        for (int k = 0; k < 7; k++)
        {
            double[] row = mtf[k];
            if (row is null || row.Length != columns)
                throw new ArgumentException("mtf rows must have equal length", nameof(mtf));
            double sum = 0;
            foreach (double m in row)
            {
                if (!double.IsFinite(m))
                    throw new ArgumentException("mtf must be finite", nameof(mtf));
                sum += TransmissionIndex(m);
            }
            mti[k] = sum / columns;
        }
        double sti = 0;
        for (int k = 0; k < 7; k++)
            sti += StiAlpha[k] * mti[k];
        for (int k = 0; k < 6; k++)
            sti -= StiBeta[k] * Math.Sqrt(mti[k] * mti[k + 1]);
        return sti;
    }

    private static double TransmissionIndex(double m)
    {
        if (m <= 0)
            return 0;
        if (m >= 1)
            return 1;
        double snr = Math.Clamp(10 * Math.Log10(m / (1 - m)), -15, 15);
        return (snr + 15) / 30;
    }
}
