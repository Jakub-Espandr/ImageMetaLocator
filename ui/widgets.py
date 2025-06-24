from pathlib import Path
import rasterio

from PySide6.QtWidgets import QFrame, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QDialog, QComboBox, QLineEdit, QFormLayout, QGroupBox, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt, Signal, QUrl, QThread
from PySide6.QtGui import QCursor, QFont, QPixmap, QDragEnterEvent, QDropEvent
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
        self.setStyleSheet("QWidget { border: 2px solid #dee2e6; border-radius: 8px; background-color: white; }")
        
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
        self.setStyleSheet("QFrame { border: 3px dashed #cccccc; border-radius: 10px; background-color: white; } QFrame:hover { border-color: #007bff; }")
        
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
        self.setStyleSheet("QFrame { border: 3px dashed #cccccc; border-radius: 10px; background-color: white; } QFrame:hover { border-color: #007bff; }")
    
    def dropEvent(self, event):
        self.setStyleSheet("QFrame { border: 3px dashed #cccccc; border-radius: 10px; background-color: white; } QFrame:hover { border-color: #007bff; }")
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if Path(file_path).suffix.lower() in {'.jpg', '.jpeg', '.tif', '.tiff', '.dng'}:
                self.file_dropped.emit(file_path)
            else:
                QMessageBox.warning(self, "Invalid File", "Please select a valid image file (JPG, JPEG, TIFF, DNG)")

class HeightRecalculationDialog(QDialog):
    """Dialog for manual height recalculation using orthomosaic TIFF resolution."""
    
    def __init__(self, parent=None, current_flight_height=None, gps_altitude=None, terrain_elevation=None):
        super().__init__(parent)
        self.current_flight_height = current_flight_height
        self.gps_altitude = gps_altitude
        self.terrain_elevation = terrain_elevation
        self.recalculated_height = None
        self.tiff_path = None
        self.tiff_resolution = None
        self.drone_reference_height = 50  # meters
        self.drone_reference_gsd = None
        
        # Drone presets with GSD values
        self.drone_presets = {
            "DJI Phantom 4 PRO": 1.36,
            "DJI Phantom 4": 2.19,
            "DJI Mavic 2 PRO": 1.17,
            "DJI Mavic 2 ZOOM": 1.82
        }
        
        self.setWindowTitle("Manual Height Recalculation")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Set dialog background
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
            QLabel {
                background-color: transparent;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                border-color: #007bff;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 5px;
            }
            QSpinBox:hover, QDoubleSpinBox:hover {
                border-color: #007bff;
            }
        """)
        
        # Warning message
        warning_label = QLabel("⚠️ Negative flight height detected! This usually indicates inaccurate data.")
        warning_label.setStyleSheet("color: #d63384; font-weight: bold; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px;")
        layout.addWidget(warning_label)
        
        # Current data display
        current_group = QGroupBox("Current Data")
        current_layout = QFormLayout(current_group)
        
        if self.gps_altitude is not None:
            current_layout.addRow("GPS Altitude:", QLabel(f"{self.gps_altitude:.2f} m"))
        if self.terrain_elevation is not None:
            current_layout.addRow("Terrain Elevation:", QLabel(f"{self.terrain_elevation:.2f} m"))
        if self.current_flight_height is not None:
            current_layout.addRow("Calculated Height:", QLabel(f"{self.current_flight_height:.2f} m"))
        
        layout.addWidget(current_group)
        
        # TIFF Upload Section
        tiff_group = QGroupBox("Orthomosaic TIFF Upload")
        tiff_layout = QFormLayout(tiff_group)
        
        # TIFF file selection
        tiff_button_layout = QHBoxLayout()
        self.tiff_label = QLabel("No TIFF file selected")
        self.tiff_label.setStyleSheet("color: #6c757d; font-style: italic;")
        self.upload_tiff_button = QPushButton("📁 Upload TIFF")
        self.upload_tiff_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.upload_tiff_button.clicked.connect(self.upload_tiff)
        tiff_button_layout.addWidget(self.tiff_label)
        tiff_button_layout.addWidget(self.upload_tiff_button)
        
        tiff_layout.addRow("Orthomosaic File:", tiff_button_layout)
        
        # Resolution display
        self.resolution_label = QLabel("Resolution will appear here after TIFF upload")
        self.resolution_label.setStyleSheet("color: #6c757d; font-style: italic;")
        tiff_layout.addRow("Map Resolution:", self.resolution_label)
        
        # Manual resolution input (fallback)
        self.manual_resolution_spin = QDoubleSpinBox()
        self.manual_resolution_spin.setRange(0.01, 10.0)
        self.manual_resolution_spin.setValue(0.05)
        self.manual_resolution_spin.setSuffix(" m/px")
        self.manual_resolution_spin.setDecimals(3)
        self.manual_resolution_spin.valueChanged.connect(self.on_resolution_changed)
        tiff_layout.addRow("Manual Resolution:", self.manual_resolution_spin)
        
        layout.addWidget(tiff_group)
        
        # DJI Drone Presets
        preset_group = QGroupBox("DJI Drone Reference (50m altitude)")
        preset_layout = QFormLayout(preset_group)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Select a drone for reference...")
        # Add drone names without GSD values
        for drone_name in self.drone_presets.keys():
            self.preset_combo.addItem(drone_name)
        self.preset_combo.addItem("Other - Manual Setup")
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        
        preset_layout.addRow("Drone Model:", self.preset_combo)
        
        # Manual drone setup (initially hidden)
        self.manual_drone_group = QGroupBox("Manual Drone Setup")
        manual_drone_layout = QFormLayout(self.manual_drone_group)
        
        self.manual_height_spin = QSpinBox()
        self.manual_height_spin.setRange(1, 500)
        self.manual_height_spin.setValue(50)
        self.manual_height_spin.setSuffix(" m")
        self.manual_height_spin.valueChanged.connect(self.on_manual_drone_changed)
        
        self.manual_gsd_spin = QDoubleSpinBox()
        self.manual_gsd_spin.setRange(0.1, 10.0)
        self.manual_gsd_spin.setValue(1.5)
        self.manual_gsd_spin.setSuffix(" cm/px")
        self.manual_gsd_spin.setDecimals(2)
        self.manual_gsd_spin.valueChanged.connect(self.on_manual_drone_changed)
        
        manual_drone_layout.addRow("Reference Height:", self.manual_height_spin)
        manual_drone_layout.addRow("Reference GSD:", self.manual_gsd_spin)
        
        self.manual_drone_group.setVisible(False)
        layout.addWidget(self.manual_drone_group)
        
        # Reference GSD display
        self.reference_gsd_label = QLabel("Reference GSD will appear here")
        self.reference_gsd_label.setStyleSheet("font-weight: bold; color: #17a2b8;")
        preset_layout.addRow("Reference GSD:", self.reference_gsd_label)
        
        layout.addWidget(preset_group)
        
        # Calculation Result
        result_group = QGroupBox("Flight Height Calculation")
        result_layout = QFormLayout(result_group)
        
        self.calculated_height_label = QLabel("Upload TIFF and select drone to calculate")
        self.calculated_height_label.setStyleSheet("font-weight: bold; color: #28a745; font-size: 14px;")
        result_layout.addRow("Calculated Height:", self.calculated_height_label)
        
        layout.addWidget(result_group)
        
        # Manual Height Adjustment
        adjustment_group = QGroupBox("Manual Height Adjustment")
        adjustment_layout = QFormLayout(adjustment_group)
        
        # Enable manual adjustment checkbox
        self.enable_manual_checkbox = QPushButton("🔧 Adjust Height Manually")
        self.enable_manual_checkbox.setCheckable(True)
        self.enable_manual_checkbox.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:checked {
                background-color: #28a745;
                color: white;
            }
        """)
        self.enable_manual_checkbox.clicked.connect(self.toggle_manual_adjustment)
        adjustment_layout.addRow("Manual Adjustment:", self.enable_manual_checkbox)
        
        # Manual height input (initially hidden)
        self.manual_height_input = QSpinBox()
        self.manual_height_input.setRange(1, 1000)
        self.manual_height_input.setValue(50)
        self.manual_height_input.setSuffix(" m")
        self.manual_height_input.valueChanged.connect(self.on_manual_height_changed)
        self.manual_height_input.setVisible(False)
        adjustment_layout.addRow("Manual Height:", self.manual_height_input)
        
        # Manual height result display
        self.manual_result_label = QLabel("Manual height will appear here")
        self.manual_result_label.setStyleSheet("font-weight: bold; color: #dc3545; font-size: 14px;")
        self.manual_result_label.setVisible(False)
        adjustment_layout.addRow("Final Height:", self.manual_result_label)
        
        adjustment_group.setVisible(True)
        layout.addWidget(adjustment_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.calculate_button = QPushButton("Recalculate Height")
        self.calculate_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.calculate_button.clicked.connect(self.accept)
        self.calculate_button.setEnabled(False)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.calculate_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
    def upload_tiff(self):
        """Upload and process TIFF file to extract resolution."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select Orthomosaic TIFF file", 
                "", 
                "TIFF files (*.tif *.tiff);;All files (*)"
            )
            
            if not file_path:
                return
                
            self.tiff_path = file_path
            self.tiff_label.setText(f"📄 {Path(file_path).name}")
            self.tiff_label.setStyleSheet("color: #28a745; font-weight: bold;")
            
            # Extract resolution from TIFF
            with rasterio.open(file_path) as src:
                if hasattr(src, 'res') and src.res:
                    # Average resolution (meters per pixel)
                    resolution = (src.res[0] + src.res[1]) / 2
                    self.tiff_resolution = resolution
                    
                    # Update resolution display
                    self.resolution_label.setText(f"{resolution:.3f} m/px ({resolution*100:.2f} cm/px)")
                    self.resolution_label.setStyleSheet("color: #28a745; font-weight: bold;")
                    
                    # Update manual resolution spinbox
                    self.manual_resolution_spin.setValue(resolution)
                    
                    # Calculate flight height if drone is selected
                    self.calculate_flight_height()
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read TIFF file:\n{str(e)}")
            self.tiff_label.setText("Error reading TIFF file")
            self.tiff_label.setStyleSheet("color: #dc3545; font-weight: bold;")
    
    def on_resolution_changed(self):
        """Handle manual resolution change."""
        self.tiff_resolution = self.manual_resolution_spin.value()
        self.calculate_flight_height()
    
    def on_manual_drone_changed(self):
        """Handle manual drone parameters change."""
        if self.preset_combo.currentText() == "Other - Manual Setup":
            self.drone_reference_height = self.manual_height_spin.value()
            self.drone_reference_gsd = self.manual_gsd_spin.value()
            self.reference_gsd_label.setText(f"{self.drone_reference_gsd:.2f} cm/px at {self.drone_reference_height} m")
            self.calculate_flight_height()
    
    def toggle_manual_adjustment(self):
        """Toggle manual height adjustment mode."""
        is_manual = self.enable_manual_checkbox.isChecked()
        
        # Show/hide manual adjustment controls
        self.manual_height_input.setVisible(is_manual)
        self.manual_result_label.setVisible(is_manual)
        
        if is_manual:
            # Set initial value to calculated height if available
            if self.recalculated_height:
                self.manual_height_input.setValue(int(self.recalculated_height))
            self.enable_manual_checkbox.setText("🔧 Manual Adjustment Active")
        else:
            self.enable_manual_checkbox.setText("🔧 Adjust Height Manually")
            self.manual_result_label.setText("Manual height will appear here")
        
        self.update_final_height()
    
    def on_manual_height_changed(self):
        """Handle manual height input change."""
        self.update_final_height()
    
    def update_final_height(self):
        """Update the final height display based on manual adjustment."""
        if self.enable_manual_checkbox.isChecked():
            manual_height = self.manual_height_input.value()
            self.manual_result_label.setText(f"{manual_height} m above terrain (Manual)")
            self.recalculated_height = manual_height
        else:
            # Use calculated height
            if self.recalculated_height:
                self.manual_result_label.setText(f"{self.recalculated_height:.2f} m above terrain (Calculated)")
    
    def calculate_flight_height(self):
        """Calculate flight height using the ratio method."""
        if not self.tiff_resolution or not self.drone_reference_gsd:
            self.calculated_height_label.setText("Upload TIFF and select drone to calculate")
            self.calculate_button.setEnabled(False)
            return
        
        # Convert map resolution to cm/px
        map_gsd_cm_per_px = self.tiff_resolution * 100
        
        # Calculate flight height using the ratio formula
        # Height = (Current_GSD_of_map / drone_reference_GSD) × drone_reference_height
        flight_height = (map_gsd_cm_per_px / self.drone_reference_gsd) * self.drone_reference_height
        
        self.recalculated_height = flight_height
        self.calculated_height_label.setText(f"{flight_height:.2f} m above terrain")
        self.calculate_button.setEnabled(True)
        
        # Update manual adjustment if active
        if self.enable_manual_checkbox.isChecked():
            self.manual_height_input.setValue(int(flight_height))
            self.update_final_height()
    
    def on_preset_changed(self, text):
        """Handle preset selection change."""
        if text == "Select a drone for reference...":
            self.reference_gsd_label.setText("Reference GSD will appear here")
            self.drone_reference_gsd = None
            self.manual_drone_group.setVisible(False)
            self.calculate_flight_height()
            return
        
        if text == "Other - Manual Setup":
            self.manual_drone_group.setVisible(True)
            self.drone_reference_height = self.manual_height_spin.value()
            self.drone_reference_gsd = self.manual_gsd_spin.value()
            self.reference_gsd_label.setText(f"{self.drone_reference_gsd:.2f} cm/px at {self.drone_reference_height} m")
        else:
            self.manual_drone_group.setVisible(False)
            # Get GSD from the drone presets dictionary
            if text in self.drone_presets:
                self.drone_reference_gsd = self.drone_presets[text]
                self.drone_reference_height = 50  # All presets are at 50m
                self.reference_gsd_label.setText(f"{self.drone_reference_gsd:.2f} cm/px at {self.drone_reference_height} m")
        
        self.calculate_flight_height()
    
    def get_recalculated_height(self):
        """Return the recalculated flight height."""
        return self.recalculated_height 