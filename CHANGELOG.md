# Changelog

## [0.2.0] - 2025-06-24

### 🚁 **Major Feature: Height Recalculation System**
- **Negative Height Detection**: Automatic detection and warning for negative flight heights
- **TIFF Orthomosaic Support**: Upload orthomosaic TIFF files to extract actual map resolution
- **DJI Drone Presets**: Pre-configured drone models with accurate GSD values:
  - DJI Phantom 4 PRO (1.36 cm/px at 50m)
  - DJI Phantom 4 (2.19 cm/px at 50m)
  - DJI Mavic 2 PRO (1.17 cm/px at 50m)
  - DJI Mavic 2 ZOOM (1.82 cm/px at 50m)
- **Custom Drone Setup**: Manual input for reference height and GSD values
- **Ratio-Based Calculation**: Uses the formula: `Height = (Map_GSD / Drone_GSD) × Drone_Height`
- **Manual Height Adjustment**: Override calculated heights when they're incorrect (e.g., showing 3m instead of actual height)

### 🎨 **UI/UX Improvements**
- **Manual Recalculation Button**: "🔧 Recalculate" button available anytime, not just for negative heights
- **Visual Indicators**: Clear distinction between calculated and manually adjusted heights
- **Enhanced Status Messages**: Better feedback for recalculation actions

### 🔧 **Technical Enhancements**
- **Rasterio Integration**: Added support for reading TIFF file metadata and resolution
- **Flexible Data Handling**: Works with or without existing flight analysis data

### 📦 **Dependencies**
- **Added**: `rasterio>=1.3.0` for TIFF file processing

---

## [0.1.2] - 2025-06-24

### Added
- **Drone Flight Height Analysis**: Complete flight height calculation with terrain elevation data
  - GPS Altitude (Total): Complete GPS altitude above sea level
  - Terrain Elevation: Ground elevation from multiple online elevation APIs
  - Drone Flight Height: Actual drone height above terrain (GPS - Terrain)
  - Data Sources: Shows number of elevation APIs used for accuracy
  - Terrain Sources: Detailed list of elevation data sources with values
- **Multiple Elevation APIs**: Integration with free elevation services:
  - Open-Elevation API
  - OpenTopoData SRTM (Shuttle Radar Topography Mission)
  - OpenTopoData ASTER dataset
- **Flight Safety Warnings**: Automatic warnings for:
  - Negative flight heights (data accuracy issues)
  - Heights above 120m (regulatory compliance)
- **Enhanced PDF Export**: Flight height analysis included in PDF reports

### Technical Improvements
- **Robust API Integration**: Multiple fallback sources for terrain elevation data
- **Enhanced Error Handling**: Better handling of network issues and API failures
- **Improved Map Loading**: More reliable map capture for PDF export with retry mechanisms

---

## [0.1.1] - 2025-06-23

### Added
- **PDF Export**: Generate professional PDF reports with original image, metadata table, and location map
- **Coordinate Format Toggle**: Switch between decimal and WGS 84 formats with a single click
- **Clickable Coordinates**: Copy coordinates to clipboard with one click
- **Smart Address Formatting**: Automatic two-line formatting for better readability

---

## [0.1.0] - 2025-06-22

### Features Added

- **Modern GUI**: A beautiful and responsive user interface built from the ground up with PySide6.
- **Dual File Input**: Support for both intuitive drag-and-drop and traditional file browsing.
- **Image Preview**: Displays a thumbnail of the selected image so you know what you're analyzing.
- **Interactive Map**: Visualizes GPS coordinates on an interactive OpenStreetMap view, complete with a location marker and popup.
- **Reverse Geocoding**: Automatically converts GPS coordinates to a human-readable address.
- **Click-to-Copy**: Easily copy the full address or date to the clipboard with a single click.
- **Live Connection Status**: An indicator in the status bar checks for internet and required service availability (`Map Service`, `Geocoding`) on startup, providing immediate feedback.
- **Performance Optimized**:
    - Uses background threads for all metadata processing and network checks to ensure the UI never freezes.
    - The map widget is lazy-loaded, meaning it only initializes when needed, resulting in a significantly faster application launch.