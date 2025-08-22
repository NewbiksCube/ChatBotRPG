import os
import json
import re
import traceback
from PyQt5.QtCore import QTimer
from core.utils import _get_player_character_name, _load_json_safely, _find_actor_file_path, _prepare_condition_text, _get_player_current_setting_name
from rules.rule_evaluator import _evaluate_conditions, _apply_rule_action, _apply_rule_actions_and_continue
from core.memory import get_npc_notes_from_character_file, format_npc_notes_for_context, add_npc_note_to_character_file
from config import get_default_model, get_default_cot_model
from core.process_keywords import inject_keywords_into_context, get_location_info_for_keywords

def _get_player_name_for_context(workflow_data_dir):
    try:
        from core.utils import _get_player_character_name
        player_name = _get_player_character_name(workflow_data_dir)
        return player_name if player_name else "Player"
    except Exception:
        return "Player"

def _start_npc_inference_threads(self):
    if self._narrator_streaming_lock:
        return
    try:
        current_tab_index = self.tab_widget.currentIndex()
        if not (0 <= current_tab_index < len(self.tabs_data)):
            return
        tab_data = self.tabs_data[current_tab_index]
        if not tab_data:
            return
        if hasattr(self, 'timer_manager') and self.timer_manager:
            self.timer_manager.pause_timers()
        is_timer_triggered = bool(
            tab_data.get('_timer_final_instruction') or 
            tab_data.get('_is_timer_narrator_action_active') or
            tab_data.get('_last_timer_action_type')
        )
        if is_timer_triggered and hasattr(self, '_character_tags'):
            self._character_tags.clear()
        if tab_data.get('_is_force_narrator_first_active', False):
            self._npc_inference_queue = []
            self._npc_message_queue = []
            self._npc_inference_in_progress = False
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        if tab_data.get('force_narrator', {}).get('active') and \
           tab_data.get('force_narrator', {}).get('order', '').lower() == 'last' and \
           tab_data.get('_fn_last_npc_turn_done', False):
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        if hasattr(self, '_character_post_effects'):
            self._character_post_effects.clear()
        if hasattr(self, '_narrator_post_effects'):
            self._narrator_post_effects.clear()
        if '_HARD_SUPPRESS_ALL_EXCEPT' in tab_data:
            self._npc_inference_queue = []
            self._npc_message_queue = []
            self._npc_inference_in_progress = False
            if hasattr(self, 'npc_inference_threads'):
                for thread in self.npc_inference_threads:
                    if thread and thread.isRunning():
                        try:
                            thread.terminate()
                            thread.wait(200)
                        except Exception as e:
                            print(f"[WARN] Error terminating thread: {e}")
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        if '_SUPPRESS_ALL_FOR_COOLDOWN_PERIOD' in tab_data:
            self._npc_inference_queue = []
            self._npc_message_queue = []
            self._npc_inference_in_progress = False
            if hasattr(self, 'npc_inference_threads'):
                for thread in self.npc_inference_threads:
                    if thread and thread.isRunning():
                        try:
                            thread.terminate()
                            thread.wait(200)
                        except Exception as e:
                            print(f"[WARN] Error terminating thread: {e}")
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        if tab_data.pop('_suppress_npcs_for_one_turn', False):
            self._npc_inference_queue = []
            self._npc_message_queue = [] 
            self._npc_inference_in_progress = False
            _start_next_npc_inference(self) 
            return
        if tab_data.get('_last_timer_action_type') == 'narrator':
            tab_data.pop('_last_timer_action_type', None)
            self._npc_inference_queue = []
            self._npc_message_queue = [] 
            self._npc_inference_in_progress = False
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        variables = {}
        variables_file = tab_data.get('variables_file')
        if variables_file and os.path.exists(variables_file):
            try:
                with open(variables_file, 'r', encoding='utf-8') as f:
                    variables = json.load(f)
            except Exception as e:
                print(f"[WARN] Could not load variables to check chat mode: {e}")
        system2 = variables.get('system2', 'parallel').lower()
        self._npc_message_queue = []
        self._npc_inference_queue = []
        self._npc_inference_in_progress = False
        tab_data['npc_mode_live'] = False
        tab_data['npc_mode_sequential'] = (system2 == 'sequential')
        all_rules = tab_data.get('thought_rules', [])
        workflow_data_dir = tab_data.get('workflow_data_dir')
        player_name = _get_player_character_name(workflow_data_dir) if workflow_data_dir else None
        npcs_in_scene = []
        current_setting_file = None
        setting_data = None
        if workflow_data_dir and player_name:
            session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
            found = False
            for root, dirs, files in os.walk(session_settings_dir):
                dirs[:] = [d for d in dirs if d.lower() != 'saves']
                for filename in files:
                    if filename.lower().endswith('_setting.json'):
                        file_path = os.path.join(root, filename)
                        temp_setting_data = _load_json_safely(file_path)
                        chars = temp_setting_data.get('characters', [])
                        if player_name in chars or (player_name and "Player" in chars):
                            current_setting_file = file_path
                            setting_data = temp_setting_data
                            found = True
                            break
                if found:
                    break
            if not current_setting_file:
                base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
                for root, dirs, files in os.walk(base_settings_dir):
                    dirs[:] = [d for d in dirs if d.lower() != 'saves']
                    for filename in files:
                        if filename.lower().endswith('_setting.json'):
                            file_path = os.path.join(root, filename)
                            temp_setting_data = _load_json_safely(file_path)
                            chars = temp_setting_data.get('characters', [])
                            if player_name in chars or (player_name and "Player" in chars):
                                current_setting_file = file_path
                                setting_data = temp_setting_data
                                found = True
                                break
                        if found:
                            break
        if current_setting_file and setting_data:
            chars = setting_data.get('characters', [])
            chars_filtered = [c for c in chars if isinstance(c, str)]
            npcs_in_scene_raw = [c for c in chars_filtered if c != player_name and c != "Player"]
            npcs_in_scene = []
            for character_entry in npcs_in_scene_raw:
                actual_name = get_actual_character_name(self, character_entry)
                if actual_name not in npcs_in_scene:
                    npcs_in_scene.append(actual_name)
        character_rules_all = [r for r in all_rules if r.get('applies_to', 'Narrator') == 'Character']
        if character_rules_all:
            for char_rule in character_rules_all:
                rule_id = char_rule.get('id', 'Unknown Character Rule')
                rule_target_character_name = char_rule.get('character_name')
                if not rule_target_character_name:
                    conditions = char_rule.get('conditions', [])
                    for condition in conditions:
                        if condition.get('character_name'):
                            rule_target_character_name = condition.get('character_name')
                            break
                if not rule_target_character_name:
                    continue
                if rule_target_character_name not in npcs_in_scene:
                    continue
                conditions = char_rule.get('conditions', [])
                operator = char_rule.get('conditions_operator', 'AND')
                current_turn = tab_data.get('turn_count', 1)
                conditions_met = False
                if conditions:
                    conditions_met = _evaluate_conditions(self, tab_data, conditions, operator, current_turn, triggered_directly=False)
                else:
                    conditions_met = True
                if conditions_met:
                    pairs = char_rule.get('tag_action_pairs', [])
                    if pairs:
                        actions = pairs[0].get('actions', [])
                        for action_obj in actions:
                            action_type = action_obj.get('type')
                            if action_type == 'Set Var':
                                var_name = action_obj.get('var_name', '').strip()
                                var_value = action_obj.get('var_value', '')
                                variable_scope = action_obj.get('variable_scope', 'Global')
                                if variable_scope != 'Character' and variable_scope != 'Global':
                                    variable_scope = action_obj.get('var_scope', 'Global')
                                if var_name:
                                    if variable_scope == 'Character':
                                        workflow_data_dir = tab_data.get('workflow_data_dir')
                                        character_name = action_obj.get('character_name', None)
                                        if not character_name and 'character_name' in char_rule:
                                            character_name = char_rule.get('character_name')
                                        if not character_name and 'char' in locals():
                                            character_name = char
                                        if workflow_data_dir and character_name:
                                            def normalize_name(name):
                                                return name.strip().lower().replace(' ', '_')
                                            normalized_char = normalize_name(character_name)
                                            game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
                                            actor_file = None
                                            for filename in os.listdir(game_actors_dir):
                                                if filename.lower().endswith('.json'):
                                                    if normalize_name(filename[:-5]) == normalized_char:
                                                        actor_file = os.path.join(game_actors_dir, filename)
                                                        break
                                            if actor_file:
                                                with open(actor_file, 'r', encoding='utf-8') as f:
                                                    actor_data = json.load(f)
                                                
                                                if 'variables' not in actor_data or not isinstance(actor_data['variables'], dict):
                                                    actor_data['variables'] = {}
                                                
                                                actor_data['variables'][var_name] = var_value
                                                
                                                with open(actor_file, 'w', encoding='utf-8') as f:
                                                    json.dump(actor_data, f, indent=2, ensure_ascii=False)
                                    
                                    elif variable_scope == 'Global':
                                        loaded_global_vars = self._load_variables(current_tab_index)
                                        if not isinstance(loaded_global_vars, dict):
                                            continue
                                        value_to_set = self.try_num(var_value)
                                        loaded_global_vars[var_name] = value_to_set
                                        self._save_variables(current_tab_index, loaded_global_vars)
                            
                            elif action_type == 'Change Actor Location':
                                dummy_user_msg = "(Rule Trigger - State Change)"
                                dummy_asst_msg = "(Rule Trigger - State Change)"
                                move_success = _apply_rule_action(self, action_obj, dummy_user_msg, dummy_asst_msg)
                            
                            elif action_type == 'New Scene':
                                current_scene = tab_data.get('scene_number', 1)
                                new_scene_number = current_scene + 1
                                tab_data['scene_number'] = new_scene_number
                                tab_data['pending_scene_update'] = True
        if not npcs_in_scene:
            if tab_data and not tab_data.get('_fn_last_npc_turn_done', False):
                force_narrator_details = tab_data.get('force_narrator', {})
                if force_narrator_details.get('active') and force_narrator_details.get('order', '').lower() == 'last':
                    tab_data['_fn_last_npc_turn_done'] = True
                    trigger_msg = self._last_user_msg_for_post_rules if hasattr(self, '_last_user_msg_for_post_rules') and self._last_user_msg_for_post_rules else "FN:Last deferred trigger (no NPCs in scene)"
                    QTimer.singleShot(0, lambda: self._complete_message_processing(trigger_msg))
                    self._npc_lock = False
                    if hasattr(self, 'timer_manager') and self.timer_manager:
                        self.timer_manager.resume_timers()
                    return
            self._npc_lock = False
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        final_npcs_to_infer_after_rules = []
        npcs_in_scene_filtered = [char for char in npcs_in_scene if isinstance(char, str)]
        for char_index, char in enumerate(sorted(npcs_in_scene_filtered)):
            character_system_context = self.get_character_system_context()
            if character_system_context:
                system_msg_base_intro = character_system_context
            else:
                system_msg_base_intro = (
                    "You are in a third-person text RPG. "
                    "You are responsible for writing ONLY the actions and dialogue of your assigned character, as if you are a narrator describing them. "
                    "You must ALWAYS write in third person (using the character's name or 'he/she/they'), NEVER in first or second person. "
                    "Assume other characters are strangers unless otherwise stated in special instructions. "
                    "Write one single open-ended response (do NOT describe the OUTCOME of actions)."
                )
            full_history_context = self.get_current_context()
            current_scene = tab_data.get('scene_number', 1)
            from core.utils import _filter_conversation_history_by_visibility
            filtered_context = _filter_conversation_history_by_visibility(
                full_history_context, char, workflow_data_dir, tab_data
            )
            
            history_to_add = []
            for msg in filtered_context:
                if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene:
                    content = msg['content']
                    if content and "Sorry, API error" in content:
                        continue
                    if (
                        msg.get('role') == 'assistant'
                        and 'metadata' in msg
                        and msg['metadata'].get('character_name')
                    ):
                        char_name = msg['metadata']['character_name']
                        if content and not content.strip().startswith(f"{char_name}:"):
                            content = f"{char_name}: {content}"
                    history_to_add.append({"role": msg['role'], "content": content})
            char_sheet_str = "(Character sheet not found)"
            npc_file_path = _find_actor_file_path(self, workflow_data_dir, char)
            if npc_file_path:
                npc_data = _load_json_safely(npc_file_path)
                if npc_data:
                    relevant_fields = ['name', 'description', 'personality', 'appearance', 'goals', 'story', 'equipment', 'left_hand_holding', 'right_hand_holding']
                    filtered_npc_data = {k: v for k, v in npc_data.items() if k in relevant_fields and v}
                    char_sheet_content = json.dumps(filtered_npc_data, indent=2)
                    char_sheet_str = f"Your character sheet (JSON format):\n```json\n{char_sheet_content}\n```"
            setting_desc = setting_data.get('description', '').strip() if setting_data else ''
            connections_dict = setting_data.get('connections', {}) if setting_data else {}
            setting_connections = ''
            if connections_dict:
                conn_lines = [f"- {name}: {desc}" if desc else f"- {name}" for name, desc in connections_dict.items()]
                if conn_lines:
                    setting_connections = "\nWays into and out of this scene and into other scenes are:\n" + "\n".join(conn_lines)
            model_to_use = self.tabs_data[current_tab_index]['settings'].get('model', get_default_model())
            context_modifications = []
            tag_for_this_npc = None
            if character_rules_all:
                for char_rule in character_rules_all:
                    if char in tab_data.get('_characters_to_exit_rules', set()):
                        break
                    rule_id = char_rule.get('id', 'Unknown Character Rule')
                    rule_scope = char_rule.get('scope', 'user_message')
                    text_condition = char_rule.get('condition', '').strip()
                    structured_conditions = char_rule.get('conditions', [])
                    operator = char_rule.get('conditions_operator', 'AND')
                    current_turn = tab_data.get('turn_count', 1)
                    structured_conditions_met = False
                    if structured_conditions:
                        structured_conditions_met = _evaluate_conditions(self, tab_data, structured_conditions, operator, current_turn, triggered_directly=False, character_name=char)
                    else:
                        structured_conditions_met = True
                    if not structured_conditions_met:
                        continue
                    llm_condition_met = True
                    tag_action_pairs = char_rule.get('tag_action_pairs', [])
                    matched_pair_data = None
                    if text_condition:
                        tags = [p.get('tag', '').strip() for p in tag_action_pairs if p.get('tag', '').strip()]
                        if not tags and not any(p.get('tag', '').strip() == '' for p in tag_action_pairs):
                                llm_condition_met = False
                        else:
                            prepared_condition_text = _prepare_condition_text(
                                self, text_condition, player_name, current_char_name=char, tab_data=tab_data, scope=rule_scope
                            )
                            last_user_msg = filtered_context[-1]['content'] if filtered_context and filtered_context[-1]['role'] == 'user' else ""
                            last_asst_msg = filtered_context[-2]['content'] if len(filtered_context) > 1 and filtered_context[-2]['role'] == 'assistant' else ""
                            target_msg_for_llm = ""
                            is_scope_valid = True
                            if rule_scope == 'llm_reply':
                                is_scope_valid = False
                            elif rule_scope == 'convo_llm_reply':
                                is_scope_valid = False
                            elif rule_scope == 'full_conversation':
                                current_scene = tab_data.get('scene_number', 1)
                                current_scene_messages = [m for m in filtered_context 
                                                         if m.get('role') != 'system' and m.get('scene', 1) == current_scene]
                                formatted_history = [f"{m.get('role','u').capitalize()}: {m.get('content','')}"
                                                    for m in current_scene_messages]
                                target_msg_for_llm = "\n".join(formatted_history)
                            elif rule_scope == 'last_exchange':
                                target_msg_for_llm = f"Assistant: {last_asst_msg}\nUser: {last_user_msg}"
                            else:
                                target_msg_for_llm = last_user_msg
                            try:
                                print(f"    [RULE DEBUG] Text evaluated for '{rule_id}' (scope={rule_scope}):\n{target_msg_for_llm}")
                            except Exception:
                                pass
                            if not is_scope_valid:
                                llm_condition_met = False
                            else:
                                tags_for_prompt = ", ".join([f"[{t}]" for t in tags])
                                final_prompt_text = prepared_condition_text
                                prompt_lower = prepared_condition_text.lower()
                                if tags and not any(f"[{tag.lower()}]" in prompt_lower for tag in tags) and "choose" not in prompt_lower:
                                    final_prompt_text += f"\nChoose the tag(s) that apply: {tags_for_prompt}"

                                cot_context = [
                                    {"role": "system", "content": f"Analyze text, respond ONLY with chosen tag ([TAG]).\nText:\n---\n{target_msg_for_llm}\n---"},
                                    {"role": "user", "content": final_prompt_text}
                                ]
                                rule_model = char_rule.get('model')
                                model_for_check = rule_model if rule_model else self.get_current_cot_model()
                                llm_result_text = self.run_utility_inference_sync(cot_context, model_for_check, 50)
                                llm_result_text_stripped = llm_result_text.strip() if llm_result_text else ""
                                try:
                                    print(f"    [RULE DEBUG] LLM reply for '{rule_id}': '{llm_result_text_stripped}'")
                                except Exception:
                                    pass
                                if llm_result_text is None:
                                    llm_condition_met = False
                                else:
                                    llm_condition_met = False
                                    for pair_data in tag_action_pairs:
                                        tag = pair_data.get('tag', '').strip()
                                        if not tag:
                                            llm_condition_met = True
                                            matched_pair_data = pair_data
                                            print(f"    ✓ Rule '{rule_id}' TEXT condition met (Empty Tag) for '{char}'.")
                                            break
                                        elif tag.lower() == llm_result_text_stripped.lower():
                                            llm_condition_met = True
                                            matched_pair_data = pair_data
                                            print(f"    ✓ Rule '{rule_id}' TEXT condition met (Exact Match: '{tag}') for '{char}'.")
                                            break
                                        elif llm_result_text_stripped.lower().startswith(tag.lower()):
                                                llm_condition_met = True
                                                matched_pair_data = pair_data
                                                print(f"    ✓ Rule '{rule_id}' TEXT condition met (Starts With: '{tag}') for '{char}'.")
                                                break
                                        elif llm_result_text_stripped.lower().startswith(f"[{tag.lower()}]"):
                                                llm_condition_met = True
                                                matched_pair_data = pair_data
                                                print(f"    ✓ Rule '{rule_id}' TEXT condition met (Starts with tag: '{tag}') for '{char}'.")
                                                break
                                    if not llm_condition_met:
                                        available_tags = [p.get('tag', '').strip() for p in tag_action_pairs if p.get('tag', '').strip()]
                                        print(f"    ✗ Rule '{rule_id}' TEXT condition FAILED for '{char}'.")
                                        print(f"      LLM Result: '{llm_result_text_stripped[:200]}{'...' if len(llm_result_text_stripped) > 200 else ''}'")
                                        print(f"      Available tags: {available_tags}")
                    elif not text_condition:
                            for pair_data in tag_action_pairs:
                                if not pair_data.get('tag', '').strip():
                                    matched_pair_data = pair_data
                                    break
                            if not matched_pair_data:
                                llm_condition_met = False
                    if llm_condition_met and matched_pair_data:
                        try:
                            dbg_widget = tab_data.get('debug_rules_widget')
                            if dbg_widget and hasattr(dbg_widget, 'on_rule_answer'):
                                dbg_widget.on_rule_answer(char_rule, llm_result_text_stripped if 'llm_result_text_stripped' in locals() else '', matched_pair_data.get('tag'))
                        except Exception:
                            pass
                        actions = matched_pair_data.get('actions', [])
                        for action_obj in actions:
                            action_type = action_obj.get('type')
                            if action_type == 'Switch Model':
                                switched_model = action_obj.get('value', '').strip()
                                if switched_model:
                                    model_to_use = switched_model
                                    print(f"        [Action] Switched model for '{char}' to: {model_to_use}")
                            elif action_type == 'System Message':
                                value = action_obj.get('value', '')
                                position = action_obj.get('position', 'prepend')
                                if value:
                                    if hasattr(self, '_substitute_variables_in_string'):
                                        value = self._substitute_variables_in_string(value, tab_data, char)
                                    context_modifications.append({'role': 'system', 'content': value, 'position': position})
                                    print(f"        [Action] Queued system message for '{char}' context ({position})")
                    if matched_pair_data:
                        returned_tag = _apply_rule_actions_and_continue(
                            self, matched_pair_data, char_rule, None, None, None, all_rules, False, False, character_name_override=char
                        )
                        if returned_tag:
                            tag_for_this_npc = returned_tag
                            print(f"    -> Captured tag '{tag_for_this_npc}' for NPC '{char}' from rule '{rule_id}'")
                        if char in tab_data.get('_characters_to_exit_rules', set()):
                            print(f"[EXIT RULE PROCESSING] Character '{char}' marked to exit rule processing - stopping further rules for this character")
                            break
                        characters_to_skip = tab_data.get('_characters_to_skip', set())
                        if char in characters_to_skip:
                            print(f"[SKIP POST] Character '{char}' marked to skip during rule '{rule_id}' - exiting rule processing early")
                            break
                        if tab_data.get('_exit_rule_processing'):
                            print(f"[EXIT RULE PROCESSING] Stopping rule processing for '{char}' due to Exit Rule Processing action")
                            tab_data['_exit_rule_processing'] = False
                            break
            npc_context_for_llm = []
            npc_context_for_llm.append({"role": "system", "content": system_msg_base_intro})
            npc_context_for_llm.append({"role": "user", "content": char_sheet_str})
            scenes_to_recall = 1
            npc_file_path = _find_actor_file_path(self, workflow_data_dir, char)
            if npc_file_path:
                try:
                    with open(npc_file_path, 'r', encoding='utf-8') as f:
                        npc_data = json.load(f)
                    variables = npc_data.get('variables', {})
                    if variables.get('following', '').strip().lower() == 'player':
                        scenes_to_recall = 2
                except Exception as e:
                    print(f"Error reading NPC file for follower check: {e}")
            chars_in_scene = set()
            if hasattr(self, 'get_character_names_in_scene_for_timers'):
                scene_chars_list = self.get_character_names_in_scene_for_timers(tab_data)
                chars_in_scene.update(s for s in scene_chars_list if s != char)
            try:
                mem_summary = _get_follower_memories_for_context(self, workflow_data_dir, char, list(chars_in_scene), filtered_context, scenes_to_recall=scenes_to_recall)
                if mem_summary:
                    npc_context_for_llm.append({"role": "user", "content": mem_summary})
            except Exception as e:
                print(f"[WARN] Could not inject follower memory summary for {char}: {e}")
            try:
                if npc_file_path:
                    npc_notes = get_npc_notes_from_character_file(npc_file_path)
                    if npc_notes:
                        formatted_notes = format_npc_notes_for_context(npc_notes, char)
                        if formatted_notes:
                            npc_context_for_llm.append({"role": "user", "content": formatted_notes})
            except Exception as e:
                print(f"[NPC NOTES] Error injecting notes for {char} in character inference: {e}")
            if setting_desc:
                setting_info_content = f"(The current setting of the scene is: {setting_desc}{setting_connections})"
                npc_context_for_llm.append({"role": "user", "content": setting_info_content})
            try:
                current_scene = tab_data.get('scene_number', 1)
                current_setting_name = _get_player_current_setting_name(workflow_data_dir) if workflow_data_dir else None
                location_info = get_location_info_for_keywords(workflow_data_dir, current_setting_file) if workflow_data_dir and current_setting_file else None
                is_narrator = False
                npc_context_for_llm = inject_keywords_into_context(
                    npc_context_for_llm, full_history_context, char, 
                    current_setting_name, location_info, workflow_data_dir, 
                    current_scene, is_narrator
                )
            except Exception as e:
                print(f"[WARN] Could not inject keywords for {char}: {e}")
            for item in history_to_add:
                npc_context_for_llm.append(item)
            for mod in context_modifications:
                if mod.get('role') == 'system' and mod.get('position') == 'prepend':
                    content = mod['content']
                    if hasattr(self, '_substitute_variables_in_string'):
                        content = self._substitute_variables_in_string(content, tab_data, char)
                    npc_context_for_llm.insert(1, {"role": "system", "content": content})
            npc_context_for_llm.append({
                "role": "user", 
                "content": f"(You are playing as: {char}. It is now {char}'s turn. What does {char} do or say next?)"
            })
            for mod in context_modifications:
                if mod.get('role') == 'system' and mod.get('position') == 'append':
                    content = mod['content']
                    if hasattr(self, '_substitute_variables_in_string'):
                        content = self._substitute_variables_in_string(content, tab_data, char)
                    npc_context_for_llm.append({"role": "system", "content": content})
            for mod in context_modifications:
                if mod.get('switch_model'):
                    model_to_use = mod['switch_model']
                    break
            characters_to_skip = tab_data.get('_characters_to_skip', set())
            if char in characters_to_skip:
                print(f"[SKIP POST] Character '{char}' marked to skip posting - skipping inference")
                characters_to_skip.discard(char)
                continue
            npc_inference_data = {
                'character': char,
                'context': npc_context_for_llm,
                'model': model_to_use,
                'tag': tag_for_this_npc
            }
            self._npc_inference_queue.append(npc_inference_data)
            final_npcs_to_infer_after_rules.append(char)
        if not final_npcs_to_infer_after_rules:
            print("[INPUT DEBUG] No characters to process (all skipped or none in scene)")
            had_npcs_but_all_skipped = len(npcs_in_scene) > 0 and len(final_npcs_to_infer_after_rules) == 0
            if tab_data and not tab_data.get('_fn_last_npc_turn_done', False):
                force_narrator_details = tab_data.get('force_narrator', {})
                narrator_also_skipped = tab_data.get('_skip_narrator_post', False)
                if narrator_also_skipped:
                    print("[INPUT DEBUG] Narrator also skipped - re-enabling input immediately")
                    tab_data.pop('_skip_narrator_post', None)
                    self._re_enable_input_after_pipeline()
                    self._allow_live_input_for_current_action = False
                elif force_narrator_details.get('active') and force_narrator_details.get('order', '').lower() == 'last':
                    tab_data['_fn_last_npc_turn_done'] = True
                    if had_npcs_but_all_skipped:
                        trigger_msg = self._last_user_msg_for_post_rules if hasattr(self, '_last_user_msg_for_post_rules') and self._last_user_msg_for_post_rules else "FN:Last deferred trigger (all NPCs skipped)"
                    else:
                        trigger_msg = self._last_user_msg_for_post_rules if hasattr(self, '_last_user_msg_for_post_rules') and self._last_user_msg_for_post_rules else "FN:Last deferred trigger (no NPCs in scene)"
                    QTimer.singleShot(0, lambda: self._complete_message_processing(trigger_msg))
                    self._npc_lock = False
                    if hasattr(self, 'timer_manager') and self.timer_manager:
                        self.timer_manager.resume_timers()
                    return
                else:
                    print("[INPUT DEBUG] No narrator action needed - re-enabling input")
                    self._re_enable_input_after_pipeline()
                    self._allow_live_input_for_current_action = False
            else:
                print("[INPUT DEBUG] No force narrator - re-enabling input")
                self._re_enable_input_after_pipeline()
                self._allow_live_input_for_current_action = False
            self._npc_lock = False
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        _start_next_npc_inference(self)
    except Exception as e:
        traceback.print_exc()

def _start_next_npc_inference(self):
    if self._narrator_streaming_lock:
        return
    if not self._npc_inference_queue:
        self._npc_inference_in_progress = False
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data.get('_is_force_narrator_first_active', False):
            self._npc_inference_queue = []
            self._npc_message_queue = []
            self._npc_inference_in_progress = False
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        if tab_data and tab_data.get('force_narrator', {}).get('active') and \
           tab_data.get('force_narrator', {}).get('order', '').lower() == 'last' and \
           tab_data.get('_fn_last_npc_turn_done', False):
            if hasattr(self, 'timer_manager') and self.timer_manager:
                self.timer_manager.resume_timers()
            return
        if tab_data and 'force_narrator' in tab_data and tab_data['force_narrator'].get('defer_to_end', False):
            tab_data['force_narrator']['defer_to_end'] = False
            self._narrator_streaming_lock = False
            tab_data['force_narrator']['active'] = True
            context = self.get_current_context()
            if context and len(context) > 0:
                last_user_msg = None
                for msg in reversed(context):
                    if msg.get('role') == 'user':
                        last_user_msg = msg.get('content', '')
                        break
                if last_user_msg:
                    saved_character = self.character_name
                    self.character_name = "Narrator"
                    def restore_character_after_processing():
                        self.character_name = saved_character
                    original_next_step = getattr(self, '_cot_next_step', None)
                    def combined_next_step():
                        restore_character_after_processing()
                        if original_next_step:
                            original_next_step()
                    self._cot_next_step = combined_next_step
                    tab_data['_deferred_last_narrator'] = True
                    QTimer.singleShot(0, lambda: self._complete_message_processing(last_user_msg))
                    return
        if hasattr(self, 'timer_manager') and self.timer_manager:
            self.timer_manager.resume_timers()
        return
    if self._npc_inference_in_progress:
        return
    tab_data = self.get_current_tab_data()
    if not tab_data:
        return
    if tab_data.get('force_narrator', {}).get('active') and \
       tab_data.get('force_narrator', {}).get('order', '').lower() == 'last' and \
       tab_data.get('_fn_last_npc_turn_done', False):
        self._npc_inference_queue = []
        if hasattr(self, 'timer_manager') and self.timer_manager:
            self.timer_manager.resume_timers()
        return
    npc_data = self._npc_inference_queue.pop(0)
    character = npc_data['character']
    context = npc_data['context']
    model = npc_data['model']
    tag = npc_data['tag']
    timer_final_instruction = tab_data.get('_timer_final_instruction') if tab_data else None
    if timer_final_instruction:
        context.append({"role": "user", "content": f"({timer_final_instruction})"})
    if character:
        pass
    else:
        print("[ERROR] Missing character in _start_next_npc_inference.")
        return
    if not context:
        print("[ERROR] Missing context in _start_next_npc_inference.")
        return
    self._npc_inference_in_progress = True

    self._current_npc_context = context.copy()
    self._current_npc_model = model

    
    from chatBotRPG import InferenceThread
    thread = InferenceThread(
        context,
        character,
        model,
        self.max_tokens,
        self.get_current_temperature()
    )

    def create_npc_result_handler(character_name, tag_to_use):
        def handler(msg):

            if isinstance(msg, str) and any(msg.strip().lower().startswith(failure_start) for failure_start in ['i\'m', 'sorry', 'ext']):
                print(f"[FALLBACK] Detected failure response '{msg}' for {character_name}, retrying with fallback models...")
                _retry_npc_inference_with_fallback(self, character_name, tag_to_use)
                return
            
            actual_character_name = get_actual_character_name(self, character_name)
            if actual_character_name and isinstance(msg, str):
                prefix = f"{actual_character_name}:"
                if msg.strip().startswith(prefix):
                    msg = msg.strip()[len(prefix):].lstrip()
            if isinstance(msg, str):
                msg = re.sub(r'<think>[\s\S]*?</think>', '', msg, flags=re.IGNORECASE).strip()
            tab_data = self.get_current_tab_data()
            has_llm_reply_rules = False
            print(f"[NPC INFERENCE] Checking for LLM reply rules for character: '{actual_character_name}'")
            if tab_data and 'thought_rules' in tab_data:
                for rule in tab_data.get('thought_rules', []):
                    rule_applies_to = rule.get('applies_to')
                    rule_scope = rule.get('scope')
                    rule_character_name = rule.get('character_name', '')
                    print(f"[NPC INFERENCE] Rule check: applies_to='{rule_applies_to}', scope='{rule_scope}', character_name='{rule_character_name}'")
                    if (rule_applies_to == 'Character' and 
                        rule_scope in ['llm_reply', 'convo_llm_reply'] and
                        (rule_character_name is None or 
                         rule_character_name == '' or 
                         rule_character_name == 'unknown' or 
                         rule_character_name == 'None' or
                         (rule_character_name and actual_character_name and rule_character_name.lower() == actual_character_name.lower()))):
                        has_llm_reply_rules = True
                        print(f"[NPC INFERENCE] Found matching rule for character '{actual_character_name}'")
                        break
            try:
                is_duplicate = False
                if tab_data and isinstance(msg, str):
                    ctx = tab_data.get('context', []) or []
                    candidate = msg.strip()
                    for m in ctx:
                        try:
                            if m.get('role') == 'assistant':
                                prev = str(m.get('content', '')).strip()
                                if prev == candidate:
                                    is_duplicate = True
                                    break
                        except Exception:
                            continue
                if is_duplicate:
                    if not hasattr(self, '_npc_dedupe_retry_done'):
                        self._npc_dedupe_retry_done = set()
                    if actual_character_name not in self._npc_dedupe_retry_done:
                        self._npc_dedupe_retry_done.add(actual_character_name)
                        print(f"[DEDUPE] NPC post for '{actual_character_name}' duplicates a previous post. Retrying with fallback models...")
                        _retry_npc_inference_with_fallback(self, actual_character_name, tag_to_use)
                        return
                    else:
                        print(f"[DEDUPE] Duplicate detected for '{actual_character_name}', but fallback already attempted. Proceeding.")
            except Exception:
                pass

            if has_llm_reply_rules:
                print(f"[NPC INFERENCE] Processing LLM reply rules for character '{actual_character_name}'")
                _process_character_llm_reply_rules(self, actual_character_name, msg, tag_to_use)
            else:
                character_text_tag = None
                if hasattr(self, '_character_tags') and actual_character_name in self._character_tags:
                    character_text_tag = self._character_tags[actual_character_name]
                    print(f"[CHARACTER INFERENCE] Found character text tag for {actual_character_name}: '{character_text_tag}'")
                _generate_and_save_npc_note(self, actual_character_name, msg)
                character_post_effects = _get_character_post_effects(self, actual_character_name)
                _queue_npc_message(self, msg, actual_character_name, character_text_tag or tag_to_use, character_post_effects)
        return handler
    npc_result_handler = create_npc_result_handler(character, tag)
    thread.result_signal.connect(npc_result_handler)
    thread.error_signal.connect(lambda err, c=character: print(f"[NPC INFERENCE ERROR] for character {c}: {err}"))
    def on_npc_thread_finished():
        _on_npc_inference_finished(self)
        self._npc_inference_in_progress = False
    thread.finished.connect(on_npc_thread_finished)
    self.npc_inference_threads.append(thread)
    QTimer.singleShot(0, lambda t=thread: t.start())

def _retry_npc_inference_with_fallback(self, character_name, tag_to_use):
    """Retry NPC inference with fallback models when primary model fails"""
    try:
        tab_data = self.get_current_tab_data()
        if not tab_data:
            print(f"[FALLBACK] No tab data available for {character_name}")
            return
        if not hasattr(self, '_current_npc_context') or not self._current_npc_context:
            print(f"[FALLBACK] No current NPC context stored for {character_name}")
            return
        original_context = self._current_npc_context
        original_model = getattr(self, '_current_npc_model', 'Unknown')
        from chatBotRPG import FALLBACK_MODEL_1, FALLBACK_MODEL_2, FALLBACK_MODEL_3
        fallback_models = [FALLBACK_MODEL_1, FALLBACK_MODEL_2, FALLBACK_MODEL_3]
        for i, fallback_model in enumerate(fallback_models):
            print(f"[FALLBACK] Attempting fallback model {i+1}: {fallback_model}")
            
            try:
                from chatBotRPG import InferenceThread
                fallback_thread = InferenceThread(
                    original_context,
                    character_name,
                    fallback_model,
                    self.max_tokens,
                    self.get_current_temperature()
                )
                
                def create_fallback_result_handler(fallback_char_name, fallback_tag, fallback_model_name):
                    def fallback_handler(msg):
                        if isinstance(msg, str) and any(msg.strip().lower().startswith(failure_start) for failure_start in ['i\'m', 'sorry', 'ext']):
                            print(f"[FALLBACK] Fallback model {fallback_model_name} also failed for {fallback_char_name}")
                            if i < len(fallback_models) - 1:
                                print(f"[FALLBACK] Will try next fallback model...")
                                return
                            else:
                                print(f"[FALLBACK] All fallback models failed for {fallback_char_name}")
                                error_msg = f"{fallback_char_name} seems to be having trouble responding right now."
                                _queue_npc_message(self, error_msg, fallback_char_name, fallback_tag, {})
                                return
                        actual_character_name = fallback_char_name
                        if actual_character_name and isinstance(msg, str):
                            prefix = f"{actual_character_name}:"
                            if msg.strip().startswith(prefix):
                                msg = msg.strip()[len(prefix):].lstrip()
                        if isinstance(msg, str):
                            msg = re.sub(r'<think>[\s\S]*?</think>', '', msg, flags=re.IGNORECASE).strip()
                        
                        tab_data = self.get_current_tab_data()
                        has_llm_reply_rules = False
                        print(f"[FALLBACK] Checking for LLM reply rules for character: '{actual_character_name}'")
                        if tab_data and 'thought_rules' in tab_data:
                            for rule in tab_data.get('thought_rules', []):
                                rule_applies_to = rule.get('applies_to')
                                rule_scope = rule.get('scope')
                                rule_character_name = rule.get('character_name', '')
                                print(f"[FALLBACK] Rule check: applies_to='{rule_applies_to}', scope='{rule_scope}', character_name='{rule_character_name}'")
                                if (rule_applies_to == 'Character' and 
                                    rule_scope in ['llm_reply', 'convo_llm_reply'] and
                                    (rule_character_name is None or 
                                     rule_character_name == '' or 
                                     rule_character_name == 'unknown' or 
                                     rule_character_name == 'None' or
                                     (rule_character_name and actual_character_name and rule_character_name.lower() == actual_character_name.lower()))):
                                    has_llm_reply_rules = True
                                    print(f"[FALLBACK] Found matching rule for character '{actual_character_name}'")
                                    break
                        
                        if has_llm_reply_rules:
                            print(f"[FALLBACK] Processing LLM reply rules for character '{actual_character_name}'")
                            _process_character_llm_reply_rules(self, actual_character_name, msg, fallback_tag)
                        else:
                            character_text_tag = None
                            if hasattr(self, '_character_tags') and actual_character_name in self._character_tags:
                                character_text_tag = self._character_tags[actual_character_name]
                                print(f"[FALLBACK] Found character text tag for {actual_character_name}: '{character_text_tag}'")
                            _generate_and_save_npc_note(self, actual_character_name, msg)
                            character_post_effects = _get_character_post_effects(self, actual_character_name)
                            _queue_npc_message(self, msg, actual_character_name, character_text_tag or fallback_tag, character_post_effects)
                    
                    return fallback_handler
                
                fallback_result_handler = create_fallback_result_handler(character_name, tag_to_use, fallback_model)
                fallback_thread.result_signal.connect(fallback_result_handler)
                fallback_thread.error_signal.connect(lambda err, c=character_name: print(f"[FALLBACK ERROR] for character {c}: {err}"))
                
                def on_fallback_thread_finished():
                    _on_npc_inference_finished(self)
                    self._npc_inference_in_progress = False
                
                fallback_thread.finished.connect(on_fallback_thread_finished)
                self.npc_inference_threads.append(fallback_thread)
                QTimer.singleShot(0, lambda t=fallback_thread: t.start())
                print(f"[FALLBACK] Started fallback inference for {character_name} using {fallback_model}")
                return
            except Exception as e:
                print(f"[FALLBACK] Error starting fallback model {fallback_model}: {e}")
                continue
        print(f"[FALLBACK] All fallback attempts failed for {character_name}")
    except Exception as e:
        print(f"[FALLBACK] Error in fallback retry for {character_name}: {e}")
        import traceback
        traceback.print_exc()

def get_actual_character_name(self, name_or_filename):
    if not hasattr(self, '_actor_name_to_actual_name'):
        return name_or_filename
    normalized_name = name_or_filename.strip().lower().replace(' ', '_')
    actual_name = self._actor_name_to_actual_name.get(normalized_name)
    return actual_name if actual_name else name_or_filename

def _get_character_post_effects(self, character_name):
    if hasattr(self, '_character_post_effects') and character_name in self._character_post_effects:
        return self._character_post_effects[character_name].copy()
    return {}

def _queue_npc_message(self, message, character_name, text_tag=None, post_effects=None):
    tab_data = self.get_current_tab_data()
    if tab_data and tab_data.get('_is_force_narrator_first_active', False):
        return
    npc_message_obj = {
        "content": message,
        "metadata": {"character_name": character_name}
    }
    if text_tag is not None:
        npc_message_obj["metadata"]["text_tag"] = text_tag
    if post_effects is not None:
        npc_message_obj["metadata"]["post_effects"] = post_effects
    if not hasattr(self, '_npc_message_queue'):
        self._npc_message_queue = []
    self._npc_message_queue.append(npc_message_obj)
    QTimer.singleShot(10, lambda: _check_process_npc_queue(self))

def _process_end_of_round_rules(self, tab_data, callback=None):
    if not tab_data:
        if callback:
            callback()
        return
    if tab_data.get('_end_of_round_rules_processed_for_turn') == tab_data.get('turn_count'):
        if callback:
            callback()
        return
    if tab_data.get('_npc_inference_in_progress', False):
        if callback:
            callback()
        return
    tab_data['_end_of_round_rules_processed_for_turn'] = tab_data.get('turn_count')
    if '_characters_to_exit_rules' in tab_data:
        print(f"[END OF ROUND] Clearing exit rule processing flags for characters: {tab_data['_characters_to_exit_rules']}")
        tab_data.pop('_characters_to_exit_rules', None)
    if '_narrator_to_exit_rules' in tab_data:
        print(f"[END OF ROUND] Clearing exit rule processing flag for narrator")
        tab_data.pop('_narrator_to_exit_rules', None)
    rules = tab_data.get('thought_rules', [])
    end_of_round_rules = [r for r in rules if r.get('applies_to') == 'End of Round']
    if not end_of_round_rules:
        if callback:
            callback()
        return
    self._cot_sequential_index = 0
    current_context = self.get_current_context()
    user_msg = ""
    assistant_msg = ""
    if current_context and len(current_context) >= 2:
        user_msg = current_context[-2].get('content', '') if current_context[-2].get('role') == 'user' else ""
        assistant_msg = current_context[-1].get('content', '') if current_context[-1].get('role') == 'assistant' else ""
    from rules.rule_evaluator import _process_next_sequential_rule_pre
    self._is_processing_eor = True
    def after_rules_with_cleanup():
        self._is_processing_eor = False
        if callback:
            callback()
    self._cot_next_step = after_rules_with_cleanup
    QTimer.singleShot(0, lambda: _process_next_sequential_rule_pre(self, user_msg, assistant_msg, end_of_round_rules))

def _check_process_npc_queue(self):
    tab_data = self.get_current_tab_data()
    if not tab_data:
        self._processing_npc_queue = False
        self._re_enable_input_after_pipeline()
        self._allow_live_input_for_current_action = False
        if hasattr(self, 'timer_manager') and self.timer_manager:
            self.timer_manager.resume_timers()
        return
    if tab_data.get('_is_force_narrator_first_active', False):
        self._npc_message_queue = []
        self._npc_inference_queue = []
        self._npc_inference_in_progress = False
        self._processing_npc_queue = False
        self._re_enable_input_after_pipeline()
        self._allow_live_input_for_current_action = False
        if hasattr(self, 'timer_manager') and self.timer_manager:
            self.timer_manager.resume_timers()
        return
    if self._npc_message_queue:
        if not self._processing_npc_queue:
            _display_next_npc_message(self)
        return
    if self._npc_inference_queue:
        if not self._processing_npc_queue:
            _start_next_npc_inference(self)
        return
    if self._processing_npc_queue:
        self._processing_npc_queue = False
    force_narrator_details = tab_data.get('force_narrator', {}) if tab_data else {}
    is_fn_last_active = force_narrator_details.get('active') and force_narrator_details.get('order', '').lower() == 'last'
    fn_last_npc_turn_done = tab_data.get('_fn_last_npc_turn_done', False) if tab_data else False
    if is_fn_last_active and not fn_last_npc_turn_done:
        if tab_data:
            tab_data['_fn_last_npc_turn_done'] = True
            self._npc_message_queue = []
            self._npc_inference_queue = []
            self._npc_inference_in_progress = False
        trigger_msg = "(The scene settles after other characters have acted.)"
        if force_narrator_details.get('system_message'):
            trigger_msg = "(A moment passes, allowing for a final narration.)"
        def fn_last_final_executor(trig_msg_param=trigger_msg):
            original_character_name_fn = self.character_name
            self.character_name = "Narrator"
            if tab_data:
                is_timer_triggered = bool(
                    tab_data.get('_timer_final_instruction') or 
                    tab_data.get('_is_timer_narrator_action_active') or
                    tab_data.get('_last_timer_action_type')
                )
                if not is_timer_triggered:
                    tab_data.pop('_timer_final_instruction', None)
                    tab_data.pop('_is_timer_narrator_action_active', None)
                    tab_data.pop('_last_timer_action_type', None)
                    tab_data.pop('_last_timer_character', None)
                    tab_data.pop('_suppress_npcs_for_one_turn', None)
            if hasattr(self, '_last_user_msg_for_post_rules') and self._last_user_msg_for_post_rules:
                self._last_user_msg_for_post_rules = None
            try:
                self._complete_message_processing(trig_msg_param)
            except Exception as e_fn_complete:
                traceback.print_exc()
                self.character_name = original_character_name_fn
                self._re_enable_input_after_pipeline()
                self._allow_live_input_for_current_action = False
                self._schedule_timer_checks()
        QTimer.singleShot(0, fn_last_final_executor)
        return
    def after_end_of_round():
        if hasattr(self, '_last_user_msg_for_post_rules') and self._last_user_msg_for_post_rules:
            self._last_user_msg_for_post_rules = None
        self._re_enable_input_after_pipeline()
        self._allow_live_input_for_current_action = False
        self._schedule_timer_checks()
        if hasattr(self, 'timer_manager') and self.timer_manager:
            self.timer_manager.resume_timers()
    if tab_data.get('_end_of_round_rules_processed_for_turn') != tab_data.get('turn_count'):
        _process_end_of_round_rules(self, tab_data, callback=after_end_of_round)
        return
    after_end_of_round()

def _display_next_npc_message(self):
    tab_data_check = self.get_current_tab_data()
    if not tab_data_check:
        return
    time_manager_widget = tab_data_check.get('time_manager_widget')
    if time_manager_widget and hasattr(time_manager_widget, 'update_time'):
        time_manager_widget.update_time(self, tab_data_check)
    self._processing_npc_queue = True
    message_data = self._npc_message_queue.pop(0)
    message_content = message_data['content']
    character_name_local = message_data['metadata']['character_name']
    text_tag_local = message_data.get('metadata', {}).get('text_tag')
    post_effects_local = message_data.get('metadata', {}).get('post_effects')
    current_scene_for_npc = tab_data_check.get('scene_number', 1)
    message_widget = self.display_message('assistant', message_content, text_tag=text_tag_local, character_name=character_name_local, post_effects=post_effects_local)
    if hasattr(self, 'return3_sound') and self.return3_sound:
        self.return3_sound.play()
    current_context = self.get_current_context()
    if current_context is not None:
        save_npc_message_obj = {
            "role": "assistant",
            "content": message_content,
            "scene": current_scene_for_npc,
            "metadata": {"character_name": character_name_local}
        }
        if text_tag_local is not None:
            save_npc_message_obj["metadata"]["text_tag"] = text_tag_local
        if post_effects_local is not None:
            save_npc_message_obj["metadata"]["post_effects"] = post_effects_local
            if 'post_visibility' in post_effects_local:
                save_npc_message_obj["metadata"]["post_visibility"] = post_effects_local['post_visibility']
        workflow_data_dir = tab_data_check.get('workflow_data_dir')
        if workflow_data_dir:
            location = _get_player_current_setting_name(workflow_data_dir)
            if location:
                save_npc_message_obj["metadata"]["location"] = location
        current_turn_for_metadata = tab_data_check.get('turn_count', 0)
        save_npc_message_obj["metadata"]["turn"] = current_turn_for_metadata
        
        if workflow_data_dir:
            try:
                tab_index = self.tabs_data.index(tab_data_check) if tab_data_check in self.tabs_data else -1
                if tab_index >= 0:
                    variables = self._load_variables(tab_index)
                    game_datetime = variables.get('datetime')
                    if game_datetime:
                        save_npc_message_obj["metadata"]["game_datetime"] = game_datetime
            except Exception as e:
                print(f"Error adding game timestamp to NPC message: {e}")
        
        current_context.append(save_npc_message_obj)
        self._save_context_for_tab(self.current_tab_index)
        
        right_splitter = tab_data_check.get('right_splitter') if tab_data_check else None
        if right_splitter and hasattr(right_splitter, 'update_game_time'):
            right_splitter.update_game_time()
        
        if hasattr(self, '_npc_inference_queue') and self._npc_inference_queue:
            self._update_remaining_character_contexts()
    time_manager_widget = tab_data_check.get('time_manager_widget') if tab_data_check else None
    if time_manager_widget and hasattr(time_manager_widget, 'update_time'):
        time_manager_widget.update_time(self, tab_data_check)
    if hasattr(self, 'timer_manager') and tab_data_check:
        pass
    theme_settings = tab_data_check.get('settings', {}) if tab_data_check else {}
    streaming_enabled = theme_settings.get("streaming_enabled", False)
    def streaming_done_callback():
        self._processing_npc_queue = False
        QTimer.singleShot(10, lambda: _check_process_npc_queue(self))
    is_currently_streaming = (streaming_enabled and
                              message_widget and
                              hasattr(message_widget, 'is_streaming') and
                              message_widget.is_streaming())
    if is_currently_streaming:
        def check_periodic_streaming_status():
            try:
                if not message_widget or not hasattr(message_widget, 'is_streaming') or not message_widget.is_streaming():
                    streaming_done_callback()
                else:
                    QTimer.singleShot(100, check_periodic_streaming_status)
            except RuntimeError:
                streaming_done_callback()
        QTimer.singleShot(100, check_periodic_streaming_status)
    else:
        streaming_done_callback()


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
        output_lines = []
        follower_memories = data.get('follower_memories', {})
        if followed_name in follower_memories:
            stored_memory = follower_memories[followed_name]
            if stored_memory and stored_memory.strip():
                output_lines.append(f"(Your memories of adventures with {followed_name_for_display}):\n" + stored_memory)
        tab_data = self.get_current_tab_data()
        if not tab_data:
            return None
        current_scene = tab_data.get('scene_number', 1)
        prior_scene = current_scene - 1
        messages_to_summarize = []
        for msg in current_context:
            scene_num = msg.get('scene', 1)
            if msg.get('role') != 'system' and scene_num < prior_scene:
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
                    if role == 'user':
                        player_name = _get_player_name_for_context(workflow_data_dir)
                        summary_lines.append(f"Scene {scene_num}: {player_name}: {content}")
                    elif role == 'assistant' and char_name:
                        summary_lines.append(f"Scene {scene_num}: {char_name}: {content}")
                if summary_lines:
                    summary = '\n'.join(summary_lines[-10:])
                    output_lines.append(f"(Summary of earlier shared scenes between {actor_name} and {followed_name_for_display}):\n" + summary)
            except Exception as e:
                import traceback
                traceback.print_exc()
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
                            scene_msgs.append(f"{followed_name_for_display}: {content}")
                        else:
                            scene_msgs.append(f"Narrator: {content}")
            if scene_msgs:
                output_lines.append(f"Your character ({actor_name}) is following ({followed_name_for_display}). Here were your interactions in the previous scene:\n" + "\n".join(scene_msgs))
        final_output = '\n\n'.join(output_lines) if output_lines else None
        return final_output
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

def _should_suppress_narrator(self, tab_data=None):
    if not tab_data:
        if hasattr(self, 'get_current_tab_data'):
            tab_data = self.get_current_tab_data()
        if not tab_data:
            return False
    if tab_data.get('_skip_narrator_post', False):
        tab_data['_skip_narrator_post'] = False
        return True
    if hasattr(self, '_narrator_streaming_lock') and self._narrator_streaming_lock:
        return False 
    if tab_data.get('_suppress_narrator_for_npcs', False):
        return True
    force_narrator_details = tab_data.get('force_narrator', {})
    fn_order = force_narrator_details.get('order')
    is_current_call_for_fn_first = tab_data.get('_is_force_narrator_first_active', False)
    if is_current_call_for_fn_first:
        if not tab_data.get('_has_narrator_posted_this_scene', False):
            characters_for_fn_first_check = self.get_character_names_in_scene_for_timers(tab_data)
            if characters_for_fn_first_check:
                tab_data['_temp_is_first_npc_scene_post'] = True
        return False
    if force_narrator_details.get('active', False) and fn_order.lower() == 'last':
        if tab_data.get('_fn_last_npc_turn_done', False):
            return False
    characters_in_scene = self.get_character_names_in_scene_for_timers(tab_data)
    if characters_in_scene:
        has_narrator_posted_this_scene = tab_data.get('_has_narrator_posted_this_scene', False)
        if not has_narrator_posted_this_scene:
            tab_data['_temp_is_first_npc_scene_post'] = True 
            return False
        else:
            return True
    if hasattr(self, '_npc_message_queue') and self._npc_message_queue:
        return True
    if hasattr(self, '_npc_inference_queue') and self._npc_inference_queue:
        return True
    return False

def _on_npc_inference_finished(self):
    finished_thread = self.sender()
    if not finished_thread:
        return
    if finished_thread in self.npc_inference_threads:
        self.npc_inference_threads.remove(finished_thread)
        try:
            finished_thread.disconnect()
        except TypeError:
                pass

def _generate_and_save_npc_note(self, character_name, npc_response):
    try:
        tab_data = self.get_current_tab_data()
        if not tab_data:
            return
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            return
        session_file_path = _ensure_session_actor_file(self, workflow_data_dir, character_name)
        if not session_file_path:
            return
        current_context = self.get_current_context()
        if not current_context:
            return
        recent_messages = []
        for msg in current_context[-5:]:
            if msg.get('role') == 'user':
                player_name = _get_player_name_for_context(workflow_data_dir)
                recent_messages.append(f"{player_name}: {msg.get('content', '')}")
            elif msg.get('role') == 'assistant':
                char_name = msg.get('metadata', {}).get('character_name', 'Unknown')
                recent_messages.append(f"{char_name}: {msg.get('content', '')}")
        recent_messages.append(f"{character_name}: {npc_response}")
        context_str = "\n".join(recent_messages)
        note_prompt = f"""Based on this recent conversation, write a very brief note (1-2 sentences max) from {character_name}'s perspective about what just happened or what they learned. Focus on key events, discoveries, or important interactions. Write in first person as {character_name}.
Recent conversation:
{context_str}
Brief note from {character_name}'s perspective:"""
        note_context = [
            {"role": "system", "content": "You are helping an NPC character write brief personal notes about recent events. Keep notes very concise and in first person."},
            {"role": "user", "content": note_prompt}
        ]
        
        model = tab_data.get('settings', {}).get('cot_model', get_default_cot_model())
        from chatBotRPG import UtilityInferenceThread
        thread = UtilityInferenceThread(
            chatbot_ui_instance=self,
            context=note_context,
            model_identifier=model,
            max_tokens=100,
            temperature=0.7
        )
        note_data = {
            'character_name': character_name,
            'session_file_path': session_file_path
        }

        def on_note_generated(note_content):
            try:
                if note_content and note_content.strip():
                    note_content = note_content.strip()
                    if note_content.startswith('"') and note_content.endswith('"'):
                        note_content = note_content[1:-1]
                    add_npc_note_to_character_file(note_data['session_file_path'], note_content)
            except Exception as e:
                import traceback
                traceback.print_exc()
        def on_note_error(error_msg):
            print(f"[NPC NOTES] Error generating note for {character_name}: {error_msg}")
        thread.result_signal.connect(on_note_generated)
        thread.error_signal.connect(on_note_error)
        if not hasattr(self, 'note_inference_threads'):
            self.note_inference_threads = []
        self.note_inference_threads.append(thread)
        def cleanup_thread():
            try:
                if thread in self.note_inference_threads:
                    self.note_inference_threads.remove(thread)
            except Exception as e:
                print(f"[NPC NOTES] Error cleaning up note thread: {e}")
        thread.finished.connect(cleanup_thread)
        thread.start()
    except Exception as e:
        pass

def _ensure_session_actor_file(self, workflow_data_dir, character_name):
    try:
        normalized_name = character_name.strip().lower().replace(' ', '_')
        session_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
        session_file_path = os.path.join(session_actors_dir, f"{normalized_name}.json")
        if os.path.exists(session_file_path):
            return session_file_path
        from utils import _find_actor_file_path
        template_file_path = _find_actor_file_path(self, workflow_data_dir, character_name)
        if not template_file_path:
            return None
        if '/resources/data files/actors/' not in template_file_path.replace('\\', '/'):
            return None
        with open(template_file_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        if 'npc_notes' in template_data:
            del template_data['npc_notes']
        os.makedirs(session_actors_dir, exist_ok=True)
        with open(session_file_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)
        return session_file_path
    except Exception as e:
        return None

def _process_character_llm_reply_rules(self, character_name, character_message, tag_to_use):
    try:
        tab_data = self.get_current_tab_data()
        if not tab_data or 'thought_rules' not in tab_data:
            _finalize_character_message(self, character_name, character_message, tag_to_use)
            return
        all_rules = tab_data.get('thought_rules', [])
        character_llm_reply_rules = []
        for rule in all_rules:
            applies_to_match = rule.get('applies_to') == 'Character'
            scope_match = rule.get('scope') in ['llm_reply', 'convo_llm_reply']
            rule_character_name_value = rule.get('character_name')
            rule_character_name_lower = None
            if isinstance(rule_character_name_value, str):
                rule_character_name_lower = rule_character_name_value.strip().lower()
            character_name_lower = character_name.strip().lower() if isinstance(character_name, str) else None
            character_match = (
                rule_character_name_value is None or
                (rule_character_name_lower in ['', 'unknown', 'none']) or
                (rule_character_name_lower is not None and character_name_lower is not None and rule_character_name_lower == character_name_lower)
            )
            if applies_to_match and scope_match and character_match:
                character_llm_reply_rules.append(rule)
        if not character_llm_reply_rules:
            _finalize_character_message(self, character_name, character_message, tag_to_use)
            return
        if not hasattr(self, '_character_message_buffers'):
            self._character_message_buffers = {}
        self._character_message_buffers[character_name] = character_message
        if not hasattr(self, '_character_original_tags'):
            self._character_original_tags = {}
        self._character_original_tags[character_name] = tag_to_use
        self._character_llm_reply_current_character = character_name
        self._character_llm_reply_rules_queue = character_llm_reply_rules
        self._character_llm_reply_rule_index = 0
        if not hasattr(self, '_character_text_tags'):
            self._character_text_tags = {}
        existing_character_tag = self._character_tags.get(character_name, "")
        self._character_text_tags[character_name] = existing_character_tag
        if character_name in self._character_tags:
            self._character_tags[character_name] = ""
        self._character_llm_reply_rule_complete_callback = _process_next_character_llm_reply_rule.__get__(self)
        self._character_llm_reply_rule_complete_callback()
    except Exception as e:
        print(f"[ERROR] Could not start character LLM reply rule processing for {character_name}: {e}")

def _process_next_character_llm_reply_rule(self):
    try:
        if (self._character_llm_reply_rule_index >= len(self._character_llm_reply_rules_queue)):
            character_name = self._character_llm_reply_current_character
            final_accumulated_tag = self._character_text_tags.get(character_name, "")
            self._character_tags[character_name] = final_accumulated_tag
            self._character_llm_reply_rule_complete_callback = None
            final_message = self._character_message_buffers.get(character_name, "")
            original_tag = self._character_original_tags.get(character_name, None)
            _finalize_character_message(self, character_name, final_message, original_tag)
            return
        rule = self._character_llm_reply_rules_queue[self._character_llm_reply_rule_index]
        character_name = self._character_llm_reply_current_character
        character_message = self._character_message_buffers.get(character_name, "")

        def on_rule_complete(chatbot_instance=None, current_user_msg=None, prev_assistant_msg=None, rules_list=None):
            rule_contribution = self._character_tags.get(character_name, "").strip()
            if rule_contribution:
                master_tag = self._character_text_tags.get(character_name, "")
                new_master_tag = (master_tag + " " + rule_contribution).strip()
                self._character_text_tags[character_name] = new_master_tag
            self._character_llm_reply_rule_index += 1
            _process_next_character_llm_reply_rule(self)
        self._character_llm_reply_rule_complete_callback = on_rule_complete
        self._character_tags[character_name] = ""
        from rules.rule_evaluator import _process_specific_rule
        _process_specific_rule(
            self, rule, getattr(self, '_last_user_msg_for_post_rules', ""), character_message, 
            self._character_llm_reply_rules_queue, 
            rule_index=self._character_llm_reply_rule_index, 
            triggered_directly=False,
            is_post_phase=True,
            character_name=character_name
        )
    except Exception as e:
        self._character_llm_reply_rule_complete_callback = None
        character_name = getattr(self, '_character_llm_reply_current_character', None)
        if character_name:
            final_message = self._character_message_buffers.get(character_name, "")
            original_tag = self._character_original_tags.get(character_name, None)
            _finalize_character_message(self, character_name, final_message, original_tag)

def _finalize_character_message(self, character_name, final_message, tag_to_use):
    try:
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data.get('_is_force_narrator_first_active', False):
            if hasattr(self, '_character_message_buffers'):
                self._character_message_buffers.pop(character_name, None)
            if hasattr(self, '_character_original_tags'):
                self._character_original_tags.pop(character_name, None)
            if hasattr(self, '_character_text_tags'):
                self._character_text_tags.pop(character_name, None)
            if hasattr(self, '_character_tags'):
                self._character_tags.pop(character_name, None)
            return
        if not final_message or not final_message.strip():
            if hasattr(self, '_character_message_buffers'):
                self._character_message_buffers.pop(character_name, None)
            if hasattr(self, '_character_original_tags'):
                self._character_original_tags.pop(character_name, None)
            if hasattr(self, '_character_text_tags'):
                self._character_text_tags.pop(character_name, None)
            if hasattr(self, '_character_tags'):
                self._character_tags.pop(character_name, None)
            return
        final_tag = self._character_tags.get(character_name, tag_to_use)
        self._current_llm_reply = final_message
        _generate_and_save_npc_note(self, character_name, final_message)
        character_post_effects = _get_character_post_effects(self, character_name)
        _queue_npc_message(self, final_message, character_name, final_tag, character_post_effects)
        
        right_splitter = tab_data.get('right_splitter') if tab_data else None
        if right_splitter and hasattr(right_splitter, 'update_game_time'):
            right_splitter.update_game_time()
        is_timer_triggered = False
        if tab_data:
            is_timer_triggered = bool(tab_data.get('_timer_final_instruction') or 
                                     tab_data.get('_is_timer_narrator_action_active') or
                                     tab_data.get('_last_timer_action_type'))
        if hasattr(self, '_character_message_buffers'):
            self._character_message_buffers.pop(character_name, None)
        if hasattr(self, '_character_original_tags'):
            self._character_original_tags.pop(character_name, None)
        if hasattr(self, '_character_text_tags'):
            self._character_text_tags.pop(character_name, None)
        if hasattr(self, '_character_tags'):
            if is_timer_triggered:
                self._character_tags.pop(character_name, None)
            else:
                self._character_tags.pop(character_name, None)
    except Exception as e:
        print(f"[ERROR] Finalizing character message for {character_name}: {e}")
        import traceback
        traceback.print_exc()