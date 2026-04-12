using Gtk;
using AI_M_OS.SystemMonitor.Services;

namespace AI_M_OS.SystemMonitor.Widgets;

public class CpuWidget
{
    private const uint PollMs = 1000;

    private readonly Box      _container;
    private readonly Label    _usageLabel;
    private readonly LevelBar _usageBar;
    private readonly Label    _coresLabel;
    private CpuSnapshot _prev;

    public Widget Root => _container;

    public CpuWidget()
    {
        _container = Box.New(Orientation.Vertical, 8);

        var title = Label.New("⬡  CPU");
        title.AddCssClass("section-title");
        title.Halign = Align.Start;
        _container.Append(title);

        var card = Box.New(Orientation.Vertical, 6);
        card.AddCssClass("glass-card");

        // Total usage row
        var totalRow = Box.New(Orientation.Horizontal, 8);
        _usageLabel = Label.New("Usage: 0%");
        _usageLabel.AddCssClass("iface-name");
        _usageLabel.Halign = Align.Start;
        _usageLabel.Hexpand = true;
        _usageBar = LevelBar.New();
        _usageBar.Hexpand = true;
        totalRow.Append(_usageLabel);
        totalRow.Append(_usageBar);
        card.Append(totalRow);

        // Per-core summary label
        _coresLabel = Label.New("");
        _coresLabel.AddCssClass("rate-rx");
        _coresLabel.Halign = Align.Start;
        _coresLabel.Wrap = true;
        card.Append(_coresLabel);

        _container.Append(card);

        _prev = SystemMetrics.ReadCpuSnapshot();
        GLib.Functions.TimeoutAdd(0, PollMs, Tick);
    }

    private bool Tick()
    {
        var curr = SystemMetrics.ReadCpuSnapshot();
        var (total, cores) = SystemMetrics.ComputeCpuUsage(_prev, curr);
        _prev = curr;

        _usageLabel.SetText($"Usage: {total:F1}%");
        _usageBar.Value = total / 100.0;

        var summary = string.Join("  ",
            cores.Select((v, i) => $"C{i}:{v:F0}%"));
        _coresLabel.SetText(summary);

        return true;
    }
}
