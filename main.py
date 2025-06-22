import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from ui.main_window import ImageMetaLocator
from utils.resources import load_fonts, get_app_icon

def main():
    """Main function to initialize and run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Image Meta Locator")
    app.setApplicationVersion("1.0")

    # Load custom fonts and application icon
    regular_font, bold_font = load_fonts()
    if regular_font:
        app.setFont(QFont(regular_font))

    icon = get_app_icon()
    if icon:
        app.setWindowIcon(icon)
    
    # Create and show the main window
    window = ImageMetaLocator(regular_font, bold_font)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
