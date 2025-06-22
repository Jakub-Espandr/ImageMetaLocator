from pathlib import Path

from PySide6.QtWidgets import QFrame, QLabel, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QCursor, QFont
from utils.resources import get_asset_path

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = None

class ClickableLabel(QLabel):
    """A QLabel that emits a signal when clicked and provides copy functionality."""
    clicked_to_copy = Signal(str, str)

    def __init__(self, display_text: str, copy_value: str, field_name: str, parent: QWidget = None):
        super().__init__(display_text, parent)
        self.copy_value = copy_value
        self.field_name = field_name
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip(f"Click to copy {self.field_name}")
        self.setWordWrap(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked_to_copy.emit(self.field_name, self.copy_value)
        super().mousePressEvent(event)

class MapWidget(QWidget):
    """Lazy-loading map widget for displaying GPS coordinates"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)
        self.setStyleSheet("QWidget { border: 2px solid #dee2e6; border-radius: 8px; background-color: #f8f9fa; }")
        
        self.layout = QVBoxLayout(self)
        self.web_view = None
        self.is_loaded = False
        self.current_html = ""
        
        self.loading_label = QLabel("🗺️ Map will load when GPS coordinates are found")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("QLabel { color: #666666; font-size: 16px; font-weight: bold; background-color: transparent; border: none; }")
        self.layout.addWidget(self.loading_label)
    
    def load_web_engine(self):
        if self.is_loaded: return
        if QWebEngineView:
            self.web_view = QWebEngineView()
            self.web_view.setStyleSheet("border: none; border-radius: 8px;")
            self.layout.removeWidget(self.loading_label)
            self.loading_label.hide()
            self.layout.addWidget(self.web_view)
            self.load_empty_map()
            self.is_loaded = True
        else:
            self.loading_label.setText("🗺️ Map feature not available\n(PySide6-WebEngine not installed)")
            self.loading_label.setStyleSheet("QLabel { color: #dc3545; font-size: 14px; font-weight: bold; background-color: transparent; border: none; }")
    
    def load_empty_map(self):
        if not self.web_view: return
        html = """<!DOCTYPE html><html><head><title>Map</title><style>body{margin:0;padding:0;}#map{height:100vh;width:100%;}</style></head><body><div id="map"></div></body></html>"""
        self.web_view.setHtml(html)
        self.current_html = html
    
    def show_location(self, lat: float, lon: float, address: str = ""):
        if not self.is_loaded: self.load_web_engine()
        if not self.web_view: return
            
        font_path = get_asset_path("fonts", "fccTYPO-Regular.ttf")
        font_face_css = ""
        font_family_css = ""
        if font_path and font_path.exists():
            font_url = font_path.as_uri()
            font_face_css = f"@font-face {{ font-family: 'fccTYPO'; src: url('{font_url}') format('truetype'); }}"
            font_family_css = "font-family: 'fccTYPO', sans-serif;"
        
        js_safe_address = address.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "<br>")
        html = f"""
        <!DOCTYPE html><html><head><title>Map</title><meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{ margin: 0; padding: 0; }} #map {{ height: 100vh; width: 100%; }}
            {font_face_css} .leaflet-popup-content-wrapper, .leaflet-popup-content {{ {font_family_css} line-height: 1.5; }}
        </style></head><body><div id="map"></div><script>
            var map = L.map('map').setView([{lat}, {lon}], 15);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ attribution: '© OpenStreetMap' }}).addTo(map);
            L.marker([{lat}, {lon}]).addTo(map).bindPopup('{js_safe_address}').openPopup();
        </script></body></html>"""
        self.web_view.setHtml(html)
        self.current_html = html
    
    def get_html_content(self):
        """Get the current HTML content for export purposes."""
        return self.current_html

class DropArea(QFrame):
    file_dropped = Signal(str)
    def __init__(self, regular_font_family, bold_font_family):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setStyleSheet("QFrame { border: 3px dashed #cccccc; border-radius: 10px; background-color: #f8f9fa; } QFrame:hover { border-color: #007bff; }")
        
        layout = QVBoxLayout(self)
        drop_label = QLabel("📷 Drop image here or click to browse")
        drop_label.setAlignment(Qt.AlignCenter)
        drop_label.setFont(QFont(bold_font_family, 16))
        drop_label.setStyleSheet("QLabel { background-color: transparent; border: none; }")
        
        supported_formats = QLabel("Supported: JPG, JPEG, TIFF, DNG")
        supported_formats.setAlignment(Qt.AlignCenter)
        supported_formats.setFont(QFont(regular_font_family, 12))
        supported_formats.setStyleSheet("QLabel { color: #999999; background-color: transparent; border: none; }")
        
        layout.addWidget(drop_label)
        layout.addWidget(supported_formats)
        
        self.browse_btn = QPushButton("Browse Files")
        self.browse_btn.setFont(QFont(bold_font_family, 12))
        self.browse_btn.setStyleSheet("QPushButton { background-color: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; } QPushButton:hover { background-color: #0056b3; }")
        self.browse_btn.clicked.connect(self.browse_files)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignCenter)
    
    def browse_files(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image File", "", "Image Files (*.jpg *.jpeg *.tif *.tiff *.dng)")
        if file_path: self.file_dropped.emit(file_path)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QFrame { border: 3px dashed #28a745; border-radius: 10px; background-color: #d4edda; }")
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("QFrame { border: 3px dashed #cccccc; border-radius: 10px; background-color: #f8f9fa; } QFrame:hover { border-color: #007bff; }")
    
    def dropEvent(self, event):
        self.setStyleSheet("QFrame { border: 3px dashed #cccccc; border-radius: 10px; background-color: #f8f9fa; } QFrame:hover { border-color: #007bff; }")
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if Path(file_path).suffix.lower() in {'.jpg', '.jpeg', '.tif', '.tiff', '.dng'}:
                self.file_dropped.emit(file_path)
            else:
                QMessageBox.warning(self, "Invalid File", "Please select a valid image file (JPG, JPEG, TIFF, DNG)") 