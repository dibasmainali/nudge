"""Generate app icon (icon.ico) from the mascot drawing code."""
import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QBuffer, QIODevice
from app.ui.icons import make_app_icon


def generate_icon():
    app = QApplication.instance() or QApplication([])
    icon = make_app_icon(False)
    sizes = [(16, 16), (20, 20), (24, 24), (32, 32), (40, 40),
             (48, 48), (64, 64), (128, 128), (256, 256)]
    pixmap = icon.pixmap(256, 256)
    buffer = QBuffer()
    if not buffer.open(QIODevice.WriteOnly):
        raise RuntimeError("Unable to open image buffer for writing")
    if not pixmap.save(buffer, "PNG"):
        raise RuntimeError("Unable to encode mascot icon as PNG")
    image = Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGBA")

    output_path = Path(__file__).parent / "icon.ico"
    image.save(str(output_path), format="ICO", sizes=sizes)
    print(f"Generated {output_path} with {len(sizes)} sizes")


if __name__ == "__main__":
    generate_icon()