from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox
import os
import re

def create_automate_section():
    automate_widget = QWidget()
    automate_layout = QVBoxLayout(automate_widget)
    automate_layout.setContentsMargins(0, 0, 0, 0)
    automate_layout.setSpacing(4)
    all_checkboxes = {}
    none_mode_labels = [
        ("Delete Linked Locations", "delete_linked_locations_cb"),
        ("Delete Linked Settings", "delete_linked_settings_cb")
    ]
    all_checkboxes['none_mode'] = []
    for text, object_name_suffix in none_mode_labels:
        cb = QCheckBox(text)
        cb.setObjectName(f"Automate_{object_name_suffix}")
        cb.setChecked(True)
        automate_layout.addWidget(cb)
        all_checkboxes['none_mode'].append((text, cb))
    add_setting_cb = QCheckBox("Generate Setting")
    add_setting_cb.setObjectName("Automate_generate_setting_cb")
    add_setting_cb.setChecked(True)
    add_setting_cb.setVisible(False)
    automate_layout.addWidget(add_setting_cb)
    all_checkboxes['add_setting_mode'] = [("Generate Setting", add_setting_cb)]
    other_modes = {
        'path_mode': [
            ("Auto-Connect Paths", "auto_connect_paths_cb"),
            ("Auto-Name Paths", "auto_name_paths_cb"),
        ],
        'road_mode': [
            ("Auto-Connect Roads", "auto_connect_roads_cb"),
            ("Auto-Generate Intersections", "auto_generate_intersections_cb"),
        ],
        'region_mode': [
            ("Auto-Color Regions", "auto_color_regions_cb"),
            ("Auto-Name Locations", "auto_name_locations_cb"),
        ]
    }
    for mode, labels in other_modes.items():
        all_checkboxes[mode] = []
        for text, object_name_suffix in labels:
            cb = QCheckBox(text)
            cb.setObjectName(f"Automate_{object_name_suffix}")
            cb.setVisible(False)  # Hide initially
            automate_layout.addWidget(cb)
            all_checkboxes[mode].append((text, cb))
    
    return automate_widget, all_checkboxes

def connect_automate_checkboxes(world_editor_ref, checkboxes_dict):
    pass

def handle_dot_deletion(world_editor_ref, dot_data, map_type):
    if map_type not in ('world', 'location'):
        return
    if not isinstance(dot_data, list) and not isinstance(dot_data, tuple):
        return
    dot_name = None
    dot_type = None
    try:
        if isinstance(dot_data, tuple):
            dot_data = list(dot_data)
        if len(dot_data) >= 6:
            dot_type = dot_data[3]
            dot_name = dot_data[4]
        elif len(dot_data) >= 5:
            dot_type = dot_data[3]
            dot_name = dot_data[4]
        elif len(dot_data) >= 4:
            dot_type = dot_data[3]
        if not dot_name:
            return
    except Exception as e:
        import traceback
        traceback.print_exc()
        return
    if map_type == 'world':
        checkboxes_dict = getattr(world_editor_ref, 'automate_checkboxes_dict', {})
    elif map_type == 'location':
        checkboxes_dict = getattr(world_editor_ref, 'location_automate_checkboxes_dict', {})
    else:
        checkboxes_dict = {}
    if not checkboxes_dict or 'none_mode' not in checkboxes_dict:
        return
    none_mode_cbs = checkboxes_dict.get('none_mode', [])
    delete_linked_settings = False
    delete_linked_locations = False
    for text, cb in none_mode_cbs:
        if text == "Delete Linked Settings" and cb.isChecked():
            delete_linked_settings = True
        elif text == "Delete Linked Locations" and cb.isChecked():
            delete_linked_locations = True

def delete_setting(world_editor_ref, setting_display_name, world_name, region_name=None, location_name=None):
    print(f"Attempting to delete setting: '{setting_display_name}' in W:'{world_name}' R:'{region_name}' L:'{location_name}'")
    if not world_editor_ref.workflow_data_dir or not world_name:
        return False
    if setting_display_name == "Elementary School" and location_name == "Elementary School":
        special_path = os.path.join(world_editor_ref.workflow_data_dir, 'resources', 'data files', 'settings', 
                                  world_name, 'elementary_school', 'elementary_school2_setting.json')
        if os.path.isfile(special_path):
            try:
                os.remove(special_path)
                print(f"  SUCCESS: Deleted special case setting file: {special_path}")
                if hasattr(world_editor_ref, 'settingAddedOrRemoved'):
                    world_editor_ref.settingAddedOrRemoved.emit()
                return True
            except Exception as e:
                print(f"  Error deleting special case setting file: {e}")
                return False
    base_world_path = os.path.join(world_editor_ref.workflow_data_dir, 'resources', 'data files', 'settings', world_name)
    setting_sanitized_name = sanitize_path_name(setting_display_name)
    setting_json_filenames = [
        f"{setting_sanitized_name}_setting.json",
        f"{sanitize_path_name(location_name)}_setting.json" if location_name else None,
        f"{setting_sanitized_name.replace('_', '')}_setting.json",
        f"{setting_display_name.lower().replace(' ', '_')}_setting.json",
        f"{setting_sanitized_name}2_setting.json",
        f"{setting_sanitized_name}_setting_2.json",
        f"{setting_sanitized_name}_2_setting.json",
    ]
    setting_json_filenames = [f for f in setting_json_filenames if f]
    search_attempt_count = 0
    setting_file_path_to_delete = None
    if location_name:
        loc_sanitized = sanitize_path_name(location_name)
        loc_path = os.path.join(base_world_path, loc_sanitized)
        if os.path.isdir(loc_path):
            for setting_filename in setting_json_filenames:
                setting_path = os.path.join(loc_path, setting_filename)
                search_attempt_count += 1
                if os.path.isfile(setting_path):
                    try:
                        data = world_editor_ref._load_json(setting_path)
                        if data.get("name", "").lower() == setting_display_name.lower():
                            setting_file_path_to_delete = setting_path
                            break
                    except Exception as e:
                        print(f"  Error checking JSON at {setting_path}: {e}")
            if not setting_file_path_to_delete:
                if os.path.isdir(loc_path):
                    for filename in os.listdir(loc_path):
                        if filename.endswith("_setting.json"):
                            setting_path = os.path.join(loc_path, filename)
                            search_attempt_count += 1
                            if os.path.isfile(setting_path):
                                try:
                                    data = world_editor_ref._load_json(setting_path)
                                    if data.get("name", "").lower() == setting_display_name.lower():
                                        setting_file_path_to_delete = setting_path
                                        break
                                except Exception as e:
                                    print(f"  Error checking fallback JSON at {setting_path}: {e}")
    if not setting_file_path_to_delete and region_name and location_name:
        reg_sanitized = sanitize_path_name(region_name)
        loc_sanitized = sanitize_path_name(location_name)
        region_loc_path = os.path.join(base_world_path, reg_sanitized, loc_sanitized)
        if os.path.isdir(region_loc_path):
            for setting_filename in setting_json_filenames:
                setting_path = os.path.join(region_loc_path, setting_filename)
                search_attempt_count += 1
                if os.path.isfile(setting_path):
                    try:
                        data = world_editor_ref._load_json(setting_path)
                        if data.get("name", "").lower() == setting_display_name.lower():
                            setting_file_path_to_delete = setting_path
                            break
                    except Exception as e:
                        print(f"  Error checking JSON at {setting_path}: {e}")
    if not setting_file_path_to_delete:
        for setting_filename in setting_json_filenames:
            setting_path = os.path.join(base_world_path, setting_filename)
            search_attempt_count += 1
            if os.path.isfile(setting_path):
                try:
                    data = world_editor_ref._load_json(setting_path)
                    if data.get("name", "").lower() == setting_display_name.lower():
                        setting_file_path_to_delete = setting_path
                        break
                except Exception as e:
                    print(f"  Error checking JSON at {setting_path}: {e}")
    if not setting_file_path_to_delete:
        for root, dirs, files in os.walk(base_world_path):
            if os.path.basename(root) == 'resources':
                dirs[:] = []
                continue
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    search_attempt_count += 1
                    setting_path = os.path.join(root, filename)
                    try:
                        data = world_editor_ref._load_json(setting_path)
                        if data.get("name", "").lower() == setting_display_name.lower():
                            setting_file_path_to_delete = setting_path
                            setting_folder_path_to_delete = root
                            break
                    except Exception as e:
                        print(f"  Error reading JSON at {setting_path}: {e}")
            if setting_file_path_to_delete:
                break
    if not setting_file_path_to_delete:
        return False
    deleted_files = False
    try:
        if os.path.exists(setting_file_path_to_delete):
            os.remove(setting_file_path_to_delete)
            print(f"  SUCCESS: Deleted setting file: {setting_file_path_to_delete}")
            deleted_files = True
        else:
            print(f"  WARNING: Setting file no longer exists at {setting_file_path_to_delete}")
        if deleted_files:
            if hasattr(world_editor_ref, 'settingAddedOrRemoved'):
                print("  Emitting settingAddedOrRemoved signal from WorldEditorWidget due to setting deletion.")
                world_editor_ref.settingAddedOrRemoved.emit()
                return True
            return True
        else:
            print("  No files were deleted.")
            return False
    except Exception as e:
        print(f"  ERROR: Failed to delete setting resources for '{setting_display_name}': {e}")
        import traceback
        traceback.print_exc()
        return False

def should_delete_linked_locations(editor_widget):
    if not hasattr(editor_widget, 'automate_checkboxes_dict'):
        return False
    try:
        checkboxes = editor_widget.automate_checkboxes_dict.get('none_mode', [])
        for cb in checkboxes:
            if cb.objectName() == "Automate_delete_linked_locations_cb":
                is_checked = cb.isChecked()
                return is_checked
        print("[DEBUG] Delete Linked Locations checkbox not found")
    except Exception as e:
        print(f"[DEBUG] Error checking delete_linked_locations: {e}")
    return False

def should_delete_linked_settings(editor_widget):
    if not hasattr(editor_widget, 'automate_checkboxes_dict'):
        return False
    try:
        checkboxes = editor_widget.automate_checkboxes_dict.get('none_mode', [])
        for cb in checkboxes:
            if cb.objectName() == "Automate_delete_linked_settings_cb":
                is_checked = cb.isChecked()
                return is_checked
        print("[DEBUG] Delete Linked Settings checkbox not found")
    except Exception as e:
        print(f"[DEBUG] Error checking delete_linked_settings: {e}")
    return False

def delete_location(world_editor_ref, location_name):
    try:
        workflow_data_dir = world_editor_ref.workflow_data_dir
        world_name = world_editor_ref.current_world_name
        if not workflow_data_dir or not world_name:
            return False
        world_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings', world_name)
        if not os.path.isdir(world_dir):
            return False
        found_location_path = None
        for region in os.listdir(world_dir):
            region_dir = os.path.join(world_dir, region)
            if os.path.isdir(region_dir) and region != "resources":
                for location_folder in os.listdir(region_dir):
                    location_path = os.path.join(region_dir, location_folder)
                    if os.path.isdir(location_path):
                        try:
                            if location_folder.lower() == location_name.lower().replace(' ', '_'):
                                found_location_path = location_path
                                found_region = region
                                break
                            loc_json_file = f"{location_folder.lower()}_location.json"
                            loc_json_path = os.path.join(location_path, loc_json_file)
                            if os.path.exists(loc_json_path):
                                try:
                                    import json
                                    with open(loc_json_path, 'r', encoding='utf-8') as f:
                                        loc_data = json.load(f)
                                    display_name = loc_data.get('name')
                                    if display_name and display_name.lower() == location_name.lower():
                                        found_location_path = location_path
                                        found_region = region
                                        break
                                except:
                                    continue
                        except:
                            continue
                            
                if found_location_path:
                    break
        if found_location_path and os.path.exists(found_location_path):
            import shutil
            shutil.rmtree(found_location_path)
            return True
        else:
            for region in os.listdir(world_dir):
                region_dir = os.path.join(world_dir, region)
                if os.path.isdir(region_dir) and region != "resources":
                    for location_folder in os.listdir(region_dir):
                        if (location_name.lower() in location_folder.lower() or 
                            location_folder.lower() in location_name.lower()):
                            location_path = os.path.join(region_dir, location_folder)
                            if os.path.isdir(location_path):
                                import shutil
                                shutil.rmtree(location_path)
                                return True
            return False
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

def sanitize_file_name(name):
    if not name:
        return "untitled"
    sanitized = re.sub(r'[^\w\-]', '_', name.lower().strip())
    return sanitized 

def sanitize_path_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', name).strip()
    sanitized = sanitized.replace(' ', '_').lower()
    return sanitized or 'untitled'

def set_automate_section_mode(checkboxes_dict, mode):
    if mode == 'hidden_mode':
        for checkbox_list in checkboxes_dict.values():
            for _, cb in checkbox_list:
                cb.setVisible(False)
        return
    for key, checkbox_list in checkboxes_dict.items():
        for _, cb in checkbox_list:
            cb.setVisible(key == mode)

def find_location_folder_by_display_name(parent_dir, display_name):
    import os, json
    if not os.path.isdir(parent_dir):
        return None
    def norm(s):
        return sanitize_file_name(s).replace('_', '').replace(' ', '').lower()
    norm_display = norm(display_name)
    for item_name_in_dir in os.listdir(parent_dir):
        current_item_path = os.path.join(parent_dir, item_name_in_dir)
        if os.path.isdir(current_item_path):
            sanitized_item_name = sanitize_file_name(item_name_in_dir)
            norm_item = norm(item_name_in_dir)
            if norm_item == norm_display:
                return current_item_path
            else:
                possible_json_filenames = [
                    f"{item_name_in_dir}_location.json", 
                    f"{sanitize_file_name(item_name_in_dir)}_location.json"
                ]
                for json_filename in possible_json_filenames:
                    json_file_path = os.path.join(current_item_path, json_filename)
                    if os.path.isfile(json_file_path):
                        try:
                            with open(json_file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            json_display_name = data.get('name')
                            if json_display_name and norm(json_display_name) == norm_display:
                                return current_item_path
                        except Exception as e:
                            print(f"[DEBUG FIND_LOC_FOLDER]         ERROR: Could not read or parse JSON file {json_file_path}: {e}")
    return None

def find_region_folder_by_display_name(parent_dir, display_name):
    import os, json
    def norm(s):
        return sanitize_file_name(s).replace('_', '').replace(' ', '').lower()
    norm_display = norm(display_name)
    if not os.path.isdir(parent_dir):
        return None
    for item_name_in_dir in os.listdir(parent_dir):
        current_item_path = os.path.join(parent_dir, item_name_in_dir)
        if os.path.isdir(current_item_path):
            norm_item = norm(item_name_in_dir)
            if norm_item == norm_display:
                return current_item_path
            possible_json_filenames = [
                f"{item_name_in_dir}_region.json",
                f"{sanitize_file_name(item_name_in_dir)}_region.json"
            ]
            for json_filename in possible_json_filenames:
                json_file_path = os.path.join(current_item_path, json_filename)
                if os.path.isfile(json_file_path):
                    try:
                        with open(json_file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        json_display_name = data.get('name')
                        if json_display_name and norm(json_display_name) == norm_display:
                            return current_item_path
                    except Exception:
                        pass
    return None

def generate_setting_file(world_editor_ref, x, y, map_type):
    import os, json, time, re
    workflow_data_dir = getattr(world_editor_ref, 'workflow_data_dir', None)

    def _clean_name_for_setting_base(name_str):
        if not isinstance(name_str, str) or not name_str.strip():
            return name_str
        temp_name = name_str.strip()
        if temp_name.lower().endswith(" setting"):
            temp_name = temp_name[:-len(" Setting")].strip()
        elif temp_name.lower().endswith("_setting"):
            temp_name = temp_name[:-len("_setting")].strip("_")
        return temp_name if temp_name else name_str

    def get_next_setting_filename(base_dir, base_name):
        pattern = re.compile(rf"^{re.escape(base_name)}(\d*)_setting\.json$")
        used_numbers = set()
        for file in os.listdir(base_dir):
            m = pattern.match(file)
            if m:
                num_str = m.group(1)
                if num_str == '':
                    used_numbers.add(0)
                else:
                    used_numbers.add(int(num_str))
        idx = 0
        while idx in used_numbers:
            idx += 1
        if idx == 0:
            return f"{base_name}_setting.json", idx
        else:
            return f"{base_name}{idx}_setting.json", idx
            
    def get_coordinates_based_filename(base_dir, base_prefix, x, y):
        x_int = int(round(x))
        y_int = int(round(y))
        coord_base = f"{sanitize_file_name(base_prefix)}_{x_int}x{y_int}"
        filename = f"{coord_base}_setting.json"
        if os.path.exists(os.path.join(base_dir, filename)):
            idx = 1
            while os.path.exists(os.path.join(base_dir, f"{coord_base}_{idx}_setting.json")):
                idx += 1
            filename = f"{coord_base}_{idx}_setting.json"
        return filename
    if map_type == 'location':
        world_name = getattr(world_editor_ref, 'current_world_name', None)
        location_name = getattr(world_editor_ref, 'current_location_name', None)
        region_name = getattr(world_editor_ref, '_world_region_name', None)
        if not all([world_name, location_name, workflow_data_dir]):
            return None
        workflow_abs = os.path.abspath(workflow_data_dir)
        world_dir = os.path.join(workflow_abs, 'resources', 'data files', 'settings', world_name)
        found_location_folder = None
        from world_editor_auto import find_location_folder_by_display_name
        direct_location = find_location_folder_by_display_name(world_dir, location_name)
        if direct_location:
            found_location_folder = direct_location
        else:
            for item in os.listdir(world_dir):
                region_path = os.path.join(world_dir, item)
                if os.path.isdir(region_path) and item.lower() != 'resources':
                    possible_location = find_location_folder_by_display_name(region_path, location_name)
                    if possible_location:
                        print(f"[GEN] Found location in region '{item}': {possible_location}")
                        found_location_folder = possible_location
                        region_name = item
                        setattr(world_editor_ref, '_world_region_name', item)
                        break
        if found_location_folder:
            location_folder_path = found_location_folder
        else:
            if not region_name or str(region_name).upper() in ("NONE", "__GLOBAL__", "GLOBAL"):
                parent_dir = world_dir
            else:
                parent_dir = os.path.join(world_dir, region_name)
            os.makedirs(parent_dir, exist_ok=True)
            sanitized_location = sanitize_file_name(location_name)
            location_folder_path = os.path.join(parent_dir, sanitized_location)
            os.makedirs(location_folder_path, exist_ok=True)
        setting_filename = get_coordinates_based_filename(location_folder_path, location_name, x, y)
        setting_file_path = os.path.join(location_folder_path, setting_filename)
        timestamp = int(time.time())
        x_int = int(round(x))
        y_int = int(round(y))
        setting_display_name = f"{location_name} Setting ({x_int},{y_int})"
        data = {
            "name": setting_display_name,
            "created": timestamp,
            "x": x,
            "y": y,
            "type": "location_setting"
        }
        with open(setting_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return setting_display_name
    else:
        region_name_at_dot = None
        if hasattr(world_editor_ref, '_get_region_at_point'):
            region_name_at_dot = world_editor_ref._get_region_at_point(x, y)
        current_world_name_from_we = getattr(world_editor_ref, 'current_world_name', None)
        workflow_data_dir_from_we = getattr(world_editor_ref, 'workflow_data_dir', None)
        if not current_world_name_from_we or not workflow_data_dir_from_we:
            return None
        world_filesystem_name = sanitize_file_name(current_world_name_from_we)
        actual_world_dir = os.path.join(workflow_data_dir_from_we, 'resources', 'data files', 'settings', world_filesystem_name)
        os.makedirs(actual_world_dir, exist_ok=True)
        target_save_dir = actual_world_dir
        base_prefix_for_name = current_world_name_from_we
        if region_name_at_dot:
            sanitized_region_name_at_dot = sanitize_file_name(str(region_name_at_dot).split(os.sep)[-1])
            strict_region_dir = os.path.join(actual_world_dir, sanitized_region_name_at_dot)
            os.makedirs(strict_region_dir, exist_ok=True)
            target_save_dir = strict_region_dir
            base_prefix_for_name = str(region_name_at_dot)
        setting_filename = get_coordinates_based_filename(target_save_dir, base_prefix_for_name, x, y)
        fpath = os.path.join(target_save_dir, setting_filename)
        x_int = int(round(x))
        y_int = int(round(y))
        setting_display_name = f"{base_prefix_for_name} Setting ({x_int},{y_int})"
        setting_data = {
            "name": setting_display_name,
            "description": "Auto-generated setting.",
            "region": region_name_at_dot or None,
            "x": x,
            "y": y,
            "world": current_world_name_from_we
        }
        try:
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(setting_data, f, indent=2)
                f.flush()
        except Exception as e:
            return None
        if hasattr(world_editor_ref, 'force_populate_dropdowns'):
            world_editor_ref.force_populate_dropdowns()
        return setting_data["name"]