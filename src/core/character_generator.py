from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import os
import json

class CharacterGeneratorWidget(QWidget):
    character_complete = pyqtSignal(int)
    def __init__(self, theme_colors=None, tab_index=None, parent=None):
        super().__init__(parent)
        self.tab_index = tab_index
        default_theme = {
            'base_color': '#00FF66',
            'bg_color': '#222222',
            'highlight': 'rgba(0,255,102,0.6)'
        }
        self.theme_colors = {**default_theme, **(theme_colors or {})}
        self._character_data = {}
        self._enabled_fields = {}
        self._prompt_text = "Create your character:"
        self._init_ui()
        self._apply_theme_styles()
        if hasattr(self, 'name_container'):
            self.name_container.setVisible(True)
        self._force_apply_input_styles()
        
    def _init_ui(self):
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(16777215, 16777215)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        title_label = QLabel("Character Creation")
        title_label.setFont(QFont('Consolas', 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("CharGenTitle")
        main_layout.addWidget(title_label)
        self.prompt_label = QLabel(self._prompt_text)
        self.prompt_label.setFont(QFont('Consolas', 12))
        self.prompt_label.setAlignment(Qt.AlignCenter)
        self.prompt_label.setObjectName("CharGenPrompt")
        main_layout.addWidget(self.prompt_label)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("CharGenScrollArea")
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_content = QWidget()
        scroll_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.fields_layout = QVBoxLayout(scroll_content)
        self.fields_layout.setSpacing(15)
        self._create_character_fields()
        self.fields_layout.addStretch(1)
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self.play_button = QPushButton("Play as [Character Name] →")
        self.play_button.setFont(QFont('Consolas', 12, QFont.Bold))
        self.play_button.setObjectName("CharGenPlayButton")
        self.play_button.setMinimumSize(300, 50)
        self.play_button.clicked.connect(self._on_play_clicked)
        button_layout.addWidget(self.play_button)
        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)
    
    def _create_character_fields(self):
        self._create_field("name", "Character Name:", QLineEdit)
        self._create_field("description", "Description:", QTextEdit, height=80)
        self._create_field("personality", "Personality:", QTextEdit, height=80)
        self._create_field("appearance", "Appearance:", QTextEdit, height=80)
        self._create_field("goals", "Goals:", QTextEdit, height=80)
        self._create_field("story", "Background Story:", QTextEdit, height=80)
        self._create_field("abilities", "Abilities:", QTextEdit, height=80)
        self._create_field("equipment", "Equipment:", QTextEdit, height=80)

    def _create_field(self, field_name, label_text, widget_class, height=None, is_required=False):
        field_container = QWidget()
        field_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        field_layout = QVBoxLayout(field_container)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(5)
        label = QLabel(label_text)
        label.setFont(QFont('Consolas', 11, QFont.Bold))
        label.setObjectName("CharGenFieldLabel")
        if is_required:
            label.setText(label_text + " *")
        field_layout.addWidget(label)
        input_widget = widget_class()
        input_widget.setObjectName(f"CharGenField_{field_name}")
        input_widget.setFont(QFont('Consolas', 11))
        input_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        if widget_class == QTextEdit:
            if height:
                input_widget.setMaximumHeight(height)
            input_widget.setMinimumHeight(60 if not height else height)
            input_widget.textChanged.connect(self._on_field_changed)
        else:
            input_widget.setMinimumHeight(30)
            input_widget.textChanged.connect(self._on_field_changed)
        field_layout.addWidget(input_widget)
        setattr(self, f"{field_name}_input", input_widget)
        setattr(self, f"{field_name}_container", field_container)
        self.fields_layout.addWidget(field_container)
        if field_name == 'name':
            field_container.setVisible(True)
        else:
            field_container.setVisible(False)

    def _on_field_changed(self):
        name = self.name_input.text().strip() if hasattr(self, 'name_input') else ""
        if name:
            self.play_button.setText(f"Play as {name} →")
        else:
            self.play_button.setText("Play as [Character Name] →")

    def _on_play_clicked(self):
        character_data = self._collect_character_data()
        if not character_data.get('name', '').strip():
            return
        if self._save_character(character_data):
            self.character_complete.emit(self.tab_index)

    def _collect_character_data(self):
        data = {}
        field_names = ['name', 'description', 'personality', 'appearance', 'goals', 'story', 'abilities', 'equipment']
        for field_name in field_names:
            if self._enabled_fields.get(field_name, False):
                input_widget = getattr(self, f"{field_name}_input", None)
                if input_widget:
                    if isinstance(input_widget, QTextEdit):
                        data[field_name] = input_widget.toPlainText().strip()
                    else:
                        data[field_name] = input_widget.text().strip()
        return data

    def _save_character(self, character_data):
        try:
            main_ui = self._get_main_ui()
            if not main_ui:
                return False
            if (not hasattr(main_ui, 'tabs_data') or 
                self.tab_index >= len(main_ui.tabs_data) or 
                not main_ui.tabs_data[self.tab_index]):
                return False
            tab_data = main_ui.tabs_data[self.tab_index]
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                return False
            game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
            os.makedirs(game_actors_dir, exist_ok=True)
            self._cleanup_existing_player_files(game_actors_dir)
            char_name = character_data.get('name', 'player')
            sanitized_name = self._sanitize_filename(char_name)
            player_file_path = os.path.join(game_actors_dir, f"{sanitized_name}.json")
            player_data = {
                "name": character_data.get('name', 'Player'),
                "isPlayer": True,
                "description": character_data.get('description', ''),
                "personality": character_data.get('personality', ''),
                "appearance": character_data.get('appearance', ''),
                "goals": character_data.get('goals', ''),
                "story": character_data.get('story', ''),
                "abilities": character_data.get('abilities', ''),
                "equipment": self._parse_equipment(character_data.get('equipment', '')),
                "variables": {},
                "relations": {},
                "location": "",
                "left_hand_holding": "",
                "right_hand_holding": ""
            }
            with open(player_file_path, 'w', encoding='utf-8') as f:
                json.dump(player_data, f, indent=2, ensure_ascii=False)
            self._update_player_name_in_settings(workflow_data_dir, char_name)
            return True
        except Exception as e:
            return False

    def _cleanup_existing_player_files(self, game_actors_dir):
        try:
            if not os.path.exists(game_actors_dir):
                return
            for filename in os.listdir(game_actors_dir):
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(game_actors_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if data.get('isPlayer', False) or data.get('variables', {}).get('is_player', False):
                            os.remove(file_path)
                    except Exception as e:
                        continue
        except Exception as e:
            pass

    def _parse_equipment(self, equipment_text):
        return {"general": equipment_text} if equipment_text else {}

    def _sanitize_filename(self, name):
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', name).strip()
        return sanitized.replace(' ', '_').lower() or 'player'

    def _get_main_ui(self):
        parent = self.parentWidget()
        while parent:
            if hasattr(parent, 'tabs_data') and hasattr(parent, 'current_tab_index'):
                return parent
            parent = parent.parentWidget()
        return None

    def _update_player_name_in_settings(self, workflow_data_dir, player_name):
        try:
            settings_dirs = [
                os.path.join(workflow_data_dir, 'game', 'settings'),
                os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
            ]
            updated_count = 0
            for settings_dir in settings_dirs:
                if not os.path.exists(settings_dir):
                    continue
                for root, dirs, files in os.walk(settings_dir):
                    if 'saves' in dirs:
                        dirs.remove('saves')
                    for filename in files:
                        if filename.lower().endswith('_setting.json'):
                            file_path = os.path.join(root, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    setting_data = json.load(f)
                                if 'characters' in setting_data and isinstance(setting_data['characters'], list):
                                    if 'Player' in setting_data['characters']:
                                        setting_data['characters'] = [
                                            player_name if char == 'Player' else char 
                                            for char in setting_data['characters']
                                        ]
                                        if 'game' in file_path:
                                            with open(file_path, 'w', encoding='utf-8') as f:
                                                json.dump(setting_data, f, indent=2, ensure_ascii=False)
                                            updated_count += 1
                                        else:
                                            relative_path = os.path.relpath(file_path, os.path.join(workflow_data_dir, 'resources', 'data files', 'settings'))
                                            game_file_path = os.path.join(workflow_data_dir, 'game', 'settings', relative_path)
                                            os.makedirs(os.path.dirname(game_file_path), exist_ok=True)
                                            with open(game_file_path, 'w', encoding='utf-8') as f:
                                                json.dump(setting_data, f, indent=2, ensure_ascii=False)
                                            updated_count += 1
                            except Exception as e:
                                continue
        except Exception as e:
            import traceback
            traceback.print_exc()

    def configure_from_intro_sequence(self, player_gen_data):
        if not player_gen_data:
            self._enabled_fields = {
                'name': True,
                'description': True, 
                'personality': True,
                'appearance': True,
                'goals': True,
                'story': True,
                'abilities': True,
                'equipment': True
            }
        else:
            self._prompt_text = player_gen_data.get('prompt', 'Create your character:')
            self.prompt_label.setText(self._prompt_text)
            checkboxes = player_gen_data.get('checkboxes', {})
            self._enabled_fields = checkboxes.copy()
        field_names = ['name', 'description', 'personality', 'appearance', 'goals', 'story', 'abilities', 'equipment']
        for field_name in field_names:
            container = getattr(self, f"{field_name}_container", None)
            if container:
                is_enabled = self._enabled_fields.get(field_name, False)
                container.setVisible(is_enabled)
        if hasattr(self, 'name_container'):
            self.name_container.setVisible(True)
            self._enabled_fields['name'] = True
        visible_count = sum(1 for field in field_names if self._enabled_fields.get(field, False))
        if visible_count == 0:
            basic_fields = ['name', 'description', 'personality', 'appearance']
            for field_name in basic_fields:
                self._enabled_fields[field_name] = True
                container = getattr(self, f"{field_name}_container", None)
                if container:
                    container.setVisible(True)
    
    def _apply_theme_styles(self):
        base_color = self.theme_colors['base_color']
        bg_color = self.theme_colors['bg_color']
        main_widget_style = f"""
            CharacterGeneratorWidget {{
                background-color: {bg_color};
                border: none;
                padding: 10px;
                min-height: 100%;
                min-width: 100%;
                max-height: 16777215px;
                max-width: 16777215px;
            }}
        """
        title_style = f"""
            QLabel#CharGenTitle {{
                color: {base_color};
                background: transparent;
            }}
        """
        prompt_style = f"""
            QLabel#CharGenPrompt {{
                color: {QColor(base_color).lighter(120).name()};
                background: transparent;
                margin: 10px 0px;
            }}
        """
        field_label_style = f"""
            QLabel#CharGenFieldLabel {{
                color: {base_color};
                background: transparent;
            }}
        """
        input_style = f"""
            QLineEdit {{
                color: {base_color};
                background-color: {QColor(bg_color).lighter(105).name()};
                border: 2px solid {base_color} !important;
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {QColor(base_color).darker(300).name()};
                selection-color: white;
                font-family: Consolas;
                font-size: 11pt;
                min-height: 20px;
            }}
            QTextEdit {{
                color: {base_color};
                background-color: {QColor(bg_color).lighter(105).name()};
                border: 2px solid {base_color} !important;
                border-radius: 4px;
                padding: 8px;
                selection-background-color: {QColor(base_color).darker(300).name()};
                selection-color: white;
                font-family: Consolas;
                font-size: 11pt;
                min-height: 60px;
            }}
            QLineEdit:focus {{
                border: 3px solid {QColor(base_color).lighter(120).name()} !important;
                background-color: {QColor(bg_color).lighter(110).name()};
            }}
            QTextEdit:focus {{
                border: 3px solid {QColor(base_color).lighter(120).name()} !important;
                background-color: {QColor(bg_color).lighter(110).name()};
            }}
        """
        button_style = f"""
            QPushButton#CharGenPlayButton {{
                background-color: transparent;
                border: 2px solid {base_color};
                color: {base_color};
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
            }}
            QPushButton#CharGenPlayButton:hover {{
                background-color: {QColor(base_color).lighter(110).name()};
                color: {bg_color};
            }}
            QPushButton#CharGenPlayButton:pressed {{
                background-color: {QColor(base_color).darker(110).name()};
                color: {bg_color};
            }}
        """
        scroll_style = f"""
            QScrollArea#CharGenScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollArea#CharGenScrollArea QWidget {{
                background: transparent;
            }}
        """
        self.setStyleSheet(main_widget_style + title_style + prompt_style + field_label_style + input_style + button_style + scroll_style)
        
    def _force_apply_input_styles(self):
        base_color = self.theme_colors['base_color']
        bg_color = self.theme_colors['bg_color']
        style = f"""
            color: {base_color};
            background-color: {QColor(bg_color).lighter(105).name()};
            border: 2px solid {base_color};
            border-radius: 4px;
            padding: 8px;
            font-family: Consolas;
            font-size: 11pt;
        """
        for widget in self.findChildren(QLineEdit):
            widget.setStyleSheet(style + "min-height: 20px;")
        for widget in self.findChildren(QTextEdit):
            widget.setStyleSheet(style + "min-height: 60px;")

    def update_theme(self, theme_colors):
        default_theme = {
            'base_color': '#00FF66',
            'bg_color': '#222222',
            'highlight': 'rgba(0,255,102,0.6)'
        }
        self.theme_colors = {**default_theme, **(theme_colors or {})}
        self._apply_theme_styles()
        self._force_apply_input_styles() 