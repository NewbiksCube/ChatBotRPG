from PyQt5.QtWidgets import QSplashScreen, QApplication
from PyQt5.QtCore import Qt, QSettings, QRect
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen
import random

class SplashScreen(QSplashScreen):
    def __init__(self, message="Loading ChatBot RPG", width=900, height=600, bg_color="#121218", fg_color="#00FF66"):
        self._base_message = message
        self._title = "CHATBOT RPG"
        self._subtitle = "Text Adventure Platform"
        settings = QSettings("ChatBotRPG", "ChatBotRPG")
        last_active_tab = settings.value("lastActiveTabName", "", type=str)
        if last_active_tab:
            import os
            data_dirs = ["data/Combat Arena", "data/Goldsprings", "data/New RPG", "data/Post-Apocalyptic"]
            for data_dir in data_dirs:
                if last_active_tab.lower() in data_dir.lower():
                    tab_settings_file = os.path.join(data_dir, "tab_settings.json")
                    if os.path.exists(tab_settings_file):
                        try:
                            import json
                            with open(tab_settings_file, 'r') as f:
                                tab_settings = json.load(f)
                                fg_color = tab_settings.get('base_color', fg_color)
                                break
                        except:
                            pass
        self._fg_color = fg_color
        pixmap = self._create_splash_pixmap(width, height)
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        self.setMask(pixmap.mask())
    def _create_splash_pixmap(self, width, height):
        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(pixmap.rect(), QColor("#121218"))
        painter.setFont(QFont('Consolas', 14))
        char_color = QColor(self._fg_color)
        char_color.setAlpha(40)
        painter.setPen(char_color)
        chars = [
            '0', '1', 'A', 'E', 'F', 'G', 'H', 'K', 'M', 'N', 'R', 'T', 'V', 'X', 'Z',
            '@', '#', '$', '%', '&', '*', '=', '+', '-',
            '∆', 'Ω', 'Σ', 'Λ', 'Ψ', 'Φ', 'Ξ', '∑', '∇', '∂', 'µ', 'π', 'λ', 'ω',
            'ｱ', 'ｳ', 'ｶ', 'ｸ', 'ｹ', 'ｺ',
            'ᚠ', 'ᚢ', 'ᚦ', 'ᚨ', 'ᚱ', 'ᚲ', 'ᚷ', 'ᚹ', 'ᛉ', 'ᛋ', 'ᛏ', 'ᛒ', 'ᛗ', 'ᛚ', 'ᛝ', 'ᛟ', 'ᛞ',
            '𐍈', '𐌰', '𐌱', '𐌲', '𐌳', '𐌴', '𐌵', '𐌶', '𐌷', '𐌸', '𐌹', '𐌺', '𐌻', '𐌼', '𐌽', '𐌾', '𐌿',
            '✦', '✧', '✩', '✫', '✬', '✭', '✮', '✯', '✰', '✶', '✷', '✸', '✹', '✺', '✻', '✼', '✽', '✾', '✿'
        ]
        for i in range(150):
            x = random.randint(0, width)
            y = random.randint(0, height)
            char = random.choice(chars)
            painter.drawText(x, y, char)
        title_font = QFont('Consolas', 52, QFont.Bold)
        painter.setFont(title_font)
        glow_color = QColor(self._fg_color)
        glow_color.setAlpha(60)
        for offset in range(1, 4):
            painter.setPen(QPen(glow_color, offset * 2))
            title_rect = QRect(0, height // 2 - 100, width, 80)
            painter.drawText(title_rect, Qt.AlignHCenter | Qt.AlignVCenter, self._title)
        painter.setPen(QColor(self._fg_color))
        title_rect = QRect(0, height // 2 - 100, width, 80)
        painter.drawText(title_rect, Qt.AlignHCenter | Qt.AlignVCenter, self._title)
        subtitle_font = QFont('Consolas', 18, QFont.Normal)
        painter.setFont(subtitle_font)
        subtitle_color = QColor(self._fg_color)
        subtitle_color.setAlpha(180)
        painter.setPen(subtitle_color)
        subtitle_rect = QRect(0, height // 2 - 40, width, 30)
        painter.drawText(subtitle_rect, Qt.AlignHCenter | Qt.AlignVCenter, self._subtitle)
        loading_font = QFont('Consolas', 16, QFont.Normal)
        painter.setFont(loading_font)
        loading_color = QColor(self._fg_color)
        loading_color.setAlpha(220)
        painter.setPen(loading_color)
        loading_text = f"[ {self._base_message}... ]"
        loading_rect = QRect(0, height // 2 + 20, width, 30)
        painter.drawText(loading_rect, Qt.AlignHCenter | Qt.AlignVCenter, loading_text)
        bracket_color = QColor(self._fg_color)
        bracket_color.setAlpha(120)
        painter.setPen(QPen(bracket_color, 3))
        painter.drawLine(30, 30, 80, 30)
        painter.drawLine(30, 30, 30, 80)
        painter.drawLine(width - 80, 30, width - 30, 30)
        painter.drawLine(width - 30, 30, width - 30, 80)
        painter.drawLine(30, height - 80, 30, height - 30)
        painter.drawLine(30, height - 30, 80, height - 30)
        painter.drawLine(width - 30, height - 80, width - 30, height - 30)
        painter.drawLine(width - 80, height - 30, width - 30, height - 30)
        scan_color = QColor(self._fg_color)
        scan_color.setAlpha(80)
        painter.setPen(QPen(scan_color, 2))
        scan_y = height // 2 + 60
        painter.drawLine(0, scan_y, width, scan_y)
        painter.setPen(Qt.NoPen)
        particle_color = QColor(self._fg_color)
        particle_color.setAlpha(100)
        painter.setBrush(particle_color)
        for _ in range(50):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 3)
            painter.drawEllipse(x, y, size, size)
        painter.end()
        return pixmap
    def show_and_center(self, app: QApplication, settings: QSettings = None):
        self.show()
        app.processEvents()
        desktop = app.desktop()
        screen_rect = desktop.screenGeometry()
        self.move(screen_rect.center() - self.rect().center())
    def finish(self, main_window):
        super().finish(main_window)
    def stop_animation(self):
        pass 
        pass 
