import os
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QLineEdit, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QListWidget, QListWidgetItem, QScrollArea, QSizePolicy,
    QRadioButton, QFormLayout, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QFont

class TimerRulesWidget(QWidget):
    
    def __init__(self, theme_colors, parent=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.setObjectName("TimerRulesContainer")
        self._timer_rules = []
        self._init_ui()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        list_controls_widget = QWidget()
        list_controls_widget.setObjectName("TimerRulesListControls")
        list_controls_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        list_controls_layout = QVBoxLayout(list_controls_widget)
        list_controls_layout.setContentsMargins(0, 0, 0, 0)
        list_controls_layout.setSpacing(5)
        filter_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setObjectName("TimerRulesFilterInput")
        self.filter_input.setPlaceholderText("Filter timer rules...")
        self.filter_input.setMaximumHeight(22)
        filter_layout.addWidget(self.filter_input)
        self.add_rule_button = QPushButton("+")
        self.add_rule_button.setObjectName("TimerRuleAddButton")
        self.add_rule_button.setFixedWidth(30)
        self.add_rule_button.setFocusPolicy(Qt.NoFocus)
        self.add_rule_button.setToolTip("Add new timer rule")
        self.remove_rule_button = QPushButton("-")
        self.remove_rule_button.setObjectName("TimerRuleRemoveButton")
        self.remove_rule_button.setFixedWidth(30)
        self.remove_rule_button.setFocusPolicy(Qt.NoFocus)
        self.remove_rule_button.setToolTip("Remove selected timer rule")
        self.refresh_rules_button = QPushButton("↻")
        self.refresh_rules_button.setObjectName("TimerRuleRefreshButton")
        self.refresh_rules_button.setFixedWidth(30)
        self.refresh_rules_button.setFocusPolicy(Qt.NoFocus)
        self.refresh_rules_button.setToolTip("Refresh timer rules from JSON files")
        filter_layout.addWidget(self.add_rule_button)
        filter_layout.addWidget(self.remove_rule_button)
        filter_layout.addWidget(self.refresh_rules_button)
        list_controls_layout.addLayout(filter_layout)
        rules_area_layout = QHBoxLayout()
        rules_area_layout.setSpacing(5)
        self.rules_list = QListWidget()
        self.rules_list.setObjectName("TimerRulesList")
        self.rules_list.setAlternatingRowColors(True)
        self.rules_list.setMinimumHeight(100)
        self.rules_list.setMaximumHeight(150)
        self.rules_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.rules_list.setFocusPolicy(Qt.NoFocus)
        rules_area_layout.addWidget(self.rules_list, 1)
        rule_buttons_layout = QVBoxLayout()
        rule_buttons_layout.setSpacing(3)
        rule_buttons_layout.setAlignment(Qt.AlignTop)
        move_up_button = QPushButton("↑")
        move_up_button.setObjectName("TimerRuleMoveUpButton")
        move_up_button.setToolTip("Move selected rule up")
        move_up_button.setFixedSize(25, 25)
        move_up_button.setFocusPolicy(Qt.NoFocus)
        rule_buttons_layout.addWidget(move_up_button)
        move_down_button = QPushButton("↓")
        move_down_button.setObjectName("TimerRuleMoveDownButton")
        move_down_button.setToolTip("Move selected rule down")
        move_down_button.setFixedSize(25, 25)
        move_down_button.setFocusPolicy(Qt.NoFocus)
        rule_buttons_layout.addWidget(move_down_button)
        rules_area_layout.addLayout(rule_buttons_layout)
        list_controls_layout.addLayout(rules_area_layout)
        id_layout = QHBoxLayout()
        id_label = QLabel("Rule ID:")
        id_label.setObjectName("TimerRuleIdLabel")
        self.id_input = QLineEdit()
        self.id_input.setObjectName("TimerRuleIdInput")
        self.id_input.setPlaceholderText("unique_rule_id")
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_input)
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setObjectName("TimerRuleDescLabel")
        self.desc_input = QLineEdit()
        self.desc_input.setObjectName("TimerRuleDescInput")
        self.desc_input.setPlaceholderText("Brief rule description")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        enable_layout = QHBoxLayout()
        self.enable_checkbox = QCheckBox("Enabled")
        self.enable_checkbox.setObjectName("TimerRuleEnabledCheckbox")
        self.enable_checkbox.setChecked(True)
        self.recurring_checkbox = QCheckBox("Recurring")
        self.recurring_checkbox.setObjectName("TimerRuleRecurringCheckbox")
        self.recurring_checkbox.setToolTip("If checked, timer keeps looping even if conditions fail. Only stops on scene change.")
        self.recurring_checkbox.setChecked(False)
        enable_layout.addWidget(self.enable_checkbox)
        enable_layout.addWidget(self.recurring_checkbox)
        enable_layout.addStretch()
        list_controls_layout.addLayout(id_layout)
        list_controls_layout.addLayout(desc_layout)
        list_controls_layout.addLayout(enable_layout)
        main_layout.addWidget(list_controls_widget)
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(10)
        left_panel_scroll = QScrollArea()
        left_panel_scroll.setObjectName("TimerLeftPanelScroll")
        left_panel_scroll.setWidgetResizable(True)
        left_panel_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_panel_widget = QWidget()
        left_panel_widget.setObjectName("TimerLeftPanelWidget")
        left_panel_layout = QVBoxLayout(left_panel_widget)
        left_panel_layout.setContentsMargins(10, 10, 10, 10)
        left_panel_layout.setSpacing(10)
        self.conditions_title_label = QLabel("Conditions:")
        self.conditions_title_label.setObjectName("TimerConditionsTitleLabel")
        self.conditions_title_label.setAlignment(Qt.AlignCenter)
        left_panel_layout.addWidget(self.conditions_title_label)
        start_after_layout_container = QWidget() 
        start_after_vertical_layout = QVBoxLayout(start_after_layout_container) 
        start_after_vertical_layout.setContentsMargins(0,0,0,0)
        start_after_vertical_layout.setSpacing(5)
        self.start_after_label = QLabel("Start After:")
        self.start_after_label.setObjectName("TimerRuleStartAfterLabel")
        start_after_vertical_layout.addWidget(self.start_after_label)
        start_after_radio_layout = QHBoxLayout()
        start_after_radio_layout.setAlignment(Qt.AlignCenter)
        self.start_after_player_radio = QRadioButton("Player")
        self.start_after_player_radio.setObjectName("TimerRuleStartAfterPlayerRadio")
        self.start_after_player_radio.setChecked(True)
        self.start_after_character_radio = QRadioButton("Character")
        self.start_after_character_radio.setObjectName("TimerRuleStartAfterCharacterRadio")
        self.start_after_scene_change_radio = QRadioButton("Scene Change")
        self.start_after_scene_change_radio.setObjectName("TimerRuleStartAfterSceneChangeRadio")
        start_after_radio_layout.addWidget(self.start_after_player_radio)
        start_after_radio_layout.addWidget(self.start_after_character_radio)
        start_after_radio_layout.addWidget(self.start_after_scene_change_radio)
        start_after_vertical_layout.addLayout(start_after_radio_layout)
        left_panel_layout.addWidget(start_after_layout_container)
        self.condition_type_widget = QWidget()
        condition_type_layout = QVBoxLayout(self.condition_type_widget)
        condition_type_layout.setContentsMargins(0,0,0,0)
        condition_type_layout.setSpacing(5)
        radio_button_layout = QHBoxLayout()
        radio_button_layout.setAlignment(Qt.AlignCenter)
        self.always_radio = QRadioButton("Always")
        self.always_radio.setObjectName("TimerRuleConditionAlwaysRadio")
        self.always_radio.setChecked(True)
        self.variable_radio = QRadioButton("Variable")
        self.variable_radio.setObjectName("TimerRuleConditionVariableRadio")
        radio_button_layout.addWidget(self.always_radio)
        radio_button_layout.addWidget(self.variable_radio)
        condition_type_layout.addLayout(radio_button_layout)
        self.variable_conditions_area = QWidget()
        self.variable_conditions_area.setObjectName("VariableConditionsArea")
        variable_conditions_area_layout = QVBoxLayout(self.variable_conditions_area)
        variable_conditions_area_layout.setContentsMargins(5, 5, 5, 5)
        variable_conditions_area_layout.setSpacing(5)
        self.variable_conditions_layout = QVBoxLayout()
        variable_conditions_area_layout.addLayout(self.variable_conditions_layout)
        self.add_variable_condition_button = QPushButton("Add Variable +")
        self.add_variable_condition_button.setObjectName("AddVariableConditionButton")
        variable_conditions_area_layout.addWidget(self.add_variable_condition_button)
        self.variable_conditions_area.setVisible(False)
        self.variable_radio.toggled.connect(self._ensure_initial_condition_row)
        condition_type_layout.addWidget(self.variable_conditions_area)
        left_panel_layout.addWidget(self.condition_type_widget)
        rule_properties_layout = QVBoxLayout()
        rule_properties_layout.setSpacing(10)
        interval_main_layout = QVBoxLayout()
        interval_main_layout.setSpacing(3)
        interval_label_layout = QHBoxLayout()
        interval_label = QLabel("Interval (seconds):")
        interval_label.setObjectName("TimerRuleIntervalLabel")
        self.interval_random_checkbox = QCheckBox("Random")
        self.interval_random_checkbox.setObjectName("TimerRuleIntervalRandomCheckbox")
        interval_label_layout.addWidget(interval_label)
        interval_label_layout.addWidget(self.interval_random_checkbox)
        interval_label_layout.addStretch(1)
        self.interval_input = QSpinBox()
        self.interval_input.setObjectName("TimerRuleIntervalInput")
        self.interval_input.setMinimum(1)
        self.interval_input.setMaximum(86400)
        self.interval_input.setValue(60)
        self.interval_input.setFixedWidth(80)
        interval_label_layout.addWidget(self.interval_input)
        interval_main_layout.addLayout(interval_label_layout)
        self.interval_random_inputs_widget = QWidget()
        self.interval_random_inputs_widget.setObjectName("TimerRuleIntervalRandomInputsWidget")
        interval_random_layout = QFormLayout(self.interval_random_inputs_widget)
        interval_random_layout.setContentsMargins(20, 3, 0, 3)
        interval_random_layout.setSpacing(5)
        self.interval_min_input = QSpinBox()
        self.interval_min_input.setObjectName("TimerRuleIntervalMinInput")
        self.interval_min_input.setMinimum(1)
        self.interval_min_input.setMaximum(86399)
        self.interval_max_input = QSpinBox()
        self.interval_max_input.setObjectName("TimerRuleIntervalMaxInput")
        self.interval_max_input.setMinimum(1)
        self.interval_max_input.setMaximum(86400)
        interval_random_layout.addRow("Min:", self.interval_min_input)
        interval_random_layout.addRow("Max:", self.interval_max_input)
        self.interval_random_inputs_widget.setVisible(False)
        interval_main_layout.addWidget(self.interval_random_inputs_widget)
        rule_properties_layout.addLayout(interval_main_layout)
        game_time_label = QLabel("<b>Game Time Interval:</b>")
        game_time_label.setObjectName("TimerRuleGameTimeIntervalLabel")
        rule_properties_layout.addWidget(game_time_label)
        game_minutes_main_layout = QVBoxLayout()
        game_minutes_main_layout.setSpacing(3)
        game_minutes_label_layout = QHBoxLayout()
        game_minutes_label = QLabel("Game Minutes:")
        game_minutes_label.setObjectName("TimerRuleGameMinutesLabel")
        self.game_minutes_random_checkbox = QCheckBox("Random")
        self.game_minutes_random_checkbox.setObjectName("TimerRuleGameMinutesRandomCheckbox")
        game_minutes_label_layout.addWidget(game_minutes_label)
        game_minutes_label_layout.addWidget(self.game_minutes_random_checkbox)
        game_minutes_label_layout.addStretch(1)
        self.game_minutes_input = QSpinBox()
        self.game_minutes_input.setObjectName("TimerRuleGameMinutesInput")
        self.game_minutes_input.setMinimum(0)
        self.game_minutes_input.setMaximum(59)
        self.game_minutes_input.setFixedWidth(80)
        game_minutes_label_layout.addWidget(self.game_minutes_input)
        game_minutes_main_layout.addLayout(game_minutes_label_layout)
        self.game_minutes_random_inputs_widget = QWidget()
        self.game_minutes_random_inputs_widget.setObjectName("TimerRuleGameMinutesRandomInputsWidget")
        game_minutes_random_layout = QFormLayout(self.game_minutes_random_inputs_widget)
        game_minutes_random_layout.setContentsMargins(20, 3, 0, 3)
        game_minutes_random_layout.setSpacing(5)
        self.game_minutes_min_input = QSpinBox()
        self.game_minutes_min_input.setObjectName("TimerRuleGameMinutesMinInput")
        self.game_minutes_min_input.setMinimum(0)
        self.game_minutes_min_input.setMaximum(58)
        self.game_minutes_max_input = QSpinBox()
        self.game_minutes_max_input.setObjectName("TimerRuleGameMinutesMaxInput")
        self.game_minutes_max_input.setMinimum(0)
        self.game_minutes_max_input.setMaximum(59)
        game_minutes_random_layout.addRow("Min:", self.game_minutes_min_input)
        game_minutes_random_layout.addRow("Max:", self.game_minutes_max_input)
        self.game_minutes_random_inputs_widget.setVisible(False)
        game_minutes_main_layout.addWidget(self.game_minutes_random_inputs_widget)
        rule_properties_layout.addLayout(game_minutes_main_layout)
        game_hours_main_layout = QVBoxLayout()
        game_hours_main_layout.setSpacing(3)
        game_hours_label_layout = QHBoxLayout()
        game_hours_label = QLabel("Game Hours:")
        game_hours_label.setObjectName("TimerRuleGameHoursLabel")
        self.game_hours_random_checkbox = QCheckBox("Random")
        self.game_hours_random_checkbox.setObjectName("TimerRuleGameHoursRandomCheckbox")
        game_hours_label_layout.addWidget(game_hours_label)
        game_hours_label_layout.addWidget(self.game_hours_random_checkbox)
        game_hours_label_layout.addStretch(1)
        self.game_hours_input = QSpinBox()
        self.game_hours_input.setObjectName("TimerRuleGameHoursInput")
        self.game_hours_input.setMinimum(0)
        self.game_hours_input.setMaximum(23)
        self.game_hours_input.setFixedWidth(80)
        game_hours_label_layout.addWidget(self.game_hours_input)
        game_hours_main_layout.addLayout(game_hours_label_layout)
        self.game_hours_random_inputs_widget = QWidget()
        self.game_hours_random_inputs_widget.setObjectName("TimerRuleGameHoursRandomInputsWidget")
        game_hours_random_layout = QFormLayout(self.game_hours_random_inputs_widget)
        game_hours_random_layout.setContentsMargins(20, 3, 0, 3)
        game_hours_random_layout.setSpacing(5)
        self.game_hours_min_input = QSpinBox()
        self.game_hours_min_input.setObjectName("TimerRuleGameHoursMinInput")
        self.game_hours_min_input.setMinimum(0)
        self.game_hours_min_input.setMaximum(22)
        self.game_hours_max_input = QSpinBox()
        self.game_hours_max_input.setObjectName("TimerRuleGameHoursMaxInput")
        self.game_hours_max_input.setMinimum(0)
        self.game_hours_max_input.setMaximum(23)
        game_hours_random_layout.addRow("Min:", self.game_hours_min_input)
        game_hours_random_layout.addRow("Max:", self.game_hours_max_input)
        self.game_hours_random_inputs_widget.setVisible(False)
        game_hours_main_layout.addWidget(self.game_hours_random_inputs_widget)
        rule_properties_layout.addLayout(game_hours_main_layout)
        game_days_main_layout = QVBoxLayout()
        game_days_main_layout.setSpacing(3)
        game_days_label_layout = QHBoxLayout()
        game_days_label = QLabel("Game Days:")
        game_days_label.setObjectName("TimerRuleGameDaysLabel")
        self.game_days_random_checkbox = QCheckBox("Random")
        self.game_days_random_checkbox.setObjectName("TimerRuleGameDaysRandomCheckbox")
        game_days_label_layout.addWidget(game_days_label)
        game_days_label_layout.addWidget(self.game_days_random_checkbox)
        game_days_label_layout.addStretch(1)
        self.game_days_input = QSpinBox()
        self.game_days_input.setObjectName("TimerRuleGameDaysInput")
        self.game_days_input.setMinimum(0)
        self.game_days_input.setMaximum(365)
        self.game_days_input.setFixedWidth(80)
        game_days_label_layout.addWidget(self.game_days_input)
        game_days_main_layout.addLayout(game_days_label_layout)
        self.game_days_random_inputs_widget = QWidget()
        self.game_days_random_inputs_widget.setObjectName("TimerRuleGameDaysRandomInputsWidget")
        game_days_random_layout = QFormLayout(self.game_days_random_inputs_widget)
        game_days_random_layout.setContentsMargins(20, 3, 0, 3)
        game_days_random_layout.setSpacing(5)
        self.game_days_min_input = QSpinBox()
        self.game_days_min_input.setObjectName("TimerRuleGameDaysMinInput")
        self.game_days_min_input.setMinimum(0)
        self.game_days_min_input.setMaximum(364)
        self.game_days_max_input = QSpinBox()
        self.game_days_max_input.setObjectName("TimerRuleGameDaysMaxInput")
        self.game_days_max_input.setMinimum(0)
        self.game_days_max_input.setMaximum(365)
        game_days_random_layout.addRow("Min:", self.game_days_min_input)
        game_days_random_layout.addRow("Max:", self.game_days_max_input)
        self.game_days_random_inputs_widget.setVisible(False)
        game_days_main_layout.addWidget(self.game_days_random_inputs_widget)
        rule_properties_layout.addLayout(game_days_main_layout)
        left_panel_layout.addLayout(rule_properties_layout)
        left_panel_layout.addStretch(1)
        left_panel_scroll.setWidget(left_panel_widget)
        panels_layout.addWidget(left_panel_scroll, 1)
        right_panel_scroll = QScrollArea() 
        right_panel_scroll.setObjectName("TimerRightPanelScroll") 
        right_panel_scroll.setWidgetResizable(True)
        right_panel_scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_panel_widget = QWidget()
        self.right_panel_widget.setObjectName("TimerRightPanelWidget")
        right_panel_scroll.setWidget(self.right_panel_widget)
        right_panel_layout = QVBoxLayout(self.right_panel_widget)
        right_panel_layout.setContentsMargins(10, 10, 10, 10)
        right_panel_layout.setSpacing(8)
        actions_section_layout = QVBoxLayout()
        actions_section_layout.setSpacing(10)
        actions_label = QLabel("Actions:")
        actions_label.setObjectName("TimerRuleActionsLabel")
        actions_label.setAlignment(Qt.AlignCenter)
        actions_section_layout.addWidget(actions_label)
        self.actions_container = QWidget()
        self.actions_container.setObjectName("TimerRuleActionsContainer")
        self.actions_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.actions_layout = QVBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(5, 5, 5, 5)
        actions_section_layout.addWidget(self.actions_container, 1)
        self.add_action_button = QPushButton("Add Action +")
        self.add_action_button.setObjectName("TimerRuleAddActionButton")
        actions_section_layout.addWidget(self.add_action_button)
        self.save_rule_button = QPushButton("Save Rule")
        self.save_rule_button.setObjectName("TimerRuleSaveButton")
        right_panel_layout.addLayout(actions_section_layout, 1)
        panels_layout.addWidget(right_panel_scroll, 1)
        main_layout.addLayout(panels_layout)
        main_layout.addWidget(self.save_rule_button)
        self.filter_input.textChanged.connect(self._filter_rules)
        self.add_rule_button.clicked.connect(self._add_rule)
        self.remove_rule_button.clicked.connect(self._remove_rule)
        self.refresh_rules_button.clicked.connect(self._refresh_timer_rules)
        self.rules_list.currentItemChanged.connect(self._rule_selected)
        self.save_rule_button.clicked.connect(self._save_rule)
        self.add_action_button.clicked.connect(self._add_action)
        move_up_button.clicked.connect(self._move_rule_up)
        move_down_button.clicked.connect(self._move_rule_down)
        self.variable_radio.toggled.connect(self._toggle_variable_condition_inputs)
        self.add_variable_condition_button.clicked.connect(self._add_variable_condition_row)
        self.interval_random_checkbox.toggled.connect(self._toggle_interval_random_inputs)
        self.game_minutes_random_checkbox.toggled.connect(self._toggle_game_minutes_random_inputs)
        self.game_hours_random_checkbox.toggled.connect(self._toggle_game_hours_random_inputs)
        self.game_days_random_checkbox.toggled.connect(self._toggle_game_days_random_inputs)
        self._apply_theme()
    
    def _toggle_variable_condition_inputs(self, checked):
        self.variable_conditions_area.setVisible(checked)
        self._update_condition_row_ui()

    def _toggle_interval_random_inputs(self, checked):
        self.interval_random_inputs_widget.setVisible(checked)
        self.interval_input.setDisabled(checked)

    def _toggle_game_minutes_random_inputs(self, checked):
        self.game_minutes_random_inputs_widget.setVisible(checked)
        self.game_minutes_input.setDisabled(checked)

    def _toggle_game_hours_random_inputs(self, checked):
        self.game_hours_random_inputs_widget.setVisible(checked)
        self.game_hours_input.setDisabled(checked)

    def _toggle_game_days_random_inputs(self, checked):
        self.game_days_random_inputs_widget.setVisible(checked)
        self.game_days_input.setDisabled(checked)
    
    def _filter_rules(self, text):
        for i in range(self.rules_list.count()):
            item = self.rules_list.item(i)
            if not text or text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _add_rule(self):
        if self.start_after_character_radio.isChecked():
            start_after_trigger = "Character"
            rule_scope = "Character"
        elif self.start_after_scene_change_radio.isChecked():
            start_after_trigger = "Scene Change"
            rule_scope = "Global"
        else:
            start_after_trigger = "Player"
            rule_scope = "Global"
        rule = {
            "id": f"timer_rule_{len(self._timer_rules) + 1}",
            "description": "New timer rule",
            "enabled": True,
            "recurring": False,
            "interval": 60,
            "interval_is_random": False, "interval_min": 1, "interval_max": 60,
            "game_minutes": 0,
            "game_minutes_is_random": False, "game_minutes_min": 0, "game_minutes_max": 0,
            "game_hours": 0,
            "game_hours_is_random": False, "game_hours_min": 0, "game_hours_max": 0,
            "game_days": 0,
            "game_days_is_random": False, "game_days_min": 0, "game_days_max": 0,
            "start_after_trigger": start_after_trigger,
            "rule_scope": rule_scope,
            "condition_type": "Always", 
            "condition_details": [],
            "actions": []
        }
        self._timer_rules.append(rule)
        self._update_rules_list()
        main_ui = get_main_ui(self)
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None
        for i in range(self.rules_list.count()):
            item = self.rules_list.item(i)
            if item.data(Qt.UserRole) == rule["id"]:
                self.rules_list.setCurrentItem(item)
                break
        self._auto_save_and_reload_timers()
    
    def _refresh_timer_rules(self):
        from PyQt5.QtWidgets import QMessageBox
        try:
            main_ui = get_main_ui(self)
            if not main_ui:
                QMessageBox.warning(self, "Error", "Could not find main UI instance.")
                return
            tab_index = -1
            for i, tab_data in enumerate(main_ui.tabs_data):
                if tab_data and tab_data.get('timer_rules_widget') is self:
                    tab_index = i
                    break
            if tab_index == -1:
                QMessageBox.warning(self, "Error", "Could not determine which tab this timer rules widget belongs to.")
                return
            from timer_rules_manager import _load_timer_rules
            timer_rules = _load_timer_rules(main_ui, tab_index)
            if timer_rules is not None:
                self.load_timer_rules(timer_rules)
                if hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
                    try:
                        main_ui.add_rule_sound.play()
                    except Exception as e:
                        print(f"Error playing refresh sound: {e}")
            else:
                QMessageBox.warning(self, "Error", "Failed to load timer rules from JSON files.")
        except Exception as e:
            print(f"Error refreshing timer rules: {e}")
            QMessageBox.critical(self, "Refresh Error", f"An error occurred while refreshing timer rules:\n{e}")

    def _remove_rule(self):
        current_item = self.rules_list.currentItem()
        if not current_item:
            return
        rule_id = current_item.data(Qt.UserRole)
        self._timer_rules = [r for r in self._timer_rules if r["id"] != rule_id]
        self._update_rules_list()
        self._clear_editor()
        main_ui = get_main_ui(self)
        if main_ui and hasattr(main_ui, 'remove_rule_sound') and main_ui.remove_rule_sound:
            try:
                main_ui.remove_rule_sound.play()
            except Exception:
                main_ui.remove_rule_sound = None
        self._auto_save_and_reload_timers()
    
    def _move_rule_up(self):
        current_item = self.rules_list.currentItem()
        if not current_item:
            return
        rule_id = current_item.data(Qt.UserRole)
        rule_index = -1
        for i, rule in enumerate(self._timer_rules):
            if rule["id"] == rule_id:
                rule_index = i
                break
        if rule_index > 0:
            self._timer_rules[rule_index], self._timer_rules[rule_index-1] = \
                self._timer_rules[rule_index-1], self._timer_rules[rule_index]
            self._update_rules_list()
            for i in range(self.rules_list.count()):
                item = self.rules_list.item(i)
                if item.data(Qt.UserRole) == rule_id:
                    self.rules_list.setCurrentItem(item)
                    break
    
    def _move_rule_down(self):
        current_item = self.rules_list.currentItem()
        if not current_item:
            return
        rule_id = current_item.data(Qt.UserRole)
        rule_index = -1
        for i, rule in enumerate(self._timer_rules):
            if rule["id"] == rule_id:
                rule_index = i
                break
        if rule_index >= 0 and rule_index < len(self._timer_rules) - 1:
            self._timer_rules[rule_index], self._timer_rules[rule_index+1] = \
                self._timer_rules[rule_index+1], self._timer_rules[rule_index]
            self._update_rules_list()
            for i in range(self.rules_list.count()):
                item = self.rules_list.item(i)
                if item.data(Qt.UserRole) == rule_id:
                    self.rules_list.setCurrentItem(item)
                    break
    
    def _rule_selected(self, current, previous):
        if not current:
            return
        rule_id = current.data(Qt.UserRole)
        rule = next((r for r in self._timer_rules if r["id"] == rule_id), None)
        if not rule:
            return
        self.id_input.setText(rule["id"])
        self.desc_input.setText(rule["description"])
        self.enable_checkbox.setChecked(rule.get("enabled", True))
        self.recurring_checkbox.setChecked(rule.get("recurring", False))
        self.interval_input.setValue(rule.get("interval", 60))
        self.interval_random_checkbox.setChecked(rule.get("interval_is_random", False))
        self.interval_min_input.setValue(rule.get("interval_min", 1))
        self.interval_max_input.setValue(rule.get("interval_max", 60))
        self._toggle_interval_random_inputs(self.interval_random_checkbox.isChecked())
        self.game_minutes_input.setValue(rule.get("game_minutes", 0))
        self.game_minutes_random_checkbox.setChecked(rule.get("game_minutes_is_random", False))
        self.game_minutes_min_input.setValue(rule.get("game_minutes_min", 0))
        self.game_minutes_max_input.setValue(rule.get("game_minutes_max", 0))
        self._toggle_game_minutes_random_inputs(self.game_minutes_random_checkbox.isChecked())
        self.game_hours_input.setValue(rule.get("game_hours", 0))
        self.game_hours_random_checkbox.setChecked(rule.get("game_hours_is_random", False))
        self.game_hours_min_input.setValue(rule.get("game_hours_min", 0))
        self.game_hours_max_input.setValue(rule.get("game_hours_max", 0))
        self._toggle_game_hours_random_inputs(self.game_hours_random_checkbox.isChecked())
        self.game_days_input.setValue(rule.get("game_days", 0))
        self.game_days_random_checkbox.setChecked(rule.get("game_days_is_random", False))
        self.game_days_min_input.setValue(rule.get("game_days_min", 0))
        self.game_days_max_input.setValue(rule.get("game_days_max", 0))
        self._toggle_game_days_random_inputs(self.game_days_random_checkbox.isChecked())
        start_after_trigger = rule.get("start_after_trigger", "Player")
        if start_after_trigger == "Character":
            self.start_after_character_radio.setChecked(True)
        elif start_after_trigger == "Scene Change":
            self.start_after_scene_change_radio.setChecked(True)
        else:
            self.start_after_player_radio.setChecked(True)
        condition_type = rule.get("condition_type", "Always")
        if condition_type == "Variable":
            self.variable_radio.setChecked(True)
            while self.variable_conditions_layout.count() > 0:
                item = self.variable_conditions_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
            condition_details = rule.get("condition_details", [])
            if condition_details:
                for cond_data in condition_details:
                    self._add_variable_condition_row(cond_data)
            else:
                self._ensure_initial_condition_row(True)
            self._update_condition_row_ui()
        else:
            self.always_radio.setChecked(True)
            rule.pop("condition_variable_name", None)
            rule.pop("condition_variable_value", None)
            rule.pop("condition_variable_scope", None)
            while self.variable_conditions_layout.count() > 0:
                item = self.variable_conditions_layout.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()
        self._clear_actions()
        for action in rule["actions"]:
            self._add_action(action)
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            for i in range(self.actions_layout.count()):
                widget = self.actions_layout.itemAt(i).widget()
                if widget:
                    self._apply_widget_theme(widget, base_color, darker_bg)
    
    def _save_rule(self):
        current_item = self.rules_list.currentItem()
        if not current_item:
            return
        rule_id = current_item.data(Qt.UserRole)
        rule = next((r for r in self._timer_rules if r["id"] == rule_id), None)
        if not rule:
            return
        new_id = self.id_input.text().strip()
        if not new_id:
            return
        if new_id != rule["id"]:
            if any(r["id"] == new_id for r in self._timer_rules):
                return
            rule["id"] = new_id
        rule["description"] = self.desc_input.text()
        rule["enabled"] = self.enable_checkbox.isChecked()
        rule["recurring"] = self.recurring_checkbox.isChecked()
        rule["interval_is_random"] = self.interval_random_checkbox.isChecked()
        if rule["interval_is_random"]:
            rule["interval_min"] = self.interval_min_input.value()
            rule["interval_max"] = self.interval_max_input.value()
            rule["interval"] = 0
        else:
            rule["interval"] = self.interval_input.value()
            rule["interval_min"] = 0
            rule["interval_max"] = 0
        rule["game_minutes_is_random"] = self.game_minutes_random_checkbox.isChecked()
        if rule["game_minutes_is_random"]:
            rule["game_minutes_min"] = self.game_minutes_min_input.value()
            rule["game_minutes_max"] = self.game_minutes_max_input.value()
            rule["game_minutes"] = 0 
        else:
            rule["game_minutes"] = self.game_minutes_input.value()
            rule["game_minutes_min"] = 0
            rule["game_minutes_max"] = 0
        rule["game_hours_is_random"] = self.game_hours_random_checkbox.isChecked()
        if rule["game_hours_is_random"]:
            rule["game_hours_min"] = self.game_hours_min_input.value()
            rule["game_hours_max"] = self.game_hours_max_input.value()
            rule["game_hours"] = 0 
        else:
            rule["game_hours"] = self.game_hours_input.value()
            rule["game_hours_min"] = 0
            rule["game_hours_max"] = 0
        rule["game_days_is_random"] = self.game_days_random_checkbox.isChecked()
        if rule["game_days_is_random"]:
            rule["game_days_min"] = self.game_days_min_input.value()
            rule["game_days_max"] = self.game_days_max_input.value()
            rule["game_days"] = 0 
        else:
            rule["game_days"] = self.game_days_input.value()
            rule["game_days_min"] = 0
            rule["game_days_max"] = 0
        if self.start_after_character_radio.isChecked():
            rule["start_after_trigger"] = "Character"
        elif self.start_after_scene_change_radio.isChecked():
            rule["start_after_trigger"] = "Scene Change"
        else:
            rule["start_after_trigger"] = "Player"
        if rule["start_after_trigger"] == "Character":
            rule["rule_scope"] = "Character"
        else:
            rule["rule_scope"] = "Global"
        if self.variable_radio.isChecked():
            rule["condition_type"] = "Variable"
            details = []
            for i in range(self.variable_conditions_layout.count()):
                widget = self.variable_conditions_layout.itemAt(i)
                if widget and widget.widget():
                    row_widget = widget.widget()
                    inter_row_op_combo = row_widget.findChild(QComboBox, "ConditionRowOperatorCombo")
                    name_input = row_widget.findChild(QLineEdit, "ConditionVarNameInput")
                    operator_combo = row_widget.findChild(QComboBox, "ConditionOperatorCombo")
                    value_input = row_widget.findChild(QLineEdit, "ConditionValueInput")
                    scope_global_radio = row_widget.findChild(QRadioButton, "ConditionScopeGlobalRadio")
                    scope_character_radio = row_widget.findChild(QRadioButton, "ConditionScopeCharacterRadio")
                    scope_setting_radio = row_widget.findChild(QRadioButton, "ConditionScopeSettingRadio")
                    name = name_input.text().strip() if name_input else ""
                    operator = operator_combo.currentText() if operator_combo else "=="
                    value = value_input.text().strip() if value_input else ""
                    logic_op = inter_row_op_combo.currentText() if inter_row_op_combo else "AND"
                    scope = "Global"
                    if scope_character_radio and scope_character_radio.isChecked():
                        scope = "Character"
                    elif scope_setting_radio and scope_setting_radio.isChecked():
                        scope = "Setting"
                    if name: 
                        detail = {
                            "name": name,
                            "operator": operator,
                            "value": value,
                            "scope": scope
                        }
                        if i > 0:
                            detail["logic_to_previous"] = logic_op
                        details.append(detail)
            rule["condition_details"] = details
            rule.pop("condition_variable_name", None)
            rule.pop("condition_variable_value", None)
            rule.pop("condition_variable_scope", None)
        else:
            rule["condition_type"] = "Always"
            rule["condition_details"] = []
            rule.pop("condition_variable_name", None)
            rule.pop("condition_variable_value", None)
            rule.pop("condition_variable_scope", None)
        rule["actions"] = self._get_actions()
        self._update_rules_list()
        for i in range(self.rules_list.count()):
            item = self.rules_list.item(i)
            if item.data(Qt.UserRole) == rule["id"]:
                self.rules_list.setCurrentItem(item)
                break
        main_ui = get_main_ui(self)
        if main_ui and hasattr(main_ui, 'update_rule_sound') and main_ui.update_rule_sound:
            try:
                main_ui.update_rule_sound.play()
            except Exception:
                main_ui.update_rule_sound = None
        self._auto_save_and_reload_timers()
    
    def _add_action(self, action=None):
        action_widget = QWidget()
        action_widget.setObjectName("TimerRuleActionRow")
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(5)
        type_combo = QComboBox()
        type_combo.setObjectName("TimerRuleActionTypeCombo")
        type_combo.addItems(["Set Var", "System Message", "Narrator Post", "Actor Post", "New Scene", "Game Over"])
        type_combo.setMinimumWidth(100)
        action_layout.addWidget(type_combo)
        value_input = QLineEdit()
        value_input.setObjectName("TimerRuleActionValueInput")
        value_input.setPlaceholderText("Action value")
        action_layout.addWidget(value_input, 1)
        set_var_widget = QWidget()
        set_var_layout = QHBoxLayout(set_var_widget)
        set_var_layout.setContentsMargins(0,0,0,0)
        set_var_layout.setSpacing(3)
        var_name_input = QLineEdit()
        var_name_input.setObjectName("TimerRuleActionVarNameInput")
        var_name_input.setPlaceholderText("Variable Name")
        set_var_layout.addWidget(var_name_input, 1)
        operation_selector = QComboBox()
        operation_selector.setObjectName("TimerRuleSetVarOperationSelector")
        operation_selector.addItems(["Set", "Increment", "Decrement", "Multiply", "Divide", "Generate"])
        operation_selector.setFixedWidth(70)
        set_var_layout.addWidget(operation_selector)
        var_value_input = QLineEdit()
        var_value_input.setObjectName("TimerRuleActionVarValueInput")
        var_value_input.setPlaceholderText("Value")
        set_var_layout.addWidget(var_value_input, 1)
        generate_context_widget = QWidget()
        generate_context_widget.setObjectName("TimerGenerateContextWidget")
        generate_context_layout = QVBoxLayout(generate_context_widget)
        generate_context_layout.setContentsMargins(5, 0, 5, 0)
        generate_context_layout.setSpacing(5)
        generate_instructions_label = QLabel("Generation instructions:")
        generate_instructions_label.setObjectName("TimerGenerateInstructionsLabel")
        generate_instructions_input = QTextEdit()
        generate_instructions_input.setObjectName("TimerGenerateInstructionsInput")
        generate_instructions_input.setMaximumHeight(60)
        generate_instructions_input.setPlaceholderText("Instructions for generating value")
        generate_context_layout.addWidget(generate_instructions_label)
        generate_context_layout.addWidget(generate_instructions_input)
        generate_context_label = QLabel("Context:")
        generate_context_label.setObjectName("TimerGenerateContextLabel")
        generate_context_layout.addWidget(generate_context_label)
        generate_context_radios = QHBoxLayout()
        generate_last_exchange_radio = QRadioButton("Last Exchange")
        generate_last_exchange_radio.setObjectName("TimerGenerateLastExchangeRadio")
        generate_last_exchange_radio.setChecked(True)
        generate_user_msg_radio = QRadioButton("User Message")
        generate_user_msg_radio.setObjectName("TimerGenerateUserMsgRadio")
        generate_full_convo_radio = QRadioButton("Full Conversation")
        generate_full_convo_radio.setObjectName("TimerGenerateFullConvoRadio")
        generate_context_group = QButtonGroup(generate_context_widget)
        generate_context_group.addButton(generate_last_exchange_radio)
        generate_context_group.addButton(generate_user_msg_radio)
        generate_context_group.addButton(generate_full_convo_radio)
        generate_context_radios.addWidget(generate_last_exchange_radio)
        generate_context_radios.addWidget(generate_user_msg_radio)
        generate_context_radios.addWidget(generate_full_convo_radio)
        generate_context_layout.addLayout(generate_context_radios)
        generate_context_widget.setVisible(False)
        set_var_layout.addWidget(generate_context_widget, 2)
        def update_set_var_operation():
            is_generate = (operation_selector.currentText() == "Generate")
            var_value_input.setVisible(not is_generate)
            generate_context_widget.setVisible(is_generate)
        operation_selector.currentIndexChanged.connect(update_set_var_operation)
        update_set_var_operation()
        scope_widget = QWidget()
        scope_layout = QHBoxLayout(scope_widget)
        scope_layout.setContentsMargins(0,0,0,0)
        scope_layout.setSpacing(3)
        scope_group = QButtonGroup(scope_widget)
        scope_global_radio = QRadioButton("Global")
        scope_global_radio.setObjectName("TimerRuleActionScopeGlobalRadio")
        scope_global_radio.setChecked(True)
        scope_character_radio = QRadioButton("Character")
        scope_character_radio.setObjectName("TimerRuleActionScopeCharacterRadio")
        scope_setting_radio = QRadioButton("Setting")
        scope_setting_radio.setObjectName("TimerRuleActionScopeSettingRadio")
        scope_group.addButton(scope_global_radio)
        scope_group.addButton(scope_character_radio)
        scope_group.addButton(scope_setting_radio)
        scope_layout.addWidget(scope_global_radio)
        scope_layout.addWidget(scope_character_radio)
        scope_layout.addWidget(scope_setting_radio)
        set_var_layout.addWidget(scope_widget)
        set_var_widget.setVisible(False)
        action_layout.addWidget(set_var_widget, 2)
        narrator_post_widget = QWidget()
        narrator_post_widget.setObjectName("TimerRuleNarratorPostWidget")
        narrator_post_layout = QVBoxLayout(narrator_post_widget)
        narrator_post_layout.setContentsMargins(0,0,0,0)
        narrator_post_layout.setSpacing(3)
        narrator_system_msg_layout = QHBoxLayout()
        narrator_system_msg_label = QLabel("System Message:")
        narrator_system_msg_label.setObjectName("TimerRuleNarratorSystemMsgLabel")
        narrator_system_msg_input = QLineEdit()
        narrator_system_msg_input.setObjectName("TimerRuleNarratorSystemMsgInput")
        narrator_system_msg_input.setPlaceholderText("Optional system message")
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            narrator_system_msg_input.setStyleSheet(f"""
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 2px;
            """)
            narrator_system_msg_label.setStyleSheet(f"""
                background-color: transparent;
                color: {base_color};
            """)
        narrator_system_msg_layout.addWidget(narrator_system_msg_label)
        narrator_system_msg_layout.addWidget(narrator_system_msg_input, 1)
        narrator_post_layout.addLayout(narrator_system_msg_layout)
        narrator_allow_live_input_layout = QHBoxLayout()
        narrator_allow_live_input_checkbox = QCheckBox("Allow Live Input")
        narrator_allow_live_input_checkbox.setObjectName("TimerNarratorAllowLiveInputCheckbox")
        narrator_allow_live_input_checkbox.setToolTip("If checked, player can continue typing during this timer action")
        narrator_allow_live_input_checkbox.setFont(QFont('Consolas', 9))
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            narrator_allow_live_input_checkbox.setStyleSheet(f"color: {base_color};")
        narrator_allow_live_input_layout.addWidget(narrator_allow_live_input_checkbox)
        narrator_allow_live_input_layout.addStretch()
        narrator_post_layout.addLayout(narrator_allow_live_input_layout)
        
        narrator_post_widget.setVisible(False)
        action_layout.addWidget(narrator_post_widget, 2)
        actor_post_widget = QWidget()
        actor_post_widget.setObjectName("TimerRuleActorPostWidget")
        actor_post_layout = QVBoxLayout(actor_post_widget)
        actor_post_layout.setContentsMargins(0,0,0,0)
        actor_post_layout.setSpacing(3)
        actor_layout = QHBoxLayout()
        actor_name_label = QLabel("Character:")
        actor_name_label.setObjectName("TimerRuleActionActorNameLabel")
        actor_name_input = QLineEdit()
        actor_name_input.setObjectName("TimerRuleActionActorNameInput")
        actor_name_input.setPlaceholderText("Leave blank for self")
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            actor_name_input.setStyleSheet(f"""
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 2px;
            """)
            actor_name_label.setStyleSheet(f"""
                background-color: transparent;
                color: {base_color};
            """)
        actor_layout.addWidget(actor_name_label)
        actor_layout.addWidget(actor_name_input, 1)
        actor_post_layout.addLayout(actor_layout)
        actor_system_msg_layout = QHBoxLayout()
        actor_system_msg_label = QLabel("System Message:")
        actor_system_msg_label.setObjectName("TimerRuleActorSystemMsgLabel")
        actor_system_msg_input = QLineEdit()
        actor_system_msg_input.setObjectName("TimerRuleActorSystemMsgInput")
        actor_system_msg_input.setPlaceholderText("Optional system message")
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            actor_system_msg_input.setStyleSheet(f"""
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 2px;
            """)
            actor_system_msg_label.setStyleSheet(f"""
                background-color: transparent;
                color: {base_color};
            """)
        actor_system_msg_layout.addWidget(actor_system_msg_label)
        actor_system_msg_layout.addWidget(actor_system_msg_input, 1)
        actor_allow_live_input_layout = QHBoxLayout()
        actor_allow_live_input_checkbox = QCheckBox("Allow Live Input")
        actor_allow_live_input_checkbox.setObjectName("TimerActorAllowLiveInputCheckbox")
        actor_allow_live_input_checkbox.setToolTip("If checked, player can continue typing during this timer action")
        actor_allow_live_input_checkbox.setFont(QFont('Consolas', 9))
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            actor_allow_live_input_checkbox.setStyleSheet(f"color: {base_color};")
        actor_allow_live_input_layout.addWidget(actor_allow_live_input_checkbox)
        actor_allow_live_input_layout.addStretch()
        actor_post_layout.addLayout(actor_allow_live_input_layout)
        
        actor_post_widget.setVisible(False)
        action_layout.addWidget(actor_post_widget, 2)
        system_message_widget = QWidget()
        system_message_widget.setObjectName("TimerRuleSystemMessageWidget")
        system_message_layout = QVBoxLayout(system_message_widget)
        system_message_layout.setContentsMargins(0,0,0,0)
        system_message_layout.setSpacing(3)
        system_msg_value_layout = QHBoxLayout()
        system_msg_value_label = QLabel("System Message:")
        system_msg_value_label.setObjectName("TimerRuleSystemMsgValueLabel")
        system_msg_value_input = QTextEdit()
        system_msg_value_input.setObjectName("TimerRuleSystemMsgValueInput")
        system_msg_value_input.setMaximumHeight(60)
        system_msg_value_input.setPlaceholderText("Enter system message content...")
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            system_msg_value_input.setStyleSheet(f"""
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 2px;
            """)
            system_msg_value_label.setStyleSheet(f"""
                background-color: transparent;
                color: {base_color};
            """)
        system_msg_value_layout.addWidget(system_msg_value_label)
        system_msg_value_layout.addWidget(system_msg_value_input, 1)
        system_message_layout.addLayout(system_msg_value_layout)
        position_layout = QHBoxLayout()
        position_label = QLabel("Position:")
        position_label.setObjectName("TimerRuleSystemMsgPositionLabel")
        position_combo = QComboBox()
        position_combo.setObjectName("TimerRuleSystemMsgPositionCombo")
        position_combo.addItems(["prepend", "append", "replace"])
        position_combo.setFixedWidth(100)
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            position_combo.setStyleSheet(f"""
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                selection-background-color: {base_color};
                selection-color: {darker_bg};
            """)
            position_label.setStyleSheet(f"""
                background-color: transparent;
                color: {base_color};
            """)
        position_layout.addWidget(position_label)
        position_layout.addWidget(position_combo)
        position_layout.addStretch()
        
        sysmsg_position_label = QLabel("System Message Position:")
        sysmsg_position_label.setObjectName("TimerRuleSystemMsgSysMsgPositionLabel")
        sysmsg_position_combo = QComboBox()
        sysmsg_position_combo.setObjectName("TimerRuleSystemMsgSysMsgPositionCombo")
        sysmsg_position_combo.addItems(["first", "last"])
        sysmsg_position_combo.setFixedWidth(100)
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            sysmsg_position_combo.setStyleSheet(f"""
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                selection-background-color: {base_color};
                selection-color: {darker_bg};
            """)
            sysmsg_position_label.setStyleSheet(f"""
                background-color: transparent;
                color: {base_color};
            """)
        position_layout.addWidget(sysmsg_position_label)
        position_layout.addWidget(sysmsg_position_combo)
        system_message_layout.addLayout(position_layout)
        
        system_message_widget.setVisible(False)
        action_layout.addWidget(system_message_widget, 2)
        game_over_widget = QWidget()
        game_over_widget.setObjectName("TimerRuleGameOverWidget")
        game_over_layout = QVBoxLayout(game_over_widget)
        game_over_layout.setContentsMargins(0, 0, 0, 0)
        game_over_layout.setSpacing(3)
        
        game_over_message_label = QLabel("Game Over Message:")
        game_over_message_label.setObjectName("TimerRuleGameOverMessageLabel")
        game_over_message_label.setFont(QFont('Consolas', 9))
        game_over_message_input = QTextEdit()
        game_over_message_input.setObjectName("TimerRuleGameOverMessageInput")
        game_over_message_input.setMaximumHeight(60)
        game_over_message_input.setPlaceholderText("Enter the message the player will see when the game ends...")
        game_over_message_input.setFont(QFont('Consolas', 10))
        
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            game_over_message_input.setStyleSheet(f"""
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 2px;
            """)
            game_over_message_label.setStyleSheet(f"""
                background-color: transparent;
                color: {base_color};
            """)
        
        game_over_layout.addWidget(game_over_message_label)
        game_over_layout.addWidget(game_over_message_input)
        game_over_widget.setVisible(False)
        action_layout.addWidget(game_over_widget, 2)
        remove_button = QPushButton("-")
        remove_button.setObjectName("TimerRuleActionRemoveButton")
        remove_button.setFixedWidth(30)
        action_layout.addWidget(remove_button)
        action_widget.setProperty("value_input", value_input)
        action_widget.setProperty("set_var_widget", set_var_widget)
        action_widget.setProperty("var_name_input", var_name_input)
        action_widget.setProperty("operation_selector", operation_selector)
        action_widget.setProperty("var_value_input", var_value_input)
        action_widget.setProperty("scope_global_radio", scope_global_radio)
        action_widget.setProperty("scope_character_radio", scope_character_radio)
        action_widget.setProperty("scope_setting_radio", scope_setting_radio)
        action_widget.setProperty("actor_post_widget", actor_post_widget)
        action_widget.setProperty("actor_name_input", actor_name_input)
        action_widget.setProperty("actor_system_msg_input", actor_system_msg_input)
        action_widget.setProperty("narrator_post_widget", narrator_post_widget)
        action_widget.setProperty("generate_context_widget", generate_context_widget)
        action_widget.setProperty("generate_instructions_input", generate_instructions_input)
        action_widget.setProperty("generate_last_exchange_radio", generate_last_exchange_radio)
        action_widget.setProperty("generate_user_msg_radio", generate_user_msg_radio)
        action_widget.setProperty("generate_full_convo_radio", generate_full_convo_radio)
        action_widget.setProperty("system_message_widget", system_message_widget)
        action_widget.setProperty("system_msg_value_input", system_msg_value_input)
        action_widget.setProperty("system_msg_position_combo", position_combo)
        action_widget.setProperty("system_msg_sysmsg_position_combo", sysmsg_position_combo)
        action_widget.setProperty("game_over_widget", game_over_widget)
        action_widget.setProperty("game_over_message_input", game_over_message_input)
        def _update_action_row_inputs():
            selected_type = type_combo.currentText()
            is_set_var = (selected_type == "Set Var")
            is_system_message = (selected_type == "System Message")
            is_actor_post = (selected_type == "Actor Post")
            is_narrator_post = (selected_type == "Narrator Post")
            is_game_over = (selected_type == "Game Over")
            widget = type_combo.parentWidget()
            val_input = widget.property("value_input")
            set_var_cont = widget.property("set_var_widget")
            system_message_cont = widget.property("system_message_widget")
            actor_post_cont = widget.property("actor_post_widget")
            narrator_post_cont = widget.property("narrator_post_widget")
            game_over_cont = widget.property("game_over_widget")
            if is_set_var:
                op_selector = widget.property("operation_selector")
                var_val_input = widget.property("var_value_input")
                gen_context_widget = widget.property("generate_context_widget")
                is_generate_op = False
                if op_selector and op_selector.currentText() == "Generate":
                    is_generate_op = True
                if var_val_input:
                    var_val_input.setVisible(not is_generate_op)
                if gen_context_widget:
                    gen_context_widget.setVisible(is_generate_op)
            if val_input:
                val_input.setVisible(not (is_set_var or is_system_message or is_actor_post or is_narrator_post or is_game_over))
            if set_var_cont:
                set_var_cont.setVisible(is_set_var)
            if system_message_cont:
                system_message_cont.setVisible(is_system_message)
            if actor_post_cont:
                actor_post_cont.setVisible(is_actor_post)
            if narrator_post_cont:
                narrator_post_cont.setVisible(is_narrator_post)
            if game_over_cont:
                game_over_cont.setVisible(is_game_over)
            if val_input:
                if selected_type == "New Scene":
                    val_input.setPlaceholderText("(No value needed)") 
                    val_input.setEnabled(False)
                else:
                    val_input.setPlaceholderText("Action value")
                    val_input.setEnabled(True)
        _update_action_row_inputs()
        type_combo.currentIndexChanged.connect(_update_action_row_inputs)
        operation_selector.currentIndexChanged.connect(_update_action_row_inputs)
        if action:
            action_type = action.get("type", "Set Var")
            index = type_combo.findText(action_type)
            if index >= 0:
                type_combo.setCurrentIndex(index)
            if action_type == "Set Var":
                var_name_input.setText(action.get("var_name", ""))
                var_value_input.setText(action.get("var_value", ""))
                scope = action.get("scope", "Global")
                scope_global_radio.setChecked(scope == "Global")
                scope_character_radio.setChecked(scope == "Character")
                scope_setting_radio.setChecked(scope == "Setting")
                op_idx = operation_selector.findText(action.get("operation", "Set"), Qt.MatchFixedString | Qt.MatchCaseSensitive)
                operation_selector.setCurrentIndex(op_idx if op_idx >= 0 else 0)
                if action.get("operation", "") == "Generate":
                    generate_instructions_input.setPlainText(action.get("generate_instructions", ""))
                    generate_context = action.get("generate_context", "Last Exchange")
                    generate_last_exchange_radio.setChecked(generate_context == "Last Exchange")
                    generate_user_msg_radio.setChecked(generate_context == "User Message")
                    generate_full_convo_radio.setChecked(generate_context == "Full Conversation")
            elif action_type == "System Message":
                system_msg_value_input.setPlainText(action.get("value", ""))
                position = action.get("position", "prepend")
                pos_idx = position_combo.findText(position, Qt.MatchFixedString | Qt.MatchCaseSensitive)
                position_combo.setCurrentIndex(pos_idx if pos_idx >= 0 else 0)
                sysmsg_position = action.get("system_message_position", "first")
                sysmsg_pos_idx = sysmsg_position_combo.findText(sysmsg_position, Qt.MatchFixedString | Qt.MatchCaseSensitive)
                sysmsg_position_combo.setCurrentIndex(sysmsg_pos_idx if sysmsg_pos_idx >= 0 else 0)
            elif action_type == "Actor Post":
                actor_name_input.setText(action.get("actor_name", ""))
                actor_system_msg_input.setText(action.get("system_message", ""))
                allow_live_input_checkbox = action_widget.findChild(QCheckBox, "TimerActorAllowLiveInputCheckbox")
                if allow_live_input_checkbox:
                    allow_live_input_checkbox.setChecked(action.get("allow_live_input", False))
            elif action_type == "Narrator Post":
                if action.get("type") == "System Message":
                    narrator_system_msg_input.setText(action.get("value", ""))
                else:
                    narrator_system_msg_input.setText(action.get("system_message", ""))
                allow_live_input_checkbox = action_widget.findChild(QCheckBox, "TimerNarratorAllowLiveInputCheckbox")
                if allow_live_input_checkbox:
                    allow_live_input_checkbox.setChecked(action.get("allow_live_input", False))
            elif action_type == "System Message":
                system_msg_value_input.setPlainText(action.get("value", ""))
                position = action.get("position", "prepend")
                pos_idx = position_combo.findText(position, Qt.MatchFixedString | Qt.MatchCaseSensitive)
                position_combo.setCurrentIndex(pos_idx if pos_idx >= 0 else 0)
                sysmsg_position = action.get("system_message_position", "first")
                sysmsg_pos_idx = sysmsg_position_combo.findText(sysmsg_position, Qt.MatchFixedString | Qt.MatchCaseSensitive)
                sysmsg_position_combo.setCurrentIndex(sysmsg_pos_idx if sysmsg_pos_idx >= 0 else 0)
            elif action_type == "Game Over":
                game_over_message_input.setPlainText(action.get("message", ""))
            else:
                value_input.setText(action.get("value", ""))
            _update_action_row_inputs()
        remove_button.clicked.connect(lambda: self._remove_action(action_widget))
        self.actions_layout.addWidget(action_widget)
    
    def _remove_action(self, widget):
        self.actions_layout.removeWidget(widget)
        widget.deleteLater()
    
    def _clear_actions(self):
        while self.actions_layout.count():
            item = self.actions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _get_actions(self):
        actions = []
        for i in range(self.actions_layout.count()):
            widget = self.actions_layout.itemAt(i).widget()
            if not widget:
                continue
            action_type = widget.findChild(QComboBox, "TimerRuleActionTypeCombo").currentText()
            action_scope = "Global"
            var_name = ""
            var_value = ""
            operation = "Set"
            if action_type == "Set Var":
                name_input = widget.property("var_name_input")
                op_selector = widget.property("operation_selector")
                val_input = widget.property("var_value_input")
                g_radio = widget.property("scope_global_radio")
                c_radio = widget.property("scope_character_radio")
                s_radio = widget.property("scope_setting_radio")
                if name_input: var_name = name_input.text().strip()
                if op_selector: operation = op_selector.currentText()
                if val_input: var_value = val_input.text().strip()
                if c_radio and c_radio.isChecked(): action_scope = "Character"
                elif s_radio and s_radio.isChecked(): action_scope = "Setting"
                else: action_scope = "Global"
                if var_name:
                    action_data = {
                        "type": action_type,
                        "var_name": var_name,
                        "operation": operation,
                        "scope": action_scope
                    }
                    if operation == "Generate":
                        gen_instructions = widget.property("generate_instructions_input")
                        gen_last_exchange = widget.property("generate_last_exchange_radio")
                        gen_user_msg = widget.property("generate_user_msg_radio")
                        gen_full_convo = widget.property("generate_full_convo_radio")
                        instructions = ""
                        if gen_instructions:
                            instructions = gen_instructions.toPlainText().strip()
                        context = "Last Exchange"
                        if gen_user_msg and gen_user_msg.isChecked():
                            context = "User Message"
                        elif gen_full_convo and gen_full_convo.isChecked():
                            context = "Full Conversation"
                        action_data["generate_instructions"] = instructions
                        action_data["generate_context"] = context
                    else:
                        action_data["var_value"] = var_value
                    actions.append(action_data)
            else:
                if action_type == "Actor Post":
                    actor_name_input = widget.property("actor_name_input")
                    system_msg_input = widget.property("actor_system_msg_input")
                    actor_name = actor_name_input.text().strip() if actor_name_input else ""
                    system_message = system_msg_input.text().strip() if system_msg_input else ""
                    action_data = {
                        "type": action_type,
                        "actor_name": actor_name
                    }
                    if system_message:
                        action_data["system_message"] = system_message
                    allow_live_input_checkbox = widget.findChild(QCheckBox, "TimerActorAllowLiveInputCheckbox")
                    if allow_live_input_checkbox:
                        action_data["allow_live_input"] = allow_live_input_checkbox.isChecked()
                    
                    actions.append(action_data)
                elif action_type == "Narrator Post":
                    system_msg_input = widget.property("narrator_system_msg_input")
                    system_message = system_msg_input.text().strip() if system_msg_input else ""
                    action_data = {
                        "type": action_type
                    }
                    if system_message:
                        action_data["system_message"] = system_message
                    allow_live_input_checkbox = widget.findChild(QCheckBox, "TimerNarratorAllowLiveInputCheckbox")
                    if allow_live_input_checkbox:
                        action_data["allow_live_input"] = allow_live_input_checkbox.isChecked()
                    
                    actions.append(action_data)
                elif action_type == "System Message":
                    system_msg_value_input = widget.property("system_msg_value_input")
                    position_combo = widget.property("system_msg_position_combo")
                    sysmsg_position_combo = widget.property("system_msg_sysmsg_position_combo")
                    if system_msg_value_input:
                        value = system_msg_value_input.toPlainText().strip()
                        if value:
                            action_data = {
                                "type": action_type,
                                "value": value,
                                "position": position_combo.currentText() if position_combo else "prepend",
                                "system_message_position": sysmsg_position_combo.currentText() if sysmsg_position_combo else "first"
                            }
                            actions.append(action_data)
                elif action_type == "Game Over":
                    game_over_message_input = widget.property("game_over_message_input")
                    message = game_over_message_input.toPlainText().strip() if game_over_message_input else ""
                    action_data = {
                        "type": action_type,
                        "message": message
                    }
                    actions.append(action_data)
                else:
                    value_input = widget.property("value_input")
                    action_value = value_input.text() if value_input else ""
                    if action_type == "New Scene":
                        action_value = None
                    action_data_to_append = {"type": action_type}
                    if action_value is not None:
                        action_data_to_append["value"] = action_value
                    actions.append(action_data_to_append)
        return actions
    
    def _update_rules_list(self):
        current_id = None
        if self.rules_list.currentItem():
            current_id = self.rules_list.currentItem().data(Qt.UserRole)
        self.rules_list.clear()
        for rule in self._timer_rules:
            enabled_str = "✓" if rule.get("enabled", True) else "✗"
            item = QListWidgetItem(f"{enabled_str} {rule['id']} - {rule['description']}")
            item.setData(Qt.UserRole, rule["id"])
            self.rules_list.addItem(item)
        if current_id:
            for i in range(self.rules_list.count()):
                item = self.rules_list.item(i)
                if item.data(Qt.UserRole) == current_id:
                    self.rules_list.setCurrentItem(item)
                    break
    
    def load_timer_rules(self, rules_data):
        if rules_data:
            self._timer_rules = rules_data
            self._update_rules_list()
    
    def get_timer_rules(self):
        return self._timer_rules
    
    def _apply_theme(self):
        if not self.theme_colors:
             return
        base_color = self.theme_colors.get("base_color", "#00FF66") 
        bg_color = self.theme_colors.get("bg_color", "#252525")
        darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
        text_color = self.theme_colors.get("text_color", "white")
        self.setStyleSheet(f"QWidget#TimerRulesContainer {{ background-color: {bg_color}; }}")
        self.rules_list.setStyleSheet(f"""
            QListWidget#TimerRulesList {{
                background-color: {darker_bg};
                alternate-background-color: {bg_color};
                border: 1px solid {base_color};
                border-radius: 3px;
            }}
        """)
        self.actions_container.setStyleSheet(f"""
            QWidget#TimerRuleActionsContainer {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
            }}
        """)
        self.right_panel_widget.setStyleSheet(f"""
            QWidget#TimerRightPanelWidget {{
                background-color: {bg_color};
            }}
        """)
        for i in range(self.actions_layout.count()):
            widget = self.actions_layout.itemAt(i).widget()
            if widget:
                widget.setStyleSheet(f"""
                    QWidget#TimerRuleActionRow {{
                        background-color: {darker_bg};
                    }}
                """)
                self._apply_widget_theme(widget, base_color, darker_bg)
        radio_style = f"""
            QRadioButton::indicator {{
                width: 15px;
                height: 15px;
                border-radius: 7px;
            }}
            QRadioButton::indicator:checked {{
                background-color: {base_color};
                border: 2px solid white;
            }}
            QRadioButton::indicator:unchecked {{
                background-color: #222;
                border: 2px solid gray;
            }}
        """
        if hasattr(self, 'start_after_player_radio'):
            self.start_after_player_radio.setStyleSheet(radio_style)
        if hasattr(self, 'start_after_character_radio'):
            self.start_after_character_radio.setStyleSheet(radio_style)
        if hasattr(self, 'start_after_scene_change_radio'):
            self.start_after_scene_change_radio.setStyleSheet(radio_style)
        if hasattr(self, 'always_radio'):
            self.always_radio.setStyleSheet(radio_style)
        if hasattr(self, 'variable_radio'):
            self.variable_radio.setStyleSheet(radio_style)

    def _apply_widget_theme(self, parent_widget, base_color, darker_bg):
        for child in parent_widget.findChildren(QWidget):
            if isinstance(child, QLineEdit) or isinstance(child, QTextEdit):
                child.setStyleSheet(f"""
                    background-color: {darker_bg};
                    color: {base_color};
                    border: 1px solid {base_color};
                    border-radius: 2px;
                """)
            elif isinstance(child, QComboBox) or isinstance(child, QSpinBox):
                child.setStyleSheet(f"""
                    background-color: {darker_bg};
                    color: {base_color};
                    border: 1px solid {base_color};
                    selection-background-color: {base_color};
                    selection-color: {darker_bg};
                """)
            elif isinstance(child, QLabel):
                child.setStyleSheet(f"""
                    background-color: transparent;
                    color: {base_color};
                """)
            elif isinstance(child, QRadioButton) or isinstance(child, QCheckBox):
                child.setStyleSheet(f"""
                    background-color: transparent;
                    color: {base_color};
                """)
    
    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        self._apply_theme()
        if self.theme_colors:
            base_color = self.theme_colors.get("base_color", "#00FF66")
            darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
            radio_style = f"""
                QRadioButton {{
                    color: {base_color};
                    background-color: transparent;
                }}
                QRadioButton::indicator {{
                    width: 15px;
                    height: 15px;
                    border-radius: 7px;
                }}
                QRadioButton::indicator:checked {{
                    background-color: {base_color};
                    border: 2px solid white;
                }}
                QRadioButton::indicator:unchecked {{
                    background-color: #222;
                    border: 2px solid gray;
                }}
            """
            radio_buttons = [
                'start_after_player_radio',
                'start_after_character_radio',
                'start_after_scene_change_radio',
                'always_radio',
                'variable_radio'
            ]
            for btn_name in radio_buttons:
                if hasattr(self, btn_name):
                    radio_btn = getattr(self, btn_name)
                    radio_btn.setStyleSheet(radio_style)
            for i in range(self.actions_layout.count()):
                widget = self.actions_layout.itemAt(i).widget()
                if widget:
                    self._apply_widget_theme(widget, base_color, darker_bg)
    @pyqtSlot(bool)
    def _ensure_initial_condition_row(self, checked):
        if checked and self.variable_conditions_layout.count() == 0:
            self._add_variable_condition_row()

    def _create_variable_condition_row(self, condition_data=None):
        row_widget = QWidget()
        row_widget.setObjectName("VariableConditionRow")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        inter_row_op_combo = QComboBox()
        inter_row_op_combo.setObjectName("ConditionRowOperatorCombo")
        inter_row_op_combo.addItems(["AND", "OR"])
        inter_row_op_combo.setFixedWidth(60)
        row_layout.addWidget(inter_row_op_combo)
        var_name_input = QLineEdit()
        var_name_input.setObjectName("ConditionVarNameInput")
        var_name_input.setPlaceholderText("Variable Name")
        row_layout.addWidget(var_name_input, 2)
        operator_combo = QComboBox()
        operator_combo.setObjectName("ConditionOperatorCombo")
        operator_combo.addItems(["==", "!=", ">", "<", ">=", "<=", "exists", "not exists", "contains", "not contains"])
        row_layout.addWidget(operator_combo, 1)
        value_input = QLineEdit()
        value_input.setObjectName("ConditionValueInput")
        value_input.setPlaceholderText("Value")
        row_layout.addWidget(value_input, 2)
        scope_group = QButtonGroup(row_widget)
        scope_global_radio = QRadioButton("Global")
        scope_global_radio.setObjectName("ConditionScopeGlobalRadio")
        scope_global_radio.setToolTip("Global variable")
        scope_global_radio.setChecked(True)
        scope_character_radio = QRadioButton("Character")
        scope_character_radio.setObjectName("ConditionScopeCharacterRadio") 
        scope_character_radio.setToolTip("Character variable (requires rule applies to Character)")
        scope_setting_radio = QRadioButton("Setting")
        scope_setting_radio.setObjectName("ConditionScopeSettingRadio")
        scope_setting_radio.setToolTip("Setting variable")
        scope_group.addButton(scope_global_radio)
        scope_group.addButton(scope_character_radio)
        scope_group.addButton(scope_setting_radio)
        row_layout.addWidget(scope_global_radio)
        row_layout.addWidget(scope_character_radio)
        row_layout.addWidget(scope_setting_radio)
        remove_button = QPushButton("-")
        remove_button.setObjectName("RemoveVariableConditionButton")
        remove_button.setFixedWidth(25)
        remove_button.clicked.connect(lambda: self._remove_variable_condition_row(row_widget))
        row_layout.addWidget(remove_button)
        row_data = {
            "widget": row_widget,
            "name": var_name_input,
            "operator": operator_combo,
            "value": value_input,
            "scope_global": scope_global_radio,
            "scope_character": scope_character_radio,
            "scope_setting": scope_setting_radio,
            "remove_button": remove_button,
            "inter_row_operator": inter_row_op_combo
        }

        if condition_data:
            var_name_input.setText(condition_data.get("name", ""))
            op_idx = operator_combo.findText(condition_data.get("operator", "=="))
            operator_combo.setCurrentIndex(op_idx if op_idx >= 0 else 0)
            value_input.setText(condition_data.get("value", ""))
            scope = condition_data.get("scope", "Global")
            scope_global_radio.setChecked(scope == "Global")
            scope_character_radio.setChecked(scope == "Character")
            scope_setting_radio.setChecked(scope == "Setting")
        def update_value_visibility():
            op = operator_combo.currentText()
            value_input.setVisible(op not in ["exists", "not exists"])
        operator_combo.currentTextChanged.connect(update_value_visibility)
        update_value_visibility()
        return row_data

    def _add_variable_condition_row(self, condition_data=None):
        row_data = self._create_variable_condition_row(condition_data)
        self.variable_conditions_layout.addWidget(row_data["widget"])
        self._update_condition_row_ui()

    def _remove_variable_condition_row(self, row_widget):
        self.variable_conditions_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self._update_condition_row_ui()

    def _update_condition_row_ui(self):
        count = self.variable_conditions_layout.count()
        for i in range(count):
            item = self.variable_conditions_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                remove_button = widget.findChild(QPushButton, "RemoveVariableConditionButton")
                inter_row_op_combo = widget.findChild(QComboBox, "ConditionRowOperatorCombo")
                
                if remove_button:
                    remove_button.setVisible(count > 1)
                if inter_row_op_combo:
                    inter_row_op_combo.setVisible(i > 0)

    def _auto_save_and_reload_timers(self):
        try:
            main_ui = get_main_ui(self)
            if not main_ui:
                return
            current_tab_index = None
            for i, tab_data in enumerate(main_ui.tabs_data):
                if tab_data and tab_data.get('timer_rules_widget') is self:
                    current_tab_index = i
                    break
            if current_tab_index is None:
                return
            _save_timer_rules(main_ui, current_tab_index)
            tab_data = main_ui.tabs_data[current_tab_index]
            timer_manager = tab_data.get('timer_manager')
            if timer_manager and hasattr(timer_manager, 'reload_timer_rules'):
                fresh_rules = _load_timer_rules(main_ui, current_tab_index)
                timer_manager.reload_timer_rules(fresh_rules, tab_data)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _clear_editor(self):
        self.id_input.clear()
        self.desc_input.clear()
        self.enable_checkbox.setChecked(True)
        self.recurring_checkbox.setChecked(False)
        self.interval_input.setValue(60)
        self.interval_random_checkbox.setChecked(False)
        self.interval_min_input.setValue(1)
        self.interval_max_input.setValue(60)
        self._toggle_interval_random_inputs(False)
        self.game_minutes_input.setValue(0)
        self.game_minutes_random_checkbox.setChecked(False)
        self.game_minutes_min_input.setValue(0)
        self.game_minutes_max_input.setValue(0)
        self._toggle_game_minutes_random_inputs(False)
        self.game_hours_input.setValue(0)
        self.game_hours_random_checkbox.setChecked(False)
        self.game_hours_min_input.setValue(0)
        self.game_hours_max_input.setValue(0)
        self._toggle_game_hours_random_inputs(False)
        self.game_days_input.setValue(0)
        self.game_days_random_checkbox.setChecked(False)
        self.game_days_min_input.setValue(0)
        self.game_days_max_input.setValue(0)
        self._toggle_game_days_random_inputs(False)
        self.start_after_player_radio.setChecked(True)
        self.always_radio.setChecked(True)
        while self.variable_conditions_layout.count() > 0:
            item = self.variable_conditions_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._clear_actions()

def _save_timer_rules(main_ui, tab_index):
    if not (0 <= tab_index < len(main_ui.tabs_data) and main_ui.tabs_data[tab_index] is not None):
        print(f"Error: Cannot save timer rules for invalid tab index {tab_index}")
        return
    tab_data = main_ui.tabs_data[tab_index]
    rules_dir = tab_data.get('rules_dir')
    if not rules_dir:
        print(f"Error saving timer rules: No rules_dir for tab {tab_index}")
        return
    timer_rules_dir = os.path.join(rules_dir, "timer_rules")
    os.makedirs(timer_rules_dir, exist_ok=True)
    timer_rules_widget = tab_data.get('timer_rules_widget')
    if not timer_rules_widget:
        print(f"Error: Timer rules widget not found for tab {tab_index}")
        return
    rules_to_save = timer_rules_widget.get_timer_rules()
    existing_files = set(os.listdir(timer_rules_dir)) if os.path.exists(timer_rules_dir) else set()
    current_files = []
    rule_ids_in_order = []
    for rule in rules_to_save:
        rule_id = rule.get('id')
        if not rule_id:
            print(f"Warning: Skipping timer rule with no ID: {rule}")
            continue
        rule_ids_in_order.append(rule_id)
        filename = f"{rule_id}_timer_rule.json"
        filepath = os.path.join(timer_rules_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rule, f, indent=2, ensure_ascii=False)
            current_files.append(filename)
        except Exception as e:
            print(f"Error saving timer rule '{rule_id}': {e}")
    order_filename = "_timer_rules_order.json"
    order_filepath = os.path.join(timer_rules_dir, order_filename)
    try:
        with open(order_filepath, 'w', encoding='utf-8') as f:
            json.dump(rule_ids_in_order, f, indent=2, ensure_ascii=False)
        print(f"Saved timer rule order to {order_filepath}")
        current_files.append(order_filename)
    except Exception as e:
        print(f"Error saving timer rule order: {e}")
    files_to_delete = existing_files - set(current_files)
    for fname in files_to_delete:
        if fname.endswith('_timer_rule.json') or fname == order_filename:
            try:
                os.remove(os.path.join(timer_rules_dir, fname))
                print(f"Deleted old timer rule file: {fname}")
            except Exception as e:
                print(f"Error deleting old timer rule file {fname}: {e}")

def _load_timer_rules(main_ui, tab_index):
    if not (0 <= tab_index < len(main_ui.tabs_data) and main_ui.tabs_data[tab_index] is not None):
        print(f"Error: Cannot load timer rules for invalid tab index {tab_index}")
        return []
    tab_data = main_ui.tabs_data[tab_index]
    rules_dir = tab_data.get('rules_dir')
    if not rules_dir:
        print(f"Error loading timer rules: No rules_dir for tab {tab_index}")
        return []
    timer_rules_dir = os.path.join(rules_dir, "timer_rules")
    if not os.path.exists(timer_rules_dir):
        os.makedirs(timer_rules_dir, exist_ok=True)
        print(f"Created timer rules directory: {timer_rules_dir}")
        return []
    loaded_rules = []
    order_filepath = os.path.join(timer_rules_dir, "_timer_rules_order.json")
    rule_files = {fname: os.path.join(timer_rules_dir, fname)
                 for fname in os.listdir(timer_rules_dir) 
                 if fname.endswith('_timer_rule.json')}
    ordered_rule_ids = []
    if os.path.exists(order_filepath):
        try:
            with open(order_filepath, 'r', encoding='utf-8') as f:
                ordered_rule_ids = json.load(f)

        except Exception as e:
            print(f"Error loading timer rule order file {order_filepath}: {e}. Falling back to directory scan.")
            ordered_rule_ids = []
    if ordered_rule_ids:
        loaded_rules_map = {}
        valid_ordered_ids = []
        for rule_id in ordered_rule_ids:
            filename = f"{rule_id}_timer_rule.json"
            fpath = rule_files.get(filename)
            
            if fpath and os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        rule = json.load(f)
                        loaded_rules_map[rule_id] = rule
                        valid_ordered_ids.append(rule_id)
                        print(f"  Loaded timer rule: {rule_id}")
                except Exception as e:
                    print(f"Error loading timer rule file {fpath} specified in order file: {e}")
            else:
                print(f"Warning: Timer rule file {filename} listed in order file not found or already processed. Skipping.")
        loaded_rules = [loaded_rules_map[rule_id] for rule_id in valid_ordered_ids]
        found_rule_files = set(loaded_rules_map.keys())
        all_rule_ids_from_files = {fname.replace('_timer_rule.json', '') for fname in rule_files.keys()}
        orphaned_rules = all_rule_ids_from_files - found_rule_files
        if orphaned_rules:
            print(f"Warning: Found timer rule files not in order file: {orphaned_rules}. Adding to end.")
            needs_resave = False
            for rule_id in sorted(list(orphaned_rules)):
                filename = f"{rule_id}_timer_rule.json"
                fpath = rule_files.get(filename)
                if fpath:
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            rule = json.load(f)
                            loaded_rules.append(rule)
                            valid_ordered_ids.append(rule_id)
                            needs_resave = True
                    except Exception as e:
                        print(f"Error loading orphaned timer rule file {fpath}: {e}")
            if needs_resave:
                try:
                    with open(order_filepath, 'w', encoding='utf-8') as f:
                        json.dump(valid_ordered_ids, f, indent=2, ensure_ascii=False)
                    print(f"Resaved timer rule order to include orphaned rules: {order_filepath}")
                except Exception as e:
                    print(f"Error resaving timer rule order file: {e}")
    else:
        rule_ids_loaded = []
        sorted_filenames = sorted(rule_files.keys())
        for fname in sorted_filenames:
            fpath = rule_files[fname]
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    rule = json.load(f)
                    loaded_rules.append(rule)
                    rule_id = rule.get('id')
                    if rule_id:
                        rule_ids_loaded.append(rule_id)
                    else:
                        fallback_id = fname.replace('_timer_rule.json', '')
                        print(f"Warning: Timer rule in {fname} missing 'id'. Using filename '{fallback_id}' for ordering.")
                        rule_ids_loaded.append(fallback_id)
            except Exception as e:
                print(f"Error loading timer rule from {fpath} during fallback scan: {e}")
        if loaded_rules:
            try:
                with open(order_filepath, 'w', encoding='utf-8') as f:
                    json.dump(rule_ids_loaded, f, indent=2, ensure_ascii=False)
                print(f"Created initial timer rule order file based on directory scan: {order_filepath}")
            except Exception as e:
                print(f"Error saving initial timer rule order file: {e}")
    return loaded_rules 

def get_main_ui(widget):
    parent = widget.parentWidget()
    while parent:
        if hasattr(parent, 'add_rule_sound'):
            return parent
        parent = parent.parentWidget()
    return None
class TimerManager:
    timer_action_signal = pyqtSignal(object, dict, object)