import os
import json
import random
import copy
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                           QTextEdit, QLineEdit, QTabWidget, QScrollArea,
                           QSizePolicy, QListWidget, QMessageBox, QInputDialog, QTableWidget, QTableWidgetItem, QMenu, QAction, QSplitter, QSpinBox, QHeaderView, QCheckBox, QFrame, QButtonGroup, QRadioButton, QStackedWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from generate.generate_random_list import generate_random_list
from PyQt5.QtWidgets import QApplication


class RandomGeneratorsWidget(QWidget):
    def __init__(self, workflow_data_dir, parent=None, theme_settings=None):
        super().__init__(parent)
        self.parent = parent
        self.workflow_data_dir = workflow_data_dir
        self.theme_settings = theme_settings or {}
        self.base_color = self.theme_settings.get('base_color', '#00ff66')
        self.text_color = self.theme_settings.get('text_color', '#ffffff')
        self.generator_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'generators')
        self.resource_generator_dir = self.generator_dir
        self.session_generator_dir = os.path.join(self.workflow_data_dir, 'game', 'generators')
        if not os.path.exists(self.session_generator_dir):
            os.makedirs(self.session_generator_dir, exist_ok=True)
        self.generator_mode = 'resource'
        self.is_loading = False
        self.initUI()
        self.load_generators()


    def _get_main_ui(self):
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'add_rule_sound'):
                return parent
            parent = parent.parentWidget()
        return None

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create scroll area for the entire content
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(f"background-color: {self.theme_settings.get('bg_color', '#2B2B2B')}; border: none;")
        
        # Create a container widget for the scroll area
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet(f"background-color: {self.theme_settings.get('bg_color', '#2B2B2B')};")
        self.scroll_content_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_content_layout.setSpacing(10)
        
        title_label = QLabel("Random Generators")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Consolas', 12, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.base_color};")
        self.scroll_content_layout.addWidget(title_label)
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setObjectName("ResourceSessionTabs")
        self.mode_tabs.setDocumentMode(True)
        self.mode_tabs.setFixedHeight(40)
        self.resource_tab = QWidget()
        self.mode_tabs.addTab(self.resource_tab, "Resource Files")
        self.session_tab = QWidget()
        self.mode_tabs.addTab(self.session_tab, "Current Game")
        self.mode_tabs.setTabPosition(QTabWidget.North)
        self.mode_tabs.tabBar().setExpanding(True)
        tab_style = f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar {{
                alignment: center;
            }}
            QTabWidget {{
                alignment: center;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {self.base_color};
                padding: 8px 16px;
                min-width: 140px; /* Make tabs wider */
                border: 1px solid {self.base_color};
                border-radius: 4px;
                margin-right: 4px;
                text-align: center; /* Center text */
            }}
            QTabBar::tab:selected {{
                background-color: {self.base_color};
                color: #ffffff; /* White text for contrast on selected tab */
            }}
            QTabBar::tab:!selected {{
                background-color: transparent;
                color: {self.base_color};
            }}
            QTabWidget::tab-bar {{
                alignment: center; /* Center the tab bar */
                border-bottom: 2px solid {self.base_color}; /* Add line under tabs */
            }}
        """
        self.mode_tabs.setStyleSheet(tab_style)
        self.mode_tabs.currentChanged.connect(self._handle_tab_change)
        self.scroll_content_layout.addSpacing(5)
        self.scroll_content_layout.addWidget(self.mode_tabs)
        self.scroll_content_layout.addSpacing(5)
        top_section = QHBoxLayout()
        top_section.setContentsMargins(0, 0, 0, 0)
        top_section_widget = QWidget()
        top_section_widget.setLayout(top_section)
        top_section_widget.setMaximumHeight(200)
        list_col = QVBoxLayout()
        list_col.setContentsMargins(0, 0, 5, 0)
        list_header = QLabel("Generators")
        list_header.setAlignment(Qt.AlignCenter)
        list_header.setFont(QFont('Consolas', 10, QFont.Bold))
        list_col.addWidget(list_header)
        self.generator_list = QListWidget()
        self.generator_list.setObjectName("RulesList")
        self.generator_list.setMinimumHeight(150)
        self.generator_list.setFont(QFont('Consolas', 10))
        self.generator_list.setSelectionMode(self.generator_list.SingleSelection)
        self.generator_list.setAlternatingRowColors(True)
        bg_color = self.theme_settings.get('bg_color', '#404040')
        darker_bg = self.theme_settings.get('darker_bg', '#303030')
        self.generator_list.setStyleSheet(f"""
            background-color: {darker_bg};
            color: {self.base_color};
            alternate-background-color: {bg_color};
            border: 1px solid {self.base_color};
            border-radius: 3px;
            padding: 3px;
        """)
        self.generator_list.setFocusPolicy(Qt.NoFocus)
        list_col.addWidget(self.generator_list, 1)

        list_btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add Generator")
        self.add_btn.setStyleSheet(f"""
            background-color: {self.base_color}; 
            color: #ffffff;
            padding: 8px 12px;
        """)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setStyleSheet(f"""
            background-color: {self.base_color}; 
            color: #ffffff;
            padding: 8px 12px;
        """)
        self.duplicate_btn = QPushButton("Duplicate")
        self.duplicate_btn.setStyleSheet(f"""
            background-color: {self.base_color}; 
            color: #ffffff;
            padding: 8px 12px;
        """)
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setStyleSheet(f"""
            background-color: {self.base_color}; 
            color: #ffffff;
            padding: 8px 12px;
        """)
        list_btn_row.addWidget(self.add_btn)
        list_btn_row.addWidget(self.delete_btn)
        list_btn_row.addWidget(self.duplicate_btn)
        list_btn_row.addWidget(self.rename_btn)
        list_col.addLayout(list_btn_row)
        top_section.addLayout(list_col, 1)
        sample_col = QVBoxLayout()
        sample_col.setContentsMargins(5, 0, 5, 0)
        sample_header = QLabel("Sample")
        sample_header.setAlignment(Qt.AlignCenter)
        sample_header.setFont(QFont('Consolas', 10, QFont.Bold))
        sample_col.addWidget(sample_header)
        self.count_spinner = QSpinBox()
        self.count_spinner.setMinimum(1)
        self.count_spinner.setMaximum(100)
        self.count_spinner.setValue(1)
        self.count_spinner.setSuffix(" results")
        darker_bg = self.theme_settings.get('darker_bg', '#303030')
        self.count_spinner.setStyleSheet(f"""
            QSpinBox {{
                background-color: {darker_bg};
                color: {self.base_color};
                border: 1px solid {self.base_color};
                border-radius: 3px;
                padding: 2px 6px;
                selection-background-color: {self.base_color};
                selection-color: #000000;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {self.base_color};
                border: none;
                width: 16px;
            }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{
                width: 10px;
                height: 10px;
            }}
        """)
        sample_col.addWidget(self.count_spinner)
        self.generate_results = QTextEdit()
        self.generate_results.setReadOnly(True)
        self.generate_results.setFont(QFont('Consolas', 10))
        darker_bg = self.theme_settings.get('darker_bg', '#303030')
        self.generate_results.setStyleSheet(f"""
            background-color: {darker_bg};
            color: {self.base_color};
            border: 1px solid {self.base_color};
            border-radius: 3px;
            padding: 5px;
        """)
        self.generate_results.setMaximumHeight(150)
        sample_col.addWidget(self.generate_results, 1)
        self.sample_btn = QPushButton("Sample")
        self.sample_btn.setStyleSheet(f"""
            background-color: {self.base_color}; 
            color: #ffffff;
            padding: 8px 12px;
        """)
        self.sample_btn.clicked.connect(self.generate_sample)
        sample_col.addWidget(self.sample_btn)
        new_generate_col = QVBoxLayout()
        new_generate_col.setContentsMargins(5, 0, 0, 0) 
        new_generate_header = QLabel("Generate") 
        new_generate_header.setAlignment(Qt.AlignCenter)
        new_generate_header.setFont(QFont('Consolas', 10, QFont.Bold))
        new_generate_col.addWidget(new_generate_header)
        self.generate_scope_group = QButtonGroup(self)
        self.permutate_radio = QRadioButton("Permutate")
        self.new_list_radio = QRadioButton("New Random List")
        radio_style = f"""
            QRadioButton {{
                color: {self.base_color};
                font-family: Consolas;
                font-size: 10pt;
                font-weight: bold;
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {self.base_color};
                border-radius: 8px;
                background: transparent;
            }}
            QRadioButton::indicator:unchecked {{
                border: 1px solid {self.base_color};
                background: transparent;
                border-radius: 8px;
            }}
            QRadioButton::indicator:checked {{
                background-color: {self.base_color};
                border-radius: 8px;
            }}
        """
        self.permutate_radio.setStyleSheet(radio_style)
        self.new_list_radio.setStyleSheet(radio_style)
        self.generate_scope_group.addButton(self.permutate_radio)
        self.generate_scope_group.addButton(self.new_list_radio)
        self.new_list_radio.setChecked(True)
        self.permutate_options_widget = QWidget()
        permutate_options_layout = QHBoxLayout(self.permutate_options_widget)
        permutate_options_layout.setContentsMargins(0, 0, 0, 0)
        self.objects_checkbox = QCheckBox("Objects")
        self.weights_checkbox = QCheckBox("Weights")
        checkbox_style = f"""
            QCheckBox {{
                color: {self.base_color};
                font-family: Consolas;
                font-size: 10pt;
                font-weight: bold;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {self.base_color};
            }}
        """
        self.objects_checkbox.setStyleSheet(checkbox_style)
        self.weights_checkbox.setStyleSheet(checkbox_style)
        permutate_options_layout.addWidget(self.objects_checkbox)
        permutate_options_layout.addWidget(self.weights_checkbox)
        permutate_options_layout.addStretch()
        self.list_source_group = QButtonGroup(self)
        self.resource_file_radio = QRadioButton("Resource File")
        self.current_game_radio = QRadioButton("Current Game")
        self.resource_file_radio.setStyleSheet(radio_style)
        self.current_game_radio.setStyleSheet(radio_style)
        self.list_source_group.addButton(self.resource_file_radio)
        self.list_source_group.addButton(self.current_game_radio)
        self.resource_file_radio.setChecked(True)
        self.new_list_options_widget = QWidget()
        new_list_options_layout = QHBoxLayout(self.new_list_options_widget)
        new_list_options_layout.setContentsMargins(0, 0, 0, 0)
        new_list_options_layout.addStretch()
        new_list_options_layout.addWidget(self.resource_file_radio)
        new_list_options_layout.addWidget(self.current_game_radio)
        new_list_options_layout.addStretch()
        self.new_generator_name_widget = QWidget()
        new_generator_name_layout = QHBoxLayout(self.new_generator_name_widget)
        new_generator_name_layout.setContentsMargins(0, 0, 0, 0)
        name_label = QLabel("Name:")
        name_label.setFont(QFont('Consolas', 10))
        name_label.setStyleSheet(f"color: {self.base_color};")
        self.new_generator_name_input = QLineEdit()
        self.new_generator_name_input.setPlaceholderText("Optional name (leave empty for AI to name)")
        self.new_generator_name_input.setMaximumWidth(300)
        self.new_generator_name_input.setStyleSheet(f"""
            background-color: {darker_bg};
            color: {self.base_color};
            border: 1px solid {self.base_color};
            border-radius: 3px;
            padding: 3px;
        """)
        new_generator_name_layout.addStretch()
        new_generator_name_layout.addWidget(name_label)
        new_generator_name_layout.addWidget(self.new_generator_name_input)
        new_generator_name_layout.addStretch()
        self.new_generator_name_widget.setVisible(True)
        new_generate_col.addWidget(self.new_list_options_widget)
        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.new_list_radio)
        radio_layout.addWidget(self.permutate_radio)
        radio_layout.addStretch()
        options_container = QStackedWidget()
        options_container.addWidget(self.new_generator_name_widget)
        options_container.addWidget(self.permutate_options_widget)
        self.new_list_radio.toggled.connect(lambda checked: options_container.setCurrentIndex(0) if checked else None)
        self.permutate_radio.toggled.connect(lambda checked: options_container.setCurrentIndex(1) if checked else None)
        options_container.setCurrentIndex(0 if self.new_list_radio.isChecked() else 1)
        radio_layout.addWidget(options_container)
        new_generate_col.addLayout(radio_layout)
        self.new_generate_input = QTextEdit()
        self.new_generate_input.setFont(QFont('Consolas', 10))
        self.new_generate_input.setPlaceholderText("Enter instructions for generation or permutation here...")
        self.new_generate_input.setStyleSheet(f"""
            background-color: {darker_bg};
            color: {self.base_color};
            border: 1px solid {self.base_color};
            border-radius: 3px;
            padding: 5px;
        """)
        self.new_generate_input.setMaximumHeight(150)
        new_generate_col.addWidget(self.new_generate_input, 1)
        self.new_generate_btn = QPushButton("Generate")
        self.new_generate_btn.setStyleSheet(f"""
            background-color: {self.base_color}; 
            color: #ffffff;
            padding: 8px 12px;
        """)
        self.new_generate_btn.clicked.connect(self._handle_generate_button)
        new_generate_col.addWidget(self.new_generate_btn)
        top_section.addLayout(list_col, 1)
        top_section.addLayout(sample_col, 1)
        top_section.addLayout(new_generate_col, 1)
        self.scroll_content_layout.addWidget(top_section_widget)
        self.scroll_content_layout.addSpacing(10)
        self.detail_widget = QWidget()
        main_detail_layout = QVBoxLayout(self.detail_widget)
        main_detail_layout.setContentsMargins(5, 5, 5, 5)
        main_detail_layout.setSpacing(10)
        self.hierarchy_info = QLabel("Generator:")
        self.hierarchy_info.setAlignment(Qt.AlignCenter)
        self.hierarchy_info.setFont(QFont('Consolas', 10))
        self.hierarchy_info.setStyleSheet(f"color: {self.base_color};")
        main_detail_layout.addWidget(self.hierarchy_info)
        levels_control_header = QHBoxLayout()
        levels_control_header.addStretch()
        level_label = QLabel("Tables:")
        level_label.setFont(QFont('Consolas', 10, QFont.Bold))
        level_label.setStyleSheet(f"color: {self.base_color};")
        levels_control_header.addWidget(level_label)
        self.add_level_btn = QPushButton("+")
        self.add_level_btn.setFixedSize(32, 32)
        self.remove_level_btn = QPushButton("-")
        self.remove_level_btn.setFixedSize(32, 32)
        levels_control_header.addWidget(self.remove_level_btn)
        levels_control_header.addWidget(self.add_level_btn)
        main_detail_layout.addLayout(levels_control_header)
        self.add_level_btn.clicked.connect(self._add_table_display_column)
        self.remove_level_btn.clicked.connect(self._remove_table_display_column)
        self.hierarchy_splitter = QSplitter(Qt.Horizontal)
        main_detail_layout.addWidget(self.hierarchy_splitter, 1)
        self.table_displays = []
        self._add_table_display_column()
        self.detail_widget.setLayout(main_detail_layout)
        self.scroll_content_layout.addWidget(self.detail_widget)
        
        # Set the scroll content as the scroll area widget
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        self.add_btn.clicked.connect(self.add_generator)
        self.delete_btn.clicked.connect(self.delete_generator)
        self.duplicate_btn.clicked.connect(self.duplicate_generator)
        self.rename_btn.clicked.connect(self.rename_generator)
        self.generator_list.itemSelectionChanged.connect(self.on_generator_selected)
        self.setLayout(layout)

    def load_generators(self):
        self.generator_list.clear()
        if not os.path.exists(self.generator_dir):
            os.makedirs(self.generator_dir)
        self.generator_files = {}
        for fname in sorted(os.listdir(self.generator_dir)):
            if fname.endswith('.json'):
                path = os.path.join(self.generator_dir, fname)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        name = data.get('name', os.path.splitext(fname)[0])
                except Exception:
                    name = os.path.splitext(fname)[0]
                
                self.generator_list.addItem(name)
                self.generator_files[name] = fname

    def add_generator(self):
        base = "untitled_generator"
        idx = 1
        while True:
            fname = f"{base}{idx if idx > 1 else ''}.json"
            path = os.path.join(self.generator_dir, fname)
            if not os.path.exists(path):
                break
            idx += 1
        display_name = f"Untitled Generator {idx}"
        data = {
            "name": display_name, 
            "description": "", 
            "tables": [
                {"title": "Table 1", "items": []}
            ]
        }
        if not os.path.exists(self.generator_dir):
            os.makedirs(self.generator_dir)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Play add sound
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None
        
        self.load_generators()
        for i in range(self.generator_list.count()):
            if self.generator_list.item(i).text() == display_name:
                self.generator_list.setCurrentRow(i)
                break

    def delete_generator(self):
        row = self.generator_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a generator to delete.")
            return
        name = self.generator_list.item(row).text()
        self.generator_list.blockSignals(True)
        self.generator_list.clearSelection()
        self.generator_list.blockSignals(False)
        self.current_data = {"tables": [], "name": ""}
        if name in self.generator_files:
            filename = self.generator_files[name]
            path = os.path.join(self.generator_dir, filename)
            if os.path.exists(path):
                try:
                    os.remove(path)
                    main_ui = self._get_main_ui()
                    if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                        try:
                            main_ui.delete_rule_sound.play()
                        except Exception:
                            main_ui.delete_rule_sound = None
                    del self.generator_files[name]
                    self.load_generators()
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete file: {e}")
        possible_filenames = [
            f"{name}.json",
            f"{name.lower()}.json",
            f"{name.replace(' ', '_')}.json",
            f"{name.lower().replace(' ', '_')}.json"
        ]
        for possible_name in possible_filenames:
            path = os.path.join(self.generator_dir, possible_name)
            if os.path.exists(path):
                try:
                    os.remove(path)
                    main_ui = self._get_main_ui()
                    if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                        try:
                            main_ui.delete_rule_sound.play()
                        except Exception:
                            main_ui.delete_rule_sound = None
                    if name in self.generator_files:
                        del self.generator_files[name]
                    self.load_generators()
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete file: {e}")
        QMessageBox.warning(self, "File Not Found", f"Could not find the generator file to delete.")

    def rename_generator(self):
        row = self.generator_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a generator to rename.")
            return
        old_name = self.generator_list.item(row).text()
        new_name, ok = QInputDialog.getText(self, "Rename Generator", "Enter new name:", text=old_name)
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        if old_name in self.generator_files:
            filename = self.generator_files[old_name]
            old_path = os.path.join(self.generator_dir, filename)
            if os.path.exists(old_path):
                try:
                    with open(old_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data['name'] = new_name
                    sanitized_name = new_name.lower().replace(' ', '_')
                    new_filename = f"{sanitized_name}.json"
                    new_path = os.path.join(self.generator_dir, new_filename)
                    if os.path.exists(new_path) and os.path.normpath(old_path) != os.path.normpath(new_path):
                        QMessageBox.warning(self, "File Exists", f"Cannot rename file to '{new_filename}' because it already exists.")
                        with open(old_path, 'w', encoding='utf-8') as wf:
                            json.dump(data, wf, indent=2, ensure_ascii=False)
                        self.generator_files[new_name] = filename
                        if old_name in self.generator_files and old_name != new_name:
                            del self.generator_files[old_name]
                        current_item = self.generator_list.currentItem()
                        if current_item:
                            current_item.setText(new_name)
                        self.play_sound('rename')
                        return
                    with open(old_path, 'w', encoding='utf-8') as wf:
                        json.dump(data, wf, indent=2, ensure_ascii=False)
                    if os.path.normpath(old_path) != os.path.normpath(new_path):
                        os.rename(old_path, new_path)
                        self.generator_files[new_name] = new_filename
                        if old_name in self.generator_files and old_name != new_name:
                            del self.generator_files[old_name]
                        current_item = self.generator_list.currentItem()
                        if current_item:
                            current_item.setText(new_name)
                            current_item.setData(Qt.UserRole, new_path)
                    self.play_sound('rename')
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to rename generator: {e}")
                    return
        possible_filenames = [
            f"{old_name}.json",
            f"{old_name.lower()}.json",
            f"{old_name.replace(' ', '_')}.json",
            f"{old_name.lower().replace(' ', '_')}.json"
        ]
        for possible_name in possible_filenames:
            old_path = os.path.join(self.generator_dir, possible_name)
            if os.path.exists(old_path):
                try:
                    with open(old_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    data['name'] = new_name
                    sanitized_name = new_name.lower().replace(' ', '_')
                    new_filename = f"{sanitized_name}.json"
                    new_path = os.path.join(self.generator_dir, new_filename)
                    if os.path.exists(new_path) and os.path.normpath(old_path) != os.path.normpath(new_path):
                        QMessageBox.warning(self, "File Exists", f"Cannot rename file to '{new_filename}' because it already exists.")
                        with open(old_path, 'w', encoding='utf-8') as wf:
                            json.dump(data, wf, indent=2, ensure_ascii=False)
                        self.generator_files[new_name] = possible_name
                        if old_name in self.generator_files and old_name != new_name:
                            del self.generator_files[old_name]
                        current_item = self.generator_list.currentItem()
                        if current_item:
                            current_item.setText(new_name)
                        self.play_sound('rename')
                        return
                    with open(old_path, 'w', encoding='utf-8') as wf:
                        json.dump(data, wf, indent=2, ensure_ascii=False)
                    if os.path.normpath(old_path) != os.path.normpath(new_path):
                        os.rename(old_path, new_path)
                        self.generator_files[new_name] = new_filename
                        if old_name in self.generator_files and old_name != new_name:
                            del self.generator_files[old_name]
                        current_item = self.generator_list.currentItem()
                        if current_item:
                            current_item.setText(new_name)
                            current_item.setData(Qt.UserRole, new_path)
                    self.play_sound('rename')
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to rename generator: {e}")
                    return
        QMessageBox.warning(self, "File Not Found", f"Could not find the generator file to rename.")

    def duplicate_generator(self):
        row = self.generator_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a generator to duplicate.")
            return
        selected_name = self.generator_list.item(row).text()
        source_filename = self.generator_files.get(selected_name)
        if not source_filename:
            sanitized_name = selected_name.lower().replace(' ', '_')
            possible_filename = f"{sanitized_name}.json"
            possible_path = os.path.join(self.generator_dir, possible_filename)
            if os.path.exists(possible_path):
                source_filename = possible_filename
            else:
                QMessageBox.warning(self, "File Not Found", f"Could not find the generator file to duplicate.")
                return
        source_path = os.path.join(self.generator_dir, source_filename)
        if not os.path.exists(source_path):
            QMessageBox.warning(self, "File Not Found", f"Could not find the generator file to duplicate.")
            return
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                source_data = json.load(f)
            new_data = copy.deepcopy(source_data)
            original_name = new_data.get('name', selected_name)
            new_name_base = original_name
            match = re.match(r"^(.*?)_copy(?:\d+)?$", original_name)
            if match:
                new_name_base = match.group(1)
            counter = 1
            new_name = f"{new_name_base}_copy"
            new_filename = f"{new_name.lower().replace(' ', '_')}.json"
            new_path = os.path.join(self.generator_dir, new_filename)
            while os.path.exists(new_path):
                counter += 1
                new_name = f"{new_name_base}_copy{counter}"
                new_filename = f"{new_name.lower().replace(' ', '_')}.json"
                new_path = os.path.join(self.generator_dir, new_filename)
            new_data['name'] = new_name
            if 'description' in new_data and new_data['description']:
                new_data['description'] = f"{new_data['description']} (Copy)"
            else:
                new_data['description'] = f"Copy of {original_name}"
            with open(new_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
            self.play_sound('add')
            self.load_generators()
            for i in range(self.generator_list.count()):
                if self.generator_list.item(i).text() == new_name:
                    self.generator_list.setCurrentRow(i)
                    break
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to duplicate generator: {e}")

    def on_generator_selected(self):
        self.is_loading = True
        while self.hierarchy_splitter.count() > 0:
            widget_to_remove = self.hierarchy_splitter.widget(0)
            widget_to_remove.setParent(None)
            widget_to_remove.deleteLater()
        self.table_displays.clear()
        row = self.generator_list.currentRow()
        if row < 0:
            for table_display in self.table_displays:
                table_display['table_widget'].setRowCount(0)
                if table_display.get('title_editor'):
                    table_display['title_editor'].setText("")
            self.hierarchy_info.setText("Generator:")
            return
        name = self.generator_list.item(row).text()
        fname = self.generator_files.get(name)
        if not fname:
            sanitized_name = name.lower().replace(' ', '_')
            possible_filename = f"{sanitized_name}.json"
            possible_path = os.path.join(self.generator_dir, possible_filename)
            if os.path.exists(possible_path):
                self.generator_files[name] = possible_filename
                fname = possible_filename
            else:
                found_file = None
                if os.path.exists(self.generator_dir):
                    for filename in os.listdir(self.generator_dir):
                        if filename.endswith('.json'):
                            try:
                                file_path = os.path.join(self.generator_dir, filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    file_data = json.load(f)
                                    if file_data.get('name') == name:
                                        found_file = filename
                                        break
                            except (json.JSONDecodeError, OSError):
                                continue
                if found_file:
                    self.generator_files[name] = found_file
                    fname = found_file
                    self.current_data = {"tables": [], "name": name}
                    while len(self.table_displays) > 0:
                        self._remove_table_display_column()
                    if not self.table_displays:
                        self._add_table_display_column()
                    if self.table_displays:
                        self.table_displays[0]['title_editor'].setText("Table 1")
                        self._populate_single_table(self.table_displays[0]['table_widget'], [])
                    self.is_loading = False
                    return
        path = os.path.join(self.generator_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.current_data = json.load(f)
        except FileNotFoundError:
            self.current_data = {"tables": [], "name": name}
            if name in self.generator_files:
                del self.generator_files[name]
            self.load_generators()
            return
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Error loading generator '{name}': {e}")
            self.current_data = {"tables": [], "name": name}
        finally:
            if 'tables' not in self.current_data or not isinstance(self.current_data['tables'], list):
                self.current_data['tables'] = []
                if 'hierarchy' in self.current_data and isinstance(self.current_data['hierarchy'], dict):
                    first_level_keys = [k for k in self.current_data['hierarchy'].keys() if k not in ['values', 'weight']]
                    migrated_items = []
                    if first_level_keys:
                        for key in first_level_keys:
                            item_data = self.current_data['hierarchy'][key]
                            migrated_items.append({
                                "name": key,
                                "weight": item_data.get("weight", 1),
                                "generate": False
                            })
                    elif "values" in self.current_data['hierarchy']:
                         for val_item in self.current_data['hierarchy'].get("values", []):
                            migrated_items.append({
                                "name": val_item.get("name", "Unknown"),
                                "weight": val_item.get("weight", 1),
                                "generate": val_item.get("generate", False)
                            })
                    table_title = "Imported Table 1"
                    if 'titles' in self.current_data and self.current_data['titles']:
                        if isinstance(self.current_data['titles'][0], list) and self.current_data['titles'][0]:
                            table_title = self.current_data['titles'][0][0]
                        elif isinstance(self.current_data['titles'][0], str):
                            table_title = self.current_data['titles'][0]
                    if migrated_items:
                        self.current_data['tables'].append({'title': table_title, 'items': migrated_items})
                if not self.current_data['tables']:
                     self.current_data['tables'].append({'title': 'Table 1', 'items': []})
            num_data_tables = len(self.current_data.get('tables', []))
            if num_data_tables == 0:
                self.current_data.setdefault('tables', []).append({'title': 'Table 1', 'items': []})
                num_data_tables = 1
            current_ui_tables = len(self.table_displays)
            while current_ui_tables < num_data_tables:
                self._add_table_display_column()
                current_ui_tables += 1
            while current_ui_tables > num_data_tables:
                self._remove_table_display_column()
                current_ui_tables -= 1
            for idx, table_data in enumerate(self.current_data.get('tables', [])):
                if idx < len(self.table_displays):
                    display_elements = self.table_displays[idx]
                    display_elements['title_editor'].setText(table_data.get('title', f"Table {idx + 1}"))
                    self._populate_single_table(display_elements['table_widget'], table_data.get('items', []))
            self.hierarchy_info.setText(f"Generator: <span style='color: {self.base_color};'>{name}</span>")
            self.hierarchy_info.setTextFormat(Qt.RichText)
            self.is_loading = False


    def _populate_single_table(self, table_widget, items_data):
        table_widget.setRowCount(0)
        for item in items_data:
                self._add_row_to_table(
                    table_widget,
                    item.get("name", ""),
                    item.get("weight", 1),
                    item.get("generate", False)
                )

    def _add_row_to_table(self, table_widget, name, weight=1, generate=False):
        row = table_widget.rowCount()
        table_widget.insertRow(row)
        name_item = QTableWidgetItem(name)
        table_widget.setItem(row, 0, name_item)
        weight_item = QTableWidgetItem(str(weight))
        weight_item.setTextAlignment(Qt.AlignCenter)
        table_widget.setItem(row, 1, weight_item)
        check_widget = QWidget()
        check_layout = QHBoxLayout(check_widget)
        check_layout.setContentsMargins(0, 0, 0, 0)
        check_layout.setAlignment(Qt.AlignCenter)
        checkbox = QCheckBox()
        checkbox.setChecked(generate)
        checkbox.stateChanged.connect(lambda state, r=row, c=2: self._handle_checkbox_change(r, c))
        check_layout.addWidget(checkbox)
        table_widget.setCellWidget(row, 2, check_widget)
        return row

    def add_list(self):
        QMessageBox.information(self, "Obsolete", 
                               "This function is no longer used. Use the 'Add' button under each table.")

    def _handle_checkbox_change(self, row, col):
        self._save_current_generator()

    def _add_table_display_column(self):
        col_idx = len(self.table_displays)
        column_widget = QWidget()
        column_widget.setStyleSheet(f"background-color: {self.theme_settings.get('darker_bg', '#303030')};")
        column_layout = QVBoxLayout(column_widget)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        darker_bg = self.theme_settings.get('darker_bg', '#303030')
        scroll.setStyleSheet(f"background-color: {darker_bg}; border: none;")
        scroll.viewport().setStyleSheet(f"background-color: {darker_bg};")
        scroll.setWidget(column_widget)
        self.hierarchy_splitter.addWidget(scroll)
        title_layout = QHBoxLayout()
        title_editor = QLineEdit()
        title_editor.setObjectName(f"TableTitleEditor_{col_idx}")
        title_editor.setFont(QFont('Consolas', 10))
        title_editor.setPlaceholderText(f"Title for Table {col_idx + 1}")
        title_editor.setStyleSheet(f"""
            QLineEdit {{
                background-color: {darker_bg};
                color: {self.base_color};
                border: 1px solid {self.base_color};
                border-radius: 3px;
                padding: 3px 6px; /* Increased padding slightly */
                selection-background-color: {self.base_color};
                selection-color: #000000;
                text-align: center;
                margin-bottom: 5px; /* Add some margin below title */
            }}
        """)
        title_editor.editingFinished.connect(self._save_current_generator)
        title_layout.addWidget(title_editor)
        column_layout.addLayout(title_layout)
        table_widget = QTableWidget(0, 3)
        table_widget.setObjectName(f"IndependentTable_{col_idx}")
        table_widget.setFont(QFont('Consolas', 10))
        table_widget.setAlternatingRowColors(True)
        table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        table_widget.customContextMenuRequested.connect(
            lambda pos, tw=table_widget, t_idx=col_idx: self._show_context_menu(tw, pos, t_idx)
        )
        table_widget.setHorizontalHeaderLabels(["Entry", "Weight", "Generate"])
        table_widget.horizontalHeader().setFont(QFont('Consolas', 10, QFont.Bold))
        header = table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        table_widget.setColumnWidth(1, 70)
        table_widget.setColumnWidth(2, 70)
        table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        table_widget.setSelectionMode(QTableWidget.SingleSelection)
        table_widget.verticalHeader().setVisible(False)
        bg_color = self.theme_settings.get('bg_color', '#404040')
        table_widget.setStyleSheet(f"""
            QTableWidget, QTableView {{
                background-color: {darker_bg};
                color: {self.base_color};
                alternate-background-color: {bg_color};
                border: 1px solid {self.base_color};
                border-radius: 3px;
                padding: 3px;
                show-decoration-selected: 1;
                selection-background-color: {self.base_color};
                selection-color: #000000;
                outline: 0px; /* Remove focus rectangle */
            }}
            QTableWidget::item:selected:active, QTableWidget::item:selected:!active,
            QTableView::item:selected:active, QTableView::item:selected:!active {{
                background-color: {self.base_color};
                color: #000000;
            }}
            /* Optional: Explicitly style focused items if outline:0px is not enough */
            /* QTableWidget::item:focus, QTableView::item:focus {{
                border: 1px solid {darker_bg}; 
            }} */
        """)
        header_style = f"""
            QHeaderView::section {{
                background-color: {darker_bg};
                color: {self.base_color};
                border: 1px solid {self.base_color};
                padding: 4px;
                font-weight: bold;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }}
        """
        table_widget.horizontalHeader().setStyleSheet(header_style)
        table_widget.verticalHeader().setStyleSheet(header_style)
        column_layout.addWidget(table_widget, 1)
        item_btn_bar = QWidget()
        item_btn_layout = QHBoxLayout(item_btn_bar)
        item_btn_layout.setContentsMargins(5, 5, 5, 5)
        item_btn_layout.setSpacing(10)
        delete_item_btn = QPushButton("Delete Item")
        delete_item_btn.setStyleSheet(f"background-color: {self.base_color}; color: #ffffff; padding: 8px 12px;")
        delete_item_btn.setFixedHeight(self.sample_btn.sizeHint().height())
        delete_item_btn.clicked.connect(lambda _, t_idx=col_idx: self._delete_hierarchy_item(t_idx))
        item_btn_layout.addWidget(delete_item_btn)
        add_item_btn = QPushButton("Add Item")
        add_item_btn.setStyleSheet(f"background-color: {self.base_color}; color: #ffffff; padding: 8px 12px;")
        add_item_btn.setFixedHeight(self.sample_btn.sizeHint().height())
        add_item_btn.clicked.connect(lambda _, t_idx=col_idx: self._add_hierarchy_item(t_idx))
        item_btn_layout.addWidget(add_item_btn)
        delete_item_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        add_item_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        column_layout.addWidget(item_btn_bar)
        table_display_elements = {
            'scroll_area': scroll,
            'column_widget': column_widget,
            'title_editor': title_editor,
            'table_widget': table_widget,
            'add_item_btn': add_item_btn,
            'delete_item_btn': delete_item_btn
        }
        self.table_displays.append(table_display_elements)
        table_widget.itemChanged.connect(
            lambda item, t_idx=col_idx: self._on_hierarchy_item_changed(item, t_idx)
        )
        table_widget.setMinimumHeight(250)
        if len(self.table_displays) > 1:
            spacer_frame = QFrame()
            spacer_frame.setFrameShape(QFrame.VLine)
            spacer_frame.setFrameShadow(QFrame.Sunken)
            spacer_frame.setFixedWidth(10)
            spacer_frame.setStyleSheet(f"background-color: {self.theme_settings.get('bg_color', '#404040')};")
            splitter_index = self.hierarchy_splitter.indexOf(scroll)
            if splitter_index > 0:
                 self.hierarchy_splitter.insertWidget(splitter_index -1, spacer_frame)
        self._save_current_generator()
        return col_idx

    def _remove_table_display_column(self):
        if len(self.table_displays) <= 1:
            QMessageBox.warning(self, "Cannot Remove", "At least one table is required.")
            return
        last_table_display = self.table_displays.pop()
        scroll_area = last_table_display['scroll_area']
        scroll_area_index = self.hierarchy_splitter.indexOf(scroll_area)
        if scroll_area_index > 0:
            widget_before = self.hierarchy_splitter.widget(scroll_area_index - 1)
            if isinstance(widget_before, QFrame):
                 widget_before.setParent(None)
                 widget_before.deleteLater()
        scroll_area.setParent(None) 
        scroll_area.deleteLater()
        self._save_current_generator()

    def generate_sample(self):
        self.generate_results.clear()
        num_results = self.count_spinner.value()
        
        if not hasattr(self, 'current_data') or not self.current_data:
            self.generate_results.setHtml(f"<span style='color: {self.base_color};'>No generator selected. Please select a generator first.</span>")
            return
            
        if not self.current_data.get('tables'):
            self.generate_results.setHtml(f"<span style='color: {self.base_color};'>No tables in this generator. Please add tables and items.</span>")
            return
        output_lines = []
        for _ in range(num_results):
            single_generated_string = self._generate_single_result()
            if single_generated_string:
                output_lines.append(single_generated_string)
        if output_lines:
            self.generate_results.setText("\n".join(output_lines))
        else:
            self.generate_results.setText("Could not generate any results. Ensure items are marked for generation within tables.")
            
    def _generate_single_result(self):
        picked_items_for_this_round = []
        if not hasattr(self, 'current_data') or 'tables' not in self.current_data:
            return ""
        for table_data in self.current_data.get('tables', []):
            generatable_items_in_table = []
            for item in table_data.get('items', []):
                if item.get('generate', False):
                    generatable_items_in_table.append((item.get('name', ''), item.get('weight', 1)))
            if generatable_items_in_table:
                names = [item[0] for item in generatable_items_in_table]
                weights = [item[1] for item in generatable_items_in_table]
                try:
                    if names:
                        selected_name_from_table = random.choices(names, weights=weights, k=1)[0]
                        picked_items_for_this_round.append(selected_name_from_table)
                except IndexError:
                    pass
        if picked_items_for_this_round:
            return ", ".join(picked_items_for_this_round)
        else:
            return ""

    def _show_context_menu(self, table_widget, pos, table_idx):
        item = table_widget.itemAt(pos)
        menu = QMenu(self)
        edit_action = QAction("Edit Properties", self)
        edit_action.triggered.connect(lambda: self._edit_hierarchy_item(table_idx, table_widget.currentRow()))
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_hierarchy_item(table_idx))
        move_up_action = QAction("Move Item Up", self)
        move_up_action.triggered.connect(lambda: self._move_hierarchy_item_up(table_idx, table_widget.currentRow()))
        move_down_action = QAction("Move Item Down", self)
        move_down_action.triggered.connect(lambda: self._move_hierarchy_item_down(table_idx, table_widget.currentRow()))
        if item:
            menu.addAction(edit_action)
            menu.addAction(delete_action)
            menu.addSeparator()
            menu.addAction(move_up_action)
            menu.addAction(move_down_action)
        else:
            pass
        menu.exec_(table_widget.mapToGlobal(pos))

    def _save_current_generator(self):
        if hasattr(self, 'is_loading') and self.is_loading:
            return
        row = self.generator_list.currentRow()
        if row < 0 or not hasattr(self, 'current_data'):
            return
        selected_generator_name = self.generator_list.item(row).text()
        fname = self.generator_files.get(selected_generator_name)
        if not fname:
            fname = f"{selected_generator_name.lower().replace(' ', '_')}.json"
            self.generator_files[selected_generator_name] = fname
        path = os.path.join(self.generator_dir, fname)
        self.current_data['name'] = selected_generator_name
        if 'tables' not in self.current_data:
             self.current_data['tables'] = []
        updated_tables_data = []
        for table_idx, display_elements in enumerate(self.table_displays):
            title = display_elements['title_editor'].text()
            table_widget = display_elements['table_widget']
            current_items = []
            for r_idx in range(table_widget.rowCount()):
                name_item = table_widget.item(r_idx, 0)
                weight_item = table_widget.item(r_idx, 1)
                name = name_item.text() if name_item else ""
                weight = 1
                if weight_item and weight_item.text().isdigit():
                    weight = int(weight_item.text())
                generate = False
                check_widget = table_widget.cellWidget(r_idx, 2)
                if check_widget:
                    checkbox = check_widget.findChild(QCheckBox)
                    if checkbox:
                        generate = checkbox.isChecked()
                current_items.append({'name': name, 'weight': weight, 'generate': generate})
            updated_tables_data.append({'title': title, 'items': current_items})
        self.current_data['tables'] = updated_tables_data
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving generator: {e}") 

    def _add_hierarchy_item(self, table_idx):
        if table_idx >= len(self.table_displays) or table_idx >= len(self.current_data['tables']):
            QMessageBox.warning(self, "Error", "Table index out of bounds.")
            return
        table_widget = self.table_displays[table_idx]['table_widget']
        table_data = self.current_data['tables'][table_idx]
        entry_count = len(table_data.get('items', [])) + 1
        name = f"New Entry {entry_count}"
        weight = 1
        generate = False
        new_item_data = {"name": name, "weight": weight, "generate": generate}
        table_data.setdefault('items', []).append(new_item_data)
        self._add_row_to_table(table_widget, name, weight, generate)
        table_widget.selectRow(table_widget.rowCount() - 1)
        self._save_current_generator()

    def _delete_hierarchy_item(self, table_idx):
        if table_idx >= len(self.table_displays) or table_idx >= len(self.current_data['tables']):
            QMessageBox.warning(self, "Error", "Table index out of bounds.")
            return
        table_widget = self.table_displays[table_idx]['table_widget']
        selected_rows = table_widget.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", f"Please select an item in '{self.current_data['tables'][table_idx]['title']}' to delete.")
            return
        row_to_delete = selected_rows[0].row()
        item_name = table_widget.item(row_to_delete, 0).text() if table_widget.item(row_to_delete, 0) else "this item"
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{item_name}' from table '{self.current_data['tables'][table_idx]['title']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        if row_to_delete < len(self.current_data['tables'][table_idx]['items']):
            self.current_data['tables'][table_idx]['items'].pop(row_to_delete)
        table_widget.removeRow(row_to_delete)
        self._save_current_generator()

    def _edit_hierarchy_item(self, table_idx, row):
        if table_idx >= len(self.table_displays) or table_idx >= len(self.current_data['tables']):
            QMessageBox.warning(self, "Error", "Table index out of bounds.")
            return
        table_widget = self.table_displays[table_idx]['table_widget']
        table_data = self.current_data['tables'][table_idx]
        if row < 0 or row >= len(table_data['items']):
            QMessageBox.warning(self, "No Selection", f"Please select a valid item in '{table_data['title']}' to edit.")
            return
        item_to_edit = table_data['items'][row]
        original_name = item_to_edit.get('name', '')
        original_weight = item_to_edit.get('weight', 1)
        new_name, ok_name = QInputDialog.getText(self, f"Edit Item in {table_data['title']}",
                                                 f"Enter new item name:", text=original_name)
        if not ok_name or not new_name.strip():
            new_name = original_name
        else:
            new_name = new_name.strip()
        new_weight_str, ok_weight = QInputDialog.getText(self, f"Edit Item Weight in {table_data['title']}",
                                                         f"Enter new weight for '{new_name}':",
                                                         text=str(original_weight))
        new_weight = original_weight
        if ok_weight and new_weight_str.strip().isdigit():
            new_weight = int(new_weight_str.strip())
        item_to_edit['name'] = new_name
        item_to_edit['weight'] = new_weight
        table_widget.item(row, 0).setText(new_name)
        table_widget.item(row, 1).setText(str(new_weight))
        self._save_current_generator()
        table_widget.selectRow(row)

    def _move_hierarchy_item_up(self, table_idx, row):
        if table_idx >= len(self.current_data['tables']) or row <= 0 or row >= len(self.current_data['tables'][table_idx]['items']):
            return
        items = self.current_data['tables'][table_idx]['items']
        items.insert(row - 1, items.pop(row))
        self._populate_single_table(self.table_displays[table_idx]['table_widget'], items)
        self.table_displays[table_idx]['table_widget'].selectRow(row - 1)
        self._save_current_generator()
        
    def _move_hierarchy_item_down(self, table_idx, row):
        if table_idx >= len(self.current_data['tables']) or row < 0 or row >= len(self.current_data['tables'][table_idx]['items']) - 1:
            return
        items = self.current_data['tables'][table_idx]['items']
        items.insert(row + 1, items.pop(row))
        self._populate_single_table(self.table_displays[table_idx]['table_widget'], items)
        self.table_displays[table_idx]['table_widget'].selectRow(row + 1)
        self._save_current_generator()

    def _on_hierarchy_item_changed(self, item, table_idx):
        if table_idx >= len(self.table_displays) or table_idx >= len(self.current_data['tables']):
            return
        table_widget = self.table_displays[table_idx]['table_widget']
        table_widget.blockSignals(True)
        row = item.row()
        col = item.column()
        new_value = item.text()
        items_list = self.current_data['tables'][table_idx].get('items', [])
        if row < len(items_list):
            item_data = items_list[row]
            changed = False
            if col == 0:
                if item_data.get('name') != new_value:
                    item_data['name'] = new_value
                    changed = True
            elif col == 1:
                try:
                    new_weight_val = int(new_value)
                    if item_data.get('weight') != new_weight_val:
                        item_data['weight'] = new_weight_val
                        changed = True
                except (ValueError, TypeError):
                    original_weight = str(item_data.get('weight', 1))
                    if item.text() != original_weight:
                        item.setText(original_weight)
            if changed:
                self._save_current_generator()
        table_widget.blockSignals(False)

    def update_theme(self, theme_settings):
        self.theme_settings = theme_settings
        self.base_color = theme_settings.get('base_color', '#00ff66')
        self.text_color = theme_settings.get('text_color', '#ffffff')
        bg_color = theme_settings.get('bg_color', '#2B2B2B')
        
        # Theme the scroll area and main widget
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
                    background: {self.base_color};
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
                    background: {self.base_color};
                    min-width: 20px;
                    border-radius: 6px;
                }}
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                    background: none;
                    width: 0px;
                }}
            """)
        
        # Theme the main widget background
        self.setStyleSheet(f"background-color: {bg_color};")
        
        # Update scroll content background
        if hasattr(self, 'scroll_content'):
            self.scroll_content.setStyleSheet(f"background-color: {bg_color};")
        
        # Fix button text colors to be white instead of black
        for child in self.findChildren((QPushButton, QLabel)):
            if isinstance(child, QPushButton) and not child.objectName().startswith("TabButton"):
                child.setStyleSheet(f"background-color: {self.base_color}; color: {self.text_color}; padding: 8px 12px;")
            elif isinstance(child, QLabel) and child.text() == "Random Generators":
                child.setStyleSheet(f"color: {self.base_color};")
            elif isinstance(child, QLabel):
                child.setStyleSheet(f"color: {self.text_color};") 
        
        if hasattr(self, 'mode_tabs'):
            tab_style = f"""
                QTabWidget::pane {{
                    border: none;
                    background: transparent;
                }}
                QTabBar {{
                    alignment: center;
                }}
                QTabWidget {{
                    alignment: center;
                }}
                QTabBar::tab {{
                    background-color: transparent;
                    color: {self.base_color};
                    padding: 8px 16px;
                    min-width: 140px; /* Make tabs wider */
                    border: 1px solid {self.base_color};
                    border-radius: 4px;
                    margin-right: 4px;
                    text-align: center; /* Center text */
                }}
                QTabBar::tab:selected {{
                    background-color: {self.base_color};
                    color: {bg_color}; /* Dark background for contrast on selected tab */
                }}
                QTabBar::tab:!selected {{
                    background-color: transparent;
                    color: {self.base_color};
                }}
                QTabWidget::tab-bar {{
                    alignment: center; /* Center the tab bar */
                    border-bottom: 2px solid {self.base_color}; /* Add line under tabs */
                }}
            """
            self.mode_tabs.setStyleSheet(tab_style)

    def _handle_tab_change(self, index):
        mode = 'resource' if index == 0 else 'session'
        self._switch_generator_mode(mode)

    def _switch_generator_mode(self, mode):
        self.mode_tabs.blockSignals(True)
        if self.generator_mode == mode:
            self.mode_tabs.setCurrentIndex(0 if mode == 'resource' else 1)
            self.mode_tabs.blockSignals(False)
            return
        self.generator_mode = mode
        self.generator_dir = self.resource_generator_dir if mode == 'resource' else self.session_generator_dir
        self.mode_tabs.setCurrentIndex(0 if mode == 'resource' else 1)
        self.generator_list.setCurrentRow(-1)
        self.load_generators()
        self.on_generator_selected()
        self.mode_tabs.blockSignals(False)
        
    def _handle_generate_button(self):
        is_permutate = self.permutate_radio.isChecked()
        use_resource = self.resource_file_radio.isChecked()
        generator_path = None
        selected_generator_name = None
        if is_permutate:
            row = self.generator_list.currentRow()
            if row < 0:
                QMessageBox.warning(self, "No Generator Selected", "Please select a generator to permutate.")
                return
            selected_generator_name = self.generator_list.item(row).text()
            fname = self.generator_files.get(selected_generator_name)
            if not fname:
                QMessageBox.warning(self, "Error", f"Could not find file for generator '{selected_generator_name}'.")
                return
            generator_path = os.path.join(self.generator_dir, fname)
        else:
            pass
        permutate_objects = self.objects_checkbox.isChecked()
        permutate_weights = self.weights_checkbox.isChecked()
        instructions = self.new_generate_input.toPlainText().strip()
        if not instructions:
            QMessageBox.warning(self, "Missing Instructions", 
                               "Please enter instructions for generation or permutation.")
            return
        model_override = None
        new_generator_name = None
        if not is_permutate:
            new_generator_name = self.new_generator_name_input.text().strip() or None
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            result = generate_random_list(
                instructions=instructions,
                is_permutate=is_permutate,
                use_resource=use_resource,
                permutate_objects=permutate_objects,
                permutate_weights=permutate_weights,
                generator_json_path=generator_path,
                resource_folder=self.resource_generator_dir,
                game_folder=self.session_generator_dir,
                model_override=model_override,
                generator_name=new_generator_name
            )
            QApplication.restoreOverrideCursor()
            if result.startswith("Error:"):
                QMessageBox.warning(self, "Generation Error", result)
                return
            self.generate_results.setText(result)
            if is_permutate and selected_generator_name:
                print(f"Generator function called with:\n  Instructions: {instructions}\n  Generator: {selected_generator_name}")
            else:
                print(f"Generator function called with:\n  Instructions: {instructions}\n  Mode: New Random List")
            if new_generator_name:
                print(f"  User-provided name: {new_generator_name}")
            print(f"Result: {result}")
            prev_selected = None
            if self.generator_list.currentItem():
                prev_selected = self.generator_list.currentItem().text()
            self.load_generators()
            if prev_selected:
                for i in range(self.generator_list.count()):
                    item = self.generator_list.item(i)
                    if item.text() == prev_selected:
                        self.generator_list.setCurrentItem(item)
                        break
            if self.generator_list.currentRow() < 0 and prev_selected:
                base_name = prev_selected.split(" ")[0]
                for i in range(self.generator_list.count()):
                    item = self.generator_list.item(i)
                    if base_name in item.text():
                        self.generator_list.setCurrentItem(item)
                        break
        except Exception as e:
            QApplication.restoreOverrideCursor()
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            self.generate_results.setText(f"Error: {str(e)}")
        