from PyQt5.QtCore import QTimer
import os
import json
import random
from core.move_character import move_characters
from rules.apply_rules import _apply_rule_side_effects
from core.utils import (_get_player_character_name, _prepare_condition_text, 
                 _get_player_current_setting_name, 
                 _get_random_filtered_entity_name)
import time

def _evaluate_conditions(self, tab_data, conditions, operator, current_turn, triggered_directly=False, character_name=None):
    from editor_panel.time_manager import update_time
    update_time(self, tab_data)
    tab_index = self.tabs_data.index(tab_data) if tab_data in self.tabs_data else -1
    if tab_index >= 0:
        variables_file = tab_data.get('variables_file')
        if variables_file and os.path.exists(variables_file):
            try:
                with open(variables_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        tab_data['variables'] = json.loads(content)
                    else:
                        tab_data['variables'] = {}
            except Exception as e:
                print(f"ERROR: Could not reload variables for rule evaluation: {e}")
    if not conditions:
        if triggered_directly:
            print(f"[RULE EVAL] No conditions and triggered_directly=True -> TRUE")
            return True
        print(f"[RULE EVAL] No conditions and triggered_directly=False -> FALSE")
        return False
    results = []
    for idx, cond_row_data in enumerate(conditions):
        if 'applies_to' not in cond_row_data and character_name:
            cond_row_data['character_name'] = character_name
        print(f"[RULE EVAL] Condition {idx+1}: {cond_row_data}")
        result = self._evaluate_condition_row(tab_data, cond_row_data, current_turn, triggered_directly)
        print(f"[RULE EVAL] Condition {idx+1} result: {result}")
        results.append(result)
        if (operator.upper() == "AND" or operator.upper() == "ALL") and not result:
            print(f"[RULE EVAL] AND operator: condition {idx+1} failed, short-circuiting -> FALSE")
            return False
        elif (operator.upper() == "OR" or operator.upper() == "ANY") and result:
            print(f"[RULE EVAL] OR operator: condition {idx+1} passed, short-circuiting -> TRUE")
            return True
    if operator.upper() == "OR" or operator.upper() == "ANY":
        final_result = any(results)
    else:
        final_result = all(results)
    return final_result

def _process_specific_rule(self, rule, current_user_msg, prev_assistant_msg, rules_list, rule_index=None, triggered_directly=False, is_post_phase=False, character_name=None, original_sequential_context=None):
    from chatBotRPG import InferenceThread
    tab_data = self.get_current_tab_data()
    if tab_data:
        applies_to_char = rule.get('applies_to', 'Narrator') == 'Character'
        char_context = character_name or rule.get('character_name')
        if applies_to_char and char_context and char_context in tab_data.get('_characters_to_exit_rules', set()):
            print(f"Skipping rule '{rule.get('id')}' for '{char_context}' due to prior Exit Rule Processing action.")
            if not triggered_directly and rule_index is not None:
                self._cot_sequential_index += 1
                from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
            elif hasattr(self, '_cot_next_step') and self._cot_next_step:
                 QTimer.singleShot(0, self._cot_next_step)
                 self._cot_next_step = None
            return

        if not applies_to_char and tab_data.get('_narrator_to_exit_rules', False):
             print(f"Skipping narrator rule '{rule.get('id')}' due to prior Exit Rule Processing action.")
             if not triggered_directly and rule_index is not None:
                self._cot_sequential_index += 1
                from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
             elif hasattr(self, '_cot_next_step') and self._cot_next_step:
                QTimer.singleShot(0, self._cot_next_step)
                self._cot_next_step = None
             return
             
    if original_sequential_context:
        self._original_sequential_context = original_sequential_context
    if self.utility_inference_thread and self.utility_inference_thread.isRunning():
        QTimer.singleShot(50, lambda: _process_specific_rule(
            self, rule, current_user_msg, prev_assistant_msg, rules_list, rule_index, triggered_directly, is_post_phase, character_name, original_sequential_context
        ))
        return
    rule_id = rule.get('id', f"#{rule_index if rule_index is not None else 'Triggered'}")
    tab_data = self.get_current_tab_data()
    if not tab_data:
        if hasattr(self, '_cot_next_step') and self._cot_next_step:
            QTimer.singleShot(0, self._cot_next_step)
            self._cot_next_step = None
        return
    applies_to = rule.get('applies_to', 'Narrator')
    if applies_to == 'Character':
        rule_character_name = rule.get('character_name')
        current_inference_character = getattr(self, 'character_name', 'Narrator')
        should_run_character_rule = False
        target_character = character_name if character_name else rule_character_name
        if current_inference_character == target_character:
            should_run_character_rule = True
        else:
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if workflow_data_dir:
                try:
                    from core.utils import _get_player_current_setting_name, _find_setting_file_prioritizing_game_dir, _load_json_safely
                    current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                    if current_setting_name and current_setting_name != "Unknown Setting":
                        setting_file_path, _ = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, current_setting_name)
                        if setting_file_path and os.path.exists(setting_file_path):
                            setting_data = _load_json_safely(setting_file_path)
                            if setting_data:
                                characters_in_setting = setting_data.get('characters', [])
                                if target_character in characters_in_setting:
                                    should_run_character_rule = True
                except Exception as e:
                    print(f"Error checking character presence for rule '{rule_id}': {e}")
        if not should_run_character_rule:
            if not triggered_directly and rule_index is not None:
                self._cot_sequential_index += 1
                from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
            elif triggered_directly:
                if hasattr(self, '_cot_next_step') and self._cot_next_step:
                    QTimer.singleShot(0, self._cot_next_step)
                    self._cot_next_step = None
            return
    conditions_met = _evaluate_conditions(self, tab_data, rule.get('conditions', []), rule.get('conditions_operator', 'AND'), tab_data.get('turn_count', 1), triggered_directly, character_name)
    if not conditions_met:
        if (hasattr(self, '_character_llm_reply_rule_complete_callback') and 
            self._character_llm_reply_rule_complete_callback and
            rule.get('applies_to') == 'Character' and 
            character_name):
            callback = self._character_llm_reply_rule_complete_callback
            QTimer.singleShot(0, callback)
            return
        if not triggered_directly and rule_index is not None:
            self._cot_sequential_index += 1
            from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
            callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
            QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
        elif triggered_directly:
            original_context = getattr(self, '_original_sequential_context', None)
            if original_context:
                self._original_sequential_context = None
                self._cot_sequential_index = original_context['sequential_index']
                if (original_context['sequential_index'] < len(original_context['rules']) and 
                    original_context['rules'][original_context['sequential_index']].get('id') == rule_id):
                    self._cot_sequential_index += 1
                from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                callback = _process_next_sequential_rule_post if original_context['is_post_phase'] else _process_next_sequential_rule_pre
                QTimer.singleShot(0, lambda: callback(self, original_context['current_user_msg'], original_context['prev_assistant_msg'], original_context['rules']))
            else:
                if hasattr(self, '_cot_next_step') and self._cot_next_step:
                    QTimer.singleShot(0, self._cot_next_step)
                    self._cot_next_step = None
            return
        return
    tag_action_pairs = rule.get('tag_action_pairs', [])
    condition_raw = rule.get('condition', '').strip()
    actor_for_condition_substitution = character_name
    condition = self._substitute_variables_in_string(condition_raw, tab_data, actor_for_condition_substitution)
    if not condition:
        found_empty_tag_action = False
        for pair in tag_action_pairs:
            tag = pair.get('tag', '').strip()
            if not tag:
                _apply_rule_actions_and_continue(
                    self, pair, rule, rule_index, current_user_msg, prev_assistant_msg, rules_list, triggered_directly, is_post_phase, character_name_for_rule_context=character_name
                )
                found_empty_tag_action = True
                return
        if not found_empty_tag_action:
            if not triggered_directly and rule_index is not None:
                self._cot_sequential_index += 1
                from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
            elif triggered_directly:
                if hasattr(self, '_cot_sequential_index') and self._cot_sequential_index is not None and rules_list:
                    self._cot_sequential_index += 1
                    from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                    callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                    QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
                else:
                    if hasattr(self, '_cot_next_step') and self._cot_next_step:
                        QTimer.singleShot(0, self._cot_next_step)
                        self._cot_next_step = None
            return
    else:
        if not tag_action_pairs:
            if not triggered_directly and rule_index is not None:
                self._cot_sequential_index += 1
                from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
            elif triggered_directly:
                    if hasattr(self, '_cot_next_step') and self._cot_next_step:
                        QTimer.singleShot(0, self._cot_next_step)
                        self._cot_next_step = None
            return
        tags = []
        for pair in tag_action_pairs:
            tag = pair.get('tag', '').strip()
            if tag:
                tags.append(tag)
        if not tags and tag_action_pairs:
                found_empty_tag_action = False
                for pair in tag_action_pairs:
                    tag = pair.get('tag', '').strip()
                    if not tag:
                        _apply_rule_actions_and_continue(
                            self, pair, rule, rule_index, current_user_msg, prev_assistant_msg, rules_list, triggered_directly, is_post_phase, character_name_for_rule_context=character_name
                        )
                        found_empty_tag_action = True
                        return
                if not found_empty_tag_action:
                    if not triggered_directly and rule_index is not None:
                        self._cot_sequential_index += 1
                        from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                        callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                        QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
                    elif triggered_directly:
                        if hasattr(self, '_cot_sequential_index') and self._cot_sequential_index is not None and rules_list:
                            self._cot_sequential_index += 1
                            from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                            callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                            QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules_list))
                        else:
                            if hasattr(self, '_cot_next_step') and self._cot_next_step:
                                QTimer.singleShot(0, self._cot_next_step)
                                self._cot_next_step = None
                    return
        elif tags:
            tags_for_prompt = ", ".join([f"[{t}]" for t in tags])
            scope = rule.get('scope', 'user_message')
            if is_post_phase or scope == 'llm_reply':
                print(f">>> Rule '{rule_id}' SCOPE: LLM Reply")
            elif scope == 'full_conversation':
                current_scene = tab_data.get('scene_number', 1)
                print(f">>> Rule '{rule_id}' SCOPE: Full Conversation (Scene {current_scene})")
            elif scope == 'last_exchange':
                print(f">>> Rule '{rule_id}' SCOPE: Last Exchange")
            elif scope == 'convo_llm_reply':
                print(f">>> Rule '{rule_id}' SCOPE: Conversation+LLM Reply")
            else:
                print(f">>> Rule '{rule_id}' SCOPE: User Message (Default)")
                
            print(f"    Rule '{rule_id}' evaluating text condition (Scope: {scope}) for '{condition[:50]}...'...")

            player_name = _get_player_character_name(self, tab_data.get('workflow_data_dir'))
            prepared_condition_text = _prepare_condition_text(self, condition, player_name, 
                                                             character_name, 
                                                             tab_data, scope, 
                                                             current_user_msg, prev_assistant_msg)
            if not any(f"[{tag.lower()}]" in condition.lower() for tag in tags) and "choose" not in condition.lower():
                    prepared_condition_text += f"\nChoose ONLY one of these responses: {tags_for_prompt}"
            cot_context = [
                {"role": "system", "content": f"You are analyzing text based on a specific instruction. Respond ONLY with one of the provided choices, based on the text and the instruction. - Respond with only the chosen tag in square brackets (e.g., [TAG_NAME]) - "},
                {"role": "user", "content": prepared_condition_text}
            ]
            rule_model = rule.get('model')
            model_to_use = rule_model if rule_model else self.get_current_cot_model()
            callback_info = {
                'rule': rule, 'rule_id': rule_id, 'rule_index': rule_index,
                'current_user_msg': current_user_msg, 'prev_assistant_msg': prev_assistant_msg,
                'rules_list': rules_list, 'triggered_directly': triggered_directly, 'is_post_phase': is_post_phase,
                'character_name': character_name
            }
            def on_inference_complete(result):
                self._handle_rule_result(
                    result, rule, rule_index,
                    current_user_msg, prev_assistant_msg, rules_list,
                    triggered_directly=triggered_directly, tried_fallback1=False, tried_fallback2=False, tried_fallback3=False,
                    is_post_phase=is_post_phase, character_name_for_rule_context=character_name
                )
            def on_inference_error(error):
                self._handle_rule_error(
                    error, rule, rule_index,
                    current_user_msg, prev_assistant_msg, rules_list,
                    triggered_directly=triggered_directly, is_post_phase=is_post_phase,
                    tried_fallback1=False, tried_fallback2=False, tried_fallback3=False,
                    character_name_for_rule_context=character_name
                )
            self.utility_inference_thread = InferenceThread(
                cot_context, self.character_name, model_to_use, 100, 0.1, is_utility_call=True
            )
            self.utility_inference_thread.result_signal.connect(on_inference_complete)
            self.utility_inference_thread.error_signal.connect(on_inference_error)
            self.utility_inference_thread.start()

def _process_next_sequential_rule_pre(self, current_user_msg, prev_assistant_msg, rules):
    tab_data = self.get_current_tab_data()
    if not tab_data:
        return
    if tab_data.get('_exit_rule_processing'):
        print("  Rule processing explicitly exited via 'Exit Rule Processing' action")
        tab_data.pop('_exit_rule_processing', None)
        if hasattr(self, '_cot_next_step') and self._cot_next_step:
            QTimer.singleShot(0, self._cot_next_step)
            self._cot_next_step = None
        return
    if not hasattr(self, '_cot_sequential_index'):
        self._cot_sequential_index = 0
    if not rules or self._cot_sequential_index >= len(rules):
        if hasattr(self, '_cot_next_step') and self._cot_next_step:
            QTimer.singleShot(0, self._cot_next_step)
            self._cot_next_step = None
        return
    rule = rules[self._cot_sequential_index]
    rule_id = rule.get('id', f"Rule_{self._cot_sequential_index}")
    should_process = True
    applies_to = rule.get('applies_to', 'Narrator')
    is_eor_processing = getattr(self, '_is_processing_eor', False)
    if applies_to == 'End of Round' and not is_eor_processing:
        self._cot_sequential_index += 1
        QTimer.singleShot(0, lambda: _process_next_sequential_rule_pre(self, current_user_msg, prev_assistant_msg, rules))
        return
    
    if applies_to == 'Character':
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if workflow_data_dir and hasattr(self, 'get_character_names_in_scene_for_timers'):
            npcs_in_scene = self.get_character_names_in_scene_for_timers(tab_data)
            if not npcs_in_scene:
                print(f"[DEBUG] Skipping character rule '{rule_id}' - no characters in scene")
                should_process = False
        else:
            print(f"[DEBUG] Skipping character rule '{rule_id}' - no workflow data dir or method")
            should_process = False
    if should_process:
        conditions = rule.get('conditions', [])
        if conditions:
            operator = rule.get('conditions_operator', 'AND')
            current_turn = tab_data.get('turn_count', 1)
            should_process = _evaluate_conditions(self, tab_data, conditions, operator, current_turn)
    if should_process:
        print(f"[DEBUG] Executing rule '{rule_id}'")
        _process_specific_rule(self, rule, current_user_msg, prev_assistant_msg, rules, 
                              rule_index=self._cot_sequential_index, triggered_directly=False, is_post_phase=False)
    else:
        self._cot_sequential_index += 1
        QTimer.singleShot(0, lambda: _process_next_sequential_rule_pre(self, current_user_msg, prev_assistant_msg, rules))

def _process_next_sequential_rule_post(self, current_user_msg, assistant_msg, rules):
    tab_data = self.get_current_tab_data()
    if not tab_data:
        return
    if tab_data.get('_exit_rule_processing'):
        print("  Rule processing explicitly exited via 'Exit Rule Processing' action")
        tab_data.pop('_exit_rule_processing', None)
        if hasattr(self, '_cot_next_step') and self._cot_next_step:
            QTimer.singleShot(0, self._cot_next_step)
            self._cot_next_step = None
        return
    
    if not hasattr(self, '_cot_sequential_index'):
        self._cot_sequential_index = 0
    if not rules or self._cot_sequential_index >= len(rules):
        if hasattr(self, '_cot_next_step') and self._cot_next_step:
            QTimer.singleShot(0, self._cot_next_step)
            self._cot_next_step = None
        return
    rule = rules[self._cot_sequential_index]
    rule_id = rule.get('id', f"Rule_{self._cot_sequential_index}")
    should_process = True
    applies_to = rule.get('applies_to', 'Narrator')
    
    is_eor_processing = getattr(self, '_is_processing_eor', False)
    if applies_to == 'End of Round' and not is_eor_processing:
        print(f"[DEBUG] Skipping End of Round rule '{rule_id}' during normal rule processing")
        self._cot_sequential_index += 1
        QTimer.singleShot(0, lambda: _process_next_sequential_rule_post(self, current_user_msg, assistant_msg, rules))
        return
    
    if applies_to == 'Character':
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if workflow_data_dir and hasattr(self, 'get_character_names_in_scene_for_timers'):
            npcs_in_scene = self.get_character_names_in_scene_for_timers(tab_data)
            if not npcs_in_scene:
                should_process = False
        else:
            should_process = False
    if should_process:
        conditions = rule.get('conditions', [])
        if conditions:
            operator = rule.get('conditions_operator', 'AND')
            current_turn = tab_data.get('turn_count', 1)
            should_process = _evaluate_conditions(self, tab_data, conditions, operator, current_turn)
    if should_process:
        _process_specific_rule(self, rule, current_user_msg, assistant_msg, rules, 
                              rule_index=self._cot_sequential_index, triggered_directly=False, is_post_phase=True)
    else:
        self._cot_sequential_index += 1
        QTimer.singleShot(0, lambda: _process_next_sequential_rule_post(self, current_user_msg, assistant_msg, rules))

def _apply_rule_actions_and_continue(self, matched_pair, rule, rule_index, current_user_msg, prev_assistant_msg, rules, triggered_directly, is_post_phase, rewrite_context=False, character_name_override=None, character_name_for_rule_context=None):
    tab_data = self.get_current_tab_data()
    if not tab_data: return
    rule_id = rule.get('id', f"Rule #{rule_index if rule_index is not None else 'Triggered'}")
    actions = matched_pair.get('actions', [])
    actor_for_substitution = None
    if character_name_for_rule_context:
        actor_for_substitution = character_name_for_rule_context
    elif character_name_override:
        actor_for_substitution = character_name_override
    elif rule.get('applies_to') == 'Character':
        actor_for_substitution = rule.get('character_name')
    force_narrator_action_obj = None
    if not hasattr(self, '_character_tags'):
        self._character_tags = {}
    character_name_for_tag = character_name_override or character_name_for_rule_context or rule.get('character_name')
    npc_text_tag_for_character_rule = None
    if rule.get('applies_to') == 'Character' and character_name_for_tag:
        npc_text_tag_for_character_rule = self._character_tags.get(character_name_for_tag, None)
    if is_post_phase:
        self._cot_rule_triggered_post = True
    else:
        self._cot_rule_triggered_pre = True
    for action_idx, action_obj in enumerate(actions):
        action_type = action_obj.get('type', 'System Message')

        if action_type == 'Force Narrator':
            if force_narrator_action_obj:
                print(f"  WARNING: Multiple 'Force Narrator' actions in rule '{rule_id}'. Only the first one will be processed.")
            else:
                force_narrator_action_obj = action_obj
            continue
        elif action_type == 'System Message':
            raw_value = action_obj.get('value', '')
            processed_value = self._substitute_variables_in_string(raw_value, tab_data, actor_for_substitution)
            position = action_obj.get('position', 'prepend')
            sysmsg_position = action_obj.get('system_message_position', 'first')
            if not rewrite_context or (rewrite_context and not is_post_phase):
                system_mod = {
                    'action': processed_value, 'position': position,
                    'system_message_position': sysmsg_position, 'switch_model': None
                }
                self._cot_system_modifications.append(system_mod)
                is_timer_triggered = tab_data and bool(
                    tab_data.get('_timer_final_instruction') or 
                    tab_data.get('_is_timer_narrator_action_active') or
                    tab_data.get('_last_timer_action_type')
                )
                if is_timer_triggered and hasattr(self, '_timer_system_modifications'):
                    existing_mod = None
                    for existing in self._timer_system_modifications:
                        if (existing.get('action') == processed_value and 
                            existing.get('position') == position and
                            existing.get('system_message_position') == sysmsg_position):
                            existing_mod = existing
                            break
                    if not existing_mod:
                        self._timer_system_modifications.append(system_mod.copy())
        elif action_type == 'Switch Model':
            switch_model_value = action_obj.get('value', '')
            if not rewrite_context or (rewrite_context and not is_post_phase):
                self._cot_system_modifications.append({
                    'action': '', 'position': rule.get('position', 'prepend'),
                    'system_message_position': rule.get('system_message_position', 'first'),
                    'switch_model': switch_model_value,
                    'temperature': action_obj.get('temperature')
                })
        elif action_type == 'Next Rule':
            pass
        elif action_type == 'Set Var':
            current_action_character_name = character_name_override
            if current_action_character_name is None:
                current_action_character_name = character_name_for_rule_context
            if current_action_character_name is None and rule.get('applies_to') == 'Character':
                 current_action_character_name = rule.get('character_name')
            operation = action_obj.get('operation', 'set').lower()
            if operation == 'generate':
                var_name = action_obj.get('var_name', '').strip()
                scope = action_obj.get('variable_scope', 'Global')
                var_filepath = tab_data.get('variables_file') if scope == 'Global' else None
                generate_mode = action_obj.get('generate_mode', 'LLM')
                if generate_mode == 'Random':
                    random_type = action_obj.get('random_type', 'Number')
                    processed_var_value = None
                    if random_type == 'Number':
                        min_str = action_obj.get('random_number_min', '0')
                        max_str = action_obj.get('random_number_max', '0')
                        actor_context_for_substitution = None
                        if character_name_override:
                            actor_context_for_substitution = character_name_override
                        elif rule.get('applies_to') == 'Character':
                            actor_context_for_substitution = rule.get('character_name')
                        elif character_name_for_rule_context:
                            actor_context_for_substitution = character_name_for_rule_context
                        min_str_substituted = self._substitute_variables_in_string(str(min_str), tab_data, actor_context_for_substitution)
                        max_str_substituted = self._substitute_variables_in_string(str(max_str), tab_data, actor_context_for_substitution)
                        
                        def parse_numeric_value(value_str, field_name):
                            try:
                                return int(value_str)
                            except ValueError:
                                try:
                                    return int(float(value_str))
                                except ValueError:
                                    cleaned = value_str.strip()
                                    if cleaned.replace('-', '').replace('.', '').isdigit():
                                        return int(float(cleaned))
                                    else:
                                        raise ValueError(f"'{value_str}' is not a valid number for {field_name}")
                        try:
                            min_val = parse_numeric_value(min_str_substituted, "min")
                            max_val = parse_numeric_value(max_str_substituted, "max")
                            if min_val > max_val:
                                min_val, max_val = max_val, min_val
                            random_number = random.randint(min_val, max_val)
                            processed_var_value = str(random_number)
                        except ValueError as e:
                            continue
                    elif random_type == 'Setting':
                        filters_str = action_obj.get('random_setting_filters', "")
                        if isinstance(filters_str, list):
                            filters_str = ",".join(filters_str)
                        setting_name = _get_random_filtered_entity_name(tab_data.get('workflow_data_dir'), 'settings', filters_str)
                        if setting_name:
                            processed_var_value = setting_name
                    elif random_type == 'Character':
                        filters_str = action_obj.get('random_character_filters', "")
                        if isinstance(filters_str, list):
                            filters_str = ",".join(filters_str)
                        char_name = _get_random_filtered_entity_name(tab_data.get('workflow_data_dir'), 'actors', filters_str)
                        if char_name:
                            processed_var_value = char_name
                    if processed_var_value is not None:
                        set_var_mode = action_obj.get('set_var_mode', 'replace')
                        delimiter = action_obj.get('set_var_delimiter', '/')
                        modified_action_obj_for_random = {
                            'type': 'Set Var',
                            'var_name': var_name,
                            'var_value': processed_var_value,
                            'variable_scope': scope,
                            'operation': 'set',
                            'set_var_mode': set_var_mode,
                            'set_var_delimiter': delimiter
                        }
                        actor_for_random_var_set = None
                        if character_name_override:
                            actor_for_random_var_set = character_name_override
                        elif rule.get('applies_to') == 'Character':
                             actor_for_random_var_set = rule.get('character_name')
                        elif character_name_for_rule_context:
                             actor_for_random_var_set = character_name_for_rule_context
                        _apply_rule_side_effects(self, modified_action_obj_for_random, rule, actor_for_random_var_set)
                        continue
                    else:
                        continue
                elif generate_mode == 'LLM':
                    gen_instructions = action_obj.get('generate_instructions', '')
                    gen_context_type = action_obj.get('generate_context', 'Last Exchange')
                    context_str = None
                    if gen_context_type == 'Full Conversation':
                        current_scene_number = tab_data.get('scene_number', 1)
                        current_scene_messages = [msg for msg in tab_data.get('context', [])
                                                if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene_number]
                        formatted_history = [f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')}"
                                            for msg in current_scene_messages]
                        context_str = "\n".join(formatted_history)
                    elif gen_context_type == 'Last Exchange':
                        context_str = f"Assistant: {prev_assistant_msg}\nUser: {current_user_msg}"
                    else:
                        context_str = current_user_msg
                    llm_gen_character_context = character_name_override
                    if llm_gen_character_context is None and rule.get('applies_to') == 'Character':
                        llm_gen_character_context = rule.get('character_name')
                    elif llm_gen_character_context is None and character_name_for_rule_context:
                        llm_gen_character_context = character_name_for_rule_context
                    from generate.generate_summary import generate_summary
                    set_var_mode = action_obj.get('set_var_mode', 'replace')
                    delimiter = action_obj.get('set_var_delimiter', '/')
                    generate_summary(self, context_str, gen_instructions, var_name, scope, var_filepath, llm_gen_character_context, tab_data, set_var_mode, delimiter)
                    continue
            else:
                var_name = action_obj.get('var_name')
                var_value_raw = action_obj.get('var_value', '') 
                var_scope = action_obj.get('variable_scope', 'Global')
                operation = action_obj.get('operation', 'set')
                actor_context_for_substitution = None
                actor_for_var_set = None
                if var_scope == 'Character' or rule.get('applies_to') == 'Character':
                    actor_for_var_set = action_obj.get('character_name')
                    if not actor_for_var_set:
                        actor_for_var_set = rule.get('character_name')
                    actor_context_for_substitution = actor_for_var_set
                if character_name_override:
                    if var_scope == 'Character' or not actor_for_var_set:
                        actor_for_var_set = character_name_override
                    actor_context_for_substitution = character_name_override
                if character_name_for_rule_context and not actor_for_var_set:
                    actor_for_var_set = character_name_for_rule_context
                    actor_context_for_substitution = character_name_for_rule_context
                processed_var_value = self._substitute_variables_in_string(str(var_value_raw), tab_data, actor_context_for_substitution)
                modified_action_obj = action_obj.copy()
                modified_action_obj['var_value'] = processed_var_value
                _apply_rule_side_effects(self, modified_action_obj, rule, actor_for_var_set)

        elif action_type == 'Set Screen Effect':
            _apply_rule_side_effects(self, action_obj, rule, actor_for_substitution)
        elif action_type == 'Change Actor Location':
            actor_name_str = action_obj.get('actor_name', '')
            location_mode = action_obj.get('location_mode', 'Setting')
            target_setting = action_obj.get('target_setting', '')
            advance_time = action_obj.get('advance_time', True)
            if actor_name_str:
                character_context = character_name_override if character_name_override else actor_for_substitution
                actor_name_str = self._substitute_placeholders_in_condition_value(actor_name_str, tab_data, character_context)
            if target_setting:
                character_context = character_name_override if character_name_override else actor_for_substitution
                target_setting = self._substitute_placeholders_in_condition_value(target_setting, tab_data, character_context)
            rule_trigger_context_for_move = None
            if location_mode == 'Adjacent':
                if is_post_phase:
                    rule_trigger_context_for_move = prev_assistant_msg
                else:
                    rule_trigger_context_for_move = current_user_msg
            move_success = _perform_change_actor_location(self, tab_data,
                                           actor_name_str,
                                           location_mode,
                                           target_setting,
                                           rule_trigger_context_for_move,
                                           advance_time
                                          )
            if not move_success:
                break
        elif action_type == 'Rewrite Post':
            if not is_post_phase:
                continue
            rewrite_instructions_val = action_obj.get('value', '').strip()
            if rewrite_instructions_val:
                character_context = character_name_override if character_name_override else actor_for_substitution
                rewrite_instructions_val = self._substitute_variables_in_string(rewrite_instructions_val, tab_data, character_context)
            if rewrite_context:
                print(f"    Warning: Already in rewrite context, ignoring nested rewrite request.")
            else:
                rewrite_instructions = rewrite_instructions_val
                if rule.get('applies_to') == 'Character':
                    current_character = character_name_for_rule_context or character_name_override or getattr(self, 'character_name', None)
                    if current_character and hasattr(self, '_character_message_buffers') and current_character in self._character_message_buffers:
                        rewrite_buffer_content = self._character_message_buffers[current_character]
                        print(f"  >> Rule '{rule_id}' Action (Phase 3): Rewrite Character Post for {current_character} (Instructions: '{rewrite_instructions[:50]}...')")
                    else:
                        print(f"    Warning: Character message buffer not found for {current_character}, falling back to assistant buffer")
                        rewrite_buffer_content = self._assistant_message_buffer
                else:
                    rewrite_buffer_content = self._assistant_message_buffer
                break

        elif action_type == 'Text Tag':
            tag_text = action_obj.get('value', '').strip()
            if tag_text:
                character_context = character_name_override if character_name_override else actor_for_substitution
                tag_text = self._substitute_placeholders_in_condition_value(tag_text, tab_data, character_context)
            tag_mode = action_obj.get('tag_mode', 'overwrite').lower()
            if tag_text:
                applies_to_rule = rule.get('applies_to', 'Narrator')
                if applies_to_rule == 'Character':
                    current_character_tag = npc_text_tag_for_character_rule or ""
                    if tag_mode == 'append':
                        if current_character_tag:
                            npc_text_tag_for_character_rule = current_character_tag + " " + tag_text
                        else:
                            npc_text_tag_for_character_rule = tag_text
                    elif tag_mode == 'prepend':
                        if current_character_tag:
                            npc_text_tag_for_character_rule = tag_text + " " + current_character_tag
                        else:
                            npc_text_tag_for_character_rule = tag_text
                    else:
                        npc_text_tag_for_character_rule = tag_text
                    if character_name_for_tag:
                        self._character_tags[character_name_for_tag] = npc_text_tag_for_character_rule
                    print(f"  >> Rule '{rule_id}' Action: Set Text Tag to '{npc_text_tag_for_character_rule}' for Character")
                else:
                    current_cot_tag = self._cot_text_tag or ""
                    if tag_mode == 'append':
                        if current_cot_tag:
                            self._cot_text_tag = current_cot_tag + " " + tag_text
                        else:
                            self._cot_text_tag = tag_text
                    elif tag_mode == 'prepend':
                        if current_cot_tag:
                            self._cot_text_tag = tag_text + " " + current_cot_tag
                        else:
                            self._cot_text_tag = tag_text
                    else:
                        self._cot_text_tag = tag_text
                    print(f"  >> Rule '{rule_id}' Action: Set Text Tag to '{self._cot_text_tag}' for Narrator")
            else:
                if tag_mode == 'overwrite':
                    applies_to_rule = rule.get('applies_to', 'Narrator')
                    if applies_to_rule == 'Character':
                        pass
                    else:
                        self._cot_text_tag = ""

        elif action_type == 'Change Brightness':
            brightness_value = action_obj.get('brightness', '1.0')
            try:
                brightness_float = float(brightness_value)
                brightness_float = max(0.0, min(2.0, brightness_float))
                applies_to_rule = rule.get('applies_to', 'Narrator')
                if applies_to_rule == 'Character':
                    character_name_for_brightness = character_name_for_rule_context or character_name_override
                    if character_name_for_brightness:
                        if not hasattr(self, '_character_post_effects'):
                            self._character_post_effects = {}
                        if character_name_for_brightness not in self._character_post_effects:
                            self._character_post_effects[character_name_for_brightness] = {}
                        self._character_post_effects[character_name_for_brightness]['brightness'] = brightness_float
                else:
                    if not hasattr(self, '_narrator_post_effects'):
                        self._narrator_post_effects = {}
                    self._narrator_post_effects['brightness'] = brightness_float
            except (ValueError, TypeError):
                print(f"  >> Rule '{rule_id}' Action: Invalid brightness value '{brightness_value}', skipping")
        elif action_type == 'New Scene':
            if tab_data:
                current_scene = tab_data.get('scene_number', 1)
                new_scene_number = current_scene + 1
                tab_data['scene_number'] = new_scene_number
                tab_data['pending_scene_update'] = True
        elif action_type == 'Generate Character':
            raw_instructions = action_obj.get('instructions', '').strip()
            instructions = self._substitute_variables_in_string(raw_instructions, tab_data, actor_for_substitution)
            location = action_obj.get('location', '').strip()
            attach_context = action_obj.get('attach_context', False)
            generation_mode = action_obj.get('generation_mode', 'Create New')
            target_directory = action_obj.get('target_directory', 'Game')
            target_actor_name = action_obj.get('target_actor_name', '').strip()
            fields_to_generate = action_obj.get('fields_to_generate', [])
            model_override = action_obj.get('model_override', '').strip()
            if target_actor_name:
                character_context = character_name_override if character_name_override else actor_for_substitution
                target_actor_name = self._substitute_placeholders_in_condition_value(target_actor_name, tab_data, character_context)
            workflow_dir = tab_data.get('workflow_data_dir')
            if attach_context:
                context_list = tab_data.get('context', [])
                current_scene = tab_data.get('scene_number', 1)
                current_scene_messages = [msg for msg in context_list 
                                         if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene]
                context_str = '\n'.join([f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')}" 
                                         for msg in current_scene_messages])
                if context_str:
                    instructions = f"[CURRENT SCENE CONTEXT]\n{context_str}\n[/CURRENT SCENE CONTEXT]\n" + instructions
            if generation_mode == 'Edit Existing' and target_actor_name and workflow_dir:
                try:
                    from core.utils import _find_actor_file_path, _load_json_safely
                    existing_actor_file = _find_actor_file_path(self, workflow_dir, target_actor_name)
                    if existing_actor_file:
                        existing_actor_data = _load_json_safely(existing_actor_file)
                        if existing_actor_data:
                            import json
                            existing_data_str = json.dumps(existing_actor_data, indent=2)
                            instructions = f"[EXISTING CHARACTER DATA]\n{existing_data_str}\n[/EXISTING CHARACTER DATA]\n\n" + instructions
                except Exception as e:
                    print(f"    >> Generate Character: Error loading existing character data: {e}")
            final_location_for_gen = location
            if not final_location_for_gen and tab_data:
                current_setting = tab_data.get('current_setting_name', '')
                if current_setting: 
                    final_location_for_gen = current_setting
            if workflow_dir:
                try:
                    if generation_mode == 'Edit Existing':
                        from generate.generate_actor import trigger_actor_edit_from_rule
                        trigger_actor_edit_from_rule(
                            target_actor_name=target_actor_name,
                            fields_to_generate=fields_to_generate,
                            instructions=instructions,
                            location=final_location_for_gen,
                            workflow_data_dir=workflow_dir,
                            target_directory=target_directory,
                            model_override=model_override if model_override else None
                        )
                        character_being_edited = character_name_for_rule_context if character_name_for_rule_context else character_name_override
                        if (character_being_edited and 
                            target_actor_name == character_being_edited and 
                            hasattr(self, 'inference_thread') and self.inference_thread and 
                            hasattr(self.inference_thread, 'context')):
                            def refresh_character_context():
                                try:
                                    from core.utils import _find_actor_file_path, _load_json_safely
                                    import os
                                    npc_file_path = _find_actor_file_path(self, workflow_dir, target_actor_name)
                                    if npc_file_path and os.path.exists(npc_file_path):
                                        file_mod_time = os.path.getmtime(npc_file_path)
                                        current_time = time.time()
                                        if (current_time - file_mod_time) < 10:
                                            updated_character_data = _load_json_safely(npc_file_path)
                                            if updated_character_data:
                                                context = self.inference_thread.context
                                                for i, msg in enumerate(context):
                                                    if (msg.get('role') == 'user' and 
                                                        msg.get('content', '').startswith('Your character sheet (JSON format):')):
                                                        import json
                                                        new_content = f"Your character sheet (JSON format):\n```json\n{json.dumps(updated_character_data, indent=2)}\n```"
                                                        context[i]['content'] = new_content
                                                        break
                                                from chatBotRPG import get_npc_notes_from_character_file, format_npc_notes_for_context
                                                updated_notes = get_npc_notes_from_character_file(npc_file_path)
                                                if updated_notes:
                                                    formatted_updated_notes = format_npc_notes_for_context(updated_notes, target_actor_name)
                                                    if formatted_updated_notes:
                                                        for i, msg in enumerate(context):
                                                            if (msg.get('role') == 'user' and 
                                                                msg.get('content', '').startswith(f"Your personal notes and memories as {target_actor_name}:")):
                                                                context[i]['content'] = formatted_updated_notes
                                                                break
                                                        else:
                                                            context.append({"role": "user", "content": formatted_updated_notes})
                                except Exception as e:
                                    import traceback
                                    traceback.print_exc()
                            QTimer.singleShot(1000, refresh_character_context)
                    else:
                        from generate.generate_actor import trigger_actor_creation_from_rule
                        trigger_actor_creation_from_rule(
                            fields_to_generate=fields_to_generate,
                            instructions=instructions,
                            location=final_location_for_gen,
                            workflow_data_dir=workflow_dir,
                            target_directory=target_directory,
                            model_override=model_override if model_override else None
                        )
                    if final_location_for_gen:
                        if is_post_phase:
                            tab_data['_deferred_actor_reload'] = final_location_for_gen
                        else:
                            from core.utils import reload_actors_for_setting
                            reload_actors_for_setting(workflow_dir, final_location_for_gen)
                except Exception as e:
                    print(f"    ERROR: Failed to trigger enhanced character generation: {e}")
        elif action_type == 'Generate Random List':
            _apply_rule_side_effects(self, action_obj, rule, actor_for_substitution)
        elif action_type == 'Skip Post':
            if tab_data:
                if rule.get('applies_to') == 'Character':
                    character_to_skip = character_name_for_rule_context or character_name_override or getattr(self, 'character_name', None)
                    if character_to_skip:
                        if '_characters_to_skip' not in tab_data:
                            tab_data['_characters_to_skip'] = set()
                        tab_data['_characters_to_skip'].add(character_to_skip)
                    else:
                        pass
                else:
                    tab_data['_skip_narrator_post'] = True
            else:
                pass
        elif action_type == 'Exit Rule Processing':
            character_to_exit = character_name_for_rule_context or character_name_override or getattr(self, 'character_name', None)
            if tab_data:
                if character_to_exit:
                    if '_characters_to_exit_rules_after_current' not in tab_data:
                        tab_data['_characters_to_exit_rules_after_current'] = set()
                    tab_data['_characters_to_exit_rules_after_current'].add(character_to_exit)
                    print(f"  >> Rule '{rule_id}' Action: Exit Rule Processing for '{character_to_exit}'. Further rules for this character will be skipped after this rule completes.")
                else:
                    tab_data['_narrator_to_exit_rules_after_current'] = True
                    print(f"  >> Rule '{rule_id}' Action: Exit Rule Processing for Narrator. Further rules will be skipped after this rule completes.")
        elif action_type == 'Game Over':
            _apply_rule_side_effects(self, action_obj, rule, actor_for_substitution)
            return None
    try:
        if force_narrator_action_obj:
            force_order = force_narrator_action_obj.get('force_narrator_order', 'First')
            raw_fn_sysmsg = force_narrator_action_obj.get('force_narrator_system_message', '').strip()
            fn_system_message = self._substitute_variables_in_string(raw_fn_sysmsg, tab_data, actor_for_substitution)
            if tab_data:
                if 'force_narrator' not in tab_data:
                    tab_data['force_narrator'] = {}
                tab_data['force_narrator']['order'] = force_order
                tab_data['force_narrator']['active'] = True
                tab_data['force_narrator']['_set_timestamp'] = time.time()
                if fn_system_message:
                    tab_data['force_narrator']['system_message'] = fn_system_message
                if force_order.lower() == 'last':
                    tab_data['force_narrator']['defer_to_end'] = True
                elif force_order.lower() == 'first':
                    self._narrator_streaming_lock = False
                    tab_data['_is_force_narrator_first_active'] = True
                    if hasattr(self, '_cot_text_tag') and self._cot_text_tag:
                        tab_data['_force_narrator_first_text_tag'] = self._cot_text_tag
                    QTimer.singleShot(0, lambda: self._complete_message_processing(current_user_msg))
                    if rule.get('applies_to') == 'Character':
                        return npc_text_tag_for_character_rule
                    else:
                        return None
                else:
                    tab_data['force_narrator']['defer_to_end'] = False
            else:
                pass
    finally:
        pass
    triggered_next_rule_id = None
    rewrite_instructions = None
    rewrite_buffer_content = None
    for action_obj in actions:
        action_type = action_obj.get('type')
        if action_type == 'Next Rule':
            next_rule_id_val = action_obj.get('value', '').strip()
            if next_rule_id_val and next_rule_id_val != "None":
                triggered_next_rule_id = next_rule_id_val
                break
        elif action_type == 'Rewrite Post':
            if not is_post_phase:
                continue
            rewrite_instructions_val = action_obj.get('value', '').strip()
            if rewrite_instructions_val:
                character_context = character_name_override if character_name_override else actor_for_substitution
                rewrite_instructions_val = self._substitute_variables_in_string(rewrite_instructions_val, tab_data, character_context)
            if rewrite_context:
                pass
            else:
                rewrite_instructions = rewrite_instructions_val
                if rule.get('applies_to') == 'Character':
                    current_character = character_name_for_rule_context or character_name_override or getattr(self, 'character_name', None)
                    if current_character and hasattr(self, '_character_message_buffers') and current_character in self._character_message_buffers:
                        rewrite_buffer_content = self._character_message_buffers[current_character]
                    else:
                        rewrite_buffer_content = self._assistant_message_buffer
                else:
                    rewrite_buffer_content = self._assistant_message_buffer
                break
    if rewrite_instructions is not None and rewrite_buffer_content is not None and is_post_phase:
        self._trigger_rule_after_rewrite = triggered_next_rule_id
        rewrite_context = [
            {"role": "system", "content": "You are helping to rewrite a message. Follow the instructions exactly and return only the rewritten content."},
            {"role": "user", "content": f"Original message:\n{rewrite_buffer_content}\n\nRewrite instructions:\n{rewrite_instructions}\n\nRewritten message:"}
        ]
        try:
            current_model = self.get_current_cot_model()
            rewritten_message = self.run_utility_inference_sync(rewrite_context, current_model, 1024)
            if rule.get('applies_to') == 'Character' and character_name_for_rule_context:
                if hasattr(self, '_character_message_buffers') and character_name_for_rule_context in self._character_message_buffers:
                    self._character_message_buffers[character_name_for_rule_context] = rewritten_message
                    if hasattr(self, '_character_llm_reply_rule_index'):
                        self._character_llm_reply_rule_index += 1
                        from core.character_inference import _process_next_character_llm_reply_rule
                        QTimer.singleShot(0, lambda: _process_next_character_llm_reply_rule(self))
                    else:
                        pass
                else:
                    pass
            else:
                original_rule_context = {
                    'character_name': character_name_for_rule_context
                }
                self._handle_rewrite_result(rewritten_message, triggered_next_rule_id, original_rule_context)
        except Exception as e:
            pass
        if rule.get('applies_to') == 'Character':
            return npc_text_tag_for_character_rule
        return None
    if triggered_next_rule_id:
        if rule.get('applies_to') == 'Character' and character_name_for_rule_context:
            next_rule_data = next((r for r in tab_data.get('thought_rules', []) if r.get('id') == triggered_next_rule_id), None)
            if next_rule_data:
                if hasattr(self, '_character_llm_reply_rules_queue'):
                    self._character_llm_reply_rules_queue.insert(self._character_llm_reply_rule_index + 1, next_rule_data)
                    if (hasattr(self, '_character_llm_reply_triggered_directly') and 
                        character_name_for_rule_context in self._character_llm_reply_triggered_directly):
                        self._character_llm_reply_triggered_directly[character_name_for_rule_context].insert(
                            self._character_llm_reply_rule_index + 1, True
                        )
                    pass
                else:
                    pass
            else:
                pass
            if rule.get('applies_to') == 'Character':
                return npc_text_tag_for_character_rule
            return None
        next_rule_data = next((r for r in tab_data.get('thought_rules', []) if r.get('id') == triggered_next_rule_id), None)
        if next_rule_data:
            triggered_is_post_phase = next_rule_data.get('scope') == 'llm_reply'
            context_msg_for_trigger = self._assistant_message_buffer if triggered_is_post_phase else self._last_user_msg_for_post_rules
            user_msg_context = self._last_user_msg_for_post_rules
            original_sequential_context = None
            if not triggered_directly and rule_index is not None:
                original_sequential_context = {
                    'sequential_index': rule_index + 1,
                    'rules': rules,
                    'current_user_msg': current_user_msg,
                    'prev_assistant_msg': prev_assistant_msg,
                    'is_post_phase': is_post_phase
                }
            QTimer.singleShot(0, lambda nr=next_rule_data, ar=tab_data.get('thought_rules', []), um=user_msg_context, pm=context_msg_for_trigger, ipp=triggered_is_post_phase, seq_ctx=original_sequential_context:
                _process_specific_rule(self, nr, um, pm, ar, rule_index=None, triggered_directly=True, is_post_phase=ipp, character_name=character_name_for_rule_context, original_sequential_context=seq_ctx)
            )
        else:
            triggered_next_rule_id = None
    if tab_data:
        if tab_data.get('_characters_to_exit_rules_after_current'):
            if '_characters_to_exit_rules' not in tab_data:
                tab_data['_characters_to_exit_rules'] = set()
            tab_data['_characters_to_exit_rules'].update(tab_data['_characters_to_exit_rules_after_current'])
            tab_data.pop('_characters_to_exit_rules_after_current', None)
        if tab_data.get('_narrator_to_exit_rules_after_current'):
            tab_data['_narrator_to_exit_rules'] = True
            tab_data.pop('_narrator_to_exit_rules_after_current', None)
    if not triggered_next_rule_id and not (rewrite_instructions is not None and rewrite_buffer_content is not None and is_post_phase):
        is_char_post_phase_rule = is_post_phase and rule.get('applies_to') == 'Character'
        if not triggered_directly and rule_index is not None and not is_char_post_phase_rule:
             if tab_data and tab_data.get('_exit_rule_processing'):
                 print("  Not continuing sequential rule processing due to 'Exit Rule Processing' action")
                 tab_data.pop('_exit_rule_processing', None)
                 if hasattr(self, '_cot_next_step') and self._cot_next_step:
                     QTimer.singleShot(0, self._cot_next_step)
                     self._cot_next_step = None
                 return None
             self._cot_sequential_index += 1
             from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
             callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
             QTimer.singleShot(0, lambda rules_arg=rules: callback(self, current_user_msg, prev_assistant_msg, rules_arg))
        elif triggered_directly:
            if tab_data:
                if tab_data.get('_characters_to_exit_rules_after_current'):
                    if '_characters_to_exit_rules' not in tab_data:
                        tab_data['_characters_to_exit_rules'] = set()
                    tab_data['_characters_to_exit_rules'].update(tab_data['_characters_to_exit_rules_after_current'])
                    tab_data.pop('_characters_to_exit_rules_after_current', None)
                if tab_data.get('_narrator_to_exit_rules_after_current'):
                    tab_data['_narrator_to_exit_rules'] = True
                    tab_data.pop('_narrator_to_exit_rules_after_current', None)
            original_context = getattr(self, '_original_sequential_context', None)
            if original_context:
                self._original_sequential_context = None
                self._cot_sequential_index = original_context['sequential_index']
                if (original_context['sequential_index'] < len(original_context['rules']) and 
                    original_context['rules'][original_context['sequential_index']].get('id') == rule_id):
                    self._cot_sequential_index += 1
                from rules.rule_evaluator import _process_next_sequential_rule_post, _process_next_sequential_rule_pre
                callback = _process_next_sequential_rule_post if original_context['is_post_phase'] else _process_next_sequential_rule_pre
                QTimer.singleShot(0, lambda: callback(self, original_context['current_user_msg'], original_context['prev_assistant_msg'], original_context['rules']))
            else:
                if hasattr(self, '_cot_next_step') and self._cot_next_step:
                    QTimer.singleShot(0, self._cot_next_step)
                    self._cot_next_step = None
                else:
                    pass
    if (hasattr(self, '_character_llm_reply_rule_complete_callback') and 
        self._character_llm_reply_rule_complete_callback and
        rule.get('applies_to') == 'Character' and 
        character_name_for_rule_context):
        if tab_data:
            if tab_data.get('_characters_to_exit_rules_after_current'):
                if '_characters_to_exit_rules' not in tab_data:
                    tab_data['_characters_to_exit_rules'] = set()
                tab_data['_characters_to_exit_rules'].update(tab_data['_characters_to_exit_rules_after_current'])
                tab_data.pop('_characters_to_exit_rules_after_current', None)
            if tab_data.get('_narrator_to_exit_rules_after_current'):
                tab_data['_narrator_to_exit_rules'] = True
                tab_data.pop('_narrator_to_exit_rules_after_current', None)
        callback = self._character_llm_reply_rule_complete_callback
        QTimer.singleShot(0, callback)
        return npc_text_tag_for_character_rule
    return None

def _perform_change_actor_location(self, tab_data, actor_string, mode, target_setting_name, rule_trigger_context=None, advance_time=True):
    if not tab_data:
        return False
    if '_BLOCK_ALL_NPC_INFERENCE_AFTER_FORCED_NARRATOR_LAST' in tab_data:
        tab_data.pop('_BLOCK_ALL_NPC_INFERENCE_AFTER_FORCED_NARRATOR_LAST', None)
    if '_HARD_SUPPRESS_ALL_EXCEPT' in tab_data:
        tab_data.pop('_HARD_SUPPRESS_ALL_EXCEPT', None)
    workflow_data_dir = tab_data.get('workflow_data_dir')
    if not workflow_data_dir:
        return False
    player_name = _get_player_character_name(self, workflow_data_dir)
    current_player_setting = _get_player_current_setting_name(workflow_data_dir)
    actors_to_move = []
    raw_actor_names = [name.strip() for name in actor_string.split(',') if name.strip()]
    is_player_in_move_list = False
    for name in raw_actor_names:
        if name.lower() == 'player' and player_name:
            if player_name not in actors_to_move:
                actors_to_move.append(player_name)
            is_player_in_move_list = True
        elif name and name not in actors_to_move:
            actors_to_move.append(name)
    if is_player_in_move_list and mode == 'Setting':
        sanitized_target_setting = target_setting_name.lower().replace(" ", "_")
        sanitized_current_setting = current_player_setting.lower().replace(" ", "_")
        if sanitized_target_setting == sanitized_current_setting:
            return False
    if not actors_to_move:
        return False
    if mode == 'Setting':
        result = move_characters(
            workflow_data_dir=workflow_data_dir,
            actors_to_move=actors_to_move,
            target_setting_name=target_setting_name,
            player_name=player_name,
            tab_data=tab_data,
            advance_time=advance_time
        )
        if result.get('success'):
            if result.get('tab_data_updates'):
                updates = result['tab_data_updates']
                if 'allow_narrator_post_after_change' in updates:
                    tab_data['allow_narrator_post_after_change'] = updates['allow_narrator_post_after_change']
                if 'turn_count' in updates:
                    tab_data['turn_count'] = updates['turn_count']
                if updates.get('scene_number_increment'):
                    if 'scene_number' in tab_data and isinstance(tab_data['scene_number'], int):
                        tab_data['scene_number'] += 1
                        tab_data['_has_narrator_posted_this_scene'] = False
                    else:
                        tab_data['scene_number'] = 1
                        tab_data['_has_narrator_posted_this_scene'] = False
                    tab_data['pending_scene_update'] = True
            if result.get('process_scene_change_timers') and hasattr(self, 'timer_manager'):
                self.timer_manager.process_scene_change(tab_data)
            if result.get('player_moved'):
                self._pending_update_top_splitter = tab_data
            return True
        elif result.get('error'):
            return False
        else:
            return False
    elif mode == 'Adjacent':
        result = move_characters(
            workflow_data_dir=workflow_data_dir,
            actors_to_move=actors_to_move,
            target_setting_name=target_setting_name,
            player_name=player_name,
            mode='Adjacent',
            context_for_move=rule_trigger_context,
            tab_data=tab_data,
            advance_time=advance_time
        )
        if result.get('success'):
            if result.get('tab_data_updates'):
                updates = result['tab_data_updates']
                if 'allow_narrator_post_after_change' in updates:
                    tab_data['allow_narrator_post_after_change'] = updates['allow_narrator_post_after_change']
                if 'turn_count' in updates:
                    tab_data['turn_count'] = updates['turn_count']
                if updates.get('scene_number_increment'):
                    if 'scene_number' in tab_data and isinstance(tab_data['scene_number'], int):
                        tab_data['scene_number'] += 1
                        tab_data['_has_narrator_posted_this_scene'] = False
                    else:
                        tab_data['scene_number'] = 1
                        tab_data['_has_narrator_posted_this_scene'] = False
                    tab_data['pending_scene_update'] = True
            if result.get('process_scene_change_timers') and hasattr(self, 'timer_manager'):
                self.timer_manager.process_scene_change(tab_data)
            if result.get('player_moved'):
                self._pending_update_top_splitter = tab_data
            return True
        elif result.get('error'):
            return False
        else:
            return False
    elif mode == 'Fast Travel':
        return False
    else:
        return False

def _apply_rule_action(self, rule, user_msg, assistant_msg, character_name=None):
    action_obj = rule
    if action_obj.get('type') == 'Change Actor Location':
        location_mode = action_obj.get('location_mode')
        actor_string = action_obj.get('actor_name', '')
        target_setting = action_obj.get('target_setting', '')
        advance_time = action_obj.get('advance_time', True)
        current_tab_index = self.tab_widget.currentIndex()
        if not actor_string.strip() and rule.get('applies_to') == 'Character' and character_name:
            actor_string = character_name
        if 0 <= current_tab_index < len(self.tabs_data):
            tab_data = self.tabs_data[current_tab_index]
            rule_trigger_context = None
            if location_mode and location_mode != 'Setting':
                rule_trigger_context = user_msg
            if location_mode == 'Setting':
                return _perform_change_actor_location(self, tab_data, actor_string, 'Setting', target_setting, advance_time=advance_time)
            else:
                return _perform_change_actor_location(self, tab_data, actor_string, location_mode, target_setting, rule_trigger_context=rule_trigger_context, advance_time=advance_time)
        else:
            return False
    elif action_obj.get('type') == 'Set Var':
         pass
    return True

def _retry_rule_with_fallback(self, rule, rule_id, rule_index, current_user_msg, prev_assistant_msg, rules_list, fallback_model, tried_fallback1=False, tried_fallback2=False, tried_fallback3=False, is_post_phase=False, triggered_directly=False, character_name_for_rule_context=None):
    from chatBotRPG import InferenceThread
    tab_data = self.get_current_tab_data()
    if not tab_data:
        return
    tag_action_pairs = rule.get('tag_action_pairs', [])
    condition_raw = rule.get('condition', '').strip()
    actor_for_condition_substitution = character_name_for_rule_context
    condition = self._substitute_variables_in_string(condition_raw, tab_data, actor_for_condition_substitution)
    tags = []
    for pair in tag_action_pairs:
        tag = pair.get('tag', '').strip()
        if tag:
            tags.append(tag)
    if not tags:
        return
    tags_for_prompt = ", ".join([f"[{t}]" for t in tags])
    scope = rule.get('scope', 'user_message')
    player_name = _get_player_character_name(self, tab_data.get('workflow_data_dir'))
    prepared_condition_text = _prepare_condition_text(self, condition, player_name, 
                                                     character_name_for_rule_context, 
                                                     tab_data, scope, 
                                                     current_user_msg, prev_assistant_msg)
    
    if not any(f"[{tag.lower()}]" in condition.lower() for tag in tags) and "choose" not in condition.lower():
        prepared_condition_text += f"\nChoose ONLY one of these responses: {tags_for_prompt}"
    cot_context = [
        {"role": "system", "content": f"You are analyzing text based on a specific instruction. Respond ONLY with one of the provided choices, based on the text and the instruction. - Respond with only the chosen tag in square brackets (e.g., [TAG_NAME]) - "},
        {"role": "user", "content": prepared_condition_text}
    ]
    def on_fallback_inference_complete(result):
        self._handle_rule_result(
            result, rule, rule_index,
            current_user_msg, prev_assistant_msg, rules_list,
            tried_fallback1=tried_fallback1, tried_fallback2=tried_fallback2, tried_fallback3=tried_fallback3,
            is_post_phase=is_post_phase, triggered_directly=triggered_directly,
            character_name_for_rule_context=character_name_for_rule_context
        )
    def on_fallback_inference_error(error):
        self._handle_rule_error(
            error, rule, rule_index,
            current_user_msg, prev_assistant_msg, rules_list,
            triggered_directly=triggered_directly, is_post_phase=is_post_phase,
            tried_fallback1=tried_fallback1, tried_fallback2=tried_fallback2, tried_fallback3=tried_fallback3,
            character_name_for_rule_context=character_name_for_rule_context
        )
    self.utility_inference_thread = InferenceThread(
        cot_context, self.character_name, fallback_model, 100, 0.1, is_utility_call=True
    )
    self.utility_inference_thread.result_signal.connect(on_fallback_inference_complete)
    self.utility_inference_thread.error_signal.connect(on_fallback_inference_error)
    self.utility_inference_thread.start()


def _find_generator_file(generator_name, workflow_data_dir):
    if not generator_name or not workflow_data_dir:
        return None
    def find_file_case_insensitive(directory, target_filename):
        if not os.path.isdir(directory):
            return None
        exact_path = os.path.join(directory, target_filename)
        if os.path.isfile(exact_path):
            return exact_path
        target_lower = target_filename.lower()
        for filename in os.listdir(directory):
            if filename.lower() == target_lower:
                return os.path.join(directory, filename)
        return None
    target_filename = f"{generator_name}.json"
    game_generators_dir = os.path.join(workflow_data_dir, 'game', 'generators')
    if os.path.exists(game_generators_dir):
        found_file = find_file_case_insensitive(game_generators_dir, target_filename)
        if found_file:
            return found_file
    resources_generators_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'generators')
    if os.path.exists(resources_generators_dir):
        found_file = find_file_case_insensitive(resources_generators_dir, target_filename)
        if found_file:
            return found_file
    alt_resources_generators_dir = os.path.join(workflow_data_dir, 'resources', 'generators')
    if os.path.exists(alt_resources_generators_dir):
        found_file = find_file_case_insensitive(alt_resources_generators_dir, target_filename)
        if found_file:
            return found_file
    return None

def _apply_string_operation_mode(self, value, var_value, operation_mode, delimiter):
    is_number_type = False
    original_number_type = None
    if isinstance(var_value, (int, float)):
        is_number_type = True
        original_number_type = type(var_value)
    if is_number_type and isinstance(value, (int, float)):
        return value
    str_value = str(value)
    str_var_value = str(var_value)
    if operation_mode == "prepend":
        if str_var_value:
            result = str_value + delimiter + str_var_value
        else:
            result = str_value
    elif operation_mode == "append":
        if str_var_value:
            result = str_var_value + delimiter + str_value
        else:
            result = str_value
    else:
        result = str_value
    if is_number_type:
        try:
            if original_number_type == int:
                return int(float(result))
            elif original_number_type == float:
                return float(result)
        except (ValueError, TypeError):
            pass
    return result
