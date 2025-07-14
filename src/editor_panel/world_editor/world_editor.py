from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget, QSplitter, QPushButton, QFileDialog, QMessageBox, QComboBox, QSlider, QLineEdit, QTextEdit, QVBoxLayout, QApplication, QCheckBox
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QPointF, QTimer
from PyQt5.QtGui import QImage, QPixmap, QColor, QPen, QBrush, QPainter, QPainterPath
import os
import json
import math
import random
import re
from editor_panel.world_editor.world_editor_canvas import _create_editor_layout
import shutil
from editor_panel.world_editor.world_editor_auto import handle_dot_deletion, set_automate_section_mode, generate_setting_file
from editor_panel.world_editor.region_toolbar import update_region_border_cache, _set_region_edit_mode
from editor_panel.world_editor.world_editor_select import select_item

def sanitize_path_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\\. ]', '', name).strip()
    sanitized = sanitized.replace(' ', '_').lower()
    return sanitized or 'untitled'

def safe_relpath(path, start):
    try:
        return os.path.relpath(path, start)
    except ValueError:
        return os.path.abspath(path)

class WorldEditorWidget(QWidget):
    settingAddedOrRemoved = pyqtSignal()

    def __init__(self, theme_colors, workflow_data_dir=None, parent=None):
        super().__init__(parent)
        self._path_details_widgets = {'world': {}, 'location': {}}
        self._path_details_mode = {'world': False, 'location': False}
        self._selected_path_index = {'world': None, 'location': None}
        self.theme_colors = theme_colors
        self.workflow_data_dir = workflow_data_dir or ""
        self.current_world_name = None
        self.current_location_name = None
        self._world_draw_mode = 'none'
        self._world_path_mode = 'draw'
        self._world_path_smoothness = 50
        self._world_dots = []
        self._world_lines = []
        self._world_regions = {} 
        self._region_masks = {}
        self._current_region_name = None
        self._world_selected_region_name = None
        self._region_brush_size = 5
        self._region_smoothness = 0
        self._world_region_sub_mode = 'select'
        self._previous_ema_point = None
        self._last_painted_position = None
        self._world_dot_type_mode = 'small'
        self._world_line_type_mode = 'small'
        self._location_draw_mode = 'none'
        self._location_path_mode = 'draw'
        self._location_path_smoothness = 50
        self._location_dot_type_mode = 'small'
        self._location_line_type_mode = 'small'
        self._location_lines = []
        self._location_dots = []
        self._world_selected_item_type = None
        self._world_selected_item_index = -1
        self._world_dragging_selection = False
        self._location_selected_item_type = None
        self._location_selected_item_index = -1
        self._location_dragging_selection = False
        self.setObjectName("WorldEditorContainer")
        self._map_cache = {}
        self._last_map_key = None
        self._current_map_relpath = None
        self.current_location_setting_name = None 
        self.current_world_setting_name = None
        self._path_assign_mode = {'world': False, 'location': False}
        self._world_features_data = {}
        self._location_features_data = {}
        self._world_feature_paint = False
        self._location_feature_paint = False
        self._current_world_feature = None
        self._current_location_feature = None
        self._world_feature_brush_size = 10
        self._location_feature_brush_size = 10
        self._world_feature_sub_mode = 'select'
        self._location_feature_sub_mode = 'select'
        self._feature_masks = {
            'world': {},
            'location': {}
        }
        self._feature_border_cache = {
            'world': {},
            'location': {}
        }
        self._feature_mask_scale = 0.25
        self._world_region_name = None
        self._feature_erase_save_timer = None
        self._pending_feature_erase_save_map_type = None
        self.settingAddedOrRemoved.connect(self._handle_setting_added_or_removed)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.nested_tab_widget = QTabWidget()
        self.nested_tab_widget.setObjectName("WorldEditorNestedTabs")
        main_layout.addWidget(self.nested_tab_widget)
        self.world_tab = QWidget()
        world_layout = QVBoxLayout(self.world_tab)
        world_layout.setContentsMargins(0, 0, 0, 0)
        world_layout.setSpacing(0)
        world_editor_splitter, self.world_map_label, self.world_map_aspect_container, \
            self.world_map_title_label, self.world_reset_btn, \
            self.world_location_label, self.world_location_dropdown, self.world_unlink_location_btn, \
            self.world_setting_dropdown, _, self.world_unlink_setting_btn, \
            self.world_scale_number_input, self.world_scale_time_input, self.world_scale_unit_dropdown = _create_editor_layout(
            world_editor_ref=self, parent=self.world_tab, toolbar_title="WORLD Toolbar", map_space_title="WORLD Map Space", theme_colors=self.theme_colors, choose_map_callback=self.choose_world_map_image, clear_map_callback=self.clear_world_map_image)
        world_layout.addWidget(world_editor_splitter)
        self.world_tab.setLayout(world_layout)
        self.nested_tab_widget.addTab(self.world_tab, "WORLD")
        self.location_tab = QWidget()
        location_layout = QVBoxLayout(self.location_tab)
        location_layout.setContentsMargins(0, 0, 0, 0)
        location_layout.setSpacing(0)
        location_editor_splitter, self.location_map_label, self.location_map_aspect_container, \
            self.location_map_title_label, self.location_reset_btn, \
            _, _, _, \
            _, self.location_setting_dropdown, self.location_unlink_setting_btn, \
            self.location_scale_number_input, self.location_scale_time_input, self.location_scale_unit_dropdown = _create_editor_layout(
            world_editor_ref=self, parent=self.location_tab, toolbar_title="LOCATION Toolbar", map_space_title="LOCATION Map Space", theme_colors=self.theme_colors, choose_map_callback=self.choose_location_map_image, clear_map_callback=self.clear_location_map_image)
        location_layout.addWidget(location_editor_splitter)
        self.location_tab.setLayout(location_layout)
        self.nested_tab_widget.addTab(self.location_tab, "LOCATION")
        world_toolbar = world_editor_splitter.widget(0)
        self.world_draw_small_line_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_DrawSmallPathButton")
        self.world_draw_medium_line_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_DrawMediumPathButton")
        self.world_draw_big_line_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_DrawBigPathButton")
        self.world_plot_setting_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_PlotSettingDotButton")
        self.world_plot_medium_location_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_PlotMediumLocationDotButton")
        self.world_plot_large_location_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_PlotBigLocationDotButton")
        self.world_region_painter_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_RegionPainterButton")
        self.world_region_selector = world_toolbar.findChild(QComboBox, "WORLDToolbar_RegionSelector")
        self.world_region_selector_label = world_toolbar.findChild(QLabel, "WORLDToolbar_RegionSelectorLabel")
        self.world_brush_size_slider = world_toolbar.findChild(QSlider, "WORLDToolbar_BrushSizeSlider")
        self.world_brush_size_label = world_toolbar.findChild(QLabel, "WORLDToolbar_BrushSizeLabel")
        self.world_region_edit_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_RegionEditButton")
        self.world_region_submode_widget = world_toolbar.findChild(QWidget, "WORLDToolbar_RegionSubmodeWidget")
        if self.world_region_submode_widget:
            self.world_region_select_submode_btn = self.world_region_submode_widget.findChild(QPushButton, "WORLDToolbar_RegionSelectButton")
            self.world_region_paint_submode_btn = self.world_region_submode_widget.findChild(QPushButton, "WORLDToolbar_RegionPaintButton")
        else:
            self.world_region_select_submode_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_RegionSelectButton")
            self.world_region_paint_submode_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_RegionPaintButton")
        location_toolbar = location_editor_splitter.widget(0)
        self.location_draw_small_line_btn = location_toolbar.findChild(QPushButton, "LOCATIONToolbar_DrawSmallPathButton")
        self.location_draw_medium_line_btn = location_toolbar.findChild(QPushButton, "LOCATIONToolbar_DrawMediumPathButton")
        self.location_draw_big_line_btn = location_toolbar.findChild(QPushButton, "LOCATIONToolbar_DrawBigPathButton")
        self.location_plot_setting_btn = location_toolbar.findChild(QPushButton, "LOCATIONToolbar_PlotSettingDotButton")
        self.location_path_mode_widget = location_toolbar.findChild(QWidget, "LOCATIONToolbar_PathModeWidget")
        self.location_draw_mode_btn = location_toolbar.findChild(QPushButton, "LOCATIONToolbar_DrawModeButton")
        self.location_line_mode_btn = location_toolbar.findChild(QPushButton, "LOCATIONToolbar_LineModeButton")
        self.location_path_smoothness_label = location_toolbar.findChild(QLabel, "LOCATIONToolbar_PathSmoothnessLabel")
        self.location_path_smoothness_slider = location_toolbar.findChild(QSlider, "LOCATIONToolbar_PathSmoothnessSlider")
        if self.world_draw_small_line_btn: self.world_draw_small_line_btn.clicked.connect(lambda checked: self._set_draw_mode('world', 'line', checked, 'small'))
        if self.world_draw_medium_line_btn: self.world_draw_medium_line_btn.clicked.connect(lambda checked: self._set_draw_mode('world', 'line', checked, 'medium'))
        if self.world_draw_big_line_btn: self.world_draw_big_line_btn.clicked.connect(lambda checked: self._set_draw_mode('world', 'line', checked, 'big'))
        if self.world_plot_setting_btn: self.world_plot_setting_btn.clicked.connect(lambda checked: self._set_draw_mode('world', 'dot', checked, 'small'))
        if self.world_plot_medium_location_btn: self.world_plot_medium_location_btn.clicked.connect(lambda checked: self._set_draw_mode('world', 'dot', checked, 'medium'))
        if self.world_plot_large_location_btn: self.world_plot_large_location_btn.clicked.connect(lambda checked: self._set_draw_mode('world', 'dot', checked, 'big'))
        if self.world_reset_btn:
             self.world_reset_btn.clicked.connect(self._reset_world_map)
        if self.location_draw_small_line_btn: self.location_draw_small_line_btn.clicked.connect(lambda checked: self._set_draw_mode('location', 'line', checked, 'small'))
        if self.location_draw_medium_line_btn: self.location_draw_medium_line_btn.clicked.connect(lambda checked: self._set_draw_mode('location', 'line', checked, 'medium'))
        if self.location_draw_big_line_btn: self.location_draw_big_line_btn.clicked.connect(lambda checked: self._set_draw_mode('location', 'line', checked, 'big'))
        if self.location_plot_setting_btn: self.location_plot_setting_btn.clicked.connect(lambda checked: self._set_draw_mode('location', 'dot', checked, 'small'))
        if self.location_reset_btn:
             self.location_reset_btn.clicked.connect(self._reset_location_map)
        if self.world_location_dropdown:
            self.world_location_dropdown.currentIndexChanged.connect(self._on_world_location_selected)
        if self.world_setting_dropdown:
            self.world_setting_dropdown.currentIndexChanged.connect(self._on_world_setting_selected)
        if self.location_setting_dropdown:
            self.location_setting_dropdown.currentIndexChanged.connect(self._on_location_setting_selected)
        if hasattr(self, 'world_unlink_location_btn') and self.world_unlink_location_btn:
            self.world_unlink_location_btn.clicked.connect(self._on_world_unlink_location_clicked)
        if hasattr(self, 'world_unlink_setting_btn') and self.world_unlink_setting_btn:
            self.world_unlink_setting_btn.clicked.connect(self._on_world_unlink_setting_clicked)
        if hasattr(self, 'location_unlink_setting_btn') and self.location_unlink_setting_btn:
            self.location_unlink_setting_btn.clicked.connect(self._on_location_unlink_setting_clicked)

        if hasattr(self, 'world_scale_number_input') and self.world_scale_number_input:
            self.world_scale_number_input.textChanged.connect(self._on_world_scale_changed)
        if hasattr(self, 'world_scale_time_input') and self.world_scale_time_input:
            self.world_scale_time_input.textChanged.connect(self._on_world_scale_changed)
        if hasattr(self, 'world_scale_unit_dropdown') and self.world_scale_unit_dropdown:
            self.world_scale_unit_dropdown.currentTextChanged.connect(self._on_world_scale_changed)
        
        if hasattr(self, 'location_scale_number_input') and self.location_scale_number_input:
            self.location_scale_number_input.textChanged.connect(self._on_location_scale_changed)
        if hasattr(self, 'location_scale_time_input') and self.location_scale_time_input:
            self.location_scale_time_input.textChanged.connect(self._on_location_scale_changed)
        if hasattr(self, 'location_scale_unit_dropdown') and self.location_scale_unit_dropdown:
            self.location_scale_unit_dropdown.currentTextChanged.connect(self._on_location_scale_changed)
        self._apply_tab_styling()
        self.setLayout(main_layout)
        self.force_populate_dropdowns()
        if self.world_region_painter_btn:
            self.world_region_painter_btn.clicked.connect(lambda checked: _set_region_edit_mode(self, 'world', checked))
        if self.world_region_selector:
            self.world_region_selector.currentIndexChanged.connect(self._on_region_selected)
        if self.world_brush_size_slider:
            self.world_brush_size_slider.valueChanged.connect(self._on_brush_size_changed)
        if self.world_region_edit_btn:
            self.world_region_edit_btn.clicked.connect(lambda checked: _set_region_edit_mode(self, 'world', checked)) # Renamed handler
        if self.world_region_select_submode_btn:
            self.world_region_select_submode_btn.clicked.connect(self._on_region_select_submode_clicked)
        if self.world_region_paint_submode_btn:
            self.world_region_paint_submode_btn.clicked.connect(self._on_region_paint_submode_clicked)
        self._region_border_cache = {}
        self.world_path_mode_widget = world_toolbar.findChild(QWidget, "WORLDToolbar_PathModeWidget")
        self.world_draw_mode_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_DrawModeButton")
        self.world_line_mode_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_LineModeButton")
        self.world_path_smoothness_label = world_toolbar.findChild(QLabel, "WORLDToolbar_PathSmoothnessLabel")
        self.world_path_smoothness_slider = world_toolbar.findChild(QSlider, "WORLDToolbar_PathSmoothnessSlider")
        if self.world_draw_mode_btn: self.world_draw_mode_btn.clicked.connect(lambda checked: self._set_path_mode('world', 'draw', checked))
        if self.world_line_mode_btn: self.world_line_mode_btn.clicked.connect(lambda checked: self._set_path_mode('world', 'line', checked))
        if self.world_path_smoothness_slider: self.world_path_smoothness_slider.valueChanged.connect(lambda value: self._set_path_smoothness('world', value))
        if self.location_draw_mode_btn: self.location_draw_mode_btn.clicked.connect(lambda checked: self._set_path_mode('location', 'draw', checked))
        if self.location_line_mode_btn: self.location_line_mode_btn.clicked.connect(lambda checked: self._set_path_mode('location', 'line', checked))
        if self.location_path_smoothness_slider: self.location_path_smoothness_slider.valueChanged.connect(lambda value: self._set_path_smoothness('location', value))
        self.world_path_details_btn = world_toolbar.findChild(QPushButton, "WORLDToolbar_PathDetailsButton")
        self.world_path_details_widget = world_toolbar.findChild(QWidget, "WORLDToolbar_PathDetailsWidget")
        self.world_path_name_input = world_toolbar.findChild(QLineEdit, "WORLDToolbar_PathNameInput")
        self.world_path_desc_input = world_toolbar.findChild(QTextEdit, "WORLDToolbar_PathDescInput")
        self.world_path_instant_checkbox = world_toolbar.findChild(QCheckBox, "WORLDToolbar_PathInstantCheckbox")
        self._path_details_widgets['world'] = {
            'btn': self.world_path_details_btn,
            'widget': self.world_path_details_widget,
            'name_input': self.world_path_name_input,
            'desc_input': self.world_path_desc_input,
            'instant_checkbox': self.world_path_instant_checkbox,
            'assign_btn': world_toolbar.findChild(QPushButton, "WORLDToolbar_PathAssignButton"),
        }
        if self.world_path_details_btn:
            self.world_path_details_btn.toggled.connect(lambda checked: self._set_path_details_mode('world', checked))
        self.location_path_details_btn = location_toolbar.findChild(QPushButton, "LOCATIONToolbar_PathDetailsButton")
        self.location_path_details_widget = location_toolbar.findChild(QWidget, "LOCATIONToolbar_PathDetailsWidget")
        self.location_path_name_input = location_toolbar.findChild(QLineEdit, "LOCATIONToolbar_PathNameInput")
        self.location_path_desc_input = location_toolbar.findChild(QTextEdit, "LOCATIONToolbar_PathDescInput")
        self.location_path_instant_checkbox = location_toolbar.findChild(QCheckBox, "LOCATIONToolbar_PathInstantCheckbox")
        self._path_details_widgets['location'] = {
            'btn': self.location_path_details_btn,
            'widget': self.location_path_details_widget,
            'name_input': self.location_path_name_input,
            'desc_input': self.location_path_desc_input,
            'instant_checkbox': self.location_path_instant_checkbox,
            'assign_btn': location_toolbar.findChild(QPushButton, "LOCATIONToolbar_PathAssignButton"),
        }
        if self.location_path_details_btn:
            self.location_path_details_btn.toggled.connect(lambda checked: self._set_path_details_mode('location', checked))
        if self._path_details_widgets['world'].get('assign_btn'):
            self._path_details_widgets['world']['assign_btn'].toggled.connect(lambda checked: self._set_path_assign_mode('world', checked))
        if self._path_details_widgets['location'].get('assign_btn'):
            self._path_details_widgets['location']['assign_btn'].toggled.connect(lambda checked: self._set_path_assign_mode('location', checked))
        for map_type in self._path_details_widgets:
            widgets = self._path_details_widgets[map_type]
            if widgets.get('name_input'):
                widgets['name_input']._user_edited = False
                widgets['name_input'].textEdited.connect(lambda: setattr(widgets['name_input'], '_user_edited', True))
                widgets['name_input'].editingFinished.connect(lambda: setattr(widgets['name_input'], '_user_edited', False))
            if widgets.get('desc_input'):
                widgets['desc_input']._user_edited = False
                widgets['desc_input'].textChanged.connect(lambda: setattr(widgets['desc_input'], '_user_edited', True))
                orig_focus_out = widgets['desc_input'].focusOutEvent
                def custom_focus_out(event, w=widgets['desc_input'], orig=orig_focus_out):
                    setattr(w, '_user_edited', False)
                    orig(event)
                widgets['desc_input'].focusOutEvent = custom_focus_out
        if hasattr(self, 'world_region_edit_btn') and self.world_region_edit_btn and self.world_region_edit_btn.isChecked():
            if self.world_region_submode_widget: self.world_region_submode_widget.setVisible(True)
            if self.world_region_selector_label: self.world_region_selector_label.setVisible(True)
            if self.world_region_selector: self.world_region_selector.setVisible(True)
        else:
            if self.world_region_submode_widget: self.world_region_submode_widget.setVisible(False)
            if self.world_region_selector_label: self.world_region_selector_label.setVisible(False)
            if self.world_region_selector: self.world_region_selector.setVisible(False)
        try:
            from editor_panel.world_editor import region_toolbar
            self._set_region_edit_mode = region_toolbar._set_region_edit_mode.__get__(self, self.__class__)
            self._init_region_masks = region_toolbar._init_region_masks.__get__(self, self.__class__)
            self._populate_region_selector = region_toolbar._populate_region_selector.__get__(self, self.__class__)
            self._on_region_selected = region_toolbar._on_region_selected.__get__(self, self.__class__)
            self.paint_region_at = region_toolbar.paint_region_at.__get__(self, self.__class__)
            self._region_toolbar_imported = True
        except Exception as e:
            pass
        if hasattr(self, 'world_region_edit_btn') and self.world_region_edit_btn and self.world_region_edit_btn.isChecked():
            if hasattr(self, 'world_region_submode_widget') and self.world_region_submode_widget:
                self.world_region_submode_widget.setVisible(True)
            if hasattr(self, 'world_region_selector_label') and self.world_region_selector_label:
                self.world_region_selector_label.setVisible(True)
            if hasattr(self, 'world_region_selector'):
                self.world_region_selector.setVisible(True)
                self._populate_region_selector()
        if hasattr(self, 'world_features_toolbar'):
            self.world_features_toolbar.feature_paint_btn.toggled.connect(lambda checked: self._on_feature_paint_toggled('world', checked))
        if hasattr(self, 'location_features_toolbar'):
            self.location_features_toolbar.feature_paint_btn.toggled.connect(lambda checked: self._on_feature_paint_toggled('location', checked))

    def _apply_tab_styling(self):
        base_color = self.theme_colors.get("base_color", "#CCCCCC")
        bg_color = self.theme_colors.get("bg_color", "#2C2C2C")
        darker_bg = self.theme_colors.get("darker_bg", "#1E1E1E")
        base_qcolor = QColor(base_color)
        r, g, b = base_qcolor.red(), base_qcolor.green(), base_qcolor.blue()
        hover_bg = f"rgba({r}, {g}, {b}, 0.3)"
        hover_border = f"rgba({min(r+30, 255)}, {min(g+30, 255)}, {min(b+30, 255)}, 0.8)"
        self.compact_region_controls_style = f"""
            QPushButton {{
                padding: 1px 3px;
                font-size: 8pt;
                min-height: 18px;
                max-height: 22px;
            }}
            QLabel {{
                font-size: 8pt;
                min-height: 14px;
                max-height: 16px;
            }}
            QComboBox {{
                font-size: 8pt;
                min-height: 18px;
                max-height: 22px;
                padding: 0px 2px;
            }}
            QSlider {{
                max-height: 16px;
            }}
        """
        if self.world_region_submode_widget:
            self.world_region_submode_widget.setStyleSheet(self.compact_region_controls_style)
        if self.world_region_selector_label:
            self.world_region_selector_label.setStyleSheet(self.compact_region_controls_style)
        if self.world_region_selector:
            self.world_region_selector.setStyleSheet(self.compact_region_controls_style)
        if self.world_brush_size_label:
            self.world_brush_size_label.setStyleSheet(self.compact_region_controls_style)
        if self.world_brush_size_slider:
            self.world_brush_size_slider.setStyleSheet(self.compact_region_controls_style)
        self.nested_tab_widget.setStyleSheet(f"""
            QTabWidget#WorldEditorNestedTabs::pane {{ /* The tab widget frame */
                border-top: 2px solid {base_color};
                margin-top: -1px; /* Adjust overlap */
                background-color: {darker_bg}; /* Set pane background to darker */
            }}
            /* Make TabBar styles specific to this widget's tab bar */
            QTabWidget#WorldEditorNestedTabs > QTabBar::tab {{
                background: {darker_bg};
                border: 1px solid {base_color};
                border-bottom-color: {base_color};
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                min-width: 8ex;
                padding: 6px 15px;
                margin-right: 1px;
                color: {base_color};
                font-weight: bold;
            }}
            QTabWidget#WorldEditorNestedTabs > QTabBar::tab:selected {{
                background: {bg_color};
                border-color: {base_color};
                border-bottom-color: {darker_bg}; /* Match pane background */
                margin-bottom: -1px;
            }}
            QTabWidget#WorldEditorNestedTabs > QTabBar::tab:!selected:hover {{
                background: {hover_bg};
                color: {hover_border};
                border: 1px solid {hover_border};
                border-bottom-color: {hover_border};
            }}
        """)
        self.nested_tab_widget.style().unpolish(self.nested_tab_widget)
        self.nested_tab_widget.style().polish(self.nested_tab_widget)
        self.nested_tab_widget.update()

    def _save_world_map_data(self):
        if not self.current_world_name or not self.workflow_data_dir:
            return
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        if not os.path.isdir(world_dir):
            os.makedirs(world_dir, exist_ok=True)
        dots_data = []
        for dot_tuple in self._world_dots:
            if len(dot_tuple) >= 6:
                x, y, pulse_offset, dot_type, linked_name, region_name = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, linked_name, region_name])
            elif len(dot_tuple) == 5:
                x, y, pulse_offset, dot_type, linked_name = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, linked_name, None])
            elif len(dot_tuple) == 4:
                x, y, pulse_offset, dot_type = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, None, None])
        lines_data = []
        for points, meta in self._world_lines:
            points_list = [list(p) if isinstance(p, tuple) else p for p in points]
            lines_data.append({
                "points": points_list,
                "meta": meta
            })
        regions_data = {}
        region_resources_dir = os.path.join(world_dir, "resources", "regions")
        os.makedirs(region_resources_dir, exist_ok=True)
        for region_name, region_areas in self._world_regions.items():
            regions_data[region_name] = [list(area) for area in region_areas]
        if hasattr(self, '_region_masks'):
            for region_name, mask in self._region_masks.items():
                if not mask.isNull():
                    mask_filename = f"{region_name.replace(' ', '_').lower()}_region_mask.png"
                    mask_path = os.path.join(region_resources_dir, mask_filename)
                    success = mask.save(mask_path, "PNG")
            
        if hasattr(self, '_feature_masks') and 'world' in self._feature_masks:
            feature_masks = self._feature_masks['world']
            feature_resources_dir = os.path.join(world_dir, "resources", "features")
            os.makedirs(feature_resources_dir, exist_ok=True)
            for feature_name, mask in feature_masks.items():
                if not mask.isNull():
                    mask_filename = f"{feature_name.replace(' ', '_').lower()}_feature_mask.png"
                    mask_path = os.path.join(feature_resources_dir, mask_filename)
                    mask.save(mask_path, "PNG")
        scale_data = self._get_world_scale_settings()
        json_data = {
            "dots": dots_data,
            "lines": lines_data,
            "regions": regions_data,
            "features_data": self._world_features_data,
            "scale_settings": scale_data
        }
        map_data_file = os.path.join(world_dir, "world_map_data.json")
        try:
            with open(map_data_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
            saved_mask_count = 0
            if os.path.isdir(region_resources_dir):
                for file in os.listdir(region_resources_dir):
                    if file.endswith('_region_mask.png'):
                        saved_mask_count += 1
        except Exception as e:
            pass

    def _load_world_map_data(self):
        if not self.current_world_name or not self.workflow_data_dir:
            self._world_dots = []
            self._world_lines = []
            self._world_regions = {}
            self._world_features_data = {}
            if hasattr(self, 'world_features_toolbar') and self.world_features_toolbar:
                self.world_features_toolbar.populate_features([])
            default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
            self._load_world_scale_settings(default_scale)
            return
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        map_data_file = os.path.join(world_dir, "world_map_data.json")
        world_json_path = os.path.join(world_dir, f"{self.current_world_name}_world.json")
        features_from_json = []
        if os.path.isfile(world_json_path):
            try:
                with open(world_json_path, 'r', encoding='utf-8') as f:
                    world_json = json.load(f)
                if isinstance(world_json, dict) and isinstance(world_json.get('features'), list):
                    for feature_item in world_json['features']:
                        if isinstance(feature_item, dict) and isinstance(feature_item.get('name'), str):
                            features_from_json.append(feature_item['name'])
            except Exception as e:
                pass
        if not os.path.isfile(map_data_file):
            self._world_dots = []
            self._world_lines = []
            self._world_regions = {}
            self._world_features_data = {}
            if hasattr(self, 'world_features_toolbar') and self.world_features_toolbar:
                self.world_features_toolbar.populate_features(features_from_json)
            default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
            self._load_world_scale_settings(default_scale)
            return
        try:
            with open(map_data_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            self._world_dots = []
            for dot_data in json_data.get('dots', []):
                if len(dot_data) >= 6:
                    self._world_dots.append(tuple(dot_data))
                elif len(dot_data) == 5:
                    x, y, pulse_offset, dot_type, linked_name = dot_data
                    self._world_dots.append((x, y, pulse_offset, dot_type, linked_name, None))
                elif len(dot_data) == 4:
                    x, y, pulse_offset, dot_type = dot_data
                    self._world_dots.append((x, y, pulse_offset, dot_type, None, None))
            self._world_lines = []
            for line_data in json_data.get('lines', []):
                points = line_data.get('points', [])
                meta = line_data.get('meta', {})
                self._world_lines.append((points, meta))
            self._world_regions = {}
            for region_name, region_areas in json_data.get('regions', {}).items():
                self._world_regions[region_name] = []
                for area in region_areas:
                    self._world_regions[region_name].append(tuple(area))
            region_resources_dir = os.path.join(world_dir, "resources", "regions")
            if os.path.isdir(region_resources_dir):
                for region_name in self._world_regions.keys():
                    mask_filename = f"{region_name.replace(' ', '_').lower()}_region_mask.png"
                    mask_path = os.path.join(region_resources_dir, mask_filename)
                    if os.path.isfile(mask_path):
                        try:
                            from PyQt5.QtGui import QImage
                            mask = QImage(mask_path)
                            if not mask.isNull():
                                if not hasattr(self, '_region_masks'):
                                    self._region_masks = {}
                                self._region_masks[region_name] = mask
                        except Exception as e:
                            print(f"[ERROR] Failed to load mask for region '{region_name}': {e}")
            self._world_features_data = json_data.get('features_data', {}) or {}
            for fname in features_from_json:
                if fname and fname not in self._world_features_data:
                    self._world_features_data[fname] = []
            if not hasattr(self, '_feature_masks'):
                self._feature_masks = {'world': {}, 'location': {}}
            elif 'world' not in self._feature_masks:
                self._feature_masks['world'] = {}
            if not hasattr(self, '_feature_border_cache'):
                self._feature_border_cache = {'world': {}, 'location': {}}
            elif 'world' not in self._feature_border_cache:
                self._feature_border_cache['world'] = {}
            self._feature_mask_scale = getattr(self, '_feature_mask_scale', 0.5)
            feature_resources_dir = os.path.join(world_dir, "resources", "features")
            all_feature_names = list(self._world_features_data.keys())
            processed_features_for_init = set()
            for feature_name in all_feature_names:
                if not feature_name: continue
                if feature_name in processed_features_for_init: continue
                mask_loaded_from_file = False
                if os.path.isdir(feature_resources_dir):
                    mask_filename = f"{feature_name.replace(' ', '_').lower()}_feature_mask.png"
                    mask_path = os.path.join(feature_resources_dir, mask_filename)
                    if os.path.isfile(mask_path):
                        try:
                            from PyQt5.QtGui import QImage
                            mask = QImage(mask_path)
                            if not mask.isNull():
                                self._feature_masks['world'][feature_name] = mask
                                mask_loaded_from_file = True
                        except Exception as e:
                            print(f"[ERROR] Failed to load mask image for feature '{feature_name}': {e}")
                if not mask_loaded_from_file:
                    if feature_name in self._world_features_data and self._world_features_data[feature_name]:
                         self._rebuild_feature_mask_from_strokes('world', feature_name)
                    else:
                        if hasattr(self, 'world_map_label'):
                            base_width = self.world_map_label._crt_image.width() if self.world_map_label._crt_image else self.world_map_label._virtual_width
                            base_height = self.world_map_label._crt_image.height() if self.world_map_label._crt_image else self.world_map_label._virtual_height
                            if base_width > 0 and base_height > 0:
                                mask_scale = self._feature_mask_scale
                                mask_width = max(1, int(base_width * mask_scale))
                                mask_height = max(1, int(base_height * mask_scale))
                                from PyQt5.QtGui import QImage, QColor
                                empty_mask = QImage(mask_width, mask_height, QImage.Format_ARGB32)
                                empty_mask.fill(QColor(0,0,0,0))
                                self._feature_masks['world'][feature_name] = empty_mask
                if feature_name in self._feature_masks['world']:
                     self.update_feature_border_cache('world', feature_name)
                processed_features_for_init.add(feature_name)
            if hasattr(self, 'world_features_toolbar') and self.world_features_toolbar:
                self.world_features_toolbar.populate_features(features_from_json)
            scale_data = json_data.get('scale_settings', {})
            if not scale_data:
                scale_data = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
            self._load_world_scale_settings(scale_data)
        except Exception as e:
            print(f"Error loading world map data: {e}")
            self._world_dots = []
            self._world_lines = []
            self._world_regions = {}
            self._world_features_data = {}
            if hasattr(self, 'world_features_toolbar') and self.world_features_toolbar:
                self.world_features_toolbar.populate_features(features_from_json)
            default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
            self._load_world_scale_settings(default_scale)

    def _save_location_map_data(self):
        if not hasattr(self, 'current_world_folder_name') or not self.current_world_folder_name:
            return
        if not hasattr(self, 'workflow_data_dir') or not self.workflow_data_dir:
            return
        if not self.current_location_name:
            return

        world_dir_for_settings = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_folder_name)

        relative_path_to_location_folder = self._find_location_folder_by_display_name(
            None,
            self.current_location_name
        )
        if not relative_path_to_location_folder:
            print(f"[ERROR] _save_location_map_data: Could not find folder for location '{self.current_location_name}' in world '{self.current_world_folder_name}'.")
            return
        location_dir = os.path.join(world_dir_for_settings, relative_path_to_location_folder)
        if not os.path.isdir(location_dir):
             os.makedirs(location_dir, exist_ok=True)
        dots_data = []
        for dot_tuple in self._location_dots:
            if len(dot_tuple) >= 6:
                x, y, pulse_offset, dot_type, linked_name, region_name_val = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, linked_name, region_name_val])
            elif len(dot_tuple) == 5:
                x, y, pulse_offset, dot_type, linked_name = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, linked_name, None])
            elif len(dot_tuple) == 4:
                x, y, pulse_offset, dot_type = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, None, None])
        lines_data = []
        for points, meta in self._location_lines:
            points_list = [list(p) if isinstance(p, tuple) else p for p in points]
            lines_data.append({
                "points": points_list,
                "meta": meta
            })
        if hasattr(self, '_feature_masks') and 'location' in self._feature_masks:
            feature_masks = self._feature_masks['location']
            for feature_name, mask_image in feature_masks.items():
                if mask_image and not mask_image.isNull():
                    feature_resources_dir = os.path.join(location_dir, "resources", "features")
                    os.makedirs(feature_resources_dir, exist_ok=True)
                    mask_filename = f"{feature_name.replace(' ', '_').lower()}_feature_mask.png"
                    mask_path = os.path.join(feature_resources_dir, mask_filename)
        scale_data = self._get_location_scale_settings()
        
        json_data = {
            "dots": dots_data,
            "lines": lines_data,
            "features_data": self._location_features_data if hasattr(self, '_location_features_data') else {},
            "scale_settings": scale_data
        }
        map_data_file = os.path.join(location_dir, "location_map_data.json")
        try:
            with open(map_data_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
            print(f"Saved location map data to {map_data_file}")
        except Exception as e:
            print(f"Error saving location map data: {e}")

    def _detect_region_name(self):
        if not self.workflow_data_dir or not self.current_world_name or not self.current_location_name:
            print("Cannot detect region name: missing workflow_data_dir, world name, or location name")
            return
        search_dirs = [
            os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name),
            os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        ]
        for world_dir in search_dirs:
            if not os.path.isdir(world_dir):
                continue
            direct_location_path = os.path.join(world_dir, self.current_location_name)
            if os.path.isdir(direct_location_path):
                loc_json_filename = f"{sanitize_path_name(self.current_location_name)}_location.json"
                location_json = os.path.join(direct_location_path, loc_json_filename)
                if os.path.isfile(location_json):
                    print(f"Found location '{self.current_location_name}' directly in world '{self.current_world_name}' (not in a region)")
                    self._world_region_name = None
                    return
        for world_dir in search_dirs:
            if not os.path.isdir(world_dir):
                continue
            for region_name in os.listdir(world_dir):
                region_path = os.path.join(world_dir, region_name)
                if not os.path.isdir(region_path):
                    continue
                region_json = os.path.join(region_path, f"{sanitize_path_name(region_name)}_region.json")
                if not os.path.isfile(region_json):
                    continue
                location_path = os.path.join(region_path, self.current_location_name)
                if os.path.isdir(location_path):
                    self._world_region_name = region_name
                    print(f"Found location '{self.current_location_name}' in region '{region_name}'")
                    return

    def _load_location_map_data(self):
        if not self.current_world_name or not self.current_location_name or not self.workflow_data_dir:
            self._location_dots = []
            self._location_lines = []
            self._location_features_data = {}
            if hasattr(self, 'location_features_toolbar') and self.location_features_toolbar:
                self.location_features_toolbar.populate_features([])
            default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
            self._load_location_scale_settings(default_scale)
            return
        base_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        location_dir = None
        try:
            from editor_panel.world_editor.world_editor_auto import find_location_folder_by_display_name, sanitize_path_name
            found_path = None
            if os.path.isdir(base_settings_dir):
                for item_name in os.listdir(base_settings_dir):
                    item_path = os.path.join(base_settings_dir, item_name)
                    if os.path.isdir(item_path):
                        potential_loc_json = os.path.join(item_path, f"{sanitize_path_name(item_name)}_location.json")
                        if os.path.isfile(potential_loc_json):
                             loc_data_check = self._load_json(potential_loc_json)
                             if loc_data_check.get('name', '').lower() == self.current_location_name.lower():
                                 found_path = item_path
                                 self._world_region_name = None
                                 break
                        if not found_path:
                            candidate_path = find_location_folder_by_display_name(item_path, self.current_location_name)
                            if candidate_path:
                                found_path = candidate_path
                                self._world_region_name = item_name
                                break
            if found_path:
                location_dir = found_path
            else:
                 potential_top_level_path = os.path.join(base_settings_dir, sanitize_path_name(self.current_location_name))
                 region_json_in_potential = os.path.join(potential_top_level_path, f"{sanitize_path_name(self.current_location_name)}_region.json")
                 if os.path.isdir(potential_top_level_path) and not os.path.exists(region_json_in_potential):
                     location_dir = potential_top_level_path
                     self._world_region_name = None
                 else:
                     found_in_region_fallback = False
                     if os.path.isdir(base_settings_dir):
                         for item_name in os.listdir(base_settings_dir):
                             item_path = os.path.join(base_settings_dir, item_name)
                             region_json_path_check = os.path.join(item_path, f"{sanitize_path_name(item_name)}_region.json")
                             if os.path.isdir(item_path) and os.path.isfile(region_json_path_check):
                                 potential_loc_folder = os.path.join(item_path, sanitize_path_name(self.current_location_name))
                                 if os.path.isdir(potential_loc_folder):
                                     location_dir = potential_loc_folder
                                     self._world_region_name = item_name
                                     found_in_region_fallback = True
                                     break
                     if not found_in_region_fallback:
                         self._location_dots = []; self._location_lines = []
                         if hasattr(self, 'location_features_toolbar') and self.location_features_toolbar:
                             self.location_features_toolbar.populate_features([])
                         default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
                         self._load_location_scale_settings(default_scale)
                         return
        except Exception as e:
            print(f"[ERROR _load_loc] Exception during location directory search: {e}")
            self._location_dots = []; self._location_lines = []
            if hasattr(self, 'location_features_toolbar') and self.location_features_toolbar:
                self.location_features_toolbar.populate_features([])
            default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
            self._load_location_scale_settings(default_scale)
            return
        if not location_dir or not os.path.isdir(location_dir):
             self._location_dots = []; self._location_lines = []
             if hasattr(self, 'location_features_toolbar') and self.location_features_toolbar:
                 self.location_features_toolbar.populate_features([])
             default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
             self._load_location_scale_settings(default_scale)
             return
        map_data_file = os.path.join(location_dir, "location_map_data.json")
        self._location_dots = []
        self._location_lines = []
        if os.path.isfile(map_data_file):
            try:
                with open(map_data_file, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                if not isinstance(map_data, dict):
                    print(f"ERROR: Invalid map data format - expected dict, got {type(map_data)}")
                else:
                    dots_data = map_data.get("dots", [])
                    if isinstance(dots_data, list):
                        for dot in dots_data:
                            try:
                                if len(dot) < 4: continue
                                x, y, pulse_offset, dot_type = dot[:4]
                                linked_name = dot[4] if len(dot) >= 5 else None
                                self._location_dots.append(tuple([float(x), float(y), float(pulse_offset), str(dot_type), linked_name, None]))
                            except (ValueError, TypeError): continue
                    lines_data = map_data.get("lines", [])
                    if isinstance(lines_data, list):
                        for line in lines_data:
                            try:
                                if not isinstance(line, dict) or "points" not in line or "meta" not in line: continue
                                points = line["points"]
                                meta = line["meta"]
                                valid_points = []
                                for p in points:
                                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                                        valid_points.append(tuple([float(p[0]), float(p[1])]))
                                if valid_points:
                                    self._location_lines.append((tuple(valid_points), meta))
                            except (ValueError, TypeError): continue
            except json.JSONDecodeError as e:
                                    print(f"ERROR: Failed to parse JSON from {map_data_file}: {e}")
            except Exception as e:
                print(f"ERROR loading location map data (drawing elements): {e}")
        if not hasattr(self, '_feature_masks'):
            self._feature_masks = {'world': {}, 'location': {}}
        elif 'location' not in self._feature_masks:
            self._feature_masks['location'] = {}
        if not hasattr(self, '_location_features_data'):
            self._location_features_data = {}
        self._init_feature_masks('location')
        location_features_names = []
        location_json_filename = f"{sanitize_path_name(self.current_location_name)}_location.json"
        location_main_json_path = os.path.join(location_dir, location_json_filename) if location_dir else None
        if location_main_json_path and os.path.isfile(location_main_json_path):
            try:
                location_main_data = self._load_json(location_main_json_path)
                if isinstance(location_main_data, dict) and isinstance(location_main_data.get('features'), list):
                    for feature_item in location_main_data['features']:
                        if isinstance(feature_item, dict) and isinstance(feature_item.get('name'), str):
                            location_features_names.append(feature_item['name'])
            except Exception as e:
                print(f"Error loading features from {location_main_json_path}: {e}")
        self._location_features_data = {}
        if map_data_file and os.path.isfile(map_data_file):
            try:
                with open(map_data_file, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                if not isinstance(map_data, dict):
                    print(f"ERROR: Invalid map data format - expected dict, got {type(map_data)}")
                else:
                    dots_data = map_data.get("dots", [])
                    if isinstance(dots_data, list):
                        for dot in dots_data:
                            try:
                                if len(dot) < 4: continue
                                x, y, pulse_offset, dot_type = dot[:4]
                                linked_name = dot[4] if len(dot) >= 5 else None
                                self._location_dots.append(tuple([float(x), float(y), float(pulse_offset), str(dot_type), linked_name, None]))
                            except (ValueError, TypeError): continue
                    lines_data = map_data.get("lines", [])
                    if isinstance(lines_data, list):
                        for line in lines_data:
                            try:
                                if not isinstance(line, dict) or "points" not in line or "meta" not in line: continue
                                points = line["points"]
                                meta = line["meta"]
                                valid_points = []
                                for p in points:
                                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                                        valid_points.append(tuple([float(p[0]), float(p[1])]))
                                if valid_points:
                                    self._location_lines.append((tuple(valid_points), meta))
                            except (ValueError, TypeError): continue
                    self._location_features_data = map_data.get("features_data", {}) or {}
            except Exception as e:
                print(f"ERROR loading location map data (drawing elements): {e}")
        for fname in location_features_names:
            if fname and fname not in self._location_features_data:
                self._location_features_data[fname] = []
        if not hasattr(self, '_feature_masks'):
            self._feature_masks = {'world': {}, 'location': {}}
        elif 'location' not in self._feature_masks:
            self._feature_masks['location'] = {}
        if not hasattr(self, '_feature_border_cache'):
            self._feature_border_cache = {'world': {}, 'location': {}}
        elif 'location' not in self._feature_border_cache:
            self._feature_border_cache['location'] = {}
        self._feature_mask_scale = getattr(self, '_feature_mask_scale', 0.5)
        feature_resources_dir = os.path.join(location_dir, "resources", "features") if location_dir else None
        all_feature_names = list(self._location_features_data.keys())
        processed_features_for_init = set()
        for feature_name in all_feature_names:
            if not feature_name: continue
            if feature_name in processed_features_for_init: continue
            mask_loaded_from_file = False
            if feature_resources_dir and os.path.isdir(feature_resources_dir):
                mask_filename = f"{feature_name.replace(' ', '_').lower()}_feature_mask.png"
                mask_path = os.path.join(feature_resources_dir, mask_filename)
                if os.path.isfile(mask_path):
                    try:
                        from PyQt5.QtGui import QImage
                        mask = QImage(mask_path)
                        if not mask.isNull():
                            self._feature_masks['location'][feature_name] = mask
                            mask_loaded_from_file = True
                    except Exception as e:
                        print(f"[ERROR] Failed to load mask image for location feature '{feature_name}': {e}")
            if not mask_loaded_from_file:
                if feature_name in self._location_features_data and self._location_features_data[feature_name]:
                    self._rebuild_feature_mask_from_strokes('location', feature_name)
                else:
                    if hasattr(self, 'location_map_label'):
                        base_width = self.location_map_label._crt_image.width() if self.location_map_label._crt_image else self.location_map_label._virtual_width
                        base_height = self.location_map_label._crt_image.height() if self.location_map_label._crt_image else self.location_map_label._virtual_height
                        if base_width > 0 and base_height > 0:
                            mask_scale = self._feature_mask_scale
                            mask_width = max(1, int(base_width * mask_scale))
                            mask_height = max(1, int(base_height * mask_scale))
                            from PyQt5.QtGui import QImage, QColor
                            empty_mask = QImage(mask_width, mask_height, QImage.Format_ARGB32)
                            empty_mask.fill(QColor(0,0,0,0))
                            self._feature_masks['location'][feature_name] = empty_mask
            if feature_name in self._feature_masks['location']:
                self.update_feature_border_cache('location', feature_name)
            processed_features_for_init.add(feature_name)
        if hasattr(self, 'location_features_toolbar') and self.location_features_toolbar:
            self.location_features_toolbar.populate_features(location_features_names)
        if map_data_file and os.path.isfile(map_data_file):
            try:
                with open(map_data_file, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                scale_data = map_data.get('scale_settings', {})
                if not scale_data:
                    scale_data = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
                self._load_location_scale_settings(scale_data)
            except Exception as e:
                default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
                self._load_location_scale_settings(default_scale)
        else:
            default_scale = {'distance': 100.0, 'time': 1.0, 'unit': 'hours'}
            self._load_location_scale_settings(default_scale)

    def set_world(self, world_name, called_from_rename=False):
        if self.current_world_name:
            self._save_world_map_data()
        self.current_world_name = world_name
        self.current_world_folder_name = sanitize_path_name(world_name)
        if hasattr(self, 'world_map_title_label') and self.world_map_title_label:
            display_name = world_name.replace("_", " ") if world_name else "WORLD Map Space"
            self.world_map_title_label.setText(display_name.title())
        self._map_cache.clear()
        self._last_map_key = None
        self._world_dots = []
        self._world_lines = []
        self._world_regions = {}
        self._region_masks = {}
        self._region_border_cache = {}
        self._region_fill_cache = {}
        self._load_world_map_data()
        self._init_region_masks() 
        self._update_dots_region_assignments()
        self.update_world_map()
        self._location_dots = []
        self._location_lines = []
        self.update_location_map()
        self.force_populate_dropdowns()
        self._current_region_name = None
        if not self.current_location_name:
            locations = self._get_location_names_for_world(self.current_world_name)
            if locations:
                default_location = sorted(locations)[0]
                self.set_location(default_location)
        if self.world_region_selector is None and hasattr(self, 'world_tab') and self.world_tab:
            world_toolbar = self.world_tab.findChild(QWidget, "WORLDToolbar")
            if world_toolbar:
                self.world_region_selector = world_toolbar.findChild(QComboBox, "WORLDToolbar_RegionSelector")
                self.world_region_selector_label = world_toolbar.findChild(QLabel, "WORLDToolbar_RegionSelectorLabel")
                self.world_brush_size_slider = world_toolbar.findChild(QSlider, "WORLDToolbar_BrushSizeSlider")
                self.world_brush_size_label = world_toolbar.findChild(QLabel, "WORLDToolbar_BrushSizeLabel")
        
    def choose_world_map_image(self):
        if not self.current_world_name:
            QMessageBox.warning(self, "No World Selected", "Please select a world first.")
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name) # MODIFIED path
        maps_dir = os.path.join(world_settings_dir, "resources", "maps")
        os.makedirs(maps_dir, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Map Image", maps_dir, "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            rel_path = os.path.relpath(file_path, maps_dir)
            world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
            try:
                data = {}
                if os.path.exists(world_json_path):
                    data = self._load_json(world_json_path)
                else:
                    data = {"locations": {}}
                data["map_image"] = rel_path
                if self._save_json(world_json_path, data):
                    self._current_map_relpath = rel_path
                    self._map_cache.clear()
                    self._init_region_masks() 
                    self.update_world_map()
                else:
                     print(f"Error saving world JSON with map image to {world_json_path}")
                     QMessageBox.critical(self, "Save Error", "Failed to save the selected map image reference.")
            except Exception as e:
                print(f"Error processing world map image selection: {e}")
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
        self.update_location_map()
        if hasattr(self, 'location_map_label') and self.location_map_label:
            self.location_map_label.update()
        self._update_location_setting_dropdown()
        self._update_world_setting_dropdown()

    def update_world_map(self, world_name=None):
        if world_name is not None:
            self.current_world_name = world_name
        active_world = self.current_world_name
        if not active_world:
            if self.world_map_label:
                self.world_map_label.clear()
                self.world_map_label.setText("No world selected.")
            return
        if not self.current_world_name:
            self.world_map_label.setPixmap(QPixmap(), orig_image=None)
            self.world_map_label.setBorderColor(self.theme_colors.get("base_color", "#CCCCCC"))
            if hasattr(self, 'world_map_aspect_container'):
                self.world_map_aspect_container.set_aspect_ratio(1.0)
            return
        cache_key = None
        world_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name) # MODIFIED path
        world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
        map_relpath = None
        if os.path.exists(world_json_path):
            try:
                data = self._load_json(world_json_path)
                map_relpath = data.get("map_image")
            except Exception as e:
                print(f"Error reading world JSON for map image ({world_json_path}): {e}")
        self._current_map_relpath = map_relpath
        base_color = self.theme_colors.get("base_color", "#CCCCCC")
        self.world_map_label.setBorderColor(base_color)
        if not map_relpath:
            self.world_map_label.setPixmap(QPixmap(), orig_image=None)
            self.world_map_label.setScaledContents(False)
            if hasattr(self, 'world_map_aspect_container'):
                self.world_map_aspect_container.set_aspect_ratio(1.0)
            return
        maps_dir = os.path.join(world_settings_dir, "resources", "maps")
        image_path = os.path.join(maps_dir, map_relpath)
        cache_key = (image_path, base_color)
        parent = self.world_map_label.parentWidget()
        if parent:
            max_w, max_h = parent.width(), parent.height()
        else:
            max_w, max_h = 800, 600
        if self._last_map_key == cache_key and cache_key in self._map_cache:
            cached_pixmap = self._map_cache[cache_key]
            if cached_pixmap is None:
                self.world_map_label.clear()
                self.world_map_label.setScaledContents(False)
            else:
                self.world_map_label.setPixmap(QPixmap(), orig_image=cached_pixmap)
            self.world_map_label.repaint()
            return
        original_image = QImage(image_path)
        if original_image.isNull():
            print(f"Warning: Could not load image from {image_path}. Creating placeholder.")
            self.world_map_label.setPixmap(QPixmap(), orig_image=None)
            self.world_map_label.setScaledContents(False)
            self._map_cache[cache_key] = None
            self._last_map_key = cache_key
            return
        self.world_map_label.setPixmap(QPixmap(), orig_image=original_image)
        self.world_map_label.setScaledContents(False)
        self.world_map_label.repaint()
        self._map_cache[cache_key] = original_image
        self._last_map_key = cache_key
        if hasattr(self, 'world_map_aspect_container'):
            w, h = original_image.width(), original_image.height()
            if w > 0 and h > 0:
                self.world_map_aspect_container.set_aspect_ratio(w / h)
            else:
                self.world_map_aspect_container.set_aspect_ratio(1.0)
            self.world_map_aspect_container.updateGeometry()
            self.world_map_aspect_container.update()
            self.world_map_aspect_container.resizeEvent(None)
            if self.world_map_aspect_container.parentWidget():
                self.world_map_aspect_container.parentWidget().updateGeometry()
                self.world_map_aspect_container.parentWidget().update()

    def clear_world_map_image(self):
        if not self.current_world_name:
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name) # MODIFIED path
        world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
        try:
            data = {}
            if os.path.exists(world_json_path):
                with open(world_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            if not isinstance(data, dict):
                data = {}
            if "locations" not in data:
                data["locations"] = {}
            if "map_image" in data:
                del data["map_image"]
            with open(world_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._current_map_relpath = None
            self._map_cache.clear()
            self.update_world_map()
        except Exception as e:
            print(f"Error clearing world map image: {e}")

    def clear_location_map_image(self):
        if not self.current_world_name or not self.current_location_name:
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name) # MODIFIED path
        world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
        try:
            data = {}
            if os.path.exists(world_json_path):
                with open(world_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            if "locations" in data and isinstance(data["locations"], dict):
                if self.current_location_name in data["locations"] and isinstance(data["locations"][self.current_location_name], dict):
                    if "map_image" in data["locations"][self.current_location_name]:
                        del data["locations"][self.current_location_name]["map_image"]
                        print(f"Removed map image reference for location '{self.current_location_name}'")
                    else:
                        print(f"No map image reference found for location '{self.current_location_name}' to remove.")
                else:
                    print(f"Location '{self.current_location_name}' not found or not a dictionary in world data.")
            else:
                print("No 'locations' section found in world data.")
            with open(world_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.update_location_map()
        except Exception as e:
            print(f"Error clearing location map image: {e}")

    def choose_location_map_image(self):
        if not self.current_world_name or not self.current_location_name:
            print(f"Warning: Cannot choose location map image - World: {self.current_world_name}, Location: {self.current_location_name}")
            QMessageBox.warning(self, "Selection Needed", "Please select a World and Location first.")
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name) # MODIFIED path
        world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
        maps_dir = os.path.join(world_settings_dir, "resources", "maps")
        os.makedirs(maps_dir, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Select Map Image for {self.current_location_name}", 
            maps_dir, 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            rel_path = os.path.relpath(file_path, maps_dir)
            try:
                data = {}
                if os.path.exists(world_json_path):
                    with open(world_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                else:
                    print(f"Creating new world JSON at {world_json_path}")
                    data = {"locations": {}}
                if "locations" not in data or not isinstance(data["locations"], dict):
                    data["locations"] = {}
                if self.current_location_name not in data["locations"]:
                    data["locations"][self.current_location_name] = {}
                data["locations"][self.current_location_name]["map_image"] = rel_path
                print(f"Saving world JSON with location map path: {rel_path}")
                with open(world_json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("Successfully saved world JSON, updating location map display")
                self.update_location_map()
            except Exception as e:
                print(f"Error updating world JSON with location map image: {e}")
                QMessageBox.critical(self, "Error", f"Failed to update location map image: {str(e)}")
        else:
            print("No file selected for location map image")

    def update_location_map(self):
        if not self.current_world_name or not self.current_location_name:
            self.location_map_label.setPixmap(QPixmap(), orig_image=None)
            self.location_map_label.setBorderColor(self.theme_colors.get("base_color", "#CCCCCC"))
            if hasattr(self, 'location_map_aspect_container'):
                self.location_map_aspect_container.set_aspect_ratio(1.0)
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name) # MODIFIED path
        world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
        try:
            if not os.path.exists(world_json_path):
                print(f"No world JSON found at {world_json_path}")
                self.location_map_label.clear()
                return
            with open(world_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "locations" not in data:
                print(f"Invalid world JSON structure at {world_json_path}")
                self.location_map_label.clear()
                return
            location_data = data["locations"].get(self.current_location_name, {})
            if not isinstance(location_data, dict):
                print(f"Invalid location data for {self.current_location_name}")
                self.location_map_label.setPixmap(QPixmap(), orig_image=None)
                if hasattr(self, 'location_map_aspect_container'): self.location_map_aspect_container.set_aspect_ratio(1.0)
                return
            map_image = location_data.get("map_image")
            if not map_image:
                self.location_map_label.setPixmap(QPixmap(), orig_image=None)
                if hasattr(self, 'location_map_aspect_container'): self.location_map_aspect_container.set_aspect_ratio(1.0)
                return
            maps_dir = os.path.join(world_settings_dir, "resources", "maps")
            image_path = os.path.join(maps_dir, map_image)
            if not os.path.exists(image_path):
                print(f"Map image not found at {image_path}")
                self.location_map_label.setPixmap(QPixmap(), orig_image=None)
                if hasattr(self, 'location_map_aspect_container'): self.location_map_aspect_container.set_aspect_ratio(1.0)
                return
            original_image = QImage(image_path)
            if original_image.isNull():
                print(f"Failed to load map image from {image_path}")
                self.location_map_label.setPixmap(QPixmap(), orig_image=None)
                if hasattr(self, 'location_map_aspect_container'): self.location_map_aspect_container.set_aspect_ratio(1.0)
                return
            base_color = self.theme_colors.get("base_color", "#CCCCCC")
            self.location_map_label.setBorderColor(base_color)
            self.location_map_label.setPixmap(QPixmap(), orig_image=original_image)
            if hasattr(self, 'location_map_aspect_container'):
                w, h = original_image.width(), original_image.height()
                if w > 0 and h > 0:
                    self.location_map_aspect_container.set_aspect_ratio(w / h)
                else:
                    self.location_map_aspect_container.set_aspect_ratio(1.0)
                self.location_map_aspect_container.updateGeometry()
                self.location_map_aspect_container.update()
                if self.location_map_aspect_container.parentWidget():
                    self.location_map_aspect_container.parentWidget().updateGeometry()
                    self.location_map_aspect_container.parentWidget().update()
            self.location_map_label.update()
        
        except Exception as e:
            print(f"Error updating location map: {e}")
            self.location_map_label.clear()
            if hasattr(self, 'location_map_aspect_container'):
                self.location_map_aspect_container.set_aspect_ratio(1.0)

    def set_location(self, location_name):
        if self.current_location_name and self._world_region_name:
            self._save_location_map_data()
        self.current_location_name = location_name
        if self._find_region_for_location(location_name):
            pass
        else:
            self._world_region_name = None
            self._detect_region_name()
        if hasattr(self, 'location_map_title_label') and self.location_map_title_label:
            display_name = location_name.replace("_", " ") if location_name else "LOCATION Map Space"
            self.location_map_title_label.setText(display_name.title())
        self._location_dots = []
        self._location_lines = []
        self._load_location_map_data()
        self.update_location_map()
        if hasattr(self, 'location_map_label') and self.location_map_label:
            print("Forcing repaint of location map label")
            self.location_map_label.update()
        self.current_location_setting_name = None
        self.force_populate_dropdowns()

    def _find_region_for_location(self, location_name):
        if not self.current_world_name or not location_name:
            return False
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name) # MODIFIED path
        if not os.path.isdir(world_dir):
            print(f"World directory not found: {world_dir}")
            return False
        found_region = False
        found_location_path = None
        try:
            for region_folder in os.listdir(world_dir):
                region_path = os.path.join(world_dir, region_folder)
                if os.path.isdir(region_path) and region_folder.lower() != 'resources':
                    for location_folder in os.listdir(region_path):
                        location_path = os.path.join(region_path, location_folder)
                        if os.path.isdir(location_path):
                            if location_folder.lower() == location_name.lower():
                                self._world_region_name = region_folder
                                found_location_path = location_path
                                found_region = True
                                print(f"Found location '{location_name}' by folder name in region '{region_folder}'")
                                break
            if not found_region:
                for region_folder in os.listdir(world_dir):
                    region_path = os.path.join(world_dir, region_folder)
                    if os.path.isdir(region_path) and region_folder.lower() != 'resources':
                        for location_folder in os.listdir(region_path):
                            location_path = os.path.join(region_path, location_folder)
                            if os.path.isdir(location_path):
                                try:
                                    location_json = f"{sanitize_path_name(location_folder)}_location.json"
                                    location_json_path = os.path.join(location_path, location_json)
                                    if os.path.isfile(location_json_path):
                                        location_data = self._load_json(location_json_path)
                                        display_name = location_data.get('name', '')
                                        
                                        if display_name.lower() == location_name.lower():
                                            self._world_region_name = region_folder
                                            found_location_path = location_path
                                            found_region = True
                                            print(f"Found location '{location_name}' by display name in region '{region_folder}'")
                                            break
                                except Exception as e:
                                    print(f"Error checking location JSON for '{location_folder}': {e}")
                    if found_region:
                        break
            if found_region and found_location_path:
                return True
            else:
                return False
        except Exception as e:
            return False

    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        self._apply_tab_styling()
        self.update_world_map()
        self.update_location_map()

    def _set_draw_mode(self, map_type, mode, checked, dot_type=None):
        if checked and mode != 'feature_paint':
            if map_type == 'world' and hasattr(self, 'world_features_toolbar') and self.world_features_toolbar.is_feature_paint_mode():
                if hasattr(self.world_features_toolbar, 'feature_paint_btn'):
                    self.world_features_toolbar.feature_paint_btn.setChecked(False)
                self._on_feature_paint_toggled('world', False)
            elif map_type == 'location' and hasattr(self, 'location_features_toolbar') and self.location_features_toolbar.is_feature_paint_mode():
                if hasattr(self.location_features_toolbar, 'feature_paint_btn'):
                    self.location_features_toolbar.feature_paint_btn.setChecked(False)
                self._on_feature_paint_toggled('location', False)
        self._update_feature_submode_widget_visibility(map_type)
        target_mode_attr = f"_{map_type}_draw_mode"
        target_dot_type_attr = f"_{map_type}_dot_type_mode"
        target_line_type_attr = f"_{map_type}_line_type_mode"
        current_mode = getattr(self, target_mode_attr, 'none')
        small_line_button = getattr(self, f"{map_type}_draw_small_line_btn", None)
        medium_line_button = getattr(self, f"{map_type}_draw_medium_line_btn", None)
        big_line_button = getattr(self, f"{map_type}_draw_big_line_btn", None)
        small_dot_button = getattr(self, f"{map_type}_plot_setting_btn", None)
        medium_dot_button = getattr(self, f"{map_type}_plot_medium_location_btn", None)
        big_dot_button = getattr(self, f"{map_type}_plot_large_location_btn", None)
        line_buttons = [small_line_button, medium_line_button, big_line_button]
        dot_buttons = [small_dot_button, medium_dot_button, big_dot_button]
        all_buttons = [btn for btn in line_buttons + dot_buttons if btn is not None]
        if checked and map_type in self._path_details_mode and self._path_details_mode[map_type]:
            path_details_btn = self._path_details_widgets.get(map_type, {}).get('btn')
            if path_details_btn and path_details_btn.isChecked():
                path_details_btn.setChecked(False)
                self._set_path_details_mode(map_type, False)
        path_mode_widget = getattr(self, f"{map_type}_path_mode_widget", None)
        path_smoothness_label = getattr(self, f"{map_type}_path_smoothness_label", None)
        path_smoothness_slider = getattr(self, f"{map_type}_path_smoothness_slider", None)
        if checked and map_type == 'world' and self._world_draw_mode == 'region_edit':
            if hasattr(self, '_set_region_edit_mode'):
                _set_region_edit_mode(self, 'world', False)
            if hasattr(self, 'world_region_edit_btn') and self.world_region_edit_btn:
                self.world_region_edit_btn.blockSignals(True)
                self.world_region_edit_btn.setChecked(False)
                self.world_region_edit_btn.blockSignals(False)
        source_button = None
        item_type_str = None
        if mode == 'line':
            item_type_str = dot_type
            if item_type_str == 'small': source_button = small_line_button
            elif item_type_str == 'medium': source_button = medium_line_button
            elif item_type_str == 'big': source_button = big_line_button
        elif mode == 'dot':
            item_type_str = dot_type
            if item_type_str == 'small': source_button = small_dot_button
            elif item_type_str == 'medium': source_button = medium_dot_button
            elif item_type_str == 'big': source_button = big_dot_button
        new_mode = current_mode
        if checked:
            setattr(self, target_mode_attr, mode)
            if mode == 'line' and item_type_str:
                setattr(self, target_line_type_attr, item_type_str)
                if path_mode_widget: path_mode_widget.setVisible(True)
                current_path_mode = getattr(self, f"_{map_type}_path_mode", 'draw')
                if current_path_mode == 'draw':
                    if path_smoothness_label: path_smoothness_label.setVisible(True)
                    if path_smoothness_slider: path_smoothness_slider.setVisible(True)
                else:
                    if path_smoothness_label: path_smoothness_label.setVisible(False)
                    if path_smoothness_slider: path_smoothness_slider.setVisible(False)
                draw_mode_btn = getattr(self, f"{map_type}_draw_mode_btn", None)
                line_mode_btn = getattr(self, f"{map_type}_line_mode_btn", None)
                if current_path_mode == 'draw':
                    if draw_mode_btn: draw_mode_btn.setChecked(True)
                    if line_mode_btn: line_mode_btn.setChecked(False)
                else:
                    if draw_mode_btn: draw_mode_btn.setChecked(False)
                    if line_mode_btn: line_mode_btn.setChecked(True)
            elif mode == 'dot' and item_type_str:
                setattr(self, target_dot_type_attr, item_type_str)
                if path_mode_widget: path_mode_widget.setVisible(False)
                if path_smoothness_label: path_smoothness_label.setVisible(False)
                if path_smoothness_slider: path_smoothness_slider.setVisible(False)
            else:
                print(f"Warning: Setting {map_type} draw mode to '{mode}' without valid type.")
                setattr(self, target_mode_attr, 'none')
                mode = 'none'
                if path_mode_widget: path_mode_widget.setVisible(False)
                if path_smoothness_label: path_smoothness_label.setVisible(False)
                if path_smoothness_slider: path_smoothness_slider.setVisible(False)
            for btn in all_buttons:
                if btn and btn != source_button and btn.isChecked():
                    btn.setChecked(False)
            new_mode = mode
        else:
            active_type = None
            if current_mode == 'line':
                active_type = getattr(self, target_line_type_attr, 'medium')
            elif current_mode == 'dot':
                active_type = getattr(self, target_dot_type_attr, 'small')
            if current_mode == mode and item_type_str == active_type:
                new_mode = 'none'
                if path_mode_widget: path_mode_widget.setVisible(False)
                if path_smoothness_label: path_smoothness_label.setVisible(False)
                if path_smoothness_slider: path_smoothness_slider.setVisible(False)
            else:
                if source_button and not source_button.isChecked():
                    pass
                return
        if new_mode == 'none':
            setattr(self, target_mode_attr, 'none')
            if path_mode_widget: path_mode_widget.setVisible(False)
            if path_smoothness_label: path_smoothness_label.setVisible(False)
            if path_smoothness_slider: path_smoothness_slider.setVisible(False)
        map_label = getattr(self, f"{map_type}_map_label", None)
        if map_label:
            if new_mode == 'line' or new_mode == 'dot':
                map_label.setCursor(Qt.CrossCursor)
            elif new_mode == 'none':
                if map_label._zoom_level > 0:
                    map_label.setCursor(Qt.OpenHandCursor)
                else:
                    map_label.setCursor(Qt.ArrowCursor)
            else:
                map_label.setCursor(Qt.ArrowCursor)
        if hasattr(self, 'automate_checkboxes_dict') and map_type == 'world':
            if mode == 'dot' and checked and dot_type == 'small':
                set_automate_section_mode(self.automate_checkboxes_dict, 'add_setting_mode')
            else:
                set_automate_section_mode(self.automate_checkboxes_dict, 'none_mode' if new_mode == 'none' else 'hidden_mode')
        if hasattr(self, 'location_automate_checkboxes_dict') and map_type == 'location':
            if mode == 'dot' and checked and dot_type == 'small':
                set_automate_section_mode(self.location_automate_checkboxes_dict, 'add_setting_mode')
            else:
                set_automate_section_mode(self.location_automate_checkboxes_dict, 'none_mode' if new_mode == 'none' else 'hidden_mode')

    def get_draw_mode(self, map_type):
        return getattr(self, f"_{map_type}_draw_mode", 'none')

    def _segments_intersect(self, p1, p2, p3, p4):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-9:
            return None
        t_num = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
        u_num = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3))
        if den > 0:
            if not (0 < t_num < den and 0 < u_num < den):
                return None
        else:
            if not (den < t_num < 0 and den < u_num < 0):
                return None
        t = t_num / den
        intersect_x = x1 + t * (x2 - x1)
        intersect_y = y1 + t * (y2 - y1)
        return (intersect_x, intersect_y)

    def _find_dot_index_by_pos(self, dot_list, pos, tol=1e-3):
        for idx, (x, y, *_rest) in enumerate(dot_list):
            if (x - pos[0]) ** 2 + (y - pos[1]) ** 2 < tol ** 2:
                return idx
        return None

    def _add_or_update_line(self, map_type, start_dot_index, end_dot_index, image_path):
        if map_type == 'world':
            line_list = self._world_lines
            dot_list = self._world_dots
            line_type_mode = self._world_line_type_mode
            dot_type_mode_attr = '_world_dot_type_mode'
            dot_adder_func = self.add_world_dot
            map_label = self.world_map_label
            path_mode = self._world_path_mode
            path_smoothness = self._world_path_smoothness
        elif map_type == 'location':
            line_list = self._location_lines
            dot_list = self._location_dots
            line_type_mode = self._location_line_type_mode
            dot_type_mode_attr = '_location_dot_type_mode'
            dot_adder_func = self.add_location_dot
            map_label = self.location_map_label
            path_mode = self._location_path_mode
            path_smoothness = self._location_path_smoothness
        else:
            return
        if path_mode == 'line' and len(image_path) >= 2:
            start_point = image_path[0]
            end_point = image_path[-1]
            image_path = [start_point, end_point]
        elif path_mode == 'draw' and path_smoothness > 0 and len(image_path) > 2:
            if path_smoothness > 0:
                import numpy as np
                from scipy.interpolate import splprep, splev
                try:
                    points = np.array(image_path)
                    x = points[:, 0]
                    y = points[:, 1]
                    num_points = len(image_path) * 2
                    smooth_factor = path_smoothness / 50.0
                    tck, u = splprep([x, y], s=smooth_factor, per=False)
                    u_new = np.linspace(0, 1, num_points)
                    x_new, y_new = splev(u_new, tck)
                    smooth_path = [(float(x_new[i]), float(y_new[i])) for i in range(len(x_new))]
                    smooth_path[0] = image_path[0]
                    smooth_path[-1] = image_path[-1]
                    image_path = smooth_path
                except (ImportError, ValueError, np.linalg.LinAlgError):
                    pass
                except Exception as e:
                    print(f"Error smoothing path: {e}")
        if len(image_path) < 2:
            return
            
        line_type = line_type_mode
        meta = {'start': start_dot_index, 'end': end_dot_index, 'type': line_type}
        new_path = list(image_path)
        existing_index = -1
        existing_type = None
        for idx, (path, meta_info) in enumerate(line_list):
            s, e, t = None, None, None
            if isinstance(meta_info, dict):
                 s, e, t = meta_info.get('start'), meta_info.get('end'), meta_info.get('type')
            if s == start_dot_index and e == end_dot_index:
                existing_index = idx
                existing_type = t
                break
        action = 'add'
        if existing_index != -1:
            action = 'replace'
        intersections_found = []
        unique_intersection_points = set()
        min_dist_sq_to_dot = 0.5**2
        min_dist_sq_to_intersection = 0.1**2
        indices_to_check = range(len(line_list))
        if action == 'replace':
             indices_to_check = [idx for idx in indices_to_check if idx != existing_index]
        for existing_line_idx in indices_to_check:
            existing_path, existing_meta = line_list[existing_line_idx]
            for j in range(len(existing_path) - 1):
                p3 = existing_path[j]
                p4 = existing_path[j+1]
                current_new_path_len = len(new_path)
                for i in range(current_new_path_len - 1):
                    if i >= len(new_path) - 1: break
                    p1 = new_path[i]
                    p2 = new_path[i+1]
                    intersection_point = self._segments_intersect(p1, p2, p3, p4)
                    if intersection_point:
                        is_near_dot = any(
                            (intersection_point[0] - dx)**2 + (intersection_point[1] - dy)**2 < min_dist_sq_to_dot
                            for dx, dy, *_rest in dot_list
                        )
                        if is_near_dot: continue
                        is_near_intersection = any(
                            (intersection_point[0] - ix)**2 + (intersection_point[1] - iy)**2 < min_dist_sq_to_intersection
                            for ix, iy in unique_intersection_points
                        )
                        if is_near_intersection: continue
                        intersections_found.append((intersection_point, i, existing_line_idx, j))
                        unique_intersection_points.add(intersection_point)
        intersection_dot_indices = {}
        if intersections_found:
            original_dot_mode = getattr(self, dot_type_mode_attr, 'small')
            setattr(self, dot_type_mode_attr, 'small')
            for point, _, _, _ in intersections_found:
                dot_adder_func(point)
            setattr(self, dot_type_mode_attr, original_dot_mode)
            for point, _, _, _ in intersections_found:
                idx = self._find_dot_index_by_pos(dot_list, point)
                if idx is not None:
                    intersection_dot_indices[point] = idx
            mods_for_new_path = []
            mods_for_existing_paths = {}
            for point, i, existing_idx, j in intersections_found:
                mods_for_new_path.append((i, point))
                if existing_idx not in mods_for_existing_paths:
                    mods_for_existing_paths[existing_idx] = []
                mods_for_existing_paths[existing_idx].append((j, point))
            mods_for_new_path.sort(key=lambda x: x[0], reverse=True)
            for i, point in mods_for_new_path:
                if i < len(new_path) - 1:
                    new_path.insert(i + 1, point)
            split_indices = [0]
            for i, point in sorted(mods_for_new_path, key=lambda x: x[0]):
                split_indices.append(i + 1)
            split_indices.append(len(new_path))
            split_segments = [new_path[split_indices[k]:split_indices[k+1]+1] for k in range(len(split_indices)-1) if split_indices[k+1] > split_indices[k]]
            if action == 'replace':
                line_list[existing_index] = None
            for seg in split_segments:
                if len(seg) < 2:
                    continue
                start_idx = self._find_dot_index_by_pos(dot_list, seg[0])
                end_idx = self._find_dot_index_by_pos(dot_list, seg[-1])
                meta = {'start': start_idx, 'end': end_idx, 'type': line_type}
                line_list.append((tuple(seg), meta))
            for existing_idx, mods in mods_for_existing_paths.items():
                mods.sort(key=lambda x: x[0], reverse=True)
                current_path_tuple = line_list[existing_idx]
                temp_path_list = list(current_path_tuple[0])
                for j, point in mods:
                    if j < len(temp_path_list) - 1:
                        temp_path_list.insert(j + 1, point)
                split_indices = [0]
                for j, point in sorted(mods, key=lambda x: x[0]):
                    split_indices.append(j + 1)
                split_indices.append(len(temp_path_list))
                split_segments = [temp_path_list[split_indices[k]:split_indices[k+1]+1] for k in range(len(split_indices)-1) if split_indices[k+1] > split_indices[k]]
                line_list[existing_idx] = None
                for seg in split_segments:
                    if len(seg) < 2:
                        continue
                    start_idx = self._find_dot_index_by_pos(dot_list, seg[0])
                    end_idx = self._find_dot_index_by_pos(dot_list, seg[-1])
                    meta = {'start': start_idx, 'end': end_idx, 'type': current_path_tuple[1]['type'] if isinstance(current_path_tuple[1], dict) else current_path_tuple[1]}
                    line_list.append((tuple(seg), meta))
            line_list[:] = [l for l in line_list if l is not None]
            if map_label:
                map_label.update()
            return
        final_line_data = (tuple(new_path), meta)
        if action == 'replace':
            line_list[existing_index] = final_line_data
        elif action == 'add':
            line_list.append(final_line_data)
        if map_label:
            map_label.update()
        if map_type == 'world':
            self._save_world_map_data()
        elif map_type == 'location':
            self._save_location_map_data()

    def add_world_line(self, start_dot_index, end_dot_index, image_path):
        self._add_or_update_line('world', start_dot_index, end_dot_index, image_path)

    def add_world_dot(self, p_img):
        dot_type = self._world_dot_type_mode
        pulse_offset = random.uniform(0, 2 * math.pi)
        region_name = self._get_region_at_point(p_img[0], p_img[1])
        linked_name = None
        if dot_type == 'small' and hasattr(self, 'automate_checkboxes_dict'):
            add_setting_cbs = self.automate_checkboxes_dict.get('add_setting_mode', [])
            for text, cb in add_setting_cbs:
                if text == 'Generate Setting' and cb.isChecked():
                    linked_name = generate_setting_file(self, p_img[0], p_img[1], 'world')
                    if linked_name:
                        self.settingAddedOrRemoved.emit()
                    break
        dot_data = (p_img[0], p_img[1], pulse_offset, dot_type, linked_name, region_name)
        self._world_dots.append(dot_data)
        self._save_world_map_data()

    def add_location_line(self, start_dot_index, end_dot_index, image_path):
        self._add_or_update_line('location', start_dot_index, end_dot_index, image_path)

    def add_location_dot(self, p_img):
        dot_type = self._location_dot_type_mode
        pulse_offset = random.uniform(0, 2 * math.pi)
        linked_name = None
        if dot_type == 'small' and hasattr(self, 'location_automate_checkboxes_dict'):
            add_setting_cbs = self.location_automate_checkboxes_dict.get('add_setting_mode', [])
            for text, cb in add_setting_cbs:
                if text == 'Generate Setting' and cb.isChecked():
                    linked_name = generate_setting_file(self, p_img[0], p_img[1], 'location')
                    if linked_name:
                        self.settingAddedOrRemoved.emit()
                    break
        dot_data = (p_img[0], p_img[1], pulse_offset, dot_type, linked_name, None)
        self._location_dots.append(dot_data)
        self._save_location_map_data()

    def get_world_draw_data(self):
        return self._world_lines, self._world_dots

    def get_location_draw_data(self):
        return self._location_lines, self._location_dots

    def clear_selection(self, map_type=None, trigger_update=True):
        cleared = False
        update_label = None
        if map_type == 'world' or map_type is None:
            if self._world_selected_item_type is not None or self._world_selected_region_name is not None:
                self._world_selected_item_type = None
                self._world_selected_item_index = -1
                self._world_selected_region_name = None
                cleared = True
                if hasattr(self, 'world_location_label') and self.world_location_label:
                    self.world_location_label.setVisible(False)
                if hasattr(self, 'world_location_dropdown') and self.world_location_dropdown:
                    self.world_location_dropdown.setVisible(False)
                if hasattr(self, 'world_unlink_location_btn') and self.world_unlink_location_btn:
                    self.world_unlink_location_btn.setVisible(False)
                world_set_label = None
                for label_widget in self.world_tab.findChildren(QLabel):
                    if label_widget.text() == "Linked Settings:":
                        world_set_label = label_widget
                        break
                if world_set_label:
                    world_set_label.setVisible(False)
                if hasattr(self, 'world_setting_dropdown') and self.world_setting_dropdown:
                    self.world_setting_dropdown.setVisible(False)
                if hasattr(self, 'world_unlink_setting_btn') and self.world_unlink_setting_btn:
                    self.world_unlink_setting_btn.setVisible(False)
            if hasattr(self, 'world_map_label') and self.world_map_label:
                label_selection_cleared = False
                if getattr(self.world_map_label, '_world_selected_item_type', None) is not None:
                    self.world_map_label._world_selected_item_type = None
                    label_selection_cleared = True
                index_val = getattr(self.world_map_label, '_world_selected_item_index', -1)
                try:
                    index_val_int = int(index_val)
                except (ValueError, TypeError):
                    index_val_int = -1
                if index_val_int >= 0:
                    self.world_map_label._world_selected_item_index = -1
                    label_selection_cleared = True
                if getattr(self.world_map_label, '_world_selected_region_name', None) is not None:
                    self.world_map_label._world_selected_region_name = None
                    label_selection_cleared = True
                if label_selection_cleared:
                    update_label = self.world_map_label
                    self.world_map_label.setFocus()
                    if getattr(self.world_map_label, '_zoom_level', 0) > 0:
                        self.world_map_label.setCursor(Qt.OpenHandCursor)
                    else:
                        self.world_map_label.setCursor(Qt.ArrowCursor)
        if map_type == 'location' or map_type is None:
            if self._location_selected_item_type is not None or self._location_selected_item_index >= 0:
                self._location_selected_item_type = None
                self._location_selected_item_index = -1
                cleared = True
                setting_label = None
                for label in self.location_tab.findChildren(QLabel):
                    if label.text() == "Settings:":
                        setting_label = label
                        break
                if setting_label:
                    setting_label.setVisible(False)
                if hasattr(self, 'location_setting_dropdown') and self.location_setting_dropdown:
                    self.location_setting_dropdown.setVisible(False)
            if hasattr(self, 'location_map_label') and self.location_map_label:
                label_selection_cleared = False
                if getattr(self.location_map_label, '_location_selected_item_type', None) is not None:
                    self.location_map_label._location_selected_item_type = None
                    label_selection_cleared = True
                loc_index_val = getattr(self.location_map_label, '_location_selected_item_index', -1)
                try:
                    loc_index_val_int = int(loc_index_val)
                except (ValueError, TypeError):
                    loc_index_val_int = -1
                if loc_index_val_int >= 0:
                    self.location_map_label._location_selected_item_index = -1
                    label_selection_cleared = True
                if label_selection_cleared:
                    update_label = self.location_map_label
                    self.location_map_label.setFocus()
                    if getattr(self.location_map_label, '_zoom_level', 0) > 0:
                        self.location_map_label.setCursor(Qt.OpenHandCursor)
                    else:
                        self.location_map_label.setCursor(Qt.ArrowCursor)
        if cleared and trigger_update:
            if update_label: 
                update_label.update()
            elif map_type is None:
                if hasattr(self, 'world_map_label') and self.world_map_label:
                    self.world_map_label.update()
                if hasattr(self, 'location_map_label') and self.location_map_label:
                    self.location_map_label.update()
        return cleared

    def get_selected_item(self, map_type):
        item_type = getattr(self, f"_{map_type}_selected_item_type", None)
        if map_type == 'world' and item_type == 'region':
            item_index_or_name = getattr(self, f"_{map_type}_selected_region_name", None)
        else:
            item_index_or_name = getattr(self, f"_{map_type}_selected_item_index", -1)
        if item_type is None or (isinstance(item_index_or_name, int) and item_index_or_name < 0) or \
           (isinstance(item_index_or_name, str) and not item_index_or_name):
            map_label = getattr(self, f"{map_type}_map_label", None)
            if map_label:
                label_type = getattr(map_label, f"_{map_type}_selected_item_type", None)
                if label_type is not None:
                    if map_type == 'world' and label_type == 'region':
                        label_index_or_name = getattr(map_label, f"_{map_type}_selected_region_name", None)
                    else:
                        label_index_or_name = getattr(map_label, f"_{map_type}_selected_item_index", -1)
                    if label_type is not None and (isinstance(label_index_or_name, int) and label_index_or_name >= 0) or \
                       (isinstance(label_index_or_name, str) and label_index_or_name):
                        item_type = label_type
                        item_index_or_name = label_index_or_name
        return item_type, item_index_or_name

    def update_world_dot_position(self, index, new_pos_img):
        if 0 <= index < len(self._world_dots):
            to_delete = [line for line in self._world_lines if isinstance(line[1], dict) and (line[1]['start'] == index or line[1]['end'] == index)]
            if to_delete:
                reply = QMessageBox.question(
                    None,
                    "Delete Connected Paths?",
                    f"Moving this dot will delete {len(to_delete)} connected path(s). Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    print("Move cancelled by user.")
                    return False
            current_dot_data = list(self._world_dots[index])
            current_region = None
            if len(current_dot_data) >= 6:
                current_region = current_dot_data[5]
            new_region = self._get_region_at_point(new_pos_img[0], new_pos_img[1])
            if current_region != new_region:
                region_change_text = ""
                if new_region is None:
                    region_change_text = "outside all regions"
                else:
                    region_change_text = f"into {self._format_region_name_for_display(new_region)}"
                if current_region is None:
                    print(f"Dot moved from outside any region {region_change_text}")
                else:
                    print(f"Dot moved from {self._format_region_name_for_display(current_region)} {region_change_text}")
            linked_name = None
            dot_type = None
            if len(current_dot_data) >= 6:
                linked_name = current_dot_data[4]
                dot_type = current_dot_data[3]
                self._world_dots[index] = (new_pos_img[0], new_pos_img[1], current_dot_data[2], 
                                           current_dot_data[3], current_dot_data[4], new_region)
            elif len(current_dot_data) == 5:
                linked_name = current_dot_data[4]
                dot_type = current_dot_data[3]
                self._world_dots[index] = (new_pos_img[0], new_pos_img[1], current_dot_data[2], 
                                           current_dot_data[3], current_dot_data[4], new_region)
            else:
                if len(current_dot_data) >= 4:
                    dot_type = current_dot_data[3]
                    self._world_dots[index] = (new_pos_img[0], new_pos_img[1], current_dot_data[2], 
                                              current_dot_data[3], None, new_region)
                else:
                    print(f"Warning: Dot data at index {index} has unexpected format with only {len(current_dot_data)} elements")
                    return False
            if current_region != new_region and linked_name and dot_type in ('big', 'medium'):
                print(f"Dot moved to different region with linked location - updating location '{linked_name}' to region '{new_region}'")
                self._update_location_region(linked_name, new_region)
            elif current_region != new_region and linked_name and dot_type == 'small':
                print(f"Dot moved to different region with linked setting - updating setting '{linked_name}' to region '{new_region}'")
                self._update_setting_region(linked_name, new_region, linked_name)
            self._world_lines = [line for line in self._world_lines if not (isinstance(line[1], dict) and (line[1]['start'] == index or line[1]['end'] == index))]
            self._save_world_map_data()
            select_item(self, 'world', 'dot', index)
            if hasattr(self, 'world_map_label') and self.world_map_label:
                self.world_map_label.update()
            return True
        return False

    def update_world_line_position(self, index, new_path):
        if 0 <= index < len(self._world_lines):
            if isinstance(new_path, list) and len(new_path) >= 2:
                line_data = self._world_lines[index]
                if isinstance(line_data, tuple) and len(line_data) == 2:
                    _, existing_meta = line_data
                else:
                    print(f"Warning: Updating world line {index} with default meta.")
                    existing_meta = {'type': 'medium'}
                self._world_lines[index] = (tuple(new_path), existing_meta)
                return True
            else:
                print(f"Error updating world path {index}: new_path is not a valid list of points.")
        return False

    def update_location_dot_position(self, index, new_pos_img):
        if 0 <= index < len(self._location_dots):
            to_delete = [line for line in self._location_lines if isinstance(line[1], dict) and (line[1]['start'] == index or line[1]['end'] == index)]
            if to_delete:
                reply = QMessageBox.question(
                    None,
                    "Delete Connected Paths?",
                    f"Moving this dot will delete {len(to_delete)} connected path(s). Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    print("Move cancelled by user.")
                    return False
            _x, _y, existing_offset, existing_type, existing_linked_name, _none_region = self._location_dots[index]
            self._location_dots[index] = (new_pos_img[0], new_pos_img[1], existing_offset, existing_type, existing_linked_name, None)
            before = len(self._location_lines)
            self._location_lines = [line for line in self._location_lines if not (isinstance(line[1], dict) and (line[1]['start'] == index or line[1]['end'] == index))]
            after = len(self._location_lines)
            if before != after:
                print(f"Deleted {before - after} location lines connected to dot {index}")
            self.location_map_label.update()
            self._save_location_map_data()
            return True
        return False

    def update_location_line_position(self, index, new_path):
        if 0 <= index < len(self._location_lines):
            if isinstance(new_path, list) and len(new_path) >= 2:
                line_data = self._location_lines[index]
                if isinstance(line_data, tuple) and len(line_data) == 2:
                    _, existing_meta = line_data
                else:
                    print(f"Warning: Updating location line {index} with default meta.")
                    existing_meta = {'type': 'medium'}
                self._location_lines[index] = (tuple(new_path), existing_meta)
                return True
            else:
                print(f"Error updating location path {index}: new_path is not a valid list of points.")
        return False

    def delete_selected_item(self, map_type):
        selected_item_type = getattr(self, f"_{map_type}_selected_item_type", None)
        selected_item_index = getattr(self, f"_{map_type}_selected_item_index", -1)
        selected_region_name = getattr(self, f"_{map_type}_selected_region_name", None) if map_type == 'world' else None
        if selected_item_type is None:
            map_label = getattr(self, f"{map_type}_map_label", None)
            if map_label:
                label_selected_type = getattr(map_label, f"_{map_type}_selected_item_type", None)
                label_selected_index = getattr(map_label, f"_{map_type}_selected_item_index", -1)
                if label_selected_type is not None:
                    selected_item_type = label_selected_type
                    selected_item_index = label_selected_index
                    if map_type == 'world' and selected_item_type == 'region':
                        selected_region_name = getattr(map_label, "_world_selected_region_name", None)
                    elif map_type == 'world' and selected_item_type != 'region':
                        selected_region_name = None
        if selected_item_type == 'region' and map_type == 'world' and not selected_region_name:
            map_label = getattr(self, f"{map_type}_map_label", None)
            if map_label and getattr(map_label, "_world_selected_item_type", None) == 'region':
                selected_region_name = getattr(map_label, "_world_selected_region_name", None)
        if selected_item_type is None or (selected_item_index < 0 and not selected_region_name) :
            return False
            
        deleted = False
        if map_type == 'world':
            dots_list = self._world_dots
            lines_list = self._world_lines
            dots_attr = '_world_dots'
            lines_attr = '_world_lines'
        elif map_type == 'location':
            dots_list = self._location_dots
            lines_list = self._location_lines
            dots_attr = '_location_dots'
            lines_attr = '_location_lines'
        else:
            return False
        try:
            if selected_item_type == 'dot':
                if 0 <= selected_item_index < len(dots_list):
                    if map_type == 'world':
                        dot_to_delete = dots_list[selected_item_index]
                    elif map_type == 'location':
                        dot_to_delete = dots_list[selected_item_index]
                    new_dots = [dot for i, dot in enumerate(dots_list) if i != selected_item_index]
                    setattr(self, dots_attr, new_dots)
                    line_indices_to_delete = []
                    for i, line_data in enumerate(lines_list):
                        if isinstance(line_data, tuple) and len(line_data) == 2 and isinstance(line_data[1], dict):
                            meta = line_data[1]
                            if meta.get('start') == selected_item_index or meta.get('end') == selected_item_index:
                                line_indices_to_delete.append(i)
                    for i in sorted(line_indices_to_delete, reverse=True):
                        if 0 <= i < len(lines_list):
                            new_lines = [line for j, line in enumerate(lines_list) if j != i]
                            setattr(self, lines_attr, new_lines)
                            lines_list = getattr(self, lines_attr)
                    if map_type == 'world':
                        try:
                            handle_dot_deletion(self, dot_to_delete, map_type)
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                    elif map_type == 'location':
                        try:
                            handle_dot_deletion(self, dot_to_delete, map_type)
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                    deleted = True
            
            elif selected_item_type == 'line':
                if 0 <= selected_item_index < len(lines_list):
                    line_data = lines_list[selected_item_index]
                    source_setting = None
                    target_setting = None
                    try:
                        if isinstance(line_data, tuple) and len(line_data) == 2 and isinstance(line_data[1], dict):
                            meta = line_data[1]
                            associated_setting = meta.get('associated_setting')
                            if associated_setting and map_type == 'location':
                                start_idx = meta.get('start')
                                end_idx = meta.get('end')
                                if start_idx is not None and end_idx is not None:
                                    if 0 <= start_idx < len(dots_list) and 0 <= end_idx < len(dots_list):
                                        start_dot = dots_list[start_idx]
                                        end_dot = dots_list[end_idx]
                                        if len(start_dot) >= 5 and start_dot[3] == 'small' and start_dot[4]:
                                            source_setting = str(start_dot[4]).strip()
                                        if len(end_dot) >= 5 and end_dot[3] == 'small' and end_dot[4]:
                                            target_setting = str(end_dot[4]).strip()
                    except Exception as e:
                        pass
                    new_lines = [line for i, line in enumerate(lines_list) if i != selected_item_index]
                    setattr(self, lines_attr, new_lines)
                    deleted = True
                    if source_setting and target_setting and hasattr(self, 'parent') and self.parent():
                        try:
                            setting_manager = None
                            if hasattr(self.parent(), 'setting_manager_tab'):
                                setting_manager = self.parent().setting_manager_tab
                            elif hasattr(self.parent(), 'parent') and self.parent().parent() and hasattr(self.parent().parent(), 'setting_manager_tab'):
                                setting_manager = self.parent().parent().setting_manager_tab
                            if setting_manager and hasattr(setting_manager, '_remove_setting_connection'):
                                location_name = self.current_location_name if map_type == 'location' else None
                                setting_manager._remove_setting_connection(source_setting, target_setting, location_name)
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
            elif selected_item_type == 'region' and map_type == 'world' and selected_region_name:
                if selected_region_name in self._world_regions:
                    del self._world_regions[selected_region_name]
                    if hasattr(self, '_region_masks') and selected_region_name in self._region_masks:
                        del self._region_masks[selected_region_name]
                    if hasattr(self, '_region_border_cache') and selected_region_name in self._region_border_cache:
                        del self._region_border_cache[selected_region_name]
                    if hasattr(self, '_region_fill_cache') and selected_region_name in self._region_fill_cache:
                        del self._region_fill_cache[selected_region_name]
                    deleted = True
        except Exception as e:
            print(f"[DEBUG DELETE] Error while deleting {map_type} {selected_item_type} at index {selected_item_index}: {e}")
        if deleted:
            self.clear_selection(map_type)
            if map_type == 'world':
                self._save_world_map_data()
                if hasattr(self, 'world_map_label'):
                    self.world_map_label.update()
            elif map_type == 'location':
                self._save_location_map_data()
                if hasattr(self, 'location_map_label'):
                    self.location_map_label.update()
            return True
        return False

    def _reset_world_map(self):
        import os
        import shutil
        if not self.current_world_name:
            QMessageBox.warning(self, "No World Selected", "Please select a world first.")
            return
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            f"Are you sure you want to reset the map image and ALL drawings for the world '{self.current_world_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.clear_world_map_image()
            world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
            map_data_file = os.path.join(world_dir, "world_map_data.json")
            if os.path.isfile(map_data_file):
                os.remove(map_data_file)
                print(f"Deleted {map_data_file}")
            backup_file = map_data_file + ".backup"
            if os.path.isfile(backup_file):
                os.remove(backup_file)
                print(f"Deleted {backup_file}")
            regions_dir = os.path.join(world_dir, "resources", "regions")
            if os.path.isdir(regions_dir):
                shutil.rmtree(regions_dir)
                print(f"Deleted region masks directory: {regions_dir}")
            self._world_dots = []
            self._world_lines = []
            self._world_regions = {}
            self._region_masks = {}
            self._region_border_cache = {}
            self._region_fill_cache = {}
            self._current_region_name = None
            self._world_dot_type_mode = 'small'
            self._world_line_type_mode = 'small'
            self.clear_selection('world', trigger_update=False)
            self._load_world_map_data()
            if self.world_map_label:
                self.world_map_label.update()
            print("World map reset complete.")
        else:
            print("World map reset cancelled.")

    def _reset_location_map(self):
        if not self.current_location_name:
            QMessageBox.warning(self, "No Location Selected", "Please select a location first.")
            return
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            f"Are you sure you want to reset the map image and ALL drawings for the location '{self.current_location_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            print(f"Resetting location map for: {self.current_location_name}")
            self.clear_location_map_image()
            self._location_dots = []
            self._location_lines = []
            self.clear_selection('location', trigger_update=False)
            self._save_location_map_data()
            if self.location_map_label:
                self.location_map_label.update()

    def cancel_draw_mode(self, map_type):
        if map_type == 'world':
            if self._world_draw_mode != 'region_edit':
                self._world_draw_mode = 'none'
            drawing_buttons = [
                self.world_draw_small_line_btn,
                self.world_draw_medium_line_btn, 
                self.world_draw_big_line_btn,
                self.world_plot_setting_btn,
                self.world_plot_medium_location_btn,
                self.world_plot_large_location_btn
            ]
            for btn in drawing_buttons:
                if btn and btn.isChecked():
                    btn.blockSignals(True)
                    btn.setChecked(False)
                    btn.blockSignals(False)
            if hasattr(self, 'world_path_mode_widget') and self.world_path_mode_widget:
                self.world_path_mode_widget.setVisible(False)
            if hasattr(self, 'world_path_smoothness_slider') and self.world_path_smoothness_slider:
                self.world_path_smoothness_slider.setVisible(False)
            if hasattr(self, 'world_path_smoothness_label') and self.world_path_smoothness_label:
                self.world_path_smoothness_label.setVisible(False)
            if self.world_region_edit_btn and self.world_region_edit_btn.isChecked():
                pass
            if hasattr(self, 'automate_checkboxes_dict'):
                set_automate_section_mode(self.automate_checkboxes_dict, 'none_mode')
        elif map_type == 'location':
            self._location_draw_mode = 'none'
            drawing_buttons = [
                self.location_draw_small_line_btn,
                self.location_draw_medium_line_btn,
                self.location_draw_big_line_btn,
                self.location_plot_setting_btn
            ]
            for btn in drawing_buttons:
                if btn and btn.isChecked():
                    btn.blockSignals(True)
                    btn.setChecked(False)
                    btn.blockSignals(False)
            if hasattr(self, 'location_path_mode_widget') and self.location_path_mode_widget:
                self.location_path_mode_widget.setVisible(False)
            if hasattr(self, 'location_path_smoothness_slider') and self.location_path_smoothness_slider:
                self.location_path_smoothness_slider.setVisible(False)
            if hasattr(self, 'location_path_smoothness_label') and self.location_path_smoothness_label:
                self.location_path_smoothness_label.setVisible(False)
            if hasattr(self, 'location_automate_checkboxes_dict'):
                set_automate_section_mode(self.location_automate_checkboxes_dict, 'none_mode')
        map_label = getattr(self, f"{map_type}_map_label", None)
        if map_label:
            if map_type == 'world' and self.world_region_edit_btn and self.world_region_edit_btn.isChecked():
                pass
            else:
                cursor = Qt.ArrowCursor if map_label._zoom_level == 0 else Qt.OpenHandCursor
                map_label.setCursor(cursor)
        features_toolbar = getattr(self, f"{map_type}_features_toolbar", None)
        if features_toolbar and features_toolbar.is_feature_paint_mode():
            features_toolbar.feature_paint_btn.blockSignals(True)
            features_toolbar.feature_paint_btn.setChecked(False)
            features_toolbar.feature_paint_btn.blockSignals(False)

    def _load_json(self, file_path):
        if not file_path or not os.path.isfile(file_path):
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"WorldEditorWidget: Error reading JSON from {file_path}: {e}")
            return {}
        except Exception as e:
            print(f"WorldEditorWidget: Unexpected error reading JSON from {file_path}: {e}")
            return {}
        
    def _update_world_location_dropdown(self):
        if not self.world_location_dropdown or not self.current_world_name:
            return
        self.world_location_dropdown.blockSignals(True)
        self.world_location_dropdown.clear()
        currently_linked_locations = set()
        selected_dot_linked_location = None
        if self._world_selected_item_type == 'dot' and 0 <= self._world_selected_item_index < len(self._world_dots):
            selected_dot_data = self._world_dots[self._world_selected_item_index]
            if len(selected_dot_data) == 5:
                selected_dot_linked_location = selected_dot_data[4]
            for i, dot_data in enumerate(self._world_dots):
                if i != self._world_selected_item_index and len(dot_data) == 5 and dot_data[3] in ['big', 'medium']:
                    if dot_data[4]:
                        currently_linked_locations.add(dot_data[4])
        else:
             for dot_data in self._world_dots:
                if len(dot_data) == 5 and dot_data[3] in ['big', 'medium'] and dot_data[4]:
                     currently_linked_locations.add(dot_data[4])
        locations = self._get_location_names_for_world(self.current_world_name)
        self.world_location_dropdown.addItem("< Select Location >") # Placeholder text, no data
        added_count = 0
        for display_name in locations:
            if display_name not in currently_linked_locations or display_name == selected_dot_linked_location:
                self.world_location_dropdown.addItem(display_name)
                added_count += 1
        index_to_select = 0
        if selected_dot_linked_location:
            idx = self.world_location_dropdown.findText(selected_dot_linked_location)
            if idx != -1:
                index_to_select = idx
        self.world_location_dropdown.setCurrentIndex(index_to_select)
        self.world_location_dropdown.blockSignals(False)
        self.world_location_dropdown.update()

    def _get_unlinked_settings_for_world(self, world_name):
        setting_names = set()
        if not world_name or not self.workflow_data_dir:
            return []
        world_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', world_name)
        if not os.path.isdir(world_settings_dir):
            return []
        for filename in os.listdir(world_settings_dir):
            if filename.lower().endswith('_setting.json'):
                file_path = os.path.join(world_settings_dir, filename)
                try:
                    setting_data = self._load_json(file_path)
                    display_name = setting_data.get('name')
                    if not display_name:
                        base_name = filename[:-len('_setting.json')]
                        display_name = base_name.replace('_', ' ').title()
                    if display_name:
                        setting_names.add(display_name)
                except Exception:
                    continue
        return sorted(list(setting_names))

    def _update_world_setting_dropdown(self):
        if not self.world_setting_dropdown or not self.current_world_name:
            return
        self.world_setting_dropdown.blockSignals(True)
        self.world_setting_dropdown.clear()
        currently_linked_settings = set()
        selected_dot_linked_setting = None
        if self._world_selected_item_type == 'dot' and 0 <= self._world_selected_item_index < len(self._world_dots):
            selected_dot_data = self._world_dots[self._world_selected_item_index]
            if len(selected_dot_data) >= 5:
                selected_dot_linked_setting = selected_dot_data[4]
            for i, dot_data in enumerate(self._world_dots):
                if i != self._world_selected_item_index and len(dot_data) >= 5 and dot_data[3] == 'small':
                    if dot_data[4]:
                        currently_linked_settings.add(dot_data[4])
        else:
            for dot_data in self._world_dots:
                if len(dot_data) >= 5 and dot_data[3] == 'small' and dot_data[4]:
                    currently_linked_settings.add(dot_data[4])
        settings = self._get_setting_names_for_world(self.current_world_name)
        self.world_setting_dropdown.addItem("< Select Setting >")
        added_count = 0
        for display_name in settings:
            if display_name not in currently_linked_settings or display_name == selected_dot_linked_setting:
                self.world_setting_dropdown.addItem(display_name)
                added_count += 1
        index_to_select = 0
        if selected_dot_linked_setting:
            idx = self.world_setting_dropdown.findText(selected_dot_linked_setting)
            if idx != -1:
                index_to_select = idx
        self.world_setting_dropdown.setCurrentIndex(index_to_select)
        self.world_setting_dropdown.blockSignals(False)
        self.world_setting_dropdown.update()

    def _update_location_setting_dropdown(self):
        if not self.location_setting_dropdown or not self.current_world_name or not self.current_location_name:
            return
        self.location_setting_dropdown.blockSignals(True)
        self.location_setting_dropdown.clear()
        currently_linked_settings = set()
        selected_dot_linked_setting = None
        if self._location_selected_item_type == 'dot' and 0 <= self._location_selected_item_index < len(self._location_dots):
            selected_dot_data = self._location_dots[self._location_selected_item_index]
            if len(selected_dot_data) == 5:
                selected_dot_linked_setting = selected_dot_data[4]
            for i, dot_data in enumerate(self._location_dots):
                if i != self._location_selected_item_index and len(dot_data) == 5:
                    if dot_data[4]:
                        currently_linked_settings.add(dot_data[4])
        else:
            for dot_data in self._location_dots:
                if len(dot_data) == 5 and dot_data[4]:
                     currently_linked_settings.add(dot_data[4])
        settings = self._get_setting_names_for_location(self.current_world_name, self.current_location_name)
        self.location_setting_dropdown.addItem("< Select Setting >")
        added_count = 0
        for display_name in settings:
            if display_name not in currently_linked_settings or display_name == selected_dot_linked_setting:
                self.location_setting_dropdown.addItem(display_name)
                added_count += 1
        index_to_select = 0
        if selected_dot_linked_setting:
            idx = self.location_setting_dropdown.findText(selected_dot_linked_setting)
            if idx != -1:
                index_to_select = idx
        self.location_setting_dropdown.setCurrentIndex(index_to_select)
        self.location_setting_dropdown.blockSignals(False)
        self.location_setting_dropdown.update()

    def _get_location_names_for_world(self, world_name):
        location_names = []
        if not world_name:
            print("  Cannot get location names: No world name provided")
            return []
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', world_name) # MODIFIED path
        if not os.path.isdir(world_dir):
            print(f"  World directory not found: {world_dir}")
            return []
        try:
            for region_folder in os.listdir(world_dir):
                region_path = os.path.join(world_dir, region_folder)
                if os.path.isdir(region_path) and region_folder.lower() != 'resources':
                    try:
                        for location_folder in os.listdir(region_path):
                            location_path = os.path.join(region_path, location_folder)
                            if os.path.isdir(location_path):
                                sanitized_location_name = sanitize_path_name(location_folder)
                                loc_json_filename = f"{sanitized_location_name}_location.json"
                                loc_json_path = os.path.join(location_path, loc_json_filename)
                                if os.path.isfile(loc_json_path):
                                    try:
                                        loc_data = self._load_json(loc_json_path)
                                        display_name = loc_data.get('name', location_folder.replace('_', ' ').title())
                                        location_names.append(display_name)
                                    except Exception as e:
                                        print(f"  Error loading location JSON at {loc_json_path}: {e}")
                    except Exception as e:
                        print(f"  Error scanning locations in region {region_folder}: {e}")
                        continue
        except Exception as e:
            print(f"  Error scanning for world locations: {e}")
        unique_locations = list(set(location_names))

        return unique_locations

    def _get_setting_names_for_world(self, world_name):
        setting_names = set()
        if not world_name or not self.workflow_data_dir:
            print("  Cannot get settings: Missing world name or workflow directory.")
            return []
        world_settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', world_name) # MODIFIED path
        if not os.path.isdir(world_settings_dir):
            print(f"  World settings directory not found: {world_settings_dir}")
            return []
        for root, dirs, files in os.walk(world_settings_dir):
            if os.path.basename(root) == 'resources' and os.path.dirname(root) == world_settings_dir:
                dirs[:] = []
                continue
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    file_path = os.path.join(root, filename)
                    try:
                        setting_data = self._load_json(file_path)
                        display_name = setting_data.get('name')
                        if not display_name:
                            base_name = filename[:-len('_setting.json')]
                            display_name = base_name.replace('_', ' ').title()
                        if display_name:
                            setting_names.add(display_name)
                    except Exception as e:
                        print(f"  Error reading setting file {file_path}: {e}")
        unique_sorted_names = sorted(list(setting_names))
        return unique_sorted_names

    def _get_setting_names_for_location(self, world_name, location_name, location_dir_path=None):
        setting_names = []
        if not world_name or not location_name:
            print("  Cannot get setting names: Missing world name or location name")
            return []
        if not location_dir_path:
            try:
                from editor_panel.world_editor.world_editor_auto import find_location_folder_by_display_name
                world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', world_name)
                found_path = None
                for region_folder in os.listdir(world_dir):
                    region_path = os.path.join(world_dir, region_folder)
                    if os.path.isdir(region_path) and region_folder.lower() != 'resources':
                        candidate = find_location_folder_by_display_name(region_path, location_name)
                        if candidate:
                            found_path = candidate
                            break
                if found_path:
                    location_dir_path = found_path
                else:
                    return []
            except Exception as e:
                print(f"  Error finding location path: {e}")
                return []
        if not os.path.isdir(location_dir_path):
            print(f"    Location directory path does not exist: {location_dir_path}")
            return []
        try:
            for filename in os.listdir(location_dir_path):
                if filename.lower().endswith("_setting.json"):
                    file_path = os.path.join(location_dir_path, filename)
                    if os.path.isfile(file_path):
                        try:
                            setting_data = self._load_json(file_path)
                            display_name = setting_data.get('name', filename.replace("_setting.json", "").replace("_", " ").title())
                            setting_names.append(display_name)
                        except Exception as e:
                            print(f"  Error loading setting JSON at {file_path}: {e}")
        except Exception as e:
            print(f"  Error scanning for location settings in {location_dir_path}: {e}")
        unique_settings = list(set(setting_names))
        return unique_settings

    def _find_location_path(self, world_name, location_display_name):
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', world_name)
        if not os.path.isdir(world_dir):
            print(f"    World directory not found: {world_dir}")
            return None
        try:
            for region_folder in os.listdir(world_dir):
                region_path = os.path.join(world_dir, region_folder)
                if os.path.isdir(region_path) and region_folder.lower() != 'resources':
                    for location_folder in os.listdir(region_path):
                        location_path = os.path.join(region_path, location_folder)
                        if os.path.isdir(location_path):
                            if location_folder.lower() == location_display_name.lower():
                                return location_path
        except OSError as e:
            print(f"  Error searching for location path: {e}")
        print(f"    Location path not found for '{location_display_name}'.")
        return None
    
    def _on_world_location_selected(self, index):
        if not self.world_location_dropdown: return
        selected_text = self.world_location_dropdown.itemText(index)
        link_name_to_save = None
        if index == 0 or selected_text == "< Select Location >":
            link_name_to_save = None
        else:
             link_name_to_save = selected_text
        selected_dot_index = self._world_selected_item_index
        selected_dot_type = self._world_selected_item_type
        if selected_dot_type == 'dot' and 0 <= selected_dot_index < len(self._world_dots):
            current_dot_data = list(self._world_dots[selected_dot_index])
            if len(current_dot_data) == 6:
                if current_dot_data[3] == 'big' or current_dot_data[3] == 'medium':
                    current_linked_name = current_dot_data[4]
                    if current_linked_name != link_name_to_save:
                        action = "Linking" if link_name_to_save else "Unlinking"
                        print(f"{action} location '{link_name_to_save if link_name_to_save else ''}' to dot {selected_dot_index}")
                        current_dot_data[4] = link_name_to_save
                        self._world_dots[selected_dot_index] = tuple(current_dot_data)
                        self._save_world_map_data()
                        if link_name_to_save:
                            region_name = current_dot_data[5] if len(current_dot_data) > 5 else None
                            self._update_location_region(link_name_to_save, region_name)
                        if link_name_to_save:
                            if hasattr(self, 'world_location_label') and self.world_location_label: self.world_location_label.setVisible(False)
                            if hasattr(self, 'world_location_dropdown') and self.world_location_dropdown: self.world_location_dropdown.setVisible(False)
                            if hasattr(self, 'world_unlink_location_btn') and self.world_unlink_location_btn: self.world_unlink_location_btn.setVisible(True)
                        else:
                            if hasattr(self, 'world_location_label') and self.world_location_label: self.world_location_label.setVisible(True)
                            if hasattr(self, 'world_location_dropdown') and self.world_location_dropdown: 
                                self.world_location_dropdown.setVisible(True)
                            if hasattr(self, 'world_unlink_location_btn') and self.world_unlink_location_btn: self.world_unlink_location_btn.setVisible(False)
                        select_item(self, 'world', 'dot', selected_dot_index)
                        if hasattr(self, 'world_map_label') and self.world_map_label: self.world_map_label.update()
                    else:
                        print(f"Link '{link_name_to_save}' already set for dot {selected_dot_index}.")
                else:
                     print(f"Error: Cannot link World Dot {selected_dot_index} (type {current_dot_data[3]}) to a location. Linkable types are 'big' or 'medium'.")
            elif len(current_dot_data) == 5:
                 print(f"Warning: Dot {selected_dot_index} has old 5-element format. Attempting to link, but region update will be skipped.")
                 if current_dot_data[3] == 'big' or current_dot_data[3] == 'medium':
                    if current_dot_data[4] != link_name_to_save:
                        current_dot_data[4] = link_name_to_save
                        self._world_dots[selected_dot_index] = tuple(current_dot_data + [None])
                        self._save_world_map_data()
                        select_item(self, 'world', 'dot', selected_dot_index)
                        self._update_world_location_dropdown()
                        self.world_map_label.update()
                        print(f"Linked location '{link_name_to_save}' to dot {selected_dot_index} (was 5-tuple). Region not updated.")
        else:
             if link_name_to_save is not None:
                 print(f"World Location Dropdown: No dot selected, ignoring selection '{selected_text}'")

    def _update_location_region(self, location_name, region_name):
        if not self.current_world_name or not location_name:
            return False
        current_location_path = None
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        current_region_folder = None
        for region_folder in os.listdir(world_dir):
            region_path = os.path.join(world_dir, region_folder)
            if os.path.isdir(region_path) and region_folder.lower() != 'resources':
                for location_folder in os.listdir(region_path):
                    location_path = os.path.join(region_path, location_folder)
                    if os.path.isdir(location_path):
                        try:
                            loc_json_filename = f"{sanitize_path_name(location_folder)}_location.json"
                            loc_json_path = os.path.join(location_path, loc_json_filename)
                            if os.path.isfile(loc_json_path):
                                loc_data = self._load_json(loc_json_path)
                                display_name = loc_data.get('name', location_folder.replace('_', ' ').title())
                                if display_name.lower() == location_name.lower():
                                    current_location_path = location_path
                                    current_region_folder = region_folder
                                    break
                        except Exception as e:
                            print(f"[ERROR] Error checking location: {e}")
                if current_location_path:
                    break
        if not current_location_path:
            return False
        if not region_name or region_name == "__global__":
            return True
        target_region_folder = sanitize_path_name(region_name)
        if current_region_folder.lower() == target_region_folder.lower():
            return True
        target_region_path = os.path.join(world_dir, target_region_folder)
        if not os.path.isdir(target_region_path):
            try:
                os.makedirs(target_region_path, exist_ok=True)
            except Exception as e:
                return False
        location_folder_name = os.path.basename(current_location_path)
        target_location_path = os.path.join(target_region_path, location_folder_name)
        try:
            if os.path.exists(target_location_path):
                for item in os.listdir(current_location_path):
                    src = os.path.join(current_location_path, item)
                    dst = os.path.join(target_location_path, item)
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                shutil.rmtree(current_location_path)
            else:
                shutil.move(current_location_path, target_location_path)
            if hasattr(self, 'current_location_name') and self.current_location_name == location_name:
                self._world_region_name = target_region_folder
            return True
        except Exception as e:
            print(f"[ERROR] Failed to move/merge location directory: {e}")
            return False

    def _update_setting_region(self, setting_name, region_name, location_name):
        if not self.current_world_name or not setting_name:
            return False
        search_dirs = [
            os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name),
            os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        ]
        current_setting_path = None
        for world_dir in search_dirs:
            if not os.path.isdir(world_dir):
                continue
            setting_json_filename = f"{sanitize_path_name(setting_name)}_setting.json"
            world_level_setting_path = os.path.join(world_dir, setting_json_filename)
            if os.path.isfile(world_level_setting_path):
                current_setting_path = world_level_setting_path
                break
            for region_folder in os.listdir(world_dir):
                region_path = os.path.join(world_dir, region_folder)
                if os.path.isdir(region_path) and region_folder.lower() != 'resources':
                    region_level_setting_path = os.path.join(region_path, setting_json_filename)
                    if os.path.isfile(region_level_setting_path):
                        current_setting_path = region_level_setting_path
                        break
                    for location_folder in os.listdir(region_path):
                        location_path = os.path.join(region_path, location_folder)
                        if os.path.isdir(location_path):
                            setting_json_path = os.path.join(location_path, setting_json_filename)
                            if os.path.isfile(setting_json_path):
                                current_setting_path = setting_json_path
                                break
                    if current_setting_path:
                        break
            if current_setting_path:
                break
        if not current_setting_path:
            return False
        is_resource_file = 'resources' in current_setting_path
        if not is_resource_file and 'game' in current_setting_path:
            target_world_dir = os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name)
            setting_json_filename = f"{sanitize_path_name(setting_name)}_setting.json"
            if not region_name or region_name == "__global__":
                os.makedirs(target_world_dir, exist_ok=True)
                target_setting_path = os.path.join(target_world_dir, setting_json_filename)
            else:
                target_region_folder = sanitize_path_name(region_name)
                target_region_path = os.path.join(target_world_dir, target_region_folder)
                if not os.path.isdir(target_region_path):
                    try:
                        os.makedirs(target_region_path, exist_ok=True)
                    except Exception as e:
                        return False
                if location_name and location_name != setting_name:
                    target_location_path = os.path.join(target_region_path, sanitize_path_name(location_name))
                    if not os.path.isdir(target_location_path):
                        try:
                            os.makedirs(target_location_path, exist_ok=True)
                        except Exception as e:
                            return False
                    target_setting_path = os.path.join(target_location_path, setting_json_filename)
                else:
                    target_setting_path = os.path.join(target_region_path, setting_json_filename)
            if os.path.normpath(current_setting_path) == os.path.normpath(target_setting_path):
                return True
            try:
                if os.path.exists(target_setting_path):
                    with open(target_setting_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    display_name = data.get('name', setting_name)
                    if display_name.lower() == setting_name.lower():
                        os.remove(current_setting_path)
                        return True
                    else:
                        return False
                with open(current_setting_path, 'r', encoding='utf-8') as f:
                    setting_data = json.load(f)
                os.makedirs(os.path.dirname(target_setting_path), exist_ok=True)
                with open(target_setting_path, 'w', encoding='utf-8') as f:
                    json.dump(setting_data, f, indent=2)
                os.remove(current_setting_path)
                return True
            except Exception as e:
                return False
        else:
            return True

    def _on_world_setting_selected(self, index):
        if not self.world_setting_dropdown: return
        selected_text = self.world_setting_dropdown.itemText(index)
        link_name_to_save = None
        if index == 0 or selected_text == "< Select Setting >":
            link_name_to_save = None
        else:
            link_name_to_save = selected_text
        selected_dot_index = self._world_selected_item_index
        selected_dot_type = self._world_selected_item_type
        if selected_dot_type == 'dot' and 0 <= selected_dot_index < len(self._world_dots):
            current_dot_data = list(self._world_dots[selected_dot_index])
            if len(current_dot_data) >= 5:
                if current_dot_data[3] == 'small':
                    if current_dot_data[4] != link_name_to_save:
                        action = "Linking" if link_name_to_save else "Unlinking"
                        current_dot_data[4] = link_name_to_save
                        if len(current_dot_data) >= 6:
                            region_name = current_dot_data[5]
                            self._world_dots[selected_dot_index] = tuple(current_dot_data)
                        else:
                            self._world_dots[selected_dot_index] = tuple(current_dot_data)
                        self._save_world_map_data()
                        if link_name_to_save:
                            region_name = current_dot_data[5] if len(current_dot_data) > 5 else None
                            location_name = None
                            for dot in self._world_dots:
                                if dot[3] in ('big', 'medium') and dot[4] and dot[4] == link_name_to_save:
                                    location_name = link_name_to_save
                                    break
                            self._update_setting_region(link_name_to_save, region_name, location_name)
                        select_item(self, 'world', 'dot', selected_dot_index)
                        self._update_world_setting_dropdown()
                        self.world_map_label.update()
        else:
            if link_name_to_save is not None:
                print(f"World Setting Dropdown: No dot selected, ignoring selection '{selected_text}'")
        self.current_world_setting_name = selected_text

    def _on_location_setting_selected(self, index):
        if not self.location_setting_dropdown: return
        selected_text = self.location_setting_dropdown.itemText(index)
        link_name_to_save = None
        if index == 0 or selected_text == "< Select Setting >":
            link_name_to_save = None
        else:
            link_name_to_save = selected_text
        selected_dot_index = self._location_selected_item_index
        selected_dot_type = self._location_selected_item_type
        if selected_dot_type == 'dot' and 0 <= selected_dot_index < len(self._location_dots):
            current_dot_data = list(self._location_dots[selected_dot_index])
            if (len(current_dot_data) == 5 or len(current_dot_data) == 6):
                if current_dot_data[3] == 'small':
                    if current_dot_data[4] != link_name_to_save:
                        action = "Linking" if link_name_to_save else "Unlinking"
                        current_dot_data[4] = link_name_to_save
                        self._location_dots[selected_dot_index] = tuple(current_dot_data)
                        self._save_location_map_data()
                        select_item(self, 'location', 'dot', selected_dot_index)
                        self._update_location_setting_dropdown()
                        self.location_map_label.update()
        else:
            if link_name_to_save is not None:
                 print(f"Location Setting Dropdown: No dot selected, ignoring selection '{selected_text}'")
        self.current_location_setting_name = selected_text

    def _navigate_to_setting(self, setting_name):
        if not self.current_world_name:
            print("Cannot navigate to setting: No world selected")
            return False
        search_dirs = [
            os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name),
            os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        ]
        setting_json_filename = f"{sanitize_path_name(setting_name)}_setting.json"
        try:
            for world_dir in search_dirs:
                if not os.path.isdir(world_dir):
                    continue
                world_level_setting_path = os.path.join(world_dir, setting_json_filename)
                if os.path.isfile(world_level_setting_path):
                    if hasattr(self, 'world_setting_dropdown') and self.world_setting_dropdown:
                        idx = self.world_setting_dropdown.findText(setting_name)
                        if idx >= 0:
                            self._on_world_setting_selected(idx)
                            if hasattr(self, 'nested_tab_widget'):
                                world_tab_index = self.nested_tab_widget.indexOf(self.world_tab)
                                if world_tab_index >= 0:
                                    self.nested_tab_widget.setCurrentIndex(world_tab_index)
                            return True
            for world_dir in search_dirs:
                if not os.path.isdir(world_dir):
                    continue
                for region_folder in os.listdir(world_dir):
                    region_path = os.path.join(world_dir, region_folder)
                    if not os.path.isdir(region_path) or region_folder.lower() == 'resources':
                        continue
                    region_level_setting_path = os.path.join(region_path, setting_json_filename)
                    if os.path.isfile(region_level_setting_path):
                        if hasattr(self, 'world_setting_dropdown') and self.world_setting_dropdown:
                            idx = self.world_setting_dropdown.findText(setting_name)
                            if idx >= 0:
                                self._on_world_setting_selected(idx)
                                if hasattr(self, 'nested_tab_widget'):
                                    world_tab_index = self.nested_tab_widget.indexOf(self.world_tab)
                                    if world_tab_index >= 0:
                                        self.nested_tab_widget.setCurrentIndex(world_tab_index)
                                return True
                    for location_folder in os.listdir(region_path):
                        location_path = os.path.join(region_path, location_folder)
                        if not os.path.isdir(location_path):
                            continue
                        for file in os.listdir(location_path):
                            if file.lower().endswith('_setting.json'):
                                setting_json_path = os.path.join(location_path, file)
                                if os.path.isfile(setting_json_path):
                                    setting_data = self._load_json(setting_json_path)
                                    display_name = setting_data.get('name', file.replace('_setting.json', '').replace('_', ' ').title())
                                    if display_name.lower() == setting_name.lower():
                                        sanitized_location_name = sanitize_path_name(location_folder)
                                        loc_json_path = os.path.join(location_path, f"{sanitized_location_name}_location.json")
                                        if os.path.isfile(loc_json_path):
                                            loc_data = self._load_json(loc_json_path)
                                            location_display_name = loc_data.get('name', location_folder.replace('_', ' ').title())
                                            print(f"Found setting '{setting_name}' in location '{location_display_name}'")
                                            self.set_location(location_display_name)
                                            self._select_location_setting(setting_name)
                                            if hasattr(self, 'nested_tab_widget'):
                                                location_tab_index = self.nested_tab_widget.indexOf(self.location_tab)
                                                if location_tab_index >= 0:
                                                    self.nested_tab_widget.setCurrentIndex(location_tab_index)
                                            return True         
        except OSError as e:
            print(f"Error searching for setting '{setting_name}': {e}")
            return False

    def _select_location_setting(self, setting_name):
        if not self.current_location_name or not setting_name:
            return False
        if self.location_setting_dropdown:
            self.location_setting_dropdown.blockSignals(True)
            idx = self.location_setting_dropdown.findText(setting_name)
            if idx >= 0:
                self.location_setting_dropdown.setCurrentIndex(idx)
            self.location_setting_dropdown.blockSignals(False)
        for idx, dot in enumerate(self._location_dots):
            if len(dot) >= 5:
                linked_name = dot[4]
                if linked_name and linked_name.lower() == setting_name.lower():
                    select_item(self, 'location', 'dot', idx)
                    if hasattr(self, 'location_map_label'):
                        self.location_map_label.update()
                    return True
        return False
        
    def update_location_from_setting(self, setting_name, location_name):
        if not setting_name or not location_name:
            print("[ERROR] update_location_from_setting: Missing setting name or location name")
            return False
        old_location = self.current_location_name
        if old_location != location_name:
            self.set_location(location_name)
        if self._select_location_setting(setting_name):
            if hasattr(self, 'nested_tab_widget'):
                location_tab_index = self.nested_tab_widget.indexOf(self.location_tab)
                if location_tab_index >= 0:
                    self.nested_tab_widget.setCurrentIndex(location_tab_index)
            return True
        else:
            return False

    def _save_json(self, file_path, data):
        if not file_path:
            return False
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            print(f"WorldEditorWidget: Error writing JSON to {file_path}: {e}")
            return False
        except Exception as e:
            print(f"WorldEditorWidget: Unexpected error writing JSON to {file_path}: {e}")
            return False

    def handle_tab_activated(self):
        if self.current_world_name:
            if hasattr(self, '_region_masks') and self._region_masks:
                self._init_region_masks()
            locations = self._get_location_names_for_world(self.current_world_name)
            settings = self._get_setting_names_for_world(self.current_world_name)
            if self.current_location_name:
                location_settings = self._get_setting_names_for_location(self.current_world_name, self.current_location_name)
        self.force_populate_dropdowns()
        if self.current_world_name and not self.current_location_name:
            locations = self._get_location_names_for_world(self.current_world_name)
            if locations:
                default_location = sorted(locations)[0]
                self.set_location(default_location)

    def _get_dropdown_widgets(self):
        world_location_dropdown = self.world_location_dropdown
        world_setting_dropdown = self.world_setting_dropdown
        location_setting_dropdown = self.location_setting_dropdown
        if not world_location_dropdown:
            world_location_dropdown = self.findChild(QComboBox, "WorldLocationDropdown")
        if not world_setting_dropdown:
            world_setting_dropdown = self.findChild(QComboBox, "WorldSettingDropdown")
        if not location_setting_dropdown:
            location_setting_dropdown = self.findChild(QComboBox, "LocationSettingDropdown")
        if not world_location_dropdown and hasattr(self, 'world_tab') and self.world_tab:
            world_location_dropdown = self.world_tab.findChild(QComboBox, "WorldLocationDropdown")
        if not world_setting_dropdown and hasattr(self, 'world_tab') and self.world_tab:
            world_setting_dropdown = self.world_tab.findChild(QComboBox, "WorldSettingDropdown")
        if not location_setting_dropdown and hasattr(self, 'location_tab') and self.location_tab:
            location_setting_dropdown = self.location_tab.findChild(QComboBox, "LocationSettingDropdown")
        if hasattr(self, 'world_tab') and self.world_tab:
            world_splitter = self.world_tab.findChild(QSplitter)
            if world_splitter and world_splitter.count() > 0:
                world_toolbar = world_splitter.widget(0)
                if world_toolbar:
                    if not world_location_dropdown:
                        world_location_dropdown = world_toolbar.findChild(QComboBox, "WorldLocationDropdown")
                    if not world_setting_dropdown:
                        world_setting_dropdown = world_toolbar.findChild(QComboBox, "WorldSettingDropdown")
        if hasattr(self, 'location_tab') and self.location_tab:
            location_splitter = self.location_tab.findChild(QSplitter)
            if location_splitter and location_splitter.count() > 0:
                location_toolbar = location_splitter.widget(0)
                if location_toolbar:
                    if not location_setting_dropdown:
                        location_setting_dropdown = location_toolbar.findChild(QComboBox, "LocationSettingDropdown")
        if not world_location_dropdown or not world_setting_dropdown or not location_setting_dropdown:
            all_combos = self.findChildren(QComboBox)
            for i, combo in enumerate(all_combos):
                if not world_location_dropdown and "location" in combo.objectName().lower() and "world" in combo.objectName().lower():
                    world_location_dropdown = combo
                if not world_setting_dropdown and "setting" in combo.objectName().lower() and "world" in combo.objectName().lower():
                    world_setting_dropdown = combo
                if not location_setting_dropdown and "setting" in combo.objectName().lower() and "location" in combo.objectName().lower():
                    location_setting_dropdown = combo
        return (world_location_dropdown, world_setting_dropdown, location_setting_dropdown)

    def force_populate_dropdowns(self):
        world_location_dropdown, world_setting_dropdown, location_setting_dropdown = self._get_dropdown_widgets()
        if not world_location_dropdown:
            world_location_dropdown = QComboBox(self)
            world_location_dropdown.setObjectName("WorldLocationDropdown")
            world_location_dropdown.currentIndexChanged.connect(self._on_world_location_selected)
            self.world_location_dropdown = world_location_dropdown
        if not world_setting_dropdown:
            world_setting_dropdown = QComboBox(self)
            world_setting_dropdown.setObjectName("WorldSettingDropdown")
            world_setting_dropdown.currentIndexChanged.connect(self._on_world_setting_selected)
            self.world_setting_dropdown = world_setting_dropdown
        if not location_setting_dropdown:
            location_setting_dropdown = QComboBox(self)
            location_setting_dropdown.setObjectName("LocationSettingDropdown")
            location_setting_dropdown.currentIndexChanged.connect(self._on_location_setting_selected)
            self.location_setting_dropdown = location_setting_dropdown
        if world_location_dropdown:
            world_location_dropdown.blockSignals(True)
            world_location_dropdown.clear()
            if not self.current_world_name:
                world_location_dropdown.addItem("< No World Selected >")
            else:
                world_location_dropdown.addItem("< Select Location >")
                location_names = self._get_location_names_for_world(self.current_world_name)
                if location_names:
                    for name in sorted(location_names):
                        if name:
                            world_location_dropdown.addItem(name)
                    if self.current_location_name:
                        idx = world_location_dropdown.findText(self.current_location_name)
                        if idx != -1:
                            world_location_dropdown.setCurrentIndex(idx)
                        else:
                            world_location_dropdown.setCurrentIndex(0)
                    else:
                        world_location_dropdown.setCurrentIndex(0)
            world_location_dropdown.blockSignals(False)
        if world_setting_dropdown:
            current_selection_text = world_setting_dropdown.currentText()
            world_setting_dropdown.blockSignals(True)
            world_setting_dropdown.clear()
            if not self.current_world_name:
                world_setting_dropdown.addItem("< No World Selected >")
                world_setting_dropdown.setCurrentIndex(0)
            else:
                world_setting_dropdown.addItem("< Select Setting >")
                setting_names = self._get_setting_names_for_world(self.current_world_name)
                if setting_names:
                    for name in sorted(setting_names):
                        if name:
                            world_setting_dropdown.addItem(name)
                    target_setting = self.current_world_setting_name if hasattr(self, 'current_world_setting_name') else current_selection_text
                    if target_setting:
                        idx = world_setting_dropdown.findText(target_setting)
                        if idx > 0:
                            world_setting_dropdown.setCurrentIndex(idx)
                        else:
                             world_setting_dropdown.setCurrentIndex(0)
                    else:
                        world_setting_dropdown.setCurrentIndex(0)
                    world_setting_dropdown.setCurrentIndex(0)
            world_setting_dropdown.blockSignals(False)
        if location_setting_dropdown:
            current_selection_text = location_setting_dropdown.currentText()
            location_setting_dropdown.blockSignals(True)
            location_setting_dropdown.clear()
            if not self.current_world_name or not self.current_location_name:
                location_setting_dropdown.addItem("< No Location Selected >")
                location_setting_dropdown.setCurrentIndex(0)
            else:
                location_setting_dropdown.addItem("< Select Setting >")
                setting_names = self._get_setting_names_for_location(self.current_world_name, self.current_location_name)
                if setting_names:
                    for name in sorted(setting_names):
                        if name:
                            location_setting_dropdown.addItem(name)
                    target_setting = self.current_location_setting_name if hasattr(self, 'current_location_setting_name') else current_selection_text
                    if target_setting:
                         idx = location_setting_dropdown.findText(target_setting)
                         if idx > 0:
                             location_setting_dropdown.setCurrentIndex(idx)
                         else:
                             location_setting_dropdown.setCurrentIndex(0)
                    else:
                         location_setting_dropdown.setCurrentIndex(0)
                else:
                    location_setting_dropdown.setCurrentIndex(0)
            location_setting_dropdown.blockSignals(False)

    def _get_dot_description(self, dot_index, dot_list):
        if 0 <= dot_index < len(dot_list):
            dot_data = dot_list[dot_index]
            x, y, size, dot_type, name, desc = dot_data[:6]
            type_display = f"{dot_type.capitalize()} Dot"
            region_name = self._get_region_at_point(x, y)
            if region_name:
                display_region = self._format_region_name_for_display(region_name)
                return f"{type_display} ({x:.1f}, {y:.1f}) in {display_region}"
            else:
                return f"{type_display} ({x:.1f}, {y:.1f})"
        return ""

    def _format_region_name_for_display(self, region_name):
        if not region_name:
            return ""
        return region_name.replace('_', ' ')

    def _on_region_select_submode_clicked(self):
        if hasattr(self, '_world_region_sub_mode'):
            self._world_region_sub_mode = 'select'
        if hasattr(self, 'world_region_select_submode_btn') and self.world_region_select_submode_btn:
            self.world_region_select_submode_btn.setChecked(True)
        if hasattr(self, 'world_region_paint_submode_btn') and self.world_region_paint_submode_btn:
            self.world_region_paint_submode_btn.setChecked(False)
        self._update_region_cursor_and_draw_mode()
        
    def _on_region_paint_submode_clicked(self):
        self._world_region_sub_mode = 'paint'
        if hasattr(self, 'world_region_select_submode_btn') and self.world_region_select_submode_btn:
            self.world_region_select_submode_btn.setChecked(False)
        if hasattr(self, 'world_region_paint_submode_btn') and self.world_region_paint_submode_btn:
            self.world_region_paint_submode_btn.setChecked(True)
        self._update_region_cursor_and_draw_mode()


    def _update_region_cursor_and_draw_mode(self):
        if self._world_draw_mode != 'region_edit':
            return
        if hasattr(self, 'world_map_label') and self.world_map_label:
            if self._world_region_sub_mode == 'select':
                self.world_map_label.setCursor(Qt.PointingHandCursor)
            else:
                self.world_map_label.setCursor(Qt.CrossCursor)
        brush_size_label = getattr(self, 'world_brush_size_label', None)
        brush_size_slider = getattr(self, 'world_brush_size_slider', None)
        
        if self._world_region_sub_mode == 'paint':
            if brush_size_label: brush_size_label.setVisible(True)
            if brush_size_slider: brush_size_slider.setVisible(True)
        else:
            if brush_size_label: brush_size_label.setVisible(False)
            if brush_size_slider: brush_size_slider.setVisible(False)
            
    def _on_brush_size_changed(self, value):
        self._region_brush_size = value

    def _rebuild_region_mask_from_strokes(self, region_name):
        if not hasattr(self, '_region_masks'):
            self._region_masks = {}
        if hasattr(self, 'world_map_label') and self.world_map_label._crt_image:
            base_width = self.world_map_label._crt_image.width()
            base_height = self.world_map_label._crt_image.height()
        else:
            base_width = getattr(self.world_map_label, '_virtual_width', 1000) if hasattr(self, 'world_map_label') else 1000
            base_height = getattr(self.world_map_label, '_virtual_height', 1000) if hasattr(self, 'world_map_label') else 1000
        mask_scale = getattr(self, '_region_mask_scale', 1.0)
        mask_width = int(base_width * mask_scale)
        mask_height = int(base_height * mask_scale)
        if mask_width <= 0 or mask_height <= 0:
            if hasattr(self, '_region_border_cache'):
                self._region_border_cache[region_name] = []
            return
        if region_name not in self._region_masks or self._region_masks[region_name].isNull() or \
           self._region_masks[region_name].width() != mask_width or self._region_masks[region_name].height() != mask_height:
            mask = QImage(mask_width, mask_height, QImage.Format_ARGB32)
            mask.fill(QColor(0, 0, 0, 0))
            self._region_masks[region_name] = mask
        else:
            self._region_masks[region_name].fill(QColor(0, 0, 0, 0))
        mask = self._region_masks[region_name]
        name_hash = sum(ord(c) for c in region_name) if region_name else 0
        hue = (name_hash % 360) / 360.0
        region_color = QColor.fromHsvF(hue, 0.7, 0.8, 0.5)
        stroke_data = self._world_regions.get(region_name, [])
        if not stroke_data:
            mask.fill(QColor(0, 0, 0, 0))
            if hasattr(self, '_region_border_cache'):
                self._region_border_cache[region_name] = []
            if mask.format() != QImage.Format_ARGB32:
                 self._region_masks[region_name] = mask.convertToFormat(QImage.Format_ARGB32)
            if hasattr(self, '_region_border_cache'):
                from region_toolbar import update_region_border_cache
                import functools
                update_func = functools.partial(update_region_border_cache, self, region_name)
                QTimer.singleShot(300, update_func)
            return
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.setBrush(QBrush(region_color))
        painter.setPen(Qt.NoPen)
        batch_size = 200
        for i in range(0, len(stroke_data), batch_size):
            batch = stroke_data[i:i+batch_size]
            for x_stroke, y_stroke, brush_size_stroke_img in batch:
                try:
                    scaled_x = x_stroke * mask_scale
                    scaled_y = y_stroke * mask_scale
                    scaled_brush_diameter = brush_size_stroke_img * mask_scale
                    scaled_brush_diameter = max(1.0, scaled_brush_diameter)
                    radius_x = scaled_brush_diameter / 2.0
                    radius_y = scaled_brush_diameter / 2.0
                    painter.drawEllipse(QPointF(scaled_x, scaled_y), radius_x, radius_y)
                except Exception as e:
                    print(f"[ERROR] _rebuild_region_mask_from_strokes: Failed to process/draw stroke point ({x_stroke}, {y_stroke}, {brush_size_stroke_img}): {str(e)}")
        painter.end()
        if mask.format() != QImage.Format_ARGB32:
            self._region_masks[region_name] = mask.convertToFormat(QImage.Format_ARGB32)
        try:
            import numpy as np
            import cv2
            mask_bits = mask.bits()
            mask_bits.setsize(mask.byteCount())
            mask_array_rgba = np.frombuffer(mask_bits, dtype=np.uint8).reshape((mask.height(), mask.width(), 4))
            mask_alpha = mask_array_rgba[..., 3].copy()
            for other_name, other_mask in self._region_masks.items():
                if other_name != region_name and not other_mask.isNull() and \
                   other_mask.width() == mask.width() and other_mask.height() == mask.height():
                    other_bits = other_mask.bits()
                    other_bits.setsize(other_mask.byteCount())
                    other_array_rgba = np.frombuffer(other_bits, dtype=np.uint8).reshape((other_mask.height(), other_mask.width(), 4))
                    other_alpha = other_array_rgba[..., 3]
                    overlap = np.logical_and(mask_alpha > 0, other_alpha > 0)
                    if np.any(overlap):
                        kernel = np.ones((3, 3), np.uint8)
                        dilated_overlap = cv2.dilate(overlap.astype(np.uint8), kernel, iterations=1)
                        mask_alpha[dilated_overlap > 0] = 0
                        mask_array_rgba[..., 3] = mask_alpha
            modified_mask = QImage(mask_array_rgba.data, mask.width(), mask.height(), QImage.Format_ARGB32)
            modified_mask.bits()
            self._region_masks[region_name] = modified_mask
        except (ImportError, Exception) as e:
            for other_name, other_mask in self._region_masks.items():
                if other_name != region_name and not other_mask.isNull():
                    if mask.width() == other_mask.width() and mask.height() == other_mask.height():
                        conflict_painter = QPainter(mask)
                        conflict_painter.setCompositionMode(QPainter.CompositionMode_DestinationOut)
                        sample_stride = 5
                        for y in range(0, other_mask.height(), sample_stride):
                            for x in range(0, other_mask.width(), sample_stride):
                                if other_mask.pixelColor(x, y).alpha() > 0:
                                    if mask.pixelColor(x, y).alpha() > 0:
                                        conflict_painter.setBrush(Qt.black)
                                        conflict_painter.setPen(Qt.NoPen)
                                        conflict_painter.drawEllipse(QPointF(x, y), 3, 3)
                        conflict_painter.end()
        if hasattr(self, '_region_border_cache'):
            self._region_border_cache[region_name] = []
        if hasattr(self, '_shared_region_boundaries'):
            self._shared_region_boundaries.pop(region_name, None)
        if hasattr(self, '_region_border_cache'):
            from editor_panel.world_editor.region_toolbar import update_region_border_cache
            import functools
            update_func = functools.partial(update_region_border_cache, self, region_name)
            QTimer.singleShot(200, update_func)

    def _get_region_at_point(self, point_x, point_y):
        if not hasattr(self, '_region_masks') or not self._region_masks:
            return None
        mask_scale = getattr(self, '_region_mask_scale', 1.0)
        for region_name, mask in self._region_masks.items():
            if mask and not mask.isNull():
                scaled_x = int(point_x * mask_scale)
                scaled_y = int(point_y * mask_scale)
                if 0 <= scaled_x < mask.width() and 0 <= scaled_y < mask.height():
                    pixel = mask.pixel(scaled_x, scaled_y)
                    alpha = (pixel >> 24) & 0xFF
                    if alpha > 10:
                        return region_name
        return None

    def _update_dots_region_assignments(self, visible_area=None, update_files=False):
        if not hasattr(self, '_world_dots') or not self._world_dots:
            return False
        have_region_masks = hasattr(self, '_region_masks') and self._region_masks
        self._dots_modified = False
        modified_count = 0
        mask_scale = getattr(self, '_region_mask_scale', 1.0)
        visible_img_area = None
        if visible_area and len(visible_area) == 4:
            x1 = visible_area[0] / mask_scale if mask_scale > 0 else visible_area[0]
            y1 = visible_area[1] / mask_scale if mask_scale > 0 else visible_area[1]
            x2 = visible_area[2] / mask_scale if mask_scale > 0 else visible_area[2]
            y2 = visible_area[3] / mask_scale if mask_scale > 0 else visible_area[3]
            margin = 50
            visible_img_area = (x1 - margin, y1 - margin, x2 + margin, y2 + margin)
        dots_to_process = []
        for i, dot_data in enumerate(self._world_dots):
            if len(dot_data) < 2:
                continue
            x, y = dot_data[0], dot_data[1]
            if visible_img_area:
                if (x < visible_img_area[0] or x > visible_img_area[2] or
                    y < visible_img_area[1] or y > visible_img_area[3]):
                    continue
            dots_to_process.append((i, dot_data))
        for i, dot_data in dots_to_process:
            x, y = dot_data[0], dot_data[1]
            current_region = None
            if len(dot_data) >= 6:
                current_region = dot_data[5]
            new_region = self._get_region_at_point(x, y) if have_region_masks else None
            if current_region != new_region:
                self._dots_modified = True
                modified_count += 1
                old_region_display = "None" if current_region is None else f"'{current_region}'"
                new_region_display = "None (world-level)" if new_region is None else f"'{new_region}'"
                if len(dot_data) >= 6:
                    self._world_dots[i] = (x, y, dot_data[2], dot_data[3], dot_data[4], new_region)
                elif len(dot_data) == 5:
                    self._world_dots[i] = (x, y, dot_data[2], dot_data[3], dot_data[4], new_region)
                elif len(dot_data) == 4:
                    self._world_dots[i] = (x, y, dot_data[2], dot_data[3], None, new_region)
                if update_files:
                    dot_type = dot_data[3] if len(dot_data) >= 4 else None
                    linked_name = dot_data[4] if len(dot_data) >= 5 else None
                    if dot_type in ('big', 'medium') and linked_name:
                        self._update_location_region(linked_name, new_region)
                    elif dot_type == 'small' and linked_name:
                        self._update_setting_region(linked_name, new_region, linked_name)
        if not visible_area and modified_count > 0:
            self._save_world_map_data()
            if hasattr(self, 'world_map_label') and self.world_map_label:
                self.world_map_label.update()
            if self._world_selected_item_type == 'dot' and 0 <= self._world_selected_item_index < len(self._world_dots):
                select_item(self, 'world', 'dot', self._world_selected_item_index)
        return self._dots_modified

    def _on_world_unlink_location_clicked(self):
        if self._world_selected_item_type == 'dot' and self._world_selected_item_index != -1 and \
           0 <= self._world_selected_item_index < len(self._world_dots):
            current_dot_data = list(self._world_dots[self._world_selected_item_index])
            if not (len(current_dot_data) == 5 or len(current_dot_data) == 6):
                print(f"[ERROR] Cannot unlink: Dot {self._world_selected_item_index} has unexpected data format len: {len(current_dot_data)}.")
                return
            dot_type = current_dot_data[3]
            if dot_type not in ['big', 'medium']:
                if self.world_unlink_location_btn: self.world_unlink_location_btn.setVisible(False)
                if self.world_location_label: self.world_location_label.setVisible(False)
                if self.world_location_dropdown: self.world_location_dropdown.setVisible(False)
                return
            if current_dot_data[4] is None:
                if self.world_unlink_location_btn: self.world_unlink_location_btn.setVisible(False)
                if self.world_location_label: self.world_location_label.setVisible(True)
                if self.world_location_dropdown: 
                    self.world_location_dropdown.setVisible(True)
                    self._update_world_location_dropdown() 
                return
            current_dot_data[4] = None
            self._world_dots[self._world_selected_item_index] = tuple(current_dot_data)
            self._save_world_map_data()
            if self.world_unlink_location_btn: self.world_unlink_location_btn.setVisible(False)
            if self.world_location_label: self.world_location_label.setVisible(True)
            if self.world_location_dropdown: 
                self.world_location_dropdown.setVisible(True)
                self._update_world_location_dropdown()
            current_index = self._world_selected_item_index
            select_item(self, 'world', 'dot', current_index) 
            if hasattr(self, 'world_map_label') and self.world_map_label: 
                self.world_map_label.update()

    def _on_world_unlink_setting_clicked(self):
        if self._world_selected_item_type == 'dot' and self._world_selected_item_index != -1 and \
           0 <= self._world_selected_item_index < len(self._world_dots):
            current_dot_data = list(self._world_dots[self._world_selected_item_index])
            if not (len(current_dot_data) == 5 or len(current_dot_data) == 6):
                print(f"[ERROR] Cannot unlink: Dot {self._world_selected_item_index} has unexpected data format len: {len(current_dot_data)}")
                return
            dot_type = current_dot_data[3]
            if dot_type != 'small':
                print(f"[INFO] Cannot unlink: Selected dot {self._world_selected_item_index} is type '{dot_type}', not a setting dot.")
                if hasattr(self, 'world_unlink_setting_btn') and self.world_unlink_setting_btn:
                    self.world_unlink_setting_btn.setVisible(False)
                return
            if current_dot_data[4] is None:
                if hasattr(self, 'world_unlink_setting_btn') and self.world_unlink_setting_btn:
                    self.world_unlink_setting_btn.setVisible(False)
                for label_widget in self.world_tab.findChildren(QLabel):
                    if label_widget.text() == "Linked Settings:":
                        label_widget.setVisible(True)
                        break
                if hasattr(self, 'world_setting_dropdown') and self.world_setting_dropdown:
                    self.world_setting_dropdown.setVisible(True)
                    self._update_world_setting_dropdown()
                return
            old_setting_name = current_dot_data[4]
            current_dot_data[4] = None
            self._world_dots[self._world_selected_item_index] = tuple(current_dot_data)
            self._save_world_map_data()
            if hasattr(self, 'world_unlink_setting_btn') and self.world_unlink_setting_btn:
                self.world_unlink_setting_btn.setVisible(False)
            for label_widget in self.world_tab.findChildren(QLabel):
                if label_widget.text() == "Linked Settings:":
                    label_widget.setVisible(True)
                    break
            if hasattr(self, 'world_setting_dropdown') and self.world_setting_dropdown:
                self.world_setting_dropdown.setVisible(True)
                self._update_world_setting_dropdown()
                if old_setting_name and self.world_setting_dropdown.findText(old_setting_name) == -1:
                    self.world_setting_dropdown.addItem(old_setting_name)
            current_index = self._world_selected_item_index
            select_item(self, 'world', 'dot', current_index)
            if hasattr(self, 'world_map_label') and self.world_map_label:
                self.world_map_label.update()
            self.force_populate_dropdowns()

    def _on_location_unlink_setting_clicked(self):
        if self._location_selected_item_type == 'dot' and self._location_selected_item_index != -1 and \
           0 <= self._location_selected_item_index < len(self._location_dots):
            current_dot_data = list(self._location_dots[self._location_selected_item_index])
            if not (len(current_dot_data) == 5 or len(current_dot_data) == 6):
                print(f"[ERROR] Cannot unlink: Dot {self._location_selected_item_index} has unexpected data format len: {len(current_dot_data)}")
                return
            dot_type = current_dot_data[3]
            if dot_type != 'small':
                if self.location_unlink_setting_btn: self.location_unlink_setting_btn.setVisible(False)
                return
            if current_dot_data[4] is None:
                if self.location_unlink_setting_btn: self.location_unlink_setting_btn.setVisible(False)
                if self.location_setting_dropdown: self.location_setting_dropdown.setVisible(True)
                self._update_location_setting_dropdown()
                return
            old_setting_name = current_dot_data[4]
            current_dot_data[4] = None
            self._location_dots[self._location_selected_item_index] = tuple(current_dot_data)
            self._save_location_map_data()
            if self.location_unlink_setting_btn: 
                self.location_unlink_setting_btn.setVisible(False)
            if self.location_setting_dropdown: 
                self.location_setting_dropdown.setVisible(True)
                self._update_location_setting_dropdown()
                if old_setting_name and self.location_setting_dropdown.findText(old_setting_name) == -1:
                    self.location_setting_dropdown.addItem(old_setting_name)
            current_index = self._location_selected_item_index
            select_item(self, 'location', 'dot', current_index)
            if hasattr(self, 'location_map_label') and self.location_map_label:
                self.location_map_label.update()
            self.force_populate_dropdowns()

    def _set_path_mode(self, map_type, mode, checked):
        draw_button = getattr(self, f"{map_type}_draw_mode_btn", None)
        line_button = getattr(self, f"{map_type}_line_mode_btn", None)
        current_mode_attr = f"_{map_type}_path_mode"
        if mode == 'draw':
            if checked:
                setattr(self, current_mode_attr, 'draw')
                if line_button and line_button.isChecked():
                    line_button.setChecked(False)
            else:
                if line_button and not line_button.isChecked() and draw_button:
                    draw_button.setChecked(True) 
                    return
        elif mode == 'line':
            if checked:
                setattr(self, current_mode_attr, 'line')
                if draw_button and draw_button.isChecked():
                    draw_button.setChecked(False)
            else:
                if draw_button and not draw_button.isChecked() and line_button:
                    draw_button.setChecked(True)
                    setattr(self, current_mode_attr, 'draw')
                    if line_button.isChecked():
                         line_button.setChecked(False)
                    return
        if draw_button and line_button and not draw_button.isChecked() and not line_button.isChecked():
            draw_button.setChecked(True)
            setattr(self, current_mode_attr, 'draw')

    def _set_path_smoothness(self, map_type, value):
        target_smoothness_attr = f"_{map_type}_path_smoothness"
        setattr(self, target_smoothness_attr, value)
        print(f"Set {map_type} path smoothness to {value}")

    def get_path_mode(self, map_type):
        mode = getattr(self, f"_{map_type}_path_mode", 'draw')
        return mode
        
    def get_path_smoothness(self, map_type):
        return getattr(self, f"_{map_type}_path_smoothness", 50)

    def _set_path_details_mode(self, map_type, enabled):
        if enabled:
            if map_type == 'world' and hasattr(self, 'world_features_toolbar') and self.world_features_toolbar.is_feature_paint_mode():
                if hasattr(self.world_features_toolbar, 'feature_paint_btn'):
                    self.world_features_toolbar.feature_paint_btn.setChecked(False)
                self._on_feature_paint_toggled('world', False)
                self._update_feature_submode_widget_visibility('world')
            elif map_type == 'location' and hasattr(self, 'location_features_toolbar') and self.location_features_toolbar.is_feature_paint_mode():
                if hasattr(self.location_features_toolbar, 'feature_paint_btn'):
                    self.location_features_toolbar.feature_paint_btn.setChecked(False)
                self._on_feature_paint_toggled('location', False)
                self._update_feature_submode_widget_visibility('location')
        self._path_details_mode[map_type] = enabled
        self._selected_path_index[map_type] = None
        widgets = self._path_details_widgets.get(map_type, {})
        if widgets.get('widget'):
            widgets['widget'].setVisible(enabled)
        if enabled:
            if widgets.get('name_input'):
                widgets['name_input'].setText("")
                widgets['name_input'].setEnabled(True)
                widgets['name_input'].setReadOnly(self._path_assign_mode.get(map_type, False))
            if widgets.get('desc_input'):
                widgets['desc_input'].setText("")
                widgets['desc_input'].setEnabled(True)
                widgets['desc_input'].setReadOnly(self._path_assign_mode.get(map_type, False))
            if widgets.get('instant_checkbox'):
                widgets['instant_checkbox'].setChecked(False)
                widgets['instant_checkbox'].setEnabled(not self._path_assign_mode.get(map_type, False))
            self.cancel_draw_mode(map_type) 
            path_mode_widget = getattr(self, f"{map_type}_path_mode_widget", None)
            if path_mode_widget: path_mode_widget.setVisible(False)
            path_smoothness_label = getattr(self, f"{map_type}_path_smoothness_label", None)
            if path_smoothness_label: path_smoothness_label.setVisible(False)
            path_smoothness_slider = getattr(self, f"{map_type}_path_smoothness_slider", None)
            if path_smoothness_slider: path_smoothness_slider.setVisible(False)
        map_label = getattr(self, f"{map_type}_map_label", None)
        if map_label:
            cursor = Qt.PointingHandCursor if enabled else \
                     (Qt.ArrowCursor if map_label._zoom_level == 0 else Qt.OpenHandCursor)
            map_label.setCursor(cursor)
            map_label.update()

    def on_path_clicked_for_details(self, map_type, path_index):
        self._selected_path_index[map_type] = path_index
        widgets = self._path_details_widgets.get(map_type, {})
        assign_mode = self._path_assign_mode.get(map_type, False)
        name_input = widgets.get('name_input')
        desc_input = widgets.get('desc_input')
        instant_checkbox = widgets.get('instant_checkbox')
        if not assign_mode:
            if name_input:
                try: name_input.textChanged.disconnect()
                except TypeError: pass
            if desc_input:
                try: desc_input.textChanged.disconnect()
                except TypeError: pass
            if instant_checkbox:
                try: instant_checkbox.stateChanged.disconnect() 
                except TypeError: pass
        if map_type == 'world':
            lines = self._world_lines
            title_label = self.world_map_title_label
        else:
            lines = self._location_lines
            title_label = self.location_map_title_label
        if 0 <= path_index < len(lines):
            meta = lines[path_index][1] if isinstance(lines[path_index], tuple) and len(lines[path_index]) == 2 else {}
            name = meta.get('name', '') if isinstance(meta, dict) else ''
            desc = meta.get('desc', '') if isinstance(meta, dict) else ''
            instant = meta.get('instant', False) if isinstance(meta, dict) else False
            path_points = lines[path_index][0] if isinstance(lines[path_index], tuple) and len(lines[path_index]) == 2 else []
            if isinstance(meta, dict):
                path_display_name = name if name else "Unnamed Path"
                line_type_disp = meta.get('type', 'path').capitalize()
                start_idx, end_idx = meta.get('start', -1), meta.get('end', -1)
                start_desc = self._get_dot_description(start_idx, self._world_dots if map_type == 'world' else self._location_dots)
                end_desc = self._get_dot_description(end_idx, self._world_dots if map_type == 'world' else self._location_dots)
                path_len = sum(math.dist(path_points[i], path_points[i+1]) for i in range(len(path_points)-1)) if len(path_points) >=2 else 0
                title = f"{path_display_name} - {line_type_disp}: {start_desc} <--> {end_desc} (Len: {path_len:.1f})"
                if map_type == 'world':
                    def valid_idx(idx):
                        return isinstance(idx, int) and idx >= 0 and idx < len(self._world_dots) and len(self._world_dots[idx]) >= 6
                    start_reg = self._world_dots[start_idx][5] if valid_idx(start_idx) else None
                    end_reg = self._world_dots[end_idx][5] if valid_idx(end_idx) else None
                    if start_reg and end_reg and start_reg != end_reg:
                        title += f"\nCrosses: {self._format_region_name_for_display(start_reg)} to {self._format_region_name_for_display(end_reg)}"
                title_label.setText(title)
            if assign_mode:
                current_name = name_input.text() if name_input else ''
                current_desc = desc_input.toPlainText() if desc_input else ''
                current_instant = instant_checkbox.isChecked() if instant_checkbox else False
                if isinstance(meta, dict):
                    meta['name'] = current_name
                    meta['desc'] = current_desc
                    meta['instant'] = current_instant
                else:
                    meta = {
                        'name': current_name, 
                        'desc': current_desc, 
                        'instant': current_instant,
                        'type': lines[path_index][1].get('type') if isinstance(lines[path_index][1], dict) else 'medium'
                    }
                lines[path_index] = (lines[path_index][0], meta)
                self._save_path_details(map_type)
                if name_input: name_input.setReadOnly(True)
                if desc_input: desc_input.setReadOnly(True)
                if instant_checkbox: instant_checkbox.setEnabled(False)
            else:
                if name_input:
                    name_input.setText(name)
                    name_input._user_edited = False
                    name_input.setReadOnly(False)
                if desc_input:
                    desc_input.setPlainText(desc)
                    desc_input._user_edited = False
                    desc_input.setReadOnly(False)
                if instant_checkbox:
                    instant_checkbox.setChecked(instant)
                    instant_checkbox.setEnabled(True)
        else:
            if name_input:
                name_input.setText("")
                name_input._user_edited = False
            if desc_input:
                desc_input.setPlainText("")
                desc_input._user_edited = False
            if name_input: name_input.setReadOnly(self._path_assign_mode.get(map_type, False))
            if desc_input: desc_input.setReadOnly(self._path_assign_mode.get(map_type, False))
        if self._path_details_mode.get(map_type, False):
            if name_input: name_input.setEnabled(True)
            if desc_input: desc_input.setEnabled(True)
        else:
            if name_input: name_input.setEnabled(False)
            if desc_input: desc_input.setEnabled(False)
        label = getattr(self, f"{map_type}_map_label", None)
        if label:
            label.update()

    def on_path_hover_for_details(self, map_type, path_index):
        widgets = self._path_details_widgets.get(map_type, {})
        assign_mode = self._path_assign_mode.get(map_type, False)
        if assign_mode:
            return
        name_input = widgets.get('name_input')
        desc_input = widgets.get('desc_input')
        instant_checkbox = widgets.get('instant_checkbox')
        if not assign_mode:
            if name_input: name_input.setEnabled(True)
            if desc_input: desc_input.setEnabled(True)
            if instant_checkbox: instant_checkbox.setEnabled(True)
        user_editing = (name_input and getattr(name_input, '_user_edited', False)) or \
                       (desc_input and getattr(desc_input, '_user_edited', False))
        focused_widget = QApplication.focusWidget()
        if user_editing or (focused_widget == name_input or focused_widget == desc_input):
            return
        if map_type == 'world':
            lines = self._world_lines
        else:
            lines = self._location_lines
        if 0 <= path_index < len(lines):
            meta = lines[path_index][1] if isinstance(lines[path_index], tuple) and len(lines[path_index]) == 2 else {}
            name = meta.get('name', '') if isinstance(meta, dict) else ''
            desc = meta.get('desc', '') if isinstance(meta, dict) else ''
            instant = meta.get('instant', False) if isinstance(meta, dict) else False
            if name_input:
                name_input.setText(name)
            if desc_input:
                desc_input.setPlainText(desc)
            if instant_checkbox:
                instant_checkbox.setChecked(instant)
        else:
            if name_input:
                name_input.setText("")
            if desc_input:
                desc_input.setPlainText("")
            if instant_checkbox:
                instant_checkbox.setChecked(False)
        label = getattr(self, f"{map_type}_map_label", None)
        if label:
            label.update()

    def _save_path_details(self, map_type):
        path_index = self._selected_path_index.get(map_type)
        widgets = self._path_details_widgets.get(map_type, {})
        if path_index is None:
            return
        if not self._path_assign_mode.get(map_type, False):
            return
        if map_type == 'world':
            lines = self._world_lines
        else:
            lines = self._location_lines
        if 0 <= path_index < len(lines):
            meta = lines[path_index][1] if isinstance(lines[path_index], tuple) and len(lines[path_index]) == 2 else {}
            if not isinstance(meta, dict):
                meta = {}
            name = widgets['name_input'].text() if widgets.get('name_input') else ''
            desc = widgets['desc_input'].toPlainText() if widgets.get('desc_input') else ''
            instant = widgets['instant_checkbox'].isChecked() if widgets.get('instant_checkbox') else False
            meta['name'] = name
            meta['desc'] = desc
            meta['instant'] = instant
            lines[path_index] = (lines[path_index][0], meta)
            if map_type == 'world':
                self._save_world_map_data()
            else:
                self._save_location_map_data()

    def _set_path_assign_mode(self, map_type, enabled):
        self._path_assign_mode[map_type] = enabled
        widgets = self._path_details_widgets.get(map_type, {})
        if widgets.get('name_input'):
            widgets['name_input'].setReadOnly(enabled)
            if enabled:
                widgets['name_input'].setStyleSheet("background-color: #222; color: #888;")
            else:
                widgets['name_input'].setStyleSheet("")
        if widgets.get('desc_input'):
            widgets['desc_input'].setReadOnly(enabled)
            if enabled:
                widgets['desc_input'].setStyleSheet("background-color: #222; color: #888;")
            else:
                widgets['desc_input'].setStyleSheet("")
        if widgets.get('instant_checkbox'):
            widgets['instant_checkbox'].setEnabled(not enabled)
            if enabled:
                widgets['instant_checkbox'].setStyleSheet("color: #888;")
            else:
                widgets['instant_checkbox'].setStyleSheet("")
        for label_key in ['name_label', 'desc_label']:
            if widgets.get(label_key):
                if enabled:
                    widgets[label_key].setStyleSheet("color: #888; font-weight: bold;")
                else:
                    widgets[label_key].setStyleSheet("")
        label = getattr(self, f"{map_type}_map_label", None)
        if label:
            if hasattr(label, '_hovered_line_index'):
                label._hovered_line_index = -1
            label.setCursor(Qt.CrossCursor if enabled else Qt.PointingHandCursor)
            label.update()

    def _get_current_path_name(self, map_type):
        widgets = self._path_details_widgets.get(map_type, {})
        if widgets and widgets.get('name_input'):
            return widgets['name_input'].text().strip()
        return ""

    def _on_feature_paint_toggled(self, map_type, checked):
        world_region_edit_btn = getattr(self, 'world_region_edit_btn', None)
        features_toolbar = getattr(self, f"{map_type}_features_toolbar", None)
        feature_paint_btn = getattr(features_toolbar, 'feature_paint_btn', None) if features_toolbar else None
        if feature_paint_btn and feature_paint_btn.isChecked() != checked:
            print(f"Synchronizing {map_type} feature paint button to {checked}")
            feature_paint_btn.blockSignals(True)
            feature_paint_btn.setChecked(checked)  
            feature_paint_btn.blockSignals(False)
            feature_paint_btn.update()
        if checked:
            self.cancel_draw_mode(map_type)
            if map_type == 'world' and world_region_edit_btn and world_region_edit_btn.isChecked():
                world_region_edit_btn.blockSignals(True)
                world_region_edit_btn.setChecked(False)
                world_region_edit_btn.blockSignals(False)
                if hasattr(self, '_set_region_edit_mode'):
                    self._set_region_edit_mode('world', False)
            if feature_paint_btn and not feature_paint_btn.isChecked():
                feature_paint_btn.blockSignals(True)
                feature_paint_btn.setChecked(True)
                feature_paint_btn.blockSignals(False)
            if map_type == 'world':
                self._world_feature_paint = True
                self._world_draw_mode = 'feature_paint'
                if getattr(self, '_world_feature_sub_mode', 'select') not in ['paint', 'erase']:
                    self._world_feature_sub_mode = 'paint' 
            elif map_type == 'location':
                self._location_feature_paint = True
                self._location_draw_mode = 'feature_paint'
                if getattr(self, '_location_feature_sub_mode', 'select') not in ['paint', 'erase']:
                    self._location_feature_sub_mode = 'paint'
            self._setup_feature_submode_buttons(map_type)
            feature_submode_widget = getattr(self, f"{map_type}_feature_submode_widget", None)
            if feature_submode_widget: feature_submode_widget.setVisible(True)
            if features_toolbar:
                if hasattr(features_toolbar, 'feature_selector_label'): features_toolbar.feature_selector_label.setVisible(True)
                if hasattr(features_toolbar, 'feature_selector'): features_toolbar.feature_selector.setVisible(True)
            if map_type == 'world': self._on_world_feature_paint_submode() if self._world_feature_sub_mode == 'paint' else self._on_world_feature_select_submode()
            if map_type == 'location': self._on_location_feature_paint_submode() if self._location_feature_sub_mode == 'paint' else self._on_location_feature_select_submode()
            if map_type == 'world':
                if hasattr(self, 'world_region_submode_widget'): self.world_region_submode_widget.setVisible(False)
                if hasattr(self, 'world_region_selector_label'): self.world_region_selector_label.setVisible(False)
                if hasattr(self, 'world_region_selector'): self.world_region_selector.setVisible(False)
                if hasattr(self, 'world_brush_size_label'): self.world_brush_size_label.setVisible(False)
                if hasattr(self, 'world_brush_size_slider'): self.world_brush_size_slider.setVisible(False)
            if not hasattr(self, '_feature_masks'):
                self._feature_masks = {'world': {}, 'location': {}}
            elif map_type not in self._feature_masks:
                self._feature_masks[map_type] = {}
                
            if not hasattr(self, '_feature_border_cache'):
                self._feature_border_cache = {'world': {}, 'location': {}}
            elif map_type not in self._feature_border_cache:
                self._feature_border_cache[map_type] = {}
            features_data = self._world_features_data if map_type == 'world' else self._location_features_data
            if features_data and not self._feature_masks[map_type]:
                print(f"Initializing {map_type} feature masks in paint toggle")
                self._feature_mask_scale = getattr(self, '_feature_mask_scale', 0.5)
                self._init_feature_masks(map_type)
            if map_type in self._feature_masks:
                for feature_name in self._feature_masks[map_type].keys():
                    if feature_name:
                        self.update_feature_border_cache(map_type, feature_name)
        else:
            if feature_paint_btn and feature_paint_btn.isChecked():
                feature_paint_btn.blockSignals(True)
                feature_paint_btn.setChecked(False)
                feature_paint_btn.blockSignals(False)
            current_draw_mode_attr = f"_{map_type}_draw_mode"
            if getattr(self, current_draw_mode_attr, None) == 'feature_paint':
                setattr(self, current_draw_mode_attr, 'none')
            if map_type == 'world': self._world_feature_paint = False
            elif map_type == 'location': self._location_feature_paint = False
            feature_submode_widget = getattr(self, f"{map_type}_feature_submode_widget", None)
            if feature_submode_widget: feature_submode_widget.setVisible(False)
            if features_toolbar:
                if hasattr(features_toolbar, 'feature_selector_label'): features_toolbar.feature_selector_label.setVisible(False)
                if hasattr(features_toolbar, 'feature_selector'): features_toolbar.feature_selector.setVisible(False)
                if hasattr(features_toolbar, 'brush_size_label'): features_toolbar.brush_size_label.setVisible(False)
                if hasattr(features_toolbar, 'brush_size_slider'): features_toolbar.brush_size_slider.setVisible(False)
            map_label = getattr(self, f"{map_type}_map_label", None)
            if map_label:
                is_region_edit_active = map_type == 'world' and world_region_edit_btn and world_region_edit_btn.isChecked()
                if not is_region_edit_active:
                    cursor = Qt.ArrowCursor if getattr(map_label, '_zoom_level', 0) == 0 else Qt.OpenHandCursor
                    map_label.setCursor(cursor)
            current_feature_sub_mode_attr = f"_{map_type}_feature_sub_mode"
            setattr(self, current_feature_sub_mode_attr, 'select')

            select_submode_btn = getattr(self, f"{map_type}_feature_select_submode_btn", None)
            paint_submode_btn = getattr(self, f"{map_type}_feature_paint_submode_btn", None)

            if select_submode_btn:
                select_submode_btn.setChecked(True)
            if paint_submode_btn:
                paint_submode_btn.setChecked(False)

        map_label_to_update = getattr(self, f"{map_type}_map_label", None)
        if map_label_to_update:
            map_label_to_update.update()
        print(f"Feature paint mode for '{map_type}' set to {checked}. Draw mode: {getattr(self, f'_{map_type}_draw_mode', 'none')}")

    def _setup_feature_submode_buttons(self, map_type):
        from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
        if map_type == 'world':
            prefix = 'world_feature'
            toolbar = getattr(self, 'world_features_toolbar', None)
        elif map_type == 'location':
            prefix = 'location_feature'
            toolbar = getattr(self, 'location_features_toolbar', None)
        else:
            return
        if not toolbar:
            return
        submode_widget_name = f"{prefix}_submode_widget"
        if not hasattr(self, submode_widget_name):
            submode_widget = QWidget()
            submode_widget.setObjectName(f"{prefix.capitalize()}SubModeWidget")
            submode_layout = QHBoxLayout(submode_widget)
            submode_layout.setContentsMargins(0, 0, 0, 0)
            submode_layout.setSpacing(2)
            select_btn = QPushButton("Select")
            select_btn.setObjectName(f"{prefix}_select_submode_btn")
            select_btn.setCheckable(True)
            select_btn.setToolTip("Select features")
            paint_btn = QPushButton("Paint")
            paint_btn.setObjectName(f"{prefix}_paint_submode_btn")
            paint_btn.setCheckable(True)
            paint_btn.setToolTip("Paint features")
            submode_layout.addWidget(select_btn)
            submode_layout.addWidget(paint_btn)
            select_btn.setChecked(True)
            paint_btn.setChecked(False)
            if map_type == 'world':
                select_btn.clicked.connect(self._on_world_feature_select_submode)
                paint_btn.clicked.connect(self._on_world_feature_paint_submode)
                self._world_feature_sub_mode = 'select'
            elif map_type == 'location':
                select_btn.clicked.connect(self._on_location_feature_select_submode)
                paint_btn.clicked.connect(self._on_location_feature_paint_submode)
                self._location_feature_sub_mode = 'select'
            setattr(self, submode_widget_name, submode_widget)
            setattr(self, f"{prefix}_select_submode_btn", select_btn)
            setattr(self, f"{prefix}_paint_submode_btn", paint_btn)
            toolbar.layout().insertWidget(1, submode_widget)
        submode_widget = getattr(self, submode_widget_name)
        submode_widget.setVisible(True)

    def _on_world_feature_select_submode(self):
        self._world_feature_sub_mode = 'select'
        world_feature_select_btn = getattr(self, 'world_feature_select_submode_btn', None)
        world_feature_paint_btn = getattr(self, 'world_feature_paint_submode_btn', None)
        if world_feature_select_btn: world_feature_select_btn.setChecked(True)
        if world_feature_paint_btn: world_feature_paint_btn.setChecked(False)
        toolbar = getattr(self, 'world_features_toolbar', None)
        if toolbar:
            if hasattr(toolbar, 'brush_size_label'): toolbar.brush_size_label.setVisible(False)
            if hasattr(toolbar, 'brush_size_slider'): toolbar.brush_size_slider.setVisible(False)
            
        map_label = getattr(self, 'world_map_label', None)
        if map_label:
            map_label.setCursor(Qt.ArrowCursor)
            map_label.update()

    def _on_world_feature_paint_submode(self):
        self._world_feature_sub_mode = 'paint'
        world_feature_select_btn = getattr(self, 'world_feature_select_submode_btn', None)
        world_feature_paint_btn = getattr(self, 'world_feature_paint_submode_btn', None)
        if world_feature_select_btn: world_feature_select_btn.setChecked(False)
        if world_feature_paint_btn: world_feature_paint_btn.setChecked(True)
        toolbar = getattr(self, 'world_features_toolbar', None)
        if toolbar:
            if hasattr(toolbar, 'brush_size_label'): toolbar.brush_size_label.setVisible(True)
            if hasattr(toolbar, 'brush_size_slider'): toolbar.brush_size_slider.setVisible(True)
        map_label = getattr(self, 'world_map_label', None)
        if map_label:
            map_label.setCursor(Qt.CrossCursor)
            map_label.update()

    def _on_location_feature_select_submode(self):
        self._location_feature_sub_mode = 'select'
        loc_feature_select_btn = getattr(self, 'location_feature_select_submode_btn', None)
        loc_feature_paint_btn = getattr(self, 'location_feature_paint_submode_btn', None)
        if loc_feature_select_btn: loc_feature_select_btn.setChecked(True)
        if loc_feature_paint_btn: loc_feature_paint_btn.setChecked(False)
        toolbar = getattr(self, 'location_features_toolbar', None)
        if toolbar:
            if hasattr(toolbar, 'brush_size_label'): toolbar.brush_size_label.setVisible(False)
            if hasattr(toolbar, 'brush_size_slider'): toolbar.brush_size_slider.setVisible(False)
        map_label = getattr(self, 'location_map_label', None)
        if map_label:
            map_label.setCursor(Qt.ArrowCursor)
            map_label.update()

    def _on_location_feature_paint_submode(self):
        self._location_feature_sub_mode = 'paint'
        loc_feature_select_btn = getattr(self, 'location_feature_select_submode_btn', None)
        loc_feature_paint_btn = getattr(self, 'location_feature_paint_submode_btn', None)
        if loc_feature_select_btn: loc_feature_select_btn.setChecked(False)
        if loc_feature_paint_btn: loc_feature_paint_btn.setChecked(True)
        toolbar = getattr(self, 'location_features_toolbar', None)
        if toolbar:
            if hasattr(toolbar, 'brush_size_label'): toolbar.brush_size_label.setVisible(True)
            if hasattr(toolbar, 'brush_size_slider'): toolbar.brush_size_slider.setVisible(True)
        map_label = getattr(self, 'location_map_label', None)
        if map_label:
            map_label.setCursor(Qt.CrossCursor)
            map_label.update()

    def on_feature_paint_mode_changed(self, map_type, checked):
        if map_type == 'world':
            self._world_feature_paint = checked
            if checked:
                self._world_draw_mode = 'feature_paint'
            else:
                self._world_draw_mode = 'none'
        elif map_type == 'location':
            self._location_feature_paint = checked
            if checked:
                self._location_draw_mode = 'feature_paint'
            else:
                self._location_draw_mode = 'none'

    def on_feature_selected(self, map_type, feature_name):
        if map_type == 'world':
            self._current_world_feature = feature_name
            if feature_name and feature_name not in self._world_features_data:
                self._world_features_data[feature_name] = []
        elif map_type == 'location':
            self._current_location_feature = feature_name
            if feature_name and feature_name not in self._location_features_data:
                self._location_features_data[feature_name] = []

    def on_feature_brush_size_changed(self, map_type, value):
        if map_type == 'world':
            self._world_feature_brush_size = value
        elif map_type == 'location':
            self._location_feature_brush_size = value

    def paint_feature_at(self, map_type, image_coords_or_stroke):
        if isinstance(image_coords_or_stroke, list):
            stroke_points = image_coords_or_stroke
        else:
            stroke_points = [image_coords_or_stroke]
        if map_type == 'world':
            if not self._current_world_feature:
                print("[Error] No world feature selected for painting")
                return
            feature_name = self._current_world_feature
            if feature_name not in self._world_features_data:
                self._world_features_data[feature_name] = []
            brush_size = self._world_feature_brush_size
            for pt in stroke_points:
                self._world_features_data[feature_name].append((pt[0], pt[1], brush_size))
            self._rebuild_feature_mask_from_strokes('world', feature_name)
            if hasattr(self, 'world_map_label') and self.world_map_label:
                self.world_map_label.update()
            if not hasattr(self, '_feature_paint_save_timer') or self._feature_paint_save_timer is None:
                self._feature_paint_save_timer = QTimer()
                self._feature_paint_save_timer.setSingleShot(True)
                self._feature_paint_save_timer.timeout.connect(self._execute_deferred_feature_paint_save)
            self._pending_feature_paint_save_map_type = map_type
            if self._feature_paint_save_timer.isActive():
                self._feature_paint_save_timer.stop()
            self._feature_paint_save_timer.start(500)
                
        elif map_type == 'location':
            if not self._current_location_feature:
                print("[Error] No location feature selected for painting")
                return
            feature_name = self._current_location_feature
            if feature_name not in self._location_features_data:
                self._location_features_data[feature_name] = []
            brush_size = self._location_feature_brush_size
            for pt in stroke_points:
                self._location_features_data[feature_name].append((pt[0], pt[1], brush_size))
            self._rebuild_feature_mask_from_strokes('location', feature_name)
            if hasattr(self, 'location_map_label') and self.location_map_label:
                self.location_map_label.update()
            if not hasattr(self, '_feature_paint_save_timer') or self._feature_paint_save_timer is None:
                self._feature_paint_save_timer = QTimer()
                self._feature_paint_save_timer.setSingleShot(True)
                self._feature_paint_save_timer.timeout.connect(self._execute_deferred_feature_paint_save)
            
            self._pending_feature_paint_save_map_type = map_type
            if self._feature_paint_save_timer.isActive():
                self._feature_paint_save_timer.stop()
            self._feature_paint_save_timer.start(500)

    def erase_feature_at(self, map_type, image_coords, erase_radius=5):
        features_data = {}
        current_feature = None
        features_to_update = []
        if map_type == 'world':
            features_data = self._world_features_data
            current_feature = self._current_world_feature
            if self._world_feature_sub_mode == 'select' and current_feature:
                features_to_process = [current_feature]
            else:
                features_to_process = list(features_data.keys())
        elif map_type == 'location':
            features_data = self._location_features_data
            current_feature = self._current_location_feature
            if self._location_feature_sub_mode == 'select' and current_feature:
                features_to_process = [current_feature]
            else:
                features_to_process = list(features_data.keys())
        else:
            return
        for feature_name in features_to_process:
            if feature_name not in features_data:
                continue
            points = features_data[feature_name]
            removed_any = False
            new_points = []
            for point in points:
                x, y, radius = point
                dist = ((x - image_coords[0])**2 + (y - image_coords[1])**2)**0.5
                if dist > (radius / 2.0 + erase_radius / 2.0):
                    new_points.append(point)
                else:
                    removed_any = True
            if removed_any:
                features_data[feature_name] = new_points
                features_to_update.append(feature_name)
        for feature_name in features_to_update:
            self._rebuild_feature_mask_from_strokes(map_type, feature_name)

        if not hasattr(self, '_feature_erase_save_timer') or self._feature_erase_save_timer is None:
            self._feature_erase_save_timer = QTimer()
            self._feature_erase_save_timer.setSingleShot(True)
            self._feature_erase_save_timer.timeout.connect(self._execute_deferred_feature_erase_save)
        
        self._pending_feature_erase_save_map_type = map_type
        if self._feature_erase_save_timer.isActive():
            self._feature_erase_save_timer.stop()
        self._feature_erase_save_timer.start(1000)

        if map_type == 'world':
            if hasattr(self, 'world_map_label') and self.world_map_label:
                self.world_map_label.update()
        elif map_type == 'location':
            if hasattr(self, 'location_map_label') and self.location_map_label:
                self.location_map_label.update()

    def _execute_deferred_feature_erase_save(self):
        if self._pending_feature_erase_save_map_type == 'world':
            print("Executing deferred save for WORLD features after erase.")
            self._save_world_map_data()
        elif self._pending_feature_erase_save_map_type == 'location':
            print("Executing deferred save for LOCATION features after erase.")
            self._save_location_map_data()
        self._pending_feature_erase_save_map_type = None

    def _update_feature_submode_widget_visibility(self, map_type):
        if map_type == 'world':
            if hasattr(self, 'world_feature_submode_widget'):
                self.world_feature_submode_widget.setVisible(getattr(self, '_world_feature_paint', False))
        elif map_type == 'location':
            if hasattr(self, 'location_feature_submode_widget'):
                self.location_feature_submode_widget.setVisible(getattr(self, '_location_feature_paint', False))

    def _init_feature_masks(self, map_type):
        if map_type not in ['world', 'location']:
            return
        features_data = self._world_features_data if map_type == 'world' else self._location_features_data
        if not features_data:
            return
        if map_type == 'world' and hasattr(self, 'world_map_label') and self.world_map_label._crt_image:
            base_width = self.world_map_label._crt_image.width()
            base_height = self.world_map_label._crt_image.height()
        elif map_type == 'location' and hasattr(self, 'location_map_label') and self.location_map_label._crt_image:
            base_width = self.location_map_label._crt_image.width()
            base_height = self.location_map_label._crt_image.height()
        elif map_type == 'world' and hasattr(self, 'world_map_label'):
            base_width = self.world_map_label._virtual_width
            base_height = self.world_map_label._virtual_height
        elif map_type == 'location' and hasattr(self, 'location_map_label'):
            base_width = self.location_map_label._virtual_width
            base_height = self.location_map_label._virtual_height
        else:
            return
        if base_width <= 0 or base_height <= 0:
            return
        mask_scale = self._feature_mask_scale
        mask_width = max(1, int(base_width * mask_scale))
        mask_height = max(1, int(base_height * mask_scale))
        
        for feature_name, painted_strokes in features_data.items():
            mask = QImage(mask_width, mask_height, QImage.Format_ARGB32)
            mask.fill(QColor(0, 0, 0, 0))
            self._feature_masks[map_type][feature_name] = mask
            if painted_strokes:
                painter = QPainter(mask)
                painter.setRenderHint(QPainter.Antialiasing, False)
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                base_color_str = self.theme_colors.get("base_color", "#00A0A0")
                feature_color = QColor(base_color_str)
                feature_color.setAlpha(128)
                painter.setBrush(QBrush(feature_color))
                painter.setPen(Qt.NoPen)
                for x_img, y_img, brush_size_img in painted_strokes:
                    scaled_x = x_img * mask_scale
                    scaled_y = y_img * mask_scale
                    scaled_brush_size = brush_size_img * mask_scale
                    scaled_brush_size = max(1.0, scaled_brush_size)
                    painter.drawEllipse(QRectF(
                        scaled_x - scaled_brush_size / 2,
                        scaled_y - scaled_brush_size / 2,
                        scaled_brush_size, scaled_brush_size
                    ))
                painter.end()
        self._feature_border_cache[map_type] = {}

    def update_feature_border_cache(self, map_type, feature_name):
        if map_type not in ['world', 'location'] or feature_name not in self._feature_masks[map_type]:
            return
        mask = self._feature_masks[map_type].get(feature_name)
        if not mask or mask.isNull():
            return
        edge_mask = mask.copy()
        mask_w, mask_h = mask.width(), mask.height()
        edge_painter = QPainter(edge_mask)
        edge_painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        edge_painter.fillRect(0, 0, mask_w, mask_h, QColor(0, 0, 0, 0))
        edge_painter.end()
        mask_bits = mask.bits()
        mask_bits.setsize(mask.byteCount())
        try:
            import numpy as np
            import cv2
            arr = np.frombuffer(mask_bits, dtype=np.uint8).reshape((mask_h, mask_w, 4))
            alpha = arr[..., 3]
            _, binary = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour_points = []
            for contour in contours:
                if len(contour) < 4:
                    continue
                points = []
                for point in contour:
                    x, y = point[0][0], point[0][1]
                    points.append((float(x), float(y)))
                if points:
                    contour_points.append(points)
            self._feature_border_cache[map_type][feature_name] = contour_points
        except (ImportError, Exception) as e:
            print(f"Error while calculating feature border: {e}")
            self._feature_border_cache[map_type][feature_name] = []

    def _rebuild_feature_mask_from_strokes(self, map_type, feature_name):
        if map_type not in ['world', 'location']:
            return
        features_data = self._world_features_data if map_type == 'world' else self._location_features_data
        if feature_name not in features_data:
            return
        painted_strokes = features_data[feature_name]
        if map_type == 'world' and hasattr(self, 'world_map_label') and self.world_map_label._crt_image:
            base_width = self.world_map_label._crt_image.width()
            base_height = self.world_map_label._crt_image.height()
        elif map_type == 'location' and hasattr(self, 'location_map_label') and self.location_map_label._crt_image:
            base_width = self.location_map_label._crt_image.width()
            base_height = self.location_map_label._crt_image.height()
        elif map_type == 'world' and hasattr(self, 'world_map_label'):
            base_width = self.world_map_label._virtual_width
            base_height = self.world_map_label._virtual_height
        elif map_type == 'location' and hasattr(self, 'location_map_label'):
            base_width = self.location_map_label._virtual_width
            base_height = self.location_map_label._virtual_height
        else:
            return
        if base_width <= 0 or base_height <= 0:
            return
        mask_scale = self._feature_mask_scale
        mask_width = max(1, int(base_width * mask_scale))
        mask_height = max(1, int(base_height * mask_scale))
        if feature_name not in self._feature_masks[map_type]:
            self._feature_masks[map_type][feature_name] = QImage(mask_width, mask_height, QImage.Format_ARGB32)
            self._feature_masks[map_type][feature_name].fill(QColor(0, 0, 0, 0))
        mask = self._feature_masks[map_type][feature_name]
        if mask.width() != mask_width or mask.height() != mask_height:
            mask = QImage(mask_width, mask_height, QImage.Format_ARGB32)
            mask.fill(QColor(0, 0, 0, 0))
            self._feature_masks[map_type][feature_name] = mask
        mask.fill(QColor(0, 0, 0, 0))
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        base_color_str = self.theme_colors.get("base_color", "#00A0A0")
        feature_color = QColor(base_color_str)
        feature_color.setAlpha(128)
        painter.setBrush(QBrush(feature_color))
        painter.setPen(Qt.NoPen)
        for x_img, y_img, brush_size_img in painted_strokes:
            scaled_x = x_img * mask_scale
            scaled_y = y_img * mask_scale
            scaled_brush_size = brush_size_img * mask_scale
            scaled_brush_size = max(1.0, scaled_brush_size)
            painter.drawEllipse(QRectF(
                scaled_x - scaled_brush_size / 2,
                scaled_y - scaled_brush_size / 2,
                scaled_brush_size, scaled_brush_size
            ))
        painter.end()
        self._feature_border_cache[map_type].pop(feature_name, None)

    def _handle_setting_added_or_removed(self):
        if self.current_world_name and hasattr(self, 'world_features_toolbar') and self.world_features_toolbar:
            world_features_names = []
            if self.workflow_data_dir:
                world_json_path = os.path.join(
                    self.workflow_data_dir, 
                    'resources', 
                    'data files', 
                    'settings', 
                    sanitize_path_name(self.current_world_name), 
                    f"{sanitize_path_name(self.current_world_name)}_world.json"
                )
                if not os.path.isfile(world_json_path):
                    world_json_path = os.path.join(
                        self.workflow_data_dir, 
                        'resources', 
                        'data files', 
                        'settings',
                        f"{sanitize_path_name(self.current_world_name)}_world.json"
                    )
                if os.path.isfile(world_json_path):
                    try:
                        world_data = self._load_json(world_json_path)
                        if isinstance(world_data, dict) and isinstance(world_data.get('features'), list):
                            for feature_item in world_data['features']:
                                if isinstance(feature_item, dict) and isinstance(feature_item.get('name'), str):
                                    world_features_names.append(feature_item['name'])
                            print(f"Loaded {len(world_features_names)} feature names for world '{self.current_world_name}'.")
                    except Exception as e:
                        print(f"Error loading features from {world_json_path}: {e}")
            self.world_features_toolbar.populate_features(world_features_names)
        if self.current_world_name and self.current_location_name and hasattr(self, 'location_features_toolbar') and self.location_features_toolbar:
            location_features_names = []
            if self.workflow_data_dir:
                location_dir = self._find_location_path(self.current_world_name, self.current_location_name)
                if location_dir and os.path.isdir(location_dir):
                    location_json_filename = f"{sanitize_path_name(self.current_location_name)}_location.json"
                    location_main_json_path = os.path.join(location_dir, location_json_filename)
                    if os.path.isfile(location_main_json_path):
                        try:
                            location_main_data = self._load_json(location_main_json_path)
                            if isinstance(location_main_data, dict) and isinstance(location_main_data.get('features'), list):
                                for feature_item in location_main_data['features']:
                                    if isinstance(feature_item, dict) and isinstance(feature_item.get('name'), str):
                                        location_features_names.append(feature_item['name'])
                                print(f"Loaded {len(location_features_names)} feature names for location '{self.current_location_name}'.")
                        except Exception as e:
                            print(f"Error loading features from {location_main_json_path}: {e}")
                self.location_features_toolbar.populate_features(location_features_names)
        self._update_world_location_dropdown()
        self._update_world_setting_dropdown()
        self._update_location_setting_dropdown()

    def finalize_region_paint_stroke(self, map_type, region_name, stroke_points):
        if map_type != 'world':
            print(f"[WARN] finalize_region_paint_stroke called for non-world map_type: {map_type}")
            return
        if not region_name:
            print("[WARN] finalize_region_paint_stroke: No region_name provided.")
            return
        if not stroke_points:
            print("[WARN] finalize_region_paint_stroke: No stroke_points provided.")
            return
        if not hasattr(self, '_world_regions'):
            self._world_regions = {}
        if region_name not in self._world_regions:
            self._world_regions[region_name] = []
        brush_size = getattr(self, '_region_brush_size', 10)
        for pt in stroke_points:
            if isinstance(pt, (list, tuple)) and len(pt) == 3:
                self._world_regions[region_name].append(tuple(pt))
            elif isinstance(pt, (list, tuple)) and len(pt) == 2:
                self._world_regions[region_name].append((pt[0], pt[1], brush_size))
            else:
                print(f"[ERROR] Invalid stroke point: {pt}")
        try:
            self._rebuild_region_mask_from_strokes(region_name)
            if hasattr(self, 'world_map_label') and self.world_map_label:
                self.world_map_label.update()
            if hasattr(self, '_region_border_cache') and len(self._world_regions[region_name]) > 3:
                QTimer.singleShot(100, lambda: update_region_border_cache(self, region_name))
            if not hasattr(self, '_save_timer'):
                self._save_timer = QTimer()
                self._save_timer.setSingleShot(True)
                self._save_timer.timeout.connect(self._save_world_map_data)
            if self._save_timer.isActive():
                self._save_timer.stop()
            self._save_timer.start(2000)
            if len(stroke_points) > 20:
                QTimer.singleShot(500, self._save_world_map_data)
            if self.workflow_data_dir and self.current_world_name:
                world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
                region_resources_dir = os.path.join(world_dir, "resources", "regions")
                os.makedirs(region_resources_dir, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Error finalizing stroke: {str(e)}")
            import traceback
            traceback.print_exc()

    def paint_region_stroke(self, region_name, stroke_points, brush_size, erase_mode=False):
        if not hasattr(self, '_region_masks'):
            self._region_masks = {}
        if not hasattr(self, 'world_map_label') or not self.world_map_label:
            print("[WARN] paint_region_stroke: No world_map_label available.")
            return
        if not region_name:
            print("[WARN] paint_region_stroke: Empty region_name provided")
            return
        if not stroke_points:
            print("[WARN] paint_region_stroke: No stroke points provided")
            return
            
        if region_name not in self._region_masks:
            if hasattr(self.world_map_label, '_crt_image') and self.world_map_label._crt_image:
                width = self.world_map_label._crt_image.width()
                height = self.world_map_label._crt_image.height()
            else:
                width = getattr(self.world_map_label, '_virtual_width', 1000)
                height = getattr(self.world_map_label, '_virtual_height', 1000)
            mask = QImage(width, height, QImage.Format_ARGB32)
            mask.fill(QColor(0, 0, 0, 0))
            self._region_masks[region_name] = mask
        mask = self._region_masks[region_name]
        name_hash = sum(ord(c) for c in region_name) if region_name else 0
        hue = (name_hash % 360) / 360.0
        if erase_mode:
            region_color = QColor(0, 0, 0, 0)
            composition_mode = QPainter.CompositionMode_Clear
            if hasattr(self, '_world_regions') and region_name in self._world_regions:
                mask_scale = getattr(self, '_region_mask_scale', 1.0)
                erase_radius = brush_size / 2
                erase_radius_sq = erase_radius ** 2
                filtered_points = []
                for region_point in self._world_regions[region_name]:
                    region_x, region_y = region_point[0], region_point[1]
                    should_keep = True
                    for stroke_point in stroke_points:
                        stroke_x, stroke_y = stroke_point[0], stroke_point[1]
                        dist_sq = (region_x - stroke_x) ** 2 + (region_y - stroke_y) ** 2
                        if dist_sq <= erase_radius_sq * 4:
                            should_keep = False
                            break
                    if should_keep:
                        filtered_points.append(region_point)
                if len(filtered_points) != len(self._world_regions[region_name]):
                    points_removed = len(self._world_regions[region_name]) - len(filtered_points)
                    self._world_regions[region_name] = list(filtered_points)
                    if len(filtered_points) == 0:
                        print(f"Region '{region_name}' was completely erased, keeping empty region definition")
                        self._world_regions[region_name] = []
                    if points_removed > 0:
                        import functools
                        rebuild_func = functools.partial(self._rebuild_region_mask_from_strokes, region_name)
                        QTimer.singleShot(100, rebuild_func)
        else:
            region_color = QColor.fromHsvF(hue, 0.7, 0.8, 0.5)
            composition_mode = QPainter.CompositionMode_Source
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setCompositionMode(composition_mode)
        if len(stroke_points) > 1:
            path = QPainterPath()
            path.moveTo(stroke_points[0][0], stroke_points[0][1])
            for i in range(1, len(stroke_points)):
                path.lineTo(stroke_points[i][0], stroke_points[i][1])
            pen = QPen(region_color, brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
        painter.setBrush(QBrush(region_color))
        painter.setPen(Qt.NoPen)
        for pt in stroke_points:
            x, y = pt
            painter.drawEllipse(QPointF(x, y), brush_size/2, brush_size/2)
        painter.end()
        if not erase_mode and hasattr(self, '_region_border_cache'):
            from region_toolbar import update_region_border_cache
            import functools
            update_func = functools.partial(update_region_border_cache, self, region_name)
            QTimer.singleShot(100, update_func)
        if hasattr(self, 'world_map_label'):
            self.world_map_label.update()
        if erase_mode:
            if hasattr(self, '_region_fill_cache') and region_name in self._region_fill_cache:
                self._region_fill_cache.pop(region_name, None)
            if not hasattr(self, '_save_timer'):
                self._save_timer = QTimer()
                self._save_timer.setSingleShot(True)
                self._save_timer.timeout.connect(self._save_world_map_data)
            if hasattr(self, '_save_timer'):
                if self._save_timer.isActive():
                    self._save_timer.stop()
                self._save_timer.start(1000)

    def toggle_region_fills(self, show_fills=None):
        if hasattr(self, 'world_map_label') and self.world_map_label:
            if show_fills is None:
                self.world_map_label._show_region_fills = not getattr(self.world_map_label, '_show_region_fills', True)
            else:
                self.world_map_label._show_region_fills = bool(show_fills)
            print(f"Region fills {'shown' if self.world_map_label._show_region_fills else 'hidden'}")
            self.world_map_label.update()
        else:
            print("[WARN] Cannot toggle region fills: world_map_label not found.")

    def _execute_deferred_feature_erase_save(self):
        if self._pending_feature_erase_save_map_type == 'world':
            print("Executing deferred save for WORLD features after erase.")
            self._save_world_map_data()
        elif self._pending_feature_erase_save_map_type == 'location':
            print("Executing deferred save for LOCATION features after erase.")
            self._save_location_map_data()
        self._pending_feature_erase_save_map_type = None

    def _update_feature_submode_widget_visibility(self, map_type):
        if map_type == 'world':
            if hasattr(self, 'world_feature_submode_widget'):
                self.world_feature_submode_widget.setVisible(getattr(self, '_world_feature_paint', False))
        elif map_type == 'location':
            if hasattr(self, 'location_feature_submode_widget'):
                self.location_feature_submode_widget.setVisible(getattr(self, '_location_feature_paint', False))

    def _find_location_folder_by_display_name(self, region_display_name_filter, target_location_display_name):
        if not hasattr(self, 'current_world_folder_name') or not self.current_world_folder_name:
            print("[ERROR] WorldEditorWidget._find_location_folder_by_display_name: current_world_folder_name is not set.")
            return None
        if not hasattr(self, 'workflow_data_dir') or not self.workflow_data_dir:
            print("[ERROR] WorldEditorWidget._find_location_folder_by_display_name: workflow_data_dir is not set.")
            return None

        world_settings_path = os.path.join(self.workflow_data_dir, "resources", "data files", "settings", self.current_world_folder_name)
        if not os.path.isdir(world_settings_path):
            print(f"[ERROR] WorldEditorWidget._find_location_folder_by_display_name: World directory not found: {world_settings_path}")
            return None
        sanitized_target = target_location_display_name.replace(' ', '_').lower()
        for region_folder_name in os.listdir(world_settings_path):
            region_path = os.path.join(world_settings_path, region_folder_name)
            if not os.path.isdir(region_path):
                continue
            location_folder_path = os.path.join(region_path, sanitized_target)
            if os.path.isdir(location_folder_path):
                return os.path.join(region_folder_name, sanitized_target)
        for region_folder_name in os.listdir(world_settings_path):
            region_path = os.path.join(world_settings_path, region_folder_name)
            if not os.path.isdir(region_path):
                continue
            for location_folder_name in os.listdir(region_path):
                location_folder_path = os.path.join(region_path, location_folder_name)
                if not os.path.isdir(location_folder_path):
                    continue
                current_location_display_name = location_folder_name.replace('_', ' ').title()
                location_json_filename = f"{location_folder_name}_location.json"
                location_json_path = os.path.join(location_folder_path, location_json_filename)
                if os.path.exists(location_json_path):
                    try:
                        with open(location_json_path, 'r', encoding='utf-8') as f:
                            location_data = json.load(f)
                        current_location_display_name = location_data.get("display_name", current_location_display_name)
                    except Exception as e:
                        print(f"[WARN] WorldEditorWidget: Error reading or parsing location meta file {location_json_path}: {e}")
                if current_location_display_name.lower() == target_location_display_name.lower():
                    return os.path.join(region_folder_name, location_folder_name)
        default_region = "default_region"
        for region_folder_name in os.listdir(world_settings_path):
            region_path = os.path.join(world_settings_path, region_folder_name)
            if os.path.isdir(region_path):
                default_region = region_folder_name
                break
        new_location_path = os.path.join(world_settings_path, default_region, sanitized_target)
        os.makedirs(new_location_path, exist_ok=True)
        return os.path.join(default_region, sanitized_target)

    def _save_location_map_data(self):
        if not hasattr(self, 'current_world_folder_name') or not self.current_world_folder_name:
            print("[ERROR] _save_location_map_data: current_world_folder_name is not set.")
            return
        if not hasattr(self, 'workflow_data_dir') or not self.workflow_data_dir:
            print("[ERROR] _save_location_map_data: workflow_data_dir is not set.")
            return
        if not self.current_location_name:
            print("[ERROR] _save_location_map_data: current_location_name is not set.")
            return
        world_dir_for_settings = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_folder_name)
        relative_path_to_location_folder = self._find_location_folder_by_display_name(
            None,
            self.current_location_name
        )
        if not relative_path_to_location_folder:
            print(f"[ERROR] _save_location_map_data: Could not find folder for location '{self.current_location_name}' in world '{self.current_world_folder_name}'.")
            return
        location_dir = os.path.join(world_dir_for_settings, relative_path_to_location_folder)
        if not os.path.isdir(location_dir):
             os.makedirs(location_dir, exist_ok=True)
        dots_data = []
        for dot_tuple in self._location_dots:
            if len(dot_tuple) >= 6:
                x, y, pulse_offset, dot_type, linked_name, region_name_val = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, linked_name, region_name_val])
            elif len(dot_tuple) == 5:
                x, y, pulse_offset, dot_type, linked_name = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, linked_name, None])
            elif len(dot_tuple) == 4:
                x, y, pulse_offset, dot_type = dot_tuple
                dots_data.append([x, y, pulse_offset, dot_type, None, None])
        lines_data = []
        for points, meta in self._location_lines:
            points_list = [list(p) if isinstance(p, tuple) else p for p in points]
            lines_data.append({
                "points": points_list,
                "meta": meta
            })
        if hasattr(self, '_feature_masks') and 'location' in self._feature_masks:
            feature_masks = self._feature_masks['location']
            for feature_name, mask_image in feature_masks.items():
                if mask_image and not mask_image.isNull():
                    feature_resources_dir = os.path.join(location_dir, "resources", "features")
                    os.makedirs(feature_resources_dir, exist_ok=True)
                    mask_filename = f"{feature_name.replace(' ', '_').lower()}_feature_mask.png"
                    mask_path = os.path.join(feature_resources_dir, mask_filename)
        scale_data = self._get_location_scale_settings()
        json_data = {
            "dots": dots_data,
            "lines": lines_data,
            "features_data": self._location_features_data if hasattr(self, '_location_features_data') else {},
            "scale_settings": scale_data
        }
        map_data_file = os.path.join(location_dir, "location_map_data.json")
        try:
            with open(map_data_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2)
            print(f"Saved location map data to {map_data_file}")
        except Exception as e:
            print(f"Error saving location map data: {e}")

    def _detect_region_name(self):
        if not self.workflow_data_dir or not self.current_world_name or not self.current_location_name:
            print("Cannot detect region name: missing workflow_data_dir, world name, or location name")
            return
        search_dirs = [
            os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name),
            os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        ]
        for world_dir in search_dirs:
            if not os.path.isdir(world_dir):
                continue
            direct_location_path = os.path.join(world_dir, self.current_location_name)
            if os.path.isdir(direct_location_path):
                loc_json_filename = f"{sanitize_path_name(self.current_location_name)}_location.json"
                location_json = os.path.join(direct_location_path, loc_json_filename)
                if os.path.isfile(location_json):
                    print(f"Found location '{self.current_location_name}' directly in world '{self.current_world_name}' (not in a region)")
                    self._world_region_name = None
                    return
        for world_dir in search_dirs:
            if not os.path.isdir(world_dir):
                continue
            for region_name in os.listdir(world_dir):
                region_path = os.path.join(world_dir, region_name)
                if not os.path.isdir(region_path):
                    continue
                region_json = os.path.join(region_path, f"{sanitize_path_name(region_name)}_region.json")
                if not os.path.isfile(region_json):
                    continue
                location_path = os.path.join(region_path, self.current_location_name)
                if os.path.isdir(location_path):
                    self._world_region_name = region_name
                    print(f"Found location '{self.current_location_name}' in region '{region_name}'")
                    return

    def _execute_deferred_feature_paint_save(self):
        if self._pending_feature_paint_save_map_type == 'world':
            print("Executing deferred save for WORLD features after painting.")
            self._save_world_map_data()
        elif self._pending_feature_paint_save_map_type == 'location':
            print("Executing deferred save for LOCATION features after painting.")
            self._save_location_map_data()
        self._pending_feature_paint_save_map_type = None

    def update_dots_for_renamed_setting(self, old_setting_name, new_setting_name):
        if not old_setting_name or not new_setting_name or old_setting_name == new_setting_name:
            return
        world_dots_updated = 0
        for i, dot in enumerate(self._world_dots):
            if len(dot) >= 5 and dot[3] == 'small' and dot[4] == old_setting_name:
                updated_dot = list(dot)
                updated_dot[4] = new_setting_name
                self._world_dots[i] = tuple(updated_dot)
                world_dots_updated += 1
        location_dots_updated = 0
        for i, dot in enumerate(self._location_dots):
            if len(dot) >= 5 and dot[3] == 'small' and dot[4] == old_setting_name:
                updated_dot = list(dot)
                updated_dot[4] = new_setting_name
                self._location_dots[i] = tuple(updated_dot)
                location_dots_updated += 1
        if world_dots_updated > 0:
            print(f"[INFO] Updated {world_dots_updated} world map dots")
            self._save_world_map_data()
            if hasattr(self, 'world_map_label') and self.world_map_label:
                self.world_map_label.update()
        if location_dots_updated > 0:
            self._save_location_map_data()
            if hasattr(self, 'location_map_label') and self.location_map_label:
                self.location_map_label.update()
        self.force_populate_dropdowns()

    def update_for_renamed_region(self, old_region_name, new_region_name):
        if hasattr(self, '_region_masks'):
            if old_region_name in self._region_masks:
                self._region_masks[new_region_name] = self._region_masks.pop(old_region_name)
            if old_region_name in self._region_masks:
                del self._region_masks[old_region_name]
        if hasattr(self, '_region_border_cache'):
            if old_region_name in self._region_border_cache:
                self._region_border_cache[new_region_name] = self._region_border_cache.pop(old_region_name)
            if old_region_name in self._region_border_cache:
                del self._region_border_cache[old_region_name]
        if hasattr(self, '_world_regions'):
            if old_region_name in self._world_regions:
                self._world_regions[new_region_name] = self._world_regions.pop(old_region_name)
            if old_region_name in self._world_regions:
                del self._world_regions[old_region_name]
        if hasattr(self, '_shared_region_boundaries'):
            if old_region_name in self._shared_region_boundaries:
                self._shared_region_boundaries[new_region_name] = self._shared_region_boundaries.pop(old_region_name)
            if old_region_name in self._shared_region_boundaries:
                del self._shared_region_boundaries[old_region_name]
            for region, boundaries in self._shared_region_boundaries.items():
                if old_region_name in boundaries:
                    boundaries.remove(old_region_name)
                    boundaries.add(new_region_name)
        if hasattr(self, 'world_map_label') and self.world_map_label:
            self.world_map_label.update()
        if hasattr(self, 'world_region_selector') and self.world_region_selector:
            current_text = self.world_region_selector.currentText()
            if current_text == old_region_name:
                for i in range(self.world_region_selector.count()):
                    if self.world_region_selector.itemText(i) == new_region_name:
                        self.world_region_selector.setCurrentIndex(i)
                        print(f"Updated region selector to show '{new_region_name}'")
                        break
        if hasattr(self, '_init_region_masks'):
            from functools import partial
            QTimer.singleShot(500, partial(self._init_region_masks))
    
    def _get_world_scale_settings(self):
        scale_data = {}
        if hasattr(self, 'world_scale_number_input') and self.world_scale_number_input:
            try:
                scale_data['distance'] = float(self.world_scale_number_input.text() or '1.0')
            except ValueError:
                scale_data['distance'] = 1.0
        else:
            scale_data['distance'] = 1.0
        
        if hasattr(self, 'world_scale_time_input') and self.world_scale_time_input:
            try:
                scale_data['time'] = float(self.world_scale_time_input.text() or '1.0')
            except ValueError:
                scale_data['time'] = 1.0
        else:
            scale_data['time'] = 1.0
        if hasattr(self, 'world_scale_unit_dropdown') and self.world_scale_unit_dropdown:
            scale_data['unit'] = self.world_scale_unit_dropdown.currentText()
        else:
            scale_data['unit'] = 'minutes'
        return scale_data
    
    def _load_world_scale_settings(self, scale_data):
        if hasattr(self, 'world_scale_number_input') and self.world_scale_number_input:
            distance = scale_data.get('distance', 1.0)
            self.world_scale_number_input.setText(str(distance))
        if hasattr(self, 'world_scale_time_input') and self.world_scale_time_input:
            time = scale_data.get('time', 1.0)
            self.world_scale_time_input.setText(str(time))
        if hasattr(self, 'world_scale_unit_dropdown') and self.world_scale_unit_dropdown:
            unit = scale_data.get('unit', 'minutes')
            index = self.world_scale_unit_dropdown.findText(unit)
            if index >= 0:
                self.world_scale_unit_dropdown.setCurrentIndex(index)
    
    def _get_location_scale_settings(self):
        scale_data = {}
        if hasattr(self, 'location_scale_number_input') and self.location_scale_number_input:
            try:
                scale_data['distance'] = float(self.location_scale_number_input.text() or '1.0')
            except ValueError:
                scale_data['distance'] = 1.0
        else:
            scale_data['distance'] = 1.0
        if hasattr(self, 'location_scale_time_input') and self.location_scale_time_input:
            try:
                scale_data['time'] = float(self.location_scale_time_input.text() or '1.0')
            except ValueError:
                scale_data['time'] = 1.0
        else:
            scale_data['time'] = 1.0
        if hasattr(self, 'location_scale_unit_dropdown') and self.location_scale_unit_dropdown:
            scale_data['unit'] = self.location_scale_unit_dropdown.currentText()
        else:
            scale_data['unit'] = 'minutes'
        return scale_data
    
    def _load_location_scale_settings(self, scale_data):
        if hasattr(self, 'location_scale_number_input') and self.location_scale_number_input:
            distance = scale_data.get('distance', 1.0)
            self.location_scale_number_input.setText(str(distance))
        
        if hasattr(self, 'location_scale_time_input') and self.location_scale_time_input:
            time = scale_data.get('time', 1.0)
            self.location_scale_time_input.setText(str(time))
        
        if hasattr(self, 'location_scale_unit_dropdown') and self.location_scale_unit_dropdown:
            unit = scale_data.get('unit', 'minutes')
            index = self.location_scale_unit_dropdown.findText(unit)
            if index >= 0:
                self.location_scale_unit_dropdown.setCurrentIndex(index)
    
    def _on_world_scale_changed(self):
        self._save_world_map_data()
    
    def _on_location_scale_changed(self):
        self._save_location_map_data()
    
    def calculate_travel_time(self, path_length, map_type='world'):
        if map_type == 'world':
            scale_data = self._get_world_scale_settings()
        else:
            scale_data = self._get_location_scale_settings()
        distance_per_unit = scale_data.get('distance', 1.0)
        time_per_unit = scale_data.get('time', 1.0)
        unit = scale_data.get('unit', 'minutes')
        if distance_per_unit <= 0:
            return 0
        time_in_units = (path_length / distance_per_unit) * time_per_unit
        if unit == 'minutes':
            return time_in_units
        elif unit == 'hours':
            return time_in_units * 60
        elif unit == 'days':
            return time_in_units * 60 * 24
        else:
            return time_in_units
