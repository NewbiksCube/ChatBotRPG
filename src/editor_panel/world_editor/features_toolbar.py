from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QSlider, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class FeaturesToolbar(QWidget):
    def __init__(self, parent_editor, map_type, theme_colors, button_text="Feature Edit", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_editor = parent_editor
        self.map_type = map_type
        self.theme_colors = theme_colors
        self._feature_paint_mode = False
        self._current_feature_name = None
        self._feature_brush_size = 10
        self._button_text = button_text
        self._init_ui()

    def _init_ui(self):
        base_color = QColor(self.theme_colors.get("base_color", "#CCCCCC"))
        pressed_color = base_color.darker(120)
        if not pressed_color.isValid(): pressed_color = base_color.darker(105)
        pressed_color_str = pressed_color.name()
        highlight_color = base_color.lighter(120)
        highlight_color_str = highlight_color.name()
        button_style = f"""
            QPushButton {{
                padding: 2px 5px;
                border-radius: 0px;
                font-size: 9pt;
            }}
            QPushButton:checked {{
                background-color: {highlight_color_str};
                color: #FFFFFF;
            }}
            QPushButton:pressed {{
                background-color: {pressed_color_str};
                color: #FFFFFF;
            }}
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self.feature_paint_btn = QPushButton(self._button_text)
        self.feature_paint_btn.setCheckable(True)
        self.feature_paint_btn.setToolTip("Paint features onto the map")
        self.feature_paint_btn.setStyleSheet(button_style)
        self.feature_paint_btn.clicked.connect(self._on_feature_paint_toggled)
        
        if hasattr(self.parent_editor, 'play_hover_sound'):
            def play_sound():
                self.parent_editor.play_hover_sound()
            self.feature_paint_btn.clicked.connect(play_sound)
            
        layout.addWidget(self.feature_paint_btn)
        self.feature_selector_label = QLabel("Feature:")
        self.feature_selector_label.setAlignment(Qt.AlignLeft)
        self.feature_selector_label.setVisible(False)
        layout.addWidget(self.feature_selector_label)
        self.feature_selector = QComboBox()
        self.feature_selector.setObjectName(f"{self.map_type.capitalize()}FeatureSelector")
        self.feature_selector.setVisible(False)
        self.feature_selector.addItem("< Select Feature >")
        self.feature_selector.currentIndexChanged.connect(self._on_feature_selected)
        layout.addWidget(self.feature_selector)
        self.brush_size_label = QLabel("Brush Size:")
        self.brush_size_label.setAlignment(Qt.AlignLeft)
        self.brush_size_label.setVisible(False)
        layout.addWidget(self.brush_size_label)
        self.brush_size_slider = QSlider(Qt.Horizontal)
        self.brush_size_slider.setMinimum(1)
        self.brush_size_slider.setMaximum(100)
        self.brush_size_slider.setValue(self._feature_brush_size)
        self.brush_size_slider.setVisible(False)
        self.brush_size_slider.valueChanged.connect(self._on_brush_size_changed)
        layout.addWidget(self.brush_size_slider)
        layout.addStretch(1)

    def _on_feature_paint_toggled(self, checked):
        self._feature_paint_mode = checked
        self.feature_selector_label.setVisible(checked)
        self.feature_selector.setVisible(checked)
        self.brush_size_label.setVisible(checked and self._current_feature_name is not None)
        self.brush_size_slider.setVisible(checked and self._current_feature_name is not None)
        
        if self.feature_paint_btn.isChecked() != checked:
            self.feature_paint_btn.blockSignals(True)
            self.feature_paint_btn.setChecked(checked)
            self.feature_paint_btn.blockSignals(False)
        
        if checked:
            if hasattr(self.parent_editor, 'cancel_draw_mode'):
                self.parent_editor.cancel_draw_mode(self.map_type)
        else:
            if hasattr(self.parent_editor, 'cancel_draw_mode'):
                self.parent_editor.cancel_draw_mode(self.map_type)
        
        if hasattr(self.parent_editor, 'on_feature_paint_mode_changed'):
            self.parent_editor.on_feature_paint_mode_changed(self.map_type, checked)

    def _on_feature_selected(self, index):
        if index == 0:
            self._current_feature_name = None
        else:
            self._current_feature_name = self.feature_selector.itemText(index)
        if hasattr(self.parent_editor, 'on_feature_selected'):
            self.parent_editor.on_feature_selected(self.map_type, self._current_feature_name)

    def _on_brush_size_changed(self, value):
        self._feature_brush_size = value
        if hasattr(self.parent_editor, 'on_feature_brush_size_changed'):
            self.parent_editor.on_feature_brush_size_changed(self.map_type, value)

    def populate_features(self, feature_list):
        current_feature = self.feature_selector.currentText() if self.feature_selector.currentIndex() > 0 else None
        self.feature_selector.blockSignals(True)
        self.feature_selector.clear()
        self.feature_selector.addItem("< Select Feature >")
        for feature in feature_list:
            self.feature_selector.addItem(feature)
        if current_feature and current_feature in feature_list:
            idx = self.feature_selector.findText(current_feature)
            if idx > 0:
                self.feature_selector.setCurrentIndex(idx)
            else:
                self.feature_selector.setCurrentIndex(0)
        else:
            self.feature_selector.setCurrentIndex(0)
        self.feature_selector.blockSignals(False)

    def is_feature_paint_mode(self):
        return self._feature_paint_mode

    def get_current_feature(self):
        return self._current_feature_name

    def get_brush_size(self):
        return self._feature_brush_size

    def set_feature_paint_mode(self, enabled):
        if self._feature_paint_mode != enabled:
            self.feature_paint_btn.setChecked(enabled)
        else:
            self._on_feature_paint_toggled(enabled) 