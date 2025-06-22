import html

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QScrollArea, QProgressBar, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap

from core.metadata import MetadataWorker, ConnectionTestWorker
from ui.widgets import DropArea, MapWidget, ClickableLabel

class ImageMetaLocator(QMainWindow):
    """Main application window"""
    
    def __init__(self, regular_font, bold_font):
        super().__init__()
        self.regular_font_family = regular_font
        self.bold_font_family = bold_font
        self.setWindowTitle("Image Meta Locator")
        self.setMinimumSize(1000, 700)
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
        self.image_preview.setStyleSheet("QLabel { border: 2px solid #dee2e6; border-radius: 8px; background-color: #f8f9fa; color: #6c757d; }")
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
        self.statusBar().setStyleSheet("background-color: #e9ecef; color: #212529;")
    
    def setup_styles(self):
        font_style = f"font-family: '{self.regular_font_family}';" if self.regular_font_family else ""
        self.setStyleSheet(f"QMainWindow {{ background-color: #f8f9fa; }} QWidget {{ {font_style} color: #212529; }}")
    
    def test_connection(self):
        self.connection_worker = ConnectionTestWorker()
        self.connection_worker.finished.connect(self.update_connection_status)
        self.connection_worker.start()

    def update_connection_status(self, is_online, message):
        self.connection_status_label.setText(f" {'🟢' if is_online else '🔴'} {message}")
        self.connection_status_label.setToolTip(f"Connection status: {message}")

    def process_image(self, image_path: str):
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
        while self.metadata_layout.count():
            child = self.metadata_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        font = QFont(self.regular_font_family, 11)
        if metadata.get('filename'):
            self.add_metadata_label(f"📷 <b>File:</b> {html.escape(metadata['filename'])}", font)
        if metadata.get('coordinates'):
            lat, lon = metadata['coordinates']
            self.add_metadata_label(f"📍 <b>Coordinates:</b> {lat:.6f}, {lon:.6f}", font)
            self.map_widget.show_location(lat, lon, metadata.get('address', ''))
        if metadata.get('address'):
            self.add_clickable_metadata("🗺️ <b>Address:</b>", metadata['address'], "Address", font)
        if metadata.get('date'):
            self.add_clickable_metadata("📅 <b>Date Taken:</b>", metadata['date'], "Date", font)
        if metadata.get('altitude') is not None:
            self.add_metadata_label(f"📏 <b>Altitude:</b> {metadata['altitude']:.2f} m", font)
            
    def add_metadata_label(self, text, font):
        label = QLabel(text)
        label.setFont(font)
        label.setWordWrap(True)
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