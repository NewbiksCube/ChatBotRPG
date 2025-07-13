from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QHBoxLayout, QPushButton, QLabel, QTextEdit, QMessageBox, QInputDialog, QScrollArea, QSizePolicy, QCheckBox
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt, QTimer, QEvent
import os
import json
import re
import shutil
from generate.generate_actor import generate_actor_fields_async

def sanitize_path_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', name).strip()
    sanitized = sanitized.replace(' ', '_').lower()
    return sanitized or 'untitled'

class ActorManagerWidget(QWidget):
    def __init__(self, workflow_data_dir, parent=None):
        super().__init__(parent)
        self.workflow_data_dir = workflow_data_dir
        self._selected_actor_path = None
        self._selected_relation_row_widget = None
        self._selected_variable_row_widget = None
        self._details_save_timer = QTimer(self)
        self._details_save_timer.setSingleShot(True)
        self._details_save_timer.timeout.connect(self._save_actor_details)
        self._default_relation_row_style = ""
        self._generation_checkboxes = {}
        self._generation_thread = None
        self.EQUIPMENT_SLOTS = {
            "head": "Head", "neck": "Neck",
            "left_shoulder": "Left Shoulder", "right_shoulder": "Right Shoulder",
            "left_hand": "Left Hand (Worn)", "right_hand": "Right Hand (Worn)",
            "upper_over": "Upper Outer", "upper_outer": "Upper Outer",
            "upper_middle": "Upper Middle", "upper_inner": "Upper Inner",
            "lower_outer": "Lower Outer", "lower_middle": "Lower Middle",
            "lower_inner": "Lower Inner",
            "left_foot_inner": "Left Foot Inner", "right_foot_inner": "Right Foot Inner",
            "left_foot_outer": "Left Foot Outer", "right_foot_outer": "Right Foot Outer",
        }
        self.EQUIPMENT_SLOT_ORDER = [
            "head", "neck",
            "left_shoulder", "right_shoulder",
            "left_hand", "right_hand",
            "upper_over", "upper_outer", "upper_middle", "upper_inner",
            "lower_outer", "lower_middle", "lower_inner",
            "left_foot_inner", "right_foot_inner",
            "left_foot_outer", "right_foot_outer"
        ]
        self._inventory_widgets = {}
        self._init_ui()
        self._ensure_initial_player()

    def eventFilter(self, obj, event):
        if isinstance(obj, QLineEdit) and obj.property("is_relation_input"):
            if event.type() == QEvent.FocusIn:
                row_widget = obj.property("row_widget")
                self._handle_relation_row_focus(row_widget)
        elif isinstance(obj, QLineEdit) and obj.property("is_variable_input"):
            if event.type() == QEvent.FocusIn:
                row_widget = obj.property("row_widget")
                try:
                    if self._selected_variable_row_widget and self._selected_variable_row_widget.isVisible():
                        self._selected_variable_row_widget.setProperty("class", "")
                        self._selected_variable_row_widget.setStyleSheet("")
                except RuntimeError:
                    self._selected_variable_row_widget = None
                row_widget.setProperty("class", "VariableRowSelected")
                row_widget.setStyleSheet("")
                self._selected_variable_row_widget = row_widget
        return super().eventFilter(obj, event)

    def _handle_relation_row_focus(self, row_widget):
        if row_widget and isinstance(row_widget, QWidget) and row_widget != self._selected_relation_row_widget:
            if self._selected_relation_row_widget:
                try:
                    self._selected_relation_row_widget.setStyleSheet(self._default_relation_row_style)
                except RuntimeError:
                    pass
            if not self._default_relation_row_style and row_widget.styleSheet() is not None:
                 self._default_relation_row_style = row_widget.styleSheet()
            palette = self.palette()
            highlight_color = palette.color(QPalette.Highlight)
            highlight_style = f"background-color: rgba({highlight_color.red()}, {highlight_color.green()}, {highlight_color.blue()}, 40);" # ~15% alpha (40/255)
            row_widget.setStyleSheet(highlight_style)
            self._selected_relation_row_widget = row_widget

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        list_layout = QVBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setObjectName("FilterInput")
        self.filter_input.setPlaceholderText("Filter by...")
        self.filter_input.textChanged.connect(self._filter_list)
        filter_button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setObjectName("RefreshButton")
        self.refresh_button.setToolTip("Refresh Actor List")
        self.refresh_button.setMaximumWidth(30)
        font = self.refresh_button.font()
        font.setPointSize(font.pointSize() + 2)
        self.refresh_button.setFont(font)
        self.refresh_button.clicked.connect(self._load_actors_from_disk)
        self.add_actor_button = QPushButton("+")
        self.add_actor_button.setObjectName("AddButton")
        self.add_actor_button.setToolTip("Add New Actor")
        self.add_actor_button.clicked.connect(self._add_actor)
        self.remove_actor_button = QPushButton("-")
        self.remove_actor_button.setObjectName("RemoveButton")
        self.remove_actor_button.setToolTip("Remove Selected Actor")
        self.remove_actor_button.clicked.connect(self._remove_actor)
        filter_button_layout.addWidget(self.filter_input, 1)
        filter_button_layout.addWidget(self.refresh_button)
        filter_button_layout.addWidget(self.add_actor_button)
        filter_button_layout.addWidget(self.remove_actor_button)
        list_layout.addLayout(filter_button_layout)
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("ActorManagerList")
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.currentItemChanged.connect(self._on_actor_selected)
        list_layout.addWidget(self.list_widget)
        edit_layout = QVBoxLayout()
        name_row_layout = QHBoxLayout()
        self.player_checkbox = QCheckBox("PLAYER")
        self.player_checkbox.setObjectName("PlayerCheckbox")
        self.player_checkbox.setToolTip("Mark this actor as the player character (only one allowed).")
        self.player_checkbox.stateChanged.connect(self._handle_player_checkbox_change)
        self.player_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        name_row_layout.addWidget(self.player_checkbox)
        label_name_actor = QLabel("Name:")
        label_name_actor.setObjectName("ActorManagerEditLabel")
        self.actor_name_input = QLineEdit()
        self.actor_name_input.setObjectName("ActorManagerNameInput")
        self.actor_name_input.editingFinished.connect(self._save_actor_details)
        self.actor_name_input.setMaximumWidth(300)
        label_location_actor = QLabel("Location:")
        label_location_actor.setObjectName("ActorManagerEditLabel")
        self.actor_location_input = QLineEdit()
        self.actor_location_input.setObjectName("ActorManagerNameInput")
        self.actor_location_input.textChanged.connect(self._schedule_details_save)
        self.actor_location_input.setMaximumWidth(300)
        self.location_refresh_button = QPushButton("↻")
        self.location_refresh_button.setObjectName("LocationRefreshButton")
        self.location_refresh_button.setToolTip("Refresh - Try to apply actor to location again")
        self.location_refresh_button.setMaximumWidth(30)
        self.location_refresh_button.clicked.connect(self._refresh_actor_location)
        name_gen_checkbox = QCheckBox("Generate Name")
        name_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        name_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['name'] = name_gen_checkbox
        name_row_layout.addStretch(1)
        name_row_layout.addWidget(label_name_actor)
        name_row_layout.addWidget(self.actor_name_input)
        name_row_layout.addWidget(name_gen_checkbox)
        name_row_layout.addStretch(1)
        location_layout = QHBoxLayout()
        location_layout.addWidget(label_location_actor)
        location_layout.addWidget(self.actor_location_input)
        location_layout.addWidget(self.location_refresh_button)
        location_layout.addStretch(1)
        name_row_layout.addLayout(location_layout)
        edit_layout.addLayout(name_row_layout)
        fields_row_layout = QHBoxLayout()
        desc_layout = QVBoxLayout()
        label_desc_actor = QLabel("Description:")
        label_desc_actor.setObjectName("ActorManagerEditLabel")
        self.actor_description_input = QTextEdit()
        self.actor_description_input.setObjectName("ActorManagerDescInput")
        self.actor_description_input.textChanged.connect(self._schedule_details_save)
        self.actor_description_input.setMaximumHeight(120)
        desc_layout.addWidget(label_desc_actor)
        desc_layout.addWidget(self.actor_description_input)
        desc_gen_checkbox = QCheckBox("Generate Description")
        desc_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        desc_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['description'] = desc_gen_checkbox
        desc_layout.addWidget(desc_gen_checkbox, alignment=Qt.AlignHCenter)
        fields_row_layout.addLayout(desc_layout, 2)
        personality_layout = QVBoxLayout()
        label_personality_actor = QLabel("Personality:")
        label_personality_actor.setObjectName("ActorManagerEditLabel")
        self.actor_personality_input = QTextEdit()
        self.actor_personality_input.setObjectName("ActorManagerDescInput")
        self.actor_personality_input.textChanged.connect(self._schedule_details_save)
        self.actor_personality_input.setMaximumHeight(120)
        personality_layout.addWidget(label_personality_actor)
        personality_layout.addWidget(self.actor_personality_input)
        pers_gen_checkbox = QCheckBox("Generate Personality")
        pers_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        pers_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['personality'] = pers_gen_checkbox
        personality_layout.addWidget(pers_gen_checkbox, alignment=Qt.AlignHCenter)
        fields_row_layout.addLayout(personality_layout, 2)
        appearance_layout = QVBoxLayout()
        label_appearance_actor = QLabel("Appearance:")
        label_appearance_actor.setObjectName("ActorManagerEditLabel")
        self.actor_appearance_input = QTextEdit()
        self.actor_appearance_input.setObjectName("ActorManagerDescInput")
        self.actor_appearance_input.textChanged.connect(self._schedule_details_save)
        self.actor_appearance_input.setMaximumHeight(120)
        appearance_layout.addWidget(label_appearance_actor)
        appearance_layout.addWidget(self.actor_appearance_input)
        app_gen_checkbox = QCheckBox("Generate Appearance")
        app_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        app_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['appearance'] = app_gen_checkbox
        appearance_layout.addWidget(app_gen_checkbox, alignment=Qt.AlignHCenter)
        fields_row_layout.addLayout(appearance_layout, 2)
        edit_layout.addLayout(fields_row_layout)
        status_goals_layout = QHBoxLayout()
        variables_layout = QVBoxLayout()
        label_variables_actor = QLabel("Variables:")
        label_variables_actor.setObjectName("ActorManagerEditLabel")
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
        variables_header_layout.addWidget(label_variables_actor)
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
        status_goals_layout.addLayout(variables_layout)
        goals_layout = QVBoxLayout()
        label_goals_actor = QLabel("Goals:")
        label_goals_actor.setObjectName("ActorManagerEditLabel")
        self.actor_goals_input = QTextEdit()
        self.actor_goals_input.setObjectName("ActorManagerDescInput")
        self.actor_goals_input.textChanged.connect(self._schedule_details_save)
        self.actor_goals_input.setMaximumHeight(80)
        goals_layout.addWidget(label_goals_actor)
        goals_layout.addWidget(self.actor_goals_input)
        goals_gen_checkbox = QCheckBox("Generate Goals")
        goals_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        goals_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['goals'] = goals_gen_checkbox
        goals_layout.addWidget(goals_gen_checkbox, alignment=Qt.AlignHCenter)
        status_goals_layout.addLayout(goals_layout)
        edit_layout.addLayout(status_goals_layout)
        inventory_section_layout = QVBoxLayout()
        inventory_section_layout.setSpacing(2)
        inventory_label_layout = QHBoxLayout()
        label_inventory_actor = QLabel("Inventory:")
        label_inventory_actor.setObjectName("ActorManagerEditLabel")
        inventory_label_layout.addWidget(label_inventory_actor)
        inventory_label_layout.addStretch(1)
        inventory_section_layout.addLayout(inventory_label_layout)
        inventory_content_widget = QWidget()
        inventory_content_widget.setObjectName("InventoryContentContainer")
        inventory_content_layout = QVBoxLayout(inventory_content_widget)
        inventory_content_layout.setContentsMargins(5, 5, 5, 5)
        inventory_content_layout.setSpacing(4)
        inventory_left_layout = QVBoxLayout()
        holding_label = QLabel("Holding")
        holding_label.setObjectName("ActorManagerEditLabel")
        holding_label.setAlignment(Qt.AlignCenter)
        inventory_left_layout.addWidget(holding_label)
        holding_fields_widget = QWidget()
        holding_fields_layout = QHBoxLayout(holding_fields_widget)
        holding_fields_layout.setContentsMargins(0, 0, 0, 0)
        holding_fields_layout.setSpacing(10)
        label_left_hand_holding = QLabel("Left Hand:")
        label_left_hand_holding.setObjectName("ActorManagerItemLabel")
        self.actor_left_hand_holding_input = QLineEdit()
        self.actor_left_hand_holding_input.setObjectName("ActorManagerItemInput")
        self.actor_left_hand_holding_input.editingFinished.connect(self._schedule_details_save)
        holding_fields_layout.addWidget(label_left_hand_holding)
        holding_fields_layout.addWidget(self.actor_left_hand_holding_input)
        label_right_hand_holding = QLabel("Right Hand:")
        label_right_hand_holding.setObjectName("ActorManagerItemLabel")
        self.actor_right_hand_holding_input = QLineEdit()
        self.actor_right_hand_holding_input.setObjectName("ActorManagerItemInput")
        self.actor_right_hand_holding_input.editingFinished.connect(self._schedule_details_save)
        holding_fields_layout.addWidget(label_right_hand_holding)
        holding_fields_layout.addWidget(self.actor_right_hand_holding_input)
        inventory_left_layout.addWidget(holding_fields_widget)
        inventory_left_layout.addSpacing(10)
        wearing_label = QLabel("Wearing & Carrying")
        wearing_label.setObjectName("ActorManagerEditLabel")
        wearing_label.setAlignment(Qt.AlignCenter)
        inventory_left_layout.addWidget(wearing_label)
        wearing_fields_widget = QWidget()
        wearing_fields_layout = QVBoxLayout(wearing_fields_widget)
        wearing_fields_layout.setContentsMargins(0, 0, 0, 0)
        wearing_fields_layout.setSpacing(1)
        head_centering_layout = QHBoxLayout()
        head_layout = QHBoxLayout()
        label_head = QLabel("Head:")
        label_head.setObjectName("ActorManagerItemLabel")
        self.actor_head_input = QLineEdit()
        self.actor_head_input.setObjectName("ActorManagerItemInput")
        self.actor_head_input.editingFinished.connect(self._schedule_details_save)
        self.actor_head_input.setMaximumWidth(300)
        head_layout.addWidget(label_head)
        head_layout.addWidget(self.actor_head_input)
        head_centering_layout.addStretch(1)
        head_centering_layout.addLayout(head_layout)
        head_centering_layout.addStretch(1)
        wearing_fields_layout.addLayout(head_centering_layout)
        neck_centering_layout = QHBoxLayout()
        neck_layout = QHBoxLayout()
        label_neck = QLabel("Neck:")
        label_neck.setObjectName("ActorManagerItemLabel")
        self.actor_neck_input = QLineEdit()
        self.actor_neck_input.setObjectName("ActorManagerItemInput")
        self.actor_neck_input.editingFinished.connect(self._schedule_details_save)
        self.actor_neck_input.setMaximumWidth(300)
        neck_layout.addWidget(label_neck)
        neck_layout.addWidget(self.actor_neck_input)
        neck_centering_layout.addStretch(1)
        neck_centering_layout.addLayout(neck_layout)
        neck_centering_layout.addStretch(1)
        wearing_fields_layout.addLayout(neck_centering_layout)
        shoulder_layout = QHBoxLayout()
        label_left_shoulder = QLabel("Left Shoulder:")
        label_left_shoulder.setObjectName("ActorManagerItemLabel")
        self.actor_left_shoulder_input = QLineEdit()
        self.actor_left_shoulder_input.setObjectName("ActorManagerItemInput")
        self.actor_left_shoulder_input.editingFinished.connect(self._schedule_details_save)
        label_right_shoulder = QLabel("Right Shoulder:")
        label_right_shoulder.setObjectName("ActorManagerItemLabel")
        self.actor_right_shoulder_input = QLineEdit()
        self.actor_right_shoulder_input.setObjectName("ActorManagerItemInput")
        self.actor_right_shoulder_input.editingFinished.connect(self._schedule_details_save)
        shoulder_layout.addWidget(label_left_shoulder)
        shoulder_layout.addWidget(self.actor_left_shoulder_input)
        shoulder_layout.addSpacing(10)
        shoulder_layout.addWidget(label_right_shoulder)
        shoulder_layout.addWidget(self.actor_right_shoulder_input)
        wearing_fields_layout.addLayout(shoulder_layout)
        hand_layout = QHBoxLayout()
        label_left_hand = QLabel("Left Hand (Worn):")
        label_left_hand.setObjectName("ActorManagerItemLabel")
        self.actor_left_hand_input = QLineEdit()
        self.actor_left_hand_input.setObjectName("ActorManagerItemInput")
        self.actor_left_hand_input.editingFinished.connect(self._schedule_details_save)
        label_right_hand = QLabel("Right Hand (Worn):")
        label_right_hand.setObjectName("ActorManagerItemLabel")
        self.actor_right_hand_input = QLineEdit()
        self.actor_right_hand_input.setObjectName("ActorManagerItemInput")
        self.actor_right_hand_input.editingFinished.connect(self._schedule_details_save)
        hand_layout.addWidget(label_left_hand)
        hand_layout.addWidget(self.actor_left_hand_input)
        hand_layout.addSpacing(10)
        hand_layout.addWidget(label_right_hand)
        hand_layout.addWidget(self.actor_right_hand_input)
        wearing_fields_layout.addLayout(hand_layout)
        upper_over_layout = QHBoxLayout()
        label_upper_over = QLabel("Upper Over:")
        label_upper_over.setObjectName("ActorManagerItemLabel")
        self.actor_upper_over_input = QLineEdit()
        self.actor_upper_over_input.setObjectName("ActorManagerItemInput")
        self.actor_upper_over_input.editingFinished.connect(self._schedule_details_save)
        upper_over_layout.addWidget(label_upper_over)
        upper_over_layout.addWidget(self.actor_upper_over_input)
        wearing_fields_layout.addLayout(upper_over_layout)
        upper_lower_container = QHBoxLayout()
        upper_column = QVBoxLayout()
        upper_outer_layout = QHBoxLayout()
        label_upper_outer = QLabel("Upper Outer:")
        label_upper_outer.setObjectName("ActorManagerItemLabel")
        self.actor_upper_outer_input = QLineEdit()
        self.actor_upper_outer_input.setObjectName("ActorManagerItemInput")
        self.actor_upper_outer_input.editingFinished.connect(self._schedule_details_save)
        upper_outer_layout.addWidget(label_upper_outer)
        upper_outer_layout.addWidget(self.actor_upper_outer_input)
        upper_column.addLayout(upper_outer_layout)
        upper_middle_layout = QHBoxLayout()
        label_upper_middle = QLabel("Upper Middle:")
        label_upper_middle.setObjectName("ActorManagerItemLabel")
        self.actor_upper_middle_input = QLineEdit()
        self.actor_upper_middle_input.setObjectName("ActorManagerItemInput")
        self.actor_upper_middle_input.editingFinished.connect(self._schedule_details_save)
        upper_middle_layout.addWidget(label_upper_middle)
        upper_middle_layout.addWidget(self.actor_upper_middle_input)
        upper_column.addLayout(upper_middle_layout)
        upper_inner_layout = QHBoxLayout()
        label_upper_inner = QLabel("Upper Inner:")
        label_upper_inner.setObjectName("ActorManagerItemLabel")
        self.actor_upper_inner_input = QLineEdit()
        self.actor_upper_inner_input.setObjectName("ActorManagerItemInput")
        self.actor_upper_inner_input.editingFinished.connect(self._schedule_details_save)
        upper_inner_layout.addWidget(label_upper_inner)
        upper_inner_layout.addWidget(self.actor_upper_inner_input)
        upper_column.addLayout(upper_inner_layout)
        lower_column = QVBoxLayout()
        lower_outer_layout = QHBoxLayout()
        label_lower_outer = QLabel("Lower Outer:")
        label_lower_outer.setObjectName("ActorManagerItemLabel")
        self.actor_lower_outer_input = QLineEdit()
        self.actor_lower_outer_input.setObjectName("ActorManagerItemInput")
        self.actor_lower_outer_input.editingFinished.connect(self._schedule_details_save)
        lower_outer_layout.addWidget(label_lower_outer)
        lower_outer_layout.addWidget(self.actor_lower_outer_input)
        lower_column.addLayout(lower_outer_layout)
        lower_middle_layout = QHBoxLayout()
        label_lower_middle = QLabel("Lower Middle:")
        label_lower_middle.setObjectName("ActorManagerItemLabel")
        self.actor_lower_middle_input = QLineEdit()
        self.actor_lower_middle_input.setObjectName("ActorManagerItemInput")
        self.actor_lower_middle_input.editingFinished.connect(self._schedule_details_save)
        lower_middle_layout.addWidget(label_lower_middle)
        lower_middle_layout.addWidget(self.actor_lower_middle_input)
        lower_column.addLayout(lower_middle_layout)
        lower_inner_layout = QHBoxLayout()
        label_lower_inner = QLabel("Lower Inner:")
        label_lower_inner.setObjectName("ActorManagerItemLabel")
        self.actor_lower_inner_input = QLineEdit()
        self.actor_lower_inner_input.setObjectName("ActorManagerItemInput")
        self.actor_lower_inner_input.editingFinished.connect(self._schedule_details_save)
        lower_inner_layout.addWidget(label_lower_inner)
        lower_inner_layout.addWidget(self.actor_lower_inner_input)
        lower_column.addLayout(lower_inner_layout)
        upper_lower_container.addLayout(upper_column)
        upper_lower_container.addSpacing(15)
        upper_lower_container.addLayout(lower_column)
        wearing_fields_layout.addLayout(upper_lower_container)
        foot_inner_layout = QHBoxLayout()
        label_left_foot_inner = QLabel("Left Foot Inner:")
        label_left_foot_inner.setObjectName("ActorManagerItemLabel")
        self.actor_left_foot_inner_input = QLineEdit()
        self.actor_left_foot_inner_input.setObjectName("ActorManagerItemInput")
        self.actor_left_foot_inner_input.editingFinished.connect(self._schedule_details_save)
        label_right_foot_inner = QLabel("Right Foot Inner:")
        label_right_foot_inner.setObjectName("ActorManagerItemLabel")
        self.actor_right_foot_inner_input = QLineEdit()
        self.actor_right_foot_inner_input.setObjectName("ActorManagerItemInput")
        self.actor_right_foot_inner_input.editingFinished.connect(self._schedule_details_save)
        foot_inner_layout.addWidget(label_left_foot_inner)
        foot_inner_layout.addWidget(self.actor_left_foot_inner_input)
        foot_inner_layout.addSpacing(10)
        foot_inner_layout.addWidget(label_right_foot_inner)
        foot_inner_layout.addWidget(self.actor_right_foot_inner_input)
        wearing_fields_layout.addLayout(foot_inner_layout)
        foot_outer_layout = QHBoxLayout()
        label_left_foot_outer = QLabel("Left Foot Outer:")
        label_left_foot_outer.setObjectName("ActorManagerItemLabel")
        self.actor_left_foot_outer_input = QLineEdit()
        self.actor_left_foot_outer_input.setObjectName("ActorManagerItemInput")
        self.actor_left_foot_outer_input.editingFinished.connect(self._schedule_details_save)
        label_right_foot_outer = QLabel("Right Foot Outer:")
        label_right_foot_outer.setObjectName("ActorManagerItemLabel")
        self.actor_right_foot_outer_input = QLineEdit()
        self.actor_right_foot_outer_input.setObjectName("ActorManagerItemInput")
        self.actor_right_foot_outer_input.editingFinished.connect(self._schedule_details_save)
        foot_outer_layout.addWidget(label_left_foot_outer)
        foot_outer_layout.addWidget(self.actor_left_foot_outer_input)
        foot_outer_layout.addSpacing(10)
        foot_outer_layout.addWidget(label_right_foot_outer)
        foot_outer_layout.addWidget(self.actor_right_foot_outer_input)
        wearing_fields_layout.addLayout(foot_outer_layout)
        inventory_left_layout.addWidget(wearing_fields_widget)
        inventory_left_layout.addStretch(1)
        inventory_content_layout.addLayout(inventory_left_layout)
        inventory_scroll_area = QScrollArea()
        inventory_scroll_area.setObjectName("InventoryScrollArea")
        inventory_scroll_area.setWidgetResizable(True)
        inventory_scroll_area.setWidget(inventory_content_widget)
        inventory_scroll_area.setMaximumHeight(300)
        inventory_section_layout.addWidget(inventory_scroll_area)
        equip_gen_checkbox = QCheckBox("Generate Equipment")
        equip_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        equip_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['equipment'] = equip_gen_checkbox
        equip_checkbox_layout = QHBoxLayout()
        equip_checkbox_layout.addStretch(1)
        equip_checkbox_layout.addWidget(equip_gen_checkbox)
        equip_checkbox_layout.addStretch(1)
        inventory_section_layout.addLayout(equip_checkbox_layout)
        relations_main_widget = QWidget()
        relations_main_widget.setObjectName("RelationsContainer")
        relations_main_layout = QVBoxLayout(relations_main_widget)
        relations_header_layout = QHBoxLayout()
        label_relations_actor = QLabel("Relations:")
        label_relations_actor.setObjectName("ActorManagerEditLabel")
        add_relation_button = QPushButton("+")
        add_relation_button.setObjectName("AddButton")
        add_relation_button.setToolTip("Add Relation")
        add_relation_button.setMaximumWidth(30)
        add_relation_button.clicked.connect(lambda: self._add_relation_row())
        remove_relation_button = QPushButton("-")
        remove_relation_button.setObjectName("RemoveButton")
        remove_relation_button.setToolTip("Remove Selected Relation")
        remove_relation_button.setMaximumWidth(30)
        remove_relation_button.clicked.connect(self._remove_selected_relation_row)
        relations_header_layout.addWidget(label_relations_actor)
        relations_header_layout.addStretch()
        relations_header_layout.addWidget(add_relation_button)
        relations_header_layout.addWidget(remove_relation_button)
        relations_main_layout.addLayout(relations_header_layout)
        self.relations_scroll_area = QScrollArea()
        self.relations_scroll_area.setWidgetResizable(True)
        self.relations_scroll_area.setObjectName("RelationsScrollArea")
        self.relations_scroll_area.setMinimumHeight(100)
        self.relations_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        relations_content_widget = QWidget()
        self.relations_list_layout = QVBoxLayout(relations_content_widget)
        self.relations_list_layout.setAlignment(Qt.AlignTop)
        self.relations_scroll_area.setWidget(relations_content_widget)
        relations_main_layout.addWidget(self.relations_scroll_area)
        bottom_row_layout = QHBoxLayout()
        bottom_row_layout.addLayout(inventory_section_layout, 1)
        bottom_row_layout.addWidget(relations_main_widget, 1)
        bottom_fields_layout = QHBoxLayout()
        abilities_layout = QVBoxLayout()
        label_abilities_actor = QLabel("Abilities:")
        label_abilities_actor.setObjectName("ActorManagerEditLabel")
        self.actor_abilities_input = QTextEdit()
        self.actor_abilities_input.setObjectName("ActorManagerDescInput")
        self.actor_abilities_input.textChanged.connect(self._schedule_details_save)
        self.actor_abilities_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        abilities_layout.addWidget(label_abilities_actor)
        abilities_layout.addWidget(self.actor_abilities_input)
        abilities_gen_checkbox = QCheckBox("Generate Abilities")
        abilities_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        abilities_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['abilities'] = abilities_gen_checkbox
        abilities_layout.addWidget(abilities_gen_checkbox, alignment=Qt.AlignHCenter)
        bottom_fields_layout.addLayout(abilities_layout, 1)
        story_layout = QVBoxLayout()
        label_story_actor = QLabel("Story:")
        label_story_actor.setObjectName("ActorManagerEditLabel")
        self.actor_story_input = QTextEdit()
        self.actor_story_input.setObjectName("ActorManagerDescInput")
        self.actor_story_input.textChanged.connect(self._schedule_details_save)
        self.actor_story_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        story_layout.addWidget(label_story_actor)
        story_layout.addWidget(self.actor_story_input)
        story_gen_checkbox = QCheckBox("Generate Story")
        story_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        story_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['story'] = story_gen_checkbox
        story_layout.addWidget(story_gen_checkbox, alignment=Qt.AlignHCenter)
        bottom_fields_layout.addLayout(story_layout, 1)
        
        schedule_layout = QVBoxLayout()
        label_schedule_actor = QLabel("Schedule:")
        label_schedule_actor.setObjectName("ActorManagerEditLabel")
        self.actor_schedule_input = QTextEdit()
        self.actor_schedule_input.setObjectName("ActorManagerDescInput")
        self.actor_schedule_input.textChanged.connect(self._schedule_details_save)
        self.actor_schedule_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        schedule_layout.addWidget(label_schedule_actor)
        schedule_layout.addWidget(self.actor_schedule_input)
        schedule_gen_checkbox = QCheckBox("Generate Schedule")
        schedule_gen_checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        schedule_gen_checkbox.stateChanged.connect(self._update_generate_button_text)
        self._generation_checkboxes['schedule'] = schedule_gen_checkbox
        schedule_layout.addWidget(schedule_gen_checkbox, alignment=Qt.AlignHCenter)
        bottom_fields_layout.addLayout(schedule_layout, 1)
        edit_layout.addLayout(name_row_layout)
        edit_layout.addLayout(fields_row_layout)
        edit_layout.addLayout(status_goals_layout)
        edit_layout.addLayout(bottom_row_layout, 1)
        edit_layout.addLayout(bottom_fields_layout, 2)
        self.generate_button = QPushButton()
        self.generate_button.setText("Generate ...")
        self.generate_button.setEnabled(False)
        self.generate_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.generate_button.clicked.connect(self._start_generation)
        self.model_override_input = QLineEdit()
        self.model_override_input.setObjectName("ModelOverrideInput")
        self.model_override_input.setPlaceholderText("Optional model (e.g. anthropic/claude-3.5-sonnet)")
        self.model_override_input.setToolTip("Override the default model for this generation only.")
        self.model_override_input.setMaximumWidth(260)
        self.additional_instructions_input = QTextEdit()
        self.additional_instructions_input.setObjectName("AdditionalInstructionsInput")
        self.additional_instructions_input.setPlaceholderText("Optional additional instructions for the LLM...")
        self.additional_instructions_input.setToolTip("Add specific instructions for the generation process (e.g., 'Make the story more dramatic').")
        font_metrics = self.additional_instructions_input.fontMetrics()
        line_height = font_metrics.lineSpacing()
        self.additional_instructions_input.setMaximumHeight(line_height * 3 + 10)
        self.additional_instructions_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        generate_button_layout = QHBoxLayout()
        generate_button_layout.addStretch(1)
        generate_button_layout.addWidget(self.generate_button)
        generate_button_layout.addWidget(self.model_override_input)
        generate_button_layout.addWidget(self.additional_instructions_input)
        generate_button_layout.addStretch(1)
        edit_layout.addLayout(generate_button_layout)
        main_layout.addLayout(list_layout, 1)
        main_layout.addLayout(edit_layout, 4)
        self._load_actors_from_disk()

    def set_actors(self, actor_data):
        self.list_widget.clear()
        for display_name, file_path, is_game_file in actor_data:
            is_player = False
            if os.path.exists(file_path):
                data = self._load_json(file_path)
                is_player = data.get('isPlayer', False)
            list_display_name = display_name
            if is_player:
                list_display_name += " (Player)"
            if is_game_file:
                list_display_name += " *"
            item = QListWidgetItem(list_display_name)
            item.setData(Qt.UserRole, file_path)
            item.setToolTip(f"{'Game' if is_game_file else 'Resource'} file: {file_path}")
            self.list_widget.addItem(item)

    def _filter_list(self, text):
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text not in item.text().lower())

    def _load_actors_from_disk(self):
        current_path = None
        if self.list_widget.currentItem():
            current_path = self.list_widget.currentItem().data(Qt.UserRole)
        actors_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
        actor_data = []
        processed_files = set()
        if os.path.isdir(actors_dir):
            for filename in os.listdir(actors_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(actors_dir, filename)
                    if file_path in processed_files:
                        continue
                    data = self._load_json(file_path)
                    if data and 'name' in data:
                        display_name = data['name']
                        actor_data.append((display_name, file_path, False))
                        processed_files.add(file_path)
        game_actors_dir = os.path.join(self.workflow_data_dir, 'game', 'actors')
        if os.path.isdir(game_actors_dir):
            for filename in os.listdir(game_actors_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(game_actors_dir, filename)
                    if file_path in processed_files:
                        continue
                    data = self._load_json(file_path)
                    if data and 'name' in data:
                        display_name = data['name']
                        actor_data.append((display_name, file_path, True))
                        processed_files.add(file_path)
        actor_data.sort(key=lambda x: x[0].lower())
        self.set_actors(actor_data)
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None
        if current_path:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.data(Qt.UserRole) == current_path:
                    self.list_widget.setCurrentItem(item)
                    break

    def _on_actor_selected(self, current_item, previous_item):
        self._details_save_timer.stop()
        if current_item:
            self._selected_actor_path = current_item.data(Qt.UserRole)
            print(f"Actor selected: {current_item.text()}, Path: {self._selected_actor_path}")
            data = self._load_json(self._selected_actor_path)
            name_from_json = data.get('name', current_item.text())
            desc_from_json = data.get('description', '')
            personality_from_json = data.get('personality', '')
            appearance_from_json = data.get('appearance', '')
            goals_from_json = data.get('goals', '')
            story_from_json = data.get('story', '')
            equipment_from_json = data.get('equipment', {})
            abilities_from_json = data.get('abilities', '')
            schedule_from_json = data.get('schedule', '')
            location_from_json = data.get('location', '')
            left_hand_holding_from_json = data.get('left_hand_holding', '')
            right_hand_holding_from_json = data.get('right_hand_holding', '')
            self.actor_name_input.setText(name_from_json)
            self.actor_description_input.blockSignals(True)
            self.actor_description_input.setPlainText(desc_from_json)
            self.actor_description_input.blockSignals(False)
            self.actor_personality_input.blockSignals(True)
            self.actor_personality_input.setPlainText(personality_from_json)
            self.actor_personality_input.blockSignals(False)
            self.actor_appearance_input.blockSignals(True)
            self.actor_appearance_input.setPlainText(appearance_from_json)
            self.actor_appearance_input.blockSignals(False)
            self.actor_goals_input.blockSignals(True)
            self.actor_goals_input.setPlainText(goals_from_json)
            self.actor_goals_input.blockSignals(False)
            self.actor_story_input.blockSignals(True)
            self.actor_story_input.setPlainText(story_from_json)
            self.actor_story_input.blockSignals(False)
            self.actor_abilities_input.blockSignals(True);
            self.actor_abilities_input.setPlainText(abilities_from_json)
            self.actor_abilities_input.blockSignals(False);
            self.actor_schedule_input.blockSignals(True)
            self.actor_schedule_input.setPlainText(schedule_from_json)
            self.actor_schedule_input.blockSignals(False)
            self.actor_location_input.blockSignals(True);
            self.actor_location_input.setText(location_from_json)
            self.actor_location_input.blockSignals(False);
            is_player = data.get('isPlayer', False)
            self.player_checkbox.blockSignals(True)
            self.player_checkbox.setChecked(is_player)
            self.player_checkbox.blockSignals(False)
            self.actor_left_hand_holding_input.blockSignals(True)
            self.actor_left_hand_holding_input.setText(left_hand_holding_from_json)
            self.actor_left_hand_holding_input.blockSignals(False)
            self.actor_right_hand_holding_input.blockSignals(True)
            self.actor_right_hand_holding_input.setText(right_hand_holding_from_json)
            self.actor_right_hand_holding_input.blockSignals(False)
            if not isinstance(equipment_from_json, dict):
                equipment_from_json = {}
            for slot_key in self.EQUIPMENT_SLOT_ORDER:
                input_attr_name = f"actor_{slot_key}_input"
                if hasattr(self, input_attr_name):
                    input_widget = getattr(self, input_attr_name)
                    input_widget.blockSignals(True)
                    input_widget.setText(equipment_from_json.get(slot_key, ''))
                    input_widget.blockSignals(False)
            self._clear_variable_rows()
            variables_from_json = data.get('variables', {})
            if isinstance(variables_from_json, dict):
                for var_name, var_value in variables_from_json.items():
                    self._add_variable_row(str(var_name), str(var_value))
        else:
            self._selected_actor_path = None
            self.actor_name_input.clear()
            self.actor_description_input.clear()
            self.actor_personality_input.clear()
            self.actor_appearance_input.clear()
            self.actor_goals_input.clear()
            self.actor_story_input.clear()
            self.actor_left_hand_holding_input.clear()
            self.actor_right_hand_holding_input.clear()
            for slot_key in self.EQUIPMENT_SLOT_ORDER:
                 input_attr_name = f"actor_{slot_key}_input"
                 if hasattr(self, input_attr_name):
                    getattr(self, input_attr_name).clear()
            self.actor_abilities_input.clear()
            self.actor_schedule_input.clear()
            self.actor_location_input.clear()
            self.player_checkbox.blockSignals(True)
            self.player_checkbox.setChecked(False)

    def _schedule_details_save(self):
        self._details_save_timer.start(500)

    def _save_actor_details(self):
        self._details_save_timer.stop()
        current_item = self.list_widget.currentItem()
        if not current_item or not self._selected_actor_path:
            return
        old_json_path = self._selected_actor_path
        old_display_name = current_item.text().replace(" (Player)", "")
        data = self._load_json(old_json_path)
        is_currently_player = data.get('isPlayer', False)
        old_location_name = data.get('location', '')
        new_display_name = self.actor_name_input.text().strip()
        new_description = self.actor_description_input.toPlainText().strip()
        new_personality = self.actor_personality_input.toPlainText().strip()
        new_appearance = self.actor_appearance_input.toPlainText().strip()
        new_relations = self._get_relations_data()
        new_goals = self.actor_goals_input.toPlainText().strip()
        new_story = self.actor_story_input.toPlainText().strip()
        new_abilities = self.actor_abilities_input.toPlainText().strip()
        new_schedule = self.actor_schedule_input.toPlainText().strip()
        new_location_name = self.actor_location_input.text().strip()
        new_left_hand_holding = self.actor_left_hand_holding_input.text().strip()
        new_right_hand_holding = self.actor_right_hand_holding_input.text().strip()
        new_equipment = {}
        for slot_key in self.EQUIPMENT_SLOT_ORDER:
            input_attr_name = f"actor_{slot_key}_input"
            if hasattr(self, input_attr_name):
                equipment_getter = getattr(self, input_attr_name, None)
                if equipment_getter and hasattr(equipment_getter, 'text'):
                    new_equipment[slot_key] = equipment_getter.text().strip()
                else:
                    print(f"[WARN] Could not get text from UI Input widget for saving equipment slot: {slot_key}")
                    new_equipment[slot_key] = data.get('equipment', {}).get(slot_key, '')
            else:
                 print(f"[WARN] UI Input widget attribute not found for saving equipment slot: {slot_key}")
                 new_equipment[slot_key] = data.get('equipment', {}).get(slot_key, '')
        data['name'] = new_display_name
        data['description'] = new_description
        data['personality'] = new_personality
        data['appearance'] = new_appearance
        data['relations'] = new_relations
        data['goals'] = new_goals
        data['story'] = new_story
        data['equipment'] = new_equipment
        data['abilities'] = new_abilities
        data['schedule'] = new_schedule
        data['location'] = new_location_name
        data['left_hand_holding'] = new_left_hand_holding
        data['right_hand_holding'] = new_right_hand_holding
        new_variables = self._get_variables_data()
        data['variables'] = new_variables
        save_successful = self._save_json(old_json_path, data)
        if not save_successful:
            print(f"Failed to save actor data to {old_json_path}")
            QMessageBox.critical(self, "Save Error", f"Failed to save actor data for '{new_display_name}'.")
            return
        if old_location_name != new_location_name:
            self._update_actor_location_in_settings(data['name'], old_location_name, new_location_name)
        if old_display_name != new_display_name:
            new_sanitized_name = sanitize_path_name(new_display_name)
            new_file_name = f"{new_sanitized_name}.json"
            target_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
            new_json_path = os.path.join(target_dir, new_file_name)
            list_display_name = new_display_name + (" (Player)" if is_currently_player else "")
            current_item.setText(list_display_name)
            if os.path.normpath(old_json_path) != os.path.normpath(new_json_path):
                rename_successful = True
                if os.path.exists(new_json_path):
                    QMessageBox.warning(self, "Rename Error", f"Cannot rename actor to '{new_display_name}' because a file named '{new_file_name}' already exists in the target directory.")
                    rename_successful = False
                else:
                    try:
                        shutil.move(old_json_path, new_json_path)
                        self._selected_actor_path = new_json_path
                    except OSError as e:
                        QMessageBox.critical(self, "Rename Error", f"Failed to rename file for actor. Error: {e}")
                        rename_successful = False

                if rename_successful:
                    current_item.setData(Qt.UserRole, new_json_path)
                else:
                    current_item.setText(old_display_name + (" (Player)" if is_currently_player else ""))
            else:
                 current_item.setData(Qt.UserRole, old_json_path) 
        else:
             list_display_name = old_display_name + (" (Player)" if is_currently_player else "")
             current_item.setText(list_display_name)
             current_item.setData(Qt.UserRole, old_json_path)

    def _add_actor(self):
        title = "Add New Actor"
        label = "Enter name for the new actor:"
        new_name, ok = QInputDialog.getText(self, title, label)
        if not ok or not new_name.strip():
            print("Add Actor cancelled.")
            return
        new_name = new_name.strip()
        sanitized_name = sanitize_path_name(new_name)
        json_filename = f"{sanitized_name}.json"
        actors_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
        new_actor_path = os.path.join(actors_dir, json_filename)
        try:
            os.makedirs(actors_dir, exist_ok=True)
        except OSError as e:
            print(f"Error ensuring actors directory exists: {e}")
            QMessageBox.critical(self, "Error", f"Could not create actors directory. Error: {e}")
            return
        if os.path.exists(new_actor_path):
            QMessageBox.warning(self, "Error", f"An actor file named '{json_filename}' already exists in the selected directory.")
            return
        try:
            default_data = {
                "name": new_name,
                "description": "",
                "personality": "",
                "appearance": "",
                "status": "",
                "relations": {},
                "goals": "",
                "story": "",
                "equipment": {key: "" for key in self.EQUIPMENT_SLOT_ORDER},
                "abilities": "",
                "schedule": "",
                "location": "",
                "left_hand_holding": "",
                "right_hand_holding": "",
                "variables": {}
            }
            if not self._save_json(new_actor_path, default_data):
                raise IOError(f"Failed to save actor JSON to {new_actor_path}")
            print(f"Created Actor JSON: {new_actor_path}")
        except (OSError, IOError) as e:
            print(f"Error creating Actor: {e}")
            QMessageBox.critical(self, "Error", f"Could not create Actor. Error: {e}")
            return
        self._load_actors_from_disk()
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == new_actor_path:
                self.list_widget.setCurrentItem(item)
                break

    def _remove_actor(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Needed", "Please select an Actor to remove.")
            return
        item_name = current_item.text().replace(" (Player)", "")
        actor_filepath = current_item.data(Qt.UserRole)
        if not actor_filepath or not isinstance(actor_filepath, str):
             QMessageBox.critical(self, "Error", "Could not determine the file path for the selected actor.")
             return
        current_location_name = ""
        actor_data = {}
        if os.path.exists(actor_filepath):
            actor_data = self._load_json(actor_filepath)
            current_location_name = actor_data.get('location', '')
            actor_name_from_data = actor_data.get('name', item_name)
            if current_location_name:
                self._update_actor_location_in_settings(actor_name_from_data, current_location_name, "")
        else:
            actor_name_from_data = item_name
        try:
            if current_location_name:
                 self._update_actor_location_in_settings(actor_name_from_data, current_location_name, "")
            if os.path.isfile(actor_filepath):
                os.remove(actor_filepath)
            else:
                print(f"Warning: File to remove not found: {actor_filepath}")
            row = self.list_widget.row(current_item)
            taken_item = self.list_widget.takeItem(row)
            if self._selected_relation_row_widget and not self._selected_relation_row_widget.parent():
                self._selected_relation_row_widget = None
            del taken_item
        except OSError as e:
            print(f"Error removing actor: {e}")
            QMessageBox.critical(self, "Error", f"Could not remove actor '{actor_name_from_data}'. Error: {e}")
            self._load_actors_from_disk()
            return
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
            try:
                main_ui.delete_rule_sound.play()
            except Exception:
                main_ui.delete_rule_sound = None

    def _load_json(self, file_path):
        if not file_path or not os.path.isfile(file_path):
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                loaded_data = json.loads(content)
                if not isinstance(loaded_data, dict):
                     return {}
                return loaded_data
        except (json.JSONDecodeError, IOError, OSError) as e:
            print(f"ActorManager: Error reading JSON from {file_path}: {e}")
            return {}

    def _save_json(self, file_path, data):
        if not file_path:
            print("ActorManager: Error - Cannot save JSON, no file path provided.")
            return False
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            print(f"ActorManager: Error writing JSON to {file_path}: {e}")
            return False
        except Exception as e:
            print(f"ActorManager: Unexpected error writing JSON to {file_path}: {e}")
            return False

    def _add_relation_row(self, name="", description=""):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        name_input = QLineEdit(name)
        name_input.setObjectName("ActorManagerNameInput")
        name_input.setPlaceholderText("Relation Name")
        name_input.editingFinished.connect(self._schedule_details_save)
        name_input.setProperty("row_widget", row_widget)
        name_input.setProperty("is_relation_input", True)
        name_input.installEventFilter(self)
        colon_label = QLabel(":")
        desc_input = QLineEdit(description)
        desc_input.setObjectName("ActorManagerNameInput")
        desc_input.setPlaceholderText("Description")
        desc_input.editingFinished.connect(self._schedule_details_save)
        desc_input.setProperty("row_widget", row_widget)
        desc_input.setProperty("is_relation_input", True)
        desc_input.installEventFilter(self)
        row_layout.addWidget(name_input, 1)
        row_layout.addWidget(colon_label)
        row_layout.addWidget(desc_input, 3)
        self.relations_list_layout.addWidget(row_widget)

    def _remove_selected_relation_row(self):
        if self._selected_relation_row_widget:
            item_to_remove = None
            index_to_remove = -1
            layout = self.relations_list_layout
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget() == self._selected_relation_row_widget:
                    item_to_remove = item
                    index_to_remove = i
                    break
            if item_to_remove is not None and index_to_remove != -1:
                layout.takeAt(index_to_remove)
                widget_to_delete = self._selected_relation_row_widget
                self._selected_relation_row_widget = None
                widget_to_delete.deleteLater()
                self._schedule_details_save()
            else:
                pass
        else:
            QMessageBox.information(self, "Remove Relation", "Click on a relation row to select it before removing.")

    def _clear_relation_rows(self):
        while self.relations_list_layout.count() > 0:
            item = self.relations_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _get_relations_data(self):
        relations_data = {}
        count = self.relations_list_layout.count()
        for i in range(count):
            row_widget = self.relations_list_layout.itemAt(i).widget()
            if row_widget:
                name_input = row_widget.findChild(QLineEdit, "ActorManagerNameInput")
                desc_input = row_widget.findChild(QLineEdit, "ActorManagerNameInput", Qt.FindChildrenRecursively)
                line_edits = row_widget.findChildren(QLineEdit, "ActorManagerNameInput")
                name_input_widget = None
                desc_input_widget = None
                if len(line_edits) >= 1:
                    name_input_widget = line_edits[0]
                if len(line_edits) >= 2:
                    desc_input_widget = line_edits[1]
                if name_input_widget and desc_input_widget:
                    name = name_input_widget.text().strip()
                    description = desc_input_widget.text().strip()
                    if name:
                        relations_data[name] = description
        return relations_data 

    def _update_generate_button_text(self):
        selected = self._get_selected_generation_fields()
        if selected:
            text = ", ".join([s.capitalize() for s in selected])
            self.generate_button.setText(f"Generate {text}")
            self.generate_button.setEnabled(True)
        else:
            self.generate_button.setText("Generate ...")
            self.generate_button.setEnabled(False)

    def _get_selected_generation_fields(self):
        return [field for field, cb in self._generation_checkboxes.items() if cb.isChecked()]

    def _get_current_actor_data_from_ui(self):
        current_data = {
            'name': self.actor_name_input.text().strip(),
            'description': self.actor_description_input.toPlainText().strip(),
            'personality': self.actor_personality_input.toPlainText().strip(),
            'appearance': self.actor_appearance_input.toPlainText().strip(),
            'variables': self._get_variables_data(),
            'relations': self._get_relations_data(),
            'goals': self.actor_goals_input.toPlainText().strip(),
            'story': self.actor_story_input.toPlainText().strip(),
            'equipment': {key: getattr(self, f"actor_{key}_input").text().strip() for key in self.EQUIPMENT_SLOT_ORDER},
            'abilities': self.actor_abilities_input.toPlainText().strip(),
            'schedule': self.actor_schedule_input.toPlainText().strip(),
            'location': self.actor_location_input.text().strip(),
            'left_hand_holding': self.actor_left_hand_holding_input.text().strip(),
            'right_hand_holding': self.actor_right_hand_holding_input.text().strip(),
        }
        return current_data

    def _set_generation_controls_enabled(self, enabled: bool):
        for cb in self._generation_checkboxes.values():
            cb.setEnabled(enabled)
        self.generate_button.setEnabled(enabled and bool(self._get_selected_generation_fields()))

    def _start_generation(self):
        fields = self._get_selected_generation_fields()
        if not fields:
            return
        actor_data = self._get_current_actor_data_from_ui()
        self._set_generation_controls_enabled(False)
        model_override = self.model_override_input.text().strip()
        additional_instructions = self.additional_instructions_input.toPlainText().strip()
        result = generate_actor_fields_async(
            actor_data,
            fields,
            model_override=model_override if model_override else None,
            additional_instructions=additional_instructions if additional_instructions else None
        )
        if result:
            self._generation_thread, self._generation_worker = result
            self._generation_worker.generation_complete.connect(self._handle_generation_complete)
            self._generation_worker.generation_error.connect(self._handle_generation_error)
            self._generation_worker.generation_complete.connect(self._generation_thread.quit)
            self._generation_worker.generation_error.connect(self._generation_thread.quit)
            self._generation_thread.finished.connect(self._generation_thread.deleteLater) 

    def _handle_generation_complete(self, generated_data):
        current_item = self.list_widget.currentItem()
        if self._selected_actor_path and current_item:
            old_json_path = self._selected_actor_path
            data = self._load_json(old_json_path)
            old_display_name = data.get('name', '')
            is_currently_player = data.get('isPlayer', False)
            new_name_generated = False
            for field, value in generated_data.items():
                if field == 'name' and value.strip():
                    if data.get('name') != value.strip():
                        new_name_generated = True
                    data[field] = value.strip()
                elif field == 'equipment' and isinstance(value, dict):
                    data['equipment'] = value
                elif field in data:
                    data[field] = value
            save_successful = self._save_json(old_json_path, data)
            if not save_successful:
                QMessageBox.critical(self, "Save Error", f"Failed to save generated data for actor '{data.get('name', 'Unknown')}' to '{old_json_path}'.")
                self._set_generation_controls_enabled(True)
                return
            new_display_name = data.get('name', old_display_name)
            if new_name_generated and old_display_name != new_display_name:
                new_sanitized_name = sanitize_path_name(new_display_name)
                new_file_name = f"{new_sanitized_name}.json"
                target_dir = os.path.dirname(old_json_path)
                new_json_path = os.path.join(target_dir, new_file_name)
                list_display_name = new_display_name + (" (Player)" if is_currently_player else "")
                current_item.setText(list_display_name)
                if os.path.normpath(old_json_path) != os.path.normpath(new_json_path):
                    if os.path.exists(new_json_path):
                        QMessageBox.warning(self, "Rename Error", f"Cannot rename actor to '{new_display_name}' because a file named '{new_file_name}' already exists.")
                        current_item.setText(old_display_name + (" (Player)" if is_currently_player else ""))
                    else:
                        try:
                            shutil.move(old_json_path, new_json_path)
                            self._selected_actor_path = new_json_path
                            current_item.setData(Qt.UserRole, new_json_path)
                        except OSError as e:
                            QMessageBox.critical(self, "Rename Error", f"Failed to rename file for actor. Error: {e}")
                            current_item.setText(old_display_name + (" (Player)" if is_currently_player else ""))
                else:
                    current_item.setData(Qt.UserRole, old_json_path)
            for field, value in generated_data.items():
                if field == 'name' and new_name_generated:
                    self.actor_name_input.blockSignals(True)
                    self.actor_name_input.setText(new_display_name)
                    self.actor_name_input.blockSignals(False)
                    continue
                if field == 'description':
                    self.actor_description_input.blockSignals(True)
                    self.actor_description_input.setPlainText(value)
                    self.actor_description_input.blockSignals(False)
                elif field == 'personality':
                    self.actor_personality_input.blockSignals(True)
                    self.actor_personality_input.setPlainText(value)
                    self.actor_personality_input.blockSignals(False)
                elif field == 'appearance':
                    self.actor_appearance_input.blockSignals(True)
                    self.actor_appearance_input.setPlainText(value)
                    self.actor_appearance_input.blockSignals(False)
                elif field == 'goals':
                    self.actor_goals_input.blockSignals(True)
                    self.actor_goals_input.setPlainText(value)
                    self.actor_goals_input.blockSignals(False)
                elif field == 'story':
                    self.actor_story_input.blockSignals(True)
                    self.actor_story_input.setPlainText(value)
                    self.actor_story_input.blockSignals(False)
                elif field == 'abilities':
                    self.actor_abilities_input.blockSignals(True)
                    self.actor_abilities_input.setPlainText(value)
                    self.actor_abilities_input.blockSignals(False)
                elif field == 'schedule':
                    self.actor_schedule_input.blockSignals(True)
                    self.actor_schedule_input.setPlainText(value)
                    self.actor_schedule_input.blockSignals(False)
                elif field == 'location':
                    self.actor_location_input.blockSignals(True)
                    self.actor_location_input.setText(value)
                    self.actor_location_input.blockSignals(False)
                elif field == 'left_hand_holding':
                    self.actor_left_hand_holding_input.blockSignals(True)
                    self.actor_left_hand_holding_input.setText(value)
                    self.actor_left_hand_holding_input.blockSignals(False)
                elif field == 'right_hand_holding':
                    self.actor_right_hand_holding_input.blockSignals(True)
                    self.actor_right_hand_holding_input.setText(value)
                    self.actor_right_hand_holding_input.blockSignals(False)
                elif field == 'equipment' and isinstance(value, dict):
                    for slot_key, item_desc in value.items():
                        input_attr_name = f"actor_{slot_key}_input"
                        if hasattr(self, input_attr_name):
                            input_widget = getattr(self, input_attr_name)
                            input_widget.blockSignals(True)
                            input_widget.setText(item_desc)
                            input_widget.blockSignals(False)
            final_location_in_data = data.get('location', '')
            self.actor_location_input.blockSignals(True)
            self.actor_location_input.setText(final_location_in_data)
            self.actor_location_input.blockSignals(False)
            self._load_actors_from_disk()
            path_to_reselect = self._selected_actor_path
            successfully_reselected = False
            if path_to_reselect:
                for i in range(self.list_widget.count()):
                    item_in_new_list = self.list_widget.item(i)
                    if item_in_new_list and item_in_new_list.data(Qt.UserRole) is not None:
                        try:
                            item_data_as_string = str(item_in_new_list.data(Qt.UserRole))
                            if os.path.normpath(item_data_as_string) == os.path.normpath(path_to_reselect):
                                self.list_widget.setCurrentItem(item_in_new_list)
                                successfully_reselected = True
                                break
                        except Exception as e: 
                            print(f"[WARN] Error comparing paths during reselection in _handle_generation_complete: {e}. Item data: {item_in_new_list.data(Qt.UserRole)}, Path: {path_to_reselect}")
            if not successfully_reselected:
                if self.list_widget.count() > 0:
                    self.list_widget.setCurrentItem(self.list_widget.item(0))
        self._set_generation_controls_enabled(True)

    def _handle_generation_error(self, error_message):
        print("Generation error:", error_message)
        self._set_generation_controls_enabled(True)

    def _find_player_character_file(self):
        actors_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
        if not os.path.isdir(actors_dir):
            return None
        for filename in os.listdir(actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(actors_dir, filename)
                data = self._load_json(file_path)
                if data.get('isPlayer') is True:
                    return file_path
        return None

    def _ensure_initial_player(self):
        if self._find_player_character_file():
            return
        actors_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
        default_player_path = os.path.join(actors_dir, 'player.json')
        default_player_name = "Player"
        try:
            os.makedirs(actors_dir, exist_ok=True)
            default_data = {
                "name": default_player_name,
                "isPlayer": True,
                "description": "The protagonist of this story.",
                "personality": "",
                "appearance": "",
                "status": "Ready for adventure!",
                "relations": {},
                "goals": "",
                "story": "",
                "equipment": {key: "" for key in self.EQUIPMENT_SLOT_ORDER},
                "abilities": "",
                "schedule": "",
                "location": "",
                "left_hand_holding": "",
                "right_hand_holding": ""
            }
            if not self._save_json(default_player_path, default_data):
                raise IOError(f"Failed to save default player JSON to {default_player_path}")
        except (OSError, IOError) as e:
            print(f"Error creating default player: {e}")
            QMessageBox.critical(self, "Error", f"Could not create default player file. Error: {e}")

    def _handle_player_checkbox_change(self, state):
        current_item = self.list_widget.currentItem()
        if not current_item:
            return 
        selected_actor_path = current_item.data(Qt.UserRole)
        selected_actor_name = self.actor_name_input.text().strip()
        if not selected_actor_path or not selected_actor_name:
            self.player_checkbox.blockSignals(True)
            self.player_checkbox.setChecked(not state)
            self.player_checkbox.blockSignals(False)
            return
        if state == Qt.Checked:
            success = self._set_player_character(selected_actor_path, selected_actor_name, current_item)
        else:
            success = self._unset_player_character(selected_actor_path, selected_actor_name, current_item)
        if not success:
            self.player_checkbox.blockSignals(True)
            self.player_checkbox.setChecked(not state)
            self.player_checkbox.blockSignals(False)
            return
        actor_path_to_reselect = selected_actor_path
        self._load_actors_from_disk()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            try:
                if os.path.normpath(item.data(Qt.UserRole)) == os.path.normpath(actor_path_to_reselect):
                    self.list_widget.setCurrentItem(item)
                    break
            except Exception as e:
                 print(f"[WARN] Error comparing paths during reselection: {e}. Path1: {item.data(Qt.UserRole)}, Path2: {actor_path_to_reselect}")

    def _set_player_character(self, new_player_path, new_player_name, list_item):
        actors_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
        for filename in os.listdir(actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(actors_dir, filename)
                if file_path == new_player_path:
                    continue
                data = self._load_json(file_path)
                if data.get('isPlayer') is True:
                    data['isPlayer'] = False
                    self._save_json(file_path, data)
        new_player_data = self._load_json(new_player_path)
        if not new_player_data:
            QMessageBox.critical(self, "Error", f"Failed to load data for the new player '{new_player_name}' from '{new_player_path}'.")
            return False
        new_player_data['isPlayer'] = True
        if not self._save_json(new_player_path, new_player_data):
            QMessageBox.critical(self, "Error", f"Failed to save isPlayer flag for new player '{new_player_name}' at '{new_player_path}'.")
            return False
        self._selected_actor_path = new_player_path
        list_item.setData(Qt.UserRole, new_player_path)
        return True

    def _unset_player_character(self, player_path, player_name, list_item):
        data = self._load_json(player_path)
        if not data.get('isPlayer'):
            return True
        data['isPlayer'] = False
        if not self._save_json(player_path, data):
            QMessageBox.critical(self, "Error", f"Failed to update isPlayer flag for '{player_name}' at '{player_path}'.")
            return False
        self._selected_actor_path = player_path
        list_item.setData(Qt.UserRole, player_path)
        return True 

    def _get_setting_json_path_by_name(self, target_setting_name):
        if not target_setting_name:
            return None
        target_setting_name_lower = target_setting_name.lower()
        target_setting_sanitized = sanitize_path_name(target_setting_name)
        session_settings_base_dir = os.path.join(self.workflow_data_dir, 'game', 'settings')
        if os.path.isdir(session_settings_base_dir):
            for root, dirs, files in os.walk(session_settings_base_dir):
                dirs[:] = [d for d in dirs if d.lower() != 'saves']
                for filename in files:
                    if filename.lower().endswith('_setting.json'):
                        file_path = os.path.join(root, filename)
                        if filename.lower().startswith(f"{target_setting_sanitized}_") or filename.lower() == f"{target_setting_sanitized}_setting.json":
                            return file_path
                        setting_data = self._load_json(file_path)
                        found_name = setting_data.get('name') if isinstance(setting_data, dict) else None
                        if found_name and (found_name.lower() == target_setting_name_lower):
                            return file_path
        settings_base_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings')
        if not os.path.isdir(settings_base_dir):
            return None
        for root, dirs, files in os.walk(settings_base_dir):
            dirs[:] = [d for d in dirs if d.lower() != 'saves']
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    json_path = os.path.join(root, filename)
                    if filename.lower().startswith(f"{target_setting_sanitized}_") or filename.lower() == f"{target_setting_sanitized}_setting.json":
                        return json_path
                    if os.path.isfile(json_path):
                        setting_data = self._load_json(json_path)
                        found_name = setting_data.get('name') if isinstance(setting_data, dict) else None
                        if found_name and (found_name.lower() == target_setting_name_lower):
                            return json_path
        return None

    def _update_actor_location_in_settings(self, actor_name, old_setting_name, new_setting_name):
        if old_setting_name == new_setting_name:
            return
        if old_setting_name:
            print(f"[INFO] Removing actor '{actor_name}' from old setting '{old_setting_name}'")
            old_json_path = self._get_setting_json_path_by_name(old_setting_name)
            if old_json_path:
                old_data = self._load_json(old_json_path)
                if isinstance(old_data, dict):
                    character_list = old_data.get("characters", [])
                    if isinstance(character_list, list) and actor_name in character_list:
                        try:
                            character_list.remove(actor_name)
                            old_data["characters"] = character_list
                            self._save_json(old_json_path, old_data)
                        except ValueError:
                            print(f"[WARN] Actor '{actor_name}' not found in characters list of '{old_json_path}' during removal attempt.")
                        except Exception as e:
                            print(f"[ERROR] Unexpected error removing actor from '{old_json_path}': {e}")
        if new_setting_name:
            new_json_path = self._get_setting_json_path_by_name(new_setting_name)
            if new_json_path:
                new_data = self._load_json(new_json_path)
                if isinstance(new_data, dict):
                    character_list = new_data.get("characters", [])
                    if not isinstance(character_list, list):
                        character_list = []
                    if actor_name not in character_list:
                        character_list.append(actor_name)
                        new_data["characters"] = character_list
                        self._save_json(new_json_path, new_data)
                QMessageBox.warning(
                    self, 
                    "Setting Not Found", 
                    f"The specified setting '{new_setting_name}' could not be found.\n\n" +
                    f"The actor's location field has been updated, but they have not been added to the setting file.\n\n" +
                    f"Please ensure the setting exists in the Setting Manager and the name matches exactly."
                )

    def _refresh_actor_location(self):
        current_item = self.list_widget.currentItem()
        if not current_item or not self._selected_actor_path:
            QMessageBox.information(self, "No Actor Selected", "Please select an actor first.")
            return
        actor_name = self.actor_name_input.text().strip()
        location_name = self.actor_location_input.text().strip()
        if not actor_name:
            QMessageBox.warning(self, "Missing Actor Name", "Actor name is required.")
            return
        if not location_name:
            QMessageBox.information(self, "No Location Set", "No location is currently set for this actor.")
            return
        self._update_actor_location_in_settings(actor_name, "", location_name)
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None
        QMessageBox.information(
            self, 
            "Location Refresh Complete", 
            f"Attempted to apply actor '{actor_name}' to location '{location_name}'.\n\n" +
            "Check the console output for detailed results."
                )

    def _add_variable_row(self, name="", value=""):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        name_input = QLineEdit(name)
        name_input.setObjectName("ActorManagerVarNameInput")
        name_input.setPlaceholderText("Variable Name")
        name_input.editingFinished.connect(self._schedule_details_save)
        name_input.setProperty("row_widget", row_widget)
        name_input.setProperty("is_variable_input", True)
        name_input.installEventFilter(self)
        colon_label = QLabel(":")
        value_input = QLineEdit(value)
        value_input.setObjectName("ActorManagerVarValueInput")
        value_input.setPlaceholderText("Value")
        value_input.editingFinished.connect(self._schedule_details_save)
        value_input.setProperty("row_widget", row_widget)
        value_input.setProperty("is_variable_input", True)
        value_input.installEventFilter(self)
        row_layout.addWidget(name_input, 1)
        row_layout.addWidget(colon_label)
        row_layout.addWidget(value_input, 3)
        self.variables_list_layout.addWidget(row_widget)

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
                self._schedule_details_save()
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
                name_input = row_widget.findChild(QLineEdit, "ActorManagerVarNameInput")
                value_input = row_widget.findChild(QLineEdit, "ActorManagerVarValueInput")
                if name_input and value_input:
                    name = name_input.text().strip()
                    value = value_input.text().strip()
                    if name:
                        variables_data[name] = value
        return variables_data

    def _get_main_ui(self):
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'add_rule_sound'):
                return parent
            parent = parent.parentWidget()
        return None 