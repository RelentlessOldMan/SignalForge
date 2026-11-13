using System.Numerics;

namespace SignalForge;

/// <summary>Causal cascade of second-order sections that keeps its state across chunks
/// (conventions: IIR filters). The first non-empty chunk fixes the filter as real or complex until
/// <see cref="Reset"/>.</summary>
public sealed class IirFilter
{
    private readonly double[][] _sos;
    private bool? _complex;
    private double[][] _realState = [];
    private Complex[][] _complexState = [];

    /// <summary>A filter with the given sections and no samples seen.</summary>
    /// <param name="sos">Sections <c>[b0, b1, b2, a0, a1, a2]</c>, at least one, finite, a0 ≠ 0.</param>
    public IirFilter(double[][] sos) => _sos = Dsp.CheckSos(sos);

    /// <summary>A copy of the sections, each with a0 = 1.</summary>
    public double[][] Sections => [.. _sos.Select(r => (double[])r.Clone())];

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
        double[] y = chunk.ToArray();
        for (int j = 0; j < _sos.Length; j++)
        {
            double[] c = _sos[j], st = _realState[j];
            double s1 = st[0], s2 = st[1]; // transposed direct form II
            for (int i = 0; i < y.Length; i++)
            {
                double v = y[i], o = c[0] * v + s1;
                s1 = c[1] * v - c[4] * o + s2;
                s2 = c[2] * v - c[5] * o;
                y[i] = o;
            }
            (st[0], st[1]) = (s1, s2);
        }
        return y;
    }

    /// <summary>The next <c>chunk.Length</c> output samples of a complex stream.</summary>
    /// <param name="chunk">The next input samples.</param>
    public Complex[] Process(ReadOnlySpan<Complex> chunk)
    {
        if (chunk.IsEmpty)
            return [];
        Start(true, nameof(chunk));
        Complex[] y = chunk.ToArray();
        for (int j = 0; j < _sos.Length; j++)
        {
            double[] c = _sos[j];
            Complex[] st = _complexState[j];
            Complex s1 = st[0], s2 = st[1];
            for (int i = 0; i < y.Length; i++)
            {
                Complex v = y[i], o = c[0] * v + s1;
                s1 = c[1] * v - c[4] * o + s2;
                s2 = c[2] * v - c[5] * o;
                y[i] = o;
            }
            (st[0], st[1]) = (s1, s2);
        }
        return y;
    }

    private void Start(bool isComplex, string paramName)
    {
        if (_complex is null)
        {
            _complex = isComplex;
            if (isComplex)
                _complexState = [.. _sos.Select(_ => new Complex[2])];
            else
                _realState = [.. _sos.Select(_ => new double[2])];
        }
        else if (_complex != isComplex)
            throw new ArgumentException($"this filter takes {(_complex.Value ? "complex" : "real")} samples until Reset()", paramName);
    }
}
