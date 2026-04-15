[![Download GIF-Overlay](https://img.shields.io/sourceforge/dt/gif-overlay.svg)](https://sourceforge.net/projects/gif-overlay/files/latest/download) [![Download GIF-Overlay](https://img.shields.io/sourceforge/dm/gif-overlay.svg)](https://sourceforge.net/projects/gif-overlay/files/latest/download)[![Download GIF-Overlay](https://img.shields.io/sourceforge/dw/gif-overlay.svg)](https://sourceforge.net/projects/gif-overlay/files/latest/download)[![Download GIF-Overlay](https://img.shields.io/sourceforge/dd/gif-overlay.svg)](https://sourceforge.net/projects/gif-overlay/files/latest/download)
# GIF Overlay - Minimalist GIF & Image Viewer

**GIF Overlay** is a lightweight, high-performance GIF and static image viewer for Windows, built with **C# WPF**. It focuses on minimalism, efficiency, and a premium aesthetic, allowing you to pin images on top of other windows with a unique translucency effect.

![GIF Overlay Demo](src/assets/demo1.gif)

## ✨ Key Features

- **Native C# WPF:** High performance with modern Windows 11 aesthetics.
- **Always on Top:** Pin images over other applications—perfect for tracing, references, or desktop decoration.
- **Translucent Background:** Fully transparent window borders, showing only the image content.
- **Adjustable Opacity:** Slide to adjust transparency for a see-through effect.
- **Flexible Transforms:** 
    - Rotate Left/Right (90° increments).
    - Flip Horizontally/Vertically.
- **Dynamic Resizing:** 
    - Scale via Ctrl + Mouse Wheel.
    - Precise adjustments via Width/Height sliders in the context menu.
- **High DPI Support:** Crisp rendering on all displays (4K, high-scale laptops).
- **Settings Persistence:** Remembers your last opened GIF, window size, and opacity.

## 🚀 How to Use

### Installation
1. Download `GIF-Overlay-Setup.exe` from the Releases section (coming soon).
2. Run the installer to register the application.
3. Right-click any `.gif` file -> **Open With** -> Select **GIF Overlay**.

### Controls
- **Move:** Left-click and drag the image (ensure window is unlocked).
- **Resize:** `Ctrl + Mouse Wheel` to scale or use sliders in Settings.
- **Context Menu (Right-Click):**
    - **Lock Window:** Prevent accidental moving or resizing.
    - **Change GIF...:** Select a different file.
    - **Settings:** Access Resizing (Scale, W, H, Opacity) and Transform (Rotate, Flip).
    - **Pause / Play:** Toggle GIF animation.
    - **Reset to Default:** Restore original size and transforms.
    - **Exit:** Close the application.

## 🛠 Development

To build from source:

1. Install **Visual Studio 2022** or **.NET 10 SDK**.
2. Clone the repository.
3. Open `src/GifOverlay.Wpf.csproj`.
4. Build and run:
   ```bash
   dotnet run --project src
   ```

## 📜 License
Released under the MIT License. Feel free to use and customize!

---
Developed by **DuyXYZ**

