from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QButtonGroup
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from rules.timer_rules_manager import TimerRulesWidget
from core.utils import is_valid_widget

class RulesToggleManager(QWidget):
    rules_type_changed = pyqtSignal(str)
    def __init__(self, theme_colors, standard_rules_widget=None, parent=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.standard_rules_widget = standard_rules_widget
        self.setObjectName("RulesToggleManager")
        self._init_ui()
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        toggle_container = QWidget()
        toggle_container.setObjectName("RulesToggleContainer")
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(5, 5, 5, 5)
        self.toggle_group = QButtonGroup(self)
        self.standard_rules_btn = QPushButton("Chat Triggers")
        self.standard_rules_btn.setObjectName("StandardRulesToggleButton")
        self.standard_rules_btn.setCheckable(True)
        self.standard_rules_btn.setChecked(True)
        self.standard_rules_btn.setMinimumHeight(30)
        self.standard_rules_btn.setFont(QFont('Consolas', 10))
        self.standard_rules_btn.setFocusPolicy(Qt.NoFocus)
        self.timer_rules_btn = QPushButton("Timer Triggers")
        self.timer_rules_btn.setObjectName("TimerRulesToggleButton")
        self.timer_rules_btn.setCheckable(True)
        self.timer_rules_btn.setMinimumHeight(30)
        self.timer_rules_btn.setFont(QFont('Consolas', 10))
        self.timer_rules_btn.setFocusPolicy(Qt.NoFocus)
        self.toggle_group.addButton(self.standard_rules_btn)
        self.toggle_group.addButton(self.timer_rules_btn)
        toggle_layout.addWidget(self.standard_rules_btn)
        toggle_layout.addWidget(self.timer_rules_btn)
        main_layout.addWidget(toggle_container)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("RulesContentStack")
        if not self.standard_rules_widget:
            self.standard_rules_widget = QWidget()
            self.standard_rules_widget.setObjectName("StandardRulesPlaceholder")
        self.timer_rules_widget = TimerRulesWidget(theme_colors=self.theme_colors)
        self.content_stack.addWidget(self.standard_rules_widget)
        self.content_stack.addWidget(self.timer_rules_widget)
        self.content_stack.setCurrentIndex(0)
        main_layout.addWidget(self.content_stack)
        self.standard_rules_btn.toggled.connect(self._on_standard_rules_toggle)
        self.timer_rules_btn.toggled.connect(self._on_timer_rules_toggle)
        self._apply_theme()
    def _on_standard_rules_toggle(self, checked):
        if checked:
            self.content_stack.setCurrentIndex(0)
            self.rules_type_changed.emit("standard")
    def _on_timer_rules_toggle(self, checked):
        if checked:
            self.content_stack.setCurrentIndex(1)
            self.rules_type_changed.emit("timer")
    def _apply_theme(self):
        if not self.theme_colors:
            return
        base_color = self.theme_colors.get('base_color', '#00FF66')
        bg_color = self.theme_colors.get('bg_color', '#2C2C2C')
        darker_bg = self.theme_colors.get('darker_bg', '#1E1E1E')
        button_style = f"""
            QPushButton {{
                color: {base_color};
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 5px;
            }}
            QPushButton:checked {{
                color: {darker_bg};
                background-color: {base_color};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {base_color};
                color: {darker_bg};
            }}
        """
        self.standard_rules_btn.setStyleSheet(button_style)
        self.timer_rules_btn.setStyleSheet(button_style)
        if is_valid_widget(self.timer_rules_widget):
            self.timer_rules_widget.update_theme(self.theme_colors)
    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        self._apply_theme()
    def set_standard_rules_widget(self, widget):
        if not is_valid_widget(widget):
            return False
        old_widget = self.content_stack.widget(0)
        if old_widget:
            self.content_stack.removeWidget(old_widget)
        self.standard_rules_widget = widget
        self.content_stack.insertWidget(0, widget)
        if self.standard_rules_btn.isChecked():
            self.content_stack.setCurrentIndex(0)
        return True
    def get_current_rules_type(self):
        return "standard" if self.standard_rules_btn.isChecked() else "timer"
    def set_active_rules_type(self, rules_type):
        if rules_type.lower() == "standard":
            self.standard_rules_btn.setChecked(True)
        elif rules_type.lower() == "timer":
            self.timer_rules_btn.setChecked(True)
    def get_timer_rules_widget(self):
        return self.timer_rules_widget 
