from PyQt5.QtWidgets import QTabWidget, QTabBar, QInputDialog, QMessageBox, QStyleOptionTab, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QSettings, QTimer
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QCursor
import os
import json
import subprocess
from core.add_tab import DEFAULT_TAB_SETTINGS

def handle_rmtree_error(func, path, exc_info):
    pass

def restore_tabs(ui_instance):
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        return
    settings = QSettings("ChatBotRPG", "ChatBotRPG")
    last_active_tab_name = settings.value("lastActiveTabName", "", type=str)
    ui_instance.tabs_data = []
    last_active_index = -1
    try:
        folder_names = [f for f in os.listdir(data_dir) 
                       if os.path.isdir(os.path.join(data_dir, f))]
        folder_names.sort()
        for i, folder_name in enumerate(folder_names):
            folder_path = os.path.join(data_dir, folder_name)
            game_dir = os.path.join(folder_path, "game")
            if not os.path.exists(game_dir):
                continue
            try:
                is_last_active = folder_name == last_active_tab_name
                if is_last_active or (not last_active_tab_name and i == 0):
                    ui_instance.add_new_tab(
                        name=folder_name,
                        log_file=os.path.join(folder_path, f"{folder_name}_log.html"),
                        notes_file=os.path.join(game_dir, "notes.json"),
                        context_file=os.path.join(game_dir, "context_history.json"),
                        system_context_file=os.path.join(game_dir, "system_context.txt"),
                        thought_rules_file=os.path.join(folder_path, "thought_rules.json"),
                        variables_file=os.path.join(game_dir, "workflow_variables.json"),
                        theme_settings=load_tab_settings(folder_path),
                        skip_heavy_loading=False
                    )
                    last_active_index = ui_instance.tab_widget.count() - 3 if ui_instance.tab_widget.count() >= 3 else 0  # account for fixed tabs
                    if is_last_active and last_active_index >= 0 and last_active_index < len(ui_instance.tabs_data):
                        restore_tab_splitter_state(ui_instance, last_active_index, folder_name)
                else:
                    create_tab_stub(ui_instance, folder_name, folder_path)
            except Exception as e:
                print(f"Failed to initialize tab '{folder_name}': {e}")
                continue
    except Exception as e:
        print(f"Error scanning data directory: {e}")
    if ui_instance.tab_widget.count() > 0:
        if 0 <= last_active_index < ui_instance.tab_widget.count():
            ui_instance.tab_widget.setCurrentIndex(last_active_index)
        else:
            ui_instance.tab_widget.setCurrentIndex(0)

def load_tab_settings(folder_path):
    settings_file = os.path.join(folder_path, "tab_settings.json")
    tab_settings = DEFAULT_TAB_SETTINGS.copy()
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                tab_settings.update(loaded_settings)
        except (json.JSONDecodeError, IOError):
            pass
    return tab_settings

def create_tab_stub(ui_instance, folder_name, folder_path):
    settings_file = os.path.join(folder_path, "tab_settings.json")
    tab_settings = DEFAULT_TAB_SETTINGS.copy()
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                tab_settings.update(loaded_settings)
        except (json.JSONDecodeError, IOError):
            pass
    stub_widget = QWidget()
    loading_label = None
    actual_index = ui_instance.tab_widget.addTab(stub_widget, folder_name)
    game_dir = os.path.join(folder_path, "game")
    stub_data = {
        'name': folder_name,
        'workflow_data_dir': folder_path,
        'widget': stub_widget,
        'loaded': False,
        'is_stub': True,
        'stub_loading_label': loading_label,
        'log_file': os.path.join(folder_path, f"{folder_name}_log.html"),
        'notes_file': os.path.join(game_dir, "notes.json"),
        'context_file': os.path.join(game_dir, "context_history.json"),
        'system_context_file': os.path.join(game_dir, "system_context.txt"),
        'thought_rules_file': os.path.join(folder_path, "thought_rules.json"),
        'variables_file': os.path.join(game_dir, "workflow_variables.json"),
        'tab_settings_file': os.path.join(folder_path, "tab_settings.json"),
        'settings': tab_settings,
        'context': [],
        'turn_count': 1,
        'scene_number': 1,
        'timer_rules_loaded': False
    }
    if actual_index >= len(ui_instance.tabs_data):
        ui_instance.tabs_data.extend([None] * (actual_index + 1 - len(ui_instance.tabs_data)))
    ui_instance.tabs_data[actual_index] = stub_data
    return actual_index

def replace_stub_with_full_tab(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data)):
        return False
    tab_data = ui_instance.tabs_data[tab_index]
    if not tab_data or not tab_data.get('is_stub', False):
        return True
    tab_data['is_stub'] = False
    try:
        tab_name = tab_data['name']
        tab_settings = tab_data['settings']
        ui_instance.tab_widget.blockSignals(True)
        try:
            ui_instance.add_new_tab(
                name=tab_name,
                log_file=tab_data['log_file'],
                notes_file=tab_data['notes_file'],
                context_file=tab_data['context_file'],
                system_context_file=tab_data['system_context_file'],
                thought_rules_file=tab_data['thought_rules_file'],
                variables_file=tab_data['variables_file'],
                theme_settings=tab_settings,
                replace_existing_index=tab_index,
                skip_heavy_loading=True
            )
        finally:
            ui_instance.tab_widget.blockSignals(False)
        ui_instance.tab_widget.setCurrentIndex(tab_index)
        QTimer.singleShot(10, lambda: finalize_tab_load(ui_instance, tab_index))
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        tab_data['is_stub'] = True
        return False

def finalize_tab_load(ui_instance, tab_index):
    if not (0 <= tab_index < len(ui_instance.tabs_data)):
        return
    td = ui_instance.tabs_data[tab_index]
    if td.get('loaded', False):
        return
    try:
        ui_instance.load_conversation_for_tab(tab_index)
        if not td.get('timer_rules_loaded', False):
            ui_instance._load_timer_rules_for_tab(tab_index)
        if hasattr(ui_instance, 'timer_manager'):
            ui_instance.timer_manager.load_timer_state(td)
        td['loaded'] = True
        td.pop('is_stub', None)
        if ui_instance.tab_widget.currentIndex() == tab_index:
            input_field = td.get('input')
            if input_field:
                input_field.setFocus()
            crt_overlay = td.get('crt_overlay')
            if crt_overlay and crt_overlay.parent():
                parent_widget = crt_overlay.parent()
                current_size = parent_widget.size()
                if current_size.width() > 0 and current_size.height() > 0:
                    crt_overlay.resize(current_size)
                    crt_overlay.raise_()
    except Exception as e:
        print(f"Error in finalize_tab_load for tab {tab_index}: {e}")

def restore_tab_splitter_state(ui_instance, tab_index, tab_name):
    try:
        settings = QSettings("ChatBotRPG", "ChatBotRPG")
        if not (0 <= tab_index < len(ui_instance.tabs_data)) or not ui_instance.tabs_data[tab_index]:
            return
        tab_data = ui_instance.tabs_data[tab_index]
        live_game_checked = settings.value(f"tab_{tab_name}_live_game_checked", True, type=bool)
        left_splitter = tab_data.get('left_splitter')
        if left_splitter and hasattr(left_splitter, 'live_game_button'):
            left_splitter.live_game_button.setChecked(live_game_checked)
        main_splitter = tab_data.get('splitter')
        if main_splitter:
            saved_sizes = settings.value(f"tab_{tab_name}_splitter_sizes")
            if saved_sizes:
                try:
                    if isinstance(saved_sizes, list):
                        sizes = [int(x) for x in saved_sizes]
                        main_splitter.setSizes(sizes)
                except (ValueError, TypeError):
                    pass
        right_splitter = tab_data.get('right_splitter')
        if right_splitter:
            right_splitter.setVisible(live_game_checked)
    except Exception as e:
        print(f"Error restoring splitter state for tab '{tab_name}': {e}")

def save_tabs_state(self):
    settings = QSettings("ChatBotRPG", "ChatBotRPG")
    current_index = self.tab_widget.currentIndex()
    if (0 <= current_index < len(self.tabs_data) and 
        self.tabs_data[current_index] is not None):
        active_tab_name = self.tabs_data[current_index].get('name', '')
        settings.setValue("lastActiveTabName", active_tab_name)
        tab_data = self.tabs_data[current_index]
        if tab_data:
            left_splitter = tab_data.get('left_splitter')
            right_splitter = tab_data.get('right_splitter')
            main_splitter = tab_data.get('splitter')
            
            if left_splitter and hasattr(left_splitter, 'live_game_button'):
                settings.setValue(f"tab_{active_tab_name}_live_game_checked", left_splitter.live_game_button.isChecked())
            
            if main_splitter:
                settings.setValue(f"tab_{active_tab_name}_splitter_sizes", main_splitter.sizes())
    else:
        settings.setValue("lastActiveTabName", "")

def remove_tab(self, index):
    if not (0 <= index < len(self.tabs_data)):
        return
    if len(self.tabs_data) <= 1:
        return
    self._save_context_for_tab(index)
    tab_data_to_delete = self.tabs_data[index]
    if not tab_data_to_delete:
        pass
    else:
        folder_to_delete = None
        if tab_data_to_delete.get('tab_settings_file'):
            folder_to_delete = os.path.dirname(tab_data_to_delete['tab_settings_file'])
        if folder_to_delete and os.path.exists(folder_to_delete):
            try:
                os.listdir(folder_to_delete)
            except Exception:
                pass
            try:
                result = subprocess.run(f'rmdir /s /q "{folder_to_delete}"', shell=True, check=False, capture_output=True, text=True)
                if os.path.exists(folder_to_delete):
                    if result.returncode != 0:
                        QMessageBox.warning(self, "Delete Error", f"OS command failed to delete the data folder for tab '{tab_data_to_delete.get('name', index)}'.\nReturn Code: {result.returncode}\nError Output (if any): {result.stderr.strip()}")
            except subprocess.CalledProcessError as e:
                QMessageBox.critical(self, "Delete Error", f"OS command failed to delete folder '{folder_to_delete}'.\nError: {e}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Delete Error", f"An unexpected error occurred while trying OS delete command for tab '{tab_data_to_delete.get('name', index)}'.\nCheck logs for details.\nError: {e}")
        elif folder_to_delete:
            pass
        else:
            pass
    widget = self.tab_widget.widget(index)
    if widget:
        try:
            self.tab_widget.add_tab_requested.disconnect()
            disconnected_signal = True
        except TypeError:
            disconnected_signal = False
        self.tab_widget.removeTab(index)
        widget.deleteLater()
        if disconnected_signal:
            try:
                from core.add_tab import DEFAULT_TAB_SETTINGS
                self.tab_widget.add_tab_requested.connect(lambda: self.add_new_tab(theme_settings=DEFAULT_TAB_SETTINGS.copy()))
            except Exception:
                pass
    if 0 <= index < len(self.tabs_data):
        removed_data = self.tabs_data.pop(index)
    save_tabs_state(self)
    self._update_turn_counter_display()

class TabManagerWidget(QTabWidget):
    add_tab_requested = pyqtSignal()
    remove_tab_requested = pyqtSignal(int)
    def __init__(self, parent=None, theme_colors=None):
        super().__init__(parent)
        self.parent = parent
        self.theme_colors = theme_colors or {"base_color": "#00ff66"}
        self.custom_tab_bar = CustomTabBar(self, self.theme_colors, use_fixed_tabs=True)
        self.setTabBar(self.custom_tab_bar)
        self.custom_tab_bar.add_tab_clicked.connect(self.add_tab_requested)
        self.custom_tab_bar.remove_tab_clicked.connect(self.remove_tab_requested)
        self.custom_tab_bar.tab_rename_requested.connect(self.rename_tab)
        self.setMovable(True)
        self.setTabsClosable(False)
        self._add_fixed_tabs()
    def _add_fixed_tabs(self):
        pass
    def rename_tab(self, index, new_name=None):
        if index < 0 or index >= self.count() - 2:
            return
        if not new_name:
            current_name = self.tabText(index)
            new_name, ok = QInputDialog.getText(self, "Rename Tab", "Enter new tab name:", text=current_name)
            if not ok or not new_name:
                return
        if hasattr(self.parent, 'update_tab_name'):
            self.parent.update_tab_name(index, new_name)
    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        self.custom_tab_bar.theme_colors = theme_colors
        self.custom_tab_bar.update()
    def addTab(self, widget, label):
        count = self.count()
        if count >= 2:
            index = super().insertTab(count - 2, widget, label)
            return index
        else:
            index = super().addTab(widget, label)
            if self.count() == 1:
                self.custom_tab_bar.add_fixed_tabs()
            return index
    
    def replaceTab(self, index, widget, label):
        if index < 0 or index >= self.count():
            return False
        was_current = (self.currentIndex() == index)
        old_widget = self.widget(index)
        if old_widget:
            super().removeTab(index)
            super().insertTab(index, widget, label)
            old_widget.setParent(None)
            old_widget.deleteLater()
            if was_current:
                self.setCurrentIndex(index)
            
            return True
        return False

class CustomTabBar(QTabBar):
    add_tab_clicked = pyqtSignal()
    remove_tab_clicked = pyqtSignal(int)
    tab_rename_requested = pyqtSignal(int, str)
    def __init__(self, parent=None, theme_colors=None, use_fixed_tabs=True):
        super().__init__(parent)
        self.parent = parent
        self.theme_colors = theme_colors or {"base_color": "#00ff66"}
        self.setExpanding(False)
        self.use_fixed_tabs = use_fixed_tabs
        self.has_fixed_tabs = False
        self.hovered_tab = -1
        self.setMouseTracking(True)
        if self.use_fixed_tabs:
            self.add_fixed_tabs()
    def add_fixed_tabs(self):
        if not self.has_fixed_tabs:
            self.addTab("-")
            self.addTab("+")
            self.has_fixed_tabs = True
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            index = self.tabAt(event.pos())
            if index >= 0 and self.use_fixed_tabs:
                count = self.count()
                if self.has_fixed_tabs and count >= 2 and index == count - 1:
                    self.add_tab_clicked.emit()
                    return
                elif self.has_fixed_tabs and count >= 2 and index == count - 2:
                    current_tab = self.parent.currentIndex()
                    if current_tab >= 0 and current_tab < count - 2:
                        self.remove_tab_clicked.emit(current_tab)
                    return
        super().mousePressEvent(event)
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            index = self.tabAt(event.pos())
            count = self.count()
            is_regular_tab = index >= 0
            if self.use_fixed_tabs and self.has_fixed_tabs and count >= 2:
                is_regular_tab = is_regular_tab and index < count - 2
            if is_regular_tab:
                self.tab_rename_requested.emit(index, None)
                return
        super().mouseDoubleClickEvent(event)
    def mouseMoveEvent(self, event):
        index = self.tabAt(event.pos())
        if index != self.hovered_tab:
            self.hovered_tab = index
            self.update()
        super().mouseMoveEvent(event)
    def leaveEvent(self, event):
        if self.hovered_tab != -1:
            self.hovered_tab = -1
            self.update()
        super().leaveEvent(event)
    def tabSizeHint(self, index):
        if self.use_fixed_tabs and self.has_fixed_tabs and (index == self.count() - 1 or index == self.count() - 2):
            base = super().tabSizeHint(index)
            return QSize(40, base.height())
        base = super().tabSizeHint(index)
        horizontal_padding = 40
        return QSize(base.width() + (2 * horizontal_padding), base.height())
    def paintEvent(self, event):
        painter = QPainter(self)
        option = QStyleOptionTab()
        mouse_pos = self.mapFromGlobal(QCursor.pos())
        last = self.count() - 1
        second_last = self.count() - 2
        theme_color = QColor(self.theme_colors["base_color"])
        for i in range(self.count()):
            self.initStyleOption(option, i)
            is_plus = self.use_fixed_tabs and self.has_fixed_tabs and i == last
            is_minus = self.use_fixed_tabs and self.has_fixed_tabs and i == second_last
            is_selected = i == self.currentIndex()
            is_hovered = i == self.hovered_tab
            if is_plus or is_minus:
                rect = option.rect
                hovered = rect.contains(mouse_pos)
                theme_color = QColor(self.theme_colors["base_color"])
                if hovered:
                    bg_color = theme_color.lighter(150)
                    text_color = QColor(30, 30, 30)
                else:
                    darker_bg = self.theme_colors.get("darker_bg", "#1a1a1a")
                    bg_color = QColor(darker_bg)
                    text_color = theme_color
                painter.setPen(Qt.NoPen)
                painter.setBrush(bg_color)
                painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 5, 5)
                painter.setPen(QPen(theme_color, 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 5, 5)
                painter.setPen(text_color)
                painter.setFont(QFont('Arial', 18, QFont.Bold))
                painter.drawText(rect, Qt.AlignCenter, self.tabText(i))
            else:
                self.style().drawControl(self.style().CE_TabBarTab, option, painter, self)
                rect = option.rect
                if is_selected or is_hovered:
                    painter.save()
                    overlay_color = theme_color
                    if is_selected:
                        overlay_color.setAlpha(70)
                    elif is_hovered:
                        overlay_color.setAlpha(30)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(overlay_color)
                    painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 5, 5)
                    painter.restore()
                if is_selected:
                    painter.setPen(QPen(theme_color, 2))
                    painter.drawLine(rect.left() + 2, rect.bottom() - 1, rect.right() - 2, rect.bottom() - 1)