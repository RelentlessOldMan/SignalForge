namespace SignalForge;

public static partial class Measurements
{
    /// <summary>The Chao-Wang-Jost entropy of a record of whole numbers at least 0 totalling
    /// more than 1 and at most 10 000, in nats: the seen kinds through Zhang's series and the
    /// unseen through the singletons and doubletons (conventions: the Chao-Wang-Jost entropy;
    /// ADR 0562).</summary>
    /// <param name="samples">Whole numbers at least 0, totalling more than 1 and at most
    /// 10 000.</param>
    /// <returns>The Chao-Wang-Jost entropy in nats.</returns>
    /// <exception cref="ArgumentException">An argument is out of range.</exception>
    public static double ChaoWangJostEntropy(ReadOnlySpan<double> samples)
    {
        int n = samples.Length;
        if (n < 1)
            throw new ArgumentException("samples must not be empty", nameof(samples));
        double total = 0;
        foreach (double v in samples)
        {
            if (!double.IsFinite(v))
                throw new ArgumentException("samples must be finite", nameof(samples));
            if (v < 0)
                throw new ArgumentException("samples must be at least 0", nameof(samples));
            if (v != Math.Floor(v))
                throw new ArgumentException("samples must be whole numbers", nameof(samples));
            total += v;
        }
        if (!(total > 0))
            throw new ArgumentException("samples must not all be 0", nameof(samples));
        if (total > 10_000)
            throw new ArgumentException("samples must total at most 10 000", nameof(samples));
        if (!(total > 1))
            throw new ArgumentException("samples must total more than 1", nameof(samples));
        int ones = 0;
        int twos = 0;
        HashSet<int> need = new();
        foreach (double v in samples)
        {
            if (v == 1)
                ones++;
            else if (v == 2)
                twos++;
            if (v > 0 && v < total)
                need.Add((int)v - 1);
        }
        Dictionary<int, double> marks = new() { [0] = 0.0 };
        double harm = 0;
        int top = (int)total;
        for (int j = 1; j < top; j++)
        {
            harm += 1.0 / j;
            if (need.Contains(j))
                marks[j] = harm;
        }
        double acc = 0;
        foreach (double v in samples)
        {
            if (v > 0 && v < total)
                acc += v / total * (harm - marks[(int)v - 1]);
        }
        if (ones == 0)
            return acc;
        double a = twos > 0
            ? 2.0 * twos / (((total - 1.0) * ones) + (2.0 * twos))
            : 2.0 / (((total - 1.0) * (ones - 1)) + 2.0);
        double q = 1.0 - a;
        double w = 1.0;
        double part = 0;
        double rest;
        if (a * total >= 1.0)
        {
            for (int m = 0; ; m++)
            {
                double term = w / (total + m);
                if (part + term == part)
                    break;
                part += term;
                w *= q;
            }
            rest = q * part;
        }
        else
        {
            for (int step = 1; step < top; step++)
            {
                w *= q;
                part += w / step;
            }
            rest = Math.Pow(q, 1.0 - total) * (-Math.Log(a) - part);
        }
        return acc + (ones / total * rest);
    }
}
