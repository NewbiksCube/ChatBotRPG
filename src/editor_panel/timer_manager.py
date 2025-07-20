import os
import json
import random
import time
import threading
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont
from core.standalone_character_inference import run_single_character_post

class TimerInstance:
    def __init__(self, rule_data, character=None, tab_data=None):
        self.rule_id = rule_data.get('id')
        self.rule_data = rule_data
        self.character = character
        self.tab_data = tab_data
        self.is_running = False
        self.interval_ms = self._calculate_interval_ms()
        self.start_time = None
        self.next_fire_time = None

    def _calculate_interval_ms(self):
        interval_ms = 60000
        
        # Check if this timer uses game time instead of real time
        use_game_time = self._should_use_game_time()
        
        if use_game_time:
            # Calculate game time interval
            game_seconds = self._calculate_game_time_interval()
            if game_seconds > 0:
                # Convert game time to real time based on time multiplier
                time_multiplier = self._get_time_multiplier()
                real_seconds = game_seconds / time_multiplier if time_multiplier > 0 else game_seconds
                interval_ms = int(real_seconds * 1000)
                print(f"[TIMER] Game time interval: {game_seconds}s game time = {real_seconds}s real time (multiplier: {time_multiplier})")
        else:
            # Use real time interval (original logic)
            if self.rule_data.get('interval_is_random', False):
                min_interval = self.rule_data.get('interval_min', 5)
                max_interval = self.rule_data.get('interval_max', 60)
                interval_seconds = random.randint(min_interval, max_interval)
                interval_ms = interval_seconds * 1000
            else:
                interval_seconds = self.rule_data.get('interval', 60)
                interval_ms = interval_seconds * 1000
        
        return interval_ms
    
    def _should_use_game_time(self):
        """Check if this timer should use game time instead of real time"""
        # Check the time_mode field first
        time_mode = self.rule_data.get('time_mode', 'real_time')
        if time_mode == 'game_time':
            return True
        
        # Fallback: Check if any game time fields are set (for backward compatibility)
        game_seconds = self.rule_data.get('game_seconds', 0)
        game_minutes = self.rule_data.get('game_minutes', 0)
        game_hours = self.rule_data.get('game_hours', 0)
        game_days = self.rule_data.get('game_days', 0)
        
        # If any game time field is non-zero, use game time
        return game_seconds > 0 or game_minutes > 0 or game_hours > 0 or game_days > 0
    
    def _calculate_game_time_interval(self):
        """Calculate the total game time interval in seconds"""
        total_seconds = 0
        
        # Add game seconds
        if self.rule_data.get('game_seconds_is_random', False):
            min_seconds = self.rule_data.get('game_seconds_min', 0)
            max_seconds = self.rule_data.get('game_seconds_max', 59)
            total_seconds += random.randint(min_seconds, max_seconds)
        else:
            total_seconds += self.rule_data.get('game_seconds', 0)
        
        # Add game minutes
        if self.rule_data.get('game_minutes_is_random', False):
            min_minutes = self.rule_data.get('game_minutes_min', 0)
            max_minutes = self.rule_data.get('game_minutes_max', 59)
            total_seconds += random.randint(min_minutes, max_minutes) * 60
        else:
            total_seconds += self.rule_data.get('game_minutes', 0) * 60
        
        # Add game hours
        if self.rule_data.get('game_hours_is_random', False):
            min_hours = self.rule_data.get('game_hours_min', 0)
            max_hours = self.rule_data.get('game_hours_max', 23)
            total_seconds += random.randint(min_hours, max_hours) * 3600
        else:
            total_seconds += self.rule_data.get('game_hours', 0) * 3600
        
        # Add game days
        if self.rule_data.get('game_days_is_random', False):
            min_days = self.rule_data.get('game_days_min', 0)
            max_days = self.rule_data.get('game_days_max', 365)
            total_seconds += random.randint(min_days, max_days) * 86400
        else:
            total_seconds += self.rule_data.get('game_days', 0) * 86400
        
        return total_seconds
    
    def _get_time_multiplier(self):
        """Get the current time multiplier from the time manager"""
        if not self.tab_data:
            return 1.0
        
        time_manager_widget = self.tab_data.get('time_manager_widget')
        if not time_manager_widget:
            return 1.0
        
        # Try to get the time multiplier from the time manager
        try:
            # Load the time passage configuration
            workflow_data_dir = self.tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                return 1.0
            
            time_passage_file = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings', 'time_passage.json')
            if os.path.exists(time_passage_file):
                with open(time_passage_file, 'r', encoding='utf-8') as f:
                    time_config = json.load(f)
                    return time_config.get('time_multiplier', 1.0)
        except Exception as e:
            print(f"[TIMER] Error getting time multiplier: {e}")
        
        return 1.0

    def start(self):
        self.is_running = True
        self.start_time = datetime.now()
        if not hasattr(self, 'interval_ms') or self.interval_ms is None:
            self.interval_ms = self._calculate_interval_ms()
        self.next_fire_time = self.start_time + timedelta(milliseconds=self.interval_ms)

    def stop(self):
        self.is_running = False

    def recalculate_interval(self):
        self.interval_ms = self._calculate_interval_ms()
        if self.is_running:
            self.next_fire_time = datetime.now() + timedelta(milliseconds=self.interval_ms)

    def time_remaining_ms(self):
        if not self.is_running or not self.next_fire_time:
            return 0
        now = datetime.now()
        if now >= self.next_fire_time:
            return 0
        delta = self.next_fire_time - now
        remaining_ms = int(delta.total_seconds() * 1000)
        return remaining_ms

    def is_expired(self):
        if not self.is_running or not self.next_fire_time:
            return False
        now = datetime.now()
        expired = now >= self.next_fire_time
        return expired

class TimerManager(QObject):
    timer_action_signal = pyqtSignal(object, object, object)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_timers = {}
        self.lock = threading.RLock()
        self.main_timer = QTimer(self)
        self.main_timer.timeout.connect(self._check_timers)
        self.main_timer.start(1000)  # Check every second
        self._creating_timers = set()  # Track timers currently being created to prevent duplicates
        self._timers_paused = False  # Track if timers are paused during NPC processing

    def pause_timers(self):
        """Pause all timer firing during NPC processing"""
        with self.lock:
            self._timers_paused = True
            print("[TIMER PAUSE] Timers paused during NPC processing")

    def resume_timers(self):
        """Resume timer firing after NPC processing completes"""
        with self.lock:
            self._timers_paused = False
            print("[TIMER RESUME] Timers resumed after NPC processing")

    def _evaluate_variable_condition(self, condition, tab_data, character_name=None):
        if not condition:
            return False
        var_name = condition.get('name', '')
        if not var_name:
            return False
        operator = condition.get('operator', '==')
        value = condition.get('value', '')
        scope = condition.get('scope', 'Global')
        
        # Apply variable substitution to the condition value if it's a string
        if isinstance(value, str) and hasattr(self.parent(), '_substitute_variables_in_string'):
            value = self.parent()._substitute_variables_in_string(value, tab_data, character_name)
        
        print(f"[TIMER DEBUG] Evaluating condition: {var_name} {operator} {value} (scope: {scope}, character: {character_name})")
        
        var_value = None
        if scope == 'Character':
            if not character_name:
                return False
            workflow_dir = tab_data.get('workflow_data_dir')
            if not workflow_dir:
                return False
            try:
                from core.utils import _get_or_create_actor_data
                actor_data, _ = _get_or_create_actor_data(self.parent(), workflow_dir, character_name)
                if actor_data and 'variables' in actor_data:
                    var_value = actor_data['variables'].get(var_name)
                    print(f"[TIMER DEBUG] Character variable '{var_name}' = {var_value} for {character_name}")
                else:
                    print(f"[TIMER DEBUG] No character variables found for {character_name}")
                    return False
            except Exception:
                return False
        elif scope == 'Setting':
            workflow_dir = tab_data.get('workflow_data_dir')
            if not workflow_dir:
                return False
            try:
                from core.utils import _get_player_current_setting_name, _find_setting_file_by_name
                setting_name = _get_player_current_setting_name(workflow_dir)
                if not setting_name:
                    return False
                session_settings_dir = os.path.join(workflow_dir, 'game', 'settings')
                setting_file = _find_setting_file_by_name(session_settings_dir, setting_name)
                if setting_file:
                    with open(setting_file, 'r', encoding='utf-8') as f:
                        setting_data = json.load(f)
                    if 'variables' in setting_data:
                        var_value = setting_data['variables'].get(var_name)
                    else:
                        return False
                else:
                    return False
            except Exception:
                return False
        else:
            try:
                main_ui = self.parent()
                tab_index = main_ui.tabs_data.index(tab_data) if tab_data in main_ui.tabs_data else -1
                if tab_index >= 0:
                    variables = main_ui._load_variables(tab_index)
                    var_value = variables.get(var_name)
                    print(f"[TIMER DEBUG] Global variable '{var_name}' = {var_value}")
                else:
                    return False
            except Exception:
                return False
        if operator == "exists":
            result = var_value is not None
        elif operator == "not exists":
            result = var_value is None
        elif var_value is None:
            if operator == "!=":
                result = True
            else:
                result = False
        else:
            try:
                # First try to handle as numeric comparison if both values can be converted to numbers
                try:
                    var_num = float(var_value) if var_value is not None else 0
                    val_num = float(value) if value is not None else 0
                    result = self._compare_numeric(var_num, val_num, operator)
                except (ValueError, TypeError):
                    # If numeric conversion fails, fall back to string comparison
                    var_str = str(var_value).lower() if var_value is not None else ""
                    val_str = str(value).lower() if value is not None else ""
                    if operator == "==":
                        result = var_str == val_str
                    elif operator == "!=":
                        result = var_str != val_str
                    elif operator == "contains":
                        result = val_str in var_str
                    elif operator == "not contains":
                        result = val_str not in var_str
                    elif operator in [">", "<", ">=", "<="]:
                        # For comparison operators, try to convert to numbers again
                        try:
                            var_num = float(var_value) if var_value is not None else 0
                            val_num = float(value) if value is not None else 0
                            result = self._compare_numeric(var_num, val_num, operator)
                        except (ValueError, TypeError):
                            result = False
                    else:
                        result = False
            except (ValueError, TypeError, AttributeError):
                var_str = str(var_value).lower() if var_value is not None else ""
                val_str = str(value).lower() if value is not None else ""
                if operator == "==":
                    result = var_str == val_str
                elif operator == "!=":
                    result = var_str != val_str
                elif operator == "contains":
                    result = val_str in var_str
                elif operator == "not contains":
                    result = val_str not in var_str
                else:
                    result = False
        return result

    def _compare_numeric(self, a, b, operator):
        if operator == "==":
            return a == b
        elif operator == "!=":
            return a != b
        elif operator == ">":
            return a > b
        elif operator == "<":
            return a < b
        elif operator == ">=":
            return a >= b
        elif operator == "<=":
            return a <= b
        return False
    
    def _evaluate_game_time_condition(self, condition, tab_data):
        """Evaluate Game Time conditions for timer rules using cyclical time"""
        if not condition or condition.get('type') != 'Game Time':
            return False
        
        operator = condition.get('operator', 'Before')
        time_type = condition.get('time_type', 'Minute')
        target_value = condition.get('value', 0)
        
        # Get current game datetime from variables
        try:
            main_ui = self.parent()
            tab_index = main_ui.tabs_data.index(tab_data) if tab_data in main_ui.tabs_data else -1
            if tab_index < 0:
                print(f"[TIMER DEBUG] Could not find tab index for Game Time condition")
                return False
            
            variables = main_ui._load_variables(tab_index)
            current_datetime_str = variables.get('datetime')
            
            if not current_datetime_str:
                print(f"[TIMER DEBUG] No game datetime found in variables")
                return False
                
            current_datetime = datetime.fromisoformat(current_datetime_str)
            
            # Extract cyclical time component based on time_type
            if time_type == 'Second':
                current_value = current_datetime.second
            elif time_type == 'Minute':
                current_value = current_datetime.minute
            elif time_type == 'Hour':
                current_value = current_datetime.hour
            elif time_type == 'Date':
                current_value = current_datetime.day
            elif time_type == 'Month':
                current_value = current_datetime.month
            elif time_type == 'Year':
                current_value = current_datetime.year
            else:
                print(f"[TIMER DEBUG] Unknown time type '{time_type}' for Game Time condition")
                return False
            
            print(f"[TIMER DEBUG] Game Time condition: {operator} {target_value} {time_type} (current: {current_value}, target: {target_value})")
            
            # Evaluate the condition using cyclical time
            if operator == 'Before':
                result = current_value < target_value
            elif operator == 'After':
                result = current_value > target_value
            elif operator == 'At':
                result = current_value == target_value
            else:
                print(f"[TIMER DEBUG] Unknown Game Time operator: {operator}")
                return False
                
            print(f"[TIMER DEBUG] Game Time condition result: {result}")
            return result
                
        except (ValueError, TypeError) as e:
            print(f"[TIMER DEBUG] Error parsing game datetime '{current_datetime_str}': {e}")
            return False
        except Exception as e:
            print(f"[TIMER DEBUG] Error evaluating Game Time condition: {e}")
            return False
    

        
    def _evaluate_rule_conditions(self, rule, tab_data, character_name=None):
        condition_type = rule.get('condition_type', 'Always')
        if condition_type == 'Always':
            return True
        elif condition_type == 'Variable':
            condition_details = rule.get('condition_details', [])
            if not condition_details:
                return False
            final_result_log = None
            condition_operator_log = rule.get('condition_operator', 'AND')
            for i, condition in enumerate(condition_details):
                logic_op_to_previous_log = condition.get('logic_to_previous', 'AND')
                
                # Check if this is a Game Time condition
                if condition.get('type') == 'Game Time':
                    cond_result_log = self._evaluate_game_time_condition(condition, tab_data)
                else:
                    cond_result_log = self._evaluate_variable_condition(condition, tab_data, character_name)
                
                if final_result_log is None:
                    final_result_log = cond_result_log
                elif logic_op_to_previous_log == 'AND':
                    final_result_log = final_result_log and cond_result_log
                elif logic_op_to_previous_log == 'OR':
                    final_result_log = final_result_log or cond_result_log
                else:
                    final_result_log = final_result_log and cond_result_log
                if condition_operator_log == 'AND' and final_result_log is False:
                    return False
            final_eval_outcome = final_result_log if final_result_log is not None else False
            return final_eval_outcome
        return False

    def process_post_events(self, is_player_post, character_name=None, tab_data=None):
        if not tab_data:
            return
        tab_id = tab_data.get('id')
        if not tab_id:
            try:
                main_ui = self.parent()
                if main_ui and hasattr(main_ui, 'tabs_data'):
                    if tab_data in main_ui.tabs_data:
                        tab_id = main_ui.tabs_data.index(tab_data)
                    else:
                        tab_id = "unknown_tab"
                else:
                    tab_id = "unknown_tab"
            except Exception as e:
                tab_id = "unknown_tab"
            tab_data['id'] = tab_id
        tab_id = str(tab_id)
        timer_rules = tab_data.get('timer_rules', [])
        if not timer_rules:
            timer_rules_widget = tab_data.get('timer_rules_widget')
            if timer_rules_widget:
                timer_rules = timer_rules_widget.get_timer_rules()
        if not timer_rules:
            return
        for rule in timer_rules:
            pass
        self._process_timer_rules(timer_rules, is_player_post, character_name, tab_data, tab_id)

    def check_for_newly_enabled_timers(self, tab_data, character_name=None):
        if not tab_data:
            return
        tab_id = tab_data.get('id')
        if not tab_id:
            try:
                main_ui = self.parent()
                if main_ui and hasattr(main_ui, 'tabs_data'):
                    if tab_data in main_ui.tabs_data:
                        tab_id = main_ui.tabs_data.index(tab_data)
                    else:
                        tab_id = "unknown_tab"
                else:
                    tab_id = "unknown_tab"
            except Exception as e:
                tab_id = "unknown_tab"
            tab_data['id'] = tab_id
        timer_rules = tab_data.get('timer_rules', [])
        if not timer_rules:
            timer_rules_widget = tab_data.get('timer_rules_widget')
            if timer_rules_widget:
                timer_rules = timer_rules_widget.get_timer_rules()
        if not timer_rules:
            return
        self._process_timer_rules(timer_rules, None, character_name, tab_data, tab_id, check_newly_enabled=True)

    def _process_timer_rules(self, timer_rules, is_player_post, character_name, tab_data, tab_id, check_newly_enabled=False):
        tab_id = str(tab_id)
        with self.lock:
            for rule in timer_rules:
                rule_id = rule.get('id')
                if not rule_id:
                    continue
                if not rule.get('enabled', True):
                    continue
                trigger_met = True
                if not check_newly_enabled:
                    trigger_met = False
                    start_after_trigger = rule.get('start_after_trigger') or rule.get('start_trigger', 'Player')
                    if start_after_trigger == 'Player' and is_player_post:
                        trigger_met = True
                    elif start_after_trigger == 'Character' and is_player_post == False:
                        trigger_met = True
                if not trigger_met:
                    continue
                final_rule_scope = rule.get('rule_scope') or rule.get('scope', 'Global')
                potential_target_characters = []
                if final_rule_scope == 'Global':
                    potential_target_characters = ['global']
                elif final_rule_scope == 'Character':
                    if character_name:
                        potential_target_characters = [character_name]
                    else:
                        continue
                if not potential_target_characters:
                    continue
                passed_condition_targets = []
                if final_rule_scope == 'Global':
                    # Check if this global timer has character-scoped conditions
                    condition_details = rule.get('condition_details', [])
                    has_character_conditions = any(cond.get('scope') == 'Character' for cond in condition_details)
                    is_recurring = rule.get('recurring', False)
                    
                    if has_character_conditions:
                        if hasattr(self.parent(), 'get_character_names_in_scene_for_timers'):
                            characters_in_scene = self.parent().get_character_names_in_scene_for_timers(tab_data)
                            for char_name in characters_in_scene:
                                if is_recurring:
                                    passed_condition_targets.append(char_name)
                                else:
                                    conditions_met_char = self._evaluate_rule_conditions(rule, tab_data, char_name)
                                    if conditions_met_char:
                                        passed_condition_targets.append(char_name)
                    else:
                        if 'global' in potential_target_characters:
                            if is_recurring:
                                passed_condition_targets.append('global')
                            else:
                                conditions_met_global = self._evaluate_rule_conditions(rule, tab_data, None)
                                if conditions_met_global:
                                    passed_condition_targets.append('global')
                elif final_rule_scope == 'Character':
                    for target_char in potential_target_characters:
                        if not target_char or target_char == 'global':
                            continue
                        is_recurring = rule.get('recurring', False)
                        if is_recurring:
                            passed_condition_targets.append(target_char)
                        else:
                            conditions_met_char = self._evaluate_rule_conditions(rule, tab_data, target_char)
                            if conditions_met_char:
                                passed_condition_targets.append(target_char)
                if not passed_condition_targets:
                    continue
                if tab_id not in self.active_timers:
                    self.active_timers[tab_id] = {}
                if rule_id not in self.active_timers[tab_id]:
                    self.active_timers[tab_id][rule_id] = {}
                for target in passed_condition_targets:
                    timer_instance_character_binding = None if target == 'global' else target
                    actual_timer_key_for_dict = target
                    
                    # For character-specific timers created from global rules, use character name as key
                    if target != 'global' and final_rule_scope == 'Global':
                        actual_timer_key_for_dict = f"global_{target}"
                    
                    # Create a unique identifier for this timer to prevent duplicates
                    timer_creation_id = f"{tab_id}:{rule_id}:{actual_timer_key_for_dict}"
                    
                    # Check if we're already creating this timer
                    if timer_creation_id in self._creating_timers:
                        continue
                    
                    existing_timer = self.active_timers[tab_id][rule_id].get(actual_timer_key_for_dict)
                    if not existing_timer:
                        # Double-check that we don't already have a timer for this exact combination
                        # This prevents race conditions where multiple timers could be created
                        if actual_timer_key_for_dict not in self.active_timers[tab_id][rule_id]:
                            # Mark this timer as being created
                            self._creating_timers.add(timer_creation_id)
                            try:
                                new_timer = TimerInstance(rule, timer_instance_character_binding, tab_data)
                                self.active_timers[tab_id][rule_id][actual_timer_key_for_dict] = new_timer
                                new_timer.start()
                                self.save_timer_state(tab_data)
                            finally:
                                # Always remove from creating set
                                self._creating_timers.discard(timer_creation_id)
                        else:
                            pass
                    else:
                        existing_timer.rule_data = rule
                        existing_timer.character = timer_instance_character_binding
                        existing_timer.stop()
                        existing_timer.recalculate_interval()
                        existing_timer.start()
                        self.save_timer_state(tab_data)

    def process_player_post(self, tab_data):
        self.process_post_events(is_player_post=True, tab_data=tab_data)

    def process_scene_change(self, tab_data):
        if not tab_data:
            return
        tab_id = tab_data.get('id')
        if not tab_id:
            try:
                main_ui = self.parent()
                if main_ui and hasattr(main_ui, 'tabs_data'):
                    if tab_data in main_ui.tabs_data:
                        tab_id = main_ui.tabs_data.index(tab_data)
                    else:
                        tab_id = "unknown_tab"
                else:
                    tab_id = "unknown_tab"
            except Exception:
                tab_id = "unknown_tab"
            tab_data['id'] = tab_id
        
        # Terminate character-specific timers when scene changes
        # since those characters are no longer in the scene
        tab_id_str = str(tab_id)
        terminated_count = 0
        with self.lock:
            if tab_id_str in self.active_timers:
                rules_to_remove = []
                for rule_id, timers_dict in self.active_timers[tab_id_str].items():
                    timers_to_remove = []
                    for timer_key, timer_instance in timers_dict.items():
                        # Check if this is a character-specific timer or a recurring timer
                        rule_data = timer_instance.rule_data
                        rule_scope = rule_data.get('rule_scope') or rule_data.get('scope', 'Global')
                        has_character_binding = timer_instance.character is not None
                        is_character_timer = rule_scope == 'Character' or has_character_binding
                        is_recurring_timer = rule_data.get('recurring', False)
                        is_global_timer = rule_data.get('global', False)
                        
                        # Don't terminate global timers on scene change
                        if is_global_timer:
                            print(f"[SCENE CHANGE] Keeping global timer for rule '{rule_id}', character: '{timer_instance.character}'")
                            continue
                        
                        if is_character_timer or is_recurring_timer:
                            timer_type = "character" if is_character_timer else "recurring"
                            print(f"[SCENE CHANGE] Terminating {timer_type} timer for rule '{rule_id}', character: '{timer_instance.character}'")
                            timer_instance.stop()
                            timers_to_remove.append(timer_key)
                            terminated_count += 1
                    
                    # Remove terminated character timers
                    for timer_key in timers_to_remove:
                        del timers_dict[timer_key]
                    
                    # If no timers left for this rule, mark rule for removal
                    if not timers_dict:
                        rules_to_remove.append(rule_id)
                
                # Remove empty rule entries
                for rule_id in rules_to_remove:
                    del self.active_timers[tab_id_str][rule_id]
                
                # If no rules left for this tab, remove tab entry
                if not self.active_timers[tab_id_str]:
                    del self.active_timers[tab_id_str]
        
        if terminated_count > 0:
            print(f"[SCENE CHANGE] Terminated {terminated_count} character-specific timers")
            self.save_timer_state(tab_data)
        timer_rules = tab_data.get('timer_rules', [])
        if not timer_rules:
            timer_rules_widget = tab_data.get('timer_rules_widget')
            if timer_rules_widget:
                timer_rules = timer_rules_widget.get_timer_rules()
        if not timer_rules:
            return
        with self.lock:
            for rule in timer_rules:
                rule_id = rule.get('id')
                if not rule_id:
                    continue
                is_enabled_from_rule = rule.get('enabled', True)
                if not is_enabled_from_rule:
                    continue
                raw_start_after_trigger = rule.get('start_after_trigger')
                raw_start_trigger = rule.get('start_trigger')
                start_after_trigger = raw_start_after_trigger or raw_start_trigger or 'Player'
                if start_after_trigger != 'Scene Change':
                    continue
                raw_rule_scope = rule.get('rule_scope')
                raw_scope = rule.get('scope')
                final_rule_scope = raw_rule_scope or raw_scope or 'Global'
                trigger_met = True
                potential_target_characters = []
                if final_rule_scope == 'Global':
                    potential_target_characters = ['global']
                elif final_rule_scope == 'Character':
                    main_ui = self.parent()
                    if main_ui and hasattr(main_ui, 'get_character_names_in_scene_for_timers') and tab_data:
                        npcs_in_scene = main_ui.get_character_names_in_scene_for_timers(tab_data)
                        potential_target_characters.extend(npcs_in_scene)
                    if not potential_target_characters:
                        continue
                passed_condition_targets = []
                if final_rule_scope == 'Global':
                    conditions_met_global = self._evaluate_rule_conditions(rule, tab_data, None)
                    if conditions_met_global:
                        passed_condition_targets.append('global')
                elif final_rule_scope == 'Character':
                    for target_char in potential_target_characters:
                        if not target_char or target_char == 'global':
                            continue
                        conditions_met_char = self._evaluate_rule_conditions(rule, tab_data, target_char)
                        if conditions_met_char:
                            passed_condition_targets.append(target_char)
                if not passed_condition_targets:
                    continue
                for final_target_key in passed_condition_targets:
                    if final_rule_scope == 'Character':
                        timer_instance_character_binding = final_target_key
                    else:
                        timer_instance_character_binding = None
                    actual_timer_key_for_dict = final_target_key
                    if tab_id not in self.active_timers:
                        self.active_timers[tab_id] = {}
                    if rule_id not in self.active_timers[tab_id]:
                        self.active_timers[tab_id][rule_id] = {}
                    existing_timer = self.active_timers[tab_id][rule_id].get(actual_timer_key_for_dict)
                    if not existing_timer:
                        new_timer = TimerInstance(rule, timer_instance_character_binding, tab_data)
                        self.active_timers[tab_id][rule_id][actual_timer_key_for_dict] = new_timer
                        new_timer.start()
                        self.save_timer_state(tab_data)
                    else:
                        existing_timer.rule_data = rule
                        existing_timer.character = timer_instance_character_binding
                        existing_timer.stop()
                        existing_timer.recalculate_interval()
                        existing_timer.start()
                        self.save_timer_state(tab_data)

    def _check_timers(self):
        if self._timers_paused:
            return  # Skip timer checks when paused
        
        expired_timers = []
        timers_to_stop = []
        current_time_for_check = datetime.now()
        with self.lock:
            for tab_id, rules_dict in self.active_timers.items():
                for rule_id, timers_dict in rules_dict.items():
                    for timer_key, timer in timers_dict.items():
                        if timer.is_running:
                            # Check if timer is already firing to prevent duplicates
                            if hasattr(timer, '_is_firing') and timer._is_firing:
                                print(f"[TIMER LOOP] Timer {rule_id} for {timer.character} is already firing, skipping")
                                continue
                            if timer.is_expired():
                                rule_data = timer.rule_data
                                tab_data = timer.tab_data
                                character_name = timer.character
                                conditions_still_met = self._evaluate_rule_conditions(rule_data, tab_data, character_name)
                                is_recurring = rule_data.get('recurring', False)
                                if conditions_still_met:
                                    timer._is_firing = True
                                    expired_timers.append((tab_id, rule_id, timer_key, timer))
                                else:
                                    if is_recurring:
                                        timer.recalculate_interval()
                                        timer.start()
                                        if tab_data:
                                            self.save_timer_state(tab_data)
                                    else:
                                        timers_to_stop.append((tab_id, rule_id, timer_key, timer))
                            else:
                                pass
            for tab_id, rule_id, timer_key, timer in timers_to_stop:
                timer.stop()
                if tab_id in self.active_timers and rule_id in self.active_timers[tab_id] and timer_key in self.active_timers[tab_id][rule_id]:
                    del self.active_timers[tab_id][rule_id][timer_key]
                    if not self.active_timers[tab_id][rule_id]:
                        del self.active_timers[tab_id][rule_id]
                    if not self.active_timers[tab_id]:
                        del self.active_timers[tab_id]
                    if timer.tab_data:
                        self.save_timer_state(timer.tab_data)

            for tab_id, rule_id, timer_key, timer in expired_timers:
                rule_data = timer.rule_data
                tab_data = timer.tab_data
                if tab_data:
                    if not rule_data.get('actions'):
                        timer._is_firing = False
                        continue
                else:
                    timer._is_firing = False
                    continue
                
                self.timer_action_signal.emit(timer, rule_data, tab_data)
                
                with self.lock:
                    if tab_id in self.active_timers and rule_id in self.active_timers[tab_id]:
                        for other_timer_key, other_timer in self.active_timers[tab_id][rule_id].items():
                            if other_timer_key != timer_key and other_timer.is_running:
                                other_timer.stop()
                                other_timer.recalculate_interval()
                                other_timer.start()
                        if tab_data:
                            self.save_timer_state(tab_data)
                
                conditions_still_met_after_firing = self._evaluate_rule_conditions(rule_data, tab_data, timer.character)
                is_recurring = rule_data.get('recurring', False)
                
                if conditions_still_met_after_firing or is_recurring:
                    timer.recalculate_interval()
                    timer.start()
                    if tab_data:
                        self.save_timer_state(tab_data)
                else:
                    timer.stop()
                    if tab_id in self.active_timers and rule_id in self.active_timers[tab_id] and timer_key in self.active_timers[tab_id][rule_id]:
                        del self.active_timers[tab_id][rule_id][timer_key]
                        if not self.active_timers[tab_id][rule_id]:
                            del self.active_timers[tab_id][rule_id]
                        if not self.active_timers[tab_id]:
                            del self.active_timers[tab_id]
                        if tab_data:
                            self.save_timer_state(tab_data)
                
                timer._is_firing = False
    
    def stop_all_timers(self):
        with self.lock:
            for tab_id, rules_dict in self.active_timers.items():
                for rule_id, timers_dict in rules_dict.items():
                    for timer_key, timer in timers_dict.items():
                        timer.stop()
            self.active_timers = {}

    def stop_timers_for_tab(self, tab_data):
        if not tab_data:
            return
        tab_id = tab_data.get('id')
        if not tab_id:
            try:
                main_ui = self.parent()
                if main_ui and hasattr(main_ui, 'tabs_data'):
                    if tab_data in main_ui.tabs_data:
                        tab_id = main_ui.tabs_data.index(tab_data)
                    else:
                        tab_id = "unknown_tab"
                else:
                    tab_id = "unknown_tab"
            except Exception:
                tab_id = "unknown_tab"
            tab_data['id'] = tab_id
        tab_id = str(tab_id)
        with self.lock:
            if tab_id in self.active_timers:
                for rule_id, timers_dict in self.active_timers[tab_id].items():
                    for timer_key, timer in timers_dict.items():
                        timer.stop()
                del self.active_timers[tab_id]
                self.save_timer_state(tab_data)

    def _execute_timer_actions_sequentially(self, rule_data, actions, index, character_name, tab_data):
        if index >= len(actions):
            return
        action = actions[index]
        action_type = action.get('type', 'unknown')
        try:
            execute_timer_action(self, rule_data, action, character_name, tab_data)
            delay_ms = 1500
            QTimer.singleShot(
                delay_ms, 
                lambda: self._execute_timer_actions_sequentially(rule_data, actions, index+1, character_name, tab_data)
            )
        except Exception as e:
            QTimer.singleShot(
                1000,
                lambda: self._execute_timer_actions_sequentially(rule_data, actions, index+1, character_name, tab_data)
            )

    def save_timer_state(self, tab_data):
        if not tab_data:
            return
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            return
        gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
        game_dir = os.path.dirname(gamestate_path)
        if not os.path.exists(game_dir):
            os.makedirs(game_dir)
        gamestate = {}
        if os.path.exists(gamestate_path):
            try:
                with open(gamestate_path, 'r', encoding='utf-8') as f:
                    gamestate = json.load(f)
            except Exception:
                pass
        if not isinstance(gamestate, dict):
            gamestate = {}
        tab_id = tab_data.get('id')
        if not tab_id:
            try:
                main_ui = self.parent()
                if main_ui and hasattr(main_ui, 'tabs_data'):
                    if tab_data in main_ui.tabs_data:
                        tab_id = main_ui.tabs_data.index(tab_data)
                    else:
                        tab_id = "unknown_tab"
            except Exception:
                tab_id = "unknown_tab"
        timer_state = []
        with self.lock:
            if tab_id in self.active_timers:
                for rule_id, timer_dict in self.active_timers[tab_id].items():
                    for timer_key, timer_instance in timer_dict.items():
                        if timer_instance.is_running:
                            try:
                                time_remaining = timer_instance.time_remaining_ms()
                                rule_data = timer_instance.rule_data
                                rule_scope = rule_data.get('rule_scope') or rule_data.get('scope', 'Global')
                                has_character_binding = timer_instance.character is not None
                                is_character_timer = rule_scope == 'Character' or has_character_binding
                                timer_data = {
                                    'rule_id': rule_id,
                                    'key': timer_key,
                                    'is_character': is_character_timer,
                                    'character': timer_instance.character,
                                    'time_remaining_ms': time_remaining,
                                    'interval_ms': timer_instance.interval_ms,
                                    'is_random': timer_instance.rule_data.get('interval_is_random', False)
                                }
                                timer_state.append(timer_data)
                            except Exception:
                                pass
        if 'timers' not in gamestate:
            gamestate['timers'] = {}
        gamestate['timers']['active_timers'] = timer_state
        gamestate['timers']['last_saved'] = datetime.now().isoformat()
        try:
            with open(gamestate_path, 'w', encoding='utf-8') as f:
                json.dump(gamestate, f, indent=2)
        except Exception:
            pass

    def load_timer_state(self, tab_data):
        if not tab_data:
            return
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            return
        gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
        if not os.path.exists(gamestate_path):
            return
        try:
            with open(gamestate_path, 'r', encoding='utf-8') as f:
                gamestate = json.load(f)
        except Exception:
            return
        if not isinstance(gamestate, dict) or 'timers' not in gamestate or 'active_timers' not in gamestate['timers']:
            return
        timer_state = gamestate['timers']['active_timers']
        if not isinstance(timer_state, list):
            return
        tab_id = tab_data.get('id')
        if not tab_id:
            try:
                main_ui = self.parent()
                if main_ui and hasattr(main_ui, 'tabs_data'):
                    if tab_data in main_ui.tabs_data:
                        tab_id = main_ui.tabs_data.index(tab_data)
                    else:
                        tab_id = "unknown_tab"
            except Exception:
                tab_id = "unknown_tab"
        with self.lock:
            if tab_id in self.active_timers:
                for rule_id, timers_dict in self.active_timers[tab_id].items():
                    for timer_key, timer in timers_dict.items():
                        timer.stop()
                self.active_timers[tab_id] = {}
        timer_rules = []
        timer_rules_widget = tab_data.get('timer_rules_widget')
        if timer_rules_widget:
            if hasattr(timer_rules_widget, 'get_timer_rules'):
                timer_rules = timer_rules_widget.get_timer_rules()
        else:
            try:
                if hasattr(self.parent(), '_load_timer_rules_for_tab'):
                    timer_rules = self.parent()._load_timer_rules_for_tab(tab_id) or []
            except Exception:
                timer_rules = []
        if timer_rules_widget and timer_rules:
            try:
                if hasattr(timer_rules_widget, 'load_timer_rules'):
                    timer_rules_widget.load_timer_rules(timer_rules)
                if hasattr(tab_data, 'get') and callable(tab_data.get):
                    tab_data['timer_rules_loaded'] = True
            except Exception:
                pass
        elif not timer_rules_widget and timer_rules:
            if hasattr(tab_data, 'get') and callable(tab_data.get):
                tab_data['timer_rules_loaded'] = True
        rule_lookup = {}
        if timer_rules:
            rule_lookup = {rule.get('id'): rule for rule in timer_rules if rule and rule.get('id')}
        if not rule_lookup:
            try:
                workflow_data_dir = tab_data.get('workflow_data_dir')
                if workflow_data_dir:
                    timer_rules_file = os.path.join(workflow_data_dir, 'game', 'timer_rules.json')
                    if os.path.exists(timer_rules_file):
                        try:
                            with open(timer_rules_file, 'r', encoding='utf-8') as f:
                                file_rules = json.load(f)
                                if isinstance(file_rules, list) and file_rules:
                                    rule_lookup = {rule.get('id'): rule for rule in file_rules if rule and rule.get('id')}
                        except Exception:
                            pass
            except Exception:
                pass
            if not rule_lookup and timer_rules_widget and hasattr(timer_rules_widget, 'get_timer_rules'):
                try:
                    widget_rules = timer_rules_widget.get_timer_rules()
                    if widget_rules:
                        rule_lookup = {rule.get('id'): rule for rule in widget_rules if rule and rule.get('id')}
                except Exception:
                    pass
            if not rule_lookup:
                return
        restored_count = 0
        with self.lock:
            for timer_data in timer_state:
                rule_id = timer_data.get('rule_id')
                timer_key = timer_data.get('key')
                is_character = timer_data.get('is_character', False)
                time_remaining_ms = timer_data.get('time_remaining_ms', 0)
                if not rule_id or not timer_key:
                    continue
                if rule_id not in rule_lookup:
                    similar_rule_id = None
                    is_character_timer = timer_data.get('is_character', False)
                    character_binding = timer_data.get('character')
                    for potential_rule_id, rule in rule_lookup.items():
                        rule_scope = rule.get('rule_scope') or rule.get('scope', 'Global')
                        is_character_rule = rule_scope == 'Character'
                        if is_character_timer == is_character_rule:
                            similar_rule_id = potential_rule_id
                            break
                    if similar_rule_id:
                        rule_id = similar_rule_id
                    else:
                        continue
                rule_data = rule_lookup[rule_id]
                if not rule_data.get('enabled', True):
                    continue
                character_binding = timer_data.get('character') if is_character else None
                
                # For character timers, validate that the character is present in the current scene
                if is_character and character_binding:
                    main_ui = self.parent()
                    if main_ui and hasattr(main_ui, 'get_character_names_in_scene_for_timers'):
                        characters_in_scene = main_ui.get_character_names_in_scene_for_timers(tab_data)
                        if character_binding not in characters_in_scene:
                            print(f"[TIMER LOAD] Skipping restoration of character timer for '{character_binding}' - character not present in current scene. Characters in scene: {characters_in_scene}")
                            continue
                        else:
                            print(f"[TIMER LOAD] Restoring character timer for '{character_binding}' - character is present in scene")
                    else:
                        print(f"[TIMER LOAD] Warning: Cannot validate scene presence for character timer '{character_binding}', skipping restoration to be safe")
                        continue
                
                if tab_id not in self.active_timers:
                    self.active_timers[tab_id] = {}
                if rule_id not in self.active_timers[tab_id]:
                    self.active_timers[tab_id][rule_id] = {}
                try:
                    timer_instance = TimerInstance(rule_data, character_binding, tab_data)
                    self.active_timers[tab_id][rule_id][timer_key] = timer_instance
                    if timer_data.get('is_random', False):
                        timer_instance.recalculate_interval()
                    elif 'interval_ms' in timer_data:
                        timer_instance.interval_ms = timer_data['interval_ms']
                    timer_instance.start()
                    if time_remaining_ms > 0:
                        now = datetime.now()
                        timer_instance.next_fire_time = now + timedelta(milliseconds=time_remaining_ms)
                    else:
                        timer_instance.next_fire_time = datetime.now() + timedelta(milliseconds=1000)
                    restored_count += 1
                except Exception:
                    pass

    def remove_timer_rule(self, rule_id, tab_data):
        if not tab_data:
            return 0
        tab_id = tab_data.get('id')
        if not tab_id:
            try:
                main_ui = self.parent()
                if main_ui and hasattr(main_ui, 'tabs_data'):
                    if tab_data in main_ui.tabs_data:
                        tab_id = main_ui.tabs_data.index(tab_data)
                    else:
                        tab_id = "unknown_tab"
            except Exception:
                tab_id = "unknown_tab"
        removed_count = 0
        with self.lock:
            if tab_id in self.active_timers and rule_id in self.active_timers[tab_id]:
                removed_count = len(self.active_timers[tab_id][rule_id])
                for timer_key, timer in list(self.active_timers[tab_id][rule_id].items()):
                    timer.stop()
                del self.active_timers[tab_id][rule_id]
                self.save_timer_state(tab_data)
        return removed_count

    def cleanup_invalid_timers(self, tab_data):
        if not tab_data:
            return 0
        valid_rule_ids = set()
        timer_rules_widget = tab_data.get('timer_rules_widget')
        if timer_rules_widget and hasattr(timer_rules_widget, 'get_timer_rules'):
            try:
                current_rules = timer_rules_widget.get_timer_rules()
                for rule in current_rules:
                    if rule and rule.get('id'):
                        valid_rule_ids.add(rule.get('id'))
            except Exception as e:
                pass
        if not valid_rule_ids and hasattr(self.parent(), '_load_timer_rules_for_tab'):
            try:
                tab_id_val = tab_data.get('id')
                if not tab_id_val and hasattr(self.parent(), 'tabs_data'):
                    if tab_data in self.parent().tabs_data:
                        tab_id_val = self.parent().tabs_data.index(tab_data)
                if tab_id_val is not None:
                    parent_rules = self.parent()._load_timer_rules_for_tab(tab_id_val) or []
                    for rule in parent_rules:
                        if rule and rule.get('id'):
                            valid_rule_ids.add(rule.get('id'))
            except Exception as e:
                pass
        if not valid_rule_ids:
            return 0
        tab_id_lookup = tab_data.get('id')
        if not tab_id_lookup:
            try:
                if tab_data in self.parent().tabs_data:
                    tab_id_lookup = self.parent().tabs_data.index(tab_data)
                else:
                    tab_id_lookup = "unknown_tab"
            except Exception:
                tab_id_lookup = "unknown_tab"
        tab_id = str(tab_id_lookup)
        removed_count = 0
        with self.lock:
            if tab_id in self.active_timers:
                active_rule_ids = list(self.active_timers[tab_id].keys())
                invalid_rule_ids = [rule_id for rule_id in active_rule_ids if rule_id not in valid_rule_ids]
                for rule_id in invalid_rule_ids:
                    rule_timer_count = len(self.active_timers[tab_id][rule_id])
                    removed_count += rule_timer_count
                    for timer_key, timer in list(self.active_timers[tab_id][rule_id].items()):
                        timer.stop()
                    del self.active_timers[tab_id][rule_id]
                if invalid_rule_ids:
                    self.save_timer_state(tab_data)
        return removed_count

    def reload_timer_rules(self, new_rules, tab_data):
        try:
            tab_id = tab_data.get('tab_id', 'unknown')
            if tab_id in self.active_timers:
                for rule_id, rule_timers in self.active_timers[tab_id].items():
                    for timer_key, timer_instance in rule_timers.items():
                        try:
                            timer_instance.stop()
                        except Exception as e:
                            pass
                self.active_timers[tab_id] = {}
            timer_rules_widget = tab_data.get('timer_rules_widget')
            if timer_rules_widget and hasattr(timer_rules_widget, 'load_timer_rules'):
                timer_rules_widget.load_timer_rules(new_rules)
            tab_data['timer_rules'] = new_rules
            self._restart_enabled_timers(new_rules, tab_data)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _restart_enabled_timers(self, rules, tab_data):
        try:
            tab_id = tab_data.get('tab_id', 'unknown')
            for rule in rules:
                if not rule or not rule.get('enabled', True):
                    continue
                rule_id = rule.get('id')
                if not rule_id:
                    continue
                start_after_trigger = rule.get('start_after_trigger', 'Player')
                rule_scope = rule.get('rule_scope', 'Global')
                should_start = False
                if start_after_trigger == 'Player':
                    should_start = (rule_scope == 'Global')
                elif start_after_trigger == 'Character':
                    should_start = True
                elif start_after_trigger == 'Scene Change':
                    should_start = (rule_scope == 'Global')
                if should_start:
                    try:
                        if tab_id not in self.active_timers:
                            self.active_timers[tab_id] = {}
                        if rule_id not in self.active_timers[tab_id]:
                            self.active_timers[tab_id][rule_id] = {}
                        if rule_scope == 'Character':
                            timer_key = 'global'
                        else:
                            timer_key = 'global'
                        timer_instance = TimerInstance(rule, None, tab_data)
                        self.active_timers[tab_id][rule_id][timer_key] = timer_instance
                        timer_instance.start()
                    except Exception as e:
                        pass
        except Exception as e:
            import traceback
            traceback.print_exc()

def execute_timer_action(main_ui, rule_data, action, character_name=None, tab_data=None):
    if not main_ui or not action or not tab_data:
        return
    time_manager_widget = tab_data.get('time_manager_widget')
    if time_manager_widget and hasattr(time_manager_widget, 'update_time'):
        time_manager_widget.update_time(main_ui, tab_data)
    action_type = action.get('type')
    allow_live_input = action.get('allow_live_input', False)
    main_ui._allow_live_input_for_current_action = allow_live_input
    if action_type in ["Narrator Post", "Actor Post"] and not allow_live_input:
        main_ui._disable_input_for_pipeline()
    if action_type == "Set Var":
        _execute_set_var_action(main_ui, action, character_name, tab_data)
    elif action_type == "System Message":
        pass
    elif action_type == "Narrator Post":
        _execute_narrator_post_action(main_ui, action, tab_data)
    elif action_type == "Actor Post":
        actor_name_from_action = action.get('actor_name', '')
        target_actor_name = character_name if not actor_name_from_action else actor_name_from_action
        if not target_actor_name:
            return
        if not tab_data:
            return
        if hasattr(main_ui, 'get_character_names_in_scene_for_timers'):
            characters_in_scene = main_ui.get_character_names_in_scene_for_timers(tab_data)
            if target_actor_name not in characters_in_scene:
                return
        action_system_message = action.get('system_message', '')
        timer_system_modifications = []
        if rule_data and 'actions' in rule_data:
            for i, rule_action in enumerate(rule_data['actions']):
                action_type = rule_action.get('type')
                if action_type == 'System Message':
                    sys_msg = rule_action.get('value', '')
                    if sys_msg:
                        if hasattr(main_ui, '_substitute_variables_in_string'):
                            sys_msg = main_ui._substitute_variables_in_string(sys_msg, tab_data, target_actor_name)
                        timer_mod = {
                            'action': sys_msg,
                            'position': rule_action.get('position', 'prepend'),
                            'system_message_position': rule_action.get('system_message_position', 'first'),
                            'switch_model': None
                        }
                        timer_system_modifications.append(timer_mod)
        run_single_character_post(
            main_ui,
            target_actor_name,
            tab_data,
            system_message_override=action_system_message,
            trigger_type="timer",
            timer_system_modifications=timer_system_modifications
        )
    elif action_type == "New Scene":
        from core.utils import increment_scene_number
        increment_scene_number(main_ui, tab_data)
    elif action_type == "Game Over":
        game_over_message = action.get("message", "Game Over")
        current_tab_index = main_ui.tab_widget.currentIndex() if hasattr(main_ui, 'tab_widget') else -1
        try:
            from core.game_over import trigger_game_over
            success = trigger_game_over(main_ui, current_tab_index, game_over_message)
        except Exception as e:
            print(f"[TIMER ACTION] Error triggering Game Over from timer rule: {e}")
        return

def _execute_set_var_action(main_ui, action, character_name, tab_data):
    var_name = action.get('var_name', '')
    var_value = action.get('var_value', '')
    scope = action.get('scope', 'Global')
    operation = action.get('operation', 'Set')
    if not var_name:
        return
    if isinstance(var_value, str) and hasattr(main_ui, '_substitute_variables_in_string'):
        print(f"[TIMER SET VAR DEBUG] Before substitution: var_value='{var_value}', character_name='{character_name}'")
        var_value = main_ui._substitute_variables_in_string(var_value, tab_data, character_name)
        print(f"[TIMER SET VAR DEBUG] After substitution: var_value='{var_value}'")
    
    if operation == 'Generate':
        gen_instructions = action.get('generate_instructions', '')
        gen_context = action.get('generate_context', 'Last Exchange')
        context_str = None
        if gen_context == 'Full Conversation':
            context_list = tab_data.get('context', [])
            formatted_history = []
            for msg in context_list:
                if msg.get('role') != 'system':
                    formatted_history.append(f"{msg.get('role', 'unknown').capitalize()}: {msg.get('content', '')}")
            context_str = "\n".join(formatted_history)
        elif gen_context == 'Last Exchange':
            prev_assistant_msg = tab_data.get('_last_assistant_msg', '')
            current_user_msg = tab_data.get('_last_user_msg', '')
            context_str = f"Assistant: {prev_assistant_msg}\nUser: {current_user_msg}"
        elif gen_context == 'User Message':
            context_str = tab_data.get('_last_user_msg', '')
        else:
            context_str = tab_data.get('_last_user_msg', '')
        var_filepath = None
        if scope == 'Global':
            if hasattr(main_ui, '_get_variables_file'):
                tab_index = main_ui.tabs_data.index(tab_data) if tab_data in main_ui.tabs_data else -1
                if tab_index >= 0:
                    var_filepath = main_ui._get_variables_file(tab_index)
            elif 'variables_file' in tab_data:
                var_filepath = tab_data['variables_file']
        from generate.generate_summary import generate_summary
        generated_value = generate_summary(main_ui, context_str, gen_instructions, var_name, scope, var_filepath, character_name, tab_data)
        var_value = generated_value
    if scope == 'Character':
        if not character_name:
            character_name = action.get('actor_name', '')
            if not character_name:
                return
        workflow_dir = tab_data.get('workflow_data_dir')
        if not workflow_dir:
            return
        try:
            from core.utils import _get_or_create_actor_data
            actor_data, actor_file = _get_or_create_actor_data(main_ui, workflow_dir, character_name)
            if not actor_data or not actor_file:
                return
            if 'variables' not in actor_data or not isinstance(actor_data['variables'], dict):
                actor_data['variables'] = {}
            _apply_variable_operation(actor_data['variables'], var_name, var_value, 'Set')
            with open(actor_file, 'w', encoding='utf-8') as f:
                json.dump(actor_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
        except ImportError:
            pass
        except Exception as e:
            pass
    elif scope == 'Setting':
        workflow_dir = tab_data.get('workflow_data_dir')
        if not workflow_dir:
            return
        try:
            from core.utils import _get_player_current_setting_name, _find_setting_file_by_name
            setting_name = _get_player_current_setting_name(workflow_dir)
            if not setting_name:
                return
            session_settings_dir = os.path.join(workflow_dir, 'game', 'settings')
            setting_file = _find_setting_file_by_name(session_settings_dir, setting_name)
            if not setting_file:
                return
            with open(setting_file, 'r', encoding='utf-8') as f:
                setting_data = json.load(f)
            if 'variables' not in setting_data or not isinstance(setting_data['variables'], dict):
                setting_data['variables'] = {}
            _apply_variable_operation(setting_data['variables'], var_name, var_value, 'Set')
            with open(setting_file, 'w', encoding='utf-8') as f:
                json.dump(setting_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
        except ImportError:
            pass
        except Exception as e:
            pass
    else:
        tab_index = main_ui.tabs_data.index(tab_data) if tab_data in main_ui.tabs_data else -1
        if tab_index < 0:
            return
        variables = main_ui._load_variables(tab_index)
        _apply_variable_operation(variables, var_name, var_value, 'Set')
        main_ui._save_variables(tab_index, variables)

def _apply_variable_operation(variables_dict, var_name, var_value, operation):
    if operation == "Set":
        variables_dict[var_name] = var_value
    else:
        current_value = variables_dict.get(var_name, 0)
        try:
            if isinstance(current_value, str):
                if '.' in current_value:
                    current_value = float(current_value)
                else:
                    current_value = int(current_value)
            if isinstance(var_value, str):
                if '.' in var_value:
                    var_value = float(var_value)
                else:
                    var_value = int(var_value)
        except (ValueError, TypeError):
            variables_dict[var_name] = f"{current_value}{var_value}"
            return
        if operation == "Increment":
            variables_dict[var_name] = current_value + var_value
        elif operation == "Decrement":
            variables_dict[var_name] = current_value - var_value
        elif operation == "Multiply":
            variables_dict[var_name] = current_value * var_value
        elif operation == "Divide":
            if var_value != 0:
                variables_dict[var_name] = current_value / var_value
            else:
                variables_dict[var_name] = current_value

def _execute_narrator_post_action(main_ui, action, tab_data):
    action_system_message = action.get('system_message', '')
    if not tab_data:
        return
    if not action_system_message:
        action_system_message = "(Describe a brief atmospheric change, ambient detail, or environmental shift in the scene.)"
    original_character_name = main_ui.character_name
    main_ui.character_name = "Narrator"
    tab_data['_timer_final_instruction'] = action_system_message
    tab_data['_is_timer_narrator_action_active'] = True
    tab_data['_last_timer_action_type'] = 'narrator'
    marker_user_message = "INTERNAL_TIMER_NARRATOR_ACTION"
    try:
        main_ui._complete_message_processing(marker_user_message)
    except Exception as e:
        pass
    finally:
        main_ui.character_name = original_character_name

def _execute_new_scene_action(main_ui, tab_data):
    if not tab_data:
        return
    current_scene = tab_data.get('scene_number', 1)
    new_scene_number = current_scene + 1
    tab_data['scene_number'] = new_scene_number
    tab_data['pending_scene_update'] = True
    if main_ui and hasattr(main_ui, 'timer_manager'):
        main_ui.timer_manager.process_scene_change(tab_data)
    output_widget = main_ui.get_current_output_widget()
    if output_widget:
        output_widget.update_all_message_scene_contexts(tab_data['scene_number'])
        tab_data['pending_scene_update'] = False



