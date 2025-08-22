import os
import re
import math
from PyQt5.QtWidgets import QLabel

def sanitize_path_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\\. ]', '', name).strip()
    sanitized = sanitized.replace(' ', '_').lower()
    return sanitized or 'untitled'

def select_item(self, map_type, item_type, item_index_or_name):
    world_loc_dropdown = getattr(self, 'world_location_dropdown', None)
    world_set_dropdown = getattr(self, 'world_setting_dropdown', None)
    self.clear_selection(trigger_update=False)
    if map_type == 'world':
        self._world_selected_item_type = item_type
        if item_type == 'region':
            self._world_selected_region_name = item_index_or_name
            self._world_selected_item_index = -1
        else:
            self._world_selected_item_index = item_index_or_name
            self._world_selected_region_name = None
        if hasattr(self, 'world_map_label') and self.world_map_label:
            if item_type == 'region':
                self.world_map_label._world_selected_item_type = item_type
                self.world_map_label._world_selected_item_index = -1
            else:
                self.world_map_label._world_selected_item_type = item_type
                self.world_map_label._world_selected_item_index = item_index_or_name
        self._location_selected_item_type = None
        self._location_selected_item_index = -1
        world_loc_label = self.world_location_label
        world_loc_dropdown = self.world_location_dropdown
        world_unlink_btn = self.world_unlink_location_btn
        world_set_label = None
        world_set_dropdown = self.world_setting_dropdown
        world_unlink_setting_btn = getattr(self, 'world_unlink_setting_btn', None)
        for label_widget in self.world_tab.findChildren(QLabel):
            if label_widget.text() == "Linked Settings:":
                world_set_label = label_widget
                break
        if world_loc_label: 
            world_loc_label.setVisible(False)
        if world_loc_dropdown: 
            world_loc_dropdown.setVisible(False)
        if world_unlink_btn: 
            world_unlink_btn.setVisible(False)
        if world_set_label: 
            world_set_label.setVisible(False)
        if world_set_dropdown: 
            world_set_dropdown.setVisible(False)
        if world_unlink_setting_btn: 
            world_unlink_setting_btn.setVisible(False)
        if item_type == 'dot' and isinstance(item_index_or_name, int) and 0 <= item_index_or_name < len(self._world_dots):
            self._world_selected_item_type = 'dot'
            self._world_selected_item_index = item_index_or_name
            dot_data = self._world_dots[item_index_or_name]
            x, y = dot_data[0], dot_data[1]
            dot_type = dot_data[3] if len(dot_data) >= 4 else 'unknown'
            linked_name = dot_data[4] if len(dot_data) >= 5 else None
            region_name = dot_data[5] if len(dot_data) >= 6 else None
            world_display_name = self.current_world_name.replace("_", " ").title() if self.current_world_name else "World Map"
            title_parts = [world_display_name]
            if linked_name:
                if dot_type == 'small':
                    fresh_setting_name = linked_name
                    setting_region = None
                    if self.workflow_data_dir and self.current_world_name:
                        search_dirs = [
                            os.path.join(self.workflow_data_dir, 'game', 'settings', self.current_world_name),
                            os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
                        ]
                        setting_json_filename = f"{sanitize_path_name(linked_name)}_setting.json"
                        found_setting = False
                        for world_dir in search_dirs:
                            if not os.path.isdir(world_dir):
                                continue
                            world_level_setting_path = os.path.join(world_dir, setting_json_filename)
                            if os.path.isfile(world_level_setting_path):
                                setting_data = self._load_json(world_level_setting_path)
                                if setting_data and 'name' in setting_data:
                                    fresh_setting_name = setting_data['name']
                                    setting_region = setting_data.get('region', None)
                                    found_setting = True
                                    break
                        if not found_setting:
                            for world_dir in search_dirs:
                                if not os.path.isdir(world_dir) or found_setting:
                                    continue
                                for region_folder in os.listdir(world_dir):
                                    region_path = os.path.join(world_dir, region_folder)
                                    if not os.path.isdir(region_path):
                                        continue
                                    region_level_setting_path = os.path.join(region_path, setting_json_filename)
                                    if os.path.isfile(region_level_setting_path):
                                        setting_data = self._load_json(region_level_setting_path)
                                        if setting_data and 'name' in setting_data:
                                            fresh_setting_name = setting_data['name']
                                            setting_region = setting_data.get('region', region_folder)
                                            found_setting = True
                                            break
                                    for location_folder in os.listdir(region_path):
                                        location_path = os.path.join(region_path, location_folder)
                                        if not os.path.isdir(location_path):
                                            continue
                                        setting_path = os.path.join(location_path, setting_json_filename)
                                        if os.path.isfile(setting_path):
                                            setting_data = self._load_json(setting_path)
                                            if setting_data and 'name' in setting_data:
                                                fresh_setting_name = setting_data['name']
                                                setting_region = setting_data.get('region', region_folder)
                                                found_setting = True
                                                break
                                    if found_setting:
                                        break
                    title_parts.append(f"Setting: {fresh_setting_name}")
                    if setting_region and setting_region != region_name:
                        title_parts.append(f"in {self._format_region_name_for_display(setting_region)}")
                    elif region_name:
                        title_parts.append(f"in {self._format_region_name_for_display(region_name)}")
                else:
                    title_parts.append(f"Linked to: {linked_name}")
            else:
                type_display_map = {'big': 'Large Location', 'medium': 'Medium Location', 'small': 'Setting'}
                type_display = type_display_map.get(dot_type, dot_type.capitalize())
                title_parts.append(f"{type_display} Dot ({x:.2f}, {y:.2f})")
                if region_name and dot_type != 'small':
                    title_parts.append(f"in {self._format_region_name_for_display(region_name)}")
            self.world_map_title_label.setText(" - ".join(filter(None, title_parts)))
            if dot_type == 'big' or dot_type == 'medium':
                if linked_name:
                    if world_loc_label: 
                        world_loc_label.setVisible(True)
                        world_loc_label.setEnabled(True)
                        world_loc_label.setStyleSheet("font-size: 8pt; font-weight: normal;")
                    if world_unlink_btn: 
                        world_unlink_btn.setVisible(True)
                        world_unlink_btn.setEnabled(True)
                    if world_loc_dropdown: 
                        world_loc_dropdown.setVisible(True)
                        world_loc_dropdown.setEnabled(False)
                else:
                    if world_loc_label: 
                        world_loc_label.setVisible(True)
                        world_loc_label.setEnabled(True)
                        world_loc_label.setStyleSheet("font-size: 8pt; font-weight: normal;")
                    if world_unlink_btn: 
                        world_unlink_btn.setVisible(True)
                        world_unlink_btn.setEnabled(False)
                    if world_loc_dropdown:
                        world_loc_dropdown.setVisible(True)
                        world_loc_dropdown.setEnabled(True)
                        self._update_world_location_dropdown()
            elif dot_type == 'small':
                world_set_label = None
                for label_widget in self.world_tab.findChildren(QLabel):
                    if label_widget.text() == "Linked Settings:":
                        world_set_label = label_widget
                        break
                world_unlink_setting_btn = getattr(self, 'world_unlink_setting_btn', None)
                if linked_name:
                    if world_set_label: 
                        world_set_label.setVisible(True)
                        world_set_label.setEnabled(True)
                        world_set_label.setStyleSheet("font-size: 8pt; font-weight: normal;")
                    if world_set_dropdown: 
                        world_set_dropdown.setVisible(True)
                        world_set_dropdown.setEnabled(False)
                    if world_unlink_setting_btn: 
                        world_unlink_setting_btn.setVisible(True)
                        world_unlink_setting_btn.setEnabled(True)
                else:
                    if world_set_label: 
                        world_set_label.setVisible(True)
                        world_set_label.setEnabled(True)
                        world_set_label.setStyleSheet("font-size: 8pt; font-weight: normal;")
                    if world_set_dropdown:
                        world_set_dropdown.setVisible(True)
                        world_set_dropdown.setEnabled(True)
                        self._update_world_setting_dropdown()
                    if world_unlink_setting_btn: 
                        world_unlink_setting_btn.setVisible(True)
                        world_unlink_setting_btn.setEnabled(False)

        elif item_type == 'line' and isinstance(item_index_or_name, int) and 0 <= item_index_or_name < len(self._world_lines):
            self._world_selected_item_type = 'line'
            self._world_selected_item_index = item_index_or_name
            line_data = self._world_lines[item_index_or_name]
            if isinstance(line_data, tuple) and len(line_data) == 2:
                path_points, meta = line_data
                if isinstance(meta, dict):
                    start_idx, end_idx = meta.get('start', -1), meta.get('end', -1)
                    line_type_disp = meta.get('type', 'path').capitalize()
                    start_desc = self._get_dot_description(start_idx, self._world_dots) if start_idx is not None and start_idx >= 0 else "Unknown Start"
                    end_desc = self._get_dot_description(end_idx, self._world_dots) if end_idx is not None and end_idx >= 0 else "Unknown End"
                    path_name = meta.get('name', '')
                    if not path_name:
                        path_display_name = "Unnamed Path"
                    else:
                        path_display_name = path_name
                    path_len = sum(math.dist(path_points[i], path_points[i+1]) for i in range(len(path_points)-1)) if len(path_points) >=2 else 0
                    def valid_idx(idx):
                        return isinstance(idx, int) and idx >= 0 and idx < len(self._world_dots) and len(self._world_dots[idx]) >= 6
                    start_reg = self._world_dots[start_idx][5] if valid_idx(start_idx) else None
                    end_reg = self._world_dots[end_idx][5] if valid_idx(end_idx) else None
                    title = f"{path_display_name} - {line_type_disp}: {start_desc} <--> {end_desc} (Len: {path_len:.1f})"
                    if start_reg and end_reg and start_reg != end_reg:
                        title += f"\nCrosses: {self._format_region_name_for_display(start_reg)} to {self._format_region_name_for_display(end_reg)}"
                    self.world_map_title_label.setText(title)
                else: self.world_map_title_label.setText("Selected World Path")
            else: self.world_map_title_label.setText("Selected World Path (Invalid Data)")

        elif item_type == 'region' and isinstance(item_index_or_name, str):
            self._world_selected_item_type = 'region'
            self._world_selected_region_name = item_index_or_name
            self._world_selected_item_index = -1 
            world_disp_name = self.current_world_name.replace("_", " ").title() if self.current_world_name else "World Map"
            self.world_map_title_label.setText(f"{world_disp_name} - Region: {self._format_region_name_for_display(str(item_index_or_name))}")

    elif map_type == 'location':
        self._location_selected_item_type = item_type
        self._location_selected_item_index = item_index_or_name
        if hasattr(self, 'location_map_label') and self.location_map_label:
            self.location_map_label._location_selected_item_type = item_type
            self.location_map_label._location_selected_item_index = item_index_or_name
        self._world_selected_item_type = None
        self._world_selected_item_index = -1
        self._world_selected_region_name = None
        if item_type == 'dot' and 0 <= item_index_or_name < len(self._location_dots):
            dot_data = self._location_dots[item_index_or_name]
            x = dot_data[0] if len(dot_data) > 0 else None
            y = dot_data[1] if len(dot_data) > 1 else None
            dot_type = dot_data[3] if len(dot_data) > 3 else None
            linked_name = dot_data[4] if len(dot_data) > 4 else None
            region_name = dot_data[5] if len(dot_data) > 5 else None
            location_display_name = "Location Map"
            if self.current_location_name:
                location_display_name = self.current_location_name.replace("_", " ").title()
            if linked_name:
                fresh_setting_name = linked_name
                setting_region = None
                if self.workflow_data_dir and self.current_world_name and self.current_location_name:
                    location_path = None
                    for base_dir in ['game', 'resources/data files']:
                        for region_name in os.listdir(os.path.join(self.workflow_data_dir, base_dir, 'settings', self.current_world_name)):
                            region_path = os.path.join(self.workflow_data_dir, base_dir, 'settings', self.current_world_name, region_name)
                            if not os.path.isdir(region_path):
                                continue
                            for location_folder in os.listdir(region_path):
                                location_candidate = os.path.join(region_path, location_folder)
                                if not os.path.isdir(location_candidate):
                                    continue
                                for file in os.listdir(location_candidate):
                                    if file.endswith('_location.json'):
                                        location_data = self._load_json(os.path.join(location_candidate, file))
                                        if location_data and location_data.get('name', '').lower() == self.current_location_name.lower():
                                            location_path = location_candidate
                                            break
                                if location_path:
                                    setting_json_filename = f"{sanitize_path_name(linked_name)}_setting.json"
                                    setting_path = os.path.join(location_path, setting_json_filename)
                                    if os.path.isfile(setting_path):
                                        setting_data = self._load_json(setting_path)
                                        if setting_data and 'name' in setting_data:
                                            fresh_setting_name = setting_data['name']
                                            setting_region = setting_data.get('region', region_name)
                                    break
                            if location_path:
                                break
                title = f"{location_display_name} - Setting: {fresh_setting_name}"
                if setting_region:
                    title += f" in {self._format_region_name_for_display(setting_region)}"
                elif region_name and len(dot_data) > 5:
                    title += f" in {self._format_region_name_for_display(region_name)}"
            else:
                title = f"{location_display_name} - Setting Dot ({x:.2f}, {y:.2f})"
            self.location_map_title_label.setText(title)
            setting_label = None
            for label in self.location_tab.findChildren(QLabel):
                if label.text() == "Settings:":
                    setting_label = label
                    break
            if setting_label: 
                setting_label.setVisible(False)
            if self.location_setting_dropdown: 
                self.location_setting_dropdown.setVisible(False)
            if self.location_unlink_setting_btn: 
                self.location_unlink_setting_btn.setVisible(False)
            if dot_type == 'small':
                if setting_label: 
                    setting_label.setVisible(True)
                    setting_label.setEnabled(True)
                    setting_label.setStyleSheet("font-size: 8pt; font-weight: normal;")
                if self.location_setting_dropdown: 
                    self.location_setting_dropdown.setVisible(True)
                    self.location_setting_dropdown.setEnabled(not linked_name)
                if self.location_unlink_setting_btn: 
                    self.location_unlink_setting_btn.setVisible(True)
                    self.location_unlink_setting_btn.setEnabled(bool(linked_name))
                self._update_location_setting_dropdown()
        elif item_type == 'line' and 0 <= item_index_or_name < len(self._location_lines):
            line_data = self._location_lines[item_index_or_name]
            if isinstance(line_data, tuple) and len(line_data) == 2:
                path_points, meta = line_data
                if isinstance(meta, dict):
                    start_idx = meta.get('start', -1)
                    end_idx = meta.get('end', -1)
                    line_type = meta.get('type', 'path').capitalize()
                    start_desc = self._get_dot_description(start_idx, self._location_dots) if start_idx is not None and start_idx >= 0 else "Unknown Start"
                    end_desc = self._get_dot_description(end_idx, self._location_dots) if end_idx is not None and end_idx >= 0 else "Unknown End"
                    location_display_name = self.current_location_name.replace("_", " ").title() if self.current_location_name else "Location Map"
                    path_length = 0
                    if len(path_points) >= 2:
                        for i in range(len(path_points) - 1):
                            path_length += math.dist(path_points[i], path_points[i+1])
                    title = f"{location_display_name} - {line_type}: {start_desc} <--> {end_desc} (Length: {path_length:.1f})"
                    self.location_map_title_label.setText(title)
                    for label in self.location_tab.findChildren(QLabel):
                        if label.text() == "Settings:":
                            label.setVisible(False)
                    if self.location_setting_dropdown: 
                        self.location_setting_dropdown.setVisible(False)
                else:
                    self.location_map_title_label.setText("Selected Location Path")
            else:
                    self.location_map_title_label.setText("Selected Location Path")
    label = getattr(self, f"{map_type}_map_label", None)
    if label: 
        if hasattr(label, '_last_selected_type') and hasattr(label, '_last_selected_index'):
            if label._last_selected_type != item_type or label._last_selected_index != item_index_or_name:
                label._last_selected_type = item_type
                label._last_selected_index = item_index_or_name
                label.update()
        else:
            label._last_selected_type = item_type
            label._last_selected_index = item_index_or_name
            label.update()
    if world_loc_dropdown and world_loc_dropdown.isVisible():
        world_loc_dropdown.blockSignals(True)
        world_loc_dropdown.blockSignals(False)
    if world_set_dropdown and world_set_dropdown.isVisible():
        world_set_dropdown.blockSignals(True)
        world_set_dropdown.blockSignals(False)