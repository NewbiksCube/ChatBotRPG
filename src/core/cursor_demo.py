import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QColorDialog, QCheckBox
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QBrush, QPen, QCursor, QPolygon

def create_themed_cursor(base_color, cursor_type="arrow", intensity=0.8, crt_effect=False):
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    color = QColor(base_color)
    if cursor_type == "arrow":
        for i in range(3, 0, -1):
            glow_color = QColor(color)
            glow_color.setAlphaF(0.2 * intensity / i)
            painter.setPen(QPen(glow_color, i * 2))
            painter.setBrush(QBrush(glow_color))
            points = [
                QPoint(2, 2), QPoint(2, 22), QPoint(8, 16), 
                QPoint(12, 20), QPoint(16, 16), QPoint(10, 10)
            ]
            polygon = QPolygon(points)
            painter.drawPolygon(polygon)
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(color))
        points = [
            QPoint(2, 2), QPoint(2, 22), QPoint(8, 16), 
            QPoint(12, 20), QPoint(16, 16), QPoint(10, 10)
        ]
        polygon = QPolygon(points)
        painter.drawPolygon(polygon)
    elif cursor_type == "hand":
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(8, 12, 12, 16)
        painter.drawRect(12, 6, 3, 10)
        painter.drawRect(9, 8, 3, 8)
        painter.drawRect(15, 8, 3, 8)
        painter.drawRect(6, 16, 3, 6)
    elif cursor_type == "resize_horizontal":
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        painter.drawLine(4, 16, 28, 16)
        painter.drawLine(4, 16, 8, 12)
        painter.drawLine(4, 16, 8, 20)
        painter.drawLine(28, 16, 24, 12)
        painter.drawLine(28, 16, 24, 20)
    elif cursor_type == "text":
        for i in range(2, 0, -1):
            glow_color = QColor(color)
            glow_color.setAlphaF(0.3 * intensity / i)
            painter.setPen(QPen(glow_color, i * 3))
            painter.drawLine(16, 6, 16, 26)
            painter.drawLine(13, 6, 19, 6)
            painter.drawLine(13, 26, 19, 26)
        painter.setPen(QPen(color, 2))
        painter.drawLine(16, 6, 16, 26)
        painter.drawLine(13, 6, 19, 6)
        painter.drawLine(13, 26, 19, 26)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(15, 5, 2, 2)
        painter.drawEllipse(15, 25, 2, 2)
    elif cursor_type == "splitter_right":
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        for i in range(2, 0, -1):
            glow_color = QColor(color)
            glow_color.setAlphaF(0.3 * intensity / i)
            painter.setPen(QPen(glow_color, i * 3))
            painter.setBrush(QBrush(glow_color))
            points = [
                QPoint(8, 10), QPoint(20, 16), QPoint(8, 22)
            ]
            polygon = QPolygon(points)
            painter.drawPolygon(polygon)
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(color))
        points = [
            QPoint(8, 10), QPoint(20, 16), QPoint(8, 22)
        ]
        polygon = QPolygon(points)
        painter.drawPolygon(polygon)
        painter.setPen(QPen(color, 2))
        painter.drawLine(6, 8, 6, 24)
        
    elif cursor_type == "splitter_left":
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        for i in range(2, 0, -1):
            glow_color = QColor(color)
            glow_color.setAlphaF(0.3 * intensity / i)
            painter.setPen(QPen(glow_color, i * 3))
            painter.setBrush(QBrush(glow_color))
            points = [
                QPoint(24, 10), QPoint(12, 16), QPoint(24, 22)
            ]
            polygon = QPolygon(points)
            painter.drawPolygon(polygon)
        painter.setPen(QPen(color, 1))
        painter.setBrush(QBrush(color))
        points = [
            QPoint(24, 10), QPoint(12, 16), QPoint(24, 22)
        ]
        polygon = QPolygon(points)
        painter.drawPolygon(polygon)
        painter.setPen(QPen(color, 2))
        painter.drawLine(26, 8, 26, 24)
    
    if crt_effect:
        num_lines = 16
        scanline_color = QColor(base_color).darker(150)
        scanline_color.setAlpha(70)
        painter.setPen(QPen(scanline_color, 1))
        for i in range(num_lines):
            y = i * 2 + (int(time.time() * 5) % 2)
            painter.drawLine(0, y, 32, y)
    painter.end()

    if cursor_type == "arrow":
        return QCursor(pixmap, 2, 2)
    elif cursor_type == "hand":
        return QCursor(pixmap, 12, 8)
    elif cursor_type == "resize_horizontal":
        return QCursor(pixmap, 16, 16)
    elif cursor_type == "text":
        return QCursor(pixmap, 16, 16)
    elif cursor_type == "splitter_right":
        return QCursor(pixmap, 14, 16)
    elif cursor_type == "splitter_left":
        return QCursor(pixmap, 18, 16)
    else:
        return QCursor(pixmap, 16, 16)


class CursorDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.current_color = "#00ff66"
        self.crt_effect_enabled = False
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Themed Cursor Demo')
        self.setGeometry(300, 300, 600, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                font-family: Arial;
                font-size: 12pt;
            }
            QPushButton {
                background-color: #333333;
                border: 2px solid #555555;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #444444;
                border-color: #777777;
            }
            QLabel {
                padding: 10px;
                border: 1px solid #555555;
                border-radius: 3px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout()
        title = QLabel("Themed Cursor Demo")
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        color_layout = QHBoxLayout()
        color_label = QLabel(f"Current Color: {self.current_color}")
        self.color_label = color_label
        color_button = QPushButton("Change Color")
        color_button.clicked.connect(self.pick_color)
        color_layout.addWidget(color_label)
        color_layout.addWidget(color_button)
        layout.addLayout(color_layout)
        crt_checkbox = QCheckBox("Enable CRT Effect on Cursor")
        crt_checkbox.toggled.connect(self.toggle_crt_effect)
        layout.addWidget(crt_checkbox)
        cursor_layout = QVBoxLayout()
        arrow_area = QLabel("ARROW CURSOR AREA\nMove your mouse here to see the themed arrow cursor")
        arrow_area.setAlignment(Qt.AlignCenter)
        arrow_area.setMinimumHeight(80)
        arrow_area.enterEvent = lambda e: self.set_cursor("arrow")
        cursor_layout.addWidget(arrow_area)
        hand_area = QLabel("HAND CURSOR AREA\nMove your mouse here to see the themed hand cursor")
        hand_area.setAlignment(Qt.AlignCenter)
        hand_area.setMinimumHeight(80)
        hand_area.enterEvent = lambda e: self.set_cursor("hand")
        cursor_layout.addWidget(hand_area)
        resize_area = QLabel("RESIZE CURSOR AREA\nMove your mouse here to see the themed resize cursor")
        resize_area.setAlignment(Qt.AlignCenter)
        resize_area.setMinimumHeight(80)
        resize_area.enterEvent = lambda e: self.set_cursor("resize_horizontal")
        cursor_layout.addWidget(resize_area)
        text_area = QLabel("TEXT CURSOR AREA\nMove your mouse here to see the themed text cursor")
        text_area.setAlignment(Qt.AlignCenter)
        text_area.setMinimumHeight(80)
        text_area.enterEvent = lambda e: self.set_cursor("text")
        cursor_layout.addWidget(text_area)
        splitter_layout = QHBoxLayout()
        left_splitter_area = QLabel("LEFT SPLITTER\n→ Right Arrow\n(Opens to right)")
        left_splitter_area.setAlignment(Qt.AlignCenter)
        left_splitter_area.setMinimumHeight(80)
        left_splitter_area.enterEvent = lambda e: self.set_cursor("splitter_right")
        splitter_layout.addWidget(left_splitter_area)
        right_splitter_area = QLabel("RIGHT SPLITTER\n← Left Arrow\n(Opens to left)")
        right_splitter_area.setAlignment(Qt.AlignCenter)
        right_splitter_area.setMinimumHeight(80)
        right_splitter_area.enterEvent = lambda e: self.set_cursor("splitter_left")
        splitter_layout.addWidget(right_splitter_area)
        cursor_layout.addLayout(splitter_layout)
        layout.addLayout(cursor_layout)
        instructions = QLabel("Instructions:\n• Move your mouse over different areas to see themed cursors\n• Click 'Change Color' to try different theme colors\n• The cursors will match your chosen color with a subtle glow effect\n• Text cursor has enhanced visibility with dots\n• Splitter cursors show directional arrows for UI panels")
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.setLayout(layout)
        self.set_cursor("arrow")
        
    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.current_color), self, "Choose Theme Color")
        if color.isValid():
            self.current_color = color.name()
            self.color_label.setText(f"Current Color: {self.current_color}")
            current_cursor_type = getattr(self, '_current_cursor_type', 'arrow')
            self.set_cursor(current_cursor_type)
            
    def toggle_crt_effect(self, checked):
        self.crt_effect_enabled = checked
        current_cursor_type = getattr(self, '_current_cursor_type', 'arrow')
        self.set_cursor(current_cursor_type)
        if self.crt_effect_enabled:
            self.start_crt_animation()
        else:
            self.stop_crt_animation()

    def update_crt_cursor(self):
        if self.crt_effect_enabled:
            current_cursor_type = getattr(self, '_current_cursor_type', 'arrow')
            self.set_cursor(current_cursor_type)

    def start_crt_animation(self):
        if not hasattr(self, 'crt_timer'):
            self.crt_timer = QTimer(self)
            self.crt_timer.timeout.connect(self.update_crt_cursor)
        self.crt_timer.start(100)

    def stop_crt_animation(self):
        if hasattr(self, 'crt_timer'):
            self.crt_timer.stop()

    def set_cursor(self, cursor_type):
        self._current_cursor_type = cursor_type
        themed_cursor = create_themed_cursor(self.current_color, cursor_type, 0.8, self.crt_effect_enabled)
        self.setCursor(themed_cursor)
        
    def leaveEvent(self, event):
        self.set_cursor("arrow")
        super().leaveEvent(event)


def main():
    app = QApplication(sys.argv)
    demo = CursorDemo()
    demo.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 