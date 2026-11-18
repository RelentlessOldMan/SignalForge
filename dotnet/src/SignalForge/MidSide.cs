namespace SignalForge;

/// <summary>The mid and side channels of a stereo pair (conventions: Mid/side coding;
/// ADR 0264).</summary>
/// <param name="Mid">Half the sum of the channels.</param>
/// <param name="Side">Half the difference of the channels.</param>
public sealed record MidSide(double[] Mid, double[] Side);

/// <summary>The left and right channels of a stereo pair (conventions: Mid/side coding;
/// ADR 0264).</summary>
/// <param name="Left">The left channel.</param>
/// <param name="Right">The right channel.</param>
public sealed record LeftRight(double[] Left, double[] Right);

public static partial class Dsp
{
    /// <summary>Encodes a stereo pair as <c>mid = (left + right)/2</c>,
    /// <c>side = (left − right)/2</c> (conventions: Mid/side coding; ADR 0264).</summary>
    /// <param name="left">The left channel, finite, at least one sample.</param>
    /// <param name="right">The right channel, finite, the same length.</param>
    /// <returns>The mid and side channels.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static MidSide MidSideEncode(ReadOnlySpan<double> left, ReadOnlySpan<double> right)
    {
        if (left.IsEmpty)
            throw new ArgumentException("left must not be empty", nameof(left));
        if (right.Length != left.Length)
            throw new ArgumentException("left and right must have the same length", nameof(right));
        var mid = new double[left.Length];
        var side = new double[left.Length];
        for (int n = 0; n < left.Length; n++)
        {
            double a = left[n], b = right[n];
            if (!double.IsFinite(a))
                throw new ArgumentException("left must be finite", nameof(left));
            if (!double.IsFinite(b))
                throw new ArgumentException("right must be finite", nameof(right));
            mid[n] = (a + b) / 2;
            side[n] = (a - b) / 2;
        }
        return new MidSide(mid, side);
    }

    /// <summary>Decodes mid and side as <c>left = mid + side</c>, <c>right = mid − side</c>
    /// (conventions: Mid/side coding; ADR 0264).</summary>
    /// <param name="mid">The mid channel, finite, at least one sample.</param>
    /// <param name="side">The side channel, finite, the same length.</param>
    /// <returns>The left and right channels.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LeftRight MidSideDecode(ReadOnlySpan<double> mid, ReadOnlySpan<double> side)
    {
        if (mid.IsEmpty)
            throw new ArgumentException("mid must not be empty", nameof(mid));
        if (side.Length != mid.Length)
            throw new ArgumentException("mid and side must have the same length", nameof(side));
        var left = new double[mid.Length];
        var right = new double[mid.Length];
        for (int n = 0; n < mid.Length; n++)
        {
            double m = mid[n], s = side[n];
            if (!double.IsFinite(m))
                throw new ArgumentException("mid must be finite", nameof(mid));
            if (!double.IsFinite(s))
                throw new ArgumentException("side must be finite", nameof(side));
            left[n] = m + s;
            right[n] = m - s;
        }
        return new LeftRight(left, right);
    }
}
