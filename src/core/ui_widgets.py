from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QScrollArea, QFrame, QSizePolicy, QPushButton
from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import pygame
import re
import os
import json
from bs4 import BeautifulSoup, NavigableString
import markdown2

def is_valid_widget(widget):
    if not widget:
        return False
    try:
        widget.objectName()
        return True
    except (RuntimeError, Exception):
        return False

def adjust_color_brightness(hex_color, factor):
    if not isinstance(hex_color, str) or not hex_color.startswith('#'):
        return hex_color
    color = QColor(hex_color)
    if not color.isValid():
        return hex_color
    h, s, v, a = color.getHsv()
    new_v = min(255, int(v * factor))
    new_color = QColor.fromHsv(h, s, new_v, a)
    return new_color.name()

class CodeClickableTextEdit(QTextEdit):
    def __init__(self, main_ui_ref, parent=None):
        super().__init__(parent)
        self.main_ui = main_ui_ref
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        if self.main_ui and hasattr(self.main_ui, 'request_save_for_current_tab'):
            self.textChanged.connect(self.on_text_changed)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            return
        super().mousePressEvent(event)

    def show_context_menu(self, pos):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        copy_action = menu.addAction("Copy Code Block")
        copy_action.triggered.connect(self.copy_code_block)
        menu.exec_(self.mapToGlobal(pos))

    def copy_code_block(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            code_match = re.match(r"^```(?:\w+)?\n(.*?)\n```$", selected_text, re.DOTALL | re.IGNORECASE)
            if code_match:
                code_block = code_match.group(1).strip()
            elif selected_text.startswith("```") and selected_text.endswith("```"):
                code_block = selected_text[3:-3].strip()
            else:
                code_block = selected_text
            if code_block:
                clipboard = QApplication.clipboard()
                clipboard.setText(code_block)
            else:
                pass
        else:
            pass

    def on_text_changed(self):
        if self.main_ui and hasattr(self.main_ui, 'request_save_for_current_tab'):
            self.main_ui.request_save_for_current_tab()

class ChatbotInputField(QWidget):
    load_requested = pyqtSignal(int)
    new_requested = pyqtSignal(int)
    intro_enter_pressed = pyqtSignal(int)
    def __init__(self, main_ui_ref, parent=None, theme_colors=None, save_check_callback=None, tab_index=None):
        super().__init__(parent)
        self.main_ui = main_ui_ref
        self.tab_index = tab_index
        self.theme_colors = theme_colors or {'base_color': '#00FF66', 'bg_color': '#181818'}
        self.save_check_callback = save_check_callback
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        self.text_input = QTextEdit(self)
        self.text_input.setAcceptRichText(False)
        self.text_input.setMaximumHeight(90)
        self.text_input.setCursorWidth(4)
        self.text_input.setObjectName("ChatbotTextInputArea")
        self.text_input.keyPressEvent = self._text_input_keyPressEvent
        self._intro_button_layout = QHBoxLayout()
        self._intro_button_layout.addStretch(1)
        self.load_button = QPushButton("LOAD")
        self.load_button.setObjectName("IntroLoadButton")
        self.load_button.setFont(QFont('Consolas', 10, QFont.Bold))
        self.load_button.setMinimumSize(80, 35)
        self.load_button.clicked.connect(lambda: self.load_requested.emit(self.tab_index) if self.tab_index is not None else self.load_requested.emit(-1))
        self.load_button.setFocusPolicy(Qt.NoFocus)
        def load_intro_mouse_press(event):
            if self.main_ui and hasattr(self.main_ui, 'hover_message_sound') and self.main_ui.hover_message_sound:
                try:
                    self.main_ui.hover_message_sound.play()
                except Exception as e:
                    print(f"Error playing hover_message_sound: {e}")
            QPushButton.mousePressEvent(self.load_button, event)
        self.load_button.mousePressEvent = load_intro_mouse_press
        self._intro_button_layout.addWidget(self.load_button)
        self.new_button = QPushButton("NEW")
        self.new_button.setObjectName("IntroNewButton")
        self.new_button.setFont(QFont('Consolas', 10, QFont.Bold))
        self.new_button.setMinimumSize(100, 45)
        self.new_button.clicked.connect(lambda: self.new_requested.emit(self.tab_index) if self.tab_index is not None else self.new_requested.emit(-1))
        self.new_button.setFocusPolicy(Qt.NoFocus)
        def new_intro_mouse_press(event):
            if self.main_ui and hasattr(self.main_ui, 'hover_message_sound') and self.main_ui.hover_message_sound:
                try:
                    self.main_ui.hover_message_sound.play()
                except Exception as e:
                    print(f"Error playing hover_message_sound: {e}")
            QPushButton.mousePressEvent(self.new_button, event)
        self.new_button.mousePressEvent = new_intro_mouse_press
        self._intro_button_layout.addWidget(self.new_button)
        self._intro_button_layout.addStretch(1)
        self._intro_button_widget = QWidget(self)
        self._intro_button_widget.setLayout(self._intro_button_layout)
        self._main_layout.addWidget(self.text_input)
        self._main_layout.addWidget(self._intro_button_widget)
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_on = False
        self._current_state = 'normal'
        self._intro_prompt_text = ""
        self._intro_ready_for_enter = False
        self.set_input_state('normal')
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
    def toPlainText(self):
        return self.text_input.toPlainText()
    def clear(self):
        self.text_input.clear()
    def setFocus(self):
        if self._current_state in ['normal', 'blinking']:
            self.text_input.setFocus()
        else:
            if self._current_state == 'intro' and self.new_button.isVisible():
                self.new_button.setFocus()
            else:
                super().setFocus()
    def set_input_state(self, state):
        self._blink_timer.stop()
        self._blink_on = False
        self._current_state = state
        base_color = self.theme_colors.get('base_color', '#00FF66')
        bg_color = self.theme_colors.get('bg_color', '#181818')
        self.text_input.setVisible(False)
        self._intro_button_widget.setVisible(False)
        self.load_button.setVisible(False)
        self.new_button.setVisible(False)
        self.setMaximumHeight(16777215)
        if hasattr(self, '_chargen_widget'):
            self._chargen_widget.setVisible(False)
            
        if state == 'normal':
            self.text_input.setVisible(True)
            self.text_input.setReadOnly(False)
            self.text_input.setEnabled(True)
            text_color = QColor(base_color).darker(150).name()
            border_color = QColor(base_color).darker(300).name()
            self.text_input.setStyleSheet(f"""
                QTextEdit#ChatbotTextInputArea {{
                    background: {bg_color};
                    border: 2px solid {border_color};
                    color: {text_color};
                    padding: 5px;
                    font-family: Consolas;
                    font-size: 16pt;
                }}
            """)
            self.text_input.setCursorWidth(4)
            self.text_input.setAlignment(Qt.AlignLeft)
            self.setMaximumHeight(self.text_input.maximumHeight())
        elif state == 'blinking':
            self.text_input.setVisible(True)
            self.text_input.setReadOnly(False)
            self.text_input.setEnabled(True)
            self._blink_timer.start(400)
            self._toggle_blink()
            self.text_input.setCursorWidth(4)
            self.setMaximumHeight(self.text_input.maximumHeight())
            self.text_input.setFocus()
            self.text_input.installEventFilter(self)
            self._has_stopped_blinking = False
        elif state == 'disabled':
            self.text_input.setVisible(True)
            self.text_input.setReadOnly(True)
            self.text_input.setEnabled(False)
            disabled_text_color = QColor(bg_color).lighter(130).name()
            self.text_input.setStyleSheet(f"QTextEdit#ChatbotTextInputArea {{ border: 2px solid {bg_color}; background: {bg_color}; color: {disabled_text_color}; padding: 5px; }}")
            self.text_input.setCursorWidth(0)
            self.setMaximumHeight(self.text_input.maximumHeight())
        elif state == 'intro_streaming':
            self.text_input.setVisible(True)
            self.text_input.setReadOnly(True)
            self.text_input.setEnabled(True)
            self._intro_ready_for_enter = False
            self._intro_prompt_text = ""
            text_color = QColor(base_color).lighter(140).name()
            self.text_input.setStyleSheet(f"""
                QTextEdit#ChatbotTextInputArea {{
                    background: {bg_color};
                    border: 2px solid {bg_color};
                    color: {text_color};
                    padding: 5px;
                    font-family: Consolas;
                    font-size: 14pt;
                }}
            """)
            self.text_input.setCursorWidth(0)
            self.text_input.clear()
            self.text_input.setAlignment(Qt.AlignCenter)
            self.setMaximumHeight(self.text_input.maximumHeight())
        elif state == 'intro':
            self._intro_button_widget.setVisible(True)
            saves_exist = self.save_check_callback() if self.save_check_callback else False
            self.load_button.setVisible(saves_exist)
            self.new_button.setVisible(True)
            button_style = f"""
                QPushButton {{
                    background-color: transparent;
                    border: 2px solid {base_color};
                    color: {base_color};
                    padding: 8px 15px;
                    min-width: 100px;
                    min-height: 40px;
                    font-size: 11pt;
                }}
                QPushButton:hover {{
                    background-color: {QColor(base_color).lighter(110).name()};
                    color: {bg_color};
                }}
                QPushButton:pressed {{
                    background-color: {QColor(base_color).darker(110).name()};
                    color: {bg_color};
                }}
            """
            self.load_button.setStyleSheet(button_style)
            self.new_button.setStyleSheet(button_style)
            button_height = self.new_button.sizeHint().height()
            layout_margins = self._intro_button_layout.contentsMargins()
            required_height = button_height + layout_margins.top() + layout_margins.bottom() + 10
            self.setMinimumHeight(required_height)
            self.setMaximumHeight(self.text_input.maximumHeight())
        elif state == 'chargen':
            self.text_input.setVisible(False)
            self._intro_button_widget.setVisible(False)
            self.load_button.setVisible(False)
            self.new_button.setVisible(False)
            if hasattr(self, '_chargen_widget'):
                self._chargen_widget.setVisible(False)
        elif state == 'game_over':
            self.text_input.setVisible(True)
            self.text_input.setReadOnly(True)
            self.text_input.setEnabled(True)
            self._intro_ready_for_enter = False
            self._intro_prompt_text = ""
            text_color = QColor(base_color).lighter(140).name()
            self.text_input.setStyleSheet(f"""
                QTextEdit#ChatbotTextInputArea {{
                    background: {bg_color};
                    border: 2px solid {bg_color};
                    color: {text_color};
                    padding: 5px;
                    font-family: Consolas;
                    font-size: 14pt;
                }}
            """)
            self.text_input.setCursorWidth(0)
            self.text_input.clear()
            self.text_input.setAlignment(Qt.AlignCenter)
            self.setMaximumHeight(self.text_input.maximumHeight())
        


    def set_intro_prompt(self, text, ready_for_enter=False):
        if self._current_state not in ['intro_streaming', 'game_over']:
            return
        self._intro_prompt_text = text
        self._intro_ready_for_enter = ready_for_enter
        base_color = self.theme_colors.get('base_color', '#00FF66')
        bg_color = self.theme_colors.get('bg_color', '#181818')
        if ready_for_enter:
            text_color = QColor(base_color).name()
            self.text_input.setStyleSheet(f"""
                QTextEdit#ChatbotTextInputArea {{
                    background: {bg_color};
                    border: 2px solid {bg_color};
                    color: {text_color};
                    padding: 5px;
                    font-family: Consolas;
                    font-size: 14pt;
                }}
            """)
            if "continue" in text.lower():
                self._blink_timer.start(500)
                self._blink_on = True
                self._toggle_blink()
        else:
            text_color = QColor(base_color).lighter(140).name()
            self.text_input.setStyleSheet(f"""
                QTextEdit#ChatbotTextInputArea {{
                    background: {bg_color};
                    border: 2px solid {bg_color};
                    color: {text_color};
                    padding: 5px;
                    font-family: Consolas;
                    font-size: 14pt;
                }}
            """)
        self.text_input.setText(text)
        self.text_input.setAlignment(Qt.AlignCenter)
    def _toggle_blink(self):
        if self._current_state != 'blinking' and self._current_state != 'intro_streaming':
            self._blink_timer.stop()
            return
        self._blink_on = not self._blink_on
        base_color = self.theme_colors.get('base_color', '#00FF66')
        bg_color = self.theme_colors.get('bg_color', '#181818')
        qcolor = QColor(base_color)
        if self._current_state == 'intro_streaming':
            if self._blink_on:
                self.text_input.setText(self._intro_prompt_text)
            else:
                self.text_input.setText("")
            self.text_input.setAlignment(Qt.AlignCenter)
            return
        if self._blink_on:
            border_color = qcolor.darker(300).name()
        else:
            border_color = qcolor.darker(250).name()
        self.text_input.setStyleSheet(f"QTextEdit#ChatbotTextInputArea {{ border: 2px solid {border_color}; background: {bg_color}; color: inherit; padding: 5px; }}")
    def _text_input_keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and (event.modifiers() & Qt.ShiftModifier):
            self.text_input.insertPlainText("\n")
        elif event.key() == Qt.Key_Return:
            if self._current_state in ['intro_streaming', 'game_over']:
                if self._intro_ready_for_enter:
                    self.setFocus()
                    self.text_input.setFocus()
                    self.intro_enter_pressed.emit(self.tab_index if self.tab_index is not None else -1)
                return

            if self.main_ui and hasattr(self.main_ui, 'on_enter_pressed'):
                self.main_ui.on_enter_pressed()
        else:
            QTextEdit.keyPressEvent(self.text_input, event)
    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors or {'base_color': '#00FF66', 'bg_color': '#181818'}
        self.set_input_state(self._current_state)
        self._apply_themed_cursor()
    def _apply_themed_cursor(self):
        if hasattr(self.main_ui, 'themed_cursors') and self.main_ui.themed_cursors:
            text_cursor = self.main_ui.themed_cursors.get('text')
            if text_cursor:
                self.text_input.viewport().setCursor(text_cursor)
                return

    
    def eventFilter(self, obj, event):
        if obj == self.text_input and self._current_state == 'blinking' and not getattr(self, '_has_stopped_blinking', False):
            if event.type() in (QEvent.MouseButtonPress, QEvent.KeyPress, QEvent.FocusIn):
                self._has_stopped_blinking = True
                self._blink_timer.stop()
                self.set_input_state('normal')
                self.text_input.removeEventFilter(self)
                return False
        return super().eventFilter(obj, event)
class ClickableLabel(QLabel):
    def mousePressEvent(self, event):
        if self.parentWidget():
            parent_event = event.__class__(event.type(), event.pos(), event.button(), event.buttons(), event.modifiers())
            QApplication.sendEvent(self.parentWidget(), parent_event)
        else:
            super().mousePressEvent(event)
class ChatMessageListWidget(QScrollArea):
    def __init__(self, theme_colors, character_name="Assistant", parent=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.character_name = character_name
        self.tab_data = {}
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setObjectName("ChatMessageListWidget")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.container = QWidget()
        self.container.setObjectName("ChatMessageListWidget_container")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.container.setLayout(self.layout)
        self.container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setWidget(self.container)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.setFrameShape(QFrame.NoFrame)
        self._event_filter_installed = False
        self._last_theme = None
    def eventFilter(self, source, event):
        if source is self.viewport() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                if not self._is_left_splitter_open():
                    return super().eventFilter(source, event)
                widget_at_click = self.container.childAt(self.viewport().mapFromGlobal(event.globalPos()))
                is_click_on_message = False
                parent_check = widget_at_click
                while parent_check:
                    if parent_check.__class__.__name__ == 'ChatMessageWidget':
                        is_click_on_message = True
                        break
                    if parent_check.__class__.__name__ == 'ClickableLabel' and parent_check.parentWidget() and parent_check.parentWidget().__class__.__name__ == 'ChatMessageWidget':
                        is_click_on_message = True
                        break
                    parent_check = parent_check.parentWidget() if hasattr(parent_check, 'parentWidget') else None
                if not is_click_on_message and ChatMessageWidget._selected_widget:
                    try:
                        if is_valid_widget(ChatMessageWidget._selected_widget):
                            ChatMessageWidget._selected_widget.deselect()
                            ChatMessageWidget._selected_widget = None
                    except RuntimeError as e:
                        ChatMessageWidget._selected_widget = None
        elif event.type() == QEvent.Resize and source is self.container:
            self._scroll_to_bottom()
            return True
        return super().eventFilter(source, event)

    def _is_left_splitter_open(self):
        try:
            widget = self
            main_app = None
            while widget:
                if hasattr(widget, 'tabs_data') and hasattr(widget, 'current_tab_index'):
                    main_app = widget
                    break
                widget = widget.parentWidget()
            if not main_app:
                return False
            current_tab_index = getattr(main_app, 'current_tab_index', -1)
            if current_tab_index < 0 or current_tab_index >= len(main_app.tabs_data):
                return False
            tab_data = main_app.tabs_data[current_tab_index]
            if not tab_data or 'splitter' not in tab_data:
                return False
            main_splitter = tab_data['splitter']
            if not main_splitter:
                return False
            
            sizes = main_splitter.sizes()
            if len(sizes) >= 1:
                return sizes[0] > 0
            return False
        except Exception as e:
            return False
    def _optimize_ellipsis_animations(self):
        try:
            for i in range(self.layout.count()):
                widget = self.layout.itemAt(i).widget()
                if widget and widget.__class__.__name__ == 'ChatMessageWidget' and is_valid_widget(widget):
                    pass
        except Exception as e:
            pass
    def add_message(self, role, content, immediate=False, text_tag=None, scene_number=1, latest_scene_in_context=1, prompt_finished_callback=None, character_name=None, post_effects=None):
        if not self._event_filter_installed:
            self.viewport().installEventFilter(self)
            self.container.installEventFilter(self)
            self.verticalScrollBar().valueChanged.connect(self._optimize_ellipsis_animations)
            self._event_filter_installed = True
        name_to_use = character_name if character_name is not None else self.character_name
        msg_widget = ChatMessageWidget(
            role, content, self.theme_colors, name_to_use, text_tag,
            message_scene=scene_number, latest_scene_in_context=latest_scene_in_context,
            parent=self.container,
            prompt_finished_callback=prompt_finished_callback,
            post_effects=post_effects
        )
        self.layout.addWidget(msg_widget)
        msg_widget.set_message_content(immediate=immediate)
        self._scroll_to_bottom()
        return msg_widget
    def clear_messages(self):
        while self.layout.count() > 0:
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                if isinstance(widget, ChatMessageWidget):
                    widget.stop_timers()
                widget.setParent(None)
                widget.deleteLater()
        ChatMessageWidget._selected_widget = None
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(self.verticalScrollBar().maximum()))

    def update_theme(self, new_theme):
        if self._last_theme == new_theme:
            return
        self._last_theme = new_theme.copy()
        self.theme_colors = new_theme.copy()
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget.__class__.__name__ == 'ChatMessageWidget' and is_valid_widget(widget):
                try:
                    widget.update_theme(new_theme)
                except RuntimeError as e:
                    pass
            elif widget:
                pass

    def update_all_message_scene_contexts(self, latest_scene_in_context):
        message_widgets = self.findChildren(ChatMessageWidget)
        for widget in message_widgets:
            if hasattr(widget, 'update_scene_context') and hasattr(widget, 'message_scene'):
                widget.update_scene_context(widget.message_scene, latest_scene_in_context)
    
    def force_complete_all_streaming(self):
        completed_any = False
        message_widgets = self.findChildren(ChatMessageWidget)
        for widget in message_widgets:
            if hasattr(widget, 'force_complete_streaming'):
                if widget.force_complete_streaming():
                    completed_any = True
        return completed_any
    
    def force_rewrap_all_messages(self):
        try:
            for i in range(self.layout.count()):
                widget = self.layout.itemAt(i).widget()
                if widget and widget.__class__.__name__ == 'ChatMessageWidget' and is_valid_widget(widget):
                    if hasattr(widget, 'label') and hasattr(widget.label, 'setWordWrap'):
                        current_text = widget.label.text()
                        widget.label.setWordWrap(True)
                        widget.label.clear()
                        QApplication.processEvents()
                        widget.label.setText(current_text)
                        widget.label.adjustSize()
                        widget.adjustSize()
                        widget.updateGeometry()
                        QApplication.processEvents()
        except Exception as e:
            print(f"Error in force_rewrap_all_messages: {e}")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, '_rewrap_timer'):
            self._rewrap_timer = QTimer()
            self._rewrap_timer.setSingleShot(True)
            self._rewrap_timer.timeout.connect(self.force_rewrap_all_messages)
        self._rewrap_timer.stop()
        self._rewrap_timer.start(50)

    def get_message_roles(self):
        roles = []
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget and hasattr(widget, 'role'):
                roles.append(widget.role)
        return roles

class ChatMessageWidget(QFrame):
    _selected_widget = None

    def __init__(self, role, content, theme_colors, character_name="Assistant", text_tag=None, message_scene=1, latest_scene_in_context=1, parent=None, prompt_finished_callback=None, post_effects=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        import copy
        self.base_theme_colors = copy.deepcopy(theme_colors) if theme_colors else {}
        self.character_name = character_name
        self.text_tag = text_tag
        self.message_scene = message_scene
        self.latest_scene_in_context = latest_scene_in_context
        self._is_dimmed = (self.message_scene < self.latest_scene_in_context)
        self._prompt_finished_callback = prompt_finished_callback
        self.post_effects = post_effects or {}
        self.theme_colors = self._get_colors_with_effects()
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setObjectName("ChatMessageWidget")
        self.setStyleSheet(self._base_style())
        self.setMouseTracking(True)
        self._selected = False
        self._init_ui()
        self.setMinimumHeight(0)
        self._streaming_timer = None
        self._full_html_content = ""
        self._displayed_content = ""
        self._prefix_html = ""
        self._chars_per_tick = 2
        self._soup = None
        self._has_ellipsis = False
        self._ellipsis_timer = None
        self._ellipsis_groups = []
        self._ellipsis_states = []
        self._ellipsis_groups_visible = []
        self._is_streaming = False
        self._selectable = True
        self._pause_timer = None
        self._intro_anim_timer = None
        self._intro_target_text = ""
        self._intro_current_text = ""
        self._intro_char_index = 0
        self._intro_html_template = ""
        self._intro_text_span_template = ""
        self._intro_desc_anim_timer = None
        self._intro_desc_target_text = ""
        self._intro_desc_current_text = ""
        self._intro_desc_char_index = 0
        self._intro_prompt_anim_timer = None
        self._intro_prompt_target_text = "Press NEW to begin..."
        self._intro_prompt_current_text = ""
        self._intro_prompt_char_index = 0
        self._intro_prompt_delay_timer = None
        self._intro_prompt_blink_timer = None
        self._intro_prompt_blink_visible = True
        self._intro_blink_timer = None
        self._intro_blink_count = 0
        self._intro_blink_state_visible = True
        self._animation_in_progress = False
        self._current_animation_stage = None
        self._estimated_final_stream_height = 0
        self.hover_sound = None
        self.select_sound = None
        self._diagnostic_counter = 0
        self._force_complete_counter = 0
        mixer_initialized = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                mixer_initialized = pygame.mixer.get_init()
            else:
                mixer_initialized = True
        except pygame.error as e:
            pass
        except Exception as e:
            pass
        if mixer_initialized:
            try:
                self.hover_sound = pygame.mixer.Sound("sounds/hoverMessage.mp3")
            except pygame.error as e:
                pass
            except Exception as e:
                pass

            try:
                self.select_sound = pygame.mixer.Sound("sounds/selectMessage.mp3")
            except pygame.error as e:
                pass
            except Exception as e:
                pass
        else:
            pass

    def _is_left_splitter_open(self):
        try:
            widget = self
            main_app = None
            while widget:
                if hasattr(widget, 'tabs_data') and hasattr(widget, 'current_tab_index'):
                    main_app = widget
                    break
                widget = widget.parentWidget()
            if not main_app:
                parent_list = self.parent_list_widget()
                if parent_list:
                    widget = parent_list
                    while widget:
                        if hasattr(widget, 'tabs_data') and hasattr(widget, 'current_tab_index'):
                            main_app = widget
                            break
                        widget = widget.parentWidget()
            if not main_app:
                return False
            current_tab_index = getattr(main_app, 'current_tab_index', -1)
            if current_tab_index < 0 or current_tab_index >= len(main_app.tabs_data):
                return False
            tab_data = main_app.tabs_data[current_tab_index]
            if not tab_data or 'splitter' not in tab_data:
                return False
            main_splitter = tab_data['splitter']
            if not main_splitter:
                return False
            sizes = main_splitter.sizes()
            if len(sizes) >= 1:
                return sizes[0] > 0
            return False
        except Exception as e:
            return False

    def _get_colors_with_effects(self):
        import copy
        colors = copy.deepcopy(self.base_theme_colors)
        if self.post_effects and 'brightness' in self.post_effects:
            brightness = self.post_effects['brightness']
            base_color = colors.get("base_color", "#00ff66")
            adjusted_base_color = adjust_color_brightness(base_color, brightness)
            colors["base_color"] = adjusted_base_color
        return colors

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        self.label = ClickableLabel()
        self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.label.setStyleSheet("background: transparent; padding: 5px;")
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    def _render_content(self):
        if self.role == 'intro':
            soup_intro = BeautifulSoup(self.content, 'html.parser')
            pre_tag = soup_intro.find('pre')
            if pre_tag:
                base_hex_intro = self.theme_colors.get("base_color", "#00ff66")
                pre_style = f"color: {base_hex_intro}; font-family: Consolas; text-align: center; margin: 10px 0 5px 0;"
                if 'style' in pre_tag.attrs:
                     pre_tag['style'] = pre_style + ";" + pre_tag['style']
                else:
                     pre_tag['style'] = pre_style

        self._has_ellipsis = False
        base_hex = self.theme_colors.get("base_color", "#00ff66")
        normal_base_color = QColor(base_hex)
        if not normal_base_color.isValid(): 
            normal_base_color = QColor("#00ff66")
        if self.role == 'user':
            text_color_to_use = normal_base_color.darker(120).name()
        elif self.role == 'assistant':
            text_color_to_use = base_hex
        elif self.role == 'system':
            text_color_to_use = normal_base_color.lighter(120).name()
        else:
            text_color_to_use = base_hex
        base_color_obj = QColor(base_hex)
        if base_color_obj.isValid():
            tag_color_to_use = base_color_obj.lighter(130).name()
            name_color_to_use = base_color_obj.lighter(130).name()
        else:
            tag_color_to_use = base_hex
            name_color_to_use = text_color_to_use
        if self._is_dimmed:
            text_color = QColor(text_color_to_use)
            if text_color.isValid():
                dimmed_text_color = text_color.darker(200)
                if dimmed_text_color.isValid():
                    text_color_to_use = dimmed_text_color.name()
            name_color = QColor(name_color_to_use)
            if name_color.isValid():
                dimmed_name_color = name_color.darker(200)
                if dimmed_name_color.isValid():
                    name_color_to_use = dimmed_name_color.name()
            tag_color = QColor(tag_color_to_use)
            if tag_color.isValid():
                dimmed_tag_color = tag_color.darker(200)
                if dimmed_tag_color.isValid():
                    tag_color_to_use = dimmed_tag_color.name()
        r_quote, g_quote, b_quote = normal_base_color.red(), normal_base_color.green(), normal_base_color.blue()
        quote_color_dynamic = f"rgba({min(r_quote + 120, 255)}, {min(g_quote + 120, 255)}, {min(b_quote + 120, 255)}, 1.0)"
        prefix_html = ""
        text_tag_html = ""
        if self.text_tag:
            tag_style = f"color: {tag_color_to_use}; text-align: center; margin-bottom: 3px; font-style: normal;"
            text_tag_html = f'<p style="{tag_style}">{self.text_tag}</p>'
        prefix_base = ""
        apply_prefix_style = False
        prefix_style_color = name_color_to_use
        prefix_is_italic = False
        if self.role == 'user':
            player_name = self._get_player_character_name()
            prefix_base = player_name if player_name else "You"
            apply_prefix_style = True
        elif self.role == 'assistant':
            if self.character_name and self.character_name.strip().lower() != 'narrator':
                prefix_base = self.character_name
                apply_prefix_style = True
        elif self.role == 'system':
            prefix_base = "System"
            apply_prefix_style = True
            prefix_is_italic = True
        if prefix_base:
            prefix_base_with_colon = f"{prefix_base}:"
            style = f'margin-bottom: 2px;'
            if apply_prefix_style:
                style += f' color: {prefix_style_color};'
            if prefix_is_italic:
                style += f' font-style: italic;'
            prefix_html = f'<p style="{style}">{prefix_base_with_colon}</p>'
        content_str = self.content
        if content_str is None:
            content_str = ""
        if self.role == 'intro':
            soup = BeautifulSoup(content_str, 'html.parser')
        else:
            content_html_md = markdown2.markdown(content_str, extras=["fenced-code-blocks", "code-friendly"])
            soup = BeautifulSoup(content_html_md, 'html.parser')
        quote_chars = r'"“'
        closing_quote_chars = r'"”'
        non_tag_non_quote_char = rf'[^<{quote_chars}{closing_quote_chars}]'
        simple_inline_tag = rf'<(?:em|strong|i|b)\b[^>]*>.*?<\/(?:em|strong|i|b)>'
        inner_quote_content = rf'(?:{non_tag_non_quote_char}*?(?:{simple_inline_tag})?)*?{non_tag_non_quote_char}*?'
        quote_pattern_str = rf'([{quote_chars}])({inner_quote_content})([{closing_quote_chars}])'
        quote_pattern = re.compile(quote_pattern_str, re.DOTALL)

        def repl_quote_match(match_obj):
            return f'<span style="color: {quote_color_dynamic};">{match_obj.group(0)}</span>'
        for block_tag in soup.find_all(['p', 'li', 'div']):
            try:
                original_inner_html = block_tag.decode_contents()
                modified_inner_html = quote_pattern.sub(repl_quote_match, original_inner_html)
                if modified_inner_html != original_inner_html:
                    block_tag.clear()
                    new_inner_soup = BeautifulSoup(modified_inner_html, 'html.parser')
                    for child_node in list(new_inner_soup.contents):
                        block_tag.append(child_node.extract())
            except Exception as e:
                pass
        text_nodes_for_ellipsis = soup.find_all(text=True, recursive=True)
        for node in text_nodes_for_ellipsis:
            if node.parent.name in ['code', 'pre', 'style', 'script']:
                continue
            original_text = str(node)
            original_text = original_text.replace('\u2026', '...')
            if '...' not in original_text:
                continue
            new_fragments = []
            last_end = 0
            for match in re.finditer(r'\.\.\.', original_text):
                start, end = match.span()
                starts_cleanly = (start == 0) or (original_text[start-1].isspace())
                ends_nicely = (end == len(original_text)) or original_text[end].isspace() or original_text[end] == '"'
                ends_cleanly_no_quote = (end == len(original_text)) or original_text[end].isspace()
                if start > last_end:
                    new_fragments.append(NavigableString(original_text[last_end:start]))
                should_animate = (ends_nicely and not starts_cleanly) or (starts_cleanly and ends_cleanly_no_quote)
                if should_animate:
                    ellipsis_marker_span = soup.new_tag('span')
                    ellipsis_marker_span['class'] = 'ellipsis_marker'
                    dot1 = soup.new_tag('span')
                    dot1.string = '.'
                    ellipsis_marker_span.append(dot1)
                    dot2 = soup.new_tag('span')
                    dot2.string = '.'
                    ellipsis_marker_span.append(dot2)
                    dot3 = soup.new_tag('span')
                    dot3.string = '.'
                    ellipsis_marker_span.append(dot3)
                    new_fragments.append(ellipsis_marker_span)
                    self._has_ellipsis = True
                else:
                    new_fragments.append(NavigableString('...'))
                last_end = end
            if last_end < len(original_text):
                new_fragments.append(NavigableString(original_text[last_end:]))
            if new_fragments:
                node.replace_with(*new_fragments)
        content_html_processed = str(soup)
        code_border_color = tag_color_to_use
        content_html_formatted = self._format_code_blocks(content_html_processed, code_border_color)
        body_wrapper_open_tag = f'<span style="color: {text_color_to_use};">'
        body_wrapper_close_tag = '</span>'
        css_reset = "<style>p { margin-top: 0; margin-bottom: 0; }</style>"
        header_html_with_reset = css_reset + text_tag_html + prefix_html
        return header_html_with_reset, body_wrapper_open_tag, content_html_formatted, body_wrapper_close_tag

    def set_message_content(self, immediate=False):
        self.stop_timers()
        self._header_html, self._body_wrapper_open_tag, body_inner_html_to_tokenize, self._body_wrapper_close_tag = self._render_content()
        self._full_html_content = self._body_wrapper_open_tag + body_inner_html_to_tokenize + self._body_wrapper_close_tag
        self._soup = BeautifulSoup(self._full_html_content, "html.parser")
        self._ellipsis_groups = []
        self._ellipsis_states = []
        self._ellipsis_groups_visible = []
        if self._has_ellipsis:
            marker_spans = self._soup.find_all('span', class_='ellipsis_marker')
            group_index = 0
            for marker in marker_spans:
                dot_spans = marker.find_all('span', recursive=False)
                if len(dot_spans) == 3:
                    self._ellipsis_groups.append(dot_spans)
                    self._ellipsis_states.append(group_index % 4)
                    self._ellipsis_groups_visible.append(False)
                    group_index += 1
        self._streaming_tokens = []
        self._current_token_index = 0
        self._current_char_in_text_token_index = 0
        self._revealed_html_content = ""
        self._estimated_final_stream_height = 0
        streaming_enabled = self.theme_colors.get("streaming_enabled", False)
        streaming_speed = self.theme_colors.get("streaming_speed", 100)
        if self.role == 'intro':
            self._is_streaming = False
            self._start_intro_animation()
        elif self.role == 'assistant' and streaming_enabled and not immediate:
            self._is_streaming = True
            self._revealed_html_content = ""
            full_final_html_for_sizing = self._header_html + self._body_wrapper_open_tag + body_inner_html_to_tokenize + self._body_wrapper_close_tag
            self.label.setWordWrap(True)
            current_width = self.label.width() if self.label.width() > 0 else 400
            self.label.setFixedWidth(current_width)
            self.label.setText(full_final_html_for_sizing)
            self._estimated_final_stream_height = self.label.heightForWidth(current_width)
            self.label.setMinimumWidth(0)
            self.label.setMaximumWidth(16777215)
            self.label.clear()
            self._streaming_tokens = self._tokenize_html(body_inner_html_to_tokenize)
            self._start_token_streaming(streaming_speed)
        else:
            self._is_streaming = False
            final_html_display = self._header_html + self._body_wrapper_open_tag + body_inner_html_to_tokenize + self._body_wrapper_close_tag
            self.label.setWordWrap(True)
            self.label.setText(final_html_display)
            self.label.setMinimumHeight(0)
            self.label.setWordWrap(True)
            self.label.adjustSize()
            self.adjustSize()
            self.updateGeometry()
            if self._has_ellipsis and self._ellipsis_groups:
                for i in range(len(self._ellipsis_groups_visible)):
                    self._ellipsis_groups_visible[i] = True
                if not hasattr(self, '_ellipsis_timer') or self._ellipsis_timer is None:
                    self._ellipsis_timer = QTimer(self)
                    self._ellipsis_timer.timeout.connect(self._animate_all_ellipses)
                if not self._ellipsis_timer.isActive():
                    self._ellipsis_timer.start(500)

    def _update_streaming_label(self):
        if self._soup:
            self.label.setText(self._header_html + str(self._soup))
        else:
            self.label.setText(self._header_html)

    def parent_list_widget(self):
        container_widget = self.parentWidget()
        if container_widget:
            list_widget = container_widget.parentWidget()
            if list_widget and list_widget.__class__.__name__ == 'ChatMessageListWidget':
                return list_widget
        parent = self.parentWidget()
        while parent:
            if parent.__class__.__name__ == 'ChatMessageListWidget':
                return parent
            parent = parent.parentWidget()
        return None

    def _format_code_blocks(self, html_message, border_color):
        def replace_code_style(match):
            code_content = match.group(1)
            return f'<pre><code style="display: block; border: 1px solid {border_color}; padding: 10px; background-color: black; color: #fff; font-family: Consolas; white-space: pre-wrap; word-wrap: break-word;">{code_content}</code></pre>'
        import re
        return re.sub(r'<pre><code[^>]*>(.*?)</code></pre>', replace_code_style, html_message, flags=re.DOTALL | re.IGNORECASE)

    def _base_style(self):
        return f"""
        QFrame#ChatMessageWidget {{
            background: transparent;
            border-radius: 0px;
            border: none;
            margin: 0px;
            padding: 0px;
        }}
        """

    def _hover_style(self):
        base_color = QColor(self.base_theme_colors.get("base_color", "#00ff66"))
        r, g, b = base_color.red(), base_color.green(), base_color.blue()
        hover_background = f"rgba({r},{g},{b},0.09)"
        return f"""
        QFrame#ChatMessageWidget {{
            background: {hover_background};
            border-radius: 0px;
            border: none;
            margin: 0px;
            padding: 0px;
        }}
        """

    def _selected_style(self):
        base_color = QColor(self.base_theme_colors.get("base_color", "#00ff66"))
        r, g, b = base_color.red(), base_color.green(), base_color.blue()
        hover_background = f"rgba({r},{g},{b},0.18)"
        return f"""
        QFrame#ChatMessageWidget {{
            background: {hover_background};
            border-radius: 0px;
            border: none;
            margin: 0px;
            padding: 0px;
        }}
        """
    
    def _selected_hover_style(self):
        base_color = QColor(self.base_theme_colors.get("base_color", "#00ff66"))
        r, g, b = base_color.red(), base_color.green(), base_color.blue()
        return f"""
        QFrame#ChatMessageWidget {{
            background: rgba({r},{g},{b},0.18);
            border-radius: 0px;
            border: none;
            margin: 0px;
            padding: 0px;
        }}
        """

    def enterEvent(self, event):
        if self.role == 'intro' or not self._selectable or not self._is_left_splitter_open():
            return
        if self.hover_sound:
            try:
                self.hover_sound.play()
            except pygame.error as e:
                self.hover_sound = None
        if self._selected:
            self.setStyleSheet(self._selected_hover_style())
        else:
            self.setStyleSheet(self._hover_style())
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.role == 'intro' or not self._selectable or not self._is_left_splitter_open():
            return
        if self._selected:
            self.setStyleSheet(self._selected_style())
        else:
            self.setStyleSheet(self._base_style())
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.role == 'intro' or not self._selectable or not self._is_left_splitter_open():
            return
        if event.button() == Qt.LeftButton:
            if self._selected:
                self.deselect()
            else:
                self.select()
        else:
            return

    def select(self, silent=False):
        if ChatMessageWidget._selected_widget and is_valid_widget(ChatMessageWidget._selected_widget):
            try:
                if ChatMessageWidget._selected_widget != self:
                    ChatMessageWidget._selected_widget.deselect()
            except RuntimeError as e:
                pass
        self._selected = True
        if not silent and self.select_sound:
            try:
                self.select_sound.play()
            except pygame.error as e:
                self.select_sound = None
        self.setStyleSheet(self._selected_style())
        ChatMessageWidget._selected_widget = self
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.content)
        except Exception as e:
            pass
        self.update()

    def deselect(self):
        self._selected = False
        if self.hover_sound:
            try:
                self.hover_sound.play()
            except pygame.error as e:
                self.hover_sound = None
        self.setStyleSheet(self._base_style())
        self.update()

    def update_theme(self, new_theme):
        import copy
        self.base_theme_colors = copy.deepcopy(new_theme) if new_theme else {}
        self.theme_colors = self._get_colors_with_effects()
        self.setStyleSheet(self._base_style())
        if self._selected:
            self.setStyleSheet(self._selected_style())
        self._render_content()

    def _tokenize_html(self, html_string):
        if not html_string:
            return []
        tag_regex = r'(</?[^>]+>)'
        parts = re.split(tag_regex, html_string)
        tokens = [part for part in parts if part]
        return tokens

    def update_streaming_speed(self, new_speed_ms):
        if self._streaming_timer and self._streaming_timer.isActive():
            self._streaming_timer.setInterval(new_speed_ms)

    def _animate_all_ellipses(self):
        if not self._ellipsis_groups or not self._soup:
            if self._ellipsis_timer: self._ellipsis_timer.stop()
            return
        if not self._is_widget_visible_in_viewport():
            return
        needs_update = False
        for group_index, dot_group in enumerate(self._ellipsis_groups):
            if not dot_group or group_index >= len(self._ellipsis_states):
                continue
            if not self._ellipsis_groups_visible[group_index]:
                continue
            current_state = self._ellipsis_states[group_index]
            num_dots_to_show = current_state
            reset_step = current_state == 3
            for dot_index_in_group, dot_span in enumerate(dot_group):
                make_visible = not reset_step and (dot_index_in_group <= num_dots_to_show)
                actual_dot_text_holder = dot_span.find('span', recursive=False)
                if not actual_dot_text_holder:
                    actual_dot_text_holder = dot_span
                current_style = actual_dot_text_holder.get('style', '')
                base_style = ';'.join(s.strip() for s in current_style.split(';') if 'color:transparent' not in s.strip().lower() and s.strip())
                target_style = base_style if make_visible else base_style + ('; ' if base_style else '') + 'color:transparent;'
                current_style_norm = ';'.join(sorted(s.strip() for s in current_style.split(';') if s.strip()))
                target_style_norm = ';'.join(sorted(s.strip() for s in target_style.split(';') if s.strip()))
                if current_style_norm != target_style_norm:
                    if target_style:
                        actual_dot_text_holder['style'] = target_style
                    elif 'style' in actual_dot_text_holder.attrs:
                        del actual_dot_text_holder.attrs['style']
                    needs_update = True
            self._ellipsis_states[group_index] = (self._ellipsis_states[group_index] + 1) % 4
        if needs_update:
            self.label.setText(self._header_html + str(self._soup))

    def _get_player_character_name(self):
        try:
            widget = self
            main_ui = None
            while widget:
                if hasattr(widget, 'tabs_data') and hasattr(widget, 'tab_widget'):
                    main_ui = widget
                    break
                widget = widget.parentWidget()
            
            if not main_ui:
                return None
            tab_data = None
            message_list_widget = self.parent_list_widget()
            if message_list_widget:
                for i, tab_data_candidate in enumerate(main_ui.tabs_data):
                    if tab_data_candidate and tab_data_candidate.get('output') == message_list_widget:
                        tab_data = tab_data_candidate
                        break
            if not tab_data:
                current_tab_index = getattr(main_ui, 'current_tab_index', -1)
                if current_tab_index >= 0 and current_tab_index < len(main_ui.tabs_data):
                    tab_data = main_ui.tabs_data[current_tab_index]
            if not tab_data:
                return None
            workflow_data_dir = tab_data.get('workflow_data_dir')
            if not workflow_data_dir:
                return None
            game_actors_dir = os.path.join(workflow_data_dir, 'game', 'actors')
            player_candidates = []
            if os.path.exists(game_actors_dir):
                for filename in os.listdir(game_actors_dir):
                    if filename.endswith('.json'):
                        file_path = os.path.join(game_actors_dir, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                actor_data = json.load(f)
                            if actor_data.get('isPlayer', False) or actor_data.get('variables', {}).get('is_player', False):
                                player_name = actor_data.get('name')
                                if player_name:
                                    player_candidates.append((filename, player_name))
                        except Exception:
                            continue
            if not player_candidates:
                resources_actors_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
                if os.path.exists(resources_actors_dir):
                    for filename in os.listdir(resources_actors_dir):
                        if filename.endswith('.json'):
                            file_path = os.path.join(resources_actors_dir, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    actor_data = json.load(f)
                                if actor_data.get('isPlayer', False) or actor_data.get('variables', {}).get('is_player', False):
                                    player_name = actor_data.get('name')
                                    if player_name:
                                        player_candidates.append((filename, player_name))
                            except Exception:
                                continue
            if player_candidates:
                for filename, player_name in player_candidates:
                    if filename.lower() != 'player.json':
                        return player_name
                for filename, player_name in player_candidates:
                    if filename.lower() == 'player.json':
                        return player_name
            return None
        except Exception as e:
            print(f"Error getting player character name: {e}")
            return None

    def _is_widget_visible_in_viewport(self):
        try:
            parent_list = self.parent_list_widget()
            if not parent_list or not is_valid_widget(parent_list):
                return True
            widget_rect = self.geometry()
            viewport_rect = parent_list.viewport().rect()
            scroll_value = parent_list.verticalScrollBar().value()
            widget_top = widget_rect.top() - scroll_value
            widget_bottom = widget_rect.bottom() - scroll_value
            viewport_top = 0
            viewport_bottom = viewport_rect.height()
            is_visible = (widget_bottom >= viewport_top and widget_top <= viewport_bottom)
            return is_visible
        except Exception as e:
            return True

    def _apply_ellipsis_states(self):
        modified_spans = False
        for group_index, dot_group in enumerate(self._ellipsis_groups):
            if group_index >= len(self._ellipsis_states):
                pass
                continue 
            current_state = self._ellipsis_states[group_index]
            num_dots_to_show = current_state
            reset_step = current_state == 3
            for dot_index_in_group, dot_span in enumerate(dot_group):
                make_visible = not reset_step and (dot_index_in_group <= num_dots_to_show)
                current_style = dot_span.get('style', '')
                base_style = ';'.join(s.strip() for s in current_style.split(';') if 'color:transparent' not in s.strip().lower() and s.strip())
                target_style = ""
                if make_visible:
                    target_style = base_style
                else:
                    target_style = base_style + ('; ' if base_style else '') + 'color:transparent;'
                current_style_norm = ';'.join(sorted(s.strip() for s in current_style.split(';') if s.strip()))
                target_style_norm = ';'.join(sorted(s.strip() for s in target_style.split(';') if s.strip()))
                if current_style_norm != target_style_norm:
                     if target_style:
                         dot_span['style'] = target_style
                     elif 'style' in dot_span.attrs:
                         del dot_span['style']
                     modified_spans = True
        return modified_spans

    def stop_timers(self):
        for attr_name in dir(self):
            if attr_name.endswith('_timer') and hasattr(self, attr_name):
                timer = getattr(self, attr_name)
                if isinstance(timer, QTimer) and timer.isActive():
                    timer.stop()
        self._is_streaming = False
    def _start_intro_animation(self):
        self.stop_timers()
        soup = BeautifulSoup(self.content, 'html.parser')
        pre_element = soup.find('pre')
        desc_element = soup.find('p', id='intro-description')
        self._animation_state = {
            'current_stage': 'title',
            'title_text': pre_element.get_text() if pre_element else "Introduction",
            'title_current': "",
            'title_index': 0,
            'desc_text': desc_element.get_text() if desc_element else "",
            'desc_current': "",
            'desc_index': 0,
            'prompt_text': "Press NEW to begin...",
            'prompt_current': "",
            'prompt_index': 0,
            'blink_count': 6,
            'blink_visible': True
        }
        self._animation_template = f"""
        <div style="text-align: center; width: 100%;">
            <div style="height: auto; min-height: 100px; margin-bottom: 20px;">
                <pre style="text-align: center; margin: 0 auto; background: transparent; font-family: 'Consolas', 'Courier New', 'Liberation Mono', 'DejaVu Sans Mono', monospace; font-size: 12pt; line-height: 1.0; letter-spacing: 0px; white-space: pre; display: inline-block;">{{title}}</pre>
            </div>
            <div style="min-height: 30px; margin-bottom: 20px;">
                <p id="intro-description" style="text-align: center; font-family: Consolas; font-size: 14pt;">{{description}}</p>
            </div>
            <div style="min-height: 20px; position: relative;">
                <p id="intro-prompt" style="text-align: center; font-family: Consolas; font-size: 10pt;">{{prompt}}</p>
            </div>
        </div>
        """
        if hasattr(self, 'label') and is_valid_widget(self.label):
            self.label.setText(self._animation_template.format(
                title="&nbsp;",
                description="&nbsp;",
                prompt="&nbsp;"
            ))
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._process_animation_step)
        self._animation_timer.start(30)
    def _process_animation_step(self):
        if not hasattr(self, '_animation_state') or not is_valid_widget(self):
            self.stop_timers()
            return
        state = self._animation_state
        current_stage = state['current_stage']
        if current_stage == 'title':
            if state['title_index'] < len(state['title_text']):
                state['title_current'] += state['title_text'][state['title_index']]
                state['title_index'] += 1
                self._update_animation_display()
            else:
                if state['desc_text']:
                    state['current_stage'] = 'description'
                    self._animation_timer.setInterval(40)
                else:
                    state['current_stage'] = 'blink'
                    self._animation_timer.setInterval(250)
        elif current_stage == 'description':
            if state['desc_index'] < len(state['desc_text']):
                state['desc_current'] += state['desc_text'][state['desc_index']]
                state['desc_index'] += 1
                self._update_animation_display()
            else:
                state['current_stage'] = 'blink'
                self._animation_timer.setInterval(250)
                
        elif current_stage == 'blink':
            if state['blink_count'] > 0:
                state['blink_visible'] = not state['blink_visible']
                state['blink_count'] -= 1
                self._update_animation_display()
            else:
                state['current_stage'] = 'prompt'
                self._animation_timer.setInterval(40)
        elif current_stage == 'prompt':
            if state['prompt_index'] < len(state['prompt_text']):
                state['prompt_current'] += state['prompt_text'][state['prompt_index']]
                state['prompt_index'] += 1
                self._update_animation_display()
            else:
                self._animation_timer.stop()
                state['blink_visible'] = True
                self._update_animation_display()
                if self._prompt_finished_callback:
                    self._prompt_finished_callback()
    
    def _update_animation_display(self):
        if not hasattr(self, '_animation_state') or not hasattr(self, '_animation_template') or not is_valid_widget(self):
            return
        state = self._animation_state
        if state['current_stage'] == 'blink' and not state['blink_visible']:
            title_html = "&nbsp;"
        else:
            title_html = state['title_current'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if state['current_stage'] == 'blink' and not state['blink_visible']:
            desc_html = "&nbsp;"
        else:
            desc_html = state['desc_current'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if state['current_stage'] == 'prompt':
            prompt_visible = state['prompt_current'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            prompt_rest = state['prompt_text'][len(state['prompt_current']):].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            prompt_html = f'{prompt_visible}<span style="opacity: 0;">{prompt_rest}</span>'
        else:
            prompt_html = state['prompt_current'].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        display_html = self._animation_template.format(
            title=title_html,
            description=desc_html,
            prompt=prompt_html
        )
        if hasattr(self, 'label') and is_valid_widget(self.label):
            self.label.setText(display_html)
    def update_scene_context(self, message_scene, latest_scene):
        new_is_dimmed = (message_scene < latest_scene)
        if new_is_dimmed != self._is_dimmed:
            self.message_scene = message_scene
            self.latest_scene_in_context = latest_scene
            self._is_dimmed = new_is_dimmed
            self.set_message_content(immediate=True)
        else:
            self.message_scene = message_scene
            self.latest_scene_in_context = latest_scene

    def is_streaming(self):
        return self._is_streaming

    def force_complete_streaming(self):
        if not self._is_streaming:
            return False
        if hasattr(self, '_streaming_timer') and self._streaming_timer and self._streaming_timer.isActive():
            self._streaming_timer.stop()
        while self._current_token_index < len(self._streaming_tokens):
            current_token = self._streaming_tokens[self._current_token_index]
            is_tag = current_token.startswith('<') and current_token.endswith('>')
            if is_tag:
                self._revealed_html_content += current_token
                self._current_token_index += 1
                self._current_char_in_text_token_index = 0
            else:
                if isinstance(current_token, str):
                    self._revealed_html_content += current_token[self._current_char_in_text_token_index:]
                self._current_char_in_text_token_index = 0
                self._current_token_index += 1
        self._current_token_index = len(self._streaming_tokens)
        current_display_html = self._header_html + self._body_wrapper_open_tag + self._revealed_html_content + self._body_wrapper_close_tag
        self.label.setText(current_display_html)
        self._is_streaming = False
        self.setMaximumHeight(16777215)
        self.setMinimumHeight(0)
        self.label.setMinimumHeight(0)
        self.label.setWordWrap(True)
        self.label.adjustSize()
        self.adjustSize()
        self.updateGeometry()
        if self._has_ellipsis and self._ellipsis_groups:
            for i in range(len(self._ellipsis_groups_visible)):
                self._ellipsis_groups_visible[i] = True
        if callable(getattr(self, '_prompt_finished_callback', None)):
            self._prompt_finished_callback()
        return True

    def set_selectable(self, selectable):
        self._selectable = selectable
        if hasattr(self, 'label'):
            if selectable:
                self.label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                self.label.setAlignment(Qt.AlignLeft)
            else:
                self.label.setTextInteractionFlags(Qt.NoTextInteraction)
                self.label.setAlignment(Qt.AlignCenter)

    def _start_token_streaming(self, speed_ms):
        self._current_token_index = 0
        self._current_char_in_text_token_index = 0
        self.label.setWordWrap(True)
        if self._estimated_final_stream_height > 0:
            self.label.setMinimumHeight(self._estimated_final_stream_height)
            self.setMinimumHeight(self._estimated_final_stream_height)
        initial_display_html = self._header_html + self._body_wrapper_open_tag + "" + self._body_wrapper_close_tag
        self.label.setText(initial_display_html)
        if self._streaming_timer and self._streaming_timer.isActive():
            self._streaming_timer.stop()
        if not hasattr(self, '_streaming_timer') or self._streaming_timer is None:
            self._streaming_timer = QTimer(self)
        try:
            self._streaming_timer.timeout.disconnect()
        except TypeError:
            pass
        self._streaming_timer.timeout.connect(self._stream_next_token_chunk)
        if self._streaming_tokens: 
            self._streaming_timer.start(speed_ms)
            if self._streaming_tokens: 
                self._stream_next_token_chunk() 
        else: 
            self._is_streaming = False 
            self.label.setWordWrap(True)
            self.setMaximumHeight(16777215)
            self.setMinimumHeight(0)
            if self._has_ellipsis and self._ellipsis_groups:
                for i in range(len(self._ellipsis_groups_visible)):
                    self._ellipsis_groups_visible[i] = True
                if not hasattr(self, '_ellipsis_timer') or self._ellipsis_timer is None:
                    self._ellipsis_timer = QTimer(self)
                    self._ellipsis_timer.timeout.connect(self._animate_all_ellipses)
                if not self._ellipsis_timer.isActive():
                    self._ellipsis_timer.start(500)

    def _stream_next_token_chunk(self):
        if not self._is_streaming:
            if self._streaming_timer and self._streaming_timer.isActive():
                self._streaming_timer.stop()
            return
        if self._current_token_index >= len(self._streaming_tokens):
            if self._streaming_timer and self._streaming_timer.isActive():
                self._streaming_timer.stop()
            if self._is_streaming:
                self._is_streaming = False
                self.setMaximumHeight(16777215)
                self.setMinimumHeight(0)
                self.label.setMinimumHeight(0)
                self.label.setWordWrap(True)
                self.label.adjustSize()
                self.adjustSize()
                self.updateGeometry()
                if self._has_ellipsis and self._ellipsis_groups:
                    for i in range(len(self._ellipsis_groups_visible)):
                        self._ellipsis_groups_visible[i] = True
                    if not hasattr(self, '_ellipsis_timer') or self._ellipsis_timer is None:
                        self._ellipsis_timer = QTimer(self)
                        self._ellipsis_timer.timeout.connect(self._animate_all_ellipses)
                    if not self._ellipsis_timer.isActive():
                        self._ellipsis_timer.start(500)
                if callable(getattr(self, '_prompt_finished_callback', None)):
                    self._prompt_finished_callback()
            return
        chars_processed_this_tick = 0
        chars_per_tick = getattr(self, '_chars_per_tick', 3)
        while (self._current_token_index < len(self._streaming_tokens) and 
               chars_processed_this_tick < chars_per_tick):
            current_token = self._streaming_tokens[self._current_token_index]
            is_tag = current_token.startswith('<') and current_token.endswith('>')
            if is_tag:
                self._revealed_html_content += current_token
                self._current_token_index += 1
                self._current_char_in_text_token_index = 0
            else:
                remaining_chars_in_token = len(current_token) - self._current_char_in_text_token_index
                chars_to_process_from_this_token = min(remaining_chars_in_token, chars_per_tick - chars_processed_this_tick)
                self._revealed_html_content += current_token[self._current_char_in_text_token_index : self._current_char_in_text_token_index + chars_to_process_from_this_token]
                self._current_char_in_text_token_index += chars_to_process_from_this_token
                chars_processed_this_tick += chars_to_process_from_this_token
                if self._current_char_in_text_token_index >= len(current_token):
                    self._current_token_index += 1
                    self._current_char_in_text_token_index = 0
                if chars_processed_this_tick >= chars_per_tick:
                    break
        current_display_html = self._header_html + self._body_wrapper_open_tag + self._revealed_html_content + self._body_wrapper_close_tag
        self.label.setText(current_display_html)
        if self._current_token_index >= len(self._streaming_tokens):
            if self._streaming_timer and self._streaming_timer.isActive():
                self._streaming_timer.stop()
            self._is_streaming = False
            self.setMaximumHeight(16777215)
            self.setMinimumHeight(0)
            self.label.setMinimumHeight(0)
            self.label.setWordWrap(True)
            self.label.adjustSize()
            self.adjustSize()
            self.updateGeometry()
            if self._has_ellipsis and self._ellipsis_groups:
                for i in range(len(self._ellipsis_groups_visible)):
                    self._ellipsis_groups_visible[i] = True
                if not hasattr(self, '_ellipsis_timer') or self._ellipsis_timer is None:
                    self._ellipsis_timer = QTimer(self)
                    self._ellipsis_timer.timeout.connect(self._animate_all_ellipses)
                if not self._ellipsis_timer.isActive():
                    self._ellipsis_timer.start(500)
            if callable(getattr(self, '_prompt_finished_callback', None)):
                self._prompt_finished_callback()
