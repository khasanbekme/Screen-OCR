import sys
import keyboard
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QPainter, QColor, QIcon
from PyQt5.QtCore import Qt, QRect
from PIL import ImageGrab, Image, ImageEnhance
import pytesseract
import clipboard

BASE_DIR = Path(__name__).resolve().parent

def extractText(image: Image) -> str:
    """Extracts text from the given image using pytesseract.

    Args:
        image (Image): The image to extract text from.

    Returns:
        str: The extracted text.
    """
    image = image.convert('L')  # Convert to grayscale
    image = ImageEnhance.Contrast(image).enhance(2.0)  # Enhance contrast
    text = pytesseract.image_to_string(image)
    return text


class TransparentWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_tray_icon()
        self.start_point = None
        self.end_point = None
        self.rect = self.screen().geometry()
        self.paint_visible = False

    def init_ui(self):
        """Initializes the UI settings."""
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setCursor(Qt.CrossCursor)

    def setup_tray_icon(self):
        """Sets up the system tray icon and its menu."""
        self.setWindowIcon(QIcon('icon.png'))
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.windowIcon())

        tray_menu = QMenu()
        exit_action = tray_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def mousePressEvent(self, event):
        self.start_point = event.pos()

    def mouseMoveEvent(self, event):
        self.end_point = event.pos()
        self.rect = QRect(self.start_point, self.end_point)
        self.repaint()  # Trigger a repaint

    def mouseReleaseEvent(self, event):
        self.end_point = event.pos()
        if self.start_point == self.end_point:
            self.close()
        self.rect = QRect(self.start_point, self.end_point)
        self.paint_visible = False
        self.repaint()
        coords = self.rect.getCoords()
        img = ImageGrab.grab(bbox=(
            min(coords[0], coords[2]), 
            min(coords[1], coords[3]), 
            max(coords[0], coords[2]), 
            max(coords[1], coords[3])
        ))
        clipboard.copy(extractText(img))
        self.hide()
    
    def paintEvent(self, event):
        if self.paint_visible:
            qp = QPainter(self)
            qp.setBrush(QColor(3, 61, 252, 70))
            qp.drawRect(self.rect)


def on_hotkey(widget: QWidget):
    widget.paint_visible = True
    widget.rect = widget.screen().geometry()
    widget.repaint()
    widget.showFullScreen()


if __name__ == '__main__':
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        pytesseract.pytesseract.tesseract_cmd = BASE_DIR / "Tesseract-OCR/tesseract"
    app = QApplication(sys.argv)
    tw = TransparentWidget()
    keyboard.add_hotkey('ctrl+alt+d', on_hotkey, args=(tw,))
    tw.showFullScreen()
    tw.hide()
    sys.exit(app.exec_())
