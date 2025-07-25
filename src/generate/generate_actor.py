from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import typing
from core.make_inference import make_inference
import os
import json
import re
from config import get_default_utility_model

class ActorData(typing.TypedDict, total=False):
    name: str
    description: str
    personality: str
    appearance: str
    status: str
    relations: dict[str, str]
    goals: str
    story: str
    equipment: dict[str, str]
    abilities: str
    location: str

GENERATABLE_FIELDS: typing.Final[list[str]] = [
    "name", "description", "personality", "appearance", "goals", "story", "equipment", "abilities"
]
GENERATION_ORDER: typing.Final[list[str]] = [
    "name", "description", "personality", "appearance", "goals", "story", "abilities", "equipment"
]
EQUIPMENT_JSON_KEYS: typing.Final[list[str]] = [
    "head", "neck", "left_shoulder", "right_shoulder", "left_hand", "right_hand",
    "upper_over", "upper_outer", "upper_middle", "upper_inner",
    "lower_outer", "lower_middle", "lower_inner",
    "left_foot_inner", "right_foot_inner", "left_foot_outer", "right_foot_outer"
]

class ActorGenerationWorker(QObject):
    generation_complete = pyqtSignal(dict)
    generation_error = pyqtSignal(str)

    def __init__(self, actor_data: ActorData, fields_to_generate: list[str], model_override=None, additional_instructions=None, parent=None):
        super().__init__(parent)
        self.actor_data = actor_data
        self.fields_to_generate = fields_to_generate
        self.model_override = model_override
        self.additional_instructions = additional_instructions
        self._is_running = True

    def run(self):
        try:
            print(f"  >> ActorGenerationWorker.run() started with fields: {self.fields_to_generate}")
            ordered_fields = [f for f in GENERATION_ORDER if f in self.fields_to_generate]
            generated_data = {}
            character_name = self.actor_data.get('name', '').strip()

            if 'name' in ordered_fields:
                ordered_fields.remove('name')
                ordered_fields.insert(0, 'name')

            for field in ordered_fields:
                print(f"  >> Generating field: {field}")
                context = self._prepare_context(field_to_exclude=field)
                
                if self.additional_instructions and '[CURRENT SCENE CONTEXT]' in self.additional_instructions:
                    scene_context_start = self.additional_instructions.find('[CURRENT SCENE CONTEXT]')
                    scene_context_end = self.additional_instructions.find('[/CURRENT SCENE CONTEXT]')
                    if scene_context_start != -1 and scene_context_end != -1:
                        scene_context = self.additional_instructions[scene_context_start + 20:scene_context_end].strip()
                        context = f"Current Scene Context:\n{scene_context}\n\nCharacter Information:\n{context}"
                        print(f"  >> Added scene context to prompt context")
                
                character_name = self.actor_data.get('name', '').strip() or "Unnamed Character"
                url_type = self.model_override if self.model_override else get_default_utility_model()
                retry_count = 0
                max_retries = 5
                llm_response = ""
                success = False
                while not success and retry_count < max_retries:
                    if field == 'name':
                        existing_name = self.actor_data.get('name', '').strip()
                        name_prompt_instruction = f"Invent a new, creative name for a character based on the information below. Avoid simply repeating the existing name ('{existing_name}') if provided. Output just the name without any formatting or extra text."
                        if not existing_name:
                             name_prompt_instruction = "Create a name for a character based on the information below. Output just the name without any formatting or extra text."
                        
                        if self.additional_instructions:
                            instruction_prefix = f"SPECIFIC INSTRUCTIONS: {self.additional_instructions}\n\n"
                            print(f"  >> Using additional instructions: {self.additional_instructions}")
                        else:
                            instruction_prefix = ""
                            print(f"  >> No additional instructions provided")
                        
                        prompt = f"""{instruction_prefix}{name_prompt_instruction}\n\nCurrent Character Sheet:\n{context}\n\nNew Name:"""
                        print(f"  >> Final prompt for {field}:\n{prompt}")
                    elif field == 'description':
                        if self.additional_instructions:
                            instruction_prefix = f"SPECIFIC INSTRUCTIONS: {self.additional_instructions}\n\n"
                            print(f"  >> Using additional instructions: {self.additional_instructions}")
                        else:
                            instruction_prefix = ""
                            print(f"  >> No additional instructions provided")
                        prompt = f"""{instruction_prefix}Given the following information about a character named {character_name}, write a detailed, vivid description of their background, personality, and physical presence. Output plain text only, no markdown formatting.\n\nCurrent Character Sheet:\n{context}\n\nDescription:"""
                        print(f"  >> Final prompt for {field}:\n{prompt}")
                    elif field == 'personality':
                        instruction_prefix = ""
                        if self.additional_instructions:
                            instruction_prefix = f"SPECIFIC INSTRUCTIONS: {self.additional_instructions}\n\n"
                        prompt = f"""{instruction_prefix}Given the following information about a character named {character_name}, write a detailed personality profile. Focus on temperament, values, quirks, and how the character interacts with others. Output plain text only, no markdown formatting.\n\nCurrent Character Sheet:\n{context}\n\nPersonality:"""
                    elif field == 'appearance':
                        instruction_prefix = ""
                        if self.additional_instructions:
                            instruction_prefix = f"SPECIFIC INSTRUCTIONS: {self.additional_instructions}\n\n"
                        prompt = f"""{instruction_prefix}Given the following information about a character named {character_name}, write a detailed physical appearance section. Include build, facial features, hair, eyes, distinguishing marks, and typical clothing style. Output plain text only, no markdown formatting.\n\nCurrent Character Sheet:\n{context}\n\nAppearance:"""
                    elif field == 'goals':
                        prompt = f"""Given the following information about a character named {character_name}, list the character's main goals and motivations. Include both short-term and long-term ambitions, and explain why these goals matter to the character. Output plain text only, no markdown formatting.\n\nCurrent Character Sheet:\n{context}\n\nGoals:"""
                    elif field == 'story':
                        prompt = f"""Given the following information about a character named {character_name}, write a short backstory or narrative that explains how {character_name} became who they are. Focus on key events, relationships, and turning points. Output plain text only, no markdown formatting.\n\nCurrent Character Sheet:\n{context}\n\nStory:"""
                    elif field == 'abilities':
                        prompt = f"""Given the following information about a character named {character_name}, describe the character's notable abilities, skills, and talents. Include both mundane and extraordinary abilities, and explain how they were acquired or developed. Output plain text only, no markdown formatting.\n\nCurrent Character Sheet:\n{context}\n\nAbilities:"""
                    elif field == 'equipment':
                        instruction_prefix = ""
                        if self.additional_instructions:
                            instruction_prefix = f"SPECIFIC INSTRUCTIONS: {self.additional_instructions}\n\n"
                        prompt = (
                            f"{instruction_prefix}You are an expert wardrobe designer. Given the following character information for {character_name}, "
                            "generate a JSON object representing the character's worn equipment. "
                            "The equipment should match the character's theme, type, and station. "
                            "Respect the genre (e.g., medieval, modern, sci-fi)."
                            "\n\n"
                            "Current Character Sheet:\n"
                            f"{context}"
                            "\n\n"
                            "The JSON object MUST contain exactly these keys: "
                            f'{", ".join(EQUIPMENT_JSON_KEYS)}.'
                            "\n\n"
                            "For each key, provide a short description of the item worn/carried in that slot. "
                            "The 'left_hand' and 'right_hand' slots are specifically for WORN items like gloves, rings, bracelets, etc. Do NOT put held items (weapons, shields, tools) here."
                            "If multiple items are worn in the 'left_hand' or 'right_hand' slot, separate them with commas (e.g., \"leather gloves, silver ring\")."
                            "Be very thorough, but if a slot is empty, use an empty string \"\"."
                            "\n\n"
                            "Examples (adapt to character & genre):\n"
                            "  head: (Modern: baseball cap, sunglasses | Medieval: leather hood, metal helm | Empty: \"\")\n"
                            "  neck: (Modern: chain necklace, scarf | Medieval: amulet, wool scarf | Empty: \"\")\n"
                            "  left_shoulder/right_shoulder: (Modern: backpack strap, purse strap | Medieval: pauldron, cloak pin | Empty: \"\")\n"
                            "  left_hand/right_hand (WORN): (Modern: watch, gloves, rings | Medieval: leather gloves, signet ring, bracers | Empty: \"\")\n"
                            "  upper_over: (Modern: jacket, blazer | Medieval: cloak, leather armor | Empty: \"\")\n"
                            "  upper_outer: (Modern: t-shirt, hoodie | Medieval: tunic, jerkin) [Usually not empty]\n"
                            "  upper_middle: (Modern: undershirt, camisole | Medieval: chemise) [Often empty for males]\n"
                            "  upper_inner: (Modern: bra | Medieval: bindings) [Often empty for males]\n"
                            "  lower_outer: (Modern: jeans, skirt | Medieval: trousers, skirt) [Usually not empty]\n"
                            "  lower_middle: (Modern: slip, bike shorts | Medieval: shorts, braies) [Often empty]\n"
                            "  lower_inner: (Modern: boxers, panties | Medieval: smallclothes, loincloth) [Usually not empty]\n"
                            "  left_foot_inner/right_foot_inner: (Modern: socks | Medieval: wool socks, foot wraps) [Often empty]\n"
                            "  left_foot_outer/right_foot_outer: (Modern: sneakers, boots | Medieval: leather boots, sandals) [Usually not empty]\n"
                            "\n\n"
                            "Do NOT include hairstyles. Provide minimal visual description. Ensure all listed keys are present."
                            "\n\n"
                            "Output ONLY the JSON object:\n"
                            "Example Output Format (using full key names):\n"
                            "{\n"
                            "  \"head\": \"worn leather cap\",\n"
                            "  \"neck\": \"\",\n"
                            "  \"left_shoulder\": \"\",\n"
                            "  \"right_shoulder\": \"heavy backpack strap\",\n"
                            "  \"left_hand\": \"leather glove, iron ring\",\n"
                            "  \"right_hand\": \"worn bracer\",\n"
                            "  ... (include all other keys using full names like left_foot_outer) ...\n"
                            "}\n"
                            "\n"
                            "Equipment JSON:"
                        )
                    else:
                        prompt = f"Given the following information about a character named {character_name}, generate a detailed {field} for this character. Output plain text only, no markdown formatting.\n\nCurrent Character Sheet:\n{context}\n\n{field.title()}:"
                    if retry_count > 0:
                        if field == 'equipment':
                            prompt += f"\n\nThis is retry #{retry_count}. Please ensure your response is a valid JSON object with ALL required keys!"
                        else:
                            prompt += f"\n\nThis is retry #{retry_count}. Please ensure your response is not empty!"

                    print(f"  >> Calling make_inference for field: {field}")
                    llm_response = make_inference(
                        context=[{"role": "user", "content": prompt}],
                        user_message=prompt,
                        character_name=character_name,
                        url_type=url_type,
                        max_tokens=512 if field == 'equipment' else 256,
                        temperature=0.7,
                        is_utility_call=True
                    )
                    print(f"  >> make_inference returned for field {field}: {llm_response[:100]}...")
                    if field == 'equipment':
                        import json, re
                        try:
                            equipment_dict = json.loads(llm_response)
                            required_keys = EQUIPMENT_JSON_KEYS
                            missing_keys = [key for key in required_keys if key not in equipment_dict]
                            if missing_keys:
                                retry_count += 1
                                continue
                            generated_data[field] = equipment_dict
                            self.actor_data[field] = equipment_dict
                            success = True
                        except Exception:
                            match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', llm_response, re.IGNORECASE)
                            if match:
                                json_str = match.group(1)
                                try:
                                    equipment_dict = json.loads(json_str)
                                    required_keys = EQUIPMENT_JSON_KEYS
                                    missing_keys = [key for key in required_keys if key not in equipment_dict]
                                    if missing_keys:
                                        retry_count += 1
                                        continue
                                    generated_data[field] = equipment_dict
                                    self.actor_data[field] = equipment_dict
                                    success = True
                                except Exception:
                                    retry_count += 1
                            else:
                                retry_count += 1
                    else:
                        if llm_response.strip():
                            generated_data[field] = llm_response
                            self.actor_data[field] = llm_response
                            if field == 'name' and llm_response.strip():
                                character_name = llm_response.strip()
                                self.actor_data['name'] = character_name
                            success = True
                        else:
                            retry_count += 1
                if not success:
                    if field == 'equipment':
                        generated_data[field] = {key: "" for key in EQUIPMENT_JSON_KEYS}
                        self.actor_data[field] = generated_data[field]
                    else:
                        generated_data[field] = f"[No {field} could be generated]"
                        self.actor_data[field] = generated_data[field]
            print(f"  >> Generation complete, emitting signal with data: {list(generated_data.keys())}")
            if self._is_running:
                self.generation_complete.emit(generated_data)
        except Exception as e:
            error_message = f"Error during actor generation: {e}"
            print(f"  >> Generation error: {error_message}")
            if self._is_running:
                self.generation_error.emit(error_message)

    def _prepare_context(self, field_to_exclude: str = None) -> str:
        print(f"  >> _prepare_context called with field_to_exclude: {field_to_exclude}")
        print(f"  >> Current actor_data: {self.actor_data}")
        
        context_parts = []
        name = self.actor_data.get('name', '').strip()
        if name:
            context_parts.append(f"Name: {name}")
        left_holding = self.actor_data.get('left_hand_holding', '').strip()
        right_holding = self.actor_data.get('right_hand_holding', '').strip()
        if left_holding:
            context_parts.append(f"Left Hand Holding: {left_holding}")
        if right_holding:
            context_parts.append(f"Right Hand Holding: {right_holding}")
        for field_name, field_value in self.actor_data.items():
            if field_name in ['name', 'left_hand_holding', 'right_hand_holding']:
                continue
            if field_name == field_to_exclude:
                continue
            if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                continue
            else:
                if isinstance(field_value, dict):
                    import json
                    formatted_value = json.dumps(field_value, indent=2)
                    context_parts.append(f"{field_name.replace('_', ' ').title()}:\n{formatted_value}")
                elif isinstance(field_value, list):
                    if field_value:
                        formatted_items = '\n'.join([f"  - {item}" for item in field_value])
                        context_parts.append(f"{field_name.replace('_', ' ').title()}:\n{formatted_items}")
                else:
                    context_parts.append(f"{field_name.replace('_', ' ').title()}: {field_value}")
        
        final_context = "\n\n".join(context_parts)
        print(f"  >> Final context for field '{field_to_exclude}':\n{final_context}")
        return final_context
    def stop(self):
        self._is_running = False


def generate_actor_fields_async(actor_data: ActorData, fields_to_generate: list[str], model_override=None, additional_instructions=None):
    print(f"  >> generate_actor_fields_async called with fields: {fields_to_generate}")
    valid_fields = [f for f in fields_to_generate if f in GENERATABLE_FIELDS]
    if not valid_fields:
        print(f"Error: No valid fields specified for generation. Requested: {fields_to_generate}, Valid: {GENERATABLE_FIELDS}")
        return None
    thread = QThread()
    worker = ActorGenerationWorker(actor_data, valid_fields, model_override=model_override, additional_instructions=additional_instructions)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    thread.start()
    return thread, worker

def create_generate_actor_widget(parent=None):
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    label = QLabel('Actor Prompt:')
    input_field = QLineEdit()
    input_field.setObjectName('ActorPromptInput')
    input_field.setText('Create a new NPC: a mysterious merchant with a secret.')
    layout.addWidget(label)
    layout.addWidget(input_field)
    widget.setLayout(layout)
    return widget

def sanitize_path_name(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\. ]', '', name).strip()
    sanitized = sanitized.replace(' ', '_').lower()
    return sanitized or 'untitled'

def _save_json_from_gen(file_path, data):
    if not file_path:
        print("GenerateActor: Error - Cannot save JSON, no file path provided.")
        return False
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except (IOError, OSError) as e:
        print(f"GenerateActor: Error writing JSON to {file_path}: {e}")
        return False
    except Exception as e:
        print(f"GenerateActor: Unexpected error writing JSON to {file_path}: {e}")
        return False

def _load_json_from_gen(file_path):
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
        print(f"GenerateActor: Error reading JSON from {file_path}: {e}")
        return {}
    except Exception as e:
        print(f"GenerateActor: Unexpected error reading JSON from {file_path}: {e}")
        return {}
_generation_threads = {}

def _handle_generation_complete_from_rule(generated_data, workflow_data_dir, location):
    actor_name = generated_data.get('name', 'Unnamed Actor').strip()
    if not actor_name:
        actor_name = "Unnamed Actor"
    final_actor_data = {**generated_data}
    final_actor_data['name'] = actor_name
    final_actor_data['isPlayer'] = False
    for key in ['description', 'personality', 'appearance', 'status', 'goals', 'story', 'abilities', 'location', 'left_hand_holding', 'right_hand_holding']:
        final_actor_data.setdefault(key, "")
    final_actor_data.setdefault('relations', {})
    equip_data = final_actor_data.get('equipment')
    if not isinstance(equip_data, dict):
        equip_data = {}
    final_equipment = {slot: equip_data.get(slot, "") for slot in EQUIPMENT_JSON_KEYS}
    final_actor_data['equipment'] = final_equipment
    session_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    if not os.path.isdir(session_actors_dir):
        os.makedirs(session_actors_dir, exist_ok=True)
    actors_dir = session_actors_dir
    base_filename = sanitize_path_name(actor_name)
    save_path = os.path.join(actors_dir, f"{base_filename}.json")
    counter = 1
    while os.path.exists(save_path):
        save_path = os.path.join(actors_dir, f"{base_filename}_{counter}.json")
        counter += 1
    if _save_json_from_gen(save_path, final_actor_data):
        print(f"Successfully saved generated actor '{actor_name}' to {save_path}")
    else:
        print(f"ERROR: Failed to save generated actor '{actor_name}' to {save_path}")
    if location and actor_name != "Unnamed Actor":
        print(f"  Attempting to add '{actor_name}' to setting named '{location}'")
        session_settings_base_dir = os.path.join(workflow_data_dir, 'game', 'settings')
        base_settings_base_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
        def find_setting_file(settings_dir, setting_name):
            for root, dirs, files in os.walk(settings_dir):
                dirs[:] = [d for d in dirs if d.lower() != 'saves']
                for filename in files:
                    if filename.lower().endswith('_setting.json'):
                        file_path = os.path.join(root, filename)
                        setting_data = _load_json_from_gen(file_path)
                        current_setting_name = setting_data.get('name', '').strip()
                        if current_setting_name.lower() == setting_name.strip().lower():
                            return file_path, setting_data
            return None, None
        session_file, session_data = find_setting_file(session_settings_base_dir, location)
        if session_file:
            print(f"    Found session setting file: {session_file}")
            target_file = session_file
            target_data = session_data
        else:
            base_file, base_data = find_setting_file(base_settings_base_dir, location)
            if base_file:
                rel_path = os.path.relpath(base_file, base_settings_base_dir)
                session_file = os.path.join(session_settings_base_dir, rel_path)
                os.makedirs(os.path.dirname(session_file), exist_ok=True)
                import shutil
                shutil.copy2(base_file, session_file)
                target_file = session_file
                target_data = _load_json_from_gen(session_file)
            else:
                print(f"    ERROR: Could not find setting file for '{location}' in either session or base dir.")
                target_file = None
                target_data = None
        if target_file and target_data is not None:
            characters = target_data.get('characters', [])
            if not isinstance(characters, list):
                characters = []
            if actor_name not in characters:
                characters.append(actor_name)
                target_data['characters'] = characters
        try:
            from core.utils import reload_actors_for_setting
            reload_actors_for_setting(workflow_data_dir, location)
        except Exception as e:
            print(f"[WARN] Could not reload actors for setting '{location}': {e}")

def _handle_generation_error_from_rule(error_message):
    print(f"GenerateActor: Error during generation: {error_message}")
    current_thread = QThread.currentThread()
    for thread_id, (thread, worker) in list(_generation_threads.items()):
        if thread == current_thread:
            del _generation_threads[thread_id]
            break

def trigger_actor_generation_from_rule(instructions, location, workflow_data_dir):
    initial_actor_data = {'location': location or ""}
    fields_to_generate = GENERATABLE_FIELDS
    result = generate_actor_fields_async(
        initial_actor_data,
        fields_to_generate,
        additional_instructions=instructions if instructions else None
    )
    if result:
        thread, worker = result
        thread_id = id(thread)
        _generation_threads[thread_id] = (thread, worker)
        worker.generation_complete.connect(lambda data, loc=location: _handle_generation_complete_from_rule(data, workflow_data_dir, loc))
        worker.generation_error.connect(_handle_generation_error_from_rule)
        worker.generation_complete.connect(thread.quit)
        worker.generation_error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)

def trigger_actor_creation_from_rule(fields_to_generate, instructions, location, workflow_data_dir, target_directory='Game', model_override=None):
    print(f"  >> trigger_actor_creation_from_rule called with fields: {fields_to_generate}")
    if not fields_to_generate:
        fields_to_generate = GENERATABLE_FIELDS.copy()
        valid_fields = [f for f in fields_to_generate if f in GENERATABLE_FIELDS]
        if not valid_fields:
            print(f"  >> No valid fields found, returning")
            return
        fields_to_generate = valid_fields
    initial_actor_data = {'location': location or ""}
    print(f"  >> Calling generate_actor_fields_async with fields: {fields_to_generate}")
    result = generate_actor_fields_async(
        initial_actor_data,
        fields_to_generate,
        model_override=model_override,
        additional_instructions=instructions if instructions else None
    )
    if result:
        thread, worker = result
        thread_id = id(thread)
        print(f"  >> Character generation started with thread_id: {thread_id}")
        _generation_threads[thread_id] = (thread, worker)
        worker.generation_complete.connect(
            lambda data, loc=location, target_dir=target_directory: 
            _handle_enhanced_creation_complete(data, workflow_data_dir, loc, target_dir)
        )
        worker.generation_error.connect(_handle_generation_error_from_rule)
        worker.generation_complete.connect(thread.quit)
        worker.generation_error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)


def trigger_actor_edit_from_rule(target_actor_name, fields_to_generate, instructions, location, workflow_data_dir, target_directory='Game', model_override=None):
    if not target_actor_name:
        print("  ERROR: No target actor name provided for editing.")
        return
    if not fields_to_generate:
        print("  ERROR: No fields specified for editing. Please specify which fields to regenerate.")
        return
    valid_fields = [f for f in fields_to_generate if f in GENERATABLE_FIELDS]
    if not valid_fields:
        print(f"  ERROR: No valid fields in request: {fields_to_generate}. Valid fields: {GENERATABLE_FIELDS}")
        return
    fields_to_generate = valid_fields
    actor_file_path = _find_existing_actor_file(target_actor_name, workflow_data_dir, target_directory)
    if not actor_file_path:
        print(f"  ERROR: Could not find actor '{target_actor_name}' in {target_directory} directory.")
        return
    existing_data = _load_json_from_gen(actor_file_path)
    if not existing_data:
        print(f"  ERROR: Could not load data for actor '{target_actor_name}' from {actor_file_path}.")
        return
    if location and 'location' in fields_to_generate:
        existing_data['location'] = location
    result = generate_actor_fields_async(
        existing_data,
        fields_to_generate,
        model_override=model_override,
        additional_instructions=instructions if instructions else None
    )
    if result:
        thread, worker = result
        thread_id = id(thread)
        _generation_threads[thread_id] = (thread, worker)
        worker.generation_complete.connect(
            lambda data, actor_path=actor_file_path, loc=location, target_dir=target_directory: 
            _handle_enhanced_edit_complete(data, actor_path, workflow_data_dir, loc, target_dir)
        )
        worker.generation_error.connect(_handle_generation_error_from_rule)
        worker.generation_complete.connect(thread.quit)
        worker.generation_error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)

def _find_existing_actor_file(actor_name, workflow_data_dir, target_directory):
    if target_directory == 'Game':
        search_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    else:
        search_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if not os.path.isdir(search_dir):
        return None
    sanitized_name = sanitize_path_name(actor_name)
    exact_path = os.path.join(search_dir, f"{sanitized_name}.json")
    if os.path.exists(exact_path):
        data = _load_json_from_gen(exact_path)
        if data:
            return exact_path
    for filename in os.listdir(search_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(search_dir, filename)
            data = _load_json_from_gen(file_path)
            if data and data.get('name', '').lower() == actor_name.lower():
                return file_path
    return None


def _handle_enhanced_creation_complete(generated_data, workflow_data_dir, location, target_directory):
    print(f"  >> _handle_enhanced_creation_complete called with actor: {generated_data.get('name', 'Unnamed Actor')}")
    actor_name = generated_data.get('name', 'Unnamed Actor').strip()
    if not actor_name:
        actor_name = "Unnamed Actor"
    final_actor_data = {**generated_data}
    final_actor_data['name'] = actor_name
    final_actor_data['isPlayer'] = False
    for key in ['description', 'personality', 'appearance', 'status', 'goals', 'story', 'abilities', 'location', 'left_hand_holding', 'right_hand_holding']:
        final_actor_data.setdefault(key, "")
    final_actor_data.setdefault('relations', {})
    final_actor_data.setdefault('variables', {})
    equip_data = final_actor_data.get('equipment')
    if not isinstance(equip_data, dict):
        equip_data = {}
    final_equipment = {slot: equip_data.get(slot, "") for slot in EQUIPMENT_JSON_KEYS}
    final_actor_data['equipment'] = final_equipment
    if target_directory == 'Game':
        actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    else:
        actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if not os.path.isdir(actors_dir):
        os.makedirs(actors_dir, exist_ok=True)
    base_filename = sanitize_path_name(actor_name)
    save_path = os.path.join(actors_dir, f"{base_filename}.json")
    counter = 1
    while os.path.exists(save_path):
        save_path = os.path.join(actors_dir, f"{base_filename}_{counter}.json")
        counter += 1
    print(f"  >> Saving character to: {save_path}")
    if _save_json_from_gen(save_path, final_actor_data):
        print(f"  >> Successfully saved character '{actor_name}' to {save_path}")
    else:
        print(f"  >> ERROR: Failed to save character '{actor_name}' to {save_path}")
    
    current_thread = QThread.currentThread()
    for thread_id, (thread, worker) in list(_generation_threads.items()):
        if thread == current_thread:
            del _generation_threads[thread_id]
            break
    if location and actor_name != "Unnamed Actor":
        _add_actor_to_setting(actor_name, location, workflow_data_dir)


def _handle_enhanced_edit_complete(generated_data, actor_file_path, workflow_data_dir, location, target_directory):
    
    existing_data = _load_json_from_gen(actor_file_path)
    if not existing_data:
        print(f"ERROR: Could not reload existing data from {actor_file_path}")
        return
    for field, value in generated_data.items():
        existing_data[field] = value
    
    if not _save_json_from_gen(actor_file_path, existing_data):
        print(f"ERROR: Failed to save updated character data to {actor_file_path}")
        return
    
    old_location = existing_data.get('location', '')
    if 'location' in generated_data:
        new_location = generated_data['location']
        if old_location != new_location:
            actor_name = existing_data.get('name', '')
            if actor_name:
                if old_location:
                    _remove_actor_from_setting(actor_name, old_location, workflow_data_dir)
                if new_location:
                    _add_actor_to_setting(actor_name, new_location, workflow_data_dir)
    current_thread = QThread.currentThread()
    for thread_id, (thread, worker) in list(_generation_threads.items()):
        if thread == current_thread:
            del _generation_threads[thread_id]
            break


def _add_actor_to_setting(actor_name, location, workflow_data_dir):
    session_settings_base_dir = os.path.join(workflow_data_dir, 'game', 'settings')
    base_settings_base_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    def find_setting_file(settings_dir, setting_name):
        for root, dirs, files in os.walk(settings_dir):
            dirs[:] = [d for d in dirs if d.lower() != 'saves']
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    file_path = os.path.join(root, filename)
                    setting_data = _load_json_from_gen(file_path)
                    current_setting_name = setting_data.get('name', '').strip()
                    if current_setting_name.lower() == setting_name.strip().lower():
                        return file_path, setting_data
        return None, None
    session_file, session_data = find_setting_file(session_settings_base_dir, location)
    if session_file:
        target_file = session_file
        target_data = session_data
    else:
        base_file, base_data = find_setting_file(base_settings_base_dir, location)
        if base_file:
            rel_path = os.path.relpath(base_file, base_settings_base_dir)
            session_file = os.path.join(session_settings_base_dir, rel_path)
            os.makedirs(os.path.dirname(session_file), exist_ok=True)
            import shutil
            shutil.copy2(base_file, session_file)
            target_file = session_file
            target_data = _load_json_from_gen(session_file)
        else:
            target_file = None
            target_data = None
    if target_file and target_data is not None:
        characters = target_data.get('characters', [])
        if not isinstance(characters, list):
            print(f"      Warning: 'characters' field in {target_file} is not a list. Resetting.")
            characters = []
        if actor_name not in characters:
            characters.append(actor_name)
            target_data['characters'] = characters
            if not _save_json_from_gen(target_file, target_data):
                print(f"      ERROR: Failed to save updated characters list to '{target_file}'")
        try:
            from core.utils import reload_actors_for_setting
            reload_actors_for_setting(workflow_data_dir, location)
        except Exception as e:
            print(f"[WARN] Could not reload actors for setting '{location}': {e}")


def _remove_actor_from_setting(actor_name, location, workflow_data_dir):
    session_settings_base_dir = os.path.join(workflow_data_dir, 'game', 'settings')
    base_settings_base_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    def find_setting_file(settings_dir, setting_name):
        for root, dirs, files in os.walk(settings_dir):
            dirs[:] = [d for d in dirs if d.lower() != 'saves']
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    file_path = os.path.join(root, filename)
                    setting_data = _load_json_from_gen(file_path)
                    current_setting_name = setting_data.get('name', '').strip()
                    if current_setting_name.lower() == setting_name.strip().lower():
                        return file_path, setting_data
        return None, None
    for settings_dir in [session_settings_base_dir, base_settings_base_dir]:
        setting_file, setting_data = find_setting_file(settings_dir, location)
        if setting_file and setting_data:
            characters = setting_data.get('characters', [])
            if isinstance(characters, list) and actor_name in characters:
                characters.remove(actor_name)
                setting_data['characters'] = characters
                if _save_json_from_gen(setting_file, setting_data):
                    return
            break
