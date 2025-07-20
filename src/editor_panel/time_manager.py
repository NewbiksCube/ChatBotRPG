from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame, QSizePolicy, QRadioButton, QButtonGroup, QLineEdit, QGridLayout, QListWidget, QComboBox, QSpinBox, QDateTimeEdit, QDoubleSpinBox, QScrollArea
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
import json
import os
from datetime import datetime
import re



class TimeManager(QWidget):
    def __init__(self, theme_colors, parent=None, workflow_data_dir=None, main_ui=None, tab_data=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.workflow_data_dir = workflow_data_dir
        self.main_ui = main_ui
        self.tab_data = tab_data
        self.setObjectName("TimeManagerWidget")
        self.time_passage_data = self._load_time_passage_data_initial()
        self.last_realtime_update = None
        self._init_ui()
        self._apply_loaded_settings()
        self._connect_signals()
    
    def set_tab_data(self, tab_data):
        self.tab_data = tab_data

    def save_state_on_shutdown(self):
        if not self.main_ui or not self.tab_data:
            return
        try:
            tab_index = self.main_ui.tabs_data.index(self.tab_data) if self.tab_data in self.main_ui.tabs_data else -1
            if tab_index < 0:
                return
            variables = self.main_ui._load_variables(tab_index)
            variables['_timer_shutdown_graceful'] = True
            variables['_timer_shutdown_time'] = datetime.now().isoformat()
            self.main_ui._save_variables(tab_index, variables)
        except Exception as e:
            print(f"[TIME MANAGER] Error saving shutdown state: {e}")

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        scroll_area = QScrollArea()
        scroll_area.setObjectName("TimeManagerScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        game_time_mode_label = QLabel("Game Time Mode")
        game_time_mode_label.setObjectName("GameTimeModeLabel")
        game_time_mode_label.setFont(QFont('Consolas', 9, QFont.Bold))
        game_time_mode_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(game_time_mode_label)
        time_mode_layout = QHBoxLayout()
        time_mode_layout.setSpacing(20)
        time_mode_layout.addStretch()
        self.time_mode_group = QButtonGroup(self)
        self.sync_computer_radio = QRadioButton("Real World (Sync to Clock)")
        self.sync_computer_radio.setObjectName("SyncComputerRadio")
        self.sync_computer_radio.setFont(QFont('Consolas', 8))
        self.time_mode_group.addButton(self.sync_computer_radio, 0)
        time_mode_layout.addWidget(self.sync_computer_radio)
        self.game_world_radio = QRadioButton("Game World")
        self.game_world_radio.setObjectName("GameWorldRadio")
        self.game_world_radio.setFont(QFont('Consolas', 8))
        self.game_world_radio.setChecked(True)
        self.time_mode_group.addButton(self.game_world_radio, 1)
        time_mode_layout.addWidget(self.game_world_radio)
        time_mode_layout.addStretch()
        layout.addLayout(time_mode_layout)
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet(f"background-color: {self.theme_colors.get('base_color', '#00E5E5')}; height: 1px; border: none; margin: 5px 0;")
        layout.addWidget(separator1)
        self.calendar_editor_widget = self._create_calendar_editor()
        layout.addWidget(self.calendar_editor_widget)
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet(f"background-color: {self.theme_colors.get('base_color', '#00E5E5')}; height: 1px; border: none; margin: 5px 0;")
        layout.addWidget(separator2)
        self.time_triggers_widget = self._create_time_triggers_section()
        layout.addWidget(self.time_triggers_widget)
        layout.addStretch()
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._apply_styling()
        self._update_section_visibility()

    def _create_calendar_editor(self):
        widget = QWidget()
        widget.setObjectName("CalendarEditorWidget")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title_label = QLabel("Calendar Editor")
        title_label.setObjectName("TimeManagerSectionTitle")
        title_label.setFont(QFont('Consolas', 9, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        months_group = QFrame()
        months_group.setObjectName("TimeManagerGroup")
        months_layout = QVBoxLayout(months_group)
        months_layout.setContentsMargins(8, 6, 8, 6)
        months_label = QLabel("Month Names:")
        months_label.setObjectName("TimeManagerGroupLabel")
        months_label.setFont(QFont('Consolas', 8, QFont.Bold))
        months_layout.addWidget(months_label)
        months_grid = QGridLayout()
        months_grid.setSpacing(5)
        self.month_inputs = []
        default_months = ["January", "February", "March", "April", "May", "June",
                         "July", "August", "September", "October", "November", "December"]
        
        for i, month in enumerate(default_months):
            month_label = QLabel(f"{i+1}:")
            month_label.setObjectName("TimeManagerFieldLabel")
            month_input = QLineEdit(self.time_passage_data.get('months', {}).get(str(i), month))
            month_input.setObjectName("TimeManagerInput")
            month_input.setFont(QFont('Consolas', 8))
            month_input.setPlaceholderText(f"Month {i+1}")
            self.month_inputs.append(month_input)
            months_grid.addWidget(month_label, i // 3, (i % 3) * 2)
            months_grid.addWidget(month_input, i // 3, (i % 3) * 2 + 1)
        months_layout.addLayout(months_grid)
        layout.addWidget(months_group)
        days_group = QFrame()
        days_group.setObjectName("TimeManagerGroup")
        days_layout = QVBoxLayout(days_group)
        days_layout.setContentsMargins(8, 6, 8, 6)
        days_label = QLabel("Day Names:")
        days_label.setObjectName("TimeManagerGroupLabel")
        days_label.setFont(QFont('Consolas', 8, QFont.Bold))
        days_layout.addWidget(days_label)
        days_grid = QGridLayout()
        days_grid.setSpacing(5)
        self.day_inputs = []
        default_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for i, day in enumerate(default_days):
            day_label = QLabel(f"{i+1}:")
            day_label.setObjectName("TimeManagerFieldLabel")
            day_input = QLineEdit(self.time_passage_data.get('days', {}).get(str(i), day))
            day_input.setObjectName("TimeManagerInput")
            day_input.setFont(QFont('Consolas', 8))
            day_input.setPlaceholderText(f"Day {i+1}")
            self.day_inputs.append(day_input)
            days_grid.addWidget(day_label, 0, i)
            days_grid.addWidget(day_input, 1, i)
        days_layout.addLayout(days_grid)
        layout.addWidget(days_group)
        return widget

    def _create_time_triggers_section(self):
        widget = QWidget()
        widget.setObjectName("TimeTriggersWidget")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        title_label = QLabel("Time-based Variable Triggers")
        title_label.setObjectName("TimeManagerSectionTitle")
        title_label.setFont(QFont('Consolas', 9, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        self.triggers_list = QListWidget()
        self.triggers_list.setObjectName("TimeManagerTriggersList")
        self.triggers_list.setFont(QFont('Consolas', 8))
        self.triggers_list.setMaximumHeight(150)
        self.triggers_list.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(self.triggers_list)
        editor_frame = QFrame()
        editor_frame.setObjectName("TimeManagerGroup")
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(8, 6, 8, 6)
        trigger_type_label = QLabel("Trigger Type:")
        trigger_type_label.setObjectName("TimeManagerGroupLabel")
        trigger_type_label.setFont(QFont('Consolas', 8, QFont.Bold))
        editor_layout.addWidget(trigger_type_label)
        trigger_type_layout = QHBoxLayout()
        self.trigger_type_group = QButtonGroup(self)
        self.exact_time_radio = QRadioButton("Exact Time")
        self.exact_time_radio.setObjectName("TimeManagerTriggerTypeRadio")
        self.exact_time_radio.setFont(QFont('Consolas', 8))
        self.exact_time_radio.setChecked(True)
        self.trigger_type_group.addButton(self.exact_time_radio, 0)
        trigger_type_layout.addWidget(self.exact_time_radio)
        self.time_range_radio = QRadioButton("Time Range")
        self.time_range_radio.setObjectName("TimeManagerTriggerTypeRadio")
        self.time_range_radio.setFont(QFont('Consolas', 8))
        self.trigger_type_group.addButton(self.time_range_radio, 1)
        trigger_type_layout.addWidget(self.time_range_radio)
        trigger_type_layout.addStretch()
        editor_layout.addLayout(trigger_type_layout)
        condition_label = QLabel("Trigger Condition:")
        condition_label.setObjectName("TimeManagerGroupLabel")
        condition_label.setFont(QFont('Consolas', 8, QFont.Bold))
        editor_layout.addWidget(condition_label)
        self.exact_time_widget = QWidget()
        exact_time_layout = QVBoxLayout(self.exact_time_widget)
        exact_time_layout.setContentsMargins(0, 0, 0, 0)
        condition_layout = QHBoxLayout()
        day_label = QLabel("Day:")
        day_label.setObjectName("TimeManagerFieldLabel")
        self.day_combo = QComboBox()
        self.day_combo.setObjectName("TimeManagerComboBox")
        self.day_combo.addItem("Any Day")
        self.day_combo.setFont(QFont('Consolas', 8))
        condition_layout.addWidget(day_label)
        condition_layout.addWidget(self.day_combo)
        month_label = QLabel("Month:")
        month_label.setObjectName("TimeManagerFieldLabel")
        self.month_combo = QComboBox()
        self.month_combo.setObjectName("TimeManagerComboBox")
        self.month_combo.addItem("Any Month")
        self.month_combo.setFont(QFont('Consolas', 8))
        condition_layout.addWidget(month_label)
        condition_layout.addWidget(self.month_combo)
        day_of_month_label = QLabel("Day of Month:")
        day_of_month_label.setObjectName("TimeManagerFieldLabel")
        self.day_of_month_spin = QSpinBox()
        self.day_of_month_spin.setObjectName("TimeManagerSpinBox")
        self.day_of_month_spin.setRange(0, 31)
        self.day_of_month_spin.setValue(0)
        self.day_of_month_spin.setSpecialValueText("Any Day of Month")
        self.day_of_month_spin.setFont(QFont('Consolas', 8))
        condition_layout.addWidget(day_of_month_label)
        condition_layout.addWidget(self.day_of_month_spin)
        year_label = QLabel("Year:")
        year_label.setObjectName("TimeManagerFieldLabel")
        self.year_spin = QSpinBox()
        self.year_spin.setObjectName("TimeManagerSpinBox")
        self.year_spin.setRange(0, 9999)
        self.year_spin.setValue(0)
        self.year_spin.setSpecialValueText("Any Year")
        self.year_spin.setFont(QFont('Consolas', 8))
        condition_layout.addWidget(year_label)
        condition_layout.addWidget(self.year_spin)
        hour_label = QLabel("Hour:")
        hour_label.setObjectName("TimeManagerFieldLabel")
        self.hour_spin = QSpinBox()
        self.hour_spin.setObjectName("TimeManagerSpinBox")
        self.hour_spin.setRange(-1, 23)
        self.hour_spin.setValue(-1)
        self.hour_spin.setSpecialValueText("Any Hour")
        self.hour_spin.setFont(QFont('Consolas', 8))
        condition_layout.addWidget(hour_label)
        condition_layout.addWidget(self.hour_spin)
        minute_label = QLabel("Minute:")
        minute_label.setObjectName("TimeManagerFieldLabel")
        self.minute_spin = QSpinBox()
        self.minute_spin.setObjectName("TimeManagerSpinBox")
        self.minute_spin.setRange(-1, 59)
        self.minute_spin.setValue(-1)
        self.minute_spin.setSpecialValueText("Any Minute")
        self.minute_spin.setFont(QFont('Consolas', 8))
        condition_layout.addWidget(minute_label)
        condition_layout.addWidget(self.minute_spin)
        exact_time_layout.addLayout(condition_layout)
        self.time_range_widget = QWidget()
        time_range_layout = QVBoxLayout(self.time_range_widget)
        time_range_layout.setContentsMargins(0, 0, 0, 0)
        from_condition_layout = QHBoxLayout()
        from_label = QLabel("From:")
        from_label.setObjectName("TimeManagerFieldLabel")
        from_label.setFont(QFont('Consolas', 8, QFont.Bold))
        from_label.setMinimumWidth(40)
        from_condition_layout.addWidget(from_label)
        from_day_label = QLabel("Day:")
        from_day_label.setObjectName("TimeManagerFieldLabel")
        self.from_day_combo = QComboBox()
        self.from_day_combo.setObjectName("TimeManagerComboBox")
        self.from_day_combo.addItem("Any Day")
        self.from_day_combo.setFont(QFont('Consolas', 8))
        from_condition_layout.addWidget(from_day_label)
        from_condition_layout.addWidget(self.from_day_combo)
        from_month_label = QLabel("Month:")
        from_month_label.setObjectName("TimeManagerFieldLabel")
        self.from_month_combo = QComboBox()
        self.from_month_combo.setObjectName("TimeManagerComboBox")
        self.from_month_combo.addItem("Any Month")
        self.from_month_combo.setFont(QFont('Consolas', 8))
        from_condition_layout.addWidget(from_month_label)
        from_condition_layout.addWidget(self.from_month_combo)
        from_day_of_month_label = QLabel("Day of Month:")
        from_day_of_month_label.setObjectName("TimeManagerFieldLabel")
        self.from_day_of_month_spin = QSpinBox()
        self.from_day_of_month_spin.setObjectName("TimeManagerSpinBox")
        self.from_day_of_month_spin.setRange(0, 31)
        self.from_day_of_month_spin.setValue(0)
        self.from_day_of_month_spin.setSpecialValueText("Any Day of Month")
        self.from_day_of_month_spin.setFont(QFont('Consolas', 8))
        from_condition_layout.addWidget(from_day_of_month_label)
        from_condition_layout.addWidget(self.from_day_of_month_spin)
        from_year_label = QLabel("Year:")
        from_year_label.setObjectName("TimeManagerFieldLabel")
        self.from_year_spin = QSpinBox()
        self.from_year_spin.setObjectName("TimeManagerSpinBox")
        self.from_year_spin.setRange(0, 9999)
        self.from_year_spin.setValue(0)
        self.from_year_spin.setSpecialValueText("Any Year")
        self.from_year_spin.setFont(QFont('Consolas', 8))
        from_condition_layout.addWidget(from_year_label)
        from_condition_layout.addWidget(self.from_year_spin)
        from_hour_label = QLabel("Hour:")
        from_hour_label.setObjectName("TimeManagerFieldLabel")
        self.from_hour_spin = QSpinBox()
        self.from_hour_spin.setObjectName("TimeManagerSpinBox")
        self.from_hour_spin.setRange(-1, 23)
        self.from_hour_spin.setValue(-1)
        self.from_hour_spin.setSpecialValueText("Any Hour")
        self.from_hour_spin.setFont(QFont('Consolas', 8))
        from_condition_layout.addWidget(from_hour_label)
        from_condition_layout.addWidget(self.from_hour_spin)
        from_minute_label = QLabel("Minute:")
        from_minute_label.setObjectName("TimeManagerFieldLabel")
        self.from_minute_spin = QSpinBox()
        self.from_minute_spin.setObjectName("TimeManagerSpinBox")
        self.from_minute_spin.setRange(-1, 59)
        self.from_minute_spin.setValue(-1)
        self.from_minute_spin.setSpecialValueText("Any Minute")
        self.from_minute_spin.setFont(QFont('Consolas', 8))
        from_condition_layout.addWidget(from_minute_label)
        from_condition_layout.addWidget(self.from_minute_spin)
        time_range_layout.addLayout(from_condition_layout)
        to_condition_layout = QHBoxLayout()
        to_label = QLabel("To:")
        to_label.setObjectName("TimeManagerFieldLabel")
        to_label.setFont(QFont('Consolas', 8, QFont.Bold))
        to_label.setMinimumWidth(40)
        to_condition_layout.addWidget(to_label)
        to_day_label = QLabel("Day:")
        to_day_label.setObjectName("TimeManagerFieldLabel")
        self.to_day_combo = QComboBox()
        self.to_day_combo.setObjectName("TimeManagerComboBox")
        self.to_day_combo.addItem("Any Day")
        self.to_day_combo.setFont(QFont('Consolas', 8))
        to_condition_layout.addWidget(to_day_label)
        to_condition_layout.addWidget(self.to_day_combo)
        to_month_label = QLabel("Month:")
        to_month_label.setObjectName("TimeManagerFieldLabel")
        self.to_month_combo = QComboBox()
        self.to_month_combo.setObjectName("TimeManagerComboBox")
        self.to_month_combo.addItem("Any Month")
        self.to_month_combo.setFont(QFont('Consolas', 8))
        to_condition_layout.addWidget(to_month_label)
        to_condition_layout.addWidget(self.to_month_combo)
        to_day_of_month_label = QLabel("Day of Month:")
        to_day_of_month_label.setObjectName("TimeManagerFieldLabel")
        self.to_day_of_month_spin = QSpinBox()
        self.to_day_of_month_spin.setObjectName("TimeManagerSpinBox")
        self.to_day_of_month_spin.setRange(0, 31)
        self.to_day_of_month_spin.setValue(0)
        self.to_day_of_month_spin.setSpecialValueText("Any Day of Month")
        self.to_day_of_month_spin.setFont(QFont('Consolas', 8))
        to_condition_layout.addWidget(to_day_of_month_label)
        to_condition_layout.addWidget(self.to_day_of_month_spin)
        to_year_label = QLabel("Year:")
        to_year_label.setObjectName("TimeManagerFieldLabel")
        self.to_year_spin = QSpinBox()
        self.to_year_spin.setObjectName("TimeManagerSpinBox")
        self.to_year_spin.setRange(0, 9999)
        self.to_year_spin.setValue(0)
        self.to_year_spin.setSpecialValueText("Any Year")
        self.to_year_spin.setFont(QFont('Consolas', 8))
        to_condition_layout.addWidget(to_year_label)
        to_condition_layout.addWidget(self.to_year_spin)
        to_hour_label = QLabel("Hour:")
        to_hour_label.setObjectName("TimeManagerFieldLabel")
        self.to_hour_spin = QSpinBox()
        self.to_hour_spin.setObjectName("TimeManagerSpinBox")
        self.to_hour_spin.setRange(-1, 23)
        self.to_hour_spin.setValue(-1)
        self.to_hour_spin.setSpecialValueText("Any Hour")
        self.to_hour_spin.setFont(QFont('Consolas', 8))
        to_condition_layout.addWidget(to_hour_label)
        to_condition_layout.addWidget(self.to_hour_spin)
        to_minute_label = QLabel("Minute:")
        to_minute_label.setObjectName("TimeManagerFieldLabel")
        self.to_minute_spin = QSpinBox()
        self.to_minute_spin.setObjectName("TimeManagerSpinBox")
        self.to_minute_spin.setRange(-1, 59)
        self.to_minute_spin.setValue(-1)
        self.to_minute_spin.setSpecialValueText("Any Minute")
        self.to_minute_spin.setFont(QFont('Consolas', 8))
        to_condition_layout.addWidget(to_minute_label)
        to_condition_layout.addWidget(self.to_minute_spin)
        time_range_layout.addLayout(to_condition_layout)
        editor_layout.addWidget(self.exact_time_widget)
        editor_layout.addWidget(self.time_range_widget)
        self.exact_time_widget.setVisible(True)
        self.time_range_widget.setVisible(False)
        action_label = QLabel("Variable Action:")
        action_label.setObjectName("TimeManagerGroupLabel")
        action_label.setFont(QFont('Consolas', 8, QFont.Bold))
        editor_layout.addWidget(action_label)
        action_layout = QHBoxLayout()
        var_name_label = QLabel("Set Variable:")
        var_name_label.setObjectName("TimeManagerFieldLabel")
        action_layout.addWidget(var_name_label)
        self.var_name_input = QLineEdit()
        self.var_name_input.setObjectName("TimeManagerInput")
        self.var_name_input.setFont(QFont('Consolas', 8))
        self.var_name_input.setPlaceholderText("Variable name")
        action_layout.addWidget(self.var_name_input)
        var_value_label = QLabel("To Value:")
        var_value_label.setObjectName("TimeManagerFieldLabel")
        action_layout.addWidget(var_value_label)
        self.var_value_input = QLineEdit()
        self.var_value_input.setObjectName("TimeManagerInput")
        self.var_value_input.setFont(QFont('Consolas', 8))
        self.var_value_input.setPlaceholderText("Variable value")
        action_layout.addWidget(self.var_value_input)
        revert_layout = QHBoxLayout()
        self.revert_checkbox = QRadioButton("Revert when condition no longer met")
        self.revert_checkbox.setObjectName("TimeManagerRevertCheckbox")
        self.revert_checkbox.setFont(QFont('Consolas', 8))
        self.revert_checkbox.setToolTip("When enabled, the variable will be reverted to its previous value when the time condition is no longer met")
        revert_layout.addWidget(self.revert_checkbox)
        revert_value_label = QLabel("Revert To:")
        revert_value_label.setObjectName("TimeManagerFieldLabel")
        revert_layout.addWidget(revert_value_label)
        self.revert_value_input = QLineEdit()
        self.revert_value_input.setObjectName("TimeManagerInput")
        self.revert_value_input.setFont(QFont('Consolas', 8))
        self.revert_value_input.setPlaceholderText("Value to revert to (leave empty to restore original)")
        revert_layout.addWidget(self.revert_value_input)
        editor_layout.addLayout(revert_layout)
        editor_layout.addLayout(action_layout)
        buttons_layout = QHBoxLayout()
        self.add_trigger_btn = QPushButton("Add Trigger")
        self.add_trigger_btn.setObjectName("TimeManagerButton")
        self.add_trigger_btn.setFont(QFont('Consolas', 8))
        buttons_layout.addWidget(self.add_trigger_btn)
        self.remove_trigger_btn = QPushButton("Remove Selected")
        self.remove_trigger_btn.setObjectName("TimeManagerButton")
        self.remove_trigger_btn.setFont(QFont('Consolas', 8))
        buttons_layout.addWidget(self.remove_trigger_btn)
        buttons_layout.addStretch()
        editor_layout.addLayout(buttons_layout)
        layout.addWidget(editor_frame)
        return widget

    def _connect_signals(self):
        self.time_mode_group.buttonClicked.connect(self._on_time_mode_changed)
        self.trigger_type_group.buttonClicked.connect(self._on_trigger_type_changed)
        self.add_trigger_btn.clicked.connect(self._add_trigger)
        self.remove_trigger_btn.clicked.connect(self._remove_trigger)
        for month_input in self.month_inputs:
            month_input.textChanged.connect(self._save_calendar_data)
        for day_input in self.day_inputs:
            day_input.textChanged.connect(self._save_calendar_data)

    def _on_time_mode_changed(self):
        self._update_section_visibility()
        self._save_time_mode()

    def _on_trigger_type_changed(self):
        is_exact_time = self.exact_time_radio.isChecked()
        self.exact_time_widget.setVisible(is_exact_time)
        self.time_range_widget.setVisible(not is_exact_time)
        if not is_exact_time:
            self._update_range_combo_boxes()

    def _update_section_visibility(self):
        is_game_world = self.game_world_radio.isChecked()
        self.calendar_editor_widget.setVisible(is_game_world)
        self._update_combo_boxes()
        self._update_time_multiplier_visibility()
    
    def _update_time_multiplier_visibility(self):
        pass

    def _update_combo_boxes(self):
        current_day = self.day_combo.currentText()
        self.day_combo.clear()
        self.day_combo.addItem("Any Day")
        for day_input in self.day_inputs:
            if day_input.text().strip():
                self.day_combo.addItem(day_input.text().strip())
        index = self.day_combo.findText(current_day)
        if index >= 0:
            self.day_combo.setCurrentIndex(index)
        current_month = self.month_combo.currentText()
        self.month_combo.clear()
        self.month_combo.addItem("Any Month")
        for month_input in self.month_inputs:
            if month_input.text().strip():
                self.month_combo.addItem(month_input.text().strip())
        index = self.month_combo.findText(current_month)
        if index >= 0:
            self.month_combo.setCurrentIndex(index)
        self._update_range_combo_boxes()

    def _update_range_combo_boxes(self):
        current_from_day = self.from_day_combo.currentText()
        self.from_day_combo.clear()
        self.from_day_combo.addItem("Any Day")
        for day_input in self.day_inputs:
            if day_input.text().strip():
                self.from_day_combo.addItem(day_input.text().strip())
        index = self.from_day_combo.findText(current_from_day)
        if index >= 0:
            self.from_day_combo.setCurrentIndex(index)
        
        current_from_month = self.from_month_combo.currentText()
        self.from_month_combo.clear()
        self.from_month_combo.addItem("Any Month")
        for month_input in self.month_inputs:
            if month_input.text().strip():
                self.from_month_combo.addItem(month_input.text().strip())
        index = self.from_month_combo.findText(current_from_month)
        if index >= 0:
            self.from_month_combo.setCurrentIndex(index)
        
        # Update To combo boxes
        current_to_day = self.to_day_combo.currentText()
        self.to_day_combo.clear()
        self.to_day_combo.addItem("Any Day")
        for day_input in self.day_inputs:
            if day_input.text().strip():
                self.to_day_combo.addItem(day_input.text().strip())
        index = self.to_day_combo.findText(current_to_day)
        if index >= 0:
            self.to_day_combo.setCurrentIndex(index)
        
        current_to_month = self.to_month_combo.currentText()
        self.to_month_combo.clear()
        self.to_month_combo.addItem("Any Month")
        for month_input in self.month_inputs:
            if month_input.text().strip():
                self.to_month_combo.addItem(month_input.text().strip())
        index = self.to_month_combo.findText(current_to_month)
        if index >= 0:
            self.to_month_combo.setCurrentIndex(index)

    def _add_trigger(self):
        var_name = self.var_name_input.text().strip()
        var_value = self.var_value_input.text().strip()
        if not var_name or not var_value:
            return
        is_exact_time = self.exact_time_radio.isChecked()
        if is_exact_time:
            conditions = []
            if self.day_combo.currentText() != "Any Day":
                conditions.append(f"Day: {self.day_combo.currentText()}")
            if self.month_combo.currentText() != "Any Month":
                conditions.append(f"Month: {self.month_combo.currentText()}")
            if self.day_of_month_spin.value() > 0:
                conditions.append(f"Day of Month: {self.day_of_month_spin.value()}")
            if self.year_spin.value() > 0:
                conditions.append(f"Year: {self.year_spin.value()}")
            if self.hour_spin.value() >= 0:
                conditions.append(f"Hour: {self.hour_spin.value()}")
            if self.minute_spin.value() >= 0:
                conditions.append(f"Minute: {self.minute_spin.value()}")
            condition_str = ", ".join(conditions) if conditions else "Always"
        else:
            from_conditions = []
            if self.from_day_combo.currentText() != "Any Day":
                from_conditions.append(f"Day: {self.from_day_combo.currentText()}")
            if self.from_month_combo.currentText() != "Any Month":
                from_conditions.append(f"Month: {self.from_month_combo.currentText()}")
            if self.from_day_of_month_spin.value() > 0:
                from_conditions.append(f"Day of Month: {self.from_day_of_month_spin.value()}")
            if self.from_year_spin.value() > 0:
                from_conditions.append(f"Year: {self.from_year_spin.value()}")
            if self.from_hour_spin.value() >= 0:
                from_conditions.append(f"Hour: {self.from_hour_spin.value()}")
            if self.from_minute_spin.value() >= 0:
                from_conditions.append(f"Minute: {self.from_minute_spin.value()}")
            
            to_conditions = []
            if self.to_day_combo.currentText() != "Any Day":
                to_conditions.append(f"Day: {self.to_day_combo.currentText()}")
            if self.to_month_combo.currentText() != "Any Month":
                to_conditions.append(f"Month: {self.to_month_combo.currentText()}")
            if self.to_day_of_month_spin.value() > 0:
                to_conditions.append(f"Day of Month: {self.to_day_of_month_spin.value()}")
            if self.to_year_spin.value() > 0:
                to_conditions.append(f"Year: {self.to_year_spin.value()}")
            if self.to_hour_spin.value() >= 0:
                to_conditions.append(f"Hour: {self.to_hour_spin.value()}")
            if self.to_minute_spin.value() >= 0:
                to_conditions.append(f"Minute: {self.to_minute_spin.value()}")
            from_str = ", ".join(from_conditions) if from_conditions else "Always"
            to_str = ", ".join(to_conditions) if to_conditions else "Always"
            condition_str = f"From ({from_str}) To ({to_str})"
        trigger_text = f"{condition_str} → Set '{var_name}' = '{var_value}'"
        if self.revert_checkbox.isChecked():
            revert_value = self.revert_value_input.text().strip()
            if revert_value:
                trigger_text += f" [Revert to: '{revert_value}']"
            else:
                trigger_text += " [Revert to original]"
        self.triggers_list.addItem(trigger_text)
        self._clear_trigger_inputs()
        self._save_triggers_data()

    def _remove_trigger(self):
        current_row = self.triggers_list.currentRow()
        if current_row >= 0:
            self.triggers_list.takeItem(current_row)
            self._save_triggers_data()

    def _clear_trigger_inputs(self):
        self.day_combo.setCurrentIndex(0)
        self.month_combo.setCurrentIndex(0)
        self.day_of_month_spin.setValue(0)
        self.year_spin.setValue(0)
        self.hour_spin.setValue(-1)
        self.minute_spin.setValue(-1)
        self.from_day_combo.setCurrentIndex(0)
        self.from_month_combo.setCurrentIndex(0)
        self.from_day_of_month_spin.setValue(0)
        self.from_year_spin.setValue(0)
        self.from_hour_spin.setValue(-1)
        self.from_minute_spin.setValue(-1)
        self.to_day_combo.setCurrentIndex(0)
        self.to_month_combo.setCurrentIndex(0)
        self.to_day_of_month_spin.setValue(0)
        self.to_year_spin.setValue(0)
        self.to_hour_spin.setValue(-1)
        self.to_minute_spin.setValue(-1)
        self.var_name_input.clear()
        self.var_value_input.clear()
        self.revert_checkbox.setChecked(False)
        self.revert_value_input.clear()

    def _load_time_passage_data_initial(self):
        if not self.workflow_data_dir:
            return {}
        file_path = os.path.join(self.workflow_data_dir, "resources", "data files", "settings", "time_passage.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            except Exception:
                return {}
        return {}
    
    def _load_time_passage_data(self):
        if not self.workflow_data_dir:
            return {}
        file_path = os.path.join(self.workflow_data_dir, "resources", "data files", "settings", "time_passage.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            except Exception:
                return {}
        return {}
    def _apply_loaded_settings(self):
        if not self.workflow_data_dir or not self.time_passage_data:
            return
    def _save_time_passage_data(self):
        if not self.workflow_data_dir:
            return
        settings_dir = os.path.join(self.workflow_data_dir, "resources", "data files", "settings")
        os.makedirs(settings_dir, exist_ok=True)
        file_path = os.path.join(settings_dir, "time_passage.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.time_passage_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[DEBUG] _save_time_passage_data - IOError: {e}")
        except Exception as e:
            print(f"[DEBUG] _save_time_passage_data - Exception: {e}")
    def _save_time_mode(self):
        time_mode = 'game_world' if self.game_world_radio.isChecked() else 'real_world'
        self.time_passage_data['time_mode'] = time_mode
        self._save_time_passage_data()

    def _save_calendar_data(self):
        months = {}
        for i, month_input in enumerate(self.month_inputs):
            if month_input.text().strip():
                months[str(i)] = month_input.text().strip()
        self.time_passage_data['months'] = months
        days = {}
        for i, day_input in enumerate(self.day_inputs):
            if day_input.text().strip():
                days[str(i)] = day_input.text().strip()
        self.time_passage_data['days'] = days
        self._save_time_passage_data()
        self._update_combo_boxes()
    def _save_triggers_data(self):
        triggers = []
        for i in range(self.triggers_list.count()):
            triggers.append(self.triggers_list.item(i).text())
        self.time_passage_data['triggers'] = triggers
        self._save_time_passage_data()

    def _parse_trigger_text(self, trigger_text):
        try:
            revert_enabled = False
            revert_value = None
            revert_match = re.search(r'\[Revert to: \'([^\']*)\'\]', trigger_text)
            if revert_match:
                revert_enabled = True
                revert_value = revert_match.group(1)
                trigger_text = trigger_text.replace(revert_match.group(0), '').strip()
            elif '[Revert to original]' in trigger_text:
                revert_enabled = True
                revert_value = None
                trigger_text = trigger_text.replace('[Revert to original]', '').strip()
            parts = trigger_text.split(' → Set ')
            if len(parts) != 2:
                return None
            condition_str = parts[0].strip()
            action_str = parts[1].strip()
            action_match = re.match(r"'([^']+)'\s*=\s*'([^']*)'", action_str)
            if not action_match:
                return None
            var_name = action_match.group(1)
            var_value = action_match.group(2)
            conditions = {}
            if condition_str != "Always":
                for condition_part in condition_str.split(', '):
                    if ':' in condition_part:
                        key, value = condition_part.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if key == "Day":
                            conditions['day'] = value
                        elif key == "Month":
                            conditions['month'] = value
                        elif key == "Day of Month":
                            conditions['day_of_month'] = int(value)
                        elif key == "Year":
                            conditions['year'] = int(value)
                        elif key == "Hour":
                            conditions['hour'] = int(value)
                        elif key == "Minute":
                            conditions['minute'] = int(value)
            return {
                'conditions': conditions,
                'var_name': var_name,
                'var_value': var_value,
                'revert_enabled': revert_enabled,
                'revert_value': revert_value,
                'original_text': trigger_text
            }
        except Exception as e:
            print(f"Error parsing trigger '{trigger_text}': {e}")
            return None

    def _check_time_triggers(self):
        if not self.main_ui or not self.tab_data:
            return
        try:
            tab_index = self.main_ui.tabs_data.index(self.tab_data) if self.tab_data in self.main_ui.tabs_data else -1
            if tab_index < 0:
                return
            variables = self.main_ui._load_variables(tab_index)
            current_datetime_str = variables.get('datetime')
            if not current_datetime_str:
                return
            try:
                current_datetime = datetime.fromisoformat(current_datetime_str)
            except (ValueError, TypeError):
                return
            triggers = self.time_passage_data.get('triggers', [])
            if not triggers:
                return
            executed_triggers = variables.get('_executed_time_triggers', [])
            trigger_original_values = variables.get('_trigger_original_values', {})
            newly_executed = []
            reverted_triggers = []
            for trigger_text in triggers:
                trigger_data = self._parse_trigger_text(trigger_text)
                if not trigger_data:
                    continue
                conditions_match = self._trigger_conditions_match(trigger_data['conditions'], current_datetime)
                if trigger_text in executed_triggers:
                    if not conditions_match and trigger_data.get('revert_enabled', False):
                        if trigger_data['revert_value'] is not None:
                            revert_value = trigger_data['revert_value']
                        else:
                            revert_value = trigger_original_values.get(trigger_text, {}).get(trigger_data['var_name'])
                        if revert_value is not None:
                            variables[trigger_data['var_name']] = revert_value
                            reverted_triggers.append(trigger_text)
                        executed_triggers.remove(trigger_text)
                        if trigger_text in trigger_original_values:
                            del trigger_original_values[trigger_text]
                else:
                    if conditions_match:
                        if trigger_data.get('revert_enabled', False):
                            if trigger_text not in trigger_original_values:
                                trigger_original_values[trigger_text] = {}
                            trigger_original_values[trigger_text][trigger_data['var_name']] = variables.get(trigger_data['var_name'])
                        variables[trigger_data['var_name']] = trigger_data['var_value']
                        newly_executed.append(trigger_text)
                        executed_triggers.append(trigger_text)
            if newly_executed or reverted_triggers:
                variables['_executed_time_triggers'] = executed_triggers
                variables['_trigger_original_values'] = trigger_original_values
                self.main_ui._save_variables(tab_index, variables)
        except Exception as e:
            print(f"[TIME TRIGGER] Error checking time triggers: {e}")

    def _trigger_conditions_match(self, conditions, current_datetime):
        if not conditions:
            return True
        if 'year' in conditions and current_datetime.year != conditions['year']:
            return False
        if 'month' in conditions:
            month_names = []
            for i in range(12):
                month_input = self.month_inputs[i] if i < len(self.month_inputs) else None
                if month_input and month_input.text().strip():
                    month_names.append(month_input.text().strip())
                else:
                    default_months = ["January", "February", "March", "April", "May", "June",
                                     "July", "August", "September", "October", "November", "December"]
                    month_names.append(default_months[i])
            try:
                month_index = month_names.index(conditions['month'])
                if current_datetime.month != month_index + 1:
                    return False
            except ValueError:
                return False
        if 'day_of_month' in conditions and current_datetime.day != conditions['day_of_month']:
            return False
        if 'hour' in conditions and current_datetime.hour != conditions['hour']:
            return False
        if 'minute' in conditions and current_datetime.minute != conditions['minute']:
            return False
        if 'day' in conditions:
            day_names = []
            for i in range(7):
                day_input = self.day_inputs[i] if i < len(self.day_inputs) else None
                if day_input and day_input.text().strip():
                    day_names.append(day_input.text().strip())
                else:
                    default_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    day_names.append(default_days[i])
            try:
                day_index = day_names.index(conditions['day'])
                if current_datetime.weekday() != day_index:
                    return False
            except ValueError:
                return False
        return True

    def update_theme(self, new_theme):
        self.theme_colors = new_theme.copy()
        self._apply_styling()
        for child in self.findChildren(QFrame):
            if child.frameShape() == QFrame.HLine:
                child.setStyleSheet(f"background-color: {self.theme_colors.get('base_color', '#00E5E5')}; height: 1px; border: none; margin: 5px 0;")
                
    def update_time(self, main_ui, tab_data):
        if not tab_data or not self.workflow_data_dir:
            return
        self.time_passage_data = self._load_time_passage_data()
        time_mode = self.time_passage_data.get('time_mode', 'game_world')
        try:
            tab_index = main_ui.tabs_data.index(tab_data) if tab_data in main_ui.tabs_data else -1
            if tab_index < 0:
                return
        except (ValueError, AttributeError):
            return
        variables = main_ui._load_variables(tab_index)
        if time_mode == 'real_world':
            current_datetime = datetime.now()
            variables['datetime'] = current_datetime.isoformat()
            variables['timemode'] = 'real_world'
        else:
            advancement_mode = self.time_passage_data.get('advancement_mode', 'static')
            variables['timemode'] = 'game_world'
            if 'datetime' not in variables:
                starting_dt_str = self.time_passage_data.get('starting_datetime')
                if starting_dt_str:
                    try:
                        starting_dt = datetime.fromisoformat(starting_dt_str)
                    except (ValueError, TypeError):
                        starting_dt = datetime.now()
                else:
                    starting_dt = datetime.now()
                    self.time_passage_data['starting_datetime'] = starting_dt.isoformat()
                    self._save_time_passage_data()
                variables['datetime'] = starting_dt.isoformat()
                variables['_last_real_time_update'] = datetime.now().isoformat()
                main_ui._save_variables(tab_index, variables)
            else:
                if advancement_mode == 'realtime':
                    time_multiplier = self.time_passage_data.get('time_multiplier', 1.0)
                    now = datetime.now()
                    try:
                        current_game_time = datetime.fromisoformat(variables['datetime'])
                    except (ValueError, TypeError):
                        starting_dt_str = self.time_passage_data.get('starting_datetime')
                        if starting_dt_str:
                            try:
                                current_game_time = datetime.fromisoformat(starting_dt_str)
                            except (ValueError, TypeError):
                                current_game_time = datetime.now()
                        else:
                            current_game_time = datetime.now()
                    last_real_time = variables.get('_last_real_time_update')
                    shutdown_time = variables.get('_timer_shutdown_time')
                    was_shutdown_graceful = variables.get('_timer_shutdown_graceful', False)
                    if not last_real_time:
                        variables['_last_real_time_update'] = now.isoformat()
                        main_ui._save_variables(tab_index, variables)
                        return
                    if was_shutdown_graceful and shutdown_time:
                        try:
                            shutdown_dt = datetime.fromisoformat(shutdown_time)
                            real_time_delta = now - shutdown_dt
                            game_time_delta = real_time_delta * time_multiplier
                            new_game_time = current_game_time + game_time_delta
                            variables['datetime'] = new_game_time.isoformat()
                            variables.pop('_timer_shutdown_graceful', None)
                            variables.pop('_timer_shutdown_time', None)
                        except (ValueError, TypeError) as e:
                            print(f"[DEBUG] Shutdown recovery error: {e}")
                    else:
                        if variables.get('_manual_time_advancement', False):
                            variables.pop('_manual_time_advancement', None)
                        elif time_multiplier > 0.0:
                            try:
                                last_update_dt = datetime.fromisoformat(last_real_time)
                                real_time_delta = now - last_update_dt
                                game_time_delta = real_time_delta * time_multiplier
                                new_game_time = current_game_time + game_time_delta
                                variables['datetime'] = new_game_time.isoformat()
                            except (ValueError, TypeError) as e:
                                print(f"[DEBUG] Normal advancement error: {e}")
                    variables['_last_real_time_update'] = now.isoformat()
                    main_ui._save_variables(tab_index, variables)
        main_ui._save_variables(tab_index, variables)
        self._check_time_triggers()

    def _apply_styling(self):
        base_color = self.theme_colors.get('base_color', '#00FF66')
        bg_value = int(80 * self.theme_colors.get("contrast", 0.5))
        bg_color = f"#{bg_value:02x}{bg_value:02x}{bg_value:02x}"
        darker_bg = f"#{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}"
        self.setStyleSheet(f"""
            QWidget#TimeManagerWidget {{
                background-color: {darker_bg};
                color: {base_color};
            }}
            QLabel#GameTimeModeLabel,
            QLabel#TimeManagerSectionTitle {{
                color: {base_color};
                background-color: transparent;
            }}
            QLabel#TimeManagerGroupLabel {{
                color: {base_color};
                background-color: transparent;
                font-weight: bold;
            }}
            QLabel#TimeManagerFieldLabel {{
                color: {base_color};
                background-color: transparent;
            }}
            QLabel#TimeManagerFormatHint {{
                color: {base_color};
                background-color: transparent;
                margin-left: 8px;
                font-style: italic;
            }}
            QFrame#TimeManagerGroup {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
            }}
            QLineEdit#TimeManagerInput {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                color: {base_color};
                padding: 4px;
            }}
            QLineEdit#TimeManagerInput:focus {{
                border: 2px solid {base_color};
                background-color: {bg_color};
            }}
            QDateTimeEdit#TimeManagerDateTimeEdit {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                color: {base_color};
                padding: 4px;
                min-width: 150px;
            }}
            QDateTimeEdit#TimeManagerDateTimeEdit::up-button,
            QDateTimeEdit#TimeManagerDateTimeEdit::down-button {{
                background-color: {bg_color};
                border: 1px solid {base_color};
                width: 16px;
            }}
            QDateTimeEdit#TimeManagerDateTimeEdit::up-arrow,
            QDateTimeEdit#TimeManagerDateTimeEdit::down-arrow {{
                width: 8px;
                height: 8px;
            }}
            QDateTimeEdit#TimeManagerDateTimeEdit::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid {base_color};
            }}
            QDateTimeEdit#TimeManagerDateTimeEdit::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {base_color};
            }}
            QComboBox#TimeManagerComboBox {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                color: {base_color};
                padding: 4px;
                min-width: 100px;
            }}
            QComboBox#TimeManagerComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox#TimeManagerComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {base_color};
                margin-right: 5px;
            }}
            QComboBox#TimeManagerComboBox QAbstractItemView {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                color: {base_color};
                selection-background-color: {base_color};
                selection-color: #000000;
            }}
            QSpinBox#TimeManagerSpinBox,
            QDoubleSpinBox#TimeManagerDoubleSpinBox {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                color: {base_color};
                padding: 4px;
                min-width: 80px;
            }}
            QSpinBox#TimeManagerSpinBox::up-button,
            QSpinBox#TimeManagerSpinBox::down-button,
            QDoubleSpinBox#TimeManagerDoubleSpinBox::up-button,
            QDoubleSpinBox#TimeManagerDoubleSpinBox::down-button {{
                background-color: {bg_color};
                border: 1px solid {base_color};
                width: 16px;
            }}
            QSpinBox#TimeManagerSpinBox::up-arrow,
            QSpinBox#TimeManagerSpinBox::down-arrow,
            QDoubleSpinBox#TimeManagerDoubleSpinBox::up-arrow,
            QDoubleSpinBox#TimeManagerDoubleSpinBox::down-arrow {{
                width: 8px;
                height: 8px;
            }}
            QSpinBox#TimeManagerSpinBox::up-arrow,
            QDoubleSpinBox#TimeManagerDoubleSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid {base_color};
            }}
            QSpinBox#TimeManagerSpinBox::down-arrow,
            QDoubleSpinBox#TimeManagerDoubleSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid {base_color};
            }}
            QListWidget#TimeManagerTriggersList {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                color: {base_color};
                alternate-background-color: {bg_color};
            }}
            QListWidget#TimeManagerTriggersList::item {{
                padding: 4px;
                border-bottom: 1px solid {bg_color};
            }}
            QListWidget#TimeManagerTriggersList::item:selected {{
                background-color: {base_color};
                color: #000000;
            }}
            QListWidget#TimeManagerTriggersList::item:hover {{
                background-color: {bg_color};
            }}
            QPushButton#TimeManagerButton {{
                background-color: {bg_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                color: {base_color};
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton#TimeManagerButton:hover {{
                background-color: {base_color};
                color: #000000;
            }}
            QPushButton#TimeManagerButton:pressed {{
                background-color: {darker_bg};
                border: 2px solid {base_color};
            }}
            QRadioButton#SyncComputerRadio,
            QRadioButton#GameWorldRadio,
            QRadioButton#StaticRadio,
            QRadioButton#RealtimeRadio,
            QRadioButton#TimeManagerRevertCheckbox {{
                color: {base_color};
                spacing: 5px;
            }}
            QRadioButton#SyncComputerRadio::indicator,
            QRadioButton#GameWorldRadio::indicator,
            QRadioButton#StaticRadio::indicator,
            QRadioButton#RealtimeRadio::indicator,
            QRadioButton#TimeManagerRevertCheckbox::indicator {{
                width: 12px;
                height: 12px;
                border-radius: 6px;
                border: 1px solid {base_color};
                background-color: {darker_bg};
            }}
            QRadioButton#SyncComputerRadio::indicator:checked,
            QRadioButton#GameWorldRadio::indicator:checked,
            QRadioButton#StaticRadio::indicator:checked,
            QRadioButton#RealtimeRadio::indicator:checked,
            QRadioButton#TimeManagerRevertCheckbox::indicator:checked {{
                background-color: {base_color};
                border: 2px solid {base_color};
            }}
        """)
