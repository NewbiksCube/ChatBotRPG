import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLabel,
                             QTextEdit, QLineEdit, QListWidget, QPushButton,
                             QRadioButton, QButtonGroup, QScrollArea, QComboBox,
                             QSpinBox, QMessageBox, QApplication, QAbstractItemView,
                             QStackedWidget, QSizePolicy, QInputDialog)
from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QFont, QColor, QPainter, QPainterPath
from core.memory import AgentMemory
from core.ui_widgets import ChatMessageListWidget, ChatbotInputField, ChatMessageWidget
from editor_panel.rules_manager import _add_rule, _load_selected_rule, _delete_selected_rule, _move_rule_up, _move_rule_down, _duplicate_selected_rule, _refresh_rules_from_json
from editor_panel.left_splitter import LeftSplitterWidget
from editor_panel.setting_manager import SettingManagerWidget
from editor_panel.time_manager import TimeManager
from editor_panel.keyword_manager import KeywordManagerWidget
from editor_panel.actor_manager import ActorManagerWidget
from player_panel.right_splitter import RightSplitterWidget
from core.top_splitter import TopSplitterWidget
from core.bottom_splitter import BottomSplitterWidget
from editor_panel.start_conditions_manager import StartConditionsManagerWidget
from editor_panel.random_generators import RandomGeneratorsWidget
from core.utils import (ensure_player_in_origin_setting, 
                   update_top_splitter_location_text, is_valid_widget,
                   get_unique_tab_dir)
from rules.rules_manager_ui import create_pair_widget
from editor_panel.notes_manager import NotesManagerWidget
from rules.rules_toggle_manager import RulesToggleManager
from rules.timer_rules_manager import _load_timer_rules
from editor_panel.inventory_manager import InventoryManagerWidget
from config import get_default_model, get_default_cot_model

class CRTEffectOverlay(QWidget):
    def __init__(self, parent, border_color="#00FF66"):
        super().__init__(parent)
        self._scanline_offset = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(140)
        self._border_color = QColor(border_color)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setFocusPolicy(Qt.NoFocus)
        self.raise_()
        self.show()

    def setBorderColor(self, color):
        self._border_color = QColor(color)
        self.update()

    def paintEvent(self, event):
        if self.width() < 10 or self.height() < 10:
            return
        path = QPainterPath()
        path.addRect(QRectF(self.rect()))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setClipPath(path)
        scanline_height = 2
        scanline_opacity = 30
        scanline_color = QColor(0, 0, 0, scanline_opacity)
        for y in range(self._scanline_offset % scanline_height, self.height(), scanline_height * 2):
            painter.fillRect(0, y, self.width(), scanline_height, scanline_color)
        painter.setClipping(False)
        pen = painter.pen()
        pen.setColor(self._border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        glow_color = QColor(self._border_color)
        glow_color.setAlpha(40)
        pen.setColor(glow_color)
        pen.setWidth(4)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.end()

    def _animate(self):
        self._scanline_offset = (self._scanline_offset + 1) % 6
        if self.isVisible():
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent():
            parent_size = self.parent().size()
            if parent_size.width() > 0 and parent_size.height() > 0:
                self.resize(parent_size)
        self.raise_()

    def setInterval(self, interval_ms):
        self._timer.setInterval(interval_ms)

DEFAULT_TAB_SETTINGS = {
    "theme_name": "Default Dark",
    "base_color": "#00FF66",
    "intensity": 0.8,
    "contrast": 0.35,
    "model": get_default_model(),
    "temperature": 0.5,
    "streaming_enabled": False,
    "streaming_speed": 35, 
    "cot_model": get_default_cot_model(),
    "crt_enabled": True,
    "crt_speed": 160
}

def get_default_tab_settings():
    return DEFAULT_TAB_SETTINGS.copy()

BASE_LOG_FILE = "conversation_log"
BASE_AGENT_NOTES_FILE = "agent_notes"
BASE_CONTEXT_FILE = "context_history"
BASE_SYSTEM_CONTEXT_FILE = "system_context"
BASE_THOUGHT_RULES_FILE = "thought_rules"
BASE_VARIABLES_FILE = "variables.json"

def save_tabs_state(self):
    pass

def add_new_tab(self, name=None, log_file=None, notes_file=None, context_file=None, system_context_file=None, thought_rules_file=None, purpose=None, variables_file=None, theme_settings=None, replace_existing_index=None, skip_heavy_loading=False):
    base_data_dir = "data"
    if name is None:
        input_name, ok = QInputDialog.getText(self, "New Workflow Name", "Enter a name for the new workflow:")
        if ok and input_name.strip():
            tab_name = input_name.strip()
        else:
            tab_name = f"Workflow {len(self.tabs_data) + 1}"
            print(f"No name entered, using default: {tab_name}")
    else:
        tab_name = name
        
    tab_dir = get_unique_tab_dir(base_data_dir, tab_name) if not log_file else os.path.dirname(log_file)
    try:
        os.makedirs(tab_dir, exist_ok=True)
        resources_dir = os.path.join(tab_dir, "resources", "data files")
        os.makedirs(resources_dir, exist_ok=True)
        rules_dir = os.path.join(resources_dir, "rules")
        os.makedirs(rules_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {tab_dir}: {e}")
        QMessageBox.critical(self, "Directory Error", f"Could not create data directory: {tab_dir}\n{e}")
        return
    final_log_file = os.path.join(tab_dir, f"{BASE_LOG_FILE}.html")
    game_dir = os.path.join(tab_dir, "game")
    os.makedirs(game_dir, exist_ok=True)
    final_notes_file = os.path.join(game_dir, f"{BASE_AGENT_NOTES_FILE}.json")
    final_context_file = os.path.join(game_dir, f"{BASE_CONTEXT_FILE}.json")
    final_system_context_file = os.path.join(resources_dir, f"{BASE_SYSTEM_CONTEXT_FILE}.txt")
    final_variables_file = os.path.join(game_dir, BASE_VARIABLES_FILE)
    final_tab_settings_file = os.path.join(tab_dir, "tab_settings.json")
    tab_settings = DEFAULT_TAB_SETTINGS.copy()
    tab_settings['dev_notes'] = ''
    if os.path.exists(final_tab_settings_file):
        try:
            with open(final_tab_settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                for key, value in loaded_settings.items():
                    if value is not None:
                         tab_settings[key] = value
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings from {final_tab_settings_file}: {e}. Using defaults.")
    else:
        try:
            with open(final_tab_settings_file, 'w', encoding='utf-8') as f:
                json.dump(tab_settings, f, indent=4)
        except IOError as e:
            print(f"Error creating default settings file {final_tab_settings_file}: {e}")
    if not os.path.exists(final_variables_file):
        with open(final_variables_file, 'w', encoding='utf-8') as f:
            json.dump({'origin': 'Default Setting', 'introduction_checked': True}, f, indent=2, ensure_ascii=False)
    else:
        try:
            with open(final_variables_file, 'r', encoding='utf-8') as f:
                variables_data = json.load(f)
            if 'origin' not in variables_data:
                variables_data['origin'] = 'Default Setting'
                if 'introduction_checked' not in variables_data:
                    variables_data['introduction_checked'] = True
                with open(final_variables_file, 'w', encoding='utf-8') as f:
                    json.dump(variables_data, f, indent=2, ensure_ascii=False)
        except Exception:
            variables_data = {}
            if 'origin' not in variables_data:
                variables_data['origin'] = 'Default Setting'
                if 'introduction_checked' not in variables_data:
                    variables_data['introduction_checked'] = True
                with open(final_variables_file, 'w', encoding='utf-8') as f:
                    json.dump(variables_data, f, indent=2, ensure_ascii=False)
    tab_content_widget = QWidget()
    tab_layout = QVBoxLayout(tab_content_widget)
    tab_layout.setContentsMargins(0,0,0,0)
    main_splitter = QSplitter(Qt.Horizontal)
    main_splitter.setChildrenCollapsible(True)
    center_vertical_splitter = QSplitter(Qt.Vertical)
    center_vertical_splitter.setChildrenCollapsible(True)
    center_vertical_splitter.setHandleWidth(2)
    conversation_widget = QWidget()
    conversation_layout = QVBoxLayout(conversation_widget)
    conversation_layout.setContentsMargins(0,0,0,0)
    output_field = ChatMessageListWidget(tab_settings, self.character_name, parent=conversation_widget)
    output_field.setObjectName("OutputField")
    conversation_layout.addWidget(output_field)

    def check_saves():
        current_tab_index = self.tabs_data.index(tab_data) if tab_data in self.tabs_data else -1
        if current_tab_index != -1:
            return self._check_saves_exist_for_tab(current_tab_index)
        return False

    input_field = ChatbotInputField(
        self,
        conversation_widget,
        theme_colors=tab_settings,
        save_check_callback=check_saves,
        tab_index=None
    )
    input_field.setObjectName(f"InputField_{len(self.tabs_data) + 1}")
    input_field.setFont(QFont('Consolas', 16))
    input_field.load_requested.connect(lambda tab_idx: self._handle_intro_load_requested(tab_idx))
    input_field.new_requested.connect(lambda tab_idx: self._handle_intro_new_requested(tab_idx))
    conversation_layout.addWidget(input_field, 1)
    left_splitter_widget = LeftSplitterWidget(tab_settings, main_app=self)
    left_splitter_widget.mode_changed.connect(self._handle_left_splitter_mode_changed)
    right_splitter_instance = RightSplitterWidget(theme_settings=tab_settings, parent=self)
    right_splitter_instance.workflow_data_dir = tab_dir
    top_splitter_widget = TopSplitterWidget(tab_settings)
    bottom_splitter_widget = BottomSplitterWidget(tab_settings)
    if top_splitter_widget:
        top_splitter_widget.setVisible(False)
    center_vertical_splitter.setStretchFactor(0, 0)
    center_vertical_splitter.setStretchFactor(1, 1)
    center_vertical_splitter.setStretchFactor(2, 0)
    right_splitter = QSplitter(Qt.Vertical)
    right_splitter.setChildrenCollapsible(True)
    rules_manager_widget = QWidget()
    rules_manager_layout = QVBoxLayout(rules_manager_widget)
    rules_manager_layout.setContentsMargins(0, 0, 0, 0)
    rules_filter_input = QLineEdit()
    rules_filter_input.setObjectName("RulesFilterInput")
    rules_filter_input.setFont(QFont('Consolas', 9))
    rules_filter_input.setPlaceholderText("Filter rules by ID or keyword...")
    rules_filter_input.setMaximumHeight(22)
    rules_manager_layout.addWidget(rules_filter_input)
    rules_area_layout = QHBoxLayout()
    rules_area_layout.setSpacing(5)
    rules_list = QListWidget()
    rules_list.setObjectName("RulesList")
    rules_list.setFont(QFont('Consolas', 10))
    rules_list.setSelectionMode(QAbstractItemView.SingleSelection)
    rules_list.setAlternatingRowColors(True)
    rules_list.setMaximumHeight(150)
    rules_list.setWordWrap(False)
    rules_list.setProperty("tab_index", -1)
    rules_list.setFocusPolicy(Qt.NoFocus)
    rules_area_layout.addWidget(rules_list, 1)
    rule_buttons_layout = QVBoxLayout()
    rule_buttons_layout.setSpacing(3)
    rule_buttons_layout.setAlignment(Qt.AlignTop)
    move_up_button = QPushButton("↑")
    move_up_button.setObjectName("MoveRuleUpButton")
    move_up_button.setToolTip("Move selected rule up")
    move_up_button.setFixedSize(25, 25)
    move_up_button.setFocusPolicy(Qt.NoFocus)
    rule_buttons_layout.addWidget(move_up_button)
    move_down_button = QPushButton("↓")
    move_down_button.setObjectName("MoveRuleDownButton")
    move_down_button.setToolTip("Move selected rule down")
    move_down_button.setFixedSize(25, 25)
    move_down_button.setFocusPolicy(Qt.NoFocus)
    rule_buttons_layout.addWidget(move_down_button)
    rules_area_layout.addLayout(rule_buttons_layout)
    add_rule_button = QPushButton("Add Rule ↑")
    add_rule_button.setFont(QFont('Consolas', 8))
    add_rule_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    add_rule_button.setFocusPolicy(Qt.NoFocus)
    rules_manager_layout.addLayout(rules_area_layout)
    duplicate_rule_button = QPushButton("Duplicate ↑")
    duplicate_rule_button.setObjectName("RuleManagerButton")
    duplicate_rule_button.setFont(QFont('Consolas', 8))
    duplicate_rule_button.setFixedHeight(20)
    duplicate_rule_button.setMinimumWidth(60)
    duplicate_rule_button.setMaximumWidth(100)
    duplicate_rule_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    duplicate_rule_button.setFocusPolicy(Qt.NoFocus)
    duplicate_rule_button.setToolTip("Duplicate the selected rule")
    clear_rule_button = QPushButton("Clear/New ↓")
    clear_rule_button.setObjectName("RuleManagerButton")
    clear_rule_button.setFont(QFont('Consolas', 8))
    clear_rule_button.setFixedHeight(20)
    clear_rule_button.setMinimumWidth(60)
    clear_rule_button.setMaximumWidth(100)
    clear_rule_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    clear_rule_button.setFocusPolicy(Qt.NoFocus)

    delete_rule_button = QPushButton("Delete ↑")
    delete_rule_button.setObjectName("RuleManagerButton")
    delete_rule_button.setFont(QFont('Consolas', 8))
    delete_rule_button.setFixedHeight(20)
    delete_rule_button.setMinimumWidth(60)
    delete_rule_button.setMaximumWidth(100)
    delete_rule_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    delete_rule_button.setFocusPolicy(Qt.NoFocus)
    delete_rule_button.setToolTip("Delete Selected Rule")
    refresh_rules_button = QPushButton("Refresh ↻")
    refresh_rules_button.setObjectName("RuleManagerButton")
    refresh_rules_button.setFont(QFont('Consolas', 8))
    refresh_rules_button.setFixedHeight(20)
    refresh_rules_button.setMinimumWidth(60)
    refresh_rules_button.setMaximumWidth(100)
    refresh_rules_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    refresh_rules_button.setFocusPolicy(Qt.NoFocus)
    refresh_rules_button.setToolTip("Refresh rules from JSON files (discards unsaved changes)")
    rule_buttons_row = QHBoxLayout()
    rule_buttons_row.addWidget(add_rule_button)
    rule_buttons_row.addWidget(duplicate_rule_button)
    rule_buttons_row.addWidget(clear_rule_button)
    rule_buttons_row.addWidget(delete_rule_button)
    rule_buttons_row.addWidget(refresh_rules_button)
    rules_manager_layout.addLayout(rule_buttons_row)
    unified_content_widget = QWidget()
    unified_content_layout = QHBoxLayout(unified_content_widget)
    unified_content_layout.setContentsMargins(0, 0, 0, 0)
    unified_content_layout.setSpacing(8)
    unified_scroll_area = QScrollArea()
    unified_scroll_area.setObjectName("UnifiedRuleScroll")
    unified_scroll_area.setWidgetResizable(True)
    unified_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    unified_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    unified_scroll_area.setWidget(unified_content_widget)
    
    rule_details_widget = QWidget()
    rule_details_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
    rule_details_layout = QVBoxLayout(rule_details_widget)
    rule_details_layout.setContentsMargins(0, 5, 0, 5)
    rule_details_layout.setSpacing(5)
    rule_id_layout = QHBoxLayout()
    rule_id_label = QLabel("Rule ID:")
    rule_id_label.setObjectName("RuleIdLabel")
    rule_id_label.setFont(QFont('Consolas', 12))
    rule_id_layout.addWidget(rule_id_label)
    rule_id_editor = QLineEdit()
    rule_id_editor.setObjectName("RuleIdEditor")
    rule_id_editor.setFont(QFont('Consolas', 10))
    rule_id_editor.setPlaceholderText("Enter a unique ID for this rule (e.g., 'check_anger')")
    rule_id_layout.addWidget(rule_id_editor)
    rule_details_layout.addLayout(rule_id_layout)
    description_layout = QHBoxLayout()
    description_label = QLabel("Description:")
    description_label.setObjectName("RuleDescriptionLabel")
    description_label.setFont(QFont('Consolas', 12))
    description_layout.addWidget(description_label)
    description_editor = QLineEdit()
    description_editor.setObjectName("RuleDescriptionEditor")
    description_editor.setFont(QFont('Consolas', 10))
    description_editor.setPlaceholderText("Optional description for this rule")
    description_layout.addWidget(description_editor)
    rule_details_layout.addLayout(description_layout)
    applies_to_layout = QHBoxLayout()
    applies_to_label = QLabel("Applies To:")
    applies_to_label.setObjectName("AppliesToLabel")
    applies_to_label.setFont(QFont('Consolas', 12))
    applies_to_layout.addWidget(applies_to_label)
    applies_to_narrator_radio = QRadioButton("Narrator")
    applies_to_narrator_radio.setObjectName("AppliesToNarratorRadio")
    applies_to_narrator_radio.setFont(QFont('Consolas', 11))
    applies_to_narrator_radio.setChecked(True)
    applies_to_narrator_radio.setToolTip("Rule actions affect the Narrator's response/context.")
    applies_to_character_radio = QRadioButton("Character")
    applies_to_character_radio.setObjectName("AppliesToCharacterRadio")
    applies_to_character_radio.setFont(QFont('Consolas', 11))
    applies_to_character_radio.setToolTip("Rule actions affect individual Characters' responses/context (runs before their turn).")
    applies_to_group = QButtonGroup(tab_content_widget)
    applies_to_group.addButton(applies_to_narrator_radio)
    applies_to_group.addButton(applies_to_character_radio)
    applies_to_layout.addWidget(applies_to_narrator_radio)
    applies_to_layout.addWidget(applies_to_character_radio)
    applies_to_layout.addStretch()
    rule_details_layout.addLayout(applies_to_layout)
    character_name_layout = QHBoxLayout()
    character_name_label = QLabel("Character Name:")
    character_name_label.setObjectName("CharacterNameLabel")
    character_name_label.setFont(QFont('Consolas', 12))
    character_name_input = QLineEdit()
    character_name_input.setObjectName("CharacterNameInput")
    character_name_input.setFont(QFont('Consolas', 10))
    character_name_input.setPlaceholderText("Enter character name (leave blank for any character)")
    character_name_input.setMinimumWidth(200)
    character_name_layout.addWidget(character_name_label)
    character_name_layout.addWidget(character_name_input)
    character_name_layout.addStretch()
    character_name_widget = QWidget()
    character_name_widget.setObjectName("CharacterNameWidget")
    character_name_widget.setLayout(character_name_layout)
    character_name_widget.setVisible(False)
    rule_details_layout.addWidget(character_name_widget)

    def update_character_name_visibility():
        is_character_selected = applies_to_character_radio.isChecked()
        character_name_widget.setVisible(is_character_selected)

    applies_to_narrator_radio.toggled.connect(update_character_name_visibility)
    applies_to_character_radio.toggled.connect(update_character_name_visibility)
    operator_layout = QHBoxLayout()
    operator_label = QLabel("If there are multiple conditions:")
    operator_label.setObjectName("ConditionsOperatorLabel")
    operator_label.setFont(QFont('Consolas', 9))
    operator_combo = QComboBox()
    operator_combo.setObjectName("ConditionsOperatorCombo")
    operator_combo.setFont(QFont('Consolas', 9))
    operator_combo.addItems(["All must be true (AND)", "Any can be true (OR)"])
    operator_layout.addWidget(operator_label)
    operator_layout.addWidget(operator_combo)
    operator_layout.addStretch()
    rule_details_layout.addLayout(operator_layout)
    conditions_container = QWidget()
    conditions_container.setObjectName("ConditionsContainer")
    conditions_layout = QVBoxLayout(conditions_container)
    conditions_layout.setContentsMargins(0, 0, 0, 0)
    conditions_layout.setSpacing(0)
    conditions_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
    condition_rows = []

    def update_all_condition_buttons():
        actual_rows_in_layout = []
        if is_valid_widget(conditions_container) and conditions_container.layout():
            layout = conditions_container.layout()
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and is_valid_widget(item.widget()) and item.widget().findChild(QComboBox, "StartConditionSelector"):
                   actual_rows_in_layout.append(item.widget())
        num_rows = len(actual_rows_in_layout)
        for i, row_widget in enumerate(actual_rows_in_layout):
            add_btn = row_widget.findChild(QPushButton, "AddConditionButton")
            remove_btn = row_widget.findChild(QPushButton, "RemoveConditionButton")
            if is_valid_widget(add_btn):
                is_last = (i == num_rows - 1)
                add_btn.setVisible(is_last)
            else:
                print(f"  Warning: Invalid add_btn for row widget at index {i}")
            if is_valid_widget(remove_btn):
                should_show_remove = (num_rows > 1)
                remove_btn.setVisible(should_show_remove)
            else:
                print(f"  Warning: Invalid remove_btn for row widget at index {i}")

    def create_condition_row(data=None):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(0)
        label = QLabel(f"Condition {len(condition_rows)+1}:")
        label.setObjectName("ConditionLabel")
        label.setFont(QFont('Consolas', 10))
        row_layout.addWidget(label)
        selector = QComboBox()
        selector.setObjectName("StartConditionSelector")
        selector.setFont(QFont('Consolas', 10))
        selector.setMinimumWidth(90)
        selector.addItems(["None", "Always", "Turn", "Variable", "Scene Count", "Setting", "Location", "Region", "World"])
        row_layout.addWidget(selector)
        geography_widget = QWidget()
        geography_layout = QHBoxLayout(geography_widget)
        geography_layout.setContentsMargins(0, 0, 0, 0)
        geography_layout.setSpacing(0)
        geography_label = QLabel("Name:")
        geography_label.setObjectName("GeographyNameLabel")
        geography_label.setFont(QFont('Consolas', 10))
        geography_editor = QLineEdit()
        geography_editor.setObjectName("GeographyNameEditor")
        geography_editor.setFont(QFont('Consolas', 9))
        geography_editor.setPlaceholderText("Enter name to match")
        geography_editor.setMinimumWidth(150)
        geography_layout.addWidget(geography_label)
        geography_layout.addWidget(geography_editor)
        geography_layout.addStretch()
        geography_widget.setVisible(False)
        row_layout.addWidget(geography_widget)
        turn_label = QLabel("Turn #:")
        turn_label.setObjectName("ConditionTurnLabel")
        turn_label.setFont(QFont('Consolas', 10))
        turn_label.setVisible(False)
        turn_spinner = QSpinBox()
        turn_spinner.setObjectName("ConditionTurnSpinner")
        turn_spinner.setFont(QFont('Consolas', 10))
        turn_spinner.setRange(1, 999)
        turn_spinner.setMinimumWidth(50)
        turn_spinner.setVisible(False)
        row_layout.addWidget(turn_label)
        turn_op_selector = QComboBox()
        turn_op_selector.setObjectName("TurnCondOpSelector")
        turn_op_selector.setFont(QFont('Consolas', 9))
        turn_op_selector.setMinimumWidth(60)
        turn_op_selector.addItems(["==", "!=", ">", "<", ">=", "<="])
        turn_op_selector.setVisible(False)
        row_layout.addWidget(turn_op_selector)
        row_layout.addWidget(turn_spinner)
        var_widget = QWidget()
        var_layout = QHBoxLayout(var_widget)
        var_layout.setContentsMargins(0, 0, 0, 0)
        var_layout.setSpacing(0)
        var_label = QLabel("Variable:")
        var_label.setObjectName("ConditionVarLabel")
        var_label.setFont(QFont('Consolas', 10))
        var_editor = QLineEdit()
        var_editor.setObjectName("ConditionVarNameEditor")
        var_editor.setFont(QFont('Consolas', 9))
        var_editor.setPlaceholderText("Name")
        var_editor.setMinimumWidth(70)
        op_selector = QComboBox()
        op_selector.setObjectName("VariableCondOpSelector")
        op_selector.setFont(QFont('Consolas', 9))
        op_selector.setMinimumWidth(70)
        op_selector.addItems(["==", "!=", ">", "<", ">=", "<=", "exists", "not exists", "contains", "not contains"])
        val_label = QLabel("Value:")
        val_label.setObjectName("ConditionValLabel")
        val_label.setFont(QFont('Consolas', 10))
        val_editor = QLineEdit()
        val_editor.setObjectName("ConditionVarValueEditor")
        val_editor.setFont(QFont('Consolas', 9))
        val_editor.setPlaceholderText("Value")
        val_editor.setMinimumWidth(70)
        var_layout.addWidget(var_label)
        var_layout.addWidget(var_editor)
        var_layout.addWidget(op_selector)
        var_layout.addWidget(val_label)
        var_layout.addWidget(val_editor)
        var_layout.addStretch()
        var_widget.setVisible(False)
        var_scope_widget = QWidget()
        var_scope_widget.setObjectName("ConditionVarScopeWidget")
        var_scope_layout = QHBoxLayout(var_scope_widget)
        var_scope_layout.setContentsMargins(5, 0, 0, 0)
        var_scope_layout.setSpacing(3)
        scope_label = QLabel("Scope:")
        scope_label.setObjectName("ConditionScopeLabel")
        scope_label.setFont(QFont('Consolas', 9))
        scope_global_radio = QRadioButton("Global")
        scope_global_radio.setObjectName("ConditionVarScopeGlobalRadio")
        scope_global_radio.setFont(QFont('Consolas', 9))
        scope_global_radio.setChecked(True)
        scope_character_radio = QRadioButton("Character")
        scope_character_radio.setObjectName("ConditionVarScopeCharacterRadio")
        scope_character_radio.setFont(QFont('Consolas', 9))
        scope_player_radio = QRadioButton("Player")
        scope_player_radio.setObjectName("ConditionVarScopePlayerRadio")
        scope_player_radio.setFont(QFont('Consolas', 9))
        scope_setting_radio = QRadioButton("Setting")
        scope_setting_radio.setObjectName("ConditionVarScopeSettingRadio")
        scope_setting_radio.setFont(QFont('Consolas', 9))
        var_scope_group = QButtonGroup(var_scope_widget)
        var_scope_group.addButton(scope_global_radio)
        var_scope_group.addButton(scope_character_radio)
        var_scope_group.addButton(scope_player_radio)
        var_scope_group.addButton(scope_setting_radio)
        var_scope_layout.addWidget(scope_label)
        var_scope_layout.addWidget(scope_global_radio)
        var_scope_layout.addWidget(scope_character_radio)
        var_scope_layout.addWidget(scope_player_radio)
        var_scope_layout.addWidget(scope_setting_radio)
        var_scope_layout.addStretch()
        var_scope_widget.setVisible(False)
        row_layout.addWidget(var_widget)
        row_layout.addWidget(var_scope_widget)
        scene_count_widget = QWidget()
        scene_count_layout = QHBoxLayout(scene_count_widget)
        scene_count_layout.setContentsMargins(0, 0, 0, 0)
        scene_count_layout.setSpacing(0)
        scene_count_label = QLabel("Scene #:")
        scene_count_label.setObjectName("ConditionSceneCountLabel")
        scene_count_label.setFont(QFont('Consolas', 10))
        scene_op_selector = QComboBox()
        scene_op_selector.setObjectName("SceneCondOpSelector")
        scene_op_selector.setFont(QFont('Consolas', 9))
        scene_op_selector.setMinimumWidth(60)
        scene_op_selector.addItems(["==", "!=", ">", "<", ">=", "<="])
        scene_count_spinner = QSpinBox()
        scene_count_spinner.setObjectName("ConditionSceneCountSpinner")
        scene_count_spinner.setFont(QFont('Consolas', 10))
        scene_count_spinner.setRange(1, 9999)
        scene_count_spinner.setMinimumWidth(50)
        scene_count_layout.addWidget(scene_count_label)
        scene_count_layout.addWidget(scene_op_selector)
        scene_count_layout.addWidget(scene_count_spinner)
        scene_count_layout.addStretch()
        scene_count_widget.setVisible(False)
        row_layout.addWidget(scene_count_widget)
        add_btn = QPushButton("+")
        add_btn.setObjectName("AddConditionButton")
        remove_btn = QPushButton("−")
        remove_btn.setObjectName("RemoveConditionButton")
        row_layout.addWidget(add_btn)
        row_layout.addWidget(remove_btn)

        def update_row_widgets():
            is_turn = (selector.currentText() == "Turn")
            is_var = (selector.currentText() == "Variable")
            is_scene_count = (selector.currentText() == "Scene Count")
            is_geography = selector.currentText() in ["Setting", "Location", "Region", "World"]
            rule_applies_to_character = False
            parent = row_widget
            rules_manager_widget = None
            while parent is not None:
                if parent.findChild(QLineEdit, "RuleIdEditor"):
                    rules_manager_widget = parent
                    break
                parent = parent.parentWidget()
            if rules_manager_widget:
                applies_to_character_radio = rules_manager_widget.findChild(QRadioButton, "AppliesToCharacterRadio")
                if applies_to_character_radio:
                    rule_applies_to_character = applies_to_character_radio.isChecked()
                else:
                    print("Debug: Found rules_manager_widget but not AppliesToCharacterRadio within it.")
            else:
                 pass
            turn_label.setVisible(is_turn)
            turn_spinner.setVisible(is_turn)
            var_widget.setVisible(is_var)
            scene_count_widget.setVisible(is_scene_count)
            geography_widget.setVisible(is_geography)
            var_scope_widget.setVisible(is_var)
            turn_op_selector.setVisible(is_turn)
            if is_var:
                op = op_selector.currentText()
                needs_value = op not in ["exists", "not exists"]
                val_label.setVisible(needs_value)
                val_editor.setVisible(needs_value)
            else:
                val_label.setVisible(False)
                val_editor.setVisible(False)
        selector.currentIndexChanged.connect(update_row_widgets)
        op_selector.currentIndexChanged.connect(update_row_widgets)
        def add_row():
            add_condition_row()
            update_all_condition_buttons()
        def remove_row():
            if len(condition_rows) > 1:
                idx_to_remove = -1
                for idx, r_data in enumerate(condition_rows):
                    if r_data['widget'] is row_widget:
                        idx_to_remove = idx
                        break
                if idx_to_remove != -1:
                    row_to_remove_data = condition_rows.pop(idx_to_remove)
                    widget_to_remove = row_to_remove_data['widget']
                    if is_valid_widget(widget_to_remove):
                        conditions_layout.removeWidget(widget_to_remove)
                        widget_to_remove.deleteLater()
                        QApplication.processEvents()
                        for i in range(conditions_layout.count()):
                            item = conditions_layout.itemAt(i)
                            if item and is_valid_widget(item.widget()):
                                remaining_row_widget = item.widget()
                                label = remaining_row_widget.findChild(QLabel, "ConditionLabel")
                                if is_valid_widget(label):
                                    label.setText(f"Condition {i+1}:")
                        
                        update_all_condition_buttons()
                        
                    else:
                        pass
                else:
                    pass
        add_btn.clicked.connect(add_row)
        remove_btn.clicked.connect(remove_row)
        if data:
            selector.setCurrentText(data.get('type', 'None'))
            if data.get('type') == 'Turn':
                turn_spinner.setValue(data.get('turn', 1))
            if data.get('type') == 'Variable':
                var_editor.setText(data.get('variable', ''))
                op_selector.setCurrentText(data.get('operator', '=='))
                val_editor.setText(data.get('value', ''))
                scope = data.get('variable_scope', 'Global')
                scope_global_radio.setChecked(scope == 'Global')
                scope_character_radio.setChecked(scope == 'Character')
                scope_setting_radio.setChecked(scope == 'Setting')
            if data.get('type') == 'Scene Count':
                scene_op_selector.setCurrentText(data.get('operator', '=='))
                scene_count_spinner.setValue(data.get('value', 1))
        row = {
            'widget': row_widget,
            'label': label,
            'selector': selector,
            'turn_spinner': turn_spinner,
            'var_editor': var_editor,
            'op_selector': op_selector,
            'val_editor': val_editor,
            'add_btn': add_btn,
            'remove_btn': remove_btn,
            'scene_count_widget': scene_count_widget,
            'scene_op_selector': scene_op_selector,
            'scene_count_spinner': scene_count_spinner,
            'var_scope_widget': var_scope_widget,
            'scope_global_radio': scope_global_radio,
            'scope_character_radio': scope_character_radio,
            'scope_setting_radio': scope_setting_radio,
            'geography_widget': geography_widget,
            'geography_editor': geography_editor,
            'update_row_widgets_func': update_row_widgets
        }
        condition_rows.append(row)
        conditions_layout.addWidget(row_widget)
        update_row_widgets()
        row_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        return row
    
    def add_condition_row(data=None):
        row = create_condition_row(data=data)
        update_all_condition_buttons()
    add_condition_row()
    rule_details_layout.addWidget(conditions_container)
    scope_layout = QHBoxLayout()
    scope_label = QLabel("Scope:")
    scope_label.setObjectName("ScopeLabel")
    scope_label.setFont(QFont('Consolas', 12))
    scope_layout.addWidget(scope_label)
    last_exchange_radio = QRadioButton("Last Exchange")
    last_exchange_radio.setObjectName("LastExchangeRadio")
    last_exchange_radio.setFont(QFont('Consolas', 11))
    last_exchange_radio.setChecked(True)
    last_exchange_radio.setToolTip("Check condition against only the last user message and assistant response.")
    full_convo_radio = QRadioButton("Full Conversation")
    full_convo_radio.setObjectName("FullConversationRadio")
    full_convo_radio.setFont(QFont('Consolas', 11))
    user_message_radio = QRadioButton("User Message")
    user_message_radio.setObjectName("UserMessageRadio")
    user_message_radio.setFont(QFont('Consolas', 11))
    user_message_radio.setToolTip("Check condition against only the last user message.")
    user_message_radio.setChecked(True) 
    llm_reply_radio = QRadioButton("LLM Reply")
    llm_reply_radio.setObjectName("LLMReplyRadio")
    llm_reply_radio.setFont(QFont('Consolas', 11))
    llm_reply_radio.setToolTip("Check condition against the LLM's latest reply (runs after inference).")
    convo_llm_reply_radio = QRadioButton("Conversation+LLM Reply")
    convo_llm_reply_radio.setObjectName("ConvoLLMReplyRadio")
    convo_llm_reply_radio.setFont(QFont('Consolas', 11))
    convo_llm_reply_radio.setToolTip("Check condition against both conversation history AND the LLM's latest reply.")
    scope_group = QButtonGroup(tab_content_widget)
    scope_group.addButton(last_exchange_radio)
    scope_group.addButton(full_convo_radio)
    scope_group.addButton(user_message_radio)
    scope_group.addButton(llm_reply_radio)
    scope_group.addButton(convo_llm_reply_radio)
    scope_layout.addWidget(last_exchange_radio)
    scope_layout.addWidget(full_convo_radio)
    scope_layout.addWidget(user_message_radio)
    scope_layout.addWidget(llm_reply_radio)
    scope_layout.addWidget(convo_llm_reply_radio)
    rule_details_layout.addLayout(scope_layout)
    condition_editor = QTextEdit()
    condition_editor.setObjectName("ConditionEditor")
    condition_editor.setFont(QFont('Consolas', 10))
    condition_editor.setMaximumHeight(80)
    rule_details_layout.addWidget(condition_editor)
    model_layout = QHBoxLayout()
    model_label = QLabel("Model:")
    model_label.setObjectName("ModelLabel")
    model_label.setFont(QFont('Consolas', 12))
    model_layout.addWidget(model_label)
    model_editor = QLineEdit()
    model_editor.setObjectName("ModelEditor")
    model_editor.setFont(QFont('Consolas', 10))
    model_editor.setPlaceholderText("Leave empty to use current model (e.g., openai/gpt-4o-mini)")
    model_layout.addWidget(model_editor)
    rule_details_layout.addLayout(model_layout)
    rule_details_layout.addStretch(1)
    rule_actions_widget = QWidget()
    rule_actions_layout = QVBoxLayout(rule_actions_widget)
    rule_actions_layout.setContentsMargins(0, 5, 0, 0)
    rule_actions_layout.setSpacing(5)
    tag_actions_container = QWidget()
    tag_actions_container.setObjectName("TagActionsContainer")
    tag_actions_layout = QVBoxLayout(tag_actions_container)
    tag_actions_layout.setContentsMargins(0, 0, 0, 0)
    pairs_header = QLabel("Tag/Action Pairs:")
    pairs_header.setObjectName("PairsHeader")
    pairs_header.setFont(QFont('Consolas', 12, QFont.Bold))
    tag_actions_layout.addWidget(pairs_header)
    pairs_container = QWidget(tag_actions_container)
    pairs_container.setObjectName("PairsContainer")
    pairs_layout = QVBoxLayout(pairs_container)
    pairs_layout.setSpacing(10)
    pairs_layout.setContentsMargins(5, 5, 5, 5)
    tag_actions_layout.addWidget(pairs_container)
    add_pair_button = QPushButton("Add Tag +")
    add_pair_button.setObjectName("AddPairButton")
    add_pair_button.setFont(QFont('Consolas', 10))
    add_pair_button.setMaximumWidth(250)
    add_pair_button_row = QHBoxLayout()
    add_pair_button_row.addStretch(1)
    add_pair_button_row.addWidget(add_pair_button)
    add_pair_button_row.addStretch(1)
    tag_actions_layout.addLayout(add_pair_button_row)
    rule_actions_layout.addWidget(tag_actions_container)
    tag_action_pairs = []

    def add_new_pair(tab_data, target_layout, add_default_action_row=True):
        tag_action_pairs = tab_data.get('tag_action_pairs')
        if tag_action_pairs is None:
            tag_action_pairs = []
            tab_data['tag_action_pairs'] = tag_action_pairs
        pair_data = create_pair_widget(tab_data)
        tag_action_pairs.append(pair_data)
        if target_layout is not None and isinstance(target_layout, QVBoxLayout):
            target_layout.addWidget(pair_data['widget'])
        else:
            if pair_data in tag_action_pairs:
                 tag_action_pairs.remove(pair_data)
            return None
        if add_default_action_row:
            pair_actions_container = pair_data['widget'].findChild(QWidget)
            pair_actions_layout = None
            if pair_actions_container:
                pair_actions_layout = pair_actions_container.layout()
            else:
                pair_actions_layout = pair_data['widget'].findChild(QVBoxLayout)
            if 'add_pair_action_row' in pair_data and callable(pair_data['add_pair_action_row']):
                if pair_actions_layout:
                    try:
                        pair_data['add_pair_action_row'](data=None, workflow_data_dir=tab_data.get('workflow_data_dir'))
                    except Exception:
                        pass
                else:
                    print("Warning: Could not find valid action layout inside new pair widget.")
            else:
                print("Warning: Could not find 'add_pair_action_row' function in pair_data for new pair.")
        return pair_data
    unified_content_layout.addWidget(rule_details_widget, 0)
    unified_content_layout.addWidget(rule_actions_widget, 0)
    rules_manager_layout.addWidget(unified_scroll_area)
    rules_manager_widget.setLayout(rules_manager_layout)
    rules_toggle_manager = RulesToggleManager(
        theme_colors=tab_settings,
        standard_rules_widget=rules_manager_widget
    )
    center_stack = QStackedWidget()
    center_stack.setObjectName("CenterPanelStack")
    center_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    center_stack.addWidget(conversation_widget)
    worldbuilding_widget = QWidget()
    worldbuilding_layout = QHBoxLayout(worldbuilding_widget)
    worldbuilding_layout.setContentsMargins(0, 0, 0, 0)
    worldbuilding_layout.setSpacing(0)
    from scribe.agent_chat import AgentPanel
    scribe_widget = AgentPanel(parent=self, theme_colors=tab_settings)
    worldbuilding_layout.addWidget(scribe_widget, 1)
    notes_manager_widget = NotesManagerWidget(theme_colors=tab_settings, tab_settings_file=final_tab_settings_file)
    worldbuilding_layout.addWidget(notes_manager_widget, 1)
    center_stack.addWidget(worldbuilding_widget)
    notes_manager_widget_standalone = NotesManagerWidget(theme_colors=tab_settings, tab_settings_file=final_tab_settings_file)
    center_stack.addWidget(notes_manager_widget_standalone)
    setting_manager_widget = SettingManagerWidget(workflow_data_dir=tab_dir, theme_colors=tab_settings)
    center_stack.addWidget(setting_manager_widget)
    time_manager_widget = TimeManager(theme_colors=tab_settings, workflow_data_dir=tab_dir)
    center_stack.addWidget(time_manager_widget)
    actor_manager_widget = ActorManagerWidget(tab_dir)
    center_stack.addWidget(actor_manager_widget)
    center_stack.addWidget(rules_toggle_manager)
    keyword_manager_widget = KeywordManagerWidget(theme_colors=tab_settings, workflow_data_dir=tab_dir)
    center_stack.addWidget(keyword_manager_widget)
    inventory_manager_widget = InventoryManagerWidget(workflow_data_dir=tab_dir)
    center_stack.addWidget(inventory_manager_widget)
    random_generators_widget = RandomGeneratorsWidget(workflow_data_dir=tab_dir, theme_settings=tab_settings)
    center_stack.addWidget(random_generators_widget)
    start_conditions_manager_widget = StartConditionsManagerWidget(
        theme_colors=tab_settings,
        system_context_file=final_system_context_file,
        variables_file=final_variables_file
    )
    center_stack.addWidget(start_conditions_manager_widget)
    center_vertical_splitter.addWidget(top_splitter_widget)
    center_vertical_splitter.addWidget(center_stack)
    center_vertical_splitter.addWidget(bottom_splitter_widget)
    main_splitter.addWidget(left_splitter_widget)
    main_splitter.addWidget(center_vertical_splitter)
    main_splitter.addWidget(right_splitter_instance)
    main_splitter.setStretchFactor(0, 0)
    main_splitter.setStretchFactor(1, 1)
    main_splitter.setStretchFactor(2, 0)

    def on_main_splitter_moved(pos, index):
        if hasattr(self, 'hover_message_sound') and self.hover_message_sound:
            sizes = main_splitter.sizes()
            if index == 1 and len(sizes) >= 2:
                left_size = sizes[0]
                if not hasattr(main_splitter, '_prev_left_size'):
                    main_splitter._prev_left_size = left_size
                    return
                prev_left_size = main_splitter._prev_left_size
                if (prev_left_size == 0 and left_size > 0) or (prev_left_size > 0 and left_size == 0):
                    try:
                        self.hover_message_sound.play()
                    except Exception as e:
                        print(f"Error playing hover_message_sound for left splitter: {e}")
                if prev_left_size > 0 and left_size == 0:
                    try:
                        if ChatMessageWidget._selected_widget:
                            tab_data['_remembered_selected_message'] = ChatMessageWidget._selected_widget
                            if hasattr(ChatMessageWidget._selected_widget, 'deselect'):
                                ChatMessageWidget._selected_widget.deselect()
                            ChatMessageWidget._selected_widget = None
                        else:
                            tab_data['_remembered_selected_message'] = None
                    except Exception as e:
                        print(f"Error handling chat message selection when left splitter closed: {e}")
                elif prev_left_size == 0 and left_size > 0:
                    try:
                        remembered_message = tab_data.get('_remembered_selected_message')
                        if remembered_message and hasattr(remembered_message, 'select'):
                            try:
                                _ = remembered_message.objectName()
                                remembered_message.select(silent=True)
                            except RuntimeError:
                                tab_data['_remembered_selected_message'] = None
                    except Exception as e:
                        print(f"Error restoring chat message selection when left splitter opened: {e}")
                main_splitter._prev_left_size = left_size
            elif index == 2 and len(sizes) >= 3:
                right_size = sizes[2]
                if not hasattr(main_splitter, '_prev_right_size'):
                    main_splitter._prev_right_size = right_size
                    return
                prev_right_size = main_splitter._prev_right_size
                if (prev_right_size == 0 and right_size > 0) or (prev_right_size > 0 and right_size == 0):
                    try:
                        self.hover_message_sound.play()
                    except Exception as e:
                        print(f"Error playing hover_message_sound for right splitter: {e}")
                    try:
                        if hasattr(output_field, 'force_rewrap_all_messages'):
                            QTimer.singleShot(100, output_field.force_rewrap_all_messages)
                    except Exception as e:
                        print(f"Error forcing chat message rewrap: {e}")
                main_splitter._prev_right_size = right_size
    main_splitter.splitterMoved.connect(on_main_splitter_moved)
    tab_layout.addWidget(main_splitter)

    def on_notes_saved(notes_text):
        if tab_data and 'settings' in tab_data:
            tab_data['settings']['dev_notes'] = notes_text
    notes_manager_widget.notes_saved.connect(on_notes_saved)
    notes_manager_widget_standalone.notes_saved.connect(on_notes_saved)

    def update_top_splitter_visibility(checked):
        if not tab_data or not top_splitter_widget or not input_field:
            if top_splitter_widget:
                top_splitter_widget.setVisible(False)
            if right_splitter_instance:
                right_splitter_instance.setVisible(False)
            return
        is_actively_showing_intro = tab_data.get('_is_showing_intro', False)
        if is_actively_showing_intro:
            top_splitter_widget.setVisible(False)
            right_splitter_instance.setVisible(False)
            return
        current_input_state = input_field._current_state if hasattr(input_field, '_current_state') else 'normal'
        is_intro_mode_via_input_state = current_input_state in ['intro', 'intro_streaming', 'disabled']
        if is_intro_mode_via_input_state:
            top_splitter_widget.setVisible(False)
            right_splitter_instance.setVisible(False)
            return
        message_roles = output_field.get_message_roles() if hasattr(output_field, 'get_message_roles') else []
        has_ongoing_conversation = any(role in ('user', 'assistant') for role in message_roles)
        if checked and has_ongoing_conversation:
            top_splitter_widget.setVisible(True)
            right_splitter_instance.setVisible(True)
        else:
            top_splitter_widget.setVisible(False)
            right_splitter_instance.setVisible(False)
    left_splitter_widget.live_game_button.toggled.connect(update_top_splitter_visibility)
    top_splitter_widget.setVisible(False)
    right_splitter_instance.setVisible(left_splitter_widget.live_game_button.isChecked())

    def update_center_panel(checked):
        sender = self.sender()
        if not checked:
            return
        if sender == left_splitter_widget.live_game_button:
            center_stack.setCurrentIndex(0)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
        elif sender == left_splitter_widget.notes_button:
            center_stack.setCurrentIndex(1)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(False)
        elif sender == left_splitter_widget.setting_manager_button:
            center_stack.setCurrentIndex(3)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
        elif sender == left_splitter_widget.time_manager_button:
            center_stack.setCurrentIndex(4)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
        elif sender == left_splitter_widget.actor_manager_button:
            center_stack.setCurrentIndex(5)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
        elif sender == left_splitter_widget.rules_button:
            center_stack.setCurrentIndex(6)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
        elif sender == left_splitter_widget.keyword_manager_button:
            center_stack.setCurrentIndex(7)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
        elif sender == left_splitter_widget.inventory_manager_button:
            center_stack.setCurrentIndex(8)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
        elif sender == left_splitter_widget.random_generators_button:
            center_stack.setCurrentIndex(9)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
        elif sender == left_splitter_widget.start_conditions_button:
            center_stack.setCurrentIndex(10)
            if hasattr(left_splitter_widget, 'agent_panel'):
                left_splitter_widget.agent_panel.setVisible(True)
    left_splitter_widget.live_game_button.toggled.connect(update_center_panel)
    left_splitter_widget.notes_button.toggled.connect(update_center_panel)
    left_splitter_widget.setting_manager_button.toggled.connect(update_center_panel)
    left_splitter_widget.time_manager_button.toggled.connect(update_center_panel)
    left_splitter_widget.actor_manager_button.toggled.connect(update_center_panel)
    left_splitter_widget.rules_button.toggled.connect(update_center_panel)
    left_splitter_widget.keyword_manager_button.toggled.connect(update_center_panel)
    left_splitter_widget.inventory_manager_button.toggled.connect(update_center_panel)
    left_splitter_widget.random_generators_button.toggled.connect(update_center_panel)
    left_splitter_widget.start_conditions_button.toggled.connect(update_center_panel)
    center_stack.setCurrentIndex(0)
    if replace_existing_index is not None:
        actual_index = replace_existing_index
        if hasattr(self.tab_widget, 'replaceTab'):
            self.tab_widget.replaceTab(actual_index, tab_content_widget, tab_name)
        else:
            print(f"Warning: replaceTab method not found, using fallback")
            old_widget = self.tab_widget.widget(actual_index)
            if old_widget:
                old_widget.setParent(None)
                old_widget.deleteLater()
            self.tab_widget.removeTab(actual_index)
            self.tab_widget.insertTab(actual_index, tab_content_widget, tab_name)
    else:
        actual_index = self.tab_widget.addTab(tab_content_widget, tab_name)
    input_field.tab_index = actual_index
    add_rule_button.setObjectName(f"add_rule_button_{actual_index}") 
    rules_list.setProperty("tab_index", actual_index)
    rules = []
    crt_overlay = CRTEffectOverlay(tab_content_widget, border_color=tab_settings["base_color"])
    crt_overlay.resize(tab_content_widget.size())
    crt_overlay.raise_()
    initial_crt_enabled = tab_settings.get("crt_enabled", True)
    initial_crt_speed = tab_settings.get("crt_speed", 160)
    crt_overlay.setVisible(initial_crt_enabled)
    crt_overlay.setInterval(initial_crt_speed)
    original_resizeEvent = tab_content_widget.resizeEvent
    
    def patched_resizeEvent(event):
        original_resizeEvent(event)
        try:
            if crt_overlay and tab_content_widget and crt_overlay.isVisible():
                _update_crt_overlay_size()
        except Exception as e:
            print(f"Error in CRT overlay resize: {e}")
    
    def _update_crt_overlay_size():
        try:
            if crt_overlay and tab_content_widget and crt_overlay.isVisible():
                current_size = tab_content_widget.size()
                if current_size.width() > 0 and current_size.height() > 0:
                    crt_overlay.resize(current_size)
                    crt_overlay.raise_()
        except Exception as e:
            print(f"Error updating CRT overlay size: {e}")
    tab_content_widget.resizeEvent = patched_resizeEvent
    original_main_splitter_resizeEvent = main_splitter.resizeEvent

    def main_splitter_patched_resizeEvent(event):
        original_main_splitter_resizeEvent(event)
        try:
            if crt_overlay and tab_content_widget and crt_overlay.isVisible():
                _update_crt_overlay_size()
        except Exception as e:
            print(f"Error in main splitter CRT overlay resize: {e}")
    main_splitter.resizeEvent = main_splitter_patched_resizeEvent
    tab_data = {
        'widget': tab_content_widget,
        'crt_overlay': crt_overlay,
        'content_widget': tab_content_widget,
        'splitter': main_splitter,
        'vertical_splitter': center_vertical_splitter,
        'top_splitter': top_splitter_widget,
        'bottom_splitter': bottom_splitter_widget,
        'left_splitter': left_splitter_widget,
        'output': output_field,
        'system_context_editor': None,
        'context': [],
        'memory': AgentMemory(notes_file=final_notes_file),
        'log_file': final_log_file,
        'notes_file': final_notes_file,
        'context_file': final_context_file,
        'system_context_file': final_system_context_file,
        'thought_rules_file': thought_rules_file,
        'thought_rules': rules,
        'rules_list': rules_list,
        'rules_toggle_manager': rules_toggle_manager,
        'timer_rules_widget': rules_toggle_manager.get_timer_rules_widget(),
        'name': tab_name,
        'purpose': purpose or "",
        'meta_strategies': [],
        'turn_count': 1,
        'variables_file': final_variables_file,
        'description_editor': description_editor,
        'input': input_field,
        'conditions_container': conditions_container,
        'condition_rows': condition_rows,
        'pairs_container': pairs_container, 
        'pairs_layout': pairs_layout,
        'tag_action_pairs': tag_action_pairs,
        'add_new_pair': add_new_pair,
        'add_condition_row': add_condition_row,
        'tab_index': actual_index,
        'id': f"tab_{actual_index}",
        'tab_settings_file': final_tab_settings_file,
        'settings': tab_settings,
        'rules_dir': rules_dir,
        'scene_number': 1,
        'right_splitter': right_splitter_instance,
        'actor_manager_widget': actor_manager_widget,
        'start_conditions_manager_widget': start_conditions_manager_widget,
        'random_generators_widget': random_generators_widget,
        'workflow_data_dir': tab_dir,
        'allow_narrator_post_after_change': True,
        'notes_manager_widget': notes_manager_widget,
        '_is_showing_intro': True,
        '_remembered_selected_message': None,
        'loaded': not skip_heavy_loading
    }
    output_field.tab_data = tab_data
    if replace_existing_index is not None:
        if replace_existing_index < len(self.tabs_data):
            old_tab_data = self.tabs_data[replace_existing_index]
            if old_tab_data and isinstance(old_tab_data, dict):
                tab_data['workflow_data_dir'] = old_tab_data.get('workflow_data_dir', tab_dir)
        self.tabs_data[replace_existing_index] = tab_data
    else:
        if actual_index >= len(self.tabs_data):
            self.tabs_data.extend([None] * (actual_index + 1 - len(self.tabs_data)))
        self.tabs_data[actual_index] = tab_data

    if os.path.exists(final_system_context_file):
        try:
            pass
        except Exception as e:
            print(f"Error loading system context for new tab: {e}")
    loaded_rules = []
    if os.path.exists(rules_dir):
        order_filepath = os.path.join(rules_dir, "_rules_order.json")
        rule_files = {fname: os.path.join(rules_dir, fname)
                      for fname in os.listdir(rules_dir) if fname.endswith('_rule.json')}
        ordered_rule_ids = []
        if os.path.exists(order_filepath):
            try:
                with open(order_filepath, 'r', encoding='utf-8') as f:
                    ordered_rule_ids = json.load(f)
            except Exception as e:
                print(f"Error loading rule order file {order_filepath}: {e}. Falling back to directory scan.")
                ordered_rule_ids = []
        if ordered_rule_ids:
            loaded_rules_map = {}
            valid_ordered_ids = []
            for rule_id in ordered_rule_ids:
                filename = f"{rule_id}_rule.json"
                fpath = rule_files.get(filename)
                if fpath and os.path.exists(fpath):
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            rule = json.load(f)
                            rule.setdefault('scope', 'last_exchange')
                            loaded_rules_map[rule_id] = rule
                            valid_ordered_ids.append(rule_id)
                    except Exception as e:
                        print(f"Error loading rule file {fpath} specified in order file: {e}")
            loaded_rules = [loaded_rules_map[rule_id] for rule_id in valid_ordered_ids]
            found_rule_files = set(loaded_rules_map.keys())
            all_rule_ids_from_files = {fname.replace('_rule.json', '') for fname in rule_files.keys()}
            orphaned_rules = all_rule_ids_from_files - found_rule_files
            if orphaned_rules:
                needs_resave = False
                for rule_id in sorted(list(orphaned_rules)):
                     filename = f"{rule_id}_rule.json"
                     fpath = rule_files.get(filename)
                     if fpath:
                         try:
                             with open(fpath, 'r', encoding='utf-8') as f:
                                 rule = json.load(f)
                                 rule.setdefault('scope', 'last_exchange')
                                 loaded_rules.append(rule)
                                 valid_ordered_ids.append(rule_id)
                                 needs_resave = True
                         except Exception as e:
                             print(f"Error loading orphaned rule file {fpath}: {e}")
                if needs_resave:
                    try:
                        with open(order_filepath, 'w', encoding='utf-8') as f:
                            json.dump(valid_ordered_ids, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        print(f"Error resaving rule order file: {e}")
        else:
            rule_ids_loaded = []
            sorted_filenames = sorted(rule_files.keys())
            for fname in sorted_filenames:
                fpath = rule_files[fname]
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        rule = json.load(f)
                        rule.setdefault('scope', 'last_exchange')
                        loaded_rules.append(rule)
                        rule_id = rule.get('id')
                        if rule_id:
                             rule_ids_loaded.append(rule_id)
                        else:
                             fallback_id = fname.replace('_rule.json', '')
                             print(f"Warning: Rule in {fname} missing 'id'. Using filename '{fallback_id}' for ordering.")
                             rule_ids_loaded.append(fallback_id)
                except Exception as e:
                    print(f"Error loading rule from {fpath} during fallback scan: {e}")
            if loaded_rules:
                 try:
                     with open(order_filepath, 'w', encoding='utf-8') as f:
                         json.dump(rule_ids_loaded, f, indent=2, ensure_ascii=False)
                 except Exception as e:
                     print(f"Error saving initial rule order file: {e}")
    if loaded_rules:
        if 'tab_data' not in locals() or not isinstance(tab_data, dict):
             print("Error: tab_data not properly initialized before rule loading.")
        else:
             tab_data['thought_rules'] = loaded_rules
             if hasattr(self, '_update_rules_display') and 'rules_list' in locals():
                 self._update_rules_display(loaded_rules, rules_list)
    else:
         if 'tab_data' in locals() and isinstance(tab_data, dict):
              tab_data['thought_rules'] = []
    timer_rules = _load_timer_rules(self, actual_index)
    if timer_rules and tab_data['timer_rules_widget']:
        tab_data['timer_rules_widget'].load_timer_rules(timer_rules)
    add_pair_button.clicked.connect(lambda checked=False, t_data=tab_data: add_new_pair(t_data, t_data['pairs_layout'], True))
    add_new_pair(tab_data, tab_data['pairs_layout'], True)
    add_rule_button.clicked.connect(lambda checked=False, idx=actual_index: _add_rule(
        self, idx, rule_id_editor, condition_editor, None, None, None, None, last_exchange_radio.isChecked(), condition_rows[0]['selector'], rules_list
    ))
    delete_rule_button.clicked.connect(lambda checked=False, idx=actual_index: _delete_selected_rule(self, idx, rules_list))
    clear_rule_button.clicked.connect(lambda checked=False, idx=actual_index: self._clear_rule_form(idx))
    rules_list.itemSelectionChanged.connect(lambda: _load_selected_rule(
        self, actual_index, rules_list
    ))
    move_up_button.clicked.connect(lambda checked=False, idx=actual_index, rl=rules_list: (self.sort_sound.play() if hasattr(self, 'sort_sound') and self.sort_sound else None, _move_rule_up(self, idx, rl)))
    move_down_button.clicked.connect(lambda checked=False, idx=actual_index, rl=rules_list: (self.sort_sound.play() if hasattr(self, 'sort_sound') and self.sort_sound else None, _move_rule_down(self, idx, rl)))
    duplicate_rule_button.clicked.connect(lambda checked=False, idx=actual_index, rl=rules_list: _duplicate_selected_rule(self, idx, rl))
    refresh_rules_button.clicked.connect(lambda checked=False, idx=actual_index, rl=rules_list: _refresh_rules_from_json(self, idx, rl))
    
    def filter_rules(text):
        tab_data = self.tabs_data[actual_index] if actual_index < len(self.tabs_data) else None
        if tab_data and 'thought_rules' in tab_data:
            self._update_rules_display(tab_data['thought_rules'], rules_list)
    
    rules_filter_input.textChanged.connect(filter_rules)
    if top_splitter_widget:
        top_splitter_widget.setVisible(False)
    if not skip_heavy_loading:
        self.load_conversation_for_tab(actual_index)
        if replace_existing_index is None:
            self.tab_widget.setCurrentIndex(actual_index)
        
    self._update_turn_counter_display()
    applies_to_narrator_radio = tab_content_widget.findChild(QRadioButton, "AppliesToNarratorRadio")
    if applies_to_narrator_radio:
        if hasattr(self, '_handle_applies_to_toggled') and callable(self._handle_applies_to_toggled):
            try:
                applies_to_narrator_radio.toggled.connect(
                    lambda checked, t_data=tab_data: self._handle_applies_to_toggled(t_data)
                )
            except Exception as e:
                print(f"Error connecting AppliesToNarratorRadio signal for tab {actual_index}: {e}")

    def update_crt_border_color():
        if 'crt_overlay' in tab_data and 'settings' in tab_data:
            base_color = tab_data['settings'].get('base_color', "#00FF66")
            tab_data['crt_overlay'].setBorderColor(base_color)
    if hasattr(self, '_apply_theme_for_tab'):
        old_apply_theme = self._apply_theme_for_tab
        def wrapped_apply_theme(tab_index):
            result = old_apply_theme(tab_index)
            if tab_index < len(self.tabs_data) and self.tabs_data[tab_index]:
                tab_data = self.tabs_data[tab_index]
                if 'crt_overlay' in tab_data and 'settings' in tab_data:
                    base_color = tab_data['settings'].get('base_color', "#00FF66")
                    tab_data['crt_overlay'].setBorderColor(base_color)
            return result
        self._apply_theme_for_tab = wrapped_apply_theme
    def update_input_box_state(tab_data):
        variables_path = tab_data.get('variables_file')
        input_widget = tab_data['input']
        state = 'normal'
        if variables_path and os.path.exists(variables_path):
            try:
                with open(variables_path, 'r', encoding='utf-8') as f:
                    variables = json.load(f)
                if variables.get('blinkingPlayerInputBox', False):
                    state = 'blinking'
                elif variables.get('disablePlayerInputBox', False):
                    state = 'disabled'
            except Exception as e:
                print(f"Error loading variables.json: {e}")
        input_widget.set_input_state(state)
    update_input_box_state(tab_data)
    wrapped_apply_theme(actual_index)
    if top_splitter_widget:
        top_splitter_widget.setVisible(False)
    if not skip_heavy_loading and replace_existing_index is None:
        self._show_introduction(actual_index)
    if hasattr(self, 'setting_manager_widget') and self.setting_manager_widget:
        self.setting_manager_widget.update_workflow_data_dir(self.workflow_data_dir)
    try:
        ensure_player_in_origin_setting(tab_dir)
    except Exception as e:
        print(f"[ERROR] Failed to run ensure_player_in_origin_setting after creating new workflow: {e}")
        QMessageBox.warning(self, "Player Placement Check Failed", 
                            f"An error occurred while checking player placement in settings:\n{e}")
    if hasattr(self, 'actor_manager_widget') and self.actor_manager_widget:
        current_tab_index = self.tab_widget.currentIndex()
        if 0 <= current_tab_index < len(self.tabs_data):
            target_tab_data = self.tabs_data[current_tab_index]
            if target_tab_data and 'actor_manager_widget' in target_tab_data:
                target_tab_data['actor_manager_widget'].update_workflow_data_dir(tab_dir)
    update_top_splitter_location_text(tab_data)
    return actual_index
