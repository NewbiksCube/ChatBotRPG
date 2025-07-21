from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QLabel, QTextEdit, QLineEdit, QHBoxLayout, QPushButton, QDateTimeEdit, QFrame, QRadioButton, QButtonGroup, QDoubleSpinBox, QScrollArea
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont, QColor
import os
import json

class StartConditionsManagerWidget(QWidget):
    def __init__(self, theme_colors=None, system_context_file=None, variables_file=None, parent=None):
        super().__init__(parent)
        default_theme = {
            'base_color': '#00FF66',
            'bg_color': '#222222',
            'highlight': 'rgba(0,255,102,0.6)'
        }
        self.theme_colors = {**default_theme, **(theme_colors or {})}
        self.system_context_file = system_context_file
        self.variables_file = variables_file
        self._init_ui()
        self._load_intro_state()
        self._load_system_prompt()
        self._load_character_system_prompt()
        self._load_origin()
        self._load_starting_datetime()
        self._load_global_vars()
        self.datetime_edit.dateTimeChanged.connect(self._save_starting_datetime)
        self.advancement_group.buttonClicked.connect(self._save_advancement_mode)
        self.time_multiplier_spin.valueChanged.connect(self._save_time_multiplier)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet(f"background-color: {self.theme_colors.get('bg_color', '#2B2B2B')};")
        layout = QVBoxLayout(self.scroll_content)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)
        self.intro_checkbox = QCheckBox("Introduction")
        self.intro_checkbox.setObjectName("IntroductionCheckbox")
        self.intro_checkbox.setFont(QFont('Consolas', 11, QFont.Bold))
        self.intro_checkbox.setChecked(False)
        layout.addWidget(self.intro_checkbox, alignment=Qt.AlignLeft)
        intro_row_layout = QHBoxLayout()
        intro_title_vbox = QVBoxLayout()
        self.intro_title_label = QLabel("Intro Title:")
        self.intro_title_label.setFont(QFont('Consolas', 11, QFont.Bold))
        self.intro_title_label.setVisible(False)
        intro_title_vbox.addWidget(self.intro_title_label)
        self.intro_title_lineedit = QLineEdit()
        self.intro_title_lineedit.setObjectName("IntroTitleLineEdit")
        self.intro_title_lineedit.setFont(QFont('Consolas', 11))
        self.intro_title_lineedit.setPlaceholderText("Enter introduction title...")
        self.intro_title_lineedit.setVisible(False)
        intro_title_vbox.addWidget(self.intro_title_lineedit)
        self.intro_title_lineedit.editingFinished.connect(self._save_intro_state)
        intro_row_layout.addLayout(intro_title_vbox)
        intro_desc_vbox = QVBoxLayout()
        self.intro_desc_label = QLabel("Title Description:")
        self.intro_desc_label.setFont(QFont('Consolas', 11, QFont.Bold))
        self.intro_desc_label.setVisible(False)
        intro_desc_vbox.addWidget(self.intro_desc_label)
        self.intro_desc_lineedit = QLineEdit()
        self.intro_desc_lineedit.setObjectName("IntroDescLineEdit")
        self.intro_desc_lineedit.setFont(QFont('Consolas', 11))
        self.intro_desc_lineedit.setPlaceholderText("Enter description (optional)...")
        self.intro_desc_lineedit.setVisible(False)
        intro_desc_vbox.addWidget(self.intro_desc_lineedit)
        self.intro_desc_lineedit.editingFinished.connect(self._save_intro_state)
        intro_row_layout.addLayout(intro_desc_vbox)
        layout.addLayout(intro_row_layout)
        self.intro_text_label = QLabel("Intro sequence (messages and player generation, displayed after clicking NEW):")
        self.intro_text_label.setFont(QFont('Consolas', 11, QFont.Bold))
        self.intro_text_label.setVisible(False)
        layout.addWidget(self.intro_text_label)
        self.intro_messages_vbox = QVBoxLayout()
        self.intro_items = []
        self._generation_checkboxes = {}
        self._add_player_generation_item()
        self._add_intro_message_editor()
        self.intro_messages_widget = QWidget()
        self.intro_messages_widget.setLayout(self.intro_messages_vbox)
        self.intro_messages_widget.setVisible(False)
        layout.addWidget(self.intro_messages_widget)
        self.origin_label = QLabel("Origin Setting:")
        self.origin_label.setFont(QFont('Consolas', 11, QFont.Bold))
        layout.addWidget(self.origin_label)
        self.origin_lineedit = QLineEdit()
        self.origin_lineedit.setObjectName("OriginLineEdit")
        self.origin_lineedit.setFont(QFont('Consolas', 11))
        self.origin_lineedit.setPlaceholderText("Default Setting")
        layout.addWidget(self.origin_lineedit)
        self.origin_lineedit.editingFinished.connect(self._save_origin)
        self.starting_datetime_label = QLabel("Starting Date/Time:")
        self.starting_datetime_label.setFont(QFont('Consolas', 11, QFont.Bold))
        layout.addWidget(self.starting_datetime_label)
        datetime_input_layout = QHBoxLayout()
        datetime_label = QLabel("Initial Date/Time:")
        datetime_label.setFont(QFont('Consolas', 11))
        datetime_input_layout.addWidget(datetime_label)
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setObjectName("StartingDateTimeEdit")
        self.datetime_edit.setFont(QFont('Consolas', 11))
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        min_date = QDateTime(1, 1, 1, 0, 0)
        max_date = QDateTime(9999, 12, 31, 23, 59)
        self.datetime_edit.setMinimumDateTime(min_date)
        self.datetime_edit.setMaximumDateTime(max_date)
        datetime_input_layout.addWidget(self.datetime_edit)
        self.format_hint = QLabel("YYYY-MM-DD HH:MM (24h)")
        self.format_hint.setFont(QFont('Consolas', 11))
        self.format_hint.setStyleSheet(f"color: {self.theme_colors['base_color']}; margin-left: 8px;")
        datetime_input_layout.addWidget(self.format_hint)
        datetime_input_layout.addStretch()
        layout.addLayout(datetime_input_layout)
        advancement_layout = QHBoxLayout()
        advancement_label = QLabel("Mode:")
        advancement_label.setFont(QFont('Consolas', 11))
        advancement_layout.addWidget(advancement_label)
        self.advancement_group = QButtonGroup(self)
        self.static_radio = QRadioButton("Static")
        self.static_radio.setFont(QFont('Consolas', 11))
        self.static_radio.setChecked(True)
        self.advancement_group.addButton(self.static_radio, 0)
        advancement_layout.addWidget(self.static_radio)
        self.realtime_radio = QRadioButton("Realtime")
        self.realtime_radio.setFont(QFont('Consolas', 11))
        self.advancement_group.addButton(self.realtime_radio, 1)
        advancement_layout.addWidget(self.realtime_radio)
        advancement_layout.addSpacing(20)
        multiplier_label = QLabel("Multiplier:")
        multiplier_label.setFont(QFont('Consolas', 11))
        advancement_layout.addWidget(multiplier_label)
        self.time_multiplier_spin = QDoubleSpinBox()
        self.time_multiplier_spin.setRange(0.0, 100.0)
        self.time_multiplier_spin.setSingleStep(0.1)
        self.time_multiplier_spin.setDecimals(1)
        self.time_multiplier_spin.setValue(1.0)
        self.time_multiplier_spin.setSuffix("x")
        self.time_multiplier_spin.setFont(QFont('Consolas', 11))
        self.time_multiplier_spin.setSpecialValueText("Static (0.0x)")
        self.time_multiplier_spin.setToolTip("Game time speed relative to real time\n\n0.0x = Static (no time advancement)\n0.5x = Half speed (1 real hour = 30 game minutes)\n1.0x = Normal speed (1 real hour = 1 game hour)\n2.0x = Double speed (1 real hour = 2 game hours)")
        advancement_layout.addWidget(self.time_multiplier_spin)
        advancement_layout.addStretch()
        layout.addLayout(advancement_layout)
        self.sys_label = QLabel("Base System Prompt:")
        self.sys_label.setFont(QFont('Consolas', 12, QFont.Bold))
        layout.addWidget(self.sys_label)
        self.system_prompt_editor = QTextEdit()
        self.system_prompt_editor.setObjectName("SystemPromptEditor")
        self.system_prompt_editor.setFont(QFont('Consolas', 12))
        self.system_prompt_editor.setPlaceholderText("Enter system instructions for the AI here.\nThis message will be sent as a system prompt with each interaction.")
        layout.addWidget(self.system_prompt_editor)
        self.system_prompt_editor.textChanged.connect(self._save_system_prompt)
        self.char_sys_label = QLabel("Character System Prompt:")
        self.char_sys_label.setFont(QFont('Consolas', 12, QFont.Bold))
        layout.addWidget(self.char_sys_label)
        self.character_system_prompt_editor = QTextEdit()
        self.character_system_prompt_editor.setObjectName("CharacterSystemPromptEditor")
        self.character_system_prompt_editor.setFont(QFont('Consolas', 12))
        self.character_system_prompt_editor.setPlaceholderText("Enter system instructions for character AI here.\nThis message will be sent as a system prompt for character interactions.")
        layout.addWidget(self.character_system_prompt_editor)
        self.character_system_prompt_editor.textChanged.connect(self._save_character_system_prompt)
        
        self.global_vars_label = QLabel("Global Variables:")
        self.global_vars_label.setFont(QFont('Consolas', 12, QFont.Bold))
        layout.addWidget(self.global_vars_label)
        
        self.global_vars_description = QLabel("Define variables that will be initialized once when starting a new game:")
        self.global_vars_description.setFont(QFont('Consolas', 10))
        self.global_vars_description.setStyleSheet(f"color: {self.theme_colors['base_color']}; margin-bottom: 8px;")
        layout.addWidget(self.global_vars_description)
        
        self.global_vars_container = QWidget()
        self.global_vars_layout = QVBoxLayout(self.global_vars_container)
        self.global_vars_layout.setContentsMargins(0, 0, 0, 0)
        self.global_vars_layout.setSpacing(8)
        
        self.global_vars_items = []
        self._add_global_var_item()
        
        add_var_btn = QPushButton("+ Add Variable")
        add_var_btn.setFont(QFont('Consolas', 10))
        add_var_btn.clicked.connect(self._add_global_var_item)
        add_var_btn.setStyleSheet(f"""
            QPushButton {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
            }}
        """)
        layout.addWidget(add_var_btn)
        layout.addWidget(self.global_vars_container)
        
        layout.addStretch(1)
        self.intro_checkbox.stateChanged.connect(self._on_intro_changed)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        self._apply_theme_styles()

    def _apply_theme_styles(self):
        self.intro_checkbox.setStyleSheet(f"""
            QCheckBox#IntroductionCheckbox {{
                color: {self.theme_colors['base_color']};
                font-weight: bold;
                spacing: 8px;
            }}
            QCheckBox#IntroductionCheckbox::indicator {{
                border: 1.5px solid {self.theme_colors['base_color']};
                background: {self.theme_colors['bg_color']};
                width: 18px; height: 18px;
            }}
            QCheckBox#IntroductionCheckbox::indicator:checked {{
                background: {self.theme_colors['base_color']};
                border: 2px solid {self.theme_colors['base_color']};
            }}
        """)
        self.intro_title_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        self.intro_title_lineedit.setStyleSheet(f"""
            QLineEdit#IntroTitleLineEdit {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        self.intro_desc_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        self.intro_desc_lineedit.setStyleSheet(f"""
            QLineEdit#IntroDescLineEdit {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        self.intro_text_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        self.system_prompt_editor.setStyleSheet(f"""
            QTextEdit#SystemPromptEditor {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        self.character_system_prompt_editor.setStyleSheet(f"""
            QTextEdit#CharacterSystemPromptEditor {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        self.origin_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        self.origin_lineedit.setStyleSheet(f"""
            QLineEdit#OriginLineEdit {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        
        self.starting_datetime_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        self.datetime_edit.setStyleSheet(f"""
            QDateTimeEdit#StartingDateTimeEdit {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        
        self.static_radio.setStyleSheet(f"""
            QRadioButton {{
                color: {self.theme_colors['base_color']};
                font-weight: bold;
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                border: 1.5px solid {self.theme_colors['base_color']};
                background: {self.theme_colors['bg_color']};
                width: 18px; height: 18px;
                border-radius: 9px;
            }}
            QRadioButton::indicator:checked {{
                background: {self.theme_colors['base_color']};
                border: 2px solid {self.theme_colors['base_color']};
            }}
        """)
        
        self.realtime_radio.setStyleSheet(f"""
            QRadioButton {{
                color: {self.theme_colors['base_color']};
                font-weight: bold;
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                border: 1.5px solid {self.theme_colors['base_color']};
                background: {self.theme_colors['bg_color']};
                width: 18px; height: 18px;
                border-radius: 9px;
            }}
            QRadioButton::indicator:checked {{
                background: {self.theme_colors['base_color']};
                border: 2px solid {self.theme_colors['base_color']};
            }}
        """)
        
        self.time_multiplier_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        
        self.system_prompt_editor.setCursorWidth(4)
        self.character_system_prompt_editor.setCursorWidth(4)
    def update_theme(self, theme_colors):
        default_theme = {
            'base_color': '#00FF66',
            'bg_color': '#222222',
            'highlight': 'rgba(0,255,102,0.6)'
        }
        self.theme_colors = {**default_theme, **(theme_colors or {})}
        if hasattr(self, 'scroll_area'):
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    background-color: {self.theme_colors.get('bg_color', '#2B2B2B')};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background: {self.theme_colors.get('bg_color', '#2B2B2B')};
                    width: 12px;
                    margin: 0px;
                }}
                QScrollBar::handle:vertical {{
                    background: {self.theme_colors.get('base_color', '#00FF66')};
                    min-height: 20px;
                    border-radius: 6px;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                    height: 0px;
                }}
                QScrollBar:horizontal {{
                    background: {self.theme_colors.get('bg_color', '#2B2B2B')};
                    height: 12px;
                    margin: 0px;
                }}
                QScrollBar::handle:horizontal {{
                    background: {self.theme_colors.get('base_color', '#00FF66')};
                    min-width: 20px;
                    border-radius: 6px;
                }}
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                    background: none;
                    width: 0px;
                }}
            """)
        
        self._apply_theme_styles()
        self.system_prompt_editor.setCursorWidth(4)
        self.character_system_prompt_editor.setCursorWidth(4)
        self.starting_datetime_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        self.datetime_edit.setStyleSheet(f"""
            QDateTimeEdit#StartingDateTimeEdit {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        self.static_radio.setStyleSheet(f"""
            QRadioButton {{
                color: {self.theme_colors['base_color']};
                font-weight: bold;
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                border: 1.5px solid {self.theme_colors['base_color']};
                background: {self.theme_colors['bg_color']};
                width: 18px; height: 18px;
                border-radius: 9px;
            }}
            QRadioButton::indicator:checked {{
                background: {self.theme_colors['base_color']};
                border: 2px solid {self.theme_colors['base_color']};
            }}
        """)
        self.realtime_radio.setStyleSheet(f"""
            QRadioButton {{
                color: {self.theme_colors['base_color']};
                font-weight: bold;
                spacing: 8px;
            }}
            QRadioButton::indicator {{
                border: 1.5px solid {self.theme_colors['base_color']};
                background: {self.theme_colors['bg_color']};
                width: 18px; height: 18px;
                border-radius: 9px;
            }}
            QRadioButton::indicator:checked {{
                background: {self.theme_colors['base_color']};
                border: 2px solid {self.theme_colors['base_color']};
            }}
        """)
        self.time_multiplier_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        for item in self.intro_items:
            if item['type'] == 'message':
                editor = item.get('editor')
                if editor:
                    editor.setStyleSheet(f"""
                        QTextEdit {{
                            color: {self.theme_colors['base_color']};
                            background-color: {self.theme_colors['bg_color']};
                            border: 1px solid {self.theme_colors['base_color']};
                            border-radius: 4px;
                            padding: 4px;
                            selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                            selection-color: white;
                        }}
                    """)
                    editor.setCursorWidth(4)
            elif item['type'] == 'player_gen':
                # Update prompt input styling
                prompt_input = item.get('prompt_input')
                if prompt_input:
                    prompt_input.setStyleSheet(f"""
                        QLineEdit#PlayerGenPromptInput {{
                            color: {self.theme_colors['base_color']};
                            background-color: {self.theme_colors['bg_color']};
                            border: 1px solid {self.theme_colors['base_color']};
                            border-radius: 4px;
                            padding: 4px;
                            selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                            selection-color: white;
                        }}
                    """)
                checkboxes = item.get('checkboxes', {})
                checkbox_style = f"""
                    QCheckBox {{
                        color: {self.theme_colors['base_color']};
                        font-weight: normal;
                        spacing: 8px;
                    }}
                    QCheckBox::indicator {{
                        border: 1.5px solid {self.theme_colors['base_color']};
                        background: {self.theme_colors['bg_color']};
                        width: 16px; height: 16px;
                    }}
                    QCheckBox::indicator:checked {{
                        background: {self.theme_colors['base_color']};
                        border: 2px solid {self.theme_colors['base_color']};
                    }}
                """
                for checkbox in checkboxes.values():
                    checkbox.setStyleSheet(checkbox_style)
        self.format_hint.setStyleSheet(f"color: {self.theme_colors['base_color']}; margin-left: 8px;")
        
        self.global_vars_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        self.global_vars_description.setStyleSheet(f"color: {self.theme_colors['base_color']}; margin-bottom: 8px;")
        
        for item in self.global_vars_items:
            name_input = item.get('name_input')
            value_input = item.get('value_input')
            if name_input:
                name_input.setStyleSheet(f"""
                    QLineEdit#GlobalVarNameInput {{
                        color: {self.theme_colors['base_color']};
                        background-color: {self.theme_colors['bg_color']};
                        border: 1px solid {self.theme_colors['base_color']};
                        border-radius: 4px;
                        padding: 4px;
                        selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                        selection-color: white;
                    }}
                """)
            if value_input:
                value_input.setStyleSheet(f"""
                    QLineEdit#GlobalVarValueInput {{
                        color: {self.theme_colors['base_color']};
                        background-color: {self.theme_colors['bg_color']};
                        border: 1px solid {self.theme_colors['base_color']};
                        border-radius: 4px;
                        padding: 4px;
                        selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                        selection-color: white;
                    }}
                """)

    def _add_global_var_item(self, var_name="", var_value=""):
        container_widget = QWidget()
        container_widget.setObjectName("GlobalVarItem")
        row = QHBoxLayout(container_widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        
        name_label = QLabel("Name:")
        name_label.setFont(QFont('Consolas', 10))
        name_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        name_label.setFixedWidth(60)
        row.addWidget(name_label)
        
        name_input = QLineEdit()
        name_input.setObjectName("GlobalVarNameInput")
        name_input.setFont(QFont('Consolas', 10))
        name_input.setPlaceholderText("variable_name")
        name_input.setText(var_name)
        name_input.setStyleSheet(f"""
            QLineEdit#GlobalVarNameInput {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        name_input.textChanged.connect(self._save_global_vars)
        row.addWidget(name_input)
        
        value_label = QLabel("Value:")
        value_label.setFont(QFont('Consolas', 10))
        value_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        value_label.setFixedWidth(50)
        row.addWidget(value_label)
        
        value_input = QLineEdit()
        value_input.setObjectName("GlobalVarValueInput")
        value_input.setFont(QFont('Consolas', 10))
        value_input.setPlaceholderText("initial_value")
        value_input.setText(var_value)
        value_input.setStyleSheet(f"""
            QLineEdit#GlobalVarValueInput {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        value_input.textChanged.connect(self._save_global_vars)
        row.addWidget(value_input)
        
        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(30)
        remove_btn.setFont(QFont('Consolas', 12, QFont.Bold))
        remove_btn.clicked.connect(lambda: self._remove_global_var_item(container_widget))
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 2px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
            }}
        """)
        row.addWidget(remove_btn)
        
        self.global_vars_layout.addWidget(container_widget)
        
        item = {
            'widget': container_widget,
            'name_input': name_input,
            'value_input': value_input
        }
        self.global_vars_items.append(item)
        
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None

    def _remove_global_var_item(self, widget):
        item_to_remove = None
        for item in self.global_vars_items:
            if item['widget'] == widget:
                item_to_remove = item
                break
        if item_to_remove:
            self.global_vars_layout.removeWidget(widget)
            widget.setParent(None)
            self.global_vars_items.remove(item_to_remove)
            main_ui = self._get_main_ui()
            if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                try:
                    main_ui.delete_rule_sound.play()
                except Exception:
                    main_ui.delete_rule_sound = None
            self._save_global_vars()

    def _toggle_intro_text(self, checked):
        self.intro_title_label.setVisible(checked)
        self.intro_title_lineedit.setVisible(checked)
        self.intro_desc_label.setVisible(checked)
        self.intro_desc_lineedit.setVisible(checked)
        self.intro_text_label.setVisible(checked)
        self.intro_messages_widget.setVisible(checked)

    def _on_intro_changed(self, *args):
        checked = self.intro_checkbox.isChecked()
        self._toggle_intro_text(checked)
        self._save_intro_state()

    def _add_intro_message_editor(self, text=""):
        container_widget = QWidget()
        container_widget.setObjectName("IntroMessageItem")
        row = QHBoxLayout(container_widget)
        row.setContentsMargins(0, 0, 0, 0)
        editor = QTextEdit()
        editor.setFont(QFont('Consolas', 11))
        editor.setPlaceholderText("Enter intro message...")
        editor.setPlainText(text)
        editor.setFixedHeight(50)
        editor.setStyleSheet(f"""
            QTextEdit {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        editor.setCursorWidth(4)
        editor.textChanged.connect(self._save_intro_state)
        row.addWidget(editor)
        up_btn = QPushButton("↑")
        up_btn.setFixedWidth(30)
        up_btn.clicked.connect(lambda: self._move_intro_message_up(editor))
        row.addWidget(up_btn)
        down_btn = QPushButton("↓")
        down_btn.setFixedWidth(30)
        down_btn.clicked.connect(lambda: self._move_intro_message_down(editor))
        row.addWidget(down_btn)
        plus_btn = QPushButton("+")
        plus_btn.setFixedWidth(30)
        plus_btn.clicked.connect(lambda: self._add_intro_message_editor())
        row.addWidget(plus_btn)
        minus_btn = QPushButton("−")
        minus_btn.setFixedWidth(30)
        minus_btn.clicked.connect(lambda: self._remove_intro_message_editor(editor))
        row.addWidget(minus_btn)
        self.intro_messages_vbox.addWidget(container_widget)
        item = {
            'type': 'message',
            'widget': container_widget,
            'editor': editor
        }
        self.intro_items.append(item)
        self._update_intro_message_buttons()
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception:
                main_ui.add_rule_sound = None

    def _add_player_generation_item(self):
        main_widget = QWidget()
        main_widget.setObjectName("PlayerGenItem")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        controls_row = QHBoxLayout()
        player_gen_label = QLabel("Player Generation:")
        player_gen_label.setFont(QFont('Consolas', 11, QFont.Bold))
        player_gen_label.setStyleSheet(f"color: {self.theme_colors['base_color']};")
        controls_row.addWidget(player_gen_label)
        controls_row.addStretch()
        up_btn = QPushButton("↑")
        up_btn.setFixedWidth(30)
        up_btn.clicked.connect(lambda: self._move_intro_item_up(main_widget))
        controls_row.addWidget(up_btn)
        down_btn = QPushButton("↓")
        down_btn.setFixedWidth(30)
        down_btn.clicked.connect(lambda: self._move_intro_item_down(main_widget))
        controls_row.addWidget(down_btn)
        main_layout.addLayout(controls_row)
        player_gen_prompt_input = QLineEdit()
        player_gen_prompt_input.setObjectName("PlayerGenPromptInput")
        player_gen_prompt_input.setFont(QFont('Consolas', 11))
        player_gen_prompt_input.setPlaceholderText("Enter player generation prompt...")
        player_gen_prompt_input.setText("Create your character:")
        player_gen_prompt_input.editingFinished.connect(self._save_intro_state)
        player_gen_prompt_input.setStyleSheet(f"""
            QLineEdit#PlayerGenPromptInput {{
                color: {self.theme_colors['base_color']};
                background-color: {self.theme_colors['bg_color']};
                border: 1px solid {self.theme_colors['base_color']};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {QColor(self.theme_colors['base_color']).darker(300).name()};
                selection-color: white;
            }}
        """)
        main_layout.addWidget(player_gen_prompt_input)
        gen_checkboxes_layout = QHBoxLayout()
        generation_checkboxes = {}
        for field_name in ['name', 'description', 'personality', 'appearance', 'goals', 'story', 'abilities', 'equipment']:
            checkbox = QCheckBox(field_name.capitalize())
            checkbox.setObjectName(f"Gen{field_name.capitalize()}Checkbox")
            checkbox.setFont(QFont('Consolas', 10))
            checkbox.stateChanged.connect(self._save_intro_state)
            checkbox.setStyleSheet(f"""
                QCheckBox {{
                    color: {self.theme_colors['base_color']};
                    font-weight: normal;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    border: 1.5px solid {self.theme_colors['base_color']};
                    background: {self.theme_colors['bg_color']};
                    width: 16px; height: 16px;
                }}
                QCheckBox::indicator:checked {{
                    background: {self.theme_colors['base_color']};
                    border: 2px solid {self.theme_colors['base_color']};
                }}
            """)
            
            generation_checkboxes[field_name] = checkbox
            self._generation_checkboxes[field_name] = checkbox
            gen_checkboxes_layout.addWidget(checkbox)
        gen_checkboxes_layout.addStretch()
        main_layout.addLayout(gen_checkboxes_layout)
        self.intro_messages_vbox.addWidget(main_widget)
        item = {
            'type': 'player_gen',
            'widget': main_widget,
            'prompt_input': player_gen_prompt_input,
            'checkboxes': generation_checkboxes
        }
        self.intro_items.append(item)

    def _remove_intro_message_editor(self, editor):
        item_to_remove = None
        for item in self.intro_items:
            if item['type'] == 'message' and item.get('editor') == editor:
                item_to_remove = item
                break
        if item_to_remove:
            widget = item_to_remove['widget']
            self.intro_messages_vbox.removeWidget(widget)
            widget.setParent(None)
            self.intro_items.remove(item_to_remove)
            main_ui = self._get_main_ui()
            if main_ui and hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
                try:
                    main_ui.delete_rule_sound.play()
                except Exception:
                    main_ui.delete_rule_sound = None
        self._update_intro_message_buttons()
        self._save_intro_state()

    def _update_intro_message_buttons(self):
        total_items = len(self.intro_items)
        message_items = [item for item in self.intro_items if item['type'] == 'message']
        for i, item in enumerate(self.intro_items):
            try:
                widget = item['widget']
                is_last_item = (i == total_items - 1)
                if item['type'] == 'message':
                    if hasattr(widget, 'layout') and widget.layout():
                        layout = widget.layout()
                        up_btn = layout.itemAt(1).widget() if layout.count() > 1 else None
                        down_btn = layout.itemAt(2).widget() if layout.count() > 2 else None
                        plus_btn = layout.itemAt(3).widget() if layout.count() > 3 else None
                        minus_btn = layout.itemAt(4).widget() if layout.count() > 4 else None
                        if up_btn:
                            up_btn.setVisible(i > 0)
                        if down_btn:
                            down_btn.setVisible(i < total_items - 1)
                        if plus_btn:
                            plus_btn.setVisible(is_last_item)
                        if minus_btn:
                            message_count = len(message_items)
                            minus_btn.setVisible(message_count > 1)
                            
                elif item['type'] == 'player_gen':
                    if hasattr(widget, 'layout') and widget.layout():
                        main_layout = widget.layout()
                        if main_layout.count() > 0:
                            controls_item = main_layout.itemAt(0)
                            if controls_item and hasattr(controls_item, 'layout'):
                                controls_layout = controls_item.layout()
                                up_btn = controls_layout.itemAt(2).widget() if controls_layout.count() > 2 else None
                                down_btn = controls_layout.itemAt(3).widget() if controls_layout.count() > 3 else None
                                if up_btn:
                                    up_btn.setVisible(i > 0)
                                if down_btn:
                                    down_btn.setVisible(i < total_items - 1)
                                if is_last_item:
                                    plus_btn = controls_layout.itemAt(4).widget() if controls_layout.count() > 4 else None
                                    if not plus_btn:
                                        plus_btn = QPushButton("+")
                                        plus_btn.setFixedWidth(30)
                                        plus_btn.clicked.connect(lambda: self._add_intro_message_editor())
                                        controls_layout.addWidget(plus_btn)
                                    plus_btn.setVisible(True)
                                else:
                                    plus_btn = controls_layout.itemAt(4).widget() if controls_layout.count() > 4 else None
                                    if plus_btn:
                                        plus_btn.setVisible(False)
            except (RuntimeError, AttributeError) as e:
                print(f"[StartConditionsManager] Widget deleted during button update: {e}")
                continue

    def _move_intro_message_up(self, editor):
        for item in self.intro_items:
            if item['type'] == 'message' and item.get('editor') == editor:
                self._move_intro_item_up(item['widget'])
                break

    def _move_intro_message_down(self, editor):
        for item in self.intro_items:
            if item['type'] == 'message' and item.get('editor') == editor:
                self._move_intro_item_down(item['widget'])
                break

    def _move_intro_item_up(self, widget):
        current_index = -1
        for i, item in enumerate(self.intro_items):
            if item['widget'] == widget:
                current_index = i
                break
        if current_index <= 0:
            return
        self.intro_items[current_index], self.intro_items[current_index - 1] = \
            self.intro_items[current_index - 1], self.intro_items[current_index]
        current_widget = self.intro_messages_vbox.itemAt(current_index).widget()
        above_widget = self.intro_messages_vbox.itemAt(current_index - 1).widget()
        self.intro_messages_vbox.removeWidget(current_widget)
        self.intro_messages_vbox.removeWidget(above_widget)
        self.intro_messages_vbox.insertWidget(current_index - 1, current_widget)
        self.intro_messages_vbox.insertWidget(current_index, above_widget)
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'sort_sound') and main_ui.sort_sound:
            try:
                main_ui.sort_sound.play()
            except Exception:
                main_ui.sort_sound = None
        self._update_intro_message_buttons()
        self._save_intro_state()

    def _move_intro_item_down(self, widget):
        current_index = -1
        for i, item in enumerate(self.intro_items):
            if item['widget'] == widget:
                current_index = i
                break
        if current_index == -1 or current_index >= len(self.intro_items) - 1:
            return
        self.intro_items[current_index], self.intro_items[current_index + 1] = \
            self.intro_items[current_index + 1], self.intro_items[current_index]
        current_widget = self.intro_messages_vbox.itemAt(current_index).widget()
        below_widget = self.intro_messages_vbox.itemAt(current_index + 1).widget()
        self.intro_messages_vbox.removeWidget(current_widget)
        self.intro_messages_vbox.removeWidget(below_widget)
        self.intro_messages_vbox.insertWidget(current_index, below_widget)
        self.intro_messages_vbox.insertWidget(current_index + 1, current_widget)
        main_ui = self._get_main_ui()
        if main_ui and hasattr(main_ui, 'sort_sound') and main_ui.sort_sound:
            try:
                main_ui.sort_sound.play()
            except Exception:
                main_ui.sort_sound = None
        self._update_intro_message_buttons()
        self._save_intro_state()

    def _load_intro_state(self):
        if not self.variables_file or not os.path.exists(self.variables_file):
            self._toggle_intro_text(False)
            return
        try:
            with open(self.variables_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            checked = data.get('introduction_checked', False)
            intro_title = data.get('introduction_title', '')
            intro_desc = data.get('introduction_description', '')
            intro_sequence = data.get('introduction_sequence', [])
            self.intro_checkbox.blockSignals(True)
            self.intro_checkbox.setChecked(checked)
            self.intro_checkbox.blockSignals(False)
            self.intro_title_lineedit.blockSignals(True)
            self.intro_title_lineedit.setText(intro_title)
            self.intro_title_lineedit.blockSignals(False)
            self.intro_desc_lineedit.blockSignals(True)
            self.intro_desc_lineedit.setText(intro_desc)
            self.intro_desc_lineedit.blockSignals(False)
            while self.intro_items:
                item = self.intro_items[0]
                widget = item['widget']
                self.intro_messages_vbox.removeWidget(widget)
                widget.setParent(None)
                self.intro_items.remove(item)
            if not intro_sequence:
                old_intro_messages = data.get('introduction_messages', [])
                old_player_generation = data.get('player_generation', {})
                if old_intro_messages or old_player_generation:
                    for msg in old_intro_messages:
                        if msg.strip():
                            self._add_intro_message_editor(msg)
                    self._add_player_generation_item()
                    if old_player_generation:
                        player_gen_item = next((item for item in self.intro_items if item['type'] == 'player_gen'), None)
                        if player_gen_item:
                            old_prompt = old_player_generation.get('prompt', 'Create your character:')
                            player_gen_item['prompt_input'].blockSignals(True)
                            player_gen_item['prompt_input'].setText(old_prompt)
                            player_gen_item['prompt_input'].blockSignals(False)
                            for field_name, checkbox in player_gen_item['checkboxes'].items():
                                checkbox.blockSignals(True)
                                checkbox.setChecked(old_player_generation.get(field_name, False))
                                checkbox.blockSignals(False)
                    self._save_intro_state()
                else:
                    self._add_player_generation_item()
                self._add_intro_message_editor()
            else:
                for item_data in intro_sequence:
                    if item_data.get('type') == 'player_gen':
                        self._add_player_generation_item()
                        if 'prompt' in item_data:
                            player_gen_item = next((item for item in self.intro_items if item['type'] == 'player_gen'), None)
                            if player_gen_item:
                                player_gen_item['prompt_input'].blockSignals(True)
                                player_gen_item['prompt_input'].setText(item_data['prompt'])
                                player_gen_item['prompt_input'].blockSignals(False)
                                checkboxes_data = item_data.get('checkboxes', {})
                                for field_name, checkbox in player_gen_item['checkboxes'].items():
                                    checkbox.blockSignals(True)
                                    checkbox.setChecked(checkboxes_data.get(field_name, False))
                                    checkbox.blockSignals(False)
                    elif item_data.get('type') == 'message':
                        self._add_intro_message_editor(item_data.get('text', ''))
            self._toggle_intro_text(checked)
        except Exception as e:
            print(f"[StartConditionsManager] Error loading intro state: {e}")
            self._toggle_intro_text(False)

    def _save_intro_state(self):
        if not self.variables_file:
            return
        try:
            if os.path.exists(self.variables_file):
                with open(self.variables_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            data['introduction_checked'] = self.intro_checkbox.isChecked()
            data['introduction_title'] = self.intro_title_lineedit.text()
            data['introduction_description'] = self.intro_desc_lineedit.text()
            intro_sequence = []
            for item in self.intro_items:
                if item['type'] == 'message':
                    editor = item.get('editor')
                    if editor and editor.toPlainText().strip():
                        intro_sequence.append({
                            'type': 'message',
                            'text': editor.toPlainText()
                        })
                elif item['type'] == 'player_gen':
                    prompt_input = item.get('prompt_input')
                    checkboxes = item.get('checkboxes', {})
                    
                    checkboxes_data = {}
                    for field_name, checkbox in checkboxes.items():
                        checkboxes_data[field_name] = checkbox.isChecked()
                    intro_sequence.append({
                        'type': 'player_gen',
                        'prompt': prompt_input.text() if prompt_input else 'Create your character:',
                        'checkboxes': checkboxes_data
                    })
            
            data['introduction_sequence'] = intro_sequence
            with open(self.variables_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[StartConditionsManager] Error saving intro state: {e}")

    def _load_origin(self):
        if not self.variables_file or not os.path.exists(self.variables_file):
            self.origin_lineedit.setText("Default Setting")
            return
        try:
            with open(self.variables_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            origin = data.get('origin', 'Default Setting')
            self.origin_lineedit.blockSignals(True)
            self.origin_lineedit.setText(origin)
            self.origin_lineedit.blockSignals(False)
        except Exception as e:
            print(f"[StartConditionsManager] Error loading origin: {e}")
            self.origin_lineedit.setText("Default Setting")

    def _save_origin(self):
        if not self.variables_file:
            return
        try:
            if os.path.exists(self.variables_file):
                with open(self.variables_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            data['origin'] = self.origin_lineedit.text() or "Default Setting"
            with open(self.variables_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[StartConditionsManager] Error saving origin: {e}")

    def _load_system_prompt(self):
        if self.system_context_file:
            try:
                gamestate_path = self.system_context_file.replace('system_context.txt', 'gamestate.json')
                if os.path.exists(gamestate_path):
                    with open(gamestate_path, 'r', encoding='utf-8') as f:
                        gamestate = json.load(f)
                    system_prompts = gamestate.get('system_prompts', {})
                    narrator_prompt = system_prompts.get('narrator', '')
                    self.system_prompt_editor.setPlainText(narrator_prompt)
                elif os.path.exists(self.system_context_file):
                    with open(self.system_context_file, 'r', encoding='utf-8') as f:
                        self.system_prompt_editor.setPlainText(f.read())
            except Exception as e:
                print(f"[StartConditionsManager] Error loading system prompt: {e}")

    def _save_system_prompt(self):
        if self.system_context_file:
            try:
                gamestate_path = self.system_context_file.replace('system_context.txt', 'gamestate.json')
                if os.path.exists(gamestate_path):
                    with open(gamestate_path, 'r', encoding='utf-8') as f:
                        gamestate = json.load(f)
                else:
                    gamestate = {}
                
                if 'system_prompts' not in gamestate:
                    gamestate['system_prompts'] = {}
                
                gamestate['system_prompts']['narrator'] = self.system_prompt_editor.toPlainText()
                
                with open(gamestate_path, 'w', encoding='utf-8') as f:
                    json.dump(gamestate, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[StartConditionsManager] Error saving system prompt: {e}")

    def _load_character_system_prompt(self):
        if self.system_context_file:
            try:
                gamestate_path = self.system_context_file.replace('system_context.txt', 'gamestate.json')
                if os.path.exists(gamestate_path):
                    with open(gamestate_path, 'r', encoding='utf-8') as f:
                        gamestate = json.load(f)
                    system_prompts = gamestate.get('system_prompts', {})
                    character_prompt = system_prompts.get('character', '')
                    self.character_system_prompt_editor.setPlainText(character_prompt)
            except Exception as e:
                print(f"[StartConditionsManager] Error loading character system prompt: {e}")

    def _save_character_system_prompt(self):
        if self.system_context_file:
            try:
                gamestate_path = self.system_context_file.replace('system_context.txt', 'gamestate.json')
                if os.path.exists(gamestate_path):
                    with open(gamestate_path, 'r', encoding='utf-8') as f:
                        gamestate = json.load(f)
                else:
                    gamestate = {}
                if 'system_prompts' not in gamestate:
                    gamestate['system_prompts'] = {}
                gamestate['system_prompts']['character'] = self.character_system_prompt_editor.toPlainText()
                with open(gamestate_path, 'w', encoding='utf-8') as f:
                    json.dump(gamestate, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[StartConditionsManager] Error saving character system prompt: {e}") 

    def _get_main_ui(self):
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'add_rule_sound'):
                return parent
            parent = parent.parentWidget()
        return None
    
    def _load_starting_datetime(self):
        if not self.variables_file or not os.path.exists(self.variables_file):
            return
        try:
            with open(self.variables_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            starting_datetime = data.get('starting_datetime', '2024-01-01 12:00:00')
            advancement_mode = data.get('advancement_mode', 'Static')
            time_multiplier = data.get('time_multiplier', 1.0)
            self.datetime_edit.blockSignals(True)
            self.datetime_edit.setDateTime(QDateTime.fromString(starting_datetime, "yyyy-MM-dd hh:mm"))
            self.datetime_edit.blockSignals(False)
            self.advancement_group.blockSignals(True)
            if advancement_mode == 'Realtime':
                self.realtime_radio.setChecked(True)
            else:
                self.static_radio.setChecked(True)
            self.advancement_group.blockSignals(False)
            self.time_multiplier_spin.blockSignals(True)
            self.time_multiplier_spin.setValue(time_multiplier)
            self.time_multiplier_spin.blockSignals(False)
        except Exception as e:
            print(f"[StartConditionsManager] Error loading starting datetime: {e}")
    
    def _save_starting_datetime(self):
        if not self.variables_file:
            return
        try:
            if os.path.exists(self.variables_file):
                with open(self.variables_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            data['starting_datetime'] = self.datetime_edit.dateTime().toString("yyyy-MM-dd hh:mm")
            with open(self.variables_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[StartConditionsManager] Error saving starting datetime: {e}")
    
    def _save_advancement_mode(self):
        if not self.variables_file:
            return
        try:
            if os.path.exists(self.variables_file):
                with open(self.variables_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            if self.realtime_radio.isChecked():
                data['advancement_mode'] = 'Realtime'
            else:
                data['advancement_mode'] = 'Static'
            
            with open(self.variables_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[StartConditionsManager] Error saving advancement mode: {e}")
    
    def _save_time_multiplier(self):
        if not self.variables_file:
            return
        try:
            if os.path.exists(self.variables_file):
                with open(self.variables_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            data['time_multiplier'] = self.time_multiplier_spin.value()
            
            with open(self.variables_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[StartConditionsManager] Error saving time multiplier: {e}")

    def _load_global_vars(self):
        if not self.variables_file or not os.path.exists(self.variables_file):
            return
        try:
            with open(self.variables_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            global_vars = data.get('global_variables', {})
            
            while self.global_vars_items:
                item = self.global_vars_items[0]
                widget = item['widget']
                self.global_vars_layout.removeWidget(widget)
                widget.setParent(None)
                self.global_vars_items.remove(item)
            
            if global_vars:
                for var_name, var_value in global_vars.items():
                    self._add_global_var_item(var_name, str(var_value))
            else:
                self._add_global_var_item()
        except Exception as e:
            print(f"[StartConditionsManager] Error loading global variables: {e}")
            self._add_global_var_item()

    def _save_global_vars(self):
        if not self.variables_file:
            return
        try:
            if os.path.exists(self.variables_file):
                with open(self.variables_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            global_vars = {}
            for item in self.global_vars_items:
                name_input = item.get('name_input')
                value_input = item.get('value_input')
                if name_input and value_input:
                    var_name = name_input.text().strip()
                    var_value = value_input.text().strip()
                    if var_name:
                        global_vars[var_name] = var_value
            
            data['global_variables'] = global_vars
            
            with open(self.variables_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[StartConditionsManager] Error saving global variables: {e}")
