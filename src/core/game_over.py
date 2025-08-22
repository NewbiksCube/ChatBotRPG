import os
import json
import pyfiglet
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication


def trigger_game_over(ui_instance, tab_index, game_over_message="Game Over"):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return False
    tab_data = ui_instance.tabs_data[tab_index]
    _stop_all_rule_processing(ui_instance, tab_data)
    _perform_game_over_reset(ui_instance, tab_index, tab_data)
    _show_game_over_screen(ui_instance, tab_index, game_over_message)
    return True

def _stop_all_rule_processing(ui_instance, tab_data):
    if '_characters_to_exit_rules' not in tab_data:
        tab_data['_characters_to_exit_rules'] = set()
    tab_data['_narrator_to_exit_rules'] = True
    workflow_data_dir = tab_data.get('workflow_data_dir')
    if workflow_data_dir and hasattr(ui_instance, 'get_character_names_in_scene_for_timers'):
        try:
            characters_in_scene = ui_instance.get_character_names_in_scene_for_timers(tab_data)
            if characters_in_scene:
                for char_name in characters_in_scene:
                    tab_data['_characters_to_exit_rules'].add(char_name)
        except Exception as e:
            pass
    tab_data['_exit_rule_processing'] = True
    if hasattr(ui_instance, '_processing_npc_queue'):
        ui_instance._processing_npc_queue = False
    if hasattr(ui_instance, 'npc_inference_threads'):
        ui_instance.npc_inference_threads.clear()
    if hasattr(ui_instance, '_npc_message_queue'):
        ui_instance._npc_message_queue.clear()

def _perform_game_over_reset(ui_instance, tab_index, tab_data):
    workflow_data_dir = tab_data.get('workflow_data_dir')
    
    # Stop ALL timers from ALL tabs to prevent cross-session contamination
    if hasattr(ui_instance, 'timer_manager'):
        ui_instance.timer_manager.stop_all_timers()
        print("  Game Over Reset: Stopped all timers from all tabs to prevent cross-session contamination")
    
    if hasattr(ui_instance, 'timer_manager'):
        ui_instance.timer_manager.stop_timers_for_tab(tab_data)
        tab_data['timer_rules_loaded'] = False
        if workflow_data_dir:
            gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
            if os.path.exists(gamestate_path):
                try:
                    with open(gamestate_path, 'r', encoding='utf-8') as f:
                        gamestate = json.load(f)
                    if 'timers' in gamestate:
                        gamestate['timers'] = {'active_timers': []}
                        with open(gamestate_path, 'w', encoding='utf-8') as f:
                            json.dump(gamestate, f, indent=2)
                        if hasattr(ui_instance, 'timer_manager'):
                            cleaned_count = ui_instance.timer_manager.cleanup_invalid_timers(tab_data)
                except Exception as e:
                    pass
    if workflow_data_dir:
        gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
        gamestate = {}
        if os.path.exists(gamestate_path):
            try:
                with open(gamestate_path, 'r', encoding='utf-8') as f:
                    gamestate = json.load(f)
            except Exception as e:
                pass
        gamestate['effects'] = {
            "blur": {"enabled": False, "radius": 5, "animation_speed": 2000, "animate": False},
            "flicker": {"enabled": False, "intensity": 0.1, "frequency": 1000, "color": "white"},
            "static": {"enabled": False, "intensity": 0.05, "frequency": 200, "dot_size": 1},
            "darken_brighten": {"enabled": False, "factor": 1.0, "animation_speed": 2000, "animate": False}
        }
        gamestate['effects_by_id'] = {}
        if 'effects_ids_order' in gamestate:
            del gamestate['effects_ids_order']
        try:
            with open(gamestate_path, 'w', encoding='utf-8') as f:
                json.dump(gamestate, f, indent=2)
        except Exception as e:
            pass
    if workflow_data_dir:
        import shutil
        game_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
        game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
        try:
            if os.path.isdir(game_settings_dir):
                shutil.rmtree(game_settings_dir)
        except Exception as e:
            pass
        try:
            if os.path.isdir(game_actors_dir):
                shutil.rmtree(game_actors_dir)
        except Exception as e:
            pass
    output_widget = tab_data.get('output')
    context_file = tab_data.get('context_file')
    log_file = tab_data.get('log_file')
    if output_widget:
        output_widget.clear_messages()
    tab_data['context'] = []
    tab_data['turn_count'] = 1
    tab_data['scene_number'] = 1
    ui_instance._update_turn_counter_display()
    tab_data['_has_narrator_posted_this_scene'] = False
    tab_data['_remembered_selected_message'] = None
    if context_file:
        try:
            with open(context_file, "w", encoding="utf-8") as f:
                json.dump([], f)
        except Exception as e:
            pass
    if log_file:
        try:
            empty_html = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">
p, li { white-space: pre-wrap; }
</style></head><body style=\" font-family:'Arial'; font-size:16pt; font-weight:400; font-style:normal;\">
<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"""
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(empty_html)
        except Exception as e:
            pass
    variables = ui_instance._load_variables(tab_index)
    if variables:
        keys_to_keep = {'introduction_checked', 'introduction_title', 'introduction_text', 'introduction_description', 'introduction_messages', 'introduction_sequence', 'origin'}
        persistent_variables = {k: v for k, v in variables.items() if k.endswith('*') or k in keys_to_keep or k.startswith('introduction_')}
        removed_count = len(variables) - len(persistent_variables)
        ui_instance._save_variables(tab_index, persistent_variables)
    if workflow_data_dir:
        from core.utils import reset_player_to_origin
        reset_player_to_origin(workflow_data_dir)
        try:
            from core.memory import cleanup_template_files_from_npc_notes
            cleanup_template_files_from_npc_notes(workflow_data_dir)
        except Exception as e:
            pass
    if hasattr(ui_instance, '_actor_name_to_file_cache'):
        ui_instance._actor_name_to_file_cache.clear()
    if hasattr(ui_instance, '_actor_name_to_actual_name'):
        ui_instance._actor_name_to_actual_name.clear()
    if tab_data is not None:
        if 'variables' in tab_data:
            tab_data['variables'] = {}
    tab_data['timer_rules_loaded'] = False


def _show_game_over_screen(ui_instance, tab_index, game_over_message):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    tab_data['_is_showing_game_over'] = True
    top_splitter = tab_data.get('top_splitter')
    if top_splitter:
        top_splitter.setVisible(False)
        QApplication.processEvents()
    right_splitter = tab_data.get('right_splitter')
    if right_splitter:
        right_splitter.setVisible(False)
        QApplication.processEvents()
    output_widget = tab_data.get('output')
    input_field = tab_data.get('input')
    if not (output_widget and input_field):
        return
    output_widget.clear_messages()
    try:
        ascii_art = pyfiglet.figlet_format("GAME OVER", font="cybermedium")
    except pyfiglet.FontNotFound:
        ascii_art = pyfiglet.figlet_format("GAME OVER")
    except Exception as e:
        ascii_art = "GAME OVER"
    escaped_ascii_art = ascii_art.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    title_html = f'<pre style="text-align: center; margin: 0 auto; background: transparent; color: #ff4444;"><code style="background: transparent; font-family: monospace; display: inline-block; text-align: left;">{escaped_ascii_art}</code></pre>'
    escaped_message = game_over_message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    message_html = f'<p id="game-over-message" style="text-align: center; font-family: Consolas; font-size: 14pt; margin-top: 20px; color: #ff6666;">{escaped_message}</p>'
    prompt_html = '<p id="game-over-prompt" style="text-align: center; font-family: Consolas; font-size: 10pt; margin-top: 30px;"></p>'
    game_over_html = f'<div style="text-align: center; width: 100%;">{title_html}{message_html}{prompt_html}</div>'
    message_type = 'intro'
    game_over_message_widget = output_widget.add_message(
        message_type,
        game_over_html,
        immediate=True,
        prompt_finished_callback=lambda idx=tab_index: _handle_game_over_prompt_finished(ui_instance, idx)
    )
    tab_data['_game_over_message_widget'] = game_over_message_widget
    input_field.set_input_state("disabled")
    QTimer.singleShot(2000, lambda: _show_game_over_options(ui_instance, tab_index))

def _show_game_over_options(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    input_field = tab_data.get('input')
    if input_field:
        saves_exist = _check_saves_exist_for_tab(ui_instance, tab_index)
        input_field.set_input_state("intro")
        try:
            input_field.load_requested.disconnect()
            input_field.new_requested.disconnect()
        except:
            pass
        input_field.load_requested.connect(
            lambda emitted_idx: _handle_game_over_load_requested(ui_instance, tab_index)
        )
        input_field.new_requested.connect(
            lambda emitted_idx: _handle_game_over_new_requested(ui_instance, tab_index)
        )
        input_field.setFocus()
    if hasattr(ui_instance, 'activateWindow'):
        ui_instance.activateWindow()
    if hasattr(ui_instance, 'raise_'):
        ui_instance.raise_()

def _handle_game_over_prompt_finished(ui_instance, tab_index):
    pass

def _handle_game_over_option_selected(ui_instance, tab_index):
    _show_game_over_options(ui_instance, tab_index)

def _show_load_new_selection(ui_instance, tab_index):
    _show_game_over_options(ui_instance, tab_index)

def _handle_load_new_key_press(ui_instance, tab_index, key_type):
    if key_type == 'load' or key_type == 'l':
        _handle_game_over_load_requested(ui_instance, tab_index)
    elif key_type == 'new' or key_type == 'n':
        _handle_game_over_new_requested(ui_instance, tab_index)

def _handle_game_over_load_requested(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    tab_data['_is_showing_game_over'] = False
    if '_game_over_message_widget' in tab_data:
        del tab_data['_game_over_message_widget']
    ui_instance.load_game_state()

def _handle_game_over_new_requested(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    tab_data['_is_showing_game_over'] = False
    if '_game_over_message_widget' in tab_data:
        del tab_data['_game_over_message_widget']
    _start_new_game_from_game_over(ui_instance, tab_index)

def _start_new_game_from_game_over(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    import core.game_intro
    core.game_intro.handle_intro_new_requested(ui_instance, tab_index)

def _check_saves_exist_for_tab(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return False
    tab_data = ui_instance.tabs_data[tab_index]
    tab_dir = os.path.dirname(tab_data.get('tab_settings_file', ''))
    if not tab_dir or not os.path.isdir(tab_dir):
        return False
    saves_dir = os.path.join(tab_dir, "saves")
    if not os.path.isdir(saves_dir):
        return False
    try:
        for item in os.listdir(saves_dir):
            if os.path.isdir(os.path.join(saves_dir, item)):
                return True
        return False
    except OSError:
        return False

def handle_keypress_for_game_over(ui_instance, event):
    tab_data = ui_instance.get_current_tab_data()
    if not tab_data or not tab_data.get('_is_showing_game_over'):
        return False
    input_field = tab_data.get('input')
    if not input_field:
        return False
    current_state = getattr(input_field, '_current_state', None)
    return False 
