from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, 
                             QLineEdit, QPushButton, QAbstractItemView, QListWidgetItem,
                             QInputDialog, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QRadioButton, QButtonGroup)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import os
import json

class KeywordManagerWidget(QWidget):
    def __init__(self, theme_colors=None, workflow_data_dir=None, parent=None):
        super().__init__(parent)
        self.theme_colors = theme_colors if theme_colors else {}
        self.workflow_data_dir = workflow_data_dir or "data"
        self.setObjectName("KeywordManagerContainer")
        self.keywords_dir = os.path.join(self.workflow_data_dir, "resources", "data files", "keywords")
        self._ensure_keywords_directory()
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        lists_layout = QHBoxLayout()
        keyword_section_layout = QVBoxLayout()
        category_filter_button_layout = QHBoxLayout()
        self.filter_category_input = QLineEdit()
        self.filter_category_input.setObjectName("FilterInput")
        self.filter_category_input.setPlaceholderText("Filter categories...")
        self.filter_category_input.textChanged.connect(self._filter_category_list)
        self.add_category_button = QPushButton("+")
        self.add_category_button.setObjectName("AddButton")
        self.add_category_button.setToolTip("Add New Category")
        self.add_category_button.clicked.connect(self._add_category)
        self.remove_category_button = QPushButton("-")
        self.remove_category_button.setObjectName("RemoveButton")
        self.remove_category_button.setToolTip("Remove Selected Category")
        self.remove_category_button.clicked.connect(self._remove_category)
        category_filter_button_layout.addWidget(self.filter_category_input, 1)
        category_filter_button_layout.addWidget(self.add_category_button)
        category_filter_button_layout.addWidget(self.remove_category_button)
        category_label = QLabel("Category:")
        category_label.setObjectName("KeywordManagerLabel")
        category_label.setFont(QFont('Consolas', 10, QFont.Bold))
        self.category_list = QListWidget()
        self.category_list.setObjectName("KeywordManagerList")
        self.category_list.setMinimumWidth(200)
        self.category_list.setAlternatingRowColors(True)
        self.category_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.category_list.setFocusPolicy(Qt.NoFocus)
        self.category_list.currentItemChanged.connect(self._on_category_selected)
        self.category_list.itemDoubleClicked.connect(self._rename_category)
        keyword_section_layout.addWidget(category_label)
        keyword_section_layout.addLayout(category_filter_button_layout)
        keyword_section_layout.addWidget(self.category_list)
        keyword_section_layout_right = QVBoxLayout()
        keyword_filter_button_layout = QHBoxLayout()
        self.filter_keyword_input = QLineEdit()
        self.filter_keyword_input.setObjectName("FilterInput")
        self.filter_keyword_input.setPlaceholderText("Filter keywords...")
        self.filter_keyword_input.textChanged.connect(self._filter_keyword_list)
        self.add_keyword_button = QPushButton("+")
        self.add_keyword_button.setObjectName("AddButton")
        self.add_keyword_button.setToolTip("Add New Keyword")
        self.add_keyword_button.clicked.connect(self._add_keyword)
        self.remove_keyword_button = QPushButton("-")
        self.remove_keyword_button.setObjectName("RemoveButton")
        self.remove_keyword_button.setToolTip("Remove Selected Keyword")
        self.remove_keyword_button.clicked.connect(self._remove_keyword)
        self.move_keyword_button = QPushButton("→")
        self.move_keyword_button.setObjectName("MoveButton")
        self.move_keyword_button.setToolTip("Move Keyword to Another Category")
        self.move_keyword_button.clicked.connect(self._move_keyword_to_category)
        keyword_filter_button_layout.addWidget(self.filter_keyword_input, 1)
        keyword_filter_button_layout.addWidget(self.add_keyword_button)
        keyword_filter_button_layout.addWidget(self.remove_keyword_button)
        keyword_filter_button_layout.addWidget(self.move_keyword_button)
        keyword_label = QLabel("Keyword:")
        keyword_label.setObjectName("KeywordManagerLabel")
        keyword_label.setFont(QFont('Consolas', 10, QFont.Bold))
        self.keyword_list = QListWidget()
        self.keyword_list.setObjectName("KeywordManagerList")
        self.keyword_list.setMinimumWidth(200)
        self.keyword_list.setAlternatingRowColors(True)
        self.keyword_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.keyword_list.setFocusPolicy(Qt.NoFocus)
        self.keyword_list.currentItemChanged.connect(self._on_keyword_selected)
        self.keyword_list.itemDoubleClicked.connect(self._rename_keyword)
        keyword_section_layout_right.addWidget(keyword_label)
        keyword_section_layout_right.addLayout(keyword_filter_button_layout)
        keyword_section_layout_right.addWidget(self.keyword_list)
        lists_layout.addLayout(keyword_section_layout, 1)
        lists_layout.addLayout(keyword_section_layout_right, 1)
        main_layout.addLayout(lists_layout, 1)
        entries_section_layout = QVBoxLayout()
        entries_management_layout = QHBoxLayout()
        entries_label = QLabel("Entries:")
        entries_label.setObjectName("KeywordManagerLabel")
        entries_label.setFont(QFont('Consolas', 11, QFont.Bold))
        self.add_entry_button = QPushButton("+")
        self.add_entry_button.setObjectName("AddButton")
        self.add_entry_button.setToolTip("Add New Entry")
        self.add_entry_button.clicked.connect(self._add_entry)
        self.remove_entry_button = QPushButton("-")
        self.remove_entry_button.setObjectName("RemoveButton")
        self.remove_entry_button.setToolTip("Remove Selected Entry")
        self.remove_entry_button.clicked.connect(self._remove_entry)
        self.move_entry_up_button = QPushButton("↑")
        self.move_entry_up_button.setObjectName("MoveButton")
        self.move_entry_up_button.setToolTip("Move Selected Entry Up")
        self.move_entry_up_button.clicked.connect(self._move_entry_up)
        self.move_entry_down_button = QPushButton("↓")
        self.move_entry_down_button.setObjectName("MoveButton")
        self.move_entry_down_button.setToolTip("Move Selected Entry Down")
        self.move_entry_down_button.clicked.connect(self._move_entry_down)
        entries_management_layout.addWidget(entries_label)
        entries_management_layout.addStretch()
        entries_management_layout.addWidget(self.add_entry_button)
        entries_management_layout.addWidget(self.remove_entry_button)
        entries_management_layout.addWidget(self.move_entry_up_button)
        entries_management_layout.addWidget(self.move_entry_down_button)
        self.entries_table = QTableWidget()
        self.entries_table.setObjectName("KeywordManagerTable")
        self.entries_table.setColumnCount(9)
        self.entries_table.setHorizontalHeaderLabels(["Order", "Scope", "Character", "Setting", "World", "Region", "Location", "Variables", "Context Output"])
        header = self.entries_table.horizontalHeader()
        header.setObjectName("KeywordManagerTableHeader")
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setSectionResizeMode(5, QHeaderView.Interactive)
        header.setSectionResizeMode(6, QHeaderView.Interactive)
        header.setSectionResizeMode(7, QHeaderView.Interactive)
        header.setSectionResizeMode(8, QHeaderView.Stretch)
        self.entries_table.setColumnWidth(0, 60)
        self.entries_table.setColumnWidth(1, 120)
        self.entries_table.setColumnWidth(2, 120)
        self.entries_table.setColumnWidth(3, 120)
        self.entries_table.setColumnWidth(4, 100)
        self.entries_table.setColumnWidth(5, 100)
        self.entries_table.setColumnWidth(6, 100)
        self.entries_table.setColumnWidth(7, 100)
        self.entries_table.verticalHeader().setVisible(False)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.entries_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setFocusPolicy(Qt.NoFocus)
        self.entries_table.itemChanged.connect(self._on_entry_item_changed)
        entries_section_layout.addLayout(entries_management_layout)
        entries_section_layout.addWidget(self.entries_table)
        main_layout.addLayout(entries_section_layout, 2)
        self.setLayout(main_layout)
        self._populate_categories()
        self.update_styles()

    def _create_scope_widget(self, scope="mention"):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        conversation_radio = QRadioButton("Conversation")
        mention_radio = QRadioButton("Mention")
        if scope.lower() == "conversation":
            conversation_radio.setChecked(True)
        else:
            mention_radio.setChecked(True)
        button_group = QButtonGroup(widget)
        button_group.addButton(conversation_radio, 0)
        button_group.addButton(mention_radio, 1)
        widget.conversation_radio = conversation_radio
        widget.mention_radio = mention_radio
        button_group.buttonClicked.connect(lambda: self._on_scope_changed())
        layout.addWidget(conversation_radio)
        layout.addWidget(mention_radio)
        layout.addStretch()
        return widget

    def _on_scope_changed(self):
        current_keyword_item = self.keyword_list.currentItem()
        current_category_item = self.category_list.currentItem()
        if current_keyword_item and current_category_item:
            category = current_category_item.data(Qt.UserRole)
            keyword_file = current_keyword_item.data(Qt.UserRole)
            self._save_entries(category, keyword_file)

    def _ensure_keywords_directory(self):
        try:
            os.makedirs(self.keywords_dir, exist_ok=True)
            if not os.listdir(self.keywords_dir):
                default_categories = ["Character Names", "Locations", "Items", "Spells", "Creatures"]
                for category in default_categories:
                    category_dir = os.path.join(self.keywords_dir, category)
                    os.makedirs(category_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating keywords directory: {e}")

    def _populate_categories(self):
        self.category_list.clear()
        if not os.path.exists(self.keywords_dir):
            return
        try:
            categories = [d for d in os.listdir(self.keywords_dir) 
                         if os.path.isdir(os.path.join(self.keywords_dir, d))]
            categories.sort()
            for category in categories:
                item = QListWidgetItem(category)
                item.setData(Qt.UserRole, category)
                self.category_list.addItem(item)
        except OSError as e:
            print(f"Error reading categories: {e}")

    def _populate_keywords(self, category):
        self.keyword_list.clear()
        if not category:
            return
        category_dir = os.path.join(self.keywords_dir, category)
        if not os.path.exists(category_dir):
            return
        try:
            json_files = [f for f in os.listdir(category_dir) if f.endswith('.json')]
            order_file = os.path.join(category_dir, '_order.json')
            if os.path.exists(order_file):
                try:
                    with open(order_file, 'r', encoding='utf-8') as f:
                        order_data = json.load(f)
                        ordered_files = order_data.get('order', [])
                        for f in json_files:
                            if f not in ordered_files and f != '_order.json':
                                ordered_files.append(f)
                        json_files = ordered_files
                except (json.JSONDecodeError, IOError):
                    pass
            for json_file in json_files:
                if json_file == '_order.json':
                    continue
                file_path = os.path.join(category_dir, json_file)
                if os.path.exists(file_path):
                    display_name = json_file[:-5] if json_file.endswith('.json') else json_file
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.UserRole, json_file)
                    self.keyword_list.addItem(item)
        except OSError as e:
            print(f"Error reading keywords from category {category}: {e}")

    def _on_category_selected(self, current_item, previous_item):
        if current_item:
            category = current_item.data(Qt.UserRole)
            self._populate_keywords(category)
        else:
            self.keyword_list.clear()
            self.entries_table.setRowCount(0)

    def _on_keyword_selected(self, current_item, previous_item):
        if current_item:
            category_item = self.category_list.currentItem()
            if category_item:
                category = category_item.data(Qt.UserRole)
                keyword_file = current_item.data(Qt.UserRole)
                self._populate_entries(category, keyword_file)
        else:
            self.entries_table.setRowCount(0)

    def _filter_category_list(self, text):
        text = text.lower()
        for i in range(self.category_list.count()):
            item = self.category_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _filter_keyword_list(self, text):
        text = text.lower()
        for i in range(self.keyword_list.count()):
            item = self.keyword_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _populate_entries(self, category, keyword_file):
        self.entries_table.setRowCount(0)
        if not category or not keyword_file:
            return
        keyword_path = os.path.join(self.keywords_dir, category, keyword_file)
        if not os.path.exists(keyword_path):
            return
        try:
            keyword_data = {}
            with open(keyword_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    keyword_data = json.loads(content)
                else:
                    print(f"Empty file detected: {keyword_path}, will create default structure when saving")
                    return
            entries = keyword_data.get('entries', [])
            for i, entry in enumerate(entries):
                row_position = self.entries_table.rowCount()
                self.entries_table.insertRow(row_position)
                order_item = QTableWidgetItem(str(i + 1))
                order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
                self.entries_table.setItem(row_position, 0, order_item)
                scope_value = entry.get("scope", "mention")
                scope_widget = self._create_scope_widget(scope_value)
                self.entries_table.setCellWidget(row_position, 1, scope_widget)
                self.entries_table.setItem(row_position, 2, QTableWidgetItem(entry.get("character", "")))
                self.entries_table.setItem(row_position, 3, QTableWidgetItem(entry.get("setting", "")))
                self.entries_table.setItem(row_position, 4, QTableWidgetItem(entry.get("world", "")))
                self.entries_table.setItem(row_position, 5, QTableWidgetItem(entry.get("region", "")))
                self.entries_table.setItem(row_position, 6, QTableWidgetItem(entry.get("location", "")))
                self.entries_table.setItem(row_position, 7, QTableWidgetItem(entry.get("variables", "")))
                self.entries_table.setItem(row_position, 8, QTableWidgetItem(entry.get("context_output", "")))
        except json.JSONDecodeError as e:
            print(f"Corrupted JSON in {keyword_path}: {e}, will recreate when saving")
        except (IOError, OSError) as e:
            print(f"Error reading file {keyword_path}: {e}")

    def _save_entries(self, category, keyword_file):
        if not category or not keyword_file:
            return
        keyword_path = os.path.join(self.keywords_dir, category, keyword_file)
        try:
            keyword_data = {}
            if os.path.exists(keyword_path):
                try:
                    with open(keyword_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            keyword_data = json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"Corrupted JSON detected in {keyword_path}, creating default structure: {e}")
            if not isinstance(keyword_data, dict):
                keyword_data = {}
            if 'name' not in keyword_data:
                base_name = os.path.splitext(keyword_file)[0]
                keyword_data['name'] = base_name
            if 'description' not in keyword_data:
                keyword_data['description'] = ""
            if 'tags' not in keyword_data:
                keyword_data['tags'] = []
            if 'created' not in keyword_data:
                keyword_data['created'] = ""
            if 'modified' not in keyword_data:
                keyword_data['modified'] = ""
            entries = []
            for row in range(self.entries_table.rowCount()):
                scope_widget = self.entries_table.cellWidget(row, 1)
                scope = "mention"
                if scope_widget and hasattr(scope_widget, 'conversation_radio'):
                    if scope_widget.conversation_radio.isChecked():
                        scope = "conversation"
                    else:
                        scope = "mention"
                entry = {
                    "scope": scope,
                    "character": self.entries_table.item(row, 2).text() if self.entries_table.item(row, 2) else "",
                    "setting": self.entries_table.item(row, 3).text() if self.entries_table.item(row, 3) else "",
                    "world": self.entries_table.item(row, 4).text() if self.entries_table.item(row, 4) else "",
                    "region": self.entries_table.item(row, 5).text() if self.entries_table.item(row, 5) else "",
                    "location": self.entries_table.item(row, 6).text() if self.entries_table.item(row, 6) else "",
                    "variables": self.entries_table.item(row, 7).text() if self.entries_table.item(row, 7) else "",
                    "context_output": self.entries_table.item(row, 8).text() if self.entries_table.item(row, 8) else ""
                }
                entries.append(entry)
            keyword_data['entries'] = entries
            with open(keyword_path, 'w', encoding='utf-8') as f:
                json.dump(keyword_data, f, indent=2, ensure_ascii=False)
                
        except (IOError, OSError) as e:
            print(f"Error saving entries to {keyword_path}: {e}")
            QMessageBox.critical(self, "Save Error", f"Could not save entries to {keyword_file}: {e}")

    def _add_category(self):
        category_name, ok = QInputDialog.getText(self, "Add Category", "Enter category name:")
        if ok and category_name.strip():
            category_name = category_name.strip()
            category_dir = os.path.join(self.keywords_dir, category_name)
            try:
                os.makedirs(category_dir, exist_ok=True)
                self._populate_categories()
                main_ui = self._get_main_ui()
                if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
                    try:
                        main_ui.add_rule_sound.play()
                    except Exception:
                        main_ui.add_rule_sound = None
                for i in range(self.category_list.count()):
                    item = self.category_list.item(i)
                    if item.data(Qt.UserRole) == category_name:
                        self.category_list.setCurrentItem(item)
                        break
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not create category: {e}")

    def _remove_category(self):
        current_item = self.category_list.currentItem()
        if not current_item:
            return
        category = current_item.data(Qt.UserRole)
        category_dir = os.path.join(self.keywords_dir, category)
        try:
            import shutil
            shutil.rmtree(category_dir)
            self._populate_categories()
            self.keyword_list.clear()
            main_ui = self._get_main_ui()
            if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                try:
                    main_ui.delete_rule_sound.play()
                except Exception:
                    main_ui.delete_rule_sound = None
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not remove category: {e}")

    def _add_keyword(self):
        current_category_item = self.category_list.currentItem()
        if not current_category_item:
            QMessageBox.warning(self, "No Category", "Please select a category first.")
            return
        category = current_category_item.data(Qt.UserRole)
        keyword_name, ok = QInputDialog.getText(self, "Add Keyword", "Enter keyword name:")
        if ok and keyword_name.strip():
            keyword_name = keyword_name.strip()
            category_dir = os.path.join(self.keywords_dir, category)
            keyword_file = os.path.join(category_dir, f"{keyword_name}.json")
            if os.path.exists(keyword_file):
                QMessageBox.warning(self, "Keyword Exists", f"Keyword '{keyword_name}' already exists in this category.")
                return
            try:
                keyword_data = {
                    "name": keyword_name,
                    "description": "",
                    "tags": [],
                    "created": "",
                    "modified": "",
                    "entries": []
                }
                with open(keyword_file, 'w', encoding='utf-8') as f:
                    json.dump(keyword_data, f, indent=2, ensure_ascii=False)
                self._populate_keywords(category)
                self._save_keyword_order(category)
                main_ui = self._get_main_ui()
                if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
                    try:
                        main_ui.add_rule_sound.play()
                    except Exception:
                        main_ui.add_rule_sound = None
                for i in range(self.keyword_list.count()):
                    item = self.keyword_list.item(i)
                    if item.text() == keyword_name:
                        self.keyword_list.setCurrentItem(item)
                        break
            except (OSError, json.JSONEncodeError) as e:
                QMessageBox.critical(self, "Error", f"Could not create keyword: {e}")

    def _remove_keyword(self):
        current_keyword_item = self.keyword_list.currentItem()
        current_category_item = self.category_list.currentItem()
        if not current_keyword_item or not current_category_item:
            return
        keyword_file = current_keyword_item.data(Qt.UserRole)
        category = current_category_item.data(Qt.UserRole)
        keyword_path = os.path.join(self.keywords_dir, category, keyword_file)
        try:
            os.remove(keyword_path)
            self._populate_keywords(category)
            self._save_keyword_order(category)
            main_ui = self._get_main_ui()
            if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                try:
                    main_ui.delete_rule_sound.play()
                except Exception:
                    main_ui.delete_rule_sound = None
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not remove keyword: {e}")

    def _add_entry(self):
        current_keyword_item = self.keyword_list.currentItem()
        current_category_item = self.category_list.currentItem()
        if not current_keyword_item or not current_category_item:
            QMessageBox.warning(self, "No Keyword", "Please select a keyword first.")
            return
        row_position = self.entries_table.rowCount()
        self.entries_table.insertRow(row_position)
        order_item = QTableWidgetItem(str(row_position + 1))
        order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
        self.entries_table.setItem(row_position, 0, order_item)
        scope_widget = self._create_scope_widget("mention")
        self.entries_table.setCellWidget(row_position, 1, scope_widget)
        self.entries_table.setItem(row_position, 2, QTableWidgetItem(""))
        self.entries_table.setItem(row_position, 3, QTableWidgetItem(""))
        self.entries_table.setItem(row_position, 4, QTableWidgetItem(""))
        self.entries_table.setItem(row_position, 5, QTableWidgetItem(""))
        self.entries_table.setItem(row_position, 6, QTableWidgetItem(""))
        self.entries_table.setItem(row_position, 7, QTableWidgetItem(""))
        self.entries_table.setItem(row_position, 8, QTableWidgetItem(""))
        self.entries_table.selectRow(row_position)
        category = current_category_item.data(Qt.UserRole)
        keyword_file = current_keyword_item.data(Qt.UserRole)
        self._save_entries(category, keyword_file)
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None

    def _remove_entry(self):
        current_row = self.entries_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an entry to remove.")
            return
        self.entries_table.removeRow(current_row)
        self._update_order_numbers()
        current_keyword_item = self.keyword_list.currentItem()
        current_category_item = self.category_list.currentItem()
        if current_keyword_item and current_category_item:
            category = current_category_item.data(Qt.UserRole)
            keyword_file = current_keyword_item.data(Qt.UserRole)
            self._save_entries(category, keyword_file)
            main_ui = self._get_main_ui()
            if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                try:
                    main_ui.delete_rule_sound.play()
                except Exception:
                    main_ui.delete_rule_sound = None

    def _move_entry_up(self):
        current_row = self.entries_table.currentRow()
        if current_row <= 0:
            return
        items = []
        for col in range(self.entries_table.columnCount()):
            item = self.entries_table.takeItem(current_row, col)
            items.append(item)
        items_above = []
        for col in range(self.entries_table.columnCount()):
            item = self.entries_table.takeItem(current_row - 1, col)
            items_above.append(item)
        for col, item in enumerate(items):
            self.entries_table.setItem(current_row - 1, col, item)
        for col, item in enumerate(items_above):
            self.entries_table.setItem(current_row, col, item)
        self.entries_table.selectRow(current_row - 1)
        self._update_order_numbers()
        self._save_current_entries()

    def _move_entry_down(self):
        current_row = self.entries_table.currentRow()
        if current_row < 0 or current_row >= self.entries_table.rowCount() - 1:
            return
        items = []
        for col in range(self.entries_table.columnCount()):
            item = self.entries_table.takeItem(current_row, col)
            items.append(item)
        items_below = []
        for col in range(self.entries_table.columnCount()):
            item = self.entries_table.takeItem(current_row + 1, col)
            items_below.append(item)
        for col, item in enumerate(items):
            self.entries_table.setItem(current_row + 1, col, item)
        for col, item in enumerate(items_below):
            self.entries_table.setItem(current_row, col, item)
        self.entries_table.selectRow(current_row + 1)
        self._update_order_numbers()
        self._save_current_entries()

    def _update_order_numbers(self):
        for row in range(self.entries_table.rowCount()):
            order_item = QTableWidgetItem(str(row + 1))
            order_item.setFlags(order_item.flags() & ~Qt.ItemIsEditable)
            self.entries_table.setItem(row, 0, order_item)

    def _save_current_entries(self):
        current_keyword_item = self.keyword_list.currentItem()
        current_category_item = self.category_list.currentItem()
        if current_keyword_item and current_category_item:
            category = current_category_item.data(Qt.UserRole)
            keyword_file = current_keyword_item.data(Qt.UserRole)
            self._save_entries(category, keyword_file)

    def _on_entry_item_changed(self, item):
        if item.column() == 0:
            return
        self._save_current_entries()

    def _move_keyword_to_category(self):
        current_keyword_item = self.keyword_list.currentItem()
        current_category_item = self.category_list.currentItem()
        if not current_keyword_item or not current_category_item:
            return
        categories = []
        for i in range(self.category_list.count()):
            cat_item = self.category_list.item(i)
            if cat_item != current_category_item:
                categories.append(cat_item.data(Qt.UserRole))
        if not categories:
            QMessageBox.information(self, "No Categories", "No other categories available.")
            return
        target_category, ok = QInputDialog.getItem(self, "Move Keyword", 
                                                  "Select target category:", 
                                                  categories, 0, False)
        if ok and target_category:
            try:
                current_category = current_category_item.data(Qt.UserRole)
                keyword_file = current_keyword_item.data(Qt.UserRole)
                source_path = os.path.join(self.keywords_dir, current_category, keyword_file)
                target_path = os.path.join(self.keywords_dir, target_category, keyword_file)
                if os.path.exists(target_path):
                    QMessageBox.warning(self, "Keyword Exists", 
                                      f"A keyword with this name already exists in '{target_category}'.")
                    return
                import shutil
                shutil.move(source_path, target_path)
                self._populate_keywords(current_category)
                self._save_keyword_order(current_category)
                self._save_keyword_order(target_category)
            except (OSError, shutil.Error) as e:
                QMessageBox.critical(self, "Error", f"Could not move keyword: {e}")

    def _save_keyword_order(self, category):
        try:
            category_dir = os.path.join(self.keywords_dir, category)
            order_file = os.path.join(category_dir, '_order.json')
            order = []
            for i in range(self.keyword_list.count()):
                item = self.keyword_list.item(i)
                order.append(item.data(Qt.UserRole))
            order_data = {"order": order}
            with open(order_file, 'w', encoding='utf-8') as f:
                json.dump(order_data, f, indent=2, ensure_ascii=False)
        except (OSError, json.JSONEncodeError) as e:
            print(f"Error saving keyword order: {e}")

    def _rename_category(self, item):
        if not item:
            return
        old_category = item.data(Qt.UserRole)
        new_category, ok = QInputDialog.getText(self, "Rename Category", 
                                               "Enter new category name:", 
                                               text=old_category)
        if ok and new_category.strip() and new_category.strip() != old_category:
            new_category = new_category.strip()
            old_category_dir = os.path.join(self.keywords_dir, old_category)
            new_category_dir = os.path.join(self.keywords_dir, new_category)
            if os.path.exists(new_category_dir):
                QMessageBox.warning(self, "Category Exists", 
                                  f"A category named '{new_category}' already exists.")
                return
            try:
                os.rename(old_category_dir, new_category_dir)
                self._populate_categories()
                for i in range(self.category_list.count()):
                    list_item = self.category_list.item(i)
                    if list_item.data(Qt.UserRole) == new_category:
                        self.category_list.setCurrentItem(list_item)
                        break
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not rename category: {e}")

    def _rename_keyword(self, item):
        if not item:
            return
        current_category_item = self.category_list.currentItem()
        if not current_category_item:
            return
        category = current_category_item.data(Qt.UserRole)
        old_keyword_file = item.data(Qt.UserRole)
        old_keyword_name = item.text()
        new_keyword_name, ok = QInputDialog.getText(self, "Rename Keyword", 
                                                   "Enter new keyword name:", 
                                                   text=old_keyword_name)
        if ok and new_keyword_name.strip() and new_keyword_name.strip() != old_keyword_name:
            new_keyword_name = new_keyword_name.strip()
            new_keyword_file = f"{new_keyword_name}.json"
            old_keyword_path = os.path.join(self.keywords_dir, category, old_keyword_file)
            new_keyword_path = os.path.join(self.keywords_dir, category, new_keyword_file)
            if os.path.exists(new_keyword_path):
                QMessageBox.warning(self, "Keyword Exists", 
                                  f"A keyword named '{new_keyword_name}' already exists in this category.")
                return
            try:
                keyword_data = {}
                if os.path.exists(old_keyword_path):
                    with open(old_keyword_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            keyword_data = json.loads(content)
                keyword_data['name'] = new_keyword_name
                with open(new_keyword_path, 'w', encoding='utf-8') as f:
                    json.dump(keyword_data, f, indent=2, ensure_ascii=False)
                os.remove(old_keyword_path)
                self._populate_keywords(category)
                self._save_keyword_order(category)
                for i in range(self.keyword_list.count()):
                    list_item = self.keyword_list.item(i)
                    if list_item.text() == new_keyword_name:
                        self.keyword_list.setCurrentItem(list_item)
                        break
            except (OSError, json.JSONDecodeError) as e:
                QMessageBox.critical(self, "Error", f"Could not rename keyword: {e}")

    def _get_main_ui(self):
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'add_rule_sound'):
                return parent
            parent = parent.parentWidget()
        return None

    def update_styles(self):
        base_color = self.theme_colors.get('base_color', '#FFFFFF')
        bg_value = int(80 * self.theme_colors.get('contrast', 0.35))
        bg_color = f"#{bg_value:02x}{bg_value:02x}{bg_value:02x}"
        darker_bg = f"#{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}"
        try:
            from PyQt5.QtGui import QColor
            qcolor = QColor(base_color)
            if qcolor.isValid():
                r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
                highlight = f"rgba({r}, {g}, {b}, 0.6)"
            else:
                highlight = "rgba(204, 204, 204, 0.6)"
        except:
            highlight = "rgba(204, 204, 204, 0.6)"
        self.setStyleSheet(f"""
            QWidget#KeywordManagerContainer {{
                background-color: {bg_color};
            }}
            QLabel#KeywordManagerLabel {{
                color: {base_color};
                font: 11pt "Consolas";
                margin-right: 10px;
            }}
            QListWidget#KeywordManagerList {{
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                selection-background-color: {highlight};
                selection-color: white;
                alternate-background-color: {bg_color};
                border-radius: 3px;
                padding: 3px;
                font: 10pt "Consolas";
            }}
            QListWidget#KeywordManagerList::item:selected {{
                background-color: {highlight};
                color: white;
            }}
            QListWidget#KeywordManagerList::item:hover {{
                background-color: {highlight};
                color: white;
            }}
            QLineEdit#FilterInput {{
                color: {base_color};
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 2px;
                font: 9pt "Consolas";
            }}
            QPushButton#AddButton, QPushButton#RemoveButton, QPushButton#MoveButton {{
                color: {base_color};
                background-color: {bg_color};
                border: 2px solid {base_color};
                padding: 5px;
                font: 14pt "Consolas";
                border-radius: 5px;
                min-height: 28px;
            }}
            QPushButton#AddButton:hover, QPushButton#RemoveButton:hover, QPushButton#MoveButton:hover {{
                background-color: {highlight};
                color: white;
                border: 2px solid {base_color};
            }}
            QTableWidget#KeywordManagerTable {{
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                selection-background-color: {highlight};
                selection-color: white;
                alternate-background-color: {bg_color};
                border-radius: 3px;
                gridline-color: rgba({r}, {g}, {b}, 0.3);
                font: 10pt "Consolas";
                outline: none;
            }}
            QTableWidget#KeywordManagerTable::item {{
                padding: 4px;
                border: none;
                outline: none;
            }}
            QTableWidget#KeywordManagerTable::item:selected {{
                background-color: {highlight};
                color: white;
                outline: none;
            }}
            QTableWidget#KeywordManagerTable::item:focus {{
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {highlight};
                outline: none;
            }}
            QHeaderView#KeywordManagerTableHeader {{
                background-color: {bg_color};
                color: {base_color};
                border: 1px solid {base_color};
                font: 10pt "Consolas";
                font-weight: bold;
            }}
            QHeaderView#KeywordManagerTableHeader::section {{
                background-color: {bg_color};
                color: {base_color};
                border: 1px solid {base_color};
                padding: 4px;
                font-weight: bold;
            }}
            QHeaderView#KeywordManagerTableHeader::section:hover {{
                background-color: {highlight};
                color: white;
            }}
        """)
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    colors = {"base_color": "#00FF66", "bg_color": "#2C2C2C", "accent_color": "#00FF66"}
    widget = KeywordManagerWidget(theme_colors=colors)
    widget.show()
    sys.exit(app.exec_()) 