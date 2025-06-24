<p align="center">
  <a href="https://i.ibb.co/c0GTpZF/icon.png">
    <img src="https://i.ibb.co/c0GTpZF/icon.png" alt="Image Meta Locator Logo" width="220"/>
  </a>
</p>

<h1 align="center">Image Meta Locator</h1>
<p align="center"><em>(Born4Flight | FlyCamCzech)</em></p>

<p align="center">
  <a href="https://ibb.co/KShNYM2">
    <img src="https://i.ibb.co/7LCgHwn/Image-Meta-Locator.png" alt="UAV AreaCalc Image Meta Locator Interface" width="50%"/>
  </a>
</p>

## 🗺️ Overview

**Image Meta Locator** is a lightweight desktop tool for extracting GPS metadata and visualizing photo locations on an interactive map. Designed with performance and elegance in mind, it supports drag-and-drop workflows, reverse geocoding, and smooth UI interaction for reviewing image coordinates, dates, and location data.

---

## ✨ Features

### 🚁 **Flight Height Analysis & Recalculation**
- **Automatic Height Calculation**: Calculate actual drone height above terrain using GPS altitude and terrain elevation data
- **Negative Height Detection**: Automatic detection and warning for inaccurate flight height data
- **TIFF Orthomosaic Support**: Upload orthomosaic TIFF files to extract actual map resolution for accurate calculations
- **DJI Drone Presets**: Pre-configured drone models with accurate GSD values:
  - DJI Phantom 4 PRO (1.36 cm/px at 50m)
  - DJI Phantom 4 (2.19 cm/px at 50m)
  - DJI Mavic 2 PRO (1.17 cm/px at 50m)
  - DJI Mavic 2 ZOOM (1.82 cm/px at 50m)
- **Custom Drone Setup**: Manual input for reference height and GSD values
- **Ratio-Based Calculation**: Professional photogrammetry formula: `Height = (Map_GSD / Drone_GSD) × Drone_Height`
- **Manual Height Adjustment**: Override calculated heights when they're incorrect (e.g., showing 3m instead of actual height)
- **Manual Recalculation Button**: "🔧 Recalculate" button available anytime, not just for negative heights

### 🎨 **Modern Interface**
- **Light Theme**: Clean, professional white background design throughout
- **Modern GUI**: Responsive interface built with PySide6  
- **Professional Dialogs**: Clean, modern height recalculation dialog with proper styling
- **Visual Indicators**: Clear distinction between calculated and manually adjusted heights
- **Enhanced Status Messages**: Better feedback for recalculation actions

### 📁 **File Handling**
- **Drag & Drop Support**: Effortlessly drag `.jpg`, `.tiff`, `.dng` files into the app window
- **Image Preview**: Instantly view the selected photo before extracting metadata
- **TIFF Processing**: Advanced support for orthomosaic TIFF files with rasterio

### 🗺️ **Mapping & Location**
- **Interactive Map**: Built-in OpenStreetMap viewer shows the GPS location with a pinpoint
- **Reverse Geocoding**: Converts coordinates into a human-readable address using `geopy`
- **Click-to-Copy**: Copy full address, photo date, or coordinates with a single click
- **Coordinate Format Toggle**: Switch between decimal and WGS 84 (degrees, minutes, seconds) formats

### 📄 **Export & Reporting**
- **PDF Export**: Generate professional PDF reports with original image, metadata, and location map
- **High-Quality Output**: Custom fccTYPO fonts and professional formatting
- **Complete Analysis**: Flight height analysis and recalculation data included in exports
- **Manual Adjustment Marking**: Properly marked manual adjustments in PDF reports

### 🔧 **Technical Features**
- **Multiple Elevation APIs**: Integration with free elevation services for accurate terrain data
- **Flight Safety Warnings**: Automatic warnings for negative heights or heights above 120m
- **Smart Address Formatting**: Automatic two-line formatting for better readability
- **Live Connection Status**: Status bar shows whether online services are available
- **Optimized Performance**: Uses lazy loading and background threads for smooth operation

---

## 🧭 Extracted Metadata

- **File Information**: Filename and file format
- **GPS Data**: Latitude, longitude, altitude (if available)
- **Flight Height Analysis**: 
  - GPS altitude (total), terrain elevation, and actual drone flight height above terrain
  - Multiple elevation data sources for accuracy
  - Flight safety warnings and compliance checks
  - Manual adjustment indicators when applicable
- **Location**: Reverse-geocoded address from coordinates
- **Date/Time**: Original photo capture date from EXIF

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
- rasterio >= 1.3.0

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

### Basic Workflow
1. Start the app with `python main.py`
2. Drag a supported image into the window, or use the file picker
3. View metadata, map, and reverse-geocoded address
4. **Copy coordinates**: Click on coordinates to copy them to clipboard
5. **Toggle coordinate format**: Use the WGS 84 button to switch between decimal and degrees/minutes/seconds format
6. **Export PDF**: Click "Export Results" to generate a professional PDF report

### Advanced Height Recalculation
1. **Automatic Detection**: When negative flight height is detected, a recalculation dialog opens automatically
2. **Manual Recalculation**: Click the "🔧 Recalculate" button anytime to open the height recalculation dialog
3. **Upload TIFF**: Select an orthomosaic TIFF file to extract actual map resolution
4. **Select Drone**: Choose from DJI presets or use "Other" for custom parameters
5. **Manual Adjustment**: If the calculated height is incorrect, enable manual adjustment and set the correct height
6. **Apply Changes**: Click "Recalculate Height" to update the metadata

### Height Calculation Methods
- **Automatic**: Uses GPS altitude and terrain elevation data
- **TIFF-Based**: Uses actual orthomosaic resolution with drone reference GSD
- **Manual Override**: Direct height input when calculations are incorrect

---

## 📁 Project Structure

```
ImageMetaLocator/
├── main.py                 # Application entry point
├── core/                   # Core functionality
│   ├── metadata.py         # Metadata extraction and flight height analysis
├── ui/                     # PySide6 GUI components
│   ├── main_window.py      # Main application window
│   └── widgets.py          # Custom widgets (dialogs, map, drop area)
├── utils/                  # Helpers
│   ├── resources.py        # Asset loading and management
│   └── config.py           # Configuration utilities
├── assets/                 # Icons, fonts, and styling
├── requirements.txt        # Python dependencies
└── LICENSE                 # License information
```

---

## 🔐 License

This project is licensed under the **Non-Commercial Public License (NCPL v1.0)**  
© 2025 Jakub Ešpandr – Born4Flight, FlyCamCzech

See the [LICENSE](https://github.com/Jakub-Espandr/ImageMetaLocator/raw/main/LICENSE) file for full terms.

---

## 🙏 Acknowledgments

- Built with ❤️ using PySide6, Pillow, rawpy, exifread, geopy, reportlab, and rasterio
- Special thanks to the open-source community for elevation APIs and mapping services
