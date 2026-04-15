[![Download GIF-Overlay](https://img.shields.io/sourceforge/dt/gif-overlay.svg)](https://sourceforge.net/projects/gif-overlay/files/latest/download) [![Download GIF-Overlay](https://img.shields.io/sourceforge/dm/gif-overlay.svg)](https://sourceforge.net/projects/gif-overlay/files/latest/download)[![Download GIF-Overlay](https://img.shields.io/sourceforge/dw/gif-overlay.svg)](https://sourceforge.net/projects/gif-overlay/files/latest/download)[![Download GIF-Overlay](https://img.shields.io/sourceforge/dd/gif-overlay.svg)](https://sourceforge.net/projects/gif-overlay/files/latest/download)
# GIF Overlay - Minimalist GIF & Image Viewer

**GIF Overlay** is a lightweight, high-performance GIF and static image viewer for Windows. It focuses on minimalism, efficiency, and a premium aesthetic, allowing you to pin images on top of other windows with a unique translucency effect.

![GIF Overlay Demo](demo1.gif)

## ✨ Key Features

- **Native UI (PyQt5):** Instant startup with extremely low system resource usage.
- **Always on Top:** Pin images over other applications—perfect for tracing, references, or desktop decoration.
- **Translucent Background:** Fully transparent window borders, showing only the image content.
- **Flexible Adjustments:** 
    - Change dimensions (Scale, Width, Height) directly from the context menu.
    - Adjust Opacity for a see-through effect.
    - Fast Rotation and Flipping (Horizontal/Vertical).
- **High DPI Support:** Crisp rendering on all displays (4K, high-scale laptops).
- **Windows Integration:** Supports "Open With" from File Explorer and can be registered as the default GIF viewer.

## 🚀 How to Use

### Installation
1. Download `GIF-Overlay-Setup.exe` from the Releases section.
2. Run the installer to register the application with your system.
3. Right-click any `.gif` file -> **Open With** -> Select **GIF Overlay** (you can check "Always" to make it default).

### Controls
- **Move:** Left-click and drag the image to move it.
- **Right-Click Menu:** Right-click the image to open the control panel:
    - **Lock Window:** Prevent accidental moving or resizing.
    - **Change GIF...:** Select a different image file.
    - **Settings:** Adjust size, opacity, rotation, and flip states.
    - **Pause / Play:** Toggle GIF animation.
    - **Quit Application:** Exit the app.

## 🛠 Development

To run from source:

1. Install Python 3.x.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python "GIF Overlay.py"
   ```

## 📜 License
Released under the MIT License. Feel free to use and customize!

---
Developed by **DuyXYZ**
