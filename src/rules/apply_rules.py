from PyQt5.QtCore import QTimer
import json
import os
import random
from core.utils import _get_player_current_setting_name, _get_or_create_actor_data, _find_player_character_file, _load_json_safely, _find_setting_file_prioritizing_game_dir

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
                    if found_setting_file:
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