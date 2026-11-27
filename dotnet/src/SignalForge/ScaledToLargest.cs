using System.Numerics;

namespace SignalForge;

public static partial class Measurements
{
    /// <summary>Divides each value by the largest one, when that is positive and finite, so no
    /// sum of the shares can overflow; otherwise returns the values unchanged for the caller's
    /// own checks to refuse (ADRs 0625, 0626).</summary>
    private static ReadOnlySpan<double> ScaledToLargest(ReadOnlySpan<double> samples)
    {
        double top = 0;
        foreach (double v in samples)
        {
            if (v > top)
                top = v;
        }
        if (!(top > 0) || double.IsInfinity(top))
            return samples;
        double[] scaled = new double[samples.Length];
        for (int i = 0; i < samples.Length; i++)
            scaled[i] = samples[i] / top;
        return scaled;
    }

    /// <summary>Divides each value by the largest magnitude, when that is positive and finite,
    /// so no square of a deviation can overflow or underflow; otherwise returns the values
    /// unchanged for the caller's own checks to refuse (ADR 0627).</summary>
    private static ReadOnlySpan<double> ScaledToLargestMagnitude(ReadOnlySpan<double> samples)
    {
        double top = 0;
        foreach (double v in samples)
        {
            if (Math.Abs(v) > top)
                top = Math.Abs(v);
        }
        if (!(top > 0) || double.IsInfinity(top))
            return samples;
        double[] scaled = new double[samples.Length];
        for (int i = 0; i < samples.Length; i++)
            scaled[i] = samples[i] / top;
        return scaled;
    }

    /// <summary>Scales both records by the power of 2 that brings the largest magnitude in
    /// either into [1, 2), when that is positive and finite, for measures that do not change
    /// when both are scaled alike, so no square of a deviation can overflow or underflow. The
    /// scaling is exact, so the result is the same as unscaled whenever nothing overflows.
    /// Otherwise leaves the records unchanged for the caller's own checks to refuse (ADR
    /// 0628).</summary>
    private static void ScaleTogether(ref ReadOnlySpan<double> x, ref ReadOnlySpan<double> y)
    {
        double top = 0;
        foreach (double v in x)
        {
            if (Math.Abs(v) > top)
                top = Math.Abs(v);
        }
        foreach (double v in y)
        {
            if (Math.Abs(v) > top)
                top = Math.Abs(v);
        }
        if (!(top > 0) || double.IsInfinity(top))
            return;
        int e = Math.ILogB(top);
        double[] sx = new double[x.Length];
        for (int i = 0; i < x.Length; i++)
            sx[i] = Math.ScaleB(x[i], -e);
        double[] sy = new double[y.Length];
        for (int i = 0; i < y.Length; i++)
            sy[i] = Math.ScaleB(y[i], -e);
        x = sx;
        y = sy;
    }

    /// <summary>The samples times the power of 2 that brings their largest magnitude into
    /// [1, 2), when that is positive and finite, for statistics that do not change when the
    /// record is scaled, so no square of a deviation can overflow or underflow. The scaling is
    /// exact. Otherwise the samples unchanged, for the caller's own checks to refuse (ADR
    /// 0629).</summary>
    private static ReadOnlySpan<double> ScaledByPowerOf2(ReadOnlySpan<double> samples)
    {
        double top = 0;
        foreach (double v in samples)
        {
            if (Math.Abs(v) > top)
                top = Math.Abs(v);
        }
        if (!(top > 0) || double.IsInfinity(top))
            return samples;
        int e = Math.ILogB(top);
        double[] scaled = new double[samples.Length];
        for (int i = 0; i < samples.Length; i++)
            scaled[i] = Math.ScaleB(samples[i], -e);
        return scaled;
    }

    /// <summary>The largest magnitude among the values, skipping NaN (ADR 0630).</summary>
    private static double LargestMagnitude(ReadOnlySpan<double> values)
    {
        double top = 0;
        foreach (double v in values)
        {
            if (Math.Abs(v) > top)
                top = Math.Abs(v);
        }
        return top;
    }

    /// <summary>The largest real or imaginary magnitude among the values, skipping NaN
    /// (ADR 0630).</summary>
    private static double LargestMagnitude(ReadOnlySpan<Complex> values)
    {
        double top = 0;
        foreach (Complex v in values)
        {
            if (Math.Abs(v.Real) > top)
                top = Math.Abs(v.Real);
            if (Math.Abs(v.Imaginary) > top)
                top = Math.Abs(v.Imaginary);
        }
        return top;
    }

    /// <summary>The exponent e with 2^e ≤ <paramref name="top"/> &lt; 2^(e + 1), when that is
    /// positive and finite; 0 otherwise, so a record the caller will refuse is left unscaled
    /// (ADR 0630).</summary>
    private static int PowerOf2Exponent(double top) =>
        top > 0 && !double.IsInfinity(top) ? Math.ILogB(top) : 0;
}
