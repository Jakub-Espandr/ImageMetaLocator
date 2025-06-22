<p align="center">
  <a href="https://i.ibb.co/c0GTpZF/icon.png">
    <img src="https://i.ibb.co/c0GTpZF/icon.png" alt="Image Meta Locator Logo" width="220"/>
  </a>
</p>

<h1 align="center">Image Meta Locator</h1>
<p align="center"><em>(Born4Flight | FlyCamCzech)</em></p>

---

## 🗺️ Overview

**Image Meta Locator** is a lightweight desktop tool for extracting GPS metadata and visualizing photo locations on an interactive map. Designed with performance and elegance in mind, it supports drag-and-drop workflows, reverse geocoding, and smooth UI interaction for reviewing image coordinates, dates, and location data.

---

## ✨ Features

- **Modern GUI**  
  - Responsive interface built with PySide6  
  - Clean split-view layout using custom fonts and icons

- **Drag & Drop Support**  
  - Effortlessly drag `.jpg`, `.tiff`, or `.dng` files into the app window

- **Image Preview**  
  - Instantly view the selected photo before extracting metadata

- **Interactive Map**  
  - Built-in OpenStreetMap viewer shows the GPS location with a pinpoint

- **Reverse Geocoding**  
  - Converts coordinates into a human-readable address using `geopy`

- **Click-to-Copy**  
  - Copy full address, photo date, or coordinates with a single click

- **Coordinate Format Toggle**  
  - Switch between decimal and WGS 84 (degrees, minutes, seconds) formats
  - Interactive button for real-time format switching

- **PDF Export**  
  - Generate professional PDF reports with original image, metadata, and location map
  - High-quality output with custom fccTYPO fonts
  - Single file export for easy sharing and archiving

- **Smart Address Formatting**  
  - Automatic two-line formatting for better readability
  - Intelligent natural break detection

- **Live Connection Status**  
  - Status bar shows whether online services (map, geocoder) are available

- **Optimized Performance**  
  - Uses lazy loading and background threads for smooth, non-blocking operation

---

## 🧭 Extracted Metadata

- **File Information**  
  - Filename and file format

- **GPS Data**  
  - Latitude, longitude, altitude (if available)

- **Location**  
  - Reverse-geocoded address from coordinates

- **Date/Time**  
  - Original photo capture date from EXIF

---

## 📦 Requirements

- Python 3.8+
- PySide6 >= 6.5.0  
- PySide6-WebEngine >= 6.5.0  
- Pillow >= 9.0.0  
- rawpy >= 0.17.0  
- exifread >= 3.0.0  
- geopy >= 2.3.0  
- requests >= 2.28.0  
- reportlab >= 4.0.0

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Jakub-Espandr/ImageMetaLocator.git
cd ImageMetaLocator

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

---

## 🛠️ Usage

1. Start the app with `python main.py`
2. Drag a supported image into the window, or use the file picker
3. View metadata, map, and reverse-geocoded address
4. **Copy coordinates**: Click on coordinates to copy them to clipboard
5. **Toggle coordinate format**: Use the WGS 84 button to switch between decimal and degrees/minutes/seconds format
6. **Export PDF**: Click "Export Results" to generate a professional PDF report with the image, metadata, and location map

---

## 📁 Project Structure

```
ImageMetaLocator/
├── main.py
├── core/              # Core functionality (metadata, export)
├── ui/                # PySide6 GUI components
├── utils/             # Helpers (resources, configuration)
├── assets/            # Icons, fonts, and styling
├── requirements.txt
└── LICENSE
```

---

## 🔐 License

This project is licensed under the **Non-Commercial Public License (NCPL v1.0)**  
© 2025 Jakub Ešpandr – Born4Flight, FlyCamCzech

See the [LICENSE](https://github.com/Jakub-Espandr/ImageMetaLocator/raw/main/LICENSE) file for full terms.

---

## 🙏 Acknowledgments

- Built with ❤️ using PySide6, Pillow, rawpy, exifread, geopy, and reportlab
