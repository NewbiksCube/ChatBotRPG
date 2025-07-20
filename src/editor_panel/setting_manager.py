from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QAbstractItemView, QLineEdit, QTextEdit, QListWidgetItem, QPushButton, QMessageBox, QInputDialog, QSizePolicy, QTabWidget, QFileDialog, QGroupBox, QScrollArea, QCheckBox, QComboBox, QCompleter, QDialog, QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt, QTimer
import os
import json
import shutil
import re
import datetime
from PyQt5.QtCore import QTimer
from editor_panel.world_editor.world_editor import WorldEditorWidget
import fnmatch

def sanitize_path_name(name):
    if not name:
        return 'untitled'
    stripped = name.strip()
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', stripped)
    sanitized = sanitized.replace(' ', '_')
    if not sanitized:
        sanitized = 'untitled'
    return sanitized

class SettingManagerWidget(QWidget):
    def __init__(self, workflow_data_dir, theme_colors, parent=None):
        super().__init__(parent)
        self.workflow_data_dir = workflow_data_dir
        self.theme_colors = theme_colors
        self._selected_world_orig = None
        self._selected_region_orig = None
        self._selected_location_orig = None
        self._selected_setting_orig = None
        self._selected_level = None
        self._editing_world_orig = None
        self._editing_region_orig = None
        self._editing_location_orig = None
        self._editing_setting_orig = None
        self._editing_level = None
        self._original_edit_level = None
        self._current_setting_file_path_absolute = None
        self._current_setting_is_game_version = False
        self._connection_desc_edits = {}
        self._is_navigating = False
        self._current_setting_item = None
        self.current_world_features = []
        self.current_location_features = []
        self.current_world_path_data_cache = {}
        self.current_location_path_data_cache = {}
        self._description_save_timer = QTimer()
        self._description_save_timer.setSingleShot(True)
        self._description_save_timer.timeout.connect(self._save_current_details)
        self._description_save_timer.setInterval(1000)
        self.world_editor_tab = None
        self._init_ui()
        self.update_theme(theme_colors)
        self._ensure_default_setting_structure()
        self.populate_worlds()
        self._is_navigating = False

    def _init_ui(self):
        self.setStyleSheet(f"background-color: {self.theme_colors.get('bg_color', '#2B2B2B')};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # Create scroll area for the tab widget
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create a container widget for the scroll area
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet(f"background-color: {self.theme_colors.get('bg_color', '#2B2B2B')};")
        self.scroll_content_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_content_layout.setSpacing(10)
        
        # Create button layout for mode selection
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        self.button_layout.setContentsMargins(0, 0, 0, 10)
        self.button_layout.setAlignment(Qt.AlignCenter)
        
        # Create mode buttons
        self.setting_details_btn = QPushButton("Setting Details")
        self.setting_details_btn.setCheckable(True)
        self.setting_details_btn.setChecked(True)
        self.setting_details_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme_colors.get('base_color', '#00ff66')};
                color: #000000;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {self.theme_colors.get('base_color', '#00ff66')};
                color: #000000;
            }}
            QPushButton:!checked {{
                background-color: transparent;
                color: {self.theme_colors.get('base_color', '#00ff66')};
                border: 1px solid {self.theme_colors.get('base_color', '#00ff66')};
            }}
        """)
        
        self.world_editor_btn = QPushButton("World Editor")
        self.world_editor_btn.setCheckable(True)
        self.world_editor_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme_colors.get('base_color', '#00ff66')};
                border: 1px solid {self.theme_colors.get('base_color', '#00ff66')};
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:checked {{
                background-color: {self.theme_colors.get('base_color', '#00ff66')};
                color: #000000;
            }}
            QPushButton:!checked {{
                background-color: transparent;
                color: {self.theme_colors.get('base_color', '#00ff66')};
                border: 1px solid {self.theme_colors.get('base_color', '#00ff66')};
            }}
        """)
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.setting_details_btn)
        self.button_layout.addWidget(self.world_editor_btn)
        self.button_layout.addStretch()
        
        # Connect button signals
        self.setting_details_btn.clicked.connect(self._on_setting_details_clicked)
        self.world_editor_btn.clicked.connect(self._on_world_editor_clicked)
        
        self.scroll_content_layout.addLayout(self.button_layout)
        
        # Create stacked widget for content
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet(f"background-color: {self.theme_colors.get('bg_color', '#2B2B2B')};")
        self.scroll_content_layout.addWidget(self.content_stack)
        
        # Set the scroll content as the scroll area widget
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        self.setting_details_tab = QWidget()
        setting_details_layout = QVBoxLayout(self.setting_details_tab)
        setting_details_layout.setContentsMargins(0, 5, 0, 0)
        setting_details_layout.setSpacing(10)
        self.content_stack.addWidget(self.setting_details_tab)
        label_width = 160
        world_section_layout = QHBoxLayout()
        world_list_filter_layout = QVBoxLayout()
        world_filter_button_layout = QHBoxLayout()
        label_world = QLabel("World:")
        label_world.setObjectName("SettingManagerLabel")
        label_world.setFixedWidth(label_width)
        self.filter_world_input = QLineEdit()
        self.filter_world_input.setObjectName("FilterInput")
        self.filter_world_input.setPlaceholderText("Filter by...")
        self.filter_world_input.textChanged.connect(self._filter_world_list)
        self.add_world_button = QPushButton("+")
        self.add_world_button.setObjectName("AddButton")
        self.add_world_button.setToolTip("Add New World")
        self.add_world_button.clicked.connect(self._add_world)
        self.remove_world_button = QPushButton("-")
        self.remove_world_button.setObjectName("RemoveButton")
        self.remove_world_button.setToolTip("Remove Selected World")
        self.remove_world_button.clicked.connect(self._remove_world)
        world_filter_button_layout.addWidget(self.filter_world_input, 1)
        world_filter_button_layout.addWidget(self.add_world_button)
        world_filter_button_layout.addWidget(self.remove_world_button)

        self.list_world = QListWidget()
        self.list_world.setObjectName("SettingManagerList")
        self.list_world.setFixedWidth(230)
        self.list_world.setAlternatingRowColors(True)
        self.list_world.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_world.setFocusPolicy(Qt.NoFocus)
        world_list_filter_layout.addLayout(world_filter_button_layout)
        world_list_filter_layout.addWidget(self.list_world)
        edit_layout_world_left = QVBoxLayout()
        label_name_world = QLabel("Name:")
        label_name_world.setObjectName("SettingManagerEditLabel")
        self.world_name_input = QLineEdit()
        self.world_name_input.setObjectName("SettingManagerNameInput")
        label_desc_world = QLabel("Description:")
        label_desc_world.setObjectName("SettingManagerEditLabel")
        self.world_description_input = QTextEdit()
        self.world_description_input.setObjectName("SettingManagerDescInput")
        self.world_description_input.setMaximumHeight(60)
        edit_layout_world_left.addWidget(label_name_world)
        edit_layout_world_left.addWidget(self.world_name_input)
        edit_layout_world_left.addWidget(label_desc_world)
        edit_layout_world_left.addWidget(self.world_description_input)
        edit_layout_world_right = QVBoxLayout()
        label_features_world = QLabel("Features:")
        label_features_world.setObjectName("SettingManagerEditLabel")
        self.world_features_list = QListWidget()
        self.world_features_list.setObjectName("SettingManagerList")
        self.world_features_list.setFixedWidth(140)
        self.world_features_list.setFixedHeight(120)
        self.world_features_list.setAlternatingRowColors(True)
        self.world_features_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.world_features_list.setFocusPolicy(Qt.NoFocus)

        features_btn_layout_world = QVBoxLayout()
        self.add_world_feature_btn = QPushButton("+")
        self.add_world_feature_btn.setObjectName("AddButton")
        self.add_world_feature_btn.setFixedSize(22, 22)
        self.add_world_feature_btn.setToolTip("Add Feature")
        self.add_world_feature_btn.clicked.connect(self._add_world_feature)
        self.remove_world_feature_btn = QPushButton("-")
        self.remove_world_feature_btn.setObjectName("RemoveButton")
        self.remove_world_feature_btn.setFixedSize(22, 22)
        self.remove_world_feature_btn.setToolTip("Remove Selected Feature")
        self.remove_world_feature_btn.clicked.connect(self._remove_world_feature)
        features_btn_layout_world.addWidget(self.add_world_feature_btn)
        features_btn_layout_world.addWidget(self.remove_world_feature_btn)
        features_btn_layout_world.addStretch(1)
        feature_fields_layout_world = QVBoxLayout()
        self.world_feature_name_input = QLineEdit()
        self.world_feature_name_input.setObjectName("SettingManagerNameInput")
        self.world_feature_name_input.setPlaceholderText("Feature Name")
        self.world_feature_desc_input = QTextEdit()
        self.world_feature_desc_input.setObjectName("SettingManagerDescInput")
        self.world_feature_desc_input.setPlaceholderText("Feature Description")
        self.world_feature_desc_input.setMaximumHeight(40)
        feature_fields_layout_world.addWidget(self.world_feature_name_input)
        feature_fields_layout_world.addWidget(self.world_feature_desc_input)
        features_hbox_world = QHBoxLayout()
        features_hbox_world.addWidget(self.world_features_list, 0)
        features_hbox_world.addLayout(features_btn_layout_world, 0)
        features_hbox_world.addLayout(feature_fields_layout_world, 2)
        edit_layout_world_right.addWidget(label_features_world)
        edit_layout_world_right.addLayout(features_hbox_world)
        edit_layout_world_paths = QVBoxLayout()
        label_paths_world = QLabel("Paths:")
        label_paths_world.setObjectName("SettingManagerEditLabel")

        self.world_paths_list = QListWidget()
        self.world_paths_list.setObjectName("SettingManagerList")
        self.world_paths_list.setFixedWidth(140)
        self.world_paths_list.setFixedHeight(120)
        self.world_paths_list.setAlternatingRowColors(True)
        self.world_paths_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.world_paths_list.setFocusPolicy(Qt.NoFocus)
        self.world_paths_list.addItem("Large Path (Default)")
        self.world_paths_list.addItem("Medium Path (Default)")
        self.world_paths_list.addItem("Small Path (Default)")
        paths_btn_layout_world = QVBoxLayout()
        self.add_world_path_btn = QPushButton("+")
        self.add_world_path_btn.setObjectName("AddButton")
        self.add_world_path_btn.setFixedSize(22, 22)
        self.add_world_path_btn.setToolTip("Add Path Type")
        self.add_world_path_btn.clicked.connect(self._add_world_path)
        self.remove_world_path_btn = QPushButton("-")
        self.remove_world_path_btn.setObjectName("RemoveButton")
        self.remove_world_path_btn.setFixedSize(22, 22)
        self.remove_world_path_btn.setToolTip("Remove Selected Path Type")
        self.remove_world_path_btn.clicked.connect(self._remove_world_path)
        paths_btn_layout_world.addWidget(self.add_world_path_btn)
        paths_btn_layout_world.addWidget(self.remove_world_path_btn)
        paths_btn_layout_world.addStretch(1)
        path_fields_layout_world = QVBoxLayout()
        self.world_path_name_input = QLineEdit()
        self.world_path_name_input.setObjectName("SettingManagerNameInput")
        self.world_path_name_input.setPlaceholderText("Path Type Name")
        self.world_path_desc_input = QTextEdit()
        self.world_path_desc_input.setObjectName("SettingManagerDescInput")
        self.world_path_desc_input.setPlaceholderText("Path Type Description")
        self.world_path_desc_input.setMaximumHeight(40)
        path_fields_layout_world.addWidget(self.world_path_name_input)
        path_fields_layout_world.addWidget(self.world_path_desc_input)
        paths_hbox_world = QHBoxLayout()
        paths_hbox_world.addWidget(self.world_paths_list, 0)
        paths_hbox_world.addLayout(paths_btn_layout_world, 0)
        paths_hbox_world.addLayout(path_fields_layout_world, 2)
        edit_layout_world_paths.addWidget(label_paths_world)
        edit_layout_world_paths.addLayout(paths_hbox_world)
        edit_layout_world_trisect = QHBoxLayout()
        edit_layout_world_trisect.addLayout(edit_layout_world_left, 3)
        edit_layout_world_trisect.addLayout(edit_layout_world_right, 2)
        edit_layout_world_trisect.addLayout(edit_layout_world_paths, 2)
        world_section_layout.addWidget(label_world)
        world_section_layout.addLayout(world_list_filter_layout)
        world_section_layout.addLayout(edit_layout_world_trisect, 1)
        setting_details_layout.addLayout(world_section_layout) 
        region_section_layout = QHBoxLayout()
        region_list_filter_layout = QVBoxLayout()
        region_filter_button_layout = QHBoxLayout()
        label1 = QLabel("Region:")
        label1.setObjectName("SettingManagerLabel")
        label1.setFixedWidth(label_width)

        self.filter_region_input = QLineEdit()
        self.filter_region_input.setObjectName("FilterInput")
        self.filter_region_input.setPlaceholderText("Filter by...")
        self.filter_region_input.textChanged.connect(self._filter_region_list)
        self.add_region_button = QPushButton("+")
        self.add_region_button.setObjectName("AddButton")
        self.add_region_button.setToolTip("Add New Region")
        self.add_region_button.clicked.connect(self._add_region)
        self.remove_region_button = QPushButton("-")
        self.remove_region_button.setObjectName("RemoveButton")
        self.remove_region_button.setToolTip("Remove Selected Region")
        self.remove_region_button.clicked.connect(self._remove_region)
        region_filter_button_layout.addWidget(self.filter_region_input, 1)
        region_filter_button_layout.addWidget(self.add_region_button)
        region_filter_button_layout.addWidget(self.remove_region_button)
        self.list1 = QListWidget()
        self.list1.setObjectName("SettingManagerList")
        self.list1.setFixedWidth(230)
        self.list1.setAlternatingRowColors(True)
        self.list1.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list1.setFocusPolicy(Qt.NoFocus)
        region_list_filter_layout.addLayout(region_filter_button_layout)
        region_list_filter_layout.addWidget(self.list1)
        label_name_region = QLabel("Name:")
        label_name_region.setObjectName("SettingManagerEditLabel")
        self.region_name_input = QLineEdit()
        self.region_name_input.setObjectName("SettingManagerNameInput")
        label_desc_region = QLabel("Description:")
        label_desc_region.setObjectName("SettingManagerEditLabel")
        self.region_description_input = QTextEdit()
        self.region_description_input.setObjectName("SettingManagerDescInput")
        self.region_description_input.setMaximumHeight(60)
        region_section_layout.addWidget(label1)
        region_section_layout.addLayout(region_list_filter_layout)
        edit_layout_region = QVBoxLayout()
        edit_layout_region.addWidget(label_name_region)
        edit_layout_region.addWidget(self.region_name_input)
        edit_layout_region.addWidget(label_desc_region)
        edit_layout_region.addWidget(self.region_description_input)
        region_section_layout.addLayout(edit_layout_region, 1)
        setting_details_layout.addLayout(region_section_layout)
        location_section_layout = QHBoxLayout()
        location_list_filter_layout = QVBoxLayout()
        location_list_filter_layout.setContentsMargins(0,0,0,0)
        location_filter_button_layout = QHBoxLayout()
        label2 = QLabel("Location:")
        label2.setObjectName("SettingManagerLabel")
        label2.setFixedWidth(label_width)

        self.filter_location_input = QLineEdit()
        self.filter_location_input.setObjectName("FilterInput")
        self.filter_location_input.setPlaceholderText("Filter by...")
        self.filter_location_input.textChanged.connect(self._filter_location_list)
        self.add_location_button = QPushButton("+")
        self.add_location_button.setObjectName("AddButton")
        self.add_location_button.setToolTip("Add New Location")
        self.add_location_button.clicked.connect(self._add_location)
        self.remove_location_button = QPushButton("-")
        self.remove_location_button.setObjectName("RemoveButton")
        self.remove_location_button.setToolTip("Remove Selected Location")
        self.remove_location_button.clicked.connect(self._remove_location)
        location_filter_button_layout.addWidget(self.filter_location_input, 1)
        location_filter_button_layout.addWidget(self.add_location_button)
        location_filter_button_layout.addWidget(self.remove_location_button)
        self.list2 = QListWidget()
        self.list2.setObjectName("SettingManagerList")
        self.list2.setFixedWidth(230)
        self.list2.setAlternatingRowColors(True)
        self.list2.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list2.setFocusPolicy(Qt.NoFocus)
        location_list_filter_layout.addLayout(location_filter_button_layout)
        location_list_filter_layout.addWidget(self.list2)
        self.location_list_filter_panel = QWidget()
        self.location_list_filter_panel.setFixedWidth(230)
        self.location_list_filter_panel.setLayout(location_list_filter_layout)
        edit_layout_location_left = QVBoxLayout()
        label_name_location = QLabel("Name:")
        label_name_location.setObjectName("SettingManagerEditLabel")
        self.location_name_input = QLineEdit()
        self.location_name_input.setObjectName("SettingManagerNameInput")
        label_desc_location = QLabel("Description:")
        label_desc_location.setObjectName("SettingManagerEditLabel")
        self.location_description_input = QTextEdit()
        self.location_description_input.setObjectName("SettingManagerDescInput")
        self.location_description_input.setMaximumHeight(60)
        edit_layout_location_left.addWidget(label_name_location)
        edit_layout_location_left.addWidget(self.location_name_input)
        edit_layout_location_left.addWidget(label_desc_location)
        edit_layout_location_left.addWidget(self.location_description_input)
        edit_layout_location_right = QVBoxLayout()
        label_features_location = QLabel("Features:")
        label_features_location.setObjectName("SettingManagerEditLabel")
        self.location_features_list = QListWidget()
        self.location_features_list.setObjectName("SettingManagerList")
        self.location_features_list.setFixedWidth(140)
        self.location_features_list.setFixedHeight(120)
        self.location_features_list.setAlternatingRowColors(True)
        self.location_features_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.location_features_list.setFocusPolicy(Qt.NoFocus)
        features_btn_layout_location = QVBoxLayout()
        self.add_location_feature_btn = QPushButton("+")
        self.add_location_feature_btn.setObjectName("AddButton")
        self.add_location_feature_btn.setFixedSize(22, 22)
        self.add_location_feature_btn.setToolTip("Add Feature")
        self.add_location_feature_btn.clicked.connect(self._add_location_feature)
        self.remove_location_feature_btn = QPushButton("-")
        self.remove_location_feature_btn.setObjectName("RemoveButton")
        self.remove_location_feature_btn.setFixedSize(22, 22)
        self.remove_location_feature_btn.setToolTip("Remove Selected Feature")
        self.remove_location_feature_btn.clicked.connect(self._remove_location_feature)
        features_btn_layout_location.addWidget(self.add_location_feature_btn)
        features_btn_layout_location.addWidget(self.remove_location_feature_btn)
        features_btn_layout_location.addStretch(1)
        feature_fields_layout_location = QVBoxLayout()
        self.location_feature_name_input = QLineEdit()
        self.location_feature_name_input.setObjectName("SettingManagerNameInput")
        self.location_feature_name_input.setPlaceholderText("Feature Name")
        self.location_feature_desc_input = QTextEdit()
        self.location_feature_desc_input.setObjectName("SettingManagerDescInput")
        self.location_feature_desc_input.setPlaceholderText("Feature Description")
        self.location_feature_desc_input.setMaximumHeight(40)
        feature_fields_layout_location.addWidget(self.location_feature_name_input)
        feature_fields_layout_location.addWidget(self.location_feature_desc_input)
        features_hbox_location = QHBoxLayout()

        features_hbox_location.addWidget(self.location_features_list, 0)
        features_hbox_location.addLayout(features_btn_layout_location, 0)
        features_hbox_location.addLayout(feature_fields_layout_location, 2)
        edit_layout_location_right.addWidget(label_features_location)
        edit_layout_location_right.addLayout(features_hbox_location)
        edit_layout_location_paths = QVBoxLayout()
        label_paths_location = QLabel("Paths:")
        label_paths_location.setObjectName("SettingManagerEditLabel")
        self.location_paths_list = QListWidget()
        self.location_paths_list.setObjectName("SettingManagerList")
        self.location_paths_list.setFixedWidth(140)
        self.location_paths_list.setFixedHeight(120)
        self.location_paths_list.setAlternatingRowColors(True)
        self.location_paths_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.location_paths_list.setFocusPolicy(Qt.NoFocus)
        self.location_paths_list.addItem("Large Path (Default)")
        self.location_paths_list.addItem("Medium Path (Default)")
        self.location_paths_list.addItem("Small Path (Default)")
        paths_btn_layout_location = QVBoxLayout()
        self.add_location_path_btn = QPushButton("+")
        self.add_location_path_btn.setObjectName("AddButton")
        self.add_location_path_btn.setFixedSize(22, 22)
        self.add_location_path_btn.setToolTip("Add Path Type")
        self.add_location_path_btn.clicked.connect(self._add_location_path)
        self.remove_location_path_btn = QPushButton("-")
        self.remove_location_path_btn.setObjectName("RemoveButton")
        self.remove_location_path_btn.setFixedSize(22, 22)
        self.remove_location_path_btn.setToolTip("Remove Selected Path Type")
        self.remove_location_path_btn.clicked.connect(self._remove_location_path)
        paths_btn_layout_location.addWidget(self.add_location_path_btn)
        paths_btn_layout_location.addWidget(self.remove_location_path_btn)
        paths_btn_layout_location.addStretch(1)
        path_fields_layout_location = QVBoxLayout()
        self.location_path_name_input = QLineEdit()
        self.location_path_name_input.setObjectName("SettingManagerNameInput")
        self.location_path_name_input.setPlaceholderText("Path Type Name")
        self.location_path_desc_input = QTextEdit()
        self.location_path_desc_input.setObjectName("SettingManagerDescInput")
        self.location_path_desc_input.setPlaceholderText("Path Type Description")
        self.location_path_desc_input.setMaximumHeight(40)
        path_fields_layout_location.addWidget(self.location_path_name_input)
        path_fields_layout_location.addWidget(self.location_path_desc_input)
        paths_hbox_location = QHBoxLayout()
        paths_hbox_location.addWidget(self.location_paths_list, 0)
        paths_hbox_location.addLayout(paths_btn_layout_location, 0)
        paths_hbox_location.addLayout(path_fields_layout_location, 2)
        edit_layout_location_paths.addWidget(label_paths_location)
        edit_layout_location_paths.addLayout(paths_hbox_location)
        edit_layout_location_connections = QVBoxLayout()
        label_connections_location = QLabel("Incoming Connections:")
        label_connections_location.setObjectName("SettingManagerEditLabel")
        self.location_connections_container = QWidget()
        self.location_connections_layout = QVBoxLayout(self.location_connections_container)
        self.location_connections_layout.setContentsMargins(5, 5, 5, 5)
        self.location_connections_layout.setSpacing(2)
        self.location_connections_container.setObjectName("SettingManagerList")
        self.location_connections_scroll = QScrollArea()
        self.location_connections_scroll.setWidgetResizable(True)
        self.location_connections_scroll.setWidget(self.location_connections_container)
        self.location_connections_scroll.setObjectName("ConnectionsScrollArea")
        edit_layout_location_connections.addWidget(label_connections_location)
        edit_layout_location_connections.addWidget(self.location_connections_scroll)
        edit_layout_location_connections.addStretch(1)
        edit_layout_location_trisect = QHBoxLayout()
        edit_layout_location_trisect.addLayout(edit_layout_location_left, 3)
        edit_layout_location_trisect.addLayout(edit_layout_location_connections, 2)
        edit_layout_location_trisect.addLayout(edit_layout_location_right, 2)
        edit_layout_location_trisect.addLayout(edit_layout_location_paths, 2)
        self.location_details_widget = QWidget()
        location_details_widget_layout = QHBoxLayout(self.location_details_widget)
        location_details_widget_layout.setContentsMargins(0,0,0,0)
        location_details_widget_layout.addLayout(edit_layout_location_trisect)
        location_section_layout.addWidget(label2)
        location_section_layout.addWidget(self.location_list_filter_panel)
        location_section_layout.addWidget(self.location_details_widget, 99)
        location_section_layout.addStretch(1)
        setting_details_layout.addLayout(location_section_layout)
        setting_section_layout = QHBoxLayout()
        setting_list_filter_layout = QVBoxLayout()
        setting_filter_button_layout = QHBoxLayout()
        label3 = QLabel("Setting:")
        label3.setObjectName("SettingManagerLabel")
        label3.setFixedWidth(label_width)

        self.filter_setting_input = QLineEdit()
        self.filter_setting_input.setObjectName("FilterInput") 
        self.filter_setting_input.setPlaceholderText("Filter by...")
        self.filter_setting_input.textChanged.connect(self._filter_setting_list)
        self.add_setting_button = QPushButton("+")
        self.add_setting_button.setObjectName("AddButton")
        self.add_setting_button.setToolTip("Add New Setting")
        self.add_setting_button.clicked.connect(self._add_setting)
        self.remove_setting_button = QPushButton("-")
        self.remove_setting_button.setObjectName("RemoveButton")
        self.remove_setting_button.setToolTip("Remove Selected Setting")
        self.remove_setting_button.clicked.connect(self._remove_setting)
        setting_filter_button_layout.addWidget(self.filter_setting_input, 1)
        setting_filter_button_layout.addWidget(self.add_setting_button)
        setting_filter_button_layout.addWidget(self.remove_setting_button)
        self.list3 = QListWidget()
        self.list3.setObjectName("SettingManagerList")
        self.list3.setFixedWidth(230)
        self.list3.setAlternatingRowColors(True)
        self.list3.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list3.setFocusPolicy(Qt.NoFocus)
        setting_list_filter_layout.addLayout(setting_filter_button_layout)
        setting_list_filter_layout.addWidget(self.list3)
        label_name_setting = QLabel("Name:")
        label_name_setting.setObjectName("SettingManagerEditLabel")
        self.setting_name_input = QLineEdit()
        self.setting_name_input.setObjectName("SettingManagerNameInput")
        label_desc_setting = QLabel("Description:")
        label_desc_setting.setObjectName("SettingManagerEditLabel")
        self.setting_description_input = QTextEdit()
        self.setting_description_input.setObjectName("SettingManagerDescInput")
        self.setting_description_input.setMaximumHeight(60)
        from .inventory_manager import ItemInstanceWidget
        
        label_inventory_setting = QLabel("Inventory:")
        label_inventory_setting.setObjectName("SettingManagerEditLabel")
        
        inventory_section_layout = QVBoxLayout()
        inventory_section_layout.setContentsMargins(0, 0, 0, 0)
        inventory_section_layout.setSpacing(2)
        
        inventory_header_layout = QHBoxLayout()
        inventory_header_layout.addWidget(label_inventory_setting)
        inventory_header_layout.addStretch(1)
        
        self.edit_inventory_btn = QPushButton("Edit")
        self.edit_inventory_btn.setObjectName("EditButton")
        self.edit_inventory_btn.setToolTip("Edit Inventory in Inventory Manager")
        self.edit_inventory_btn.setMaximumWidth(60)
        self.edit_inventory_btn.clicked.connect(self._edit_inventory_in_manager)
        inventory_header_layout.addWidget(self.edit_inventory_btn)
        
        inventory_section_layout.addLayout(inventory_header_layout)
        
        self.setting_inventory_table = QTableWidget()
        self.setting_inventory_table.setObjectName("SettingManagerTable")
        self.setting_inventory_table.setColumnCount(4)
        self.setting_inventory_table.setHorizontalHeaderLabels(["Name", "Quantity", "Owner", "Description"])
        header = self.setting_inventory_table.horizontalHeader()
        header.setObjectName("SettingManagerTableHeader")
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.setting_inventory_table.setColumnWidth(1, 80)
        self.setting_inventory_table.setColumnWidth(2, 100)
        self.setting_inventory_table.verticalHeader().setVisible(False)
        self.setting_inventory_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setting_inventory_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setting_inventory_table.setAlternatingRowColors(True)
        self.setting_inventory_table.setFocusPolicy(Qt.NoFocus)
        self.setting_inventory_table.setMaximumHeight(150)
        self.setting_inventory_table.itemChanged.connect(self._on_inventory_item_changed)
        
        inventory_section_layout.addWidget(self.setting_inventory_table)
        setting_section_layout.addWidget(label3)
        setting_section_layout.addLayout(setting_list_filter_layout)
        edit_layout_setting = QVBoxLayout()
        name_desc_layout_setting = QHBoxLayout() 
        name_desc_layout_setting.addWidget(label_name_setting)
        name_desc_layout_setting.addWidget(self.setting_name_input)
        name_desc_layout_setting.addWidget(label_desc_setting)
        name_desc_layout_setting.addWidget(self.setting_description_input)
        variables_layout = QVBoxLayout()
        label_variables_setting = QLabel("Variables:")
        label_variables_setting.setObjectName("SettingManagerEditLabel")
        add_variable_button = QPushButton("+")
        add_variable_button.setObjectName("AddButton")
        add_variable_button.setToolTip("Add Variable")
        add_variable_button.setMaximumWidth(30)
        add_variable_button.clicked.connect(lambda: self._add_variable_row())
        remove_variable_button = QPushButton("-")
        remove_variable_button.setObjectName("RemoveButton")
        remove_variable_button.setToolTip("Remove Selected Variable")
        remove_variable_button.setMaximumWidth(30)
        remove_variable_button.clicked.connect(self._remove_selected_variable_row)
        variables_header_layout = QHBoxLayout()
        variables_header_layout.addWidget(label_variables_setting)
        variables_header_layout.addStretch()

        variables_header_layout.addWidget(add_variable_button)
        variables_header_layout.addWidget(remove_variable_button)
        variables_layout.addLayout(variables_header_layout)
        self.variables_scroll_area = QScrollArea()
        self.variables_scroll_area.setWidgetResizable(True)
        self.variables_scroll_area.setObjectName("VariablesScrollArea")
        self.variables_scroll_area.setMinimumHeight(80)
        self.variables_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        variables_content_widget = QWidget()
        self.variables_list_layout = QVBoxLayout(variables_content_widget)
        self.variables_list_layout.setAlignment(Qt.AlignTop)
        self.variables_scroll_area.setWidget(variables_content_widget)
        variables_layout.addWidget(self.variables_scroll_area)
        connections_layout = QVBoxLayout()
        label_connections_setting = QLabel("Connections:")
        label_connections_setting.setObjectName("SettingManagerEditLabel")
        connections_layout.addWidget(label_connections_setting)
        self.connections_content_widget = QWidget()
        self.connections_content_layout = QVBoxLayout(self.connections_content_widget)
        self.connections_content_layout.setAlignment(Qt.AlignTop)
        self.connections_scroll_area = QScrollArea()
        self.connections_scroll_area.setWidgetResizable(True)
        self.connections_scroll_area.setObjectName("ConnectionsScrollArea")
        self.connections_scroll_area.setMinimumHeight(80)
        self.connections_scroll_area.setMaximumHeight(250)
        self.connections_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.connections_scroll_area.setWidget(self.connections_content_widget)
        connections_layout.addWidget(self.connections_scroll_area)
        actors_layout = QVBoxLayout()
        actors_layout.setSpacing(2)
        actors_layout.setContentsMargins(0, 0, 0, 0)
        
        actors_header_layout = QHBoxLayout()
        actors_label = QLabel("Actors:")
        actors_label.setObjectName("SettingManagerEditLabel")
        actors_header_layout.addWidget(actors_label)
        actors_header_layout.addStretch()
        
        self.add_actor_to_setting_button = QPushButton("+")
        self.add_actor_to_setting_button.setObjectName("AddButton")
        self.add_actor_to_setting_button.setToolTip("Add Actor to this Setting")
        self.add_actor_to_setting_button.setMaximumWidth(30)
        self.add_actor_to_setting_button.clicked.connect(self._add_actor_to_setting)
        actors_header_layout.addWidget(self.add_actor_to_setting_button)
        
        self.remove_actor_from_setting_button = QPushButton("-")
        self.remove_actor_from_setting_button.setObjectName("RemoveButton")
        self.remove_actor_from_setting_button.setToolTip("Remove selected Actor from this Setting")
        self.remove_actor_from_setting_button.setMaximumWidth(30)
        self.remove_actor_from_setting_button.clicked.connect(self._remove_actor_from_setting)
        actors_header_layout.addWidget(self.remove_actor_from_setting_button)
        
        actors_layout.addLayout(actors_header_layout)
        
        # Add text input for actor name
        self.actor_name_input = QLineEdit()
        self.actor_name_input.setObjectName("SettingManagerNameInput")
        self.actor_name_input.setPlaceholderText("Enter actor name...")
        self.actor_name_input.setMaximumWidth(150)
        actors_layout.addWidget(self.actor_name_input)
        
        self.actors_in_setting_list = QListWidget()
        self.actors_in_setting_list.setObjectName("SettingManagerList")
        self.actors_in_setting_list.setFixedWidth(150)
        self.actors_in_setting_list.setAlternatingRowColors(True)
        self.actors_in_setting_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.actors_in_setting_list.setFocusPolicy(Qt.StrongFocus)
        self.actors_in_setting_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        actors_layout.addWidget(self.actors_in_setting_list)
        variables_connections_row = QHBoxLayout()
        variables_connections_row.setSpacing(12)
        variables_connections_row.addLayout(variables_layout, 1)
        variables_connections_row.addLayout(connections_layout, 1)
        variables_connections_row.addLayout(actors_layout, 0)
        inventory_variables_row = QHBoxLayout()
        inventory_variables_row.setSpacing(12)
        inventory_variables_row.addLayout(inventory_section_layout, 1)
        inventory_variables_row.addLayout(variables_connections_row, 2)
        from PyQt5.QtWidgets import QFrame
        self.connections_separator = QFrame()
        self.connections_separator.setFrameShape(QFrame.HLine)
        self.connections_separator.setObjectName("SettingManagerHSeparator")
        self.connections_group = QGroupBox("Connections")
        self.connections_group.setObjectName("SettingConnectionsGroup")
        self.connections_layout = QVBoxLayout()
        self.connections_group.setLayout(self.connections_layout)
        self.connections_group.setVisible(False)
        edit_layout_setting.addLayout(name_desc_layout_setting)
        edit_layout_setting.addLayout(inventory_variables_row)
        self.setting_extra_area_container = QWidget()
        self.setting_extra_area_container.setObjectName("SettingExtraAreaContainer")
        self.setting_extra_area_layout = QVBoxLayout(self.setting_extra_area_container)
        self.setting_extra_area_layout.setContentsMargins(0, 0, 0, 0)
        self.setting_extra_area_layout.setSpacing(6)
        self.setting_exterior_checkbox = QCheckBox()
        self.setting_exterior_checkbox.setObjectName("SettingExteriorCheckbox")
        self.setting_exterior_checkbox.stateChanged.connect(self._schedule_description_save)
        self.setting_exterior_checkbox.stateChanged.connect(self._save_exterior_state_immediately)
        exterior_layout = QHBoxLayout()
        exterior_label = QLabel("Exterior:")

        exterior_label.setObjectName("SettingManagerEditLabel")
        exterior_layout.addWidget(exterior_label)
        exterior_layout.addWidget(self.setting_exterior_checkbox)
        exterior_layout.addStretch(1)
        self.setting_extra_area_layout.addLayout(exterior_layout)
        self.visible_section_container = QWidget()
        self.visible_section_container.setObjectName("VisibleSectionContainer")
        self.visible_section_layout = QVBoxLayout(self.visible_section_container)
        self.visible_section_layout.setContentsMargins(0, 0, 0, 0)
        self.visible_section_layout.setSpacing(2)
        directions = [
            "North", "Northeast", "East", "Southeast",
            "South", "Southwest", "West", "Northwest"
        ]
        for direction in directions:
            dir_label = QLabel(f"Visible {direction}:")
            dir_label.setObjectName("SettingManagerEditLabel")
            self.visible_section_layout.addWidget(dir_label)
        self.setting_extra_area_layout.addWidget(self.visible_section_container)
        self.setting_extra_area_layout.addStretch(1)
        self.setting_extra_area_scroll = QScrollArea()
        self.setting_extra_area_scroll.setObjectName("SettingExtraAreaScroll")
        self.setting_extra_area_scroll.setWidgetResizable(True)
        self.setting_extra_area_scroll.setWidget(self.setting_extra_area_container)
        self.setting_extra_area_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.generation_options_container = QWidget()
        self.generation_options_container.setObjectName("GenerationOptionsContainer")
        self.generation_options_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        generation_options_layout = QHBoxLayout(self.generation_options_container)
        generation_options_layout.setContentsMargins(2, 2, 2, 2)
        generation_options_layout.setSpacing(4)
        checkboxes_layout = QVBoxLayout()
        checkboxes_layout.setSpacing(6)
        self.name_gen_checkbox = QCheckBox("Name")
        self.name_gen_checkbox.setObjectName("NameGenCheckbox")
        self.name_gen_checkbox.setLayoutDirection(Qt.LeftToRight)
        checkboxes_layout.addWidget(self.name_gen_checkbox)
        self.desc_gen_checkbox = QCheckBox("Description")
        self.desc_gen_checkbox.setObjectName("DescGenCheckbox")
        self.desc_gen_checkbox.setLayoutDirection(Qt.LeftToRight)
        checkboxes_layout.addWidget(self.desc_gen_checkbox)
        self.conn_gen_checkbox = QCheckBox("Connections")
        self.conn_gen_checkbox.setObjectName("ConnGenCheckbox")
        self.conn_gen_checkbox.setLayoutDirection(Qt.LeftToRight)
        checkboxes_layout.addWidget(self.conn_gen_checkbox)
        self.inv_gen_checkbox = QCheckBox("Inventory")
        self.inv_gen_checkbox.setObjectName("InvGenCheckbox")
        self.inv_gen_checkbox.setLayoutDirection(Qt.LeftToRight)
        checkboxes_layout.addWidget(self.inv_gen_checkbox)
        generate_button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate")
        self.generate_button.setObjectName("GenerateButton")
        self.generate_button.clicked.connect(self._call_generate_setting_details)
        generate_button_layout.addWidget(self.generate_button)
        instructions_layout = QVBoxLayout()
        instructions_layout.setSpacing(1)
        instructions_layout.setContentsMargins(0, 0, 0, 0)
        self.generation_instructions_input = QTextEdit()
        self.generation_instructions_input.setObjectName("GenerateInstructionsInput")
        self.generation_instructions_input.setFixedHeight(50)
        self.generation_instructions_input.setPlaceholderText("Additional instructions...")
        instructions_layout.addWidget(self.generation_instructions_input, 1)
        top_row_layout = QHBoxLayout()
        top_row_layout.addLayout(checkboxes_layout, 0)
        top_row_layout.addLayout(instructions_layout, 1)
        overall_layout = QVBoxLayout()
        overall_layout.addLayout(top_row_layout)
        overall_layout.addLayout(generate_button_layout)
        generation_options_layout.addLayout(overall_layout, 1)
        self.generation_options_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        setting_details_horizontal_layout = QHBoxLayout()
        setting_details_horizontal_layout.addWidget(self.setting_extra_area_scroll, 1)
        setting_details_horizontal_layout.addWidget(self.generation_options_container, 0)
        setting_details_horizontal_layout.addLayout(variables_connections_row, 2)
        edit_layout_setting.addLayout(setting_details_horizontal_layout)
        setting_section_layout.addLayout(edit_layout_setting, 1)
        setting_details_layout.addLayout(setting_section_layout)
        self.world_editor_tab = WorldEditorWidget(theme_colors=self.theme_colors, workflow_data_dir=self.workflow_data_dir)
        self.content_stack.addWidget(self.world_editor_tab)
        self.list_world.currentItemChanged.connect(self._on_world_selected)
        self.list1.currentItemChanged.connect(self._on_region_selected)
        self.list2.currentItemChanged.connect(self._on_location_selected)
        self.list3.currentItemChanged.connect(self._on_setting_selected)
        if hasattr(self.world_editor_tab, 'settingAddedOrRemoved'):

            self.world_editor_tab.settingAddedOrRemoved.connect(self._handle_setting_added_or_removed)
        self.world_name_input.editingFinished.connect(self._save_current_details)
        self.world_description_input.textChanged.connect(self._schedule_description_save)
        self.region_name_input.editingFinished.connect(self._save_current_details)
        self.region_description_input.textChanged.connect(self._schedule_description_save)
        self.location_name_input.editingFinished.connect(self._save_current_details)
        self.location_description_input.textChanged.connect(self._schedule_description_save)
        self.setting_name_input.editingFinished.connect(self._save_current_details)
        self.setting_description_input.textChanged.connect(self._schedule_description_save)

        self.world_name_input.installEventFilter(self)
        self.world_description_input.installEventFilter(self)
        self.region_name_input.installEventFilter(self)
        self.region_description_input.installEventFilter(self)
        self.location_name_input.installEventFilter(self)
        self.location_description_input.installEventFilter(self)
        self.setting_name_input.installEventFilter(self)
        self.setting_description_input.installEventFilter(self)


        self._ensure_default_setting_structure()
        self.populate_worlds()
        self.visible_section_container.setVisible(False)
        self.world_paths_list.currentRowChanged.connect(self._on_world_path_selected)
        self.world_path_name_input.editingFinished.connect(self._on_world_path_name_edited)
        self.world_path_desc_input.textChanged.connect(self._on_world_path_desc_edited)
        self.location_paths_list.currentRowChanged.connect(self._on_location_path_selected)
        self.location_path_name_input.editingFinished.connect(self._on_location_path_name_edited)
        self.location_path_desc_input.textChanged.connect(self._on_location_path_desc_edited)
        self.world_features_list.currentRowChanged.connect(self._on_world_feature_selected)
        self.world_feature_name_input.editingFinished.connect(self._on_world_feature_name_edited)
        self.world_feature_desc_input.textChanged.connect(self._on_world_feature_desc_edited)
        self.location_features_list.currentRowChanged.connect(self._on_location_feature_selected)
        self.location_feature_name_input.editingFinished.connect(self._on_location_feature_name_edited)
        self.location_feature_desc_input.textChanged.connect(self._on_location_feature_desc_edited)

    def _handle_setting_added_or_removed(self):
        actual_location_path = None
        if self._selected_location_orig == "__global__" or self._selected_location_orig is None:
            if self._selected_region_orig and self._selected_region_orig != "__global__":
                actual_location_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig, self._selected_region_orig)
            elif self._selected_world_orig:
                actual_location_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
        else:
            actual_location_path = self._get_actual_location_path_for_setting_creation(
                self._selected_world_orig,
                self._selected_region_orig,
                self._selected_location_orig
            )
        self.list3.clear()
        self.setting_name_input.clear()
        self.setting_description_input.clear()
        self.setting_inventory_table.setRowCount(0)
        self._clear_variable_rows()
        self.actors_in_setting_list.clear()
        if actual_location_path:
            self.populate_settings(actual_location_path)
        else:
            print("[ERROR] Could not determine location path for settings refresh.")

    def _on_setting_details_clicked(self):
        self.setting_details_btn.setChecked(True)
        self.world_editor_btn.setChecked(False)
        self.content_stack.setCurrentIndex(0)
        if self.world_editor_tab is not None:
            self.world_editor_tab.hide()
    
    def _on_world_editor_clicked(self):
        self.setting_details_btn.setChecked(False)
        self.world_editor_btn.setChecked(True)
        self.content_stack.setCurrentIndex(1)
        if self.world_editor_tab is not None:
            self.world_editor_tab.show()
    


    def populate_worlds(self):
        self.list_world.clear()
        self.list1.clear()
        self.list2.clear()
        self.list3.clear()
        settings_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
        if not os.path.isdir(settings_dir):
            print(f"SettingManager: World settings directory not found: {settings_dir}")
            return
        items_added = []
        for folder_name in os.listdir(settings_dir):
            actual_folder_name = folder_name
            folder_path = os.path.join(settings_dir, actual_folder_name)
            if os.path.isdir(folder_path):
                actual_world_json_path = None
                world_data = None
                pattern1 = f"{actual_folder_name}_world.json"
                path1 = self._find_file_case_insensitive(folder_path, pattern1)
                if path1:
                    actual_world_json_path = path1
                else:
                    pattern2 = f"{sanitize_path_name(actual_folder_name)}_world.json"
                    path2 = self._find_file_case_insensitive(folder_path, pattern2)
                    if path2:
                        actual_world_json_path = path2
                    else:
                        try:
                            for f_name in os.listdir(folder_path):
                                if fnmatch.fnmatch(f_name.lower(), "*_world.json"):
                                    actual_world_json_path = os.path.join(folder_path, f_name)
                                    break 
                        except Exception as e_scan:
                            print(f"  Error during generic scan for world JSON in {actual_folder_name}: {e_scan}")
                if actual_world_json_path:
                    world_data = self._load_json(actual_world_json_path)
                    display_name = world_data.get('name', actual_folder_name.replace("_", " ").replace("-", " ").title())
    
                    item = QListWidgetItem()
                    item.setText(display_name)
                    item.setData(Qt.UserRole, actual_folder_name)
                    self.list_world.addItem(item)
                    items_added.append(item)
                else:
                    print(f"  Skipping folder (no world JSON): {actual_folder_name} in '{folder_path}' after multiple attempts.")
        if items_added:
            items_added.sort(key=lambda x: x.text().lower())
            self.list_world.sortItems()
            if self.list_world.count() > 0:
                self.list_world.setCurrentItem(self.list_world.item(0))

    def _on_world_selected(self, current_item, previous_item):
        self._is_navigating = True
        self._description_save_timer.stop()
        self.list1.clear(); self.list2.clear(); self.list3.clear()
        self.region_name_input.clear(); self.region_description_input.clear()
        self.location_name_input.clear(); self.location_description_input.clear()
        self.setting_name_input.clear(); self.setting_description_input.clear()
        self.setting_inventory_table.setRowCount(0); self.actors_in_setting_list.clear()
        self._selected_level = None; self._selected_region_orig = None
        self._selected_location_orig = None; self._selected_setting_orig = None
        self.world_features_list.clear(); self.world_feature_name_input.clear(); self.world_feature_desc_input.clear()
        self.current_world_features = []
        self.location_features_list.clear(); self.location_feature_name_input.clear(); self.location_feature_desc_input.clear()
        self.current_location_features = []
        self.world_paths_list.clear()
        self.world_path_name_input.clear(); self.world_path_desc_input.clear()
        self.current_world_path_data_cache.clear()
        if current_item is None:
            try:
                self.world_name_input.editingFinished.disconnect()
            except TypeError:
                pass
            try:
                self.world_description_input.textChanged.disconnect()
            except TypeError:
                pass
            self.world_name_input.clear(); self.world_description_input.clear()
            self._selected_world_orig = None
            self.world_name_input.editingFinished.connect(self._save_current_details)
            self.world_description_input.textChanged.connect(self._schedule_description_save)
            self.list1.addItem("NONE") 
            self.list1.item(0).setData(Qt.UserRole, "__global__")
            if self.list1.count() > 0:
                self.list1.setCurrentItem(self.list1.item(0))
            self._is_navigating = False
            return
        self._selected_world_orig = current_item.data(Qt.UserRole)
        if not self._selected_world_orig:
            self.world_name_input.clear(); self.world_description_input.clear(); return
        self._selected_level = 'world'
        world_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
        world_json_path = self._get_json_path('world', self._selected_world_orig) 
        world_data = self._load_json(world_json_path) if world_json_path else {}
        display_name_for_input = world_data.get('name', current_item.text())
        try:
            self.world_name_input.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.world_description_input.textChanged.disconnect()
        except TypeError:
            pass
        self.world_name_input.setText(display_name_for_input)
        self.world_description_input.setPlainText(world_data.get('description', ''))
        self.world_name_input.editingFinished.connect(self._save_current_details)
        self.world_description_input.textChanged.connect(self._schedule_description_save)
        self.current_world_features = world_data.get('features', [])
        self._populate_world_features_list()
        default_path_names = ["Large Path (Default)", "Medium Path (Default)", "Small Path (Default)"]
        default_descriptions = {
            "Large Path (Default)": "A wide, well-maintained path suitable for vehicles and heavy traffic.",
            "Medium Path (Default)": "A regular path that can comfortably accommodate foot traffic and small carts.",
            "Small Path (Default)": "A narrow trail or footpath that may be difficult to traverse."
        }
        for name in default_path_names:
            default_desc = default_descriptions.get(name, "")
            self.current_world_path_data_cache[name] = {"name": name, "description": default_desc}
        persisted_paths = world_data.get('paths', [])
        for path_entry in persisted_paths:
            if isinstance(path_entry, dict) and 'name' in path_entry:
                name = path_entry['name']
                desc = path_entry.get('description', '')
                self.current_world_path_data_cache[name] = {"name": name, "description": desc}
        final_path_list_names = list(default_path_names)
        for name in self.current_world_path_data_cache.keys():
            if name not in final_path_list_names:
                final_path_list_names.append(name)
        self.world_paths_list.clear()
        for name in final_path_list_names:
            self.world_paths_list.addItem(name)
        if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
            self.world_editor_tab.set_world(self._selected_world_orig)
            self.populate_regions(world_path)
        self.populate_settings(world_path)
        self._is_navigating = False

    def populate_regions(self, world_path):
        self.list1.clear()
        self.list2.clear()
        self.list3.clear()
        if not os.path.isdir(world_path):
            print(f"SettingManager: World path does not exist or is not a directory: {world_path}")
            return
        none_item = QListWidgetItem()
        none_item.setText("NONE")
        none_item.setData(Qt.UserRole, "__global__")
        none_item.setToolTip("Settings placed directly in world (no region)")
        self.list1.addItem(none_item)
        items_added_to_list1 = [none_item]
        region_folders_data = []
        for region_folder_name_actual in os.listdir(world_path):
            actual_region_folder_name = region_folder_name_actual
            region_folder_path = os.path.join(world_path, actual_region_folder_name)
            if os.path.isdir(region_folder_path) and actual_region_folder_name.lower() != 'resources':
                actual_region_json_path = None
                region_data = None
                pattern1 = f"{actual_region_folder_name}_region.json"
                path1 = self._find_file_case_insensitive(region_folder_path, pattern1)
                if path1:
                    actual_region_json_path = path1
                else:
                    pattern2 = f"{sanitize_path_name(actual_region_folder_name)}_region.json"
                    path2 = self._find_file_case_insensitive(region_folder_path, pattern2)
                    if path2:
                        actual_region_json_path = path2
                    else:
                        try:
                            for f_name in os.listdir(region_folder_path):
                                if fnmatch.fnmatch(f_name.lower(), "*_region.json"):
                                    actual_region_json_path = os.path.join(region_folder_path, f_name)
                                    break
                        except Exception as e_scan:
                             print(f"  Error during generic scan for region JSON in {actual_region_folder_name}: {e_scan}")
                if actual_region_json_path:
                    region_data = self._load_json(actual_region_json_path)
                    display_name = region_data.get('name', actual_region_folder_name.replace("_", " ").replace("-"," ").title())
                    region_folders_data.append((display_name, actual_region_folder_name))
        region_folders_data.sort(key=lambda x: x[0].lower())
        for display_name, actual_folder_name in region_folders_data:
            item = QListWidgetItem()
            item.setText(display_name)
            item.setData(Qt.UserRole, actual_folder_name)
            self.list1.addItem(item)
            items_added_to_list1.append(item)
        if items_added_to_list1:
            self.list1.setCurrentItem(items_added_to_list1[0]) 
        else:
            self.list1.clear()
            self.list2.clear()
            self.list3.clear()
            self.region_name_input.clear()
            self.region_description_input.clear()
            self.location_name_input.clear()
            self.location_description_input.clear()
            self.setting_name_input.clear()
            self.setting_description_input.clear()
            self.setting_inventory_table.setRowCount(0)
            self.actors_in_setting_list.clear()

    def _on_region_selected(self, current_item, previous_item):
        self._is_navigating = True
        self._description_save_timer.stop()
        self.list2.clear()
        self.list3.clear()
        self.location_name_input.clear(); self.location_description_input.clear()
        self.setting_name_input.clear(); self.setting_description_input.clear()
        self.setting_inventory_table.setRowCount(0)
        self.actors_in_setting_list.clear()
        self._selected_level = None
        self._selected_location_orig = None
        self._selected_setting_orig = None
        self.location_features_list.clear()
        self.location_feature_name_input.clear()
        self.location_feature_desc_input.clear()
        self.current_location_features = []
        self.actors_in_setting_list.clear()
        if current_item is None:
            self.region_name_input.clear(); self.region_description_input.clear()
            self._selected_region_orig = None
            if self._selected_world_orig:
                self._selected_level = 'world'
                self.populate_locations(None)
                world_settings_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
                self.populate_settings(world_settings_path)
            else:
                self.list2.clear(); self.list3.clear()
                self.location_name_input.clear(); self.location_description_input.clear()
                self.setting_name_input.clear(); self.setting_description_input.clear()
                self.setting_inventory_table.setRowCount(0); self.actors_in_setting_list.clear()
            return
        self._selected_region_orig = current_item.data(Qt.UserRole)
        if not self._selected_region_orig :
             print("[ERROR] _on_region_selected: current_item has no UserRole data for region original name.")
             self.region_name_input.clear(); self.region_description_input.clear()
             return
        if self._selected_region_orig == "__global__":
            try:
                self.region_name_input.editingFinished.disconnect()
            except TypeError:
                pass
            try:
                self.region_description_input.textChanged.disconnect()
            except TypeError:
                pass
            self.region_name_input.setText("World Level")
            self.region_description_input.setPlainText("Settings and locations here are placed directly in the world folder.")
            self.region_name_input.setReadOnly(True)
            self.region_description_input.setReadOnly(True)
            self._selected_level = 'world'
            self.region_name_input.editingFinished.connect(self._save_current_details)
            self.region_description_input.textChanged.connect(self._schedule_description_save)
            self.populate_locations(None)
            if self._selected_world_orig:
                world_folder = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
                self.populate_settings(world_folder)
            else:
                self.list3.clear()
                self.setting_name_input.clear(); self.setting_description_input.clear()
                self.setting_inventory_table.setRowCount(0); self.actors_in_setting_list.clear()
            return
        self.region_name_input.setReadOnly(False)
        self.region_description_input.setReadOnly(False)
        self._selected_level = 'region'
        if not self._selected_world_orig:
            self.region_name_input.clear(); self.region_description_input.clear()
            self.list2.clear(); self.list3.clear()
            self.location_name_input.clear(); self.location_description_input.clear()
            self.setting_name_input.clear(); self.setting_description_input.clear()
            self.setting_inventory_table.setRowCount(0); self.actors_in_setting_list.clear()
            return
        region_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig, self._selected_region_orig)
        region_json_path = self._get_json_path('region', self._selected_world_orig, self._selected_region_orig)
        region_data = self._load_json(region_json_path) if region_json_path else {}
        try:
            self.region_name_input.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.region_description_input.textChanged.disconnect()
        except TypeError:
            pass
        self.region_name_input.setText(region_data.get('name', self._selected_region_orig.replace('_', ' ').title()))
        self.region_description_input.setPlainText(region_data.get('description', ''))
        self.region_name_input.editingFinished.connect(self._save_current_details)
        self.region_description_input.textChanged.connect(self._schedule_description_save)
        self.populate_locations(region_path)
        self.populate_settings(region_path)
        self._is_navigating = False

    def _on_location_selected(self, current_item, previous_item):
        self._is_navigating = True
        self._description_save_timer.stop()
        self.list3.clear(); self.setting_name_input.clear(); self.setting_description_input.clear()
        self.setting_inventory_table.setRowCount(0); self.actors_in_setting_list.clear()
        self._selected_level = None; self._selected_setting_orig = None
        self.location_features_list.clear(); self.location_feature_name_input.clear(); self.location_feature_desc_input.clear()
        self.current_location_features = []
        self.location_paths_list.clear()
        self.location_path_name_input.clear(); self.location_path_desc_input.clear()
        self.current_location_path_data_cache.clear()
        if current_item is None:
            self.location_name_input.clear()
            self.location_description_input.clear()
            self._selected_location_orig = None
            self.location_details_widget.setVisible(False)
            if self._selected_region_orig and self._selected_region_orig != "__global__":
                self._selected_level = 'region'
                parent_path = os.path.join(
                    self.workflow_data_dir,
                    'resources',
                    'data files',
                    'settings',
                    self._selected_world_orig,
                    self._selected_region_orig
                )
                self.populate_settings(parent_path)
            elif self._selected_world_orig:
                self._selected_level = 'world'
                parent_path = os.path.join(
                    self.workflow_data_dir,
                    'resources',
                    'data files',
                    'settings',
                    self._selected_world_orig
                )
                self.populate_settings(parent_path)
            return
        self._selected_location_orig = current_item.data(Qt.UserRole)
        location_display_name = current_item.text()
        if not self._selected_location_orig:
            self.location_name_input.clear(); self.location_description_input.clear()
            return
        actual_location_path = self._get_actual_location_path_for_setting_creation(
            self._selected_world_orig, self._selected_region_orig, self._selected_location_orig)
        if actual_location_path:
            self.populate_settings(actual_location_path)
        if (
            hasattr(self, 'world_editor_tab')
            and self.world_editor_tab
            and self._selected_location_orig != "__global__"
        ):
            if location_display_name and self._selected_world_orig:
                self.world_editor_tab.set_location(location_display_name)
                
        if self._selected_location_orig == "__global__":
            self.location_name_input.setText("Region Level")
            self.location_description_input.setPlainText(
                "Settings here are placed directly in the region folder."
            )
            self.location_name_input.setReadOnly(True)
            self.location_description_input.setReadOnly(True)
            self._selected_level = 'region'
            self.location_details_widget.setVisible(False)
            if self._selected_region_orig and self._selected_region_orig != "__global__":
                region_folder = os.path.join(
                    self.workflow_data_dir,
                    'resources',
                    'data files',
                    'settings',
                    self._selected_world_orig,
                    self._selected_region_orig
                )
                self.populate_settings(region_folder)
            else:
                world_folder = os.path.join(
                    self.workflow_data_dir,
                    'resources',
                    'data files',
                    'settings',
                    self._selected_world_orig
                )
                self.populate_settings(world_folder)
            return
        self.location_name_input.setReadOnly(False)
        self.location_description_input.setReadOnly(False)
        self._selected_level = 'location'
        self.location_details_widget.setVisible(True)
        location_json_path = self._get_json_path(
            'location',
            self._selected_world_orig,
            self._selected_region_orig,
            self._selected_location_orig
        )
        location_data = self._load_json(location_json_path) if location_json_path else {}
        try:
            self.location_name_input.editingFinished.disconnect()
        except TypeError:
            pass
        try:
            self.location_description_input.textChanged.disconnect()
        except TypeError:
            pass
        self.location_name_input.setText(
            location_data.get('name', self._selected_location_orig.replace('_', ' ').title())
        )
        self.location_description_input.setPlainText(location_data.get('description', ''))
        
        # Reconnect signals
        self.location_name_input.editingFinished.connect(self._save_current_details)
        self.location_description_input.textChanged.connect(self._schedule_description_save)
        self.current_location_features = location_data.get('features', [])
        self._populate_location_features_list()
        self._populate_location_connections()
        default_path_names = ["Large Path (Default)", "Medium Path (Default)", "Small Path (Default)"]
        default_descriptions = {
            "Large Path (Default)": "A wide, well-maintained path suitable for vehicles and heavy traffic.",
            "Medium Path (Default)": "A regular path that can comfortably accommodate foot traffic and small carts.",
            "Small Path (Default)": "A narrow trail or footpath that may be difficult to traverse."
        }
        for name in default_path_names:
            default_desc = default_descriptions.get(name, "")
            self.current_location_path_data_cache[name] = {"name": name, "description": default_desc}
        persisted_paths = location_data.get('paths', [])
        for path_entry in persisted_paths:
            if isinstance(path_entry, dict) and 'name' in path_entry:
                name = path_entry['name']
                desc = path_entry.get('description', '')
                self.current_location_path_data_cache[name] = {"name": name, "description": desc}
        final_path_list_names = list(default_path_names)
        for name in self.current_location_path_data_cache.keys():
            if name not in final_path_list_names:
                final_path_list_names.append(name)
        self.location_paths_list.clear()
        for name in final_path_list_names:
            self.location_paths_list.addItem(name)
        self._is_navigating = False

    def _on_setting_selected(self, current_item, previous_item):
        self._is_navigating = True
        if previous_item and self._selected_setting_orig and self._current_setting_file_path_absolute and hasattr(self, '_current_setting_item') and self._current_setting_item:
            try:
                is_valid = False
                for i in range(self.list3.count()):
                    if self.list3.item(i) is self._current_setting_item:
                        is_valid = True
                        break
                if is_valid:
                    self._save_current_details()
                else:
                    print("Skipping save of previous setting - item is no longer valid")
            except Exception as e:
                print(f"Error saving previous setting details when switching: {e}")
        self._description_save_timer.stop()
        self._selected_level = None
        self._selected_setting_orig = None
        self._current_setting_file_path_absolute = None
        self._current_setting_is_game_version = False
        if hasattr(self, 'connections_content_layout'):
            while self.connections_content_layout.count():
                item = self.connections_content_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        self._connection_desc_edits = {}
        self._clear_variable_rows()
        if current_item is None:
            self.setting_name_input.clear(); self.setting_description_input.clear()
            self.setting_inventory_table.setRowCount(0); self._clear_variable_rows()
            self.actors_in_setting_list.clear()
            self._is_navigating = False
            return
        original_world_name = self._selected_world_orig
        original_region_name = self._selected_region_orig
        original_location_name = self._selected_location_orig
        if not original_world_name:
            self.setting_name_input.clear(); self.setting_description_input.clear()
            self.setting_inventory_table.setRowCount(0); self._clear_variable_rows()
            self.actors_in_setting_list.clear()
            self._is_navigating = False
            return
        item_data = current_item.data(Qt.UserRole)
        if not item_data:
            print("Error: No data associated with selected setting item.")
            self.setting_name_input.clear(); self.setting_description_input.clear()
            self.setting_inventory_table.setRowCount(0); self._clear_variable_rows()
            self.actors_in_setting_list.clear()
            self._is_navigating = False
            return
        original_setting_filename = item_data.get("filename")
        self._current_setting_is_game_version = item_data.get("is_game_version", False)
        self._current_setting_file_path_absolute = item_data.get("path")
        if not self._current_setting_file_path_absolute or not os.path.isfile(self._current_setting_file_path_absolute):
            print(f"  ERROR: Setting file not found at resolved path: {self._current_setting_file_path_absolute}")
            self.setting_name_input.clear(); self.setting_description_input.clear()
            self.setting_inventory_table.setRowCount(0); self._clear_variable_rows()
            self.actors_in_setting_list.clear()
            self._is_navigating = False
            return
        setting_data = self._load_json(self._current_setting_file_path_absolute)
        name_from_json = setting_data.get('name', original_setting_filename.replace('_setting.json', '').replace('_', ' ').title())
        if hasattr(self, 'world_editor_tab') and self.world_editor_tab and original_location_name and original_location_name != "__global__":
            location_display_name = None
            if original_location_name:
                location_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', 
                                        original_world_name, original_region_name, original_location_name)
                location_json_path = os.path.join(location_path, f"{sanitize_path_name(original_location_name)}_location.json")
                if os.path.isfile(location_json_path):
                    location_data = self._load_json(location_json_path)
                    location_display_name = location_data.get('name', original_location_name.replace('_', ' ').title())
                else:
                    location_display_name = original_location_name.replace('_', ' ').title()
            if location_display_name and name_from_json:
                print(f"  Updating World Editor to show setting '{name_from_json}' in location '{location_display_name}'")
                self.world_editor_tab.update_location_from_setting(name_from_json, location_display_name)
        try:
            self.setting_name_input.editingFinished.disconnect()
        except TypeError:
            pass
        self.setting_name_input.setText(name_from_json)
        self._selected_setting_orig = original_setting_filename
        self._selected_level = 'setting'
        self._current_setting_item = current_item
        self.setting_name_input.editingFinished.connect(self._save_current_details)
        description = setting_data.get('description', '')
        self.setting_description_input.blockSignals(True)
        self.setting_description_input.setText(description)
        self.setting_description_input.blockSignals(False)
        self.setting_inventory_table.setRowCount(0)
        inventory = setting_data.get('inventory', [])
        if isinstance(inventory, str):
            inventory = [line.strip() for line in inventory.splitlines() if line.strip()]
        if isinstance(inventory, list):
            self.setting_inventory_table.setRowCount(0)
            for item in inventory:
                if isinstance(item, dict):
                    row = self.setting_inventory_table.rowCount()
                    self.setting_inventory_table.insertRow(row)
                    self.setting_inventory_table.setItem(row, 0, QTableWidgetItem(item.get('name', '')))
                    self.setting_inventory_table.setItem(row, 1, QTableWidgetItem(item.get('quantity', '1')))
                    self.setting_inventory_table.setItem(row, 2, QTableWidgetItem(item.get('owner', '')))
                    self.setting_inventory_table.setItem(row, 3, QTableWidgetItem(item.get('description', '')))
                elif isinstance(item, str):
                    row = self.setting_inventory_table.rowCount()
                    self.setting_inventory_table.insertRow(row)
                    self.setting_inventory_table.setItem(row, 0, QTableWidgetItem(item))
                    self.setting_inventory_table.setItem(row, 1, QTableWidgetItem('1'))
                    self.setting_inventory_table.setItem(row, 2, QTableWidgetItem(''))
                    self.setting_inventory_table.setItem(row, 3, QTableWidgetItem(''))
            self.setting_exterior_checkbox.blockSignals(True)
            is_exterior = bool(setting_data.get('exterior', False))
            self.setting_exterior_checkbox.setChecked(is_exterior)
            self.setting_exterior_checkbox.blockSignals(False)
        is_exterior = self.setting_exterior_checkbox.isChecked()
        has_dot = self._setting_has_map_dot(name_from_json, original_world_name, original_region_name, original_location_name)
        self.visible_section_container.setVisible(is_exterior and has_dot)
        self._populate_actors_in_setting_list(setting_data)
        current_list_text = name_from_json
        if self._current_setting_is_game_version:
            if not current_list_text.endswith(" *"):
                 current_list_text += " *"
        else:
            if current_list_text.endswith(" *"):
                current_list_text = current_list_text[:-2]
        current_item.setText(current_list_text)
        connections = []
        this_setting_name_for_map = name_from_json.strip()
        map_data_file = None
        map_data = None
        dots = []
        lines = []
        if original_location_name and original_location_name != "__global__":
            map_data_file = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings',
                original_world_name, original_region_name, original_location_name, 'location_map_data.json')
        else:
            map_data_file = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings',
                original_world_name, 'world_map_data.json')
        if os.path.isfile(map_data_file):
            try:
                with open(map_data_file, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                dots = map_data.get('dots', [])
                lines = map_data.get('lines', [])
                this_dot_indices = [i for i, d in enumerate(dots)
                                    if len(d) >= 5 and str(d[4]).strip().lower() == this_setting_name_for_map.lower()]
                if this_dot_indices:
                    for this_dot_index in this_dot_indices:
                        for line_idx, line in enumerate(lines):
                            meta = line.get('meta', {})
                            start = meta.get('start', -1)
                            end = meta.get('end', -1)
                            other_index = None
                            if start == this_dot_index:
                                other_index = end
                            elif end == this_dot_index:
                                other_index = start
                            if other_index is not None and 0 <= other_index < len(dots):
                                other_dot = dots[other_index]
                                if len(other_dot) >= 5 and other_dot[3] == 'small' and other_dot[4]:
                                    other_name = str(other_dot[4]).strip()
                                    if other_name and other_name.lower() != this_setting_name_for_map.lower() and other_name not in connections:
                                        connections.append(other_name)
            except Exception as e:
                print(f"Error loading map data for connections: {e}")
        setting_data = self._load_json(self._current_setting_file_path_absolute)
        json_connections = setting_data.get('connections', {})
        if not isinstance(json_connections, dict):
            json_connections = {}
        for json_conn_name in json_connections:
            if json_conn_name not in connections:
                connections.append(json_conn_name)
        connection_descs = json_connections.copy()
        if connections:
            for conn_name in sorted(connections):
                label = QLabel(conn_name)
                label.setObjectName("ConnectionLabel")
                label.setStyleSheet("font-weight: bold; margin-top: 8px;")
                desc_edit = QTextEdit()
                desc_edit.setObjectName("SettingManagerDescInput")
                desc_edit.setMaximumHeight(50)
                desc_edit.setPlaceholderText("Describe this connection...")
                desc_edit.blockSignals(True)
                desc_edit.setText(connection_descs.get(conn_name, ""))
                desc_edit.blockSignals(False)
                desc_edit.textChanged.connect(self._schedule_description_save)
                desc_edit.installEventFilter(self)
                self.connections_content_layout.addWidget(label)
                self.connections_content_layout.addWidget(desc_edit)
                self._connection_desc_edits[conn_name] = desc_edit
        try:
            setting_name_for_map = this_setting_name_for_map
            setting_dot_indices = []
            for i, d in enumerate(dots):
                if len(d) >= 5 and isinstance(d[4], str) and d[4].strip().lower() == setting_name_for_map.lower():
                    setting_dot_indices.append(i)
            if setting_dot_indices:
                for setting_dot_idx in setting_dot_indices:
                    for line_idx, line in enumerate(lines):
                        meta = line.get('meta', {})
                        start_idx = meta.get('start', -1)
                        end_idx = meta.get('end', -1)
                        other_idx = None
                        if start_idx == setting_dot_idx:
                            other_idx = end_idx
                        elif end_idx == setting_dot_idx:
                            other_idx = start_idx
                        if other_idx is not None and 0 <= other_idx < len(dots):
                            other_dot = dots[other_idx]
                            if len(other_dot) >= 5 and (other_dot[3] == 'big' or other_dot[3] == 'medium') and other_dot[4]:
                                location_name = str(other_dot[4]).strip()
                                associated_setting = meta.get('associated_setting', '')
                                if associated_setting and associated_setting.lower() != setting_name_for_map.lower():
                                    if associated_setting not in connections:
                                        label = QLabel(associated_setting)
                                        label.setObjectName("ConnectionLabel")
                                        desc_edit = QTextEdit()
                                        desc_edit.setObjectName("SettingManagerDescInput")
                                        desc_edit.setMaximumHeight(50)
                                        desc_edit.setPlaceholderText(f"Connected via {location_name}...")
                                        desc_edit.blockSignals(True)
                                        desc_edit.setText(connection_descs.get(associated_setting, ""))
                                        desc_edit.blockSignals(False)
                                        desc_edit.textChanged.connect(self._schedule_description_save)
                                        desc_edit.installEventFilter(self)
                                        indirect_label = QLabel(f"(via {location_name})")
                                        indirect_label.setObjectName("IndirectConnectionLabel")
                                        self.connections_content_layout.addWidget(label)
                                        self.connections_content_layout.addWidget(indirect_label)
                                        self.connections_content_layout.addWidget(desc_edit)
                                        self._connection_desc_edits[associated_setting] = desc_edit
                                        connections.append(associated_setting)
        except Exception as e:
            print(f"Error processing setting-to-location connections: {e}")
        variables = setting_data.get('variables', {})
        if isinstance(variables, dict):
            for var_name, var_value in variables.items():
                self._add_variable_row(var_name, str(var_value))
        current_debug_info = f"Last loaded: {datetime.datetime.now().strftime('%H:%M:%S')}"
        if hasattr(self._current_setting_item, 'setToolTip'):
            try:
                self._current_setting_item.setToolTip(current_debug_info)
            except:
                pass
        self._is_navigating = False

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
            print(f"SettingManager: Error reading JSON from {file_path}: {e}")
            return {}
        except Exception as e:
            print(f"SettingManager: Unexpected error reading JSON from {file_path}: {e}")
            return {}

    def _save_json(self, file_path, data):
        if not file_path:
            print("SettingManager: Error - Cannot save JSON, no file path provided.")
            return False
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            print(f"SettingManager: Error writing JSON to {file_path}: {e}")
            return False
        except Exception as e:
            print(f"SettingManager: Unexpected error writing JSON to {file_path}: {e}")
            return False

    def _get_json_path(self, level, world_orig, region_orig=None, location_orig=None, setting_file=None, respect_game_override=False):
        if not world_orig:
            return None
        resource_base_path_parts = [self.workflow_data_dir, 'resources', 'data files', 'settings', world_orig]
        if region_orig: resource_base_path_parts.append(region_orig)
        if location_orig and location_orig != "__global__": resource_base_path_parts.append(location_orig)
        resource_path = os.path.join(*resource_base_path_parts)
        target_filename = None
        if level == 'world':
            target_filename = f"{sanitize_path_name(world_orig)}_world.json"
            resource_path = os.path.join(resource_path, target_filename)
        elif level == 'region' and region_orig:
            target_filename = f"{sanitize_path_name(region_orig)}_region.json"
            resource_path = os.path.join(resource_path, target_filename)
        elif level == 'location' and location_orig:
            target_filename = f"{sanitize_path_name(location_orig)}_location.json"
            resource_path = os.path.join(resource_path, target_filename)
        elif level == 'setting' and setting_file:
            target_filename = setting_file
            resource_path = os.path.join(resource_path, target_filename)
        else:
            return None

        if respect_game_override and target_filename:
            game_path_parts = [self.workflow_data_dir, 'game', 'settings', world_orig]
            if region_orig: game_path_parts.append(region_orig)
            if location_orig: game_path_parts.append(location_orig)
            game_path_parts.append(target_filename)
            game_file_path = os.path.join(*game_path_parts)
            if os.path.isfile(game_file_path):
                return game_file_path
        return resource_path

    def _load_description(self, level, world_orig, region_orig=None, location_orig=None, setting_file=None):
        file_path = self._get_json_path(level, world_orig, region_orig, location_orig, setting_file, respect_game_override=True)
        data = self._load_json(file_path)
        return data.get('description', '')

    def _load_inventory(self, level, world_orig, region_orig=None, location_orig=None, setting_file=None):
        file_path = self._get_json_path(level, world_orig, region_orig, location_orig, setting_file, respect_game_override=True)
        data = self._load_json(file_path)
        return data.get('inventory', '')

    def _schedule_description_save(self):
        self._description_save_timer.start(500)
        
    def _save_exterior_state_immediately(self, state):
        if not self._selected_setting_orig or not self._current_setting_file_path_absolute:
            return
        try:
            current_data = self._load_json(self._current_setting_file_path_absolute)
            if not isinstance(current_data, dict):
                current_data = {}
            current_data['exterior'] = bool(state)
            self._save_json(self._current_setting_file_path_absolute, current_data)
        except Exception as e:
            print(f"Error saving exterior state: {e}")

    def _save_current_details(self):
        if hasattr(self, '_is_navigating') and self._is_navigating:
            return
        level_to_save = self._editing_level if self._editing_level else self._selected_level
        world_orig_to_save = self._editing_world_orig if self._editing_world_orig else self._selected_world_orig
        region_orig_to_save = self._editing_region_orig if self._editing_region_orig else self._selected_region_orig
        location_orig_to_save = self._editing_location_orig if self._editing_location_orig else self._selected_location_orig
        setting_orig_to_save = self._editing_setting_orig if self._editing_setting_orig else self._selected_setting_orig
        if not level_to_save or not world_orig_to_save:
            self._editing_level = None
            return
        json_path = None
        data = {}
        name_input_field = None
        desc_input_field = None
        current_list_widget = None
        original_fs_name = None
        current_list_item = None
        if level_to_save == 'world':
            if not world_orig_to_save:
                self._editing_level = None
                return
            json_path = self._get_json_path('world', world_orig_to_save)
            name_input_field = self.world_name_input
            desc_input_field = self.world_description_input
            current_list_widget = self.list_world
            original_fs_name = sanitize_path_name(world_orig_to_save)
            if current_list_widget and current_list_widget.currentItem() and current_list_widget.currentItem().data(Qt.UserRole) == original_fs_name:
                current_list_item = current_list_widget.currentItem()
            if json_path: data = self._load_json(json_path)
            data['features'] = self.current_world_features
            data['locations'] = {}
            path_list = []
            for path_name, path_data in self.current_world_path_data_cache.items():
                if isinstance(path_data, dict):
                    path_entry = path_data.copy()
                    if 'name' not in path_entry:
                        path_entry['name'] = path_name
                    if 'description' not in path_entry:
                        path_entry['description'] = ""
                    path_list.append(path_entry)
                else:
                    path_list.append({"name": path_name, "description": ""})
            data['paths'] = path_list
        elif level_to_save == 'region':
            if not region_orig_to_save:
                self._editing_level = None
                return
            if region_orig_to_save == "__global__":
                self._editing_level = None
                return
            json_path = self._get_json_path('region', world_orig_to_save, region_orig_to_save)
            name_input_field = self.region_name_input
            desc_input_field = self.region_description_input
            current_list_widget = self.list1
            original_fs_name = sanitize_path_name(region_orig_to_save)
            if current_list_widget and current_list_widget.currentItem() and current_list_widget.currentItem().data(Qt.UserRole) == original_fs_name:
                current_list_item = current_list_widget.currentItem()
            if json_path: data = self._load_json(json_path)
            data['features'] = self.current_location_features
            paths_data = []
            existing_paths = {}
            if 'paths' in data and isinstance(data['paths'], list):
                for path_data in data['paths']:
                    if isinstance(path_data, dict) and 'name' in path_data and 'description' in path_data:
                        existing_paths[path_data['name']] = path_data['description']
            for i in range(self.location_paths_list.count()):
                path_name = self.location_paths_list.item(i).text()
                path_desc = ""
                if path_name == self.location_path_name_input.text():
                    path_desc = self.location_path_desc_input.toPlainText()
                elif path_name in existing_paths:
                    path_desc = existing_paths[path_name]
                paths_data.append({"name": path_name, "description": path_desc})
            data['paths'] = paths_data
        elif level_to_save == 'location':
            if not region_orig_to_save:
                self._editing_level = None; return
            if not location_orig_to_save or location_orig_to_save == "__global__":
                self._editing_level = None; return
            json_path = self._get_json_path('location', world_orig_to_save, region_orig_to_save, location_orig_to_save)
            name_input_field = self.location_name_input
            desc_input_field = self.location_description_input
            current_list_widget = self.list2
            original_fs_name = sanitize_path_name(location_orig_to_save)
            if current_list_widget and current_list_widget.currentItem() and current_list_widget.currentItem().data(Qt.UserRole) == original_fs_name:
                current_list_item = current_list_widget.currentItem()
            if json_path: data = self._load_json(json_path)
            data['features'] = self.current_location_features
            path_list = []
            for path_name, path_data in self.current_location_path_data_cache.items():
                if isinstance(path_data, dict):
                    path_entry = path_data.copy()
                    if 'name' not in path_entry:
                        path_entry['name'] = path_name
                    if 'description' not in path_entry:
                        path_entry['description'] = ""
                    path_list.append(path_entry)
                else:
                    path_list.append({"name": path_name, "description": ""})
            data['paths'] = path_list
        elif level_to_save == 'setting':
            if not setting_orig_to_save:
                print("SettingManager: Cannot save setting, no original setting name.")
                self._editing_level = None; return
            current_list_widget = self.list3
            if not hasattr(self, '_current_setting_item') or not self._current_setting_item:
                self._editing_level = None; return
            item_still_in_list = False
            for i in range(current_list_widget.count()):
                if current_list_widget.item(i) is self._current_setting_item:
                    item_still_in_list = True
                    break
            if not item_still_in_list:
                self._editing_level = None; return
            item_data = self._current_setting_item.data(Qt.UserRole)
            if not isinstance(item_data, dict) or not item_data.get("path") or not item_data.get("filename"):
                self._editing_level = None; return
            json_path = item_data.get("path")
            if not os.path.isfile(json_path):
                self._editing_level = None; return
            name_input_field = self.setting_name_input
            desc_input_field = self.setting_description_input
            original_fs_name = setting_orig_to_save.replace(f'_{level_to_save}.json', '')
            current_list_item = self._current_setting_item
            if json_path: data = self._load_json(json_path)
            else:
                print(f"SettingManager: Error, json_path is None for setting save. Setting: {setting_orig_to_save}")
                self._editing_level = None; return
        else:
            print(f"SettingManager: Unknown level to save: {level_to_save}")
            self._editing_level = None; return
        if not json_path:
            print(f"SettingManager: Could not determine JSON path for saving {level_to_save}.")
            self._editing_level = None; return
        if name_input_field is None or desc_input_field is None:
            print(f"SettingManager: Name or description field not found for level {level_to_save}.")
            self._editing_level = None; return
        if not isinstance(data, dict): data = {}
        new_display_name_from_input = name_input_field.text().strip()
        if level_to_save in ['world', 'region', 'setting'] and not new_display_name_from_input:
            print(f"SettingManager: Cannot save {level_to_save} - no name provided.")
            self._editing_level = None
            return
        new_sanitized_fs_name = sanitize_path_name(new_display_name_from_input)
        needs_rename = (new_sanitized_fs_name != original_fs_name) and original_fs_name
        if level_to_save in ['world', 'region', 'location'] and current_list_item:
            current_item_actual_fs_name = current_list_item.data(Qt.UserRole)
            if current_item_actual_fs_name != original_fs_name:
                original_fs_name = current_item_actual_fs_name
                needs_rename = (new_sanitized_fs_name != original_fs_name)
        if needs_rename:
            old_item_fs_path = ""
            new_item_fs_path = ""
            old_item_json_filename = f"{original_fs_name}_{level_to_save}.json"
            new_item_json_filename = f"{new_sanitized_fs_name}_{level_to_save}.json"
            settings_root = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
            actual_world_folder_name = self._selected_world_orig
            actual_region_folder_name = self._selected_region_orig if self._selected_region_orig and self._selected_region_orig != "__global__" else None
            actual_location_folder_name = self._selected_location_orig if self._selected_location_orig and self._selected_location_orig != "__global__" else None
            if level_to_save == 'world':
                old_item_fs_path = os.path.join(settings_root, original_fs_name)
                new_item_fs_path = os.path.join(settings_root, new_sanitized_fs_name)
            elif level_to_save == 'region':
                if not actual_world_folder_name: self._editing_level = None; return
                old_item_fs_path = os.path.join(settings_root, actual_world_folder_name, original_fs_name)
                new_item_fs_path = os.path.join(settings_root, actual_world_folder_name, new_sanitized_fs_name)
            elif level_to_save == 'location':
                if not actual_world_folder_name: self._editing_level = None; return
                path_parts_old = [settings_root, actual_world_folder_name]
                if actual_region_folder_name: path_parts_old.append(actual_region_folder_name)
                path_parts_old.append(original_fs_name)
                old_item_fs_path = os.path.join(*path_parts_old)
                path_parts_new = [settings_root, actual_world_folder_name]
                if actual_region_folder_name: path_parts_new.append(actual_region_folder_name)
                path_parts_new.append(new_sanitized_fs_name)
                new_item_fs_path = os.path.join(*path_parts_new)
            elif level_to_save == 'setting':
                old_item_fs_path = json_path
                new_item_fs_path = os.path.join(os.path.dirname(json_path), new_item_json_filename)
            if os.path.exists(new_item_fs_path):
                self._editing_level = None
                return
            try:
                if level_to_save in ['world', 'region', 'location']:
                    search_parent_dir = os.path.dirname(old_item_fs_path)
                    target_dir_name = os.path.basename(old_item_fs_path)
                    actual_old_dir_path = self._find_directory_case_insensitive(
                        search_parent_dir, target_dir_name)
                    if not actual_old_dir_path:
                        for possible_parent in [os.path.dirname(search_parent_dir), 
                                               os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')]:
                            if os.path.isdir(possible_parent):
                                actual_old_dir_path = self._find_directory_case_insensitive(
                                    possible_parent, target_dir_name)
                                if actual_old_dir_path:
                                    print(f"Found directory in alternative location: {actual_old_dir_path}")
                                    break
                    old_internal_json_path = None
                    if actual_old_dir_path:
                        old_internal_json_path = self._find_file_case_insensitive(
                            actual_old_dir_path, old_item_json_filename)
                    if old_internal_json_path:
                        print(f"Found internal JSON: {old_internal_json_path}")
                        temp_new_internal_json_path_in_old_folder = os.path.join(
                            os.path.dirname(old_internal_json_path), new_item_json_filename)
                        os.rename(old_internal_json_path, temp_new_internal_json_path_in_old_folder)
                        found_jsons = []
                        if actual_old_dir_path:
                            for file in os.listdir(actual_old_dir_path):
                                file_lower = file.lower()
                                if file_lower.endswith(f"_{level_to_save.lower()}.json"):
                                    found_jsons.append(file)
                                    print(f"  Found potential match: {file}")
                            if found_jsons:
                                selected_json = found_jsons[0]
                                old_internal_json_path = os.path.join(actual_old_dir_path, selected_json)
                                temp_new_internal_json_path_in_old_folder = os.path.join(
                                    actual_old_dir_path, new_item_json_filename)
                                os.rename(old_internal_json_path, temp_new_internal_json_path_in_old_folder)
                    if actual_old_dir_path:
                        os.rename(actual_old_dir_path, new_item_fs_path)
                        print(f"Renamed directory from '{actual_old_dir_path}' to '{new_item_fs_path}'")
                    json_path = os.path.join(new_item_fs_path, new_item_json_filename)
                    if level_to_save == 'location':
                        self._update_references_for_renamed_location(
                            actual_world_folder_name, 
                            actual_region_folder_name,
                            original_fs_name, 
                            new_sanitized_fs_name, 
                            new_display_name_from_input
                        )
                    elif level_to_save == 'region':
                        print(f"Calling _update_references_for_renamed_region for {original_fs_name} -> {new_sanitized_fs_name}")
                        self._update_references_for_renamed_region(
                            actual_world_folder_name,
                            original_fs_name,
                            new_sanitized_fs_name,
                            new_display_name_from_input
                        )
                elif level_to_save == 'setting':
                    search_parent_dir = os.path.dirname(old_item_fs_path)
                    target_file_name = os.path.basename(old_item_fs_path)
                    actual_old_file_path = self._find_file_case_insensitive(
                        search_parent_dir, target_file_name)
                    if not actual_old_file_path:
                        if self._current_setting_file_path_absolute and os.path.isfile(self._current_setting_file_path_absolute):
                            actual_old_file_path = self._current_setting_file_path_absolute
                    old_setting_name = data.get('name', '')
                    os.rename(actual_old_file_path, new_item_fs_path)
                    json_path = new_item_fs_path
                    self._current_setting_file_path_absolute = new_item_fs_path
                    if old_setting_name and new_display_name_from_input and old_setting_name != new_display_name_from_input:
                        self._update_connections_for_renamed_setting(old_setting_name, new_display_name_from_input)
                        if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
                            if hasattr(self.world_editor_tab, 'update_dots_for_renamed_setting'):
                                self.world_editor_tab.update_dots_for_renamed_setting(old_setting_name, new_display_name_from_input)
                if current_list_item:
                    if level_to_save == 'setting':
                        new_user_data_val = new_item_json_filename
                        item_data_dict = current_list_item.data(Qt.UserRole)
                        if isinstance(item_data_dict, dict):
                             item_data_dict['filename'] = new_user_data_val
                             item_data_dict['path'] = json_path
                             current_list_item.setData(Qt.UserRole, item_data_dict)
                    else:
                        new_user_data_val = new_sanitized_fs_name
                        current_list_item.setData(Qt.UserRole, new_user_data_val)
                if level_to_save == 'world': self._selected_world_orig = new_sanitized_fs_name
                elif level_to_save == 'region': self._selected_region_orig = new_sanitized_fs_name
                elif level_to_save == 'location': self._selected_location_orig = new_sanitized_fs_name
                elif level_to_save == 'setting': self._selected_setting_orig = new_item_json_filename
                if self._editing_level == level_to_save:
                    if level_to_save == 'world': self._editing_world_orig = new_sanitized_fs_name
                    elif level_to_save == 'region': self._editing_region_orig = new_sanitized_fs_name
                    elif level_to_save == 'location': self._editing_location_orig = new_sanitized_fs_name
                    elif level_to_save == 'setting': self._editing_setting_orig = new_item_json_filename
                original_fs_name = new_sanitized_fs_name
                if level_to_save == 'setting':
                    map_data_files = []
                    if actual_world_folder_name:
                        base_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', actual_world_folder_name)
                        if actual_region_folder_name:
                            base_path = os.path.join(base_path, actual_region_folder_name)
                        if actual_location_folder_name:
                            base_path = os.path.join(base_path, actual_location_folder_name)
                            map_data_files.append(os.path.join(base_path, 'location_map_data.json'))
                        else:
                            map_data_files.append(os.path.join(base_path, 'world_map_data.json'))
                    for map_data_file in map_data_files:
                        if os.path.isfile(map_data_file):
                            try:
                                with open(map_data_file, 'r', encoding='utf-8') as f:
                                    map_data = json.load(f)
                                dots = map_data.get('dots', [])
                                changed = False
                                for d in dots:
                                    if len(d) >= 5 and isinstance(d[4], str):
                                        if d[4].strip() == original_fs_name or d[4].strip() == old_item_json_filename.replace('_setting.json',''):
                                            d[4] = new_display_name_from_input
                                            changed = True
                                if changed:
                                    map_data['dots'] = dots
                                    with open(map_data_file, 'w', encoding='utf-8') as f:
                                        json.dump(map_data, f, indent=2, ensure_ascii=False)
                            except Exception as e:
                                print(f"[WARN] Failed to update map dot names in {map_data_file}: {e}")
            except OSError as e:
                print(f"Error renaming {level_to_save}: {e}")
                QMessageBox.critical(self, "Rename Error", f"Could not rename {level_to_save}. Error: {e}")
                if 'name' in data: name_input_field.setText(data['name'])
                self._editing_level = None
                return
        data['name'] = new_display_name_from_input
        new_description_from_input = desc_input_field.toPlainText().strip()
        data['description'] = new_description_from_input
        if level_to_save == 'setting':
            inventory_items = []
            for row in range(self.setting_inventory_table.rowCount()):
                item_name = self.setting_inventory_table.item(row, 0)
                quantity = self.setting_inventory_table.item(row, 1)
                owner = self.setting_inventory_table.item(row, 2)
                description = self.setting_inventory_table.item(row, 3)
                
                if item_name and item_name.text().strip():
                    inventory_items.append({
                        'name': item_name.text().strip(),
                        'quantity': quantity.text().strip() if quantity else '1',
                        'owner': owner.text().strip() if owner else '',
                        'description': description.text().strip() if description else ''
                    })
            
            if inventory_items:
                data['inventory'] = inventory_items
            else:
                data.pop('inventory', None)
            variables_data = self._get_variables_data()
            if variables_data:
                data['variables'] = variables_data
            elif 'variables' in data and not variables_data:
                data['variables'] = {}
            if level_to_save == 'setting':
                existing_connections = data.get('connections', {})
                if not isinstance(existing_connections, dict):
                    existing_connections = {}
                if hasattr(self, '_connection_desc_edits'):
                    for conn_name, edit_widget in self._connection_desc_edits.items():
                        desc = edit_widget.toPlainText().strip()
                        if desc:
                            existing_connections[conn_name] = desc
                if existing_connections:
                    data['connections'] = existing_connections
                elif 'connections' in data:
                    del data['connections']
            data['exterior'] = self.setting_exterior_checkbox.isChecked()
            print(f"Successfully saved setting: {new_display_name_from_input} to {json_path}")
        if self._save_json(json_path, data):
            if current_list_item:
                if level_to_save == 'setting':
                    is_game_version_flag = False
                    item_data = current_list_item.data(Qt.UserRole)
                    if isinstance(item_data, dict):
                        is_game_version_flag = item_data.get("is_game_version", False)
                    display_text = new_display_name_from_input
                    if is_game_version_flag:
                        display_text += " *"
                    current_list_item.setText(display_text)
                else:
                    current_list_item.setText(new_display_name_from_input)
            else:
                if level_to_save == 'world' and self.list_world.currentItem() and self.list_world.currentItem().data(Qt.UserRole) == (new_sanitized_fs_name if needs_rename else original_fs_name):
                    self.list_world.currentItem().setText(new_display_name_from_input)
                elif level_to_save == 'region' and self.list1.currentItem() and self.list1.currentItem().data(Qt.UserRole) == (new_sanitized_fs_name if needs_rename else original_fs_name):
                    self.list1.currentItem().setText(new_display_name_from_input)
                elif level_to_save == 'location' and self.list2.currentItem() and self.list2.currentItem().data(Qt.UserRole) == (new_sanitized_fs_name if needs_rename else original_fs_name):
                    self.list2.currentItem().setText(new_display_name_from_input)
                elif level_to_save == 'setting' and self.list3.currentItem():
                    item_data = self.list3.currentItem().data(Qt.UserRole)
                    current_filename = item_data.get('filename') if isinstance(item_data, dict) else None
                    expected_filename = new_item_json_filename if needs_rename else f"{original_fs_name}_{level_to_save}.json"
                    if current_filename == expected_filename:
                        is_game_version_flag = item_data.get("is_game_version", False) if isinstance(item_data, dict) else False
                        display_text = new_display_name_from_input
                        if is_game_version_flag: display_text += " *"
                        self.list3.currentItem().setText(display_text)
        if hasattr(self, '_original_edit_level') and self._original_edit_level is not None:
            self._editing_level = self._original_edit_level
            self._original_edit_level = None
        else:
            self._editing_level = None
        
    def _update_connections_for_renamed_setting(self, old_setting_name, new_setting_name):
        if not self.workflow_data_dir or not old_setting_name or not new_setting_name or old_setting_name == new_setting_name:
            return
        settings_root = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
        if not os.path.isdir(settings_root):
            return
        setting_files_to_check = []
        for world_name in os.listdir(settings_root):
            world_path = os.path.join(settings_root, world_name)
            if not os.path.isdir(world_path):
                continue
            for item_in_world in os.listdir(world_path):
                item_in_world_path = os.path.join(world_path, item_in_world)
                if os.path.isfile(item_in_world_path) and item_in_world.lower().endswith('_setting.json'):
                    setting_files_to_check.append(item_in_world_path)
                elif os.path.isdir(item_in_world_path):
                    for sub_item_in_world_dir in os.listdir(item_in_world_path):
                        sub_item_path = os.path.join(item_in_world_path, sub_item_in_world_dir)
                        if os.path.isfile(sub_item_path) and sub_item_in_world_dir.lower().endswith('_setting.json'):
                             if sub_item_path not in setting_files_to_check: setting_files_to_check.append(sub_item_path)
                        elif os.path.isdir(sub_item_path):
                             for file_in_loc_dir in os.listdir(sub_item_path):
                                file_in_loc_path = os.path.join(sub_item_path, file_in_loc_dir)
                                if os.path.isfile(file_in_loc_path) and file_in_loc_dir.lower().endswith('_setting.json'):
                                    if file_in_loc_path not in setting_files_to_check: setting_files_to_check.append(file_in_loc_path)
        updated_count = 0
        sanitized_new_name_for_comparison = f"{sanitize_path_name(new_setting_name)}_setting.json"
        for setting_file_path in setting_files_to_check:
            try:
                if os.path.basename(setting_file_path) == sanitized_new_name_for_comparison:
                    pass
                setting_data = self._load_json(setting_file_path)
                if not setting_data or not isinstance(setting_data, dict):
                    continue
                if setting_data.get('name') == new_setting_name:
                    continue
                connections_list = setting_data.get('connections')
                modified_this_file = False
                if isinstance(connections_list, list):
                    for connection_obj in connections_list:
                        if isinstance(connection_obj, dict) and \
                           connection_obj.get("connected_setting_name") == old_setting_name:
                            connection_obj["connected_setting_name"] = new_setting_name
                            modified_this_file = True
                elif isinstance(connections_list, dict):
                    if old_setting_name in connections_list:
                        connection_desc = connections_list[old_setting_name]
                        del connections_list[old_setting_name]
                        connections_list[new_setting_name] = connection_desc
                        modified_this_file = True
                if modified_this_file:
                    setting_data['connections'] = connections_list
                    with open(setting_file_path, 'w', encoding='utf-8') as f:
                        json.dump(setting_data, f, indent=2, ensure_ascii=False)
                    updated_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to update connection in {setting_file_path}: {e}")
                import traceback
                traceback.print_exc()

    def _update_references_for_renamed_location(self, world_name, region_name, old_location_fs_name, new_location_fs_name, new_location_display_name):
        settings_base_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
        world_path = os.path.join(settings_base_path, world_name)
        for w_name in os.listdir(settings_base_path):
            w_path = os.path.join(settings_base_path, w_name)
            if not os.path.isdir(w_path):
                continue
            for item_name_under_world in os.listdir(w_path):
                path_item_under_world = os.path.join(w_path, item_name_under_world)
                if not os.path.isdir(path_item_under_world) or item_name_under_world.lower() == 'resources':
                    continue
                if os.path.exists(os.path.join(path_item_under_world, f"{sanitize_path_name(item_name_under_world)}_location.json")):
                    location_folders_to_scan_paths = {item_name_under_world: path_item_under_world}
                else:
                    location_folders_to_scan_paths = {}
                    for loc_name_under_region in os.listdir(path_item_under_world):
                        path_loc_under_region = os.path.join(path_item_under_world, loc_name_under_region)
                        if os.path.isdir(path_loc_under_region):
                            if os.path.exists(os.path.join(path_loc_under_region, f"{sanitize_path_name(loc_name_under_region)}_location.json")):
                                location_folders_to_scan_paths[loc_name_under_region] = path_loc_under_region
                for l_fs_name, current_l_path in location_folders_to_scan_paths.items():
                    if not os.path.isdir(current_l_path):
                        continue
                    for setting_file_name in os.listdir(current_l_path):
                        if setting_file_name.endswith("_setting.json"):
                            setting_file_path = os.path.join(current_l_path, setting_file_name)
                            setting_data = self._load_json(setting_file_path)
                            if not setting_data:
                                continue
                            made_change_to_setting = False
                            if "connections" in setting_data and isinstance(setting_data["connections"], list):
                                new_connections = []
                                for conn in setting_data["connections"]:
                                    if isinstance(conn, dict) and \
                                       conn.get("world") == world_name and \
                                       conn.get("region") == region_name and \
                                       conn.get("location") == old_location_fs_name:
                                       
                                        print(f"[Rename Location] Updating connection in '{setting_file_path}': Target location '{old_location_fs_name}' -> '{new_location_fs_name}'")
                                        conn["location"] = new_location_fs_name
                                        made_change_to_setting = True
                                    new_connections.append(conn)
                                if made_change_to_setting:
                                    setting_data["connections"] = new_connections
        world_map_data_file = os.path.join(world_path, "world_map_data.json")
        if os.path.isfile(world_map_data_file):
            map_data = self._load_json(world_map_data_file)
            if not map_data:
                print(f"[Rename Location] [ERROR] Could not load world_map_data.json for {world_name}")
                return
            made_change_to_map = False
            if "dots" in map_data and isinstance(map_data["dots"], list):
                new_dots = []
                for dot_info in map_data["dots"]:
                    if isinstance(dot_info, list) and len(dot_info) >= 6:
                        dot_type = dot_info[3]
                        linked_name = dot_info[4]
                        dot_placement_region_name = dot_info[5]
                        if dot_type in ["big", "medium"] and linked_name and \
                           (isinstance(linked_name, str) and sanitize_path_name(linked_name.strip()) == old_location_fs_name) and \
                           dot_placement_region_name == region_name:
                            print(f"[Rename Location] Updating dot (Location type) in world_map_data.json: '{linked_name}' ({old_location_fs_name}) -> '{new_location_display_name}' ({new_location_fs_name})")
                            dot_info[4] = new_location_display_name 
                            made_change_to_map = True
                    new_dots.append(dot_info)
                if made_change_to_map:
                    map_data["dots"] = new_dots
            if made_change_to_map:
                if not self._save_json(world_map_data_file, map_data):
                    print(f"[Rename Location] [ERROR] Failed to save updated world_map_data.json for {world_name}")

    def _update_references_for_renamed_region(self, world_name, old_region_fs_name, new_region_fs_name, new_region_display_name):
        settings_base_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
        world_path = os.path.join(settings_base_path, world_name)
        world_map_data_file = os.path.join(world_path, "world_map_data.json")
        if os.path.isfile(world_map_data_file):
            map_data = self._load_json(world_map_data_file)
            if not map_data:
                print(f"[Rename Region] [ERROR] Could not load world_map_data.json for {world_name}")
            else:
                if "dots" in map_data and isinstance(map_data["dots"], list):
                    for dot_info in map_data["dots"]:
                        if isinstance(dot_info, list) and len(dot_info) >= 6:
                            dot_placement_region_name = dot_info[5]
                            if dot_placement_region_name == old_region_fs_name:
                                dot_info[5] = new_region_display_name
        for w_name in os.listdir(settings_base_path):
            w_path = os.path.join(settings_base_path, w_name)
            if not os.path.isdir(w_path):
                continue
            for item_name in os.listdir(w_path):
                item_path = os.path.join(w_path, item_name)
                if not os.path.isdir(item_path) or item_name.lower() == 'resources':
                    continue
                if w_name == world_name and item_name == new_region_fs_name:
                    continue
                for loc_name in os.listdir(item_path):
                    loc_path = os.path.join(item_path, loc_name)
                    if not os.path.isdir(loc_path):
                        continue
                    for setting_file in os.listdir(loc_path):
                        if not setting_file.endswith('_setting.json'):
                            continue
                        setting_path = os.path.join(loc_path, setting_file)
                        setting_data = self._load_json(setting_path)
                        if not setting_data:
                            continue
                        if 'region' in setting_data and setting_data['region'] == old_region_fs_name:
                            setting_data['region'] = new_region_display_name
                        if 'connections' in setting_data and isinstance(setting_data['connections'], dict):
                            for conn_key, conn_data in setting_data['connections'].items():
                                if isinstance(conn_data, dict) and conn_data.get('region') == old_region_fs_name:
                                    conn_data['region'] = new_region_display_name
        self._rename_region_mask(world_name, old_region_fs_name, new_region_fs_name)
        if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
            if hasattr(self.world_editor_tab, 'update_for_renamed_region'):
                self.world_editor_tab.update_for_renamed_region(old_region_fs_name, new_region_display_name)

    def _rename_region_mask(self, world_name, old_region_fs_name, new_region_fs_name):
        region_resources_dir = os.path.join(
            self.workflow_data_dir, 
            'resources', 'data files', 'settings', 
            world_name, 'resources', 'regions'
        )
        if not os.path.isdir(region_resources_dir):
            return False
        old_mask_filename = f"{old_region_fs_name.lower()}_region_mask.png"
        new_mask_filename = f"{new_region_fs_name.lower()}_region_mask.png"
        old_mask_path = os.path.join(region_resources_dir, old_mask_filename)
        new_mask_path = os.path.join(region_resources_dir, new_mask_filename)
        if os.path.isfile(old_mask_path):
            try:
                os.rename(old_mask_path, new_mask_path)
                print(f"[Rename Region] Successfully renamed mask file from '{old_mask_filename}' to '{new_mask_filename}'")
                return True
            except Exception as e:
                print(f"[Rename Region] [ERROR] Failed to rename region mask file: {e}")
                return False
        else:
            print(f"[Rename Region] [WARN] Region mask file not found: {old_mask_path}")
            return False

    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        base_color = theme_colors.get('base_color', '#FFFFFF')
        bg_color = theme_colors.get('bg_color', '#2B2B2B')
        
        # Theme the scroll area
        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    background-color: {bg_color};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: {bg_color};
                    width: 12px;
                    margin: 0px;
                }}
                QScrollBar::handle:vertical {{
                    background: {base_color};
                    min-height: 20px;
                    border-radius: 6px;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                    height: 0px;
                }}
                QScrollBar:horizontal {{
                    background: {bg_color};
                    height: 12px;
                    margin: 0px;
                }}
                QScrollBar::handle:horizontal {{
                    background: {base_color};
                    min-width: 20px;
                    border-radius: 6px;
                }}
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                    background: none;
                    width: 0px;
                }}
            """)
        

        
        stylesheet = f"""
        QLabel#ConnectionLabel {{
            color: {base_color};
            font-weight: bold; 
            margin-top: 8px;
        }}
        
        QLabel#IndirectConnectionLabel {{
            color: {base_color};
            font-style: italic;
            font-size: 8pt;
        }}
        """
        if hasattr(self, 'connections_content_layout'):
            for i in range(self.connections_content_layout.count()):
                item = self.connections_content_layout.itemAt(i)
                if item and item.widget():
                    if isinstance(item.widget(), QLabel):
                        item.widget().setStyleSheet(stylesheet)
        if hasattr(self, 'location_connections_layout'):
            for i in range(self.location_connections_layout.count()):
                item = self.location_connections_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if widget.objectName() == "ConnectionListItem":
                        for child in widget.findChildren(QLabel):
                            if child.objectName() == "ConnectionLabel" or child.objectName() == "IndirectConnectionLabel":
                                child.setStyleSheet(stylesheet)
        # Update button styling
        if hasattr(self, 'setting_details_btn'):
            self.setting_details_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {base_color};
                    color: #000000;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:checked {{
                    background-color: {base_color};
                    color: #000000;
                }}
                QPushButton:!checked {{
                    background-color: transparent;
                    color: {base_color};
                    border: 1px solid {base_color};
                }}
            """)
        
        if hasattr(self, 'world_editor_btn'):
            self.world_editor_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {base_color};
                    border: 1px solid {base_color};
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:checked {{
                    background-color: {base_color};
                    color: #000000;
                }}
                QPushButton:!checked {{
                    background-color: transparent;
                    color: {base_color};
                    border: 1px solid {base_color};
                }}
            """)
        
        if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
            self.world_editor_tab.update_theme(theme_colors)
        else:
            print("Warning: world_editor_tab not found during theme update.")

    def eventFilter(self, obj, event):
        if event.type() == event.FocusIn:
            if obj == self.world_name_input or obj == self.world_description_input:
                self._editing_level = 'world'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = None
                self._editing_location_orig = None
                self._editing_setting_orig = None
            elif obj == self.region_name_input or obj == self.region_description_input:
                self._editing_level = 'region'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = self._selected_region_orig
                self._editing_location_orig = None
                self._editing_setting_orig = None
            elif obj == self.location_name_input or obj == self.location_description_input:
                self._editing_level = 'location'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = self._selected_region_orig
                self._editing_location_orig = self._selected_location_orig
                self._editing_setting_orig = None
            elif obj == self.setting_name_input or obj == self.setting_description_input:
                self._editing_level = 'setting'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = self._selected_region_orig
                self._editing_location_orig = self._selected_location_orig
                self._editing_setting_orig = self._selected_setting_orig
            elif obj.objectName() == "SettingManagerVarNameInput" or obj.objectName() == "SettingManagerVarValueInput":
                self._editing_level = 'setting'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = self._selected_region_orig
                self._editing_location_orig = self._selected_location_orig
                self._editing_setting_orig = self._selected_setting_orig
                parent_widget = obj.parentWidget()
                if parent_widget and parent_widget.objectName() == "VariableRow":
                    self._selected_variable_row_widget = parent_widget
            elif hasattr(self, '_connection_desc_edits') and obj in self._connection_desc_edits.values():
                self._editing_level = 'setting'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = self._selected_region_orig
                self._editing_location_orig = self._selected_location_orig
                self._editing_setting_orig = self._selected_setting_orig
        elif event.type() == event.MouseButtonRelease and obj.objectName() == "VariableRow":
            self._selected_variable_row_widget = obj
        return super().eventFilter(obj, event)

    def _filter_world_list(self, text):
        text = text.lower()
        for i in range(self.list_world.count()):
            item = self.list_world.item(i)
            item.setHidden(text not in item.text().lower())

    def _filter_region_list(self, text):
        text = text.lower()
        for i in range(self.list1.count()):
            item = self.list1.item(i)
            item.setHidden(text not in item.text().lower())

    def _filter_location_list(self, text):
        text = text.lower()
        for i in range(self.list2.count()):
            item = self.list2.item(i)
            item.setHidden(text not in item.text().lower())

    def _filter_setting_list(self, text):
        text = text.lower()
        for i in range(self.list3.count()):
            item = self.list3.item(i)
            item.setHidden(text not in item.text().lower())

    def _add_item(self, level, parent_path_args=None):
        item_type_name = level.capitalize()
        title = f"Add New {item_type_name}"
        label = f"Enter name for the new {item_type_name}:"
        new_name, ok = QInputDialog.getText(self, title, label)
        if not ok or not new_name.strip():
            print(f"Add {item_type_name} cancelled.")
            return
        new_name = new_name.strip()
        sanitized_name = sanitize_path_name(new_name)
        base_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
        if parent_path_args:
            base_path = os.path.join(base_path, *parent_path_args)
        if level == 'location' and parent_path_args and len(parent_path_args) == 1:
            new_item_path = os.path.join(base_path, sanitized_name)
        else:
            new_item_path = os.path.join(base_path, sanitized_name if level != 'setting' else f"{sanitized_name}_setting.json")
        if level == 'setting':
            if os.path.isfile(new_item_path):
                 QMessageBox.warning(self, "Error", f"A setting file named '{os.path.basename(new_item_path)}' already exists.")
                 return
        elif os.path.exists(new_item_path):
            QMessageBox.warning(self, "Error", f"An item directory named '{sanitized_name}' already exists.")
            return
        if level in ('world', 'region', 'location'):
            item_dir_path = new_item_path
            try:
                os.makedirs(item_dir_path, exist_ok=True)
                json_filename = f"{sanitized_name}_{level}.json"
                json_path = os.path.join(item_dir_path, json_filename)
                default_data = {"name": new_name, "description": ""}
                if level == 'location':
                    default_data["exterior"] = True
                if not self._save_json(json_path, default_data):
                    raise IOError(f"Failed to save default JSON to {json_path}")
            except (OSError, IOError) as e:
                QMessageBox.critical(self, "Error", f"Could not create {item_type_name}. Error: {e}")
                if os.path.exists(item_dir_path) and not os.listdir(item_dir_path):
                    try: os.rmdir(item_dir_path)
                    except OSError: pass
                return
        elif level == 'setting':
            actual_location_dir = self._get_actual_location_path_for_setting_creation(
                self._selected_world_orig,
                self._selected_region_orig,
                self._selected_location_orig
            )
            if not actual_location_dir:
                QMessageBox.critical(self, "Error", "Could not determine the correct directory to create the setting.")
                return None
            setting_filename = f"{sanitized_name}_setting.json"
            item_file_path = os.path.join(actual_location_dir, setting_filename)
            if os.path.isfile(item_file_path):
                 QMessageBox.warning(self, "Error", f"A setting file named '{setting_filename}' already exists in '{os.path.basename(actual_location_dir)}'.")
                 return None
            try:
                os.makedirs(actual_location_dir, exist_ok=True)
                default_data = {"name": new_name, "description": "", "inventory": ""}
                if not self._save_json(item_file_path, default_data):
                    raise IOError(f"Failed to save setting JSON to {item_file_path}")
            except (OSError, IOError) as e:
                print(f"Error creating Setting: {e}")
                QMessageBox.critical(self, "Error", f"Could not create Setting. Error: {e}")
                return None
        target_list = None
        data_to_match = None
        item_data_to_match = None
        if level == 'world':
            self.populate_worlds()
            target_list = self.list_world
            data_to_match = sanitized_name
        elif level == 'region' and parent_path_args:
            world_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0])
            self.populate_regions(world_path)
            target_list = self.list1
            data_to_match = sanitized_name
        elif level == 'location' and parent_path_args:
            if len(parent_path_args) == 1:
                world_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0])
                self.populate_locations(world_path)
            elif len(parent_path_args) > 1:
                region_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', *parent_path_args)
                self.populate_locations(region_path)
            else:
                return
            target_list = self.list2
            data_to_match = sanitized_name
        elif level == 'setting' and parent_path_args:
            is_global_location = (len(parent_path_args) == 1)
            if is_global_location:
                location_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0])
            else:
                location_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', *parent_path_args)
            self.populate_settings(location_path)
            target_list = self.list3
            data_to_match = f"{sanitized_name}_setting.json"
        else:
            return
        if target_list is not None:
            for i in range(target_list.count()):
                item = target_list.item(i)
                if level == 'setting' and isinstance(item.data(Qt.UserRole), dict) and item_data_to_match:
                    if item.data(Qt.UserRole).get('filename') == item_data_to_match.get('filename'):
                        target_list.setCurrentItem(item)
                        break
                elif data_to_match and item.data(Qt.UserRole) == data_to_match:
                    target_list.setCurrentItem(item)
                    break
        if level == 'location' and hasattr(self, 'world_editor_tab') and self.world_editor_tab:
            self.world_editor_tab.set_location(new_name)
        if level == 'world':
            world_dir_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', sanitized_name)
            self._create_default_region_in(world_dir_path)
        elif level == 'region':
            region_dir_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0], sanitized_name)
            self._create_default_location_in(region_dir_path)
        elif level == 'location':
            if len(parent_path_args) == 1:
                location_dir_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0], sanitized_name)
            else:
                location_dir_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0], parent_path_args[1], sanitized_name)
            self._create_default_setting_in(location_dir_path)
        if level == 'world':
            self.populate_worlds()
            target_list = self.list_world
            data_to_match = sanitized_name
            for i in range(target_list.count()):
                item = target_list.item(i)
                if item.data(Qt.UserRole) == data_to_match:
                    target_list.setCurrentItem(item)
                    break
        elif level == 'region' and parent_path_args:
            world_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0])
            self.populate_regions(world_path)
            target_list = self.list1
            data_to_match = sanitized_name
            for i in range(target_list.count()):
                item = target_list.item(i)
                if item.data(Qt.UserRole) == data_to_match:
                    target_list.setCurrentItem(item)
                    break
        elif level == 'location' and parent_path_args:
            if len(parent_path_args) == 1:
                world_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0])
                self.populate_locations(world_path)
            elif len(parent_path_args) > 1:
                region_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', *parent_path_args)
                self.populate_locations(region_path)
            target_list = self.list2
            data_to_match = sanitized_name
            for i in range(target_list.count()):
                item = target_list.item(i)
                if item.data(Qt.UserRole) == data_to_match:
                    target_list.setCurrentItem(item)
                    break
        elif level == 'setting' and parent_path_args:
            is_global_location = (len(parent_path_args) == 1)
            if is_global_location:
                location_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', parent_path_args[0])
            else:
                location_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', *parent_path_args)
            self.populate_settings(location_path)
            target_list = self.list3
            data_to_match = f"{sanitized_name}_setting.json"
            for i in range(target_list.count()):
                item = target_list.item(i)
                item_data = item.data(Qt.UserRole)
                if isinstance(item_data, dict) and item_data.get('filename') == data_to_match:
                    target_list.setCurrentItem(item)
                    break
        if target_list is not None and level != 'setting':
            for i in range(target_list.count()):
                item = target_list.item(i)
                if data_to_match and item.data(Qt.UserRole) == data_to_match:
                    target_list.setCurrentItem(item)
                    break
        elif level != 'setting':
            print(f"[WARN _add_item] target_list was None after repopulation for level '{level}'. Cannot select new item.")
            
        # Play add sound
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None

    def _remove_item(self, level, list_widget, requires_parent=False):
        current_item = list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Needed", f"Please select a {level} to remove.")
            return
        item_name = current_item.text()
        original_name_data = current_item.data(Qt.UserRole)
        parent_path_args = []
        if level == 'region':
            if self._selected_world_orig: parent_path_args.append(self._selected_world_orig)
        elif level == 'location':
            if self._selected_world_orig: parent_path_args.append(self._selected_world_orig)
            if self._selected_region_orig: parent_path_args.append(self._selected_region_orig)
        elif level == 'setting':
            if self._selected_world_orig: parent_path_args.append(self._selected_world_orig)
            if self._selected_region_orig: parent_path_args.append(self._selected_region_orig)
            if self._selected_location_orig: parent_path_args.append(self._selected_location_orig)
        if requires_parent and not parent_path_args:
             QMessageBox.critical(self, "Error", f"Cannot determine parent path to remove {level}.")
             return
        reply = QMessageBox.question(self, f"Confirm Remove",
                                   f"Are you sure you want to remove the {level} '{item_name}'?\nThis will permanently delete its directory and all contents (if applicable).",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        base_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', *parent_path_args)
        path_to_delete = os.path.join(base_path, original_name_data)
        try:
            if level in ('world', 'region', 'location'):
                if os.path.isdir(path_to_delete):
                    print(f"Removing directory: {path_to_delete}")
                    shutil.rmtree(path_to_delete)
                else:
                    print(f"Warning: Directory to remove not found: {path_to_delete}")
            elif level == 'setting':
                if os.path.isfile(path_to_delete):
                    print(f"Removing file: {path_to_delete}")
                    os.remove(path_to_delete)
                else:
                    print(f"Warning: File to remove not found: {path_to_delete}")
            row = list_widget.row(current_item)
            list_widget.takeItem(row)
            if self._editing_level == level:
                 if level == 'world': self.world_name_input.clear(); self.world_description_input.clear()
                 elif level == 'region': self.region_name_input.clear(); self.region_description_input.clear()
                 elif level == 'location': self.location_name_input.clear(); self.location_description_input.clear()
                 elif level == 'setting': self.setting_name_input.clear(); self.setting_description_input.clear(); self.setting_inventory_table.setRowCount(0)
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not remove {level} '{item_name}'. Error: {e}")
            return
        if list_widget.count() > 0:
            new_row_to_select = row
            if new_row_to_select >= list_widget.count():
                new_row_to_select = list_widget.count() - 1
            if new_row_to_select >= 0:
                list_widget.setCurrentItem(list_widget.item(new_row_to_select))
            elif list_widget.count() > 0:
                list_widget.setCurrentItem(list_widget.item(0))
        else:
            if level == 'world':
                self.world_name_input.clear(); self.world_description_input.clear()
                self.world_features_list.clear(); self.world_feature_name_input.clear(); self.world_feature_desc_input.clear()
                self.current_world_features = []
                self.world_paths_list.clear(); self.world_path_name_input.clear(); self.world_path_desc_input.clear()
                self.current_world_path_data_cache.clear()
                self.list1.clear(); self.list2.clear(); self.list3.clear()
                self.region_name_input.clear(); self.region_description_input.clear()
                self.location_name_input.clear(); self.location_description_input.clear()
                self.location_features_list.clear(); self.location_feature_name_input.clear(); self.location_feature_desc_input.clear()
                self.current_location_features = []
                self.location_paths_list.clear(); self.location_path_name_input.clear(); self.location_path_desc_input.clear()
                self.current_location_path_data_cache.clear()
                self.setting_name_input.clear(); self.setting_description_input.clear(); self.setting_inventory_table.setRowCount(0); self._clear_variable_rows(); self.actors_in_setting_list.clear()
                self._clear_connections_ui()
            elif level == 'region':
                self.region_name_input.clear(); self.region_description_input.clear()
                self.list2.clear(); self.list3.clear()
                self.location_name_input.clear(); self.location_description_input.clear()
                self.location_features_list.clear(); self.location_feature_name_input.clear(); self.location_feature_desc_input.clear()
                self.current_location_features = []
                self.location_paths_list.clear(); self.location_path_name_input.clear(); self.location_path_desc_input.clear()
                self.current_location_path_data_cache.clear()
                self.setting_name_input.clear(); self.setting_description_input.clear(); self.setting_inventory_table.setRowCount(0); self._clear_variable_rows(); self.actors_in_setting_list.clear()
                self._clear_connections_ui()
            elif level == 'location':
                self.location_name_input.clear(); self.location_description_input.clear()
                self.location_features_list.clear(); self.location_feature_name_input.clear(); self.location_feature_desc_input.clear()
                self.current_location_features = []
                self.location_paths_list.clear(); self.location_path_name_input.clear(); self.location_path_desc_input.clear()
                self.current_location_path_data_cache.clear()
                self.list3.clear()
                self.setting_name_input.clear(); self.setting_description_input.clear(); self.setting_inventory_table.setRowCount(0); self._clear_variable_rows(); self.actors_in_setting_list.clear()
                self._clear_connections_ui()
            elif level == 'setting':
                self.setting_name_input.clear(); self.setting_description_input.clear(); self.setting_inventory_table.setRowCount(0); self._clear_variable_rows(); self.actors_in_setting_list.clear()
                self._clear_connections_ui()
                self.setting_exterior_checkbox.setChecked(False)
                self.visible_section_container.setVisible(False)
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
            try:
                main_ui.delete_rule_sound.play()
            except Exception:
                main_ui.delete_rule_sound = None

    def _add_world(self):
        self._add_item('world')

    def _remove_world(self):
        self._remove_item('world', self.list_world)

    def _add_region(self):
        if not self._selected_world_orig:
            QMessageBox.warning(self, "Selection Needed", "Please select a World first.")
            return
        self._add_item('region', parent_path_args=[self._selected_world_orig])

    def _remove_region(self):
        current_item = self.list1.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Needed", "Please select a Region to remove.")
            return
        if current_item.text() == "NONE" or current_item.data(Qt.UserRole) == "__global__":
            QMessageBox.warning(self, "Cannot Remove", "The 'NONE' region cannot be deleted as it represents global settings.")
            return
        self._remove_item('region', self.list1, requires_parent=True)

    def _add_location(self):
        if not self._selected_world_orig:
            QMessageBox.warning(self, "Selection Needed", "Please select a World first.")
            return
        parent_path_args = [self._selected_world_orig]
        if self._selected_region_orig and self._selected_region_orig != "__global__":
            parent_path_args.append(self._selected_region_orig)
        self._add_item('location', parent_path_args=parent_path_args)

    def _remove_location(self):
        current_item = self.list2.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Needed", "Please select a Location to remove.")
            return
        if current_item.text() == "NONE" or current_item.data(Qt.UserRole) == "__global__":
            QMessageBox.warning(self, "Cannot Remove", "The 'NONE' location cannot be deleted as it represents global settings.")
            return
        self._remove_item('location', self.list2, requires_parent=True)

    def _add_setting(self):
        if not self._selected_world_orig:
            QMessageBox.warning(self, "Selection Needed", "Please select a World first.")
            return
        parent_path_args = [self._selected_world_orig]
        if self._selected_region_orig and self._selected_region_orig != "__global__":
            parent_path_args.append(self._selected_region_orig)
            if self._selected_location_orig and self._selected_location_orig != "__global__":
                parent_path_args.append(self._selected_location_orig)
        created_setting_info = self._add_item('setting', parent_path_args=parent_path_args)
        if created_setting_info and isinstance(created_setting_info, dict):
            actual_location_dir = created_setting_info.get("path")
            new_setting_filename = created_setting_info.get("filename")
            if actual_location_dir and new_setting_filename:
                self.populate_settings(actual_location_dir)
                for i in range(self.list3.count()):
                    item = self.list3.item(i)
                    item_data = item.data(Qt.UserRole)
                    if isinstance(item_data, dict) and item_data.get('filename') == new_setting_filename:
                        self.list3.setCurrentItem(item)
                        break

    def _remove_setting(self):
        current_item = self.list3.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Needed", "Please select a Setting to remove.")
            return
        item_name = current_item.text()
        item_data = current_item.data(Qt.UserRole)
        if isinstance(item_data, dict):
            setting_filename = item_data.get('filename')
        else:
            setting_filename = item_data
        if not setting_filename:
            QMessageBox.warning(self, "Error", f"No filename found for setting '{item_name}'.")
            return
        parent_path_args = []
        if self._selected_world_orig and self._selected_world_orig != "__global__":
            parent_path_args.append(self._selected_world_orig)
            if self._selected_region_orig and self._selected_region_orig != "__global__":
                parent_path_args.append(self._selected_region_orig)
                if self._selected_location_orig and self._selected_location_orig != "__global__":
                    parent_path_args.append(self._selected_location_orig)
        if not parent_path_args:
            QMessageBox.warning(self, "Error", "Cannot determine the setting's location.")
            return
        if self.workflow_data_dir is None:
            QMessageBox.critical(self, "Error", "Workflow data directory is not set.")
            return
        base_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', *parent_path_args)
        setting_path = os.path.join(base_path, setting_filename)
        if not os.path.exists(setting_path):
            QMessageBox.warning(self, "File Not Found", f"Setting file not found at: {setting_path}")
            return
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to delete the setting '{item_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                old_setting_name = item_name
                old_location_name = None
                if self._selected_location_orig and self._selected_location_orig != "__global__":
                    location_json_path = self._get_json_path(
                        'location',
                        self._selected_world_orig,
                        self._selected_region_orig,
                        self._selected_location_orig
                    )
                    location_data = self._load_json(location_json_path) if location_json_path else {}
                    old_location_name = location_data.get('name', self._selected_location_orig.replace('_', ' ').title())
                os.remove(setting_path)
                self._selected_setting_orig = None
                self.setting_name_input.clear()
                self.setting_description_input.clear()
                self.setting_inventory_table.setRowCount(0)
                self._clear_variable_rows()
                self.actors_in_setting_list.clear()
                self._clear_connections_ui()
                self.setting_exterior_checkbox.setChecked(False)
                self.visible_section_container.setVisible(False)
                if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
                    self.world_editor_tab.settingAddedOrRemoved.emit()
                    if old_location_name and self._selected_location_orig != "__global__":
                        self.world_editor_tab.set_location(old_location_name)
                self.populate_settings(base_path)
                
                # Play delete sound
                main_ui = self._get_main_ui()
                if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                    try:
                        main_ui.delete_rule_sound.play()
                    except Exception:
                        main_ui.delete_rule_sound = None
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete setting file: {e}")

    def _create_default_region_in(self, world_path):
        default_region_display = "Default Region"
        default_region_sanitized = sanitize_path_name(default_region_display)
        region_dir = os.path.join(world_path, default_region_sanitized)
        region_json_path = os.path.join(region_dir, f"{default_region_sanitized}_region.json")
        existing_regions = []
        if os.path.isdir(world_path):
            existing_regions = [d for d in os.listdir(world_path) 
                               if os.path.isdir(os.path.join(world_path, d))]
            for region in existing_regions:
                region_path = os.path.join(world_path, region)
                region_json = os.path.join(region_path, f"{region}_region.json")
                if os.path.isfile(region_json):
                    try:
                        data = self._load_json(region_json)
                        if data.get('name', '').lower() == default_region_display.lower():
                            return
                    except Exception as e:
                        print(f"    Error checking region JSON {region_json}: {e}")
        try:
            if not os.path.isdir(region_dir):
                os.makedirs(region_dir, exist_ok=True)
                if not os.path.isfile(region_json_path):
                    self._save_json(region_json_path, {"name": default_region_display, "description": "Default starting region."})
                self._create_default_location_in(region_dir)
        except (OSError, IOError) as e:
            print(f"  ERROR: Could not create default region structure in {world_path}: {e}")

    def _create_default_location_in(self, region_path):
        default_location_display = "Default Location"
        default_location_sanitized = sanitize_path_name(default_location_display)
        location_dir = os.path.join(region_path, default_location_sanitized)
        location_json_path = os.path.join(location_dir, f"{default_location_sanitized}_location.json")
        try:
            if not os.path.isdir(location_dir):
                os.makedirs(location_dir, exist_ok=True)
                if not os.path.isfile(location_json_path):
                    self._save_json(location_json_path, {
                        "name": default_location_display, 
                        "description": "Default starting location.",
                        "exterior": True
                    }) 
                self._create_default_setting_in(location_dir)
        except (OSError, IOError) as e:
             print(f"    ERROR: Could not create default location structure in {region_path}: {e}")
    
    def _create_default_setting_in(self, location_path):
        default_setting_display = "Default Setting"
        default_setting_sanitized = sanitize_path_name(default_setting_display)
        setting_json_path = os.path.join(location_path, f"{default_setting_sanitized}_setting.json")
        try:
            if not os.path.isfile(setting_json_path):
                 existing_settings = [f for f in os.listdir(location_path) 
                                      if f.lower().endswith("_setting.json") and os.path.isfile(os.path.join(location_path, f))]
                 if not existing_settings:
                    self._save_json(setting_json_path, {"name": default_setting_display, "description": "Default starting setting.", "inventory": ""})
        except (OSError, IOError) as e:
             print(f"      ERROR: Could not create default setting structure in {location_path}: {e}")
    
    def _ensure_default_setting_structure(self):
        default_world_display = "Default World"
        default_world_sanitized = sanitize_path_name(default_world_display)
        default_region_display = "Default Region"
        default_region_sanitized = sanitize_path_name(default_region_display)
        default_location_display = "Default Location"
        default_location_sanitized = sanitize_path_name(default_location_display)
        default_setting_display = "Default Setting"
        default_setting_sanitized = sanitize_path_name(default_setting_display)
        settings_base_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
        world_dir = os.path.join(settings_base_dir, default_world_sanitized)
        region_dir = os.path.join(world_dir, default_region_sanitized)
        location_dir = os.path.join(region_dir, default_location_sanitized)
        world_json_path = os.path.join(world_dir, f"{default_world_sanitized}_world.json")
        region_json_path = os.path.join(region_dir, f"{default_region_sanitized}_region.json")
        location_json_path = os.path.join(location_dir, f"{default_location_sanitized}_location.json")
        setting_json_path = os.path.join(location_dir, f"{default_setting_sanitized}_setting.json")
        try:
            os.makedirs(settings_base_dir, exist_ok=True)
            existing_worlds = [d for d in os.listdir(settings_base_dir) 
                               if os.path.isdir(os.path.join(settings_base_dir, d))]
            world_created_or_exists = False
            if not existing_worlds:
                os.makedirs(world_dir, exist_ok=True)
                if not os.path.isfile(world_json_path):
                    self._save_json(world_json_path, {"name": default_world_display, "description": "Default starting world.", "locations": {}})
                world_created_or_exists = True
            elif os.path.isdir(world_dir):
                world_created_or_exists = True
            region_created_or_exists = False
            if world_created_or_exists:
                os.makedirs(world_dir, exist_ok=True)
                existing_regions = [d for d in os.listdir(world_dir) 
                                    if os.path.isdir(os.path.join(world_dir, d)) and d != 'resources']
                if not existing_regions:
                    os.makedirs(region_dir, exist_ok=True)
                    if not os.path.isfile(region_json_path):
                        self._save_json(region_json_path, {"name": default_region_display, "description": "Default starting region."}) 
                    region_created_or_exists = True
                elif os.path.isdir(region_dir):
                    region_created_or_exists = True
            location_created_or_exists = False
            if region_created_or_exists:
                os.makedirs(region_dir, exist_ok=True)
                existing_locations = [d for d in os.listdir(region_dir) 
                                      if os.path.isdir(os.path.join(region_dir, d))]
                if not existing_locations:
                    os.makedirs(location_dir, exist_ok=True)
                    if not os.path.isfile(location_json_path):
                        self._save_json(location_json_path, {
                            "name": default_location_display, 
                            "description": "Default starting location.",
                            "exterior": True
                        })
                    location_created_or_exists = True
                elif os.path.isdir(location_dir):
                     location_created_or_exists = True
                else:
                    print(f"    Existing locations found in default region. Skipping default location creation.")
            if location_created_or_exists:
                os.makedirs(location_dir, exist_ok=True)
                existing_settings = [f for f in os.listdir(location_dir) 
                                     if f.lower().endswith("_setting.json") and os.path.isfile(os.path.join(location_dir, f))]
                if not existing_settings:
                    if not os.path.isfile(setting_json_path):
                        self._save_json(setting_json_path, {"name": default_setting_display, "description": "Default starting setting.", "inventory": ""})
        except (OSError, IOError) as e:
            QMessageBox.critical(self, "Initialization Error",
                                 f"Failed to create default setting directories or files.\nError: {e}")

    def choose_location_map_image(self):
        if not self.current_world_name or not self.current_location_name:
            QMessageBox.warning(self, "Selection Needed", "Please select a World and Location first.")
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name)
        world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Select Map Image for {self.current_location_name}", 
            world_settings_dir, 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            rel_path = os.path.relpath(file_path, world_settings_dir)
            try:
                data = {}
                data["locations"] = {self.current_location_name: {"map_image": rel_path}}
                with open(world_json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.world_editor_tab.update_location_map()
            except Exception as e:
                print(f"Error choosing location map image: {e}")

    def clear_location_map_image(self):
        if not self.current_world_name or not self.current_location_name:
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name)
        world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
        try:
            data = {}
            if "locations" in data and self.current_location_name in data["locations"]:
                if "map_image" in data["locations"][self.current_location_name]:
                    del data["locations"][self.current_location_name]["map_image"]
            with open(world_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.world_editor_tab.update_location_map()
        except Exception as e:
            print(f"Error clearing location map image: {e}")

    def choose_world_map_image(self):
        if not self.current_world_name:
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name)
        maps_dir = os.path.join(world_settings_dir, "resources", "maps")
        os.makedirs(maps_dir, exist_ok=True)
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Map Image", maps_dir, "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            rel_path = os.path.relpath(file_path, maps_dir)
            world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
            try:
                data = {}
                data["map_image"] = rel_path
                with open(world_json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
                    self.world_editor_tab.update_world_map()
                else:
                     print("Warning: World editor tab not found after choosing world map image.")
            except Exception as e:
                print(f"Error choosing world map image: {e}")

    def clear_world_map_image(self):
        if not self.current_world_name:
            return
        world_settings_dir = os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name)
        world_json_path = os.path.join(world_settings_dir, f"{self.current_world_name}_world.json")
        try:
            data = {}
            if "map_image" in data:
                del data["map_image"]
            with open(world_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
                self.world_editor_tab.update_world_map()
            else:
                 print("Warning: World editor tab not found after clearing world map image.")
        except Exception as e:
            print(f"Error clearing world map image: {e}")

    def update_workflow_data_dir(self, new_workflow_data_dir):
        self.workflow_data_dir = new_workflow_data_dir
        if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
            self.world_editor_tab.workflow_data_dir = new_workflow_data_dir
            self.world_editor_tab.set_world(None)
            self.world_editor_tab.set_location(None)
            
    def _find_file_case_insensitive(self, directory, target_filename):
        if not os.path.isdir(directory):
            print(f"Directory not found: {directory}")
            return None
        exact_path = os.path.join(directory, target_filename)
        if os.path.isfile(exact_path):
            return exact_path
        target_lower = target_filename.lower()
        target_with_underscores = target_lower.replace(' ', '_')
        target_with_spaces = target_lower.replace('_', ' ')
        for filename in os.listdir(directory):
            file_lower = filename.lower()
            file_with_underscores = file_lower.replace(' ', '_')
            file_with_spaces = file_lower.replace('_', ' ')
            if (file_lower == target_lower or
                file_with_underscores == target_with_underscores or
                file_with_spaces == target_with_spaces or
                file_with_underscores == target_with_spaces or
                file_with_spaces == target_with_underscores):
                return os.path.join(directory, filename)
        return None
        
    def _find_directory_case_insensitive(self, parent_dir, target_dirname):
        if not os.path.isdir(parent_dir):
            print(f"Parent directory not found: {parent_dir}")
            return None
        exact_path = os.path.join(parent_dir, target_dirname)
        if os.path.isdir(exact_path):
            return exact_path
        target_lower = target_dirname.lower()
        target_with_underscores = target_lower.replace(' ', '_')
        target_with_spaces = target_lower.replace('_', ' ')
        for dirname in os.listdir(parent_dir):
            dir_path = os.path.join(parent_dir, dirname)
            if not os.path.isdir(dir_path):
                continue
            dir_lower = dirname.lower()
            dir_with_underscores = dir_lower.replace(' ', '_')
            dir_with_spaces = dir_lower.replace('_', ' ')
            if (dir_lower == target_lower or
                dir_with_underscores == target_with_underscores or
                dir_with_spaces == target_with_spaces or
                dir_with_underscores == target_with_spaces or
                dir_with_spaces == target_with_underscores):
                return dir_path
        return None

    def _add_variable_row(self, name="", value=""):
        row_widget = QWidget()
        row_widget.setObjectName("VariableRow")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        name_input = QLineEdit()
        name_input.setObjectName("SettingManagerVarNameInput")
        name_input.setPlaceholderText("Variable name")
        name_input.setText(name)
        name_input.installEventFilter(self)
        name_input.textChanged.connect(self._schedule_description_save)
        value_input = QLineEdit()
        value_input.setObjectName("SettingManagerVarValueInput")
        value_input.setPlaceholderText("Value")
        value_input.setText(value)
        value_input.installEventFilter(self)
        value_input.textChanged.connect(self._schedule_description_save)
        row_layout.addWidget(name_input, 1)
        row_layout.addWidget(value_input, 1)
        row_widget.setProperty("name_input", name_input)
        row_widget.setProperty("value_input", value_input)
        row_widget.installEventFilter(self)
        self.variables_list_layout.addWidget(row_widget)
        return row_widget
        
    def _remove_selected_variable_row(self):
        if hasattr(self, '_selected_variable_row_widget') and self._selected_variable_row_widget:
            item_to_remove = None
            index_to_remove = -1
            layout = self.variables_list_layout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget() == self._selected_variable_row_widget:
                    item_to_remove = item
                    index_to_remove = i
                    break
            if item_to_remove is not None and index_to_remove != -1:
                layout.takeAt(index_to_remove)
                widget_to_delete = self._selected_variable_row_widget
                self._selected_variable_row_widget = None
                widget_to_delete.deleteLater()
                self._schedule_description_save()
        else:
            QMessageBox.information(self, "Remove Variable", "Click on a variable row to select it before removing.")
    
    def _clear_variable_rows(self):
        while self.variables_list_layout.count() > 0:
            item = self.variables_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def _get_variables_data(self):
        variables_data = {}
        count = self.variables_list_layout.count()
        for i in range(count):
            row_widget = self.variables_list_layout.itemAt(i).widget()
            if row_widget:
                name_input = row_widget.findChild(QLineEdit, "SettingManagerVarNameInput")
                value_input = row_widget.findChild(QLineEdit, "SettingManagerVarValueInput")
                if name_input and value_input:
                    name = name_input.text().strip()
                    value = value_input.text().strip()
                    if name:
                        variables_data[name] = value
        return variables_data

    def _get_actual_location_path_for_setting_creation(self, world_orig, region_orig, location_orig):
        if not world_orig:
            return None
        world_base_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', world_orig)
        if not location_orig or location_orig == "__global__":
            if region_orig and region_orig != "__global__":
                return os.path.join(world_base_path, region_orig)
            else:
                return world_base_path
        sanitized_location_name = sanitize_path_name(location_orig)
        if region_orig and region_orig != "__global__":
            region_location_path = os.path.join(world_base_path, region_orig, sanitized_location_name)
            if os.path.isdir(region_location_path):
                return region_location_path
        world_location_path = os.path.join(world_base_path, sanitized_location_name)
        if os.path.isdir(world_location_path):
            region_json = os.path.join(world_location_path, f"{sanitized_location_name}_region.json")
            if not os.path.exists(region_json):
                return world_location_path
        for item_name in os.listdir(world_base_path):
            item_path = os.path.join(world_base_path, item_name)
            region_json = os.path.join(item_path, f"{item_name}_region.json")
            if os.path.isdir(item_path) and os.path.exists(region_json):
                potential_location_path = os.path.join(item_path, sanitized_location_name)
                if os.path.isdir(potential_location_path):
                    return potential_location_path
        if region_orig and region_orig != "__global__":
            creation_path = os.path.join(world_base_path, region_orig, sanitized_location_name)
            return creation_path
        else:
            creation_path = os.path.join(world_base_path, sanitized_location_name)
            return creation_path

    def populate_settings(self, location_path):
        self.list3.clear()
        if not location_path or not os.path.isdir(location_path):
            return
        try:
            for filename in os.listdir(location_path):
                if filename.lower().endswith('_setting.json'):
                    file_path = os.path.join(location_path, filename)
                    try:
                        setting_data = self._load_json(file_path)
                        display_name = setting_data.get('name', filename.replace('_setting.json', '').replace('_', ' ').title())
                        is_game_version = 'game' in file_path.split(os.sep)
                        item_text = display_name
                        if is_game_version:
                            item_text += " *"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, {'filename': filename, 'path': file_path, 'is_game_version': is_game_version})
                        self.list3.addItem(item)
                    except Exception as e:
                        print(f"Error loading setting JSON at {file_path}: {e}")
        except Exception as e:
            print(f"Error listing files in {location_path}: {e}")
        self.list3.sortItems()
        if self.list3.count() > 0:
            self.list3.setCurrentItem(self.list3.item(0))
        else:
            self.setting_name_input.clear()
            self.setting_description_input.clear()
            self.setting_inventory_table.setRowCount(0)
            self._clear_variable_rows()
            self.actors_in_setting_list.clear()
            self._clear_connections_ui()
            self.setting_exterior_checkbox.setChecked(False) 
            self.visible_section_container.setVisible(False)

    def populate_locations(self, parent_path):
        self.list2.clear()
        none_item = QListWidgetItem("NONE")
        none_item.setData(Qt.UserRole, "__global__")
        none_item.setToolTip("Settings placed directly in the current folder (no extra location)")
        self.list2.addItem(none_item)
        if not self._selected_world_orig:
            return
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
        path_to_scan = None
        is_scanning_world_level = False
        if parent_path is None or os.path.abspath(parent_path) == os.path.abspath(world_dir):
            path_to_scan = world_dir
            is_scanning_world_level = True
        elif os.path.isdir(parent_path):
            path_to_scan = parent_path
            is_scanning_world_level = False
        else:
             return
        if not os.path.isdir(path_to_scan):
            return
        location_items = []
        try:
            for item_name_actual in os.listdir(path_to_scan):
                item_path = os.path.join(path_to_scan, item_name_actual)
                if os.path.isdir(item_path):
                    if item_name_actual.lower() == 'resources':
                        continue
                    is_region_folder = False
                    json_check_path = None
                    pattern1_reg = f"{item_name_actual}_region.json"
                    path1_reg = self._find_file_case_insensitive(item_path, pattern1_reg)
                    if path1_reg:
                        is_region_folder = True
                        json_check_path = path1_reg
                    else:
                        pattern2_reg = f"{sanitize_path_name(item_name_actual)}_region.json"
                        path2_reg = self._find_file_case_insensitive(item_path, pattern2_reg)
                        if path2_reg:
                            is_region_folder = True
                            json_check_path = path2_reg
                        else:
                            try:
                                for f_name_check in os.listdir(item_path):
                                    if fnmatch.fnmatch(f_name_check.lower(), "*_region.json"):
                                        is_region_folder = True
                                        json_check_path = os.path.join(item_path, f_name_check)
                                        break
                            except Exception as e_scan_reg:
                                print(f"  Error during generic scan for region JSON (check) in {item_name_actual}: {e_scan_reg}")
                    if is_scanning_world_level and is_region_folder:
                        continue
                    if not is_scanning_world_level and is_region_folder: 
                        continue
                    actual_location_json_path = None
                    loc_data = None
                    pattern1_loc = f"{item_name_actual}_location.json"
                    path1_loc = self._find_file_case_insensitive(item_path, pattern1_loc)
                    if path1_loc:
                        actual_location_json_path = path1_loc
                    else:
                        pattern2_loc = f"{sanitize_path_name(item_name_actual)}_location.json"
                        path2_loc = self._find_file_case_insensitive(item_path, pattern2_loc)
                        if path2_loc:
                            actual_location_json_path = path2_loc
                        else:
                            try:
                                for f_name_loc in os.listdir(item_path):
                                    if fnmatch.fnmatch(f_name_loc.lower(), "*_location.json"):
                                        actual_location_json_path = os.path.join(item_path, f_name_loc)
                                        break
                            except Exception as e_scan_loc:
                                print(f"  Error during generic scan for location JSON in {item_name_actual}: {e_scan_loc}")
                    display_name = item_name_actual.replace("_", " ").replace("-"," ").title()
                    if actual_location_json_path:
                        try:
                            loc_data = self._load_json(actual_location_json_path)
                            if loc_data.get('name'):
                                display_name = loc_data['name']
                        except Exception as e_load_loc:
                            print(f"[populate_locations] Error reading {actual_location_json_path}: {e_load_loc}")
                    else:
                        if not is_scanning_world_level: 
                             print(f"  Treating as location (inside region scan): '{display_name}' (folder: {item_name_actual}, no specific location JSON found)")
                        else: 
                            continue
                    list_item = QListWidgetItem(display_name)
                    list_item.setData(Qt.UserRole, item_name_actual) 
                    location_items.append(list_item)
        except Exception as e:
            import traceback
            traceback.print_exc()
        location_items.sort(key=lambda x: x.text().lower())
        for item in location_items:
            self.list2.addItem(item)
        if self.list2.count() > 0:
            self.list2.setCurrentItem(self.list2.item(0))

    def refresh_all(self):
        world = self._selected_world_orig
        region = self._selected_region_orig
        location = self._selected_location_orig
        setting = self._selected_setting_orig
        self.populate_worlds()
        if world:
            for i in range(self.list_world.count()):
                item = self.list_world.item(i)
                if item.text() == world or item.text() == world.replace('_', ' ').title():
                    self.list_world.setCurrentItem(item)
                    break
        if region:
            for i in range(self.list1.count()):
                item = self.list1.item(i)
                if item.data(Qt.UserRole) == region:
                    self.list1.setCurrentItem(item)
                    break
        if location:
            for i in range(self.list2.count()):
                item = self.list2.item(i)
                if item.data(Qt.UserRole) == location:
                    self.list2.setCurrentItem(item)
                    break
        if setting:
            for i in range(self.list3.count()):
                item = self.list3.item(i)
                if isinstance(item.data(Qt.UserRole), dict) and item.data(Qt.UserRole).get('filename') == setting:
                    self.list3.setCurrentItem(item)
                    break
        if self.list_world.count() > 0 and self.list_world.currentItem() is None:
            self.list_world.setCurrentItem(self.list_world.item(0))
        if self.list1.count() > 0 and self.list1.currentItem() is None:
            self.list1.setCurrentItem(self.list1.item(0))
        if self.list2.count() > 0 and self.list2.currentItem() is None:
            self.list2.setCurrentItem(self.list2.item(0))
        if self.list3.count() > 0 and self.list3.currentItem() is None:
            self.list3.setCurrentItem(self.list3.item(0))

    def _update_location_region(self, location_name, region_name):
        try:
            if hasattr(self.parent(), 'refresh_all'):
                self.parent().refresh_all()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to move/merge location directory: {e}")
            return False

    def _update_setting_region(self, setting_name, region_name, location_name):
        try:
            self.refresh_all()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to move setting file: {e}")
            return False
    def _add_world_feature(self):
        if not self._selected_world_orig:
            QMessageBox.warning(self, "No World Selected", "Please select a world first.")
            return
        feature_name = self.world_feature_name_input.text().strip()
        if feature_name and any(f['name'].lower() == feature_name.lower() for f in self.current_world_features):
            feature_name, ok = QInputDialog.getText(self, "Add World Feature", "Enter feature name (previous name already exists):")
            if not (ok and feature_name):
                print("Add world feature cancelled or no name entered.")
                return
        elif not feature_name:
            feature_name, ok = QInputDialog.getText(self, "Add World Feature", "Enter feature name:")
            if not (ok and feature_name):
                print("Add world feature cancelled or no name entered.")
                return
        if any(f['name'].lower() == feature_name.lower() for f in self.current_world_features):
            QMessageBox.warning(self, "Duplicate Feature", f"A feature named '{feature_name}' already exists for this world.")
            return
        new_feature = {
            "name": feature_name,
            "description": ""
        }
        self.current_world_features.append(new_feature)
        item = QListWidgetItem(feature_name)
        item.setData(Qt.UserRole, new_feature)
        self.world_features_list.addItem(item)
        self.world_features_list.setCurrentRow(self.world_features_list.count() - 1)
        self._editing_level = 'world'
        self._editing_world_orig = self._selected_world_orig
        self._editing_region_orig = None
        self._editing_location_orig = None
        self._editing_setting_orig = None
        self._save_current_details()
        self.world_feature_name_input.clear()

    def _remove_world_feature(self):
        if not self._selected_world_orig:
            QMessageBox.warning(self, "No World Selected", "Please select a world first.")
            return
            
        current_row = self.world_features_list.currentRow()
        if current_row < 0 or current_row >= len(self.current_world_features):
            QMessageBox.warning(self, "No Feature Selected", "Please select a feature to remove.")
            return

        feature_to_remove = self.current_world_features[current_row]
        reply = QMessageBox.question(self, "Remove Feature",
                                     f"Are you sure you want to remove the feature '{feature_to_remove['name']}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.current_world_features[current_row]
            self._populate_world_features_list()
            self._save_current_details()
            if hasattr(self, 'world_editor_tab') and hasattr(self.world_editor_tab, 'settingAddedOrRemoved'):
                self.world_editor_tab.settingAddedOrRemoved.emit()

    def _add_location_feature(self):
        if not self._selected_location_orig or self._selected_location_orig == "__global__":
            QMessageBox.warning(self, "No Location Selected", "Please select a specific location first (not 'Global').")
            return
        feature_name = self.location_feature_name_input.text().strip()
        if feature_name and any(f['name'].lower() == feature_name.lower() for f in self.current_location_features):
            feature_name, ok = QInputDialog.getText(self, "Add Location Feature", "Enter feature name (previous name already exists):")
            if not (ok and feature_name):
                print("Add location feature cancelled or no name entered.")
                return
        elif not feature_name:
            feature_name, ok = QInputDialog.getText(self, "Add Location Feature", "Enter feature name:")
            if not (ok and feature_name):
                print("Add location feature cancelled or no name entered.")
                return
        if any(f['name'].lower() == feature_name.lower() for f in self.current_location_features):
            QMessageBox.warning(self, "Duplicate Feature", f"A feature named '{feature_name}' already exists for this location.")
            return
        new_feature = {
            "name": feature_name,
            "description": ""
        }
        self.current_location_features.append(new_feature)
        item = QListWidgetItem(feature_name)
        item.setData(Qt.UserRole, new_feature)
        self.location_features_list.addItem(item)
        self.location_features_list.setCurrentRow(self.location_features_list.count() - 1)
        self._editing_level = 'location'
        self._editing_world_orig = self._selected_world_orig
        self._editing_region_orig = self._selected_region_orig
        self._editing_location_orig = self._selected_location_orig
        self._editing_setting_orig = None
        self._save_current_details()
        self.location_feature_name_input.clear()

    def _remove_location_feature(self):
        if not self._selected_location_orig or self._selected_location_orig == "__global__":
            QMessageBox.warning(self, "No Location Selected", "Please select a specific location first.")
            return
        current_row = self.location_features_list.currentRow()
        if current_row < 0 or current_row >= len(self.current_location_features):
            QMessageBox.warning(self, "No Feature Selected", "Please select a feature to remove.")
            return
        feature_to_remove = self.current_location_features[current_row]
        reply = QMessageBox.question(self, "Remove Feature",
                                     f"Are you sure you want to remove the feature '{feature_to_remove['name']}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.current_location_features[current_row]
            self._populate_location_features_list()
            self._save_current_details()
            if hasattr(self, 'world_editor_tab') and hasattr(self.world_editor_tab, 'settingAddedOrRemoved'):
                self.world_editor_tab.settingAddedOrRemoved.emit()
    def _populate_world_features_list(self):
        self.world_features_list.clear()
        self.world_feature_name_input.clear()
        self.world_feature_desc_input.clear()
        for feature_data in self.current_world_features:
            name = feature_data.get("name", "Unnamed Feature")
            description = feature_data.get("description", "")
            item = QListWidgetItem(name)
            item.setToolTip(description)
            item.setData(Qt.UserRole, feature_data)
            self.world_features_list.addItem(item)

    def _populate_location_features_list(self):
        self.location_features_list.clear()
        self.location_feature_name_input.clear()
        self.location_feature_desc_input.clear()
        for feature_data in self.current_location_features:
            name = feature_data.get("name", "Unnamed Feature")
            description = feature_data.get("description", "")
            item = QListWidgetItem(name)
            item.setToolTip(description)
            item.setData(Qt.UserRole, feature_data)
            self.location_features_list.addItem(item)
            
    def _on_world_feature_selected(self, row):
        if 0 <= row < len(self.current_world_features):
            feature_data = self.current_world_features[row]
            self.world_feature_name_input.setText(feature_data.get("name", ""))
            self.world_feature_desc_input.blockSignals(True)
            self.world_feature_desc_input.setPlainText(feature_data.get("description", ""))
            self.world_feature_desc_input.blockSignals(False)
        else:
            self.world_feature_name_input.clear()
            self.world_feature_desc_input.clear()

    def _on_world_feature_name_edited(self):
        current_row = self.world_features_list.currentRow()
        if 0 <= current_row < len(self.current_world_features):
            new_name = self.world_feature_name_input.text().strip()
            if not new_name:
                QMessageBox.warning(self, "Invalid Name", "Feature name cannot be empty.")
                self.world_feature_name_input.setText(self.current_world_features[current_row]["name"])
                return
            for i, feat in enumerate(self.current_world_features):
                if i != current_row and feat['name'].lower() == new_name.lower():
                    QMessageBox.warning(self, "Duplicate Feature", f"Another feature named '{new_name}' already exists for this world.")
                    self.world_feature_name_input.setText(self.current_world_features[current_row]["name"]) # Revert
                    return
            if self.current_world_features[current_row]["name"] != new_name:
                self.current_world_features[current_row]["name"] = new_name
                list_item = self.world_features_list.item(current_row)
                if list_item:
                    list_item.setText(new_name)
                self._editing_level = 'world'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = None
                self._editing_location_orig = None
                self._editing_setting_orig = None
                self._save_current_details()

    def _on_world_feature_desc_edited(self):
        current_row = self.world_features_list.currentRow()
        if 0 <= current_row < len(self.current_world_features):
            new_desc = self.world_feature_desc_input.toPlainText().strip()
            if self.current_world_features[current_row]["description"] != new_desc:
                self.current_world_features[current_row]["description"] = new_desc
                list_item = self.world_features_list.item(current_row)
                if list_item:
                    list_item.setToolTip(new_desc)
                self._editing_level = 'world'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = None
                self._editing_location_orig = None
                self._editing_setting_orig = None
                if not hasattr(self, '_feature_desc_save_timer_world'):
                    self._feature_desc_save_timer_world = QTimer(self)
                    self._feature_desc_save_timer_world.setSingleShot(True)
                    self._feature_desc_save_timer_world.timeout.connect(self._save_current_details)
                self._feature_desc_save_timer_world.start(1000)

    def _on_location_feature_selected(self, row):
        if 0 <= row < len(self.current_location_features):
            feature_data = self.current_location_features[row]
            self.location_feature_name_input.setText(feature_data.get("name", ""))
            self.location_feature_desc_input.blockSignals(True)
            self.location_feature_desc_input.setPlainText(feature_data.get("description", ""))
            self.location_feature_desc_input.blockSignals(False)
        else:
            self.location_feature_name_input.clear()
            self.location_feature_desc_input.clear()
            
    def _on_location_feature_name_edited(self):
        current_row = self.location_features_list.currentRow()
        if 0 <= current_row < len(self.current_location_features):
            new_name = self.location_feature_name_input.text().strip()
            if not new_name:
                QMessageBox.warning(self, "Invalid Name", "Feature name cannot be empty.")
                self.location_feature_name_input.setText(self.current_location_features[current_row]["name"])
                return
            for i, feat in enumerate(self.current_location_features):
                if i != current_row and feat['name'].lower() == new_name.lower():
                    QMessageBox.warning(self, "Duplicate Feature", f"Another feature named '{new_name}' already exists for this location.")
                    self.location_feature_name_input.setText(self.current_location_features[current_row]["name"])
                    return
            if self.current_location_features[current_row]["name"] != new_name:
                self.current_location_features[current_row]["name"] = new_name
                list_item = self.location_features_list.item(current_row)
                if list_item:
                    list_item.setText(new_name)
                self._editing_level = 'location'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = self._selected_region_orig
                self._editing_location_orig = self._selected_location_orig
                self._editing_setting_orig = None
                self._save_current_details()

    def _on_location_feature_desc_edited(self):
        current_row = self.location_features_list.currentRow()
        if 0 <= current_row < len(self.current_location_features):
            new_desc = self.location_feature_desc_input.toPlainText().strip()
            if self.current_location_features[current_row]["description"] != new_desc:
                self.current_location_features[current_row]["description"] = new_desc
                list_item = self.location_features_list.item(current_row)
                if list_item:
                    list_item.setToolTip(new_desc)
                self._editing_level = 'location'
                self._editing_world_orig = self._selected_world_orig
                self._editing_region_orig = self._selected_region_orig
                self._editing_location_orig = self._selected_location_orig
                self._editing_setting_orig = None
                if not hasattr(self, '_feature_desc_save_timer_location'):
                    self._feature_desc_save_timer_location = QTimer(self)
                    self._feature_desc_save_timer_location.setSingleShot(True)
                    self._feature_desc_save_timer_location.timeout.connect(self._save_current_details)
                self._feature_desc_save_timer_location.start(1000)

    def _populate_actors_in_setting_list(self, setting_data):
        self.actors_in_setting_list.clear()
        characters = setting_data.get('characters', [])
        if isinstance(characters, list):
            clean_characters = []
            for char in characters:
                if isinstance(char, str) and char.strip():
                    clean_characters.append(char.strip())
            self.actors_in_setting_list.addItems(sorted(clean_characters))

    def _add_actor_to_setting(self):
        actor_to_add = self.actor_name_input.text().strip()
        if not actor_to_add:
            QMessageBox.warning(self, "No Actor Name", "Please enter an actor name in the text field.")
            return
        selected_setting_item = self.list3.currentItem()
        if not selected_setting_item:
            QMessageBox.warning(self, "No Setting Selected", "Please select a setting first.")
            return
        setting_name = selected_setting_item.text().split(" *")[0]
        world_item = self.list_world.currentItem()
        region_item = self.list1.currentItem()
        location_item = self.list2.currentItem()
        if not all([world_item, region_item, location_item]):
             QMessageBox.warning(self, "Incomplete Selection", "World, Region, and Location must be selected.")
             return
        world_name = world_item.data(Qt.UserRole) if world_item.data(Qt.UserRole) else world_item.text().split(" *")[0]
        region_name = region_item.data(Qt.UserRole) if region_item.data(Qt.UserRole) else region_item.text().split(" *")[0]
        location_name = location_item.data(Qt.UserRole) if location_item.data(Qt.UserRole) else location_item.text().split(" *")[0]
        if location_name == "__global__":
            location_name = None
        setting_item_data = selected_setting_item.data(Qt.UserRole)
        if not isinstance(setting_item_data, dict) or 'filename' not in setting_item_data:
            QMessageBox.critical(self, "Error", f"Could not get filename for setting '{setting_name}'.")
            return
        setting_filename = setting_item_data['filename']
        setting_path = setting_item_data.get('path')
        if not setting_path or not os.path.exists(setting_path) or setting_item_data.get('is_game_version', False):
            setting_path = self._get_json_path('setting', world_name, region_name, location_name, setting_filename, respect_game_override=False)
        if not setting_path or not os.path.exists(setting_path):
            manual_base_path = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
            if os.path.exists(manual_base_path):
                for root, dirs, files in os.walk(manual_base_path):
                    if setting_filename in files:
                        found_path = os.path.join(root, setting_filename)
            return
        setting_data = self._load_json(setting_path)
        all_actors = self._get_available_actors()
        if actor_to_add not in all_actors:
            QMessageBox.warning(self, "Actor Not Found", f"An actor with the name '{actor_to_add}' does not exist.")
            return
        current_actors_set = set(setting_data.get('characters', []))
        if actor_to_add in current_actors_set:
            QMessageBox.information(self, "Actor Already Exists", f"The actor '{actor_to_add}' is already in this setting.")
            return
        current_actors_set.add(actor_to_add)
        setting_data['characters'] = sorted(list(current_actors_set))
        if not self._save_json(setting_path, setting_data):
            QMessageBox.critical(self, "Save Error", f"Failed to save updated setting file at {setting_path}")
            return
        actor_path = self._get_actor_json_path_by_name(actor_to_add)
        if actor_path:
            actor_data = self._load_json(actor_path)
            actor_data['location'] = setting_name
        self.actor_name_input.clear()
        self._populate_actors_in_setting_list(setting_data)

    def _remove_actor_from_setting(self):
        selected_actor_item = self.actors_in_setting_list.currentItem()
        if not selected_actor_item:
            QMessageBox.warning(self, "No Actor Selected", "Please select an actor from the list to remove.")
            return
        actor_to_remove = selected_actor_item.text()
        selected_setting_item = self.list3.currentItem()
        if not selected_setting_item:
            QMessageBox.warning(self, "No Setting Selected", "Cannot remove actor because no setting is selected.")
            return
        setting_name = selected_setting_item.text().split(" *")[0]
        world_item = self.list_world.currentItem()
        region_item = self.list1.currentItem()
        location_item = self.list2.currentItem()
        if not all([world_item, region_item, location_item]):
             QMessageBox.warning(self, "Incomplete Selection", "World, Region, and Location must be selected.")
             return
        world_name = world_item.data(Qt.UserRole) if world_item.data(Qt.UserRole) else world_item.text().split(" *")[0]
        region_name = region_item.data(Qt.UserRole) if region_item.data(Qt.UserRole) else region_item.text().split(" *")[0]
        location_name = location_item.data(Qt.UserRole) if location_item.data(Qt.UserRole) else location_item.text().split(" *")[0]
        if location_name == "__global__":
            location_name = None
        setting_item_data = selected_setting_item.data(Qt.UserRole)
        if not isinstance(setting_item_data, dict) or 'filename' not in setting_item_data:
            QMessageBox.critical(self, "Error", f"Could not get filename for setting '{setting_name}'.")
            return
        setting_filename = setting_item_data['filename']
        setting_path = setting_item_data.get('path')
        if not setting_path or not os.path.exists(setting_path) or setting_item_data.get('is_game_version', False):
            setting_path = self._get_json_path('setting', world_name, region_name, location_name, setting_filename, respect_game_override=False)
        if not setting_path or not os.path.exists(setting_path):
            return
        setting_data = self._load_json(setting_path)
        current_actors = setting_data.get('characters', [])
        if actor_to_remove in current_actors:
            current_actors.remove(actor_to_remove)
            setting_data['characters'] = sorted(current_actors)
            if not self._save_json(setting_path, setting_data):
                QMessageBox.critical(self, "Save Error", f"Failed to save updated setting file at {setting_path}")
                return
            actor_path = self._get_actor_json_path_by_name(actor_to_remove)
            if actor_path:
                actor_data = self._load_json(actor_path)
                if actor_data.get('location') == setting_name:
                    actor_data['location'] = ""
                    if not self._save_json(actor_path, actor_data):
                        QMessageBox.warning(self, "Save Warning", f"Failed to clear location for actor '{actor_to_remove}' in {actor_path}")
            self._populate_actors_in_setting_list(setting_data)
            print(f"Removed actor '{actor_to_remove}' from setting '{setting_name}'.")

    def _get_available_actors(self):
        actors = {}
        resources_actors_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
        if os.path.isdir(resources_actors_dir):
            for filename in os.listdir(resources_actors_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(resources_actors_dir, filename)
                    data = self._load_json(file_path)
                    if data and 'name' in data:
                        actors[data['name']] = 'resource'
        game_actors_dir = os.path.join(self.workflow_data_dir, 'game', 'actors')
        if os.path.isdir(game_actors_dir):
            for filename in os.listdir(game_actors_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(game_actors_dir, filename)
                    data = self._load_json(file_path)
                    if data and 'name' in data:
                        actors[data['name']] = 'game'
        return sorted(list(actors.keys()))

    def _get_actor_json_path_by_name(self, actor_name):
        game_actors_dir = os.path.join(self.workflow_data_dir, 'game', 'actors')
        if os.path.isdir(game_actors_dir):
            for filename in os.listdir(game_actors_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(game_actors_dir, filename)
                    data = self._load_json(file_path)
                    if data and data.get('name', '').lower() == actor_name.lower():
                        return file_path
        resources_actors_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
        if os.path.isdir(resources_actors_dir):
            for filename in os.listdir(resources_actors_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(resources_actors_dir, filename)
                    data = self._load_json(file_path)
                    if data and data.get('name', '').lower() == actor_name.lower():
                        return file_path
        return None

    def _setting_has_map_dot(self, setting_display_name, world_name, region_name, location_name):
        if not (setting_display_name and world_name):
            return False
        if location_name:
            location_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', world_name)
            if region_name and region_name != "__global__":
                location_dir = os.path.join(location_dir, region_name)
            location_dir = os.path.join(location_dir, location_name)
            map_data_file = os.path.join(location_dir, "location_map_data.json")
            if os.path.isfile(map_data_file):
                try:
                    with open(map_data_file, 'r', encoding='utf-8') as f:
                        map_data = json.load(f)
                    dots = map_data.get('dots', [])
                    for d in dots:
                        if len(d) >= 5 and isinstance(d[4], str):
                            if d[4].strip().lower() == setting_display_name.strip().lower():
                                return True
                except Exception as e:
                    print(f"[DEBUG] Error reading location map data for dot check: {e}")
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', world_name)
        map_data_file = os.path.join(world_dir, "world_map_data.json")
        if os.path.isfile(map_data_file):
            try:
                with open(map_data_file, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                dots = map_data.get('dots', [])
                for d in dots:
                    if len(d) >= 5 and isinstance(d[4], str):
                        if d[4].strip().lower() == setting_display_name.strip().lower():
                            return True
            except Exception as e:
                print(f"[DEBUG] Error reading world map data for dot check: {e}")
        return False

    def _add_inventory_item(self):
        row = self.setting_inventory_table.rowCount()
        self.setting_inventory_table.insertRow(row)
        self.setting_inventory_table.setItem(row, 0, QTableWidgetItem(""))
        self.setting_inventory_table.setItem(row, 1, QTableWidgetItem("1"))
        self.setting_inventory_table.setItem(row, 2, QTableWidgetItem(""))
        self.setting_inventory_table.setItem(row, 3, QTableWidgetItem(""))
        self._schedule_description_save()

    def _remove_inventory_item(self):
        current_row = self.setting_inventory_table.currentRow()
        if current_row >= 0:
            self.setting_inventory_table.removeRow(current_row)
            self._schedule_description_save()

    def _on_inventory_item_changed(self, item):
        self._schedule_description_save()
    
    def _edit_inventory_in_manager(self):
        current_setting_item = self.list3.currentItem()
        if not current_setting_item:
            QMessageBox.warning(self, "No Selection", "Please select a setting first.")
            return
        setting_name = current_setting_item.text().replace(" *", "")
        main_ui = self._get_main_ui()
        if not main_ui:
            return
        try:
            import pygame
            if hasattr(main_ui, '_left_splitter_sound') and main_ui._left_splitter_sound:
                main_ui._left_splitter_sound.play()
            else:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                left_splitter_sound = pygame.mixer.Sound('sounds/LeftSplitterSelection.mp3')
                left_splitter_sound.play()
                main_ui._left_splitter_sound = left_splitter_sound
        except Exception:
            pass
        main_window = self
        while True:
            if hasattr(main_window, 'parentWidget') and main_window.parentWidget() is not None:
                main_window = main_window.parentWidget()
            else:
                break
        from PyQt5.QtWidgets import QStackedWidget, QPushButton
        inventory_manager_button = None
        for button in main_window.findChildren(QPushButton):
            if hasattr(button, 'objectName') and button.objectName() == "InventoryManagerButtonLeft":
                inventory_manager_button = button
                break
        if not inventory_manager_button:
            QMessageBox.warning(self, "Navigation Error", "Could not find Inventory Manager button.")
            return
        inventory_manager_button.setChecked(True)
        center_stack = None
        for stack in main_window.findChildren(QStackedWidget):
            if stack.count() > 8:
                center_stack = stack
                break
        if not center_stack:
            QMessageBox.warning(self, "Navigation Error", "Could not find center stack widget.")
            return
        inventory_manager_widget = center_stack.widget(8)
        if not inventory_manager_widget or not hasattr(inventory_manager_widget, 'instances_btn'):
            QMessageBox.warning(self, "Navigation Error", "Could not find Inventory Manager widget.")
            return
        center_stack.setCurrentIndex(8)
        inventory_manager_widget.instances_btn.setChecked(True)
        inventory_manager_widget.select_setting_in_instances(setting_name)

    def _add_world_path(self):
        if not self._selected_world_orig:
            return
        path_type_name = self.world_path_name_input.text().strip()
        if path_type_name and path_type_name in self.current_world_path_data_cache:
            path_type_name, ok = QInputDialog.getText(self, "Add Path Type", "Enter path type name (previous name already exists):")
            if not (ok and path_type_name):
                return
        elif not path_type_name:
            path_type_name, ok = QInputDialog.getText(self, "Add Path Type", "Enter path type name:")
            if not (ok and path_type_name):
                return
        path_type_name = path_type_name.strip()
        if not path_type_name:
            QMessageBox.warning(self, "Invalid Name", "Path type name cannot be empty.")
            return
        if path_type_name in self.current_world_path_data_cache:
            QMessageBox.warning(self, "Duplicate Path Type", f"A path type named '{path_type_name}' already exists.")
            return
        description = self.world_path_desc_input.toPlainText().strip()
        self.world_paths_list.addItem(path_type_name)
        self.current_world_path_data_cache[path_type_name] = {"name": path_type_name, "description": description}
        self.world_paths_list.setCurrentRow(self.world_paths_list.count() - 1)
        self._schedule_description_save()
        self.world_path_name_input.clear()
            
    def _remove_world_path(self):
        if not self._selected_world_orig:
            return
        current_row = self.world_paths_list.currentRow()
        if current_row < 0:
            return
        current_path_type = self.world_paths_list.item(current_row).text()
        if current_path_type.endswith("(Default)"):
            return
        reply = QMessageBox.question(self, "Remove Path Type",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.world_paths_list.takeItem(current_row)
            self.current_world_path_data_cache.pop(current_path_type, None)
            self.world_path_name_input.clear()
            self.world_path_desc_input.clear()
            self._schedule_description_save()
            
    def _add_location_path(self):
        if not self._selected_location_orig or self._selected_location_orig == "__global__":
            return
        path_type_name = self.location_path_name_input.text().strip()
        if path_type_name and path_type_name in self.current_location_path_data_cache:
            path_type_name, ok = QInputDialog.getText(self, "Add Path Type", "Enter path type name (previous name already exists):")
            if not (ok and path_type_name):
                return
        elif not path_type_name:
            path_type_name, ok = QInputDialog.getText(self, "Add Path Type", "Enter path type name:")
            if not (ok and path_type_name):
                return
        path_type_name = path_type_name.strip()
        if not path_type_name:
            QMessageBox.warning(self, "Invalid Name", "Path type name cannot be empty.")
            return
        if path_type_name in self.current_location_path_data_cache:
            QMessageBox.warning(self, "Duplicate Path Type", f"A path type named '{path_type_name}' already exists.")
            return
        description = self.location_path_desc_input.toPlainText().strip()
        self.location_paths_list.addItem(path_type_name)
        self.current_location_path_data_cache[path_type_name] = {"name": path_type_name, "description": description}
        self.location_paths_list.setCurrentRow(self.location_paths_list.count() - 1)
        self._schedule_description_save()
        self.location_path_name_input.clear()
            
    def _remove_location_path(self):
        if not self._selected_location_orig or self._selected_location_orig == "__global__":
            return
        current_row = self.location_paths_list.currentRow()
        if current_row < 0:
            return
        current_path_type = self.location_paths_list.item(current_row).text()
        if current_path_type.endswith("(Default)"):
            return
        reply = QMessageBox.question(self, "Remove Path Type",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.location_paths_list.takeItem(current_row)
            self.current_location_path_data_cache.pop(current_path_type, None)
            self.location_path_name_input.clear()
            self.location_path_desc_input.clear()
            self._schedule_description_save()

    def _on_world_path_selected(self, row):
        if row < 0 or row >= self.world_paths_list.count():
            self.world_path_name_input.clear()
            self.world_path_desc_input.clear()
            return
        path_name = self.world_paths_list.item(row).text()
        self.world_path_name_input.setText(path_name)
        path_entry_from_cache = self.current_world_path_data_cache.get(path_name, {"description": ""})
        self.world_path_desc_input.setPlainText(path_entry_from_cache.get('description', ''))
        is_default = path_name.endswith("(Default)")
        self.world_path_name_input.setReadOnly(is_default)
        
    def _on_world_path_name_edited(self):
        current_row = self.world_paths_list.currentRow()
        if current_row < 0: return
        item = self.world_paths_list.item(current_row)
        old_name_from_list = item.text()
        if old_name_from_list.endswith("(Default)"):
            self.world_path_name_input.setText(old_name_from_list)
            return
        new_name_from_input = self.world_path_name_input.text().strip()
        if not new_name_from_input:
            QMessageBox.warning(self, "Invalid Name", "Path type name cannot be empty.")
            self.world_path_name_input.setText(old_name_from_list); return
        for name_in_cache in self.current_world_path_data_cache.keys():
            if name_in_cache.lower() == new_name_from_input.lower() and name_in_cache != old_name_from_list:
                QMessageBox.warning(self, "Duplicate Path Type", f"A path type named '{new_name_from_input}' already exists.")
                self.world_path_name_input.setText(old_name_from_list); return
        if old_name_from_list != new_name_from_input:
            item.setText(new_name_from_input)
            cached_data = self.current_world_path_data_cache.pop(old_name_from_list, {"description": ""})
            cached_data['name'] = new_name_from_input
            self.current_world_path_data_cache[new_name_from_input] = cached_data
            self._schedule_description_save()

    def _on_world_path_desc_edited(self):
        current_row = self.world_paths_list.currentRow()
        if current_row < 0: return
        path_name_selected_in_list = self.world_paths_list.item(current_row).text()
        current_desc_from_input = self.world_path_desc_input.toPlainText()
        path_entry = self.current_world_path_data_cache.get(path_name_selected_in_list)
        if path_entry:
            path_entry['description'] = current_desc_from_input
        else:
            self.current_world_path_data_cache[path_name_selected_in_list] = {"name": path_name_selected_in_list, "description": current_desc_from_input}
        self._original_edit_level = self._editing_level
        if self._selected_region_orig == "__global__":
            self._editing_level = 'world'
        self._schedule_description_save()
        
    def _on_location_path_selected(self, row):
        if row < 0 or row >= self.location_paths_list.count():
            self.location_path_name_input.clear()
            self.location_path_desc_input.clear()
            return
        path_name = self.location_paths_list.item(row).text()
        self.location_path_name_input.setText(path_name)
        path_entry_from_cache = self.current_location_path_data_cache.get(path_name, {"description": ""})
        self.location_path_desc_input.setPlainText(path_entry_from_cache.get('description', ''))
        is_default = path_name.endswith("(Default)")
        self.location_path_name_input.setReadOnly(is_default)
        
    def _on_location_path_name_edited(self):
        current_row = self.location_paths_list.currentRow()
        if current_row < 0: return
        item = self.location_paths_list.item(current_row)
        old_name_from_list = item.text()
        if old_name_from_list.endswith("(Default)"):
            self.location_path_name_input.setText(old_name_from_list); return
        new_name_from_input = self.location_path_name_input.text().strip()
        if not new_name_from_input:
            QMessageBox.warning(self, "Invalid Name", "Path type name cannot be empty.")
            self.location_path_name_input.setText(old_name_from_list); return
        for name_in_cache in self.current_location_path_data_cache.keys():
            if name_in_cache.lower() == new_name_from_input.lower() and name_in_cache != old_name_from_list:
                QMessageBox.warning(self, "Duplicate Path Type", f"A path type named '{new_name_from_input}' already exists.")
                self.location_path_name_input.setText(old_name_from_list); return
        if old_name_from_list != new_name_from_input:
            item.setText(new_name_from_input)
            cached_data = self.current_location_path_data_cache.pop(old_name_from_list, {"description": ""})
            cached_data['name'] = new_name_from_input
            self.current_location_path_data_cache[new_name_from_input] = cached_data
            self._schedule_description_save()

    def _on_location_path_desc_edited(self):
        current_row = self.location_paths_list.currentRow()
        if current_row < 0: return
        path_name_selected_in_list = self.location_paths_list.item(current_row).text()
        current_desc_from_input = self.location_path_desc_input.toPlainText()
        path_entry = self.current_location_path_data_cache.get(path_name_selected_in_list)
        if path_entry:
            path_entry['description'] = current_desc_from_input
        else:
            self.current_location_path_data_cache[path_name_selected_in_list] = {"name": path_name_selected_in_list, "description": current_desc_from_input}
        self._schedule_description_save()

    def _call_generate_setting_details(self):
        if not self._selected_setting_orig or not self._current_setting_file_path_absolute:
            QMessageBox.warning(self, "No Setting Selected", "Please select a setting to generate details for.")
            return
        setting_filepath = self._current_setting_file_path_absolute
        current_setting_data = self._load_json(setting_filepath)
        setting_name = current_setting_data.get('name', self._selected_setting_orig.replace("_setting.json", ""))
        options = {
            "name": self.name_gen_checkbox.isChecked(),
            "description": self.desc_gen_checkbox.isChecked(),
            "connections": self.conn_gen_checkbox.isChecked(),
            "inventory": self.inv_gen_checkbox.isChecked()
        }
        if not self._selected_world_orig:
            QMessageBox.warning(self, "Error", "World context is missing.")
            return
        world_json_path = self._get_json_path('world', self._selected_world_orig)
        raw_world_data = self._load_json(world_json_path) if world_json_path else {}
        world_data_arg = {
            "name": raw_world_data.get('name', self._selected_world_orig),
            "description": raw_world_data.get('description', ''),
            "path_types": self.current_world_path_data_cache
        }
        region_data_arg = None
        if self._selected_region_orig and self._selected_region_orig != "__global__":
            region_json_path = self._get_json_path('region', self._selected_world_orig, self._selected_region_orig)
            raw_region_data = self._load_json(region_json_path) if region_json_path else {}
            region_data_arg = {
                "name": raw_region_data.get('name', self._selected_region_orig),
                "description": raw_region_data.get('description', '')
            }
        location_data_arg = None
        map_type_for_connections = "world"
        active_location_path_cache = self.current_world_path_data_cache
        if self._selected_location_orig and self._selected_location_orig != "__global__":
            location_json_path = self._get_json_path('location', self._selected_world_orig, self._selected_region_orig, self._selected_location_orig)
            raw_location_data = self._load_json(location_json_path) if location_json_path else {}
            location_data_arg = {
                "name": raw_location_data.get('name', self._selected_location_orig),
                "description": raw_location_data.get('description', ''),
                "path_types": self.current_location_path_data_cache
            }
            map_type_for_connections = "location"
            active_location_path_cache = self.current_location_path_data_cache
        map_connections_data_arg = []
        this_setting_name_for_map = setting_name
        map_data_file = None
        dots = []
        lines = []
        user_connection_descs = current_setting_data.get('connections', {}) if isinstance(current_setting_data.get('connections', {}), dict) else {}
        map_data_file = None
        setting_parent_dir = None
        if self._current_setting_file_path_absolute:
            setting_parent_dir = os.path.dirname(self._current_setting_file_path_absolute)
        if self._selected_location_orig and self._selected_location_orig != "__global__":
            parent_dir_for_map = self._get_actual_location_path_for_setting_creation(
                self._selected_world_orig, self._selected_region_orig, self._selected_location_orig
            )
            if parent_dir_for_map:
                map_data_file = os.path.join(parent_dir_for_map, 'location_map_data.json')
        elif self._selected_region_orig and self._selected_region_orig != "__global__" and setting_parent_dir:
            world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
            map_data_file = os.path.join(world_dir, 'world_map_data.json')
        elif self._selected_world_orig:
            world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
            map_data_file = os.path.join(world_dir, 'world_map_data.json')
        if map_data_file and os.path.isfile(map_data_file):
            try:
                with open(map_data_file, 'r', encoding='utf-8') as f:
                    map_data_content = json.load(f)
                dots = map_data_content.get('dots', [])
                lines = map_data_content.get('lines', [])
                this_dot_indices = [i for i, d in enumerate(dots)
                                    if len(d) >= 5 and isinstance(d[4], str) and d[4].strip().lower() == this_setting_name_for_map.lower()]
                if this_dot_indices:
                    for this_dot_index in this_dot_indices:
                        for line in lines:
                            line_meta = line.get('meta', {})
                            start_dot_idx = line_meta.get('start', -1)
                            end_dot_idx = line_meta.get('end', -1)
                            other_index = None
                            if start_dot_idx == this_dot_index: other_index = end_dot_idx
                            elif end_dot_idx == this_dot_index: other_index = start_dot_idx
                            if other_index is not None and 0 <= other_index < len(dots):
                                other_dot = dots[other_index]
                                if len(other_dot) >= 5 and isinstance(other_dot[4], str) and other_dot[4]:
                                    connected_setting_name = other_dot[4].strip()
                                    if connected_setting_name.lower() != this_setting_name_for_map.lower():
                                        map_line_meta_name = line_meta.get('name')
                                        path_type_description = "Default Path Description (Not Specified)"
                                        if map_line_meta_name and map_line_meta_name in active_location_path_cache:
                                            path_type_description = active_location_path_cache[map_line_meta_name].get('description', path_type_description)
                                        elif map_line_meta_name:
                                            if map_line_meta_name in active_location_path_cache:
                                                 path_type_description = active_location_path_cache[map_line_meta_name].get('description', path_type_description)
                                            elif "Small Path (Default)" in map_line_meta_name and "Small Path (Default)" in active_location_path_cache:
                                                path_type_description = active_location_path_cache["Small Path (Default)"].get('description', path_type_description)
                                            elif "Medium Path (Default)" in map_line_meta_name and "Medium Path (Default)" in active_location_path_cache:
                                                path_type_description = active_location_path_cache["Medium Path (Default)"].get('description', path_type_description)
                                            elif "Large Path (Default)" in map_line_meta_name and "Large Path (Default)" in active_location_path_cache:
                                                path_type_description = active_location_path_cache["Large Path (Default)"].get('description', path_type_description)
                                        segment_desc = line_meta.get('desc', None)
                                        user_connection_desc = user_connection_descs.get(connected_setting_name, "")
                                        map_line_meta_name = line_meta.get('name')
                                        path_type = line_meta.get('path_type', 'path')
                                        if (map_line_meta_name is None or map_line_meta_name == 'None') and path_type:
                                            map_line_meta_name = path_type
                                        meta_type = line_meta.get('type')
                                        map_connections_data_arg.append({
                                            "connected_setting_name": connected_setting_name,
                                            "map_line_meta_name": map_line_meta_name,
                                            "path_type_description": path_type_description,
                                            "segment_desc": segment_desc,
                                            "user_connection_desc": user_connection_desc,
                                            "meta_type": meta_type
                                        })
            except Exception as e:
                print(f"Error processing map data for connections: {e}")
        containing_features_data_arg = []
        target_map_view = None
        dot_coords_on_map = None
        source_feature_list_for_desc = []
        for i, d in enumerate(dots):
            if len(d) >= 5 and isinstance(d[4], str) and d[4].strip().lower() == this_setting_name_for_map.lower():
                dot_coords_on_map = (d[0], d[1])
                break
        if hasattr(self, 'world_editor_tab') and self.world_editor_tab and dot_coords_on_map:
            if map_type_for_connections == "location" and hasattr(self.world_editor_tab, 'map_view_location'):
                target_map_view = self.world_editor_tab.map_view_location
                source_feature_list_for_desc = location_data_arg.get("features", []) if location_data_arg else []
            elif map_type_for_connections == "world" and hasattr(self.world_editor_tab, 'map_view_world'):
                target_map_view = self.world_editor_tab.map_view_world
                source_feature_list_for_desc = world_data_arg.get("features", [])
            if target_map_view:
                try:
                    feature_names_at_dot = target_map_view.get_features_at_point(dot_coords_on_map)
                    if feature_names_at_dot:
                        for f_name in feature_names_at_dot:
                            f_desc = "Feature description not found."
                            for feat_detail in source_feature_list_for_desc:
                                if feat_detail.get("name") == f_name:
                                    f_desc = feat_detail.get("description", f_desc)
                                    break
                            containing_features_data_arg.append({"feature_name": f_name, "feature_description": f_desc})
                except Exception as e:
                    print(f"Error getting features at point from map view: {e}")
        try:
            additional_instructions = self.generation_instructions_input.toPlainText().strip()
            model_override = None
            if hasattr(self, 'setting_gen_model_override') and self.setting_gen_model_override.text().strip():
                model_override = self.setting_gen_model_override.text().strip()
            from generate.generate_setting import trigger_setting_generation_async
            generation_thread, generation_worker = trigger_setting_generation_async(
                setting_filepath=setting_filepath,
                setting_name=setting_name,
                current_setting_data=current_setting_data,
                options=options,
                world_data=world_data_arg,
                region_data=region_data_arg,
                location_data=location_data_arg,
                map_connections_data=map_connections_data_arg,
                map_type_for_connections=map_type_for_connections,
                containing_features_data=containing_features_data_arg,
                additional_instructions=additional_instructions,
                cot_model=model_override
            )
            generation_worker.generation_complete.connect(lambda result: self._handle_setting_generation_complete(result, None, setting_name))
            generation_worker.generation_error.connect(lambda error: self._handle_setting_generation_error(error, None))
            self._setting_generation_thread = generation_thread
            self._setting_generation_worker = generation_worker
        except Exception as e:
            print(f"Error during setting generation call or simulation: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Generation Error", f"An error occurred: {e}")

    def _clear_connections_ui(self):
        if hasattr(self, 'connections_content_layout'):
            while self.connections_content_layout.count():
                item = self.connections_content_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        self._connection_desc_edits = {}
        pass

    def _populate_location_connections(self):
        self.current_location_connections = []
        while self.location_connections_layout.count():
            item = self.location_connections_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self._selected_world_orig or not self._selected_location_orig or self._selected_location_orig == "__global__":
            return
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
        world_map_data_file = os.path.join(world_dir, 'world_map_data.json')
        if not os.path.isfile(world_map_data_file):
            return
        try:
            with open(world_map_data_file, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            dots = map_data.get('dots', [])
            lines = map_data.get('lines', [])
            location_dot_indices = []
            location_display_name = None
            if self._selected_location_orig:
                location_path = None
                if self._selected_region_orig and self._selected_region_orig != "__global__":
                    location_path = os.path.join(world_dir, self._selected_region_orig, self._selected_location_orig)
                else:
                    location_path = os.path.join(world_dir, self._selected_location_orig)
                location_json_file = os.path.join(location_path, f"{sanitize_path_name(self._selected_location_orig)}_location.json")
                if os.path.isfile(location_json_file):
                    location_data = self._load_json(location_json_file)
                    location_display_name = location_data.get('name', self._selected_location_orig.replace('_', ' ').title())
                else:
                    location_display_name = self._selected_location_orig.replace('_', ' ').title()
            if not location_display_name:
                return
            for i, dot in enumerate(dots):
                if len(dot) >= 5 and (dot[3] == 'big' or dot[3] == 'medium') and isinstance(dot[4], str) and dot[4].strip() == location_display_name.strip():
                    location_dot_indices.append(i)
            if not location_dot_indices:
                return
            connections_found = 0
            for line_idx, line in enumerate(lines):
                meta = line.get('meta', {})
                start_idx = meta.get('start', -1)
                end_idx = meta.get('end', -1)
                is_connected_to_location = False
                connected_dot_idx = -1
                if start_idx in location_dot_indices:
                    is_connected_to_location = True
                    connected_dot_idx = end_idx
                elif end_idx in location_dot_indices:
                    is_connected_to_location = True
                    connected_dot_idx = start_idx
                if is_connected_to_location and 0 <= connected_dot_idx < len(dots):
                    connected_dot = dots[connected_dot_idx]
                    if len(connected_dot) >= 5 and not ((connected_dot[3] == 'big' or connected_dot[3] == 'medium') and connected_dot[4] == location_display_name):
                        connections_found += 1
                        connection_widget = QWidget()
                        connection_widget.setObjectName("ConnectionListItem")
                        connection_layout = QHBoxLayout(connection_widget)
                        connection_layout.setContentsMargins(5, 5, 5, 5)
                        connection_layout.setSpacing(5)
                        source_name = str(connected_dot[4]) if len(connected_dot) >= 5 and connected_dot[4] else f"Dot {connected_dot_idx}"
                        source_type = str(connected_dot[3]) if len(connected_dot) >= 4 and connected_dot[3] else "unknown"
                        path_type = "Path"
                        if 'path_type' in meta:
                            path_type = meta['path_type']
                        connection_label = QLabel(f"{path_type} from: {source_name}")
                        connection_label.setObjectName("ConnectionLabel")
                        connection_label.setWordWrap(True)
                        settings_dropdown = QComboBox()
                        settings_dropdown.setObjectName("SettingManagerDropdown")
                        settings_dropdown.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
                        settings_dropdown.setMinimumContentsLength(10)
                        settings_dropdown.addItem("Link to setting...")
                        settings = self._get_setting_names_for_location()
                        seen_settings = set()
                        settings_to_add = []
                        for setting_name in settings:
                            if setting_name.lower() not in seen_settings:
                                seen_settings.add(setting_name.lower())
                                settings_to_add.append(setting_name)
                        
                        for setting_name in settings_to_add:
                            settings_dropdown.addItem(setting_name)
                        current_setting = meta.get('associated_setting', '')
                        if current_setting:
                            index = settings_dropdown.findText(current_setting)
                            if index >= 0:
                                settings_dropdown.setCurrentIndex(index)
                        settings_dropdown.currentIndexChanged.connect(
                            lambda idx, line_id=line_idx, dropdown=settings_dropdown: 
                            self._update_line_associated_setting(line_id, dropdown.currentText() if idx > 0 else "")
                        )
                        connection_inner_layout = QVBoxLayout()
                        connection_inner_layout.setContentsMargins(0, 0, 0, 0)
                        connection_inner_layout.setSpacing(2)
                        connection_inner_layout.addWidget(connection_label)
                        connection_inner_layout.addWidget(settings_dropdown)
                        connection_layout.addLayout(connection_inner_layout)
                        self.location_connections_layout.addWidget(connection_widget)
                        self.current_location_connections.append({
                            'line_idx': line_idx,
                            'source_dot_idx': connected_dot_idx,
                            'source_name': source_name,
                            'source_type': source_type,
                            'widget': connection_widget,
                            'dropdown': settings_dropdown
                        })
            self.location_connections_layout.addStretch()
        except Exception as e:
            print(f"Error loading map data for connections: {e}")
            import traceback
            traceback.print_exc()

    def _update_line_associated_setting(self, line_idx, setting_name):
        if not self._selected_world_orig:
            return
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
        world_map_data_file = os.path.join(world_dir, 'world_map_data.json')
        if not os.path.isfile(world_map_data_file):
            return
        try:
            with open(world_map_data_file, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            lines = map_data.get('lines', [])
            dots = map_data.get('dots', [])
            if 0 <= line_idx < len(lines):
                if 'meta' not in lines[line_idx]:
                    lines[line_idx]['meta'] = {}
                if setting_name:
                    lines[line_idx]['meta']['associated_setting'] = setting_name
                elif 'associated_setting' in lines[line_idx]['meta']:
                    del lines[line_idx]['meta']['associated_setting']
                with open(world_map_data_file, 'w', encoding='utf-8') as f:
                    json.dump(map_data, f, indent=2, ensure_ascii=False)
                meta = lines[line_idx].get('meta', {})
                start_idx = meta.get('start', -1)
                end_idx = meta.get('end', -1)
                if start_idx >= 0 and end_idx >= 0 and start_idx < len(dots) and end_idx < len(dots):
                    start_dot = dots[start_idx]
                    end_dot = dots[end_idx]
                    location_dot = None
                    location_dot_idx = -1
                    setting_dot = None
                    if len(start_dot) >= 5 and (start_dot[3] == 'big' or start_dot[3] == 'medium') and start_dot[4]:
                        location_dot = start_dot
                        location_dot_idx = start_idx
                        setting_dot = end_dot
                    elif len(end_dot) >= 5 and (end_dot[3] == 'big' or end_dot[3] == 'medium') and end_dot[4]:
                        location_dot = end_dot
                        location_dot_idx = end_idx
                        setting_dot = start_dot
                    if location_dot and setting_dot and len(setting_dot) >= 5 and setting_dot[3] == 'small' and setting_dot[4]:
                        location_name = str(location_dot[4]).strip()
                        connected_setting_name = str(setting_dot[4]).strip()
                        connected_settings = []
                        for i, line in enumerate(lines):
                            line_meta = line.get('meta', {})
                            line_start = line_meta.get('start', -1)
                            line_end = line_meta.get('end', -1)
                            line_setting = line_meta.get('associated_setting', '')
                            current_line_setting = setting_name if i == line_idx else line_setting
                            if not current_line_setting:
                                continue
                            if line_start == location_dot_idx or line_end == location_dot_idx:
                                other_idx = line_end if line_start == location_dot_idx else line_start
                                if 0 <= other_idx < len(dots):
                                    other_dot = dots[other_idx]
                                    if len(other_dot) >= 5 and other_dot[3] == 'small' and other_dot[4]:
                                        other_setting_name = str(other_dot[4]).strip()
                                        if connected_setting_name == other_setting_name:
                                            continue
                                        if other_setting_name and current_line_setting:
                                            connected_settings.append((other_setting_name, current_line_setting))
                                            connected_settings.append((current_line_setting, other_setting_name))
                        if setting_name and connected_setting_name:
                            self._update_setting_connection(connected_setting_name, setting_name, location_name)
                            self._update_setting_connection(setting_name, connected_setting_name, location_name)
                        if len(connected_settings) > 0:
                            seen_pairs = set()
                            unique_connected_settings = []
                            for source, target in connected_settings:
                                if source == target:
                                    continue
                                pair = (source, target)
                                if pair not in seen_pairs:
                                    seen_pairs.add(pair)
                                    unique_connected_settings.append(pair)
                            for source_setting, target_setting in unique_connected_settings:
                                self._update_setting_connection(source_setting, target_setting, location_name)
                                self._update_setting_connection(target_setting, source_setting, location_name)
                if hasattr(self, 'world_editor_tab') and self.world_editor_tab:
                    self.world_editor_tab.update_world_map()
                if self._selected_setting_orig:
                    current_setting_item = self.list3.currentItem()
                    if current_setting_item:
                        self._on_setting_selected(current_setting_item, None)
        except Exception as e:
            print(f"Error updating map data for connection: {e}")
            import traceback
            traceback.print_exc()
            
    def _update_setting_connection(self, setting_name, connected_setting, location_name):
        if not setting_name or not connected_setting or not self._selected_world_orig:
            return False
        setting_file_path = None
        target_setting_file_path = None
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
        all_regions = []
        try:
            if os.path.exists(world_dir):
                dir_contents = os.listdir(world_dir)
                for item in dir_contents:
                    item_path = os.path.join(world_dir, item)
            all_regions = [region for region in os.listdir(world_dir) 
                          if os.path.isdir(os.path.join(world_dir, region)) 
                          and region.lower() != 'resources']
        except Exception as e:
            print(f"[ERROR] Failed to list regions: {e}")
        if not os.path.exists(world_dir):
            workflow_data_dir = os.path.dirname(os.path.dirname(os.path.dirname(world_dir)))
            settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
            if os.path.exists(settings_dir):
                for world_folder in os.listdir(settings_dir):
                    if world_folder.lower() == self._selected_world_orig.lower():
                        world_dir = os.path.join(settings_dir, world_folder)
                        break
        for region_folder in all_regions:
            region_path = os.path.join(world_dir, region_folder)
            try:
                region_contents = os.listdir(region_path)
                for item in region_contents:
                    item_path = os.path.join(region_path, item)
                region_setting_files = [item for item in region_contents 
                                      if item.lower().endswith('_setting.json')]
                if not setting_file_path:
                    source_setting_filename = f"{sanitize_path_name(setting_name)}_setting.json"
                    potential_file = os.path.join(region_path, source_setting_filename)
                    if os.path.isfile(potential_file):
                        setting_data = self._load_json(potential_file)
                        if setting_data and 'name' in setting_data:
                            if setting_data['name'].lower() == setting_name.lower():
                                setting_file_path = potential_file
                if not target_setting_file_path:
                    target_setting_filename = f"{sanitize_path_name(connected_setting)}_setting.json"
                    potential_file = os.path.join(region_path, target_setting_filename)
                    if os.path.isfile(potential_file):
                        setting_data = self._load_json(potential_file)
                        if setting_data and 'name' in setting_data:
                            if setting_data['name'].lower() == connected_setting.lower():
                                target_setting_file_path = potential_file
                if not setting_file_path or not target_setting_file_path:
                    for setting_file in region_setting_files:
                        file_path = os.path.join(region_path, setting_file)
                        try:
                            setting_data = self._load_json(file_path)
                            if setting_data and 'name' in setting_data:
                                if not setting_file_path and setting_data['name'].lower() == setting_name.lower():
                                    setting_file_path = file_path
                                if not target_setting_file_path and setting_data['name'].lower() == connected_setting.lower():
                                    target_setting_file_path = file_path
                            if setting_file_path and target_setting_file_path:
                                break
                        except Exception as e:
                            print(f"[ERROR] Failed to check region setting file {setting_file}: {e}")
                all_locations = [loc for loc in region_contents
                                if os.path.isdir(os.path.join(region_path, loc))]
                for location_folder in all_locations:
                    location_path = os.path.join(region_path, location_folder)
                    try:
                        location_contents = [f for f in os.listdir(location_path) if f.lower().endswith('_setting.json')]
                    except Exception as loc_e:
                        print(f"[ERROR] Failed to list location contents: {loc_e}")
                        continue
                    if not setting_file_path:
                        source_setting_filename = f"{sanitize_path_name(setting_name)}_setting.json"
                        potential_file = os.path.join(location_path, source_setting_filename)
                        if os.path.isfile(potential_file):
                            setting_data = self._load_json(potential_file)
                            if setting_data and 'name' in setting_data:
                                if setting_data['name'].lower() == setting_name.lower():
                                    setting_file_path = potential_file
                    if not target_setting_file_path:
                        target_setting_filename = f"{sanitize_path_name(connected_setting)}_setting.json"
                        potential_file = os.path.join(location_path, target_setting_filename)
                        if os.path.isfile(potential_file):
                            target_setting_data = self._load_json(potential_file)
                            if target_setting_data and 'name' in target_setting_data:
                                if target_setting_data['name'].lower() == connected_setting.lower():
                                    target_setting_file_path = potential_file
                    if setting_file_path and target_setting_file_path:
                        print(f"[DEBUG] Found both settings, stopping search")
                        break
            except Exception as e:
                print(f"[ERROR] Error searching region {region_folder}: {e}")
                import traceback
                traceback.print_exc()
                continue
            if setting_file_path and target_setting_file_path:
                break
        if not setting_file_path or not target_setting_file_path:
            for region_folder in all_regions:
                region_path = os.path.join(world_dir, region_folder)
                try:
                    region_setting_files = [f for f in os.listdir(region_path) 
                                          if f.lower().endswith('_setting.json')]
                    for setting_file in region_setting_files:
                        file_path = os.path.join(region_path, setting_file)
                        if not setting_file_path:
                            print(f"[DEBUG] Checking region file: {setting_file} for source setting '{setting_name}'")
                            try:
                                setting_data = self._load_json(file_path)
                                if setting_data and 'name' in setting_data:
                                    if setting_data['name'].lower() == setting_name.lower():
                                        setting_file_path = file_path
                                        print(f"[DEBUG] Found source setting in region: {file_path}")
                            except Exception as e:
                                print(f"[ERROR] Failed to load region setting file: {e}")
                        if not target_setting_file_path:
                            try:
                                setting_data = self._load_json(file_path)
                                if setting_data and 'name' in setting_data:
                                    if setting_data['name'].lower() == connected_setting.lower():
                                        target_setting_file_path = file_path
                                        print(f"[DEBUG] Found target setting in region: {file_path}")
                            except Exception as e:
                                print(f"[ERROR] Failed to load region setting file: {e}")
                    for location_folder in os.listdir(region_path):
                        location_path = os.path.join(region_path, location_folder)
                        if not os.path.isdir(location_path):
                            continue
                        if not setting_file_path:
                            for filename in os.listdir(location_path):
                                if filename.lower().endswith('_setting.json'):
                                    potential_file = os.path.join(location_path, filename)
                                    try:
                                        setting_data = self._load_json(potential_file)
                                        if setting_data and 'name' in setting_data:
                                            if setting_data['name'].lower() == setting_name.lower():
                                                setting_file_path = potential_file
                                                break
                                    except Exception as file_e:
                                        print(f"[ERROR] Error checking file {filename}: {file_e}")
                        if not target_setting_file_path:
                            for filename in os.listdir(location_path):
                                if filename.lower().endswith('_setting.json'):
                                    potential_file = os.path.join(location_path, filename)
                                    try:
                                        setting_data = self._load_json(potential_file)
                                        if setting_data and 'name' in setting_data:
                                            if setting_data['name'].lower() == connected_setting.lower():
                                                target_setting_file_path = potential_file
                                                break
                                    except Exception as file_e:
                                        print(f"[ERROR] Error checking file {filename}: {file_e}")
                        if setting_file_path and target_setting_file_path:
                            break
                except Exception as e:
                    print(f"[ERROR] Error in secondary search for region {region_folder}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
                if setting_file_path and target_setting_file_path:
                    break
        if not setting_file_path:
            setting_file_path = self._find_setting_by_name(world_dir, setting_name)
        if not target_setting_file_path:
            target_setting_file_path = self._find_setting_by_name(world_dir, connected_setting)
        if not setting_file_path:
            return False
        if not target_setting_file_path:
            print(f"[ERROR] Failed to find target setting file for '{connected_setting}' after exhaustive search")
        try:
            setting_data = self._load_json(setting_file_path)
            if not setting_data:
                return False
            connections = setting_data.get('connections')
            connection_description = f"Connected through {location_name}"
            if connections is None:
                setting_data['connections'] = [
                    {
                        "connected_setting_name": connected_setting,
                        "description": connection_description,
                        "type": "leads_to"
                    }
                ]
            elif isinstance(connections, dict):
                connections[connected_setting] = connections.get(connected_setting, connection_description)
                setting_data['connections'] = connections
            elif isinstance(connections, list):
                connection_exists = False
                for conn in connections:
                    if isinstance(conn, dict) and conn.get("connected_setting_name") == connected_setting:
                        connection_exists = True
                        break
                
                if not connection_exists:
                    connections.append({
                        "connected_setting_name": connected_setting,
                        "description": connection_description,
                        "type": "leads_to"
                    })
                setting_data['connections'] = connections
                print(f"[DEBUG] Updated list-style connections for '{setting_name}'")
            else:
                setting_data['connections'] = [
                    {
                        "connected_setting_name": connected_setting,
                        "description": connection_description,
                        "type": "leads_to"
                    }
                ]
            if not os.path.isfile(setting_file_path):
                print(f"[ERROR] Source setting file path is invalid: {setting_file_path}")
                return False
            try:
                with open(setting_file_path, 'w', encoding='utf-8') as f:
                    json.dump(setting_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return False
            if target_setting_file_path:
                try:
                    target_setting_data = self._load_json(target_setting_file_path)
                    if not target_setting_data:
                        print(f"[ERROR] Failed to load target setting file: {target_setting_file_path}")
                    else:
                        target_connections = target_setting_data.get('connections')
                        if target_connections is None:
                            target_setting_data['connections'] = [
                                {
                                    "connected_setting_name": setting_name,
                                    "description": connection_description,
                                    "type": "leads_to"
                                }
                            ]
                        elif isinstance(target_connections, dict):
                            target_connections[setting_name] = target_connections.get(setting_name, connection_description)
                            target_setting_data['connections'] = target_connections
                        elif isinstance(target_connections, list):
                            connection_exists = False
                            for conn in target_connections:
                                if isinstance(conn, dict) and conn.get("connected_setting_name") == setting_name:
                                    connection_exists = True
                                    break
                            if not connection_exists:
                                target_connections.append({
                                    "connected_setting_name": setting_name,
                                    "description": connection_description,
                                    "type": "leads_to"
                                })
                            target_setting_data['connections'] = target_connections
                        else:
                            target_setting_data['connections'] = [
                                {
                                    "connected_setting_name": setting_name,
                                    "description": connection_description,
                                    "type": "leads_to"
                                }
                            ]
                        with open(target_setting_file_path, 'w', encoding='utf-8') as f:
                            json.dump(target_setting_data, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"[ERROR] Failed to update target setting: {e}")
                current_setting_display_name = None
                if hasattr(self, 'setting_name_input') and self.setting_name_input:
                    current_setting_display_name = self.setting_name_input.text().strip()
                if current_setting_display_name:
                    current_item = self.list3.currentItem()
                    if current_setting_display_name.lower() == setting_name.lower():
                        if current_item:
                            self._on_setting_selected(current_item, None)
                    elif current_setting_display_name.lower() == connected_setting.lower():
                        if current_item:
                            self._on_setting_selected(current_item, None)
                else:
                    if self._selected_level == 'location':
                        self._try_select_setting_in_current_location(setting_name) or self._try_select_setting_in_current_location(connected_setting)
            return True
        except Exception as e:
            print(f"Error updating setting connection: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _get_setting_names_for_location(self):
        settings = []
        if not self._selected_world_orig or not self._selected_location_orig or self._selected_location_orig == "__global__":
            return settings
        actual_location_path = self._get_actual_location_path_for_setting_creation(
            self._selected_world_orig,
            self._selected_region_orig,
            self._selected_location_orig
        )
        if actual_location_path and os.path.isdir(actual_location_path):
            try:
                for filename in os.listdir(actual_location_path):
                    if filename.lower().endswith('_setting.json'):
                        file_path = os.path.join(actual_location_path, filename)
                        setting_data = self._load_json(file_path)
                        if setting_data and 'name' in setting_data:
                            settings.append(setting_data['name'])
                        else:
                            setting_name = filename.replace('_setting.json', '').replace('_', ' ').title()
                            settings.append(setting_name)
            except Exception as e:
                print(f"[ERROR] Error getting settings from location: {e}")
                import traceback
                traceback.print_exc()
        if self._selected_world_orig and self._selected_region_orig:
            region_path = os.path.join(
                self.workflow_data_dir, 
                'resources', 'data files', 'settings',
                self._selected_world_orig,
                self._selected_region_orig
            )
            if os.path.isdir(region_path):
                try:
                    for filename in os.listdir(region_path):
                        if filename.lower().endswith('_setting.json') and os.path.isfile(os.path.join(region_path, filename)):
                            file_path = os.path.join(region_path, filename)
                            setting_data = self._load_json(file_path)
                            if setting_data and 'name' in setting_data:
                                if setting_data['name'] not in settings:
                                    settings.append(setting_data['name'])
                            else:
                                setting_name = filename.replace('_setting.json', '').replace('_', ' ').title()
                                if setting_name not in settings:
                                    settings.append(setting_name)
                except Exception as e:
                    print(f"[ERROR] Error getting settings from region: {e}")
                    import traceback
                    traceback.print_exc()
        return sorted(settings)

    def _try_select_setting_in_current_location(self, setting_name):
        if not setting_name or not self._selected_location_orig or not self.list3:
            return False
        if self.list3.count() == 0:
            try:
                actual_location_path = self._get_actual_location_path_for_setting_creation(
                    self._selected_world_orig,
                    self._selected_region_orig,
                    self._selected_location_orig
                )
                if actual_location_path:
                    self.populate_settings(actual_location_path)
            except Exception as e:
                print(f"[ERROR] Failed to populate settings list: {e}")
                import traceback
                traceback.print_exc()
                return False
        for i in range(self.list3.count()):
            item = self.list3.item(i)
            if not item:
                continue
            item_text = item.text()
            clean_item_text = item_text.split(" [")[0].strip()
            if clean_item_text.lower() == setting_name.lower():
                self.list3.setCurrentItem(item)
                return True
        return False

    def _find_setting_by_name(self, world_dir, setting_name):
        if not os.path.isdir(world_dir):
            print(f"[ERROR] World directory does not exist: {world_dir}")
            return None
        setting_name_lower = setting_name.lower()
        sanitized_setting_name = sanitize_path_name(setting_name)
        try:
            world_setting_filename = f"{sanitized_setting_name}_setting.json"
            world_setting_path = os.path.join(world_dir, world_setting_filename)
            if os.path.isfile(world_setting_path):
                setting_data = self._load_json(world_setting_path)
                if setting_data and 'name' in setting_data and setting_data['name'].lower() == setting_name_lower:
                    return world_setting_path
        except Exception as e:
            print(f"[ERROR] Error checking world directory for setting: {e}")
        try:
            regions = [region for region in os.listdir(world_dir) 
                      if os.path.isdir(os.path.join(world_dir, region)) 
                      and region.lower() != 'resources']
            for region in regions:
                region_path = os.path.join(world_dir, region)
                try:
                    region_setting_filename = f"{sanitized_setting_name}_setting.json"
                    region_setting_path = os.path.join(region_path, region_setting_filename)
                    if os.path.isfile(region_setting_path):
                        setting_data = self._load_json(region_setting_path)
                        if setting_data and 'name' in setting_data and setting_data['name'].lower() == setting_name_lower:
                            return region_setting_path
                    region_setting_files = [f for f in os.listdir(region_path) 
                                           if f.lower().endswith('_setting.json')]
                    for setting_file in region_setting_files:
                        file_path = os.path.join(region_path, setting_file)
                        try:
                            setting_data = self._load_json(file_path)
                            if setting_data and 'name' in setting_data and setting_data['name'].lower() == setting_name_lower:
                                return file_path
                        except Exception as e:
                            print(f"[ERROR] Failed to load setting file in region: {e}")
                            continue
                except Exception as e:
                    print(f"[ERROR] Error checking region directory for settings: {e}")
                try:
                    locations = [loc for loc in os.listdir(region_path) 
                                if os.path.isdir(os.path.join(region_path, loc))]
                    for location in locations:
                        location_path = os.path.join(region_path, location)
                        try:
                            exact_match_filename = f"{sanitized_setting_name}_setting.json"
                            exact_match_path = os.path.join(location_path, exact_match_filename)
                            if os.path.isfile(exact_match_path):
                                setting_data = self._load_json(exact_match_path)
                                if setting_data and 'name' in setting_data:
                                    if setting_data['name'].lower() == setting_name_lower:
                                        return exact_match_path
                            setting_files = [f for f in os.listdir(location_path) 
                                           if f.lower().endswith('_setting.json')]
                            for setting_file in setting_files:
                                file_path = os.path.join(location_path, setting_file)
                                try:
                                    setting_data = self._load_json(file_path)
                                    if setting_data and 'name' in setting_data:
                                        if setting_data['name'].lower() == setting_name_lower:
                                            return file_path
                                except Exception as e:
                                    continue
                        except Exception as e:
                            continue
                except Exception as e:
                    continue
        except Exception as e:
            return None
        return None

    def _handle_setting_generation_complete(self, result, progress_dialog, setting_name):
        if progress_dialog:
            progress_dialog.accept()
        if result:
            generated_fields = result.get('generated', {})
            file_renamed = result.get('renamed', False)
            old_filepath = result.get('old_filepath')
            new_filepath = result.get('new_filepath')
            current_item = None
            if hasattr(self, 'list3'):
                current_item = self.list3.currentItem()
            if current_item and file_renamed and old_filepath and new_filepath:
                item_data = current_item.data(Qt.UserRole)
                if item_data:
                    item_data['filepath'] = new_filepath
                    item_data['filename'] = os.path.basename(new_filepath)
                    current_item.setData(Qt.UserRole, item_data)
            if current_item and 'name' in generated_fields and generated_fields['name'] != setting_name:
                display_name = generated_fields['name']
                item_data = current_item.data(Qt.UserRole)
                if item_data and item_data.get('is_game_version', False) and not display_name.endswith(" *"):
                    display_name += " *"
                current_item.setText(display_name)
            if current_item:
                self._on_setting_selected(current_item, None)
    
    def _handle_setting_generation_error(self, error, progress_dialog):
        if progress_dialog:
            progress_dialog.accept()
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(self, "Setting Generation Error", 
                           f"Failed to generate setting content:\n\n{error}\n\n"
                           f"Please check your API configuration and try again.")
        print(f"Setting generation error: {error}")

    def _get_main_ui(self):
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'add_rule_sound'):
                return parent
            parent = parent.parentWidget()
        return None

    def _remove_setting_connection(self, setting_name, connected_setting, location_name=None):
        if not setting_name or not connected_setting or not self._selected_world_orig:
            return False
        setting_file_path = None
        target_setting_file_path = None
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self._selected_world_orig)
        all_regions = []
        try:
            if os.path.exists(world_dir):
                all_regions = [region for region in os.listdir(world_dir) 
                             if os.path.isdir(os.path.join(world_dir, region)) 
                             and region.lower() != 'resources']
        except Exception as e:
            print(f"[ERROR] Failed to list regions: {e}")
        if not os.path.exists(world_dir):
            workflow_data_dir = os.path.dirname(os.path.dirname(os.path.dirname(world_dir)))
            settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
            if os.path.exists(settings_dir):
                for world_folder in os.listdir(settings_dir):
                    if world_folder.lower() == self._selected_world_orig.lower():
                        world_dir = os.path.join(settings_dir, world_folder)
                        break
        for region_folder in all_regions:
            region_path = os.path.join(world_dir, region_folder)
            region_contents = os.listdir(region_path)
            region_setting_files = [item for item in region_contents 
                                  if item.lower().endswith('_setting.json')]
            if not setting_file_path:
                source_setting_filename = f"{sanitize_path_name(setting_name)}_setting.json"
                potential_file = os.path.join(region_path, source_setting_filename)
                if os.path.isfile(potential_file):
                    setting_data = self._load_json(potential_file)
                    if setting_data and 'name' in setting_data and setting_data['name'].lower() == setting_name.lower():
                        setting_file_path = potential_file
            if not target_setting_file_path:
                target_setting_filename = f"{sanitize_path_name(connected_setting)}_setting.json"
                potential_file = os.path.join(region_path, target_setting_filename)
                if os.path.isfile(potential_file):
                    setting_data = self._load_json(potential_file)
                    if setting_data and 'name' in setting_data and setting_data['name'].lower() == connected_setting.lower():
                        target_setting_file_path = potential_file
            if not setting_file_path or not target_setting_file_path:
                for setting_file in region_setting_files:
                    file_path = os.path.join(region_path, setting_file)
                    try:
                        setting_data = self._load_json(file_path)
                        if setting_data and 'name' in setting_data:
                            if not setting_file_path and setting_data['name'].lower() == setting_name.lower():
                                setting_file_path = file_path
                            if not target_setting_file_path and setting_data['name'].lower() == connected_setting.lower():
                                target_setting_file_path = file_path
                        if setting_file_path and target_setting_file_path:
                            break
                    except Exception as e:
                        print(f"[ERROR] Failed to check region setting file {setting_file}: {e}")
                all_locations = [loc for loc in region_contents
                                if os.path.isdir(os.path.join(region_path, loc))]
                for location_folder in all_locations:
                    location_path = os.path.join(region_path, location_folder)
                    try:
                        location_contents = [f for f in os.listdir(location_path) if f.lower().endswith('_setting.json')]
                    except Exception as loc_e:
                        print(f"[ERROR] Failed to list location contents: {loc_e}")
                        continue
                    if not setting_file_path:
                        source_setting_filename = f"{sanitize_path_name(setting_name)}_setting.json"
                        potential_file = os.path.join(location_path, source_setting_filename)
                        if os.path.isfile(potential_file):
                            setting_data = self._load_json(potential_file)
                            if setting_data and 'name' in setting_data and setting_data['name'].lower() == setting_name.lower():
                                setting_file_path = potential_file
                    if not target_setting_file_path:
                        target_setting_filename = f"{sanitize_path_name(connected_setting)}_setting.json"
                        potential_file = os.path.join(location_path, target_setting_filename)
                        if os.path.isfile(potential_file):
                            target_setting_data = self._load_json(potential_file)
                            if target_setting_data and 'name' in target_setting_data and target_setting_data['name'].lower() == connected_setting.lower():
                                target_setting_file_path = potential_file
                    if setting_file_path and target_setting_file_path:
                        break
                    for filename in location_contents:
                        potential_file = os.path.join(location_path, filename)
                        try:
                            setting_data = self._load_json(potential_file)
                            if setting_data and 'name' in setting_data:
                                if not setting_file_path and setting_data['name'].lower() == setting_name.lower():
                                    setting_file_path = potential_file
                                if not target_setting_file_path and setting_data['name'].lower() == connected_setting.lower():
                                    target_setting_file_path = potential_file
                        except Exception as e:
                            print(f"[ERROR] Error checking file {filename}: {e}")
                        if setting_file_path and target_setting_file_path:
                            break
                if setting_file_path and target_setting_file_path:
                    break
            if setting_file_path and target_setting_file_path:
                break
        if not setting_file_path or not target_setting_file_path:
            for root, dirs, files in os.walk(world_dir):
                if os.path.basename(root) == 'resources':
                    dirs[:] = []
                    continue
                for filename in files:
                    if filename.lower().endswith('_setting.json'):
                        setting_path = os.path.join(root, filename)
                        try:
                            data = self._load_json(setting_path)
                            if data and 'name' in data:
                                if not setting_file_path and data['name'].lower() == setting_name.lower():
                                    setting_file_path = setting_path
                                if not target_setting_file_path and data['name'].lower() == connected_setting.lower():
                                    target_setting_file_path = setting_path
                                if setting_file_path and target_setting_file_path:
                                    break
                        except Exception as e:
                            print(f"[ERROR] Error checking file {setting_path}: {e}")
                if setting_file_path and target_setting_file_path:
                    break
        connection_removed = False
        if setting_file_path:
            try:
                setting_data = self._load_json(setting_file_path)
                if setting_data:
                    connections = setting_data.get('connections')
                    if connections:
                        if isinstance(connections, dict) and connected_setting in connections:
                            connections.pop(connected_setting)
                            connection_removed = True
                        elif isinstance(connections, list):
                            original_length = len(connections)
                            connections = [conn for conn in connections 
                                         if not (isinstance(conn, dict) and 
                                                conn.get("connected_setting_name") == connected_setting)]
                            connection_removed = len(connections) < original_length
                            setting_data['connections'] = connections
                        if connection_removed:
                            self._save_json(setting_file_path, setting_data)
                            print(f"[DEBUG] Removed connection to '{connected_setting}' from '{setting_name}'")
            except Exception as e:
                print(f"[ERROR] Failed to update source setting: {e}")
        if target_setting_file_path:
            try:
                target_setting_data = self._load_json(target_setting_file_path)
                if target_setting_data:
                    target_connections = target_setting_data.get('connections')
                    if target_connections:
                        if isinstance(target_connections, dict) and setting_name in target_connections:
                            target_connections.pop(setting_name)
                            connection_removed = True
                        elif isinstance(target_connections, list):
                            original_length = len(target_connections)
                            target_connections = [conn for conn in target_connections 
                                               if not (isinstance(conn, dict) and 
                                                      conn.get("connected_setting_name") == setting_name)]
                            connection_removed = len(target_connections) < original_length
                            target_setting_data['connections'] = target_connections
                        if connection_removed:
                            self._save_json(target_setting_file_path, target_setting_data)
                            print(f"[DEBUG] Removed connection to '{setting_name}' from '{connected_setting}'")
            except Exception as e:
                print(f"[ERROR] Failed to update target setting: {e}")
        return connection_removed

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    colors = {"base_color": "#00FF66", "darker_bg": "#1E1E1E", "bg_color": "#2C2C2C", "highlight": "rgba(0, 255, 102, 0.6)", "contrast": 0.5}
    test_dir = os.path.join(os.getcwd(), "test_workflow_data")
    test_settings_path = os.path.join(test_dir, "resources", "data files", "settings", "testworld1")
    os.makedirs(test_settings_path, exist_ok=True)
    test_world_json_path = os.path.join(test_settings_path, "testworld1_world.json")
    with open(test_world_json_path, "w") as f:
        f.write("{}")
    widget = SettingManagerWidget(colors, test_dir)
    widget.setStyleSheet(f"""
        QWidget#SettingManagerContainer {{ background-color: {colors['bg_color']}; }}
        QLabel#SettingManagerLabel {{ color: {colors['base_color']}; }}
        QLabel#SettingManagerEditLabel {{ color: #DDDDDD; font: 9pt "Consolas"; }} /* Style for edit labels */
        QLineEdit#SettingManagerNameInput {{ 
            color: {colors['base_color']};
            background-color: {colors['darker_bg']};
            border: 1px solid {colors['base_color']};
            border-radius: 3px;
            padding: 2px;
            font: 10pt "Consolas";
        }}
        QTextEdit#SettingManagerDescInput {{
            color: {colors['base_color']};
            background-color: {colors['darker_bg']};
            border: 1px solid {colors['base_color']};
            border-radius: 3px;
            padding: 2px;
            font: 10pt "Consolas";
        }}
        QListWidget#SettingManagerList {{
            background-color: {colors['darker_bg']};
            color: {colors['base_color']};
            border: 1px solid {colors['base_color']};
            alternate-background-color: {colors['bg_color']};
            border-radius: 3px;
        }}
        QListWidget#SettingManagerList::item:selected {{
            background-color: {colors['highlight']};
            color: white;
        }}
    """)
    widget.show()
    sys.exit(app.exec_())
