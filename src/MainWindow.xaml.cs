using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using WpfAnimatedGif;

namespace GifOverlay.Wpf
{
    public partial class MainWindow : Window
    {
        // - [x] Implement Pause/Play Logic
        // - [x] Add Settings Save Debounce
        // - [x] Refine Menu Grouping (Resizing/Transform)
        // - [ ] Implement NativeAOT optimization
        // - [x] Verify functionality and performance (Feature Parity)
        // - [x] Remove Aspect Ratio Lock
        private AppSettings _settings;
        private double _rotation = 0;
        private bool _flipH = false;
        private bool _flipV = false;
        private Size _originalSize = new Size(300, 300);
        private System.Windows.Threading.DispatcherTimer _saveTimer;

        public bool IsLocked 
        { 
            get => _settings.IsLocked; 
            set { 
                _settings.IsLocked = value; 
                SettingsService.Save(_settings); 
            } 
        }

        public MainWindow(string[] args = null)
        {
            InitializeComponent();
            _settings = SettingsService.Load();
            
            _saveTimer = new System.Windows.Threading.DispatcherTimer();
            _saveTimer.Interval = TimeSpan.FromMilliseconds(500);
            _saveTimer.Tick += (s, e) => {
                _saveTimer.Stop();
                SettingsService.Save(_settings);
            };

            try {
                // Sử dụng URI đầy đủ bao gồm tên Assembly để đảm bảo tìm thấy resource
                var iconUri = new Uri("pack://application:,,,/GIF-Overlay;component/assets/app_icon.ico", UriKind.RelativeOrAbsolute);
                this.Icon = BitmapFrame.Create(iconUri);
            } catch (Exception ex) {
                Console.WriteLine($"Icon load failed: {ex.Message}");
            }

            // Window Startup Location takes care of initial screen centering
            // We do not apply saved Width/Height anymore to allow each image to load natively.
            
            // Ưu tiên 1: File được truyền qua dòng lệnh (Open With)
            if (args != null && args.Length > 0 && System.IO.File.Exists(args[0]))
            {
                LoadGif(args[0]);
            }
            // Ưu tiên 2: File cuối cùng đã mở
            else if (!string.IsNullOrEmpty(_settings.LastGifPath) && System.IO.File.Exists(_settings.LastGifPath))
            {
                LoadGif(_settings.LastGifPath);
            }
            // Ưu tiên 3: Demo mặc định
            else
            {
                string demoPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "assets", "demo1.gif");
                if (System.IO.File.Exists(demoPath)) LoadGif(demoPath);
            }
        }

        public void LoadGif(string path)
        {
            try
            {
                var image = new BitmapImage();
                image.BeginInit();
                image.UriSource = new Uri(path, UriKind.Absolute);
                image.CacheOption = BitmapCacheOption.OnLoad;
                image.EndInit();
                
                ImageBehavior.SetAnimatedSource(GifImage, image);
                _originalSize = new Size(image.PixelWidth, image.PixelHeight);
                
                // Auto fit window to image size at 1:1, scale down if larger than 80% screen
                double targetW = _originalSize.Width;
                double targetH = _originalSize.Height;
                
                if (targetW > SystemParameters.PrimaryScreenWidth * 0.8 || targetH > SystemParameters.PrimaryScreenHeight * 0.8)
                {
                    double ratio = Math.Min(SystemParameters.PrimaryScreenWidth * 0.8 / targetW, SystemParameters.PrimaryScreenHeight * 0.8 / targetH);
                    targetW *= ratio;
                    targetH *= ratio;
                }

                ResizeWindow(targetW, targetH);
                
                // Center the window
                this.Left = (SystemParameters.PrimaryScreenWidth - this.Width) / 2;
                this.Top = (SystemParameters.PrimaryScreenHeight - this.Height) / 2;
                
                _settings.LastGifPath = path;
                ScheduleSave();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Failed to load GIF: {ex.Message}", "Error");
            }
        }
        public void RotateLeft()
        {
            _rotation = (_rotation - 90 + 360) % 360;
            GifRotation.Angle = _rotation;
            // Swap dimensions
            double temp = this.Width;
            this.Width = this.Height;
            this.Height = temp;
        }

        public void RotateRight()
        {
            _rotation = (_rotation + 90) % 360;
            GifRotation.Angle = _rotation;
            // Swap dimensions
            double temp = this.Width;
            this.Width = this.Height;
            this.Height = temp;
        }

        private void Rotate_Click(object sender, RoutedEventArgs e) => RotateRight();
        private void RotateLeft_Click(object sender, RoutedEventArgs e) => RotateLeft();
        private void FlipH_Click(object sender, RoutedEventArgs e) => ToggleFlipH();
        private void FlipV_Click(object sender, RoutedEventArgs e) => ToggleFlipV();
        
        private void Lock_Click(object sender, RoutedEventArgs e)
        {
            _settings.IsLocked = !_settings.IsLocked;
            SettingsService.Save(_settings);
        }

        private void Open_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Microsoft.Win32.OpenFileDialog
            {
                Filter = "GIF Files (*.gif)|*.gif",
                Title = "Select GIF File"
            };
            if (dialog.ShowDialog() == true)
            {
                LoadGif(dialog.FileName);
            }
        }

        private void Reset_Click(object sender, RoutedEventArgs e)
        {
            _rotation = 0;
            GifRotation.Angle = 0;
            _flipH = false;
            GifScale.ScaleX = 1;
            _flipV = false;
            GifScale.ScaleY = 1;
            
            double targetW = _originalSize.Width;
            double targetH = _originalSize.Height;
            
            // Scaled down if too big for screen
            if (targetW > SystemParameters.PrimaryScreenWidth * 0.8 || targetH > SystemParameters.PrimaryScreenHeight * 0.8)
            {
                double ratio = Math.Min(SystemParameters.PrimaryScreenWidth * 0.8 / targetW, SystemParameters.PrimaryScreenHeight * 0.8 / targetH);
                targetW *= ratio;
                targetH *= ratio;
            }

            ResizeWindow(targetW, targetH);
            this.Opacity = 1.0;
            _settings.Opacity = 1.0;
            ScheduleSave();
        }

        private void Pause_Click(object sender, RoutedEventArgs e)
        {
            var controller = ImageBehavior.GetAnimationController(GifImage);
            if (controller != null)
            {
                if (controller.IsPaused) controller.Play();
                else controller.Pause();
            }
        }

        private void ScheduleSave()
        {
            _saveTimer.Stop();
            _saveTimer.Start();
        }

        public void ToggleFlipH()
        {
            _flipH = !_flipH;
            GifScale.ScaleX = _flipH ? -1 : 1;
        }

        public void ToggleFlipV()
        {
            _flipV = !_flipV;
            GifScale.ScaleY = _flipV ? -1 : 1;
        }

        private void Exit_Click(object sender, RoutedEventArgs e)
        {
            _settings.Width = (int)this.Width;
            _settings.Height = (int)this.Height;
            SettingsService.Save(_settings);
            Application.Current.Shutdown();
        }

        private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (!_settings.IsLocked && e.ChangedButton == MouseButton.Left)
                this.DragMove();
        }

        private void Window_MouseWheel(object sender, MouseWheelEventArgs e)
        {
            if (Keyboard.Modifiers == ModifierKeys.Control)
            {
                double delta = e.Delta > 0 ? 1.1 : 0.9;
                ResizeWindow(this.Width * delta, this.Height * delta);
            }
        }

        private void ResizeWindow(double newW, double newH)
        {
            if (newW < 50 || newH < 50) return;
            this.Width = newW;
            this.Height = newH;
            _settings.Width = (int)newW;
            _settings.Height = (int)newH;
            ScheduleSave();
        }

        private void UpdateSliderValueText(object sender, string format)
        {
            if (sender is Slider slider && slider.Parent is Grid grid && grid.Children.Count > 2)
            {
                if (grid.Children[2] is TextBlock tb)
                    tb.Text = format;
            }
        }

        private void ScaleSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (IsLoaded && GifImage.Source is BitmapSource bs)
            {
                double ratio = (double)bs.PixelWidth / bs.PixelHeight;
                double newW = 300 * (e.NewValue / 100) * (ratio > 1 ? ratio : 1);
                double newH = 300 * (e.NewValue / 100) / (ratio < 1 ? 1 / ratio : 1);
                ResizeWindow(newW, newH);
                UpdateSliderValueText(sender, $"{(int)e.NewValue}%");
            }
        }

        private void WidthSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (IsLoaded)
            {
                ResizeWindow(e.NewValue, this.Height);
                UpdateSliderValueText(sender, $"{(int)e.NewValue}px");
            }
        }

        private void HeightSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (IsLoaded)
            {
                ResizeWindow(this.Width, e.NewValue);
                UpdateSliderValueText(sender, $"{(int)e.NewValue}px");
            }
        }

        private void OpacitySlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (IsLoaded)
            {
                this.Opacity = e.NewValue / 100.0;
                _settings.Opacity = this.Opacity;
                ScheduleSave();
                UpdateSliderValueText(sender, $"{(int)e.NewValue}%");
            }
        }
    }
}