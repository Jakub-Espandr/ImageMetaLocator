import html
from datetime import datetime
from pathlib import Path
import io
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QScrollArea, QProgressBar, QMessageBox, QTabWidget,
    QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QFont, QPixmap

from core.metadata import MetadataWorker, ConnectionTestWorker, ExportWorker
from ui.widgets import DropArea, MapWidget, ClickableLabel, HeightRecalculationDialog

class ImageMetaLocator(QMainWindow):
    """Main application window"""
    
    def __init__(self, regular_font, bold_font):
        super().__init__()
        self.regular_font_family = regular_font
        self.bold_font_family = bold_font
        self.setWindowTitle("Image Meta Locator")
        self.setMinimumSize(1000, 700)
        self.current_image_path = None
        self.current_metadata = None
        self.coordinates_decimal = None
        self.coordinates_wgs84 = None
        self.showing_wgs84 = False
        self.setup_ui()
        self.setup_styles()
        self.test_connection()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Image Meta Locator")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont(self.bold_font_family, 22))
        title.setStyleSheet("QLabel { background-color: transparent; }")
        main_layout.addWidget(title)
        
        self.drop_area = DropArea(self.regular_font_family, self.bold_font_family)
        self.drop_area.file_dropped.connect(self.process_image)
        main_layout.addWidget(self.drop_area)
        
        # Export button (initially hidden)
        self.export_button = QPushButton("📁 Export Results")
        self.export_button.setFont(QFont(self.bold_font_family, 12))
        self.export_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; } QPushButton:hover { background-color: #218838; } QPushButton:disabled { background-color: #6c757d; }")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setVisible(False)
        main_layout.addWidget(self.export_button, alignment=Qt.AlignCenter)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar::tab:selected { color: #212529; } QTabBar::tab:hover { color: #212529; }")

        # Metadata Tab
        metadata_tab = QWidget()
        metadata_layout = QHBoxLayout(metadata_tab)
        
        self.image_preview = QLabel("No image selected")
        self.image_preview.setMinimumSize(300, 200)
        self.image_preview.setMaximumSize(400, 300)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setFont(QFont(self.regular_font_family, 10))
        self.image_preview.setStyleSheet("QLabel { border: 2px solid #dee2e6; border-radius: 8px; background-color: white; color: #6c757d; }")
        metadata_layout.addWidget(self.image_preview)
        
        metadata_widget = QWidget()
        metadata_display_layout = QVBoxLayout(metadata_widget)
        metadata_title = QLabel("Metadata")
        metadata_title.setFont(QFont(self.bold_font_family, 16))
        metadata_title.setStyleSheet("QLabel { background-color: transparent; }")
        metadata_display_layout.addWidget(metadata_title)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: 2px solid #dee2e6; border-radius: 8px; background-color: white; }")
        
        metadata_container = QWidget()
        metadata_container.setStyleSheet("background-color: white;")
        self.metadata_layout = QVBoxLayout(metadata_container)
        self.metadata_layout.setAlignment(Qt.AlignTop)
        self.metadata_layout.setSpacing(15)
        self.metadata_placeholder = QLabel("Image metadata will appear here...")
        self.metadata_placeholder.setFont(QFont(self.regular_font_family, 11))
        self.metadata_placeholder.setStyleSheet("QLabel { background-color: transparent; color: #6c757d; }")
        self.metadata_layout.addWidget(self.metadata_placeholder)
        scroll_area.setWidget(metadata_container)
        metadata_display_layout.addWidget(scroll_area)
        metadata_layout.addWidget(metadata_widget)
        self.tab_widget.addTab(metadata_tab, "Metadata")
        
        # Map Tab
        map_tab = QWidget()
        map_layout = QVBoxLayout(map_tab)
        map_title = QLabel("Location Map")
        map_title.setFont(QFont(self.bold_font_family, 16))
        map_title.setStyleSheet("QLabel { background-color: transparent; }")
        map_layout.addWidget(map_title)
        self.map_widget = MapWidget()
        map_layout.addWidget(self.map_widget)
        self.tab_widget.addTab(map_tab, "Map")
        main_layout.addWidget(self.tab_widget)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: 2px solid #dee2e6; border-radius: 5px; text-align: center; background-color: #e9ecef; color: #495057; } QProgressBar::chunk { background-color: #007bff; border-radius: 3px; }")
        main_layout.addWidget(self.progress_bar)
        
        self.statusBar().showMessage("Ready")
        self.connection_status_label = QLabel("🌐 Checking connection...")
        self.statusBar().addPermanentWidget(self.connection_status_label)
        self.statusBar().setStyleSheet("background-color: white; color: #212529; border-top: 1px solid #dee2e6;")
    
    def setup_styles(self):
        font_style = f"font-family: '{self.regular_font_family}';" if self.regular_font_family else ""
        self.setStyleSheet(f"""
            QMainWindow {{ 
                background-color: white; 
            }} 
            QWidget {{ 
                {font_style} 
                color: #212529; 
                background-color: white;
            }}
            QTabWidget::pane {{
                border: 1px solid #dee2e6;
                background-color: white;
            }}
            QTabBar::tab {{
                background-color: #f8f9fa;
                color: #6c757d;
                padding: 8px 16px;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: white;
                color: #212529;
                border-bottom: 1px solid white;
            }}
            QTabBar::tab:hover {{
                background-color: #e9ecef;
                color: #212529;
            }}
            QScrollArea {{
                background-color: white;
                border: 1px solid #dee2e6;
            }}
            QScrollBar:vertical {{
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #dee2e6;
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #adb5bd;
            }}
            QProgressBar {{
                background-color: #e9ecef;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                color: #495057;
            }}
            QProgressBar::chunk {{
                background-color: #007bff;
                border-radius: 3px;
            }}
        """)
    
    def test_connection(self):
        self.connection_worker = ConnectionTestWorker()
        self.connection_worker.finished.connect(self.update_connection_status)
        self.connection_worker.start()

    def update_connection_status(self, is_online, message):
        self.connection_status_label.setText(f" {'🟢' if is_online else '🔴'} {message}")
        self.connection_status_label.setToolTip(f"Connection status: {message}")

    def process_image(self, image_path: str):
        self.current_image_path = image_path
        self.export_button.setVisible(False)
        self.statusBar().showMessage("Processing image...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.load_image_preview(image_path)
        self.worker = MetadataWorker(image_path)
        self.worker.finished.connect(self.display_metadata)
        self.worker.error.connect(self.handle_error)
        self.worker.start()
    
    def load_image_preview(self, image_path: str):
        try:
            pixmap = QPixmap(image_path).scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if not pixmap.isNull():
                self.image_preview.setPixmap(pixmap)
            else:
                self.image_preview.setText("Preview not available")
        except Exception as e:
            self.image_preview.setText(f"Error loading preview:\n{str(e)}")
    
    def display_metadata(self, metadata: dict):
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Metadata extracted successfully")
        self.current_metadata = metadata
        self.export_button.setVisible(True)
        
        # Check for negative flight height and show recalculation dialog
        if metadata.get('flight_analysis'):
            flight = metadata['flight_analysis']
            flight_height = flight.get('flight_height')
            if flight_height is not None and flight_height < 0:
                self.show_height_recalculation_dialog(metadata)
                return
        
        self.display_metadata_content(metadata)
    
    def show_height_recalculation_dialog(self, metadata: dict):
        """Show the height recalculation dialog for negative flight height."""
        # Get flight analysis data if available
        flight = metadata.get('flight_analysis', {})
        flight_height = flight.get('flight_height') if flight else None
        gps_altitude = flight.get('gps_altitude') if flight else metadata.get('altitude')
        terrain_elevation = flight.get('terrain_elevation_avg') if flight else None
        
        dialog = HeightRecalculationDialog(
            self, 
            current_flight_height=flight_height,
            gps_altitude=gps_altitude,
            terrain_elevation=terrain_elevation
        )
        
        if dialog.exec() == HeightRecalculationDialog.Accepted:
            recalculated_height = dialog.get_recalculated_height()
            if recalculated_height is not None:
                # Create flight analysis if it doesn't exist
                if 'flight_analysis' not in metadata:
                    metadata['flight_analysis'] = {
                        'gps_altitude': gps_altitude,
                        'terrain_elevation_avg': terrain_elevation or 0,
                        'terrain_elevations': {},
                        'sources_used': 0
                    }
                
                # Update the metadata with recalculated height
                metadata['flight_analysis']['flight_height'] = recalculated_height
                metadata['flight_analysis']['recalculated'] = True
                # Check if manual adjustment was used
                if hasattr(dialog, 'enable_manual_checkbox') and dialog.enable_manual_checkbox.isChecked():
                    metadata['flight_analysis']['manual_adjustment'] = True
                self.statusBar().showMessage(f"Height recalculated to {recalculated_height:.2f} m")
        
        # Display the metadata (with or without recalculation)
        self.display_metadata_content(metadata)
    
    def display_metadata_content(self, metadata: dict):
        """Display the metadata content (separated from dialog logic)."""
        while self.metadata_layout.count():
            child = self.metadata_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        font = QFont(self.regular_font_family, 11)
        if metadata.get('filename'):
            self.add_metadata_label(f"📷 <b>File:</b> {html.escape(metadata['filename'])}", font)
        if metadata.get('coordinates'):
            lat, lon = metadata['coordinates']
            
            # Store both coordinate formats
            self.coordinates_decimal = f"{lat:.6f}, {lon:.6f}"
            lat_deg, lat_min, lat_sec = self.decimal_to_dms(lat)
            lon_deg, lon_min, lon_sec = self.decimal_to_dms(lon)
            lat_hemisphere = "N" if lat >= 0 else "S"
            lon_hemisphere = "E" if lon >= 0 else "W"
            self.coordinates_wgs84 = f"{lat_deg}° {lat_min}' {lat_sec:.2f}\" {lat_hemisphere}, {lon_deg}° {lon_min}' {lon_sec:.2f}\" {lon_hemisphere}"
            self.showing_wgs84 = False
            
            # Create container for coordinates and toggle button
            coord_container = QWidget()
            coord_layout = QHBoxLayout(coord_container)
            coord_layout.setContentsMargins(0, 0, 0, 0)
            coord_layout.setSpacing(10)
            
            # Coordinates label
            self.coord_label = ClickableLabel(f"📍 <b>Coordinates:</b> {html.escape(self.coordinates_decimal)}", self.coordinates_decimal, "Coordinates")
            self.coord_label.setFont(font)
            self.coord_label.clicked_to_copy.connect(self.copy_to_clipboard)
            coord_layout.addWidget(self.coord_label)
            
            # Toggle button
            self.toggle_button = QPushButton("WGS 84")
            self.toggle_button.setFont(QFont(self.bold_font_family, 9))
            self.toggle_button.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; border: none; padding: 5px 10px; border-radius: 3px; } QPushButton:hover { background-color: #138496; }")
            self.toggle_button.clicked.connect(self.toggle_coordinates)
            coord_layout.addWidget(self.toggle_button)
            
            self.metadata_layout.addWidget(coord_container)
            
            # Update map with coordinates
            self.map_widget.show_location(lat, lon, metadata.get('address', ''))
        
        if metadata.get('address'):
            self.add_clickable_metadata("🏠 <b>Address:</b>", metadata['address'], "Address", font)
        
        if metadata.get('date'):
            self.add_clickable_metadata("📅 <b>Date:</b>", metadata['date'], "Date", font)
        
        if metadata.get('altitude'):
            self.add_clickable_metadata("📊 <b>GPS Altitude:</b>", f"{metadata['altitude']:.2f} m", "GPS Altitude", font)
        
        # Flight analysis section
        if metadata.get('flight_analysis'):
            flight = metadata['flight_analysis']
            
            # Check if height was recalculated
            if flight.get('recalculated'):
                if flight.get('manual_adjustment'):
                    self.add_metadata_label("🚁 <b>FLIGHT HEIGHT ANALYSIS (MANUAL ADJUSTMENT)</b>", QFont(self.bold_font_family, 12))
                    self.add_metadata_label("🔧 <b>Height manually adjusted by user</b>", font)
                else:
                    self.add_metadata_label("🚁 <b>FLIGHT HEIGHT ANALYSIS (RECALCULATED)</b>", QFont(self.bold_font_family, 12))
                    self.add_metadata_label("✅ <b>Height recalculated using drone camera GSD</b>", font)
            else:
                self.add_metadata_label("🚁 <b>FLIGHT HEIGHT ANALYSIS</b>", QFont(self.bold_font_family, 12))
            
            # Terrain elevation
            self.add_metadata_label(f"🏔️ <b>Terrain Elevation:</b> {flight['terrain_elevation_avg']:.2f} m n.m.", font)
            
            # Flight height with recalculation button
            flight_height = flight['flight_height']
            height_color = "green" if 0 <= flight_height <= 120 else "red"
            
            # Create container for height display and recalculation button
            height_container = QWidget()
            height_layout = QHBoxLayout(height_container)
            height_layout.setContentsMargins(0, 0, 0, 0)
            height_layout.setSpacing(10)
            
            # Height text
            height_text = f"🎯 <b>Drone Flight Height:</b> <span style='color: {height_color};'>{flight_height:.2f} m</span> above terrain"
            if flight.get('recalculated'):
                if flight.get('manual_adjustment'):
                    height_text += " <span style='color: #dc3545;'>(Manual Adjustment)</span>"
                else:
                    height_text += " <span style='color: #28a745;'>(Recalculated)</span>"
            
            height_label = QLabel(height_text)
            height_label.setFont(font)
            height_label.setTextFormat(Qt.RichText)
            height_layout.addWidget(height_label)
            
            # Recalculation button
            recalc_button = QPushButton("🔧 Recalculate")
            recalc_button.setFont(QFont(self.bold_font_family, 9))
            recalc_button.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            recalc_button.clicked.connect(lambda: self.show_height_recalculation_dialog(metadata))
            height_layout.addWidget(recalc_button)
            
            self.metadata_layout.addWidget(height_container)
            
            # Data sources
            self.add_metadata_label(f"📡 <b>Data Sources:</b> {flight['sources_used']} elevation APIs used", font)
            
            # Warnings
            if flight_height < 0 and not flight.get('recalculated'):
                self.add_metadata_label("⚠️ <b>Warning:</b> Negative flight height! Possible data inaccuracies.", QFont(self.bold_font_family, 10))
            elif flight_height > 120:
                self.add_metadata_label("⚠️ <b>Warning:</b> Flight height above 120m! Check local regulations.", QFont(self.bold_font_family, 10))
            
            # Detailed terrain elevation sources
            if flight['terrain_elevations']:
                self.add_metadata_label("🌐 <b>Terrain Elevation Sources:</b>", font)
                for source, elevation in flight['terrain_elevations'].items():
                    if elevation is not None:
                        source_name = source.replace('_', ' ').title()
                        self.add_metadata_label(f"   • {source_name}: {elevation:.2f} m", font)
        elif metadata.get('altitude') is not None:
            # If we have GPS altitude but can't get terrain elevation
            self.add_metadata_label("🚁 <b>FLIGHT HEIGHT ANALYSIS</b>", QFont(self.bold_font_family, 12))
            self.add_metadata_label("❌ <b>Unable to calculate flight height:</b> Could not retrieve terrain elevation data", font)
            
            # Add recalculation button even when no flight analysis is available
            recalc_button = QPushButton("🔧 Calculate Height Manually")
            recalc_button.setFont(QFont(self.bold_font_family, 10))
            recalc_button.setStyleSheet("""
                QPushButton {
                    background-color: #17a2b8;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #138496;
                }
            """)
            recalc_button.clicked.connect(lambda: self.show_height_recalculation_dialog(metadata))
            self.metadata_layout.addWidget(recalc_button, alignment=Qt.AlignCenter)
    
    def add_metadata_label(self, text, font):
        label = QLabel(text)
        label.setFont(font)
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)
        self.metadata_layout.addWidget(label)

    def add_clickable_metadata(self, prefix, value, field_name, font):
        label = ClickableLabel(f"{prefix} {html.escape(value)}", value, field_name)
        label.setFont(font)
        label.clicked_to_copy.connect(self.copy_to_clipboard)
        self.metadata_layout.addWidget(label)
    
    def copy_to_clipboard(self, field_name: str, value: str):
        try:
            QApplication.clipboard().setText(value)
            self.statusBar().showMessage(f"{field_name} copied to clipboard!", 3000)
        except Exception as e:
            self.statusBar().showMessage(f"Error copying to clipboard: {e}", 3000)

    def handle_error(self, error_message: str):
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Error processing image")
        QMessageBox.critical(self, "Error", f"Failed to process image:\n{error_message}")

    def export_results(self):
        """Export results as a single PDF file."""
        if not self.current_image_path or not self.current_metadata:
            QMessageBox.warning(self, "No Data", "No image data to export.")
            return
        
        # Get export file path from user
        image_name = Path(self.current_image_path).stem
        default_filename = f"ImageMetaLocator_Report_{image_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        pdf_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save PDF Report", 
            str(Path.home() / "Desktop" / default_filename),
            "PDF Files (*.pdf)"
        )
        
        if not pdf_path:
            return
        
        # Capture map image from the map widget
        map_image = self.capture_map_image()
        
        # Start export worker
        self.export_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.statusBar().showMessage("Generating PDF report...")
        
        self.export_worker = ExportWorker(
            self.current_image_path, 
            self.current_metadata, 
            "",  # map_html not used anymore
            pdf_path,
            map_image
        )
        self.export_worker.finished.connect(self.export_finished)
        self.export_worker.error.connect(self.export_error)
        self.export_worker.progress.connect(self.progress_bar.setValue)
        self.export_worker.start()
    
    def ensure_map_loaded(self):
        """Ensure the map is loaded and visible before capture."""
        try:
            # Switch to map tab
            self.tab_widget.setCurrentIndex(1)
            
            # Force the map widget to be visible
            self.map_widget.show()
            self.map_widget.raise_()
            
            # Process events multiple times to ensure rendering
            for _ in range(5):  # Increased from 3 to 5
                QApplication.processEvents()
                import time
                time.sleep(0.8)  # Increased from 0.5 to 0.8
            
            # If web view exists, ensure it's loaded
            if hasattr(self.map_widget, 'web_view') and self.map_widget.web_view:
                print("Ensuring web view is loaded...")
                # Force the web view to be visible
                self.map_widget.web_view.show()
                self.map_widget.web_view.raise_()
                
                # Additional wait for web view to render
                for _ in range(3):
                    QApplication.processEvents()
                    time.sleep(0.5)
                
        except Exception as e:
            print(f"Error ensuring map is loaded: {e}")

    def capture_map_image(self):
        """Capture the current map widget as an image."""
        try:
            print("Starting map capture...")
            
            # Ensure map is loaded
            self.ensure_map_loaded()
            
            # Check if map widget has web view
            has_web_view = hasattr(self.map_widget, 'web_view') and self.map_widget.web_view
            print(f"Map widget has web view: {has_web_view}")
            
            # Capture the map widget
            if has_web_view:
                print("Capturing web view...")
                # Try to capture the web view content
                pixmap = self.map_widget.web_view.grab()
                
                # If the web view is empty or too small, try capturing the entire widget
                if pixmap.isNull() or pixmap.size().width() < 100 or pixmap.size().height() < 100:
                    print("Web view capture failed or too small, trying entire widget...")
                    pixmap = self.map_widget.grab()
                    
                    # If still no success, try to wait a bit more and retry
                    if pixmap.isNull() or pixmap.size().width() < 100:
                        print("Waiting for map to load and retrying...")
                        import time
                        time.sleep(2)
                        QApplication.processEvents()
                        pixmap = self.map_widget.web_view.grab()
                        if pixmap.isNull():
                            pixmap = self.map_widget.grab()
            else:
                print("Capturing entire map widget...")
                pixmap = self.map_widget.grab()
            
            print(f"Pixmap captured, is null: {pixmap.isNull()}")
            print(f"Pixmap size: {pixmap.size()}")
            
            if not pixmap.isNull() and pixmap.size().width() > 50 and pixmap.size().height() > 50:
                print("Converting pixmap to bytes...")
                # Convert QPixmap to QByteArray, then to bytes
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                
                # Use higher quality settings for better DPI
                success = pixmap.save(buffer, "PNG", quality=100)
                buffer.close()
                
                print(f"Pixmap save success: {success}")
                print(f"Byte array size: {byte_array.size()}")
                
                if success and byte_array.size() > 0:
                    # Convert to bytes for the export worker
                    img_buffer = io.BytesIO(byte_array.data())
                    print(f"Created BytesIO buffer, size: {len(img_buffer.getvalue())}")
                    
                    # Optionally enhance the image quality further
                    try:
                        from PIL import Image, ImageEnhance
                        img_buffer.seek(0)
                        pil_image = Image.open(img_buffer)
                        
                        # Enhance sharpness slightly for better text readability
                        enhancer = ImageEnhance.Sharpness(pil_image)
                        enhanced_image = enhancer.enhance(1.2)  # Slight sharpening
                        
                        # Save with high quality
                        enhanced_buffer = io.BytesIO()
                        enhanced_image.save(enhanced_buffer, format='PNG', optimize=False)
                        enhanced_buffer.seek(0)
                        
                        print("Enhanced image quality for better DPI")
                        return enhanced_buffer
                    except Exception as e:
                        print(f"Image enhancement failed, using original: {e}")
                        img_buffer.seek(0)
                        return img_buffer
                else:
                    print("Failed to save pixmap or byte array is empty")
                    return None
            else:
                print("Failed to capture map - pixmap is null or too small")
                return None
                
        except Exception as e:
            print(f"Error capturing map image: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def export_finished(self, pdf_path: str):
        """Handle successful PDF export completion."""
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        self.statusBar().showMessage("PDF report generated successfully!")
        
        # Show success message with option to open PDF
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("PDF Export Complete")
        msg.setText(f"PDF report generated successfully:\n{pdf_path}")
        msg.setInformativeText("The PDF includes the image, metadata, and location information.")
        
        open_button = msg.addButton("Open PDF", QMessageBox.ActionRole)
        open_folder_button = msg.addButton("Open Folder", QMessageBox.ActionRole)
        msg.addButton("OK", QMessageBox.AcceptRole)
        
        msg.exec()
        
        clicked_button = msg.clickedButton()
        if clicked_button == open_button:
            import subprocess
            import platform
            try:
                if platform.system() == "Windows":
                    subprocess.run(["start", pdf_path], shell=True)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", pdf_path])
                else:  # Linux
                    subprocess.run(["xdg-open", pdf_path])
            except Exception:
                pass
        elif clicked_button == open_folder_button:
            import subprocess
            import platform
            try:
                folder_path = str(Path(pdf_path).parent)
                if platform.system() == "Windows":
                    subprocess.run(["explorer", folder_path])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", folder_path])
                else:  # Linux
                    subprocess.run(["xdg-open", folder_path])
            except Exception:
                pass
    
    def export_error(self, error_message: str):
        """Handle export error."""
        self.progress_bar.setVisible(False)
        self.export_button.setEnabled(True)
        self.statusBar().showMessage("Export failed")
        QMessageBox.critical(self, "Export Error", f"Failed to export results:\n{error_message}")

    def toggle_coordinates(self):
        """Toggle between decimal and WGS 84 coordinate formats."""
        if not self.coordinates_decimal or not self.coordinates_wgs84:
            return
        
        self.showing_wgs84 = not self.showing_wgs84
        
        if self.showing_wgs84:
            # Switch to WGS 84
            self.coord_label.setText(f"📍 <b>Coordinates:</b> {html.escape(self.coordinates_wgs84)}")
            self.coord_label.copy_value = self.coordinates_wgs84
            self.toggle_button.setText("Decimal")
            self.toggle_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 3px; } QPushButton:hover { background-color: #218838; }")
        else:
            # Switch to decimal
            self.coord_label.setText(f"📍 <b>Coordinates:</b> {html.escape(self.coordinates_decimal)}")
            self.coord_label.copy_value = self.coordinates_decimal
            self.toggle_button.setText("WGS 84")
            self.toggle_button.setStyleSheet("QPushButton { background-color: #17a2b8; color: white; border: none; padding: 5px 10px; border-radius: 3px; } QPushButton:hover { background-color: #138496; }")
        
        self.statusBar().showMessage(f"Switched to {'WGS 84' if self.showing_wgs84 else 'Decimal'} format", 2000)
    
    def decimal_to_dms(self, decimal_degrees: float) -> tuple:
        """Convert decimal degrees to degrees, minutes, seconds."""
        # Handle negative values
        is_negative = decimal_degrees < 0
        decimal_degrees = abs(decimal_degrees)
        
        # Extract degrees, minutes, seconds
        degrees = int(decimal_degrees)
        minutes_decimal = (decimal_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        return degrees, minutes, seconds 