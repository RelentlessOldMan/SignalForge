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

/// <summary>Which channel <see cref="Dsp.Haas"/> delays (conventions: Haas widener;
/// ADR 0276).</summary>
public enum StereoSide
{
    /// <summary>The left channel.</summary>
    Left,

    /// <summary>The right channel.</summary>
    Right,
}

/// <summary>How <see cref="Dsp.Pan"/> splits a mono signal (conventions: Panner;
/// ADR 0265).</summary>
public enum PanLaw
{
    /// <summary><c>gL = cos θ</c>, <c>gR = sin θ</c>, <c>θ = (position + 1)·π/4</c>.</summary>
    ConstantPower,

    /// <summary><c>gL = (1 − position)/2</c>, <c>gR = (1 + position)/2</c>.</summary>
    Linear,
}

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

    /// <summary>Pans a mono signal to left and right, <paramref name="position"/> from −1 (left)
    /// to 1 (right) (conventions: Panner; ADR 0265).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="position">From −1 (hard left) to 1 (hard right).</param>
    /// <param name="law">The pan law.</param>
    /// <returns>The left and right channels.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LeftRight Pan(ReadOnlySpan<double> samples, double position, PanLaw law = PanLaw.ConstantPower)
    {
        if (!double.IsFinite(position) || position < -1 || position > 1)
            throw new ArgumentOutOfRangeException(nameof(position), "position must be from -1 to 1");
        CheckPanLaw(law);
        (double gl, double gr) = PanGains(position, law);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        var left = new double[samples.Length];
        var right = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            left[n] = v * gl;
            right[n] = v * gr;
        }
        return new LeftRight(left, right);
    }

    /// <summary>Scales the side channel by <paramref name="width"/>: 0 is mono, 1 unchanged
    /// (conventions: Stereo width; ADR 0267).</summary>
    /// <param name="left">The left channel, finite, at least one sample.</param>
    /// <param name="right">The right channel, finite, the same length.</param>
    /// <param name="width">The side gain, finite and at least 0.</param>
    /// <returns>The left and right channels.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LeftRight StereoWidth(ReadOnlySpan<double> left, ReadOnlySpan<double> right, double width)
    {
        if (!double.IsFinite(width) || width < 0)
            throw new ArgumentOutOfRangeException(nameof(width), "width must be at least 0");
        if (left.IsEmpty)
            throw new ArgumentException("left must not be empty", nameof(left));
        if (right.Length != left.Length)
            throw new ArgumentException("left and right must have the same length", nameof(right));
        var outLeft = new double[left.Length];
        var outRight = new double[left.Length];
        for (int n = 0; n < left.Length; n++)
        {
            double a = left[n], b = right[n];
            if (!double.IsFinite(a))
                throw new ArgumentException("left must be finite", nameof(left));
            if (!double.IsFinite(b))
                throw new ArgumentException("right must be finite", nameof(right));
            double m = (a + b) / 2, s = (a - b) / 2 * width;
            outLeft[n] = m + s;
            outRight[n] = m - s;
        }
        return new LeftRight(outLeft, outRight);
    }

    /// <summary>Pans a mono signal under a cosine LFO, position
    /// <c>depth·cos((2π·rate)·(n/fs))</c> (conventions: Auto-panner; ADR 0270).</summary>
    /// <param name="samples">Finite samples, at least one.</param>
    /// <param name="rate">The LFO frequency, Hz, finite.</param>
    /// <param name="depth">The swing either side of centre, 0 to 1.</param>
    /// <param name="sampleRate">The sample rate, Hz, finite and positive.</param>
    /// <param name="law">The pan law.</param>
    /// <returns>The left and right channels.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LeftRight AutoPan(ReadOnlySpan<double> samples, double rate, double depth, double sampleRate, PanLaw law = PanLaw.ConstantPower)
    {
        if (!double.IsFinite(depth) || depth < 0 || depth > 1)
            throw new ArgumentOutOfRangeException(nameof(depth), "depth must be in [0, 1]");
        CheckPanLaw(law);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double[] c = RingCarrier(samples.Length, rate, sampleRate, 0);
        var left = new double[samples.Length];
        var right = new double[samples.Length];
        for (int n = 0; n < samples.Length; n++)
        {
            double v = samples[n];
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            (double gl, double gr) = PanGains(depth * c[n], law);
            left[n] = v * gl;
            right[n] = v * gr;
        }
        return new LeftRight(left, right);
    }

    private static void CheckPanLaw(PanLaw law)
    {
        if (!Enum.IsDefined(law))
            throw new ArgumentOutOfRangeException(nameof(law), "law must be ConstantPower or Linear");
    }

    private static (double Left, double Right) PanGains(double position, PanLaw law)
    {
        if (law == PanLaw.Linear)
            return ((1 - position) / 2, (1 + position) / 2);
        double theta = (position + 1) * (Math.PI / 4);
        return (Math.Cos(theta), Math.Sin(theta));
    }

    /// <summary>Echoes every <paramref name="delay"/> samples that alternate left and right,
    /// each bounce scaled by <paramref name="feedback"/>, mixed with the dry signal
    /// (conventions: Ping-pong delay; ADR 0275).</summary>
    /// <param name="samples">Real, finite mono samples, at least one.</param>
    /// <param name="delay">The echo spacing, samples, at least 1.</param>
    /// <param name="feedback">The gain per bounce, finite, magnitude below 1.</param>
    /// <param name="mix">The wet share, 0 to 1.</param>
    /// <returns>The left and right channels, each as long as the input.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LeftRight PingPongDelay(ReadOnlySpan<double> samples, int delay, double feedback, double mix)
    {
        if (delay < 1)
            throw new ArgumentOutOfRangeException(nameof(delay), "delay must be at least 1");
        if (!double.IsFinite(feedback) || !(Math.Abs(feedback) < 1))
            throw new ArgumentOutOfRangeException(nameof(feedback), "feedback must be in (-1, 1)");
        CheckMix(mix);
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        int len = samples.Length;
        var a = new double[len];
        var b = new double[len];
        for (int n = delay; n < len; n++)
        {
            a[n] = samples[n - delay] + feedback * b[n - delay];
            b[n] = feedback * a[n - delay];
        }
        var left = new double[len];
        var right = new double[len];
        for (int n = 0; n < len; n++)
        {
            double dry = samples[n] * (1 - mix);
            left[n] = dry + a[n] * mix;
            right[n] = dry + b[n] * mix;
        }
        return new LeftRight(left, right);
    }

    /// <summary>A mono signal on both sides, one side <paramref name="delay"/> samples late
    /// (conventions: Haas widener; ADR 0276).</summary>
    /// <param name="samples">Real, finite mono samples, at least one.</param>
    /// <param name="delay">The delay of the late side, samples, at least 0.</param>
    /// <param name="side">The side to delay.</param>
    /// <returns>The left and right channels, each as long as the input.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LeftRight Haas(ReadOnlySpan<double> samples, int delay, StereoSide side = StereoSide.Right)
    {
        if (delay < 0)
            throw new ArgumentOutOfRangeException(nameof(delay), "delay must be at least 0");
        if (side is not (StereoSide.Left or StereoSide.Right))
            throw new ArgumentOutOfRangeException(nameof(side), "side must be Left or Right");
        if (samples.IsEmpty)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
        }
        double[] dry = samples.ToArray();
        var late = new double[samples.Length];
        for (int n = delay; n < samples.Length; n++)
            late[n] = samples[n - delay];
        return side == StereoSide.Left ? new LeftRight(late, dry) : new LeftRight(dry, late);
    }

    /// <summary>Turns down the side away from <paramref name="position"/> by
    /// <c>1 − |position|</c>; the near side is unchanged (conventions: Stereo balance;
    /// ADR 0277).</summary>
    /// <param name="left">Real, finite left samples, at least one.</param>
    /// <param name="right">Real, finite right samples, as many as <paramref name="left"/>.</param>
    /// <param name="position">From −1 (left only) through 0 (unchanged) to 1 (right only).</param>
    /// <returns>The balanced left and right channels.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static LeftRight Balance(ReadOnlySpan<double> left, ReadOnlySpan<double> right, double position)
    {
        if (!double.IsFinite(position) || position < -1 || position > 1)
            throw new ArgumentOutOfRangeException(nameof(position), "position must be from -1 to 1");
        if (left.IsEmpty)
            throw new ArgumentException("left must not be empty", nameof(left));
        if (right.Length != left.Length)
            throw new ArgumentException("left and right must have the same length", nameof(right));
        double gl = position > 0 ? 1 - position : 1.0;
        double gr = position < 0 ? 1 + position : 1.0;
        var outLeft = new double[left.Length];
        var outRight = new double[left.Length];
        for (int n = 0; n < left.Length; n++)
        {
            if (!double.IsFinite(left[n]))
                throw new ArgumentException("left must be finite", nameof(left));
            if (!double.IsFinite(right[n]))
                throw new ArgumentException("right must be finite", nameof(right));
            outLeft[n] = left[n] * gl;
            outRight[n] = right[n] * gr;
        }
        return new LeftRight(outLeft, outRight);
    }
}
