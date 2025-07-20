from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt

def get_display_name_from_setting(setting_name):
    if not setting_name or setting_name == "--":
        return "--"
    parts = setting_name.split(',')
    return parts[-1].strip() if parts else setting_name

class TopSplitterWidget(QWidget):
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.setObjectName("TopSplitterContainer")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        placeholder_label = QLabel("Top Splitter Content")
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setObjectName("TopSplitterLabel")
        placeholder_label.setSizePolicy(placeholder_label.sizePolicy().horizontalPolicy(), QSizePolicy.Ignored)
        layout.addWidget(placeholder_label)
        self.setLayout(layout)
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self.location_label = placeholder_label

    def set_location_text(self, text):
        if hasattr(self, 'location_label') and self.location_label:
            display_name = get_display_name_from_setting(text)
            self.location_label.setText(display_name)

    def update_theme(self, new_theme):
        self.theme_colors = new_theme.copy()
        pass 
