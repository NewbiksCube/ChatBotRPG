import os
import sys
import pygame
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QComboBox, QHBoxLayout, QLabel, QPushButton, QMessageBox, QInputDialog, QDialog, QListWidget, QListWidgetItem, QRadioButton, QScrollArea, QLineEdit, QSizePolicy, QRadioButton, QSizePolicy, QListWidget, QListWidgetItem
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer, QSettings, QPoint, QPropertyAnimation, QEventLoop
from PyQt5.QtGui import QFont
import json
import time
import re
import core.game_intro
from core.theme_customizer import ThemeCustomizationDialog, update_ui_colors
from core.tab_manager import TabManagerWidget, restore_tabs, save_tabs_state, remove_tab
from core.make_inference import make_inference
from core.add_tab import add_new_tab, get_default_tab_settings, update_top_splitter_location_text
from core.utils import reset_player_to_origin, _get_player_current_setting_name, _load_json_safely, _save_json_safely, _get_or_create_actor_data, save_game_state, sanitize_folder_name, _get_player_character_name, _find_setting_file_prioritizing_game_dir
import shutil
from rules.rule_evaluator import _process_specific_rule, _process_next_sequential_rule_pre, _process_next_sequential_rule_post, _apply_rule_actions_and_continue, _evaluate_conditions
from core.character_inference import _start_npc_inference_threads, _get_follower_memories_for_context, _should_suppress_narrator, _check_process_npc_queue
from core.memory import get_npc_notes_from_character_file, format_npc_notes_for_context
from editor_panel.timer_manager import TimerManager, execute_timer_action
from rules.screen_effects import BlurEffect, FlickerEffect, StaticNoiseEffect, DarkenBrightenEffect, load_effects_from_gamestate
from core.splash_screen import SplashScreen
from config import get_default_model, get_default_cot_model, get_api_key_for_service, get_base_url_for_service, get_current_service
from core.process_keywords import inject_keywords_into_context, get_location_info_for_keywords
from editor_panel.time_manager import update_time

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FAVORITES_FILE = "model_favorites.json"
BASE_LOG_FILE = "conversation_log"
BASE_CONTEXT_FILE = "context_history"
BASE_SYSTEM_CONTEXT_FILE = "system_context"
BASE_THOUGHT_RULES_FILE = "thought_rules"
BASE_VARIABLES_FILE = "workflow_variables"
FALLBACK_MODEL_1 = "google/gemini-2.5-flash-lite-preview-06-17"
FALLBACK_MODEL_2 = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
FALLBACK_MODEL_3 = "thedrummer/anubis-70b-v1.1"


class InferenceThread(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, context, character_name, url_type, max_tokens, temperature, is_utility_call=False):
        super().__init__()
        self.context = context
        self.character_name = character_name
        self.url_type = url_type
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.is_utility_call = is_utility_call

    def run(self):
        try:
            log_header = "Context for Utility LLM" if self.is_utility_call else "Context for LLM"
            print(f"--- [{log_header} (Character: {self.character_name})] ---")
            try:
                print(json.dumps(self.context, indent=2))
            except Exception as json_e:
                print(f"    (Could not json dump context: {json_e})")
                print(self.context)
            print(f"--- [End {log_header} (Character: {self.character_name})] ---")
            user_message = self.context[-1]['content'] if self.context and self.context[-1]['role'] == 'user' else ""
            print(f"--- [Thread {self.character_name}] Calling make_inference --- User Msg: '{user_message[:30]}...'")
            assistant_message = make_inference(
                self.context,
                user_message,
                self.character_name,
                self.url_type,
                self.max_tokens,
                self.temperature,
                is_utility_call=self.is_utility_call
            )
            self.result_signal.emit(assistant_message)
        except Exception as e:
            error_msg = f"Error in InferenceThread.run for {self.character_name}: {e}"
            self.error_signal.emit(f"Inference error: {error_msg}")


class UtilityInferenceThread(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, chatbot_ui_instance, context, model_identifier, max_tokens, temperature, parent=None):
        super().__init__(parent)
        self.chatbot_ui_instance = chatbot_ui_instance
        self.context = context
        self.model_identifier = model_identifier
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.result_data = None
        self.error_message = None

    def run(self):
        try:
            
            current_service = get_current_service()
            api_key = get_api_key_for_service()
            if not api_key and current_service != "local":
                service_names = {"openrouter": "OpenRouter", "google": "Google GenAI"}
                service_name = service_names.get(current_service, current_service.title())
                error_msg = f"{service_name} API key not configured. Please check config.json file."
                print(f"[UtilityInferenceThread] {error_msg}")
                self.error_message = error_msg
                self.error_signal.emit(error_msg)
                return
            base_url = get_base_url_for_service()
            if base_url.endswith('/'):
                base_url = base_url.rstrip('/')
            for i, msg in enumerate(self.context):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
            result = self.chatbot_ui_instance._make_api_call_sync(
                api_key=api_key,
                base_url=base_url,
                model_name=self.model_identifier,
                messages=self.context,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            if result:
                self.result_data = result
                self.result_signal.emit(result)
            else:
                error_msg = "No result returned from API call"
                print(f"[UtilityInferenceThread] {error_msg}")
                self.error_message = error_msg
                self.error_signal.emit(error_msg)
        except Exception as e:
            error_msg = f"Exception in UtilityInferenceThread: {str(e)}"
            print(f"[UtilityInferenceThread] {error_msg}")
            import traceback
            traceback.print_exc()
            self.error_message = error_msg
            self.error_signal.emit(error_msg)


class ChatbotUI(QWidget):
    add_new_tab = add_new_tab
    def __init__(self):
        super().__init__()
        self.favorites = self.load_favorites()
        self.tabs_data = []
        self.current_tab_index = -1
        self.current_applied_theme = None
        self._narrator_streaming_lock = False
        self._npc_lock = False
        self._npc_inference_queue = []
        self._npc_inference_in_progress = False
        self._npc_message_queue = []
        self._screen_effects = {}
        self.current_applied_theme = get_default_tab_settings()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._drag_position = None
        self._resize_direction = None
        self._border_width = 5
        self._is_maximized = False
        self.character_name = "Narrator"
        self.max_tokens = 1024
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._perform_save_active_tab)
        self._save_requested = False
        self.initUI()
        QApplication.processEvents()
        self._restore_window_geometry()
        QApplication.processEvents()
        restore_tabs(self) 
        QApplication.processEvents()
        self.setup_sounds()
        final_active_index = -1
        if self.tab_widget.count() > 0:
             current_widget_index = self.tab_widget.currentIndex()
             if 0 <= current_widget_index < len(self.tabs_data) and self.tabs_data[current_widget_index]:
                 final_active_index = current_widget_index
             else:
                 final_active_index = next((i for i, data in enumerate(self.tabs_data) if data is not None), 0)
                 print(f"Warning: Index from restore_tabs ({current_widget_index}) invalid. Falling back to {final_active_index}")
                 self.tab_widget.setCurrentIndex(final_active_index)
             print(f"Final active tab index determined: {final_active_index}")
             self._apply_theme_for_tab(final_active_index)
        else:
             print("No tabs loaded, adding default tab.")
             self.add_new_tab(theme_settings=get_default_tab_settings()) 
             if self.tab_widget.count() > 0:
                  final_active_index = 0
                  self.tab_widget.setCurrentIndex(final_active_index)
                  self._apply_theme_for_tab(final_active_index)
        self.current_tab_index = final_active_index
        self._update_turn_counter_display()
        if final_active_index >= 0 and final_active_index < len(self.tabs_data) and self.tabs_data[final_active_index]:
            tab_data = self.tabs_data[final_active_index]
            right_splitter = tab_data.get('right_splitter')
            left_splitter = tab_data.get('left_splitter')
            if right_splitter and left_splitter and hasattr(left_splitter, 'live_game_button'):
                live_game_checked = left_splitter.live_game_button.isChecked()
                right_splitter.setVisible(live_game_checked)
        QApplication.processEvents()
        self.inference_thread = None
        self.utility_inference_thread = None
        self.utility_inference_thread_done_connect = False
        self._last_user_msg = ""
        self._last_assistant_msg = ""
        self._processing_cot_rules = False
        self._cot_next_step = None
        self._cot_rule_triggered_pre = False
        self._cot_rule_triggered_post = False
        self._cot_system_modifications = [] 
        self._timer_system_modifications = []
        self._cot_sequential_index = 0
        self._assistant_message_buffer = None
        self._last_user_msg_for_post_rules = None
        self._is_loading_rule = False
        self._is_loading_state = False
        self.files_to_delete_on_exit = []
        self._cleanup_old_backup_files()
        self.npc_inference_threads = []
        self._npc_display_timer = None
        self._processing_npc_queue = False
        self.timer_manager = TimerManager(self)
        self.timer_manager.timer_action_signal.connect(self._handle_timer_fired)
        if final_active_index >= 0 and final_active_index < len(self.tabs_data):
            active_tab_data = self.tabs_data[final_active_index]
            if active_tab_data:
                try:
                    workflow_data_dir = active_tab_data.get('workflow_data_dir')
                    if workflow_data_dir:
                        gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
                        if os.path.exists(gamestate_path):
                            try:
                                with open(gamestate_path, 'r', encoding='utf-8') as f:
                                    gamestate = json.load(f)
                                if 'timers' in gamestate and 'active_timers' in gamestate['timers']:
                                    timer_count = len(gamestate['timers']['active_timers'])
                            except Exception as e:
                                print(f"Error reading gamestate.json: {e}")
                    if not active_tab_data.get('timer_rules_loaded', False):
                        self._load_timer_rules_for_tab(final_active_index)
                        active_tab_data['timer_rules_loaded'] = True
                    self.timer_manager.load_timer_state(active_tab_data)
                    tab_id = active_tab_data.get('id')
                    if tab_id in self.timer_manager.active_timers:
                        timer_count = sum(len(timers) for timers in self.timer_manager.active_timers[tab_id].values())
                except Exception as e:
                    print(f"Error loading timer state on startup: {e}")
                    import traceback
                    traceback.print_exc()
        self.start_effects_check_timer()
        self._input_disabled_for_pipeline = False
        self._allow_live_input_for_current_action = False

    def _schedule_timer_checks(self):
        def comprehensive_timer_processing():
            tab_data = self.get_current_tab_data()
            if not tab_data or not hasattr(self, 'timer_manager'):
                return
            if hasattr(self, '_last_user_msg_for_post_rules') and self._last_user_msg_for_post_rules:
                self._just_processed_player_post = True
                self.timer_manager.process_post_events(
                    is_player_post=True,
                    tab_data=tab_data
                )
            current_context = self.get_current_context()
            just_processed_flag = hasattr(self, '_just_processed_player_post')
            if current_context and not just_processed_flag:
                current_scene = tab_data.get('scene_number', 1)
                current_turn = tab_data.get('turn_count', 0)
                characters_processed = []
                for msg in reversed(current_context[-10:]):
                    if (msg.get('role') == 'assistant' and 
                        msg.get('scene', 1) == current_scene and
                        msg.get('metadata', {}).get('turn', 0) == current_turn):
                        character_name = msg.get('metadata', {}).get('character_name')
                        if character_name and character_name not in characters_processed:
                    
                            characters_processed.append(character_name)
                            self.timer_manager.process_post_events(
                                is_player_post=False,
                                character_name=character_name,
                                tab_data=tab_data
                            )
            if hasattr(self, '_just_processed_player_post'):
                delattr(self, '_just_processed_player_post')
            self.timer_manager.check_for_newly_enabled_timers(
                tab_data=tab_data,
                character_name=None
            )
            self.timer_manager._check_timers()
        QTimer.singleShot(100, comprehensive_timer_processing)

    def _disable_input_for_pipeline(self):
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data.get('input'):
            current_state = getattr(tab_data['input'], '_current_state', 'normal')
            if current_state == 'normal':
                tab_data['input'].set_input_state('disabled')
                self._input_disabled_for_pipeline = True

    def _re_enable_input_after_pipeline(self):
        if self._input_disabled_for_pipeline:
            tab_data = self.get_current_tab_data()
            if tab_data and tab_data.get('input'):
                tab_data['input'].set_input_state('normal')
                tab_data['input'].setFocus()
                self._input_disabled_for_pipeline = False
                self._allow_live_input_for_current_action = False

    def _check_saves_exist_for_tab(self, tab_index):
        return core.game_intro.check_saves_exist_for_tab(self, tab_index)

    def _handle_intro_load_requested(self, tab_index):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index]):
            return
        core.game_intro.handle_intro_load_requested(self, tab_index)

    def _handle_intro_new_requested(self, tab_index):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index]):
            return
        core.game_intro.handle_intro_new_requested(self, tab_index)

    def _begin_intro_text_streaming(self, intro_messages):
        core.game_intro.begin_intro_text_streaming(self, intro_messages)
        
    def _stream_next_intro_line(self):
        core.game_intro.stream_next_intro_line(self)
    
    def _show_intro_continue_prompt(self):
        core.game_intro.show_intro_continue_prompt(self)
  
    def _handle_intro_text_continue(self):
        core.game_intro.handle_intro_text_continue(self)
    
    def _finish_intro_sequence(self):
        core.game_intro.finish_intro_sequence(self)

    def _handle_intro_prompt_finished(self):
        core.game_intro.handle_intro_prompt_finished(self)
    
    def _handle_character_generation_complete(self, tab_index):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index]):
            print(f"Error in _handle_character_generation_complete: Invalid tab_index {tab_index}")
            return
        tab_data = self.tabs_data[tab_index]
        chargen_widget = tab_data.get('_chargen_widget')
        output_widget = tab_data.get('output')
        if chargen_widget and output_widget:
            chargen_widget.setVisible(False)
            if hasattr(output_widget, 'container') and hasattr(output_widget.container, 'layout'):
                container_layout = output_widget.container.layout()
                if container_layout:
                    container_layout.removeWidget(chargen_widget)
            chargen_widget.setParent(None)
            chargen_widget.deleteLater()
            del tab_data['_chargen_widget']
        if hasattr(self, '_actor_name_to_file_cache'):
            self._actor_name_to_file_cache.clear()
        right_splitter = tab_data.get('right_splitter')
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if right_splitter and workflow_data_dir:
            from core.utils import _get_player_current_setting_name
            current_setting = _get_player_current_setting_name(workflow_data_dir)
            if current_setting:
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: right_splitter.update_setting_name(current_setting, workflow_data_dir))
        if hasattr(self, 'current_intro_sequence_index') and hasattr(self, 'intro_sequence'):
            self.current_intro_sequence_index += 1
            input_field = tab_data.get('input')
            if input_field:
                input_field.set_input_state('intro_streaming')
                input_field.set_intro_prompt("", False)
                try:
                    input_field.intro_enter_pressed.disconnect()
                except:
                    pass
                input_field.intro_enter_pressed.connect(
                    lambda emitted_idx: core.game_intro.handle_intro_sequence_continue(self, tab_index if emitted_idx == -1 else emitted_idx)
                )
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: core.game_intro.process_next_intro_sequence_item(self, tab_index))
        else:
            from core.game_intro import _finish_intro_to_normal_chat
            _finish_intro_to_normal_chat(self, tab_index)

    def setup_sounds(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load('sounds/sound.mp3')
            pygame.mixer.music.play()
            self.return1_sound = pygame.mixer.Sound('sounds/return1.mp3')
            self.return3_sound = pygame.mixer.Sound('sounds/message.mp3')
            self.add_rule_sound = pygame.mixer.Sound('sounds/AddRule.mp3')
            self.update_rule_sound = pygame.mixer.Sound('sounds/UpdateRule.mp3')
            self.delete_rule_sound = pygame.mixer.Sound('sounds/DeleteRule.mp3')
            self.splash_sound = pygame.mixer.Sound('sounds/SplashScreen.mp3')
            self.sort_sound = pygame.mixer.Sound('sounds/Sort.mp3')
            self.medium_click_sound = pygame.mixer.Sound('sounds/MediumClick.mp3')
            self.hover_message_sound = pygame.mixer.Sound('sounds/hoverMessage.mp3')
        except pygame.error as e:
            print(f"Pygame sound error: {e}. Sounds disabled.")
            self.return1_sound = None
            self.return3_sound = None
            self.add_rule_sound = None
            self.update_rule_sound = None
            self.delete_rule_sound = None
            self.splash_sound = None
            self.sort_sound = None
            self.medium_click_sound = None
            self.hover_message_sound = None
        except FileNotFoundError as e:
            print(f"Sound file not found: {e}. Sounds disabled.")
            self.return1_sound = None
            self.return3_sound = None
            self.add_rule_sound = None
            self.update_rule_sound = None
            self.delete_rule_sound = None
            self.splash_sound = None
            self.sort_sound = None
            self.medium_click_sound = None
            self.hover_message_sound = None

    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2) 
        main_container = QWidget()
        main_container.setObjectName("MainContainer")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(30)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 5, 0)
        self.options_button = QPushButton("⋮")
        self.options_button.setObjectName("OptionsButton")
        self.options_button.setFixedSize(24, 24)
        self.options_button.setFont(QFont('Consolas', 14, QFont.Bold))
        self.options_button.setToolTip("Open Theme and Settings Customizer")
        self.options_button.setFocusPolicy(Qt.NoFocus)
        self.options_button.clicked.connect(self.open_color_picker)
        def options_mouse_press(event):
            if hasattr(self, 'medium_click_sound') and self.medium_click_sound:
                try:
                    self.medium_click_sound.play()
                except Exception as e:
                    print(f"Error playing medium_click_sound: {e}")
            QPushButton.mousePressEvent(self.options_button, event)
        self.options_button.mousePressEvent = options_mouse_press
        title_bar_layout.addWidget(self.options_button)
        title_bar_layout.addStretch(1)
        title_label = QLabel("ChatBot RPG")
        title_label.setObjectName("TitleLabel")
        title_label.setFont(QFont('Consolas', 10, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        window_controls = QHBoxLayout()
        window_controls.setSpacing(5)
        window_controls.setContentsMargins(0, 0, 0, 0)
        minimize_button = QPushButton("—")
        minimize_button.setObjectName("MinimizeButton")
        minimize_button.setFixedSize(24, 24)
        minimize_button.setFocusPolicy(Qt.NoFocus)
        minimize_button.clicked.connect(self.showMinimized)
        self.maximize_button = QPushButton("□")
        self.maximize_button.setObjectName("MaximizeButton")
        self.maximize_button.setFixedSize(24, 24)
        self.maximize_button.setFocusPolicy(Qt.NoFocus)
        self.maximize_button.clicked.connect(self.toggle_maximize)
        close_button = QPushButton("×")
        close_button.setObjectName("CloseButton")
        close_button.setFixedSize(24, 24)
        close_button.setFocusPolicy(Qt.NoFocus)
        close_button.clicked.connect(self.close)
        window_controls.addWidget(minimize_button)
        window_controls.addWidget(self.maximize_button)
        window_controls.addWidget(close_button)
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch(1)
        title_bar_layout.addLayout(window_controls)
        main_layout.addWidget(title_bar)
        content_area = QWidget()
        content_area.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(10, 10, 10, 10)
        info_reset_layout = QHBoxLayout()
        self.save_button = QPushButton("SAVE")
        self.save_button.setObjectName("SaveButton")
        self.save_button.setFont(QFont('Consolas', 6))
        self.save_button.setToolTip("Save the current game state (context, variables, etc.)")
        self.save_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.save_button.setFocusPolicy(Qt.NoFocus)
        self.save_button.clicked.connect(lambda: save_game_state(self))
        def save_mouse_press(event):
            if hasattr(self, 'hover_message_sound') and self.hover_message_sound:
                try:
                    self.hover_message_sound.play()
                except Exception as e:
                    print(f"Error playing hover_message_sound: {e}")
            QPushButton.mousePressEvent(self.save_button, event)
        self.save_button.mousePressEvent = save_mouse_press
        info_reset_layout.addWidget(self.save_button)
        self.load_button = QPushButton("LOAD")
        self.load_button.setObjectName("LoadButton")
        self.load_button.setFont(QFont('Consolas', 6))
        self.load_button.setToolTip("Load a previously saved game state")
        self.load_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.load_button.setFocusPolicy(Qt.NoFocus)
        self.load_button.clicked.connect(self.load_game_state)
        def load_mouse_press(event):
            if hasattr(self, 'hover_message_sound') and self.hover_message_sound:
                try:
                    self.hover_message_sound.play()
                except Exception as e:
                    print(f"Error playing hover_message_sound: {e}")
            QPushButton.mousePressEvent(self.load_button, event)
        self.load_button.mousePressEvent = load_mouse_press
        info_reset_layout.addWidget(self.load_button)
        info_reset_layout.addStretch(1)
        self.reset_button = QPushButton("RESET")
        self.reset_button.setObjectName("ResetButton")
        self.reset_button.setFont(QFont('Consolas', 6))
        self.reset_button.setToolTip("Reset current workflow (conversation, notes, variables [except *], etc.)")
        self.reset_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.reset_button.setFocusPolicy(Qt.NoFocus)
        self.reset_button.clicked.connect(self.reset_current_tab)
        def reset_mouse_press(event):
            if hasattr(self, 'medium_click_sound') and self.medium_click_sound:
                try:
                    self.medium_click_sound.play()
                except Exception as e:
                    print(f"Error playing medium_click_sound: {e}")
            QPushButton.mousePressEvent(self.reset_button, event)
        self.reset_button.mousePressEvent = reset_mouse_press
        info_reset_layout.addWidget(self.reset_button)
        content_layout.addLayout(info_reset_layout)
        self.tab_widget = TabManagerWidget(self, self.current_applied_theme)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.add_tab_requested.connect(lambda: self.add_new_tab(theme_settings=get_default_tab_settings())) # Pass defaults
        self.tab_widget.remove_tab_requested.connect(lambda index: remove_tab(self, index))
        content_layout.addWidget(self.tab_widget)
        
        if hasattr(self, 'left_splitter') and self.left_splitter:
            self.left_splitter.mode_changed.connect(self._handle_left_splitter_mode_changed)
        main_layout.addWidget(content_area)
        layout.addWidget(main_container)
        self.setLayout(layout)

    def toggle_maximize(self):
        if self._is_maximized:
            self.showNormal()
            self.maximize_button.setText("□")
            self._is_maximized = False
        else:
            self.showMaximized()
            self.maximize_button.setText("❐")
            self._is_maximized = True
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resize_direction = self._get_resize_direction(event.pos())
            if self._resize_direction:
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
                event.accept()
            elif event.pos().y() < 30:
                self._drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            else:
                super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 30:
            self.toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
    
    def mouseMoveEvent(self, event):
        resize_dir = self._get_resize_direction(event.pos())
        if resize_dir and not self._is_maximized:
            if resize_dir in ["left", "right"]:
                self.setCursor(Qt.SizeHorCursor)
            elif resize_dir in ["top", "bottom"]:
                self.setCursor(Qt.SizeVerCursor)
            elif resize_dir in ["topleft", "bottomright"]:
                self.setCursor(Qt.SizeFDiagCursor)
            elif resize_dir in ["topright", "bottomleft"]:
                self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        if event.buttons() == Qt.LeftButton:
            if self._resize_direction and not self._is_maximized:
                self._do_resize(event.globalPos())
                event.accept()
            elif self._drag_position is not None:
                if not self._is_maximized:
                    self.move(event.globalPos() - self._drag_position)
                else:
                    self.showNormal()
                    self._is_maximized = False
                    self.maximize_button.setText("□")
                    new_pos = event.globalPos()
                    new_pos.setX(new_pos.x() - (self.width() // 2))
                    new_pos.setY(new_pos.y() - 15)
                    self.move(new_pos)
                    self._drag_position = QPoint(self.width() // 2, 15)
                event.accept()
            else:
                super().mouseMoveEvent(event)
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self._drag_position = None
        self._resize_direction = None
        super().mouseReleaseEvent(event)
    
    def _get_resize_direction(self, pos):
        if self._is_maximized:
            return None
        rect = self.rect()
        border = self._border_width
        if pos.x() <= border and pos.y() <= border:
            return "topleft"
        elif pos.x() >= rect.width() - border and pos.y() <= border:
            return "topright"
        elif pos.x() <= border and pos.y() >= rect.height() - border:
            return "bottomleft"
        elif pos.x() >= rect.width() - border and pos.y() >= rect.height() - border:
            return "bottomright"
        elif pos.y() <= border:
            return "top"
        elif pos.y() >= rect.height() - border:
            return "bottom"
        elif pos.x() <= border:
            return "left"
        elif pos.x() >= rect.width() - border:
            return "right"
        return None
    
    def _do_resize(self, global_pos):
        rect = self.geometry()
        if self._resize_direction == "right":
            rect.setRight(global_pos.x())
        elif self._resize_direction == "left":
            rect.setLeft(global_pos.x())
        elif self._resize_direction == "bottom":
            rect.setBottom(global_pos.y())
        elif self._resize_direction == "top":
            rect.setTop(global_pos.y())
        elif self._resize_direction == "topleft":
            rect.setTopLeft(global_pos)
        elif self._resize_direction == "topright":
            rect.setTopRight(global_pos)
        elif self._resize_direction == "bottomleft":
            rect.setBottomLeft(global_pos)
        elif self._resize_direction == "bottomright":
            rect.setBottomRight(global_pos)
        min_width = 320
        min_height = 240
        if rect.width() < min_width:
            if self._resize_direction in ["left", "topleft", "bottomleft"]:
                rect.setLeft(rect.right() - min_width)
            else:
                rect.setWidth(min_width)
        if rect.height() < min_height:
            if self._resize_direction in ["top", "topleft", "topright"]:
                rect.setTop(rect.bottom() - min_height)
            else:
                rect.setHeight(min_height)
        self.setGeometry(rect)

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().screenGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def _restore_window_geometry(self):
        settings = QSettings("ChatBotRPG", "ChatBotRPG")
        geometry = settings.value("geometry", None)
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(850, 1000)
            self.center()

    def on_tab_changed(self, index):
        previous_index = self.current_tab_index
        if previous_index != index and 0 <= previous_index < len(self.tabs_data):
            self._save_context_for_tab(previous_index)
            prev_tab_data = self.tabs_data[previous_index]
            if prev_tab_data and 'notes_manager_widget' in prev_tab_data and prev_tab_data['notes_manager_widget']:
                prev_tab_data['notes_manager_widget'].force_save()
            self._save_tab_settings(previous_index)
            if hasattr(self, 'timer_manager') and prev_tab_data:
                self.timer_manager.save_timer_state(prev_tab_data)
                self.timer_manager.stop_timers_for_tab(prev_tab_data)
            from core.tab_manager import save_tabs_state
            save_tabs_state(self)
            if prev_tab_data:
                chargen_widget = prev_tab_data.get('_chargen_widget')
                if chargen_widget:
                    chargen_widget.setVisible(False)
        elif previous_index == index:
            return
        if 0 <= index < len(self.tabs_data) and self.tabs_data[index]:
            tab_data = self.tabs_data[index]
            if tab_data.get('is_stub', False):
                from core.tab_manager import replace_stub_with_full_tab
                if not replace_stub_with_full_tab(self, index):
                    print(f"Failed to load full tab {index}")
                    return
        if 0 <= index < len(self.tabs_data):
            tab_data = self.tabs_data[index]
            if tab_data:
                 self.current_tab_index = index
                 if not tab_data.get('timer_rules_loaded', False):
                     self._load_timer_rules_for_tab(index)
                     tab_data['timer_rules_loaded'] = True
                 if hasattr(self, 'timer_manager'):
                     self.timer_manager.load_timer_state(tab_data)
                 self._apply_theme_for_tab(index)
                 crt_overlay = tab_data.get('crt_overlay')
                 if crt_overlay and crt_overlay.parent():
                     parent_widget = crt_overlay.parent()
                     current_size = parent_widget.size()
                     if current_size.width() > 0 and current_size.height() > 0:
                         crt_overlay.resize(current_size)
                         crt_overlay.raise_()
                 
                 current_input_field = tab_data.get('input')
                 top_splitter = tab_data.get('top_splitter')
                 tab_name_for_debug = tab_data.get('name', 'Unknown Tab')
                 is_actively_showing_intro = tab_data.get('_is_showing_intro', False)
                 if current_input_field:
                     if is_actively_showing_intro:
                         self._show_introduction(index) 
                     elif current_input_field._current_state == 'chargen':
                         chargen_widget = tab_data.get('_chargen_widget')
                         if chargen_widget:
                             chargen_widget.setVisible(True)
                     else:
                         current_input_field.set_input_state('normal')
                 if top_splitter: 
                     if is_actively_showing_intro:
                 
                         top_splitter.setVisible(False)
                     elif current_input_field and current_input_field._current_state == 'intro_streaming':
                 
                         top_splitter.setVisible(False)
                     elif current_input_field and current_input_field._current_state == 'chargen':
                 
                         top_splitter.setVisible(False)
                     else:
                         left_splitter = tab_data.get('left_splitter')
                         if left_splitter and hasattr(left_splitter, 'live_game_button'):
                             live_game_checked = left_splitter.live_game_button.isChecked()
                             if live_game_checked:
                                 output_widget = tab_data.get('output')
                                 has_ongoing_conversation = False
                                 if output_widget and hasattr(output_widget, 'get_message_roles'):
                                     message_roles = output_widget.get_message_roles()
                                     if message_roles:
                                         user_messages = [role for role in message_roles if role == 'user']
                                         assistant_messages = [role for role in message_roles if role == 'assistant']
                                         has_ongoing_conversation = len(user_messages) > 0 and len(assistant_messages) > 0
                                 top_splitter.setVisible(has_ongoing_conversation)
                             else:
                                 top_splitter.setVisible(False)
                         else:
                             top_splitter.setVisible(False)
                 right_splitter = tab_data.get('right_splitter')
                 left_splitter = tab_data.get('left_splitter')
                 if right_splitter:
                     if is_actively_showing_intro or (current_input_field and current_input_field._current_state == 'intro_streaming'):
                         right_splitter.setVisible(False)
                     elif left_splitter and hasattr(left_splitter, 'live_game_button'):
                         live_game_checked = left_splitter.live_game_button.isChecked()
                         right_splitter.setVisible(live_game_checked)
                     else:
                         right_splitter.setVisible(False)
                 
                 if current_input_field:
                     current_input_field.setFocus()
                 right_splitter_for_update = tab_data.get('right_splitter')
                 workflow_data_dir = tab_data.get('workflow_data_dir')
                 if (right_splitter_for_update and 
                     hasattr(right_splitter_for_update, 'update_setting_name') and 
                     callable(getattr(right_splitter_for_update, 'update_setting_name', None)) and 
                     workflow_data_dir):
                     try:
                         try:
                             current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                         except Exception as setting_name_error:
                             print(f"Error getting player current setting name: {setting_name_error}")
                             current_setting_name = "Unknown Setting"
                         try:
                             right_splitter_for_update.update_setting_name(current_setting_name, workflow_data_dir)
                             if not is_actively_showing_intro and not (current_input_field and current_input_field._current_state == 'intro_streaming'):
                                 if left_splitter and hasattr(left_splitter, 'live_game_button'):
                                     live_game_checked = left_splitter.live_game_button.isChecked()
                                     right_splitter_for_update.setVisible(live_game_checked)
                                 else:
                                     right_splitter_for_update.setVisible(False)
                         except Exception as update_error:
                             import traceback
                             traceback.print_exc()
                             if hasattr(right_splitter, 'setting_name_label'):
                                 right_splitter.setting_name_label.setText(f"Setting: {current_setting_name}")
                     except Exception as e:
                         print(f"Critical error in right splitter update section: {e}")
                         import traceback
                         traceback.print_exc()
                 elif not right_splitter:
                      print(f"Warning: right_splitter not found in tab_data for index {index}")
                 elif not workflow_data_dir:
                      print(f"Warning: workflow_data_dir not found in tab_data for index {index}, cannot determine setting name.")
                 self._update_turn_counter_display()
                 if 'notes_manager_widget' in tab_data and tab_data['notes_manager_widget']:
                    tab_data['notes_manager_widget'].load_notes()
            else:
                first_valid_index = next((i for i, data in enumerate(self.tabs_data) if data is not None), -1)
                if first_valid_index != -1:
                    self.current_tab_index = first_valid_index
                    self.tab_widget.setCurrentIndex(first_valid_index)
                    self._apply_theme_for_tab(self.current_tab_index)
                    recovered_tab_data = self.tabs_data[first_valid_index]
                    if recovered_tab_data:
                        right_splitter_recovery = recovered_tab_data.get('right_splitter')
                        left_splitter_recovery = recovered_tab_data.get('left_splitter')
                        workflow_data_dir = recovered_tab_data.get('workflow_data_dir')
                        if (right_splitter_recovery and 
                            hasattr(right_splitter_recovery, 'update_setting_name') and 
                            callable(getattr(right_splitter_recovery, 'update_setting_name', None)) and 
                            workflow_data_dir):
                             try:
                                 try:
                                     current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                                 except Exception as setting_name_error:
                                     print(f"Error getting player current setting name (recovery): {setting_name_error}")
                                     current_setting_name = "Unknown Setting"
                                 try:
                                     right_splitter_recovery.update_setting_name(current_setting_name, workflow_data_dir)
                                     if left_splitter_recovery and hasattr(left_splitter_recovery, 'live_game_button'):
                                         live_game_checked = left_splitter_recovery.live_game_button.isChecked()
                                         right_splitter_recovery.setVisible(live_game_checked)
                                     else:
                                         right_splitter_recovery.setVisible(False)
                                 except Exception as update_error:
                                     print(f"Error in update_setting_name method (recovery): {update_error}")
                                     import traceback
                                     traceback.print_exc()
                                     if hasattr(right_splitter, 'setting_name_label'):
                                         right_splitter.setting_name_label.setText(f"Setting: {current_setting_name}")
                             except Exception as e:
                                 print(f"Critical error in recovered tab's right splitter update: {e}")
                                 import traceback
                                 traceback.print_exc()
                    current_input_field = recovered_tab_data.get('input')
                    if current_input_field:
                        current_input_field.setFocus()
                    self._update_turn_counter_display()
                    if 'notes_manager_widget' in recovered_tab_data and recovered_tab_data['notes_manager_widget']:
                        recovered_tab_data['notes_manager_widget'].load_notes()
                else:
                     self.current_tab_index = -1
                     self._update_turn_counter_display()
        elif index >= len(self.tabs_data) and self.tab_widget.count() > len(self.tabs_data):
             if self.current_tab_index != -1 and 0 <= self.current_tab_index < len(self.tabs_data):
                 previous_tab_data = self.tabs_data[self.current_tab_index]
                 previous_input_field = previous_tab_data.get('input') if previous_tab_data else None
                 if previous_input_field:
                     print(f"Switching away from regular tab {self.current_tab_index}, setting focus to its input field.")
                     previous_input_field.setFocus()
        else:
            print(f"Warning: Invalid or unexpected tab index {index} on switch (tabs_data length: {len(self.tabs_data)}, widget count: {self.tab_widget.count()}). Setting internal index to -1.")
            any_right_splitter = None
            for data in self.tabs_data:
                 if data and data.get('right_splitter'):
                     any_right_splitter = data.get('right_splitter')
                     break
            if (any_right_splitter and 
                hasattr(any_right_splitter, 'update_setting_name') and 
                callable(getattr(any_right_splitter, 'update_setting_name', None))):
                try:
                    any_right_splitter.update_setting_name("--")
                    print("Cleared right splitter setting name as no valid tab is active.")
                except Exception as e:
                    print(f"Error clearing right splitter setting name: {e}")
                    import traceback
                    traceback.print_exc()
            self.current_tab_index = -1
            self._update_turn_counter_display()

    def get_current_tab_data(self):
        if 0 <= self.current_tab_index < len(self.tabs_data) and self.tabs_data[self.current_tab_index] is not None:
            return self.tabs_data[self.current_tab_index]
        return None

    def get_current_output_widget(self):
        data = self.get_current_tab_data()
        return data['output'] if data else None

    def get_current_context(self):
        data = self.get_current_tab_data()
        return data['context'] if data else []

    def get_current_log_file(self):
        data = self.get_current_tab_data()
        return data['log_file'] if data else None

    def load_conversation_for_tab(self, index):
        if not (0 <= index < len(self.tabs_data) and self.tabs_data[index] is not None):
             return
        tab_data = self.tabs_data[index]
        context_file = tab_data['context_file']
        output_widget = tab_data['output']
        output_widget.clear_messages()
        tab_data['context'] = []
        tab_data['_remembered_selected_message'] = None
        loaded_context = []
        try:
            if os.path.exists(context_file):
                with open(context_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                         parsed_content = json.loads(content)
                         if isinstance(parsed_content, list):
                             loaded_context = parsed_content
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {context_file}. Starting fresh.")
            loaded_context = []
        except Exception as e:
            print(f"Error loading context from {context_file}: {e}. Starting fresh.")
            loaded_context = []
        tab_data['context'] = loaded_context
        latest_scene_in_context = 1
        if loaded_context:
            try:
                latest_scene_in_context = max(msg.get('scene', 1) for msg in loaded_context)
            except ValueError:
                 latest_scene_in_context = 1
        if loaded_context:
            last_msg = loaded_context[-1]
            last_scene = last_msg.get('scene')
            if isinstance(last_scene, int) and last_scene >= 1:
                desired_scene = last_scene
            else:
                desired_scene = latest_scene_in_context
        else:
            desired_scene = 1
        tab_data['scene_number'] = desired_scene
        if loaded_context:
            for message_data in loaded_context:
                role = message_data.get('role')
                content = message_data.get('content')
                metadata = message_data.get('metadata', {})
                text_tag = metadata.get('text_tag', None)
                character_name = metadata.get('character_name', None)
                post_effects = metadata.get('post_effects', None)
                message_scene = message_data.get('scene', 1)

                if message_scene != desired_scene:
                    continue

                if role and isinstance(content, str):
                    output_widget.add_message(
                        role,
                        content,
                        immediate=True,
                        text_tag=text_tag,
                        scene_number=message_scene,
                        latest_scene_in_context=desired_scene,
                        character_name=character_name,
                        post_effects=post_effects
                    )
        output_widget._scroll_to_bottom()
        if loaded_context:
            last_message = loaded_context[-1]
            last_scene_from_msg = last_message.get('scene')
            if isinstance(last_scene_from_msg, int) and last_scene_from_msg >= 1:
                tab_data['scene_number'] = last_scene_from_msg
            else:
                tab_data['scene_number'] = latest_scene_in_context
        else:
            tab_data['scene_number'] = 1
        assistant_message_count = sum(1 for msg in loaded_context if msg.get('role') == 'assistant')
        tab_data['turn_count'] = assistant_message_count + 1
        if index == self.tab_widget.currentIndex():
            self._update_turn_counter_display()
        show_intro = not loaded_context
        tab_data['_is_showing_intro'] = show_intro
        current_scene_for_tab = tab_data.get('scene_number', 1)
        narrator_posted_in_current_scene_on_load = False
        if loaded_context:
            for message_data in loaded_context:
                msg_scene = message_data.get('scene', 1)
                msg_role = message_data.get('role')
                msg_char_name = message_data.get('metadata', {}).get('character_name')
                is_narrator_post = (msg_role == 'assistant' and 
                                    (msg_char_name == "Narrator" or not msg_char_name))

                if msg_scene == current_scene_for_tab and is_narrator_post:
                    narrator_posted_in_current_scene_on_load = True
                    break
        tab_data['_has_narrator_posted_this_scene'] = narrator_posted_in_current_scene_on_load
        top_splitter = tab_data.get('top_splitter')
        if show_intro:
            if top_splitter:
                top_splitter.setVisible(False)
            right_splitter = tab_data.get('right_splitter')
            if right_splitter:
                right_splitter.setVisible(False)
            self._show_introduction(index)
            if top_splitter:
                if top_splitter.isVisible():
                    print("Warning: Top splitter became visible during intro - hiding again")
                    top_splitter.setVisible(False)
            if right_splitter:
                if right_splitter.isVisible():
                    print("Warning: Right splitter became visible during intro - hiding again")
                    right_splitter.setVisible(False)
            if not top_splitter:
                print("Warning: Could not find top_splitter to hide for intro.")
            if not right_splitter:
                print("Warning: Could not find right_splitter to hide for intro.")
        elif tab_data.get('input'):
            input_field = tab_data.get('input')
            input_field.set_input_state('normal')
            if top_splitter:
                top_splitter.setVisible(True)
        if not tab_data.get('timer_rules_loaded', False):
            self._load_timer_rules_for_tab(index)
            tab_data['timer_rules_loaded'] = True
        if hasattr(self, 'timer_manager'):
            self.timer_manager.load_timer_state(tab_data)

    def request_save_for_current_tab(self):
        if not self._save_requested:
             self._save_requested = True
             self._save_timer.start(1000) 

    def _perform_save_active_tab(self):
        self._save_requested = False
        output_widget = self.get_current_output_widget()
        log_file = self.get_current_log_file()
        if not output_widget or not log_file:
            return
        current_content = output_widget.toHtml()
        try:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                 os.makedirs(log_dir)
            with open(log_file, "w", encoding="utf-8") as file:
                file.write(current_content)
        except IOError as e:
            print(f"Error saving log file {log_file}: {e}")
        except Exception as e:
            print(f"Unexpected error saving log file {log_file}: {e}")

    def _save_context_for_tab(self, index):
        if not (0 <= index < len(self.tabs_data) and self.tabs_data[index] is not None):
            return
        tab_data = self.tabs_data[index]
        context = tab_data['context']
        context_file = tab_data['context_file']
        if not context_file:
            print(f"Error: No context file path defined for tab index {index}")
            return
        try:
            context_dir = os.path.dirname(context_file)
            if context_dir and not os.path.exists(context_dir):
                 os.makedirs(context_dir)
            with open(context_file, "w", encoding="utf-8") as f:
                json.dump(context, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving context file {context_file}: {e}")
        except Exception as e:
            print(f"Unexpected error saving context file {context_file}: {e}")

    def on_enter_pressed(self):
        print("on_enter_pressed method called")
        try:
            tab_data = self.get_current_tab_data()
            if tab_data:
                if '_characters_to_exit_rules' in tab_data:
                    del tab_data['_characters_to_exit_rules']
                if '_narrator_to_exit_rules' in tab_data:
                    del tab_data['_narrator_to_exit_rules']
            if self.current_tab_index < 0 or self.current_tab_index >= len(self.tabs_data) or self.tabs_data[self.current_tab_index] is None:
                self.statusBar.showMessage("Error: No active tab. Please create a new tab first.", 5000)
                return
            tab_data = self.get_current_tab_data()
            input_field = tab_data['input'] if tab_data and 'input' in tab_data else None
            if not input_field:
                print("Error: Input field not found.")
                self.statusBar.showMessage("Error: Input field not found.", 5000)
                return
            output_widget = self.get_current_output_widget()
            if output_widget and hasattr(output_widget, 'force_complete_all_streaming'):
                streaming_was_forced = output_widget.force_complete_all_streaming()
            user_message = input_field.toPlainText().strip()
            if not user_message:
                print("Message was empty, not sending.")
                return
            input_field.clear()
            if tab_data:
                tab_data['turn_count'] += 1
            self._update_turn_counter_display()
            self._disable_input_for_pipeline()
            self._continue_message_processing(user_message)
        except Exception as e:
            self.statusBar.showMessage(f"Error processing message: {str(e)}", 5000)

    def _continue_message_processing(self, user_message):
        try:
            self._cot_text_tag = None
            if hasattr(self, '_character_tags'):
                self._character_tags.clear()
            if not user_message or not user_message.strip():
                return
            output_widget = self.get_current_output_widget()
            if output_widget and hasattr(output_widget, 'force_complete_all_streaming'):
                streaming_was_forced = output_widget.force_complete_all_streaming()
                if streaming_was_forced:
                    print("Forced completion of streaming message(s) before processing new message")
            if not self.character_name:
                self.character_name = "Narrator" 
            self.display_message("user", user_message, self.get_current_output_widget())
            tab_data = self.get_current_tab_data()
            prev_assistant_msg = ""
            current_context = self.get_current_context()
            current_scene_number = tab_data.get('scene_number', 1)
            if current_context:
                best_prev_assistant_msg = ""
                found_conversational_assistant_msg_in_current_scene = False
                for i in range(len(current_context) - 1, -1, -1):
                    msg = current_context[i]
                    if msg['role'] == 'user' and msg.get('scene', 1) == current_scene_number and msg['content'] == user_message:
                        continue
                    if msg.get('scene', 1) == current_scene_number and msg['role'] == 'assistant':
                        msg_turn = msg.get('metadata', {}).get('turn')
                        msg_char_name = msg.get('metadata', {}).get('character_name', '')
                        is_narrator_intro = (msg_turn == 1 and (msg_char_name == "Narrator" or not msg_char_name))
                        if not is_narrator_intro:
                            best_prev_assistant_msg = msg['content']
                            found_conversational_assistant_msg_in_current_scene = True
                            break
                        elif not best_prev_assistant_msg:
                            best_prev_assistant_msg = msg['content']
                if not found_conversational_assistant_msg_in_current_scene and current_scene_number > 1:
                    for i in range(len(current_context) - 1, -1, -1):
                        msg = current_context[i]
                        if msg.get('scene', 1) < current_scene_number and msg['role'] == 'assistant':
                            msg_turn = msg.get('metadata', {}).get('turn')
                            msg_char_name = msg.get('metadata', {}).get('character_name', '')
                            is_narrator_intro_prev_scene = (msg_turn == 1 and (msg_char_name == "Narrator" or not msg_char_name))
                            if not is_narrator_intro_prev_scene:
                                best_prev_assistant_msg = msg['content']
                                break
                            elif not best_prev_assistant_msg:
                                best_prev_assistant_msg = msg['content']
                prev_assistant_msg = best_prev_assistant_msg
            if self.inference_thread and self.inference_thread.isRunning():
                return
            output_widget = self.get_current_output_widget()
            current_context = self.get_current_context()
            if output_widget is None or current_context is None:
                return
            if not user_message:
                return
            if self.return1_sound: self.return1_sound.play()
            if hasattr(self, 'timer_manager') and tab_data:
                pass
            tab_data = self.get_current_tab_data()
            current_scene = tab_data.get('scene_number', 1) if tab_data else 1
            workflow_data_dir = tab_data.get('workflow_data_dir') if tab_data else None
            location = _get_player_current_setting_name(workflow_data_dir) if workflow_data_dir else None
            current_turn_for_metadata = tab_data.get('turn_count', 0)
            user_msg_obj = {"role": "user", "content": user_message, "scene": current_scene}
            if "metadata" not in user_msg_obj:
                user_msg_obj["metadata"] = {}
            user_msg_obj["metadata"]["turn"] = current_turn_for_metadata
            if location:
                user_msg_obj["metadata"]["location"] = location
            current_context.append(user_msg_obj)
            self._save_context_for_tab(self.current_tab_index)
            self._last_user_msg_for_post_rules = user_message
            if tab_data and 'thought_rules' in tab_data and tab_data['thought_rules']:
                self._cot_next_step = lambda: self._complete_message_processing(user_message)
                QTimer.singleShot(0, lambda: self._apply_chain_of_thought_rules_pre(user_message, prev_assistant_msg))
            else:
                self._processing_cot_rules = False
                QTimer.singleShot(0, lambda: self._complete_message_processing(user_message))
        except Exception as e:
            print(f"Error in _continue_message_processing: {str(e)}")
            self.statusBar.showMessage(f"Error processing message: {str(e)}", 5000)
            
    def _complete_message_processing(self, user_message):
        tab_data = self.get_current_tab_data()
        if tab_data is None:
            return
        update_time(self, tab_data)
        
        if hasattr(self, 'timer_manager') and tab_data:
            pass
        try:
            tab_data = self.get_current_tab_data()
            if not tab_data:
                return
            current_processing_character = "Narrator" 
            is_timer_triggered_action = ("INTERNAL_TIMER_" in user_message) or bool(tab_data.get('_timer_final_instruction'))
            if is_timer_triggered_action:
                if "INTERNAL_TIMER_NARRATOR_ACTION" in user_message:
                    current_processing_character = "Narrator"
                elif "INTERNAL_TIMER_ACTION_FOR_" in user_message:
                    try:
                        name_and_instruction_part = user_message.split("INTERNAL_TIMER_ACTION_FOR_", 1)[1]
                        char_name_candidate = ""
                        if '(' in name_and_instruction_part:
                            char_name_candidate = name_and_instruction_part.split('(', 1)[0].strip()
                        else:
                            char_name_candidate = name_and_instruction_part.strip()
                        char_name_candidate = char_name_candidate.replace('_', ' ')
                        if 3 < len(char_name_candidate) < 50: 
                            current_processing_character = char_name_candidate
                        else:
                            current_processing_character = "Narrator"
                    except Exception as e_marker_parse:
                        current_processing_character = "Narrator"
                elif tab_data.get('_timer_final_instruction') and current_processing_character == "Narrator":
                    pass
            self.character_name = current_processing_character 
            is_narrator_specific_timer_action = is_timer_triggered_action and self.character_name == "Narrator"
            if self.character_name == "Narrator" and not is_narrator_specific_timer_action:
                    is_timer_triggered = bool(
                        tab_data.get('_timer_final_instruction') or 
                        tab_data.get('_is_timer_narrator_action_active') or
                        tab_data.get('_last_timer_action_type')
                    )
                    
                    if not is_timer_triggered:
                        if '_last_timer_action_type' in tab_data:
                            tab_data.pop('_last_timer_action_type', None)
                        if '_last_timer_character' in tab_data:
                            tab_data.pop('_last_timer_character', None)
                    force_narrator_details = tab_data.get('force_narrator')
                    if force_narrator_details and force_narrator_details.get('active', False):
                        order = force_narrator_details.get('order')
                        fn_timestamp = force_narrator_details.get('_set_timestamp', 0)
                        current_time = time.time()
                        recently_set = (current_time - fn_timestamp) < 2.0
                        if order.lower() != 'last' and not recently_set:
                            if not tab_data.get('_is_force_narrator_first_active', False) or order.lower() != 'first':
                                force_narrator_details['active'] = False
                                if not force_narrator_details.get('system_message'):
                                    tab_data.pop('force_narrator', None)
            if self.inference_thread and self.inference_thread.isRunning():
                return
            output_widget = self.get_current_output_widget()
            current_context = self.get_current_context()
            tab_data = self.get_current_tab_data()
            if output_widget is None or current_context is None or tab_data is None:
                print("Error: No active tab selected or tab data missing for _complete_message_processing.")
                return
            if is_timer_triggered_action and "INTERNAL_TIMER_NARRATOR_ACTION" in user_message:
                self.character_name = "Narrator"
            context_for_llm = []
            final_system_prompt_content = ""
            forced_narrator_sys_msg = None
            is_current_call_force_narrator_first = False
            is_current_call_force_narrator_last = False
            if tab_data.get('force_narrator', {}).get('active', False) and \
                tab_data['force_narrator'].get('order') == 'First' and \
                tab_data.get('_is_force_narrator_first_active', False):
                is_current_call_force_narrator_first = True
                forced_narrator_sys_msg = tab_data['force_narrator'].get('system_message')
            elif tab_data.get('force_narrator', {}).get('active', False) and \
                tab_data['force_narrator'].get('order', '').lower() == 'last' and \
                self.character_name == "Narrator":
                is_current_call_force_narrator_last = True
                forced_narrator_sys_msg = tab_data['force_narrator'].get('system_message')
            if is_timer_triggered_action:
                if self.character_name == "Narrator":
                    base_sys = self.get_system_context()
                    base_sys += "\\nRemember, you are the Narrator. Describe events and environments, do not speak as or embody other characters."
                    final_system_prompt_content = base_sys
                    actor_specific_base = ""
                    workflow_data_dir_for_timer = tab_data.get('workflow_data_dir')
                    if workflow_data_dir_for_timer:
                        try:
                            from core.utils import _get_or_create_actor_data
                            actor_data, _ = _get_or_create_actor_data(self, workflow_data_dir_for_timer, self.character_name)
                            if actor_data:
                                actor_specific_base = actor_data.get('system_message', '')
                        except Exception as e:
                            print(f"[WARN] Could not get base system prompt for {self.character_name} during timer action: {e}")
                    final_system_prompt_content = actor_specific_base
            else:
                base_sys = self.get_system_context()
                if is_current_call_force_narrator_first and forced_narrator_sys_msg:
                    base_sys += f"\\n\\n{forced_narrator_sys_msg}" 
            
                elif is_current_call_force_narrator_last and forced_narrator_sys_msg:
                    base_sys += f"\\n\\n{forced_narrator_sys_msg}" 
            
                if self.character_name == "Narrator": 
                     base_sys += "\\nRemember, you are the Narrator, not an NPC. Describe events and environments objectively. Do not adopt a character's voice or perspective."
                final_system_prompt_content = base_sys
            if final_system_prompt_content:
                context_for_llm.append({"role": "system", "content": final_system_prompt_content})
            cot_modifications = getattr(self, '_cot_system_modifications', [])
            if is_timer_triggered_action and hasattr(self, '_timer_system_modifications'):
                for timer_mod in self._timer_system_modifications:
                    if timer_mod not in cot_modifications:
                        cot_modifications.append(timer_mod)
            first_mods = [mod for mod in cot_modifications if mod.get('system_message_position') == 'first']
            if first_mods and context_for_llm and context_for_llm[0].get('role') == 'system':
                current_system_content = context_for_llm[0]['content']
                for mod in first_mods:
                    action_text = mod.get('action', '')
                    position = mod.get('position', 'prepend')
                    if position == 'replace':
                        current_system_content = action_text
                    elif position == 'prepend':
                        if current_system_content:
                            current_system_content = action_text + "\n\n" + current_system_content
                        else:
                            current_system_content = action_text
                    elif position == 'append':
                        if current_system_content:
                            current_system_content = current_system_content + "\n\n" + action_text
                        else:
                            current_system_content = action_text
                context_for_llm[0]['content'] = current_system_content
            elif first_mods:
                system_content = ""
                for mod in first_mods:
                    action_text = mod.get('action', '')
                    if system_content:
                        system_content += "\n\n" + action_text
                    else:
                        system_content = action_text
                if system_content:
                    context_for_llm.insert(0, {"role": "system", "content": system_content})
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if self.character_name != "Narrator":
                acting_character_for_memory = self.character_name
                if acting_character_for_memory and workflow_data_dir:
                    try:
                        chars_in_scene = set()
                        if hasattr(self, 'get_character_names_in_scene_for_timers'):
                            scene_chars_list = self.get_character_names_in_scene_for_timers(tab_data)
                            chars_in_scene.update(s for s in scene_chars_list if s != acting_character_for_memory)
                        scenes_to_recall = 1
                        actor_data_mem_check, _ = _get_or_create_actor_data(self, workflow_data_dir, acting_character_for_memory)
                        if actor_data_mem_check and actor_data_mem_check.get('variables', {}).get('following', '').strip().lower() == 'player':
                            scenes_to_recall = 2
                        mem_summary = _get_follower_memories_for_context(self, workflow_data_dir, acting_character_for_memory, list(chars_in_scene), current_context, scenes_to_recall=scenes_to_recall)
                        if mem_summary:
                            context_for_llm.append({"role": "user", "content": mem_summary})
                    except Exception as e:
                        print(f"[WARN] Could not inject follower memory summary for {self.character_name}: {e}")
                    try:
                        from core.utils import _find_actor_file_path
                        npc_file_path = _find_actor_file_path(self, workflow_data_dir, acting_character_for_memory)
                        if npc_file_path:
                            npc_notes = get_npc_notes_from_character_file(npc_file_path)
                            if npc_notes:
                                formatted_notes = format_npc_notes_for_context(npc_notes, acting_character_for_memory)
                                if formatted_notes:
                                    context_for_llm.append({"role": "user", "content": formatted_notes})
                    except Exception as e:
                        print(f"[NPC NOTES] Error injecting notes for {acting_character_for_memory} in main inference: {e}")
            if workflow_data_dir:
                try:
                    player_name = _get_player_character_name(self, workflow_data_dir)
                    current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                    setting_info_msg_content = None
                    setting_file_path = None
                    if player_name and current_setting_name and current_setting_name != "Unknown Setting":
                        setting_file_path, is_session_specific = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, current_setting_name)
                        if setting_file_path:
                            setting_data = _load_json_safely(setting_file_path)
                            setting_desc = setting_data.get('description', '').strip()
                            visit_count = setting_data.get('player_visit_count', 0)
                            setting_info_msg_content = f"(The current setting of the scene is: {setting_desc}"
                            connections_dict = setting_data.get('connections', {})
                            if connections_dict:
                                conn_lines = [f"- {name}: {desc}" if desc else f"- {name}" for name, desc in connections_dict.items()]
                                if conn_lines:
                                    setting_info_msg_content += "\\\\nWays into and out of this scene and into other scenes are:\\\\n" + "\\\\n".join(conn_lines)
                            setting_info_msg_content += ")"
                            if is_session_specific and not is_timer_triggered_action :
                                new_visit_count = visit_count + 1
                                setting_data['player_visit_count'] = new_visit_count
                                _save_json_safely(setting_file_path, setting_data)
                    if setting_info_msg_content:
                        context_for_llm.append({"role": "user", "content": setting_info_msg_content})
                    current_scene = tab_data.get('scene_number', 1)
                    location_info = get_location_info_for_keywords(workflow_data_dir, setting_file_path)
                    is_narrator = self.character_name == "Narrator"
                    context_for_llm = inject_keywords_into_context(
                        context_for_llm, current_context, self.character_name, 
                        current_setting_name, location_info, workflow_data_dir, 
                        current_scene, is_narrator
                    )
                except Exception as e:
                    print(f"[WARN] Could not inject setting description as user message: {e}")
            history_to_add = []
            current_scene = tab_data.get('scene_number', 1)
            print(f"  Filtering history for {self.character_name}. Keeping messages from scene {current_scene}.")
            for msg in current_context:
                if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene:
                    content = msg['content']
                    if is_timer_triggered_action and "INTERNAL_TIMER_" in content and msg['role'] == 'user':
                        continue
                    if content and "Sorry, API error" in content:
                        continue
                    if (msg.get('role') == 'assistant'
                        and 'metadata' in msg
                        and msg['metadata'].get('character_name')):
                        char_name = msg['metadata']['character_name']
                        if content and not content.strip().startswith(f"{char_name}:"):
                            content = f"{char_name}: {content}"
                    history_to_add.append({"role": msg['role'], "content": content})
            context_for_llm.extend(history_to_add)
            if is_timer_triggered_action:
                has_player_user_message_this_scene = False
                for hist_msg in reversed(history_to_add):
                    if hist_msg.get('role') == 'user' and not hist_msg.get('content','').startswith('INTERNAL_TIMER_'):
                        has_player_user_message_this_scene = True
                        break
                if not has_player_user_message_this_scene:
                    context_for_llm.append({"role": "user", "content": "(A moment passes...)"})
            
            timer_instruction = tab_data.get('_timer_final_instruction')
            if timer_instruction:
                context_for_llm.append({"role": "user", "content": f"({timer_instruction})"})
        
            last_mods = [mod for mod in cot_modifications if mod.get('system_message_position') == 'last']
            for mod in last_mods:
                action_text = mod['action']
                context_for_llm.append({"role": "user", "content": action_text})
            model_to_use = self.get_current_model()
            if hasattr(self, '_cot_system_modifications') and self._cot_system_modifications:
                last_switch_model = None
                custom_temperature = None
                for mod in reversed(cot_modifications):
                    if mod.get('switch_model'):
                        last_switch_model = mod['switch_model']
                        if 'temperature' in mod and mod['temperature']:
                            try:
                                custom_temperature = float(mod['temperature'])
                                print(f"Using custom temperature {custom_temperature} from Switch Model action")
                            except (ValueError, TypeError):
                                print(f"Invalid temperature value in Switch Model action: {mod['temperature']}")
                        break
                if last_switch_model:
                    model_to_use = last_switch_model
            tab_data = self.get_current_tab_data()
            temperature_to_use = custom_temperature if 'custom_temperature' in locals() and custom_temperature is not None else self.get_current_temperature()
            is_narrator_timer_call = is_timer_triggered_action and self.character_name == "Narrator"
            should_suppress = False
            if not is_narrator_timer_call:
                if self.character_name == "Narrator": 
                    should_suppress = _should_suppress_narrator(self, tab_data)
            if should_suppress:
        
                self._narrator_streaming_lock = False
                if tab_data and self.character_name == "Narrator":
                    is_timer_triggered = bool(
                        tab_data.get('_timer_final_instruction') or 
                        tab_data.get('_is_timer_narrator_action_active') or
                        tab_data.get('_last_timer_action_type')
                    )
                    
                    if not is_timer_triggered:
                        tab_data.pop('_is_timer_narrator_action_active', None)
                QTimer.singleShot(0, lambda: _start_npc_inference_threads(self))
                return
            self.inference_thread = InferenceThread(
                context_for_llm,
                self.character_name,
                model_to_use,
                self.max_tokens,
                temperature_to_use
            )
            self.inference_thread.result_signal.connect(self.handle_assistant_message)
            self.inference_thread.error_signal.connect(self.handle_inference_error)
            self.inference_thread.finished.connect(self.on_inference_finished)
            self.inference_thread.start()
        except Exception as e:
            print(f"Error in _complete_message_processing: {str(e)}")
            import traceback
            traceback.print_exc()
            tab_data_on_error = self.get_current_tab_data()
            if tab_data_on_error and '_timer_final_instruction' in tab_data_on_error:
                is_timer_triggered = bool(
                    tab_data_on_error.get('_timer_final_instruction') or 
                    tab_data_on_error.get('_is_timer_narrator_action_active') or
                    tab_data_on_error.get('_last_timer_action_type')
                )
                if not is_timer_triggered:
                    del tab_data_on_error['_timer_final_instruction']
        tab_data = self.get_current_tab_data()
        if tab_data and 'right_splitter' in tab_data and isinstance(tab_data['context'], list):
            if len(tab_data['context']) == 1 and not tab_data['right_splitter'].isVisible():
                left_splitter = tab_data.get('left_splitter')
                if left_splitter and hasattr(left_splitter, 'live_game_button') and left_splitter.live_game_button.isChecked():
                    tab_data['right_splitter'].setVisible(True)
                output_field = tab_data.get('output')
                if output_field and hasattr(output_field, 'force_rewrap_all_messages'):
                    try:
                        QTimer.singleShot(200, output_field.force_rewrap_all_messages)
                        QTimer.singleShot(500, output_field.force_rewrap_all_messages)
                    except Exception as e:
                        print(f"Error forcing chat message rewrap on first right splitter show: {e}")

    def on_inference_finished(self):
        finishing_thread = self.sender()
        if not finishing_thread:
            return
        if finishing_thread == self.inference_thread:
            print(f"Narrator inference finished for tab {self.current_tab_index}.")
            self.inference_thread = None
            if finishing_thread:
                try:
                    finishing_thread.disconnect()
                except TypeError:
                    pass 
        else:
            pass

    def handle_inference_error(self, error_message):
        print(f"Error during inference for tab {self.current_tab_index}: {error_message}")
        tab_data = self.get_current_tab_data()
        if tab_data:
            update_time(self, tab_data)
        self.display_message('assistant', f"Sorry, an error occurred: {error_message}")
        if self.return3_sound: self.return3_sound.play()

    def handle_assistant_message(self, message, tried_fallback1=False, tried_fallback2=False, tried_fallback3=False):
        output_widget = self.get_current_output_widget()
        current_context = self.get_current_context()
        if output_widget is None or current_context is None:
            print("Error: No active tab selected or tab data missing.")
            return
        tab_data = self.get_current_tab_data()
        char_name = self.character_name if hasattr(self, 'character_name') else None
        if char_name and isinstance(message, str):
            prefix = f"{char_name}:"
            if message.strip().startswith(prefix):
                message = message.strip()[len(prefix):].lstrip()
        if isinstance(message, str):
            message = re.sub(r'<think>[\s\S]*?</think>', '', message, flags=re.IGNORECASE).strip()
        if not message.strip() or message.strip().lower().startswith("i'm sorry"):
            if not tried_fallback1:
                print("LLM refusal or empty response detected, retrying with fallback model 1...")
                if current_context and current_context[-1].get('role') == 'assistant':
                    current_context.pop()
                self.inference_thread = InferenceThread(
                    current_context,
                    self.character_name,
                    FALLBACK_MODEL_1,
                    self.max_tokens,
                    self.get_current_temperature()
                )
                self.inference_thread.result_signal.connect(lambda msg: self.handle_assistant_message(msg, tried_fallback1=True, tried_fallback2=False, tried_fallback3=False))
                self.inference_thread.error_signal.connect(self.handle_inference_error)
                self.inference_thread.finished.connect(self.on_inference_finished)
                self.inference_thread.start()
                return
            elif not tried_fallback2:
                print("Fallback model 1 also refused, retrying with fallback model 2...")
                if current_context and current_context[-1].get('role') == 'assistant':
                    current_context.pop()
                self.inference_thread = InferenceThread(
                    current_context,
                    self.character_name,
                    FALLBACK_MODEL_2,
                    self.max_tokens,
                    self.get_current_temperature()
                )
                self.inference_thread.result_signal.connect(lambda msg: self.handle_assistant_message(msg, tried_fallback1=True, tried_fallback2=True, tried_fallback3=False))
                self.inference_thread.error_signal.connect(self.handle_inference_error)
                self.inference_thread.finished.connect(self.on_inference_finished)
                self.inference_thread.start()
                return
            elif not tried_fallback3:
                print("Fallback model 2 also refused, retrying with fallback model 3...")
                if current_context and current_context[-1].get('role') == 'assistant':
                    current_context.pop()
                self.inference_thread = InferenceThread(
                    current_context,
                    self.character_name,
                    FALLBACK_MODEL_3,
                    self.max_tokens,
                    self.get_current_temperature()
                )
                self.inference_thread.result_signal.connect(lambda msg: self.handle_assistant_message(msg, tried_fallback1=True, tried_fallback2=True, tried_fallback3=True))
                self.inference_thread.error_signal.connect(self.handle_inference_error)
                self.inference_thread.finished.connect(self.on_inference_finished)
                self.inference_thread.start()
                return
        self._assistant_message_buffer = message
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data.get('_is_force_narrator_first_active', False):
            self._finalize_assistant_message()
        elif tab_data and 'thought_rules' in tab_data and tab_data['thought_rules']:
            self._cot_next_step = lambda: self._finalize_assistant_message()
            user_msg_for_post = self._last_user_msg_for_post_rules if self._last_user_msg_for_post_rules else ""
            QTimer.singleShot(0, lambda: self._apply_chain_of_thought_rules_post(user_msg_for_post, message))
        else:
            self._finalize_assistant_message()

    def _finalize_assistant_message(self):
        message = self._assistant_message_buffer
        if message is None:
            print("Error finalizing message: buffer is None.")
            return
        output_widget = self.get_current_output_widget()
        current_context = self.get_current_context()
        if output_widget is None or current_context is None:
            print("Error finalizing message: Tab data missing.")
            return
        tab_data = self.get_current_tab_data()
        if tab_data and '_HARD_SUPPRESS_ALL_EXCEPT' in tab_data:
            allowed_character = tab_data.get('_HARD_SUPPRESS_ALL_EXCEPT')
            if self.character_name != allowed_character:
                self._assistant_message_buffer = None
                return
        text_tag_to_use = getattr(self, '_cot_text_tag', None)
        is_fn_first_call = tab_data.pop('_is_force_narrator_first_active', False)
        if is_fn_first_call:
            fn_first_tag_value = tab_data.pop('_force_narrator_first_text_tag', None)
            if fn_first_tag_value is not None:
                text_tag_to_use = fn_first_tag_value
            if tab_data and 'force_narrator' in tab_data and \
               tab_data['force_narrator'].get('order') == 'First' and \
               tab_data['force_narrator'].get('active', False):
                tab_data['force_narrator']['active'] = False
                fn_entry = tab_data['force_narrator']
                if not fn_entry.get('system_message') and \
                   not fn_entry.get('defer_to_end', False) and \
                   not fn_entry.get('text_tag_for_first'):
                    tab_data.pop('force_narrator', None)
        should_display = True
        workflow_data_dir = None
        if tab_data:
            workflow_data_dir = tab_data.get('workflow_data_dir')
        is_timer_triggered = tab_data and bool(
            tab_data.get('_timer_final_instruction') or 
            tab_data.get('_is_timer_narrator_action_active') or
            tab_data.get('_last_timer_action_type')
        )
        if not is_timer_triggered and tab_data and '_timer_final_instruction' in tab_data:
            tab_data.pop('_timer_final_instruction', None)
        is_actually_a_timer_narrator_action = False
        if tab_data:
            is_actually_a_timer_narrator_action = tab_data.pop('_is_timer_narrator_action_active', False)
        if tab_data and 'force_narrator' in tab_data and tab_data['force_narrator'].get('active', False):
            if tab_data['force_narrator'].get('order', '').lower() != 'last':
                tab_data['force_narrator']['active'] = False
                fn_data = tab_data['force_narrator']
                if not fn_data.get('system_message') and \
                   not fn_data.get('text_tag_for_first') and \
                   not fn_data.get('defer_to_end'):
                    tab_data.pop('force_narrator', None)
        if self.character_name == "Narrator":
            self._narrator_streaming_lock = True
            if is_actually_a_timer_narrator_action:
                should_display = True
                tab_data['_suppress_npcs_for_one_turn'] = True
            elif is_fn_first_call:
                should_display = True
                if tab_data:
                    if not tab_data.get('_has_narrator_posted_this_scene', False):
                        tab_data['_has_narrator_posted_this_scene'] = True
            else:
                suppress_narrator = _should_suppress_narrator(self, tab_data)
                should_display = not suppress_narrator
        narrator_msg_widget = None
        if should_display:
            narrator_post_effects = {}
            if hasattr(self, '_narrator_post_effects'):
                narrator_post_effects = self._narrator_post_effects.copy()
            narrator_msg_widget = self.display_message('assistant', message, text_tag=text_tag_to_use, post_effects=narrator_post_effects)
            if self.return3_sound: self.return3_sound.play()
            message_obj = {"role": "assistant", "content": message}
            meta = {}
            if text_tag_to_use:
                meta["text_tag"] = text_tag_to_use
            if tab_data and self.character_name != "Narrator":
                meta["character_name"] = self.character_name
            if workflow_data_dir:
                location = _get_player_current_setting_name(workflow_data_dir)
                meta["location"] = location
            current_turn_for_metadata = 0
            if tab_data:
                current_turn_for_metadata = tab_data.get('turn_count', 0)
            meta["turn"] = current_turn_for_metadata
            if narrator_post_effects:
                meta["post_effects"] = narrator_post_effects
            if meta:
                message_obj["metadata"] = meta
            current_scene = tab_data.get('scene_number', 1) if tab_data else 1
            message_obj["scene"] = current_scene
            if workflow_data_dir:
                try:
                    tab_index = self.tabs_data.index(tab_data) if tab_data in self.tabs_data else -1
                    if tab_index >= 0:
                        variables = self._load_variables(tab_index)
                        game_datetime = variables.get('datetime')
                        if game_datetime:
                            if 'metadata' not in message_obj:
                                message_obj['metadata'] = {}
                            message_obj['metadata']['game_datetime'] = game_datetime
                except Exception as e:
                    print(f"Error adding game timestamp to message: {e}")
            
            if self.character_name == "Narrator" and tab_data:
                if tab_data.pop('_temp_is_first_npc_scene_post', False):
                    if not tab_data.get('_has_narrator_posted_this_scene', False):
                        tab_data['_has_narrator_posted_this_scene'] = True
            current_context.append(message_obj)
            self._save_context_for_tab(self.current_tab_index)
            if self.character_name != "Narrator" and workflow_data_dir:
                self._generate_and_save_npc_note_main(self.character_name, message, workflow_data_dir)
        else:
            if self.character_name == "Narrator":
                self._narrator_streaming_lock = False
        if tab_data:
            tab_data['turn_count'] += 1
        if hasattr(self, '_pending_update_top_splitter') and self._pending_update_top_splitter:
            update_top_splitter_location_text(self._pending_update_top_splitter)
            self._pending_update_top_splitter = None
        self._assistant_message_buffer = None
        self._last_user_msg_for_post_rules = None
        self._cot_text_tag = None

        def check_narrator_streaming_then_handle_npcs():
            theme_settings = tab_data.get('settings', {}) if tab_data else {}
            streaming_enabled = theme_settings.get("streaming_enabled", False)
            if not narrator_msg_widget or not streaming_enabled or not should_display:
                self._narrator_streaming_lock = False
                if tab_data and self.character_name == "Narrator":
                    force_narrator_details = tab_data.get('force_narrator', {})
                    if force_narrator_details.get('active') and \
                       force_narrator_details.get('order', '').lower() == 'last' and \
                       tab_data.get('_fn_last_npc_turn_done', False):
                        tab_data.pop('force_narrator', None)
                        tab_data.pop('_fn_last_npc_turn_done', None)
                        return
                _start_npc_inference_threads(self)
                _check_process_npc_queue(self)
                return
            try:
                if hasattr(narrator_msg_widget, 'is_streaming') and narrator_msg_widget.is_streaming():
                    QTimer.singleShot(200, check_narrator_streaming_then_handle_npcs)
                else:
                    def double_check_streaming_done():
                        try:
                            if hasattr(narrator_msg_widget, 'is_streaming') and narrator_msg_widget.is_streaming():
                                QTimer.singleShot(200, check_narrator_streaming_then_handle_npcs)
                            else:
                                def release_lock_and_check_queue():
                                    self._narrator_streaming_lock = False
                                    if tab_data and self.character_name == "Narrator":
                                        force_narrator_details = tab_data.get('force_narrator', {})
                                        if force_narrator_details.get('active') and \
                                           force_narrator_details.get('order', '').lower() == 'last' and \
                                           tab_data.get('_fn_last_npc_turn_done', False):
                                            was_fn_last_narrator_turn = True
                                            tab_data.pop('force_narrator', None)
                                            tab_data.pop('_fn_last_npc_turn_done', None)
                                            return 
                                    _start_npc_inference_threads(self)
                                    _check_process_npc_queue(self)
                                QTimer.singleShot(100, release_lock_and_check_queue)
                        except RuntimeError as e:
                            print(f"Warning: Error in double-check streaming state: {e}")
                            self._narrator_streaming_lock = False
                            def fallback_npc_processing():
                                if tab_data and self.character_name == "Narrator":
                                    force_narrator_details = tab_data.get('force_narrator', {})
                                    if force_narrator_details.get('active') and \
                                       force_narrator_details.get('order', '').lower() == 'last' and \
                                       tab_data.get('_fn_last_npc_turn_done', False):
                                        tab_data.pop('force_narrator', None)
                                        tab_data.pop('_fn_last_npc_turn_done', None)
                                        return
                                _start_npc_inference_threads(self)
                                _check_process_npc_queue(self)
                            QTimer.singleShot(100, fallback_npc_processing)
                    QTimer.singleShot(100, double_check_streaming_done)
            except RuntimeError as e:
                self._narrator_streaming_lock = False
                def fallback_npc_processing2():
                    current_tab_data = self.get_current_tab_data()
                    if current_tab_data and self.character_name == "Narrator":
                        force_narrator_details = current_tab_data.get('force_narrator', {})
                        if force_narrator_details.get('active') and \
                           force_narrator_details.get('order', '').lower() == 'last' and \
                           current_tab_data.get('_fn_last_npc_turn_done', False):
                            current_tab_data.pop('force_narrator', None)
                            current_tab_data.pop('_fn_last_npc_turn_done', None)
                            return
                    _start_npc_inference_threads(self)
                    _check_process_npc_queue(self)
                QTimer.singleShot(100, fallback_npc_processing2)
        if should_display and self.character_name == "Narrator":
            QTimer.singleShot(100, check_narrator_streaming_then_handle_npcs)
        else:
            if self.character_name == "Narrator":
                def process_npcs_immediately():
                    _start_npc_inference_threads(self)
                    _check_process_npc_queue(self)
                QTimer.singleShot(0, process_npcs_immediately)
        if tab_data and tab_data.get('_deferred_actor_reload'):
            deferred_setting = tab_data.pop('_deferred_actor_reload', None)
            if deferred_setting and workflow_data_dir:
                try:
                    from core.utils import reload_actors_for_setting
                    reload_actors_for_setting(workflow_data_dir, deferred_setting)
                except Exception as e:
                    print(f"[WARN] Deferred reload_actors_for_setting failed: {e}")
        if tab_data and tab_data.get('_pending_screen_effect_update'):
            print("  _finalize_assistant_message: Detected _pending_screen_effect_update.")
            if hasattr(self, '_update_screen_effects') and callable(self._update_screen_effects):
                self._update_screen_effects(tab_data)
                print("    Called _update_screen_effects.")
            else:
                print("    WARNING: _update_screen_effects not found or not callable on self.")
            tab_data['_pending_screen_effect_update'] = False
            print("    Reset _pending_screen_effect_update to False.")
        self._update_turn_counter_display()
        self.on_inference_finished()
        tab_data = self.get_current_tab_data()
        force_narrator_details = tab_data.get('force_narrator', {}) if tab_data else {}
        is_fn_last_active = force_narrator_details.get('active') and force_narrator_details.get('order', '').lower() == 'last'
        fn_last_npc_turn_done = tab_data.get('_fn_last_npc_turn_done', False) if tab_data else False
        if is_fn_last_active and fn_last_npc_turn_done and self.character_name == "Narrator":
    
            self._re_enable_input_after_pipeline()
            self._allow_live_input_for_current_action = False
        else:
            pass

    def _load_timer_rules_for_tab(self, tab_index):
        if tab_index < 0 or tab_index >= len(self.tabs_data):
            return []
        tab_data = self.tabs_data[tab_index]
        if not tab_data:
            return []
        if tab_data.get('timer_rules_loaded', False):
            return tab_data.get('timer_rules', [])
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            print(f"Error loading timer rules: No workflow_data_dir for tab {tab_index}")
            return []
        rules_dir = tab_data.get('rules_dir')
        if not rules_dir:
            print(f"Error loading timer rules: No rules_dir for tab {tab_index}")
            return []
        tab_data['timer_rules_loaded'] = True
        timer_rules = []
        try:
            timer_rules_file = os.path.join(workflow_data_dir, 'game', 'timer_rules.json')
            if os.path.exists(timer_rules_file):
                try:
                    with open(timer_rules_file, 'r', encoding='utf-8') as f:
                        file_rules = json.load(f)
                        if isinstance(file_rules, list):
                            timer_rules = file_rules
                except Exception as file_err:
                    print(f"Error loading timer rules from file: {file_err}")
            if not timer_rules:
                try:
                    from rules.timer_rules_manager import _load_timer_rules
                    timer_rules = _load_timer_rules(self, tab_index) or []
                except Exception as module_err:
                    print(f"Error loading timer rules from module: {module_err}")
        except Exception as e:
            print(f"Error during timer rules loading process: {e}")
        tab_data['timer_rules'] = timer_rules
        timer_rules_widget = tab_data.get('timer_rules_widget')
        if timer_rules_widget:
            timer_rules_widget.load_timer_rules(timer_rules)
        return timer_rules

    def on_utility_inference_finished(self):
        finishing_thread = self.utility_inference_thread
        if self.utility_inference_thread == finishing_thread:
            self.utility_inference_thread = None
        if finishing_thread:
            finishing_thread.disconnect()
            if finishing_thread.isRunning():
                finishing_thread.wait(100)
        save_tabs_state(self)
        self._update_turn_counter_display()

    def _apply_chain_of_thought_rules_pre(self, current_user_msg, prev_assistant_msg):
        if self.utility_inference_thread and self.utility_inference_thread.isRunning():
            QTimer.singleShot(200, lambda: self._apply_chain_of_thought_rules_pre(current_user_msg, prev_assistant_msg))
            return
        tab_data = self.get_current_tab_data()
        if not tab_data or 'thought_rules' not in tab_data or not tab_data['thought_rules']:
            if hasattr(self, '_cot_next_step') and self._cot_next_step:
                QTimer.singleShot(0, self._cot_next_step)
                self._cot_next_step = None
            return
        rules = tab_data['thought_rules']
        post_inference_scopes = ['llm_reply', 'convo_llm_reply']
        pre_rules = [rule for rule in rules if rule.get('scope') not in post_inference_scopes and rule.get('applies_to') != 'End of Round']
        if not pre_rules:
            if hasattr(self, '_cot_next_step') and self._cot_next_step:
                QTimer.singleShot(0, self._cot_next_step)
                self._cot_next_step = None
            return
        self._cot_rule_triggered_pre = False
        self._cot_sequential_index = 0
        tab_data = self.get_current_tab_data()
        is_timer_triggered = tab_data and bool(
            tab_data.get('_timer_final_instruction') or 
            tab_data.get('_is_timer_narrator_action_active') or
            tab_data.get('_last_timer_action_type')
        )
        if not is_timer_triggered:
            self._cot_system_modifications = []
        else:
            if hasattr(self, '_timer_system_modifications'):
                self._cot_system_modifications = self._timer_system_modifications.copy()
        from rules.rule_evaluator import _process_next_sequential_rule_pre
        _process_next_sequential_rule_pre(self, current_user_msg, prev_assistant_msg, pre_rules)

    def _apply_chain_of_thought_rules_post(self, current_user_msg, assistant_message):
        if self.utility_inference_thread and self.utility_inference_thread.isRunning():
            QTimer.singleShot(200, lambda: self._apply_chain_of_thought_rules_post(current_user_msg, assistant_message))
            return
        tab_data = self.get_current_tab_data()
        if not tab_data or 'thought_rules' not in tab_data or not tab_data['thought_rules']:
            if hasattr(self, '_cot_next_step') and self._cot_next_step:
                QTimer.singleShot(0, self._cot_next_step)
                self._cot_next_step = None
            return
        rules = tab_data['thought_rules']
        post_rules = [rule for rule in rules if rule.get('scope') in ['llm_reply', 'convo_llm_reply'] and rule.get('applies_to') != 'End of Round']
        if not post_rules:
            if hasattr(self, '_cot_next_step') and self._cot_next_step:
                QTimer.singleShot(0, self._cot_next_step)
                self._cot_next_step = None
            return
        self._cot_rule_triggered_post = False
        self._cot_sequential_index = 0
        self._process_next_sequential_rule_post(current_user_msg, assistant_message, post_rules)

    def _handle_rule_error(self, error, rule, rule_index, current_user_msg, prev_assistant_msg, rules, triggered_directly=False, is_post_phase=False, tried_fallback1=False, tried_fallback2=False, tried_fallback3=False, character_name_for_rule_context=None):
        self.on_utility_inference_finished()
        import traceback
        traceback.print_exc()
        is_char_post_phase_rule = is_post_phase and rule.get('applies_to') == 'Character'
        if is_char_post_phase_rule:
            if hasattr(self, '_character_llm_reply_rule_complete_callback') and self._character_llm_reply_rule_complete_callback:
                print(f"--- Calling character LLM reply completion callback after error. ---")
                QTimer.singleShot(0, self._character_llm_reply_rule_complete_callback)
        elif not triggered_directly and rule_index is not None:
            self._cot_sequential_index += 1
            from rules.rule_evaluator import _process_next_sequential_rule_pre, _process_next_sequential_rule_post
            callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
            QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules))
        elif triggered_directly:
            if hasattr(self, '_cot_next_step') and self._cot_next_step:
                QTimer.singleShot(0, self._cot_next_step)
                self._cot_next_step = None

    def display_message(self, role, content, output_widget=None, text_tag=None, character_name=None, post_effects=None):
        if output_widget is None:
            output_widget = self.get_current_output_widget()
        if output_widget:
            tab_data = self.get_current_tab_data()
            if not tab_data:
                 return None
            if tab_data.get('pending_scene_update', False) and role == 'assistant':
                output_widget.clear_messages()
                tab_data['pending_scene_update'] = False
            current_scene = tab_data.get('scene_number', 1)
            latest_scene_in_context = tab_data.get('scene_number', 1)
            name_for_widget = character_name if character_name is not None else self.character_name
            if role == 'user':
                name_for_widget = None
            message_widget = output_widget.add_message(
                role, 
                content, 
                text_tag=text_tag, 
                scene_number=current_scene, 
                latest_scene_in_context=latest_scene_in_context,
                character_name=name_for_widget,
                post_effects=post_effects
            )
            return message_widget
        else:
            print(f"ERROR: Cannot display message, output widget not found for role {role}.")
            return None

    def _format_code_blocks(self, html_message, border_color, text_color):
        def replace_code_style(match):
            code_content = match.group(1)
            return f'<pre><code style="display: block; border: 1px solid {border_color}; padding: 10px; background-color: black; color: {text_color}; font-family: Consolas; white-space: pre-wrap; word-wrap: break-word;">{code_content}</code></pre>'
        formatted_message = re.sub(r'<pre><code[^>]*>(.*?)</code></pre>', replace_code_style, html_message, flags=re.DOTALL | re.IGNORECASE)
        return formatted_message


    def get_current_model(self):
        tab_data = self.get_current_tab_data()
        if tab_data and 'settings' in tab_data and 'model' in tab_data['settings']:
            model_path = tab_data['settings'].get('model')
            if model_path:
                return model_path.strip()
        print(f"[WARN] Could not get model from tab {self.current_tab_index} settings, returning default: {get_default_model()}")
        return get_default_model()

    def get_current_cot_model(self):
        tab_data = self.get_current_tab_data()
        if tab_data and 'settings' in tab_data and 'cot_model' in tab_data['settings']:
            model_path = tab_data['settings'].get('cot_model')
            if model_path:
                return model_path.strip()
        print(f"[WARN] Could not get CoT model from tab {self.current_tab_index} settings, returning default: {get_default_cot_model()}")
        return get_default_cot_model()

    def get_current_temperature(self):
        tab_data = self.get_current_tab_data()
        if tab_data and 'settings' in tab_data and 'temperature' in tab_data['settings']:
            temp = tab_data['settings'].get('temperature')
            if temp is not None:
                return float(temp)
        return get_default_tab_settings().get('temperature', 0.5)

    def load_favorites(self):
        try:
            with open(FAVORITES_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_favorites(self):
        with open(FAVORITES_FILE, 'w') as f:
            json.dump(self.favorites, f, indent=4)

    def save_current_as_favorite(self):
        current_path = self.get_current_model()
        if not current_path:
            tab_data = self.get_current_tab_data()
            if not tab_data:
                 QMessageBox.warning(self, "Error", "No active tab found to get model path from.")
                 return
            else:
                 QMessageBox.warning(self, "Error", "Could not retrieve model path from current tab settings.")
                 return
        name, ok = QInputDialog.getText(
            self, 
            "Save Favorite Model",
            f"Enter a name for this model path:\n({current_path})",
            text=current_path.split('/')[-1]
        )
        if ok and name:
            self.favorites[name] = current_path
            self.save_favorites()
            QMessageBox.information(self, "Success", f"Saved model '{current_path}' as favorite '{name}'!")

    def delete_current_favorite(self):
        current = self.favorites_combo.currentText()
        if not current:
            return
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete '{current}' from favorites?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if current in self.favorites:
                del self.favorites[current]
                self.save_favorites()
                self.update_favorites_combo()
            else:
                 QMessageBox.warning(self, "Not Found", f"Favorite '{current}' not found.")

    def update_favorites_combo(self):
        current_text = self.favorites_combo.currentText()
        self.favorites_combo.clear()
        self.favorites_combo.addItems(self.favorites.keys())
        index = self.favorites_combo.findText(current_text)
        if index != -1:
            self.favorites_combo.setCurrentIndex(index)
        elif self.favorites:
             self.favorites_combo.setCurrentIndex(0)

    def configure_agent_strategies(self, tab_index):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
            return
        pass

    def run_quick_utility_check(self, prompt, max_tokens=10):
        context = [{"role": "user", "content": prompt}]
        try:
            return make_inference(
                context,
                prompt,
                self.character_name,
                self.get_current_model(),
                max_tokens,
                0.1,
                is_utility_call=True
            )
        except Exception as e:
            print(f"Quick utility check error: {e}")
            return "no"

    def save_system_context(self, tab_index, event=None):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
            print(f"Error: Cannot save system context for invalid tab index {tab_index}")
            if event:
                editor = self.tabs_data[tab_index].get('system_context_editor')
                if editor and hasattr(editor, 'focusOutEvent'):
                    QTextEdit.focusOutEvent(editor, event)
            return
        tab_data = self.tabs_data[tab_index]
        system_context_editor = tab_data.get('system_context_editor')
        system_context_file = tab_data.get('system_context_file')
        if not system_context_editor and 'start_conditions_manager_widget' in tab_data:
            system_context_editor = tab_data['start_conditions_manager_widget']
        if not system_context_editor or not system_context_file:
            print(f"Error: Missing system context editor or file path for tab {tab_index}")
            if event:
                if hasattr(system_context_editor, 'focusOutEvent'):
                    QTextEdit.focusOutEvent(system_context_editor, event)
            return
        try:
            context_dir = os.path.dirname(system_context_file)
            if context_dir and not os.path.exists(context_dir):
                os.makedirs(context_dir)
            if hasattr(system_context_editor, '_save_system_prompt'):
                system_context_editor._save_system_prompt()
            elif hasattr(system_context_editor, 'toPlainText'):
                system_context = system_context_editor.toPlainText()
                with open(system_context_file, 'w', encoding='utf-8') as f:
                    f.write(system_context)
            else:
                print(f"Error: system_context_editor has no recognized save method.")
            print(f"System context saved for tab {tab_index} to {system_context_file}")
        except Exception as e:
            print(f"Error saving system context: {e}")
        if event:
            if hasattr(system_context_editor, 'focusOutEvent'):
                QTextEdit.focusOutEvent(system_context_editor, event)

    def get_system_context(self, tab_index=None):
        if tab_index is None:
            tab_index = self.current_tab_index
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
            return ""
        tab_data = self.tabs_data[tab_index]
        system_context_file = tab_data.get('system_context_file')
        if not system_context_file or not os.path.exists(system_context_file):
            return ""
        try:
            with open(system_context_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading system context from file {system_context_file}: {e}")
            return ""

    def _update_rules_display(self, rules, rules_list):
        filter_input = rules_list.parent().findChild(QLineEdit, "RulesFilterInput")
        filter_text = filter_input.text().strip().lower() if filter_input else ""
        rules_list.clear()
        for rule in rules:
            rule_id = rule.get('id', 'unnamed')
            description = rule.get('description', '')
            display_text = f"ID: {rule_id}"
            if description:
                display_text += f" - {description}"
            if not filter_text or filter_text in rule_id.lower() or filter_text in description.lower():
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, rule)
                rules_list.addItem(item)
        tab_index = rules_list.property("tab_index")
        if tab_index is not None:
            self._update_rule_selectors(tab_index)

    def _update_rule_selectors(self, tab_index):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
            return
        tab_data = self.tabs_data[tab_index]
        if not tab_data.get('widget'):
            return
        tab_widget = tab_data['widget']
        rules = tab_data.get('thought_rules', [])
        rule_ids = ["None"]
        for rule in rules:
            if 'id' in rule and rule['id']:
                rule_ids.append(rule['id'])
        trigger_selector = tab_widget.findChild(QComboBox, "StartConditionSelector")
        if trigger_selector:
            current_start_text = trigger_selector.currentText()
            trigger_selector.clear()
            trigger_selector.addItem("None")
            trigger_selector.addItem("Always")
            trigger_selector.addItem("Turn")
            trigger_selector.addItem("Variable")
            for rule_id in rule_ids:
                if rule_id not in ["None", "Always"]:
                    trigger_selector.addItem(rule_id)
            start_index = trigger_selector.findText(current_start_text)
            if start_index >= 0:
                trigger_selector.setCurrentIndex(start_index)
        next_rule_selectors = tab_widget.findChildren(QComboBox, "NextRuleSelector")
        for i, selector in enumerate(next_rule_selectors):
            current_next_text = selector.currentText()
            selector.clear()
            for rule_id in rule_ids:
                selector.addItem(rule_id)
            next_index = selector.findText(current_next_text)
            if next_index >= 0:
                selector.setCurrentIndex(next_index)
            else:
                selector.setCurrentIndex(0) 

    def _clear_rule_form(self, tab_index):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
            print(f"Error clearing form: Invalid tab index {tab_index}")
            return
        tab_content = self.tabs_data[tab_index]['widget']
        if not tab_content:
            print("Error clearing form: Tab content widget not found")
            return
        rule_id_editor = tab_content.findChild(QLineEdit, "RuleIdEditor")
        description_editor = tab_content.findChild(QLineEdit, "RuleDescriptionEditor")
        condition_editor = tab_content.findChild(QTextEdit, "ConditionEditor")
        trigger_selector = tab_content.findChild(QComboBox, "StartConditionSelector")
        model_editor = tab_content.findChild(QLineEdit, "ModelEditor")
        last_exchange_radio = tab_content.findChild(QRadioButton, "LastExchangeRadio")
        full_convo_radio = tab_content.findChild(QRadioButton, "FullConversationRadio")
        user_message_radio = tab_content.findChild(QRadioButton, "UserMessageRadio")
        prepend_radio = tab_content.findChild(QRadioButton, "PrependRadio")
        append_radio = tab_content.findChild(QRadioButton, "AppendRadio")
        replace_radio = tab_content.findChild(QRadioButton, "ReplaceRadio")
        first_sysmsg_radio = tab_content.findChild(QRadioButton, "FirstSysMsgRadio")
        last_sysmsg_radio = tab_content.findChild(QRadioButton, "LastSysMsgRadio")
        add_rule_button = tab_content.findChild(QPushButton, f"add_rule_button_{tab_index}")
        rules_list = tab_content.findChild(QListWidget, "RulesList")
        if rule_id_editor: rule_id_editor.clear()
        if description_editor: description_editor.clear()
        if condition_editor: condition_editor.clear()
        if trigger_selector: trigger_selector.setCurrentIndex(trigger_selector.findText("None"))
        if model_editor: model_editor.clear()
        if last_exchange_radio: last_exchange_radio.setChecked(True)
        if full_convo_radio: full_convo_radio.setChecked(False)
        if user_message_radio: user_message_radio.setChecked(False)
        if prepend_radio: prepend_radio.setChecked(True)
        if append_radio: append_radio.setChecked(False)
        if replace_radio: replace_radio.setChecked(False)
        if first_sysmsg_radio: first_sysmsg_radio.setChecked(True)
        if last_sysmsg_radio: last_sysmsg_radio.setChecked(False)
        add_pair_button = None
        for btn in tab_content.findChildren(QPushButton):
            if "Add Tag/Action Pair" in btn.text():
                add_pair_button = btn
                break
        pairs_container = None
        scroll_areas = tab_content.findChildren(QScrollArea)
        for scroll_area in scroll_areas:
            container_widget = scroll_area.widget()
            if container_widget and container_widget.findChild(QTextEdit, "TagEditor"):
                pairs_container = container_widget
                break
        if pairs_container and pairs_container.layout():
            layout = pairs_container.layout()
            while layout.count() > 0:
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
            QApplication.processEvents()
        else:
            print("Warning: Could not find pairs container or layout to clear.")
        if add_pair_button:
            add_pair_button.click()
            print("Added one empty pair after clearing")
        else:
            print("Warning: Could not find Add Pair button.")
        if add_rule_button:
            add_rule_button.setText("Add Rule")
        if rules_list: 
            rules_list.clearSelection()
        tab_data = self.tabs_data[tab_index]
        turn_spinner = tab_data.get('turn_spinner')
        turn_spinner_label = tab_data.get('turn_spinner_label')
        if turn_spinner:
             turn_spinner.setValue(turn_spinner.minimum())
             turn_spinner.setVisible(False)
        if turn_spinner_label:
             turn_spinner_label.setVisible(False)
        variable_condition_widget = tab_content.findChild(QWidget, "VariableConditionWidget")
        if variable_condition_widget:
            variable_var_editor = variable_condition_widget.findChild(QLineEdit, "VariableCondVarEditor")
            variable_op_selector = variable_condition_widget.findChild(QComboBox, "VariableCondOpSelector")
            variable_val_editor = variable_condition_widget.findChild(QLineEdit, "VariableCondValEditor")
            if variable_var_editor: variable_var_editor.clear()
            if variable_op_selector: variable_op_selector.setCurrentIndex(0)
            if variable_val_editor: variable_val_editor.clear()
            variable_condition_widget.setVisible(False)
        if pairs_container and pairs_container.layout():
            layout = pairs_container.layout()
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    pair_widget = item.widget()
                    set_var_name_editor = pair_widget.findChild(QLineEdit, "SetVariableNameEditor")
                    set_var_value_editor = pair_widget.findChild(QLineEdit, "SetVariableValueEditor")
                    if set_var_name_editor: set_var_name_editor.clear()
                    if set_var_value_editor: set_var_value_editor.clear()


    def _evaluate_condition_row(self, tab_data, cond, current_turn, triggered_directly=False):
        ctype = cond.get('type', 'None')
        character_name = None
        if cond.get('applies_to') == 'Character' or ('variable_scope' in cond and cond.get('variable_scope') == 'Character') or ('var_scope' in cond and cond.get('var_scope') == 'Character'):
            character_name = cond.get('character_name')
            print(f"  Evaluating condition for character: {character_name}")
        if ctype == 'None':
            if triggered_directly:
                print(f"  Condition type is 'None' but rule was triggered directly. Treating as TRUE.")
                return True
            else:
                print(f"  Condition type is 'None' and rule was NOT triggered directly. Treating as FALSE.")
                return False
        elif ctype == 'Always':
             return True
        elif ctype == 'Turn':
            turn = cond.get('turn')
            operator = cond.get('operator', '==')
            try:
                target_turn = int(turn)
                print(f"  Evaluating Turn: Current={current_turn}, Op='{operator}', Target={target_turn}")
                if operator == '==':
                    result = current_turn == target_turn
                elif operator == '!=':
                    result = current_turn != target_turn
                elif operator == '>':
                    result = current_turn > target_turn
                elif operator == '<':
                    result = current_turn < target_turn
                elif operator == '>=':
                    result = current_turn >= target_turn
                elif operator == '<=':
                    result = current_turn <= target_turn
                else:
                    print(f"  Warning: Unknown operator '{operator}' for Turn condition. Evaluating as False.")
                    result = False
                print(f"    => {result}")
                return result
            except (ValueError, TypeError):
                print(f"  Warning: Invalid Turn value '{turn}'. Evaluating as False.")
                return False
        elif ctype == 'Variable':
            original_value = cond.get('value', '')
            substituted_value = self._substitute_placeholders_in_condition_value(original_value, tab_data, character_name)
            cond['value'] = substituted_value
            return self._evaluate_variable_condition(tab_data, cond, character_name)
        elif ctype == 'Scene Count':
            operator = cond.get('operator', '==')
            target_value = cond.get('value')
            if target_value is None:
                print(f"  Warning: Scene Count condition has no target value. Evaluating as False.")
                return False
            current_scene = tab_data.get('scene_number', 1)
            try:
                target_scene = int(target_value)
            except (ValueError, TypeError):
                print(f"  Warning: Scene Count target value '{target_value}' is not an integer. Evaluating as False.")
                return False
            print(f"  Evaluating Scene Count: Current={current_scene}, Op='{operator}', Target={target_scene}")
            if operator == '==':
                return current_scene == target_scene
            elif operator == '!=':
                return current_scene != target_scene
            elif operator == '>':
                return current_scene > target_scene
            elif operator == '<':
                return current_scene < target_scene
            elif operator == '>=':
                return current_scene >= target_scene
            elif operator == '<=':
                return current_scene <= target_scene
            else:
                print(f"  Warning: Unknown operator '{operator}' for Scene Count. Evaluating as False.")
                return False
        elif ctype in ['Setting', 'Location', 'Region', 'World']:
            target_name = cond.get('geography_name', '').strip().lower().replace(' ', '_')
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                print(f"  Warning: No workflow_data_dir in tab_data. Evaluating as False.")
                return False
            current_setting = _get_player_current_setting_name(workflow_data_dir)
            setting_file, _ = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, current_setting)
            current_location = current_region = current_world = None
            if setting_file and os.path.isfile(setting_file):
                parts = os.path.normpath(setting_file).split(os.sep)
                try:
                    idx = parts.index('settings')
                    current_world = parts[idx+1] if len(parts) > idx+1 else None
                    current_region = parts[idx+2] if len(parts) > idx+2 else None
                    current_location = parts[idx+3] if len(parts) > idx+3 else None
                except Exception as e:
                    print(f"  Warning: Could not parse world/region/location from setting file path: {setting_file} ({e})")
            def norm(x):
                return x.strip().lower().replace(' ', '_') if x else ''
            if ctype == 'Setting':
                result = norm(current_setting) == target_name
                print(f"  Evaluating Setting: Current='{current_setting}' Target='{cond.get('geography_name','')}' => {result}")
                return result
            elif ctype == 'Location':
                result = norm(current_location) == target_name
                print(f"  Evaluating Location: Current='{current_location}' Target='{cond.get('geography_name','')}' => {result}")
                return result
            elif ctype == 'Region':
                result = norm(current_region) == target_name
                print(f"  Evaluating Region: Current='{current_region}' Target='{cond.get('geography_name','')}' => {result}")
                return result
            elif ctype == 'World':
                result = norm(current_world) == target_name
                print(f"  Evaluating World: Current='{current_world}' Target='{cond.get('geography_name','')}' => {result}")
                return result
        print(f"  Warning: Unknown condition type '{ctype}'. Evaluating as False.") # Added warning
        return False


    def _handle_rule_result(self, result, rule, rule_index, current_user_msg, prev_assistant_msg, rules, triggered_directly=False, tried_fallback1=False, tried_fallback2=False, tried_fallback3=False, is_post_phase=False, character_name_for_rule_context=None):
        self.on_utility_inference_finished()
        tab_data = self.get_current_tab_data()
        if not tab_data:
            print("Error: No tab data in _handle_rule_result")
            return
        tag_action_pairs = rule.get('tag_action_pairs', [])
        result = result.strip()
        found_tag = False
        matched_pair = None
        for pair in tag_action_pairs:
            tag = pair.get('tag', '').strip()
            print(f"  Checking pair with tag: '{tag}'")
            if not tag:
                found_tag = True
                matched_pair = pair
                print(f"✓ FOUND TAG (empty tag): Automatically matched. LLM said: '{result}'")
                break
            elif tag.lower() == result.lower():
                found_tag = True
                matched_pair = pair
                print(f"✓ FOUND TAG (exact match): '{tag}' in LLM result: '{result}'")
                break
            elif result.lower().startswith(tag.lower()):
                found_tag = True
                matched_pair = pair
                print(f"✓ FOUND TAG (at start): '{tag}' in LLM result: '{result}'")
                break
            elif tag.lower() in result.lower():
                found_tag = True
                matched_pair = pair
                print(f"✓ FOUND TAG (contained): '{tag}' in LLM result: '{result}'")
                break
        if not found_tag:
            if (hasattr(self, '_character_llm_reply_rule_complete_callback') and 
                self._character_llm_reply_rule_complete_callback and
                rule.get('applies_to') == 'Character' and 
                character_name_for_rule_context):
                callback = self._character_llm_reply_rule_complete_callback
                self._character_llm_reply_rule_complete_callback = None
                QTimer.singleShot(0, callback)
                return
            if not triggered_directly and rule_index is not None:
                self._cot_sequential_index += 1
                callback = _process_next_sequential_rule_post if is_post_phase else _process_next_sequential_rule_pre
                QTimer.singleShot(0, lambda: callback(self, current_user_msg, prev_assistant_msg, rules))
            elif triggered_directly:
                if hasattr(self, '_cot_next_step') and self._cot_next_step:
                    QTimer.singleShot(0, self._cot_next_step)
                    self._cot_next_step = None
            return
        if found_tag and matched_pair:
            _apply_rule_actions_and_continue(self, matched_pair, rule, rule_index, current_user_msg, prev_assistant_msg, rules, triggered_directly, is_post_phase, character_name_for_rule_context=character_name_for_rule_context)
            if (hasattr(self, '_character_llm_reply_rule_complete_callback') and 
                self._character_llm_reply_rule_complete_callback and
                rule.get('applies_to') == 'Character' and 
                character_name_for_rule_context):
                callback = self._character_llm_reply_rule_complete_callback
                self._character_llm_reply_rule_complete_callback = None
                QTimer.singleShot(0, callback)
                return

    def _update_turn_counter_display(self):
        pass

    def reset_current_tab(self):
        tab_index = self.current_tab_index
        tab_data = self.get_current_tab_data()
        if not tab_data:
            QMessageBox.warning(self, "No Tab Selected", "Please select a workflow tab to reset.")
            return
        if hasattr(self, 'timer_manager'):
            self.timer_manager.stop_all_timers()
            print("  Reset: Stopped all timers from all tabs to prevent cross-session contamination")
        
        if hasattr(self, 'timer_manager'):
            self.timer_manager.stop_timers_for_tab(tab_data)
            tab_data['timer_rules_loaded'] = False
        
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if workflow_data_dir:
            gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
            gamestate = {}
            if os.path.exists(gamestate_path):
                try:
                    with open(gamestate_path, 'r', encoding='utf-8') as f:
                        gamestate = json.load(f)
                except Exception as e:
                    print(f"  Error reading gamestate.json for effects init: {e}")
            gamestate['effects'] = {
                "blur": {"enabled": False, "radius": 5, "animation_speed": 2000, "animate": False},
                "flicker": {"enabled": False, "intensity": 0.1, "frequency": 1000, "color": "white"},
                "static": {"enabled": False, "intensity": 0.05, "frequency": 200, "dot_size": 1},
                "darken_brighten": {"enabled": False, "factor": 1.0, "animation_speed": 2000, "animate": False}
            }
            try:
                with open(gamestate_path, 'w', encoding='utf-8') as f:
                    json.dump(gamestate, f, indent=2)
                print(f"  Ensured default screen effects structure in {os.path.basename(gamestate_path)}")
            except Exception as e:
                print(f"  Error writing gamestate.json after effects init: {e}")
        
        if workflow_data_dir:
            game_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
            game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
            try:
                if os.path.isdir(game_settings_dir):
                    shutil.rmtree(game_settings_dir)
                    print(f"  Removed directory: {game_settings_dir}")
                else:
                    print(f"  Directory not found, skipping removal: {game_settings_dir}")
            except Exception as e:
                print(f"  Error removing directory {game_settings_dir}: {e}")
            try:
                if os.path.isdir(game_actors_dir):
                    shutil.rmtree(game_actors_dir)
                    print(f"  Removed directory: {game_actors_dir}")
                else:
                    print(f"  Directory not found, skipping removal: {game_actors_dir}")
            except Exception as e:
                print(f"  Error removing directory {game_actors_dir}: {e}")
        output_widget = tab_data.get('output')
        context_file = tab_data.get('context_file')
        log_file = tab_data.get('log_file')
        if output_widget:
            output_widget.clear_messages()
        tab_data['context'] = []
        tab_data['turn_count'] = 1
        tab_data['scene_number'] = 1
        self._update_turn_counter_display()
        tab_data['_has_narrator_posted_this_scene'] = False
        tab_data['_remembered_selected_message'] = None
        
        if context_file:
            try:
                with open(context_file, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception as e:
                print(f"  Error clearing context file {context_file}: {e}")
        
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
                print(f"  Error clearing log file {log_file}: {e}")
        
        variables = self._load_variables(tab_index)
        if variables:
            keys_to_keep = {'introduction_checked', 'introduction_title', 'introduction_text', 'introduction_description', 'introduction_messages', 'introduction_sequence', 'origin'}
            persistent_variables = {k: v for k, v in variables.items() 
                                  if k.endswith('*') or k in keys_to_keep or k.startswith('introduction_')}
            removed_count = len(variables) - len(persistent_variables)
            self._save_variables(tab_index, persistent_variables)
        
        if variables.get('introduction_checked', False):
            if input_field := tab_data.get('input'):
                print("  Reset: Intro checked, setting input to DISABLED initially.")
                input_field.set_input_state("disabled")
            else:
                print("  Warning: Input field not found during reset.")
        
        if workflow_data_dir:
            if 'origin' in variables:
                reset_player_to_origin(workflow_data_dir)
            else:
                reset_player_to_origin(workflow_data_dir)
            from core.memory import cleanup_template_files_from_npc_notes
            cleanup_template_files_from_npc_notes(workflow_data_dir)
        import core.game_intro
        tab_data['context'] = []
        core.game_intro.show_introduction(self, tab_index)
        top_splitter = tab_data.get('top_splitter')
        if top_splitter:
            top_splitter.setVisible(False)
        right_splitter = tab_data.get('right_splitter')
        if right_splitter:
            right_splitter.setVisible(False)
        update_top_splitter_location_text(tab_data)
        right_splitter = tab_data.get('right_splitter')
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if right_splitter and workflow_data_dir:
            try:
                current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                right_splitter.update_setting_name(current_setting_name, workflow_data_dir)
                print(f"  Reset: Updated right splitter setting name to: {current_setting_name}")
            except Exception as e:
                print(f"  Reset: Error updating right splitter setting name: {e}")
        
        if hasattr(self, '_actor_name_to_file_cache'):
            self._actor_name_to_file_cache.clear()
        if hasattr(self, '_actor_name_to_actual_name'):
            self._actor_name_to_actual_name.clear()
        if hasattr(self, '_npc_message_queue'):
            self._npc_message_queue.clear()
        if hasattr(self, 'npc_inference_threads'):
            self.npc_inference_threads.clear()
        self._processing_npc_queue = False
        
        if tab_data is not None:
            if 'variables' in tab_data:
                tab_data['variables'] = {}
        
        tab_data['timer_rules_loaded'] = False
        if right_splitter:
            right_splitter.setVisible(False)

    def _load_variables(self, tab_index):
        return core.game_intro.load_variables(self, tab_index)

    def _save_variables(self, tab_index, variables_data):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
            print(f"Error saving variables: Invalid tab index {tab_index}")
            return
        tab_data = self.tabs_data[tab_index]
        variables_file = tab_data.get('variables_file')
        if not variables_file:
            print(f"Error: No variables file path defined for tab index {tab_index}")
            return
        try:
            variables_dir = os.path.dirname(variables_file)
            if variables_dir and not os.path.exists(variables_dir):
                os.makedirs(variables_dir)
            with open(variables_file, 'w', encoding='utf-8') as f:
                json.dump(variables_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving variables file {variables_file}: {e}")
        except Exception as e:
            print(f"Unexpected error saving variables file {variables_file}: {e}")

    def closeEvent(self, event):
        if hasattr(self, 'effects_check_timer') and self.effects_check_timer.isActive():
            self.effects_check_timer.stop()
        if hasattr(self, '_screen_effects'):
            for tab_effects in self._screen_effects.values():
                for effect in tab_effects.values():
                    if hasattr(effect, 'timer') and effect.timer.isActive():
                        effect.timer.stop()
                    if hasattr(effect, 'anim'):
                        try:
                            if effect.anim.state() == QPropertyAnimation.Running:
                                effect.anim.stop()
                        except Exception as e:
                            print(f"Error stopping animation: {e}")
        if hasattr(self, 'timer_manager'):
            for i in range(self.tab_widget.count() - 2):
                if i < len(self.tabs_data) and self.tabs_data[i] is not None:
                    tab_data = self.tabs_data[i]
            self.timer_manager.stop_all_timers()
        for i in range(self.tab_widget.count() - 2):
            if i < len(self.tabs_data) and self.tabs_data[i] is not None:
                tab_data = self.tabs_data[i]
                time_manager_widget = tab_data.get('time_manager_widget')
                if time_manager_widget and hasattr(time_manager_widget, 'save_state_on_shutdown'):
                    time_manager_widget.save_state_on_shutdown()
        print("Time state saved for all tabs")

        settings = QSettings("ChatBotRPG", "ChatBotRPG")
        settings.setValue("geometry", self.saveGeometry())
        save_tabs_state(self)
        print(f"Saving data for {self.tab_widget.count() - 2} regular tabs before closing...")
        for i in range(self.tab_widget.count() - 2):
            self._save_context_for_tab(i)
            tab_data = self.tabs_data[i]
            if tab_data:
                if 'notes_manager_widget' in tab_data and tab_data['notes_manager_widget']:
                    tab_data['notes_manager_widget'].force_save()
                if 'system_context_editor' in tab_data:
                    self.save_system_context(i)
                self._save_tab_settings(i)
        print("Attempting to delete deferred items...")
        if hasattr(self, 'files_to_delete_on_exit') and self.files_to_delete_on_exit:
            print(f"  Found {len(self.files_to_delete_on_exit)} file(s) scheduled for deletion:")
            for p in self.files_to_delete_on_exit: print(f"    - {p}")
            successful_deletes = 0
            failed_deletes = []
            for file_path in self.files_to_delete_on_exit:
                print(f"  Attempting to delete: {file_path}")
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"    Successfully deleted: {os.path.basename(file_path)}")
                        successful_deletes += 1
                    except OSError as del_err:
                        print(f"    ERROR deleting deferred file {os.path.basename(file_path)}: {del_err}")
                        failed_deletes.append(file_path)
                else:
                    print(f"    File already gone: {os.path.basename(file_path)}")
                    successful_deletes += 1
            if not failed_deletes:
                self.files_to_delete_on_exit = []
                print("Cleared deferred deletion list.")
            else:
                self.files_to_delete_on_exit = []
        else:
            print("  No files scheduled for deferred deletion.")
        super().closeEvent(event)

    def _evaluate_variable_condition(self, tab_data, variable_condition, character_name=None):
        variable_scope = variable_condition.get('variable_scope', 'Global') or variable_condition.get('var_scope', 'Global')
        variable = variable_condition.get('variable', '')
        operator = variable_condition.get('operator', '==')
        value = variable_condition.get('value', '')
        if not variable:
            return False
        variables = {}
        if variable_scope == "Character" and character_name:
            workflow_dir = tab_data.get('workflow_data_dir')
            if not workflow_dir:
                 return False
            actor_data, _ = _get_or_create_actor_data(self, workflow_dir, character_name)
            if actor_data and 'variables' in actor_data and isinstance(actor_data['variables'], dict):
                variables = actor_data['variables']
            else:
                variables = {}
        elif variable_scope == "Player":
            workflow_dir = tab_data.get('workflow_data_dir')
            if not workflow_dir:
                return False
            player_name = _get_player_character_name(self, workflow_dir)
            if not player_name:
                return False
            actor_data, actor_file_path = _get_or_create_actor_data(self, workflow_dir, player_name)
            if actor_file_path and os.path.exists(actor_file_path):
                try:
                    with open(actor_file_path, 'r', encoding='utf-8') as f:
                        fresh_actor_data = json.load(f)
                    if fresh_actor_data and 'variables' in fresh_actor_data and isinstance(fresh_actor_data['variables'], dict):
                        variables = fresh_actor_data['variables']
                        print(f"  Loaded variables for Player '{player_name}': {variables}")
                    else:
                        print(f"  No variables found in Player file for '{player_name}'.")
                        variables = {}
                except Exception as e:
                    print(f"  Error reading Player file for '{player_name}': {e}")
                    if actor_data and 'variables' in actor_data and isinstance(actor_data['variables'], dict):
                        variables = actor_data['variables']
                        print(f"  Loaded variables for Player '{player_name}' (fallback to cached): {variables}")
                    else:
                        print(f"  No variables found or defined for Player '{player_name}' (fallback).")
                        variables = {}
            else:
                print(f"  No Player file found for '{player_name}'.")
                variables = {}
        elif variable_scope == "Setting":
            workflow_dir = tab_data.get('workflow_data_dir')
            if not workflow_dir:
                return False
            try:
                from core.utils import _get_player_current_setting_name, _find_setting_file_by_name
            except ImportError as e:
                return False
            player_setting_name = _get_player_current_setting_name(workflow_dir)
            if not player_setting_name or player_setting_name == "Unknown Setting":
                return False
            session_settings_dir = os.path.join(workflow_dir, 'game', 'settings')
            found_setting_file = _find_setting_file_by_name(session_settings_dir, player_setting_name)
            if not found_setting_file:
                base_settings_dir = os.path.join(workflow_dir, 'resources', 'data files', 'settings')
                found_base_setting_file = _find_setting_file_by_name(base_settings_dir, player_setting_name)
                if found_base_setting_file:
                    rel_path = os.path.relpath(found_base_setting_file, base_settings_dir)
                    dest_path = os.path.join(session_settings_dir, rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    import shutil
                    try:
                        shutil.copy2(found_base_setting_file, dest_path)
                    except Exception as e:
                        return False
                    found_setting_file = dest_path
                else:
                    return False
            try:
                with open(found_setting_file, 'r', encoding='utf-8') as f:
                    setting_data = json.load(f)
                if 'variables' not in setting_data or not isinstance(setting_data['variables'], dict):
                    setting_data['variables'] = {}
                variables = setting_data['variables']
            except Exception as e:
                return False
        else:
            tab_index = self.tabs_data.index(tab_data) if tab_data in self.tabs_data else -1
            if tab_index < 0:
                return False
            variables_file = tab_data.get('variables_file')
            if os.path.exists(variables_file):
                try:
                    with open(variables_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            variables = json.loads(content)
                except Exception as e:
                    print(f"ERROR: Could not load variables: {e}")
        if operator == "exists":
            result = variable in variables
            return result
        elif operator == "not exists":
            result = variable not in variables
            return result
        var_val = variables.get(variable)
        if var_val is None:
            if operator == "!=":
                return True
            elif operator == "==":
                 is_target_none = value is None or value == ""
                 return is_target_none
            else:
                return False
        
        def smart_convert(val):
            if isinstance(val, (int, float)):
                return val
            if isinstance(val, str):
                val_stripped = val.strip()
                if val_stripped == "":
                    return val_stripped
                try:
                    if '.' not in val_stripped and val_stripped.lstrip('-').isdigit():
                        return int(val_stripped)
                    return float(val_stripped)
                except (ValueError, TypeError):
                    return val_stripped
            return val
        var_val_converted = smart_convert(var_val)
        value_converted = smart_convert(value)
        if operator == "==":
            if isinstance(var_val_converted, (int, float)) and isinstance(value_converted, (int, float)):
                result = var_val_converted == value_converted
                return result
            else:
                var_val_str = str(var_val_converted).strip().lower()
                value_str = str(value_converted).strip().lower()
                result = var_val_str == value_str
                return result
        elif operator == "!=":
            if isinstance(var_val_converted, (int, float)) and isinstance(value_converted, (int, float)):
                result = var_val_converted != value_converted
                return result
            else:
                var_val_str = str(var_val_converted).strip().lower()
                value_str = str(value_converted).strip().lower()
                result = var_val_str != value_str
                return result
        elif operator == ">":
            result = var_val_converted > value_converted if isinstance(var_val_converted, (int, float)) and isinstance(value_converted, (int, float)) else False
            return result
        elif operator == "<":
            result = var_val_converted < value_converted if isinstance(var_val_converted, (int, float)) and isinstance(value_converted, (int, float)) else False
            return result
        elif operator == ">=":
            result = var_val_converted >= value_converted if isinstance(var_val_converted, (int, float)) and isinstance(value_converted, (int, float)) else False
            return result
        elif operator == "<=":
            result = var_val_converted <= value_converted if isinstance(var_val_converted, (int, float)) and isinstance(value_converted, (int, float)) else False
            return result
        elif operator == "contains":
            result = str(value_converted).lower() in str(var_val_converted).lower()
            return result
        elif operator == "not contains":
            result = str(value_converted).lower() not in str(var_val_converted).lower()
            return result
        return False

    def try_num(self, x):
        try:
            return float(x)
        except (ValueError, TypeError):
            return x

    def _handle_rewrite_result(self, rewritten_message, next_rule_id_after_rewrite, original_rule_context):
        self.on_utility_inference_finished()
        self._assistant_message_buffer = rewritten_message
        character_name_for_next_rule = original_rule_context.get('character_name')
        if next_rule_id_after_rewrite and next_rule_id_after_rewrite != "None":
            tab_data = self.get_current_tab_data()
            if tab_data:
                all_rules_full_list = tab_data.get('thought_rules', [])
                next_rule_data = None
                for r_iter in all_rules_full_list:
                    if r_iter.get('id') == next_rule_id_after_rewrite:
                        next_rule_data = r_iter
                        break
                if next_rule_data:
                    next_rule_actor_name = None
                    if next_rule_data.get('applies_to') == 'Character':
                        next_rule_actor_name = next_rule_data.get('character_name', character_name_for_next_rule)
                    triggered_is_post_phase = next_rule_data.get('scope') == 'llm_reply'
                    QTimer.singleShot(0, lambda nr=next_rule_data, ar=all_rules_full_list, cm=self._last_user_msg_for_post_rules, pm=rewritten_message, ipp=triggered_is_post_phase, char_ctx=next_rule_actor_name:
                        _process_specific_rule(self, nr, cm, pm, ar, rule_index=None, triggered_directly=True, is_post_phase=ipp, character_name=char_ctx)
                    )
                    return
                else:
                    pass
        if hasattr(self, '_cot_next_step') and self._cot_next_step:
            QTimer.singleShot(0, self._cot_next_step)
            self._cot_next_step = None
        else:
            pass

    def _apply_theme_for_tab(self, tab_index):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index]):
            if self.current_applied_theme is None:
                 from core.add_tab import get_default_tab_settings
                 self.current_applied_theme = get_default_tab_settings()
                 update_ui_colors(self, self.current_applied_theme)
                 if hasattr(self, 'color_btn'):
                     self.color_btn.setStyleSheet(
                         f"background-color: {self.current_applied_theme['base_color']}; "
                         f"border: 2px solid {self.current_applied_theme['base_color']};"
                     )
            return
        tab_data = self.tabs_data[tab_index]
        theme_settings = tab_data.get('settings')
        if not theme_settings:
             from core.add_tab import get_default_tab_settings
             theme_settings = get_default_tab_settings()
             tab_data['settings'] = theme_settings
             self._save_tab_settings(tab_index)
        self.current_applied_theme = theme_settings
        update_ui_colors(self, theme_settings)
        if hasattr(self, 'left_splitter') and self.left_splitter:
            self.left_splitter.update_theme(theme_settings)
        right_splitter = tab_data.get('right_splitter')
        if right_splitter:
            right_splitter.update_theme(theme_settings)
        input_field = tab_data.get('input')
        if input_field and hasattr(input_field, 'update_theme'):
            input_field.update_theme(theme_settings)
        crt_overlay = tab_data.get('crt_overlay')
        if crt_overlay:
            crt_enabled = theme_settings.get("crt_enabled", True)
            crt_speed = theme_settings.get("crt_speed", 160)
            crt_overlay.setVisible(crt_enabled)
            crt_overlay.setInterval(crt_speed)
            if crt_enabled:
                pass
            else:
                pass
        else:
            print(f"Warning: Could not find crt_overlay in tab_data to update for index {tab_index}")

    def _save_tab_settings(self, tab_index):
        if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index]):
             print(f"Error saving settings: Invalid tab index {tab_index}")
             return
        tab_data = self.tabs_data[tab_index]
        settings_to_save = tab_data.get('settings')
        settings_file = tab_data.get('tab_settings_file')
        if not settings_to_save or not settings_file:
             print(f"Error: Cannot save settings for tab {tab_index}. Missing settings data or file path.")
             return
        try:
            existing_settings = {}
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    existing_settings = json.load(f)
            
            if not isinstance(existing_settings, dict):
                existing_settings = {}

            existing_settings.update(settings_to_save)

            settings_dir = os.path.dirname(settings_file)
            if settings_dir and not os.path.exists(settings_dir):
                 os.makedirs(settings_dir)
            with open(settings_file, 'w', encoding='utf-8') as f:
                 json.dump(existing_settings, f, indent=4)
        except IOError as e:
             print(f"Error saving settings file {settings_file}: {e}")
        except Exception as e:
             print(f"Unexpected error saving settings file {settings_file}: {e}")

    def open_color_picker(self):
        tab_data = self.get_current_tab_data()
        if not tab_data:
            QMessageBox.warning(self, "Error", "No active tab found to customize theme.")
            return
        current_tab_theme = tab_data.get('settings')
        if not current_tab_theme:
             QMessageBox.warning(self, "Error", "Could not load theme settings for the current tab.")
             return
        
        dialog = ThemeCustomizationDialog(self, current_tab_theme)
        if dialog.exec_() == QDialog.Accepted:
            new_theme_settings = dialog.get_theme()
            current_settings = tab_data.get('settings', {})
            existing_dev_notes = current_settings.get('dev_notes', '')
            tab_data['settings'] = new_theme_settings
            tab_data['settings']['dev_notes'] = existing_dev_notes
            self._save_tab_settings(self.current_tab_index)
            self._apply_theme_for_tab(self.current_tab_index)
            right_splitter = tab_data.get('right_splitter')
            if right_splitter:
                 right_splitter.update_theme(new_theme_settings)
            print("Tab-specific theme updated and applied.")

    def update_tab_name(self, index, new_name):
        if not (0 <= index < len(self.tabs_data) and self.tabs_data[index]):
            print(f"Error renaming tab: Invalid index {index}")
            return
        tab_data = self.tabs_data[index]
        old_name = tab_data['name']
        base_data_dir = "data"
        old_folder_path = ""
        if tab_data.get('tab_settings_file'):
             old_folder_path = os.path.dirname(tab_data['tab_settings_file'])
        if not old_folder_path or not os.path.exists(old_folder_path):
             print(f"Error renaming tab: Could not determine or find old folder path ('{old_folder_path}') for tab '{old_name}'")
             QMessageBox.critical(self, "Rename Error", f"Could not find the data folder for tab '{old_name}'. Rename aborted.")
             return
        sanitized_new_name = sanitize_folder_name(new_name)
        new_folder_path = os.path.join(base_data_dir, sanitized_new_name)
        if old_folder_path != new_folder_path and os.path.exists(new_folder_path):
            print(f"Error renaming tab: Target folder '{new_folder_path}' already exists.")
            QMessageBox.warning(self, "Rename Error", 
                              f"A folder named '{sanitized_new_name}' already exists. Please choose a different name.")
            return
        if old_folder_path != new_folder_path:
            try:
                os.rename(old_folder_path, new_folder_path)
                print(f"Successfully renamed folder.")
            except OSError as e:
                print(f"Error renaming folder: {e}")
                QMessageBox.critical(self, "Rename Error", f"Could not rename the data folder for tab '{old_name}'.\nError: {e}")
                return
        tab_data['name'] = new_name
        try:
            for key in ['log_file', 'tab_settings_file']:
                if key in tab_data and tab_data[key]:
                    old_basename = os.path.basename(tab_data[key])
                    tab_data[key] = os.path.join(new_folder_path, old_basename)
            game_folder_path = os.path.join(new_folder_path, "game")
            for key in ['notes_file', 'context_file', 'system_context_file', 'variables_file']:
                if key in tab_data and tab_data[key]:
                    old_basename = os.path.basename(tab_data[key])
                    tab_data[key] = os.path.join(game_folder_path, old_basename)
            if 'rules_dir' in tab_data and tab_data['rules_dir']:
                 tab_data['rules_dir'] = os.path.join(new_folder_path, "rules")
            if 'thought_rules_file' in tab_data and tab_data['thought_rules_file']:
                 old_tr_basename = os.path.basename(tab_data['thought_rules_file'])
                 if os.path.dirname(tab_data['thought_rules_file']) == old_folder_path:
                      tab_data['thought_rules_file'] = os.path.join(new_folder_path, old_tr_basename)
        except Exception as path_e:
             print(f"ERROR updating file paths in tab_data after rename: {path_e}")
             QMessageBox.critical(self, "Rename Error", f"Folder was renamed, but failed to update internal file paths.\\nPlease check console output and potentially restart.\\nError: {path_e}")
        self.tab_widget.setTabText(index, new_name)
        save_tabs_state(self)


    def _show_introduction(self, tab_index):
        core.game_intro.show_introduction(self, tab_index)

    def keyPressEvent(self, event):
        if core.game_intro.handle_keypress_for_intro(self, event):
            return
        try:
            from core.game_over import handle_keypress_for_game_over
            if handle_keypress_for_game_over(self, event):
                return
        except ImportError:
            pass
        
        super().keyPressEvent(event)

    def _handle_left_splitter_mode_changed(self, button_object_name):
        try:
            import pygame
            mixer_initialized = pygame.mixer.get_init()
            if not hasattr(self, '_eft_splitter_sound') or self._eft_splitter_sound is None:
                if not mixer_initialized:
                    pygame.mixer.init()
                    mixer_initialized_after_attempt = pygame.mixer.get_init()
                    if not mixer_initialized_after_attempt:
                        self._eft_splitter_sound = None
                        raise RuntimeError("Failed to initialize pygame.mixer")
                self._eft_splitter_sound = pygame.mixer.Sound('sounds/LeftSplitterSelection.mp3')
            if self._eft_splitter_sound:
                self._eft_splitter_sound.play()

        except Exception as e:
            print(f"[ERROR] Exception in _handle_left_splitter_mode_changed (sound part): {e}")
            self._eft_splitter_sound = None
        tab_data = self.get_current_tab_data()
        if not tab_data:
            return
        if button_object_name == "LiveGameButtonLeft":
            input_field = tab_data.get('input')
            top_splitter = tab_data.get('top_splitter')
            right_splitter = tab_data.get('right_splitter')
            if input_field and top_splitter:
                if getattr(input_field, '_current_state', None) == 'intro_streaming':
                    top_splitter.setVisible(False)
                    if right_splitter:
                        right_splitter.setVisible(False)
                else:
                    top_splitter.setVisible(True)
                    if right_splitter:
                        left_splitter = tab_data.get('left_splitter')
                        if left_splitter and hasattr(left_splitter, 'live_game_button'):
                            right_splitter.setVisible(left_splitter.live_game_button.isChecked())
                        else:
                            right_splitter.setVisible(False)

    def run_utility_inference_sync(self, context, model, max_tokens, temperature=0.7):
        print("--- [Context for Utility LLM (Sync)] ---")
        try:
            print(json.dumps(context, indent=2))
        except Exception as json_e:
            print(f"    (Could not json dump context: {json_e})")
            print(context)
        print("--- [End Context for Utility LLM (Sync)] ---")

        thread = UtilityInferenceThread(
            chatbot_ui_instance=self,
            context=context,
            model_identifier=model, 
            max_tokens=max_tokens,
            temperature=temperature
        )
        loop = QEventLoop()
        thread.finished.connect(loop.quit)
        thread.start()
        loop.exec_()
        if thread.error_message:
            return None 
        return thread.result_data

    def _make_api_call_sync(self, api_key, base_url, model_name, messages, max_tokens, temperature):
        current_service = get_current_service()
        
        if current_service == "google":
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                
                formatted_messages = []
                for msg in messages:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    
                    if role == 'system':
                        formatted_messages.append(genai.types.Content(role='user', parts=[genai.types.Part(text=f"[SYSTEM] {content}")]))
                    elif role == 'user':
                        formatted_messages.append(genai.types.Content(role='user', parts=[genai.types.Part(text=content)]))
                    elif role == 'assistant':
                        formatted_messages.append(genai.types.Content(role='model', parts=[genai.types.Part(text=content)]))
                
                converted_model_name = model_name[7:] if model_name.startswith("google/") else model_name
                
                config = genai.types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.95
                )
                
                response = client.models.generate_content(
                    model=converted_model_name,
                    contents=formatted_messages,
                    config=config
                )
                
                if response and response.candidates:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        return candidate.content.parts[0].text
                
                return ""
            except ImportError:
                print("[ERROR] google-genai package not installed. Please install it with 'pip install google-genai'")
                return None
            except Exception as e:
                print(f"[ERROR] Google GenAI synchronous request failed: {e}")
                return None
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if current_service == "openrouter":
            headers["Authorization"] = f"Bearer {api_key}"
            headers["HTTP-Referer"] = "https://github.com/your-repo/your-project"
            headers["X-Title"] = "ChatBot RPG"
        elif current_service == "local":
            if api_key and api_key != "local":
                headers["Authorization"] = f"Bearer {api_key}"
        
        data = {
             "model": model_name,
             "messages": messages,
             "max_tokens": max_tokens,
             "temperature": temperature,
             "top_p": 0.95,
        }
        base_url_clean = base_url
        if base_url_clean.endswith('/'):
            base_url_clean = base_url_clean.rstrip('/')
        actual_url = f"{base_url_clean}/chat/completions"
        try:
            import requests 
            response = requests.post(actual_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            response_data = response.json()
            choices = response_data.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                return message.get('content', '')
            return ""
        except ImportError:
             print("[ERROR] `requests` library not installed. Cannot make synchronous API call.")
             return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Synchronous API request failed: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to process synchronous API response: {e}")
            return None

    def _process_next_sequential_rule_post(self, current_user_msg, assistant_msg, rules):
        tab_data = self.get_current_tab_data()
        if not tab_data or 'thought_rules' not in tab_data:
            print("Error in _process_next_sequential_rule_post: Tab data or rules missing.")
            if hasattr(self, '_cot_next_step') and self._cot_next_step:
                QTimer.singleShot(0, self._cot_next_step)
                self._cot_next_step = None
            return
        rule_index = self._cot_sequential_index
        if rule_index >= len(rules):
            print("Finished processing all POST-inference sequential rules.")
            if hasattr(self, '_cot_next_step') and self._cot_next_step:
                QTimer.singleShot(0, self._cot_next_step)
                self._cot_next_step = None
            return
        rule = rules[rule_index]
        applies_to = rule.get('applies_to', 'Narrator')
        scope = rule.get('scope')
        if applies_to != 'Narrator' or scope != 'llm_reply':
            self._cot_sequential_index += 1
            QTimer.singleShot(0, lambda: self._process_next_sequential_rule_post(current_user_msg, assistant_msg, rules))
            return
        conditions = rule.get('conditions', [])
        operator = rule.get('conditions_operator', 'AND')
        current_turn = tab_data.get('turn_count', 1)
        should_process = False
        if conditions:
            should_process = _evaluate_conditions(self, tab_data, conditions, operator, current_turn)
        if should_process:
            _process_specific_rule(self, rule, current_user_msg, assistant_msg, rules, rule_index, triggered_directly=False, is_post_phase=True)
        else:
            self._cot_sequential_index += 1
            QTimer.singleShot(0, lambda: self._process_next_sequential_rule_post(current_user_msg, assistant_msg, rules))

    def _handle_timer_fired(self, timer_instance, rule_data, tab_data):
        current_tab_data = self.get_current_tab_data()
        if current_tab_data != tab_data:
            return
        current_tab_id = str(current_tab_data.get('id', '')) if current_tab_data else ''
        timer_tab_id = str(tab_data.get('id', '')) if tab_data else ''
        if current_tab_id and timer_tab_id and current_tab_id != timer_tab_id:
            return
        actions = rule_data.get('actions', [])
        if not actions:
            return
        self._execute_timer_actions_sequentially(rule_data, actions, 0, timer_instance.character, tab_data)
    
    def _execute_timer_actions_sequentially(self, rule_data, actions, index, character_name, tab_data):
        if index >= len(actions):
            return
        action = actions[index]
        try:
            execute_timer_action(self, rule_data, action, character_name, tab_data)
            delay_ms = 50
            QTimer.singleShot(
                delay_ms, 
                lambda: self._execute_timer_actions_sequentially(rule_data, actions, index+1, character_name, tab_data)
            )
        except Exception as e:
            QTimer.singleShot(
                50,
                lambda: self._execute_timer_actions_sequentially(rule_data, actions, index+1, character_name, tab_data)
            )

    def get_character_names_in_scene_for_timers(self, tab_data):
        if not tab_data:
            return []
        workflow_data_dir = tab_data.get('workflow_data_dir')
        if not workflow_data_dir:
            return []
        player_character_name = _get_player_character_name(self, workflow_data_dir)
        current_setting_name = _get_player_current_setting_name(workflow_data_dir)
        if not current_setting_name or current_setting_name == "Unknown Setting":
            return []
        setting_file_path, _ = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, current_setting_name)
        if not setting_file_path or not os.path.exists(setting_file_path):
            return []
        try:
            setting_data = _load_json_safely(setting_file_path)
            characters_in_setting = setting_data.get('characters', [])
            npc_names = [name for name in characters_in_setting if isinstance(name, str) and name != player_character_name]
            return npc_names
        except Exception as e:
            return []

    def load_game_state(self, index=None):
        from core.utils import load_game_state as original_load_game_state
        result = original_load_game_state(self)
        if index is None:
            index = self.current_tab_index
        if 0 <= index < len(self.tabs_data) and self.tabs_data[index]:
            self._update_screen_effects(self.tabs_data[index])
        return result

    def start_effects_check_timer(self):
        self.effects_check_timer = QTimer()
        self.effects_check_timer.timeout.connect(self._check_effects_updates)
        self.effects_check_timer.start(5000)
        
    def _check_effects_updates(self):
        tab_data = self.get_current_tab_data()
        if tab_data and tab_data.get('loaded', True):
            try:
                self._update_screen_effects(tab_data)
            except RuntimeError as e:
                if "deleted" in str(e):
                    tab_index = self.tabs_data.index(tab_data) if tab_data in self.tabs_data else -1
                    if tab_index >= 0 and tab_index in self._screen_effects:
                        del self._screen_effects[tab_index]
                else:
                    print(f"Screen effects error: {e}")
            except Exception as e:
                print(f"Screen effects error: {e}")

    def _update_screen_effects(self, tab_data):
        if not tab_data:
            return
        tab_index = self.tabs_data.index(tab_data) if tab_data in self.tabs_data else -1
        if tab_index < 0:
            return
        effects_config = load_effects_from_gamestate(tab_data)
        if tab_index not in self._screen_effects:
            self._screen_effects[tab_index] = {}
        def get_target_widget():
            content_widget = tab_data.get('widget')
            if not content_widget:
                print(f"Warning: Could not find content_widget for tab {tab_index} to apply effects.")
            return content_widget
        if not effects_config:
            for effect_type, effect_instance in self._screen_effects.get(tab_index, {}).items():
                if hasattr(effect_instance, 'set_config'):
                    effect_instance.set_config(enabled=False)
            return
        blur_config = effects_config.get('blur', {})
        target_widget = get_target_widget()
        if 'blur' not in self._screen_effects[tab_index] and target_widget:
            self._screen_effects[tab_index]['blur'] = BlurEffect(target_widget)
        if 'blur' in self._screen_effects[tab_index]:
            self._screen_effects[tab_index]['blur'].set_config(
                enabled=blur_config.get('enabled', False),
                radius=blur_config.get('radius', 5),
                animation_speed=blur_config.get('animation_speed', 2000),
                animate=blur_config.get('animate', True)
            )
        flicker_config = effects_config.get('flicker', {})
        if 'flicker' not in self._screen_effects[tab_index] and target_widget:
             self._screen_effects[tab_index]['flicker'] = FlickerEffect(target_widget)
        if 'flicker' in self._screen_effects[tab_index]:
            self._screen_effects[tab_index]['flicker'].set_config(
                enabled=flicker_config.get('enabled', False),
                intensity=flicker_config.get('intensity', 0.3),
                frequency=flicker_config.get('frequency', 500),
                color_mode=flicker_config.get('color', 'white')
            )
        static_config = effects_config.get('static', {})
        if 'static' not in self._screen_effects[tab_index] and target_widget:
            self._screen_effects[tab_index]['static'] = StaticNoiseEffect(target_widget)
        if 'static' in self._screen_effects[tab_index]:
            self._screen_effects[tab_index]['static'].set_config(
                enabled=static_config.get('enabled', False),
                intensity=static_config.get('intensity', 0.2),
                frequency=static_config.get('frequency', 100),
                dot_size=static_config.get('dot_size', 3)
            )
        darken_brighten_config = effects_config.get('darken_brighten', {})
        if 'darken_brighten' not in self._screen_effects[tab_index] and target_widget:
            self._screen_effects[tab_index]['darken_brighten'] = DarkenBrightenEffect(target_widget)
        if 'darken_brighten' in self._screen_effects[tab_index]:
            self._screen_effects[tab_index]['darken_brighten'].set_config(
                enabled=darken_brighten_config.get('enabled', False),
                factor=darken_brighten_config.get('factor', 1.0),
                animate=darken_brighten_config.get('animate', False),
                animation_speed=darken_brighten_config.get('animation_speed', 2000)
            )

    def _substitute_variables_in_string(self, text_to_process, tab_data, actor_name_context=None):
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
        if '(character)' in result_text and actor_name_context:
            result_text = result_text.replace('(character)', actor_name_context)
        if '(player)' in result_text:
            workflow_data_dir = tab_data.get('workflow_data_dir') if tab_data else None
            if workflow_data_dir:
                from core.utils import _get_player_character_name
                player_name = _get_player_character_name(self, workflow_data_dir)
                if player_name:
                    result_text = result_text.replace('(player)', player_name)
        if '(setting)' in result_text:
            workflow_data_dir = tab_data.get('workflow_data_dir') if tab_data else None
            if workflow_data_dir:
                from core.utils import _get_player_current_setting_name
                setting_name = _get_player_current_setting_name(workflow_data_dir)
                if setting_name and setting_name != "Unknown Setting":
                    result_text = result_text.replace('(setting)', setting_name)
        def get_var_value(scope, var_name):
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not var_name: return ""
            if scope == "global":
                if not workflow_data_dir: return ""
                tab_index = -1
                try:
                    tab_index = self.tabs_data.index(tab_data)
                except ValueError:
                    return ""
                all_vars = self._load_variables(tab_index)
                value = all_vars.get(var_name, "")
                return value
            if not workflow_data_dir: return ""
            if scope == "player":
                player_name = _get_player_character_name(self, workflow_data_dir)
                if player_name:
                    actor_data, _ = _get_or_create_actor_data(self, workflow_data_dir, player_name)
                    return actor_data.get('variables', {}).get(var_name, "")
                return ""
            elif scope == "actor":
                if actor_name_context:
                    actor_data, _ = _get_or_create_actor_data(self, workflow_data_dir, actor_name_context)
                    return actor_data.get('variables', {}).get(var_name, "")
                return ""
            elif scope == "character":
                if actor_name_context:
                    actor_data, _ = _get_or_create_actor_data(self, workflow_data_dir, actor_name_context)
                    return actor_data.get('variables', {}).get(var_name, "")
                return ""
            elif scope == "setting":
                current_setting_name = _get_player_current_setting_name(workflow_data_dir)
                if current_setting_name and current_setting_name != "Unknown Setting":
                    setting_file_path, _ = _find_setting_file_prioritizing_game_dir(self, workflow_data_dir, current_setting_name)
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
            final_str = str(val)
            return final_str
        pattern = r'\[(global|player|actor|character|setting),\s*([^,\]]+?)\s*\]'
        final_result = re.sub(pattern, replace_match, result_text)
        return final_result

    def _generate_and_save_npc_note_main(self, character_name, npc_response, workflow_data_dir):
        try:
            session_file_path = self._ensure_session_actor_file_main(workflow_data_dir, character_name)
            if not session_file_path:
                return
            current_context = self.get_current_context()
            if not current_context:
                return
            recent_messages = []
            for msg in current_context[-5:]:
                if msg.get('role') == 'user':
                    tab_data = self.get_current_tab_data()
                    if tab_data:
                        from core.utils import _get_player_character_name
                        player_name = _get_player_character_name(self, workflow_data_dir)
                        player_name = player_name if player_name else "Player"
                    else:
                        player_name = "Player"
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
            tab_data = self.get_current_tab_data()
            model = tab_data.get('settings', {}).get('model', get_default_model()) if tab_data else get_default_model()
            generated_note = self.run_utility_inference_sync(note_context, model, 100)
            if generated_note and generated_note.strip():
                note_content = generated_note.strip()
                if note_content.startswith('"') and note_content.endswith('"'):
                    note_content = note_content[1:-1]
                from core.memory import add_npc_note_to_character_file
                game_datetime = None
                if tab_data:
                    try:
                        tab_index = self.tabs_data.index(tab_data) if tab_data in self.tabs_data else -1
                        if tab_index >= 0:
                            variables = self._load_variables(tab_index)
                            game_datetime = variables.get('datetime')
                    except Exception:
                        pass
                success = add_npc_note_to_character_file(session_file_path, note_content, game_datetime)
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _ensure_session_actor_file_main(self, workflow_data_dir, character_name):
        try:
            normalized_name = character_name.strip().lower().replace(' ', '_')
            session_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
            session_file_path = os.path.join(session_actors_dir, f"{normalized_name}.json")
            if os.path.exists(session_file_path):
                return session_file_path
            from core.utils import _find_actor_file_path
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

    def _substitute_placeholders_in_condition_value(self, value_string, tab_data, rule_character_context_name=None):
        if not value_string or not isinstance(value_string, str):
            return value_string
        substituted_string = value_string
        workflow_data_dir = tab_data.get('workflow_data_dir')
        player_name = ""
        setting_name = ""
        if workflow_data_dir:
            player_name = _get_player_character_name(self, workflow_data_dir) or ""
            setting_name = _get_player_current_setting_name(workflow_data_dir) or ""
        character_name_to_use = rule_character_context_name or ""
        def replace_placeholder(match):
            placeholder = match.group(1).lower()
            if placeholder == 'player':
                return player_name
            elif placeholder == 'character':
                return character_name_to_use
            elif placeholder == 'setting':
                return setting_name
            return match.group(0)
        substituted_string = re.sub(r'\((player|character|setting)\)', replace_placeholder, substituted_string, flags=re.IGNORECASE)
        return substituted_string

    def _update_remaining_character_contexts(self):
        try:
            if not hasattr(self, '_npc_inference_queue') or not self._npc_inference_queue:
                return
            tab_data = self.get_current_tab_data()
            if not tab_data:
                return
            full_history_context = self.get_current_context()
            current_scene = tab_data.get('scene_number', 1)
            for inference_data in self._npc_inference_queue:
                character_name = inference_data['character']
                context = inference_data['context']
                final_prompt_index = -1
                for i, msg in enumerate(context):
                    if (msg.get('role') == 'user' and 
                        msg.get('content', '').startswith(f"(You are playing as: {character_name}")):
                        final_prompt_index = i
                        break
                if final_prompt_index == -1:
                    continue
                new_context = []
                setup_complete = False
                for i, msg in enumerate(context):
                    if i >= final_prompt_index:
                        break
                    if (msg.get('role') == 'user' and 
                        ('current setting of the scene' in msg.get('content', '').lower() or
                         'character sheet' in msg.get('content', '').lower())):
                        new_context.append(msg)
                        setup_complete = True
                    elif not setup_complete or msg.get('role') == 'system':
                        new_context.append(msg)
                for msg in full_history_context:
                    if msg.get('role') != 'system' and msg.get('scene', 1) == current_scene:
                        content = msg['content']
                        if (msg.get('role') == 'assistant' and 
                            'metadata' in msg and 
                            msg['metadata'].get('character_name')):
                            char_name = msg['metadata']['character_name']
                            if content and not content.strip().startswith(f"{char_name}:"):
                                content = f"{char_name}: {content}"
                        new_context.append({"role": msg['role'], "content": content})
                for i in range(final_prompt_index, len(context)):
                    new_context.append(context[i])
                inference_data['context'] = new_context
        except Exception as e:
            import traceback
            traceback.print_exc()

    def _cleanup_old_backup_files(self):
        try:
            import re
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=1)
            for tab_data in self.tabs_data:
                if not tab_data:
                    continue
                workflow_data_dir = tab_data.get('workflow_data_dir')
                if not workflow_data_dir:
                    continue
                game_dir = os.path.join(workflow_data_dir, 'game')
                if not os.path.exists(game_dir):
                    continue
                for root, dirs, files in os.walk(game_dir):
                    for filename in files:
                        match = re.search(r'_old_(\d{20})$', filename)
                        if match:
                            timestamp_str = match.group(1)
                            try:
                                file_time = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S%f')
                                if file_time < cutoff_time:
                                    file_path = os.path.join(root, filename)
                                    os.remove(file_path)
                                    print(f"Cleaned up old backup file: {file_path}")
                            except (ValueError, OSError) as e:
                                continue
        except Exception as e:
            print(f"Error during backup file cleanup: {e}")

def main():
    QApplication.setApplicationName("Chatbot RPG | A Text Adventure Game")
    app = QApplication(sys.argv)
    settings = QSettings("ChatBotRPG", "ChatBotRPG")
    splash = SplashScreen()
    splash.show_and_center(app, settings)
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        splash_sound = pygame.mixer.Sound('sounds/SplashScreen.mp3')
        splash_sound.play()
    except Exception:
        pass
    app.processEvents()
    class ChatbotUIWithSplash(ChatbotUI):
        def __init__(self, splash_screen):
            self._splash = splash_screen
            super().__init__()
        def _update_splash(self):
            if self._splash:
                SplashScreen.process_with_splash(self._splash)
    chatbot_ui = ChatbotUIWithSplash(splash)
    app.processEvents()
    chatbot_ui.show()
    splash.finish(chatbot_ui)
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
