using Gtk;
using AI_M_OS.SystemMonitor.Services;

namespace AI_M_OS.SystemMonitor.Widgets;

public class RamWidget
{
    private const uint PollMs = 2000;

    private readonly Box      _container;
    private readonly Label    _ramLabel;
    private readonly LevelBar _ramBar;
    private readonly Label    _swapLabel;
    private readonly LevelBar _swapBar;

    public Widget Root => _container;

    public RamWidget()
    {
        _container = Box.New(Orientation.Vertical, 8);

        var title = Label.New("⬡  MEMORY");
        title.AddCssClass("section-title");
        title.Halign = Align.Start;
        _container.Append(title);

        var card = Box.New(Orientation.Vertical, 6);
        card.AddCssClass("glass-card");

        // RAM row
        var ramRow = Box.New(Orientation.Horizontal, 8);
        _ramLabel = Label.New("RAM: 0 MB / 0 MB");
        _ramLabel.AddCssClass("iface-name");
        _ramLabel.Halign = Align.Start;
        _ramLabel.Hexpand = true;
        _ramBar = LevelBar.New();
        _ramBar.Hexpand = true;
        ramRow.Append(_ramLabel);
        ramRow.Append(_ramBar);
        card.Append(ramRow);

        // Swap row
        var swapRow = Box.New(Orientation.Horizontal, 8);
        _swapLabel = Label.New("Swap: 0 MB / 0 MB");
        _swapLabel.AddCssClass("rate-tx");
        _swapLabel.Halign = Align.Start;
        _swapLabel.Hexpand = true;
        _swapBar = LevelBar.New();
        _swapBar.Hexpand = true;
        swapRow.Append(_swapLabel);
        swapRow.Append(_swapBar);
        card.Append(swapRow);

        _container.Append(card);
        GLib.Functions.TimeoutAdd(0, PollMs, Tick);
    }

    private bool Tick()
    {
        var mem = SystemMetrics.ReadMemInfo();

        _ramLabel.SetText(
            $"RAM: {FormatMb(mem.UsedKb)} / {FormatMb(mem.TotalKb)}");
        _ramBar.Value = mem.TotalKb > 0
            ? (double)mem.UsedKb / mem.TotalKb : 0;

        _swapLabel.SetText(
            $"Swap: {FormatMb(mem.SwapUsedKb)} / {FormatMb(mem.SwapTotalKb)}");
        _swapBar.Value = mem.SwapTotalKb > 0
            ? (double)mem.SwapUsedKb / mem.SwapTotalKb : 0;

        return true;
    }

    private static string FormatMb(long kb) =>
        kb >= 1_048_576 ? $"{kb / 1_048_576.0:F1} GB"
        : kb >= 1_024   ? $"{kb / 1_024.0:F0} MB"
        : $"{kb} KB";
}
