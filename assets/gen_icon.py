"""Generate app icon (icon.ico) from the mascot drawing code."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap, QImage
from PySide6.QtCore import QBuffer, QIODevice
from app.ui.icons import make_app_icon


def generate_icon():
    app = QApplication.instance() or QApplication([])
    icon = make_app_icon(False)
    sizes = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    pixmaps = []
    for s in sizes:
        pm = icon.pixmap(s, s)
        pixmaps.append(pm)

    # Save as .ico with multiple sizes using QImage
    output_path = Path(__file__).parent / "icon.ico"

    # QIcon can save multi-resolution ICO directly
    icon_to_save = QIcon()
    for pm in pixmaps:
        icon_to_save.addPixmap(pm)

    # Use QImage to save ICO with multiple resolutions
    # Actually, QIcon doesn't have a direct save method. Use QPixmap approach.
    # For ICO, we need to use a workaround - save the largest as ICO and hope Qt embeds others
    # Or use PIL/Pillow if available. Let's try with the largest pixmap.
    pixmaps[-1].save(str(output_path), "ICO")
    print(f"Generated {output_path}")


if __name__ == "__main__":
    generate_icon()