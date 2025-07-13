from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSlider, QSplitter, QFrame, QSizePolicy, QLineEdit, QTextEdit, QCheckBox
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF, QEvent, QObject, QSize
from PyQt5.QtGui import QColor, QPen
from editor_panel.world_editor.world_editor_paint import paintEvent, mousePressEvent, mouseMoveEvent, mouseReleaseEvent, _find_item_at_pos
from editor_panel.world_editor.world_editor_auto import create_automate_section, connect_automate_checkboxes
from editor_panel.world_editor.features_toolbar import FeaturesToolbar
import math
import time

VIRTUAL_CANVAS_WIDTH = 350
VIRTUAL_CANVAS_HEIGHT = 350

class PlaceholderLineEditHandler(QObject):
    def __init__(self, line_edit, placeholder_text, parent=None):
        super().__init__(parent)
        self._line_edit = line_edit
        self._placeholder_text = placeholder_text
        self._has_placeholder = self._line_edit.text() == self._placeholder_text

    def eventFilter(self, watched, event):
        if watched == self._line_edit:
            if event.type() == QEvent.FocusIn:
                if self._line_edit.text() == self._placeholder_text:
                    self._has_placeholder = True
                    QTimer.singleShot(0, self._line_edit.clear)
                else:
                    self._has_placeholder = False
            elif event.type() == QEvent.FocusOut:
                if self._has_placeholder and not self._line_edit.text():
                    combo_box = self.parent()
                    if isinstance(combo_box, QComboBox):
                        combo_box.setCurrentIndex(0)
                self._has_placeholder = self._line_edit.text() == self._placeholder_text
        return super().eventFilter(watched, event)


class MapAspectRatioContainer(QWidget):
    def __init__(self, crt_label, parent=None):
        super().__init__(parent)
        self.crt_label = crt_label
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.crt_label)
        self._aspect_ratio = 1.0
        self.setMinimumSize(40, 40)

    def set_aspect_ratio(self, aspect):
        self._aspect_ratio = max(0.01, aspect)
        self.update()
        self.updateGeometry()

    def resizeEvent(self, event):
        w, h = self.width(), self.height()
        if self._aspect_ratio > 0:
            if w / h > self._aspect_ratio:
                new_h = h
                new_w = int(h * self._aspect_ratio)
            else:
                new_w = w
                new_h = int(w / self._aspect_ratio)
            x = (w - new_w) // 2
            y = (h - new_h) // 2
            self.crt_label.setGeometry(x, y, new_w, new_h)
        else:
            self.crt_label.setGeometry(0, 0, w, h)
        super().resizeEvent(event)

    def sizeHint(self):
        return QSize(400, 400)
    
def _create_editor_layout(world_editor_ref, parent, toolbar_title, map_space_title, theme_colors, choose_map_callback=None, clear_map_callback=None):
    splitter = QSplitter(Qt.Horizontal, parent)
    splitter.setObjectName(f"{toolbar_title.replace(' ', '')}_Splitter")
    splitter.setHandleWidth(0)
    splitter.setChildrenCollapsible(False)
    base_color = QColor(theme_colors.get("base_color", "#CCCCCC"))
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
    dropdown_style = """
        QComboBox {
            padding: 1px 5px 1px 3px;
            border-radius: 0px;
            font-size: 9pt;
            min-height: 1.5em;
        }
        QComboBox::drop-down {
            border-radius: 0px;
        }
    """
    toolbar = QWidget()
    toolbar.setObjectName(toolbar_title.replace(' ', ''))
    toolbar.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
    toolbar.setMinimumWidth(220)
    toolbar_layout = QVBoxLayout(toolbar)
    toolbar_layout.setObjectName(f"{toolbar_title.replace(' ', '')}_Layout")
    toolbar_layout.setContentsMargins(10, 10, 10, 10)
    toolbar_layout.setAlignment(Qt.AlignTop)
    map_section = QVBoxLayout()
    map_label = QLabel("Map Image:")
    map_label.setObjectName(f"{toolbar_title.replace(' ', '')}_MapLabel")
    map_label.setAlignment(Qt.AlignCenter)
    map_label.setStyleSheet("font-size: 8pt; font-weight: bold;")
    map_section.addWidget(map_label)
    if choose_map_callback:
        choose_map_btn = QPushButton("Choose Map Image")
        choose_map_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_ChooseMapImageButton")
        choose_map_btn.clicked.connect(choose_map_callback)
        map_section.addWidget(choose_map_btn)
        choose_map_btn.setStyleSheet(button_style)
    if clear_map_callback:
        clear_map_btn = QPushButton("Clear Map Image")
        clear_map_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_ClearMapImageButton")
        clear_map_btn.clicked.connect(clear_map_callback)
        map_section.addWidget(clear_map_btn)
        clear_map_btn.setStyleSheet(button_style)
    toolbar_layout.addLayout(map_section)

    scale_section = QVBoxLayout()
    scale_label = QLabel("Map Scale:")
    scale_label.setObjectName(f"{toolbar_title.replace(' ', '')}_ScaleLabel")
    scale_label.setAlignment(Qt.AlignCenter)
    scale_label.setStyleSheet("font-size: 8pt; font-weight: bold;")
    scale_section.addWidget(scale_label)
    
    scale_input_row = QHBoxLayout()
    scale_input_row.setContentsMargins(0, 0, 0, 0)
    scale_input_row.setSpacing(5)
    
    scale_number_input = QLineEdit()
    scale_number_input.setObjectName(f"{toolbar_title.replace(' ', '')}_ScaleNumberInput")
    scale_number_input.setPlaceholderText("1.0")
    scale_number_input.setText("1.0")
    scale_number_input.setToolTip("Distance value for map scale")
    scale_input_row.addWidget(scale_number_input)
    
    scale_unit_label = QLabel("=")
    scale_unit_label.setStyleSheet("font-size: 8pt;")
    scale_input_row.addWidget(scale_unit_label)
    
    scale_time_input = QLineEdit()
    scale_time_input.setObjectName(f"{toolbar_title.replace(' ', '')}_ScaleTimeInput")
    scale_time_input.setPlaceholderText("30")
    scale_time_input.setText("30")
    scale_time_input.setToolTip("Time value for map scale")
    scale_input_row.addWidget(scale_time_input)
    
    scale_unit_dropdown = QComboBox()
    scale_unit_dropdown.setObjectName(f"{toolbar_title.replace(' ', '')}_ScaleUnitDropdown")
    scale_unit_dropdown.addItems(["minutes", "hours", "days"])
    scale_unit_dropdown.setCurrentText("minutes")
    scale_unit_dropdown.setToolTip("Time unit for travel calculation")
    scale_input_row.addWidget(scale_unit_dropdown)
    
    scale_section.addLayout(scale_input_row)
    
    scale_help_label = QLabel("Path length → travel time by walking")
    scale_help_label.setStyleSheet(f"font-size: 7pt; color: {base_color.name()}; font-style: italic;")
    scale_help_label.setAlignment(Qt.AlignCenter)
    scale_section.addWidget(scale_help_label)
    
    toolbar_layout.addLayout(scale_section)
    
    divider1 = QFrame()
    divider1.setFrameShape(QFrame.HLine)
    divider1.setFrameShadow(QFrame.Sunken)
    divider1.setStyleSheet(f"color: {base_color.name()}; background-color: {base_color.name()};")
    toolbar_layout.addWidget(divider1)
    
    path_section = QVBoxLayout()
    draw_label = QLabel("Path:")
    draw_label.setObjectName(f"{toolbar_title.replace(' ', '')}_DrawLabel")
    draw_label.setAlignment(Qt.AlignCenter)
    draw_label.setStyleSheet("font-size: 8pt; font-weight: bold;")
    path_section.addWidget(draw_label)
    path_buttons_info = [
        ("Small", "small", "Activate small path drawing mode"),
        ("Medium", "medium", "Activate medium path drawing mode"),
        ("Big", "big", "Activate big path drawing mode"),
    ]
    for label, type_str, tooltip in path_buttons_info:
        draw_path_btn = QPushButton(f"Draw {label} Path")
        draw_path_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_Draw{label}PathButton")
        draw_path_btn.setCheckable(True)
        draw_path_btn.setToolTip(tooltip)
        path_section.addWidget(draw_path_btn)
        draw_path_btn.setStyleSheet(button_style)
    path_details_btn = QPushButton("Path Details")
    path_details_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_PathDetailsButton")
    path_details_btn.setCheckable(True)
    path_details_btn.setToolTip("Edit details for existing paths/roads")
    path_section.addWidget(path_details_btn)
    path_details_btn.setStyleSheet(button_style)
    path_details_widget = QWidget()
    path_details_widget.setObjectName(f"{toolbar_title.replace(' ', '')}_PathDetailsWidget")
    path_details_layout = QVBoxLayout(path_details_widget)
    path_details_layout.setContentsMargins(0, 0, 0, 0)
    path_details_layout.setSpacing(4)
    path_details_widget.setVisible(False)
    path_details_instruction = QLabel("Click a road/path to edit its details.")
    path_details_instruction.setStyleSheet("font-size: 8pt; color: #888;")
    path_details_layout.addWidget(path_details_instruction)
    name_row = QHBoxLayout()
    path_name_label = QLabel("Name:")
    path_name_label.setStyleSheet("font-size: 8pt;")
    name_row.addWidget(path_name_label)
    path_name_input = QLineEdit()
    path_name_input.setObjectName(f"{toolbar_title.replace(' ', '')}_PathNameInput")
    path_name_input.setProperty("styleClass", "PathDetailsNameInput")
    name_row.addWidget(path_name_input)
    assign_btn = QPushButton()
    assign_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_PathAssignButton")
    assign_btn.setCheckable(True)
    assign_btn.setFixedSize(22, 22)
    assign_btn.setToolTip("Toggle assign mode (click a road to assign name/description)")
    assign_btn.setText("→")
    name_row.addWidget(assign_btn)
    name_row.addStretch(1)
    path_details_layout.addLayout(name_row)
    path_desc_label = QLabel("Description:")
    path_desc_label.setStyleSheet("font-size: 8pt;")
    path_details_layout.addWidget(path_desc_label)
    path_desc_input = QTextEdit()
    path_desc_input.setObjectName(f"{toolbar_title.replace(' ', '')}_PathDescInput")
    path_desc_input.setProperty("styleClass", "PathDetailsDescInput")
    path_desc_input.setMaximumHeight(50)
    path_details_layout.addWidget(path_desc_input)
    instant_row = QHBoxLayout()
    path_instant_label = QLabel("Instant:")
    path_instant_label.setStyleSheet("font-size: 8pt;")
    instant_row.addWidget(path_instant_label)
    path_instant_checkbox = QCheckBox()
    path_instant_checkbox.setObjectName(f"{toolbar_title.replace(' ', '')}_PathInstantCheckbox")
    path_instant_checkbox.setProperty("styleClass", "PathDetailsInstantCheckbox")
    instant_row.addWidget(path_instant_checkbox)
    instant_row.addStretch(1)
    path_details_layout.addLayout(instant_row)
    path_section.addWidget(path_details_widget)

    def toggle_path_details_widget(checked):
        path_details_widget.setVisible(checked)
    path_details_btn.toggled.connect(toggle_path_details_widget)
    path_mode_widget = QWidget()
    path_mode_widget.setObjectName(f"{toolbar_title.replace(' ', '')}_PathModeWidget")
    path_mode_layout = QHBoxLayout(path_mode_widget)
    path_mode_layout.setContentsMargins(0, 0, 0, 0)
    path_mode_layout.setSpacing(2)
    draw_mode_btn = QPushButton("Draw")
    draw_mode_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_DrawModeButton")
    draw_mode_btn.setCheckable(True)
    draw_mode_btn.setChecked(True)
    draw_mode_btn.setToolTip("Freehand drawing mode for paths")
    path_mode_layout.addWidget(draw_mode_btn)
    line_mode_btn = QPushButton("Line")
    line_mode_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_LineModeButton")
    line_mode_btn.setCheckable(True)
    line_mode_btn.setToolTip("Straight line mode for paths")
    path_mode_layout.addWidget(line_mode_btn)
    path_mode_widget.setVisible(False)
    path_section.addWidget(path_mode_widget)
    path_smoothness_label = QLabel("Smoothness:")
    path_smoothness_label.setObjectName(f"{toolbar_title.replace(' ', '')}_PathSmoothnessLabel")
    path_smoothness_label.setAlignment(Qt.AlignLeft)
    path_smoothness_label.setStyleSheet("font-size: 8pt; font-weight: normal;")
    path_smoothness_label.setVisible(False)
    path_section.addWidget(path_smoothness_label)
    path_smoothness_slider = QSlider(Qt.Horizontal)
    path_smoothness_slider.setObjectName(f"{toolbar_title.replace(' ', '')}_PathSmoothnessSlider")
    path_smoothness_slider.setMinimum(0)
    path_smoothness_slider.setMaximum(100)
    path_smoothness_slider.setValue(50)
    path_smoothness_slider.setToolTip("Adjust path smoothness")
    path_smoothness_slider.setVisible(False)
    path_section.addWidget(path_smoothness_slider)
    toolbar_layout.addLayout(path_section)
    divider_path_poi = QFrame()
    divider_path_poi.setFrameShape(QFrame.HLine)
    divider_path_poi.setFrameShadow(QFrame.Sunken)
    divider_path_poi.setStyleSheet(f"color: {base_color.name()}; background-color: {base_color.name()};")
    toolbar_layout.addWidget(divider_path_poi)

    poi_section = QVBoxLayout()
    poi_label = QLabel("Points of Interest:")
    poi_label.setAlignment(Qt.AlignCenter)
    poi_label.setStyleSheet("font-size: 8pt; font-weight: bold;")
    poi_section.addWidget(poi_label)
    map_type = 'world' if "WORLD" in map_space_title.upper() else 'location' if "LOCATION" in map_space_title.upper() else 'unknown'
    if map_type == 'world':
        dot_buttons_info = [
            ("BigLocation", "big", "Activate large location plotting mode", "Add Large Location"),
            ("MediumLocation", "medium", "Activate medium location plotting mode", "Add Medium Location"),
            ("Setting", "small", "Activate setting plotting mode", "Add Setting"),
        ]
    else:
        dot_buttons_info = [
            ("Setting", "small", "Activate setting plotting mode for settings", "Add Setting"),
        ]
    for name_suffix, type_str, tooltip, button_text in dot_buttons_info:
        plot_dot_btn = QPushButton(button_text)
        plot_dot_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_Plot{name_suffix}DotButton")
        plot_dot_btn.setCheckable(True)
        plot_dot_btn.setToolTip(tooltip)
        poi_section.addWidget(plot_dot_btn)
        plot_dot_btn.setStyleSheet(button_style)
    setting_label = QLabel("Linked Settings:")
    setting_label.setObjectName("ToolbarDropdownLabel")
    setting_label.setAlignment(Qt.AlignCenter)
    setting_label.setStyleSheet("font-size: 8pt; font-weight: normal;")
    setting_label.setVisible(False)
    poi_section.addWidget(setting_label)
    setting_dropdown = QComboBox()
    setting_dropdown.setObjectName("WorldSettingDropdown" if map_type == 'world' else "LocationSettingDropdown")
    setting_dropdown.setFocusPolicy(Qt.StrongFocus)
    setting_dropdown.addItem("< Select Setting >")
    setting_dropdown.setVisible(False)
    setting_dropdown.setEditable(True)
    setting_dropdown.setInsertPolicy(QComboBox.NoInsert)
    poi_section.addWidget(setting_dropdown)
    setting_dropdown.setStyleSheet(dropdown_style)
    if setting_dropdown.isEditable():
        line_edit = setting_dropdown.lineEdit()
        if line_edit:
            placeholder_text = setting_dropdown.itemText(0)
            handler = PlaceholderLineEditHandler(line_edit, placeholder_text, setting_dropdown)
            line_edit.installEventFilter(handler)
            setting_dropdown._placeholder_handler = handler
    if map_type == 'world':
        unlink_setting_btn = QPushButton("Unlink Setting")
        unlink_setting_btn.setObjectName("WorldUnlinkSettingButton")
        unlink_setting_btn.setVisible(False)
        unlink_setting_btn.setStyleSheet(button_style)
        poi_section.addWidget(unlink_setting_btn)
        world_unlink_setting_btn = unlink_setting_btn
    elif map_type == 'location':
        unlink_setting_btn = QPushButton("Unlink Setting")
        unlink_setting_btn.setObjectName("LocationUnlinkSettingButton")
        unlink_setting_btn.setVisible(False)
        unlink_setting_btn.setStyleSheet(button_style)
        poi_section.addWidget(unlink_setting_btn)
        location_unlink_setting_btn = unlink_setting_btn

    if map_type == 'world':
        location_label = QLabel("Linked Locations:")
        location_label.setObjectName("ToolbarDropdownLabel")
        location_label.setAlignment(Qt.AlignCenter)
        location_label.setStyleSheet("font-size: 8pt; font-weight: normal;")
        location_label.setVisible(False)
        poi_section.addWidget(location_label)
        location_dropdown = QComboBox()
        location_dropdown.setObjectName("WorldLocationDropdown")
        location_dropdown.setFocusPolicy(Qt.StrongFocus)
        location_dropdown.addItem("< Select Location >")
        location_dropdown.setVisible(False)
        location_dropdown.setEditable(True)
        location_dropdown.setInsertPolicy(QComboBox.NoInsert)
        poi_section.addWidget(location_dropdown)
        location_dropdown.setStyleSheet(dropdown_style)
        if location_dropdown.isEditable():
            line_edit = location_dropdown.lineEdit()
            if line_edit:
                placeholder_text = location_dropdown.itemText(0)
                handler = PlaceholderLineEditHandler(line_edit, placeholder_text, location_dropdown)
                line_edit.installEventFilter(handler)
                location_dropdown._placeholder_handler = handler
        unlink_location_btn = QPushButton("Unlink Location")
        unlink_location_btn.setObjectName("WorldUnlinkLocationButton")
        unlink_location_btn.setVisible(False)
        unlink_location_btn.setStyleSheet(button_style)
        poi_section.addWidget(unlink_location_btn)
        world_unlink_location_btn = unlink_location_btn
    toolbar_layout.addLayout(poi_section)
    divider2 = QFrame()
    divider2.setFrameShape(QFrame.HLine)
    divider2.setFrameShadow(QFrame.Sunken)
    divider2.setStyleSheet(f"color: {base_color.name()}; background-color: {base_color.name()};")
    toolbar_layout.addWidget(divider2)
    if map_type == 'world':
        toolbar_layout.addSpacing(10)
        region_edit_btn = QPushButton("Region Edit")
        region_edit_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_RegionEditButton")
        region_edit_btn.setCheckable(True)
        region_edit_btn.setToolTip("Edit regions on the map (select or paint)")
        toolbar_layout.addWidget(region_edit_btn)
        region_submode_widget = QWidget()
        region_submode_widget.setObjectName(f"{toolbar_title.replace(' ', '')}_RegionSubmodeWidget")
        region_submode_layout = QHBoxLayout(region_submode_widget)
        region_submode_layout.setContentsMargins(0,0,0,0)
        region_submode_layout.setSpacing(2)
        region_select_btn = QPushButton("Select")
        region_select_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_RegionSelectButton")
        region_select_btn.setCheckable(True)
        region_select_btn.setChecked(True)
        region_submode_layout.addWidget(region_select_btn)
        region_paint_btn = QPushButton("Paint")
        region_paint_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_RegionPaintButton")
        region_paint_btn.setCheckable(True)
        region_submode_layout.addWidget(region_paint_btn)
        region_submode_widget.setVisible(False)
        toolbar_layout.addWidget(region_submode_widget)
        region_selector_label = QLabel("Region:")
        region_selector_label.setObjectName(f"{toolbar_title.replace(' ', '')}_RegionSelectorLabel")
        region_selector_label.setAlignment(Qt.AlignLeft)
        region_selector_label.setVisible(False)
        toolbar_layout.addWidget(region_selector_label)
        region_selector = QComboBox()
        region_selector.setObjectName(f"{toolbar_title.replace(' ', '')}_RegionSelector")
        region_selector.setVisible(False)
        region_selector.setStyleSheet(dropdown_style)
        toolbar_layout.addWidget(region_selector)
        brush_size_label = QLabel("Brush Size:")
        brush_size_label.setObjectName(f"{toolbar_title.replace(' ', '')}_BrushSizeLabel")
        brush_size_label.setAlignment(Qt.AlignLeft)
        brush_size_label.setVisible(False)
        toolbar_layout.addWidget(brush_size_label)
        brush_size_slider = QSlider(Qt.Horizontal)
        brush_size_slider.setObjectName(f"{toolbar_title.replace(' ', '')}_BrushSizeSlider")
        brush_size_slider.setMinimum(1)
        brush_size_slider.setMaximum(100)
        brush_size_slider.setValue(5)
        brush_size_slider.setVisible(False)
        toolbar_layout.addWidget(brush_size_slider)
        features_toolbar = FeaturesToolbar(world_editor_ref, 'world', theme_colors, button_text="Feature Edit")
        toolbar_layout.addWidget(features_toolbar)
        world_editor_ref.world_features_toolbar = features_toolbar
        toolbar_layout.addStretch(1)
        automate_label = QLabel("Automate:")
        automate_label.setStyleSheet("font-size: 8pt; font-weight: bold; margin-top: 10px;")
        toolbar_layout.addWidget(automate_label)
        automate_widget, automate_checkboxes_dict = create_automate_section()
        toolbar_layout.addWidget(automate_widget)
        world_editor_ref.automate_checkboxes_dict = automate_checkboxes_dict 
        connect_automate_checkboxes(world_editor_ref, automate_checkboxes_dict)

    elif map_type == 'location':
        features_toolbar = FeaturesToolbar(world_editor_ref, 'location', theme_colors, button_text="Feature Edit")
        toolbar_layout.addWidget(features_toolbar)
        world_editor_ref.location_features_toolbar = features_toolbar
        toolbar_layout.addStretch(1)
        automate_label = QLabel("Automate:")
        automate_label.setStyleSheet("font-size: 8pt; font-weight: bold; margin-top: 10px;")
        toolbar_layout.addWidget(automate_label)
        automate_widget, automate_checkboxes_dict = create_automate_section()
        toolbar_layout.addWidget(automate_widget)
        world_editor_ref.location_automate_checkboxes_dict = automate_checkboxes_dict
        connect_automate_checkboxes(world_editor_ref, automate_checkboxes_dict)
    toolbar_layout.addSpacing(15)
    world_location_dropdown = None
    world_setting_dropdown = None
    location_setting_dropdown = None
    world_location_label = None
    world_unlink_location_btn = None
    world_unlink_setting_btn = None

    if map_type == 'world':
        world_location_dropdown = location_dropdown
        world_location_label = location_label
        world_unlink_location_btn = unlink_location_btn
        world_setting_dropdown = setting_dropdown
        world_unlink_setting_btn = unlink_setting_btn
    elif map_type == 'location':
        location_setting_dropdown = setting_dropdown
        location_unlink_setting_btn = unlink_setting_btn

    toolbar_layout.addStretch(1)
    reset_map_btn = QPushButton("Reset")
    reset_map_btn.setObjectName(f"{toolbar_title.replace(' ', '')}_ResetMapButton")
    reset_map_btn.setToolTip("Reset map image, zoom, pan, and clear all drawings for this map.")
    reset_map_btn.setStyleSheet(button_style)
    toolbar_layout.addWidget(reset_map_btn)
    splitter.addWidget(toolbar)
    map_space = QWidget()
    map_space.setObjectName(f"{map_space_title.replace(' ', '')}")
    map_space.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    map_layout = QVBoxLayout(map_space)
    map_layout.setContentsMargins(0, 0, 0, 0)
    map_layout.setSpacing(0)
    map_space_title_label = QLabel(map_space_title)
    map_space_title_label.setObjectName(f"{map_space_title.replace(' ', '')}_TitleLabel")
    map_space_title_label.setAlignment(Qt.AlignCenter)
    map_layout.addWidget(map_space_title_label, 0)
    map_display = QWidget()
    map_display.setObjectName(f"{map_space_title.replace(' ', '')}_Display")
    map_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    map_display_layout = QVBoxLayout(map_display)
    map_display_layout.setContentsMargins(5, 5, 5, 5)
    map_display_layout.setSpacing(0)
    map_type_id = 'world' if 'WORLD' in map_space_title.upper() else 'location'
    image_label = CRTEffectLabel("No image loaded.", world_editor_ref, map_type_id)
    image_label.setObjectName(f"{map_space_title.replace(' ', '')}_ImageLabel")
    image_label.setAlignment(Qt.AlignCenter)
    aspect_container = MapAspectRatioContainer(image_label)
    aspect_container.setObjectName(f"{map_space_title.replace(' ', '')}_AspectContainer")
    aspect_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    map_display_layout.addWidget(aspect_container, 1)
    map_layout.addWidget(map_display, 1)
    splitter.addWidget(map_space)
    splitter.setSizes([150, 550])
    splitter.setStretchFactor(0, 0)
    splitter.setStretchFactor(1, 1)
    return splitter, image_label, aspect_container, map_space_title_label, reset_map_btn, \
           world_location_label, world_location_dropdown, world_unlink_location_btn, \
           world_setting_dropdown, location_setting_dropdown, world_unlink_setting_btn if map_type == 'world' else location_unlink_setting_btn, \
           scale_number_input, scale_time_input, scale_unit_dropdown

class CRTEffectLabel(QLabel):
    def __init__(self, text, parent_editor, map_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_editor = parent_editor
        self.map_type = map_type
        self._crt_pixmap = None
        self._crt_image = None
        self._border_color = QColor("#CCCCCC")
        self._zoom = 1.0
        self._pan = [0, 0]
        self._dragging = False
        self._last_mouse_pos = None
        self._dragging_selection = False
        self._drag_start_widget_pos = None
        self._selected_item_start_img_pos = None
        self._is_linking_dots = False
        self._link_start_dot_index = -1
        self._link_start_dot_img_pos = None
        self._link_start_dot_widget_pos = None
        self._link_preview_end_widget_pos = None
        self._hovered_dot_index = -1
        self._link_path_widget = []
        self._link_path_image = []
        self._link_visited_dot_indices = []
        self._link_visited_dot_positions = []
        self._world_selected_item_type = None
        self._world_selected_item_index = -1
        self._world_dragging_selection = False
        self._location_selected_item_type = None
        self._location_selected_item_index = -1
        self._location_dragging_selection = False
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._zoom_level = 0
        self._zoom_step_factor = 1.15
        self._max_zoom_level_allowed = 20
        self._pulse_time = 0.0
        self._virtual_width = VIRTUAL_CANVAS_WIDTH
        self._virtual_height = VIRTUAL_CANVAS_HEIGHT
        self.setText(text)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_animate)
        self._pulse_timer.start(50)
        self._region_border_cache = {}
        self._last_visible_rect = None
        self._show_region_fills = True
    paintEvent = paintEvent
    mousePressEvent = mousePressEvent
    mouseMoveEvent = mouseMoveEvent
    mouseReleaseEvent = mouseReleaseEvent
    _find_item_at_pos = _find_item_at_pos

    def _pulse_animate(self):
        self._pulse_time += 0.1
        if self._pulse_time > 2 * math.pi:
            self._pulse_time -= 2 * math.pi
        current_draw_mode = ""
        needs_update = False
        if self.parent_editor and hasattr(self.parent_editor, 'get_draw_mode'):
            current_draw_mode = self.parent_editor.get_draw_mode(self.map_type)
            if current_draw_mode == 'region_edit':
                needs_update = self._dragging or hasattr(self, '_painting_active') and self._painting_active
            elif current_draw_mode == 'feature_paint':
                needs_update = self._dragging
            else:
                needs_update = True
        else:
            needs_update = True
        if needs_update:
            self.update()

    def _min_zoom(self):
        label_w, label_h = self.width(), self.height()
        if label_w <= 0 or label_h <= 0: return 1.0
        if self._crt_image is None:
            img_w, img_h = self._virtual_width, self._virtual_height
        else:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
        if img_w <= 0 or img_h <= 0:
            return 1.0
        scale = min(label_w / img_w, label_h / img_h)
        return max(scale, 0.01)

    def _clamp_pan(self):
        if self._crt_image is not None:
            changed = False
            label_w, label_h = self.width(), self.height()
            if self._crt_image.width() <= 0 or self._crt_image.height() <= 0:
                if abs(self._pan[0]) > 1e-6 or abs(self._pan[1]) > 1e-6:
                    self._pan = [0, 0]
                    return True
                return False
            img_rect_base = self._get_image_rect()
            if img_rect_base.width() <= 0 or img_rect_base.height() <= 0:
                if abs(self._pan[0]) > 1e-6 or abs(self._pan[1]) > 1e-6:
                    self._pan = [0, 0]
                    return True
                return False
            user_zoom_factor = self._zoom_step_factor ** self._zoom_level
            draw_w = img_rect_base.width() * user_zoom_factor
            draw_h = img_rect_base.height() * user_zoom_factor
            max_pan_x = max(0, (draw_w - label_w) / 2.0)
            max_pan_y = max(0, (draw_h - label_h) / 2.0)
            new_pan_x = min(max(self._pan[0], -max_pan_x), max_pan_x)
            new_pan_y = min(max(self._pan[1], -max_pan_y), max_pan_y)
            if self._zoom_level == 0:
                new_pan_x = 0
                new_pan_y = 0
            if abs(new_pan_x - self._pan[0]) > 1e-6 or abs(new_pan_y - self._pan[1]) > 1e-6:
                self._pan[0] = new_pan_x
                self._pan[1] = new_pan_y
                changed = True
            return changed
        else:
            if self._zoom_level == 0:
                if abs(self._pan[0]) > 1e-6 or abs(self._pan[1]) > 1e-6:
                    self._pan = [0, 0]
                    return True
            return False

    def setPixmap(self, pixmap, orig_image=None):
        self._crt_pixmap = pixmap
        if orig_image is not None and not orig_image.isNull():
            self._crt_image = orig_image
            w, h = orig_image.width(), orig_image.height()
            if w > 0 and h > 0:
                aspect = w / h
                min_dim = 80
                self.setMinimumSize(int(min_dim * aspect) if aspect >=1 else min_dim, min_dim if aspect >= 1 else int(min_dim / aspect))
                self.setMaximumSize(16777215, 16777215)
            else:
                self._crt_image = None
                self.setMinimumSize(40, 40)
                self.setMaximumSize(16777215, 16777215)
        else:
            self._crt_image = None
            self._virtual_width = VIRTUAL_CANVAS_WIDTH
            self._virtual_height = VIRTUAL_CANVAS_HEIGHT
            self.setMinimumSize(40, 40)
            self.setMaximumSize(16777215, 16777215)
        self._zoom_level = 0
        self._pan = [0, 0]
        self.updateGeometry()
        self.update()

    def setBorderColor(self, color):
        self._border_color = QColor(color)
        self.update()

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        old_zoom_level = self._zoom_level
        level_changed = False
        pan_needs_reset = False
        new_zoom_level = old_zoom_level
        if angle > 0:
            if self._crt_image is None or old_zoom_level < self._max_zoom_level_allowed:
                new_zoom_level = old_zoom_level + 1
                level_changed = True
        elif angle < 0:
            if self._crt_image is None:
                if old_zoom_level > -50:
                    new_zoom_level = old_zoom_level - 1
                    level_changed = True
            elif old_zoom_level > 0:
                new_zoom_level = old_zoom_level - 1
                level_changed = True
                if new_zoom_level == 0:
                    pan_needs_reset = True
        if not level_changed:
            event.accept()
            return
        if self._crt_image is None:
            virtual_coords_before = self._widget_to_image_coords(event.pos())
            self._zoom_level = new_zoom_level
            if virtual_coords_before:
                new_scale = self._zoom_step_factor ** self._zoom_level
                if abs(new_scale) < 1e-9:
                    self._zoom_level = old_zoom_level
                    print("Zoom limit reached")
                else:
                    self._pan[0] = event.pos().x() - virtual_coords_before[0] * new_scale
                    self._pan[1] = event.pos().y() - virtual_coords_before[1] * new_scale
            else:
                pass
            self.update()
            event.accept()
            return
        else:
            old_pan = list(self._pan)
            base_rect = self._get_image_rect()
            user_zoom_old = self._zoom_step_factor ** old_zoom_level
            user_zoom_new = self._zoom_step_factor ** new_zoom_level
            if base_rect.width() > 0 and base_rect.height() > 0:
                draw_w_old = base_rect.width() * user_zoom_old
                draw_h_old = base_rect.height() * user_zoom_old
                center_x_old = base_rect.x() + base_rect.width() / 2.0 + old_pan[0]
                center_y_old = base_rect.y() + base_rect.height() / 2.0 + old_pan[1]
                x_old = center_x_old - draw_w_old / 2.0
                y_old = center_y_old - draw_h_old / 2.0
                if draw_w_old > 1e-6 and draw_h_old > 1e-6:
                    mouse_norm_x = (event.pos().x() - x_old) / draw_w_old
                    mouse_norm_y = (event.pos().y() - y_old) / draw_h_old
                    draw_w_new = base_rect.width() * user_zoom_new
                    draw_h_new = base_rect.height() * user_zoom_new
                    x_new = event.pos().x() - mouse_norm_x * draw_w_new
                    y_new = event.pos().y() - mouse_norm_y * draw_h_new
                    center_x_new = x_new + draw_w_new / 2.0
                    center_y_new = y_new + draw_h_new / 2.0
                    new_pan_x = center_x_new - (base_rect.x() + base_rect.width() / 2.0)
                    new_pan_y = center_y_new - (base_rect.y() + base_rect.height() / 2.0)
                    self._pan = [new_pan_x, new_pan_y]
                else:
                    pass
            self._zoom_level = new_zoom_level
            if pan_needs_reset:
                self._pan = [0, 0]
            pan_clamped = self._clamp_pan()
            if level_changed or pan_clamped or pan_needs_reset:
                if hasattr(self, '_clear_coord_cache'):
                    self._clear_coord_cache()
                self.update()
        event.accept()

    def keyPressEvent(self, event):
        if self.parent_editor is None:
            super().keyPressEvent(event)
            return
        if event.key() == Qt.Key_Delete:
            selected_type, selected_index = self.parent_editor.get_selected_item(self.map_type)
            if selected_type == 'region' and isinstance(selected_index, str) and selected_index:
                self.parent_editor.delete_selected_item(self.map_type)
                event.accept()
                return
            elif selected_type is not None and isinstance(selected_index, int) and selected_index >= 0:
                self.parent_editor.delete_selected_item(self.map_type)
                event.accept()
                return
            else:
                event.accept()
                return
        super().keyPressEvent(event)

    def _get_image_rect(self):
        label_w, label_h = self.width(), self.height()
        if label_w <= 0 or label_h <= 0:
            return QRectF(0, 0, label_w, label_h)
        if self._crt_image is None:
            img_w, img_h = self._virtual_width, self._virtual_height
        else:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
        if img_w <= 0 or img_h <= 0:
            return QRectF(0, 0, label_w, label_h)
        scale = min(label_w / img_w, label_h / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale
        x = (label_w - draw_w) / 2
        y = (label_h - draw_h) / 2
        return QRectF(x, y, draw_w, draw_h)

    def _animate(self):
        self._pulse_time = time.time()
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._clamp_pan()
        self.update()

    def _widget_to_image_coords(self, widget_pos):
        img_rect_base = self._get_image_rect()
        if img_rect_base.width() <= 0 or img_rect_base.height() <= 0:
            return None
        if self._crt_image is None:
            scale = self._zoom_step_factor ** self._zoom_level
            if abs(scale) < 1e-9: return None
            virtual_x = (widget_pos.x() - self._pan[0]) / scale
            virtual_y = (widget_pos.y() - self._pan[1]) / scale
            return (virtual_x, virtual_y)
        else:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
            if img_w <= 0 or img_h <= 0: return None
            user_zoom_factor = self._zoom_step_factor ** self._zoom_level
            pan_x, pan_y = self._pan[0], self._pan[1]
        draw_w = img_rect_base.width() * user_zoom_factor
        draw_h = img_rect_base.height() * user_zoom_factor
        center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + pan_x
        center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + pan_y
        x_top_left = center_x - draw_w / 2.0
        y_top_left = center_y - draw_h / 2.0
        if draw_w <= 1e-6 or draw_h <= 1e-6:
             return None
        relative_x = (widget_pos.x() - x_top_left) / draw_w
        relative_y = (widget_pos.y() - y_top_left) / draw_h
        image_x = relative_x * img_w
        image_y = relative_y * img_h
        image_x = max(0, min(img_w, image_x))
        image_y = max(0, min(img_h, image_y))
        return (image_x, image_y)

    def _image_to_widget_coords(self, image_pos):
        img_rect_base = self._get_image_rect()
        if img_rect_base.width() <= 0 or img_rect_base.height() <= 0:
            return None

        if self._crt_image is None:
            scale = self._zoom_step_factor ** self._zoom_level
            widget_x = image_pos[0] * scale + self._pan[0]
            widget_y = image_pos[1] * scale + self._pan[1]
            return QPointF(widget_x, widget_y)
        else:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
            if img_w <= 0 or img_h <= 0: return None
            user_zoom_factor = self._zoom_step_factor ** self._zoom_level
            pan_x, pan_y = self._pan[0], self._pan[1]
        draw_w = img_rect_base.width() * user_zoom_factor
        draw_h = img_rect_base.height() * user_zoom_factor
        center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + pan_x
        center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + pan_y
        x_top_left = center_x - draw_w / 2.0
        y_top_left = center_y - draw_h / 2.0
        relative_x = image_pos[0] / img_w if img_w > 0 else 0
        relative_y = image_pos[1] / img_h if img_h > 0 else 0
        widget_x = x_top_left + relative_x * draw_w
        widget_y = y_top_left + relative_y * draw_h
        return QPointF(widget_x, widget_y)

    def _expand_virtual_canvas(self, coord_x, coord_y):
        expanded = False
        new_width = self._virtual_width
        new_height = self._virtual_height
        if coord_x >= self._virtual_width:
            new_width = coord_x + 100
            expanded = True
        if coord_y >= self._virtual_height:
            new_height = coord_y + 100
            expanded = True
        if expanded:
            self._virtual_width = new_width
            self._virtual_height = new_height
            self.update()

    def _draw_virtual_grid(self, painter):
        if self._crt_image is not None:
            return
        grid_color = QColor(60, 60, 60, 150)
        grid_pen = QPen(grid_color, 0.5)
        painter.setPen(grid_pen)
        painter.setBrush(Qt.NoBrush)
        base_grid_spacing = 50.0
        user_zoom_factor = self._zoom_step_factor ** self._zoom_level
        widget_pixels_per_virtual_unit = self._get_image_rect().width() / self._virtual_width * user_zoom_factor if self._virtual_width > 0 else 1.0
        current_grid_spacing = base_grid_spacing
        while current_grid_spacing * widget_pixels_per_virtual_unit < 15:
             current_grid_spacing *= 5
        while current_grid_spacing * widget_pixels_per_virtual_unit > 150:
             current_grid_spacing /= 5
        top_left_widget = QPointF(0, 0)
        bottom_right_widget = QPointF(self.width(), self.height())
        top_left_virtual = self._widget_to_image_coords(top_left_widget)
        bottom_right_virtual = self._widget_to_image_coords(bottom_right_widget)
        if top_left_virtual is None or bottom_right_virtual is None:
             start_x_virtual, start_y_virtual = 0, 0
             end_x_virtual, end_y_virtual = self._virtual_width, self._virtual_height
        else:
            start_x_virtual = max(0, top_left_virtual[0])
            start_y_virtual = max(0, top_left_virtual[1])
            end_x_virtual = bottom_right_virtual[0]
            end_y_virtual = bottom_right_virtual[1]
        first_vx = math.floor(start_x_virtual / current_grid_spacing) * current_grid_spacing
        first_vy = math.floor(start_y_virtual / current_grid_spacing) * current_grid_spacing
        vx = first_vx
        while True:
            p1_virtual = (vx, start_y_virtual - current_grid_spacing)
            p2_virtual = (vx, end_y_virtual + current_grid_spacing)
            p1_widget = self._image_to_widget_coords(p1_virtual)
            p2_widget = self._image_to_widget_coords(p2_virtual)
            if p1_widget and p2_widget:
                 line_rect = QRectF(p1_widget, p2_widget).normalized()
                 if line_rect.intersects(QRectF(self.rect().adjusted(-1,-1,1,1))):
                      painter.drawLine(p1_widget, p2_widget)
            if p1_widget and p1_widget.x() > self.width() + 10: break
            if vx > end_x_virtual + current_grid_spacing: break
            vx += current_grid_spacing
            if vx > self._virtual_width + current_grid_spacing * 2: break
        vy = first_vy
        while True:
            p1_virtual = (start_x_virtual - current_grid_spacing, vy)
            p2_virtual = (end_x_virtual + current_grid_spacing, vy)
            p1_widget = self._image_to_widget_coords(p1_virtual)
            p2_widget = self._image_to_widget_coords(p2_virtual)
            if p1_widget and p2_widget:
                 line_rect = QRectF(p1_widget, p2_widget).normalized()
                 if line_rect.intersects(QRectF(self.rect().adjusted(-1,-1,1,1))):
                      painter.drawLine(p1_widget, p2_widget)
            if p1_widget and p1_widget.y() > self.height() + 10: break
            if vy > end_y_virtual + current_grid_spacing: break
            vy += current_grid_spacing
            if vy > self._virtual_height + current_grid_spacing * 2: break

    def _is_line_visible(self, path_points, visible_rect):
        if not path_points or len(path_points) < 2:
            return False
        for point in path_points:
            widget_point = self._get_cached_widget_coords(point)
            if widget_point and visible_rect.contains(widget_point):
                return True
        
        return False

    def _get_cached_widget_coords(self, image_coords):
        if not hasattr(self, '_coord_cache'):
            self._coord_cache = {}
        
        cache_key = (image_coords[0], image_coords[1], self._zoom_level, self._pan[0], self._pan[1])
        if cache_key in self._coord_cache:
            return self._coord_cache[cache_key]
        
        result = self._image_to_widget_coords(image_coords)
        self._coord_cache[cache_key] = result
        return result

    def _clear_coord_cache(self):
        if hasattr(self, '_coord_cache'):
            self._coord_cache.clear()