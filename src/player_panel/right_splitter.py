from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSplitter, QPushButton, QHBoxLayout, QStackedWidget, QScrollArea, QFrame, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import json
import os
import glob
from datetime import datetime

def get_display_name_from_setting(setting_name):
    if not setting_name or setting_name == "--":
        return "--"
    parts = setting_name.split(',')
    return parts[-1].strip() if parts else setting_name

class RightSplitterWidget(QWidget):
    def __init__(self, theme_settings=None, parent=None):
        super().__init__(parent)
        self.setObjectName("RightSplitterWidget")
        self.theme_settings = theme_settings if theme_settings is not None else {}
        self.main_app = parent
        self._workflow_data_dir = None
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        button_layout = QHBoxLayout()
        self.setting_button = QPushButton("Setting")
        self.setting_button.setFocusPolicy(Qt.NoFocus)
        self.character_button = QPushButton("Character")
        self.character_button.setFocusPolicy(Qt.NoFocus)
        self.inventory_button = QPushButton("Inventory")
        self.inventory_button.setFocusPolicy(Qt.NoFocus)
        button_layout.addWidget(self.character_button)
        button_layout.addWidget(self.inventory_button)
        button_layout.addWidget(self.setting_button)
        main_layout.addLayout(button_layout)
        self.stacked_widget = QStackedWidget()
        self.character_page = self._create_character_page()
        self.inventory_page = self._create_inventory_page()
        self.setting_page = self._create_setting_page()
        self.stacked_widget.addWidget(self.character_page)
        self.stacked_widget.addWidget(self.inventory_page)
        self.stacked_widget.addWidget(self.setting_page)
        self.character_button.clicked.connect(lambda: self._switch_to_tab_with_sound(0))
        self.inventory_button.clicked.connect(lambda: self._switch_to_tab_with_sound(1))
        self.setting_button.clicked.connect(lambda: self._switch_to_tab_with_sound(2))
        self.stacked_widget.currentChanged.connect(self._update_button_states)
        main_layout.addWidget(self.stacked_widget)
        self._apply_button_theme()
        self.stacked_widget.setCurrentIndex(2)
        self.setLayout(main_layout)
        self.setMaximumWidth(300)

    @property
    def workflow_data_dir(self):
        return self._workflow_data_dir
    
    @workflow_data_dir.setter
    def workflow_data_dir(self, value):
        self._workflow_data_dir = value
        if value:
            self.load_character_data()
            self._update_game_time()

    def _create_setting_page(self):
        page = QWidget()
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        self.setting_name_label = QLabel("--")
        self.setting_name_label.setAlignment(Qt.AlignCenter)
        self.setting_name_label.setStyleSheet("font-weight: bold; padding: 2px; border-bottom: 1px solid gray;")
        top_layout.addWidget(self.setting_name_label)
        self.setting_description_label = QLabel("--")
        self.setting_description_label.setAlignment(Qt.AlignCenter)
        self.setting_description_label.setWordWrap(True)
        self.setting_description_label.setStyleSheet("font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace; font-size: 9pt; padding: 1px; margin: 0;")
        top_layout.addWidget(self.setting_description_label)
        self.characters_label = QLabel("Characters: --")
        self.characters_label.setAlignment(Qt.AlignLeft)
        self.characters_label.setWordWrap(True)
        self.characters_label.setStyleSheet("font-weight: bold; font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace; font-size: 10pt; margin: 0; padding: 1px;")
        top_layout.addWidget(self.characters_label)
        self.game_time_label = QLabel("Game Time: --")
        self.game_time_label.setAlignment(Qt.AlignCenter)
        self.game_time_label.setStyleSheet("font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace; font-size: 10pt; padding: 1px; margin: 0;")
        top_layout.addWidget(self.game_time_label)
        try:
            from player_panel.world_map import create_world_map
            self.setting_minimap_widget = create_world_map(parent=self, theme_settings=self.theme_settings)
            self.setting_minimap_widget.setObjectName("SettingMiniMap")
        except ImportError:
            self.setting_minimap_widget = QWidget()
            self.setting_minimap_widget.setMinimumHeight(80)
            self.setting_minimap_widget.setObjectName("SettingMiniMap")
            if not self.setting_minimap_widget.layout():
                minimap_layout = QVBoxLayout(self.setting_minimap_widget)
                minimap_layout.setContentsMargins(0, 0, 0, 0)
                minimap_label = QLabel("World map will display here when a setting is selected.\nIt will automatically load the appropriate map for each location.")
                minimap_label.setAlignment(Qt.AlignCenter)
                minimap_label.setStyleSheet("color: #888; font-style: italic; padding: 8px; background-color: rgba(0,0,0,0.1); border-radius: 5px;")
                minimap_layout.addWidget(minimap_label)
        splitter.addWidget(top_widget)
        splitter.addWidget(self.setting_minimap_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        self.setting_minimap_widget.setMinimumHeight(200)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        return page
    
    def _create_inventory_page(self):
        page = QWidget()
        page.setObjectName("InventoryPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        scroll_area = QScrollArea()
        scroll_area.setObjectName("InventoryScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.NoFrame)
        inventory_content = QWidget()
        inventory_content.setObjectName("InventoryContent")
        inv_layout = QVBoxLayout(inventory_content)
        inv_layout.setContentsMargins(5, 5, 5, 5)
        inv_layout.setSpacing(5)
        held_frame = self._create_section_frame("Held Items")
        held_layout = QGridLayout()
        held_layout.setSpacing(3)
        left_hand_label = QLabel("Left:")
        left_hand_label.setObjectName("HeldItemSlotLabel")
        self.left_hand_item = QLabel("(empty)")
        self.left_hand_item.setObjectName("HeldItemLabel")
        right_hand_label = QLabel("Right:")
        right_hand_label.setObjectName("HeldItemSlotLabel")
        self.right_hand_item = QLabel("(empty)")
        self.right_hand_item.setObjectName("HeldItemLabel")
        held_layout.addWidget(left_hand_label, 0, 0)
        held_layout.addWidget(self.left_hand_item, 1, 0)
        held_layout.addWidget(right_hand_label, 0, 1)
        held_layout.addWidget(self.right_hand_item, 1, 1)
        held_frame.layout().addLayout(held_layout)
        inv_layout.addWidget(held_frame)
        equipment_frame = self._create_section_frame("Equipment")
        equipment_grid = QGridLayout()
        equipment_grid.setSpacing(2)
        equipment_groups = [
            # Group 1: Head & Neck
            [[("head", "Head", 1)], [("neck", "Neck", 1)]],
            # Group 2: Shoulders
            [[("left_shoulder", "L.Shoulder", 0), ("right_shoulder", "R.Shoulder", 2)]],
            # Group 3: Hands
            [[("left_hand", "L.Hand (Worn)", 0), ("right_hand", "R.Hand (Worn)", 2)]],
            # Group 4: Uppers
            [[("upper_over", "Upper Layer 4", 1)], [("upper_outer", "Upper Layer 3", 1)], [("upper_middle", "Upper Layer 2", 1)], [("upper_inner", "Upper Layer 1", 1)]],
            # Group 5: Lowers
            [[("lower_outer", "Lower Layer 3", 1)], [("lower_middle", "Lower Layer 2", 1)], [("lower_inner", "Lower Layer 1", 1)]],
            # Group 6: Feet
            [[("left_foot_outer", "L.Foot Outer", 0), ("right_foot_outer", "R.Foot Outer", 2)], [("left_foot_inner", "L.Foot Inner", 0), ("right_foot_inner", "R.Foot Inner", 2)]]
        ]
        row = 0
        self.equipment_labels = {}
        base_color = self.theme_settings.get("base_color", "#CCCCCC")
        try:
            q_base_color = QColor(base_color)
            separator_color = q_base_color.darker(160).name() if q_base_color.isValid() else "#444444"
        except:
            separator_color = "#444444"
        for group_idx, group in enumerate(equipment_groups):
            for row_items in group:
                for slot_key, display_name, col in row_items:
                    slot_label = QLabel(f"{display_name}:")
                    slot_label.setObjectName("EquipmentSlotLabel")
                    equipment_grid.addWidget(slot_label, row, col)
                    item_label = QLabel("(empty)")
                    item_label.setObjectName("EquipmentItemLabel")
                    item_label.setWordWrap(True)
                    equipment_grid.addWidget(item_label, row + 1, col)
                    self.equipment_labels[slot_key] = item_label
                row += 2
            if group_idx < len(equipment_groups) - 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet(f"QFrame {{ border: none; background-color: {separator_color}; min-height: 1px; max-height: 1px; }}")
                equipment_grid.addWidget(separator, row, 0, 1, 3)
                row += 1
        equipment_frame.layout().addLayout(equipment_grid)
        inv_layout.addWidget(equipment_frame)
        containers_frame = self._create_section_frame("Containers")
        containers_frame.layout().addStretch(1)
        inv_layout.addWidget(containers_frame, 1)
        scroll_area.setWidget(inventory_content)
        layout.addWidget(scroll_area)
        return page
    
    def _create_character_page(self):
        page = QWidget()
        page.setObjectName("CharacterSheetPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        self.char_name_label = QLabel("Loading character...")
        self.char_name_label.setObjectName("CharacterNameLabel")
        self.char_name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.char_name_label)
        self.char_status_label = QLabel("Status: Loading...")
        self.char_status_label.setObjectName("CharacterStatusLabel")
        self.char_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.char_status_label)
        desc_frame = self._create_section_frame("Description")
        self.char_description_label = QLabel("Loading character description...")
        self.char_description_label.setObjectName("CharacterDescriptionLabel")
        self.char_description_label.setWordWrap(True)
        self.char_description_label.setAlignment(Qt.AlignTop)
        desc_frame.layout().addWidget(self.char_description_label)
        layout.addWidget(desc_frame, 1)
        appearance_frame = self._create_section_frame("Appearance")
        self.char_appearance_label = QLabel("Loading appearance...")
        self.char_appearance_label.setObjectName("CharacterAppearanceLabel")
        self.char_appearance_label.setWordWrap(True)
        self.char_appearance_label.setAlignment(Qt.AlignTop)
        appearance_frame.layout().addWidget(self.char_appearance_label)
        layout.addWidget(appearance_frame, 1)
        if self.workflow_data_dir:
            self.load_character_data()
        return page
    
    def _create_section_frame(self, title):
        frame = QFrame()
        frame.setObjectName("CharacterSectionFrame")
        frame.setFrameStyle(QFrame.Box)
        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(5)
        title_label = QLabel(title)
        title_label.setObjectName("CharacterSectionTitle")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        return frame

    def _apply_button_theme(self):
        base_color = self.theme_settings.get("base_color", "#CCCCCC")
        contrast = self.theme_settings.get("contrast", 0.35)
        try:
            q_base_color = QColor(base_color)
            if not q_base_color.isValid():
                raise ValueError("Invalid base color")
            bg_value_default = int(80 * contrast)
            bg_color_hex_default = f"#{bg_value_default:02x}{bg_value_default:02x}{bg_value_default:02x}"
            text_color_hex_default = q_base_color.darker(170).name()
            border_color_hex_default = base_color
            bg_color_hex_selected = q_base_color.darker(110).name()
            text_color_hex_selected = q_base_color.darker(200).name()
            border_color_hex_selected = q_base_color.name()
        except (ValueError, TypeError):
            bg_color_hex_default = "#222222"
            text_color_hex_default = "#999999"
            border_color_hex_default = "#555555"
            bg_color_hex_selected = "#333333"
            text_color_hex_selected = "#BBBBBB"
            border_color_hex_selected = "#AAAAAA"
        self.button_default_style = f"""
            QPushButton {{
                background-color: {bg_color_hex_default};
                color: {text_color_hex_default};
                border: 1px solid {border_color_hex_default};
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {q_base_color.lighter(120).name() if 'q_base_color' in locals() else '#383838'};
            }}
            QPushButton:pressed {{
                background-color: {q_base_color.darker(120).name() if 'q_base_color' in locals() else '#1a1a1a'};
            }}
        """
        self.button_selected_style = f"""
            QPushButton {{
                background-color: {bg_color_hex_selected};
                color: {text_color_hex_selected};
                border: 1px solid {border_color_hex_selected};
                border-bottom: 3px solid {border_color_hex_selected}; /* Highlight with thicker bottom border */
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }}
        """

    def _update_button_states(self, index):
        all_buttons = [self.character_button, self.inventory_button, self.setting_button]
        for i, button in enumerate(all_buttons):
            if i == index:
                button.setStyleSheet(self.button_selected_style)
            else:
                button.setStyleSheet(self.button_default_style)
        if index == 0 and hasattr(self, 'char_name_label'):
            self.load_character_data()
        elif index == 1 and hasattr(self, 'equipment_labels'):
            self.load_character_data()
        elif index == 2 and hasattr(self, 'setting_minimap_widget'):
            pass

    def update_theme(self, theme_settings):
        self.theme_settings = theme_settings if theme_settings is not None else {}
        self._apply_button_theme()
        if hasattr(self, 'setting_minimap_widget') and hasattr(self.setting_minimap_widget, 'map_display'):
            try:
                from player_panel.world_map import update_map_theme
                update_map_theme(self.setting_minimap_widget, theme_settings)
            except ImportError:
                pass

    def _apply_actors_list_theme(self):
        base_color = self.theme_settings.get("base_color", "#CCCCCC")
        contrast = self.theme_settings.get("contrast", 0.35)
        try:
            q_base_color = QColor(base_color)
            if not q_base_color.isValid():
                raise ValueError("Invalid base color")
            bg_value = int(80 * contrast)
            bg_color_hex = f"#{bg_value:02x}{bg_value:02x}{bg_value:02x}"
            text_color_hex = q_base_color.darker(170).name()
            border_color_hex = base_color
        except (ValueError, TypeError):
            bg_color_hex = "#222222"
            text_color_hex = "#999999"
            border_color_hex = "#555555"
        style = f"""
            QListWidget {{
                background-color: {bg_color_hex};
                color: {text_color_hex};
                border: 1px solid {border_color_hex};
                font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
                font-size: 10pt;
            }}
            QListWidget:disabled {{
                background-color: #333333;
                color: #888888;
                border: 1px solid #555555;
            }}
        """
        self.actors_list.setStyleSheet(style)

    def update_setting_name(self, setting_name, workflow_data_dir=None):
        try:
            display_name = get_display_name_from_setting(setting_name)
            if hasattr(self, 'setting_name_label'):
                self.setting_name_label.setText(display_name)
            
            setting_description = "--"
            if workflow_data_dir and setting_name and setting_name != "--":
                setting_description = self._load_setting_description(setting_name, workflow_data_dir)
            
            if hasattr(self, 'setting_description_label'):
                self.setting_description_label.setText(setting_description)
            
            if workflow_data_dir:
                self.workflow_data_dir = workflow_data_dir
            if hasattr(self, 'workflow_data_dir') and self.workflow_data_dir:
                self.load_character_data()
            if not (hasattr(self, '_last_loaded_setting') and self._last_loaded_setting == setting_name):
                try:
                    from player_panel.world_map import set_map_image_from_qimage
                    set_map_image_from_qimage(self.setting_minimap_widget, None)
                except ImportError:
                    pass
                except Exception:
                    pass
            if workflow_data_dir is None and hasattr(self, 'workflow_data_dir'):
                workflow_data_dir = self.workflow_data_dir
            qimage_for_map = None
            if workflow_data_dir and setting_name and setting_name != "--" and hasattr(self, 'setting_minimap_widget'):
                try:
                    try:
                        from player_panel.world_map import set_map_image_from_qimage, update_player_position
                        from PyQt5.QtGui import QImage
                        world_map_available = True
                    except ImportError:
                        world_map_available = False
                    if world_map_available:
                        def resolve_relative_path(base_path, relative_path):
                            if relative_path.startswith(".."):
                                rel_components = relative_path.replace('\\', '/').split('/')
                                current_path = base_path
                                
                                i = 0
                                while i < len(rel_components) and rel_components[i] == "..":
                                    parent = os.path.dirname(current_path)
                                    current_path = parent
                                    i += 1
                                remaining_components = rel_components[i:]
                                if remaining_components:
                                    remaining_path = os.path.join(*remaining_components)
                                    resolved = os.path.normpath(os.path.join(current_path, remaining_path))
                                else:
                                    resolved = os.path.normpath(current_path)
                                return resolved
                            else:
                                resolved = os.path.normpath(os.path.join(base_path, relative_path))
                                return resolved
                        
                        def load_image_if_exists(image_path):
                            if not image_path:
                                return None
                            dir_path = os.path.dirname(image_path)
                            filename = os.path.basename(image_path)
                            if os.path.exists(dir_path):
                                try:
                                    files_in_dir = os.listdir(dir_path)
                                    filename_lower = filename.lower()
                                    for file in files_in_dir:
                                        if file.lower() == filename_lower:
                                            actual_path = os.path.join(dir_path, file)
                                            if os.path.exists(actual_path):
                                                image_path = actual_path
                                                break
                                except Exception:
                                    pass
                            if not os.path.exists(image_path):
                                import getpass
                                username = getpass.getuser()
                                user_fallback_path = None
                                if "Downloads" in image_path:
                                    if image_path.startswith("C:\\Downloads"):
                                        user_fallback_path = image_path.replace("C:\\Downloads", f"C:\\Users\\{username}\\Downloads")
                                    elif image_path.startswith("Downloads\\") or image_path == "Downloads":
                                        relative_part = image_path[len("Downloads\\"):] if image_path.startswith("Downloads\\") else ""
                                        user_fallback_path = os.path.join(f"C:\\Users\\{username}\\Downloads", relative_part)
                                elif "Pictures" in image_path:
                                    if image_path.startswith("C:\\Pictures"):
                                        user_fallback_path = image_path.replace("C:\\Pictures", f"C:\\Users\\{username}\\Pictures")
                                    elif image_path.startswith("Pictures\\") or image_path == "Pictures":
                                        relative_part = image_path[len("Pictures\\"):] if image_path.startswith("Pictures\\") else ""
                                        user_fallback_path = os.path.join(f"C:\\Users\\{username}\\Pictures", relative_part)
                                if user_fallback_path:
                                    if os.path.exists(user_fallback_path):
                                        image_path = user_fallback_path
                                    else:
                                        return None
                                else:
                                    return None
                            try:
                                temp_qimage = QImage(image_path)
                                if not temp_qimage.isNull():
                                    return temp_qimage
                            except Exception as e:
                                pass
                            return None
                        setting_file = None
                        search_dirs = [
                            os.path.join(workflow_data_dir, "game", "settings"),
                            os.path.join(workflow_data_dir, "resources", "data files", "settings")
                        ]
                        for settings_dir in search_dirs:
                            if os.path.exists(settings_dir):
                                for root, dirs, files in os.walk(settings_dir):
                                    for file in files:
                                        if file.endswith("_setting.json"):
                                            file_path = os.path.join(root, file)
                                            try:
                                                with open(file_path, 'r', encoding='utf-8') as f:
                                                    data = json.load(f)
                                                if data.get("name") == setting_name:
                                                    setting_file = file_path
                                                    break
                                            except: 
                                                continue
                                        if setting_file:
                                            break
                                    if setting_file:
                                        break
                                if setting_file:
                                    break
                        if setting_file:
                            setting_dir = os.path.dirname(setting_file)
                            world_name = None
                            path_parts = setting_dir.replace('\\', '/').split('/')
                            if len(path_parts) >= 2:
                                if 'settings' in path_parts:
                                    settings_index = len(path_parts) - 1 - path_parts[::-1].index('settings')
                                    if settings_index + 1 < len(path_parts):
                                        world_name = path_parts[settings_index + 1]
                            if world_name:
                                world_json_locations = [
                                    os.path.join(workflow_data_dir, "resources", "data files", "settings", world_name, f"{world_name}_world.json"),
                                    os.path.join(workflow_data_dir, "game", "settings", world_name, f"{world_name}_world.json")
                                ]
                                for world_json_path in world_json_locations:
                                    if os.path.exists(world_json_path):
                                        try:
                                            with open(world_json_path, 'r', encoding='utf-8') as f:
                                                world_data = json.load(f)
                                            map_image_path = world_data.get('map_image')
                                            if map_image_path:
                                                resolved_path = resolve_relative_path(os.path.dirname(world_json_path), map_image_path)
                                                qimage_for_map = load_image_if_exists(resolved_path)
                                                if qimage_for_map:
                                                    break
                                        except Exception as e:
                                            pass
                                    if qimage_for_map:
                                        break
                            if not qimage_for_map:
                                current_dir = os.path.dirname(setting_file)
                                hierarchy_levels = ["setting", "location", "region"]
                                for level_idx, level_name in enumerate(hierarchy_levels):
                                    if not current_dir or not os.path.exists(current_dir):
                                        break
                                    json_patterns = []
                                    if level_name == "setting":
                                        json_patterns = ["*_setting.json"]
                                    elif level_name == "location":
                                        json_patterns = ["*_location.json"]
                                    elif level_name == "region":
                                        json_patterns = ["*_region.json"]
                                    for pattern in json_patterns:
                                        matching_files = glob.glob(os.path.join(current_dir, pattern))
                                        for json_file in matching_files:
                                            try:
                                                with open(json_file, 'r', encoding='utf-8') as f:
                                                    data = json.load(f)
                                                map_image_path = data.get('map_image')
                                                if map_image_path:
                                                    resolved_path = resolve_relative_path(os.path.dirname(json_file), map_image_path)
                                                    qimage_for_map = load_image_if_exists(resolved_path)
                                                    if qimage_for_map:
                                                        break
                                            except Exception as e:
                                                pass
                                        if qimage_for_map:
                                            break
                                    
                                    if qimage_for_map:
                                        break
                                    parent_dir = os.path.dirname(current_dir)
                                    if parent_dir == current_dir:
                                        break
                                    current_dir = parent_dir
                        if not qimage_for_map:
                            map_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
                            for root, dirs, files in os.walk(workflow_data_dir):
                                for file in files:
                                    if ('map' in file.lower() or 'world' in file.lower()) and any(file.lower().endswith(ext) for ext in map_extensions):
                                        potential_map = os.path.join(root, file)
                                        qimage_for_map = load_image_if_exists(potential_map)
                                        if qimage_for_map:
                                            break
                                if qimage_for_map:
                                    break
                        if qimage_for_map and not qimage_for_map.isNull():
                            try:
                                if hasattr(self, '_last_loaded_setting') and self._last_loaded_setting == setting_name:
                                    if hasattr(self.setting_minimap_widget, 'map_display'):
                                        update_player_position(self.setting_minimap_widget.map_display, workflow_data_dir)
                                    else:
                                        update_player_position(self.setting_minimap_widget, workflow_data_dir)
                                else:
                                    set_map_image_from_qimage(self.setting_minimap_widget, qimage_for_map, preserve_view_state=False)
                                    
                                    if hasattr(self.setting_minimap_widget, 'map_display'):
                                        update_player_position(self.setting_minimap_widget.map_display, workflow_data_dir)
                                    else:
                                        update_player_position(self.setting_minimap_widget, workflow_data_dir)
                                self._last_loaded_setting = setting_name
                            except Exception:
                                try:
                                    set_map_image_from_qimage(self.setting_minimap_widget, None)
                                except:
                                    pass
                except Exception:
                    pass
            try:
                self._update_characters_list(setting_name, workflow_data_dir)
            except Exception:
                if hasattr(self, 'characters_label'):
                    self.characters_label.setText("Characters: (error loading)")
        except Exception:
            if hasattr(self, 'setting_name_label'):
                self.setting_name_label.setText(setting_name)
            if hasattr(self, 'characters_label'):
                self.characters_label.setText("Characters: (error)")

    def _load_setting_description(self, setting_name, workflow_data_dir):
        if not workflow_data_dir or not setting_name or setting_name == "--":
            return "--"
        
        try:
            setting_file = None
            game_settings_dir = os.path.join(workflow_data_dir, "game", "settings")
            resources_settings_dir = os.path.join(workflow_data_dir, "resources", "data files", "settings")
            
            for settings_dir in [game_settings_dir, resources_settings_dir]:
                if os.path.exists(settings_dir):
                    for root, dirs, files in os.walk(settings_dir):
                        for file in files:
                            if file.endswith("_setting.json"):
                                file_path = os.path.join(root, file)
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                    if data.get("name") == setting_name:
                                        setting_file = file_path
                                        break
                                except: 
                                    continue
                            if setting_file:
                                break
                        if setting_file:
                            break
                    if setting_file:
                        break
            
            if setting_file:
                with open(setting_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                description = data.get('description', '--')
                return description if description else "--"
            
            return "--"
        except Exception:
            return "--"

    def _update_characters_list(self, setting_name, workflow_data_dir):
        if not workflow_data_dir or not setting_name or setting_name == "--":
            return
        try:
            setting_file_for_chars = None
            game_settings_dir = os.path.join(workflow_data_dir, "game", "settings")
            resources_settings_dir = os.path.join(workflow_data_dir, "resources", "data files", "settings")
            for settings_dir in [game_settings_dir, resources_settings_dir]:
                if os.path.exists(settings_dir):
                    for root, dirs, files in os.walk(settings_dir):
                        for file in files:
                            if file.endswith("_setting.json") and os.path.exists(os.path.join(root, file)):
                                path_char = os.path.join(root, file)
                                with open(path_char, 'r', encoding='utf-8') as f_char:
                                    try:
                                        data_char = json.load(f_char)
                                        if data_char.get("name") == setting_name:
                                            setting_file_for_chars = path_char
                                    except: 
                                        continue
                                if setting_file_for_chars: 
                                    break
                        if setting_file_for_chars: 
                            break
                    if setting_file_for_chars: 
                        break
            actors = []
            if setting_file_for_chars:
                with open(setting_file_for_chars, 'r', encoding='utf-8') as f_char_data:
                    data_char_list = json.load(f_char_data)
                actors_raw = data_char_list.get('characters', [])
            actors = [actor for actor in actors_raw if isinstance(actor, str)]
            player_name = None
            actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
            if os.path.isdir(actors_dir):
                for filename in os.listdir(actors_dir):
                    if filename.lower().endswith('.json'):
                        file_path = os.path.join(actors_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f_actor:
                                data_actor = json.load(f_actor)
                            if data_actor.get('isPlayer', False) or data_actor.get('variables', {}).get('is_player', False):
                                player_name = data_actor.get('name')
                                break
                        except Exception:
                            pass
            if not player_name:
                player_name = 'Player'
            if player_name and player_name != 'Player':
                actors = [a for a in actors if a.lower() != 'player']
            if player_name and player_name not in actors:
                actors = [player_name] + actors
            elif player_name:
                actors = [player_name] + [a for a in actors if a != player_name]
            characters_text = f"Characters: {', '.join(actors) if actors else '--'}"
            if hasattr(self, 'characters_label'):
                self.characters_label.setText(characters_text)
        except Exception:
            if hasattr(self, 'characters_label'):
                self.characters_label.setText("Characters: (error loading)")

    def load_character_data(self):
        if not self.workflow_data_dir:
            self._set_character_loading_state("No workflow directory set")
            return
        if not hasattr(self, 'char_name_label'):
            return
        try:
            player_data = None
            session_actors_dir = os.path.join(self.workflow_data_dir, 'game', 'actors')
            if os.path.isdir(session_actors_dir):
                for filename in os.listdir(session_actors_dir):
                    if filename.lower().endswith('.json'):
                        file_path = os.path.join(session_actors_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            if data.get('isPlayer') is True:
                                player_data = data
                                player_name = data.get('name', 'Player')
                                break
                        except Exception as e:
                            pass
            if not player_data:
                base_actors_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'actors')
                if os.path.isdir(base_actors_dir):
                    for filename in os.listdir(base_actors_dir):
                        if filename.lower().endswith('.json'):
                            file_path = os.path.join(base_actors_dir, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                if data.get('isPlayer') is True:
                                    player_data = data
                                    player_name = data.get('name', 'Player')
                                    break
                            except Exception as e:
                                pass
            if not player_data:
                for actors_dir in [session_actors_dir, base_actors_dir]:
                    if os.path.isdir(actors_dir):
                        for filename in os.listdir(actors_dir):
                            if filename.lower().endswith('.json'):
                                file_path = os.path.join(actors_dir, filename)
                                try:
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        data = json.load(f)
                                    if data.get('variables', {}).get('is_player', False):
                                        player_data = data
                                        player_name = data.get('name', 'Player')
                                        break
                                except Exception as e:
                                    pass
                        if player_data:
                            break
            if not player_data:
                self._set_character_loading_state("Player character not found")
                return
            self._update_character_display(player_data)
        except Exception as e:
            self._set_character_loading_state(f"Error loading character: {e}")
    
    def _set_character_loading_state(self, message):
        if hasattr(self, 'char_name_label'):
            self.char_name_label.setText("Character")
            self.char_status_label.setText(f"Status: {message}")
            self.char_description_label.setText(message)
            self.char_appearance_label.setText("")
        if hasattr(self, 'equipment_labels'):
            for label in self.equipment_labels.values():
                label.setText("(empty)")
                label.setProperty("equipped", False)
                label.style().unpolish(label)
                label.style().polish(label)
        if hasattr(self, 'left_hand_item'):
            self.left_hand_item.setText("(empty)")
            self.left_hand_item.setProperty("equipped", False)
            self.left_hand_item.style().unpolish(self.left_hand_item)
            self.left_hand_item.style().polish(self.left_hand_item)
        if hasattr(self, 'right_hand_item'):
            self.right_hand_item.setText("(empty)")
            self.right_hand_item.setProperty("equipped", False)
            self.right_hand_item.style().unpolish(self.right_hand_item)
            self.right_hand_item.style().polish(self.right_hand_item)

    def _update_character_display(self, player_data):
        name = player_data.get('name', 'Player')
        status = player_data.get('status', 'Ready for adventure!')
        description = player_data.get('description', 'No description available.')
        appearance = player_data.get('appearance', 'No appearance description.')
        if hasattr(self, 'char_name_label'):
            self.char_name_label.setText(name)
            self.char_status_label.setText(f"Status: {status}")
            self.char_description_label.setText(description if description.strip() else "No description available.")
            self.char_appearance_label.setText(appearance if appearance.strip() else "No appearance description.")
        if hasattr(self, 'equipment_labels'):
            equipment = player_data.get('equipment', {})
            for slot_key, label in self.equipment_labels.items():
                item = equipment.get(slot_key, "")
                if item and item.strip():
                    label.setText(item)
                    label.setProperty("equipped", True)
                else:
                    label.setText("(empty)")
                    label.setProperty("equipped", False)
                label.style().unpolish(label)
                label.style().polish(label)
        if hasattr(self, 'left_hand_item') and hasattr(self, 'right_hand_item'):
            left_hand = player_data.get('left_hand_holding', "")
            right_hand = player_data.get('right_hand_holding', "")
            if left_hand and left_hand.strip():
                self.left_hand_item.setText(left_hand)
                self.left_hand_item.setProperty("equipped", True)
            else:
                self.left_hand_item.setText("(empty)")
                self.left_hand_item.setProperty("equipped", False)
            
            if right_hand and right_hand.strip():
                self.right_hand_item.setText(right_hand)
                self.right_hand_item.setProperty("equipped", True)
            else:
                self.right_hand_item.setText("(empty)")
                self.right_hand_item.setProperty("equipped", False)
            self.left_hand_item.style().unpolish(self.left_hand_item)
            self.left_hand_item.style().polish(self.left_hand_item)
            self.right_hand_item.style().unpolish(self.right_hand_item)
            self.right_hand_item.style().polish(self.right_hand_item)
    
    def refresh_character_sheet(self):
        self.load_character_data()

    def update_game_time(self):
        self._update_game_time()

    def _switch_to_tab_with_sound(self, tab_index):
        if self.main_app and hasattr(self.main_app, 'hover_message_sound') and self.main_app.hover_message_sound:
            try:
                self.main_app.hover_message_sound.play()
            except Exception as e:
                print(f"Error playing hover_message_sound in right splitter: {e}")
        self.stacked_widget.setCurrentIndex(tab_index)
        if tab_index == 0:
            self.load_character_data()
    
    def _switch_to_character_tab(self):
        self.stacked_widget.setCurrentIndex(0)
        self.load_character_data()
    
    def _update_game_time(self):
        if not hasattr(self, 'game_time_label') or not self.workflow_data_dir:
            return
        
        try:
            variables_file = os.path.join(self.workflow_data_dir, 'game', 'variables.json')
            print(f"[GAME TIME] Checking variables file: {variables_file}")
            
            if os.path.exists(variables_file):
                with open(variables_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        variables = json.loads(content)
                        print(f"[GAME TIME] Variables keys: {list(variables.keys())}")
                        game_time_str = variables.get('datetime') or variables.get('game_datetime')
                        print(f"[GAME TIME] Found time string: {game_time_str}")
                        
                        if game_time_str:
                            try:
                                game_time = datetime.fromisoformat(game_time_str)
                                time_str = game_time.strftime("%Y-%m-%d %H:%M:%S")
                                self.game_time_label.setText(f"Game Time: {time_str}")
                                print(f"[GAME TIME] Updated to: {time_str}")
                                return
                            except ValueError as e:
                                print(f"[GAME TIME] Error parsing time: {e}")
                                pass
                    else:
                        print(f"[GAME TIME] Variables file is empty")
            else:
                print(f"[GAME TIME] Variables file not found")
            
            self.game_time_label.setText("Game Time: --")
        except Exception as e:
            print(f"[GAME TIME] Error updating game time: {e}")
            self.game_time_label.setText("Game Time: --")
