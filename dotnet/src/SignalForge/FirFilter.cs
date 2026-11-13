using System.Numerics;

namespace SignalForge;

/// <summary>Causal direct-form FIR filter that keeps its state across chunks (conventions: FIR
/// filters). The first non-empty chunk fixes the filter as real or complex until
/// <see cref="Reset"/>.</summary>
public sealed class FirFilter
{
    private readonly double[] _taps;
    private bool? _complex;
    private double[] _realState = [];
    private Complex[] _complexState = [];

    /// <summary>A filter with the given taps and no samples seen.</summary>
    /// <param name="taps">Real taps, non-empty and finite.</param>
    public FirFilter(ReadOnlySpan<double> taps)
    {
        Dsp.CheckTaps(taps);
        _taps = taps.ToArray();
    }

    /// <summary>A copy of the taps.</summary>
    public double[] Taps => (double[])_taps.Clone();

    /// <summary>Forgets every sample seen, as if new.</summary>
    public void Reset()
    {
        _complex = null;
        _realState = [];
        _complexState = [];
    }

    /// <summary>The next <c>chunk.Length</c> output samples of a real stream.</summary>
    /// <param name="chunk">The next input samples.</param>
    public double[] Process(ReadOnlySpan<double> chunk)
    {
        if (chunk.IsEmpty)
            return [];
        Start(false, nameof(chunk));
        return Run(chunk, ref _realState);
    }

    /// <summary>The next <c>chunk.Length</c> output samples of a complex stream.</summary>
    /// <param name="chunk">The next input samples.</param>
    public Complex[] Process(ReadOnlySpan<Complex> chunk)
    {
        if (chunk.IsEmpty)
            return [];
        Start(true, nameof(chunk));
        return Run(chunk, ref _complexState);
    }

    private void Start(bool isComplex, string paramName)
    {
        if (_complex is null)
        {
            _complex = isComplex;
            if (isComplex)
                _complexState = new Complex[_taps.Length - 1];
            else
                _realState = new double[_taps.Length - 1];
        }
        else if (_complex != isComplex)
            throw new ArgumentException($"this filter takes {(_complex.Value ? "complex" : "real")} samples until Reset()", paramName);
    }

    /// <summary>Filters <paramref name="x"/> after the stored inputs and keeps the last N − 1.</summary>
    private double[] Run(ReadOnlySpan<double> x, ref double[] state)
    {
        int m = _taps.Length - 1;
        double[] ext = [.. state, .. x];
        var y = new double[x.Length];
        for (int i = 0; i < x.Length; i++)
        {
            double s = 0;
            for (int k = 0; k <= m; k++)
                s += ext[i + m - k] * _taps[k];
            y[i] = s;
        }
        state = ext[x.Length..];
        return y;
    }

    /// <summary>Complex form of <see cref="Run(ReadOnlySpan{double}, ref double[])"/>.</summary>
    private Complex[] Run(ReadOnlySpan<Complex> x, ref Complex[] state)
    {
        int m = _taps.Length - 1;
        Complex[] ext = [.. state, .. x];
        var y = new Complex[x.Length];
        for (int i = 0; i < x.Length; i++)
        {
            Complex s = Complex.Zero;
            for (int k = 0; k <= m; k++)
                s += ext[i + m - k] * _taps[k];
            y[i] = s;
        }
        state = ext[x.Length..];
        return y;
    }
}
