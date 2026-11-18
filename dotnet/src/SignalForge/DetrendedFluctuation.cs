namespace SignalForge;

/// <summary>DFA-1 fluctuations and their scaling exponent (conventions: Detrended fluctuation
/// analysis; ADR 0332).</summary>
/// <param name="Scales">The box sizes in samples, in the order given.</param>
/// <param name="Fluctuations">The RMS of the detrended profile at each box size.</param>
/// <param name="Alpha">The least-squares slope of <c>ln F</c> against <c>ln s</c>.</param>
public sealed record DetrendedFluctuation(int[] Scales, double[] Fluctuations, double Alpha);

public static partial class Measurements
{
    /// <summary>Detrended fluctuation analysis, DFA-1: the RMS of the linearly detrended profile
    /// in boxes of each size, and the log-log slope <c>α</c> (conventions: Detrended fluctuation
    /// analysis; ADR 0332).</summary>
    /// <param name="samples">Real samples, finite.</param>
    /// <param name="scales">At least two box sizes, strictly increasing, each from 4 to the
    /// number of samples.</param>
    /// <returns>The scales, the fluctuation at each, and <c>α</c>.</returns>
    /// <exception cref="ArgumentException">An argument is out of range, or the detrended profile
    /// is zero at some scale.</exception>
    public static DetrendedFluctuation DetrendedFluctuation(ReadOnlySpan<double> samples, ReadOnlySpan<int> scales)
    {
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int size = samples.Length;
        if (scales.Length < 2)
            throw new ArgumentException("scales must have at least two entries", nameof(scales));
        for (int i = 0; i < scales.Length; i++)
        {
            if (scales[i] < 4 || scales[i] > size)
                throw new ArgumentException("each scale must be at least 4 and at most samples.Length", nameof(scales));
            if (i > 0 && scales[i] <= scales[i - 1])
                throw new ArgumentException("scales must be strictly increasing", nameof(scales));
        }
        double mean = 0;
        foreach (double v in samples)
            mean += v;
        mean /= size;
        var profile = new double[size];
        double run = 0;
        for (int i = 0; i < size; i++)
        {
            run += samples[i] - mean;
            profile[i] = run;
        }
        var fluctuations = new double[scales.Length];
        for (int f = 0; f < scales.Length; f++)
        {
            int s = scales[f];
            int boxes = size / s;
            double centre = (s - 1) / 2.0;
            double stt = 0;
            for (int t = 0; t < s; t++)
                stt += (t - centre) * (t - centre);
            double total = 0;
            for (int b = 0; b < boxes; b++)
            {
                int start = b * s;
                double ym = 0;
                for (int t = 0; t < s; t++)
                    ym += profile[start + t];
                ym /= s;
                double sty = 0;
                for (int t = 0; t < s; t++)
                    sty += (t - centre) * (profile[start + t] - ym);
                double slope = sty / stt;
                for (int t = 0; t < s; t++)
                {
                    double r = profile[start + t] - ym - (slope * (t - centre));
                    total += r * r;
                }
            }
            fluctuations[f] = Math.Sqrt(total / ((double)boxes * s));
            if (!(fluctuations[f] > 0))
                throw new ArgumentException("the detrended profile must fluctuate at every scale", nameof(samples));
        }
        double mx = 0, my = 0;
        for (int f = 0; f < scales.Length; f++)
        {
            mx += Math.Log(scales[f]);
            my += Math.Log(fluctuations[f]);
        }
        mx /= scales.Length;
        my /= scales.Length;
        double sxy = 0, sxx = 0;
        for (int f = 0; f < scales.Length; f++)
        {
            double dx = Math.Log(scales[f]) - mx;
            sxy += dx * (Math.Log(fluctuations[f]) - my);
            sxx += dx * dx;
        }
        return new DetrendedFluctuation(scales.ToArray(), fluctuations, sxy / sxx);
    }
}
