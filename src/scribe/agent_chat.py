import sys
import os
import json
import base64
from datetime import datetime
import markdown2
from core.make_inference import make_inference

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QFileDialog, QTextBrowser, QMessageBox, 
                             QMainWindow)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QRect, QBuffer, QByteArray, QIODevice
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

try:
    from config import get_api_key_for_service, get_current_service, get_default_model, get_default_utility_model
    current_service = get_current_service()
    LLM_API_KEY = get_api_key_for_service(current_service)
    DEFAULT_MODEL = get_default_model()
    if current_service == "openrouter":
        SEARCH_MODEL = "openai/gpt-4o-mini-search-preview"
    else:
        SEARCH_MODEL = get_default_model()
except (ImportError, ModuleNotFoundError):
    LLM_API_KEY = os.environ.get("LLM_API_KEY", "your_api_key_here")
    DEFAULT_MODEL = "google/gemini-2.5-flash-lite-preview-06-17"
    SEARCH_MODEL = "google/gemini-2.5-flash-lite-preview-06-17"

STANDALONE_PRIMARY_COLOR = "#00FF66"
STANDALONE_BG_COLOR = "#1E1E1E"
STANDALONE_SECONDARY_COLOR = "#2A2A2A"
STANDALONE_TERTIARY_COLOR = "#3D3D3D"
STANDALONE_LINK_COLOR = "#99FFBB"
DEFAULT_TEMP = 0.7
MAX_HISTORY = 200
CONVERSATION_DIR = "conversations"
SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "gif", "webp"]
SYSTEM_PROMPT = """You are the "Scribe," an expert AI assistant integrated into the "ChatBot RPG Construction Toolkit." Your purpose is to assist the "Game Master" (the user) in building and running a dynamic, **single-player text adventure** where the player interacts with AI characters and the game world.

**COMMUNICATION STYLE:**
- Avoid long blocks of text
- Keep responses focused and actionable

**Your Relationship to the Game:**
You are a **development assistant**. Your conversation with the Game Master is separate from the game simulation. You are here to help build the world, the characters, and most importantly, the underlying logic that will bring the game to life. You are not affected by the game's rules engine; rather, you help the user create those rules.

**The Single-Player Game You Help The User Build:**
The Game Master is creating a **single-player text adventure** that operates on a unique principle:
*   **Dynamic Context:** The game's narrative and character interactions are not pre-scripted. Instead, an external **rules engine** dynamically constructs the context for each turn of the game.
*   **Player Experience:** The player types actions and dialogue, and AI characters (NPCs) respond dynamically based on rules, personality, and context.
*   **The Rules System:** This is the core of the toolkit. The Game Master will create rules (for example, as JSON objects) that act as 'if-then' statements. These rules are processed on every turn of the game simulation.
    *   **Conditions:** Rules check for things like a character's location, game variables (e.g., `has_found_the_amulet`), or keywords in the player's input.
    *   **Actions:** If conditions are met, rules can perform actions like changing variables, moving NPCs, and even rewriting the text that in-game characters say.

**TIME PASSAGE SYSTEM:**
The toolkit includes a sophisticated time management system:

**Time Modes:**
- **Real World (Sync to Clock):** Game time syncs with your computer's clock
- **Game World:** Custom time progression with three advancement modes:
  - **Static:** Time stays fixed at starting datetime
  - **Realtime:** Time advances based on real time with configurable multiplier
  - **Manual:** Time advances only when manually triggered

**Time Triggers:**
- Set variables to change at specific times/dates
- Supports exact times, recurring patterns (daily, weekly, monthly)
- Can revert variables when conditions no longer match
- Triggers check year, month, day, hour, minute, day of week
- Custom calendar support (rename months/days)

**Time Variables:**
- `datetime`: Current game time (ISO format)
- `timemode`: Current time mode ("real_world", "game_world")
- `_executed_time_triggers`: List of triggers already executed
- `_trigger_original_values`: Stored original values for reverting

**Your Role as the Scribe:**
1.  **Collaborative World-Builder:** Help the Game Master brainstorm and write content for their single-player adventure: settings, character backstories, item descriptions, plot hooks, and dialogue.
2.  **Toolkit Expert:** Explain the different components of the toolkit (Origin, Rules, Lists, Setting, Time Manager, etc.) and guide the user on how to use them effectively.
3.  **Rules Architect:** This is your most critical function. Help the Game Master translate their gameplay ideas into the formal logic of the rules system that will drive the single-player experience.
4.  **Time System Expert:** Help users understand and configure the time passage system for dynamic world events.

Your primary goal is to be a knowledgeable creative and technical partner, empowering the Game Master to build their single-player text adventure using this powerful, context-driven toolkit."""

class InferenceThread(QThread):
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self, context, user_message, model_path, temperature=0.7, image_path=None):
        super().__init__()
        self.context = context
        self.user_message = user_message
        self.model_path = model_path
        self.temperature = temperature
        self.image_path = image_path

    def run(self):
        try:
            self.status_signal.emit("Processing request...")
            response = self.make_inference()
            self.result_signal.emit(response)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.status_signal.emit("")

    def make_inference(self):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if self.context:
            messages.extend(self.context)
        messages.append({"role": "user", "content": self.user_message})
        return make_inference(
            context=messages,
            user_message=self.user_message,
            character_name="Scribe",
            url_type=self.model_path,
            max_tokens=4000,
            temperature=self.temperature,
            is_utility_call=True
        )

class IntentAnalysisThread(QThread):
    result_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, message, model_path, temperature=0.1, context=None):
        super().__init__()
        self.message = message
        self.model_path = model_path
        self.temperature = temperature
        self.context = context or []
        
    def run(self):
        try:
            result = self.analyze_intent()
            self.result_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))
            
    def analyze_intent(self):
        system_content = (
            "You are a helpful assistant that analyzes user messages to determine their intent. "
            "Your task is to analyze the ENTIRE conversation and determine what context is needed for the current message.\n\n"
            "CONTEXT TYPES:\n"
            "1. SEARCH: Requires current information from the internet\n"
            "2. GAME_CONTEXT: Involves working with, analyzing, or referencing the current game's conversation/chat history\n"
            "3. RULES_CONTEXT: Involves working with, analyzing, or modifying the game's rules system (triggers, conditions, actions)\n"
            "4. CHARACTER_GENERATION: Involves creating, editing, or managing game characters/actors and their locations\n"
            "5. NORMAL: Regular conversation that doesn't need search, game context, rules context, or character generation\n\n"
            "ANALYSIS APPROACH:\n"
            "- Analyze the ENTIRE conversation history, not just the current message\n"
            "- Look for conversation themes, ongoing topics, and context that should persist\n"
            "- If the conversation has been about rules, game context, or characters, maintain that context\n"
            "- Follow-up questions should inherit context from previous messages\n"
            "- Consider what information the user would need to continue the conversation effectively\n\n"
            "GAME_CONTEXT examples:\n"
            "- 'What happened in the last scene?'\n"
            "- 'Summarize the conversation so far'\n"
            "- 'What did the character say about X?'\n"
            "- 'Analyze the dialogue between characters'\n"
            "- 'Help me understand what's happening in the game'\n"
            "- 'What are the key events from the current scene?'\n\n"
            "RULES_CONTEXT examples:\n"
            "- 'Show me the current rules'\n"
            "- 'Help me create a rule for character movement'\n"
            "- 'Why isn't my combat rule triggering?'\n"
            "- 'Analyze my rules system'\n"
            "- 'Help me write a rule that triggers when...'\n"
            "- 'What rules are currently active?'\n"
            "- 'Debug my timer rules'\n"
            "- 'Create a rule for this scene'\n"
            "- 'Write a rule that sets a variable when...'\n"
            "- 'Edit the rule named X to do Y'\n"
            "- 'Generate a rule for NPC behavior'\n"
            "- 'Make a timer rule that triggers every 5 turns'\n"
            "- 'Delete the rule called X'\n"
            "- 'Modify my combat rules'\n"
            "- 'Create a game over rule when health reaches zero'\n"
            "- 'Add a rule that ends the game if the player fails the quest'\n"
            "- 'Make a timer rule that triggers game over after 10 turns'\n\n"
            "CHARACTER_GENERATION examples:\n"
            "- 'Create a new character named John'\n"
            "- 'Generate a merchant for the tavern'\n"
            "- 'Add a guard to the castle gates'\n"
            "- 'Edit Sarah's appearance and personality'\n"
            "- 'Move the blacksmith to the market square'\n"
            "- 'Generate equipment for the warrior'\n"
            "- 'Create an NPC and place them in the forest'\n"
            "- 'Update the wizard's backstory'\n"
            "- 'Generate a random character for this scene'\n"
            "- 'Add a new character to [location name]'\n"
            "- 'Edit the description of [character name]'\n"
            "- 'Create a character with specific traits'\n"
            "- 'Generate personality for existing character'\n"
            "- 'Move [character] from [place] to [place]'\n"
            "- 'Create multiple characters for the scene'"
        )
        context_text = ""
        conversation_summary = ""
        if self.context:
            user_messages = []
            conversation_themes = []
            for msg in self.context:
                if msg["role"] == "user":
                    user_messages.append(msg['content'])
                    context_text += f"User: {msg['content']}\n"
                else:
                    content = msg["content"]
                    if len(content) > 100:
                        content = content[:100] + "..."
                    context_text += f"Scribe: {content}\n"
            if len(user_messages) > 1:
                conversation_themes = [
                    "rules" if any("rule" in msg.lower() or "timer" in msg.lower() or "trigger" in msg.lower() for msg in user_messages) else None,
                    "game" if any("scene" in msg.lower() or "character" in msg.lower() or "what happened" in msg.lower() for msg in user_messages) else None,
                    "search" if any("search" in msg.lower() or "news" in msg.lower() or "current" in msg.lower() for msg in user_messages) else None,
                    "character_gen" if any("create" in msg.lower() or "generate" in msg.lower() or "character" in msg.lower() for msg in user_messages) else None
                ]
                conversation_themes = [theme for theme in conversation_themes if theme]
                conversation_summary = f"Conversation themes detected: {', '.join(conversation_themes)}" if conversation_themes else "No specific themes detected"
                        
        user_message = (
            f"Analyze the following message within its FULL conversation context:\n\n"
            f"Conversation summary: {conversation_summary}\n"
            f"Full conversation context:\n{context_text}\n"
            f"Current message: \"{self.message}\"\n\n"
            "Based on the ENTIRE conversation, determine what context is needed for this message.\n"
            "Consider ongoing themes and whether this is a follow-up to previous topics.\n\n"
            "Respond with JSON only in this exact format:\n"
            "{\n"
            "  \"intent_type\": \"[SEARCH|GAME_CONTEXT|RULES_CONTEXT|CHARACTER_GENERATION|NORMAL]\",\n"
            "  \"requires_search\": [true if SEARCH or conversation has search themes, false otherwise],\n"
            "  \"requires_game_context\": [true if GAME_CONTEXT or conversation has game themes, false otherwise],\n"
            "  \"requires_rules_context\": [true if RULES_CONTEXT or conversation has rules themes, false otherwise],\n"
            "  \"requires_character_generation\": [true if CHARACTER_GENERATION or conversation has character themes, false otherwise],\n"
            "  \"confidence\": [0-1 decimal],\n"
            "  \"reasoning\": \"[brief explanation considering full conversation context]\",\n"
            "  \"scenes_requested\": [number of scenes back if specified, default 1 for current scene]\n"
            "}"
        )
        try:
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message}
            ]
            response_content = make_inference(
                context=messages,
                user_message=user_message,
                character_name="IntentAnalyzer",
                url_type=self.model_path,
                max_tokens=500,
                temperature=self.temperature,
                is_utility_call=True
            )
            try:
                cleaned_response = response_content.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                intent_data = json.loads(cleaned_response)
                if "requires_search" not in intent_data:
                    intent_data["requires_search"] = intent_data.get("intent_type") == "SEARCH"
                if "requires_game_context" not in intent_data:
                    intent_data["requires_game_context"] = intent_data.get("intent_type") == "GAME_CONTEXT"
                if "requires_rules_context" not in intent_data:
                    intent_data["requires_rules_context"] = intent_data.get("intent_type") == "RULES_CONTEXT"
                if "requires_character_generation" not in intent_data:
                    intent_data["requires_character_generation"] = intent_data.get("intent_type") == "CHARACTER_GENERATION"
                if "scenes_requested" not in intent_data:
                    intent_data["scenes_requested"] = 1
                return intent_data
            except json.JSONDecodeError:
                print(f"[ERROR] Failed to parse response_content as JSON: {response_content}")
                return {
                    "intent_type": "NORMAL",
                    "requires_search": False,
                    "requires_game_context": False,
                    "requires_rules_context": False,
                    "requires_character_generation": False,
                    "confidence": 0.0,
                    "reasoning": "Failed to parse response",
                    "scenes_requested": 1
                }
        except Exception as e:
            print(f"Exception during intent analysis: {str(e)}")
            raise Exception(f"Intent analysis error: {str(e)}")


class ChatInput(QTextEdit):
    def __init__(self, agent_panel, theme_colors):
        super().__init__()
        self.agent_panel = agent_panel
        self.setAcceptRichText(False)
        self.setMinimumHeight(56)
        self.setMaximumHeight(56)
        self.setPlaceholderText("Type your message...")
        font = QFont('Consolas', 12)
        self.setFont(font)
        self.setCursorWidth(4)
        self.setStyleSheet(f"""
            QTextEdit {{
                color: {theme_colors['UI_PRIMARY_COLOR']};
                background-color: #0A0A0A !important;
                border: 1px solid {theme_colors['UI_PRIMARY_COLOR']};
                border-radius: 2px;
                padding: 8px;
                font-family: Consolas;
                font-size: 12pt;
                selection-background-color: {theme_colors['UI_COLOR_DARK']};
            }}
        """)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not (event.modifiers() & Qt.ShiftModifier):
            self.agent_panel.send_message()
            event.accept()
        else:
            super().keyPressEvent(event)
class ChatOutput(QTextBrowser):
    def __init__(self, theme_colors):
        super().__init__()
        self.setReadOnly(True)
        self.setOpenLinks(True)
        font = self.font()
        font.setPointSize(12)
        self.setFont(font)
        self.setStyleSheet(f"""
            QTextBrowser {{
                color: {theme_colors['UI_PRIMARY_COLOR']};
                background-color: #0A0A0A !important;
                border: 1px solid {theme_colors['UI_PRIMARY_COLOR']};
                border-radius: 2px;
                padding: 5px;
                font-size: 11pt;
                selection-background-color: {theme_colors['UI_COLOR_DARK']};
            }}
            QScrollBar:vertical {{
                border: none; background: #0A0A0A !important; width: 8px; margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {theme_colors['UI_PRIMARY_COLOR']};
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                border: none; background: none; height: 0px;
            }}
        """)
        document = self.document()
        document.setDefaultStyleSheet(f"""
            a {{ color: {theme_colors['UI_PRIMARY_COLOR']}; text-decoration: underline; }}
            a:hover {{ color: {theme_colors['UI_COLOR_DARK']}; }}
            hr {{ border: 1px solid {theme_colors['UI_PRIMARY_COLOR']}; }}
        """)
        self._show_default_hint()

    def _show_default_hint(self):
        color = self.parent().theme_colors.get('UI_PRIMARY_COLOR', '#00FF66') if self.parent() else '#00FF66'
        if color.startswith('#') and len(color) == 7:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            rgba = f'rgba({r},{g},{b},0.5)'
        else:
            rgba = 'rgba(0,255,102,0.5)'
        hint = (
            f"<span style='color:{rgba};'>"
            "The Scribe agent is your creative and technical assistant for building and running your RPG. "
            "Ask it about worldbuilding, rules, time systems, or how to use the toolkit. "
            "<br><br>"
            "Currently, the agent only understands basic concepts about the game engine and is still in development. "
            "Don't expect any miracles. Those will come later."
            "</span>"
        )
        super().setHtml(hint)

    def setHtml(self, html):
        if not html.strip():
            self._show_default_hint()
        else:
            super().setHtml(html)

    def clear(self):
        super().clear()
        self._show_default_hint()
        
    def refresh_hint_text(self):
        if not self.toPlainText().strip():
            self._show_default_hint()

class AgentPanel(QWidget):
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent)
        self.parent_app = parent
        self.theme_colors = {}
        if theme_colors and 'base_color' in theme_colors:
            self.theme_colors['UI_PRIMARY_COLOR'] = theme_colors['base_color']
            self.theme_colors['UI_COLOR_DARK'] = theme_colors['base_color']
            self.theme_colors['UI_COLOR_DARKER'] = theme_colors['bg_color']
            self.theme_colors['UI_BACKGROUND'] = theme_colors['bg_color']
        else:
            self.theme_colors['UI_PRIMARY_COLOR'] = STANDALONE_PRIMARY_COLOR
            self.theme_colors['UI_BACKGROUND'] = STANDALONE_BG_COLOR
            self.theme_colors['UI_COLOR_DARK'] = STANDALONE_SECONDARY_COLOR
            self.theme_colors['UI_COLOR_DARKER'] = STANDALONE_TERTIARY_COLOR
        self.setObjectName("agentPanel")
        self.sound_player = QMediaPlayer()
        self.context = []
        self.model_path = DEFAULT_MODEL
        self.temperature = DEFAULT_TEMP
        self.conversation_name = "conversation_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_image_path = None
        self.game_context_injected = False
        self.rules_context_injected = False
        self.setAcceptDrops(True)
        self.setup_ui()
        self.try_load_recent_conversation()
        if LLM_API_KEY == "your_api_key_here":
            service_name = current_service.title() if 'current_service' in locals() else "API"
            QMessageBox.warning(self, "API Key Missing", f"{service_name} API key not set. Please check config.json file.")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        self.setStyleSheet(f"""
            QWidget#agentPanel, QWidget#agentPanel > * {{
                background-color: {self.theme_colors['UI_BACKGROUND']} !important;
            }}
        """)
        self.scribe_label = QLabel("Game Master's Scribe")
        self.scribe_label.setAlignment(Qt.AlignCenter)
        self.scribe_label.setStyleSheet(f"font-size: 10pt; color: {self.theme_colors['UI_PRIMARY_COLOR']}; padding: 2px; background-color: transparent;")
        layout.addWidget(self.scribe_label)
        self.output_field = ChatOutput(self.theme_colors)
        layout.addWidget(self.output_field, 1)
        self.attachment_area = QWidget()
        self.attachment_area.setStyleSheet(f"background-color: {self.theme_colors['UI_BACKGROUND']};")
        self.attachment_layout = QHBoxLayout(self.attachment_area)
        self.attachment_layout.setContentsMargins(0, 5, 0, 0)
        self.image_preview = QLabel()
        self.image_preview.setFixedSize(80, 60)
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.remove_attachment_btn = QPushButton("×")
        self.remove_attachment_btn.setFixedSize(20, 20)
        self.remove_attachment_btn.setStyleSheet(f"""
            QPushButton {{
                color: {self.theme_colors['UI_PRIMARY_COLOR']}; background-color: {self.theme_colors['UI_BACKGROUND']};
                border: 1px solid {self.theme_colors['UI_PRIMARY_COLOR']}; border-radius: 10px;
                font-size: 16px;
            }}
            QPushButton:hover {{ background-color: {self.theme_colors['UI_COLOR_DARKER']}; }}
            QPushButton:pressed {{ background-color: {self.theme_colors['UI_COLOR_DARK']}; color: {self.theme_colors['UI_COLOR_DARK']}; }}
        """)
        self.remove_attachment_btn.clicked.connect(self.clear_attachment)
        self.attachment_layout.addWidget(self.image_preview)
        self.attachment_layout.addWidget(self.remove_attachment_btn, 0, Qt.AlignTop)
        self.attachment_layout.addStretch()
        self.attachment_area.setVisible(False)
        layout.addWidget(self.attachment_area)
        self.input_field = ChatInput(self, self.theme_colors)
        layout.addWidget(self.input_field)
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        bottom_bar.setSpacing(3)
        button_style = f"""
            QPushButton {{
                color: {self.theme_colors['UI_PRIMARY_COLOR']}; background-color: {self.theme_colors['UI_BACKGROUND']};
                border: 1px solid {self.theme_colors['UI_PRIMARY_COLOR']}; border-radius: 2px;
                padding: 5px 10px; font-size: 10pt;
            }}
            QPushButton:hover {{ background-color: {self.theme_colors['UI_COLOR_DARKER']}; }}
            QPushButton:pressed {{ background-color: {self.theme_colors['UI_COLOR_DARK']}; color: {self.theme_colors['UI_COLOR_DARK']}; }}
            QPushButton:disabled {{ color: #666; border-color: #666; }}
        """
        self.clear_button = QPushButton("Clear")
        self.clear_button.setStyleSheet(button_style)
        self.clear_button.clicked.connect(self.clear_conversation)
        self.attach_button = QPushButton("Attach")
        self.attach_button.setStyleSheet(button_style)
        self.attach_button.clicked.connect(self.attach_image)
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet(button_style)
        self.send_button.setDefault(True)
        self.send_button.clicked.connect(self.send_message)
        bottom_bar.addWidget(self.clear_button)
        bottom_bar.addStretch(1)
        bottom_bar.addWidget(self.attach_button)
        bottom_bar.addWidget(self.send_button)
        layout.addLayout(bottom_bar)
        layout.addStretch(0)

    def play_sound(self, sound_name):
        try:
            sound_path = os.path.join(os.path.dirname(__file__), "sounds", sound_name)
            if os.path.exists(sound_path):
                self.sound_player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_path)))
                self.sound_player.play()
        except Exception:
            pass

    def send_message(self):
        if not self.send_button.isEnabled():
            return 
        message = self.input_field.toPlainText().strip()
        if not message:
            return
        self.send_button.setEnabled(False)
        try:
            sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "MessageOut.mp3")
            self.sound_player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_path)))
            self.sound_player.play()
        except Exception:
            pass
        self.input_field.clear()
        self.context.append({"role": "user", "content": message})
        user_display_message = self._format_user_message(message)
        if self.current_image_path:
            self.display_message(user_display_message, image_path=self.current_image_path)
        else:
            self.display_message(user_display_message)
        if self.parent_app:
            for child in self.parent_app.findChildren(AgentPanel):
                if child != self:
                    child.context.append({"role": "user", "content": message})
        self.intent_thread = IntentAnalysisThread(
            message,
            self.model_path,
            0.1,
            self.context
        )
        self.intent_thread.result_signal.connect(lambda result: self.handle_analyzed_intent(message, result))
        self.intent_thread.error_signal.connect(lambda error: self.process_normal_message(message, already_displayed=True))
        self.intent_thread.start()
        if self.current_image_path:
            self.clear_attachment()

    def _format_assistant_message(self, content):
        response_html = markdown2.markdown(content, extras=['fenced-code-blocks', 'code-friendly']).strip()
        base_color = self.theme_colors.get('UI_PRIMARY_COLOR', '#00ff66')
        base_color_obj = QColor(base_color)
        if base_color_obj.isValid():
            nametag_color = base_color_obj.lighter(130).name()
        else:
            nametag_color = base_color
        if response_html.startswith('<p>') and response_html.endswith('</p>'):
            return f'<span style="color: {nametag_color};"><b>Scribe:</b></span> {response_html[3:-4]}'
        return f'<span style="color: {nametag_color};"><b>Scribe:</b></span> {response_html}'

    def _format_user_message(self, content):
        base_color = self.theme_colors.get('UI_PRIMARY_COLOR', '#00ff66')
        base_color_obj = QColor(base_color)
        if base_color_obj.isValid():
            nametag_color = base_color_obj.lighter(130).name()
        else:
            nametag_color = base_color
        
        return f'<span style="color: {nametag_color};"><b>Game Master:</b></span> {content}'

    def handle_analyzed_intent(self, message, intent_data):
        requires_search = intent_data.get("requires_search", False)
        requires_game_context = intent_data.get("requires_game_context", False)
        requires_rules_context = intent_data.get("requires_rules_context", False)
        requires_character_generation = intent_data.get("requires_character_generation", False)
        confidence = intent_data.get("confidence", 0.0)
        scenes_requested = intent_data.get("scenes_requested", 1)
        if requires_search and confidence > 0.7:
            self.process_search_query(message)
        elif requires_game_context and confidence > 0.7:
            self.process_game_context_message(message, scenes_requested)
        elif requires_rules_context and confidence > 0.7:
            self.process_rules_context_message(message, scenes_requested)
        elif requires_character_generation and confidence > 0.7:
            self.process_character_generation_message(message)
        else:
            self.process_normal_message(message, already_displayed=True)

    def display_message(self, html_message, image_path=None, skip_sync=False):
        if self.output_field.toPlainText().strip():
            self.output_field.append("<hr>")
        if image_path:
            try:
                pixmap = QPixmap(image_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                pixmap.save(buffer, "PNG")
                img_base64 = base64.b64encode(byte_array.data()).decode("utf-8")
                img_html = f'<img src="data:image/png;base64,{img_base64}" /><br>'
                html_message = img_html + html_message
            except Exception as e:
                html_message += f"<i style='color:red'>[Could not display image: {e}]</i>"
        self.output_field.append(html_message)
        self.output_field.verticalScrollBar().setValue(self.output_field.verticalScrollBar().maximum())
        if not skip_sync and self.parent_app:
            for child in self.parent_app.findChildren(AgentPanel):
                if child != self:
                    child._rebuild_display_from_context()

    def attach_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Attach Image", "", f"Images ({' '.join(['*.'+f for f in SUPPORTED_IMAGE_FORMATS])})"
        )
        if file_path:
            self.set_attachment(file_path)

    def set_attachment(self, file_path):
        self.current_image_path = file_path
        pixmap = QPixmap(file_path).scaled(
            self.image_preview.width(), self.image_preview.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.image_preview.setPixmap(pixmap)
        self.attachment_area.setVisible(True)

    def clear_attachment(self):
        self.current_image_path = None
        self.image_preview.clear()
        self.attachment_area.setVisible(False)
        
    def _rebuild_display_from_context(self):
        self.output_field.clear()
        for i, message in enumerate(self.context):
            role = message.get("role")
            content = message.get("content")
            if role == "user":
                display_message = self._format_user_message(content)
                self.display_message(display_message, skip_sync=True)
            elif role == "assistant":
                display_message = self._format_assistant_message(content)
                self.display_message(display_message, skip_sync=True)

    def clear_conversation(self):
        self.context = []
        self.output_field.clear()
        self.clear_attachment()
        self.conversation_name = "conversation_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        self.game_context_injected = False
        self.rules_context_injected = False
        self.character_generation_context_injected = False
        auto_save_dir = os.path.join(self.get_conversation_dir(), "autosave")
        file_path = os.path.join(auto_save_dir, f"{self.conversation_name}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        if self.parent_app:
            for child in self.parent_app.findChildren(AgentPanel):
                if child != self:
                    child.context = []
                    child.output_field.clear()
                    child.clear_attachment()
                    child.conversation_name = "conversation_" + datetime.now().strftime("%Y%m%d_%H%M%S")
                    child.game_context_injected = False
                    child.rules_context_injected = False
                    child.character_generation_context_injected = False
                    auto_save_dir = os.path.join(child.get_conversation_dir(), "autosave")
                    file_path = os.path.join(auto_save_dir, f"{child.conversation_name}.json")
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass

    def auto_save_conversation(self):
        try:
            auto_save_dir = os.path.join(self.get_conversation_dir(), "autosave")
            os.makedirs(auto_save_dir, exist_ok=True)
            file_path = os.path.join(auto_save_dir, f"{self.conversation_name}.json")
            data = {"context": self.context, "model": self.model_path, "temperature": self.temperature}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            pass

    def update_theme(self, new_theme):
        if new_theme and 'base_color' in new_theme:
            self.theme_colors['UI_PRIMARY_COLOR'] = new_theme['base_color']
            self.theme_colors['UI_COLOR_DARK'] = new_theme['base_color']
            self.theme_colors['UI_COLOR_DARKER'] = new_theme['bg_color']
            self.theme_colors['UI_BACKGROUND'] = new_theme['bg_color']
            self.setStyleSheet(f"""
                QWidget#agentPanel, QWidget#agentPanel > * {{
                    background-color: {self.theme_colors['UI_BACKGROUND']} !important;
                }}
            """)
            if hasattr(self, 'scribe_label'):
                self.scribe_label.setStyleSheet(
                    f"font-size: 10pt; color: {self.theme_colors['UI_PRIMARY_COLOR']}; "
                    f"padding: 2px; background-color: transparent;"
                )
            if hasattr(self, 'output_field'):
                self.output_field.setStyleSheet(f"""
                    QTextBrowser {{
                        color: {self.theme_colors['UI_PRIMARY_COLOR']};
                        background-color: {self.theme_colors['UI_BACKGROUND']} !important;
                        border: 1px solid {self.theme_colors['UI_PRIMARY_COLOR']};
                        border-radius: 2px;
                        padding: 5px;
                        font-size: 11pt;
                        selection-background-color: {self.theme_colors['UI_COLOR_DARK']};
                    }}
                    QScrollBar:vertical {{
                        border: none; background: {self.theme_colors['UI_BACKGROUND']} !important; width: 8px; margin: 0px;
                    }}
                    QScrollBar::handle:vertical {{
                        background: {self.theme_colors['UI_PRIMARY_COLOR']};
                        min-height: 20px;
                    }}
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                        border: none; background: none; height: 0px;
                    }}
                """)
                document = self.output_field.document()
                document.setDefaultStyleSheet(f"""
                    a {{ color: {self.theme_colors['UI_PRIMARY_COLOR']}; text-decoration: underline; }}
                    a:hover {{ color: {self.theme_colors['UI_COLOR_DARK']}; }}
                    hr {{ border: 1px solid {self.theme_colors['UI_PRIMARY_COLOR']}; }}
                """)
                self.output_field.refresh_hint_text()
            if hasattr(self, 'input_field'):
                self.input_field.setStyleSheet(f"""
                    QTextEdit {{
                        color: {self.theme_colors['UI_PRIMARY_COLOR']};
                        background-color: {self.theme_colors['UI_BACKGROUND']} !important;
                        border: 1px solid {self.theme_colors['UI_PRIMARY_COLOR']};
                        border-radius: 2px;
                        padding: 8px;
                        font-family: Consolas;
                        font-size: 12pt;
                        selection-background-color: {self.theme_colors['UI_COLOR_DARK']};
                    }}
                """)
            if hasattr(self, 'attachment_area'):
                self.attachment_area.setStyleSheet(f"background-color: {self.theme_colors['UI_BACKGROUND']};")
            button_style = f"""
                QPushButton {{
                    color: {self.theme_colors['UI_PRIMARY_COLOR']}; 
                    background-color: {self.theme_colors['UI_BACKGROUND']} !important;
                    border: 1px solid {self.theme_colors['UI_PRIMARY_COLOR']}; 
                    border-radius: 2px;
                    padding: 5px 10px; 
                    font-size: 10pt;
                }}
                QPushButton:hover {{ 
                    background-color: {self.theme_colors['UI_COLOR_DARKER']} !important; 
                }}
                QPushButton:pressed {{ 
                    background-color: {self.theme_colors['UI_COLOR_DARK']} !important; 
                    color: {self.theme_colors['UI_COLOR_DARK']};
                }}
                QPushButton:disabled {{ 
                    color: #666; 
                    border-color: #666; 
                }}
            """
            if hasattr(self, 'clear_button'):
                self.clear_button.setStyleSheet(button_style)
            if hasattr(self, 'attach_button'):
                self.attach_button.setStyleSheet(button_style)
            if hasattr(self, 'send_button'):
                self.send_button.setStyleSheet(button_style)
            if hasattr(self, 'remove_attachment_btn'):
                self.remove_attachment_btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {self.theme_colors['UI_PRIMARY_COLOR']}; 
                        background-color: {self.theme_colors['UI_BACKGROUND']} !important;
                        border: 1px solid {self.theme_colors['UI_PRIMARY_COLOR']}; 
                        border-radius: 10px;
                        font-size: 16px;
                    }}
                    QPushButton:hover {{ 
                        background-color: {self.theme_colors['UI_COLOR_DARKER']} !important; 
                    }}
                    QPushButton:pressed {{ 
                        background-color: {self.theme_colors['UI_COLOR_DARK']} !important; 
                        color: {self.theme_colors['UI_COLOR_DARK']};
                    }}
                """)

    def try_load_recent_conversation(self):
        try:
            auto_save_dir = os.path.join(self.get_conversation_dir(), "autosave")
            if not os.path.exists(auto_save_dir):
                return
            files = [os.path.join(auto_save_dir, f) for f in os.listdir(auto_save_dir) if f.endswith('.json')]
            if not files:
                return
            most_recent_file = max(files, key=os.path.getmtime)
            self.load_conversation_from_file(most_recent_file)
        except Exception as e:
            pass

    def load_conversation_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.context = data.get("context", [])
            self.conversation_name = os.path.splitext(os.path.basename(file_path))[0]
            self.output_field.clear()
            for message in self.context:
                role = message.get("role")
                content = message.get("content")
                if role == "user":
                    display_message = self._format_user_message(content)
                    self.display_message(display_message)
                elif role == "assistant":
                    display_message = self._format_assistant_message(content)
                    self.display_message(display_message)
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load conversation: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                ext = os.path.splitext(file_path)[1].lower().replace('.', '')
                if ext in SUPPORTED_IMAGE_FORMATS:
                    event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.set_attachment(file_path)
            event.acceptProposedAction()

    def process_search_query(self, message):
        if self.current_image_path:
            self.context.append({
                "role": "user",
                "content": f"{message}\n[Image attached: {os.path.basename(self.current_image_path)}]"
            })
        else:
            self.context.append({"role": "user", "content": message})
        original_model = self.model_path
        self.model_path = SEARCH_MODEL
        self.inference_thread = InferenceThread(
            self.context,
            message,
            self.model_path,
            self.temperature,
            self.current_image_path
        )
        self.inference_thread.result_signal.connect(
            lambda response: self.handle_search_response(response, original_model)
        )
        self.inference_thread.error_signal.connect(
            lambda error: self.handle_search_error(error, original_model)
        )
        self.inference_thread.status_signal.connect(self.update_status)
        self.inference_thread.start()
        if self.current_image_path:
            self.clear_attachment()

    def handle_search_response(self, response, original_model):
        self.model_path = original_model
        self.handle_response(response)

    def handle_search_error(self, error_message, original_model):
        self.model_path = original_model
        self.handle_error(error_message)

    def handle_response(self, response):
        self.send_button.setEnabled(True)
        if "EXECUTE_RULE_ACTION:" in response:
            self.process_rule_action_command(response)
            return
        if "EXECUTE_CHARACTER_ACTION:" in response:
            self.process_character_action_command(response)
            return
        self.context.append({"role": "assistant", "content": response})
        response_html = self._format_assistant_message(response)
        self.display_message(response_html)
        self.auto_save_conversation()
        if self.parent_app:
            for child in self.parent_app.findChildren(AgentPanel):
                if child != self:
                    child.context.append({"role": "assistant", "content": response})
                    child.auto_save_conversation()
        try:
            sound_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds", "MessageIn.mp3")
            self.sound_player.setMedia(QMediaContent(QUrl.fromLocalFile(sound_path)))
            self.sound_player.play()
        except Exception as e:
            print(f"Sound error: {str(e)}")

    def process_rule_action_command(self, response):
        try:
            command_start = response.find("EXECUTE_RULE_ACTION:") + len("EXECUTE_RULE_ACTION:")
            command_end = response.find("\n", command_start)
            if command_end == -1:
                command_end = len(response)
            command_json = response[command_start:command_end].strip()
            command_data = json.loads(command_json)
            action = command_data.get("action")
            rule_type = command_data.get("rule_type", "trigger")
            rule_id = command_data.get("rule_id")
            rule_data = command_data.get("rule_data")
            if action == "create":
                success, message = self.write_new_rule(rule_data, rule_type)
            elif action == "edit":
                success, message = self.edit_existing_rule(rule_id, rule_data, rule_type)
            elif action == "delete":
                success, message = self.delete_rule(rule_id, rule_type)
            else:
                success, message = False, f"Unknown action: {action}"
            if success:
                result_html = f"<b>✅ Rule Operation Successful:</b> {message}"
                explanation_part = response[:response.find("EXECUTE_RULE_ACTION:")].strip()
                if explanation_part:
                    explanation_html = self._format_assistant_message(explanation_part)
                    self.display_message(explanation_html)
            else:
                result_html = f"<b>❌ Rule Operation Failed:</b> {message}"
                explanation_part = response[:response.find("EXECUTE_RULE_ACTION:")].strip()
                if explanation_part:
                    explanation_html = self._format_assistant_message(explanation_part)
                    self.display_message(explanation_html)
            self.display_message(result_html)
            clean_response = response[:response.find("EXECUTE_RULE_ACTION:")].strip()
            if clean_response:
                self.context.append({"role": "assistant", "content": clean_response})
            self.auto_save_conversation()
            
        except Exception as e:
            error_html = f"<b>❌ Error processing rule command:</b> {str(e)}"
            self.display_message(error_html)
            response_html = self._format_assistant_message(response)
            self.display_message(response_html)

    def process_character_action_command(self, response):
        try:
            command_start = response.find("EXECUTE_CHARACTER_ACTION:") + len("EXECUTE_CHARACTER_ACTION:")
            command_end = response.find("\n", command_start)
            if command_end == -1:
                command_end = len(response)
            command_json = response[command_start:command_end].strip()
            command_data = json.loads(command_json)
            action = command_data.get("action")
            character_name = command_data.get("character_name", "")
            fields_to_generate = command_data.get("fields_to_generate", [])
            target_location = command_data.get("target_location", "")
            instructions = command_data.get("instructions", "")
            target_directory = command_data.get("target_directory", "Game")
            if not self.parent_app or not hasattr(self.parent_app, 'get_current_tab_data'):
                raise Exception("No parent app available")
            tab_data = self.parent_app.get_current_tab_data()
            if not tab_data:
                raise Exception("No tab data available")
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                raise Exception("No workflow_data_dir available")
            if action == "create":
                success, message = self.execute_character_creation(
                    fields_to_generate, instructions, target_location, workflow_data_dir, target_directory
                )
            elif action == "edit":
                success, message = self.execute_character_edit(
                    character_name, fields_to_generate, instructions, target_location, workflow_data_dir, target_directory
                )
            elif action == "move":
                success, message = self.execute_character_move(
                    character_name, target_location, workflow_data_dir
                )
            elif action == "create_and_place":
                success, message = self.execute_character_creation_and_placement(
                    fields_to_generate, instructions, target_location, workflow_data_dir, target_directory
                )
            else:
                success, message = False, f"Unknown character action: {action}"
            if success:
                result_html = f"<b>✅ Character Operation Successful:</b> {message}"
                explanation_part = response[:response.find("EXECUTE_CHARACTER_ACTION:")].strip()
                if explanation_part:
                    explanation_html = self._format_assistant_message(explanation_part)
                    self.display_message(explanation_html)
            else:
                result_html = f"<b>❌ Character Operation Failed:</b> {message}"
                explanation_part = response[:response.find("EXECUTE_CHARACTER_ACTION:")].strip()
                if explanation_part:
                    explanation_html = self._format_assistant_message(explanation_part)
                    self.display_message(explanation_html)
            self.display_message(result_html)
            clean_response = response[:response.find("EXECUTE_CHARACTER_ACTION:")].strip()
            if clean_response:
                self.context.append({"role": "assistant", "content": clean_response})
            self.auto_save_conversation()
            
        except Exception as e:
            error_html = f"<b>❌ Error processing character command:</b> {str(e)}"
            self.display_message(error_html)
            response_html = self._format_assistant_message(response)
            self.display_message(response_html)

    def handle_error(self, error_message):
        self.play_sound("AgentError.mp3")
        error_display_message = f"<p style='color:red;'><b>Error:</b><br>{error_message}</p>"
        self.display_message(error_display_message)
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")

    def update_status(self, status):
        print(f"Status: {status}")

    def process_normal_message(self, message, already_displayed=True):
        if self.current_image_path:
            self.context.append({
                "role": "user",
                "content": f"{message}\n[Image attached: {os.path.basename(self.current_image_path)}]"
            })
            if not already_displayed:
                user_display_message = self._format_user_message(message)
                self.display_message(user_display_message, image_path=self.current_image_path)
            original_model = self.model_path
            image_model = DEFAULT_MODEL
            self.inference_thread = InferenceThread(
                self.context,
                message,
                image_model,
                self.temperature,
                self.current_image_path
            )
            self.inference_thread.result_signal.connect(
                lambda response: self.handle_image_response(response, original_model)
            )
            self.inference_thread.error_signal.connect(
                lambda error: self.handle_image_error(error, original_model)
            )
            self.inference_thread.status_signal.connect(self.update_status)
        else:
            self.context.append({"role": "user", "content": message})
            if not already_displayed:
                user_display_message = self._format_user_message(message)
                self.display_message(user_display_message)
            if len(self.context) > MAX_HISTORY:
                self.context = self.context[-MAX_HISTORY:]
            self.inference_thread = InferenceThread(
                self.context,
                message,
                self.model_path,
                self.temperature
            )
            self.inference_thread.result_signal.connect(self.handle_response)
            self.inference_thread.error_signal.connect(self.handle_error)
            self.inference_thread.status_signal.connect(self.update_status)
        self.inference_thread.start()
        if self.current_image_path:
            self.clear_attachment()

    def handle_image_response(self, response, original_model):
        self.model_path = original_model
        self.handle_response(response)

    def handle_image_error(self, error_message, original_model):
        self.model_path = original_model
        self.handle_error(error_message)

    def get_game_context(self, scenes_back=1):
        if not self.parent_app or not hasattr(self.parent_app, 'get_current_tab_data'):
            return None
        try:
            tab_data = self.parent_app.get_current_tab_data()
            if not tab_data:
                return None
            if 'context' not in tab_data:
                return None
            context = tab_data['context']
            if not context:
                return None
            current_scene = tab_data.get('scene_number', 1)
            target_scenes = []
            for i in range(scenes_back):
                scene_num = current_scene - i
                if scene_num >= 1:
                    target_scenes.append(scene_num)
            game_messages = []
            for msg in context:
                msg_scene = msg.get('scene', 1)
                if msg_scene in target_scenes:
                    game_messages.append(msg)
            if not game_messages:
                return None
            formatted_context = {
                'scenes_included': target_scenes,
                'current_scene': current_scene,
                'messages': game_messages,
                'total_messages': len(game_messages)
            }
            return formatted_context
        except Exception as e:
            return None
    
    def format_game_context_for_llm(self, game_context):
        if not game_context:
            return ""
        messages = game_context['messages']
        scenes = game_context['scenes_included']
        current_scene = game_context['current_scene']
        context_text = f"=== GAME CONVERSATION CONTEXT ===\n"
        context_text += f"Current Scene: {current_scene}\n"
        context_text += f"Scenes Included: {', '.join(map(str, scenes))}\n"
        context_text += f"Total Messages: {len(messages)}\n\n"
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            scene = msg.get('scene', 1)
            metadata = msg.get('metadata', {})
            character_name = metadata.get('character_name')
            text_tag = metadata.get('text_tag')
            if role == 'user':
                context_text += f"[Scene {scene}] USER: {content}\n"
            elif role == 'assistant':
                if character_name:
                    context_text += f"[Scene {scene}] {character_name.upper()}"
                    if text_tag:
                        context_text += f" ({text_tag})"
                    context_text += f": {content}\n"
                else:
                    context_text += f"[Scene {scene}] NARRATOR"
                    if text_tag:
                        context_text += f" ({text_tag})"
                    context_text += f": {content}\n"
        context_text += "=== END GAME CONTEXT ===\n\n"
        return context_text

    def process_game_context_message(self, message, scenes_back=1):
        try:
            game_context = self.get_game_context(scenes_back)
            if game_context:
                context_text = self.format_game_context_for_llm(game_context)
                if not self.game_context_injected:
                    system_message = {
                        "role": "system",
                        "content": (
                            "You are an AI assistant helping with a single-player text adventure game. "
                            "The user may ask you to analyze, summarize, or work with the game's conversation history. "
                            "When game context is provided, use it to give accurate and helpful responses about the game."
                        )
                    }
                    self.context.insert(0, system_message)
                    self.game_context_injected = True
                enhanced_message = f"{context_text}USER QUESTION: {message}"
                self.process_normal_message(enhanced_message, already_displayed=False)
            else:
                no_context_message = (
                    "I don't have access to the current game conversation context. "
                    "This might be because there's no active game session or no conversation history available. "
                    "I'll try to help with your question based on general knowledge instead."
                )
                enhanced_message = f"SYSTEM NOTE: {no_context_message}\n\nUSER QUESTION: {message}"
                self.process_normal_message(enhanced_message, already_displayed=False)
        except Exception as e:
            self.process_normal_message(message, already_displayed=True)

    def process_rules_context_message(self, message, scenes_back=1):
        try:
            rules_context = self.get_rules_context(scenes_back)
            if rules_context:
                context_text = self.format_rules_context_for_llm(rules_context)
                rules_system_message = {
                    "role": "system",
                    "content": context_text
                }
                self.context = [msg for msg in self.context if not (msg["role"] == "system" and msg["content"].startswith("=== GAME RULES SYSTEM CONTEXT ==="))]
                self.context.insert(0, rules_system_message)
                if not self.rules_context_injected:
                    system_message = {
                        "role": "system",
                        "content": (
                            "You are an AI assistant helping with a single-player text adventure game's rules system. "
                            "You can READ, WRITE, EDIT, and DELETE rules. When rules context is provided, use it to give accurate responses. "
                            "\n\nIMPORTANT RULE WRITING GUIDELINES:\n"
                            "1. When asked to create or edit rules, ALWAYS ask for user confirmation before making changes\n"
                            "2. Present the complete JSON rule structure for review\n"
                            "3. Explain what the rule does in plain English\n"
                            "4. Use the exact schema provided in the rules context\n"
                            "5. Validate all required fields are present\n"
                            "6. For edits, show both the original and modified versions\n"
                            "7. Never write rules without explicit user approval\n"
                            "\nWhen the user confirms a rule creation/edit, respond with:\n"
                            "EXECUTE_RULE_ACTION: {\"action\": \"create|edit|delete\", \"rule_type\": \"trigger|timer\", \"rule_id\": \"id\", \"rule_data\": {...}}\n"
                            "\nThis special format will trigger the actual file operations."
                        )
                    }
                    self.context.insert(0, system_message)
                    self.rules_context_injected = True
                self.process_normal_message(message, already_displayed=True)
            else:
                no_context_message = (
                    "I don't have access to the current game rules context. "
                    "This might be because there's no active game session or no rules history available. "
                    "I'll try to help with your question based on general knowledge instead."
                )
                enhanced_message = f"SYSTEM NOTE: {no_context_message}\n\nUSER QUESTION: {message}"
                self.process_normal_message(enhanced_message, already_displayed=False)
        except Exception as e:
            self.process_normal_message(message, already_displayed=True)

    def get_rules_context(self, scenes_back=1):
        if not self.parent_app or not hasattr(self.parent_app, 'get_current_tab_data'):
            return None
        try:
            tab_data = self.parent_app.get_current_tab_data()
            if not tab_data:
                return None
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                return None
            rules_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'rules')
            if not os.path.exists(rules_dir):
                return None
            order_file = os.path.join(rules_dir, '_rules_order.json')
            rules_order = []
            if os.path.exists(order_file):
                try:
                    with open(order_file, 'r', encoding='utf-8') as f:
                        rules_order = json.load(f)
                except Exception as e:
                    print(f"[DEBUG] Error loading rules order: {e}")
            rules_data = {}
            rule_files = [f for f in os.listdir(rules_dir) if f.endswith('_rule.json')]
            for rule_file in rule_files:
                rule_path = os.path.join(rules_dir, rule_file)
                try:
                    with open(rule_path, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                        rule_id = rule_data.get('id')
                        if rule_id:
                            rules_data[rule_id] = rule_data
                except Exception as e:
                    print(f"[DEBUG] Error loading rule file {rule_file}: {e}")
            timer_rules_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'rules', 'timer_rules')
            timer_rules_data = {}
            if os.path.exists(timer_rules_dir):
                timer_rule_files = [f for f in os.listdir(timer_rules_dir) if f.endswith('_timer_rule.json')]
                for timer_rule_file in timer_rule_files:
                    timer_rule_path = os.path.join(timer_rules_dir, timer_rule_file)
                    try:
                        with open(timer_rule_path, 'r', encoding='utf-8') as f:
                            timer_rule_data = json.load(f)
                            timer_rule_id = timer_rule_data.get('id')
                            if timer_rule_id:
                                timer_rules_data[timer_rule_id] = timer_rule_data
                    except Exception as e:
                        print(f"[DEBUG] Error loading timer rule file {timer_rule_file}: {e}")
            if not rules_data and not timer_rules_data:
                return None
            rules_context = {
                'rules_order': rules_order,
                'rules_data': rules_data,
                'timer_rules_data': timer_rules_data,
                'rules_dir': rules_dir,
                'total_rules': len(rules_data),
                'total_timer_rules': len(timer_rules_data)
            }
            return rules_context
        except Exception as e:
            return None
    
    def format_rules_context_for_llm(self, rules_context):
        if not rules_context:
            return ""
        rules_data = rules_context['rules_data']
        timer_rules_data = rules_context['timer_rules_data']
        rules_order = rules_context['rules_order']
        
        context_text = f"=== GAME RULES SYSTEM CONTEXT ===\n"
        context_text += f"Total Rules: {len(rules_data)}\n"
        context_text += f"Total Timer Rules: {len(timer_rules_data)}\n\n"
        context_text += "RULES SYSTEM EXPLANATION:\n"
        context_text += "The game uses a sophisticated rules system with two types of rules:\n\n"
        context_text += "1. TRIGGER RULES: Execute based on conditions like turn count, variables, location, etc.\n"
        context_text += "   - Can apply to 'Narrator' (affects main game flow) or 'Character' (affects specific NPCs)\n"
        context_text += "   - Have conditions that must be met for the rule to trigger\n"
        context_text += "   - Have tag/action pairs that define what happens when triggered\n"
        context_text += "   - Can modify system messages, switch models, set variables, move characters, etc.\n\n"
        context_text += "2. TIMER RULES: Execute at specific intervals or after delays\n"
        context_text += "   - Can be one-time or repeating\n"
        context_text += "   - Can be triggered by scene changes, character actions, etc.\n\n"
        context_text += "=== RULE CREATION SCHEMA ===\n\n"
        context_text += "TRIGGER RULE STRUCTURE:\n"
        context_text += "{\n"
        context_text += '  "id": "unique_rule_name",\n'
        context_text += '  "description": "Human readable description",\n'
        context_text += '  "applies_to": "Narrator" or "Character",\n'
        context_text += '  "character_name": "NPC Name" (only if applies_to is Character),\n'
        context_text += '  "scope": "user_message" or "assistant_message" or "llm_reply" or "convo_llm_reply",\n'
        context_text += '  "conditions_operator": "AND" or "OR",\n'
        context_text += '  "conditions": [array of condition objects],\n'
        context_text += '  "tag_action_pairs": [array of tag/action pair objects]\n'
        context_text += "}\n\n"
        
        context_text += "=== CRITICAL SCOPING SYSTEM ===\n\n"
        context_text += "RULE EXECUTION SCOPING:\n"
        context_text += "1. RULE APPLIES_TO SCOPE:\n"
        context_text += '   - "Narrator": Rule affects main game flow and narrator responses\n'
        context_text += '   - "Character": Rule only applies to specific NPC (requires character_name)\n'
        context_text += "   - Character rules only execute when that specific character is active in scene\n\n"
        
        context_text += "2. MESSAGE SCOPE (when rules trigger):\n"
        context_text += '   - "user_message": Rule processes BEFORE assistant response (pre-phase)\n'
        context_text += '   - "assistant_message": Rule processes AFTER assistant response (post-phase)\n'
        context_text += "   - Pre-phase rules can modify system messages and context\n"
        context_text += "   - Post-phase rules can react to what was just said\n\n"
        
        context_text += "3. VARIABLE SCOPING (where variables are stored/accessed):\n"
        context_text += '   - "Global": Stored in tab data, accessible across entire game\n'
        context_text += '   - "Character": Stored in specific character file (requires character context)\n'
        context_text += '   - "Player": Stored in player character file\n'
        context_text += '   - "Setting": Stored in current setting file\n'
        context_text += '   - "Scene Characters": Stored in current setting, affects all NPCs in scene\n\n'
        
        context_text += "4. ACTION SCOPING (how actions behave based on rule context):\n"
        context_text += "   - Text Tags: Narrator rules affect narrator tags, Character rules affect character tags\n"
        context_text += "   - System Messages: Always affect the current inference context\n"
        context_text += "   - Variable operations respect the variable_scope setting\n"
        context_text += "   - Location changes can target specific actors or use rule context\n\n"
        
        context_text += "5. RULE EXECUTION PHASES:\n"
        context_text += "   PRE-PHASE (user_message scope):\n"
        context_text += "   - Triggered BEFORE assistant generates response\n"
        context_text += "   - Can modify system messages, set variables, change context\n"
        context_text += "   - Perfect for setting up conditions for the response\n"
        context_text += "   - Can use Force Narrator to override normal response flow\n\n"
        
        context_text += "   POST-PHASE (assistant_message scope):\n"
        context_text += "   - Triggered AFTER assistant generates response\n"
        context_text += "   - Can react to what was said, update game state\n"
        context_text += "   - Can trigger follow-up actions or chain to other rules\n"
        context_text += "   - Can modify variables based on response content\n\n"
        
        context_text += "6. CHARACTER RULE ACTIVATION:\n"
        context_text += "   - Character rules only execute when that specific character is active\n"
        context_text += "   - Activation occurs when character is in current scene/setting\n"
        context_text += "   - Character context is automatically provided to rule actions\n"
        context_text += "   - Character variables are accessible within character rule scope\n\n"
        
        context_text += "CONDITION TYPES:\n"
        context_text += "1. Variable Condition:\n"
        context_text += '   {"type": "Variable", "variable": "var_name", "operator": "==|!=|>|<|>=|<=|contains", "value": "comparison_value", "variable_scope": "Global|Character|Setting|Player"}\n\n'
        context_text += "2. Turn Condition:\n"
        context_text += '   {"type": "Turn", "operator": "==|!=|>|<|>=|<=", "turn": number}\n\n'
        context_text += "3. Scene Count Condition:\n"
        context_text += '   {"type": "Scene Count", "operator": "==|!=|>|<|>=|<=", "count": number}\n\n'
        context_text += "4. Geography Conditions:\n"
        context_text += '   {"type": "Setting", "geography_name": "setting_name"}\n'
        context_text += '   {"type": "Location", "geography_name": "location_name"}\n'
        context_text += '   {"type": "Region", "geography_name": "region_name"}\n'
        context_text += '   {"type": "World", "geography_name": "world_name"}\n\n'
        
        context_text += "ACTION TYPES:\n"
        context_text += "1. System Message:\n"
        context_text += '   {"type": "System Message", "value": "message text with {placeholders}", "position": "prepend|append|replace", "system_message_position": "first|last"}\n\n'
        context_text += "2. Set Variable:\n"
        context_text += '   {"type": "Set Var", "var_name": "variable_name", "var_value": "value", "variable_scope": "Global|Character|Setting|Player", "operation": "set|increment|decrement|multiply|divide|generate|from_random_list|from_var", "set_var_mode": "replace|append|prepend", "set_var_delimiter": "/"}\n\n'
        context_text += "3. Text Tag:\n"
        context_text += '   {"type": "Text Tag", "value": "tag text", "tag_mode": "replace|append|prepend"}\n\n'
        context_text += "4. Switch Model:\n"
        context_text += '   {"type": "Switch Model", "value": "model_identifier"}\n\n'
        context_text += "5. Next Rule:\n"
        context_text += '   {"type": "Next Rule", "value": "rule_id_to_execute_next"}\n\n'
        context_text += "6. Change Actor Location:\n"
        context_text += '   {"type": "Change Actor Location", "actor_name": "character_name", "location_mode": "Setting|Adjacent|Location", "target_setting": "setting_name"}\n\n'
        context_text += "7. Force Narrator:\n"
        context_text += '   {"type": "Force Narrator", "value": "", "force_narrator_order": "First|Last", "force_narrator_system_message": "system message for narrator"}\n\n'
        context_text += "8. New Scene:\n"
        context_text += '   {"type": "New Scene", "value": "scene_description"}\n\n'
        context_text += "9. Rewrite Post:\n"
        context_text += '   {"type": "Rewrite Post", "value": "rewrite_instructions"}\n\n'
        context_text += "10. Generate Content:\n"
        context_text += '   {"type": "Generate Setting", "generator_name": "generator_file_name"}\n'
        context_text += '   {"type": "Generate Story", "generator_name": "story_generator_name"}\n'
        context_text += '   {"type": "Generate Character", "generator_name": "character_generator_name"}\n'
        context_text += '   {"type": "Generate Random List", "generator_name": "list_generator_name", "count": number}\n\n'
        context_text += "11. Screen Effects:\n"
        context_text += '   {"type": "Set Screen Effect", "effect_type": "blur|fade|flicker|shake", "operation": "set|clear", "param_name": "intensity|duration|color", "param_value": "value", "enabled": true/false}\n\n'
        context_text += "12. Rule Flow Control:\n"
        context_text += '   {"type": "Skip Post", "value": ""}\n'
        context_text += '   {"type": "Exit Rule Processing", "value": ""}\n\n'
        context_text += "13. Game Over:\n"
        context_text += '   {"type": "Game Over", "game_over_message": "Custom game over message with optional HTML formatting"}\n'
        context_text += "   - Immediately stops all rule processing (like Exit Rule Processing)\n"
        context_text += "   - Performs a complete game reset (clears conversation, resets variables, etc.)\n"
        context_text += "   - Shows custom game over screen with ASCII art border\n"
        context_text += "   - Displays Load/New options to continue or restart\n"
        context_text += "   - Available in both trigger rules and timer rules\n\n"
        context_text += "14. Legacy/Deprecated Actions:\n"
        context_text += '   {"type": "Change Brightness", "value": "brightness_level"} (deprecated - use Set Screen Effect instead)\n\n'
        
        context_text += "TAG/ACTION PAIR STRUCTURE:\n"
        context_text += "{\n"
        context_text += '  "tag": "text that appears in chat",\n'
        context_text += '  "actions": [array of action objects]\n'
        context_text += "}\n\n"
        
        context_text += "TIMER RULE STRUCTURE:\n"
        context_text += "{\n"
        context_text += '  "id": "unique_timer_rule_name",\n'
        context_text += '  "description": "Human readable description",\n'
        context_text += '  "trigger_type": "interval|delay|scene_change",\n'
        context_text += '  "interval_turns": number (for interval type),\n'
        context_text += '  "delay_turns": number (for delay type),\n'
        context_text += '  "repeat": true/false,\n'
        context_text += '  "actions": [array of action objects],\n'
        context_text += '  "conditions": [optional array of condition objects]\n'
        context_text += "}\n\n"
        context_text += "TIMER RULE SPECIFIC ACTIONS:\n"
        context_text += "Timer rules support a focused set of action types:\n"
        context_text += '- "Set Var": Variable operations (same as trigger rules)\n'
        context_text += '- "Narrator Post": Force narrator to post a message\n'
        context_text += '- "Actor Post": Force specific character to post a message\n'
        context_text += '- "New Scene": Trigger a new scene\n'
        context_text += '- "Game Over": End the game with custom message\n\n'
        
        context_text += "=== VARIABLE SCOPING DETAILS ===\n\n"
        context_text += "VARIABLE STORAGE LOCATIONS:\n"
        context_text += "1. Global Variables:\n"
        context_text += "   - File: Tab data in memory, persisted with conversation\n"
        context_text += "   - Access: Available to all rules and characters\n"
        context_text += "   - Use: Game-wide state, turn counters, global flags\n\n"
        
        context_text += "2. Character Variables:\n"
        context_text += "   - File: /game/characters/{character_name}_character.json\n"
        context_text += "   - Access: Only when that character is in context\n"
        context_text += "   - Use: Character-specific stats, relationships, memories\n\n"
        
        context_text += "3. Player Variables:\n"
        context_text += "   - File: /game/characters/Player_character.json\n"
        context_text += "   - Access: Always available\n"
        context_text += "   - Use: Player stats, inventory, personal flags\n\n"
        
        context_text += "4. Setting Variables:\n"
        context_text += "   - File: /game/settings/{setting_name}_setting.json\n"
        context_text += "   - Access: Only when in that specific setting\n"
        context_text += "   - Use: Location-specific state, environmental conditions\n\n"
        
        context_text += "5. Scene Characters Variables:\n"
        context_text += "   - File: Current setting file, affects all NPCs in scene\n"
        context_text += "   - Access: All characters present in current setting\n"
        context_text += "   - Use: Shared scene state, group dynamics\n\n"
        
        context_text += "VARIABLE OPERATIONS:\n"
        context_text += "- set: Direct assignment (with string modes: replace/append/prepend)\n"
        context_text += "- increment/decrement: Numeric operations\n"
        context_text += "- multiply/divide: Mathematical operations\n"
        context_text += "- generate: Use LLM generation or random list generators\n"
        context_text += "- from_random_list: Sample from generator files\n"
        context_text += "- from_var: Copy value from another variable (any scope)\n\n"
        
        context_text += "=== ADVANCED SUBSTITUTION MECHANISMS ===\n\n"
        context_text += "PLACEHOLDER SUBSTITUTION (available in all text fields):\n"
        context_text += "1. Basic Placeholders:\n"
        context_text += "   - {character_name} - Current active character\n"
        context_text += "   - {setting_name} - Current setting\n"
        context_text += "   - {location_name} - Current location\n"
        context_text += "   - {turn_count} - Current turn number\n"
        context_text += "   - {random:1-10} - Random number in range\n\n"
        
        context_text += "2. Variable Substitution:\n"
        context_text += "   - {var:variable_name} - Value from any scope\n"
        context_text += "   - Automatically resolves scope (Global > Character > Player > Setting)\n"
        context_text += "   - Works in condition values, action values, system messages\n\n"
        
        context_text += "3. Condition-Specific Substitution:\n"
        context_text += "   - (player) - Resolves to player character name\n"
        context_text += "   - (character) - Resolves to rule's character context\n"
        context_text += "   - (setting) - Resolves to current setting name\n"
        context_text += "   - Case-insensitive, works in Variable condition values\n\n"
        
        context_text += "=== ADVANCED VARIABLE OPERATIONS ===\n\n"
        context_text += "SET VAR OPERATION MODES:\n"
        context_text += "1. String Operations (for text variables):\n"
        context_text += "   - replace: Overwrites existing value\n"
        context_text += "   - append: Adds to end with optional delimiter\n"
        context_text += "   - prepend: Adds to beginning with optional delimiter\n"
        context_text += "   - delimiter: Custom separator (default: '/')\n\n"
        
        context_text += "2. Numeric Operations:\n"
        context_text += "   - set: Direct numeric assignment\n"
        context_text += "   - increment: Add to existing value\n"
        context_text += "   - decrement: Subtract from existing value\n"
        context_text += "   - multiply: Multiply existing value\n"
        context_text += "   - divide: Divide existing value\n\n"
        
        context_text += "3. Generator Operations:\n"
        context_text += "   - generate (LLM mode): Use AI to generate content\n"
        context_text += "     * generate_instructions: Prompt for LLM\n"
        context_text += "     * generate_context: 'Last Exchange', 'User Message', 'Full Conversation'\n"
        context_text += "   - generate (Random mode): Use random generators\n"
        context_text += "     * random_type: 'Number', 'List Item', 'Dice Roll'\n"
        context_text += "     * Parameters vary by type\n"
        context_text += "   - from_random_list: Sample from generator files\n"
        context_text += "     * random_list_generator: Name of generator file\n"
        context_text += "   - from_var: Copy from another variable\n"
        context_text += "     * source_var_name: Variable to copy from\n"
        context_text += "     * source_var_scope: Scope of source variable\n\n"
        
        context_text += "=== SCREEN EFFECTS SYSTEM ===\n\n"
        context_text += "AVAILABLE SCREEN EFFECTS:\n"
        context_text += "1. Blur Effect:\n"
        context_text += "   - enabled: true/false\n"
        context_text += "   - radius: Blur intensity (1-20)\n"
        context_text += "   - animation_speed: Transition time in ms\n"
        context_text += "   - animate: Whether to animate transitions\n\n"
        
        context_text += "2. Flicker Effect:\n"
        context_text += "   - enabled: true/false\n"
        context_text += "   - intensity: Flicker strength (0.0-1.0)\n"
        context_text += "   - frequency: Flicker speed in ms\n"
        context_text += "   - color: 'white' or 'black'\n\n"
        
        context_text += "3. Static Noise Effect:\n"
        context_text += "   - enabled: true/false\n"
        context_text += "   - intensity: Noise strength (0.0-1.0)\n"
        context_text += "   - frequency: Update rate in ms\n"
        context_text += "   - dot_size: Size of noise particles\n\n"
        
        context_text += "4. Darken/Brighten Effect:\n"
        context_text += "   - enabled: true/false\n"
        context_text += "   - mode: 'darken' or 'brighten'\n"
        context_text += "   - intensity: Effect strength (0.0-1.0)\n"
        context_text += "   - animation_speed: Transition time in ms\n\n"
        
        context_text += "=== GAME OVER ACTION EXAMPLES ===\n\n"
        context_text += "TRIGGER RULE WITH GAME OVER:\n"
        context_text += "{\n"
        context_text += '  "id": "player_death_game_over",\n'
        context_text += '  "description": "End game when player health reaches zero",\n'
        context_text += '  "applies_to": "Narrator",\n'
        context_text += '  "scope": "user_message",\n'
        context_text += '  "conditions_operator": "AND",\n'
        context_text += '  "conditions": [\n'
        context_text += '    {"type": "Variable", "variable": "player_health", "operator": "<=", "value": "0", "variable_scope": "Player"}\n'
        context_text += '  ],\n'
        context_text += '  "tag_action_pairs": [\n'
        context_text += '    {\n'
        context_text += '      "tag": "GAME_OVER",\n'
        context_text += '      "actions": [\n'
        context_text += '        {\n'
        context_text += '          "type": "Game Over",\n'
        context_text += '          "game_over_message": "<h2>You Have Died!</h2><p>Your health reached zero and you could not continue your quest. The darkness consumes you...</p>"\n'
        context_text += '        }\n'
        context_text += '      ]\n'
        context_text += '    }\n'
        context_text += '  ]\n'
        context_text += "}\n\n"
        context_text += "TIMER RULE WITH GAME OVER:\n"
        context_text += "{\n"
        context_text += '  "id": "time_limit_game_over",\n'
        context_text += '  "description": "End game after 20 turns if quest not completed",\n'
        context_text += '  "trigger_type": "delay",\n'
        context_text += '  "delay_turns": 20,\n'
        context_text += '  "repeat": false,\n'
        context_text += '  "conditions": [\n'
        context_text += '    {"type": "Variable", "variable": "quest_completed", "operator": "!=", "value": "true", "variable_scope": "Global"}\n'
        context_text += '  ],\n'
        context_text += '  "actions": [\n'
        context_text += '    {\n'
        context_text += '      "type": "Game Over",\n'
        context_text += '      "game_over_message": "<h2>Time Runs Out!</h2><p>You have failed to complete your quest within the time limit. The kingdom falls to darkness...</p>"\n'
        context_text += '    }\n'
        context_text += '  ]\n'
        context_text += "}\n\n"
        context_text += "=== TIMER RULES SYSTEM ===\n\n"
        context_text += "TIMER RULE TYPES:\n"
        context_text += "1. Interval Timers:\n"
        context_text += "   - trigger_type: 'interval'\n"
        context_text += "   - interval: Fixed seconds between triggers\n"
        context_text += "   - interval_is_random: Use random intervals\n"
        context_text += "   - interval_min/interval_max: Random range\n"
        context_text += "   - repeat: true/false for recurring timers\n\n"
        
        context_text += "2. Delay Timers:\n"
        context_text += "   - trigger_type: 'delay'\n"
        context_text += "   - delay_turns: Number of turns to wait\n"
        context_text += "   - repeat: Usually false for one-time delays\n\n"
        
        context_text += "3. Game Time Timers:\n"
        context_text += "   - game_minutes/game_hours/game_days: Time intervals\n"
        context_text += "   - game_*_is_random: Use random time ranges\n"
        context_text += "   - game_*_min/game_*_max: Random ranges\n"
        context_text += "   - Triggers based on in-game time progression\n\n"
        
        context_text += "TIMER RULE EXECUTION:\n"
        context_text += "- Timer rules execute independently of user input\n"
        context_text += "- Can target specific characters or run globally\n"
        context_text += "- Support all same actions as trigger rules\n"
        context_text += "- Only execute when their tab is currently active\n"
        context_text += "- Can have conditions to control when they fire\n\n"
        
        context_text += "=== RULE EXECUTION TIMING & PHASES ===\n\n"
        context_text += "RULE EXECUTION PHASES:\n"
        context_text += "1. Pre-Phase (user_message scope):\n"
        context_text += "   - Rules execute BEFORE assistant response generation\n"
        context_text += "   - Can modify context, set variables, trigger effects\n"
        context_text += "   - System messages affect the upcoming assistant response\n\n"
        
        context_text += "2. Post-Phase (assistant_message scope):\n"
        context_text += "   - Rules execute AFTER assistant response is generated\n"
        context_text += "   - Can react to what the assistant said\n"
        context_text += "   - System messages affect future responses\n\n"
        
        context_text += "3. LLM Reply Phase (llm_reply scope):\n"
        context_text += "   - SPECIAL: Rules execute AFTER LLM response but BEFORE character processing\n"
        context_text += "   - For Narrator rules: Analyzes narrator's response\n"
        context_text += "   - For Character rules: Analyzes CHARACTER's response (after character inference)\n"
        context_text += "   - Perfect for triggering character responses or post-processing character output\n"
        context_text += "   - Allows inspection of LLM output to decide character actions or rewrite posts\n\n"
        
        context_text += "4. Conversation+LLM Reply Phase (convo_llm_reply scope):\n"
        context_text += "   - ADVANCED: Rules check both conversation history AND the latest LLM reply\n"
        context_text += "   - Provides full context for complex conditional logic\n"
        context_text += "   - Perfect for rules that need to consider conversation flow AND current response\n"
        context_text += "   - Enables sophisticated character behavior based on conversation patterns\n\n"
        
        context_text += "CHARACTER RULE ACTIVATION:\n"
        context_text += "- Character rules only execute when that character is 'active'\n"
        context_text += "- A character becomes active when mentioned in conversation\n"
        context_text += "- Character context persists until another character takes focus\n"
        context_text += "- Timer rules can target specific characters regardless of active status\n\n"
        
        context_text += "PLACEHOLDERS (for use in System Messages and other text):\n"
        context_text += "- {character_name} - Current character name\n"
        context_text += "- {setting_name} - Current setting\n"
        context_text += "- {location_name} - Current location\n"
        context_text += "- {turn_count} - Current turn number\n"
        context_text += "- {var:variable_name} - Value of a variable (respects current scope)\n"
        context_text += "- {global:variable_name} - Force global scope variable access\n"
        context_text += "- {character:variable_name} - Force character scope variable access\n"
        context_text += "- {player:variable_name} - Force player scope variable access\n"
        context_text += "- {setting:variable_name} - Force setting scope variable access\n"
        context_text += "- {random:1-10} - Random number in range\n\n"

        if rules_data:
            context_text += f"CURRENT TRIGGER RULES: {len(rules_data)} rules loaded\n"
            if rules_order:
                context_text += f"Rules in execution order: {', '.join(rules_order[:10])}"
                if len(rules_order) > 10:
                    context_text += f" (and {len(rules_order) - 10} more...)"
                context_text += "\n"
            else:
                rule_names = list(rules_data.keys())[:10]
                context_text += f"Available rules: {', '.join(rule_names)}"
                if len(rules_data) > 10:
                    context_text += f" (and {len(rules_data) - 10} more...)"
                context_text += "\n"
        if timer_rules_data:
            context_text += f"\nCURRENT TIMER RULES: {len(timer_rules_data)} timer rules loaded\n"
            timer_names = list(timer_rules_data.keys())[:10]
            context_text += f"Available timer rules: {', '.join(timer_names)}"
            if len(timer_rules_data) > 10:
                context_text += f" (and {len(timer_rules_data) - 10} more...)"
            context_text += "\n"
        context_text += "\n=== END RULES CONTEXT ===\n\n"
        return context_text

    def write_new_rule(self, rule_data, rule_type="trigger"):
        if not self.parent_app or not hasattr(self.parent_app, 'get_current_tab_data'):
            return False, "No parent app available"
        try:
            tab_data = self.parent_app.get_current_tab_data()
            if not tab_data:
                return False, "No tab data available"
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                return False, "No workflow_data_dir in tab data"
            validation_result = self.validate_rule_data(rule_data, rule_type)
            if not validation_result[0]:
                return False, f"Rule validation failed: {validation_result[1]}"
            if rule_type == "timer":
                rules_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'timer_rules')
                filename = f"{rule_data['id']}_timer_rule.json"
            else:
                rules_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'rules')
                filename = f"{rule_data['id']}_rule.json"
            os.makedirs(rules_dir, exist_ok=True)
            file_path = os.path.join(rules_dir, filename)
            if os.path.exists(file_path):
                return False, f"Rule with ID '{rule_data['id']}' already exists"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rule_data, f, indent=2)
            if rule_type == "trigger":
                self.update_rules_order(rules_dir, rule_data['id'], "add")
            return True, f"Successfully created {rule_type} rule: {rule_data['id']}"
        except Exception as e:
            return False, f"Error writing rule: {str(e)}"
    
    def edit_existing_rule(self, rule_id, rule_data, rule_type="trigger"):
        if not self.parent_app or not hasattr(self.parent_app, 'get_current_tab_data'):
            return False, "No parent app available"
        try:
            tab_data = self.parent_app.get_current_tab_data()
            if not tab_data:
                return False, "No tab data available"
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                return False, "No workflow_data_dir in tab data"
            validation_result = self.validate_rule_data(rule_data, rule_type)
            if not validation_result[0]:
                return False, f"Rule validation failed: {validation_result[1]}"
            if rule_type == "timer":
                rules_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'timer_rules')
                filename = f"{rule_id}_timer_rule.json"
            else:
                rules_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'rules')
                filename = f"{rule_id}_rule.json"
            file_path = os.path.join(rules_dir, filename)
            if not os.path.exists(file_path):
                return False, f"Rule with ID '{rule_id}' does not exist"
            backup_path = file_path + ".backup"
            with open(file_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(original_data, f, indent=2)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rule_data, f, indent=2)
            return True, f"Successfully updated {rule_type} rule: {rule_id}"
        except Exception as e:
            return False, f"Error editing rule: {str(e)}"
    
    def validate_rule_data(self, rule_data, rule_type="trigger"):
        try:
            if not isinstance(rule_data, dict):
                return False, "Rule data must be a JSON object"
            if 'id' not in rule_data:
                return False, "Rule must have an 'id' field"
            if not rule_data['id'] or not isinstance(rule_data['id'], str):
                return False, "Rule 'id' must be a non-empty string"
            if rule_type == "timer":
                required_fields = ['id', 'trigger_type']
                for field in required_fields:
                    if field not in rule_data:
                        return False, f"Timer rule missing required field: {field}"
                if rule_data['trigger_type'] not in ['interval', 'delay', 'scene_change']:
                    return False, "Timer rule trigger_type must be 'interval', 'delay', or 'scene_change'"
                if rule_data['trigger_type'] == 'interval' and 'interval_turns' not in rule_data:
                    return False, "Interval timer rule must have 'interval_turns' field"
                if rule_data['trigger_type'] == 'delay' and 'delay_turns' not in rule_data:
                    return False, "Delay timer rule must have 'delay_turns' field"
            else:
                required_fields = ['id', 'applies_to']
                for field in required_fields:
                    if field not in rule_data:
                        return False, f"Trigger rule missing required field: {field}"
                if rule_data['applies_to'] not in ['Narrator', 'Character']:
                    return False, "Rule 'applies_to' must be 'Narrator' or 'Character'"
                if rule_data['applies_to'] == 'Character' and 'character_name' not in rule_data:
                    return False, "Character rule must have 'character_name' field"
                if 'conditions' in rule_data and rule_data['conditions']:
                    for i, condition in enumerate(rule_data['conditions']):
                        if not isinstance(condition, dict) or 'type' not in condition:
                            return False, f"Condition {i+1} must be an object with 'type' field"
                if 'tag_action_pairs' in rule_data and rule_data['tag_action_pairs']:
                    for i, pair in enumerate(rule_data['tag_action_pairs']):
                        if not isinstance(pair, dict) or 'actions' not in pair:
                            return False, f"Tag/action pair {i+1} must have 'actions' field"
                        if not isinstance(pair['actions'], list):
                            return False, f"Tag/action pair {i+1} 'actions' must be an array"
            return True, "Rule validation passed"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def update_rules_order(self, rules_dir, rule_id, operation="add"):
        try:
            order_file = os.path.join(rules_dir, '_rules_order.json')
            if os.path.exists(order_file):
                with open(order_file, 'r', encoding='utf-8') as f:
                    rules_order = json.load(f)
            else:
                rules_order = []
            if operation == "add" and rule_id not in rules_order:
                rules_order.append(rule_id)
            elif operation == "remove" and rule_id in rules_order:
                rules_order.remove(rule_id)
            with open(order_file, 'w', encoding='utf-8') as f:
                json.dump(rules_order, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to update rules order: {e}")

    def delete_rule(self, rule_id, rule_type="trigger"):
        if not self.parent_app or not hasattr(self.parent_app, 'get_current_tab_data'):
            return False, "No parent app available"
        try:
            tab_data = self.parent_app.get_current_tab_data()
            if not tab_data:
                return False, "No tab data available"
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                return False, "No workflow_data_dir in tab data"
            if rule_type == "timer":
                rules_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'timer_rules')
                filename = f"{rule_id}_timer_rule.json"
            else:
                rules_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'rules')
                filename = f"{rule_id}_rule.json"
            file_path = os.path.join(rules_dir, filename)
            if not os.path.exists(file_path):
                return False, f"Rule with ID '{rule_id}' does not exist"
            backup_path = file_path + ".deleted_backup"
            with open(file_path, 'r', encoding='utf-8') as f:
                rule_data = json.load(f)
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(rule_data, f, indent=2)
            os.remove(file_path)
            if rule_type == "trigger":
                self.update_rules_order(rules_dir, rule_id, "remove")
            return True, f"Successfully deleted {rule_type} rule: {rule_id}"
        except Exception as e:
            return False, f"Error deleting rule: {str(e)}"

    def process_character_generation_message(self, message):
        try:
            if not self.parent_app or not hasattr(self.parent_app, 'get_current_tab_data'):
                self.process_normal_message(message, already_displayed=True)
                return
            tab_data = self.parent_app.get_current_tab_data()
            if not tab_data:
                self.process_normal_message(message, already_displayed=True)
                return
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                self.process_normal_message(message, already_displayed=True)
                return
            if not hasattr(self, 'character_generation_context_injected') or not self.character_generation_context_injected:
                system_message = {
                    "role": "system",
                                            "content": (
                            "You are an AI assistant specialized in character generation and management for single-player text adventure games. "
                            "You can CREATE, EDIT, and MANAGE game characters/actors and their locations in settings. "
                        "\n\nYour capabilities include:\n"
                        "1. **Character Creation**: Generate new characters with any combination of fields\n"
                        "2. **Character Editing**: Modify existing characters' specific attributes\n"
                        "3. **Location Management**: Add characters to settings, move them between locations\n"
                        "4. **Smart File Operations**: Find settings by name and update them automatically\n"
                        "5. **Flexible Generation**: Support partial edits, full generation, and location placement\n"
                        "\n**Available Character Fields:**\n"
                        "- name: Character's name\n"
                        "- description: Physical and general description\n"
                        "- personality: Character traits, temperament, behavior\n"
                        "- appearance: Detailed physical appearance\n"
                        "- status: Current condition, health, mood\n"
                        "- goals: Motivations, objectives, ambitions\n"
                        "- story: Backstory, history, key events\n"
                        "- abilities: Skills, talents, special powers\n"
                        "- equipment: Items, weapons, tools (as key-value pairs)\n"
                        "- relations: Relationships with other characters (as key-value pairs)\n"
                        "- location: Current setting/location name\n"
                        "\n**Operation Types:**\n"
                        "1. **CREATE_CHARACTER**: Generate a new character\n"
                        "2. **EDIT_CHARACTER**: Modify existing character's specific fields\n"
                        "3. **MOVE_CHARACTER**: Change character's location\n"
                        "4. **CREATE_AND_PLACE**: Generate character and add to specific setting\n"
                        "\n**IMPORTANT INSTRUCTIONS:**\n"
                        "- Always ask for confirmation before performing character operations\n"
                        "- Present clear summaries of what will be created/modified\n"
                        "- Explain the operation in plain English\n"
                        "- When user confirms, respond with the special command format:\n"
                        "\nEXECUTE_CHARACTER_ACTION: {\"action\": \"create|edit|move|create_and_place\", \"character_name\": \"name\", \"fields_to_generate\": [\"field1\", \"field2\"], \"target_location\": \"location_name\", \"instructions\": \"generation_instructions\", \"target_directory\": \"Game\"}\n"
                        "\n**Examples:**\n"
                        "- User: 'Create a merchant for the tavern' → Ask details, then CREATE_AND_PLACE\n"
                        "- User: 'Edit Sarah's personality' → Ask confirmation, then EDIT_CHARACTER\n"
                        "- User: 'Move the blacksmith to the market' → Ask confirmation, then MOVE_CHARACTER\n"
                        "- User: 'Generate equipment for John' → Ask confirmation, then EDIT_CHARACTER with equipment field\n"
                        "\nThis special format will trigger the actual character operations."
                    )
                }
                self.context.insert(0, system_message)
                self.character_generation_context_injected = True
            settings_context = self.get_available_settings_context(workflow_data_dir)
            characters_context = self.get_available_characters_context(workflow_data_dir)
            enhanced_message = f"{settings_context}{characters_context}USER REQUEST: {message}"
            self.process_normal_message(enhanced_message, already_displayed=True)
        except Exception as e:
            print(f"[ERROR] Failed to process character generation message: {e}")
            self.process_normal_message(message, already_displayed=True)

    def get_available_settings_context(self, workflow_data_dir):
        try:
            game_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
            base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
            available_settings = []
            if os.path.exists(game_settings_dir):
                for root, dirs, files in os.walk(game_settings_dir):
                    for file in files:
                        if file.endswith('_setting.json'):
                            setting_path = os.path.join(root, file)
                            try:
                                with open(setting_path, 'r', encoding='utf-8') as f:
                                    setting_data = json.load(f)
                                    setting_name = setting_data.get('name', file.replace('_setting.json', ''))
                                    location_path = os.path.relpath(root, game_settings_dir)
                                    available_settings.append({
                                        'name': setting_name,
                                        'path': location_path,
                                        'type': 'game',
                                        'actors': setting_data.get('actors', [])
                                    })
                            except Exception as e:
                                print(f"[DEBUG] Error reading game setting {setting_path}: {e}")
            if os.path.exists(base_settings_dir):
                for root, dirs, files in os.walk(base_settings_dir):
                    for file in files:
                        if file.endswith('_setting.json'):
                            setting_path = os.path.join(root, file)
                            try:
                                with open(setting_path, 'r', encoding='utf-8') as f:
                                    setting_data = json.load(f)
                                    setting_name = setting_data.get('name', file.replace('_setting.json', ''))
                                    location_path = os.path.relpath(root, base_settings_dir)
                                    if not any(s['name'].lower() == setting_name.lower() and s['type'] == 'game' for s in available_settings):
                                        available_settings.append({
                                            'name': setting_name,
                                            'path': location_path,
                                            'type': 'base',
                                            'actors': setting_data.get('actors', [])
                                        })
                            except Exception as e:
                                print(f"[DEBUG] Error reading base setting {setting_path}: {e}")
            if available_settings:
                context_text = "=== AVAILABLE GAME SETTINGS ===\n"
                context_text += f"Total Settings: {len(available_settings)}\n\n"
                for setting in available_settings[:20]:
                    context_text += f"Setting: \"{setting['name']}\"\n"
                    context_text += f"  Location: {setting['path']}\n"
                    context_text += f"  Type: {setting['type']}\n"
                    if setting['actors']:
                        context_text += f"  Current Actors: {', '.join(setting['actors'])}\n"
                    context_text += "\n"
                if len(available_settings) > 20:
                    context_text += f"... and {len(available_settings) - 20} more settings\n\n"
                context_text += "=== END SETTINGS CONTEXT ===\n\n"
                return context_text
            else:
                return "=== NO SETTINGS AVAILABLE ===\nNo game settings found for character placement.\n\n"
        except Exception as e:
            print(f"[ERROR] Failed to get settings context: {e}")
            return "=== SETTINGS CONTEXT ERROR ===\nCould not load available settings.\n\n"

    def get_available_characters_context(self, workflow_data_dir):
        try:
            game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
            base_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
            available_characters = []
            if os.path.exists(game_actors_dir):
                for file in os.listdir(game_actors_dir):
                    if file.endswith('.json'):
                        actor_path = os.path.join(game_actors_dir, file)
                        try:
                            with open(actor_path, 'r', encoding='utf-8') as f:
                                actor_data = json.load(f)
                                actor_name = actor_data.get('name', file.replace('.json', ''))
                                available_characters.append({
                                    'name': actor_name,
                                    'location': actor_data.get('location', 'Unknown'),
                                    'type': 'game',
                                    'description': actor_data.get('description', '')[:100] + '...' if len(actor_data.get('description', '')) > 100 else actor_data.get('description', '')
                                })
                        except Exception as e:
                            print(f"[DEBUG] Error reading game actor {actor_path}: {e}")
            if os.path.exists(base_actors_dir):
                for file in os.listdir(base_actors_dir):
                    if file.endswith('.json'):
                        actor_path = os.path.join(base_actors_dir, file)
                        try:
                            with open(actor_path, 'r', encoding='utf-8') as f:
                                actor_data = json.load(f)
                                actor_name = actor_data.get('name', file.replace('.json', ''))
                                if not any(c['name'].lower() == actor_name.lower() and c['type'] == 'game' for c in available_characters):
                                    available_characters.append({
                                        'name': actor_name,
                                        'location': actor_data.get('location', 'Unknown'),
                                        'type': 'base',
                                        'description': actor_data.get('description', '')[:100] + '...' if len(actor_data.get('description', '')) > 100 else actor_data.get('description', '')
                                    })
                        except Exception as e:
                            print(f"[DEBUG] Error reading base actor {actor_path}: {e}")
            if available_characters:
                context_text = "=== AVAILABLE GAME CHARACTERS ===\n"
                context_text += f"Total Characters: {len(available_characters)}\n\n"
                for character in available_characters[:15]:
                    context_text += f"Character: \"{character['name']}\"\n"
                    context_text += f"  Current Location: {character['location']}\n"
                    context_text += f"  Type: {character['type']}\n"
                    if character['description']:
                        context_text += f"  Description: {character['description']}\n"
                    context_text += "\n"
                if len(available_characters) > 15:
                    context_text += f"... and {len(available_characters) - 15} more characters\n\n"
                context_text += "=== END CHARACTERS CONTEXT ===\n\n"
                return context_text
        except Exception as e:
            return "=== CHARACTERS CONTEXT ERROR ===\nCould not load available characters.\n\n"

    def execute_character_creation(self, fields_to_generate, instructions, target_location, workflow_data_dir, target_directory):
        try:
            from generate.generate_actor import trigger_actor_creation_from_rule
            if not fields_to_generate:
                fields_to_generate = ['name', 'description', 'personality', 'appearance']
            trigger_actor_creation_from_rule(
                fields_to_generate=fields_to_generate,
                instructions=instructions,
                location=target_location,
                workflow_data_dir=workflow_data_dir,
                target_directory=target_directory
            )
            return True, f"Character creation started. Generating fields: {', '.join(fields_to_generate)}"
        except Exception as e:
            return False, f"Failed to create character: {str(e)}"

    def execute_character_edit(self, character_name, fields_to_generate, instructions, target_location, workflow_data_dir, target_directory):
        try:
            from generate.generate_actor import trigger_actor_edit_from_rule
            if not character_name:
                return False, "Character name is required for editing"
            if not fields_to_generate:
                return False, "No fields specified for editing"
            trigger_actor_edit_from_rule(
                target_actor_name=character_name,
                fields_to_generate=fields_to_generate,
                instructions=instructions,
                location=target_location,
                workflow_data_dir=workflow_data_dir,
                target_directory=target_directory
            )
            return True, f"Character '{character_name}' edit started. Updating fields: {', '.join(fields_to_generate)}"
        except Exception as e:
            return False, f"Failed to edit character '{character_name}': {str(e)}"

    def execute_character_move(self, character_name, target_location, workflow_data_dir):
        try:
            from generate.generate_actor import _add_actor_to_setting, _remove_actor_from_setting
            from core.utils import _find_setting_file_by_name
            if not character_name:
                return False, "Character name is required for moving"
            if not target_location:
                return False, "Target location is required for moving"
            current_location = self.find_character_current_location(character_name, workflow_data_dir)
            if current_location:
                _remove_actor_from_setting(character_name, current_location, workflow_data_dir)
            _add_actor_to_setting(character_name, target_location, workflow_data_dir)
            return True, f"Moved character '{character_name}' to '{target_location}'"
        except Exception as e:
            return False, f"Failed to move character '{character_name}': {str(e)}"

    def execute_character_creation_and_placement(self, fields_to_generate, instructions, target_location, workflow_data_dir, target_directory):
        try:
            from generate.generate_actor import trigger_actor_creation_from_rule
            if not target_location:
                return False, "Target location is required for create_and_place operation"
            if not fields_to_generate:
                fields_to_generate = ['name', 'description', 'personality', 'appearance', 'location']
            elif 'location' not in fields_to_generate:
                fields_to_generate.append('location')
            trigger_actor_creation_from_rule(
                fields_to_generate=fields_to_generate,
                instructions=instructions,
                location=target_location,
                workflow_data_dir=workflow_data_dir,
                target_directory=target_directory
            )
            return True, f"Character creation and placement started for '{target_location}'. Generating fields: {', '.join(fields_to_generate)}"
        except Exception as e:
            return False, f"Failed to create and place character: {str(e)}"

    def find_character_current_location(self, character_name, workflow_data_dir):
        try:
            game_settings_dir = os.path.join(workflow_data_dir, 'game', 'settings')
            if os.path.exists(game_settings_dir):
                for root, dirs, files in os.walk(game_settings_dir):
                    for file in files:
                        if file.endswith('_setting.json'):
                            setting_path = os.path.join(root, file)
                            try:
                                with open(setting_path, 'r', encoding='utf-8') as f:
                                    setting_data = json.load(f)
                                    actors = setting_data.get('actors', [])
                                    if character_name in actors:
                                        return setting_data.get('name', file.replace('_setting.json', ''))
                            except Exception as e:
                                pass
            base_settings_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
            if os.path.exists(base_settings_dir):
                for root, dirs, files in os.walk(base_settings_dir):
                    for file in files:
                        if file.endswith('_setting.json'):
                            setting_path = os.path.join(root, file)
                            try:
                                with open(setting_path, 'r', encoding='utf-8') as f:
                                    setting_data = json.load(f)
                                    actors = setting_data.get('actors', [])
                                    if character_name in actors:
                                        return setting_data.get('name', file.replace('_setting.json', ''))
                            except Exception as e:
                                pass
            return None
        except Exception as e:
            return None

    def get_conversation_dir(self):
        try:
            if not self.parent_app or not hasattr(self.parent_app, 'get_current_tab_data'):
                return CONVERSATION_DIR
            tab_data = self.parent_app.get_current_tab_data()
            if not tab_data:
                return CONVERSATION_DIR
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                return CONVERSATION_DIR
            agent_dir = os.path.join(workflow_data_dir, "agent")
            os.makedirs(agent_dir, exist_ok=True)
            return agent_dir
        except Exception as e:
            print(f"Error getting conversation directory: {e}")
            return CONVERSATION_DIR

class StandaloneAgentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #000000;
                border: 1px solid {STANDALONE_PRIMARY_COLOR};
            }}
        """)
        self.setMouseTracking(True)
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        self.title_bar = self.create_title_bar()
        main_layout.addWidget(self.title_bar)
        self.agent_panel = AgentPanel()
        main_layout.addWidget(self.agent_panel)
        self.setCentralWidget(main_widget)
        self.dragging = False
        self.resizing = False
        self.resize_grip_size = 8
        
    def create_title_bar(self):
        title_bar = QWidget()
        title_bar.setFixedHeight(30)
        title_bar.setStyleSheet(f"background-color: #000000; border-bottom: 1px solid {STANDALONE_PRIMARY_COLOR};")
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.addStretch()
        button_style = f"""
            QPushButton {{
                color: {STANDALONE_PRIMARY_COLOR}; background-color: transparent; border: none;
                font-size: 14pt; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {STANDALONE_SECONDARY_COLOR}; }}
        """
        minimize_btn = QPushButton("−")
        minimize_btn.setFixedSize(30, 30)
        minimize_btn.setStyleSheet(button_style)
        minimize_btn.clicked.connect(self.showMinimized)
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(30, 30)
        self.maximize_btn.setStyleSheet(button_style)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                color: {STANDALONE_PRIMARY_COLOR}; background-color: transparent; border: none;
                font-size: 16pt; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #ff4444; color: white; }}
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(close_btn)
        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        title_bar.mouseReleaseEvent = self.title_bar_mouse_release
        return title_bar
            
    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")
            
    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            
    def title_bar_mouse_move(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            
    def title_bar_mouse_release(self, event):
        self.dragging = False
            
    def _get_resize_edge(self, pos):
        rect = self.rect()
        grip = self.resize_grip_size
        edge = 0
        if pos.x() < grip: edge |= Qt.LeftEdge
        if pos.x() > rect.width() - grip: edge |= Qt.RightEdge
        if pos.y() < grip: edge |= Qt.TopEdge
        if pos.y() > rect.height() - grip: edge |= Qt.BottomEdge
        return edge
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.isMaximized():
            self.resize_edge = self._get_resize_edge(event.pos())
            if self.resize_edge:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geom = self.geometry()
                event.accept()
        super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        if self.resizing and not self.isMaximized():
            delta = event.globalPos() - self.resize_start_pos
            new_geom = QRect(self.resize_start_geom)
            min_w, min_h = 400, 300
            if self.resize_edge & Qt.LeftEdge:
                new_geom.setLeft(min(new_geom.right() - min_w, new_geom.left() + delta.x()))
            if self.resize_edge & Qt.RightEdge:
                new_geom.setRight(max(new_geom.left() + min_w, new_geom.right() + delta.x()))
            if self.resize_edge & Qt.TopEdge:
                new_geom.setTop(min(new_geom.bottom() - min_h, new_geom.top() + delta.y()))
            if self.resize_edge & Qt.BottomEdge:
                new_geom.setBottom(max(new_geom.top() + min_h, new_geom.bottom() + delta.y()))
            self.setGeometry(new_geom)
        elif not self.resizing and not self.isMaximized():
            edge = self._get_resize_edge(event.pos())
            if edge == (Qt.LeftEdge | Qt.TopEdge) or edge == (Qt.RightEdge | Qt.BottomEdge):
                self.setCursor(Qt.SizeFDiagCursor)
            elif edge == (Qt.RightEdge | Qt.TopEdge) or edge == (Qt.LeftEdge | Qt.BottomEdge):
                self.setCursor(Qt.SizeBDiagCursor)
            elif edge in [Qt.LeftEdge, Qt.RightEdge]:
                self.setCursor(Qt.SizeHorCursor)
            elif edge in [Qt.TopEdge, Qt.BottomEdge]:
                self.setCursor(Qt.SizeVerCursor)
            else:
                self.unsetCursor()
        super().mouseMoveEvent(event)
                
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.resizing:
            self.resizing = False
            self.unsetCursor()
        super().mouseReleaseEvent(event)

if __name__ == '__main__':
    if not os.path.exists("sounds"):
        os.makedirs("sounds")
        print("Created 'sounds' directory. Please add MessageIn.mp3, MessageOut.mp3, AgentError.mp3 for sound effects.")
    app = QApplication(sys.argv)
    window = StandaloneAgentWindow()
    window.resize(700, 800)
    window.show()
    sys.exit(app.exec_())
