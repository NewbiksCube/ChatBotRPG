from PyQt5.QtCore import QTimer
import json
import os
import random
import time
from core.utils import _get_player_current_setting_name, _get_or_create_actor_data, _find_player_character_file, _load_json_safely, _find_setting_file_prioritizing_game_dir, _get_player_character_name, _find_actor_file_path
from editor_panel.inventory_manager import generate_item_id
import re

def _apply_string_operation_mode(prev_value, new_value, set_var_mode, delimiter="/"):
    if isinstance(prev_value, (int, float)) and isinstance(new_value, (int, float)):
        return new_value
    if set_var_mode == 'prepend' and prev_value is not None:
        use_delimiter = delimiter if prev_value and new_value else ""
        return str(new_value) + use_delimiter + str(prev_value)
    elif set_var_mode == 'append' and prev_value is not None:
        use_delimiter = delimiter if prev_value and new_value else ""
        return str(prev_value) + use_delimiter + str(new_value)
    else:
        return new_value

def smart_convert_variable_value(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        value_stripped = value.strip()
        if value_stripped == "":
            return value_stripped
        try:
            if '.' not in value_stripped and value_stripped.lstrip('-').isdigit():
                return int(value_stripped)
            try:
                float_val = float(value_stripped)
                if float_val.is_integer():
                    return int(float_val)
                return float_val
            except ValueError:
                return value_stripped
        except (ValueError, TypeError) as e:
            return value_stripped
    return value

def _find_item_by_name_or_id(inventory, item_identifier):
    if not inventory:
        return None, -1
    for i, item in enumerate(inventory):
        if not isinstance(item, dict):
            continue
        if item_identifier.lower().startswith('item_') and item.get('item_id', '').lower() == item_identifier.lower():
            return item, i
        if item.get('name') == item_identifier:
            return item, i
    return None, -1

def _find_item_in_container_recursive(inventory, item_identifier, container_path=None):
    if not inventory:
        return None, None
    for item in inventory:
        if not isinstance(item, dict):
            continue
        if (item_identifier.startswith('item_') and item.get('item_id') == item_identifier) or \
           item.get('name') == item_identifier:
            return item, container_path
        containers = item.get('containers', {})
        for container_name, container_items in containers.items():
            current_path = container_path or []
            new_path = current_path + [(item.get('name', ''), container_name)]
            result, result_path = _find_item_in_container_recursive(container_items, item_identifier, new_path)
            if result:
                return result, result_path
    return None, None

def _add_item_to_container(inventory, target_item_identifier, container_name, new_item):
    target_item, _ = _find_item_by_name_or_id(inventory, target_item_identifier)
    if not target_item:
        return False
    containers = target_item.get('containers', {})
    if container_name not in containers:
        return False
    containers[container_name].append(new_item)
    return True

def _remove_item_from_container(inventory, target_item_identifier, container_name, item_name, quantity=1):
    target_item, _ = _find_item_by_name_or_id(inventory, target_item_identifier)
    if not target_item:
        return 0
    containers = target_item.get('containers', {})
    if container_name not in containers:
        return 0
    container_items = containers[container_name]
    removed_count = 0
    items_to_remove = quantity
    for i in range(len(container_items) - 1, -1, -1):
        item = container_items[i]
        if item.get('name') == item_name:
            current_quantity = item.get('quantity', 1)
            if current_quantity <= items_to_remove:
                removed_count += current_quantity
                container_items.pop(i)
                items_to_remove -= current_quantity
            else:
                item['quantity'] = current_quantity - items_to_remove
                removed_count += items_to_remove
                items_to_remove = 0
            if items_to_remove <= 0:
                break
    return removed_count

def _move_item_between_containers(inventory, from_item_identifier, from_container_name, 
                                 to_item_identifier, to_container_name, item_name, quantity=1):
    removed_count = _remove_item_from_container(inventory, from_item_identifier, from_container_name, item_name, quantity)
    if removed_count == 0:
        return 0
    new_item = {
        'item_id': f"item_{generate_item_id()}",
        'name': item_name,
        'quantity': removed_count,
        'owner': '',
        'description': '',
        'location': '',
        'containers': {}
    }
    success = _add_item_to_container(inventory, to_item_identifier, to_container_name, new_item)
    if not success:
        _add_item_to_container(inventory, from_item_identifier, from_container_name, new_item)
        return 0
    return removed_count

def _apply_rule_side_effects(self, obj, rule, character_name=None, current_user_msg=None, prev_assistant_msg=None):
    from rules.rule_evaluator import _process_specific_rule
    tab_data = self.get_current_tab_data()
    if not tab_data:
        print("Error: No tab data available for rule side effects.")
        return
    obj_type = obj.get('type', '')
    if obj_type == 'Generate Random List':
        var_format = obj.get('var_format', 'comma')
        var_format_separator = obj.get('var_format_separator', ' ')
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot generate random list - workflow_data_dir not found")
            return
        instructions = obj.get('instructions', '')
        print(f"DEBUG: Original instructions before substitution: '{instructions}'")
        instructions = _substitute_variables_in_string(instructions, tab_data, character_name)
        print(f"DEBUG: Instructions after substitution: '{instructions}'")
        generator_name = obj.get('generator_name', '')
        generator_name = _substitute_variables_in_string(generator_name, tab_data, character_name)
        is_permutate = obj.get('is_permutate', False)
        model_override = obj.get('model_override', None)
        generate_context = obj.get('generate_context', 'No Context')
        print(f"DEBUG: Generate Random List - generate_context = '{generate_context}'")
        print(f"DEBUG: Original instructions = '{instructions}'")
        if generate_context != 'No Context':
            context_text = ""
            if generate_context == 'Last Exchange':
                context_text = self.get_current_context()
                print(f"DEBUG: Last Exchange context retrieved: '{context_text}'")
            elif generate_context == 'User Message':
                current_context = self.get_current_context()
                print(f"DEBUG: Current context for User Message: '{current_context}'")
                if current_context:
                    lines = current_context.strip().split('\n')
                    user_lines = [line for line in lines if line.startswith('User:')]
                    if user_lines:
                        context_text = user_lines[-1]
                        print(f"DEBUG: Extracted user message: '{context_text}'")
            elif generate_context == 'Full Conversation':
                context_text = self.get_current_context()
                print(f"DEBUG: Full Conversation context retrieved: '{context_text}'")
            if context_text:
                instructions = f"""CONVERSATION CONTEXT:
{context_text}

INSTRUCTIONS:
{instructions}"""
                print(f"DEBUG: Final instructions with context: '{instructions}'")
            else:
                print(f"DEBUG: No context text was retrieved, using original instructions")
        else:
            print(f"DEBUG: No context requested, using original instructions")
        permutate_objects = obj.get('permutate_objects', False)
        permutate_weights = obj.get('permutate_weights', False)
        var_name = obj.get('var_name', '')
        var_scope = obj.get('var_scope', 'Global')
        generator_json_path = None
        if is_permutate and generator_name:
            from rules.rule_evaluator import _find_generator_file
            generator_json_path = _find_generator_file(generator_name, workflow_data_dir)
            if not generator_json_path:
                print(f"WARNING: Could not find generator '{generator_name}' for permutation")
        resource_folder = os.path.join(workflow_data_dir, 'resources', 'generators')
        game_folder = os.path.join(workflow_data_dir, 'game', 'generators')
        os.makedirs(game_folder, exist_ok=True)
        os.makedirs(resource_folder, exist_ok=True)
        from generate.generate_random_list import generate_random_list
        result = generate_random_list(
            instructions=instructions,
            is_permutate=is_permutate,
            use_resource=False,
            permutate_objects=permutate_objects,
            permutate_weights=permutate_weights,
            generator_json_path=generator_json_path,
            resource_folder=resource_folder,
            game_folder=game_folder,
            model_override=model_override,
            generator_name=generator_name
        )
        if var_name and var_scope:
            generator_file_path = None
            sample_result = None
            if isinstance(result, dict) and "file_path" in result:
                generator_file_path = result.get("file_path")
            elif isinstance(result, str) and "Created" in result:
                import re
                generator_name_match = re.search(r"'([^']+)'", result)
                if generator_name_match:
                    found_name = generator_name_match.group(1)
                    for filename in os.listdir(game_folder):
                        if filename.lower().endswith('.json'):
                            try:
                                file_path = os.path.join(game_folder, filename)
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    gen_data = json.load(f)
                                    if gen_data.get('name') == found_name:
                                        generator_file_path = file_path
                                        break
                            except Exception as e:
                                print(f"Error checking generator file {filename}: {e}")
            if generator_file_path and os.path.exists(generator_file_path):
                try:
                    with open(generator_file_path, 'r', encoding='utf-8') as f:
                        generator_data = json.load(f)
                    sampled_values = []
                    if "tables" in generator_data and isinstance(generator_data["tables"], list):
                        for table in generator_data["tables"]:
                            if "items" in table and isinstance(table["items"], list) and table["items"]:
                                generate_items = [item for item in table["items"] if item.get("generate", True)]
                                if generate_items:
                                    total_weight = sum(item.get("weight", 1) for item in generate_items)
                                    rand_value = random.randint(1, total_weight)
                                    current_weight = 0
                                    selected_item = None
                                    for item in generate_items:
                                        current_weight += item.get("weight", 1)
                                        if rand_value <= current_weight:
                                            selected_item = item
                                            break
                                    if selected_item:
                                        sampled_values.append(selected_item.get("name", ""))
                    if sampled_values:
                        try:
                            if var_format == 'comma':
                                sample_result = ", ".join(sampled_values)
                            elif var_format == 'space':
                                sample_result = " ".join(sampled_values)
                            elif var_format == 'custom':
                                sample_result = var_format_separator.join(sampled_values)
                            else:
                                sample_result = ", ".join(sampled_values)
                        except NameError:
                            sample_result = ", ".join(sampled_values)
                        print(f"  >> Generated Random List: Sampled values from {len(generator_data.get('tables', []))} tables: {sampled_values}")
                        print(f"  >> Using format: {var_format} (separator: '{var_format_separator}')")
                        print(f"  >> Final result: {sample_result}")
                    else:
                        sample_result = f"Error: No items found in generator {generator_data.get('name', 'Unknown')}"
                except Exception as e:
                    print(f"Error sampling from generator: {e}")
                    sample_result = f"Error sampling from generator: {e}"
            else:
                sample_result = f"Error: Could not find generator file to sample from. Result: {result}"
            store_value = sample_result if sample_result is not None else str(result)
            var_mode = obj.get('var_mode', 'replace')
            var_delimiter = obj.get('var_delimiter', '/')
            
            if var_scope == 'Global':
                variables_file = tab_data.get('variables_file')
                if variables_file:
                    variables = {}
                    if os.path.exists(variables_file):
                        try:
                            with open(variables_file, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                if content:
                                    variables = json.loads(content)
                        except Exception as e:
                            print(f"Error loading variables file: {e}")
                    
                    prev_value = variables.get(var_name, "")
                    if var_mode == 'replace':
                        variables[var_name] = store_value
                    elif var_mode == 'prepend':
                        variables[var_name] = f"{store_value}{var_delimiter}{prev_value}" if prev_value else store_value
                    elif var_mode == 'append':
                        variables[var_name] = f"{prev_value}{var_delimiter}{store_value}" if prev_value else store_value
                    try:
                        with open(variables_file, 'w', encoding='utf-8') as f:
                            json.dump(variables, f, indent=2, ensure_ascii=False)
                        print(f"Successfully stored sampled result in global variable: {var_name}")
                    except Exception as e:
                        print(f"Error saving variables file: {e}")
                else:
                    print(f"ERROR: Cannot store global variable - variables_file not found in tab_data")
            
            elif var_scope == 'Character':
                if not character_name:
                    print(f"ERROR: variable_scope is 'Character' but character_name is missing. Cannot store variable.")
                else:
                    actor_data, actor_path = _get_or_create_actor_data(self, workflow_data_dir, character_name)
                    if actor_data:
                        if 'variables' not in actor_data:
                            actor_data['variables'] = {}
                        prev_value = actor_data['variables'].get(var_name, "")
                        if var_mode == 'replace':
                            actor_data['variables'][var_name] = store_value
                        elif var_mode == 'prepend':
                            actor_data['variables'][var_name] = f"{store_value}{var_delimiter}{prev_value}" if prev_value else store_value
                        elif var_mode == 'append':
                            actor_data['variables'][var_name] = f"{prev_value}{var_delimiter}{store_value}" if prev_value else store_value
                        
                        try:
                            with open(actor_path, 'w', encoding='utf-8') as f:
                                json.dump(actor_data, f, indent=2, ensure_ascii=False)
                                f.flush()
                                os.fsync(f.fileno())
                            print(f"Successfully stored sampled result in character variable: {var_name} for {character_name}")
                        except Exception as e:
                            print(f"Error saving character data: {e}")
                    else:
                        print(f"ERROR: Could not load character data for {character_name}")
            
            elif var_scope == 'Player':
        
                workflow_data_dir = tab_data.get('workflow_data_dir')
                if not workflow_data_dir:
                    print(f"ERROR: Cannot set player variable - workflow_data_dir not found")
                    return
                game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
                player_file = None
                player_name = None
                if os.path.exists(game_actors_dir):
                    for filename in os.listdir(game_actors_dir):
                        if filename.lower().endswith('.json'):
                            file_path = os.path.join(game_actors_dir, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    actor_data = json.load(f)
                                    if actor_data.get('is_player', False) or actor_data.get('isPlayer', False):
                                        player_file = file_path
                                        player_name = actor_data.get('name', 'Player')
                                        break
                            except Exception as e:
                                print(f"Error reading potential player file {file_path}: {e}")
                if not player_file:
                    base_player_file, base_player_name = _find_player_character_file(workflow_data_dir)
                    if base_player_file and base_player_name:
                        os.makedirs(game_actors_dir, exist_ok=True)
                        import shutil
                        player_filename = os.path.basename(base_player_file)
                        player_file = os.path.join(game_actors_dir, player_filename)
                        player_name = base_player_name
                        
                        try:
                            shutil.copy2(base_player_file, player_file)
                            print(f"Copied player file from base to game directory: {player_name} ({player_file})")
                        except Exception as e:
                            print(f"ERROR: Failed to copy player file to game directory: {e}")
                            return
                    else:
                        print(f"ERROR: Could not find player character file with isPlayer=True")
                        return
                try:
                    with open(player_file, 'r', encoding='utf-8') as f:
                        player_data = json.load(f)
                    if 'variables' not in player_data:
                        player_data['variables'] = {}
                    prev_value = player_data['variables'].get(var_name, "")
                    if var_mode == 'replace':
                        player_data['variables'][var_name] = store_value
                    elif var_mode == 'prepend':
                        player_data['variables'][var_name] = f"{store_value}{var_delimiter}{prev_value}" if prev_value else store_value
                    elif var_mode == 'append':
                        player_data['variables'][var_name] = f"{prev_value}{var_delimiter}{store_value}" if prev_value else store_value
                    with open(player_file, 'w', encoding='utf-8') as f:
                        json.dump(player_data, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                    print(f"Successfully stored sampled result in player variable: {var_name}")
                except Exception as e:
                    print(f"Error updating player data: {e}")
            
            elif var_scope == 'Setting':
                current_setting = _get_player_current_setting_name(workflow_data_dir)
                if current_setting:
                    setting_file = _find_setting_file_prioritizing_game_dir(workflow_data_dir, current_setting)
                    if setting_file and os.path.exists(setting_file):
                        try:
                            with open(setting_file, 'r', encoding='utf-8') as f:
                                setting_data = json.load(f)
                            
                            if 'variables' not in setting_data:
                                setting_data['variables'] = {}
                            prev_value = setting_data['variables'].get(var_name, "")
                            if var_mode == 'replace':
                                setting_data['variables'][var_name] = store_value
                            elif var_mode == 'prepend':
                                setting_data['variables'][var_name] = f"{store_value}{var_delimiter}{prev_value}" if prev_value else store_value
                            elif var_mode == 'append':
                                setting_data['variables'][var_name] = f"{prev_value}{var_delimiter}{store_value}" if prev_value else store_value
                            with open(setting_file, 'w', encoding='utf-8') as f:
                                json.dump(setting_data, f, indent=2, ensure_ascii=False)
                                f.flush()
                                os.fsync(f.fileno())
                            print(f"Successfully stored sampled result in setting variable: {var_name} for {current_setting}")
                        except Exception as e:
                            print(f"Error updating setting data: {e}")
            
            elif var_scope == 'Scene Characters':
                if character_name:
                    actor_data, actor_path = _get_or_create_actor_data(self, workflow_data_dir, character_name)
                    if actor_data:
                        if 'variables' not in actor_data:
                            actor_data['variables'] = {}
                        prev_value = actor_data['variables'].get(var_name, "")
                        if var_mode == 'replace':
                            actor_data['variables'][var_name] = store_value
                        elif var_mode == 'prepend':
                            actor_data['variables'][var_name] = f"{store_value}{var_delimiter}{prev_value}" if prev_value else store_value
                        elif var_mode == 'append':
                            actor_data['variables'][var_name] = f"{prev_value}{var_delimiter}{store_value}" if prev_value else store_value
                        try:
                            with open(actor_path, 'w', encoding='utf-8') as f:
                                json.dump(actor_data, f, indent=2, ensure_ascii=False)
                                f.flush()
                                os.fsync(f.fileno())
                            print(f"Successfully stored sampled result in scene character variable: {var_name} for {character_name}")
                        except Exception as e:
                            print(f"Error saving character data for {character_name}: {e}")
                    else:
                        print(f"ERROR: Could not load character data for character {character_name}")
                    variables_file = tab_data.get('variables_file')
                    if variables_file:
                        variables = {}
                        if os.path.exists(variables_file):
                            try:
                                with open(variables_file, 'r', encoding='utf-8') as f:
                                    content = f.read().strip()
                                    if content:
                                        variables = json.loads(content)
                            except Exception as e:
                                print(f"Error loading variables file: {e}")
                        variables[var_name] = store_value
                        try:
                            with open(variables_file, 'w', encoding='utf-8') as f:
                                json.dump(variables, f, indent=2, ensure_ascii=False)
                            print(f"Successfully stored sampled result in global variable as fallback: {var_name}")
                        except Exception as e:
                            print(f"Error saving variables file: {e}")
        return
    if obj_type == 'Set Screen Effect':
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot set screen effect - workflow_data_dir not found")
            return
        effect_type = obj.get('effect_type', 'Blur')
        operation = obj.get('operation', 'set').lower()
        param_name = obj.get('param_name', '')
        param_value = obj.get('param_value', '')
        enabled = obj.get('enabled', True)
        if not param_name:
            print(f"ERROR: Cannot set screen effect - param_name is empty")
            return
        gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
        gamestate = {}
        if os.path.exists(gamestate_path):
            try:
                with open(gamestate_path, 'r', encoding='utf-8') as f:
                    gamestate = json.load(f)
            except Exception as e:
                print(f"Error loading gamestate.json for screen effects: {e}")
        if 'effects' not in gamestate:
            gamestate['effects'] = {}
        effect_key = effect_type.lower()
        if effect_type == "Darken/Brighten":
            effect_key = "darken_brighten"
        if effect_key not in gamestate['effects']:
            gamestate['effects'][effect_key] = {}
        effect_config = gamestate['effects'][effect_key]
        effect_config['enabled'] = enabled
        current_value = effect_config.get(param_name)
        new_value = param_value
        if param_name in ["animate", "enabled"]:
            if param_value.lower() in ["true", "yes", "1"]:
                new_value = True
            elif param_value.lower() in ["false", "no", "0"]:
                new_value = False
        else:
            try:
                if current_value is not None:
                    current_num = float(current_value)
                    try:
                        param_num = float(param_value)
                        if operation == "increment":
                            new_value = current_num + param_num
                        elif operation == "decrement":
                            new_value = current_num - param_num
                        elif operation == "set":
                            new_value = param_num
                        if isinstance(current_value, int) and new_value.is_integer():
                            new_value = int(new_value)
                    except ValueError:
                        new_value = param_value
                else:
                    try:
                        param_num = float(param_value)
                        if operation == "increment":
                            new_value = param_num
                        elif operation == "decrement":
                            new_value = -param_num
                        elif operation == "set":
                            new_value = param_num
                        if new_value.is_integer():
                            new_value = int(new_value)
                    except ValueError:
                        new_value = param_value
            except (ValueError, TypeError):
                new_value = param_value
        effect_config[param_name] = new_value
        try:
            with open(gamestate_path, 'w', encoding='utf-8') as f:
                json.dump(gamestate, f, indent=2)
            if tab_data:
                tab_data['_pending_screen_effect_update'] = True
                print(f"  Marked _pending_screen_effect_update = True in tab_data.")
            else:
                print(f"  WARNING: tab_data not available to mark _pending_screen_effect_update.")
        except Exception as e:
            print(f"Error saving gamestate.json: {e}")
    elif obj_type == 'system_message':
        message_text = _substitute_variables_in_string(obj.get('value', ''), tab_data, character_name)
        position = obj.get('position', 'prepend')
        sysmsg_position = obj.get('system_message_position', 'first')
        self._cot_system_modifications.append({
            'action': message_text,
            'position': position,
            'system_message_position': sysmsg_position,
            'switch_model': None
        })
    elif obj_type == 'switch_model':
        model_name = _substitute_variables_in_string(obj.get('value', ''), tab_data, character_name)
        self._cot_system_modifications.append({
            'action': '',
            'position': rule.get('position', 'prepend'),
            'system_message_position': rule.get('system_message_position', 'first'),
            'switch_model': model_name
        })
    elif obj_type == 'Set Var':
        var_name = obj.get('var_name', '')
        if not var_name:
            var_name = obj.get('variable', '')
        var_value = obj.get('var_value', '')
        if var_value == '' and 'value' in obj:
            var_value = obj.get('value', '')
        variable_scope = obj.get('variable_scope', 'Global')
        valid_scopes = ['Character', 'Global', 'Scene Characters', 'Setting', 'Player']
        if variable_scope not in valid_scopes:
            variable_scope = obj.get('var_scope', 'Global')
        operation = obj.get('operation', 'set').lower()
        if operation == 'from random list':
            gen_name = obj.get('random_list_generator', '')
            random_list_context = obj.get('random_list_context', 'No Context')
            workflow_data_dir = tab_data.get('workflow_data_dir')
            sample_result = None
            if workflow_data_dir and gen_name:
                if random_list_context != 'No Context':
                    context_text = ""
                    if random_list_context == 'Last Exchange':
                        context_text = self.get_current_context()
                    elif random_list_context == 'User Message':
                        current_context = self.get_current_context()
                        if current_context:
                            lines = current_context.strip().split('\n')
                            user_lines = [line for line in lines if line.startswith('User:')]
                            if user_lines:
                                context_text = user_lines[-1]
                    elif random_list_context == 'Full Conversation':
                        context_text = self.get_current_context()
                    try:
                        from generate.generate_random_list import generate_random_list
                        instructions_with_context = f"Based on the following conversation context, generate/permutate the random list '{gen_name}':\n\n{context_text}\n\nGenerate appropriate items for the list."
                        result = generate_random_list(
                            workflow_data_dir=workflow_data_dir,
                            generator_name=gen_name,
                            instructions=instructions_with_context,
                            is_permutate=True,
                            permutate_objects=True,
                            permutate_weights=True,
                            model_override=None
                        )
                        if result and result.get('success'):
                            gen_data = result.get('generator_data', {})
                            sampled = []
                            for table in gen_data.get('tables', []):
                                items = [it for it in table.get('items', []) if it.get('generate', True)]
                                if items:
                                    total = sum(it.get('weight', 1) for it in items)
                                    r = random.randint(1, total)
                                    c = 0
                                    for it in items:
                                        c += it.get('weight', 1)
                                        if r <= c:
                                            sampled.append(it.get('name', ''))
                                            break
                            sample_result = ", ".join(sampled) if sampled else f"Error: No items generated for '{gen_name}'"
                        else:
                            sample_result = f"Error generating list with context: {result.get('error', 'Unknown error')}"
                    except Exception as e:
                        sample_result = f"Error: Failed to generate list with context: {e}"
                else:
                    from rules.rule_evaluator import _find_generator_file
                    generator_json_path = _find_generator_file(gen_name, workflow_data_dir)
                    if generator_json_path:
                        try:
                            with open(generator_json_path, 'r', encoding='utf-8') as f:
                                gen_data = json.load(f)
                            sampled = []
                            for i, table in enumerate(gen_data.get('tables', [])):
                                items = [it for it in table.get('items', []) if it.get('generate', True)]
                                if items:
                                    total = sum(it.get('weight', 1) for it in items)
                                    r = random.randint(1, total)
                                    c = 0
                                    for it in items:
                                        c += it.get('weight', 1)
                                        if r <= c:
                                            selected_item = it.get('name', '')
                                            sampled.append(selected_item)
                                            break
                            sample_result = ", ".join(sampled) if sampled else f"Error: No items in generator '{gen_name}'"
                        except Exception as e:
                            sample_result = f"Error sampling from generator '{gen_name}': {e}"
                    else:
                        sample_result = f"Error: Generator '{gen_name}' not found"
            else:
                sample_result = f"Error: Missing workflow_data_dir or generator name"
            var_value = sample_result
            operation = 'set'
        if var_name:
            var_value_converted = smart_convert_variable_value(var_value)
            if operation == 'from var':
                from_var_name = obj.get('from_var_name', '')
                from_var_scope = obj.get('from_var_scope', 'Global')
                if not from_var_name:
                    return
                source_value = None
                if from_var_scope == 'Global':
                    variables_file = tab_data.get('variables_file')
                    if variables_file and os.path.exists(variables_file):
                        try:
                            with open(variables_file, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                                if content:
                                    global_variables = json.loads(content)
                                    if isinstance(global_variables, dict):
                                        source_value = global_variables.get(from_var_name)
                        except Exception as e:
                    
                            source_value = None
                    else:
                        source_value = None
                elif from_var_scope == 'Player':
                    workflow_data_dir = tab_data.get('workflow_data_dir')
                    if workflow_data_dir:
                        game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
                        player_file = None
                        if os.path.exists(game_actors_dir):
                            for filename in os.listdir(game_actors_dir):
                                if filename.lower().endswith('.json'):
                                    file_path = os.path.join(game_actors_dir, filename)
                                    try:
                                        with open(file_path, 'r', encoding='utf-8') as f:
                                            actor_data = json.load(f)
                                            if actor_data.get('is_player', False) or actor_data.get('isPlayer', False):
                                                player_file = file_path
                                                break
                                    except Exception as e:
                                        print(f"Error reading potential player file {file_path}: {e}")
                        if not player_file:
                            player_file, player_name = _find_player_character_file(workflow_data_dir)
                        
                        if player_file:
                            try:
                                with open(player_file, 'r', encoding='utf-8') as f:
                                    player_data = json.load(f)
                                source_value = player_data.get('variables', {}).get(from_var_name)
                            except Exception as e:
                        
                                source_value = None
                        else:
                            source_value = None
                    else:
                        source_value = None
                elif from_var_scope == 'Character' and character_name:
                    workflow_dir = tab_data.get('workflow_data_dir')
                    if workflow_dir:
                        actor_data, actor_path = _get_or_create_actor_data(self, workflow_dir, character_name)
                        source_value = actor_data.get('variables', {}).get(from_var_name)
                elif from_var_scope == 'Setting':
                    workflow_data_dir = tab_data.get('workflow_data_dir')
                    if workflow_data_dir:
                        player_setting_name = _get_player_current_setting_name(workflow_data_dir)
                        if player_setting_name and player_setting_name != "Unknown Setting":
                            session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
                            found_setting_file = None
                            for root, dirs, files in os.walk(session_settings_dir):
                                dirs[:] = [d for d in dirs if d.lower() != 'saves']
                                for filename in files:
                                    if filename.lower().endswith('_setting.json'):
                                        file_path = os.path.join(root, filename)
                                        setting_data = _load_json_safely(file_path)
                                        if setting_data and setting_data.get('name') == player_setting_name:
                                            source_value = setting_data.get('variables', {}).get(from_var_name)
                                            break
                                if source_value is not None:
                                    break
                elif from_var_scope == 'Scene Characters':
                    source_value = tab_data.get('scene_characters_variables', {}).get(from_var_name)
                if source_value is None:
                    source_value = ""
                var_value_converted = source_value
                operation = 'set'
            
            if variable_scope == 'Character':
                if not character_name:
                    print(f"ERROR: variable_scope is 'Character' but character_name is missing. Will NOT set global variable. Skipping.")
                    return
                workflow_data_dir = tab_data.get('workflow_data_dir')
                if not workflow_data_dir:
                    print(f"ERROR: Cannot set character variable - workflow_data_dir not found")
                    return
                actor_data, actor_path = _get_or_create_actor_data(self, workflow_data_dir, character_name)
        
                if not actor_data:
                    print(f"ERROR: Could not find or create actor data for '{character_name}'")
                    return
                if 'variables' not in actor_data:
                    actor_data['variables'] = {}
                elif not isinstance(actor_data.get('variables'), dict):
                    print(f"WARNING: 'variables' in actor data is not a dictionary. Resetting to empty dict.")
                    actor_data['variables'] = {}
                prev_value = actor_data['variables'].get(var_name)
                new_value = var_value_converted
                if operation == 'set':
                    set_var_mode = obj.get('set_var_mode', 'replace')
                    delimiter = obj.get('set_var_delimiter', '/')
                    new_value = _apply_string_operation_mode(prev_value, new_value, set_var_mode, delimiter)
                elif operation != 'set':
                    try:
                        prev_num = float(prev_value) if prev_value is not None else 0.0
                        arg_num = float(var_value_converted)
                        if operation == 'increment':
                            new_value = prev_num + arg_num
                        elif operation == 'decrement':
                            new_value = prev_num - arg_num
                        elif operation == 'multiply':
                            new_value = prev_num * arg_num
                        elif operation == 'divide':
                            new_value = prev_num / arg_num if arg_num != 0 else prev_num
                        if prev_value is not None and isinstance(prev_value, int) and isinstance(new_value, float) and new_value.is_integer():
                            new_value = int(new_value)
                    except Exception as e:
                        print(f"[SetVar] Math operation failed, falling back to set: {e}")
                        new_value = var_value_converted
                actor_data['variables'][var_name] = new_value
                save_success = False
                try:
                    with open(actor_path, 'w', encoding='utf-8') as f:
                        json.dump(actor_data, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                    save_success = True
                except Exception as e:
                    print(f"ERROR: Failed to save updated actor data: {e}")
                if save_success:
                    print(f"✓ Successfully updated character variable for '{character_name}': {var_name} = {new_value}")
                else:
                    print(f"✗ FAILED to update character variable for '{character_name}': {var_name} = {new_value}")
            elif variable_scope == 'Player':
                workflow_data_dir = tab_data.get('workflow_data_dir')
                if not workflow_data_dir:
                    print(f"ERROR: Cannot set player variable - workflow_data_dir not found")
                    return
                game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
                player_file = None
                player_name = None
                if os.path.exists(game_actors_dir):
                    for filename in os.listdir(game_actors_dir):
                        if filename.lower().endswith('.json'):
                            file_path = os.path.join(game_actors_dir, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    actor_data = json.load(f)
                                    if actor_data.get('is_player', False) or actor_data.get('isPlayer', False):
                                        player_file = file_path
                                        player_name = actor_data.get('name', 'Player')
                                        break
                            except Exception as e:
                                print(f"Error reading potential player file {file_path}: {e}")
                if not player_file:
                    base_player_file, base_player_name = _find_player_character_file(workflow_data_dir)
                    if base_player_file and base_player_name:
                        os.makedirs(game_actors_dir, exist_ok=True)
                        import shutil
                        player_filename = os.path.basename(base_player_file)
                        player_file = os.path.join(game_actors_dir, player_filename)
                        player_name = base_player_name
                        
                        try:
                            shutil.copy2(base_player_file, player_file)
                            print(f"Copied player file from base to game directory: {player_name} ({player_file})")
                        except Exception as e:
                            print(f"ERROR: Failed to copy player file to game directory: {e}")
                            return
                    else:
                        print(f"ERROR: Could not find player character file with isPlayer=True")
                        return
                try:
                    with open(player_file, 'r', encoding='utf-8') as f:
                        player_data = json.load(f)
                    if 'variables' not in player_data:
                        player_data['variables'] = {}
                    player_data['variables'][var_name] = var_value_converted
                    with open(player_file, 'w', encoding='utf-8') as f:
                        json.dump(player_data, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                    print(f"Successfully stored sampled result in player variable: {var_name}")
                except Exception as e:
                    print(f"Error updating player data: {e}")
            elif variable_scope == 'Setting':
                workflow_data_dir = tab_data.get('workflow_data_dir')
                if not workflow_data_dir:
                    print(f"ERROR: Cannot set setting variable - workflow_data_dir not found")
                    return
                player_setting_name = _get_player_current_setting_name(workflow_data_dir)
                if not player_setting_name or player_setting_name == "Unknown Setting":
                    print(f"ERROR: Cannot determine current setting name for player.")
                    return
                session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
                found_setting_file = None
                for root, dirs, files in os.walk(session_settings_dir):
                    dirs[:] = [d for d in dirs if d.lower() != 'saves']
                    for filename in files:
                        if filename.lower().endswith('_setting.json'):
                            file_path = os.path.join(root, filename)
                            setting_data = _load_json_safely(file_path)
                            if setting_data.get('name') == player_setting_name:
                                found_setting_file = file_path
                                break
                    if source_value is not None:
                        break
                if not found_setting_file:
                    base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
                    found_base_setting_file = None
                    for root, dirs, files in os.walk(base_settings_dir):
                        dirs[:] = [d for d in dirs if d.lower() != 'saves']
                        for filename in files:
                            if filename.lower().endswith('_setting.json'):
                                file_path = os.path.join(root, filename)
                                setting_data = _load_json_safely(file_path)
                                if setting_data.get('name') == player_setting_name:
                                    found_base_setting_file = file_path
                                    break
                        if found_base_setting_file:
                            break
                    if found_base_setting_file:
                        rel_path = os.path.relpath(found_base_setting_file, base_settings_dir)
                        dest_path = os.path.join(session_settings_dir, rel_path)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        import shutil
                        try:
                            shutil.copy2(found_base_setting_file, dest_path)
                            found_setting_file = dest_path
                        except Exception as e:
                            print(f"ERROR: Failed to copy base setting file: {e}")
                            found_setting_file = found_base_setting_file
                    else:
                        print(f"ERROR: Could not find setting file for '{player_setting_name}' in either /game/settings or /resources/data files/settings")
                        return
                try:
                    with open(found_setting_file, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                    if 'variables' not in setting_data or not isinstance(setting_data['variables'], dict):
                        setting_data['variables'] = {}
                    prev_value = setting_data['variables'].get(var_name)
                    new_value = var_value_converted
                    if operation == 'set':
                        set_var_mode = obj.get('set_var_mode', 'replace')
                        delimiter = obj.get('set_var_delimiter', '/')
                        new_value = _apply_string_operation_mode(prev_value, new_value, set_var_mode, delimiter)
                    elif operation != 'set':
                        try:
                            prev_num = float(prev_value) if prev_value is not None else 0.0
                            arg_num = float(var_value_converted)
                            if operation == 'increment':
                                new_value = prev_num + arg_num
                            elif operation == 'decrement':
                                new_value = prev_num - arg_num
                            elif operation == 'multiply':
                                new_value = prev_num * arg_num
                            elif operation == 'divide':
                                new_value = prev_num / arg_num if arg_num != 0 else prev_num
                            if prev_value is not None and isinstance(prev_value, int) and isinstance(new_value, float) and new_value.is_integer():
                                new_value = int(new_value)
                        except Exception as e:
                            print(f"[SetVar] Math operation failed, falling back to set: {e}")
                            new_value = var_value_converted
                    setting_data['variables'][var_name] = new_value
                    with open(found_setting_file, 'w', encoding='utf-8') as f:
                        json.dump(setting_data, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                except Exception as e:
                    print(f"✗ FAILED to update setting variable for '{player_setting_name}': {var_name} = {var_value_converted}. Error: {e}")
                    return
            elif variable_scope == 'Global':
                tab_index_for_var = -1
                try:
                    tab_index_for_var = self.tabs_data.index(tab_data)
                except ValueError:
                    print(f"ERROR: Could not find tab_data in self.tabs_data for global variable saving.")
                    return 
                variables_file = tab_data.get('variables_file')
                if not variables_file:
                    print(f"ERROR: No variables_file found in tab_data for global variable setting.")
                    return
                variables = {}
                if os.path.exists(variables_file):
                    try:
                        with open(variables_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                variables = json.loads(content)
                    except Exception as e:
                        print(f"ERROR: Could not load variables file for global variable setting: {e}")
                        return
                if not isinstance(variables, dict):
                    print(f"ERROR: Loaded global variables is not a dict! Will not overwrite file. Value: {variables}")
                    return
                prev_value = variables.get(var_name)
                new_value = var_value_converted
                if operation == 'set':
                    set_var_mode = obj.get('set_var_mode', 'replace')
                    delimiter = obj.get('set_var_delimiter', '/')
                    new_value = _apply_string_operation_mode(prev_value, new_value, set_var_mode, delimiter)
                elif operation != 'set':
                    try:
                        prev_num = float(prev_value) if prev_value is not None else 0.0
                        arg_num = float(var_value_converted)
                        if operation == 'increment':
                            new_value = prev_num + arg_num
                        elif operation == 'decrement':
                            new_value = prev_num - arg_num
                        elif operation == 'multiply':
                            new_value = prev_num * arg_num
                        elif operation == 'divide':
                            new_value = prev_num / arg_num if arg_num != 0 else prev_num
                        if prev_value is not None and isinstance(prev_value, int) and isinstance(new_value, float) and new_value.is_integer():
                            new_value = int(new_value)
                
                    except Exception as e:
                        print(f"[SetVar] Math operation failed, falling back to set: {e}")
                        new_value = var_value_converted
                variables[var_name] = new_value
                try:
                    variables_dir = os.path.dirname(variables_file)
                    if variables_dir and not os.path.exists(variables_dir):
                        os.makedirs(variables_dir)
                    with open(variables_file, 'w', encoding='utf-8') as f:
                        json.dump(variables, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                    tab_data['variables'] = variables.copy()
                    pass
                except Exception as e:
                    print(f"✗ FAILED to update global variable: {var_name} = {new_value}. Error: {e}")
            elif variable_scope == 'Scene Characters':
                workflow_data_dir = tab_data.get('workflow_data_dir')
                if not workflow_data_dir:
                    print(f"ERROR: Cannot set Scene Characters variable - workflow_data_dir not found")
                    return
                current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                if not current_setting_name or current_setting_name == "Unknown Setting":
                    print(f"ERROR: Cannot set Scene Characters variable - _get_player_current_setting_name could not determine current setting.")
                    return
                else:
                    pass
                setting_file_result = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, current_setting_name)
                setting_file_path = setting_file_result[0] if isinstance(setting_file_result, tuple) else setting_file_result
                if not setting_file_path or not os.path.exists(setting_file_path):
                    print(f"ERROR: Setting file for '{current_setting_name}' not found at expected path.")
                    return
                try:
                    with open(setting_file_path, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                        pass
                except Exception as e:
                    print(f"ERROR: Failed to load setting file '{setting_file_path}': {e}")
                    return
                characters = setting_data.get('characters', [])
                if not isinstance(characters, list):
                    print(f"WARN: 'characters' field in setting file is not a list. Treating as empty.")
                    characters = []
                if not characters:
                    print(f"    -> No characters found in setting '{current_setting_name}'. Nothing to update.")
                    return
                update_count = 0
                for char_name in characters:
                    if not isinstance(char_name, str) or not char_name or char_name.strip() == '':
                        continue
                    actor_data, actor_path = _get_or_create_actor_data(self, workflow_data_dir, char_name)
                    if not actor_data or not actor_path:
                        print(f"    -> Could not find or create actor data for '{char_name}'. Skipping.")
                        continue
                    if 'variables' not in actor_data:
                        print(f"    -> Creating new 'variables' section for '{char_name}'")
                        actor_data['variables'] = {}
                    elif not isinstance(actor_data.get('variables'), dict):
                        print(f"    -> Existing 'variables' is not a dictionary. Resetting.")
                        actor_data['variables'] = {}
                    
                    prev_value = actor_data['variables'].get(var_name)
                    new_value = var_value_converted
                    if operation == 'set':
                        set_var_mode = obj.get('set_var_mode', 'replace')
                        delimiter = obj.get('set_var_delimiter', '/')
                        new_value = _apply_string_operation_mode(prev_value, new_value, set_var_mode, delimiter)
                    elif operation != 'set':
                        try:
                            prev_num = float(prev_value) if prev_value is not None else 0.0
                            arg_num = float(var_value_converted)
                            if operation == 'increment':
                                new_value = prev_num + arg_num
                            elif operation == 'decrement':
                                new_value = prev_num - arg_num
                            elif operation == 'multiply':
                                new_value = prev_num * arg_num
                            elif operation == 'divide':
                                new_value = prev_num / arg_num if arg_num != 0 else prev_num
                            if prev_value is not None and isinstance(prev_value, int) and isinstance(new_value, float) and new_value.is_integer():
                                new_value = int(new_value)
                        except Exception as e:
                            print(f"[SetVar] Math operation failed, falling back to set: {e}")
                            new_value = var_value_converted
                    actor_data['variables'][var_name] = new_value
                    try:
                        with open(actor_path, 'w', encoding='utf-8') as f:
                            json.dump(actor_data, f, indent=2, ensure_ascii=False)
                            f.flush()
                            os.fsync(f.fileno())
                        update_count += 1
                    except Exception as e:
                        print(f"    ✗ Failed to update variable for character '{char_name}': {e}")
            else:
                print(f"WARNING: Cannot set variable '{var_name}'. Scope is '{variable_scope}', but required context (e.g., character_name for 'Character' scope) might be missing or scope is unhandled.")
        else:
            print(f"ERROR: Cannot set variable - var_name is empty.")
    
    elif obj_type == 'Add Item':
        item_name = obj.get('item_name', '')
        quantity = obj.get('quantity', '1')
        owner = obj.get('owner', '')
        description = obj.get('description', '')
        location = obj.get('location', '')
        target_type = obj.get('target_type', 'Setting')
        target_name = obj.get('target_name', '')
        generate = obj.get('generate', False)
        generate_description = obj.get('generate_description', False)
        generate_location = obj.get('generate_location', False)
        generate_instructions = obj.get('generate_instructions', '')
        attach_scene_context = obj.get('attach_scene_context', False)
        attach_location_desc = obj.get('attach_location_desc', False)
        attach_character_desc = obj.get('attach_character_desc', False)
        target_container_enabled = obj.get('target_container_enabled', False)
        target_item_name = obj.get('target_item_name', '')
        target_container_name = obj.get('target_container_name', '')
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot process Add Item - workflow_data_dir not found")
            return
        if not item_name:
            print(f"ERROR: Cannot add item - item_name is empty")
            return
        player_name = _get_player_character_name(workflow_data_dir)
        current_setting_name = _get_player_current_setting_name(workflow_data_dir)
        owner = _substitute_variables_in_string(owner, tab_data, character_name)
        description = _substitute_variables_in_string(description, tab_data, character_name)
        location = _substitute_variables_in_string(location, tab_data, character_name)
        
        if (generate_description and not description) or (generate_location and not location) or generate:
            try:
                context_parts = []
                if attach_scene_context:
                    context_list = tab_data.get('context', [])
                    current_scene = tab_data.get('scene_number', 1)
                    current_scene_messages = [msg for msg in context_list 
                                             if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene]
                    if current_scene_messages:
                        scene_context = '\n'.join([f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')}" 
                                                   for msg in current_scene_messages[-5:]])  # Last 5 messages
                        context_parts.append(f"Scene Context:\n{scene_context}")
                
                if attach_location_desc:
                    current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                    if current_setting_name:
                        setting_file_path = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, current_setting_name)
                        if isinstance(setting_file_path, tuple):
                            setting_file_path = setting_file_path[0]
                        if setting_file_path and os.path.exists(setting_file_path):
                            try:
                                with open(setting_file_path, 'r', encoding='utf-8') as f:
                                    setting_data = json.load(f)
                                    setting_desc = setting_data.get('description', '')
                                    if setting_desc:
                                        context_parts.append(f"Location Description:\n{setting_desc}")
                            except Exception:
                                pass
                
                if attach_character_desc and character_name:
                    class DummySelf:
                        pass
                    dummy_self = DummySelf()
                    character_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, character_name)
                    if character_file_path and os.path.exists(character_file_path):
                        try:
                            with open(character_file_path, 'r', encoding='utf-8') as f:
                                character_data = json.load(f)
                                character_desc = character_data.get('description', '')
                                if character_desc:
                                    context_parts.append(f"Character Description:\n{character_desc}")
                        except Exception:
                            pass
                
                context_text = ""
                if context_parts:
                    context_text = "\n\n".join(context_parts) + "\n\n"
                
                if generate_instructions:
                    instructions = generate_instructions
                else:
                    instructions = f"Generate details for an item called '{item_name}'."
                    if generate_description and not description and generate_location and not location:
                        instructions += " Provide ONLY a brief description (under 100 words) on the first line, and a brief location (under 50 words) on the second line. Do not include any other text."
                    elif generate_description and not description:
                        instructions += " Provide ONLY a brief, descriptive description (under 100 words). Do not include any other text."
                    elif generate_location and not location:
                        instructions += " Provide ONLY a brief, logical location description (under 50 words). Do not include any other text."
                
                if context_text:
                    instructions = f"{context_text}Instructions: {instructions}"
                
                model = self.get_current_model()
                max_tokens = 200
                temperature = 0.7
                context = [
                    {"role": "user", "content": instructions}
                ]
                result = self.run_utility_inference_sync(context, model, max_tokens, temperature)
                
                if result and result.strip():
                    result = result.strip()
                    
                    if generate_description and not description and generate_location and not location:
                        lines = result.split('\n')
                        if len(lines) >= 2:
                            description = lines[0].strip()
                            location = lines[1].strip()
                        else:
                            description = result
                    elif generate_description and not description:
                        description = result
                    elif generate_location and not location:
                        location = result
                        
            except Exception as e:
                print(f"Warning: Failed to generate details for item '{item_name}': {e}")
        if not target_name and current_setting_name:
            target_name = current_setting_name
        target_file_path = None
        if target_type == 'Setting':
            target_file_path = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, target_name)
            if isinstance(target_file_path, tuple):
                target_file_path = target_file_path[0]
        elif target_type == 'Character':
            class DummySelf:
                pass
            dummy_self = DummySelf()
            target_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, target_name)
        
        if not target_file_path or not os.path.exists(target_file_path):
            print(f"ERROR: Cannot add item - target file not found: {target_file_path}")
            return
        try:
            with open(target_file_path, 'r', encoding='utf-8') as f:
                target_data = json.load(f)
            if 'inventory' not in target_data:
                target_data['inventory'] = []
            new_item = {
                'item_id': f"item_{generate_item_id()}",
                'name': item_name,
                'quantity': int(quantity) if quantity.isdigit() else 1,
                'owner': owner,
                'description': description,
                'location': location,
                'containers': {}
            }
            if target_container_enabled and target_item_name and target_container_name:
                success = _add_item_to_container(target_data['inventory'], target_item_name, target_container_name, new_item)
                if not success:
                    print(f"ERROR: Cannot add item '{item_name}' to container '{target_container_name}' in item '{target_item_name}' - target item or container not found")
                    return
                print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully added item '{item_name}' (qty: {quantity}) to container '{target_container_name}' in {target_type} '{target_name}'")
            else:
                target_data['inventory'].append(new_item)
                print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully added item '{item_name}' (qty: {quantity}) to {target_type} '{target_name}'")
            with open(target_file_path, 'w', encoding='utf-8') as f:
                json.dump(target_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ERROR: Failed to add item '{item_name}' to {target_type} '{target_name}': {e}")
    
    elif obj_type == 'Remove Item':
        item_name = _substitute_variables_in_string(obj.get('item_name', ''), tab_data, character_name)
        quantity = _substitute_variables_in_string(obj.get('quantity', '1'), tab_data, character_name)
        target_type = obj.get('target_type', 'Setting')
        target_name = _substitute_variables_in_string(obj.get('target_name', ''), tab_data, character_name)
        target_container_enabled = obj.get('target_container_enabled', False)
        target_item_name = _substitute_variables_in_string(obj.get('target_item_name', ''), tab_data, character_name)
        target_container_name = _substitute_variables_in_string(obj.get('target_container_name', ''), tab_data, character_name)
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot process Remove Item - workflow_data_dir not found")
            return
        if not item_name:
            print(f"ERROR: Cannot remove item - item_name is empty")
            return
        item_identifiers = [identifier.strip() for identifier in item_name.split(',') if identifier.strip()]
        if not item_identifiers:
            print(f"ERROR: Cannot remove item - no valid item identifiers found in '{item_name}'")
            return
        player_name = _get_player_character_name(workflow_data_dir)
        current_setting_name = _get_player_current_setting_name(workflow_data_dir)
        if not target_name and current_setting_name:
            target_name = current_setting_name
        target_file_path = None
        if target_type == 'Setting':
            target_file_path = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, target_name)
            if isinstance(target_file_path, tuple):
                target_file_path = target_file_path[0]
        elif target_type == 'Character':
            class DummySelf:
                pass
            dummy_self = DummySelf()
            target_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, target_name)
        if not target_file_path or not os.path.exists(target_file_path):
            print(f"ERROR: Cannot remove item - target file not found: {target_file_path}")
            return
        try:
            with open(target_file_path, 'r', encoding='utf-8') as f:
                target_data = json.load(f)
            inventory = target_data.get('inventory', [])
            if not inventory:
                print(f"WARNING: No inventory found in {target_type} '{target_name}'")
                return
            total_removed = 0
            items_to_remove_per_item = int(quantity) if quantity.isdigit() else 1
            for item_identifier in item_identifiers:
                if target_container_enabled and target_item_name and target_container_name:
                    removed_count = _remove_item_from_container(inventory, target_item_name, target_container_name, item_identifier, items_to_remove_per_item)
                    if removed_count > 0:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully removed {removed_count} of item '{item_identifier}' from container '{target_container_name}' in {target_type} '{target_name}'")
                        total_removed += removed_count
                    else:
                        print(f"WARNING: No items '{item_identifier}' found in container '{target_container_name}' of item '{target_item_name}' in {target_type} '{target_name}'")
                else:
                    removed_count = 0
                    items_to_remove = items_to_remove_per_item
                    print(f"[DEBUG] Remove Item: Looking for item_identifier='{item_identifier}' in {target_type} '{target_name}'")
                    print(f"[DEBUG] Remove Item: Inventory contains {len(inventory)} items")
                    for i, item in enumerate(inventory):
                        print(f"[DEBUG] Remove Item: Item {i}: name='{item.get('name', 'N/A')}', item_id='{item.get('item_id', 'N/A')}'")
                    for i in range(len(inventory) - 1, -1, -1):
                        item = inventory[i]
                        print(f"[DEBUG] Remove Item: Checking item {i}: name='{item.get('name', 'N/A')}', item_id='{item.get('item_id', 'N/A')}'")
                        print(f"[DEBUG] Remove Item: Comparing '{item_identifier}' with name='{item.get('name', 'N/A')}' and item_id='{item.get('item_id', 'N/A')}'")
                        item_id_match = item_identifier.lower().startswith('item_') and item.get('item_id', '').lower() == item_identifier.lower()
                        name_match = item.get('name') == item_identifier
                        print(f"[DEBUG] Remove Item: item_id_match = {item_id_match} (comparing '{item.get('item_id', '')}'.lower() == '{item_identifier}'.lower())")
                        print(f"[DEBUG] Remove Item: name_match = {name_match}")
                        if item_id_match or name_match:
                            current_quantity = item.get('quantity', 1)
                            if current_quantity <= items_to_remove:
                                removed_count += current_quantity
                                inventory.pop(i)
                                items_to_remove -= current_quantity
                            else:
                                item['quantity'] = current_quantity - items_to_remove
                                removed_count += items_to_remove
                                items_to_remove = 0
                            if items_to_remove <= 0:
                                break
                    if removed_count > 0:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully removed {removed_count} of item '{item_identifier}' from {target_type} '{target_name}'")
                        total_removed += removed_count
                    else:
                        print(f"WARNING: No items '{item_identifier}' found in {target_type} '{target_name}'")
            if total_removed > 0:
                consume = obj.get('consume', False)
                print(f"[DEBUG] Remove Item: consume={consume}")
                if consume:
                    consume_scope = obj.get('consume_scope', 'Player')
                    print(f"[DEBUG] Remove Item: consume_scope={consume_scope}")
                    for item_identifier in item_identifiers:
                        print(f"[DEBUG] Remove Item: Checking if '{item_identifier}' is consumable")
                        if _is_item_consumable(item_identifier, workflow_data_dir):
                            print(f"[DEBUG] Remove Item: '{item_identifier}' is consumable, applying effects")
                            _apply_item_consume_effects(item_identifier, consume_scope, workflow_data_dir, tab_data, character_name)
                        else:
                            print(f"WARNING: Cannot consume item '{item_identifier}' - item is not marked as consumable in Inventory Reference")
                else:
                    print(f"[DEBUG] Remove Item: consume=False, skipping variable effects")
                with open(target_file_path, 'w', encoding='utf-8') as f:
                    json.dump(target_data, f, indent=2, ensure_ascii=False)
            else:
                print(f"WARNING: No items were removed from {target_type} '{target_name}'")
        except Exception as e:
            print(f"ERROR: Failed to remove items from {target_type} '{target_name}': {e}")
    
    elif obj_type == 'Move Item':
        item_name = _substitute_variables_in_string(obj.get('item_name', ''), tab_data, character_name)
        quantity = _substitute_variables_in_string(obj.get('quantity', 1), tab_data, character_name)
        from_type = obj.get('from_type', '')
        from_name = _substitute_variables_in_string(obj.get('from_name', ''), tab_data, character_name)
        to_type = obj.get('to_type', '')
        to_name = _substitute_variables_in_string(obj.get('to_name', ''), tab_data, character_name)
        from_container_enabled = obj.get('from_container_enabled', False)
        from_item_name = _substitute_variables_in_string(obj.get('from_item_name', ''), tab_data, character_name)
        from_container_name = _substitute_variables_in_string(obj.get('from_container_name', ''), tab_data, character_name)
        to_container_enabled = obj.get('to_container_enabled', False)
        to_item_name = _substitute_variables_in_string(obj.get('to_item_name', ''), tab_data, character_name)
        to_container_name = _substitute_variables_in_string(obj.get('to_container_name', ''), tab_data, character_name)
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot process Move Item - workflow_data_dir not found")
            return
        if not item_name:
            print(f"ERROR: Cannot move item - item_name is empty")
            return
        
        item_identifiers = [identifier.strip() for identifier in item_name.split(',') if identifier.strip()]
        if not item_identifiers:
            print(f"ERROR: Cannot move item - no valid item identifiers found in '{item_name}'")
            return
        player_name = _get_player_character_name(workflow_data_dir)
        current_setting_name = _get_player_current_setting_name(workflow_data_dir)
        if from_name == "(Player)" and player_name:
            from_name = player_name
        elif not from_name and current_setting_name:
            from_name = current_setting_name
        if to_name == "(Player)" and player_name:
            to_name = player_name
        elif not to_name and current_setting_name:
            to_name = current_setting_name
        from_file_path = None
        to_file_path = None
        if from_type == 'Setting':
            from_file_path = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, from_name)
            if isinstance(from_file_path, tuple):
                from_file_path = from_file_path[0]
        elif from_type == 'Character':
            class DummySelf:
                pass
            dummy_self = DummySelf()
            from_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, from_name)
        if to_type == 'Setting':
            to_file_path = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, to_name)
            if isinstance(to_file_path, tuple):
                to_file_path = to_file_path[0]
        elif to_type == 'Character':
            class DummySelf:
                pass
            dummy_self = DummySelf()
            to_file_path = _find_actor_file_path(dummy_self, workflow_data_dir, to_name)
        if not from_file_path or not os.path.exists(from_file_path):
            print(f"ERROR: Cannot move item - source file not found: {from_file_path}")
            return
        if not to_file_path or not os.path.exists(to_file_path):
            print(f"ERROR: Cannot move item - destination file not found: {to_file_path}")
            return
        try:
            with open(from_file_path, 'r', encoding='utf-8') as f:
                from_data = json.load(f)
            with open(to_file_path, 'r', encoding='utf-8') as f:
                to_data = json.load(f)
            from_inventory = from_data.get('inventory', [])
            to_inventory = to_data.get('inventory', [])
            if not from_inventory:
                print(f"WARNING: No inventory found in source {from_type} '{from_name}'")
                return
            if not to_inventory:
                to_inventory = []
                to_data['inventory'] = to_inventory
            
            total_moved = 0
            items_to_move_per_item = int(quantity) if str(quantity).isdigit() else int(quantity)
            
            for item_identifier in item_identifiers:
                if from_container_enabled and from_item_name and from_container_name and to_container_enabled and to_item_name and to_container_name:
                    if from_file_path == to_file_path:
                        moved_count = _move_item_between_containers(from_inventory, from_item_name, from_container_name, 
                                                                  to_item_name, to_container_name, item_identifier, items_to_move_per_item)
                    else:
                        removed_count = _remove_item_from_container(from_inventory, from_item_name, from_container_name, item_identifier, items_to_move_per_item)
                        if removed_count == 0:
                            print(f"WARNING: No items '{item_identifier}' found in container '{from_container_name}' of item '{from_item_name}' in source {from_type} '{from_name}'")
                            continue
                        new_item = {
                            'item_id': f"item_{generate_item_id()}",
                            'name': item_identifier,
                            'quantity': removed_count,
                            'owner': '',
                            'description': '',
                            'location': '',
                            'containers': {}
                        }
                        success = _add_item_to_container(to_inventory, to_item_name, to_container_name, new_item)
                        if not success:
                            _add_item_to_container(from_inventory, from_item_name, from_container_name, new_item)
                            print(f"ERROR: Cannot add item '{item_identifier}' to container '{to_container_name}' in item '{to_item_name}' in destination {to_type} '{to_name}' - target item or container not found")
                            continue
                        moved_count = removed_count
                    if moved_count > 0:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully moved {moved_count} of item '{item_identifier}' from container '{from_container_name}' to container '{to_container_name}'")
                        total_moved += moved_count
                elif from_container_enabled and from_item_name and from_container_name:
                    removed_count = _remove_item_from_container(from_inventory, from_item_name, from_container_name, item_identifier, items_to_move_per_item)
                    if removed_count > 0:
                        new_item = {
                            'item_id': f"item_{generate_item_id()}",
                            'name': item_identifier,
                            'quantity': removed_count,
                            'owner': '',
                            'description': '',
                            'location': '',
                            'containers': {}
                        }
                        to_inventory.append(new_item)
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully moved {removed_count} of item '{item_identifier}' from container '{from_container_name}' to main inventory")
                        total_moved += removed_count
                    else:
                        print(f"WARNING: No items '{item_identifier}' found in container '{from_container_name}' of item '{from_item_name}' in source {from_type} '{from_name}'")
                elif to_container_enabled and to_item_name and to_container_name:
                    moved_count = 0
                    items_to_move = items_to_move_per_item
                    for i in range(len(from_inventory) - 1, -1, -1):
                        item = from_inventory[i]
                        if (item_identifier.lower().startswith('item_') and item.get('item_id', '').lower() == item_identifier.lower()) or \
                           item.get('name') == item_identifier:
                            current_quantity = item.get('quantity', 1)
                            if current_quantity <= items_to_move:
                                moved_count += current_quantity
                                from_inventory.pop(i)
                                items_to_move -= current_quantity
                                new_item = {
                                    'item_id': f"item_{generate_item_id()}",
                                    'name': item_identifier,
                                    'quantity': current_quantity,
                                    'owner': '',
                                    'description': '',
                                    'location': '',
                                    'containers': {}
                                }
                                success = _add_item_to_container(to_inventory, to_item_name, to_container_name, new_item)
                                if not success:
                                    from_inventory.append(new_item)
                                    print(f"ERROR: Cannot add item '{item_identifier}' to container '{to_container_name}' in item '{to_item_name}' in destination {to_type} '{to_name}' - target item or container not found")
                                    continue
                            else:
                                item['quantity'] = current_quantity - items_to_move
                                moved_count += items_to_move
                                items_to_move = 0
                                new_item = {
                                    'item_id': f"item_{generate_item_id()}",
                                    'name': item_identifier,
                                    'quantity': items_to_move,
                                    'owner': '',
                                    'description': '',
                                    'location': '',
                                    'containers': {}
                                }
                                success = _add_item_to_container(to_inventory, to_item_name, to_container_name, new_item)
                                if not success:
                                    item['quantity'] = current_quantity
                                    print(f"ERROR: Cannot add item '{item_identifier}' to container '{to_container_name}' in item '{to_item_name}' in destination {to_type} '{to_name}' - target item or container not found")
                                    continue
                            if items_to_move <= 0:
                                break
                    if moved_count > 0:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully moved {moved_count} of item '{item_identifier}' from main inventory to container '{to_container_name}'")
                        total_moved += moved_count
                    else:
                        print(f"WARNING: No items '{item_identifier}' found in source {from_type} '{from_name}'")
                else:
                    moved_count = 0
                    items_to_move = items_to_move_per_item
                    for i in range(len(from_inventory) - 1, -1, -1):
                        item = from_inventory[i]
                        if (item_identifier.lower().startswith('item_') and item.get('item_id', '').lower() == item_identifier.lower()) or \
                           item.get('name') == item_identifier:
                            current_quantity = item.get('quantity', 1)
                            if current_quantity <= items_to_move:
                                moved_count += current_quantity
                                from_inventory.pop(i)
                                items_to_move -= current_quantity
                                new_item = {
                                    'item_id': f"item_{generate_item_id()}",
                                    'name': item_identifier,
                                    'quantity': current_quantity,
                                    'owner': '',
                                    'description': '',
                                    'location': '',
                                    'containers': {}
                                }
                                success = _add_item_to_container(to_inventory, to_item_name, to_container_name, new_item)
                                if not success:
                                    from_inventory.append(new_item)
                                    print(f"ERROR: Cannot add item '{item_identifier}' to container '{to_container_name}' in item '{to_item_name}' in destination {to_type} '{to_name}' - target item or container not found")
                                    continue
                            else:
                                item['quantity'] = current_quantity - items_to_move
                                moved_count += items_to_move
                                items_to_move = 0
                                new_item = {
                                    'item_id': f"item_{generate_item_id()}",
                                    'name': item_identifier,
                                    'quantity': items_to_move,
                                    'owner': '',
                                    'description': '',
                                    'location': '',
                                    'containers': {}
                                }
                                success = _add_item_to_container(to_inventory, to_item_name, to_container_name, new_item)
                                if not success:
                                    item['quantity'] = current_quantity
                                    print(f"ERROR: Cannot add item '{item_identifier}' to container '{to_container_name}' in item '{to_item_name}' in destination {to_type} '{to_name}' - target item or container not found")
                                    continue
                            if items_to_move <= 0:
                                break
                    if moved_count > 0:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully moved {moved_count} of item '{item_identifier}' from {from_type} '{from_name}' to {to_type} '{to_name}'")
                        total_moved += moved_count
                    else:
                        print(f"WARNING: No items '{item_identifier}' found in source {from_type} '{from_name}'")
            
            if total_moved > 0:
                from_data['inventory'] = from_inventory
                to_data['inventory'] = to_inventory
                with open(from_file_path, 'w', encoding='utf-8') as f:
                    json.dump(from_data, f, indent=2, ensure_ascii=False)
                with open(to_file_path, 'w', encoding='utf-8') as f:
                    json.dump(to_data, f, indent=2, ensure_ascii=False)
            else:
                print(f"WARNING: No items were moved from {from_type} '{from_name}' to {to_type} '{to_name}'")
        except Exception as e:
            print(f"ERROR: Failed to move items from {from_type} '{from_name}' to {to_type} '{to_name}': {e}")
    
    elif obj_type == 'Determine Items':
        scope = obj.get('scope', 'Player')
        return_type = obj.get('return_type', 'Return Single Item')
        owner = _substitute_variables_in_string(obj.get('owner', ''), tab_data, character_name)
        description = _substitute_variables_in_string(obj.get('description', ''), tab_data, character_name)
        location = _substitute_variables_in_string(obj.get('location', ''), tab_data, character_name)
        text = _substitute_variables_in_string(obj.get('text', ''), tab_data, character_name)
        text_scope = obj.get('text_scope', 'Full Conversation')
        if not text:
            print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Determine Items - No search text provided, skipping")
            return
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot determine items - workflow_data_dir not found")
            return
        result = _determine_items_with_inference(
            self, text, text_scope, scope, owner, description, location, 
            return_type, workflow_data_dir, tab_data, character_name, 
            current_user_msg, prev_assistant_msg
        )
        if result is not None:
            var_name = 'items' if return_type in ['Return Multiple Items', 'Multiple Items'] else 'item'
            item_details = {}
            
            if result != "NONE":
                items_data = _load_items_data(workflow_data_dir, scope, character_name)
                print(f"[DEBUG] Loaded {len(items_data)} items from inventory")
                print(f"[DEBUG] Looking for item ID: {result}")
                item_details = _extract_item_details_from_result(result, items_data)
                print(f"[DEBUG] Extracted item details: {item_details}")
                if return_type in ['Return Multiple Items', 'Multiple Items']:
                    if 'names' in item_details:
                        _save_global_variable(workflow_data_dir, 'itemnames', item_details.get('names', ''))
                        _save_global_variable(workflow_data_dir, 'itemdescriptions', item_details.get('descriptions', ''))
                        _save_global_variable(workflow_data_dir, 'itemlocations', item_details.get('locations', ''))
                        _save_global_variable(workflow_data_dir, 'itemowners', item_details.get('owners', ''))
                    elif 'name' in item_details:
                        _save_global_variable(workflow_data_dir, 'itemnames', item_details.get('name', ''))
                        _save_global_variable(workflow_data_dir, 'itemdescriptions', item_details.get('description', ''))
                        _save_global_variable(workflow_data_dir, 'itemlocations', item_details.get('location', ''))
                        _save_global_variable(workflow_data_dir, 'itemowners', item_details.get('owner', ''))
                else:
                    if 'name' in item_details:
                        _save_global_variable(workflow_data_dir, 'itemname', item_details.get('name', ''))
                        _save_global_variable(workflow_data_dir, 'itemdescription', item_details.get('description', ''))
                        _save_global_variable(workflow_data_dir, 'itemlocation', item_details.get('location', ''))
                        _save_global_variable(workflow_data_dir, 'itemowner', item_details.get('owner', ''))
                    elif 'names' in item_details:
                        _save_global_variable(workflow_data_dir, 'itemname', item_details.get('names', ''))
                        _save_global_variable(workflow_data_dir, 'itemdescription', item_details.get('descriptions', ''))
                        _save_global_variable(workflow_data_dir, 'itemlocation', item_details.get('locations', ''))
                        _save_global_variable(workflow_data_dir, 'itemowner', item_details.get('owners', ''))
            
            _save_global_variable(workflow_data_dir, var_name, result)
            print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Determine Items - Stored result '{result}' in global variable '{var_name}'")
            
            if result == "NONE":
                _save_global_variable(workflow_data_dir, 'item', 'NONE')
                _save_global_variable(workflow_data_dir, 'itemnames', 'NONE')
                _save_global_variable(workflow_data_dir, 'itemdescriptions', 'NONE')
                _save_global_variable(workflow_data_dir, 'itemlocations', 'NONE')
                _save_global_variable(workflow_data_dir, 'itemowners', 'NONE')
                _save_global_variable(workflow_data_dir, 'itemname', 'NONE')
                _save_global_variable(workflow_data_dir, 'itemdescription', 'NONE')
                _save_global_variable(workflow_data_dir, 'itemlocation', 'NONE')
                _save_global_variable(workflow_data_dir, 'itemowner', 'NONE')
                print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Determine Items - Cleared all item variables to NONE")
            elif result != "NONE" and item_details:
                if return_type in ['Return Multiple Items', 'Multiple Items']:
                    if 'names' in item_details:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Determine Items - Also stored: itemnames='{item_details.get('names', '')}', itemdescriptions='{item_details.get('descriptions', '')}', itemlocations='{item_details.get('locations', '')}', itemowners='{item_details.get('owners', '')}'")
                    elif 'name' in item_details:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Determine Items - Also stored: itemnames='{item_details.get('name', '')}', itemdescriptions='{item_details.get('description', '')}', itemlocations='{item_details.get('location', '')}', itemowners='{item_details.get('owner', '')}'")
                else:
                    if 'name' in item_details:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Determine Items - Also stored: itemname='{item_details.get('name', '')}', itemdescription='{item_details.get('description', '')}', itemlocation='{item_details.get('location', '')}', itemowner='{item_details.get('owner', '')}'")
                    elif 'names' in item_details:
                        print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Determine Items - Also stored: itemname='{item_details.get('names', '')}', itemdescription='{item_details.get('descriptions', '')}', itemlocation='{item_details.get('locations', '')}', itemowner='{item_details.get('owners', '')}'")
        else:
            print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Determine Items - No items found matching criteria")
    
    elif obj_type == 'Game Over':
        game_over_message = _substitute_variables_in_string(obj.get('game_over_message', 'Game Over'), tab_data, character_name)
        rule_id = rule.get('id', 'Unknown') if rule else 'Unknown'
        current_tab_index = self.tab_widget.currentIndex() if hasattr(self, 'tab_widget') else -1
        try:
            from core.game_over import trigger_game_over
            success = trigger_game_over(self, current_tab_index, game_over_message)
            if success:
                print(f"  >> Rule '{rule_id}' Action: Game Over successfully triggered")
            else:
                print(f"  >> Rule '{rule_id}' Action: Game Over failed to trigger")
        except Exception as e:
            print(f"  >> Rule '{rule_id}' Action: Error triggering Game Over: {e}")
            import traceback
            traceback.print_exc()

    elif obj_type == 'Advance Time':
        advance_amount = _substitute_variables_in_string(obj.get('advance_amount', ''), tab_data, character_name)
        if not advance_amount:
            print(f"ERROR: Cannot advance time - advance_amount is empty")
            return
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot advance time - workflow_data_dir not found")
            return
        try:
            from datetime import datetime, timedelta
            import re
            current_time_str = None
            variables_file = tab_data.get('variables_file')
            if variables_file and os.path.exists(variables_file):
                try:
                    with open(variables_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            variables = json.loads(content)
                            current_time_str = variables.get('datetime')
                except Exception as e:
                    print(f"Error loading variables for time advancement: {e}")
            if not current_time_str:
                print(f"ERROR: Cannot advance time - no current datetime found in variables")
                return
            current_time = datetime.fromisoformat(current_time_str)
            print(f"[ADVANCE TIME] Current time: {current_time.isoformat()}")
            total_seconds = 0
            advance_amount_lower = advance_amount.lower().replace(' ', '')
            time_patterns = [
                (r'(\d+)d', lambda m: int(m.group(1)) * 24 * 3600),
                (r'(\d+)h', lambda m: int(m.group(1)) * 3600),
                (r'(\d+)m', lambda m: int(m.group(1)) * 60),
                (r'(\d+)s', lambda m: int(m.group(1)))
            ]
            for pattern, converter in time_patterns:
                matches = re.finditer(pattern, advance_amount_lower)
                for match in matches:
                    total_seconds += converter(match)
            if total_seconds == 0:
                print(f"ERROR: Could not parse time advancement amount: {advance_amount}")
                return
            advancement_mode = 'static'
            time_passage_file = os.path.join(workflow_data_dir, "resources", "data files", "settings", "time_passage.json")
            if os.path.exists(time_passage_file):
                try:
                    with open(time_passage_file, 'r', encoding='utf-8') as f:
                        time_passage_data = json.load(f)
                        advancement_mode = time_passage_data.get('advancement_mode', 'static')
                except Exception as e:
                    print(f"Error loading time passage data: {e}")
            automatic_advancement = timedelta(0)
            last_real_time = variables.get('_last_real_time_update')
            if last_real_time and advancement_mode == 'realtime':
                try:
                    from datetime import datetime
                    now = datetime.now()
                    last_update_dt = datetime.fromisoformat(last_real_time)
                    real_time_delta = now - last_update_dt
                    time_multiplier = time_passage_data.get('time_multiplier', 1.0)
                    if time_multiplier > 0.0:
                        automatic_advancement = real_time_delta * time_multiplier
                        print(f"[ADVANCE TIME] Automatic advancement would be: {automatic_advancement}")
                except Exception as e:
                    print(f"Error calculating automatic advancement: {e}")
            total_advancement = automatic_advancement + timedelta(seconds=total_seconds)
            new_time = current_time + total_advancement
            print(f"[ADVANCE TIME] Total advancement: {automatic_advancement} + {timedelta(seconds=total_seconds)} = {total_advancement}")
            print(f"[ADVANCE TIME] Advancing to: {new_time.isoformat()}")
            if variables_file:
                try:
                    with open(variables_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            variables = json.loads(content)
                        else:
                            variables = {}
                except Exception as e:
                    print(f"Error loading variables file: {e}")
                    variables = {}
                variables['datetime'] = new_time.isoformat()
                variables['game_datetime'] = new_time.isoformat()
                variables['_last_real_time_update'] = datetime.now().isoformat()
                variables['_manual_time_advancement'] = True
                try:
                    with open(variables_file, 'w', encoding='utf-8') as f:
                        json.dump(variables, f, indent=2, ensure_ascii=False)
                    if tab_data:
                        tab_data['variables'] = variables.copy()
                    print(f"✓ Successfully advanced time by {advance_amount} to {new_time.isoformat()}")
                except Exception as e:
                    print(f"✗ FAILED to save advanced time: {e}")
        except Exception as e:
            print(f"ERROR: Failed to advance time: {e}")
            import traceback
            traceback.print_exc()
    
    elif obj_type == 'Change Time Passage':
        passage_mode = obj.get('passage_mode', 'static')
        time_multiplier = obj.get('time_multiplier', 1.0)
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot change time passage - workflow_data_dir not found")
            return
        try:
            settings_dir = os.path.join(workflow_data_dir, "resources", "data files", "settings")
            os.makedirs(settings_dir, exist_ok=True)
            time_passage_file = os.path.join(settings_dir, "time_passage.json")
            time_passage_data = {}
            if os.path.exists(time_passage_file):
                try:
                    with open(time_passage_file, 'r', encoding='utf-8') as f:
                        time_passage_data = json.load(f)
                except Exception as e:
                    print(f"Error loading time passage data: {e}")
                    time_passage_data = {}
            time_passage_data['advancement_mode'] = passage_mode
            time_passage_data['time_multiplier'] = time_multiplier
            try:
                with open(time_passage_file, 'w', encoding='utf-8') as f:
                    json.dump(time_passage_data, f, indent=2, ensure_ascii=False)
                print(f"✓ Successfully changed time passage mode to {passage_mode} with multiplier {time_multiplier}x")
            except Exception as e:
                print(f"✗ FAILED to save time passage settings: {e}")
        except Exception as e:
            print(f"ERROR: Failed to change time passage: {e}")
            import traceback
            traceback.print_exc()
    elif obj_type == 'Delete Character':
        target_character_name = obj.get('target_character_name', '').strip()
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot delete character - workflow_data_dir not found")
            return
        
        if not target_character_name and character_name:
            target_character_name = character_name
        elif not target_character_name:
            print(f"ERROR: Cannot delete character - no target character name provided and no character context")
            return
        
        if character_name == 'Narrator':
            print(f"ERROR: Cannot delete character - Delete Character action does not work for Narrator")
            return
        
        try:
            variables_file = os.path.join(workflow_data_dir, "game", "variables.json")
            variables = {}
            if os.path.exists(variables_file):
                try:
                    with open(variables_file, 'r', encoding='utf-8') as f:
                        variables = json.load(f)
                except Exception as e:
                    print(f"Error loading variables file: {e}")
                    variables = {}
            
            characters_to_delete = variables.get('CharactersToDelete', [])
            if not isinstance(characters_to_delete, list):
                characters_to_delete = []
            
            if target_character_name not in characters_to_delete:
                characters_to_delete.append(target_character_name)
                variables['CharactersToDelete'] = characters_to_delete
                
                try:
                    with open(variables_file, 'w', encoding='utf-8') as f:
                        json.dump(variables, f, indent=2, ensure_ascii=False)
                    print(f"✓ Successfully marked character '{target_character_name}' for deletion")
                except Exception as e:
                    print(f"✗ FAILED to save deletion mark: {e}")
            else:
                print(f"Character '{target_character_name}' is already marked for deletion")
        except Exception as e:
            print(f"ERROR: Failed to mark character for deletion: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"Warning: Unknown rule side effect type: {obj_type}")
        return
    next_rule_id = obj.get('next_rule')
    if next_rule_id and next_rule_id != "None":
        tab_data = self.get_current_tab_data()
        if tab_data:
            all_rules = tab_data.get('thought_rules', [])
            next_rule_data = None
            for r in all_rules:
                if r.get('id') == next_rule_id:
                    next_rule_data = r
                    break
            if next_rule_data:
                user_msg_for_next_rule = current_user_msg if current_user_msg is not None else ''
                assistant_msg_for_next_rule = prev_assistant_msg if prev_assistant_msg is not None else ''
                QTimer.singleShot(0, lambda nr=next_rule_data: _process_specific_rule(self, nr, user_msg_for_next_rule, assistant_msg_for_next_rule, rules_list=tab_data.get('thought_rules', []), rule_index=None, triggered_directly=True))

def _substitute_variables_in_string(text_to_process, tab_data, actor_name_context=None):
    if not text_to_process or not isinstance(text_to_process, str):
        return text_to_process
    from core.utils import (
        _get_player_character_name,
        _get_or_create_actor_data,
        _get_player_current_setting_name,
        _find_setting_file_prioritizing_game_dir,
        _load_json_safely
    )
    result_text = text_to_process
    workflow_data_dir = tab_data.get('workflow_data_dir') if tab_data else None
    if '(character)' in result_text.lower() and actor_name_context:
        result_text = re.sub(r'(?<!\[)\(character\)(?![^,\]]*\])', actor_name_context, result_text, flags=re.IGNORECASE)
    if '(player)' in result_text.lower() and workflow_data_dir:
        player_name = _get_player_character_name(workflow_data_dir)
        if player_name:
            result_text = re.sub(r'\(player\)', player_name, result_text, flags=re.IGNORECASE)
            result_text = re.sub(r'\(Player\)', player_name, result_text)
    if '(setting)' in result_text.lower() and workflow_data_dir:
        setting_name = _get_player_current_setting_name(workflow_data_dir)
        if setting_name and setting_name != "Unknown Setting":
            result_text = re.sub(r'\(setting\)', setting_name, result_text, flags=re.IGNORECASE)
    if workflow_data_dir:
        class DummySelf:
            pass
        dummy_self = DummySelf()
        def get_var_value(scope, var_name):
            if scope == "global":
                variables_file = os.path.join(workflow_data_dir, "game", "variables.json")
                if os.path.exists(variables_file):
                    try:
                        with open(variables_file, 'r', encoding='utf-8') as f:
                            variables = json.load(f)
                            return variables.get(var_name, "")
                    except:
                        return ""
                return ""
            elif scope == "player":
                player_name = _get_player_character_name(workflow_data_dir)
                if player_name:
                    actor_data, _ = _get_or_create_actor_data(dummy_self, workflow_data_dir, player_name)
                    return actor_data.get('variables', {}).get(var_name, "")
                return ""
            elif scope == "actor" or scope == "character":
                if actor_name_context:
                    actor_data, _ = _get_or_create_actor_data(dummy_self, workflow_data_dir, actor_name_context)
                    return actor_data.get('variables', {}).get(var_name, "")
                return ""
            elif scope == "setting":
                current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                if current_setting_name and current_setting_name != "Unknown Setting":
                    setting_file_path, _ = _find_setting_file_prioritizing_game_dir(dummy_self, workflow_data_dir, current_setting_name)
                    if setting_file_path and os.path.exists(setting_file_path):
                        setting_data = _load_json_safely(setting_file_path)
                        if setting_data:
                            return setting_data.get('variables', {}).get(var_name, "")
                return ""
            return ""
        
        def replace_match(match):
            scope = match.group(1).lower()
            var_name = match.group(2).strip()
            val = get_var_value(scope, var_name)
            return str(val)
        pattern = r'\[(global|player|actor|character|setting),\s*([^,\]]+?)\s*\]'
        result_text = re.sub(pattern, replace_match, result_text)
    return result_text

def _apply_item_consume_effects(item_identifier, consume_scope, workflow_data_dir, tab_data, character_name=None):
    if not item_identifier or not workflow_data_dir:
        return
    
    item_name = item_identifier
    
    if item_identifier.lower().startswith('item_'):
        try:
            from core.utils import _get_player_character_name, _get_player_current_setting_name
            player_name = _get_player_character_name(workflow_data_dir)
            current_setting_name = _get_player_current_setting_name(workflow_data_dir)
            
            found_item_name = None
            
            if player_name:
                actor_data, _ = _get_or_create_actor_data(None, workflow_data_dir, player_name)
                if actor_data and 'inventory' in actor_data:
                    for item in actor_data['inventory']:
                        if item.get('item_id', '').lower() == item_identifier.lower():
                            found_item_name = item.get('name')
                            break
            
            if not found_item_name and current_setting_name:
                setting_file_path, _ = _find_setting_file_prioritizing_game_dir(None, workflow_data_dir, current_setting_name)
                if setting_file_path and os.path.exists(setting_file_path):
                    with open(setting_file_path, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                    inventory = setting_data.get('inventory', [])
                    for item in inventory:
                        if item.get('item_id', '').lower() == item_identifier.lower():
                            found_item_name = item.get('name')
                            break
            
            if found_item_name:
                item_name = found_item_name
                print(f"[DEBUG] Found item name '{found_item_name}' for item ID '{item_identifier}' in consume effects")
            else:
                print(f"[DEBUG] Could not find item name for item ID '{item_identifier}' in consume effects")
        except Exception as e:
            print(f"[DEBUG] Error looking up item name for ID '{item_identifier}' in consume effects: {e}")
    
    if not _is_item_consumable(item_identifier, workflow_data_dir):
        print(f"ERROR: Cannot apply consume effects to '{item_identifier}' - item is not marked as consumable")
        return
    
    items_dir = os.path.join(workflow_data_dir, "resources", "data files", "items")
    if not os.path.exists(items_dir):
        print(f"WARNING: Items directory not found: {items_dir}")
        return
    
    item_ref = None
    for category in os.listdir(items_dir):
        category_path = os.path.join(items_dir, category)
        if os.path.isdir(category_path):
            for filename in os.listdir(category_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(category_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            item_data = json.load(f)
                        if item_data.get('name') == item_name:
                            item_ref = item_data
                            break
                    except Exception as e:
                        print(f"ERROR: Failed to load item file {file_path}: {e}")
                        continue
        if item_ref:
            break
    
    if not item_ref:
        print(f"WARNING: Item '{item_name}' not found in items directory")
        return
    
    variables_to_apply = item_ref.get('variable_actions', [])
    if not variables_to_apply:
        print(f"INFO: Item '{item_name}' has no variable effects to apply")
        return
    
    print(f"  >> Applying consume effects for '{item_name}' to scope '{consume_scope}'")
    for var_effect in variables_to_apply:
        if not isinstance(var_effect, dict):
            continue
        var_name = var_effect.get('variable_name', '')
        operation = var_effect.get('operation', '')
        value = var_effect.get('value', '')
        if not var_name:
            continue
        if isinstance(value, str):
            value = _substitute_variables_in_string(value, tab_data, character_name)
        _apply_variable_effect(var_name, operation, value, consume_scope, workflow_data_dir, tab_data, character_name)

def _apply_variable_effect(var_name, operation, value, scope, workflow_data_dir, tab_data, character_name=None):
    try:
        if scope == "Player":
            player_name = _get_player_character_name(workflow_data_dir)
            if player_name:
                actor_data, actor_path = _get_or_create_actor_data(None, workflow_data_dir, player_name)
                if actor_data:
                    if 'variables' not in actor_data:
                        actor_data['variables'] = {}
                    _apply_operation_to_variable(actor_data['variables'], var_name, operation, value)
                    with open(actor_path, 'w', encoding='utf-8') as f:
                        json.dump(actor_data, f, indent=2, ensure_ascii=False)
                    print(f"    Applied {operation} '{var_name}' = '{value}' to Player")
        
        elif scope == "Character":
            if character_name:
                actor_data, actor_path = _get_or_create_actor_data(None, workflow_data_dir, character_name)
                if actor_data:
                    if 'variables' not in actor_data:
                        actor_data['variables'] = {}
                    _apply_operation_to_variable(actor_data['variables'], var_name, operation, value)
                    with open(actor_path, 'w', encoding='utf-8') as f:
                        json.dump(actor_data, f, indent=2, ensure_ascii=False)
                    print(f"    Applied {operation} '{var_name}' = '{value}' to Character '{character_name}'")
        
        elif scope == "Setting":
            current_setting_name = _get_player_current_setting_name(workflow_data_dir)
            if current_setting_name and current_setting_name != "Unknown Setting":
                setting_file_path, _ = _find_setting_file_prioritizing_game_dir(None, workflow_data_dir, current_setting_name)
                if setting_file_path and os.path.exists(setting_file_path):
                    with open(setting_file_path, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                    if 'variables' not in setting_data:
                        setting_data['variables'] = {}
                    _apply_operation_to_variable(setting_data['variables'], var_name, operation, value)
                    with open(setting_file_path, 'w', encoding='utf-8') as f:
                        json.dump(setting_data, f, indent=2, ensure_ascii=False)
                    print(f"    Applied {operation} '{var_name}' = '{value}' to Setting '{current_setting_name}'")
        
        elif scope == "Scene Characters":
            current_setting_name = _get_player_current_setting_name(workflow_data_dir)
            if current_setting_name and current_setting_name != "Unknown Setting":
                setting_file_path, _ = _find_setting_file_prioritizing_game_dir(None, workflow_data_dir, current_setting_name)
                if setting_file_path and os.path.exists(setting_file_path):
                    with open(setting_file_path, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                    player_name = _get_player_character_name(workflow_data_dir)
                    if player_name:
                        actor_data, actor_path = _get_or_create_actor_data(None, workflow_data_dir, player_name)
                        if actor_data:
                            if 'variables' not in actor_data:
                                actor_data['variables'] = {}
                            _apply_operation_to_variable(actor_data['variables'], var_name, operation, value)
                            with open(actor_path, 'w', encoding='utf-8') as f:
                                json.dump(actor_data, f, indent=2, ensure_ascii=False)
                            print(f"    Applied {operation} '{var_name}' = '{value}' to Player")
                    scene_characters = setting_data.get('characters', [])
                    for char_name in scene_characters:
                        if char_name != player_name:
                            actor_data, actor_path = _get_or_create_actor_data(None, workflow_data_dir, char_name)
                            if actor_data:
                                if 'variables' not in actor_data:
                                    actor_data['variables'] = {}
                                _apply_operation_to_variable(actor_data['variables'], var_name, operation, value)
                                with open(actor_path, 'w', encoding='utf-8') as f:
                                    json.dump(actor_data, f, indent=2, ensure_ascii=False)
                                print(f"    Applied {operation} '{var_name}' = '{value}' to Character '{char_name}'")
    except Exception as e:
        print(f"ERROR: Failed to apply variable effect '{var_name}' to scope '{scope}': {e}")

def _apply_operation_to_variable(variables_dict, var_name, operation, value):
    current_value = variables_dict.get(var_name, 0)
    try:
        if operation in ['increment', 'decrement', 'multiply', 'divide']:
            try:
                if isinstance(value, str):
                    value = float(value) if '.' in value else int(value)
                elif not isinstance(value, (int, float)):
                    value = 0
            except (ValueError, TypeError):
                value = 0
        if operation == 'set':
            variables_dict[var_name] = value
        elif operation == 'increment':
            if isinstance(current_value, (int, float)) and isinstance(value, (int, float)):
                variables_dict[var_name] = current_value + value
            else:
                variables_dict[var_name] = value
        elif operation == 'decrement':
            if isinstance(current_value, (int, float)) and isinstance(value, (int, float)):
                variables_dict[var_name] = current_value - value
            else:
                variables_dict[var_name] = value
        elif operation == 'multiply':
            if isinstance(current_value, (int, float)) and isinstance(value, (int, float)):
                variables_dict[var_name] = current_value * value
            else:
                variables_dict[var_name] = value
        elif operation == 'divide':
            if isinstance(current_value, (int, float)) and isinstance(value, (int, float)) and value != 0:
                variables_dict[var_name] = current_value / value
            else:
                variables_dict[var_name] = value
        else:
            variables_dict[var_name] = value
    except Exception as e:
        print(f"ERROR: Failed to apply operation '{operation}' to variable '{var_name}': {e}")
        variables_dict[var_name] = value

def _is_item_consumable(item_identifier, workflow_data_dir):
    if not item_identifier or not workflow_data_dir:
        return False
    
    items_dir = os.path.join(workflow_data_dir, "resources", "data files", "items")
    if not os.path.exists(items_dir):
        print(f"WARNING: Items directory not found: {items_dir}")
        return False
    
    item_name = item_identifier
    
    if item_identifier.lower().startswith('item_'):
        try:
            from core.utils import _get_player_character_name, _get_player_current_setting_name
            player_name = _get_player_character_name(workflow_data_dir)
            current_setting_name = _get_player_current_setting_name(workflow_data_dir)
            
            found_item_name = None
            
            if player_name:
                actor_data, _ = _get_or_create_actor_data(None, workflow_data_dir, player_name)
                if actor_data and 'inventory' in actor_data:
                    for item in actor_data['inventory']:
                        if item.get('item_id', '').lower() == item_identifier.lower():
                            found_item_name = item.get('name')
                            break
            
            if not found_item_name and current_setting_name:
                setting_file_path, _ = _find_setting_file_prioritizing_game_dir(None, workflow_data_dir, current_setting_name)
                if setting_file_path and os.path.exists(setting_file_path):
                    with open(setting_file_path, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                    inventory = setting_data.get('inventory', [])
                    for item in inventory:
                        if item.get('item_id', '').lower() == item_identifier.lower():
                            found_item_name = item.get('name')
                            break
            
            if found_item_name:
                item_name = found_item_name
                print(f"[DEBUG] Found item name '{found_item_name}' for item ID '{item_identifier}'")
            else:
                print(f"[DEBUG] Could not find item name for item ID '{item_identifier}'")
        except Exception as e:
            print(f"[DEBUG] Error looking up item name for ID '{item_identifier}': {e}")
    
    for category in os.listdir(items_dir):
        category_path = os.path.join(items_dir, category)
        if os.path.isdir(category_path):
            for filename in os.listdir(category_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(category_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            item_data = json.load(f)
                        if item_data.get('name') == item_name:
                            properties = item_data.get('properties', '')
                            is_consumable = 'Consumable' in properties
                            print(f"[DEBUG] Item '{item_name}' consumable: {is_consumable} (properties: {properties})")
                            return is_consumable
                    except Exception as e:
                        print(f"ERROR: Failed to load item file {file_path}: {e}")
                        continue
    print(f"WARNING: Item '{item_name}' not found in items directory")
    return False

def _determine_items_with_inference(chatbot_instance, text, text_scope, scope, owner, description, location, return_type, workflow_data_dir, tab_data, character_name, current_user_msg, prev_assistant_msg):
    try:
        context_text = _get_context_for_text_scope(text_scope, tab_data, current_user_msg, prev_assistant_msg)
        if not context_text:
            print(f"WARNING: No context available for text scope '{text_scope}'")
            return "NONE"
        items_data = _get_items_from_scope(scope, workflow_data_dir, tab_data, character_name)
        if not items_data:
            print(f"WARNING: No items found in scope '{scope}'")
            return "NONE"
        if owner:
            filtered_items = [item for item in items_data if item.get('owner', '').lower() == owner.lower()]
            if not filtered_items:
                print(f"WARNING: No items found with owner '{owner}' in scope '{scope}'")
                return "NONE"
            items_data = filtered_items
        items_text = _format_items_for_llm(items_data)
        if return_type == 'Return Multiple Items':
            prompt = _create_determine_multiple_items_prompt(text, context_text, items_text)
        else:
            prompt = _create_determine_single_item_prompt(text, context_text, items_text)
        model = chatbot_instance.get_current_model()
        max_tokens = 50
        temperature = 0.1
        context = [
            {"role": "user", "content": prompt}
        ]
        result = chatbot_instance.run_utility_inference_sync(context, model, max_tokens, temperature)
        if not result:
            print(f"ERROR: Inference call failed for Determine Items")
            return "NONE"
        parsed_result = _parse_determine_items_result(result, return_type)
        print(f"[DETERMINE ITEMS] LLM Response: '{result}' -> Parsed: '{parsed_result}'")
        return parsed_result
    except Exception as e:
        print(f"ERROR: Failed to determine items with inference: {e}")
        import traceback
        traceback.print_exc()
        return "NONE"

def _get_context_for_text_scope(text_scope, tab_data, current_user_msg, prev_assistant_msg):
    if text_scope == 'Full Conversation':
        return tab_data.get('context', [])
    elif text_scope == 'User Message':
        if current_user_msg:
            return current_user_msg
        context = tab_data.get('context', [])
        for msg in reversed(context):
            if msg.get('role') == 'user':
                return msg.get('content', '')
        return ""
    elif text_scope == 'LLM Reply':
        if prev_assistant_msg:
            return prev_assistant_msg
        context = tab_data.get('context', [])
        for msg in reversed(context):
            if msg.get('role') == 'assistant':
                return msg.get('content', '')
        return ""
    elif text_scope == 'Conversation plus LLM Reply':
        context = tab_data.get('context', [])
        if prev_assistant_msg:
            context.append({"role": "assistant", "content": prev_assistant_msg})
        return context
    else:
        return ""

def _get_items_from_scope(scope, workflow_data_dir, tab_data, character_name):
    items = []
    if scope == 'Player':
        player_name = _get_player_character_name(workflow_data_dir)
        if player_name:
            actor_data, _ = _get_or_create_actor_data(None, workflow_data_dir, player_name)
            if actor_data and 'inventory' in actor_data:
                items.extend(actor_data['inventory'])
    elif scope == 'Character':
        if character_name:
            actor_data, _ = _get_or_create_actor_data(None, workflow_data_dir, character_name)
            if actor_data and 'inventory' in actor_data:
                items.extend(actor_data['inventory'])
    elif scope == 'Setting':
        current_setting_name = _get_player_current_setting_name(workflow_data_dir)
        if current_setting_name:
            setting_file_path, _ = _find_setting_file_prioritizing_game_dir(None, workflow_data_dir, current_setting_name)
            if setting_file_path and os.path.exists(setting_file_path):
                try:
                    with open(setting_file_path, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                    if 'inventory' in setting_data:
                        items.extend(setting_data['inventory'])
                except Exception as e:
                    print(f"ERROR: Failed to load setting inventory: {e}")
    return items

def _format_items_for_llm(items_data):
    if not items_data:
        return "No items available."
    formatted_items = []
    for item in items_data:
        item_id = item.get('item_id', 'unknown')
        name = item.get('name', 'unnamed')
        owner = item.get('owner', 'unknown')
        description = item.get('description', 'no description')
        location = item.get('location', 'unknown location')
        quantity = item.get('quantity', 1)
        formatted_item = f"Item ID: {item_id}\nName: {name}\nOwner: {owner}\nDescription: {description}\nLocation: {location}\nQuantity: {quantity}"
        formatted_items.append(formatted_item)
    return "\n\n".join(formatted_items)

def _create_determine_single_item_prompt(text, context_text, items_text):
    context_str = ""
    if isinstance(context_text, list):
        context_lines = []
        for msg in context_text:
            role = msg.get('role', 'unknown').capitalize()
            content = msg.get('content', '')
            context_lines.append(f"{role}: {content}")
        context_str = "\n".join(context_lines)
    else:
        context_str = str(context_text)
    
    prompt = f"""You are an AI assistant that analyzes text and item data to determine which SINGLE item best matches the given criteria. Return ONLY the Item ID of the best match, or NONE if no items feasibly match.

CONTEXT:
{context_str}

AVAILABLE ITEMS:
{items_text}

QUESTION: {text}

INSTRUCTIONS:
- Return a SINGLE Item ID (the best match)
- If no items match, return "NONE"
- If no items are available, return "NONE"
- Return ONLY the Item ID or "NONE" - no other text

RESPONSE:"""
    
    return prompt

def _create_determine_multiple_items_prompt(text, context_text, items_text):
    context_str = ""
    if isinstance(context_text, list):
        context_lines = []
        for msg in context_text:
            role = msg.get('role', 'unknown').capitalize()
            content = msg.get('content', '')
            context_lines.append(f"{role}: {content}")
        context_str = "\n".join(context_lines)
    else:
        context_str = str(context_text)
    
    prompt = f"""You are an AI assistant that analyzes text and item data to determine which MULTIPLE items match the given criteria. Return ONLY a comma-separated list of Item IDs, or NONE if no items feasibly match.

CONTEXT:
{context_str}

AVAILABLE ITEMS:
{items_text}

QUESTION: {text}

INSTRUCTIONS:
- Return a comma-separated list of Item IDs (e.g., "item_123,item_456")
- If no items match, return "NONE"
- If no items are available, return "NONE"
- Return ONLY the Item IDs or "NONE" - no other text

RESPONSE:"""
    
    return prompt

def _parse_determine_items_result(result, return_type):
    if not result:
        return "NONE"
    result = result.strip().upper()
    if result in ["NONE", "NO", "NONE.", "NO."]:
        return "NONE"
    if return_type == 'Return Multiple Items':
        item_ids = [item_id.strip() for item_id in result.split(',') if item_id.strip()]
        if not item_ids:
            return "NONE"
        return ",".join(item_ids)
    else:
        return result

def _extract_item_details_from_result(result, items_data):
    if not result or result == "NONE" or not items_data:
        return {}
    
    if ',' in result:
        item_ids = [item_id.strip().upper() for item_id in result.split(',')]
        names = []
        descriptions = []
        locations = []
        owners = []
        
        for item_id in item_ids:
            item = _find_item_by_id(items_data, item_id)
            if item:
                names.append(item.get('name', ''))
                descriptions.append(item.get('description', ''))
                locations.append(item.get('location', ''))
                owners.append(item.get('owner', ''))
        
        return {
            'names': ', '.join(names),
            'descriptions': ', '.join(descriptions),
            'locations': ', '.join(locations),
            'owners': ', '.join(owners)
        }
    else:
        item_id = result.upper()
        item = _find_item_by_id(items_data, item_id)
        if item:
            return {
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'location': item.get('location', ''),
                'owner': item.get('owner', '')
            }
        return {}

def _find_item_by_id(items_data, item_id):
    for item in items_data:
        item_id_in_data = item.get('item_id', '')
        if item_id_in_data.upper() == item_id.upper():
            return item
    return None

def _save_global_variable(workflow_data_dir, var_name, var_value):
    if not workflow_data_dir:
        return
    variables_file = os.path.join(workflow_data_dir, "game", "variables.json")
    try:
        variables = {}
        if os.path.exists(variables_file):
            with open(variables_file, 'r', encoding='utf-8') as f:
                variables = json.load(f)
        variables[var_name] = var_value
        os.makedirs(os.path.dirname(variables_file), exist_ok=True)
        with open(variables_file, 'w', encoding='utf-8') as f:
            json.dump(variables, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR: Failed to save global variable '{var_name}': {e}")

def _load_items_data(workflow_data_dir, scope='Setting', character_name=None):
    if not workflow_data_dir:
        return []
    items = []
    if scope == 'Player':
        from core.utils import _get_player_character_name, _get_or_create_actor_data
        player_name = _get_player_character_name(workflow_data_dir)
        if player_name:
            actor_data, _ = _get_or_create_actor_data(None, workflow_data_dir, player_name)
            if actor_data and 'inventory' in actor_data:
                items.extend(actor_data['inventory'])
    elif scope == 'Character':
        if character_name:
            from core.utils import _get_or_create_actor_data
            actor_data, _ = _get_or_create_actor_data(None, workflow_data_dir, character_name)
            if actor_data and 'inventory' in actor_data:
                items.extend(actor_data['inventory'])
    elif scope == 'Setting':
        from core.utils import _get_player_current_setting_name, _find_setting_file_prioritizing_game_dir
        current_setting_name = _get_player_current_setting_name(workflow_data_dir)
        if current_setting_name:
            setting_file_path, _ = _find_setting_file_prioritizing_game_dir(None, workflow_data_dir, current_setting_name)
            if setting_file_path and os.path.exists(setting_file_path):
                try:
                    with open(setting_file_path, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                    if 'inventory' in setting_data:
                        items.extend(setting_data['inventory'])
                except Exception as e:
                    print(f"ERROR: Failed to load setting inventory: {e}")
    return items
