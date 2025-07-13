import json
import os
import re
import traceback
from core.utils import _find_actor_file_path, _load_json_safely, _find_player_character_file, _get_player_current_setting_name, _get_player_character_name
from rules.rule_evaluator import _evaluate_conditions, _apply_rule_actions_and_continue

def _get_player_name_for_context(workflow_data_dir):
    try:
        from core.utils import _get_player_character_name
        class DummyUI:
            pass
        dummy_ui = DummyUI()
        player_name = _get_player_character_name(dummy_ui, workflow_data_dir)
        return player_name if player_name else "Player"
    except Exception:
        return "Player"

def _get_follower_memories_for_context(self, workflow_data_dir, actor_name, chars_in_scene, current_context, scenes_to_recall=1):
    if not workflow_data_dir or not actor_name or not current_context:
        return None
    normalized_actor_name = actor_name.strip().lower().replace(' ', '_')
    actor_file = os.path.join(workflow_data_dir, 'game', 'actors', f"{normalized_actor_name}.json")
    if not os.path.exists(actor_file):
        return None
    try:
        with open(actor_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        variables = data.get('variables', {})
        followed_name = variables.get('following', '').strip()
        if not followed_name:
            return None
        
        followed_name_for_display = followed_name
        if followed_name.lower() == 'player':
            player_name = _get_player_name_for_context(workflow_data_dir)
            followed_name_for_display = player_name
        
        tab_data = self.get_current_tab_data()
        if not tab_data:
            return None
        current_scene = tab_data.get('scene_number', 1)
        prior_scene = current_scene - 1
        
        if 'scene_summaries' not in data:
            data['scene_summaries'] = {}
        
        scene_summaries = data['scene_summaries']
        output_lines = []
        
        summary_key = f"scenes_with_{followed_name.lower()}"
        cached_summary = scene_summaries.get(summary_key)
        needs_update = False
        
        if not cached_summary or cached_summary.get('last_scene_processed', 0) < prior_scene:
            needs_update = True
        
        if needs_update and prior_scene > 0:
            messages_to_summarize = []
            for msg in current_context:
                scene_num = msg.get('scene', 1)
                if msg.get('role') != 'system' and scene_num < current_scene:
                    meta = msg.get('metadata', {})
                    char_name = meta.get('character_name', None)
                    involved_actors = {m.get('metadata', {}).get('character_name') for m in current_context if m.get('scene') == scene_num}
                    if msg.get('role') == 'user': 
                        involved_actors.add('Player')
                    if actor_name in involved_actors and (followed_name in involved_actors or (followed_name.lower() == 'player' and 'Player' in involved_actors)):
                        messages_to_summarize.append(msg)
            
            unique_summarize_msgs = {(msg.get('scene'), msg.get('content')): msg for msg in messages_to_summarize}
            messages_to_summarize = list(unique_summarize_msgs.values())
            
            if messages_to_summarize:
                try:
                    summary_lines = []
                    for msg in messages_to_summarize:
                        scene_num = msg.get('scene', 1)
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        char_name = msg.get('metadata', {}).get('character_name', '')
                        game_time = msg.get('metadata', {}).get('game_datetime')
                        time_label = game_time if game_time else f"Scene {scene_num}"
                        if role == 'user':
                            player_name = _get_player_name_for_context(workflow_data_dir)
                            summary_lines.append(f"{time_label}: {player_name}: {content}")
                        elif role == 'assistant' and char_name:
                            summary_lines.append(f"{time_label}: {char_name}: {content}")
                    
                    if summary_lines:
                        summary = '\n'.join(summary_lines[-10:])
                        scene_summaries[summary_key] = {
                            'summary': summary,
                            'last_scene_processed': prior_scene,
                            'last_updated': current_scene
                        }
                        
                        with open(actor_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        
                        output_lines.append(f"(Summary of earlier shared scenes between {actor_name} and {followed_name_for_display}):\n" + summary)
                except Exception as e:
                    traceback.print_exc()
        elif cached_summary and cached_summary.get('summary'):
            output_lines.append(f"(Summary of earlier shared scenes between {actor_name} and {followed_name_for_display}):\n" + cached_summary['summary'])
        
        if prior_scene >= 1:
            scene_msgs = []
            for m in current_context:
                if m.get('scene', 1) == prior_scene and m.get('role') != 'system':
                    meta = m.get('metadata', {})
                    char_name = meta.get('character_name', None)
                    role = m.get('role', '')
                    content = m.get('content', '')
                    if char_name in (actor_name, followed_name) or (role == 'user' and followed_name.lower() == 'player'):
                        if char_name:
                            scene_msgs.append(f"{char_name}: {content}")
                        elif role == 'user':
                            player_name = _get_player_name_for_context(workflow_data_dir)
                            scene_msgs.append(f"{player_name}: {content}")
                        else:
                            scene_msgs.append(f"Narrator: {content}")
            if scene_msgs:
                output_lines.append(f"Your character ({actor_name}) is following ({followed_name_for_display}). Here were your interactions in the previous scene:\n" + "\n".join(scene_msgs))
        
        final_output = '\n\n'.join(output_lines) if output_lines else None
        return final_output
    except Exception as e:
        return None

def run_single_character_post(self, character_name, tab_data=None, system_message_override=None, 
                             trigger_type="manual", skip_rules=False, return_result=False, timer_system_modifications=None):
    if not character_name:
        return None
    from editor_panel.time_manager import update_time
    update_time(self, tab_data)
    
    is_timer_triggered = trigger_type == "timer" or (tab_data and bool(
        tab_data.get('_timer_final_instruction') or 
        tab_data.get('_is_timer_narrator_action_active') or
        tab_data.get('_last_timer_action_type')
    ))
    
    if is_timer_triggered and hasattr(self, '_character_tags'):
        print(f"[CHARACTER TAGS] Clearing character tag for '{character_name}' before timer-based rule evaluation to prevent stacking")
        self._character_tags.pop(character_name, None)
    
    original_character = getattr(self, 'character_name', None)
    self.character_name = character_name

    if tab_data is None:
        tab_data = self.get_current_tab_data()
        if not tab_data:
            return None
    try:
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            return None
        full_history_context = self.get_current_context()
        if not full_history_context:
            return None
        current_scene = tab_data.get('scene_number', 1)
        system_msg_base_intro = (
            "You are in a third-person text RPG. "
            "You are responsible for writing ONLY the actions and dialogue of your assigned character, as if you are a narrator describing them. "
            "You must ALWAYS write in third person (using the character's name or 'he/she/they'), NEVER in first or second person. "
            "Assume other characters are strangers unless otherwise stated in special instructions. "
            "Keep dialogue short and brisk (1-5 lines) unless otherwise instructed. "
            "Do not use nametags (your post will be assigned a nametag automatically already, so you just need to write the post), do not switch characters (otherwise, the computer-assigned nametag given to your response will be incorrect, breaking the game). "
            "Write one single open-ended response (do NOT describe the OUTCOME of actions)."
        )
        npc_context_for_llm = []
        npc_context_for_llm.append({"role": "system", "content": system_msg_base_intro})
        char_sheet_str = "(Character sheet not found)"
        npc_file_path = _find_actor_file_path(self, workflow_data_dir, character_name)
        if npc_file_path:
            npc_data = _load_json_safely(npc_file_path)
            if npc_data:
                fields_to_exclude = ['isPlayer', 'npc_notes', 'memory_summary']
                filtered_npc_data = {k: v for k, v in npc_data.items() if k not in fields_to_exclude}
                char_sheet_content = json.dumps(filtered_npc_data, indent=2)
                char_sheet_str = f"Your character sheet (JSON format):\n```json\n{char_sheet_content}\n```"
        npc_context_for_llm.append({"role": "user", "content": char_sheet_str})
        try:
            scenes_to_recall = 1
            if npc_file_path and os.path.exists(npc_file_path):
                with open(npc_file_path, 'r', encoding='utf-8') as f:
                    npc_data_mem_check = json.load(f)
                variables_mem_check = npc_data_mem_check.get('variables', {})
                if variables_mem_check.get('following', '').strip().lower() == 'player':
                    scenes_to_recall = 2
            npcs_in_scene = []
            mem_summary = _get_follower_memories_for_context(
                self, workflow_data_dir, character_name, npcs_in_scene, full_history_context, scenes_to_recall=scenes_to_recall)
            if mem_summary:
                npc_context_for_llm.append({"role": "user", "content": mem_summary})
        except Exception as e:
            traceback.print_exc()
        try:
            setting_name = _get_player_current_setting_name(workflow_data_dir)
            if setting_name:
                setting_info_msg_content = f"(The current setting of the scene is: {setting_name})"
                npc_context_for_llm.append({"role": "user", "content": setting_info_msg_content})
        except Exception as e:
            traceback.print_exc()
        history_to_add = []
        for msg in full_history_context:
            if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene:
                content = msg['content']
                if (msg.get('role') == 'assistant' and 'metadata' in msg and 
                    msg['metadata'].get('character_name')):
                    char_name_hist = msg['metadata']['character_name']
                    if content and not content.strip().startswith(f"{char_name_hist}:"):
                        content = f"{char_name_hist}: {content}"
                history_to_add.append({"role": msg['role'], "content": content})
        for item in history_to_add:
            npc_context_for_llm.append(item)
        context_modifications = []
        tag_for_this_npc = None
        model_to_use = tab_data['settings'].get('model', self.get_current_model())
        if not skip_rules:
            if tab_data and character_name:
                if character_name in tab_data.get('_characters_to_exit_rules', set()):
                    print(f"Skipping all rules for '{character_name}' due to prior Exit Rule Processing action.")
                else:
                    if not hasattr(self, '_character_tags'):
                        self._character_tags = {}
                    character_rules = [r for r in tab_data.get('thought_rules', []) 
                                      if r.get('applies_to', 'Narrator') == 'Character']
                    for char_rule in character_rules:
                        if character_name in tab_data.get('_characters_to_exit_rules', set()):
                            print(f"Stopping rule processing for '{character_name}' due to Exit Rule Processing action during rule evaluation.")
                            break
                        rule_target_character = char_rule.get('character_name')
                        if rule_target_character and rule_target_character != character_name:
                            continue
                        conditions_struct = char_rule.get('conditions', [])
                        operator = char_rule.get('conditions_operator', 'AND')
                        current_turn = tab_data.get('turn_count', 1)
                        conditions_met = False
                        if isinstance(conditions_struct, list) and len(conditions_struct) > 0:
                            conditions_met = _evaluate_conditions(
                                self, tab_data, conditions_struct, operator, current_turn, 
                                triggered_directly=False, character_name=character_name
                            )
                        else:
                            if char_rule.get('condition_type', '').lower() == 'always':
                                conditions_met = True
                            else:
                                conditions_met = False
                        if conditions_met:
                            tag_action_pairs = char_rule.get('tag_action_pairs', [])
                            matched_pair = None
                            if tag_action_pairs:
                                matched_pair = tag_action_pairs[0]
                            if matched_pair:
                                returned_tag = _apply_rule_actions_and_continue(
                                    self, matched_pair, char_rule, None, None, None, [], 
                                    False, False, character_name_override=character_name
                                )
                                if returned_tag:
                                    tag_for_this_npc = returned_tag
                                actions = matched_pair.get('actions', [])
                                for action_obj in actions:
                                    action_type = action_obj.get('type')
                                    if action_type == 'Switch Model':
                                        model_to_use = action_obj.get('value', '').strip() or model_to_use
                                    elif action_type == 'System Message':
                                        value = action_obj.get('value', '')
                                        position = action_obj.get('position', 'prepend')
                                        if value:
                                            value = self._substitute_variables_in_string(value, tab_data, character_name)
                                            context_modifications.append({
                                                'role': 'system', 
                                                'content': value, 
                                                'position': position
                                            })
                    if hasattr(self, '_character_tags') and character_name in self._character_tags:
                        final_character_tag = self._character_tags[character_name]
                        if final_character_tag:
                            tag_for_this_npc = final_character_tag
            else:
                if not hasattr(self, '_character_tags'):
                    self._character_tags = {}
                character_rules = [r for r in tab_data.get('thought_rules', []) 
                                  if r.get('applies_to', 'Narrator') == 'Character']
                for char_rule in character_rules:
                    if character_name in tab_data.get('_characters_to_exit_rules', set()):
                        print(f"Stopping rule processing for '{character_name}' due to Exit Rule Processing action during rule evaluation.")
                        break
                    rule_target_character = char_rule.get('character_name')
                    if rule_target_character and rule_target_character != character_name:
                        continue
                    conditions_struct = char_rule.get('conditions', [])
                    operator = char_rule.get('conditions_operator', 'AND')
                    current_turn = tab_data.get('turn_count', 1)
                    conditions_met = False
                    if isinstance(conditions_struct, list) and len(conditions_struct) > 0:
                        conditions_met = _evaluate_conditions(
                            self, tab_data, conditions_struct, operator, current_turn, 
                            triggered_directly=False, character_name=character_name
                        )
                    else:
                        if char_rule.get('condition_type', '').lower() == 'always':
                            conditions_met = True
                        else:
                            conditions_met = False
                    if conditions_met:
                        tag_action_pairs = char_rule.get('tag_action_pairs', [])
                        matched_pair = None
                        if tag_action_pairs:
                            matched_pair = tag_action_pairs[0]
                        if matched_pair:
                            returned_tag = _apply_rule_actions_and_continue(
                                self, matched_pair, char_rule, None, None, None, [], 
                                False, False, character_name_override=character_name
                            )
                            if returned_tag:
                                tag_for_this_npc = returned_tag
                            actions = matched_pair.get('actions', [])
                            for action_obj in actions:
                                action_type = action_obj.get('type')
                                if action_type == 'Switch Model':
                                    model_to_use = action_obj.get('value', '').strip() or model_to_use
                                elif action_type == 'System Message':
                                    value = action_obj.get('value', '')
                                    position = action_obj.get('position', 'prepend')
                                    if value:
                                        value = self._substitute_variables_in_string(value, tab_data, character_name)
                                        context_modifications.append({
                                            'role': 'system', 
                                            'content': value, 
                                            'position': position
                                        })
                if hasattr(self, '_character_tags') and character_name in self._character_tags:
                    final_character_tag = self._character_tags[character_name]
                    if final_character_tag:
                        tag_for_this_npc = final_character_tag
        for mod in context_modifications:
            if mod.get('role') == 'system':
                position = mod.get('position', 'prepend')
                content = mod['content']
                if position == 'prepend':
                    npc_context_for_llm.insert(1, {"role": "system", "content": content})
                elif position == 'append':
                    npc_context_for_llm.append({"role": "user", "content": content})
                elif position == 'replace':
                    if len(npc_context_for_llm) > 0 and npc_context_for_llm[0].get('role') == 'system':
                        npc_context_for_llm[0]['content'] = content
                    else:
                        npc_context_for_llm.insert(0, {"role": "system", "content": content})
        if is_timer_triggered:
            print(f"[TIMER DEBUG] Character post for {character_name}: is_timer_triggered={is_timer_triggered}, timer_system_modifications={timer_system_modifications}")
            if timer_system_modifications:
                for i, timer_mod in enumerate(timer_system_modifications):
                    position = timer_mod.get('position', 'prepend')
                    content = timer_mod.get('action', '')
                    sys_msg_position = timer_mod.get('system_message_position', 'first')
                    if content:
                        if sys_msg_position == 'first':
                            if position == 'prepend':
                                npc_context_for_llm.insert(1, {"role": "system", "content": content})
                            elif position == 'append':
                                npc_context_for_llm.append({"role": "user", "content": content})
                            elif position == 'replace':
                                if len(npc_context_for_llm) > 0 and npc_context_for_llm[0].get('role') == 'system':
                                    npc_context_for_llm[0]['content'] = content
                                else:
                                    npc_context_for_llm.insert(0, {"role": "system", "content": content})
                        else:
                            npc_context_for_llm.append({"role": "user", "content": content})

        if system_message_override:
            npc_context_for_llm.append({"role": "system", "content": system_message_override})
        npc_context_for_llm.append({
            "role": "user", 
            "content": f"(You are playing as: {character_name}. It is now {character_name}'s turn. What does {character_name} do or say next?)"
        })
        for i, msg in enumerate(npc_context_for_llm):
            content = msg.get('content', '')
        try:
            max_tokens = self.max_tokens
            result_text = self.run_utility_inference_sync(npc_context_for_llm, model_to_use, max_tokens)
            if result_text and isinstance(result_text, str):
                prefix = f"{character_name}:"
                if result_text.strip().startswith(prefix):
                    result_text = result_text.strip()[len(prefix):].lstrip()
                result_text = re.sub(r'<think>[\s\S]*?</think>', '', result_text, flags=re.IGNORECASE).strip()
            if return_result:
                return result_text
            metadata_obj = {"character_name": character_name}
            if tag_for_this_npc:
                metadata_obj["text_tag"] = tag_for_this_npc
            character_post_effects = None
            if hasattr(self, '_character_post_effects') and character_name in self._character_post_effects:
                character_post_effects = self._character_post_effects[character_name].copy()
                metadata_obj["post_effects"] = character_post_effects
            self.display_message('assistant', result_text, text_tag=tag_for_this_npc, character_name=character_name, post_effects=character_post_effects)
            if hasattr(self, 'return3_sound') and self.return3_sound:
                self.return3_sound.play()
            save_message_obj = {
                "role": "assistant",
                "content": result_text,
                "scene": current_scene,
                "metadata": metadata_obj
            }
            location = _get_player_current_setting_name(workflow_data_dir)
            if location:
                save_message_obj["metadata"]["location"] = location
            current_turn_for_metadata = tab_data.get('turn_count', 0)
            save_message_obj["metadata"]["turn"] = current_turn_for_metadata
            if workflow_data_dir:
                try:
                    tab_index = self.tabs_data.index(tab_data) if tab_data in self.tabs_data else -1
                    if tab_index >= 0:
                        variables = self._load_variables(tab_index)
                        game_datetime = variables.get('datetime')
                        if game_datetime:
                            if 'metadata' not in save_message_obj:
                                save_message_obj['metadata'] = {}
                            save_message_obj['metadata']['game_datetime'] = game_datetime
                except Exception as e:
                    print(f"Error adding game timestamp to timer message: {e}")
            full_history_context.append(save_message_obj)
            current_tab_index = self.tab_widget.currentIndex()
            self._save_context_for_tab(current_tab_index)
            if hasattr(self, '_re_enable_input_after_pipeline'):
                self._re_enable_input_after_pipeline()
            return result_text
        except Exception as e:
            if hasattr(self, '_re_enable_input_after_pipeline'):
                self._re_enable_input_after_pipeline()
            return None
    finally:
        self.character_name = original_character
        if hasattr(self, '_re_enable_input_after_pipeline'):
            self._re_enable_input_after_pipeline()