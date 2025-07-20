from PyQt5.QtCore import QTimer
import json
import os
import random
import time
from core.utils import _get_player_current_setting_name, _get_or_create_actor_data, _find_player_character_file, _load_json_safely, _find_setting_file_prioritizing_game_dir, _get_player_character_name, _find_actor_file_path
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
        if item_identifier.startswith('item_') and item.get('item_id') == item_identifier:
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
        'item_id': f"item_{int(time.time() * 1000)}",
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
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot generate random list - workflow_data_dir not found")
            return
        instructions = obj.get('instructions', '')
        generator_name = obj.get('generator_name', '')
        is_permutate = obj.get('is_permutate', False)
        model_override = obj.get('model_override', None)
        generate_context = obj.get('generate_context', 'No Context')
        if generate_context != 'No Context':
            context_text = ""
            if generate_context == 'Last Exchange':
                context_text = self.get_current_context()
            elif generate_context == 'User Message':
                current_context = self.get_current_context()
                if current_context:
                    lines = current_context.strip().split('\n')
                    user_lines = [line for line in lines if line.startswith('User:')]
                    if user_lines:
                        context_text = user_lines[-1]
            elif generate_context == 'Full Conversation':
                context_text = self.get_current_context()
            if context_text:
                instructions = f"Based on the following conversation context, {instructions}\n\nConversation context:\n{context_text}"
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
                        sample_result = ", ".join(sampled_values)
                    else:
                        sample_result = f"Error: No items found in generator {generator_data.get('name', 'Unknown')}"
                except Exception as e:
                    print(f"Error sampling from generator: {e}")
                    sample_result = f"Error sampling from generator: {e}"
            else:
                sample_result = f"Error: Could not find generator file to sample from. Result: {result}"
            store_value = sample_result if sample_result is not None else str(result)
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
                    variables[var_name] = store_value
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
                        actor_data['variables'][var_name] = store_value
                        
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
                    player_data['variables'][var_name] = store_value
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
                            setting_data['variables'][var_name] = store_value
                            with open(setting_file, 'w', encoding='utf-8') as f:
                                json.dump(setting_data, f, indent=2, ensure_ascii=False)
                                f.flush()
                                os.fsync(f.fileno())
                            print(f"Successfully stored sampled result in setting variable: {var_name} for {current_setting}")
                        except Exception as e:
                            print(f"Error updating setting data: {e}")
                    else:
                        print(f"ERROR: Could not find setting file for {current_setting}")
                else:
                    print(f"ERROR: Could not determine current setting")
            
            elif var_scope == 'Scene Characters':
                if character_name:
                    actor_data, actor_path = _get_or_create_actor_data(self, workflow_data_dir, character_name)
                    if actor_data:
                        if 'variables' not in actor_data:
                            actor_data['variables'] = {}
                        actor_data['variables'][var_name] = store_value
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
                        new_value = float(param_value)
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
        message_text = obj.get('value', '')
        position = obj.get('position', 'prepend')
        sysmsg_position = obj.get('system_message_position', 'first')
        self._cot_system_modifications.append({
            'action': message_text,
            'position': position,
            'system_message_position': sysmsg_position,
            'switch_model': None
        })
    elif obj_type == 'switch_model':
        model_name = obj.get('value', '')
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
                print(f"    <- _get_or_create_actor_data returned: Path={actor_path}, Data={actor_data}")
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
                    print(f"✓ Successfully updated global variable: {var_name} = {new_value} (file and cache updated)")
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
                    print(f"    -> Current setting identified as: '{current_setting_name}' by _get_player_current_setting_name")
                setting_file_result = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, current_setting_name)
                setting_file_path = setting_file_result[0] if isinstance(setting_file_result, tuple) else setting_file_result
                if not setting_file_path or not os.path.exists(setting_file_path):
                    print(f"ERROR: Setting file for '{current_setting_name}' not found at expected path.")
                    return
                try:
                    with open(setting_file_path, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                        print(f"    -> Successfully loaded setting JSON")
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
                        print(f"    ✓ Successfully updated variable for character '{char_name}'")
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
                'item_id': f"item_{int(time.time() * 1000)}",
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
        item_name = obj.get('item_name', '')
        quantity = obj.get('quantity', '1')
        target_type = obj.get('target_type', 'Setting')
        target_name = obj.get('target_name', '')
        target_container_enabled = obj.get('target_container_enabled', False)
        target_item_name = obj.get('target_item_name', '')
        target_container_name = obj.get('target_container_name', '')
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot process Remove Item - workflow_data_dir not found")
            return
        if not item_name:
            print(f"ERROR: Cannot remove item - item_name is empty")
            return
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
            if target_container_enabled and target_item_name and target_container_name:
                removed_count = _remove_item_from_container(inventory, target_item_name, target_container_name, item_name, int(quantity) if quantity.isdigit() else 1)
                if removed_count == 0:
                    print(f"WARNING: No items '{item_name}' found in container '{target_container_name}' of item '{target_item_name}' in {target_type} '{target_name}'")
                    return
                print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully removed {removed_count} of item '{item_name}' from container '{target_container_name}' in {target_type} '{target_name}'")
            else:
                items_to_remove = int(quantity) if quantity.isdigit() else 1
                removed_count = 0
                
                for i in range(len(inventory) - 1, -1, -1):
                    item = inventory[i]
                    if item.get('name') == item_name:
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
                if removed_count == 0:
                    print(f"WARNING: No items '{item_name}' found in {target_type} '{target_name}'")
                    return
                print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully removed {removed_count} of item '{item_name}' from {target_type} '{target_name}'")
            with open(target_file_path, 'w', encoding='utf-8') as f:
                json.dump(target_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ERROR: Failed to remove item '{item_name}' from {target_type} '{target_name}': {e}")
    
    elif obj_type == 'Move Item':
        item_name = obj.get('item_name', '')
        quantity = obj.get('quantity', 1)
        from_type = obj.get('from_type', '')
        from_name = obj.get('from_name', '')
        to_type = obj.get('to_type', '')
        to_name = obj.get('to_name', '')
        from_container_enabled = obj.get('from_container_enabled', False)
        from_item_name = obj.get('from_item_name', '')
        from_container_name = obj.get('from_container_name', '')
        to_container_enabled = obj.get('to_container_enabled', False)
        to_item_name = obj.get('to_item_name', '')
        to_container_name = obj.get('to_container_name', '')
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"ERROR: Cannot process Move Item - workflow_data_dir not found")
            return
        if not item_name:
            print(f"ERROR: Cannot move item - item_name is empty")
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
            if 'inventory' not in to_data:
                to_data['inventory'] = []
            items_to_move = int(quantity) if isinstance(quantity, str) and quantity.isdigit() else int(quantity)
            moved_count = 0
            if from_container_enabled and to_container_enabled and from_item_name and to_item_name and from_container_name and to_container_name:
                if from_file_path == to_file_path:
                    moved_count = _move_item_between_containers(from_inventory, from_item_name, from_container_name, 
                                                              to_item_name, to_container_name, item_name, items_to_move)
                else:
                    removed_count = _remove_item_from_container(from_inventory, from_item_name, from_container_name, item_name, items_to_move)
                    if removed_count == 0:
                        print(f"WARNING: No items '{item_name}' found in container '{from_container_name}' of item '{from_item_name}' in source {from_type} '{from_name}'")
                        return
                    new_item = {
                        'item_id': f"item_{int(time.time() * 1000)}",
                        'name': item_name,
                        'quantity': removed_count,
                        'owner': '',
                        'description': '',
                        'location': '',
                        'containers': {}
                    }
                    success = _add_item_to_container(to_inventory, to_item_name, to_container_name, new_item)
                    if not success:
                        _add_item_to_container(from_inventory, from_item_name, from_container_name, new_item)
                        print(f"ERROR: Cannot add item '{item_name}' to container '{to_container_name}' in item '{to_item_name}' in destination {to_type} '{to_name}' - target item or container not found")
                        return
                    moved_count = removed_count
                if moved_count > 0:
                    print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully moved {moved_count} of item '{item_name}' from container '{from_container_name}' to container '{to_container_name}'")
            elif from_container_enabled and from_item_name and from_container_name:
                removed_count = _remove_item_from_container(from_inventory, from_item_name, from_container_name, item_name, items_to_move)
                if removed_count == 0:
                    print(f"WARNING: No items '{item_name}' found in container '{from_container_name}' of item '{from_item_name}' in source {from_type} '{from_name}'")
                    return
                new_item = {
                    'item_id': f"item_{int(time.time() * 1000)}",
                    'name': item_name,
                    'quantity': removed_count,
                    'owner': '',
                    'description': '',
                    'location': '',
                    'containers': {}
                }
                to_inventory.append(new_item)
                moved_count = removed_count
                print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully moved {moved_count} of item '{item_name}' from container '{from_container_name}' to main inventory")
            elif to_container_enabled and to_item_name and to_container_name:
                for i in range(len(from_inventory) - 1, -1, -1):
                    item = from_inventory[i]
                    if item.get('name') == item_name:
                        current_quantity = item.get('quantity', 1)
                        if current_quantity <= items_to_move:
                            moved_count += current_quantity
                            from_inventory.pop(i)
                            items_to_move -= current_quantity
                            new_item = {
                                'item_id': f"item_{int(time.time() * 1000)}",
                                'name': item_name,
                                'quantity': current_quantity,
                                'owner': '',
                                'description': '',
                                'location': '',
                                'containers': {}
                            }
                            success = _add_item_to_container(to_inventory, to_item_name, to_container_name, new_item)
                            if not success:
                                from_inventory.append(new_item)
                                print(f"ERROR: Cannot add item '{item_name}' to container '{to_container_name}' in item '{to_item_name}' in destination {to_type} '{to_name}' - target item or container not found")
                                return
                        else:
                            item['quantity'] = current_quantity - items_to_move
                            moved_count += items_to_move
                            items_to_move = 0
                            new_item = {
                                'item_id': f"item_{int(time.time() * 1000)}",
                                'name': item_name,
                                'quantity': items_to_move,
                                'owner': '',
                                'description': '',
                                'location': '',
                                'containers': {}
                            }
                            success = _add_item_to_container(to_inventory, to_item_name, to_container_name, new_item)
                            if not success:
                                item['quantity'] = current_quantity
                                print(f"ERROR: Cannot add item '{item_name}' to container '{to_container_name}' in item '{to_item_name}' in destination {to_type} '{to_name}' - target item or container not found")
                                return
                        if items_to_move <= 0:
                            break
                if moved_count == 0:
                    print(f"WARNING: No items '{item_name}' found in source {from_type} '{from_name}'")
                    return
                print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully moved {moved_count} of item '{item_name}' from main inventory to container '{to_container_name}'")
            else:
                for i in range(len(from_inventory) - 1, -1, -1):
                    item = from_inventory[i]
                    if item.get('name') == item_name:
                        current_quantity = item.get('quantity', 1)
                        if current_quantity <= items_to_move:
                            moved_count += current_quantity
                            from_inventory.pop(i)
                            items_to_move -= current_quantity
                            new_item = {
                                'item_id': f"item_{int(time.time() * 1000)}",
                                'name': item_name,
                                'quantity': current_quantity,
                                'owner': '',
                                'description': '',
                                'location': '',
                                'containers': {}
                            }
                            to_inventory.append(new_item)
                        else:
                            item['quantity'] = current_quantity - items_to_move
                            moved_count += items_to_move
                            items_to_move = 0
                            
                            new_item = {
                                'item_id': f"item_{int(time.time() * 1000)}",
                                'name': item_name,
                                'quantity': items_to_move,
                                'owner': '',
                                'description': '',
                                'location': '',
                                'containers': {}
                            }
                            to_inventory.append(new_item)
                        if items_to_move <= 0:
                            break
                if moved_count == 0:
                    print(f"WARNING: No items '{item_name}' found in source {from_type} '{from_name}'")
                    return
                print(f"  >> Rule '{rule.get('id', 'Unknown')}' Action: Successfully moved {moved_count} of item '{item_name}' from {from_type} '{from_name}' to {to_type} '{to_name}'")
            from_data['inventory'] = from_inventory
            to_data['inventory'] = to_inventory
            with open(from_file_path, 'w', encoding='utf-8') as f:
                json.dump(from_data, f, indent=2, ensure_ascii=False)
            with open(to_file_path, 'w', encoding='utf-8') as f:
                json.dump(to_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ERROR: Failed to move item '{item_name}' from {from_type} '{from_name}' to {to_type} '{to_name}': {e}")
    
    elif obj_type == 'Game Over':
        game_over_message = obj.get('game_over_message', 'Game Over')
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
        advance_amount = obj.get('advance_amount', '')
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
    if '(character)' in result_text and actor_name_context:
        result_text = result_text.replace('(character)', actor_name_context)
    if '(player)' in result_text and workflow_data_dir:
        player_name = _get_player_character_name(workflow_data_dir)
        if player_name:
            result_text = result_text.replace('(player)', player_name)
    if '(setting)' in result_text and workflow_data_dir:
        setting_name = _get_player_current_setting_name(workflow_data_dir)
        if setting_name and setting_name != "Unknown Setting":
            result_text = result_text.replace('(setting)', setting_name)
    if workflow_data_dir:
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
                    actor_data, _ = _get_or_create_actor_data(None, workflow_data_dir, player_name)
                    return actor_data.get('variables', {}).get(var_name, "")
                return ""
            elif scope == "actor" or scope == "character":
                if actor_name_context:
                    actor_data, _ = _get_or_create_actor_data(None, workflow_data_dir, actor_name_context)
                    return actor_data.get('variables', {}).get(var_name, "")
                return ""
            elif scope == "setting":
                current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                if current_setting_name and current_setting_name != "Unknown Setting":
                    setting_file_path, _ = _find_setting_file_prioritizing_game_dir(None, workflow_data_dir, current_setting_name)
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
