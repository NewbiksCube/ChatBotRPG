from typing import List, Dict, Optional, Any
import json
import os
import re
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt5.QtCore import QObject, pyqtSignal

def sanitize_path_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', name).strip()
    sanitized = sanitized.replace(' ', '_').lower()
    return sanitized or 'untitled'

def _save_json(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON to {file_path}: {e}")
        return False

def _load_json(file_path):
    try:
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return {}

def create_generate_setting_widget(parent=None):
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    label = QLabel('Setting Description:')
    input_field = QLineEdit()
    input_field.setObjectName('SettingDescriptionInput')
    input_field.setText('Describe a fantasy city built on floating islands.')
    layout.addWidget(label)
    layout.addWidget(input_field)
    widget.setLayout(layout)
    return widget 

class SettingGenerationWorker(QObject):
    generation_complete = pyqtSignal(dict)
    generation_error = pyqtSignal(str)

    def __init__(self, 
                 setting_filepath: str,
                 setting_name: str,
                 current_setting_data: Dict[str, Any],
                 options: Dict[str, bool],
                 world_data: Dict[str, Any],
                 region_data: Optional[Dict[str, Any]],
                 location_data: Optional[Dict[str, Any]],
                 map_connections_data: List[Dict[str, Any]],
                 map_type_for_connections: str,
                 containing_features_data: List[Dict[str, Any]],
                 additional_instructions: str = "",
                 cot_model=None,
                 temperature=0.7,
                 parent=None):
        super().__init__(parent)
        self.setting_filepath = setting_filepath
        self.setting_name = setting_name
        self.current_setting_data = current_setting_data
        self.options = options
        self.world_data = world_data
        self.region_data = region_data
        self.location_data = location_data
        self.map_connections_data = map_connections_data
        self.map_type_for_connections = map_type_for_connections
        self.containing_features_data = containing_features_data
        self.additional_instructions = additional_instructions
        self.cot_model = cot_model
        self.temperature = temperature
        self._is_running = False
        
    def run(self):
        self._is_running = True
        try:
            generated_data = {}
            ordered_fields = []
            if self.options.get("description", False): ordered_fields.append("description")
            if self.options.get("name", False): ordered_fields.append("name")
            if self.options.get("connections", False): ordered_fields.append("connections")
            if self.options.get("inventory", False): ordered_fields.append("inventory")
            for field in ordered_fields:
                if not self._is_running:
                    return
                try:
                    context = ""
                    if field == "description":
                        context = self._prepare_context_for_description()
                    elif field == "name":
                        context = self._prepare_context_for_name(self.current_setting_data.get("description"))
                    elif field == "connections":
                        context = self._prepare_context_for_connections(self.current_setting_data.get("description"))
                    elif field == "inventory":
                        context = self._prepare_context_for_inventory(self.current_setting_data.get("description"))
                    generated_value = self._generate_field(field, context)
                    self.current_setting_data[field] = generated_value
                    generated_data[field] = generated_value
                    if field == "connections" and isinstance(generated_value, dict):
                        variables = {}
                        for connected_setting, description in generated_value.items():
                            var_name = f"travel_notes_to_{sanitize_path_name(connected_setting)}"
                            variables[var_name] = description
                        if "variables" not in self.current_setting_data:
                            self.current_setting_data["variables"] = {}
                        self.current_setting_data["variables"].update(variables)
                        generated_data["variables"] = variables
                except Exception as e:
                    error_msg = f"Failed to generate '{field}': {e}"
                    print(error_msg)
                    self.generation_error.emit(error_msg)
                    return
            if self._is_running and generated_data:
                self._handle_generation_complete(generated_data)
            elif self._is_running:
                self.generation_error.emit("No fields were selected for generation.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.generation_error.emit(str(e))
    
    def _prepare_context_for_description(self) -> str:
        context_parts = []
        context_parts.append(f"WORLD INFORMATION:")
        context_parts.append(f"World Name: {self.world_data.get('name', 'Unknown World')}")
        context_parts.append(f"World Description: {self.world_data.get('description', 'No description available.')}")
        if self.region_data:
            context_parts.append(f"\nREGION INFORMATION:")
            context_parts.append(f"Region Name: {self.region_data.get('name', 'Unknown Region')}")
            context_parts.append(f"Region Description: {self.region_data.get('description', 'No description available.')}")
        if self.location_data:
            context_parts.append(f"\nLOCATION INFORMATION:")
            context_parts.append(f"Location Name: {self.location_data.get('name', 'Unknown Location')}")
            context_parts.append(f"Location Description: {self.location_data.get('description', 'No description available.')}")
        if self.containing_features_data:
            context_parts.append(f"\nCONTAINING FEATURES:")
            for feature in self.containing_features_data:
                context_parts.append(f"- {feature.get('feature_name')}: {feature.get('feature_description')}")
        if self.additional_instructions:
            context_parts.append(f"\nADDITIONAL INSTRUCTIONS:")
            context_parts.append(self.additional_instructions)
        context_parts.append(f"\nCURRENT SETTING NAME: {self.setting_name}")
        return "\n".join(context_parts)
    
    def _prepare_context_for_name(self, generated_description=None) -> str:
        context_parts = []
        if generated_description:
            context_parts.append(f"SETTING DESCRIPTION: {generated_description}")
        elif self.current_setting_data.get("description"):
            context_parts.append(f"SETTING DESCRIPTION: {self.current_setting_data.get('description')}")
        context_parts.append(f"WORLD NAME: {self.world_data.get('name', 'Unknown World')}")
        if self.location_data:
            context_parts.append(f"LOCATION NAME: {self.location_data.get('name', 'Unknown Location')}")
        if self.additional_instructions:
            context_parts.append(f"ADDITIONAL INSTRUCTIONS: {self.additional_instructions}")
        return "\n".join(context_parts)
    
    def _prepare_context_for_connections(self, description=None) -> str:
        context_parts = []
        if description:
            context_parts.append(f"SETTING DESCRIPTION: {description}")
        context_parts.append(f"SETTING NAME: {self.setting_name}")
        context_parts.append(f"\nCONNECTIONS INFORMATION:")
        for conn in self.map_connections_data:
            connected_setting = conn.get('connected_setting_name', 'Unknown')
            segment_desc = conn.get('segment_desc')
            path_type_desc = conn.get('path_type_description')
            map_line_meta_name = conn.get('map_line_meta_name')
            if segment_desc and segment_desc.strip():
                path_desc = segment_desc.strip()
            elif path_type_desc and path_type_desc.strip():
                path_desc = path_type_desc.strip()
            else:
                path_desc = f"Default path of type {map_line_meta_name or 'unknown'}"
            context_parts.append(f"- Connected to: {connected_setting}")
            context_parts.append(f"  Path Type: {map_line_meta_name or 'unknown'}")
            context_parts.append(f"  Path Description: {path_desc}")
        if self.additional_instructions:
            context_parts.append(f"\nADDITIONAL INSTRUCTIONS: {self.additional_instructions}")
        return "\n".join(context_parts)
    
    def _prepare_context_for_inventory(self, description=None) -> str:
        context_parts = []
        if description:
            context_parts.append(f"SETTING DESCRIPTION: {description}")
        context_parts.append(f"SETTING NAME: {self.setting_name}")
        if self.containing_features_data:
            context_parts.append(f"\nCONTAINING FEATURES:")
            for feature in self.containing_features_data:
                context_parts.append(f"- {feature.get('feature_name')}: {feature.get('feature_description')}")
        if self.additional_instructions:
            context_parts.append(f"\nADDITIONAL INSTRUCTIONS: {self.additional_instructions}")
        return "\n".join(context_parts)
    
    def _generate_field(self, field_name, context):
        from core.make_inference import make_inference
        from config import get_default_utility_model
        import json
        import re
        url_type_to_use = self.cot_model if self.cot_model else get_default_utility_model()
        temperature_to_use = self.temperature if self.temperature is not None else 0.7
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            if field_name == "description":
                prompt = f"Generate a short, simple, and to-the-point description for a setting based on the following context. Limit your answer to 1-2 clear sentences. Avoid extra detail or atmosphere. Output plain text only, no markdown formatting.\n\nCONTEXT:\n{context}\n\nDESCRIPTION:"
            elif field_name == "name":
                prompt = f"Suggest a single, concise, evocative name for a setting based on the following context. The name should be 1-4 words, no explanations, no lists, no punctuation, and no quotes. Return ONLY the name, nothing else. Output plain text only, no markdown formatting.\n\nCONTEXT:\n{context}\n\nSETTING NAME:"
            elif field_name == "connections":
                prompt = f"For a setting with the following context, generate a brief, direct phrase for each path leading to connected locations. Include a small amount of detail or atmosphere, preferably something unique and memorable, but keep it short. Do NOT include directions such as north or south.\n\nCONTEXT:\n{context}\n\nDescribe each connection as a JSON object with location names as keys and short path descriptions as values. Example:\n{{\n  \"Forest Clearing\": \"Narrow dirt path\",\n  \"Mountain Pass\": \"Steep rocky trail\"\n}}\n\nOutput ONLY the JSON object:\nCONNECTIONS:"
            elif field_name == "inventory":
                prompt = f"Generate a list of notable items or objects that would be found in this setting based on the context. These items might be interactable, collectible, or simply part of the atmosphere. Include 3-7 items that make sense for this type of location.\n\nCONTEXT:\n{context}\n\nItems present in this setting (output as a JSON array of strings):\nINVENTORY:"
            else:
                prompt = f"Generate content for the '{field_name}' of a setting based on this context: {context}"
            if self.additional_instructions:
                prompt += f"\n\nAdditional Instructions:\n{self.additional_instructions}"
            if retry_count > 0:
                prompt += f"\n\nThis is retry #{retry_count}. Please provide a valid, non-empty response."
                if field_name in ["connections", "inventory"]:
                    prompt += " The response should be valid JSON."
            llm_response = make_inference(
                context=[{"role": "user", "content": prompt}],
                user_message=prompt,
                character_name=self.setting_name,
                url_type=url_type_to_use,
                max_tokens=800 if field_name == "description" else 400,
                temperature=temperature_to_use,
                is_utility_call=True
            )
            if not llm_response or any(err in llm_response.lower() for err in ["sorry, api error", "request timed out", "unexpected error"]):
                print(f"API Error or empty response on attempt #{retry_count + 1}: {llm_response}")
                retry_count += 1
                continue
            if field_name == "connections":
                try:
                    json_match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', llm_response, re.IGNORECASE)
                    if json_match:
                        parsed_json = json.loads(json_match.group(1))
                    else:
                        parsed_json = json.loads(llm_response)
                    if isinstance(parsed_json, dict) and parsed_json:
                        return parsed_json
                except json.JSONDecodeError:
                    print(f"Failed to parse connections JSON on attempt #{retry_count + 1}.")
                    retry_count += 1
                    continue
            
            elif field_name == "inventory":
                try:
                    json_match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', llm_response, re.IGNORECASE)
                    if json_match:
                        parsed_json = json.loads(json_match.group(1))
                    else:
                        parsed_json = json.loads(llm_response)
                    if isinstance(parsed_json, list) and parsed_json:
                        return parsed_json
                except json.JSONDecodeError:
                    items = [item.strip() for item in llm_response.split('\n') if item.strip() and not item.startswith(">")]
                    if items:
                        return items
                    print(f"Failed to parse inventory JSON or list on attempt #{retry_count + 1}.")
                    retry_count += 1
                    continue
            else:
                processed_response = llm_response.strip()
                if field_name == "name":
                    processed_response = processed_response.splitlines()[0].strip('"\' .,:;')[:64]
                if processed_response:
                    return processed_response
                else:
                    print(f"Received empty response for {field_name} on attempt #{retry_count + 1}.")
                    retry_count += 1
                    continue
        raise Exception(f"Failed to generate valid content for '{field_name}' after {max_retries} attempts.")
    
    def stop(self):
        self._is_running = False
    def _handle_generation_complete(self, generated_data):
        json_data = self.current_setting_data.copy()
        old_name = json_data.get('name', self.setting_name)
        name_changed = False
        new_name = None
        for field, value in generated_data.items():
            if field == 'name' and value != old_name:
                name_changed = True
                new_name = value
                json_data[field] = value
            elif field != "variables":
                json_data[field] = value
        if "variables" in generated_data:
            if "variables" not in json_data:
                json_data["variables"] = {}
            json_data["variables"].update(generated_data["variables"])
        success = _save_json(self.setting_filepath, json_data)
        if not success:
            self.generation_error.emit(f"Failed to save setting data to {self.setting_filepath}")
            return
        result_data = {"setting_data": json_data, "generated": generated_data}
        if name_changed and new_name:
            old_filepath = self.setting_filepath
            self._handle_setting_rename(old_name, new_name)
            result_data["renamed"] = True
            result_data["old_filepath"] = old_filepath
            result_data["new_filepath"] = self.setting_filepath
        self.generation_complete.emit(result_data)

    def _handle_setting_rename(self, old_name, new_name):
        import os
        import shutil
        dir_path = os.path.dirname(self.setting_filepath)
        new_file_name = f"{sanitize_path_name(new_name)}_setting.json"
        new_filepath = os.path.join(dir_path, new_file_name)
        self._update_setting_references(old_name, new_name)
        if os.path.normpath(new_filepath) != os.path.normpath(self.setting_filepath):
            try:
                if os.path.exists(self.setting_filepath):
                    shutil.move(self.setting_filepath, new_filepath)
                    self.setting_filepath = new_filepath
                else:
                    self.setting_filepath = new_filepath
            except Exception as e:
                print(f"Error renaming setting file from {self.setting_filepath} to {new_filepath}: {e}")

    def _update_setting_references(self, old_name, new_name):
        import os
        try:
            path_parts = self.setting_filepath.split(os.sep)
            settings_index = path_parts.index("settings")
            base_settings_dir = os.sep.join(path_parts[:settings_index+1])
        except (ValueError, IndexError):
            return
        for root, _, files in os.walk(base_settings_dir):
            for file in files:
                if file.endswith("_setting.json"):
                    file_path = os.path.join(root, file)
                    if os.path.normpath(file_path) == os.path.normpath(self.setting_filepath):
                        continue
                    try:
                        setting_data = _load_json(file_path)
                        if not setting_data or 'connections' not in setting_data:
                            continue
                        connections = setting_data.get('connections', {})
                        if isinstance(connections, dict) and old_name in connections:
                            print(f"Found reference to '{old_name}' in {file_path}")
                            connections[new_name] = connections.pop(old_name)
                            setting_data['connections'] = connections
                            if 'variables' in setting_data:
                                old_var_name = f"travel_notes_to_{sanitize_path_name(old_name)}"
                                if old_var_name in setting_data['variables']:
                                    new_var_name = f"travel_notes_to_{sanitize_path_name(new_name)}"
                                    setting_data['variables'][new_var_name] = setting_data['variables'].pop(old_var_name)
                            if _save_json(file_path, setting_data):
                                print(f"Updated connection reference in {file_path}")
                    except Exception as e:
                        print(f"Error updating references in {file_path}: {e}")

def trigger_setting_generation_async(
    setting_filepath: str,
    setting_name: str,
    current_setting_data: Dict[str, Any],
    options: Dict[str, bool],
    world_data: Dict[str, Any],
    region_data: Optional[Dict[str, Any]],
    location_data: Optional[Dict[str, Any]],
    map_connections_data: List[Dict[str, Any]],
    map_type_for_connections: str,
    containing_features_data: List[Dict[str, Any]],
    additional_instructions: str = "",
    cot_model: Optional[str] = None,
    temperature: float = 0.7
):
    from PyQt5.QtCore import QThread
    generation_thread = QThread()
    generation_worker = SettingGenerationWorker(
        setting_filepath,
        setting_name, 
        current_setting_data,
        options, 
        world_data, 
        region_data, 
        location_data, 
        map_connections_data,
        map_type_for_connections,
        containing_features_data,
        additional_instructions,
        cot_model,
        temperature
    )
    generation_worker.moveToThread(generation_thread)
    generation_thread.started.connect(generation_worker.run)
    generation_worker.generation_complete.connect(generation_thread.quit)
    generation_worker.generation_error.connect(generation_thread.quit)
    generation_thread.finished.connect(generation_thread.deleteLater)
    generation_worker.generation_complete.connect(generation_worker.deleteLater)
    generation_worker.generation_error.connect(generation_worker.deleteLater)
    generation_thread.start()
    return generation_thread, generation_worker
