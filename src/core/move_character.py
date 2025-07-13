import os
import json
from core.make_inference import make_inference
from config import get_default_utility_model

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
    except Exception:
        return {}

def _save_json_safely(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def _summarize_follower_memory(follower_name, leader_name, scene_interactions, workflow_data_dir):
    game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    follower_file = os.path.join(game_actors_dir, f"{follower_name}.json")
    if not os.path.exists(follower_file):
        return
    with open(follower_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    memories = data.get("follower_memories", {})
    old_summary = memories.get(leader_name, "")
    if old_summary:
        prompt = f"""Here is the previous summary of {follower_name}'s adventures with {leader_name}:
{old_summary}

Here is what happened next:
{scene_interactions}

Please update the summary to include the new events, keeping it concise and continuous."""
    else:
        prompt = f"""Summarize the following interactions between {follower_name} and {leader_name} as a story so far:
{scene_interactions}
"""
    try:
        summary = make_inference(
            context=[{"role": "user", "content": prompt}],
            user_message=prompt,
            character_name=follower_name,
            url_type=get_default_utility_model(),
            max_tokens=256,
            temperature=0.2,
            is_utility_call=True
        )
        if summary:
            memories[leader_name] = summary.strip()
            data["follower_memories"] = memories
            with open(follower_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        pass

def move_characters(
    workflow_data_dir,
    actors_to_move,
    target_setting_name,
    player_name=None,
    mode='Setting',
    context_for_move=None,
    tab_data=None,
    advance_time=True
):
    result = {
        'success': False,
        'player_moved': False,
        'target_setting_file': None,
        'moved_actors': [],
        'error': None,
        'tab_data_updates': None,
        'process_scene_change_timers': False
    }
    if not workflow_data_dir or not actors_to_move:
        result['error'] = 'Missing required arguments.'
        return result
    name_mapping = {}
    reverse_mapping = {}
    game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    if os.path.exists(game_actors_dir):
        for filename in os.listdir(game_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(game_actors_dir, filename)
                character_data = _load_json_safely(file_path)
                if character_data and 'name' in character_data:
                    filename_base = os.path.splitext(filename)[0]
                    actual_name = character_data['name']
                    name_mapping[filename_base] = actual_name
                    reverse_mapping[actual_name] = filename_base
    resource_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if os.path.exists(resource_actors_dir):
        for root, dirs, files in os.walk(resource_actors_dir):
            for filename in files:
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(root, filename)
                    character_data = _load_json_safely(file_path)
                    if character_data and 'name' in character_data:
                        filename_base = os.path.splitext(filename)[0]
                        actual_name = character_data['name']
                        if filename_base not in name_mapping:
                            name_mapping[filename_base] = actual_name
                            reverse_mapping[actual_name] = filename_base
    normalized_actors_to_move = []
    for actor in actors_to_move:
        if actor in name_mapping:
            actual_name = name_mapping[actor]
            if actual_name not in normalized_actors_to_move:
                normalized_actors_to_move.append(actual_name)
        elif actor in reverse_mapping:
            if actor not in normalized_actors_to_move:
                normalized_actors_to_move.append(actor)
        else:
            if actor not in normalized_actors_to_move:
                normalized_actors_to_move.append(actor)
    actors_to_move = normalized_actors_to_move
    current_setting_name = None
    current_setting_file = None
    session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
    found = False
    for root, dirs, files in os.walk(session_settings_dir):
        dirs[:] = [d for d in dirs if d.lower() != 'saves']
        for filename in files:
            if filename.lower().endswith('_setting.json'):
                file_path = os.path.join(root, filename)
                setting_data = _load_json_safely(file_path)
                chars = setting_data.get('characters', [])
                if any(actor in chars for actor in actors_to_move) or (player_name in actors_to_move and "Player" in chars):
                    current_setting_name = setting_data.get('name')
                    current_setting_file = file_path
                    found = True
                    break
        if found:
            break
    if current_setting_name and current_setting_file:
        setting_data = _load_json_safely(current_setting_file)
        chars_in_setting = setting_data.get('characters', [])
        original_actors_to_move = actors_to_move.copy()
        for character_name in chars_in_setting:
            if not isinstance(character_name, str):
                print(f"[WARN] Skipping non-string character name: {character_name}")
                continue
            if character_name in original_actors_to_move:
                continue
            character_json_path = None
            filename_to_check = reverse_mapping.get(character_name, character_name)
            actor_file = os.path.join(workflow_data_dir, 'game', 'actors', f"{filename_to_check}.json")
            if os.path.exists(actor_file):
                character_json_path = actor_file
            else:
                for root, dirs, files in os.walk(os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')):
                    for filename in files:
                        if filename.lower() == f"{filename_to_check.lower()}.json":
                            character_json_path = os.path.join(root, filename)
                            break
            if character_json_path:
                character_data = _load_json_safely(character_json_path)
                variables = character_data.get('variables', {})
                following = variables.get('following', '')
                actual_character_name = character_data.get('name', character_name)
                if following == "Player" and player_name:
                    following = player_name
                if following and following in original_actors_to_move:
                    if actual_character_name not in actors_to_move:
                        actors_to_move.append(actual_character_name)
    if 'original_actors_to_move' not in locals():
        original_actors_to_move = actors_to_move.copy()
    game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
    if os.path.exists(game_actors_dir):
        for filename in os.listdir(game_actors_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(game_actors_dir, filename)
                character_data = _load_json_safely(file_path)
                if not character_data:
                    continue
                actual_character_name = character_data.get('name', os.path.splitext(filename)[0])
                if actual_character_name in actors_to_move:
                    continue
                variables = character_data.get('variables', {})
                following = variables.get('following', '')
                if following == "Player" and player_name:
                    following = player_name
                if following and following in original_actors_to_move:
                    if actual_character_name not in actors_to_move:
                        actors_to_move.append(actual_character_name)
    resource_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
    if 'original_actors_to_move' not in locals():
        original_actors_to_move = actors_to_move.copy()
    if os.path.exists(resource_actors_dir):
        for root, dirs, files in os.walk(resource_actors_dir):
            for filename in files:
                if filename.lower().endswith('.json'):
                    file_path = os.path.join(root, filename)
                    character_data = _load_json_safely(file_path)
                    if not character_data:
                        continue
                    actual_character_name = character_data.get('name', os.path.splitext(filename)[0])
                    if actual_character_name in actors_to_move:
                        continue
                    variables = character_data.get('variables', {})
                    following = variables.get('following', '')
                    if following == "Player" and player_name:
                        following = player_name
                    if following and following in original_actors_to_move:
                        if actual_character_name not in actors_to_move:
                            actors_to_move.append(actual_character_name)
    if mode == 'Adjacent':
        if not current_setting_name:
            base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
            for root, dirs, files in os.walk(base_settings_dir):
                dirs[:] = [d for d in dirs if d.lower() != 'saves']
                for filename in files:
                    if filename.lower().endswith('_setting.json'):
                        file_path = os.path.join(root, filename)
                        setting_data = _load_json_safely(file_path)
                        chars = setting_data.get('characters', [])
                        if any(actor in chars for actor in actors_to_move) or (player_name in actors_to_move and "Player" in chars):
                            current_setting_name = setting_data.get('name')
                            current_setting_file = file_path
                            found = True
                            break
                if found:
                    break
        if not current_setting_name:
            result['error'] = 'Could not determine current setting for actor(s).'
            return result
        connections = {}
        setting_data = _load_json_safely(current_setting_file)
        connections_dict = setting_data.get('connections', {})
        location_map_data_file = os.path.join(os.path.dirname(current_setting_file), 'location_map_data.json')
        if os.path.isfile(location_map_data_file):
            try:
                with open(location_map_data_file, 'r', encoding='utf-8') as f:
                    map_data = json.load(f)
                dots = map_data.get('dots', [])
                lines = map_data.get('lines', [])
                this_dot_indices = [i for i, d in enumerate(dots)
                                    if len(d) >= 5 and str(d[4]).strip().lower() == current_setting_name.lower()]
                connected_names = set()
                if this_dot_indices:
                    for this_dot_index in this_dot_indices:
                        for line in lines:
                            meta = line.get('meta', {})
                            start = meta.get('start', -1)
                            end = meta.get('end', -1)
                            other_index = None
                            if start == this_dot_index:
                                other_index = end
                            elif end == this_dot_index:
                                other_index = start
                            if other_index is not None and 0 <= other_index < len(dots):
                                other_dot = dots[other_index]
                                if len(other_dot) >= 5 and other_dot[3] == 'small' and other_dot[4]:
                                    other_name = str(other_dot[4]).strip()
                                    if other_name and other_name.lower() != current_setting_name.lower():
                                        connected_names.add(other_name)
                connections = {name: connections_dict.get(name, "") for name in connected_names}
            except Exception as e:
                connections = connections_dict
        else:
            connections = connections_dict
        if not connections:
            result['error'] = f"No connections found for current setting '{current_setting_name}'."
            return result
        llm_prompt = _build_adjacent_move_prompt(context_for_move, connections)
        llm_response = make_inference(
            context=[{"role": "user", "content": llm_prompt}],
            user_message=llm_prompt,
            character_name=actors_to_move[0] if actors_to_move else "Player",
            url_type=get_default_utility_model(),
            max_tokens=32,
            temperature=0.0,
            is_utility_call=True
        )
        chosen_setting = None
        for name in connections.keys():
            if name.lower() in llm_response.lower():
                chosen_setting = name
                break
        if not chosen_setting and '[NEITHER]' in llm_response.upper():
            result['error'] = 'LLM did not match any connection. Character movement canceled.'
            return result
        if not chosen_setting:
            for name in connections.keys():
                if llm_response.strip() == name:
                    chosen_setting = name
                    break
        if not chosen_setting:
            result['error'] = f'LLM did not return a valid setting name. Response: {llm_response}'
            return result
        target_setting_name = chosen_setting
    session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
    base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    target_file_path = None
    source_dir = None
    for root, dirs, files in os.walk(session_settings_dir):
        dirs[:] = [d for d in dirs if d.lower() != 'saves']
        for filename in files:
            if filename.lower().endswith('_setting.json'):
                file_path = os.path.join(root, filename)
                setting_data = _load_json_safely(file_path)
                if setting_data.get('name') == target_setting_name:
                    target_file_path = file_path
                    source_dir = 'game'
                    break
        if target_file_path:
            break
    if not target_file_path:
        for root, dirs, files in os.walk(base_settings_dir):
            dirs[:] = [d for d in dirs if d.lower() != 'saves']
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    file_path = os.path.join(root, filename)
                    setting_data = _load_json_safely(file_path)
                    if setting_data.get('name') == target_setting_name:
                        target_file_path = file_path
                        source_dir = 'resources'
                        break
            if target_file_path:
                break
        if not target_file_path:
            target_dir_name = target_setting_name.lower().replace(' ', '_')
            location_dir_game = os.path.join(session_settings_dir, target_dir_name)
            if os.path.isdir(location_dir_game):
                actual_dir_name = os.path.basename(location_dir_game).lower()
                if actual_dir_name == target_dir_name:
                    matching_settings = []
                    for root, dirs, files in os.walk(location_dir_game):
                        for filename in files:
                            if filename.lower().endswith('_setting.json'):
                                file_path = os.path.join(root, filename)
                                setting_data = _load_json_safely(file_path)
                                if setting_data:
                                    if setting_data.get('name', '').lower() == target_setting_name.lower():
                                        matching_settings.append((file_path, setting_data))
                    if matching_settings:
                        target_file_path = matching_settings[0][0]
                        source_dir = 'game'
                        actual_setting_name = matching_settings[0][1].get('name')
                    else:
                        fallback_settings = []
                        for root, dirs, files in os.walk(location_dir_game):
                            for filename in files:
                                if filename.lower().endswith('_setting.json'):
                                    file_path = os.path.join(root, filename)
                                    setting_data = _load_json_safely(file_path)
                                    if setting_data:
                                        fallback_settings.append((file_path, setting_data))
                        if fallback_settings:
                            priority_settings = []
                            for file_path, setting_data in fallback_settings:
                                setting_name = setting_data.get('name', '').lower()
                                if 'base' in setting_name or 'main' in setting_name or 'entry' in setting_name:
                                    priority_settings.append((file_path, setting_data))
                            if priority_settings:
                                target_file_path = priority_settings[0][0]
                                source_dir = 'game'
                                actual_setting_name = priority_settings[0][1].get('name')
                            else:
                                target_file_path = fallback_settings[0][0]
                                source_dir = 'game'
                                actual_setting_name = fallback_settings[0][1].get('name')
            if not target_file_path:
                location_dir_resources = None
                for root, dirs, files in os.walk(base_settings_dir):
                    for dirname in dirs:
                        if dirname.lower() == target_dir_name:
                            location_dir_resources = os.path.join(root, dirname)
                            break
                    if location_dir_resources:
                        break
                if location_dir_resources and os.path.isdir(location_dir_resources):
                    matching_settings = []
                    for root, dirs, files in os.walk(location_dir_resources):
                        for filename in files:
                            if filename.lower().endswith('_setting.json'):
                                file_path = os.path.join(root, filename)
                                setting_data = _load_json_safely(file_path)
                                if setting_data:
                                    if setting_data.get('name', '').lower() == target_setting_name.lower():
                                        matching_settings.append((file_path, setting_data))
                    if matching_settings:
                        target_file_path = matching_settings[0][0]
                        source_dir = 'resources'
                        actual_setting_name = matching_settings[0][1].get('name')
                    else:
                        fallback_settings = []
                        for root, dirs, files in os.walk(location_dir_resources):
                            for filename in files:
                                if filename.lower().endswith('_setting.json'):
                                    file_path = os.path.join(root, filename)
                                    setting_data = _load_json_safely(file_path)
                                    if setting_data:
                                        fallback_settings.append((file_path, setting_data))
                        if fallback_settings:
                            priority_settings = []
                            for file_path, setting_data in fallback_settings:
                                setting_name = setting_data.get('name', '').lower()
                                if 'base' in setting_name or 'main' in setting_name or 'entry' in setting_name:
                                    priority_settings.append((file_path, setting_data))
                            if priority_settings:
                                target_file_path = priority_settings[0][0]
                                source_dir = 'resources'
                                actual_setting_name = priority_settings[0][1].get('name')
                            else:
                                target_file_path = fallback_settings[0][0]
                                source_dir = 'resources'
                                actual_setting_name = fallback_settings[0][1].get('name')
    if not target_file_path:
        error_msg = f"Target setting '{target_setting_name}' not found - checked for exact setting match and as a location name."
        result['error'] = error_msg
        return result
    target_setting_data = _load_json_safely(target_file_path)
    if 'characters' not in target_setting_data or not isinstance(target_setting_data.get('characters'), list):
        target_setting_data['characters'] = []
    added_to_target = False
    for actor in actors_to_move:
        actor_to_add = "Player" if actor == player_name else actor
        if actor_to_add not in target_setting_data['characters']:
            target_setting_data['characters'].append(actor_to_add)
            added_to_target = True
    result['moved_actors'] = list(actors_to_move)
    result['player_moved'] = player_name in actors_to_move if player_name else False
    game_dir = os.path.join(workflow_data_dir, 'game')
    resources_dir = os.path.join(workflow_data_dir, 'resources', 'data files')
    relative_path = os.path.relpath(target_file_path, start=game_dir if source_dir == 'game' else resources_dir)
    save_path = os.path.join(game_dir, relative_path)
    result['target_setting_file'] = save_path
    save_successful = True
    if added_to_target or source_dir == 'resources':
        try:
            if not os.path.exists(os.path.dirname(save_path)):
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
            save_result = _save_json_safely(save_path, target_setting_data)
            if not save_result:
                error_msg = f"Failed to save modified target setting to {save_path}"
                result['error'] = error_msg
                save_successful = False
        except Exception as e:
            error_msg = f"Exception while saving target setting: {e}"
            result['error'] = error_msg
            save_successful = False
    if save_successful:
        removal_count = 0
        for root, dirs, files in os.walk(session_settings_dir):
            dirs[:] = [d for d in dirs if d.lower() != 'saves']
            for filename in files:
                if filename.lower().endswith('_setting.json'):
                    current_file_path = os.path.join(root, filename)
                    if os.path.normpath(current_file_path) == os.path.normpath(save_path):
                        continue
                    try:
                        other_setting_data = _load_json_safely(current_file_path)
                        if 'characters' in other_setting_data and isinstance(other_setting_data['characters'], list):
                            original_chars = list(other_setting_data['characters'])
                            new_chars = []
                            for c in original_chars:
                                should_remove = c in actors_to_move
                                if not should_remove and player_name in actors_to_move and c == "Player":
                                    should_remove = True
                                if not should_remove:
                                    new_chars.append(c)
                            if len(new_chars) < len(original_chars):
                                other_setting_data['characters'] = new_chars
                                if _save_json_safely(current_file_path, other_setting_data):
                                    removal_count += 1
                    except Exception as e:
                        pass
    if save_successful and result['player_moved']:
        updates = {
            'allow_narrator_post_after_change': True,
            'turn_count': 1,
            'scene_number_increment': True
        }
        result['tab_data_updates'] = updates
        result['process_scene_change_timers'] = True
    result['success'] = save_successful

    if tab_data and current_setting_name and current_setting_file:
        context = tab_data.get('context', [])
        for actor in actors_to_move:
            actor_file = os.path.join(game_actors_dir, f"{actor}.json")
            if not os.path.exists(actor_file):
                continue
            actor_data = _load_json_safely(actor_file)
            variables = actor_data.get('variables', {})
            following = variables.get('following', '')
            if following == "Player" and player_name:
                following = player_name
            if following and following in actors_to_move:
                scene_messages = {}
                for msg in context:
                    scene_num = msg.get('scene', 1)
                    meta = msg.get('metadata', {})
                    char_name = meta.get('character_name', None)
                    if char_name in (actor, following) or (msg.get('role') == 'user' and actor == player_name):
                        scene_messages.setdefault(scene_num, []).append(msg)
                sorted_scenes = sorted(scene_messages.keys())
                if len(sorted_scenes) > 2:
                    scenes_to_summarize = sorted_scenes[:-2]
                    scenes_to_keep = sorted_scenes[-2:]
                    summary_msgs = []
                    for s in scenes_to_summarize:
                        for m in scene_messages[s]:
                            summary_msgs.append(f"{m.get('role','')}: {m.get('content','')}")
                    scene_interactions = '\n'.join(summary_msgs)
                    _summarize_follower_memory(actor, following, scene_interactions, workflow_data_dir)
                    recent_msgs = []
                    for s in scenes_to_keep:
                        recent_msgs.extend(scene_messages[s])
                    if 'recent_follower_context' not in actor_data:
                        actor_data['recent_follower_context'] = {}
                    actor_data['recent_follower_context'][following] = recent_msgs
                else:
                    recent_msgs = []
                    for s in sorted_scenes:
                        recent_msgs.extend(scene_messages[s])
                    if 'recent_follower_context' not in actor_data:
                        actor_data['recent_follower_context'] = {}
                    actor_data['recent_follower_context'][following] = recent_msgs
                    if 'follower_memories' in actor_data and following in actor_data['follower_memories']:
                        del actor_data['follower_memories'][following]
                _save_json_safely(actor_file, actor_data)
    result['success'] = save_successful
    if result['success']:
        moved_names = result['moved_actors']
        player_info = " (including Player)" if result['player_moved'] else ""
        actual_setting_name = None
        try:
            if target_file_path and os.path.exists(target_file_path):
                setting_data = _load_json_safely(target_file_path)
                if setting_data and setting_data.get('name') != target_setting_name:
                    actual_setting_name = setting_data.get('name')
        except Exception:
            pass
    if result['success'] and result['player_moved'] and tab_data:
        right_splitter = tab_data.get('right_splitter')
        workflow_data_dir_for_update = tab_data.get('workflow_data_dir')
        final_player_setting_name = None
        if result.get('target_setting_file') and os.path.exists(result['target_setting_file']):
            final_setting_data = _load_json_safely(result['target_setting_file'])
            if final_setting_data:
                final_player_setting_name = final_setting_data.get('name')
        if not final_player_setting_name:
            final_player_setting_name = target_setting_name
        if advance_time and current_setting_name and final_player_setting_name and current_setting_name != final_player_setting_name:
            travel_time_minutes = _calculate_travel_time_between_settings(
                workflow_data_dir_for_update, 
                current_setting_name, 
                final_player_setting_name
            )
            if travel_time_minutes > 0:
                _advance_game_time(workflow_data_dir_for_update, travel_time_minutes)
        
        if right_splitter and workflow_data_dir_for_update and final_player_setting_name:
            from PyQt5.QtCore import QTimer
            try:
                QTimer.singleShot(0, lambda: right_splitter.update_setting_name(final_player_setting_name, workflow_data_dir_for_update))
            except Exception as e_ui_update:
                pass
    return result

def _build_adjacent_move_prompt(context, connections):
    prompt = """You are a text adventure engine. The player has just performed an action. Below is the context of the action, and a list of possible connections (exits or transitions) from the current setting. Your job is to determine if the player's action matches any of the connection descriptions.\n\n"""
    prompt += f"Context:\n{context}\n\n"
    prompt += "Connections (each leads to a different setting):\n"
    for name, desc in connections.items():
        prompt += f"- {name}: {desc}\n"
    prompt += "\nIf the player's action matches one of the connection descriptions, output ONLY the exact setting name (case-sensitive, as shown above). If neither matches, output [NEITHER].\n\nOutput:"
    return prompt

def _calculate_travel_time_between_settings(workflow_data_dir, from_setting, to_setting):
    world_map_data = _find_world_map_data_for_settings(workflow_data_dir, from_setting, to_setting)
    if world_map_data:
        path_length = _calculate_path_length_between_dots(world_map_data, from_setting, to_setting)
        if path_length > 0:
            travel_time = _calculate_travel_time_from_path_length(world_map_data, path_length, 'world')
            return travel_time
    location_map_data = _find_location_map_data_for_settings(workflow_data_dir, from_setting, to_setting)
    if location_map_data:
        path_length = _calculate_path_length_between_dots(location_map_data, from_setting, to_setting)
        if path_length > 0:
            travel_time = _calculate_travel_time_from_path_length(location_map_data, path_length, 'location')
            return travel_time
    return 0

def _find_world_map_data_for_settings(workflow_data_dir, from_setting, to_setting):
    base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    for root, dirs, files in os.walk(base_settings_dir):
        for filename in files:
            if filename == 'world_map_data.json':
                try:
                    with open(os.path.join(root, filename), 'r', encoding='utf-8') as f:
                        map_data = json.load(f)
                    dots = map_data.get('dots', [])
                    found_from = False
                    found_to = False
                    for dot in dots:
                        if len(dot) >= 5 and dot[3] == 'small':
                            dot_name = str(dot[4]).strip()
                            if dot_name.lower() == from_setting.lower():
                                found_from = True
                            elif dot_name.lower() == to_setting.lower():
                                found_to = True
                    if found_from and found_to:
                        return map_data
                except Exception as e:
                    print(f"Error reading world map data {filename}: {e}")
    return None

def _find_location_map_data_for_settings(workflow_data_dir, from_setting, to_setting):
    base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
    for root, dirs, files in os.walk(base_settings_dir):
        for filename in files:
            if filename == 'location_map_data.json':
                try:
                    with open(os.path.join(root, filename), 'r', encoding='utf-8') as f:
                        map_data = json.load(f)
                    dots = map_data.get('dots', [])
                    found_from = False
                    found_to = False
                    for dot in dots:
                        if len(dot) >= 5 and dot[3] == 'small':
                            dot_name = str(dot[4]).strip()
                            if dot_name.lower() == from_setting.lower():
                                found_from = True
                            elif dot_name.lower() == to_setting.lower():
                                found_to = True
                    
                    if found_from and found_to:
                        return map_data
                except Exception as e:
                    print(f"Error reading location map data {filename}: {e}")
    return None

def _calculate_path_length_between_dots(map_data, from_setting, to_setting):
    import math
    dots = map_data.get('dots', [])
    lines = map_data.get('lines', [])
    from_index = None
    to_index = None
    for i, dot in enumerate(dots):
        if len(dot) >= 5 and dot[3] == 'small':
            dot_name = str(dot[4]).strip()
            if dot_name.lower() == from_setting.lower():
                from_index = i
            elif dot_name.lower() == to_setting.lower():
                to_index = i
    if from_index is None or to_index is None:
        return 0
    graph = {}
    for i in range(len(dots)):
        graph[i] = []
    for line in lines:
        meta = line.get('meta', {})
        start = meta.get('start', -1)
        end = meta.get('end', -1)
        if start >= 0 and end >= 0 and start < len(dots) and end < len(dots):
            points = line.get('points', [])
            if len(points) >= 2:
                segment_length = 0
                for i in range(len(points) - 1):
                    p1 = points[i]
                    p2 = points[i + 1]
                    if len(p1) >= 2 and len(p2) >= 2:
                        segment_length += math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                graph[start].append((end, segment_length))
                graph[end].append((start, segment_length))
    import heapq
    distances = {i: float('inf') for i in range(len(dots))}
    distances[from_index] = 0
    pq = [(0, from_index)]
    visited = set()
    while pq:
        current_dist, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)
        if current == to_index:
            return distances[to_index]
        for neighbor, edge_length in graph[current]:
            if neighbor not in visited:
                new_dist = current_dist + edge_length
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    heapq.heappush(pq, (new_dist, neighbor))
    return 0

def _calculate_travel_time_from_path_length(map_data, path_length, map_type):
    scale_data = map_data.get('scale_settings', {})
    distance_per_unit = scale_data.get('distance', 1.0)
    time_per_unit = scale_data.get('time', 1.0)
    unit = scale_data.get('unit', 'minutes')
    if distance_per_unit <= 0:
        return 0
    time_in_units = (path_length / distance_per_unit) * time_per_unit
    if unit == 'minutes':
        return time_in_units
    elif unit == 'hours':
        return time_in_units * 60
    elif unit == 'days':
        return time_in_units * 60 * 24
    else:
        return time_in_units

def _advance_game_time(workflow_data_dir, minutes_to_advance):
    from datetime import datetime, timedelta
    game_dir = os.path.join(workflow_data_dir, 'game')
    gamestate_file = os.path.join(game_dir, 'gamestate.json')
    if not os.path.exists(gamestate_file):
        print(f"Gamestate file not found: {gamestate_file}")
        return
    try:
        gamestate = _load_json_safely(gamestate_file)
        if not gamestate:
            print("Failed to load gamestate")
            return
        current_time_str = gamestate.get('datetime', '')
        if not current_time_str:
            print("No datetime found in gamestate")
            return
        current_time = datetime.fromisoformat(current_time_str.replace('Z', '+00:00'))
        new_time = current_time + timedelta(minutes=minutes_to_advance)
        gamestate['datetime'] = new_time.isoformat()
    except Exception as e:
        print(f"Error advancing game time: {e}") 