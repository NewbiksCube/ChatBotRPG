from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, 
                             QHBoxLayout, QInputDialog, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QLineEdit, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt
import os
import json
import re
import shutil

def sanitize_path_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', name).strip()
    sanitized = sanitized.replace(' ', '_').lower()
    return sanitized or 'untitled'

class InventoryCategoryPage(QWidget):
    def __init__(self, category_name, parent=None):
        super().__init__(parent)
        self.category_name = category_name
        self.parent_manager = parent
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        item_management_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setObjectName("FilterInput")
        self.filter_input.setPlaceholderText("Filter items...")
        self.filter_input.textChanged.connect(self._filter_items)
        self.add_item_button = QPushButton("+")
        self.add_item_button.setObjectName("AddInventoryItemButton_Tab")
        self.add_item_button.setToolTip("Add new item to this category")
        self.add_item_button.clicked.connect(self._add_item)
        self.remove_item_button = QPushButton("-")
        self.remove_item_button.setObjectName("RemoveInventoryItemButton_Tab")
        self.remove_item_button.setToolTip("Remove selected item")
        self.remove_item_button.clicked.connect(self._remove_item)
        item_management_layout.addWidget(QLabel("Items:"))
        item_management_layout.addWidget(self.filter_input, 1)
        item_management_layout.addWidget(self.add_item_button)
        item_management_layout.addWidget(self.remove_item_button)
        layout.addLayout(item_management_layout)
        self.item_table_widget = QTableWidget()
        self.item_table_widget.setObjectName("InventoryTableWidget_Tab")
        self.item_table_widget.setColumnCount(5)
        self.item_table_widget.setHorizontalHeaderLabels(["Name", "Properties", "Variables", "Base Value", "Description"])
        self.item_table_widget.horizontalHeader().setObjectName("InventoryTableWidget_Tab_HorizontalHeader")
        self.item_table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.item_table_widget.setColumnWidth(1, 250)
        self.item_table_widget.setColumnWidth(2, 500)
        self.item_table_widget.verticalHeader().setObjectName("InventoryTableWidget_Tab_VerticalHeader")
        self.item_table_widget.verticalHeader().setVisible(False)
        self.item_table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.item_table_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.item_table_widget.setFocusPolicy(Qt.NoFocus)
        self.item_table_widget.itemChanged.connect(self._on_item_data_changed)
        self.item_table_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.item_table_widget.verticalHeader().setDefaultSectionSize(60)
        layout.addWidget(self.item_table_widget)
        self._load_items_from_disk()
    def _create_properties_widget(self, properties="Consumable"):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        first_row = QHBoxLayout()
        first_row.setSpacing(8)
        consumable_checkbox = QCheckBox("Consumable")
        consumable_checkbox.setObjectName("InventoryConsumableRadio")
        weapon_checkbox = QCheckBox("Weapon")
        weapon_checkbox.setObjectName("InventoryWeaponRadio")
        first_row.addWidget(consumable_checkbox)
        first_row.addWidget(weapon_checkbox)
        second_row = QHBoxLayout()
        second_row.setSpacing(8)
        wearable_checkbox = QCheckBox("Wearable")
        wearable_checkbox.setObjectName("InventoryWearableRadio")
        readable_checkbox = QCheckBox("Readable")
        readable_checkbox.setObjectName("InventoryReadableRadio")
        second_row.addWidget(wearable_checkbox)
        second_row.addWidget(readable_checkbox)
        layout.addLayout(first_row)
        layout.addLayout(second_row)
        widget.consumable_checkbox = consumable_checkbox
        widget.weapon_checkbox = weapon_checkbox
        widget.wearable_checkbox = wearable_checkbox
        widget.readable_checkbox = readable_checkbox
        if isinstance(properties, str):
            if properties.lower() == "weapon":
                weapon_checkbox.setChecked(True)
            elif properties.lower() == "wearable":
                wearable_checkbox.setChecked(True)
            elif properties.lower() == "readable":
                readable_checkbox.setChecked(True)
            else:
                consumable_checkbox.setChecked(True)
        elif isinstance(properties, list):
            for prop in properties:
                if prop.lower() == "consumable":
                    consumable_checkbox.setChecked(True)
                elif prop.lower() == "weapon":
                    weapon_checkbox.setChecked(True)
                elif prop.lower() == "wearable":
                    wearable_checkbox.setChecked(True)
                elif prop.lower() == "readable":
                    readable_checkbox.setChecked(True)
        if not any([consumable_checkbox.isChecked(), weapon_checkbox.isChecked(), wearable_checkbox.isChecked(), readable_checkbox.isChecked()]):
            consumable_checkbox.setChecked(True)
        consumable_checkbox.stateChanged.connect(lambda: self._on_properties_changed())
        weapon_checkbox.stateChanged.connect(lambda: self._on_properties_changed())
        wearable_checkbox.stateChanged.connect(lambda: self._on_properties_changed())
        readable_checkbox.stateChanged.connect(lambda: self._on_properties_changed())
        return widget
    def _create_variable_actions_widget(self, variable_actions=None):
        if variable_actions is None:
            variable_actions = []
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(1)
        actions_container = QWidget()
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(1)
        actions_layout.setAlignment(Qt.AlignTop)
        main_layout.addWidget(actions_container)
        main_widget.actions_layout = actions_layout
        main_widget._parent_table = None
        main_widget._table_row = -1
        def updateRowHeight():
            if hasattr(main_widget, '_parent_table') and main_widget._parent_table and main_widget._table_row >= 0:
                total_height = 10
                for i in range(actions_layout.count()):
                    item = actions_layout.itemAt(i)
                    if item and item.widget():
                        total_height += 28
                main_widget._parent_table.setRowHeight(main_widget._table_row, max(total_height, 50))
        def updateSize():
            updateRowHeight()
        main_widget.updateRowHeight = updateRowHeight
        main_widget.updateSize = updateSize
        for action in variable_actions:
            self._add_variable_action_row(main_widget, action)
        if not variable_actions:
            self._add_variable_action_row(main_widget)
        main_widget.updateSize()
        return main_widget
    def _add_variable_action_row(self, parent_widget, action_data=None):
        if action_data is None:
            action_data = {
                "variable_name": "",
                "operation": "set",
                "value": ""
            }
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        var_name_input = QLineEdit(action_data.get("variable_name", ""))
        var_name_input.setObjectName("InventoryVarNameInput")
        var_name_input.setPlaceholderText("Variable name")
        var_name_input.setMaximumWidth(100)
        var_name_input.textChanged.connect(self._on_variable_action_changed)
        operation_combo = QComboBox()
        operation_combo.setObjectName("InventoryVarOperationCombo")
        operation_combo.addItems(["set", "increment", "decrement", "multiply", "divide"])
        operation_combo.setCurrentText(action_data.get("operation", "set"))
        operation_combo.setMaximumWidth(80)
        operation_combo.currentTextChanged.connect(self._on_variable_action_changed)
        value_input = QLineEdit(action_data.get("value", ""))
        value_input.setObjectName("InventoryVarValueInput")
        value_input.setPlaceholderText("Value")
        value_input.setMaximumWidth(70)
        value_input.textChanged.connect(self._on_variable_action_changed)
        add_button = QPushButton("+")
        add_button.setObjectName("AddConditionButton")
        add_button.setMaximumWidth(22)
        add_button.setMaximumHeight(22)
        add_button.setToolTip("Add variable action")
        add_button.clicked.connect(lambda: self._add_variable_action_row(parent_widget))
        remove_button = QPushButton("-")
        remove_button.setObjectName("RemoveConditionButton")
        remove_button.setMaximumWidth(22)
        remove_button.setMaximumHeight(22)
        remove_button.setToolTip("Remove this variable action")
        remove_button.clicked.connect(lambda: self._remove_this_variable_action_row(row_widget, parent_widget))
        row_layout.addWidget(var_name_input)
        row_layout.addWidget(operation_combo)
        row_layout.addWidget(value_input)
        row_layout.addStretch()
        row_layout.addWidget(add_button)
        row_layout.addWidget(remove_button)
        row_widget.var_name_input = var_name_input
        row_widget.operation_combo = operation_combo
        row_widget.value_input = value_input
        parent_widget.actions_layout.addWidget(row_widget)
        if hasattr(parent_widget, 'updateSize') and callable(parent_widget.updateSize):
            parent_widget.updateSize()
    def _remove_variable_action_row(self, parent_widget):
        layout = parent_widget.actions_layout
        if layout.count() > 0:
            item = layout.takeAt(layout.count() - 1)
            if item and item.widget():
                item.widget().deleteLater()
                self._on_variable_action_changed()
    def _remove_this_variable_action_row(self, row_widget, parent_widget):
        layout = parent_widget.actions_layout
        will_be_empty = layout.count() <= 1
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() == row_widget:
                layout.takeAt(i)
                row_widget.deleteLater()
                if will_be_empty:
                    self._add_variable_action_row(parent_widget)
                if hasattr(parent_widget, 'updateSize') and callable(parent_widget.updateSize):
                    parent_widget.updateSize()
                self._on_variable_action_changed()
                break
    def _on_variable_action_changed(self):
        sender = self.sender()
        if sender:
            current = sender
            main_widget = None
            while current and current != self:
                if hasattr(current, 'actions_layout') and hasattr(current, 'updateSize'):
                    main_widget = current
                    break
                current = current.parentWidget()
            if main_widget and hasattr(main_widget, 'updateSize') and callable(main_widget.updateSize):
                main_widget.updateSize()
            current = sender
            while current and current != self:
                if hasattr(current, 'parent') and isinstance(current.parent(), QTableWidget):
                    table = current.parent()
                    for row in range(table.rowCount()):
                        for col in range(table.columnCount()):
                            cell_widget = table.cellWidget(row, col)
                            if cell_widget and self._widget_contains_sender(cell_widget, sender):
                                table.resizeRowToContents(row)
                                dummy_item = QTableWidgetItem()
                                dummy_item.row = lambda: row
                                self._on_item_data_changed(dummy_item)
                                return
                current = current.parentWidget()
    def _widget_contains_sender(self, widget, sender):
        if widget == sender:
            return True
        for child in widget.findChildren(type(sender)):
            if child == sender:
                return True
        return False
    def _get_variable_actions_from_widget(self, widget):
        actions = []
        if not widget or not hasattr(widget, 'actions_layout'):
            return actions
        layout = widget.actions_layout
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                row_widget = item.widget()
                if hasattr(row_widget, 'var_name_input'):
                    var_name = row_widget.var_name_input.text().strip()
                    if var_name:
                        action = {
                            "variable_name": var_name,
                            "operation": row_widget.operation_combo.currentText(),
                            "value": row_widget.value_input.text().strip()
                        }
                        actions.append(action)
        return actions
    def _filter_items(self, text):
        text = text.lower()
        for row in range(self.item_table_widget.rowCount()):
            name_item = self.item_table_widget.item(row, 0)
            if name_item:
                should_show = text in name_item.text().lower()
                self.item_table_widget.setRowHidden(row, not should_show)
    def _load_items_from_disk(self):
        if not self.parent_manager:
            return
        workflow_data_dir = self.parent_manager.workflow_data_dir
        category_folder = sanitize_path_name(self.category_name)
        items_data = []
        processed_files = set()
        resource_items_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'items', category_folder)
        if os.path.isdir(resource_items_dir):
            for filename in os.listdir(resource_items_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(resource_items_dir, filename)
                    if file_path in processed_files:
                        continue
                    data = self._load_json(file_path)
                    if data and 'name' in data:
                        items_data.append((data, file_path, False))
                        processed_files.add(file_path)
        game_items_dir = os.path.join(workflow_data_dir, 'game', 'items', category_folder)
        if os.path.isdir(game_items_dir):
            for filename in os.listdir(game_items_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(game_items_dir, filename)
                    if file_path in processed_files:
                        continue
                    data = self._load_json(file_path)
                    if data and 'name' in data:
                        items_data.append((data, file_path, True))
                        processed_files.add(file_path)
        items_data.sort(key=lambda x: x[0].get('name', '').lower())
        self.item_table_widget.blockSignals(True)
        self.item_table_widget.setRowCount(len(items_data))
        for row, (data, file_path, is_game_file) in enumerate(items_data):
            display_name = data.get('name', '')
            if is_game_file:
                display_name += " *"
            name_item = QTableWidgetItem(display_name)
            name_item.setData(Qt.UserRole, file_path)
            name_item.setToolTip(f"{'Game' if is_game_file else 'Resource'} file: {file_path}")
            self.item_table_widget.setItem(row, 0, name_item)
            properties_widget = self._create_properties_widget(data.get("properties", "Consumable"))
            self.item_table_widget.setCellWidget(row, 1, properties_widget)
            variable_actions = data.get("variable_actions", [])
            variables_widget = self._create_variable_actions_widget(variable_actions)
            self.item_table_widget.setCellWidget(row, 2, variables_widget)
            if hasattr(variables_widget, '_parent_table'):
                variables_widget._parent_table = self.item_table_widget
                variables_widget._table_row = row
            value_item = QTableWidgetItem(str(data.get("base_value", "0")))
            self.item_table_widget.setItem(row, 3, value_item)
            desc_item = QTableWidgetItem(data.get("description", ""))
            self.item_table_widget.setItem(row, 4, desc_item)
        self.item_table_widget.blockSignals(False)
        for row in range(self.item_table_widget.rowCount()):
            self.item_table_widget.resizeRowToContents(row)
    def _add_item(self):
        item_name, ok = QInputDialog.getText(self, "Add Item", f"Enter item name for {self.category_name}:")
        if not ok or not item_name.strip():
            return
        item_name = item_name.strip()
        sanitized_name = sanitize_path_name(item_name)
        json_filename = f"{sanitized_name}.json"
        items_dir = os.path.join(self.parent_manager.workflow_data_dir, 'resources', 'data files', 'items', sanitize_path_name(self.category_name))
        item_path = os.path.join(items_dir, json_filename)
        try:
            os.makedirs(items_dir, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not create items directory. Error: {e}")
            return
        if os.path.exists(item_path):
            QMessageBox.warning(self, "Error", f"An item named '{json_filename}' already exists in this category.")
            return
        default_data = {
            "name": item_name,
            "properties": "Consumable",
            "variable_actions": [],
            "base_value": "0",
            "description": ""
        }
        if not self._save_json(item_path, default_data):
            QMessageBox.critical(self, "Error", f"Failed to create item '{item_name}'.")
            return
        self._load_items_from_disk()
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None
    def _remove_item(self):
        current_row = self.item_table_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select an item to remove.")
            return
        name_item = self.item_table_widget.item(current_row, 0)
        if not name_item:
            return
        file_path = name_item.data(Qt.UserRole)
        item_name = name_item.text().replace(" *", "")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            self._load_items_from_disk()
            main_ui = self._get_main_ui()
            if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                try:
                    main_ui.delete_rule_sound.play()
                except Exception:
                    main_ui.delete_rule_sound = None
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not remove item. Error: {e}")
    def _on_item_data_changed(self, item):
        if not item:
            return
        row = item.row()
        name_item = self.item_table_widget.item(row, 0)
        if not name_item:
            return
        file_path = name_item.data(Qt.UserRole)
        if not file_path:
            return
        data = self._get_item_data_from_table_row(row)
        old_data = self._load_json(file_path)
        old_name = old_data.get('name', '') if old_data else ''
        new_name = data.get('name', '')
        if not self._save_json(file_path, data):
            QMessageBox.critical(self, "Save Error", f"Failed to save item data.")
            return
        if old_name != new_name and new_name.strip():
            new_sanitized_name = sanitize_path_name(new_name)
            new_filename = f"{new_sanitized_name}.json"
            new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
            if os.path.normpath(file_path) != os.path.normpath(new_file_path):
                if os.path.exists(new_file_path):
                    QMessageBox.warning(self, "Name Conflict", f"An item named '{new_filename}' already exists.")
                    self.item_table_widget.blockSignals(True)
                    name_item.setText(old_name)
                    self.item_table_widget.blockSignals(False)
                    return
                try:
                    shutil.move(file_path, new_file_path)
                    name_item.setData(Qt.UserRole, new_file_path)
                    self._load_items_from_disk()
                except OSError as e:
                    QMessageBox.critical(self, "Rename Error", f"Failed to rename item file. Error: {e}")
    def _get_item_data_from_table_row(self, row):
        data = {}
        name_item = self.item_table_widget.item(row, 0)
        data['name'] = name_item.text().replace(" *", "") if name_item else ""
        properties_widget = self.item_table_widget.cellWidget(row, 1)
        if properties_widget:
            selected_properties = []
            if hasattr(properties_widget, 'consumable_checkbox') and properties_widget.consumable_checkbox.isChecked():
                selected_properties.append("Consumable")
            if hasattr(properties_widget, 'weapon_checkbox') and properties_widget.weapon_checkbox.isChecked():
                selected_properties.append("Weapon")
            if hasattr(properties_widget, 'wearable_checkbox') and properties_widget.wearable_checkbox.isChecked():
                selected_properties.append("Wearable")
            if hasattr(properties_widget, 'readable_checkbox') and properties_widget.readable_checkbox.isChecked():
                selected_properties.append("Readable")
            if len(selected_properties) > 1:
                data['properties'] = selected_properties
            elif len(selected_properties) == 1:
                data['properties'] = selected_properties[0]
            else:
                data['properties'] = "Consumable"
        else:
            data['properties'] = "Consumable"
        variables_widget = self.item_table_widget.cellWidget(row, 2)
        if variables_widget:
            data['variable_actions'] = self._get_variable_actions_from_widget(variables_widget)
        else:
            data['variable_actions'] = []
        value_item = self.item_table_widget.item(row, 3)
        data['base_value'] = value_item.text() if value_item else "0"
        desc_item = self.item_table_widget.item(row, 4)
        data['description'] = desc_item.text() if desc_item else ""
        return data
    def _load_json(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return {}
    def _save_json(self, file_path, data):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            return False
    def _get_main_ui(self):
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'add_rule_sound'):
                return parent
            parent = parent.parentWidget()
        return None
    def _on_properties_changed(self):
        sender = self.sender()
        if not sender:
            return
        current = sender
        while current and current != self:
            parent = current.parentWidget()
            if isinstance(parent, QTableWidget):
                table = parent
                for row in range(table.rowCount()):
                    for col in range(table.columnCount()):
                        cell_widget = table.cellWidget(row, col)
                        if cell_widget and self._widget_contains_checkbox(cell_widget, sender):
                            dummy_item = QTableWidgetItem()
                            dummy_item.row = lambda: row
                            self._on_item_data_changed(dummy_item)
                            return
            current = parent
    def _widget_contains_checkbox(self, widget, checkbox):
        if widget == checkbox:
            return True
        if hasattr(widget, 'consumable_checkbox') and widget.consumable_checkbox == checkbox:
            return True
        if hasattr(widget, 'weapon_checkbox') and widget.weapon_checkbox == checkbox:
            return True
        if hasattr(widget, 'wearable_checkbox') and widget.wearable_checkbox == checkbox:
            return True
        if hasattr(widget, 'readable_checkbox') and widget.readable_checkbox == checkbox:
            return True
        return False


class InventoryManagerWidget(QWidget):
    def __init__(self, parent=None, workflow_data_dir=None):
        super().__init__(parent)
        self.workflow_data_dir = workflow_data_dir or "data"
        self._init_ui()
        self._load_categories()
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        tab_management_layout = QHBoxLayout()
        self.categories_label = QLabel("Categories:")
        self.categories_label.setObjectName("InventoryTabHeaderLabel")
        self.categories_label.setAlignment(Qt.AlignCenter)
        tab_management_layout.addStretch(1)
        tab_management_layout.addWidget(self.categories_label)
        tab_management_layout.addStretch(1)
        self.add_tab_button = QPushButton("+")
        self.add_tab_button.setObjectName("AddInventoryTabButton")
        self.add_tab_button.setToolTip("Add new inventory category")
        self.add_tab_button.clicked.connect(self._add_category)
        self.remove_tab_button = QPushButton("-")
        self.remove_tab_button.setObjectName("RemoveInventoryTabButton")
        self.remove_tab_button.setToolTip("Remove current inventory category")
        self.remove_tab_button.clicked.connect(self._remove_category)
        tab_management_layout.addWidget(self.add_tab_button)
        tab_management_layout.addWidget(self.remove_tab_button)
        main_layout.addLayout(tab_management_layout)
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("InventoryTabWidget")
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setExpanding(False)
        tab_bar.setElideMode(Qt.ElideNone)
        tab_bar.setUsesScrollButtons(True)
        self.tab_widget.currentChanged.connect(self._play_tab_switch_sound)
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    def _load_categories(self):
        categories = set()
        resource_items_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'items')
        if os.path.isdir(resource_items_dir):
            for folder_name in os.listdir(resource_items_dir):
                folder_path = os.path.join(resource_items_dir, folder_name)
                if os.path.isdir(folder_path):
                    display_name = folder_name.replace('_', ' ').title()
                    categories.add(display_name)
        game_items_dir = os.path.join(self.workflow_data_dir, 'game', 'items')
        if os.path.isdir(game_items_dir):
            for folder_name in os.listdir(game_items_dir):
                folder_path = os.path.join(game_items_dir, folder_name)
                if os.path.isdir(folder_path):
                    display_name = folder_name.replace('_', ' ').title()
                    categories.add(display_name)
        if not categories:
            categories = {"All", "Weapons", "Armor", "Consumables"}
        for category in sorted(categories):
            self._create_category_tab(category)
    def _create_category_tab(self, category_name):
        page_widget = InventoryCategoryPage(category_name, self)
        self.tab_widget.addTab(page_widget, category_name)
        page_widget._load_items_from_disk()
    def _add_category(self):
        category_name, ok = QInputDialog.getText(self, "Add Category", "Enter category name:")
        if not ok or not category_name.strip():
            return
        category_name = category_name.strip()
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i).lower() == category_name.lower():
                QMessageBox.warning(self, "Category Exists", f"Category '{category_name}' already exists.")
                return
        sanitized_category = sanitize_path_name(category_name)
        category_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'items', sanitized_category)
        try:
            os.makedirs(category_dir, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Error", f"Could not create category directory. Error: {e}")
            return
        self._create_category_tab(category_name)
        new_index = self.tab_widget.count() - 1
        self.tab_widget.setCurrentIndex(new_index)
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None
    def _remove_category(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < 0:
            QMessageBox.warning(self, "No Category", "No category selected to remove.")
            return
        if self.tab_widget.count() == 1:
            QMessageBox.information(self, "Cannot Remove", "Cannot remove the last category.")
            return
        category_name = self.tab_widget.tabText(current_index)
        sanitized_category = sanitize_path_name(category_name)
        for base_dir in ['resources', 'game']:
            category_dir = os.path.join(self.workflow_data_dir, base_dir, 'data files', 'items', sanitized_category)
            if os.path.exists(category_dir):
                try:
                    import shutil
                    shutil.rmtree(category_dir)
                except OSError as e:
                    pass
        widget_to_remove = self.tab_widget.widget(current_index)
        self.tab_widget.removeTab(current_index)
        if widget_to_remove:
            widget_to_remove.deleteLater()
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
            try:
                main_ui.delete_rule_sound.play()
            except Exception:
                main_ui.delete_rule_sound = None
    def _play_tab_switch_sound(self, index):
        try:
            import pygame
            mixer_initialized = pygame.mixer.get_init()
            main_ui = self._get_main_ui()
            if not main_ui:
                return
            if hasattr(main_ui, '_eft_splitter_sound') and main_ui._eft_splitter_sound:
                main_ui._eft_splitter_sound.play()
            else:
                if not mixer_initialized:
                    pygame.mixer.init()
                    mixer_initialized_after_attempt = pygame.mixer.get_init()
                    if not mixer_initialized_after_attempt:
                        return
                left_splitter_sound = pygame.mixer.Sound('sounds/LeftSplitterSelection.mp3')
                left_splitter_sound.play()
                main_ui._eft_splitter_sound = left_splitter_sound
        except Exception as e:
            pass
    def _get_main_ui(self):
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'add_rule_sound'):
                return parent
            parent = parent.parentWidget()
        return None