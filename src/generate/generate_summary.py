from core.make_inference import make_inference
from config import get_default_utility_model
import os
import json
from core.utils import _get_or_create_actor_data, _get_player_current_setting_name, _find_setting_file_by_name
from rules.apply_rules import _apply_string_operation_mode

def generate_summary(self, context, instructions, var_name, var_scope, var_filepath=None, character_name=None, tab_data=None, set_var_mode='replace', delimiter='/'):
    if not var_name:
        return None
    prompt = f"""{instructions.strip() if instructions else ''}\n\nContext:\n{context.strip() if context else ''}\n\nGenerate a summary or value for the variable '{var_name}'. Output only the value as plain text."""
    result = make_inference(
        context=[{"role": "user", "content": prompt}],
        user_message=prompt,
        character_name=None,
        url_type=get_default_utility_model(),
        max_tokens=1024,
        temperature=0.7,
        is_utility_call=True
    )
    generated_value = result.strip() if result else ""
    if var_scope == 'Character':
        if not tab_data or not character_name:
            return generated_value
        workflow_data_dir = tab_data.get('workflow_data_dir')
        actor_data, actor_path = _get_or_create_actor_data(self, workflow_data_dir, character_name)
        if not actor_data or not actor_path:
            return generated_value
        if 'variables' not in actor_data or not isinstance(actor_data['variables'], dict):
            actor_data['variables'] = {}
        prev_value = actor_data['variables'].get(var_name)
        final_value = _apply_string_operation_mode(prev_value, generated_value, set_var_mode, delimiter)
        actor_data['variables'][var_name] = final_value
        try:
            with open(actor_path, 'w', encoding='utf-8') as f:
                json.dump(actor_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    elif var_scope == 'Setting':
        if not tab_data:
            return generated_value
        workflow_data_dir = tab_data.get('workflow_data_dir')
        player_setting_name = _get_player_current_setting_name(workflow_data_dir)
        if not player_setting_name or player_setting_name == "Unknown Setting":
            return generated_value
        session_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
        found_setting_file = _find_setting_file_by_name(session_settings_dir, player_setting_name)
        if not found_setting_file:
            base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
            found_base_setting_file = _find_setting_file_by_name(base_settings_dir, player_setting_name)
            if found_base_setting_file:
                rel_path = os.path.relpath(found_base_setting_file, base_settings_dir)
                dest_path = os.path.join(session_settings_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                import shutil
                try:
                    shutil.copy2(found_base_setting_file, dest_path)
                except Exception:
                    return generated_value
                found_setting_file = dest_path
            else:
                return generated_value
        try:
            with open(found_setting_file, 'r', encoding='utf-8') as f:
                setting_data = json.load(f)
            if 'variables' not in setting_data or not isinstance(setting_data['variables'], dict):
                setting_data['variables'] = {}
            prev_value = setting_data['variables'].get(var_name)
            final_value = _apply_string_operation_mode(prev_value, generated_value, set_var_mode, delimiter)
            setting_data['variables'][var_name] = final_value
            with open(found_setting_file, 'w', encoding='utf-8') as f:
                json.dump(setting_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    elif var_scope == 'Global':
        if not var_filepath:
            return generated_value
        try:
            if not os.path.exists(var_filepath):
                variables = {}
            else:
                with open(var_filepath, 'r', encoding='utf-8') as f:
                    variables = json.load(f)
        except Exception:
            variables = {}
        prev_value = variables.get(var_name)
        final_value = _apply_string_operation_mode(prev_value, generated_value, set_var_mode, delimiter)
        variables[var_name] = final_value
        try:
            with open(var_filepath, 'w', encoding='utf-8') as f:
                json.dump(variables, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    return generated_value
