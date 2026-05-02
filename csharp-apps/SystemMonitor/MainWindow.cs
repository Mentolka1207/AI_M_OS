using Gtk;
using AI_M_OS.SystemMonitor.Widgets;

namespace AI_M_OS.SystemMonitor;

public class MainWindow : Adw.ApplicationWindow, IDisposable
{
    private readonly CpuWidget       _cpuWidget;
    private readonly RamWidget       _ramWidget;
    private readonly NetworkWidget   _networkWidget;
    private readonly DiskWidget      _diskWidget;
    private readonly SchedulerWidget _schedulerWidget;   // ← новый виджет
    private bool _disposed;

    public MainWindow(Adw.Application app) : base()
    {
        Application  = app;
        Title        = "AI_M_OS System Monitor";
        DefaultWidth = 440; DefaultHeight = 900;       // +100px для нового виджета
        AddCssClass("aimos-monitor");
        LoadCss();

        var header = Adw.HeaderBar.New();
        header.AddCssClass("glass-header");
        header.TitleWidget = Label.New("System Monitor");

        var scroll = ScrolledWindow.New();
        scroll.Vexpand = true;
        scroll.HscrollbarPolicy = PolicyType.Never;

        _cpuWidget       = new CpuWidget();
        _ramWidget       = new RamWidget();
        _networkWidget   = new NetworkWidget();
        _diskWidget      = new DiskWidget();
        _schedulerWidget = new SchedulerWidget();
        _schedulerWidget = new SchedulerWidget();
        _schedulerWidget = new SchedulerWidget();

        var content = Box.New(Orientation.Vertical, 16);
        content.AddCssClass("content-box");
        content.Append(_cpuWidget.Root);
        content.Append(_ramWidget.Root);
        content.Append(_networkWidget.Root);
        content.Append(_diskWidget.Root);
        content.Append(_schedulerWidget.Root);
        content.Append(_schedulerWidget.Root);
        content.Append(_schedulerWidget.Root);   // ← добавлен последним

        scroll.Child = content;

        var root = Box.New(Orientation.Vertical, 0);
        root.Append(header);
        root.Append(scroll);

        Content = root;
        OnCloseRequest += (_, _) => { Dispose(); return false; };
    }

    public new void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _cpuWidget.Dispose();
        _ramWidget.Dispose();
        _networkWidget.Dispose();
        _diskWidget.Dispose();
        _schedulerWidget.Dispose();
        _schedulerWidget.Dispose();
        _schedulerWidget.Dispose();
    }

    private static void LoadCss()
    {
        var provider = CssProvider.New();
        var cssPath  = Path.Combine(AppContext.BaseDirectory, "themes", "glassmorphism.css");
        if (File.Exists(cssPath))
            provider.LoadFromPath(cssPath);
        else
            provider.LoadFromString(
                "window.aimos-monitor{background:rgba(12,12,24,.82)}" +
                ".glass-card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:14px;padding-bottom:8px}" +
                ".section-title{font-size:10px;font-weight:700;letter-spacing:2px;color:rgba(255,255,255,.35)}" +
                ".iface-name{font-size:13px;font-weight:600;color:rgba(255,255,255,.88)}" +
                ".rate-rx{color:#33d9e0;font-size:12px;min-width:110px}" +
                ".rate-tx{color:#ff8c35;font-size:12px;min-width:110px}" +
                ".content-box{padding:20px 16px}");
        Gtk.StyleContext.AddProviderForDisplay(
            Gdk.Display.GetDefault()!,
            provider,
            Gtk.Constants.STYLE_PROVIDER_PRIORITY_APPLICATION);
    }
}
