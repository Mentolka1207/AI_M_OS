using Gtk;

using AI_M_OS.SystemMonitor.Services;



namespace AI_M_OS.SystemMonitor.Widgets;



public class CpuWidget : IDisposable

{

    private const uint PollMs = 1000;

    private readonly Box      _container;

    private readonly Label    _usageLabel;

    private readonly LevelBar _usageBar;

    private readonly Label    _coresLabel;

    private CpuSnapshot _prev;

    private uint _timerId;

    private bool _disposed;



    public Widget Root => _container;



    public CpuWidget()

    {

        _container = Box.New(Orientation.Vertical, 8);

        var title = Label.New("o  CPU");

        title.AddCssClass("section-title");

        title.Halign = Align.Start;

        _container.Append(title);

        var card = Box.New(Orientation.Vertical, 6);

        card.AddCssClass("glass-card");

        var totalRow = Box.New(Orientation.Horizontal, 8);

        _usageLabel = Label.New("Usage: 0%");

        _usageLabel.AddCssClass("iface-name");        _usageLabel.Halign = Align.Start;
        _usageLabel.Hexpand = true;
        _usageBar = LevelBar.New();
        _usageBar.Hexpand = true;
        totalRow.Append(_usageLabel);
        totalRow.Append(_usageBar);
        card.Append(totalRow);
        _coresLabel = Label.New("");
        _coresLabel.AddCssClass("rate-rx");
        _coresLabel.Halign = Align.Start;
        _coresLabel.Wrap = true;
        card.Append(_coresLabel);
        _container.Append(card);
        _prev = SystemMetrics.ReadCpuSnapshot();
        _timerId = GLib.Functions.TimeoutAdd(0, PollMs, Tick);
    }

    private bool Tick()
    {
        try
        {
            var curr = SystemMetrics.ReadCpuSnapshot();
            var (total, cores) = SystemMetrics.ComputeCpuUsage(_prev, curr);
            _prev = curr;
            _usageLabel.SetText("Usage: " + total.ToString("F1") + "%");
            _usageBar.Value = Math.Clamp(total / 100.0, 0.0, 1.0);
            var summary = cores is null ? "N/A"
                : string.Join("  ", cores.Select((v, i) => "C" + i + ":" + v.ToString("F0") + "%"));
            _coresLabel.SetText(summary);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("[CpuWidget] Tick error: " + ex.Message);
        }
        return true;
    }
    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        if (_timerId != 0) { GLib.Functions.SourceRemove(_timerId); _timerId = 0; }
    }
}
