import os
import json
import re
import shutil
import gc
import time
import random
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt

BASE_VARIABLES_FILE = "variables.json"

def sanitize_folder_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9\- ]', '', name).strip()
    return sanitized or 'Workflow'

def save_game_state(self):
    tab_data = self.get_current_tab_data()
    if not tab_data:
        QMessageBox.warning(self, "No Workflow Active", "Please select a workflow tab to save its state.")
        return
    tab_name = tab_data.get('name', f"Tab {self.current_tab_index + 1}")
    tab_dir = os.path.dirname(tab_data.get('tab_settings_file', ''))
    if not tab_dir or not os.path.isdir(tab_dir):
        QMessageBox.critical(self, "Error", f"Could not determine the data directory for workflow '{tab_name}'.")
        return
    game_dir = os.path.join(tab_dir, "game")
    saves_dir = os.path.join(tab_dir, "saves")
    if not os.path.isdir(game_dir):
        QMessageBox.warning(self, "Nothing to Save", f"The 'game' directory for workflow '{tab_name}' does not exist.")
        return
    dialog = QDialog(self)
    dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
    dialog.setWindowTitle("Save Game State")
    dialog.setModal(True)
    dialog.resize(400, 150)
    if hasattr(self, 'current_applied_theme') and self.current_applied_theme:
        theme_colors = self.current_applied_theme
        base_color = theme_colors.get("base_color", "#00FF66")
        bg_color = theme_colors.get("bg_color", "#252525")
        darker_bg = theme_colors.get("darker_bg", "#1A1A1A")
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {base_color};
                border: 2px solid {base_color};
                border-radius: 5px;
            }}
            QLabel {{
                color: {base_color};
                font-family: "Consolas";
            }}
            QLineEdit {{
                color: {base_color};
                background-color: {darker_bg};
                border: 1px solid {base_color};
                padding: 8px;
                border-radius: 3px;
                font: 11pt "Consolas";
                selection-background-color: {base_color};
                selection-color: {bg_color};
            }}
            QPushButton {{
                color: {base_color};
                background-color: {darker_bg};
                border: 1px solid {base_color};
                padding: 8px 16px;
                border-radius: 3px;
                font: 11pt "Consolas";
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {base_color};
                color: {bg_color};
            }}
            QPushButton:default {{
                border: 2px solid {base_color};
                font-weight: bold;
            }}
        """)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(10, 10, 10, 10)
    title_label = QLabel("Save Game State")
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
    layout.addWidget(title_label)
    desc_label = QLabel(f"Enter a name for this save (workflow: '{tab_name}'):")
    layout.addWidget(desc_label)
    save_name_input = QLineEdit()
    save_name_input.setPlaceholderText("Save name...")
    layout.addWidget(save_name_input)
    button_layout = QHBoxLayout()
    cancel_button = QPushButton("Cancel")
    ok_button = QPushButton("Save")
    ok_button.setDefault(True)
    button_layout.addStretch()
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(ok_button)
    layout.addLayout(button_layout)
    ok_button.setFocusPolicy(Qt.NoFocus)
    cancel_button.setFocusPolicy(Qt.NoFocus)
    result = [False, ""]
    def on_ok():
        result[0] = True
        result[1] = save_name_input.text()
        dialog.accept()
    def on_cancel():
        if hasattr(self, 'hover_message_sound') and self.hover_message_sound:
            try:
                self.hover_message_sound.play()
            except Exception as e:
                print(f"Error playing hover_message_sound: {e}")
        result[0] = False
        dialog.reject()
    ok_button.clicked.connect(on_ok)
    cancel_button.clicked.connect(on_cancel)
    save_name_input.returnPressed.connect(on_ok)
    if self:
        dialog.move(self.x() + (self.width() - dialog.width()) // 2,
                   self.y() + (self.height() - dialog.height()) // 2)
    dialog.exec_()
    ok = result[0]
    save_name = result[1]
    if not ok or not save_name.strip():
        return
    sanitized_save_name = sanitize_folder_name(save_name)
    save_dest_path = os.path.join(saves_dir, sanitized_save_name)
    os.makedirs(saves_dir, exist_ok=True)
    overwrite = False
    if os.path.exists(save_dest_path):
        reply = QMessageBox.question(
            self, "Overwrite Save?",
            f"A save named '{sanitized_save_name}' already exists. Overwrite?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            overwrite = True
        else:
            return
    try:
        if overwrite:
            shutil.rmtree(save_dest_path)
        if hasattr(self, 'timer_manager'):
            self.timer_manager.save_timer_state(tab_data)
        shutil.copytree(game_dir, save_dest_path)
        if hasattr(self, 'medium_click_sound') and self.medium_click_sound:
            try:
                self.medium_click_sound.play()
            except Exception as e:
                print(f"Error playing medium_click_sound after save: {e}")
    except OSError as e:
        QMessageBox.critical(self, "Save Error", f"Could not save game state.\nError: {e}")
    except Exception as e:
        QMessageBox.critical(self, "Save Error", f"An unexpected error occurred during save.\\nError: {e}")

def load_game_state(self):
    tab_data = self.get_current_tab_data()
    if not tab_data:
        QMessageBox.warning(self, "No Workflow Active", "Please select a workflow tab to load a state into.")
        return
    tab_name = tab_data.get('name', f"Tab {self.current_tab_index + 1}")
    tab_dir = os.path.dirname(tab_data.get('tab_settings_file', ''))
    if not tab_dir or not os.path.isdir(tab_dir):
        QMessageBox.critical(self, "Error", f"Could not determine the data directory for workflow '{tab_name}'.")
        return
    game_dir = os.path.join(tab_dir, "game")
    saves_dir = os.path.join(tab_dir, "saves")
    if not os.path.isdir(saves_dir):
        QMessageBox.information(self, "No Saves Found", f"No saves directory found for workflow '{tab_name}'.")
        return
    try:
        available_saves = [d for d in os.listdir(saves_dir) if os.path.isdir(os.path.join(saves_dir, d))]
    except OSError as e:
        QMessageBox.critical(self, "Load Error", f"Could not read available saves.\nError: {e}")
        return
    if not available_saves:
        QMessageBox.information(self, "No Saves Found", f"No saved states found in '{saves_dir}'.")
        return
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem
    from PyQt5.QtCore import Qt
    dialog = QDialog(self)
    dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
    dialog.setWindowTitle("Load Game State")
    dialog.setModal(True)
    dialog.resize(400, 300)
    if hasattr(self, 'current_applied_theme') and self.current_applied_theme:
        theme_colors = self.current_applied_theme
        base_color = theme_colors.get("base_color", "#00FF66")
        bg_color = theme_colors.get("bg_color", "#252525")
        darker_bg = theme_colors.get("darker_bg", "#1A1A1A")
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {base_color};
                border: 2px solid {base_color};
                border-radius: 5px;
            }}
            QLabel {{
                color: {base_color};
                font-family: "Consolas";
            }}
            QPushButton {{
                color: {base_color};
                background-color: {darker_bg};
                border: 1px solid {base_color};
                padding: 8px 16px;
                border-radius: 3px;
                font: 11pt "Consolas";
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {base_color};
                color: {bg_color};
            }}
            QPushButton:default {{
                border: 2px solid {base_color};
                font-weight: bold;
            }}
        """)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(10, 10, 10, 10)
    title_label = QLabel("Load Game State")
    title_label.setAlignment(Qt.AlignCenter)
    title_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
    layout.addWidget(title_label)
    desc_label = QLabel(f"Select a save state to load for '{tab_name}':")
    layout.addWidget(desc_label)
    saves_list = QListWidget()
    if hasattr(self, 'current_applied_theme') and self.current_applied_theme:
        theme_colors = self.current_applied_theme
        base_color = theme_colors.get("base_color", "#00FF66")
        bg_color = theme_colors.get("bg_color", "#252525")
        darker_bg = theme_colors.get("darker_bg", "#1A1A1A")
        from PyQt5.QtGui import QColor
        try:
            q_base_color = QColor(base_color)
            if q_base_color.isValid():
                highlight = q_base_color.lighter(130).name()
            else:
                highlight = "#00AA44"
        except:
            highlight = "#00AA44"
        
        saves_list.setStyleSheet(f"""
            QListWidget {{
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
            QListWidget::item:selected {{
                background-color: {highlight};
                color: white;
            }}
            QListWidget::item:hover {{
                background-color: {highlight};
                color: white;
            }}
        """)
    for save in available_saves:
        item = QListWidgetItem(save)
        saves_list.addItem(item)
    if available_saves:
        saves_list.setCurrentRow(0)
    saves_list.setFocusPolicy(Qt.NoFocus)
    def on_save_selected():
        if hasattr(self, 'hover_message_sound') and self.hover_message_sound:
            try:
                self.hover_message_sound.play()
            except Exception as e:
                print(f"Error playing hover_message_sound: {e}")
    saves_list.itemSelectionChanged.connect(on_save_selected)
    layout.addWidget(saves_list)
    button_layout = QHBoxLayout()
    cancel_button = QPushButton("Cancel")
    delete_button = QPushButton("Delete")
    load_button = QPushButton("Load")
    load_button.setDefault(True)
    cancel_button.setFocusPolicy(Qt.NoFocus)
    delete_button.setFocusPolicy(Qt.NoFocus)
    load_button.setFocusPolicy(Qt.NoFocus)
    button_layout.addStretch()
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(delete_button)
    button_layout.addWidget(load_button)
    layout.addLayout(button_layout)
    result = [False, ""]
    def on_load():
        current_item = saves_list.currentItem()
        if current_item:
            result[0] = True
            result[1] = current_item.text()
            dialog.accept()

    def on_cancel():
        if hasattr(self, 'hover_message_sound') and self.hover_message_sound:
            try:
                self.hover_message_sound.play()
            except Exception as e:
                print(f"Error playing hover_message_sound: {e}")
        result[0] = False
        dialog.reject()
    
    def on_delete():
        current_item = saves_list.currentItem()
        if not current_item:
            return
        save_name = current_item.text()
        save_path = os.path.join(saves_dir, save_name)
        try:
            import shutil
            if os.path.exists(save_path):
                shutil.rmtree(save_path)
            row = saves_list.row(current_item)
            saves_list.takeItem(row)
            if hasattr(self, 'hover_message_sound') and self.hover_message_sound:
                try:
                    self.hover_message_sound.play()
                except Exception as e:
                    print(f"Error playing hover_message_sound: {e}")
            if saves_list.count() == 0:
                result[0] = False
                dialog.reject()
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(dialog, "Delete Error", f"Could not delete save '{save_name}'.\nError: {e}")
    load_button.clicked.connect(on_load)
    cancel_button.clicked.connect(on_cancel)
    delete_button.clicked.connect(on_delete)
    saves_list.itemDoubleClicked.connect(on_load)
    if self:
        dialog.move(self.x() + (self.width() - dialog.width()) // 2,
                   self.y() + (self.height() - dialog.height()) // 2)
    dialog.exec_()
    ok = result[0]
    selected_save = result[1]
    if not ok or not selected_save:
        return
    save_src_path = os.path.join(saves_dir, selected_save)
    try:
        if tab_data:
            if 'memory' in tab_data and tab_data['memory']:
                old_memory = tab_data['memory']
                tab_data['memory'] = None
                del old_memory
            output_widget = tab_data.get('output')
            if output_widget:
                output_widget.clear_messages()
                timeout = 3000
                start_time = time.time()
                while output_widget.layout.count() > 0 and (time.time() - start_time) * 1000 < timeout:
                    QApplication.processEvents()
                    time.sleep(0.05)
                if output_widget.layout.count() > 0:
                    while output_widget.layout.count() > 0:
                        item = output_widget.layout.takeAt(0)
                        widget = item.widget()
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()
                    QApplication.processEvents()
            tab_data['context'] = []
            tab_data['_remembered_selected_message'] = None
            system_editor = tab_data.get('system_context_editor')
            if system_editor:
                system_editor.clear()
    except Exception as clear_err:
        QMessageBox.critical(self, "Load Error", f"Could not clear existing tab resources before loading.\nError: {clear_err}")
        return
    gc.collect()
    try:
        renamed_files = []
        if os.path.exists(game_dir):
            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                for item_name in os.listdir(game_dir):
                    item_path = os.path.join(game_dir, item_name)
                    if os.path.isfile(item_path):
                        base, ext = os.path.splitext(item_name)
                        new_name = f"{base}{ext}_old_{timestamp}"
                        new_path = os.path.join(game_dir, new_name)
                        try:
                            os.rename(item_path, new_path)
                            renamed_files.append(new_path)
                        except OSError as file_rename_err:
                            for old_file_path in renamed_files:
                                try:
                                    original_name = os.path.basename(old_file_path).replace(f"_old_{timestamp}", "")
                                    os.rename(old_file_path, os.path.join(game_dir, original_name))
                                except OSError:
                                    pass
                            QMessageBox.critical(self, "Load Error - File Rename Failed",
                                                f"Could not rename file: {item_name}\nReason: {file_rename_err}\n\nLoad operation cancelled.")
                            return
            except Exception as list_rename_err:
                QMessageBox.critical(self, "Load Error - File Access", f"Could not access files in {game_dir} for renaming.\nLoad cancelled.")
                return
        copied_files = []
        try:
            if not os.path.exists(game_dir):
                os.makedirs(game_dir)
            for item_name in os.listdir(save_src_path):
                source_item_path = os.path.join(save_src_path, item_name)
                dest_item_path = os.path.join(game_dir, item_name)
                if os.path.isfile(source_item_path):
                    shutil.copy2(source_item_path, dest_item_path)
                    copied_files.append(dest_item_path)
                elif os.path.isdir(source_item_path):
                    if os.path.exists(dest_item_path):
                        shutil.rmtree(dest_item_path)
                    shutil.copytree(source_item_path, dest_item_path)
            actors_dir = os.path.join(game_dir, 'actors')
            if os.path.exists(actors_dir):
                for actor_file in os.listdir(actors_dir):
                    if actor_file.endswith('.json'):
                        actor_path = os.path.join(actors_dir, actor_file)
                        try:
                            with open(actor_path, 'r', encoding='utf-8') as f:
                                actor_data = json.load(f)
                            notes = actor_data.get('npc_notes', '')
                            if notes:
                                note_count = len([line for line in notes.split('\n') if line.strip().startswith('[')])
                            else:
                                pass
                        except Exception:
                            pass
        except Exception as copy_err:
            for copied_file in copied_files:
                try: os.remove(copied_file) 
                except OSError: pass
            for old_file_path in renamed_files:
                try:
                    match = re.match(r"(.+?)_old_(\d{20})$", os.path.basename(old_file_path))
                    if match:
                        original_name = match.group(1)
                        os.rename(old_file_path, os.path.join(game_dir, original_name))
                except OSError: pass
            QMessageBox.critical(self, "Load Error - Copy Failed", f"Could not copy saved files.\nReason: {copy_err}\n\nLoad operation cancelled.")
            return
        self.load_conversation_for_tab(self.current_tab_index)
        self._load_variables(self.current_tab_index)
        system_context_content = self.get_system_context(self.current_tab_index)
        if tab_data and system_context_content is not None:
            system_editor = tab_data.get('system_context_editor')
            if system_editor and hasattr(system_editor, 'setPlainText'):
                system_editor.setPlainText(system_context_content)
            elif system_editor:
                if hasattr(system_editor, '_load_system_prompt_from_string'):
                    system_editor._load_system_prompt_from_string(system_context_content)
        if hasattr(self, 'timer_manager'):
            self.timer_manager.stop_all_timers()
        tab_data = self.get_current_tab_data()
        if tab_data and not tab_data.get('timer_rules_loaded', False):
            self._load_timer_rules_for_tab(self.current_tab_index)
            tab_data['timer_rules_loaded'] = True
        if tab_data and hasattr(self, 'timer_manager'):
            self.timer_manager.stop_timers_for_tab(tab_data)
        if tab_data and hasattr(self, 'timer_manager'):
            self.timer_manager.load_timer_state(tab_data)
        if hasattr(self, '_actor_name_to_file_cache'):
            self._actor_name_to_file_cache.clear()
        if hasattr(self, '_actor_name_to_actual_name'):
            self._actor_name_to_actual_name.clear()
        loaded_context_check = tab_data.get('context', [])
        top_splitter = tab_data.get('top_splitter')
        if loaded_context_check:
            if tab_data.get('input'):
                tab_data['input'].set_input_state('normal')
            if top_splitter:
                top_splitter.setVisible(True)
        elif not loaded_context_check:
            if top_splitter:
                top_splitter.setVisible(False)
            pass 
        if renamed_files:
            if not hasattr(self, 'files_to_delete_on_exit'):
                self.files_to_delete_on_exit = []
            self.files_to_delete_on_exit.extend(renamed_files)
            _cleanup_old_backup_files_in_directory(game_dir)
        right_splitter = tab_data.get('right_splitter')
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if right_splitter and workflow_data_dir:
            try:
                from core.utils import _get_player_current_setting_name
                current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                right_splitter.update_setting_name(current_setting_name, workflow_data_dir)
                right_splitter.load_character_data()
                right_splitter.update_game_time()
                print(f"Load: Updated right splitter with setting: {current_setting_name}")
            except Exception as e:
                print(f"Load: Error updating right splitter: {e}")
        if hasattr(self, 'medium_click_sound') and self.medium_click_sound:
            try:
                self.medium_click_sound.play()
            except Exception as e:
                print(f"Error playing medium_click_sound after load: {e}")
    except Exception as e:
        QMessageBox.critical(self, "Load Error", f"Could not complete load operation.\nError: {e}\n\nAttempting to restore clean state.")
        try:
            if os.path.exists(game_dir):
                shutil.rmtree(game_dir)
            self.load_conversation_for_tab(self.current_tab_index)
            self._load_variables(self.current_tab_index)
        except Exception as restore_err:
            QMessageBox.critical(self, "Restore Error", f"Failed to restore tab to empty state after load error.\nPlease restart the application.\nError: {restore_err}")

def load_system_context_from_file(self, tab_index):
    if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
        return
    tab_data = self.tabs_data[tab_index]
    system_context_editor = tab_data.get('system_context_editor')
    system_context_file = tab_data.get('system_context_file')
    if not system_context_editor:
        return
    if not system_context_file:
        system_context_editor.clear()
        return
    try:
        if os.path.exists(system_context_file):
            with open(system_context_file, 'r', encoding='utf-8') as f:
                content = f.read()
                system_context_editor.setText(content)
        else:
            system_context_editor.clear()
    except Exception as e:
        QMessageBox.warning(self, "System Context Load Error", f"Could not load system context from file.\n{e}")

def _get_player_character_name(workflow_data_dir):
    session_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    player_candidates = []
    if os.path.isdir(session_actors_dir):
        for filename in os.listdir(session_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(session_actors_dir, filename)
                data = _load_json_safely(file_path)
                if data.get('isPlayer') is True or data.get('variables', {}).get('is_player', False):
                    player_name = data.get('name')
                    if player_name:
                        player_candidates.append((filename, player_name))
    base_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if not player_candidates and os.path.isdir(base_actors_dir):
        for filename in os.listdir(base_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(base_actors_dir, filename)
                data = _load_json_safely(file_path)
                if data.get('isPlayer') is True or data.get('variables', {}).get('is_player', False):
                    player_name = data.get('name')
                    if player_name:
                        player_candidates.append((filename, player_name))
    for filename, player_name in player_candidates:
        if filename.lower() != 'player.json':
            return player_name
    for filename, player_name in player_candidates:
        if filename.lower() == 'player.json':
            return player_name
    return None

def _filter_conversation_history_by_visibility(conversation_history, target_character_name, workflow_data_dir, tab_data):
    if not conversation_history:
        return conversation_history
    actual_player_name = _get_player_character_name(workflow_data_dir)
    filtered_history = []
    for msg in conversation_history:
        if msg.get('role') == 'system':
            filtered_history.append(msg)
            continue
        metadata = msg.get('metadata', {})
        visibility_data = metadata.get('post_visibility')
        if not visibility_data:
            filtered_history.append(msg)
            continue
        mode = visibility_data.get('mode', 'Visible Only To')
        condition_type = visibility_data.get('condition_type', 'Name Match')
        should_show = _evaluate_post_visibility(
            mode, condition_type, visibility_data, 
            target_character_name, actual_player_name, workflow_data_dir, tab_data
        )
        if should_show:
            filtered_history.append(msg)
    return filtered_history

def _evaluate_post_visibility(mode, condition_type, visibility_data, target_character_name, actual_player_name, workflow_data_dir, tab_data):
    is_inclusionary = (mode == "Visible Only To")
    if condition_type == "Name Match":
        actor_names = visibility_data.get('actor_names', [])
        resolved_names = []
        for name in actor_names:
            name_lower = name.strip().lower()
            if name_lower == "player":
                if actual_player_name:
                    resolved_names.append(actual_player_name)
                else:
                    resolved_names.append("Player")
            elif name_lower == "narrator":
                resolved_names.append("Narrator")
            else:
                resolved_names.append(name.strip())
        target_in_list = target_character_name in resolved_names
        if is_inclusionary:
            result = target_in_list
        else:
            result = not target_in_list
        return result
    elif condition_type == "Variable":
        variable_conditions = visibility_data.get('variable_conditions', [])
        if not variable_conditions:
            return True if is_inclusionary else False
        conditions_met = []
        for cond in variable_conditions:
            condition_met = _evaluate_variable_condition(
                cond, target_character_name, actual_player_name, workflow_data_dir, tab_data
            )
            conditions_met.append(condition_met)
        all_conditions_met = all(conditions_met)
        if is_inclusionary:
            return all_conditions_met
        else:
            return not all_conditions_met
    return True

def _evaluate_variable_condition(condition, target_character_name, actual_player_name, workflow_data_dir, tab_data):
    try:
        if isinstance(condition, dict):
            var_name = condition.get('var_name')
            operator = condition.get('operator')
            value = condition.get('value')
            var_scope = condition.get('variable_scope', 'Global')
            var_value = None
            if var_scope == 'Global':
                if tab_data and 'variables' in tab_data:
                    global_vars = tab_data['variables']
                    if var_name in global_vars:
                        var_value = global_vars[var_name]
            elif var_scope == 'Character':
                if target_character_name and workflow_data_dir:
                    from core.utils import _find_actor_file_path, _load_json_safely
                    class DummySelf:
                        pass
                    dummy_self = DummySelf()
                    actor_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, target_character_name)
                    if actor_file_path:
                        actor_data = _load_json_safely(actor_file_path)
                        if actor_data and 'variables' in actor_data:
                            char_vars = actor_data['variables']
                            if var_name in char_vars:
                                var_value = char_vars[var_name]
            elif var_scope == 'Player':
                if actual_player_name and workflow_data_dir:
                    from core.utils import _find_actor_file_path, _load_json_safely
                    class DummySelf:
                        pass
                    dummy_self = DummySelf()
                    player_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, actual_player_name)
                    if player_file_path:
                        player_data = _load_json_safely(player_file_path)
                        if player_data and 'variables' in player_data:
                            player_vars = player_data['variables']
                            if var_name in player_vars:
                                var_value = player_vars[var_name]
            elif var_scope == 'Setting':
                if workflow_data_dir:
                    from core.utils import _get_player_current_setting_name, _find_setting_file_prioritizing_game_dir, _load_json_safely
                    current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                    if current_setting_name and current_setting_name != "Unknown Setting":
                        class DummySelf:
                            pass
                        dummy_self = DummySelf()
                        setting_file_path, _ = _find_setting_file_prioritizing_game_dir(dummy_self, workflow_data_dir, current_setting_name)
                        if setting_file_path:
                            setting_data = _load_json_safely(setting_file_path)
                            if setting_data and 'variables' in setting_data:
                                setting_vars = setting_data['variables']
                                if var_name in setting_vars:
                                    var_value = setting_vars[var_name]
            if operator == "==":
                return str(var_value) == str(value)
            elif operator == "!=":
                return str(var_value) != str(value)
            elif operator == ">":
                try:
                    return float(var_value) > float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == "<":
                try:
                    return float(var_value) < float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == ">=":
                try:
                    return float(var_value) >= float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == "<=":
                try:
                    return float(var_value) <= float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == "contains":
                return str(value) in str(var_value)
            elif operator == "not contains":
                return str(value) not in str(var_value)
            elif operator == "exists":
                return var_value is not None and var_value != ""
            elif operator == "not exists":
                return var_value is None or var_value == ""
            return False
        else:
            parts = condition.strip().split()
            if len(parts) < 2:
                return False
            var_name = parts[0]
            operator = parts[1]
            value = " ".join(parts[2:]) if len(parts) > 2 else None
            if operator in ["exists", "not exists"]:
                value = None
            var_value = _get_variable_value_for_visibility(var_name, target_character_name, actual_player_name, workflow_data_dir, tab_data)
            if operator == "==":
                return str(var_value) == str(value)
            elif operator == "!=":
                return str(var_value) != str(value)
            elif operator == ">":
                try:
                    return float(var_value) > float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == "<":
                try:
                    return float(var_value) < float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == ">=":
                try:
                    return float(var_value) >= float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == "<=":
                try:
                    return float(var_value) <= float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == "contains":
                return str(value) in str(var_value)
            elif operator == "not contains":
                return str(value) not in str(var_value)
            elif operator == "exists":
                return var_value is not None and var_value != ""
            elif operator == "not exists":
                return var_value is None or var_value == ""
            return False
    except Exception as e:
        print(f"Error evaluating variable condition '{condition}': {e}")
        return False

def _get_variable_value_for_visibility(var_name, target_character_name, actual_player_name, workflow_data_dir, tab_data):
    if tab_data and 'variables' in tab_data:
        global_vars = tab_data['variables']
        if var_name in global_vars:
            return global_vars[var_name]
    if target_character_name and workflow_data_dir:
        try:
            from core.utils import _find_actor_file_path, _load_json_safely
            class DummySelf:
                pass
            dummy_self = DummySelf()
            actor_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, target_character_name)
            if actor_file_path:
                actor_data = _load_json_safely(actor_file_path)
                if actor_data and 'variables' in actor_data:
                    char_vars = actor_data['variables']
                    if var_name in char_vars:
                        return char_vars[var_name]
        except Exception:
            pass
    if actual_player_name and workflow_data_dir:
        try:
            from core.utils import _find_actor_file_path, _load_json_safely
            class DummySelf:
                pass
            dummy_self = DummySelf()
            player_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, actual_player_name)
            if player_file_path:
                player_data = _load_json_safely(player_file_path)
                if player_data and 'variables' in player_data:
                    player_vars = player_data['variables']
                    if var_name in player_vars:
                        return player_vars[var_name]
        except Exception:
            pass
    if workflow_data_dir:
        try:
            from core.utils import _get_player_current_setting_name, _find_setting_file_prioritizing_game_dir, _load_json_safely
            current_setting_name = _get_player_current_setting_name(workflow_data_dir)
            if current_setting_name and current_setting_name != "Unknown Setting":
                class DummySelf:
                    pass
                dummy_self = DummySelf()
                setting_file_path, _ = _find_setting_file_prioritizing_game_dir(dummy_self, workflow_data_dir, current_setting_name)
                if setting_file_path:
                    setting_data = _load_json_safely(setting_file_path)
                    if setting_data and 'variables' in setting_data:
                        setting_vars = setting_data['variables']
                        if var_name in setting_vars:
                            return setting_vars[var_name]
        except Exception:
            pass
    return None

def _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, target_setting_name):
    if not target_setting_name:
        return None, None
    session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
    if os.path.isdir(session_settings_dir):
        for root, dirs, files in os.walk(session_settings_dir):
            dirs[:] = [d for d in dirs if d.lower() != 'saves']
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    file_path = os.path.join(root, filename)
                    setting_data = _load_json_safely(file_path)
                    if setting_data.get('name') == target_setting_name:
                        return file_path, 'game'
    base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    if os.path.isdir(base_settings_dir):
        for root, dirs, files in os.walk(base_settings_dir):
            dirs[:] = [d for d in dirs if d.lower() != 'saves']
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    file_path = os.path.join(root, filename)
                    setting_data = _load_json_safely(file_path)
                    if setting_data.get('name') == target_setting_name:
                        return file_path, 'resources'
    return None, None

def _find_actor_file_path(self, workflow_data_dir, actor_name):
    if not hasattr(self, '_actor_name_to_file_cache'):
        self._actor_name_to_file_cache = {}
        self._actor_name_to_actual_name = {}
        return _rebuild_actor_cache(self, workflow_data_dir, actor_name)
    normalized_name = actor_name.strip().lower().replace(' ', '_')
    if normalized_name in self._actor_name_to_file_cache:
        file_path = self._actor_name_to_file_cache[normalized_name]
        return file_path
    return _rebuild_actor_cache(self, workflow_data_dir, actor_name)

def _rebuild_actor_cache(self, workflow_data_dir, actor_name=None):
    self._actor_name_to_file_cache = {}
    self._actor_name_to_actual_name = {}
    found_file = None
    if actor_name is not None and not isinstance(actor_name, str):
        return None
    session_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    if os.path.isdir(session_actors_dir):
        for filename in os.listdir(session_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(session_actors_dir, filename)
                data = _load_json_safely(file_path)
                if data and 'name' in data:
                    actual_name = data.get('name')
                    filename_base = os.path.splitext(filename)[0]
                    normalized_actual = actual_name.strip().lower().replace(' ', '_')
                    normalized_filename = filename_base.strip().lower()
                    self._actor_name_to_file_cache[normalized_actual] = file_path
                    self._actor_name_to_file_cache[normalized_filename] = file_path
                    self._actor_name_to_actual_name[normalized_actual] = actual_name
                    self._actor_name_to_actual_name[normalized_filename] = actual_name
                    if actor_name and (actor_name == actual_name or 
                                        actor_name.strip().lower().replace(' ', '_') == normalized_actual or
                                        actor_name.strip().lower() == normalized_filename):
                        found_file = file_path
    base_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if os.path.isdir(base_actors_dir):
        for filename in os.listdir(base_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(base_actors_dir, filename)
                data = _load_json_safely(file_path)
                if data and 'name' in data:
                    actual_name = data.get('name')
                    filename_base = os.path.splitext(filename)[0]
                    normalized_actual = actual_name.strip().lower().replace(' ', '_')
                    normalized_filename = filename_base.strip().lower()
                    if normalized_actual not in self._actor_name_to_file_cache:
                        self._actor_name_to_file_cache[normalized_actual] = file_path
                        self._actor_name_to_actual_name[normalized_actual] = actual_name
                    if normalized_filename not in self._actor_name_to_file_cache:
                        self._actor_name_to_file_cache[normalized_filename] = file_path
                        self._actor_name_to_actual_name[normalized_filename] = actual_name
                    if not found_file and actor_name and (actor_name == actual_name or 
                                                        actor_name.strip().lower().replace(' ', '_') == normalized_actual or
                                                        actor_name.strip().lower() == normalized_filename):
                        found_file = file_path
    return found_file

def _load_json_safely(file_path):
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
        return {}
    except Exception as e:
        return {}

def _save_json_safely(file_path, data):
    if not file_path:
        return False
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, OSError) as e:
        return False
    except Exception as e:
        return False

def _find_player_character_file(workflow_data_dir):
    actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if not os.path.isdir(actors_dir):
        return None, None
    for filename in os.listdir(actors_dir):
        if filename.lower().endswith('.json'):
            file_path = os.path.join(actors_dir, filename)
            data = _load_json_safely(file_path)
            if data and data.get('isPlayer') is True:
                player_name = data.get('name')
                if player_name:
                    return file_path, player_name
    return None, None

def _scan_settings_for_player(settings_base_dir, player_name):
    if not os.path.isdir(settings_base_dir):
        return False
    for root, dirs, files in os.walk(settings_base_dir):
        dirs[:] = [d for d in dirs if d.lower() != 'saves'] 
        for filename in files:
            if filename.lower().endswith('_setting.json'):
                file_path = os.path.join(root, filename)
                setting_data = _load_json_safely(file_path)
                characters_list = setting_data.get('characters')
                if isinstance(characters_list, list) and player_name in characters_list:
                    return True
    return False

def _find_setting_file_by_name(settings_base_dir, target_setting_name):
    if not os.path.isdir(settings_base_dir) or not target_setting_name:
        return None
    for root, dirs, files in os.walk(settings_base_dir):
        dirs[:] = [d for d in dirs if d.lower() != 'saves']
        for filename in files:
            if filename.lower().endswith('_setting.json'):
                file_path = os.path.join(root, filename)
                setting_data = _load_json_safely(file_path)
                if setting_data.get('name') == target_setting_name:
                    return file_path
    return None

def ensure_player_in_origin_setting(workflow_data_dir):
    player_file_path, player_name = _find_player_character_file(workflow_data_dir)
    if not player_name:
        return
    settings_base_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    if _scan_settings_for_player(settings_base_dir, player_name):
        return
    variables_file = os.path.join(workflow_data_dir, 'game', BASE_VARIABLES_FILE)
    if not os.path.exists(variables_file):
        return
    variables_data = _load_json_safely(variables_file)
    origin_setting_name = variables_data.get('origin')
    if not origin_setting_name:
        return
    origin_setting_file = _find_setting_file_by_name(settings_base_dir, origin_setting_name)
    if not origin_setting_file:
        return
    origin_data = _load_json_safely(origin_setting_file)
    if origin_data is None:
        return
    if 'characters' not in origin_data or not isinstance(origin_data.get('characters'), list):
        origin_data['characters'] = []
    if player_name not in origin_data['characters']:
        origin_data['characters'].append(player_name)
        _save_json_safely(origin_setting_file, origin_data)

def _get_player_current_setting_name(workflow_data_dir):
    player_file_path, player_name = _find_player_character_file(workflow_data_dir)
    if not player_name:
        return "Unknown Setting"
    session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
    if os.path.isdir(session_settings_dir):
        found_settings = []
        for root, dirs, files in os.walk(session_settings_dir):
            dirs[:] = [d for d in dirs if d.lower() != 'saves']
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    file_path = os.path.join(root, filename)
                    setting_data = _load_json_safely(file_path)
                    if setting_data:
                        characters_list = setting_data.get('characters')
                        setting_name = setting_data.get('name', os.path.basename(root))
                        found_settings.append({
                            'path': file_path,
                            'name': setting_name,
                            'characters': characters_list,
                            'has_player': isinstance(characters_list, list) and player_name in characters_list
                        })
        for setting in found_settings:
            if setting['has_player']:
                return setting['name']
    settings_base_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    if not os.path.isdir(settings_base_dir):
        variables_file = os.path.join(workflow_data_dir, 'game', BASE_VARIABLES_FILE)
        variables_data = _load_json_safely(variables_file)
        origin_setting_name = variables_data.get('origin', "Unknown Setting") if variables_data else "Unknown Setting"
        return origin_setting_name
    found_base_settings = []
    for root, dirs, files in os.walk(settings_base_dir):
        dirs[:] = [d for d in dirs if d.lower() != 'saves']
        for filename in files:
            if filename.lower().endswith('_setting.json'):
                file_path = os.path.join(root, filename)
                setting_data = _load_json_safely(file_path)
                if setting_data:
                    characters_list = setting_data.get('characters')
                    setting_name = setting_data.get('name', os.path.basename(root))
                    found_base_settings.append({
                        'path': file_path,
                        'name': setting_name,
                        'characters': characters_list,
                        'has_player': isinstance(characters_list, list) and player_name in characters_list
                    })
    for setting in found_base_settings:
        if setting['has_player']:
            return setting['name']
    variables_file = os.path.join(workflow_data_dir, 'game', BASE_VARIABLES_FILE)
    variables_data = _load_json_safely(variables_file)
    origin_setting_name = variables_data.get('origin', "Unknown Setting") if variables_data else "Unknown Setting"
    return origin_setting_name
def update_top_splitter_location_text(tab_data):
    if not tab_data or not isinstance(tab_data, dict):
        return
    top_splitter = tab_data.get('top_splitter')
    workflow_data_dir = tab_data.get('workflow_data_dir')
    if not top_splitter or not workflow_data_dir:
        return
    if not hasattr(top_splitter, 'set_location_text'):
        return
    current_setting_name = _get_player_current_setting_name(workflow_data_dir)
    top_splitter.set_location_text(current_setting_name)

def reset_player_to_origin(workflow_data_dir):
    player_file_path, player_name = _find_player_character_file(workflow_data_dir)
    if not player_name:
        return False
    variables_file = os.path.join(workflow_data_dir, 'game', BASE_VARIABLES_FILE)
    if not os.path.exists(variables_file):
        return False
    variables_data = _load_json_safely(variables_file)
    origin_setting_name = variables_data.get('origin')
    if not origin_setting_name:
        return False
    settings_base_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    origin_setting_file = _find_setting_file_by_name(settings_base_dir, origin_setting_name)
    if not origin_setting_file:
        return False
    player_removed = False
    for root, dirs, files in os.walk(settings_base_dir):
        dirs[:] = [d for d in dirs if d.lower() != 'saves']
        for filename in files:
            if filename.lower().endswith('_setting.json'):
                file_path = os.path.join(root, filename)
                setting_data = _load_json_safely(file_path)
                if not isinstance(setting_data, dict) or 'characters' not in setting_data:
                    continue
                characters_list = setting_data.get('characters', [])
                if not isinstance(characters_list, list):
                    setting_data['characters'] = []
                    characters_list = []
                if player_name in characters_list:
                    setting_name = setting_data.get('name', os.path.basename(root))
                    if file_path == origin_setting_file:
                        return False
                    characters_list.remove(player_name)
                    setting_data['characters'] = characters_list
                    if _save_json_safely(file_path, setting_data):
                        player_removed = True
    origin_data = _load_json_safely(origin_setting_file)
    if not isinstance(origin_data, dict):
        return False
    if 'characters' not in origin_data or not isinstance(origin_data.get('characters'), list):
        origin_data['characters'] = []
    if player_name not in origin_data['characters']:
        origin_data['characters'].append(player_name)
        if _save_json_safely(origin_setting_file, origin_data):
            return True
        else:
            return False
    else:
        if player_removed:
            return True
        else:
            return False

def _get_available_actors(workflow_data_dir):
    actors = {}
    session_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    if os.path.isdir(session_actors_dir):
        for filename in os.listdir(session_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(session_actors_dir, filename)
                actor_data = _load_json_safely(file_path)
                actor_name = actor_data.get('name')
                if actor_name:
                    actors[actor_name] = 'session'
    base_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if os.path.isdir(base_actors_dir):
        for filename in os.listdir(base_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(base_actors_dir, filename)
                actor_data = _load_json_safely(file_path)
                actor_name = actor_data.get('name')
                if actor_name and actor_name not in actors:
                    actors[actor_name] = 'base'
    return sorted(list(actors.keys()))

def _get_available_settings(workflow_data_dir):
    settings = {}
    session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
    if os.path.isdir(session_settings_dir):
        for root, dirs, files in os.walk(session_settings_dir):
             dirs[:] = [d for d in dirs if d.lower() != 'saves']
             for filename in files:
                 if filename.lower().endswith('_setting.json'):
                     file_path = os.path.join(root, filename)
                     setting_data = _load_json_safely(file_path)
                     setting_name = setting_data.get('name')
                     if setting_name:
                         settings[setting_name] = 'session'
    base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    if os.path.isdir(base_settings_dir):
        for root, dirs, files in os.walk(base_settings_dir):
             dirs[:] = [d for d in dirs if d.lower() != 'saves']
             for filename in files:
                 if filename.lower().endswith('_setting.json'):
                     file_path = os.path.join(root, filename)
                     setting_data = _load_json_safely(file_path)
                     setting_name = setting_data.get('name')
                     if setting_name and setting_name not in settings:
                         settings[setting_name] = 'base'
    variables_file = os.path.join(workflow_data_dir, 'game', BASE_VARIABLES_FILE)
    variables_data = _load_json_safely(variables_file)
    origin_setting_name = variables_data.get('origin')
    if origin_setting_name and origin_setting_name not in settings:
        settings[origin_setting_name] = 'origin_fallback'
    return sorted(list(settings.keys()))

def is_valid_widget(widget):
    if not widget:
        return False
    try:
        widget.objectName()
        return True
    except (RuntimeError, Exception):
        return False

def sanitize_folder_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9\- ]', '', name).strip()
    return sanitized or 'Workflow'

def get_unique_tab_dir(base_data_dir, base_name):
    sanitized = sanitize_folder_name(base_name)
    candidate = sanitized
    i = 1
    while os.path.exists(os.path.join(base_data_dir, candidate)):
        candidate = f"{sanitized}_{i}"
        i += 1
    return os.path.join(base_data_dir, candidate)

def reload_actors_for_setting(workflow_data_dir, setting_name):
    settings_base_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    game_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
    setting_file = _find_setting_file_by_name(game_settings_dir, setting_name)
    if not setting_file:
        setting_file = _find_setting_file_by_name(settings_base_dir, setting_name)
    if not setting_file:
        return
    setting_data = _load_json_safely(setting_file)
    actor_names = setting_data.get('characters', [])
    if not isinstance(actor_names, list):
        actor_names = []
    game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    resource_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    for actor_name in actor_names:
        found = False
        target_norm = re.sub(r'[_\s]', '', actor_name).lower()
        if os.path.isdir(game_actors_dir):
            for fname in os.listdir(game_actors_dir):
                if not fname.lower().endswith('.json'):
                    continue
                file_path = os.path.join(game_actors_dir, fname)
                data = _load_json_safely(file_path)
                file_name_field = data.get('name', '')
                file_norm = re.sub(r'[_\s]', '', file_name_field).lower()
                if file_norm == target_norm:
                    found = True
                    break
        if not found and os.path.isdir(resource_actors_dir):
            for fname in os.listdir(resource_actors_dir):
                if not fname.lower().endswith('.json'):
                    continue
                file_path = os.path.join(resource_actors_dir, fname)
                data = _load_json_safely(file_path)
                file_name_field = data.get('name', '')
                file_norm = re.sub(r'[_\s]', '', file_name_field).lower()
                if file_norm == target_norm:
                    found = True
                    break
                    
def _get_or_create_actor_data(self, workflow_data_dir, actor_name):
    if not workflow_data_dir or not actor_name:
        return None, None
    def normalize_name(name):
        return name.strip().lower().replace(' ', '_')
    normalized_actor_name = normalize_name(actor_name)
    game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    resources_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if os.path.isdir(game_actors_dir):
        for filename in os.listdir(game_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(game_actors_dir, filename)
                data = _load_json_safely(file_path)
                internal_name = data.get('name', '')
                normalized_internal_name = normalize_name(internal_name)
                normalized_filename = normalize_name(filename[:-5]) # remove .json
                if normalized_internal_name == normalized_actor_name or normalized_filename == normalized_actor_name:
                    return data, file_path
    if os.path.isdir(resources_actors_dir):
        for filename in os.listdir(resources_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(resources_actors_dir, filename)
                data = _load_json_safely(file_path)
                internal_name = data.get('name', '')
                normalized_internal_name = normalize_name(internal_name)
                normalized_filename = normalize_name(filename[:-5])
                if normalized_internal_name == normalized_actor_name or normalized_filename == normalized_actor_name:
                    target_game_actor_path = os.path.join(game_actors_dir, filename)
                    try:
                        os.makedirs(game_actors_dir, exist_ok=True)
                        if not os.path.exists(target_game_actor_path):
                            _save_json_safely(target_game_actor_path, data)
                        return data, target_game_actor_path
                    except Exception as e:
                        return None, None
    return None, None

def _prepare_condition_text(self, condition_text, player_name, current_char_name=None, tab_data=None, scope='user_message', current_user_msg=None, prev_assistant_msg=None):
    if not condition_text:
        return ''
    modified_text = condition_text
    target_msg = ''
    if scope == 'full_conversation' and tab_data and 'context' in tab_data:
        current_scene = tab_data.get('scene_number', 1)
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if current_char_name and workflow_data_dir:
            from core.utils import _filter_conversation_history_by_visibility
            full_context = tab_data['context']
            filtered_context = _filter_conversation_history_by_visibility(
                full_context, current_char_name, workflow_data_dir, tab_data
            )
            current_scene_messages = [msg for msg in filtered_context 
                                     if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene]
        else:
            current_scene_messages = [msg for msg in tab_data['context'] 
                                     if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene]
        formatted_history = [f"{msg.get('role','unknown').capitalize()}: {msg.get('content','')}"
                            for msg in current_scene_messages]
        target_msg = "\n".join(formatted_history)
    elif scope == 'last_exchange':
        target_msg = f"Assistant: {prev_assistant_msg}\nUser: {current_user_msg}"
    elif scope == 'llm_reply':
        target_msg = prev_assistant_msg
    elif scope == 'user_message':
        target_msg = current_user_msg
    elif scope == 'convo_llm_reply':
        current_scene = tab_data.get('scene_number', 1)
        current_scene_messages = [msg for msg in tab_data.get('context', [])
                                 if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene]
        formatted_history = [f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')}"
                            for msg in current_scene_messages]
        conversation_part = "\n".join(formatted_history)
        target_msg = f"{conversation_part}\n\nLatest LLM Response: {prev_assistant_msg}"
    if player_name:
        modified_text = re.sub(r'\(Player\)', player_name, modified_text, flags=re.IGNORECASE)
    else:
        pass 
    if current_char_name:
        modified_text = re.sub(r'\(Character\)', current_char_name, modified_text, flags=re.IGNORECASE)
    if target_msg:
        final_text = f"Text to analyze:\n---\n{target_msg}\n---\n\n{modified_text}"
        return final_text
    else:
        return modified_text

def _parse_filter_string(filter_str):
    filters = []
    if not filter_str:
        return filters
    pairs = filter_str.split(',')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            filters.append((key.strip(), value.strip()))
        else:
            pass
    return filters

def _get_random_filtered_entity_name(workflow_data_dir, entity_type, filter_str):
    if not workflow_data_dir:
        return None
    entity_dir_name = entity_type
    entity_path = os.path.join(workflow_data_dir, entity_dir_name)
    if not os.path.isdir(entity_path):
        return None
    parsed_filters = _parse_filter_string(filter_str)
    matching_entity_names = []
    for filename in os.listdir(entity_path):
        if filename.endswith(".json"):
            file_path = os.path.join(entity_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                entity_name = data.get("name")
                if not entity_name:
                    continue
                all_filters_match = True
                if parsed_filters:
                    for key, expected_value in parsed_filters:
                        actual_value = data.get(key)
                        if actual_value is None and "variables" in data and isinstance(data["variables"], dict):
                            actual_value = data["variables"].get(key)
                        if actual_value is None and "custom_vars" in data and isinstance(data["custom_vars"], dict):
                            actual_value = data["custom_vars"].get(key)
                        if actual_value is not None:
                            actual_value_str = str(actual_value).lower()
                            expected_value_str = str(expected_value).lower()
                            if expected_value_str in ["true", "false"]:
                                if actual_value_str != expected_value_str:
                                    all_filters_match = False
                                    break
                            elif actual_value_str != expected_value_str:
                                all_filters_match = False
                                break
                        else:
                            all_filters_match = False
                            break
                if all_filters_match:
                    matching_entity_names.append(entity_name)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                pass
    if not matching_entity_names:
        return None
    chosen_name = random.choice(matching_entity_names)
    return chosen_name

def _cleanup_old_backup_files_in_directory(directory):
    try:
        import re
        from datetime import datetime, timedelta
        if not os.path.exists(directory):
            return
        cutoff_time = datetime.now() - timedelta(minutes=10)
        files_cleaned = 0
        for filename in os.listdir(directory):
            match = re.search(r'_old_(\d{20})$', filename)
            if match:
                timestamp_str = match.group(1)
                try:
                    file_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S%f')
                    if file_time < cutoff_time:
                        file_path = os.path.join(directory, filename)
                        os.remove(file_path)
                        files_cleaned += 1
                except (ValueError, OSError):
                    continue
        if files_cleaned > 0:
            print(f"Cleaned up {files_cleaned} old backup files in {directory}")
    except Exception as e:
        print(f"Error during directory backup cleanup: {e}")
