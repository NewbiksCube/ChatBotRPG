import os
import pyfiglet
import json
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication

def handle_intro_load_requested(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    ui_instance.tab_widget.setCurrentIndex(tab_index)
    from core.utils import load_game_state
    load_game_state(ui_instance)

def handle_intro_new_requested(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    if tab_data:
        if hasattr(ui_instance, 'timer_manager'):
            print(f"Stopping all timers for tab {tab_index} before starting new game...")
            ui_instance.timer_manager.stop_timers_for_tab(tab_data)
            tab_data['timer_rules_loaded'] = False
        variables = load_variables(ui_instance, tab_index)
        intro_sequence = variables.get('introduction_sequence', [])
        if not intro_sequence:
            intro_messages = variables.get('introduction_messages', [])
            if intro_messages:
                intro_sequence = []
                for msg in intro_messages:
                    intro_sequence.append({'type': 'message', 'text': msg})
        input_field = tab_data.get('input')
        if input_field:
            input_field.set_input_state('intro_streaming')
            input_field.set_intro_prompt("", False)
            try:
                input_field.intro_enter_pressed.disconnect()
            except:
                pass
            input_field.intro_enter_pressed.connect(
                lambda emitted_idx: handle_intro_sequence_continue(ui_instance, tab_index if emitted_idx == -1 else emitted_idx)
            )
            begin_intro_sequence_streaming(ui_instance, tab_index, intro_sequence)

def begin_intro_sequence_streaming(ui_instance, tab_index, intro_sequence):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    if not intro_sequence:
        finish_intro_sequence(ui_instance, tab_index)
        return
    ui_instance.intro_sequence = intro_sequence
    ui_instance.current_intro_sequence_index = 0
    if tab_data and tab_data.get('output'):
        output_widget = tab_data.get('output')
        output_widget.clear_messages()
        message_type = 'assistant'
        tab_data['_intro_text_message_widget'] = output_widget.add_message(
            message_type, 
            "", 
            immediate=True
        )
        if tab_data['_intro_text_message_widget']:
            tab_data['_intro_text_message_widget'].set_selectable(False)
        process_next_intro_sequence_item(ui_instance, tab_index)
    else:
        print(f"Error: Cannot find output widget for intro sequence streaming on tab {tab_index}")

def process_next_intro_sequence_item(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    if ui_instance.current_intro_sequence_index >= len(ui_instance.intro_sequence):
        finish_intro_sequence(ui_instance, tab_index)
        return
    current_item = ui_instance.intro_sequence[ui_instance.current_intro_sequence_index]
    item_type = current_item.get('type')
    if item_type == 'message':
        message_text = current_item.get('text', '').strip()
        if not message_text:
            ui_instance.current_intro_sequence_index += 1
            QTimer.singleShot(50, lambda: process_next_intro_sequence_item(ui_instance, tab_index))
            return
        substituted_text = substitute_player_name_in_message(ui_instance, tab_index, message_text)
        intro_message_widget = tab_data.get('_intro_text_message_widget')
        if not intro_message_widget:
            output_widget = tab_data.get('output')
            if output_widget:
                message_type = 'assistant'
                intro_message_widget = output_widget.add_message(message_type, "", immediate=True)
                tab_data['_intro_text_message_widget'] = intro_message_widget
                if intro_message_widget:
                    intro_message_widget.set_selectable(False)
            else:
                print(f"Error: Cannot recreate intro message widget, output widget not found on tab {tab_index}")
                finish_intro_sequence(ui_instance, tab_index)
                return
        if intro_message_widget and hasattr(intro_message_widget, 'set_message_content'):
            intro_message_widget.content = substituted_text
            intro_message_widget.set_message_content(immediate=False)
            estimated_time = len(substituted_text) * 25
            QTimer.singleShot(
                estimated_time,  
                lambda: show_intro_continue_prompt(ui_instance, tab_index)
            )
        else:
            finish_intro_sequence(ui_instance, tab_index)
    elif item_type == 'player_gen':
        checkboxes = current_item.get('checkboxes', {})
        has_enabled_fields = any(checkboxes.values())
        if has_enabled_fields:
            print(f"Processing player generation item at index {ui_instance.current_intro_sequence_index}")
            show_character_generator(ui_instance, tab_index, current_item)
            return
        else:
            ui_instance.current_intro_sequence_index += 1
            QTimer.singleShot(100, lambda: process_next_intro_sequence_item(ui_instance, tab_index))
    else:
        ui_instance.current_intro_sequence_index += 1
        QTimer.singleShot(100, lambda: process_next_intro_sequence_item(ui_instance, tab_index))

def substitute_player_name_in_message(ui_instance, tab_index, message_text):
    if '(player)' not in message_text:
        return message_text
    tab_data = ui_instance.tabs_data[tab_index]
    workflow_data_dir = tab_data.get('workflow_data_dir')
    if not workflow_data_dir:
        return message_text
    try:
        from core.utils import _get_player_character_name
        player_name = _get_player_character_name(workflow_data_dir)
        if player_name:
            return message_text.replace('(player)', player_name)
        else:
            return message_text.replace('(player)', '[Player Name]')
    except Exception as e:
        return message_text.replace('(player)', '[Player Name]')

def handle_intro_sequence_continue(ui_instance, tab_index):
    print(f"handle_intro_sequence_continue called with tab_index: {tab_index}")
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    input_field = tab_data.get('input')
    if not input_field or not input_field._intro_ready_for_enter:
        return
    input_field.set_intro_prompt("", False)
    input_field.setFocus()
    if hasattr(ui_instance, 'current_intro_sequence_index'):
        ui_instance.current_intro_sequence_index += 1
        QTimer.singleShot(50, lambda: process_next_intro_sequence_item(ui_instance, tab_index))

def show_intro_continue_prompt(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    intro_message_widget = tab_data.get('_intro_text_message_widget')
    if intro_message_widget and hasattr(intro_message_widget, 'is_streaming') and intro_message_widget.is_streaming():
        QTimer.singleShot(500, lambda: show_intro_continue_prompt(ui_instance, tab_index))
        return
    input_field = tab_data.get('input')
    if input_field:
        input_field.set_intro_prompt("Press ENTER to continue...", True)
        input_field.setFocus()
    if hasattr(ui_instance, 'activateWindow'):
        ui_instance.activateWindow()
    if hasattr(ui_instance, 'raise_'):
        ui_instance.raise_()
def finish_intro_sequence(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    _finish_intro_to_normal_chat(ui_instance, tab_index)

def show_character_generator(ui_instance, tab_index, player_gen_data):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        return
    tab_data = ui_instance.tabs_data[tab_index]
    output_widget = tab_data.get('output')
    if not output_widget:
        print(f"Error: Could not find output widget for character generation on tab {tab_index}")
        return
    output_widget.clear_messages()
    if '_intro_text_message_widget' in tab_data:
        del tab_data['_intro_text_message_widget']
    if not tab_data.get('_chargen_widget'):
        from core.character_generator import CharacterGeneratorWidget
        theme_colors = tab_data.get('settings', {})
        if not theme_colors or 'base_color' not in theme_colors:
            theme_colors = {
                'base_color': '#00FF66', 
                'bg_color': '#181818',
                'text_color': '#00FF66',
                'border_color': '#00FF66'
            }
        chargen_widget = CharacterGeneratorWidget(
            theme_colors=theme_colors, 
            tab_index=tab_index, 
            parent=output_widget
        )
        if hasattr(chargen_widget, 'update_theme'):
            chargen_widget.update_theme(theme_colors)
        def on_character_complete(completed_tab_index):
            if hasattr(ui_instance, '_handle_character_generation_complete'):
                ui_instance._handle_character_generation_complete(completed_tab_index)
        chargen_widget.character_complete.connect(on_character_complete)
        chargen_widget.configure_from_intro_sequence(player_gen_data)
        tab_data['_chargen_widget'] = chargen_widget
    chargen_widget = tab_data['_chargen_widget']
    if hasattr(output_widget, 'container') and hasattr(output_widget.container, 'layout'):
        container_layout = output_widget.container.layout()
        if container_layout:
            if hasattr(container_layout, 'addWidget'):
                container_layout.addWidget(chargen_widget)
                if hasattr(container_layout, 'addStretch'):
                    while container_layout.count() > 1:
                        item = container_layout.itemAt(container_layout.count() - 1)
                        if hasattr(item, 'spacerItem') and item.spacerItem():
                            container_layout.removeItem(item)
                            break
                        else:
                            break
    from PyQt5.QtWidgets import QSizePolicy
    chargen_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    if hasattr(output_widget, 'size'):
        parent_size = output_widget.size()
        chargen_widget.resize(parent_size)
    if hasattr(output_widget, 'container'):
        container_rect = output_widget.container.geometry()
        chargen_widget.setGeometry(container_rect)
        chargen_widget.setMinimumSize(container_rect.width(), container_rect.height())
    chargen_widget.setVisible(True)
    chargen_widget.raise_()
    input_field = tab_data.get('input')
    if input_field:
        input_field.set_input_state('chargen')
    top_splitter = tab_data.get('top_splitter')
    if top_splitter:
        top_splitter.setVisible(False)
    right_splitter = tab_data.get('right_splitter')
    if right_splitter:
        right_splitter.setVisible(False)

def _finish_intro_to_normal_chat(ui_instance, tab_index):
    tab_data = ui_instance.tabs_data[tab_index]
    input_field = tab_data.get('input')
    input_field.set_input_state('normal')
    input_field.setFocus()
    if hasattr(input_field, 'text_input'):
        input_field.text_input.setFocus()
    tab_data['_is_showing_intro'] = False
    top_splitter = tab_data.get('top_splitter')
    if top_splitter:
        top_splitter.setVisible(True)
    right_splitter = tab_data.get('right_splitter')
    left_splitter = tab_data.get('left_splitter')
    if right_splitter and left_splitter and hasattr(left_splitter, 'live_game_button'):
        live_game_checked = left_splitter.live_game_button.isChecked()
        right_splitter.setVisible(live_game_checked)
    elif right_splitter:
        right_splitter.setVisible(False)
    if '_intro_text_message_widget' in tab_data:
        del tab_data['_intro_text_message_widget']
    if hasattr(ui_instance, 'intro_sequence'):
        del ui_instance.intro_sequence
    if hasattr(ui_instance, 'current_intro_sequence_index'):
        del ui_instance.current_intro_sequence_index

def handle_intro_prompt_finished(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        print(f"Error in handle_intro_prompt_finished: Invalid tab_index {tab_index}")
        return
    tab_data = ui_instance.tabs_data[tab_index]
    print(f"handle_intro_prompt_finished for tab: {tab_data.get('name', tab_index)}")

    if tab_data:
        input_field = tab_data.get('input')
        if input_field:
            input_field.set_input_state("intro")
            saves_exist = input_field.save_check_callback() if input_field.save_check_callback else False

def check_saves_exist_for_tab(ui_instance, tab_index):
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

def show_introduction(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index]):
        print(f"Cannot show introduction for invalid tab index {tab_index}")
        return
    tab_data = ui_instance.tabs_data[tab_index]
    tab_data['_is_showing_intro'] = True
    top_splitter = tab_data.get('top_splitter')
    if top_splitter:
        top_splitter.setVisible(False)
        QApplication.processEvents()
    else:
        print(f"Warning: Could not find top_splitter to hide for intro on tab {tab_index}.")
    right_splitter = tab_data.get('right_splitter')
    if right_splitter:
        right_splitter.setVisible(False)
        QApplication.processEvents()
    output_widget = tab_data.get('output')
    input_field = tab_data.get('input')
    variables = load_variables(ui_instance, tab_index)
    context = tab_data.get('context', [])
    show_intro_vars = variables.get('introduction_checked', False)
    intro_title = variables.get('introduction_title', "Introduction")
    intro_desc = variables.get('introduction_description', '')
    if show_intro_vars and not context and input_field and output_widget:
        output_widget.clear_messages()
        try:
            ascii_art = pyfiglet.figlet_format(intro_title, font="cybermedium") 
        except pyfiglet.FontNotFound:
            print(f"Warning: Font 'cybermedium' not found. Falling back to standard.")
            ascii_art = pyfiglet.figlet_format(intro_title)
        except Exception as e:
            print(f"Error generating ASCII art: {e}")
            ascii_art = intro_title
        escaped_ascii_art = ascii_art.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        title_html = f'<pre style="text-align: center; margin: 0 auto; background: transparent;"><code style="background: transparent; font-family: monospace; display: inline-block; text-align: left;">{escaped_ascii_art}</code></pre>'
        desc_html = f'<p id="intro-description" style="text-align: center; font-family: Consolas; font-size: 11pt; margin-top: 20px;">{intro_desc}</p>' if intro_desc else ""
        prompt_html = '<p id="intro-prompt" style="text-align: center; font-family: Consolas; font-size: 10pt; margin-top: 15px;"></p>'
        intro_message_html = f'<div style="text-align: center; width: 100%;">{title_html}{desc_html}{prompt_html}</div>'
        message_type = 'intro'
        output_widget.add_message(
            message_type,
            intro_message_html,
            immediate=True,
            prompt_finished_callback=lambda idx=tab_index: handle_intro_prompt_finished(ui_instance, idx)
        )
        
        if input_field:
            input_field.set_input_state("disabled")
        from core.add_tab import update_top_splitter_location_text
        update_top_splitter_location_text(tab_data)
    elif not show_intro_vars:
        print(f"Intro not checked for tab {tab_index}. Finishing intro sequence early.")
        finish_intro_sequence(ui_instance, tab_index) 

def handle_keypress_for_intro(ui_instance, event):
    tab_data = ui_instance.get_current_tab_data()
    if tab_data and 'input' in tab_data:
        input_field = tab_data['input']
        if (getattr(input_field, '_current_state', None) == 'intro_streaming' and
            getattr(input_field, '_intro_ready_for_enter', False) and
            event.key() in (Qt.Key_Return, Qt.Key_Enter)):
            current_tab_index = -1
            for i in range(len(ui_instance.tabs_data)):
                if ui_instance.tabs_data[i] == tab_data:
                    current_tab_index = i
                    break
            if current_tab_index != -1:
                handle_intro_sequence_continue(ui_instance, current_tab_index)
            else:
                print("Error: Could not determine current_tab_index in handle_keypress_for_intro.")
            event.accept()
            return True
    return False

def load_variables(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data) and ui_instance.tabs_data[tab_index] is not None):
        print(f"Error loading variables: Invalid tab index {tab_index}")
        return {}
    tab_data = ui_instance.tabs_data[tab_index]
    variables_file = tab_data.get('variables_file')
    if not variables_file:
        print(f"Error: No variables file path defined for tab index {tab_index}")
        return {}
    if not os.path.exists(variables_file):
        return {}
    try:
        with open(variables_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return {}
            variables = json.loads(content)

            return variables
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Warning: Could not load or parse variables file {variables_file}. Returning empty. Error: {e}")
        try:
            variables_dir = os.path.dirname(variables_file)
            if variables_dir and not os.path.exists(variables_dir):
                os.makedirs(variables_dir)
            with open(variables_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        except Exception as create_err:
            print(f"  Additionally failed to create empty variables file: {create_err}")

        return {}
    except Exception as e:
        print(f"Unexpected error loading variables from {variables_file}: {e}")
        return {}

def begin_intro_text_streaming(ui_instance, tab_index, intro_messages):
    intro_sequence = []
    for msg in intro_messages:
        intro_sequence.append({'type': 'message', 'text': msg})
    begin_intro_sequence_streaming(ui_instance, tab_index, intro_sequence)

def stream_next_intro_line(ui_instance, tab_index):
    process_next_intro_sequence_item(ui_instance, tab_index)

def handle_intro_text_continue(ui_instance, tab_index):
    handle_intro_sequence_continue(ui_instance, tab_index)
