from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, 
    QPushButton, QColorDialog, QTextEdit, QSlider, QWidget, QVBoxLayout,
    QCheckBox, QDoubleSpinBox, QSpacerItem, QSizePolicy, QComboBox
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QBrush, QPen, QCursor, QPolygon
from core.tab_manager import TabManagerWidget
from core.apply_stylesheet import generate_and_apply_stylesheet
from core.ui_widgets import ChatMessageWidget, ChatMessageListWidget
from editor_panel.world_editor.world_editor import WorldEditorWidget
from editor_panel.start_conditions_manager import StartConditionsManagerWidget
from config import get_default_model, get_default_cot_model, get_openrouter_api_key, get_openrouter_base_url, get_current_service, get_api_key_for_service, get_base_url_for_service


def create_themed_cursor(base_color, cursor_type="arrow", intensity=0.8):
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
        
    elif cursor_type == "resize_vertical":
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        painter.drawLine(16, 4, 16, 28)
        painter.drawLine(16, 4, 12, 8)
        painter.drawLine(16, 28, 12, 24)
        painter.drawLine(16, 28, 20, 24)
        
    elif cursor_type == "resize_diagonal_1":
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        painter.drawLine(6, 6, 26, 26)
        painter.drawLine(6, 6, 10, 6)
        painter.drawLine(6, 6, 6, 10)
        painter.drawLine(26, 26, 22, 26)
        painter.drawLine(26, 26, 26, 22)
        
    elif cursor_type == "resize_diagonal_2":
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        painter.drawLine(26, 6, 6, 26)
        painter.drawLine(26, 6, 22, 6)
        painter.drawLine(26, 6, 26, 10)
        painter.drawLine(6, 26, 10, 26)
        painter.drawLine(6, 26, 6, 22)
        
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
    painter.end()
    if cursor_type == "arrow":
        return QCursor(pixmap, 2, 2)
    elif cursor_type == "hand":
        return QCursor(pixmap, 12, 8)
    elif cursor_type in ["resize_horizontal", "resize_vertical", "resize_diagonal_1", "resize_diagonal_2"]:
        return QCursor(pixmap, 16, 16)
    elif cursor_type == "text":
        return QCursor(pixmap, 16, 16)
    elif cursor_type == "splitter_right":
        return QCursor(pixmap, 14, 16)
    elif cursor_type == "splitter_left":
        return QCursor(pixmap, 18, 16)
    else:
        return QCursor(pixmap, 16, 16)


def create_cursor_set(base_color, intensity=0.8):
    return {
        'arrow': create_themed_cursor(base_color, "arrow", intensity),
        'hand': create_themed_cursor(base_color, "hand", intensity),
        'resize_horizontal': create_themed_cursor(base_color, "resize_horizontal", intensity),
        'resize_vertical': create_themed_cursor(base_color, "resize_vertical", intensity),
        'resize_diagonal_1': create_themed_cursor(base_color, "resize_diagonal_1", intensity),
        'resize_diagonal_2': create_themed_cursor(base_color, "resize_diagonal_2", intensity),
        'text': create_themed_cursor(base_color, "text", intensity),
        'splitter_right': create_themed_cursor(base_color, "splitter_right", intensity),
        'splitter_left': create_themed_cursor(base_color, "splitter_left", intensity)
    }


def _update_all_world_editors(widget, theme):
    if isinstance(widget, WorldEditorWidget):
        widget.update_theme(theme)
    if hasattr(widget, 'children'):
        for child in widget.children():
            if hasattr(child, 'setObjectName'):
                _update_all_world_editors(child, theme)

def update_ui_colors(chatbot_ui_instance, theme_colors):
    base_color = theme_colors.get("base_color", "#CCCCCC")
    contrast = theme_colors.get("contrast", 0.35)
    bg_value = int(80 * contrast)
    theme_colors["bg_color"] = f"#{bg_value:02x}{bg_value:02x}{bg_value:02x}"
    theme_colors["darker_bg"] = f"#{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}"
    theme_colors["highlight"] = "rgba(204, 204, 204, 0.6)"
    theme_colors["brighter"] = "rgba(234, 234, 234, 0.8)"
    if hasattr(chatbot_ui_instance, '_last_theme') and chatbot_ui_instance._last_theme == theme_colors:
        return
    chatbot_ui_instance._last_theme = theme_colors.copy()
    intensity = theme_colors.get("intensity", 0.8)
    themed_cursors = create_cursor_set(base_color, intensity)
    chatbot_ui_instance.themed_cursors = themed_cursors
    chatbot_ui_instance.setCursor(themed_cursors['arrow'])
    new_theme = theme_colors
    if hasattr(chatbot_ui_instance, 'tab_widget') and isinstance(chatbot_ui_instance.tab_widget, TabManagerWidget):
        chatbot_ui_instance.tab_widget.update_theme(new_theme)
        for i in range(chatbot_ui_instance.tab_widget.count()):
            tab_widget = chatbot_ui_instance.tab_widget.widget(i)
            _update_all_world_editors(tab_widget, new_theme)
    generate_and_apply_stylesheet(chatbot_ui_instance, new_theme)
    window_bg_style = f"ChatbotUI {{ background-color: {base_color}; }}"
    chatbot_ui_instance.setStyleSheet(window_bg_style)
    if hasattr(chatbot_ui_instance, 'tabs_data'):
        for i, tab_data in enumerate(chatbot_ui_instance.tabs_data):
            if tab_data:
                if 'output' in tab_data and isinstance(tab_data['output'], ChatMessageListWidget):
                    chat_list_widget = tab_data['output']
                    chat_list_widget.update_theme(new_theme)
                    container_layout = chat_list_widget.container.layout()
                    if container_layout:
                        for j in range(container_layout.count()):
                            item = container_layout.itemAt(j)
                            if item and item.widget() and isinstance(item.widget(), ChatMessageWidget):
                                msg_widget = item.widget()
                                try:
                                    msg_widget.update_theme(new_theme)
                                except Exception as e:
                                    pass
                if 'input' in tab_data and tab_data['input']:
                    input_widget = tab_data['input']
                    if hasattr(input_widget, 'text_input') and hasattr(chatbot_ui_instance, 'themed_cursors'):
                        text_cursor = chatbot_ui_instance.themed_cursors.get('text')
                        if text_cursor:
                            input_widget.text_input.setCursor(text_cursor)
                    elif hasattr(chatbot_ui_instance, 'themed_cursors'):
                        text_cursor = chatbot_ui_instance.themed_cursors.get('text')
                        if text_cursor:
                            input_widget.setCursor(text_cursor)
                    if hasattr(input_widget, '_chargen_widget') and input_widget._chargen_widget:
                        try:
                            input_widget._chargen_widget.update_theme(new_theme)
                        except Exception as e:
                            pass
                if 'start_conditions_manager_widget' in tab_data and isinstance(tab_data['start_conditions_manager_widget'], StartConditionsManagerWidget):
                    try:
                        tab_data['start_conditions_manager_widget'].update_theme(new_theme)
                    except Exception as e:
                         pass
                if 'timer_rules_widget' in tab_data and tab_data['timer_rules_widget']:
                    try:
                        tab_data['timer_rules_widget'].update_theme(new_theme)
                    except Exception as e:
                        pass
                if 'notes_manager_widget' in tab_data and tab_data['notes_manager_widget']:
                    try:
                        tab_data['notes_manager_widget'].update_theme(new_theme)
                    except Exception as e:
                        pass
                if 'rules_toggle_manager' in tab_data and tab_data['rules_toggle_manager']:
                    try:
                        tab_data['rules_toggle_manager'].update_theme(new_theme)
                    except Exception as e:
                        pass
            else:
                pass


class ThemeCustomizationDialog(QDialog):
    
    def __init__(self, parent=None, current_theme=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowTitle("Theme Customizer")
        self.current_theme = current_theme or {
            "base_color": "#00ff66",
            "intensity": 0.8,
            "contrast": 0.35,
            "streaming_enabled": False,
            "streaming_speed": 50,
            "crt_enabled": True,
            "crt_speed": 120
        }
        self.result_theme = self.current_theme.copy()
        self._drag_position = None
        bg_value = int(80 * self.current_theme["contrast"])
        self.bg_color = f"#{bg_value:02x}{bg_value:02x}{bg_value:02x}"
        darker_bg = f"#{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.bg_color};
                color: {self.current_theme["base_color"]};
                border: 1px solid {self.current_theme["base_color"]};
                border-radius: 3px;
            }}
            QWidget#TitleBar {{
                background-color: {darker_bg};
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                border-bottom: 1px solid {self.current_theme["base_color"]};
            }}
            QLabel#TitleLabel {{
                color: {self.current_theme["base_color"]};
                font-weight: bold;
            }}
            QLabel {{
                color: {self.current_theme["base_color"]};
            }}
            QPushButton#CloseButton {{
                background-color: transparent;
                color: {self.current_theme["base_color"]};
                border: none;
                font-size: 16px;
                font-weight: bold;
                border-radius: 12px;
            }}
            QPushButton#CloseButton:hover {{
                color: rgba({QColor(self.current_theme["base_color"]).red()}, {QColor(self.current_theme["base_color"]).green()}, {QColor(self.current_theme["base_color"]).blue()}, 1.0);
                background-color: rgba({QColor(self.current_theme["base_color"]).red()}, {QColor(self.current_theme["base_color"]).green()}, {QColor(self.current_theme["base_color"]).blue()}, 0.2);
            }}
            QPushButton {{ 
                color: {self.current_theme["base_color"]}; 
                background-color: {darker_bg}; 
                border: 1px solid {self.current_theme["base_color"]}; 
                padding: 5px; 
                border-radius: 3px;
            }}
            QPushButton:hover {{ 
                background-color: rgba({QColor(self.current_theme["base_color"]).red()}, 
                                     {QColor(self.current_theme["base_color"]).green()}, 
                                     {QColor(self.current_theme["base_color"]).blue()}, 0.3); 
            }}
            QTextEdit {{ /* Style all QTextEdits for consistency */
                color: {self.current_theme["base_color"]};
                background-color: {darker_bg};
                border: 1px solid {self.current_theme["base_color"]};
                selection-background-color: rgba({QColor(self.current_theme["base_color"]).red()}, {QColor(self.current_theme["base_color"]).green()}, {QColor(self.current_theme["base_color"]).blue()}, 0.5);
                selection-color: white;
                border-radius: 3px;
                font: 12pt "Arial"; /* Match main model font */
            }}
            QTextEdit#ModelInput, QTextEdit#CoTModelInput {{ /* Can be specific if needed */
                /* Inherits default QTextEdit style */
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {self.current_theme["base_color"]};
                height: 8px;
                background: {darker_bg};
                margin: 2px 0;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {self.current_theme["base_color"]};
                border: 1px solid {self.current_theme["base_color"]};
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }}
            /* Add style for QCheckBox */
            QCheckBox {{
                color: {self.current_theme["base_color"]};
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 13px;
                height: 13px;
                border: 1px solid {self.current_theme["base_color"]};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.current_theme["base_color"]};
            }}
            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid rgba({QColor(self.current_theme["base_color"]).red()}, {QColor(self.current_theme["base_color"]).green()}, {QColor(self.current_theme["base_color"]).blue()}, 0.7);
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: rgba({QColor(self.current_theme["base_color"]).red()}, {QColor(self.current_theme["base_color"]).green()}, {QColor(self.current_theme["base_color"]).blue()}, 0.7);
                border: 1px solid {self.current_theme["base_color"]};
            }}
        """)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.initUI()
        
    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(30)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 5, 0)
        title_label = QLabel("Theme Customizer")
        title_label.setObjectName("TitleLabel")
        title_label.setFont(QFont('Arial', 10, QFont.Bold))
        close_button = QPushButton("×")
        close_button.setObjectName("CloseButton")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self._close_with_sound)
        def close_mouse_press(event):
            if hasattr(self, 'parent') and self.parent():
                parent = self.parent()
                if hasattr(parent, 'medium_click_sound') and parent.medium_click_sound:
                    try:
                        parent.medium_click_sound.play()
                    except Exception as e:
                        print(f"Error playing medium_click_sound: {e}")
            QPushButton.mousePressEvent(close_button, event)
        close_button.mousePressEvent = close_mouse_press
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(title_bar)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        api_section_label = QLabel("API Configuration:")
        api_section_label.setFont(QFont('Arial', 12, QFont.Bold))
        content_layout.addWidget(api_section_label)
        
        service_layout = QHBoxLayout()
        self.service_label = QLabel("Service:")
        self.service_label.setFont(QFont('Arial', 12))
        self.service_dropdown = QComboBox()
        self.service_dropdown.setFont(QFont('Arial', 12))
        self.service_dropdown.addItems(["OpenRouter", "Google GenAI", "Local API"])
        current_service = get_current_service()
        if current_service == "openrouter":
            self.service_dropdown.setCurrentText("OpenRouter")
        elif current_service == "google":
            self.service_dropdown.setCurrentText("Google GenAI")
        elif current_service == "local":
            self.service_dropdown.setCurrentText("Local API")
        self.service_dropdown.currentTextChanged.connect(self.update_service)
        service_layout.addWidget(self.service_label)
        service_layout.addWidget(self.service_dropdown)
        service_layout.addStretch(1)
        content_layout.addLayout(service_layout)
        
        api_key_layout = QHBoxLayout()
        self.api_key_label = QLabel("API Key:")
        self.api_key_label.setFont(QFont('Arial', 12))
        self.api_key_input = QTextEdit()
        self.api_key_input.setObjectName("ApiKeyInput")
        self.api_key_input.setMaximumHeight(40)
        self.api_key_input.setFont(QFont('Arial', 12))
        self.api_key_input.setPlaceholderText("Enter your API key (hidden)")
        self.api_key_input.setStyleSheet("QTextEdit { color: #666666; }")
        self.api_key_input.textChanged.connect(self.update_api_key)
        self.api_key_input.focusInEvent = lambda event: self._handle_api_key_focus()
        self.api_key_input.focusOutEvent = lambda event: self._handle_api_key_blur()
        self.api_key_modified = False
        self.original_api_key = None
        self.modified_api_key = None
        current_service = get_current_service()
        current_api_key = get_api_key_for_service(current_service) or ""
        if current_api_key:
            self.api_key_input.setText("*" * len(current_api_key))
        self.api_key_input.setToolTip("Click to edit API key")
        api_key_layout.addWidget(self.api_key_label)
        api_key_layout.addWidget(self.api_key_input, 1)
        content_layout.addLayout(api_key_layout)
        
        api_url_layout = QHBoxLayout()
        self.api_url_label = QLabel("API Base URL:")
        self.api_url_label.setFont(QFont('Arial', 12))
        self.api_url_input = QTextEdit()
        self.api_url_input.setObjectName("ApiUrlInput")
        self.api_url_input.setMaximumHeight(40)
        self.api_url_input.setFont(QFont('Arial', 12))
        self.api_url_input.setPlaceholderText("e.g., https://openrouter.ai/api/v1 or http://127.0.0.1:1234/v1")
        self.api_url_input.textChanged.connect(self.update_api_url)
        current_service = get_current_service()
        current_api_url = get_base_url_for_service(current_service) or ""
        self.api_url_input.setText(current_api_url)
        api_url_layout.addWidget(self.api_url_label)
        api_url_layout.addWidget(self.api_url_input, 1)
        content_layout.addLayout(api_url_layout)
        
        model_temp_layout = QHBoxLayout()
        self.model_label = QLabel("Model:")
        self.model_label.setFont(QFont('Arial', 12))
        self.model_input = QTextEdit()
        self.model_input.setObjectName("ModelInput")
        self.model_input.setMaximumHeight(40)
        self.model_input.setFont(QFont('Arial', 12))
        self.model_input.setText(self.current_theme.get("model", get_default_model()))
        self.model_input.textChanged.connect(self.update_model)
        self.temperature_label = QLabel("Temperature:")
        self.temperature_label.setFont(QFont('Arial', 12))
        self.temperature_spinbox = QDoubleSpinBox()
        self.temperature_spinbox.setRange(0.0, 1.2)
        self.temperature_spinbox.setSingleStep(0.1)
        self.temperature_spinbox.setFont(QFont('Arial', 12))
        self.temperature_spinbox.setValue(self.current_theme.get("temperature", 0.5))
        self.temperature_spinbox.valueChanged.connect(self.update_temperature)
        model_temp_layout.addWidget(self.model_label)
        model_temp_layout.addWidget(self.model_input, 1)
        model_temp_layout.addWidget(self.temperature_label)
        model_temp_layout.addWidget(self.temperature_spinbox)
        content_layout.addLayout(model_temp_layout)
        cot_model_layout = QHBoxLayout()
        self.cot_model_label = QLabel("CoT Model:")
        self.cot_model_label.setFont(QFont('Arial', 12))
        self.cot_model_input = QTextEdit()
        self.cot_model_input.setObjectName("CoTModelInput")
        self.cot_model_input.setMaximumHeight(40)
        self.cot_model_input.setFont(QFont('Arial', 12))
        self.cot_model_input.setText(self.current_theme.get("cot_model", get_default_cot_model()))
        self.cot_model_input.textChanged.connect(self.update_cot_model)
        cot_model_layout.addWidget(self.cot_model_label)
        cot_model_layout.addWidget(self.cot_model_input, 1)
        content_layout.addLayout(cot_model_layout)
        
        color_layout = QHBoxLayout()
        self.color_label = QLabel("Base Color:")
        self.color_label.setFont(QFont('Arial', 12))
        self.color_btn = QPushButton("")
        self.color_btn.setFixedSize(60, 30)
        self.color_btn.setStyleSheet(f"background-color: {self.current_theme['base_color']}; border: 2px solid {self.current_theme['base_color']};")
        self.color_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch(1)
        content_layout.addLayout(color_layout)
        intensity_layout = QHBoxLayout()
        self.intensity_label = QLabel("Color Intensity:")
        self.intensity_label.setFont(QFont('Arial', 12))
        self.intensity_slider = QSlider(Qt.Horizontal)
        self.intensity_slider.setRange(30, 100)
        self.intensity_slider.setValue(int(self.current_theme["intensity"] * 100))
        self.intensity_slider.valueChanged.connect(self.update_intensity)
        self.intensity_value = QLabel(f"{self.current_theme['intensity']:.2f}")
        self.intensity_value.setFont(QFont('Arial', 12))
        self.intensity_value.setAlignment(Qt.AlignCenter)
        self.intensity_value.setFixedWidth(50)
        intensity_layout.addWidget(self.intensity_label)
        intensity_layout.addWidget(self.intensity_slider, 1)
        intensity_layout.addWidget(self.intensity_value)
        content_layout.addLayout(intensity_layout)
        contrast_layout = QHBoxLayout()
        self.contrast_label = QLabel("Background Brightness:")
        self.contrast_label.setFont(QFont('Arial', 12))
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(10, 80)
        self.contrast_slider.setValue(int(self.current_theme["contrast"] * 100))
        self.contrast_slider.valueChanged.connect(self.update_contrast)
        self.contrast_value = QLabel(f"{self.current_theme['contrast']:.2f}")
        self.contrast_value.setFont(QFont('Arial', 12))
        self.contrast_value.setAlignment(Qt.AlignCenter)
        self.contrast_value.setFixedWidth(50)
        contrast_layout.addWidget(self.contrast_label)
        contrast_layout.addWidget(self.contrast_slider, 1)
        contrast_layout.addWidget(self.contrast_value)
        content_layout.addLayout(contrast_layout)
        streaming_check_layout = QHBoxLayout()
        self.streaming_label = QLabel("Streaming Effect:")
        self.streaming_label.setFont(QFont('Arial', 12))
        self.streaming_checkbox = QCheckBox("Enable for Assistant")
        self.streaming_checkbox.setFont(QFont('Arial', 12))
        self.streaming_checkbox.setChecked(self.current_theme.get("streaming_enabled", False))
        self.streaming_checkbox.stateChanged.connect(self.update_streaming_enabled)
        streaming_check_layout.addWidget(self.streaming_label)
        streaming_check_layout.addWidget(self.streaming_checkbox)
        streaming_check_layout.addStretch(1)
        content_layout.addLayout(streaming_check_layout)
        streaming_speed_layout = QHBoxLayout()
        self.streaming_speed_label = QLabel("Delay (ms/char):")
        self.streaming_speed_label.setFont(QFont('Arial', 12))
        self.streaming_speed_slider = QSlider(Qt.Horizontal)
        self.streaming_speed_slider.setRange(10, 800)
        self.streaming_speed_slider.setValue(self.current_theme.get("streaming_speed", 50))
        self.streaming_speed_slider.valueChanged.connect(self.update_streaming_speed)
        self.streaming_speed_value = QLabel(f"{self.current_theme.get('streaming_speed', 50)} ms")
        self.streaming_speed_value.setFont(QFont('Arial', 12))
        self.streaming_speed_value.setAlignment(Qt.AlignCenter)
        self.streaming_speed_value.setFixedWidth(50)
        streaming_speed_layout.addWidget(self.streaming_speed_label)
        streaming_speed_layout.addWidget(self.streaming_speed_slider, 1)
        streaming_speed_layout.addWidget(self.streaming_speed_value)
        content_layout.addLayout(streaming_speed_layout)
        crt_layout = QHBoxLayout()
        self.crt_label = QLabel("CRT Effect:")
        self.crt_label.setFont(QFont('Arial', 12))
        self.crt_checkbox = QCheckBox("Enable Overlay")
        self.crt_checkbox.setFont(QFont('Arial', 12))
        self.crt_checkbox.setChecked(self.current_theme.get("crt_enabled", True))
        self.crt_checkbox.stateChanged.connect(self.update_crt_enabled)
        
        self.crt_speed_label = QLabel("Scanline Speed:")
        self.crt_speed_label.setFont(QFont('Arial', 12))
        self.crt_speed_slider = QSlider(Qt.Horizontal)
        self.crt_speed_slider.setRange(50, 500)
        self.crt_speed_slider.setValue(self.current_theme.get("crt_speed", 160))
        self.crt_speed_slider.valueChanged.connect(self.update_crt_speed)
        self.crt_speed_value = QLabel(f"{self.current_theme.get('crt_speed', 160)} ms")
        self.crt_speed_value.setFont(QFont('Arial', 12))
        self.crt_speed_value.setAlignment(Qt.AlignCenter)
        self.crt_speed_value.setFixedWidth(50)
        crt_layout.addWidget(self.crt_label)
        crt_layout.addWidget(self.crt_checkbox)
        crt_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        crt_layout.addWidget(self.crt_speed_label)
        crt_layout.addWidget(self.crt_speed_slider)
        crt_layout.addWidget(self.crt_speed_value)
        content_layout.addLayout(crt_layout)
        self.crt_speed_label.setEnabled(self.crt_checkbox.isChecked())
        self.crt_speed_slider.setEnabled(self.crt_checkbox.isChecked())
        self.crt_speed_value.setEnabled(self.crt_checkbox.isChecked())
        self.preview_label = QLabel("PREVIEW:")
        self.preview_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFixedHeight(120)
        self.update_preview()
        content_layout.addWidget(self.preview_label)
        content_layout.addWidget(self.preview)
        button_layout = QHBoxLayout()
        self.ok_btn = QPushButton("APPLY THEME")
        self.ok_btn.setFont(QFont('Arial', 14))
        self.cancel_btn = QPushButton("CANCEL")
        self.cancel_btn.setFont(QFont('Arial', 14))
        self.ok_btn.clicked.connect(self._accept_with_sound)
        self.cancel_btn.clicked.connect(self._close_with_sound)
        def ok_mouse_press(event):
            if hasattr(self, 'parent') and self.parent():
                parent = self.parent()
                if hasattr(parent, 'medium_click_sound') and parent.medium_click_sound:
                    try:
                        parent.medium_click_sound.play()
                    except Exception as e:
                        print(f"Error playing medium_click_sound: {e}")
            QPushButton.mousePressEvent(self.ok_btn, event)
        self.ok_btn.mousePressEvent = ok_mouse_press
        def cancel_mouse_press(event):
            if hasattr(self, 'parent') and self.parent():
                parent = self.parent()
                if hasattr(parent, 'medium_click_sound') and parent.medium_click_sound:
                    try:
                        parent.medium_click_sound.play()
                    except Exception as e:
                        print(f"Error playing medium_click_sound: {e}")
            QPushButton.mousePressEvent(self.cancel_btn, event)
        self.cancel_btn.mousePressEvent = cancel_mouse_press
        button_layout.addStretch(1)
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        content_layout.addLayout(button_layout)
        main_layout.addWidget(content_widget)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.pos().y() < 30:
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_position is not None:
            self.move(event.globalPos() - self._drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._drag_position = None
        super().mouseReleaseEvent(event)
    
    def pick_color(self):
        color = QColorDialog.getColor(QColor(self.result_theme["base_color"]), self, "Choose Theme Color")
        if color.isValid():
            self.result_theme["base_color"] = color.name()
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 2px solid {color.name()};")
            self.update_preview()
    
    def update_intensity(self, value):
        intensity = value / 100.0
        self.result_theme["intensity"] = intensity
        self.intensity_value.setText(f"{intensity:.2f}")
        self.update_preview()
    
    def update_contrast(self, value):
        contrast = value / 100.0
        self.result_theme["contrast"] = contrast
        self.contrast_value.setText(f"{contrast:.2f}")
        self.update_preview()

    def update_streaming_enabled(self, state):
        enabled = state == Qt.Checked
        self.result_theme["streaming_enabled"] = enabled
        self.streaming_speed_label.setEnabled(enabled)
        self.streaming_speed_slider.setEnabled(enabled)
        self.streaming_speed_value.setEnabled(enabled)

    def update_streaming_speed(self, value):
        self.result_theme["streaming_speed"] = value
        self.streaming_speed_value.setText(f"{value} ms")

    def update_crt_enabled(self, state):
        enabled = state == Qt.Checked
        self.result_theme["crt_enabled"] = enabled
        self.crt_speed_label.setEnabled(enabled)
        self.crt_speed_slider.setEnabled(enabled)
        self.crt_speed_value.setEnabled(enabled)
        self.update_preview()

    def update_crt_speed(self, value):
        self.result_theme["crt_speed"] = value
        self.crt_speed_value.setText(f"{value} ms")
        self.update_preview()

    def update_preview(self):
        base_color = self.result_theme["base_color"]
        intensity = self.result_theme["intensity"]
        contrast = self.result_theme["contrast"]
        bg_value = int(80 * contrast)
        bg_color = f"#{bg_value:02x}{bg_value:02x}{bg_value:02x}"
        qcolor = QColor(base_color)
        self.preview.setStyleSheet(f"""
            background-color: {bg_color}; 
            color: {base_color}; 
            border: 2px solid {base_color};
            font: 14pt "Arial";
        """)
        text_color = base_color
        if contrast > 0.5:
            text_color = "#333333"
        
        self.preview.setHtml(f"""
            <div style='margin: 10px;'>
            <span style='color: {base_color};'>This is preview text in your chosen color.</span><br>
            <span style='color: rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, 0.7);'>
            Theme with {intensity:.2f} intensity and {contrast:.2f} brightness.
            </span>
            </div>
        """)
    
    def get_theme(self):
        return self.result_theme
    
    def _close_with_sound(self):
        self.reject()
    
    def update_model(self):
        self.result_theme["model"] = self.model_input.toPlainText().strip()

    def update_temperature(self, value):
        self.result_theme["temperature"] = value

    def update_cot_model(self):
        self.result_theme["cot_model"] = self.cot_model_input.toPlainText().strip()

    def update_api_key(self):
        self.result_theme["api_key"] = self.api_key_input.toPlainText().strip()

    def update_service(self):
        service_map = {"OpenRouter": "openrouter", "Google GenAI": "google", "Local API": "local"}
        new_service = service_map.get(self.service_dropdown.currentText(), "openrouter")
        from config import update_config
        update_config("current_service", new_service)
        self.refresh_api_fields()
    
    def refresh_api_fields(self):
        current_service = get_current_service()
        current_api_key = get_api_key_for_service(current_service) or ""
        current_api_url = get_base_url_for_service(current_service) or ""
        
        if current_api_key:
            self.api_key_input.setText("*" * len(current_api_key))
        else:
            self.api_key_input.setText("")
            
        self.api_url_input.setText(current_api_url)
    
    def update_api_url(self):
        self.result_theme["api_url"] = self.api_url_input.toPlainText().strip()

    def _handle_api_key_focus(self):
        current_service = get_current_service()
        current_api_key = get_api_key_for_service(current_service) or ""
        if current_api_key and self.api_key_input.toPlainText().strip() == "*" * len(current_api_key):
            self.api_key_input.setText(current_api_key)
            self.api_key_input.setStyleSheet("QTextEdit { color: #000000; }")
        self.original_api_key = current_api_key

    def _handle_api_key_blur(self):
        api_key = self.api_key_input.toPlainText().strip()
        if api_key and not api_key.startswith("*"):
            if api_key != self.original_api_key:
                self.api_key_modified = True
                self.modified_api_key = api_key
            self.api_key_input.setText("*" * len(api_key))
            self.api_key_input.setStyleSheet("QTextEdit { color: #666666; }")

    def _accept_with_sound(self):
        api_key = self.api_key_input.toPlainText().strip()
        api_url = self.api_url_input.toPlainText().strip()
        current_service = get_current_service()
        
        if api_key or api_url:
            from config import update_config
            if api_url:
                update_config(f"{current_service}_base_url", api_url)
            
            if self.api_key_modified and hasattr(self, 'modified_api_key'):
                update_config(f"{current_service}_api_key", self.modified_api_key)
            elif api_key and not api_key.startswith("*"):
                update_config(f"{current_service}_api_key", api_key)
        
        self.accept()
