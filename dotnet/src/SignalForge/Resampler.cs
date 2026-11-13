using System.Numerics;

namespace SignalForge;

/// <summary>Causal rational resampler that keeps its state across chunks (conventions: Resampling,
/// Streaming resampling; ADR 0027). Its stream is <see cref="Dsp.Resample(ReadOnlySpan{double}, int, int, double[])"/>
/// with the taps delayed by N − 1. The first non-empty chunk fixes the stream as real or complex
/// until <see cref="Reset"/>.</summary>
public sealed class Resampler
{
    private readonly double[] _taps;
    private readonly int _l, _m, _t;
    private readonly double[][] _poly; // row p: L·h[p + t·L], t = 0 … T − 1
    private bool? _complex;
    private long _count, _next;
    private double[] _realHistory = [];
    private Complex[] _complexHistory = [];

    /// <summary>A resampler by <paramref name="up"/>/<paramref name="down"/> with no samples seen.</summary>
    /// <param name="up">Up-sampling factor, at least 1.</param>
    /// <param name="down">Down-sampling factor, at least 1.</param>
    /// <param name="taps">Real taps, non-empty and finite, any length; null for
    /// <see cref="Dsp.ResampleTaps"/> (or a copy when the factors reduce to 1/1).</param>
    public Resampler(int up, int down, double[]? taps = null)
    {
        (_l, _m) = Dsp.Factors(up, down);
        if (taps is null)
            _taps = _l == 1 && _m == 1 ? [1.0] : Dsp.ResampleTaps(_l, _m);
        else
        {
            Dsp.CheckTaps(taps);
            _taps = (double[])taps.Clone();
        }
        _t = (_taps.Length + _l - 1) / _l;
        _poly = new double[_l][];
        for (int p = 0; p < _l; p++)
        {
            _poly[p] = new double[_t];
            for (int t = 0; t < _t && p + t * _l < _taps.Length; t++)
                _poly[p][t] = _l * _taps[p + t * _l];
        }
    }

    /// <summary>A copy of the taps.</summary>
    public double[] Taps => (double[])_taps.Clone();

    /// <summary>Forgets every sample seen, as if new.</summary>
    public void Reset()
    {
        _complex = null;
        _count = _next = 0;
        _realHistory = [];
        _complexHistory = [];
    }

    /// <summary>Every output whose last input is in the chunk: ⌈n·L/M⌉ in all after n inputs.</summary>
    /// <param name="chunk">The next input samples.</param>
    public double[] Process(ReadOnlySpan<double> chunk)
    {
        if (chunk.IsEmpty)
            return [];
        Start(false, nameof(chunk));
        double[] buf = [.. _realHistory, .. chunk];
        var y = new double[Outputs(chunk.Length)];
        for (int i = 0; i < y.Length; i++)
        {
            var (p, at) = Position(i);
            double s = 0;
            for (int t = 0; t < _t; t++)
                s += _poly[p][t] * buf[at - t];
            y[i] = s;
        }
        _realHistory = buf[^(_t - 1)..];
        Advance(chunk.Length, y.Length);
        return y;
    }

    /// <summary>Every output whose last input is in the chunk: ⌈n·L/M⌉ in all after n inputs.</summary>
    /// <param name="chunk">The next input samples.</param>
    public Complex[] Process(ReadOnlySpan<Complex> chunk)
    {
        if (chunk.IsEmpty)
            return [];
        Start(true, nameof(chunk));
        Complex[] buf = [.. _complexHistory, .. chunk];
        var y = new Complex[Outputs(chunk.Length)];
        for (int i = 0; i < y.Length; i++)
        {
            var (p, at) = Position(i);
            Complex s = Complex.Zero;
            for (int t = 0; t < _t; t++)
                s += _poly[p][t] * buf[at - t];
            y[i] = s;
        }
        _complexHistory = buf[^(_t - 1)..];
        Advance(chunk.Length, y.Length);
        return y;
    }

    private void Start(bool isComplex, string paramName)
    {
        if (_complex is null)
        {
            _complex = isComplex;
            if (isComplex)
                _complexHistory = new Complex[_t - 1];
            else
                _realHistory = new double[_t - 1];
        }
        else if (_complex != isComplex)
            throw new ArgumentException($"this resampler takes {(_complex.Value ? "complex" : "real")} samples until Reset()", paramName);
    }

    /// <summary>How many outputs a chunk of <paramref name="n"/> inputs completes.</summary>
    private int Outputs(int n) => (int)(((_count + n) * _l + _m - 1) / _m - _next);

    /// <summary>The phase of the i-th new output and the buffer index of its last input; the buffer
    /// starts T − 1 samples before the chunk.</summary>
    private (int Phase, int At) Position(int i)
    {
        long mm = (_next + i) * _m;
        return ((int)(mm % _l), (int)(mm / _l - _count + _t - 1));
    }

    private void Advance(int inputs, int outputs)
    {
        _count += inputs;
        _next += outputs;
    }
}
