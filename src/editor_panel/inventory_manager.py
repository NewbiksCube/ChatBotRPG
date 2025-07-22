from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, 
                             QHBoxLayout, QInputDialog, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QLineEdit, QComboBox, QCheckBox, QTreeWidget, QTreeWidgetItem,
                             QDialog, QFormLayout, QSpinBox, QTextEdit, QDialogButtonBox,
                             QScrollArea, QSplitter, QButtonGroup, QStackedWidget,
                             QListWidget, QListWidgetItem)
from PyQt5.QtGui import QFont, QDrag
from PyQt5.QtCore import Qt, QMimeData
import os
import json
import re
import shutil
import uuid

def sanitize_path_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', name).strip()
    sanitized = sanitized.replace(' ', '_').lower()
    return sanitized or 'untitled'

def generate_item_id():
    return f"{uuid.uuid4().hex[:8]}"

class ItemInstanceDialog(QDialog):
    def __init__(self, parent=None, workflow_data_dir=None, existing_item_data=None):
        super().__init__(parent)
        self.workflow_data_dir = workflow_data_dir
        self.existing_item_data = existing_item_data
        self.selected_resource_item = None
        self.selected_resource_category = None
        self._init_ui()
        self._load_resource_items()
        if existing_item_data:
            self._populate_from_existing()
    
    def _init_ui(self):
        self.setWindowTitle("Add/Edit Item Instance")
        self.setModal(True)
        self.resize(600, 500)
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.resource_category_combo = QComboBox()
        self.resource_category_combo.currentTextChanged.connect(self._on_category_changed)
        form_layout.addRow("Resource Category:", self.resource_category_combo)
        self.resource_item_combo = QComboBox()
        self.resource_item_combo.currentTextChanged.connect(self._on_item_changed)
        form_layout.addRow("Resource Item:", self.resource_item_combo)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(999)
        self.quantity_spin.setValue(1)
        form_layout.addRow("Quantity:", self.quantity_spin)
        self.durability_spin = QSpinBox()
        self.durability_spin.setMinimum(0)
        self.durability_spin.setMaximum(100)
        self.durability_spin.setValue(100)
        form_layout.addRow("Durability (%):", self.durability_spin)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", self.description_edit)
        layout.addLayout(form_layout)
        self.custom_properties_label = QLabel("Custom Properties:")
        layout.addWidget(self.custom_properties_label)
        self.custom_properties_edit = QTextEdit()
        self.custom_properties_edit.setMaximumHeight(100)
        self.custom_properties_edit.setPlaceholderText("Enter custom properties as JSON (e.g., {\"enchantment\": \"fire\", \"crafted_by\": \"Blacksmith\"})")
        layout.addWidget(self.custom_properties_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_resource_items(self):
        self.resource_categories = []
        self.resource_items = {}
        resource_items_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'items')
        if os.path.isdir(resource_items_dir):
            for category_name in os.listdir(resource_items_dir):
                category_path = os.path.join(resource_items_dir, category_name)
                if os.path.isdir(category_path):
                    self.resource_categories.append(category_name)
                    self.resource_items[category_name] = []
                    for filename in os.listdir(category_path):
                        if filename.lower().endswith('.json'):
                            file_path = os.path.join(category_path, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    item_data = json.load(f)
                                    if 'name' in item_data:
                                        self.resource_items[category_name].append(item_data['name'])
                            except Exception:
                                continue
        
        self.resource_category_combo.addItems(sorted(self.resource_categories))
    
    def _on_category_changed(self, category):
        self.resource_item_combo.clear()
        if category in self.resource_items:
            self.resource_item_combo.addItems(sorted(self.resource_items[category]))
        self.selected_resource_category = category
    
    def _on_item_changed(self, item_name):
        self.selected_resource_item = item_name
    
    def _populate_from_existing(self):
        if not self.existing_item_data:
            return
        resource_item = self.existing_item_data.get('resource_item', '')
        resource_category = self.existing_item_data.get('resource_category', '')
        if resource_category in self.resource_categories:
            self.resource_category_combo.setCurrentText(resource_category)
            if resource_item in self.resource_items.get(resource_category, []):
                self.resource_item_combo.setCurrentText(resource_item)
        self.quantity_spin.setValue(self.existing_item_data.get('quantity', 1))
        self.durability_spin.setValue(self.existing_item_data.get('durability', 100))
        self.description_edit.setPlainText(self.existing_item_data.get('description', ''))
        custom_props = self.existing_item_data.get('custom_properties', {})
        if custom_props:
            self.custom_properties_edit.setPlainText(json.dumps(custom_props, indent=2))
    
    def get_item_data(self):
        try:
            custom_props_text = self.custom_properties_edit.toPlainText().strip()
            custom_properties = {}
            if custom_props_text:
                custom_properties = json.loads(custom_props_text)
        except json.JSONDecodeError:
            custom_properties = {}
        
        return {
            "item_id": self.existing_item_data.get('item_id', generate_item_id()) if self.existing_item_data else generate_item_id(),
            "resource_item": self.selected_resource_item,
            "resource_category": self.selected_resource_category,
            "quantity": self.quantity_spin.value(),
            "durability": self.durability_spin.value(),
            "description": self.description_edit.toPlainText().strip(),
            "custom_properties": custom_properties,
            "contains": self.existing_item_data.get('contains', []) if self.existing_item_data else []
        }

class ItemInstanceWidget(QWidget):
    def __init__(self, parent=None, workflow_data_dir=None, owner_id=None, location_id=None):
        super().__init__(parent)
        self.workflow_data_dir = workflow_data_dir
        self.owner_id = owner_id
        self.location_id = location_id
        self._init_ui()
        self._load_items()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Inventory Items:"))
        header_layout.addStretch()
        self.add_item_btn = QPushButton("+")
        self.add_item_btn.setObjectName("AddButton")
        self.add_item_btn.setToolTip("Add Item Instance")
        self.add_item_btn.setMaximumWidth(30)
        self.add_item_btn.clicked.connect(self._add_item_instance)
        header_layout.addWidget(self.add_item_btn)
        self.remove_item_btn = QPushButton("-")
        self.remove_item_btn.setObjectName("RemoveButton")
        self.remove_item_btn.setToolTip("Remove Selected Item")
        self.remove_item_btn.setMaximumWidth(30)
        self.remove_item_btn.clicked.connect(self._remove_item_instance)
        header_layout.addWidget(self.remove_item_btn)
        layout.addLayout(header_layout)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setObjectName("InventoryTreeWidget")
        self.tree_widget.setHeaderLabels(["Item", "Quantity", "Durability", "Description"])
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree_widget.setFocusPolicy(Qt.NoFocus)
        self.tree_widget.itemDoubleClicked.connect(self._edit_item_instance)
        self.tree_widget.setColumnWidth(0, 200)
        self.tree_widget.setColumnWidth(1, 80)
        self.tree_widget.setColumnWidth(2, 80)
        layout.addWidget(self.tree_widget)
    
    def _load_items(self):
        self.tree_widget.clear()
        if not hasattr(self, 'current_items'):
            self.current_items = []
        for item_data in self.current_items:
            self._add_item_to_tree(item_data)
    
    def _add_item_to_tree(self, item_data, parent_item=None):
        display_name = item_data.get('resource_item', 'Unknown Item')
        quantity = item_data.get('quantity', 1)
        durability = item_data.get('durability', 100)
        description = item_data.get('description', '')
        if quantity > 1:
            display_name = f"{display_name} (x{quantity})"
        if durability < 100:
            display_name = f"{display_name} [{durability}%]"
        tree_item = QTreeWidgetItem(parent_item or self.tree_widget)
        tree_item.setText(0, display_name)
        tree_item.setText(1, str(quantity))
        tree_item.setText(2, f"{durability}%")
        tree_item.setText(3, description[:50] + "..." if len(description) > 50 else description)
        tree_item.setData(0, Qt.UserRole, item_data)
        if parent_item:
            parent_item.addChild(tree_item)
        else:
            self.tree_widget.addTopLevelItem(tree_item)
        contains = item_data.get('contains', [])
        for contained_item in contains:
            self._add_item_to_tree(contained_item, tree_item)
        if contains:
            tree_item.setExpanded(True)
    
    def _add_item_instance(self):
        dialog = ItemInstanceDialog(self, self.workflow_data_dir)
        if dialog.exec_() == QDialog.Accepted:
            item_data = dialog.get_item_data()
            item_data['owner'] = self.owner_id
            item_data['location'] = self.location_id
            self.current_items.append(item_data)
            self._add_item_to_tree(item_data)
            self._save_items()
    
    def _remove_item_instance(self):
        current_item = self.tree_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an item to remove.")
            return
        item_data = current_item.data(0, Qt.UserRole)
        if not item_data:
            return
        reply = QMessageBox.question(self, "Remove Item", 
                                   f"Are you sure you want to remove '{item_data.get('resource_item', 'Unknown')}'?",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._remove_item_from_list(item_data)
            self._load_items()
            self._save_items()
    
    def _remove_item_from_list(self, target_item_data, items_list=None):
        if items_list is None:
            items_list = self.current_items
        
        for i, item_data in enumerate(items_list):
            if item_data.get('item_id') == target_item_data.get('item_id'):
                items_list.pop(i)
                return True
            
            contains = item_data.get('contains', [])
            if self._remove_item_from_list(target_item_data, contains):
                return True
        
        return False
    
    def _edit_item_instance(self, item, column):
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        dialog = ItemInstanceDialog(self, self.workflow_data_dir, item_data)
        if dialog.exec_() == QDialog.Accepted:
            new_item_data = dialog.get_item_data()
            new_item_data['owner'] = self.owner_id
            new_item_data['location'] = self.location_id
            new_item_data['contains'] = item_data.get('contains', [])
            
            self._update_item_in_list(item_data.get('item_id'), new_item_data)
            self._load_items()
            self._save_items()
    
    def _update_item_in_list(self, target_item_id, new_item_data, items_list=None):
        if items_list is None:
            items_list = self.current_items
        
        for i, item_data in enumerate(items_list):
            if item_data.get('item_id') == target_item_id:
                items_list[i] = new_item_data
                return True
            
            contains = item_data.get('contains', [])
            if self._update_item_in_list(target_item_id, new_item_data, contains):
                return True
        
        return False
    
    def _save_items(self):
        if hasattr(self.parent(), '_schedule_details_save'):
            self.parent()._schedule_details_save()
    
    def set_items(self, items_data):
        self.current_items = items_data if items_data else []
        self._load_items()
    
    def get_items(self):
        return self.current_items

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
        self.item_table_widget.setColumnCount(7)
        self.item_table_widget.setHorizontalHeaderLabels(["Name", "Properties", "Containers", "Variables", "Base Value", "Weight", "Description"])
        self.item_table_widget.horizontalHeader().setObjectName("InventoryTableWidget_Tab_HorizontalHeader")
        self.item_table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.item_table_widget.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.item_table_widget.setColumnWidth(1, 250)
        self.item_table_widget.setColumnWidth(2, 250)
        self.item_table_widget.setColumnWidth(3, 500)
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
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setSpacing(4)
        first_row = QHBoxLayout()
        first_row.setSpacing(8)
        consumable_checkbox = QCheckBox("Consumable")
        consumable_checkbox.setObjectName("InventoryConsumableRadio")
        wearable_checkbox = QCheckBox("Wearable")
        wearable_checkbox.setObjectName("InventoryWearableRadio")
        first_row.addWidget(consumable_checkbox)
        first_row.addWidget(wearable_checkbox)
        second_row = QHBoxLayout()
        second_row.setSpacing(8)
        readable_checkbox = QCheckBox("Readable")
        readable_checkbox.setObjectName("InventoryReadableRadio")
        liquid_checkbox = QCheckBox("Liquid")
        liquid_checkbox.setObjectName("InventoryLiquidRadio")
        second_row.addWidget(readable_checkbox)
        second_row.addWidget(liquid_checkbox)
        second_row.addStretch()
        layout.addLayout(first_row)
        layout.addLayout(second_row)
        widget.setMinimumHeight(60)
        widget.consumable_checkbox = consumable_checkbox
        widget.wearable_checkbox = wearable_checkbox
        widget.readable_checkbox = readable_checkbox
        widget.liquid_checkbox = liquid_checkbox
        if isinstance(properties, str):
            if properties.lower() == "wearable":
                wearable_checkbox.setChecked(True)
            elif properties.lower() == "readable":
                readable_checkbox.setChecked(True)
            elif properties.lower() == "liquid":
                liquid_checkbox.setChecked(True)
            else:
                consumable_checkbox.setChecked(True)
        elif isinstance(properties, list):
            for prop in properties:
                if prop.lower() == "consumable":
                    consumable_checkbox.setChecked(True)
                elif prop.lower() == "wearable":
                    wearable_checkbox.setChecked(True)
                elif prop.lower() == "readable":
                    readable_checkbox.setChecked(True)
                elif prop.lower() == "liquid":
                    liquid_checkbox.setChecked(True)
        if not any([consumable_checkbox.isChecked(), wearable_checkbox.isChecked(), readable_checkbox.isChecked(), liquid_checkbox.isChecked()]):
            consumable_checkbox.setChecked(True)
        consumable_checkbox.stateChanged.connect(lambda: self._on_properties_changed())
        wearable_checkbox.stateChanged.connect(lambda: self._on_properties_changed())
        readable_checkbox.stateChanged.connect(lambda: self._on_properties_changed())
        liquid_checkbox.stateChanged.connect(lambda: self._on_properties_changed())
        return widget

    def _create_containers_widget(self, containers=None, liquid_containers=None):
        if containers is None:
            containers = []
        if liquid_containers is None:
            liquid_containers = []
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        if not containers:
            no_containers_label = QLabel("None")
            no_containers_label.setObjectName("InventoryContainerLabel")
            no_containers_label.setStyleSheet("font: 9pt 'Consolas';")
            layout.addWidget(no_containers_label)
        else:
            for container_name in containers:
                container_row = QHBoxLayout()
                container_row.setSpacing(4)
                
                container_label = QLabel(container_name)
                container_label.setObjectName("InventoryContainerLabel")
                container_label.setStyleSheet("font: 9pt 'Consolas';")
                container_label.setMaximumWidth(120)
                
                liquid_checkbox = QCheckBox("Holds Liquids")
                liquid_checkbox.setObjectName("InventoryContainerLiquidCheckbox")
                liquid_checkbox.setChecked(container_name in liquid_containers)
                liquid_checkbox.stateChanged.connect(lambda state, name=container_name, w=widget: self._on_container_liquid_changed(w, name, state))
                
                container_row.addWidget(container_label)
                container_row.addWidget(liquid_checkbox)
                container_row.addStretch()
                layout.addLayout(container_row)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)
        add_container_btn = QPushButton("+")
        add_container_btn.setObjectName("AddConditionButton")
        add_container_btn.setMaximumWidth(22)
        add_container_btn.setMaximumHeight(22)
        add_container_btn.setToolTip("Add container")
        add_container_btn.clicked.connect(lambda: self._add_container_item(widget, containers, liquid_containers))
        remove_container_btn = QPushButton("-")
        remove_container_btn.setObjectName("RemoveConditionButton")
        remove_container_btn.setMaximumWidth(22)
        remove_container_btn.setMaximumHeight(22)
        remove_container_btn.setToolTip("Remove container")
        remove_container_btn.clicked.connect(lambda: self._remove_container_item(widget, containers, liquid_containers))
        buttons_layout.addWidget(add_container_btn)
        buttons_layout.addWidget(remove_container_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        widget.containers = containers
        widget.liquid_containers = liquid_containers
        widget.setMinimumHeight(40)
        return widget

    def _add_container_item(self, widget, containers, liquid_containers):
        container_name, ok = QInputDialog.getText(self, "Add Container", "Enter container name:")
        if ok and container_name.strip():
            containers.append(container_name.strip())
            widget.containers = containers
            self._on_containers_changed()

    def _remove_container_item(self, widget, containers, liquid_containers):
        if not containers:
            return
        container_name, ok = QInputDialog.getItem(self, "Remove Container", "Select container to remove:", containers, 0, False)
        if ok and container_name:
            containers.remove(container_name)
            if container_name in liquid_containers:
                liquid_containers.remove(container_name)
            widget.containers = containers
            widget.liquid_containers = liquid_containers
            self._on_containers_changed()

    def _on_container_liquid_changed(self, widget, container_name, state):
        if not hasattr(widget, 'liquid_containers'):
            widget.liquid_containers = []
        
        if state == Qt.Checked:
            if container_name not in widget.liquid_containers:
                widget.liquid_containers.append(container_name)
        else:
            if container_name in widget.liquid_containers:
                widget.liquid_containers.remove(container_name)
        
        self._on_containers_changed()

    def _on_containers_changed(self):
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
                        if cell_widget and hasattr(cell_widget, 'containers') and self._widget_contains_sender(cell_widget, sender):
                            dummy_item = QTableWidgetItem()
                            dummy_item.row = lambda: row
                            self._on_item_data_changed(dummy_item)
                            return
            current = parent

    def _get_containers_from_widget(self, widget):
        containers = []
        liquid_containers = []
        if not widget or not hasattr(widget, 'containers'):
            return containers, liquid_containers
        containers = widget.containers.copy()
        if hasattr(widget, 'liquid_containers'):
            liquid_containers = widget.liquid_containers.copy()
        return containers, liquid_containers
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
                        total_height += 35
                main_widget._parent_table.setRowHeight(main_widget._table_row, max(total_height, 60))
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
            containers_widget = self._create_containers_widget(data.get("containers", []), data.get("liquid_containers", []))
            self.item_table_widget.setCellWidget(row, 2, containers_widget)
            variable_actions = data.get("variable_actions", [])
            variables_widget = self._create_variable_actions_widget(variable_actions)
            self.item_table_widget.setCellWidget(row, 3, variables_widget)
            if hasattr(variables_widget, '_parent_table'):
                variables_widget._parent_table = self.item_table_widget
                variables_widget._table_row = row
            value_item = QTableWidgetItem(str(data.get("base_value", "0")))
            self.item_table_widget.setItem(row, 4, value_item)
            weight_item = QTableWidgetItem(str(data.get("weight", "0")))
            self.item_table_widget.setItem(row, 5, weight_item)
            desc_item = QTableWidgetItem(data.get("description", ""))
            self.item_table_widget.setItem(row, 6, desc_item)
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
            "containers": [],
            "variable_actions": [],
            "base_value": "0",
            "weight": "0",
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
            if hasattr(properties_widget, 'wearable_checkbox') and properties_widget.wearable_checkbox.isChecked():
                selected_properties.append("Wearable")
            if hasattr(properties_widget, 'readable_checkbox') and properties_widget.readable_checkbox.isChecked():
                selected_properties.append("Readable")
            if hasattr(properties_widget, 'liquid_checkbox') and properties_widget.liquid_checkbox.isChecked():
                selected_properties.append("Liquid")
            if len(selected_properties) > 1:
                data['properties'] = selected_properties
            elif len(selected_properties) == 1:
                data['properties'] = selected_properties[0]
            else:
                data['properties'] = "Consumable"
        else:
            data['properties'] = "Consumable"
        containers_widget = self.item_table_widget.cellWidget(row, 2)
        if containers_widget:
            containers, liquid_containers = self._get_containers_from_widget(containers_widget)
            data['containers'] = containers
            if liquid_containers:
                data['liquid_containers'] = liquid_containers
        else:
            data['containers'] = []
        variables_widget = self.item_table_widget.cellWidget(row, 3)
        if variables_widget:
            data['variable_actions'] = self._get_variable_actions_from_widget(variables_widget)
        else:
            data['variable_actions'] = []
        value_item = self.item_table_widget.item(row, 4)
        data['base_value'] = value_item.text() if value_item else "0"
        weight_item = self.item_table_widget.item(row, 5)
        data['weight'] = weight_item.text() if weight_item else "0"
        desc_item = self.item_table_widget.item(row, 6)
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
        if hasattr(widget, 'wearable_checkbox') and widget.wearable_checkbox == checkbox:
            return True
        if hasattr(widget, 'readable_checkbox') and widget.readable_checkbox == checkbox:
            return True
        if hasattr(widget, 'liquid_checkbox') and widget.liquid_checkbox == checkbox:
            return True
        return False

class DraggableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.tabBar().setExpanding(False)
        self.tabBar().setElideMode(Qt.ElideNone)
        self.tabBar().setUsesScrollButtons(True)
        self.tabBar().installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.tabBar() and event.type() == event.MouseButtonDblClick:
            tab_index = self.tabBar().tabAt(event.pos())
            if tab_index >= 0:
                self._rename_tab(tab_index)
                return True
        return super().eventFilter(obj, event)

    def _rename_tab(self, tab_index):
        current_name = self.tabText(tab_index)
        new_name, ok = QInputDialog.getText(self, "Rename Category", 
                                           "Enter new category name:", 
                                           text=current_name)
        if ok and new_name.strip() and new_name.strip() != current_name:
            new_name = new_name.strip()
            
            for i in range(self.count()):
                if i != tab_index and self.tabText(i).lower() == new_name.lower():
                    QMessageBox.warning(self, "Category Exists", 
                                       f"Category '{new_name}' already exists.")
                    return
            
            self.setTabText(tab_index, new_name)
            
            if hasattr(self.parent(), '_save_tab_order'):
                self.parent()._save_tab_order()

class InventoryManagerWidget(QWidget):
    def __init__(self, parent=None, workflow_data_dir=None, theme_colors=None):
        super().__init__(parent)
        self.workflow_data_dir = workflow_data_dir or "data"
        self.theme_colors = theme_colors or {}
        self.current_inventory_data = []
        self.is_loading_data = False
        self.container_selection_path = []
        self._init_ui()
        self._load_categories()
        if self.theme_colors:
            self.update_theme(self.theme_colors)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        mode_toggle_container = QWidget()
        mode_toggle_container.setObjectName("InventoryModeToggleContainer")
        mode_toggle_layout = QHBoxLayout(mode_toggle_container)
        mode_toggle_layout.setContentsMargins(5, 5, 5, 5)
        mode_toggle_layout.setSpacing(10)
        self.mode_toggle_group = QButtonGroup(self)
        self.references_btn = QPushButton("References")
        self.references_btn.setObjectName("InventoryReferencesToggleButton")
        self.references_btn.setCheckable(True)
        self.references_btn.setChecked(True)
        self.references_btn.setMinimumHeight(30)
        self.references_btn.setFont(QFont('Consolas', 10))
        self.references_btn.setFocusPolicy(Qt.NoFocus)
        self.instances_btn = QPushButton("Instances")
        self.instances_btn.setObjectName("InventoryInstancesToggleButton")
        self.instances_btn.setCheckable(True)
        self.instances_btn.setMinimumHeight(30)
        self.instances_btn.setFont(QFont('Consolas', 10))
        self.instances_btn.setFocusPolicy(Qt.NoFocus)
        self.mode_toggle_group.addButton(self.references_btn)
        self.mode_toggle_group.addButton(self.instances_btn)
        mode_toggle_layout.addWidget(self.references_btn)
        mode_toggle_layout.addWidget(self.instances_btn)
        main_layout.addWidget(mode_toggle_container)
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("InventoryContentStack")
        self.references_widget = QWidget()
        references_layout = QVBoxLayout(self.references_widget)
        references_layout.setContentsMargins(0, 0, 0, 0)
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
        references_layout.addLayout(tab_management_layout)
        self.tab_widget = DraggableTabWidget()
        self.tab_widget.setObjectName("InventoryTabWidget")

        self.tab_widget.currentChanged.connect(self._play_tab_switch_sound)
        self.tab_widget.tabBar().tabMoved.connect(self._on_tab_moved)
        references_layout.addWidget(self.tab_widget)
        self.instances_widget = QWidget()
        instances_main_layout = QVBoxLayout(self.instances_widget)
        instances_main_layout.setContentsMargins(0, 0, 0, 0)
        instances_main_layout.setSpacing(0)
        self.instances_splitter = QSplitter(Qt.Vertical)
        self.instances_splitter.setObjectName("InventoryInstancesSplitter")
        lists_container = QWidget()
        lists_layout = QHBoxLayout(lists_container)
        lists_layout.setContentsMargins(10, 10, 10, 10)
        lists_layout.setSpacing(10)
        settings_col = QVBoxLayout()
        settings_col.setSpacing(5)
        settings_label = QLabel("Settings")
        settings_label.setObjectName("InventoryInstancesSettingsLabel")
        settings_label.setAlignment(Qt.AlignCenter)
        settings_label.setFont(QFont('Consolas', 10, QFont.Bold))
        self.settings_search = QLineEdit()
        self.settings_search.setObjectName("TimerRulesFilterInput")
        self.settings_search.setPlaceholderText("Search settings...")
        self.settings_search.setMinimumHeight(24)
        self.settings_search.setFont(QFont('Consolas', 10))
        self.settings_list = QListWidget()
        self.settings_list.setObjectName("RulesList")
        self.settings_list.setAlternatingRowColors(True)
        self.settings_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.settings_list.setFocusPolicy(Qt.NoFocus)
        self.settings_list.setFont(QFont('Consolas', 10))
        self.settings_list.itemSelectionChanged.connect(self._on_instances_selection_changed)
        settings_col.addWidget(settings_label)
        settings_col.addWidget(self.settings_search)
        settings_col.addWidget(self.settings_list, 1)
        lists_layout.addLayout(settings_col, 1)
        actors_col = QVBoxLayout()
        actors_col.setSpacing(5)
        actors_label = QLabel("Actors")
        actors_label.setObjectName("InventoryInstancesActorsLabel")
        actors_label.setAlignment(Qt.AlignCenter)
        actors_label.setFont(QFont('Consolas', 10, QFont.Bold))
        self.actors_search = QLineEdit()
        self.actors_search.setObjectName("TimerRulesFilterInput")
        self.actors_search.setPlaceholderText("Search actors...")
        self.actors_search.setMinimumHeight(24)
        self.actors_search.setFont(QFont('Consolas', 10))
        self.actors_list = QListWidget()
        self.actors_list.setObjectName("RulesList")
        self.actors_list.setAlternatingRowColors(True)
        self.actors_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.actors_list.setFocusPolicy(Qt.NoFocus)
        self.actors_list.setFont(QFont('Consolas', 10))
        self.actors_list.itemSelectionChanged.connect(self._on_instances_selection_changed)
        actors_col.addWidget(actors_label)
        actors_col.addWidget(self.actors_search)
        actors_col.addWidget(self.actors_list, 1)
        lists_layout.addLayout(actors_col, 1)
        lists_container.setLayout(lists_layout)
        self.instances_splitter.addWidget(lists_container)
        self.instances_bottom_widget = QWidget()
        self.instances_bottom_widget.setObjectName("InventoryInstancesBottomWidget")
        self.instances_bottom_widget.setMinimumHeight(100)
        bottom_layout = QVBoxLayout(self.instances_bottom_widget)
        bottom_layout.setContentsMargins(10, 10, 10, 10)
        table_header_layout = QHBoxLayout()
        self.inventory_title_label = QLabel("Items in (selected item):")
        self.inventory_title_label.setObjectName("InventoryInstancesTitleLabel")
        self.inventory_title_label.setAlignment(Qt.AlignCenter)
        self.inventory_title_label.setFont(QFont('Consolas', 10, QFont.Bold))
        table_header_layout.addWidget(self.inventory_title_label)
        table_header_layout.addStretch()
        self.add_instance_btn = QPushButton("+")
        self.add_instance_btn.setObjectName("AddButton")
        self.add_instance_btn.setToolTip("Add Item Instance")
        self.add_instance_btn.setMaximumWidth(30)
        self.add_instance_btn.clicked.connect(self._add_instance_row)
        table_header_layout.addWidget(self.add_instance_btn)
        self.remove_instance_btn = QPushButton("-")
        self.remove_instance_btn.setObjectName("RemoveButton")
        self.remove_instance_btn.setToolTip("Remove Selected Item Instance")
        self.remove_instance_btn.setMaximumWidth(30)
        self.remove_instance_btn.clicked.connect(self._remove_instance_row)
        table_header_layout.addWidget(self.remove_instance_btn)
        bottom_layout.addLayout(table_header_layout)
        self.instances_table = QTableWidget()
        self.instances_table.setObjectName("SettingManagerTable")
        self.instances_table.setColumnCount(6)
        self.instances_table.setHorizontalHeaderLabels(["Item ID", "Name", "Quantity", "Owner", "Description", "Location"])
        header = self.instances_table.horizontalHeader()
        header.setObjectName("SettingManagerTableHeader")
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.instances_table.setColumnWidth(0, 80)
        self.instances_table.setColumnWidth(2, 80)
        self.instances_table.setColumnWidth(3, 100)
        self.instances_table.verticalHeader().setVisible(False)
        self.instances_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.instances_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.instances_table.setAlternatingRowColors(True)
        self.instances_table.setFocusPolicy(Qt.NoFocus)
        self.instances_table.setMinimumHeight(150)
        self.instances_table.itemChanged.connect(self._on_instance_item_changed)
        self.instances_table.itemSelectionChanged.connect(self._on_instances_selection_changed)
        bottom_layout.addWidget(self.instances_table)
        self.containers_label = QLabel("Containers:")
        self.containers_label.setObjectName("InventoryInstancesContainersLabel")
        self.containers_label.setAlignment(Qt.AlignCenter)
        self.containers_label.setFont(QFont('Consolas', 10, QFont.Bold))
        bottom_layout.addWidget(self.containers_label)
        self.containers_scroll_area = QScrollArea()
        self.containers_scroll_area.setObjectName("InventoryContainersScrollArea")
        self.containers_scroll_area.setWidgetResizable(True)
        self.containers_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.containers_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.containers_widget = QWidget()
        self.containers_widget.setObjectName("InventoryContainersWidget")
        self.containers_layout = QVBoxLayout(self.containers_widget)
        self.containers_layout.setContentsMargins(5, 5, 5, 5)
        self.containers_layout.setSpacing(5)
        self.default_container_label = QLabel("Either no item selected, or selected item does not have containers.")
        self.default_container_label.setObjectName("InventoryDefaultContainerLabel")
        self.default_container_label.setAlignment(Qt.AlignCenter)
        self.default_container_label.setFont(QFont('Consolas', 9))
        self.containers_layout.addWidget(self.default_container_label)
        self.containers_scroll_area.setWidget(self.containers_widget)
        bottom_layout.addWidget(self.containers_scroll_area, 1)
        self.instances_splitter.addWidget(self.instances_bottom_widget)
        self.instances_splitter.setStretchFactor(0, 1)
        self.instances_splitter.setStretchFactor(1, 2)
        instances_main_layout.addWidget(self.instances_splitter, 1)
        self.settings_search.textChanged.connect(self._on_settings_search)
        self.actors_search.textChanged.connect(self._on_actors_search)
        self._populate_instances_lists()
        self.content_stack.addWidget(self.references_widget)
        self.content_stack.addWidget(self.instances_widget)
        self.content_stack.setCurrentIndex(0)
        main_layout.addWidget(self.content_stack, 1)
        self.references_btn.toggled.connect(self._on_references_toggle)
        self.instances_btn.toggled.connect(self._on_instances_toggle)
        self.setLayout(main_layout)

    def update_theme(self, theme_colors):
        base_color = theme_colors.get('base_color', '#00FF66')
        bg_color = theme_colors.get('bg_color', '#2B2B2B')
        darker_bg = theme_colors.get('darker_bg', '#1E1E1E')
        highlight = theme_colors.get('highlight', 'rgba(0,255,102,0.6)')
        from core.apply_stylesheet import generate_and_apply_stylesheet
        generate_and_apply_stylesheet(self, theme_colors)
        containers_style = f"""
            QScrollArea#InventoryContainersScrollArea {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
            }}
            QWidget#InventoryContainersWidget {{
                background-color: {darker_bg};
            }}
            QLabel#InventoryDefaultContainerLabel {{
                color: {base_color};
                font: 9pt 'Consolas';
                background-color: {darker_bg};
                padding: 10px;
                border: 1px solid {base_color};
                border-radius: 3px;
            }}
            QLabel#InventoryContainerHeaderLabel {{
                color: {base_color};
                font: 9pt 'Consolas' bold;
                background-color: {darker_bg};
                padding: 5px;
                border: 1px solid {base_color};
                border-radius: 3px;
            }}
        """
        self.containers_scroll_area.setStyleSheet(containers_style)
        
        self._update_all_container_table_styles()

    def _update_all_container_table_styles(self):
        base_color = self.theme_colors.get('base_color', '#00FF66') if self.theme_colors else '#00FF66'
        selection_color = f"rgba({int(base_color[1:3], 16)}, {int(base_color[3:5], 16)}, {int(base_color[5:7], 16)}, 0.3)"
        table_style = f"""
            QTableWidget::item:selected {{
                background-color: {selection_color};
                color: {base_color};
            }}
            QTableWidget::item:selected:active {{
                background-color: {selection_color};
                color: {base_color};
            }}
            QTableWidget::item:selected:!active {{
                background-color: {selection_color};
                color: {base_color};
            }}
        """
        
        def update_table_styles_recursively(widget):
            if hasattr(widget, 'container_table'):
                widget.container_table.setStyleSheet(table_style)
            if hasattr(widget, 'layout') and widget.layout():
                for i in range(widget.layout().count()):
                    child_item = widget.layout().itemAt(i)
                    if child_item and child_item.widget():
                        update_table_styles_recursively(child_item.widget())
        for i in range(self.containers_layout.count()):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                update_table_styles_recursively(item.widget())

    def _on_instance_item_changed(self, item):
        if not item or self.is_loading_data:
            return
        row = item.row()
        col = item.column()
        if col == 1:
            name_item = self.instances_table.item(row, 1)
            if name_item and name_item.text().strip():
                item_name = name_item.text().strip()
                containers = self._get_containers_for_item(item_name)
                if containers:
                    self._ensure_container_widgets_exist_for_item(item_name, containers)
        self._update_instance_item_in_memory(row)
        self._save_current_inventory()

    def _update_instance_item_in_memory(self, row):
        if not hasattr(self, 'current_inventory_data'):
            self.current_inventory_data = []
        if row >= len(self.current_inventory_data):
            while len(self.current_inventory_data) <= row:
                self.current_inventory_data.append({
                    'item_id': '',
                    'name': '',
                    'quantity': 1,
                    'owner': '',
                    'description': '',
                    'location': '',
                    'containers': {}
                })
        item_id = self.instances_table.item(row, 0)
        name = self.instances_table.item(row, 1)
        quantity = self.instances_table.item(row, 2)
        owner = self.instances_table.item(row, 3)
        description = self.instances_table.item(row, 4)
        location = self.instances_table.item(row, 5)
        if not item_id or not item_id.text().strip():
            return
        item_id_text = item_id.text().strip()
        item_name = name.text().strip() if name else ''
        quantity_value = int(quantity.text().strip()) if quantity and quantity.text().strip().isdigit() else 1
        owner_text = owner.text().strip() if owner else ''
        description_text = description.text().strip() if description else ''
        location_text = location.text().strip() if location else ''
        updated_item = {
            'item_id': item_id_text,
            'name': item_name,
            'quantity': quantity_value,
            'owner': owner_text,
            'description': description_text,
            'location': location_text,
            'containers': {}
        }
        if item_name:
            containers = self._get_containers_for_item(item_name)
            for container_name in containers:
                container_items = self._get_container_items_recursive(1, item_name, container_name)
                if container_items:
                    updated_item['containers'][container_name] = container_items
        
        self.current_inventory_data[row] = updated_item

    def _save_current_inventory(self):
        selected_setting = self.settings_list.currentItem()
        selected_actor = self.actors_list.currentItem()
        if not selected_setting and not selected_actor:
            return
        inventory_data = self._get_inventory_from_table()
        self.current_inventory_data = inventory_data
        if selected_setting:
            self._save_inventory_to_setting(selected_setting.data(Qt.UserRole), inventory_data)
        elif selected_actor:
            self._save_inventory_to_actor(selected_actor.data(Qt.UserRole), inventory_data)

    def _get_inventory_from_table(self):
        def collect_container_data_from_widgets(level, item_name, container_name):
            container_widget = self._find_container_level_widget(level, item_name, container_name)
            if not container_widget or not hasattr(container_widget, 'container_table'):
                return []
            container_items = []
            container_table = container_widget.container_table
            for row in range(container_table.rowCount()):
                item_id_item = container_table.item(row, 0)
                name_item = container_table.item(row, 1)
                quantity_item = container_table.item(row, 2)
                owner_item = container_table.item(row, 3)
                description_item = container_table.item(row, 4)
                location_item = container_table.item(row, 5)
                if item_id_item and item_id_item.text().strip():
                    container_item = {
                        'item_id': item_id_item.text().strip(),
                        'name': name_item.text().strip() if name_item else '',
                        'quantity': int(quantity_item.text().strip()) if quantity_item and quantity_item.text().strip().isdigit() else 1,
                        'owner': owner_item.text().strip() if owner_item else '',
                        'description': description_item.text().strip() if description_item else '',
                        'location': location_item.text().strip() if location_item else '',
                        'containers': {}
                    }
                    container_item_name = name_item.text().strip() if name_item else ''
                    if container_item_name:
                        reference_containers = self._get_containers_for_item(container_item_name)
                        for ref_container_name in reference_containers:
                            nested_items = collect_container_data_from_widgets(level + 1, container_item_name, ref_container_name)
                            if not nested_items:
                                nested_items = collect_container_data_from_memory(level + 1, container_item_name, ref_container_name)
                            if nested_items:
                                container_item['containers'][ref_container_name] = nested_items
                    container_items.append(container_item)
            return container_items

        def collect_container_data_from_memory(level, item_name, container_name):
            if not hasattr(self, 'current_inventory_data') or not self.current_inventory_data:
                return []
            
            def find_container_at_level(data, current_level, target_level, target_item_name, target_container_name):
                if current_level == target_level:
                    for item in data:
                        if item.get('name') == target_item_name:
                            containers = item.get('containers', {})
                            if target_container_name in containers:
                                return containers[target_container_name]
                    return None
                else:
                    for item in data:
                        containers = item.get('containers', {})
                        for container_name, container_items in containers.items():
                            result = find_container_at_level(container_items, current_level + 1, target_level, target_item_name, target_container_name)
                            if result is not None:
                                return result
                    return None
            container_items = find_container_at_level(self.current_inventory_data, 1, level, item_name, container_name)
            if container_items is None:
                return []
            result_items = []
            for container_item in container_items:
                if isinstance(container_item, dict):
                    result_item = container_item.copy()
                    container_item_name = container_item.get('name', '')
                    if container_item_name:
                        reference_containers = self._get_containers_for_item(container_item_name)
                        for ref_container_name in reference_containers:
                            nested_items = collect_container_data_from_memory(level + 1, container_item_name, ref_container_name)
                            if nested_items:
                                result_item['containers'][ref_container_name] = nested_items
                    result_items.append(result_item)
            return result_items
        inventory = []
        for row in range(self.instances_table.rowCount()):
            item_id = self.instances_table.item(row, 0)
            name = self.instances_table.item(row, 1)
            quantity = self.instances_table.item(row, 2)
            owner = self.instances_table.item(row, 3)
            description = self.instances_table.item(row, 4)
            location = self.instances_table.item(row, 5)
            if item_id and item_id.text().strip():
                item_data = {
                    'item_id': item_id.text().strip(),
                    'name': name.text().strip() if name else '',
                    'quantity': int(quantity.text().strip()) if quantity and quantity.text().strip().isdigit() else 1,
                    'owner': owner.text().strip() if owner else '',
                    'description': description.text().strip() if description else '',
                    'location': location.text().strip() if location else '',
                    'containers': {}
                }
                item_name = name.text().strip() if name else ''
                if item_name:
                    containers = self._get_containers_for_item(item_name)
                    for container_name in containers:
                        container_items = collect_container_data_from_widgets(1, item_name, container_name)
                        if not container_items:
                            container_items = collect_container_data_from_memory(1, item_name, container_name)
                        if container_items:
                            item_data['containers'][container_name] = container_items
                
                inventory.append(item_data)
        return inventory

    def _get_container_items_recursive(self, level, item_name, container_name):
        def find_container_at_level(data, current_level, target_level, target_item_name, target_container_name):
            if current_level == target_level:
                for item in data:
                    if item.get('name') == target_item_name:
                        containers = item.get('containers', {})
                        if target_container_name in containers:
                            return containers[target_container_name]
                return None
            else:
                for item in data:
                    containers = item.get('containers', {})
                    for container_name, container_items in containers.items():
                        result = find_container_at_level(container_items, current_level + 1, target_level, target_item_name, target_container_name)
                        if result is not None:
                            return result
                return None
        container_items = find_container_at_level(self.current_inventory_data, 1, level, item_name, container_name)
        if container_items is None:
            return []
        result_items = []
        for container_item in container_items:
            if isinstance(container_item, dict):
                result_item = container_item.copy()
                container_item_name = container_item.get('name', '')
                if container_item_name:
                    reference_containers = self._get_containers_for_item(container_item_name)
                    if reference_containers:
                        for ref_container_name in reference_containers:
                            nested_items = self._get_container_items_recursive(level + 1, container_item_name, ref_container_name)
                            if nested_items:
                                result_item['containers'][ref_container_name] = nested_items
                result_items.append(result_item)
        return result_items

    def _save_inventory_to_setting(self, setting_file_path, inventory_data):
        if not setting_file_path or not os.path.exists(setting_file_path):
            return
        try:
            with open(setting_file_path, 'r', encoding='utf-8') as f:
                setting_data = json.load(f)
            setting_data['inventory'] = inventory_data
            with open(setting_file_path, 'w', encoding='utf-8') as f:
                json.dump(setting_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def _save_inventory_to_actor(self, actor_file_path, inventory_data):
        if not actor_file_path or not os.path.exists(actor_file_path):
            return
        try:
            with open(actor_file_path, 'r', encoding='utf-8') as f:
                actor_data = json.load(f)
            actor_data['inventory'] = inventory_data
            with open(actor_file_path, 'w', encoding='utf-8') as f:
                json.dump(actor_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def _load_inventory_for_setting(self, setting_file_path):
        if not setting_file_path or not os.path.exists(setting_file_path):
            self._clear_instances_table()
            return
        try:
            with open(setting_file_path, 'r', encoding='utf-8') as f:
                setting_data = json.load(f)
            self.current_inventory_data = setting_data.get('inventory', [])
            self._clear_containers()
            self._populate_instances_table(self.current_inventory_data)
        except Exception as e:
            self._clear_instances_table()

    def _load_inventory_for_actor(self, actor_file_path):
        if not actor_file_path or not os.path.exists(actor_file_path):
            self._clear_instances_table()
            return
        try:
            with open(actor_file_path, 'r', encoding='utf-8') as f:
                actor_data = json.load(f)
            self.current_inventory_data = actor_data.get('inventory', [])
            self._clear_containers()
            self._populate_instances_table(self.current_inventory_data)
        except Exception as e:
            self._clear_instances_table()

    def _populate_instances_table(self, inventory_data):
        self.is_loading_data = True
        self.instances_table.blockSignals(True)
        self.instances_table.setRowCount(0)
        if not inventory_data:
            self.instances_table.blockSignals(False)
            self.is_loading_data = False
            return
        
        for item in inventory_data:
            if isinstance(item, dict):
                row = self.instances_table.rowCount()
                self.instances_table.insertRow(row)
                self.instances_table.setItem(row, 0, QTableWidgetItem(item.get('item_id', generate_item_id())))
                self.instances_table.setItem(row, 1, QTableWidgetItem(item.get('name', '')))
                self.instances_table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', '1'))))
                self.instances_table.setItem(row, 3, QTableWidgetItem(item.get('owner', '')))
                self.instances_table.setItem(row, 4, QTableWidgetItem(item.get('description', '')))
                self.instances_table.setItem(row, 5, QTableWidgetItem(item.get('location', '')))
            elif isinstance(item, str):
                row = self.instances_table.rowCount()
                self.instances_table.insertRow(row)
                self.instances_table.setItem(row, 0, QTableWidgetItem(generate_item_id()))
                self.instances_table.setItem(row, 1, QTableWidgetItem(item))
                self.instances_table.setItem(row, 2, QTableWidgetItem('1'))
                self.instances_table.setItem(row, 3, QTableWidgetItem(''))
                self.instances_table.setItem(row, 4, QTableWidgetItem(''))
                self.instances_table.setItem(row, 5, QTableWidgetItem(''))
        
        self.instances_table.blockSignals(False)
        if self.instances_table.rowCount() > 0:
            self.instances_table.setCurrentCell(0, 0)
            self.instances_table.selectRow(0)
            if self.instances_table.rowCount() == 1:
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(10, self._handle_single_item_selection)
        else:
            self._clear_containers()
        self.is_loading_data = False

    def _clear_instances_table(self):
        self.instances_table.setRowCount(0)
        self._clear_containers()

    def _clear_containers(self):
        for i in reversed(range(self.containers_layout.count())):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self.default_container_label = QLabel("Either no item selected, or selected item does not have containers.")
        self.default_container_label.setObjectName("InventoryDefaultContainerLabel")
        self.default_container_label.setAlignment(Qt.AlignCenter)
        self.default_container_label.setFont(QFont('Consolas', 9))
        self.containers_layout.addWidget(self.default_container_label)
        self._update_containers_label("")

    def _create_container_level_widget(self, level, item_name, container_name):
        level_widget = QWidget()
        level_layout = QVBoxLayout(level_widget)
        level_layout.setContentsMargins(5, 5, 5, 5)
        level_layout.setSpacing(2)
        level_header = QLabel(f"Level {level}: {item_name} → {container_name}")
        level_header.setObjectName("InventoryContainerHeaderLabel")
        level_header.setAlignment(Qt.AlignCenter)
        level_header.setFont(QFont('Consolas', 9, QFont.Bold))
        level_layout.addWidget(level_header)
        table_header_layout = QHBoxLayout()
        table_header_layout.addWidget(QLabel(f"Items in {item_name}, {container_name}:"))
        table_header_layout.addStretch()
        level_layout.addLayout(table_header_layout)
        container_table = QTableWidget()
        container_table.setObjectName("SettingManagerTable")
        container_table.setColumnCount(6)
        container_table.setHorizontalHeaderLabels(["Item ID", "Name", "Quantity", "Owner", "Description", "Location"])
        header = container_table.horizontalHeader()
        header.setObjectName("SettingManagerTableHeader")
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        container_table.setColumnWidth(0, 80)
        container_table.setColumnWidth(2, 80)
        container_table.setColumnWidth(3, 100)
        container_table.verticalHeader().setVisible(False)
        container_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        container_table.setSelectionMode(QAbstractItemView.SingleSelection)
        container_table.setAlternatingRowColors(True)
        container_table.setFocusPolicy(Qt.StrongFocus)
        container_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        container_table.setMinimumHeight(120)
        container_table.setMinimumWidth(300)
        
        base_color = self.theme_colors.get('base_color', '#00FF66') if self.theme_colors else '#00FF66'
        selection_color = f"rgba({int(base_color[1:3], 16)}, {int(base_color[3:5], 16)}, {int(base_color[5:7], 16)}, 0.3)"
        container_table.setStyleSheet(f"""
            QTableWidget::item:selected {{
                background-color: {selection_color};
                color: {base_color};
            }}
            QTableWidget::item:selected:active {{
                background-color: {selection_color};
                color: {base_color};
            }}
            QTableWidget::item:selected:!active {{
                background-color: {selection_color};
                color: {base_color};
            }}
        """)
        container_table.itemChanged.connect(self._on_container_item_changed)
        container_table.itemSelectionChanged.connect(self._on_container_table_selection_changed)
        container_table.level = level
        container_table.item_name = item_name
        container_table.container_name = container_name
        add_container_item_btn = QPushButton("+")
        add_container_item_btn.setObjectName("AddButton")
        add_container_item_btn.setToolTip("Add Item to Container")
        add_container_item_btn.setMaximumWidth(30)
        add_container_item_btn.clicked.connect(self._add_container_item_row)
        add_container_item_btn.container_table = container_table
        add_container_item_btn.level = level
        add_container_item_btn.item_name = item_name
        add_container_item_btn.container_name = container_name
        table_header_layout.addWidget(add_container_item_btn)
        remove_container_item_btn = QPushButton("-")
        remove_container_item_btn.setObjectName("RemoveButton")
        remove_container_item_btn.setToolTip("Remove Selected Item from Container")
        remove_container_item_btn.setMaximumWidth(30)
        remove_container_item_btn.clicked.connect(self._remove_container_item_row)
        remove_container_item_btn.container_table = container_table
        table_header_layout.addWidget(remove_container_item_btn)
        level_layout.addWidget(container_table)
        level_widget.level = level
        level_widget.item_name = item_name
        level_widget.container_name = container_name
        level_widget.container_table = container_table
        level_widget.setMinimumWidth(320)
        return level_widget

    def _create_container_table(self, container_name):
        return self._create_container_level_widget(1, "Main Item", container_name)

    def _on_container_item_changed(self, item):
        if not item or self.is_loading_data:
            return
        table = item.tableWidget()
        if not table or not hasattr(table, 'level'):
            return
        row = item.row()
        col = item.column()
        
        if col == 1:
            name_item = table.item(row, 1)
            if name_item and name_item.text().strip():
                item_name = name_item.text().strip()
                level = table.level
                parent_item_name = table.item_name
                parent_container_name = table.container_name
                containers = self._get_containers_for_item(item_name)
                if containers:
                    self._ensure_nested_container_widgets_exist(level + 1, item_name, containers, parent_item_name, parent_container_name)
        
        self._update_container_item_in_memory(table, row)
        self._save_current_inventory()

    def _update_container_item_in_memory(self, table, row):
        if not hasattr(table, 'level') or not hasattr(table, 'item_name') or not hasattr(table, 'container_name'):
            return
        
        level = table.level
        parent_item_name = table.item_name
        parent_container_name = table.container_name
        
        item_id_item = table.item(row, 0)
        name_item = table.item(row, 1)
        quantity_item = table.item(row, 2)
        owner_item = table.item(row, 3)
        description_item = table.item(row, 4)
        location_item = table.item(row, 5)
        
        if not item_id_item or not item_id_item.text().strip():
            return
        
        item_id = item_id_item.text().strip()
        item_name = name_item.text().strip() if name_item else ''
        quantity = int(quantity_item.text().strip()) if quantity_item and quantity_item.text().strip().isdigit() else 1
        owner = owner_item.text().strip() if owner_item else ''
        description = description_item.text().strip() if description_item else ''
        location = location_item.text().strip() if location_item else ''
        
        updated_item = {
            'item_id': item_id,
            'name': item_name,
            'quantity': quantity,
            'owner': owner,
            'description': description,
            'location': location,
            'containers': {}
        }
        
        if item_name:
            reference_containers = self._get_containers_for_item(item_name)
            for ref_container_name in reference_containers:
                nested_items = self._get_container_items_recursive(level + 1, item_name, ref_container_name)
                if nested_items:
                    updated_item['containers'][ref_container_name] = nested_items
        
        def update_container_at_level(data, current_level, target_level, target_parent_name, target_container_name, target_item_id, new_item_data):
            if current_level == target_level:
                for item in data:
                    if item.get('name') == target_parent_name:
                        containers = item.get('containers', {})
                        if target_container_name in containers:
                            for i, container_item in enumerate(containers[target_container_name]):
                                if container_item.get('item_id') == target_item_id:
                                    containers[target_container_name][i] = new_item_data
                                    return True
                return False
            else:
                for item in data:
                    containers = item.get('containers', {})
                    for container_name, container_items in containers.items():
                        if update_container_at_level(container_items, current_level + 1, target_level, target_parent_name, target_container_name, target_item_id, new_item_data):
                            return True
                return False
        
        if hasattr(self, 'current_inventory_data') and self.current_inventory_data:
            update_container_at_level(self.current_inventory_data, 1, level, parent_item_name, parent_container_name, item_id, updated_item)

    def _ensure_nested_container_widgets_exist(self, level, item_name, containers, parent_item_name, parent_container_name):
        existing_widgets = []
        for i in range(self.containers_layout.count()):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'layout') and widget.layout():
                    for j in range(widget.layout().count()):
                        child_item = widget.layout().itemAt(j)
                        if child_item and child_item.widget():
                            child_widget = child_item.widget()
                            if (hasattr(child_widget, 'item_name') and 
                                child_widget.item_name == item_name and
                                hasattr(child_widget, 'level') and 
                                child_widget.level == level):
                                existing_widgets.append(child_widget)
                elif (hasattr(widget, 'item_name') and 
                      widget.item_name == item_name and
                      hasattr(widget, 'level') and 
                      widget.level == level):
                    existing_widgets.append(widget)
        if not existing_widgets:
            all_containers = self._get_containers_for_item(item_name)
            if all_containers:
                level_row_widget = QWidget()
                level_row_layout = QHBoxLayout(level_row_widget)
                level_row_layout.setContentsMargins(5, 5, 5, 5)
                level_row_layout.setSpacing(10)
                for container in all_containers:
                    level_widget = self._create_container_level_widget(level, item_name, container)
                    level_row_layout.addWidget(level_widget)
                self.containers_layout.addWidget(level_row_widget)

    def _on_container_table_selection_changed(self):
        table = self.sender()
        if not table or not hasattr(table, 'level'):
            return
        current_row = table.currentRow()
        if current_row < 0:
            self._remove_container_widgets_deeper_than(table.level)
            return
        self._clear_other_container_selections_in_row(table)
        level = table.level
        parent_item_name = table.item_name
        parent_container_name = table.container_name
        name_item = table.item(current_row, 1)
        if not name_item:
            self._remove_container_widgets_deeper_than(level)
            return
        item_name = name_item.text().strip()
        if not item_name:
            self._remove_container_widgets_deeper_than(level)
            return
        reference_containers = self._get_containers_for_item(item_name)
        if not reference_containers:
            self._remove_container_widgets_deeper_than(level)
            return
        item_data = self._find_item_data_in_container(level, parent_item_name, parent_container_name, item_name)
        containers_data = item_data.get('containers', {}) if item_data else {}
        if not containers_data:
            containers_data = {container: [] for container in reference_containers}
        self._remove_container_widgets_deeper_than(level)
        self._expand_container_item(level + 1, item_name, containers_data)

    def _clear_other_container_selections_in_row(self, selected_table):
        if not selected_table or not hasattr(selected_table, 'level'):
            return
        level = selected_table.level
        item_name = selected_table.item_name
        for i in range(self.containers_layout.count()):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'layout') and widget.layout():
                    for j in range(widget.layout().count()):
                        child_item = widget.layout().itemAt(j)
                        if child_item and child_item.widget():
                            child_widget = child_item.widget()
                            if (hasattr(child_widget, 'container_table') and 
                                hasattr(child_widget, 'level') and 
                                hasattr(child_widget, 'item_name') and
                                child_widget.level == level and 
                                child_widget.item_name == item_name and
                                child_widget.container_table != selected_table):
                                child_widget.container_table.clearSelection()
                elif (hasattr(widget, 'container_table') and 
                      hasattr(widget, 'level') and 
                      hasattr(widget, 'item_name') and
                      widget.level == level and 
                      widget.item_name == item_name and
                      widget.container_table != selected_table):
                    widget.container_table.clearSelection()

    def _on_container_item_double_clicked(self, level, parent_item_name, parent_container_name, item, col):
        if col == 1:
            item_name = item.text().strip()
            if item_name:
                item_data = self._find_item_data_in_container(level, parent_item_name, parent_container_name, item_name)
                containers_data = item_data.get('containers', {}) if item_data else {}
                reference_containers = self._get_containers_for_item(item_name)
                if reference_containers:
                    if not containers_data:
                        containers_data = {container: [] for container in reference_containers}
                    self._expand_container_item(level + 1, item_name, containers_data)

    def _find_item_data_in_container(self, level, parent_item_name, parent_container_name, item_name):
        def find_container_at_level(data, current_level, target_level, target_parent_name, target_container_name):
            if current_level == target_level:
                for item in data:
                    if item.get('name') == target_parent_name:
                        containers = item.get('containers', {})
                        if target_container_name in containers:
                            return containers[target_container_name]
                return None
            else:
                for item in data:
                    containers = item.get('containers', {})
                    for container_name, container_items in containers.items():
                        result = find_container_at_level(container_items, current_level + 1, target_level, target_parent_name, target_container_name)
                        if result is not None:
                            return result
                return None
        target_container = find_container_at_level(self.current_inventory_data, 1, level, parent_item_name, parent_container_name)
        if target_container is not None:
            for item in target_container:
                if item.get('name') == item_name:
                    return item
        return None

    def _expand_container_item(self, level, item_name, containers_data):
        level_row_widget = QWidget()
        level_row_layout = QHBoxLayout(level_row_widget)
        level_row_layout.setContentsMargins(5, 5, 5, 5)
        level_row_layout.setSpacing(10)
        all_containers = self._get_containers_for_item(item_name)
        sorted_containers = sorted(all_containers)
        for container_name in sorted_containers:
            level_widget = self._create_container_level_widget(level, item_name, container_name)
            level_row_layout.addWidget(level_widget)
            container_items = containers_data.get(container_name, [])
            container_table = level_widget.container_table
            container_table.blockSignals(True)
            container_table.setRowCount(0)
            for container_item in container_items:
                if isinstance(container_item, dict):
                    row = container_table.rowCount()
                    container_table.insertRow(row)
                    item_id_item = QTableWidgetItem(container_item.get('item_id', generate_item_id()))
                    item_id_item.setFlags(item_id_item.flags() | Qt.ItemIsEditable)
                    container_table.setItem(row, 0, item_id_item)
                    name_item = QTableWidgetItem(container_item.get('name', ''))
                    name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
                    container_table.setItem(row, 1, name_item)
                    quantity_item = QTableWidgetItem(str(container_item.get('quantity', '1')))
                    quantity_item.setFlags(quantity_item.flags() | Qt.ItemIsEditable)
                    container_table.setItem(row, 2, quantity_item)
                    owner_item = QTableWidgetItem(container_item.get('owner', ''))
                    owner_item.setFlags(owner_item.flags() | Qt.ItemIsEditable)
                    container_table.setItem(row, 3, owner_item)
                    description_item = QTableWidgetItem(container_item.get('description', ''))
                    description_item.setFlags(description_item.flags() | Qt.ItemIsEditable)
                    container_table.setItem(row, 4, description_item)
                    location_item = QTableWidgetItem(container_item.get('location', ''))
                    location_item.setFlags(location_item.flags() | Qt.ItemIsEditable)
                    container_table.setItem(row, 5, location_item)
            container_table.blockSignals(False)
            if container_table.rowCount() == 1:
                container_table.setCurrentCell(0, 0)
                container_table.selectRow(0)
        insert_position = level - 1
        if insert_position < 0:
            insert_position = 0
        if insert_position >= self.containers_layout.count():
            self.containers_layout.addWidget(level_row_widget)
        else:
            self.containers_layout.insertWidget(insert_position, level_row_widget)
    def _add_container_item_row(self):
        button = self.sender()
        if not button or not hasattr(button, 'container_table'):
            return
        container_table = button.container_table
        row = container_table.rowCount()
        new_item_id = generate_item_id()
        new_item = {
            'item_id': new_item_id,
            'name': '',
            'quantity': 1,
            'owner': '',
            'description': '',
            'location': '',
            'containers': {}
        }
        level = getattr(container_table, 'level', 1)
        parent_item_name = getattr(container_table, 'item_name', '')
        parent_container_name = getattr(container_table, 'container_name', '')
        success = self._add_item_to_container_data(level, parent_item_name, parent_container_name, new_item)
        if success:
            container_table.insertRow(row)
            item_id_item = QTableWidgetItem(new_item_id)
            item_id_item.setFlags(item_id_item.flags() | Qt.ItemIsEditable)
            container_table.setItem(row, 0, item_id_item)
            name_item = QTableWidgetItem("")
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            container_table.setItem(row, 1, name_item)
            quantity_item = QTableWidgetItem("1")
            quantity_item.setFlags(quantity_item.flags() | Qt.ItemIsEditable)
            container_table.setItem(row, 2, quantity_item)
            owner_item = QTableWidgetItem("")
            owner_item.setFlags(owner_item.flags() | Qt.ItemIsEditable)
            container_table.setItem(row, 3, owner_item)
            description_item = QTableWidgetItem("")
            description_item.setFlags(description_item.flags() | Qt.ItemIsEditable)
            container_table.setItem(row, 4, description_item)
            location_item = QTableWidgetItem("")
            location_item.setFlags(location_item.flags() | Qt.ItemIsEditable)
            container_table.setItem(row, 5, location_item)
            self._save_current_inventory()
            if container_table.rowCount() == 1:
                container_table.setCurrentCell(0, 0)
                container_table.selectRow(0)
            main_ui = self._get_main_ui()
            if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
                try:
                    main_ui.add_rule_sound.play()
                except Exception:
                    main_ui.add_rule_sound = None
        else:
            QMessageBox.warning(self, "Add Failed", f"Failed to add item to data structure.")

    def _remove_container_item_row(self):
        button = self.sender()
        if not button or not hasattr(button, 'container_table'):
            return
        container_table = button.container_table
        current_row = container_table.currentRow()
        if current_row >= 0:
            item_id_item = container_table.item(current_row, 0)
            item_name_item = container_table.item(current_row, 1)
            if item_id_item and item_name_item:
                item_id = item_id_item.text().strip()
                item_name = item_name_item.text().strip()
                level = getattr(container_table, 'level', 1)
                parent_item_name = getattr(container_table, 'item_name', '')
                parent_container_name = getattr(container_table, 'container_name', '')
                self._cleanup_container_widgets_for_item(item_name, level, parent_item_name, parent_container_name)
                success = self._remove_item_from_container_data(level, parent_item_name, parent_container_name, item_id, item_name)
                if success:
                    container_table.removeRow(current_row)
                    self._save_current_inventory()
                    if container_table.rowCount() == 1:
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(10, self._on_container_table_selection_changed)
                    main_ui = self._get_main_ui()
                    if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                        try:
                            main_ui.delete_rule_sound.play()
                        except Exception:
                            main_ui.delete_rule_sound = None
                else:
                    QMessageBox.warning(self, "Remove Failed", f"Failed to remove item '{item_name}' from data structure.")

    def _cleanup_container_widgets_for_item(self, item_name, level=None, parent_item_name=None, parent_container_name=None):
        def remove_widget_recursively(widget):
            if hasattr(widget, 'layout') and widget.layout():
                for i in range(widget.layout().count()):
                    child_item = widget.layout().itemAt(i)
                    if child_item and child_item.widget():
                        remove_widget_recursively(child_item.widget())
            widget.deleteLater()
        
        def find_and_remove_widgets_recursively(parent_widget, target_item_name, target_level):
            widgets_to_remove = []
            if hasattr(parent_widget, 'layout') and parent_widget.layout():
                for i in range(parent_widget.layout().count()):
                    child_item = parent_widget.layout().itemAt(i)
                    if child_item and child_item.widget():
                        child_widget = child_item.widget()
                        if (hasattr(child_widget, 'item_name') and 
                            child_widget.item_name == target_item_name and
                            hasattr(child_widget, 'level') and 
                            child_widget.level == target_level):
                            widgets_to_remove.append((i, child_widget))
                        else:
                            widgets_to_remove.extend(find_and_remove_widgets_recursively(child_widget, target_item_name, target_level))
            return widgets_to_remove
        if level is None:
            return
        target_level = level + 1
        widgets_to_remove = []
        for i in range(self.containers_layout.count()):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                found_widgets = find_and_remove_widgets_recursively(widget, item_name, target_level)
                for layout_index, found_widget in found_widgets:
                    widgets_to_remove.append((i, layout_index, found_widget))
        for row_index, layout_index, widget in sorted(widgets_to_remove, key=lambda x: (x[0], x[1]), reverse=True):
            row_widget = self.containers_layout.itemAt(row_index).widget()
            if row_widget and hasattr(row_widget, 'layout') and row_widget.layout():
                row_widget.layout().takeAt(layout_index)
                remove_widget_recursively(widget)
                if row_widget.layout().count() == 0:
                    self.containers_layout.takeAt(row_index)
                    row_widget.deleteLater()
        if level is not None:
            self.container_selection_path = [entry for entry in self.container_selection_path if entry[0] < level]

    def _ensure_container_widgets_exist_for_item(self, item_name, containers):
        existing_widgets = []
        for i in range(self.containers_layout.count()):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'layout') and widget.layout():
                    for j in range(widget.layout().count()):
                        child_item = widget.layout().itemAt(j)
                        if child_item and child_item.widget():
                            child_widget = child_item.widget()
                            if (hasattr(child_widget, 'item_name') and 
                                child_widget.item_name == item_name and
                                hasattr(child_widget, 'level') and 
                                child_widget.level == 1):
                                existing_widgets.append(child_widget)
                elif (hasattr(widget, 'item_name') and 
                      widget.item_name == item_name and
                      hasattr(widget, 'level') and 
                      widget.level == 1):
                    existing_widgets.append(widget)
        if not existing_widgets:
            level1_row_widget = QWidget()
            level1_row_layout = QHBoxLayout(level1_row_widget)
            level1_row_layout.setContentsMargins(5, 5, 5, 5)
            level1_row_layout.setSpacing(10)
            for container in containers:
                container_widget = self._create_container_level_widget(1, item_name, container)
                level1_row_layout.addWidget(container_widget)
            self.containers_layout.addWidget(level1_row_widget)

    def _update_containers_for_item(self, item_name):
        if self.is_loading_data:
            return
        for i in reversed(range(self.containers_layout.count())):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self.container_selection_path = []
        containers = self._get_containers_for_item(item_name)
        if not containers:
            self.default_container_label = QLabel("Either no item selected, or selected item does not have containers.")
            self.default_container_label.setObjectName("InventoryDefaultContainerLabel")
            self.default_container_label.setAlignment(Qt.AlignCenter)
            self.default_container_label.setFont(QFont('Consolas', 9))
            self.containers_layout.addWidget(self.default_container_label)
            return
        level1_row_widget = QWidget()
        level1_row_layout = QHBoxLayout(level1_row_widget)
        level1_row_layout.setContentsMargins(5, 5, 5, 5)
        level1_row_layout.setSpacing(10)
        for container in containers:
            container_widget = self._create_container_level_widget(1, item_name, container)
            level1_row_layout.addWidget(container_widget)
        self.containers_layout.addWidget(level1_row_widget)
        self._update_containers_label(item_name)

    def _get_containers_for_item(self, item_name):
        containers = []
        for i in range(self.tab_widget.count()):
            page = self.tab_widget.widget(i)
            if hasattr(page, 'item_table_widget'):
                for row in range(page.item_table_widget.rowCount()):
                    name_item = page.item_table_widget.item(row, 0)
                    if name_item and name_item.text() == item_name:
                        containers_widget = page.item_table_widget.cellWidget(row, 2)
                        if containers_widget and hasattr(containers_widget, 'containers'):
                            containers = containers_widget.containers.copy()
                            break
                if containers:
                    break
        if not containers:
            for item_data in self.current_inventory_data:
                if item_data.get('name') == item_name:
                    item_containers = item_data.get('containers', {})
                    if item_containers:
                        containers = list(item_containers.keys())
                        break
        return sorted(containers)

    def _find_container_level_widget(self, level, item_name, container_name):
        for i in range(self.containers_layout.count()):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'level') and hasattr(widget, 'item_name') and hasattr(widget, 'container_name'):
                    if widget.level == level and widget.item_name == item_name and widget.container_name == container_name:
                        return widget
                elif hasattr(widget, 'layout') and widget.layout():
                    for j in range(widget.layout().count()):
                        child_item = widget.layout().itemAt(j)
                        if child_item and child_item.widget():
                            child_widget = child_item.widget()
                            if hasattr(child_widget, 'level') and hasattr(child_widget, 'item_name') and hasattr(child_widget, 'container_name'):
                                if child_widget.level == level and child_widget.item_name == item_name and child_widget.container_name == container_name:
                                    return child_widget
        return None

    def _find_container_widget(self, container_name):
        for i in range(self.containers_layout.count()):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if hasattr(widget, 'container_name') and widget.container_name == container_name:
                    return widget
                elif hasattr(widget, 'layout') and widget.layout():
                    for j in range(widget.layout().count()):
                        child_item = widget.layout().itemAt(j)
                        if child_item and child_item.widget():
                            child_widget = child_item.widget()
                            if hasattr(child_widget, 'container_name') and child_widget.container_name == container_name:
                                return child_widget
        return None

    def _delayed_load_containers(self, item_name, containers_data):
        self._load_containers_for_item(item_name, containers_data)

    def _load_containers_for_item(self, item_name, containers_data):
        def collect_all_container_data_recursive(level, parent_item_name, parent_container_name, container_items, all_containers):
            for container_item in container_items:
                if not isinstance(container_item, dict):
                    continue
                container_item_name = container_item.get('name', '')
                if not container_item_name:
                    continue
                container_item_containers = container_item.get('containers', {})
                if container_item_containers:
                    for container_name, nested_items in container_item_containers.items():
                        all_containers.append((level + 1, container_item_name, container_name, nested_items))
                        collect_all_container_data_recursive(level + 1, container_item_name, container_name, nested_items, all_containers)
        
        def load_containers_in_level_order():
            all_containers = []
            containers = self._get_containers_for_item(item_name)
            for container_name in containers:
                container_items = containers_data.get(container_name, [])
                collect_all_container_data_recursive(1, item_name, container_name, container_items, all_containers)
            max_level = max([level for level, _, _, _ in all_containers]) if all_containers else 0
            for level in range(2, max_level + 1):
                level_containers = [(l, item, container, items) for l, item, container, items in all_containers if l == level]
                for level_container in level_containers:
                    level_num, item_name_level, container_name_level, container_items_level = level_container
                    existing_widget = self._find_container_level_widget(level_num, item_name_level, container_name_level)
                    if not existing_widget:
                        containers_data_for_level = {container_name_level: container_items_level}
                        self._expand_container_item(level_num, item_name_level, containers_data_for_level)
            for level, item_name_level, container_name_level, container_items_level in all_containers:
                container_widget = self._find_container_level_widget(level, item_name_level, container_name_level)
                if container_widget:
                    container_table = container_widget.container_table
                    container_table.blockSignals(True)
                    container_table.setRowCount(0)
                    for container_item in container_items_level:
                        if isinstance(container_item, dict):
                            row = container_table.rowCount()
                            container_table.insertRow(row)
                            item_id_item = QTableWidgetItem(container_item.get('item_id', generate_item_id()))
                            item_id_item.setFlags(item_id_item.flags() | Qt.ItemIsEditable)
                            container_table.setItem(row, 0, item_id_item)
                            name_item = QTableWidgetItem(container_item.get('name', ''))
                            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
                            container_table.setItem(row, 1, name_item)
                            quantity_item = QTableWidgetItem(str(container_item.get('quantity', '1')))
                            quantity_item.setFlags(quantity_item.flags() | Qt.ItemIsEditable)
                            container_table.setItem(row, 2, quantity_item)
                            owner_item = QTableWidgetItem(container_item.get('owner', ''))
                            owner_item.setFlags(owner_item.flags() | Qt.ItemIsEditable)
                            container_table.setItem(row, 3, owner_item)
                            description_item = QTableWidgetItem(container_item.get('description', ''))
                            description_item.setFlags(description_item.flags() | Qt.ItemIsEditable)
                            container_table.setItem(row, 4, description_item)
                            location_item = QTableWidgetItem(container_item.get('location', ''))
                            location_item.setFlags(location_item.flags() | Qt.ItemIsEditable)
                            container_table.setItem(row, 5, location_item)
                    container_table.blockSignals(False)
                    container_widget.show()
                    container_table.show()
        containers = self._get_containers_for_item(item_name)
        for container_name in containers:
            container_widget = self._find_container_level_widget(1, item_name, container_name)
            if container_widget:
                container_items = containers_data.get(container_name, [])
                container_table = container_widget.container_table
                container_table.blockSignals(True)
                container_table.setRowCount(0)
                for container_item in container_items:
                    if isinstance(container_item, dict):
                        row = container_table.rowCount()
                        container_table.insertRow(row)
                        item_id = container_item.get('item_id', generate_item_id())
                        item_name = container_item.get('name', '')
                        item_quantity = str(container_item.get('quantity', '1'))
                        item_owner = container_item.get('owner', '')
                        item_description = container_item.get('description', '')
                        item_location = container_item.get('location', '')
                        item_id_item = QTableWidgetItem(item_id)
                        item_id_item.setFlags(item_id_item.flags() | Qt.ItemIsEditable)
                        container_table.setItem(row, 0, item_id_item)
                        name_item = QTableWidgetItem(item_name)
                        name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
                        container_table.setItem(row, 1, name_item)
                        quantity_item = QTableWidgetItem(item_quantity)
                        quantity_item.setFlags(quantity_item.flags() | Qt.ItemIsEditable)
                        container_table.setItem(row, 2, quantity_item)
                        owner_item = QTableWidgetItem(item_owner)
                        owner_item.setFlags(owner_item.flags() | Qt.ItemIsEditable)
                        container_table.setItem(row, 3, owner_item)
                        description_item = QTableWidgetItem(item_description)
                        description_item.setFlags(description_item.flags() | Qt.ItemIsEditable)
                        container_table.setItem(row, 4, description_item)
                        location_item = QTableWidgetItem(item_location)
                        location_item.setFlags(location_item.flags() | Qt.ItemIsEditable)
                        container_table.setItem(row, 5, location_item)
                container_table.blockSignals(False)
                container_widget.show()
                container_table.show()
        load_containers_in_level_order()



    def _update_containers_label(self, item_name):
        if item_name:
            self.containers_label.setText(f"{item_name} Containers:")
        else:
            self.containers_label.setText("Containers:")

    def _on_settings_search(self, text):
        self._populate_settings_list(search=text)

    def _on_actors_search(self, text):
        self._populate_actors_list(search=text)

    def _on_instances_selection_changed(self):
        sender = self.sender()
        if sender == self.settings_list:
            selected_item = self.settings_list.currentItem()
            if selected_item:
                self.actors_list.blockSignals(True)
                self.actors_list.clearSelection()
                self.actors_list.blockSignals(False)
                self.inventory_title_label.setText(f"Items in {selected_item.text()}:")
                self._load_inventory_for_setting(selected_item.data(Qt.UserRole))
        elif sender == self.actors_list:
            selected_item = self.actors_list.currentItem()
            if selected_item:
                self.settings_list.blockSignals(True)
                self.settings_list.clearSelection()
                self.settings_list.blockSignals(False)
                self.inventory_title_label.setText(f"{selected_item.text()}'s Items:")
                self._load_inventory_for_actor(selected_item.data(Qt.UserRole))
        elif sender == self.instances_table:
            current_row = self.instances_table.currentRow()
            if current_row < 0:
                self._clear_containers()
                return
            name_item = self.instances_table.item(current_row, 1)
            if not name_item or not name_item.text().strip():
                self._clear_containers()
                return
            item_name = name_item.text().strip()
            
            self._save_current_inventory()
            
            containers_data = {}
            for item_data in self.current_inventory_data:
                if item_data.get('name') == item_name:
                    containers_data = item_data.get('containers', {})
                    break
            
            self._update_containers_for_item(item_name)
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(5, lambda: self._delayed_load_containers(item_name, containers_data))
            self._update_containers_label(item_name)

    def _populate_settings_list(self, search=""):
        self.settings_list.clear()
        items = []
        search_dirs = [
            os.path.join(self.workflow_data_dir, "resources", "data files", "settings")
        ]
        for base_dir in search_dirs:
            if os.path.isdir(base_dir):
                for root, dirs, files in os.walk(base_dir):
                    dirs[:] = [d for d in dirs if d.lower() != 'saves']
                    for filename in files:
                        if filename.lower().endswith('_setting.json'):
                            try:
                                file_path = os.path.join(root, filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    setting_data = json.load(f)
                                    setting_name = setting_data.get('name', filename.replace('_setting.json', '').replace('_', ' ').title())
                                    if setting_name.lower() == "default setting":
                                        continue
                                    if search.lower() in setting_name.lower():
                                        items.append((setting_name, file_path))
                            except Exception:
                                continue
        for display_name, file_path in sorted(items, key=lambda x: x[0].lower()):
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, file_path)
            self.settings_list.addItem(item)
        if self.settings_list.count() > 0:
            self.settings_list.setCurrentRow(0)

    def _populate_actors_list(self, search=""):
        self.actors_list.clear()
        items = []
        base_dir = os.path.join(self.workflow_data_dir, "resources", "data files", "actors")
        if os.path.isdir(base_dir):
            for fname in os.listdir(base_dir):
                if fname.lower().endswith(".json"):
                    actor_name = fname.replace('.json', '').replace('_', ' ').title()
                    if search.lower() in actor_name.lower():
                        items.append((actor_name, os.path.join(base_dir, fname)))
        for display_name, file_path in sorted(items, key=lambda x: x[0].lower()):
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, file_path)
            self.actors_list.addItem(item)
        if self.actors_list.count() > 0:
            self.actors_list.setCurrentRow(0)

    def _populate_instances_lists(self):
        self._populate_settings_list()
        self._populate_actors_list()
        if self.settings_list.count() > 0:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self._load_initial_selection)

    def _load_initial_selection(self):
        if self.settings_list.count() > 0:
            selected_item = self.settings_list.currentItem()
            if selected_item:
                self.inventory_title_label.setText(f"Items in {selected_item.text()}:")
                self._load_inventory_for_setting(selected_item.data(Qt.UserRole))

    def _handle_single_item_selection(self):
        current_row = self.instances_table.currentRow()
        if current_row < 0:
            self._clear_containers()
            return
        name_item = self.instances_table.item(current_row, 1)
        if not name_item or not name_item.text().strip():
            self._clear_containers()
            return
        item_name = name_item.text().strip()
        
        self._save_current_inventory()
        
        containers_data = {}
        for item_data in self.current_inventory_data:
            if item_data.get('name') == item_name:
                containers_data = item_data.get('containers', {})
                break
        
        self._update_containers_for_item(item_name)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(5, lambda: self._delayed_load_containers(item_name, containers_data))
        self._update_containers_label(item_name)

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
            categories = {"All", "Weapons", "Armor", "Sumables"}
        self._load_tab_order()
        for category in sorted(categories):
            self._create_category_tab(category)
        self._apply_tab_order()

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
        self._save_tab_order()
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
        self._save_tab_order()

    def _on_tab_moved(self, from_index, to_index):
        self._save_tab_order()

    def _save_tab_order(self):
        tab_order = []
        for i in range(self.tab_widget.count()):
            tab_order.append(self.tab_widget.tabText(i))
        
        config_dir = os.path.join(self.workflow_data_dir, 'config')
        os.makedirs(config_dir, exist_ok=True)
        order_file = os.path.join(config_dir, 'inventory_tab_order.json')
        
        try:
            with open(order_file, 'w', encoding='utf-8') as f:
                json.dump(tab_order, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving tab order: {e}")

    def _load_tab_order(self):
        config_dir = os.path.join(self.workflow_data_dir, 'config')
        order_file = os.path.join(config_dir, 'inventory_tab_order.json')
        
        if not os.path.exists(order_file):
            return
        
        try:
            with open(order_file, 'r', encoding='utf-8') as f:
                saved_order = json.load(f)
            
            if not isinstance(saved_order, list):
                return
            
            self.saved_tab_order = saved_order
        except Exception as e:
            print(f"Error loading tab order: {e}")

    def _apply_tab_order(self):
        if not hasattr(self, 'saved_tab_order') or not self.saved_tab_order:
            return
        
        current_tabs = []
        for i in range(self.tab_widget.count()):
            current_tabs.append(self.tab_widget.tabText(i))
        
        ordered_tabs = []
        for saved_tab in self.saved_tab_order:
            if saved_tab in current_tabs:
                ordered_tabs.append(saved_tab)
        
        for tab_name in current_tabs:
            if tab_name not in ordered_tabs:
                ordered_tabs.append(tab_name)
        
        for i, tab_name in enumerate(ordered_tabs):
            current_index = None
            for j in range(self.tab_widget.count()):
                if self.tab_widget.tabText(j) == tab_name:
                    current_index = j
                    break
            
            if current_index is not None and current_index != i:
                self.tab_widget.tabBar().moveTab(current_index, i)

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

    def _on_references_toggle(self, checked):
        if checked:
            self.content_stack.setCurrentIndex(0)
            self._play_tab_switch_sound(0)

    def _on_instances_toggle(self, checked):
        if checked:
            self.content_stack.setCurrentIndex(1)
            self._play_tab_switch_sound(1)
    
    def select_setting_in_instances(self, setting_name):
        self.instances_btn.setChecked(True)
        for i in range(self.settings_list.count()):
            item = self.settings_list.item(i)
            if item and item.text() == setting_name:
                self.settings_list.setCurrentItem(item)
                return True
        return False
    def select_actor_in_instances(self, actor_name):
        self.instances_btn.setChecked(True)
        for i in range(self.actors_list.count()):
            item = self.actors_list.item(i)
            if item and item.text() == actor_name:
                self.actors_list.setCurrentItem(item)
                return True
        return False

    def _add_instance_row(self):
        row = self.instances_table.rowCount()
        self.instances_table.insertRow(row)
        self.instances_table.setItem(row, 0, QTableWidgetItem(generate_item_id()))
        self.instances_table.setItem(row, 1, QTableWidgetItem(""))
        self.instances_table.setItem(row, 2, QTableWidgetItem("1"))
        self.instances_table.setItem(row, 3, QTableWidgetItem(""))
        self.instances_table.setItem(row, 4, QTableWidgetItem(""))
        self.instances_table.setItem(row, 5, QTableWidgetItem(""))
        
        if not hasattr(self, 'current_inventory_data'):
            self.current_inventory_data = []
        
        new_item = {
            'item_id': self.instances_table.item(row, 0).text().strip(),
            'name': '',
            'quantity': 1,
            'owner': '',
            'description': '',
            'location': '',
            'containers': {}
        }
        self.current_inventory_data.append(new_item)
        
        self._save_current_inventory()
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None

    def _remove_instance_row(self):
        current_row = self.instances_table.currentRow()
        if current_row >= 0:
            if hasattr(self, 'current_inventory_data') and current_row < len(self.current_inventory_data):
                self.current_inventory_data.pop(current_row)
            self.instances_table.removeRow(current_row)
            self._save_current_inventory()
            if self.instances_table.rowCount() == 1:
                self.instances_table.setCurrentCell(0, 0)
                self.instances_table.selectRow(0)
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(10, self._on_instances_selection_changed)
            main_ui = self._get_main_ui()
            if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                try:
                    main_ui.delete_rule_sound.play()
                except Exception:
                    main_ui.delete_rule_sound = None

    def _remove_item_from_container_data(self, level, parent_item_name, parent_container_name, item_id, item_name):
        def find_container_at_level(data, current_level, target_level, target_parent_name, target_container_name):
            if current_level == target_level:
                for item in data:
                    if item.get('name') == target_parent_name:
                        containers = item.get('containers', {})
                        if target_container_name in containers:
                            return containers[target_container_name]
                return None
            else:
                for item in data:
                    containers = item.get('containers', {})
                    for container_name, container_items in containers.items():
                        result = find_container_at_level(container_items, current_level + 1, target_level, target_parent_name, target_container_name)
                        if result is not None:
                            return result
                return None
        
        target_container = find_container_at_level(self.current_inventory_data, 1, level, parent_item_name, parent_container_name)
        if target_container is not None:
            for i, item in enumerate(target_container):
                if item.get('item_id') == item_id or item.get('name') == item_name:
                    target_container.pop(i)
                    return True
        return False

    def _add_item_to_container_data(self, level, parent_item_name, parent_container_name, new_item):
        def find_container_at_level(data, current_level, target_level, target_parent_name, target_container_name):
            if current_level == target_level:
                for item in data:
                    if item.get('name') == target_parent_name:
                        if 'containers' not in item:
                            item['containers'] = {}
                        if target_container_name not in item['containers']:
                            item['containers'][target_container_name] = []
                        return item['containers'][target_container_name]
                return None
            else:
                for item in data:
                    containers = item.get('containers', {})
                    for container_name, container_items in containers.items():
                        result = find_container_at_level(container_items, current_level + 1, target_level, target_parent_name, target_container_name)
                        if result is not None:
                            return result
                return None
        
        target_container = find_container_at_level(self.current_inventory_data, 1, level, parent_item_name, parent_container_name)
        if target_container is not None:
            target_container.append(new_item)
            return True
        return False

    def _remove_container_widgets_deeper_than(self, level):
        def remove_widget_recursively(widget):
            if hasattr(widget, 'layout') and widget.layout():
                for i in range(widget.layout().count()):
                    child_item = widget.layout().itemAt(i)
                    if child_item and child_item.widget():
                        remove_widget_recursively(child_item.widget())
            widget.deleteLater()
        
        def find_and_remove_widgets_recursively(parent_widget, target_level):
            widgets_to_remove = []
            if hasattr(parent_widget, 'layout') and parent_widget.layout():
                for i in range(parent_widget.layout().count()):
                    child_item = parent_widget.layout().itemAt(i)
                    if child_item and child_item.widget():
                        child_widget = child_item.widget()
                        if hasattr(child_widget, 'level') and child_widget.level > target_level:
                            widgets_to_remove.append((i, child_widget))
                        else:
                            widgets_to_remove.extend(find_and_remove_widgets_recursively(child_widget, target_level))
            return widgets_to_remove
        widgets_to_remove = []
        
        for i in range(self.containers_layout.count()):
            item = self.containers_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                found_widgets = find_and_remove_widgets_recursively(widget, level)
                for layout_index, found_widget in found_widgets:
                    widgets_to_remove.append((i, layout_index, found_widget))
        for row_index, layout_index, widget in sorted(widgets_to_remove, key=lambda x: (x[0], x[1]), reverse=True):
            row_widget = self.containers_layout.itemAt(row_index).widget()
            if row_widget and hasattr(row_widget, 'layout') and row_widget.layout():
                row_widget.layout().takeAt(layout_index)
                remove_widget_recursively(widget)
                if row_widget.layout().count() == 0:
                    self.containers_layout.takeAt(row_index)
                    row_widget.deleteLater()
