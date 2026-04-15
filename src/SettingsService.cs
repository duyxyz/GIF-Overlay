using System;
using System.IO;
using System.Text.Json;

namespace GifOverlay.Wpf
{
    public class AppSettings
    {
        public int Width { get; set; } = 300;
        public int Height { get; set; } = 300;
        public double Opacity { get; set; } = 1.0;
        public bool IsLocked { get; set; } = false;
        public string? LastGifPath { get; set; }
    }

    public static class SettingsService
    {
        private static readonly string SettingsPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "settings.json");

        public static AppSettings Load()
        {
            try
            {
                if (File.Exists(SettingsPath))
                {
                    string json = File.ReadAllText(SettingsPath);
                    return JsonSerializer.Deserialize<AppSettings>(json) ?? new AppSettings();
                }
            }
            catch { }
            return new AppSettings();
        }

        public static void Save(AppSettings settings)
        {
            try
            {
                string json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(SettingsPath, json);
            }
            catch { }
        }
    }
}
