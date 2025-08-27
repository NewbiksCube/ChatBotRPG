import os
import json
import random
from PyQt5.QtCore import QObject, QTimer

from core.music_manager import get_music_manager


class GameMusicController(QObject):
    """Controls runtime game music selection based on music groups and conditions.

    Behavior:
    - When activated for a tab, evaluates groups (top-first) to find the first matching group.
    - Plays a random non-repeating (unless only one) track from that group.
    - Tracks do not loop; when one ends, it re-evaluates and plays the next.
    - "Next Track" requests fade out current track then immediately selects the next.
    """

    def __init__(self):
        super().__init__()
        self._active_ui = None
        self._active_tab_index = -1
        self._armed_for_start = False
        self._eval_timer = QTimer(self)
        self._eval_timer.setSingleShot(True)
        self._eval_timer.timeout.connect(self._evaluate_and_play_next)
        self._music_manager = get_music_manager()
        # Listen for stop events (both manual stop and natural end)
        try:
            self._music_manager.music_stopped.connect(self._on_music_stopped)
        except Exception:
            pass

    def activate_for_tab(self, ui_instance, tab_index):
        """Activate runtime music for the specified tab.

        If a track is currently playing (e.g., intro), wait until it ends; otherwise, start immediately.
        """
        if not (0 <= tab_index < len(ui_instance.tabs_data)):
            return
        tab_data = ui_instance.tabs_data[tab_index]
        if not isinstance(tab_data, dict):
            return
        # Do not run during intro
        if tab_data.get('_is_showing_intro', False):
            return

        self._active_ui = ui_instance
        self._active_tab_index = tab_index
        tab_data['_game_music_active'] = True
        # If music is already playing (e.g., intro track still finishing), arm and wait for stop
        try:
            self._armed_for_start = bool(self._music_manager.is_playing())
        except Exception:
            self._armed_for_start = False
        # Always schedule a quick evaluation so startup never silently skips
        self._schedule_eval(delay_ms=50)

    def deactivate_for_tab(self, ui_instance, tab_index):
        if self._active_ui is ui_instance and self._active_tab_index == tab_index:
            self._active_ui = None
            self._active_tab_index = -1
        try:
            if 0 <= tab_index < len(ui_instance.tabs_data):
                ui_instance.tabs_data[tab_index]['_game_music_active'] = False
        except Exception:
            pass
        self._eval_timer.stop()

    def next_track(self, ui_instance):
        """Skip to the next track by fading out current music."""
        try:
            # Ensure controller is active for current tab
            if ui_instance is not self._active_ui:
                # Try to activate for current tab
                current_tab = getattr(ui_instance, 'current_tab_index', -1)
                if current_tab >= 0:
                    self.activate_for_tab(ui_instance, current_tab)
                    if ui_instance is not self._active_ui:
                        return
                else:
                    return
            # Check what group WOULD be selected - don't stop if it's the same as current
            tab_index = self._active_tab_index
            tab_data = ui_instance.tabs_data[tab_index]
            current_group = tab_data.get('_game_music_last_group')

            data = self._load_music_data(tab_data)
            if not data:
                return

            selected_group = self._select_matching_group(ui_instance, tab_data, data)
            # If same group would be selected, don't stop current music
            if selected_group == current_group and self._music_manager.is_playing():
                return
            
            self._armed_for_start = True
            self._music_manager.stop_music(fade_out_ms=1500)
        except Exception as e:
            pass

    def _on_music_stopped(self):
        # Only respond if this controller is active and the owning UI/tab is active
        ui = self._active_ui
        if not ui or self._active_tab_index < 0:
            return
        # Ensure the UI's current tab is the active one
        try:
            if hasattr(ui, 'tab_widget') and ui.tab_widget.currentIndex() != self._active_tab_index:
                return
        except Exception:
            return
        if not self._is_active_for_current_tab():
            return
        # If we were armed or music ended naturally, schedule evaluation
        self._schedule_eval(delay_ms=100)

    def _schedule_eval(self, delay_ms=100):
        self._eval_timer.stop()
        self._eval_timer.start(max(0, int(delay_ms)))

    def _is_active_for_current_tab(self):
        if not self._active_ui or self._active_tab_index < 0:
            return False
        try:
            tab_data = self._active_ui.tabs_data[self._active_tab_index]
            return bool(tab_data and tab_data.get('_game_music_active', False) and not tab_data.get('_is_showing_intro', False))
        except Exception:
            return False

    def _load_music_data(self, tab_data):
        try:
            workflow_dir = tab_data.get('workflow_data_dir')
            if not workflow_dir:
                return None
            music_file = os.path.join(workflow_dir, 'resources', 'data files', 'settings', 'music_data.json')
            if not os.path.exists(music_file):
                return None
            with open(music_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            # Normalize keys to the evaluation schema
            if 'groups' in raw:
                # Already normalized
                return raw
            # Convert from editor schema to runtime schema if needed
            groups = raw.get('music_groups', {})
            files = raw.get('files', {})
            conditions = raw.get('music_group_conditions', {})
            priority = raw.get('group_priority_order', [])
            return {
                'groups': groups,
                'files': files,
                'conditions': conditions,
                'group_priority_order': priority,
            }
        except Exception:
            return None

    def _select_matching_group(self, ui_instance, tab_data, data_dict):
        groups = data_dict.get('groups', {})
        conditions = data_dict.get('conditions', {})
        priority = data_dict.get('group_priority_order', [])
        ordered = [g for g in priority if g in groups]
        for g in sorted(groups.keys()):
            if g not in ordered:
                ordered.append(g)
        for group_name in ordered:
            cond_list = conditions.get(group_name, [])
            if self._all_conditions_met(cond_list, ui_instance, tab_data):
                return group_name
        return None

    def _evaluate_and_play_next(self):
        if not self._is_active_for_current_tab():
            return
        ui = self._active_ui
        tab_index = self._active_tab_index
        tab_data = ui.tabs_data[tab_index]
        data = self._load_music_data(tab_data)
        if not data:
            return
        groups = data.get('groups', {})  # group_name -> [filenames]
        files = data.get('files', {})    # filename -> { filepath, display_name, group }
        conditions = data.get('conditions', {})  # group_name -> [ { variable, operator, value, scope } ]
        priority = data.get('group_priority_order', [])

        # Build ordered groups list
        ordered = [g for g in priority if g in groups]
        for g in sorted(groups.keys()):
            if g not in ordered:
                ordered.append(g)

        selected_group = self._select_matching_group(ui, tab_data, {
            'groups': groups,
            'conditions': conditions,
            'group_priority_order': priority
        })

        if not selected_group:
            # Nothing matches now; retry later if still idle
            self._schedule_eval(delay_ms=3000)
            return

        # Check if we're already playing from this group - if so, don't change!
        current_group = tab_data.get('_game_music_last_group')
        if current_group == selected_group and self._music_manager.is_playing():
            return

        filenames = list(groups.get(selected_group, []))
        if not filenames:
            self._schedule_eval(delay_ms=3000)
            return

        last_played = tab_data.get('_game_music_last_filename')
        if len(filenames) > 1 and last_played in filenames:
            # Avoid immediate repeat
            filenames = [fn for fn in filenames if fn != last_played] or filenames

        chosen = random.choice(filenames)
        file_info = files.get(chosen, {})
        filepath = file_info.get('filepath')
        # Ensure workflow_dir is available for fallback path resolution
        workflow_dir = tab_data.get('workflow_data_dir')
        if not workflow_dir:
            return
        if not filepath or not os.path.exists(filepath):
            # Try to reconstruct path under music folder
            candidate = os.path.join(workflow_dir, 'resources', 'audio', 'music', chosen)
            if os.path.exists(candidate):
                filepath = candidate
            else:
                # Skip and try again soon
                self._schedule_eval(delay_ms=1000)
                return

        # Play non-looping; when it ends naturally, _on_music_stopped will schedule next
        try:
            # Apply UI volume if available
            if hasattr(ui, '_music_volume'):
                self._music_manager.set_volume(ui._music_volume)
            success = self._music_manager.play_music(filepath, fade_in_ms=1500, loop=False)
            if success:
                tab_data['_game_music_last_filename'] = chosen
                tab_data['_game_music_last_group'] = selected_group
                self._armed_for_start = False
            else:
                # Retry later
                self._schedule_eval(delay_ms=1500)
        except Exception as e:
            self._schedule_eval(delay_ms=1500)

    def _all_conditions_met(self, cond_list, ui_instance, tab_data):
        if not cond_list:
            return True
        try:
            # Reuse existing variable condition evaluation from TimerManager
            timer_mgr = getattr(ui_instance, 'timer_manager', None)
            if not timer_mgr:
                return True
            for cond in cond_list:
                # Map fields to timer manager's expected keys
                condition = {
                    'name': cond.get('variable', ''),
                    'operator': cond.get('operator', '=='),
                    'value': cond.get('value', ''),
                    'scope': cond.get('scope', 'Global')
                }
                if not timer_mgr._evaluate_variable_condition(condition, tab_data):
                    return False
            return True
        except Exception:
            return False


_controller = None


def get_game_music_controller():
    global _controller
    if _controller is None:
        _controller = GameMusicController()
    return _controller


