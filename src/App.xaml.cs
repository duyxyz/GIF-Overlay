using System.Configuration;
using System.Data;
using System.Windows;

namespace GifOverlay.Wpf;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        this.DispatcherUnhandledException += (s, ex) => {
            try {
                System.IO.File.WriteAllText("crash_log.txt", ex.Exception.ToString());
            } catch { }
            MessageBox.Show(ex.Exception.Message, "Fatal Error");
        };
    }
}

