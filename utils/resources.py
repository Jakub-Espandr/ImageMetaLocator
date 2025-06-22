import os
import sys
from PySide6.QtGui import QIcon, QFontDatabase
from pathlib import Path

def get_asset_path(asset_type, asset_name=""):
    """Constructs the full path to an asset."""
    try:
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys._MEIPASS)
        else:
            # __file__ is resources.py, which is in utils/. We need the parent of utils/.
            base_dir = Path(__file__).parent.parent

        asset_path = base_dir / "assets" / asset_type / asset_name
        return asset_path
    except Exception:
        return Path("assets") / asset_type / asset_name

def get_app_icon():
    """Gets the application icon, choosing the best format for the OS."""
    try:
        if sys.platform == "darwin":
            icon_path = get_asset_path("icons", "icon.icns")
        else:
            icon_path = get_asset_path("icons", "icon.ico")

        print(f"DEBUG: Attempting to load icon from: {icon_path.resolve()}")
        if icon_path and icon_path.exists():
            print("SUCCESS: Application icon found.")
            return QIcon(str(icon_path))
        else:
            print("WARNING: Application icon not found at the specified path.")
            return None
    except Exception as e:
        print(f"ERROR: Could not load application icon: {e}")
        return None

def load_fonts():
    """Loads all custom fonts from the assets/fonts directory."""
    fonts_dir = get_asset_path("fonts")
    print(f"DEBUG: Attempting to load fonts from: {fonts_dir.resolve()}")

    if not fonts_dir.exists():
        print(f"WARNING: Fonts directory not found at {fonts_dir.resolve()}")
        return None, None

    regular_family, bold_family = None, None

    regular_font_path = fonts_dir / "fccTYPO-Regular.ttf"
    if regular_font_path.exists():
        regular_id = QFontDatabase.addApplicationFont(str(regular_font_path))
        if regular_id != -1:
            families = QFontDatabase.applicationFontFamilies(regular_id)
            if families:
                regular_family = families[0]
                print(f"SUCCESS: Loaded font '{regular_family}'")
        else:
            print(f"WARNING: Failed to load regular font from {regular_font_path}")
    else:
        print(f"WARNING: Regular font file not found: {regular_font_path}")

    bold_font_path = fonts_dir / "fccTYPO-Bold.ttf"
    if bold_font_path.exists():
        bold_id = QFontDatabase.addApplicationFont(str(bold_font_path))
        if bold_id != -1:
            families = QFontDatabase.applicationFontFamilies(bold_id)
            if families:
                bold_family = families[0]
                print(f"SUCCESS: Loaded font '{bold_family}'")
        else:
            print(f"WARNING: Failed to load bold font from {bold_font_path}")
    else:
        print(f"WARNING: Bold font file not found: {bold_font_path}")

    return regular_family, bold_family 