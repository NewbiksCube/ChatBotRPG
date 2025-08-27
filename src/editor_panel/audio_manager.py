from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame, QSizePolicy, QRadioButton, QButtonGroup, QLineEdit, QGridLayout, QListWidget, QComboBox, QSpinBox, QScrollArea, QSlider, QCheckBox, QGroupBox, QStackedWidget, QListWidgetItem, QFileDialog, QMessageBox, QInputDialog, QProgressBar, QDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor
import json
import os
import subprocess
import threading
import time
from pathlib import Path

class OGGConverterThread(QThread):
    progress_updated = pyqtSignal(int)
    conversion_finished = pyqtSignal(str, str)
    conversion_failed = pyqtSignal(str, str)
    
    def __init__(self, input_file, output_file):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
    
    def run(self):
        try:
            output_dir = os.path.dirname(self.output_file)
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"Starting conversion: {self.input_file} -> {self.output_file}")
            
            cmd = [
                'ffmpeg', '-i', self.input_file, 
                '-c:a', 'libvorbis', '-b:a', '128k', '-ar', '44100',
                '-y', self.output_file
            ]
            
            print(f"FFmpeg command: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate()
            
            print(f"FFmpeg stdout: {stdout.decode()}")
            print(f"FFmpeg stderr: {stderr.decode()}")
            print(f"FFmpeg return code: {process.returncode}")
            
            if process.returncode == 0 and os.path.exists(self.output_file):
                file_size = os.path.getsize(self.output_file)
                print(f"Output file size: {file_size} bytes")
                if file_size > 0:
                    self.conversion_finished.emit(self.input_file, self.output_file)
                else:
                    self.conversion_failed.emit(self.input_file, "Output file is 0 bytes")
            else:
                self.conversion_failed.emit(self.input_file, f"FFmpeg conversion failed with return code {process.returncode}")
                
        except Exception as e:
            print(f"Conversion error: {e}")
            self.conversion_failed.emit(self.input_file, str(e))

class MusicPlayerThread(QThread):
    playback_finished = pyqtSignal()
    
    def __init__(self, music_file):
        super().__init__()
        self.music_file = music_file
        self._stop_playback = False
        self._process = None
    
    def run(self):
        try:
            print(f"Starting music playback: {self.music_file}")
            
            if not os.path.exists(self.music_file):
                print(f"Music file does not exist: {self.music_file}")
                self.playback_finished.emit()
                return
            
            file_size = os.path.getsize(self.music_file)
            print(f"Music file size: {file_size} bytes")
            
            if file_size == 0:
                print("Music file is 0 bytes, cannot play")
                self.playback_finished.emit()
                return
            
            if self._try_ffplay():
                return
            elif self._try_pygame():
                return
            else:
                print("No audio playback method available")
                self.playback_finished.emit()
                
        except Exception as e:
            print(f"Music playback error: {e}")
            self.playback_finished.emit()
    
    def _try_ffplay(self):
        try:
            cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'error', '-af', 'volume=0.5', self.music_file]
            print(f"Trying FFplay: {' '.join(cmd)}")
            
            self._process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            while self._process.poll() is None and not self._stop_playback:
                time.sleep(0.1)
            
            if not self._stop_playback:
                print("FFplay playback completed normally")
                self.playback_finished.emit()
                return True
            else:
                print("FFplay playback stopped by user")
                if self._process:
                    self._process.terminate()
                    self._process.wait()
                return True
                
        except Exception as e:
            print(f"FFplay failed: {e}")
            return False
    
    def _try_pygame(self):
        try:
            import pygame
            print("Trying pygame audio playback")
            
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy() and not self._stop_playback:
                time.sleep(0.1)
            
            if not self._stop_playback:
                print("Pygame playback completed normally")
                self.playback_finished.emit()
                return True
            else:
                print("Pygame playback stopped by user")
                pygame.mixer.music.stop()
                return True
                
        except Exception as e:
            print(f"Pygame failed: {e}")
            return False
    
    def stop(self):
        print("Stopping music playback")
        self._stop_playback = True
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=2)
            except:
                pass
    
    def quit(self):
        self.stop()
        super().quit()
    
    def terminate(self):
        self.stop()
        super().terminate()

class AudioManager(QWidget):
    def __init__(self, theme_colors, parent=None, workflow_data_dir=None, main_ui=None, tab_data=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.workflow_data_dir = workflow_data_dir
        self.main_ui = main_ui
        self.tab_data = tab_data
        self.setObjectName("AudioManagerWidget")
        self.current_music_player = None
        self.ogg_converter = None
        
        try:
            self._init_ui()
            self._apply_loaded_settings()
            self._connect_signals()
        except Exception as e:
            print(f"Error initializing AudioManager: {e}")
            import traceback
            traceback.print_exc()
    
    def closeEvent(self, event):
        self._cleanup_audio()
        super().closeEvent(event)
    
    def __del__(self):
        self._cleanup_audio()
    
    def hideEvent(self, event):
        self._stop_current_music()
        super().hideEvent(event)
    
    def _cleanup_audio(self):
        try:
            if self.current_music_player:
                if isinstance(self.current_music_player, MusicPlayerThread):
                    if self.current_music_player.isRunning():
                        print("Stopping music player thread...")
                        self.current_music_player.stop()
                        self.current_music_player.quit()
                        self.current_music_player.wait(3000)
                        if self.current_music_player.isRunning():
                            self.current_music_player.terminate()
                            self.current_music_player.wait(1000)
                else:
                    try:
                        from core.music_manager import get_music_manager
                        music_manager = get_music_manager()
                        music_manager.stop_music(fade_out_ms=500)
                    except Exception as e:
                        print(f"Error stopping music: {e}")
                
                self.current_music_player = None
        except Exception as e:
            print(f"Error cleaning up music player: {e}")
        
        try:
            if self.ogg_converter and self.ogg_converter.isRunning():
                print("Stopping OGG converter thread...")
                self.ogg_converter.quit()
                self.ogg_converter.wait(3000)
                if self.ogg_converter.isRunning():
                    self.ogg_converter.terminate()
                    self.ogg_converter.wait(1000)
        except Exception as e:
            print(f"Error cleaning up OGG converter: {e}")
    
    def _force_kill_audio_processes(self):
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['taskkill', '/f', '/im', 'ffplay.exe'], 
                             capture_output=True, timeout=5)
            else:  # Linux/Mac
                subprocess.run(['pkill', '-f', 'ffplay'], 
                             capture_output=True, timeout=5)
        except Exception as e:
            print(f"Error force-killing audio processes: {e}")
    
    def _stop_current_music(self):
        try:
            if self.current_music_player:
                if isinstance(self.current_music_player, MusicPlayerThread):
                    if self.current_music_player.isRunning():
                        print("Stopping current music playback...")
                        self.current_music_player.stop()
                        self.current_music_player.quit()
                        self.current_music_player.wait(3000)
                        if self.current_music_player.isRunning():
                            self.current_music_player.terminate()
                            self.current_music_player.wait(1000)
                else:
                    try:
                        from core.music_manager import get_music_manager
                        music_manager = get_music_manager()
                        music_manager.stop_music(fade_out_ms=500)
                    except Exception as e:
                        print(f"Error stopping music: {e}")
                
                self.current_music_player = None
            
            self.test_music_button.setEnabled(True)
            self.stop_music_button.setEnabled(False)
            
            for i in range(self.music_files_list.count()):
                item = self.music_files_list.item(i)
                if item.background() != QColor(0, 0, 0, 0):
                    item.setBackground(QColor(0, 0, 0, 0))
                    item.setToolTip("")
                    break
        except Exception as e:
            print(f"Error stopping music: {e}")
    
    def set_tab_data(self, tab_data):
        self.tab_data = tab_data
        try:
            self._load_title_music_from_variables()
            self._load_intro_music_from_variables()
            self._load_music_data()
        except Exception as e:
            print(f"AudioManager: failed to load music after tab_data set: {e}")
    
    def set_main_ui(self, main_ui):
        self.main_ui = main_ui
        if main_ui:
            try:
                main_ui.aboutToQuit.connect(self._cleanup_audio)
            except:
                pass
    
    def update_theme(self, theme_colors):
        self.theme_colors = theme_colors
        self._apply_styling()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        toggle_container = QWidget()
        toggle_container.setObjectName("AudioToggleContainer")
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(5, 5, 5, 5)
        
        self.toggle_group = QButtonGroup(self)
        
        self.sfx_btn = QPushButton("SFX")
        self.sfx_btn.setObjectName("SFXAudioToggleButton")
        self.sfx_btn.setCheckable(True)
        self.sfx_btn.setChecked(True)
        self.sfx_btn.setMinimumHeight(30)
        self.sfx_btn.setFont(QFont('Consolas', 10))
        self.sfx_btn.setFocusPolicy(Qt.NoFocus)
        
        self.music_btn = QPushButton("MUSIC")
        self.music_btn.setObjectName("MusicAudioToggleButton")
        self.music_btn.setCheckable(True)
        self.music_btn.setMinimumHeight(30)
        self.music_btn.setFont(QFont('Consolas', 10))
        self.music_btn.setFocusPolicy(Qt.NoFocus)
        
        self.toggle_group.addButton(self.sfx_btn)
        self.toggle_group.addButton(self.music_btn)
        
        toggle_layout.addWidget(self.sfx_btn)
        toggle_layout.addWidget(self.music_btn)
        
        main_layout.addWidget(toggle_container)
        
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("AudioContentStack")
        
        self.sfx_widget = self._create_sfx_widget()
        self.music_widget = self._create_music_widget()
        
        self.content_stack.addWidget(self.sfx_widget)
        self.content_stack.addWidget(self.music_widget)
        self.content_stack.setCurrentIndex(0)
        
        main_layout.addWidget(self.content_stack)
        
        self._apply_styling()
    
    def _create_sfx_widget(self):
        widget = QWidget()
        widget.setObjectName("SFXAudioWidget")
        
        scroll_area = QScrollArea()
        scroll_area.setObjectName("AudioManagerScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        content_widget.setObjectName("AudioManagerContent")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        audio_settings_label = QLabel("Sound Effects Settings")
        audio_settings_label.setObjectName("AudioSettingsLabel")
        audio_settings_label.setFont(QFont('Consolas', 9, QFont.Bold))
        audio_settings_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(audio_settings_label)
        
        master_group = QGroupBox("Master Volume")
        master_group.setObjectName("MasterVolumeGroup")
        master_layout = QVBoxLayout(master_group)
        
        master_volume_layout = QHBoxLayout()
        master_volume_label = QLabel("Master Volume:")
        master_volume_label.setObjectName("MasterVolumeLabel")
        self.master_volume_slider = QSlider(Qt.Horizontal)
        self.master_volume_slider.setObjectName("MasterVolumeSlider")
        self.master_volume_slider.setRange(0, 100)
        self.master_volume_slider.setValue(100)
        self.volume_value_label = QLabel("100%")
        self.volume_value_label.setObjectName("VolumeValueLabel")
        self.volume_value_label.setMinimumWidth(40)
        
        master_volume_layout.addWidget(master_volume_label)
        master_volume_layout.addWidget(self.master_volume_slider)
        master_volume_layout.addWidget(self.volume_value_label)
        master_layout.addLayout(master_volume_layout)
        layout.addWidget(master_group)
        
        sfx_group = QGroupBox("Sound Effects")
        sfx_group.setObjectName("SFXGroup")
        sfx_layout = QVBoxLayout(sfx_group)
        
        self.sfx_enabled_checkbox = QCheckBox("Enable Sound Effects")
        self.sfx_enabled_checkbox.setObjectName("SFXEnabledCheckbox")
        self.sfx_enabled_checkbox.setChecked(True)
        sfx_layout.addWidget(self.sfx_enabled_checkbox)
        
        sfx_volume_layout = QHBoxLayout()
        sfx_volume_label = QLabel("SFX Volume:")
        sfx_volume_label.setObjectName("SFXVolumeLabel")
        self.sfx_volume_slider = QSlider(Qt.Horizontal)
        self.sfx_volume_slider.setObjectName("SFXVolumeSlider")
        self.sfx_volume_slider.setRange(0, 100)
        self.sfx_volume_slider.setValue(75)
        sfx_layout.addLayout(sfx_volume_layout)
        sfx_layout.addWidget(sfx_volume_label)
        sfx_layout.addWidget(self.sfx_volume_slider)
        
        test_sfx_layout = QHBoxLayout()
        self.test_sfx_button = QPushButton("Test SFX")
        self.test_sfx_button.setObjectName("TestSFXButton")
        test_sfx_layout.addWidget(self.test_sfx_button)
        sfx_layout.addLayout(test_sfx_layout)
        
        layout.addWidget(sfx_group)
        
        voice_group = QGroupBox("Voice")
        voice_group.setObjectName("VoiceGroup")
        voice_layout = QVBoxLayout(voice_group)
        
        self.voice_enabled_checkbox = QCheckBox("Enable Voice")
        self.voice_enabled_checkbox.setObjectName("VoiceEnabledCheckbox")
        self.voice_enabled_checkbox.setChecked(True)
        voice_layout.addWidget(self.voice_enabled_checkbox)
        
        voice_volume_layout = QHBoxLayout()
        voice_volume_label = QLabel("Voice Volume:")
        voice_volume_label.setObjectName("VoiceVolumeLabel")
        self.voice_volume_slider = QSlider(Qt.Horizontal)
        self.voice_volume_slider.setObjectName("VoiceVolumeSlider")
        self.voice_volume_slider.setRange(0, 100)
        self.voice_volume_slider.setValue(100)
        voice_layout.addLayout(voice_volume_layout)
        voice_layout.addWidget(voice_volume_label)
        voice_layout.addWidget(self.voice_volume_slider)
        
        test_voice_layout = QHBoxLayout()
        self.test_voice_button = QPushButton("Test Voice")
        self.test_voice_button.setObjectName("TestVoiceButton")
        test_voice_layout.addWidget(self.test_voice_button)
        voice_layout.addLayout(test_voice_layout)
        
        layout.addWidget(voice_group)
        
        scroll_area.setWidget(content_widget)
        main_layout = QVBoxLayout(widget)
        main_layout.addWidget(scroll_area)
        
        return widget
    
    def _create_music_widget(self):
        widget = QWidget()
        widget.setObjectName("MusicAudioWidget")
        
        scroll_area = QScrollArea()
        scroll_area.setObjectName("AudioManagerScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        content_widget = QWidget()
        content_widget.setObjectName("AudioManagerContent")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        audio_settings_label = QLabel("Music Management")
        audio_settings_label.setObjectName("AudioSettingsLabel")
        audio_settings_label.setFont(QFont('Consolas', 9, QFont.Bold))
        audio_settings_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(audio_settings_label)
        
        title_music_group = QGroupBox("Title Music")
        title_music_group.setObjectName("TitleMusicGroup")
        title_music_layout = QVBoxLayout(title_music_group)
        
        title_music_buttons_layout = QHBoxLayout()
        self.set_title_music_button = QPushButton("Set Title Music")
        self.set_title_music_button.setObjectName("SetTitleMusicButton")
        self.set_title_music_button.setMaximumHeight(25)
        self.set_title_music_button.clicked.connect(self._set_title_music)
        
        self.clear_title_music_button = QPushButton("Clear Title Music")
        self.clear_title_music_button.setObjectName("ClearTitleMusicButton")
        self.clear_title_music_button.setMaximumHeight(25)
        self.clear_title_music_button.clicked.connect(self._clear_title_music)
        
        title_music_buttons_layout.addWidget(self.set_title_music_button)
        title_music_buttons_layout.addWidget(self.clear_title_music_button)
        title_music_layout.addLayout(title_music_buttons_layout)
        
        self.title_music_label = QLabel("No title music set")
        self.title_music_label.setObjectName("TitleMusicLabel")
        self.title_music_label.setAlignment(Qt.AlignCenter)
        title_music_layout.addWidget(self.title_music_label)
        

        layout.addWidget(title_music_group)
        
        intro_music_group = QGroupBox("Introduction Music")
        intro_music_group.setObjectName("IntroMusicGroup")
        intro_music_layout = QVBoxLayout(intro_music_group)
        
        intro_music_buttons_layout = QHBoxLayout()
        self.set_intro_music_button = QPushButton("Set Intro Music")
        self.set_intro_music_button.setObjectName("SetIntroMusicButton")
        self.set_intro_music_button.setMaximumHeight(25)
        self.set_intro_music_button.clicked.connect(self._set_intro_music)
        
        self.clear_intro_music_button = QPushButton("Clear Intro Music")
        self.clear_intro_music_button.setObjectName("ClearIntroMusicButton")
        self.clear_intro_music_button.setMaximumHeight(25)
        self.clear_intro_music_button.clicked.connect(self._clear_intro_music)
        
        intro_music_buttons_layout.addWidget(self.set_intro_music_button)
        intro_music_buttons_layout.addWidget(self.clear_intro_music_button)
        intro_music_layout.addLayout(intro_music_buttons_layout)
        
        self.intro_music_label = QLabel("No intro music set")
        self.intro_music_label.setObjectName("IntroMusicLabel")
        self.intro_music_label.setAlignment(Qt.AlignCenter)
        intro_music_layout.addWidget(self.intro_music_label)
        

        layout.addWidget(intro_music_group)
        
        groups_group = QGroupBox("Music Groups")
        groups_group.setObjectName("MusicGroupsGroup")
        groups_layout = QVBoxLayout(groups_group)
        
        groups_buttons_layout = QHBoxLayout()
        self.add_group_button = QPushButton("Add Group")
        self.add_group_button.setObjectName("AddGroupButton")
        self.add_group_button.setMaximumHeight(25)
        self.add_group_button.clicked.connect(self._add_music_group)
        
        self.remove_group_button = QPushButton("Remove Group")
        self.remove_group_button.setObjectName("RemoveGroupButton")
        self.remove_group_button.setMaximumHeight(25)
        self.remove_group_button.clicked.connect(self._remove_music_group)
        
        self.move_group_up_button = QPushButton("↑")
        self.move_group_up_button.setObjectName("MoveGroupUpButton")
        self.move_group_up_button.setMaximumHeight(25)
        self.move_group_up_button.setMaximumWidth(30)
        self.move_group_up_button.setToolTip("Move Group Up")
        self.move_group_up_button.clicked.connect(self._move_group_up)
        self.move_group_up_button.setEnabled(False)
        
        self.move_group_down_button = QPushButton("↓")
        self.move_group_down_button.setObjectName("MoveGroupDownButton")
        self.move_group_down_button.setMaximumHeight(25)
        self.move_group_down_button.setMaximumWidth(30)
        self.move_group_down_button.setToolTip("Move Group Down")
        self.move_group_down_button.clicked.connect(self._move_group_down)
        self.move_group_down_button.setEnabled(False)
        
        groups_buttons_layout.addWidget(self.add_group_button)
        groups_buttons_layout.addWidget(self.remove_group_button)
        groups_buttons_layout.addWidget(self.move_group_up_button)
        groups_buttons_layout.addWidget(self.move_group_down_button)
        groups_layout.addLayout(groups_buttons_layout)
        
        self.groups_list = QListWidget()
        self.groups_list.setObjectName("MusicGroupsList")
        self.groups_list.itemClicked.connect(self._on_group_selected)
        groups_layout.addWidget(self.groups_list)
        
        self.group_details_widget = QWidget()
        self.group_details_widget.setObjectName("GroupDetailsWidget")
        self.group_details_widget.setVisible(False)
        group_details_layout = QVBoxLayout(self.group_details_widget)
        

        
        conditions_group = QGroupBox("Playback Conditions")
        conditions_group.setObjectName("ConditionsGroup")
        conditions_group.setMinimumWidth(300)
        conditions_layout = QVBoxLayout(conditions_group)
        
        self.conditions_area = QWidget()
        self.conditions_area.setObjectName("ConditionsArea")
        self.conditions_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        conditions_area_layout = QVBoxLayout(self.conditions_area)
        conditions_area_layout.setContentsMargins(5, 5, 5, 5)
        conditions_area_layout.setSpacing(5)
        self.conditions_layout = QVBoxLayout()
        conditions_area_layout.addLayout(self.conditions_layout)
        
        self.add_condition_button = QPushButton("+")
        self.add_condition_button.setObjectName("AddConditionButton")
        self.add_condition_button.setToolTip("Add Condition")
        self.add_condition_button.clicked.connect(self._add_condition)
        conditions_area_layout.addWidget(self.add_condition_button)
        
        conditions_layout.addWidget(self.conditions_area)
        
        group_details_layout.addWidget(conditions_group)
        groups_layout.addWidget(self.group_details_widget)
        
        layout.addWidget(groups_group)
        
        files_group = QGroupBox("Music Files")
        files_group.setObjectName("MusicFilesGroup")
        files_layout = QVBoxLayout(files_group)
        
        files_buttons_layout = QHBoxLayout()
        self.convert_mp3_button = QPushButton("Convert MP3 to OGG")
        self.convert_mp3_button.setObjectName("ConvertMP3Button")
        self.convert_mp3_button.setMaximumHeight(25)
        self.convert_mp3_button.clicked.connect(self._convert_mp3_to_ogg)
        
        self.add_music_file_button = QPushButton("Add Music File")
        self.add_music_file_button.setObjectName("AddMusicFileButton")
        self.add_music_file_button.setMaximumHeight(25)
        self.add_music_file_button.clicked.connect(self._add_music_file)
        
        self.remove_music_file_button = QPushButton("Remove File")
        self.remove_music_file_button.setObjectName("RemoveMusicFileButton")
        self.remove_music_file_button.setMaximumHeight(25)
        self.remove_music_file_button.clicked.connect(self._remove_music_file)
        
        files_buttons_layout.addWidget(self.convert_mp3_button)
        files_buttons_layout.addWidget(self.add_music_file_button)
        files_buttons_layout.addWidget(self.remove_music_file_button)
        files_layout.addLayout(files_buttons_layout)
        
        self.music_files_list = QListWidget()
        self.music_files_list.setObjectName("MusicFilesList")
        self.music_files_list.setMaximumHeight(150)
        self.music_files_list.itemDoubleClicked.connect(self._play_music_file)
        files_layout.addWidget(self.music_files_list)
        
        test_music_layout = QHBoxLayout()
        self.test_music_button = QPushButton("Test Current Music")
        self.test_music_button.setObjectName("TestMusicButton")
        self.test_music_button.setMaximumHeight(25)
        self.test_music_button.clicked.connect(self._test_current_music)
        
        self.stop_music_button = QPushButton("Stop Music")
        self.stop_music_button.setObjectName("StopMusicButton")
        self.stop_music_button.setMaximumHeight(25)
        self.stop_music_button.clicked.connect(self._stop_current_music)
        self.stop_music_button.setEnabled(False)
        
        test_music_layout.addWidget(self.test_music_button)
        test_music_layout.addWidget(self.stop_music_button)
        files_layout.addLayout(test_music_layout)
        
        layout.addWidget(files_group)
        
        self.conversion_progress = QProgressBar()
        self.conversion_progress.setVisible(False)
        self.conversion_progress.setObjectName("ConversionProgress")
        layout.addWidget(self.conversion_progress)
        
        scroll_area.setWidget(content_widget)
        main_layout = QVBoxLayout(widget)
        main_layout.addWidget(scroll_area)
        
        self.current_music_player = None
        self.music_groups = {}
        self.music_files = {}
        self.title_music_file = None
        self.intro_music_file = None
        self.music_conditions = {}
        self.group_priority_order = []
        
        return widget
    
    def _apply_styling(self):
        if not self.theme_colors:
            return
        
        base_color = self.theme_colors.get('base_color', '#00FF66')
        bg_value = int(80 * self.theme_colors.get("contrast", 0.5))
        bg_color = f"#{bg_value:02x}{bg_value:02x}{bg_value:02x}"
        darker_bg = f"#{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}"
        
        self.setStyleSheet(f"""
            QWidget#AudioManagerWidget {{
                background-color: {darker_bg};
                color: {base_color};
            }}
            
            QWidget#AudioToggleContainer {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 5px;
            }}
            
            QPushButton#SFXAudioToggleButton, QPushButton#MusicAudioToggleButton {{
                background-color: {bg_color};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 5px;
                font-weight: bold;
            }}
            
            QPushButton#SFXAudioToggleButton:checked, QPushButton#MusicAudioToggleButton:checked {{
                background-color: {base_color};
                color: #000000;
            }}
            
            QWidget#AudioManagerScrollArea {{
                background-color: {darker_bg};
                border: none;
            }}
            
            QWidget#AudioManagerContent {{
                background-color: {darker_bg};
            }}
            
            QLabel#AudioSettingsLabel {{
                color: {base_color};
                font-weight: bold;
                background-color: transparent;
            }}
            
            QGroupBox {{
                color: {base_color};
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                margin-top: 6px;
                font-weight: bold;
            }}
            
            QGroupBox::title {{
                color: {base_color};
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                background-color: {darker_bg};
            }}
            
            QSlider::groove:horizontal {{
                height: 6px;
                background: {bg_color};
                border: 1px solid {base_color};
                border-radius: 3px;
            }}
            
            QSlider::handle:horizontal {{
                background: {base_color};
                border: 1px solid {base_color};
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            
            QCheckBox {{
                color: {base_color};
                spacing: 5px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {base_color};
                background: {bg_color};
                border-radius: 3px;
            }}
            
            QCheckBox::indicator:checked {{
                background: {base_color};
            }}
            
            QPushButton {{
                background-color: {bg_color};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 6px 12px;
                min-height: 20px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {base_color};
                color: #000000;
            }}
            
            QPushButton:pressed {{
                background-color: {darker_bg};
                border: 2px solid {base_color};
            }}
            
            QListWidget {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                color: {base_color};
                selection-background-color: {base_color};
                selection-color: #000000;
                outline: none;
            }}
            
            QListWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {bg_color};
            }}
            
            QListWidget::item:selected {{
                background-color: {base_color};
                color: #000000;
            }}
            
            QListWidget::item:hover {{
                background-color: {bg_color};
            }}
            
            QProgressBar {{
                border: 1px solid {base_color};
                border-radius: 3px;
                text-align: center;
                color: {base_color};
                background-color: {darker_bg};
            }}
            
            QProgressBar::chunk {{
                background-color: {base_color};
                border-radius: 2px;
            }}
            
            QLineEdit {{
                background-color: {bg_color};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 4px 8px;
                selection-background-color: {base_color};
                selection-color: #000000;
            }}
            
            QLineEdit:focus {{
                border: 2px solid {base_color};
                background-color: {darker_bg};
            }}
            
            QComboBox {{
                background-color: {bg_color};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 4px 8px;
                min-width: 80px;
            }}
            
            QComboBox:focus {{
                border: 2px solid {base_color};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {base_color};
                margin-right: 5px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                selection-background-color: {base_color};
                selection-color: #000000;
            }}
            
            QRadioButton {{
                color: {base_color};
                spacing: 5px;
            }}
            
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {base_color};
                background: {bg_color};
                border-radius: 8px;
            }}
            
            QRadioButton::indicator:checked {{
                background: {base_color};
            }}
        """)
    
    def _apply_loaded_settings(self):
        if not self.workflow_data_dir:
            return
        
        settings_file = os.path.join(self.workflow_data_dir, "resources", "data files", "settings", "audio_settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.master_volume_slider.setValue(settings.get('master_volume', 100))
                self.sfx_enabled_checkbox.setChecked(settings.get('sfx_enabled', True))
                self.sfx_volume_slider.setValue(settings.get('sfx_volume', 75))
                self.voice_enabled_checkbox.setChecked(settings.get('voice_enabled', True))
                self.voice_volume_slider.setValue(settings.get('voice_volume', 100))
                
                self.volume_value_label.setText(f"{self.master_volume_slider.value()}%")
                self.sfx_volume_slider.setEnabled(self.sfx_enabled_checkbox.isChecked())
                self.voice_volume_slider.setEnabled(self.voice_enabled_checkbox.isChecked())
            except Exception as e:
                print(f"Error loading audio settings: {e}")
        
        self._load_music_data()
        self._load_title_music_from_variables()
    
    def _connect_signals(self):
        self.sfx_btn.toggled.connect(self._on_sfx_toggle)
        self.music_btn.toggled.connect(self._on_music_toggle)
        
        self.master_volume_slider.valueChanged.connect(self._on_master_volume_changed)
        self.sfx_enabled_checkbox.toggled.connect(self._on_sfx_enabled_changed)
        self.sfx_volume_slider.valueChanged.connect(self._on_sfx_volume_changed)
        self.voice_enabled_checkbox.toggled.connect(self._on_voice_enabled_changed)
        self.voice_volume_slider.valueChanged.connect(self._on_voice_volume_changed)
        
        self.test_sfx_button.clicked.connect(self._test_sfx)
        self.test_music_button.clicked.connect(self._test_current_music)
        self.test_voice_button.clicked.connect(self._test_voice)
    
    def _on_sfx_toggle(self, checked):
        if checked:
            self.content_stack.setCurrentIndex(0)
    
    def _on_music_toggle(self, checked):
        if checked:
            self.content_stack.setCurrentIndex(1)
    
    def _on_master_volume_changed(self, value):
        self.volume_value_label.setText(f"{value}%")
        self._save_audio_settings()
    
    def _on_sfx_enabled_changed(self, enabled):
        self.sfx_volume_slider.setEnabled(enabled)
        self._save_audio_settings()
    
    def _on_sfx_volume_changed(self, value):
        self._save_audio_settings()
    
    def _on_voice_enabled_changed(self, enabled):
        self.voice_volume_slider.setEnabled(enabled)
        self._save_audio_settings()
    
    def _on_voice_volume_changed(self, value):
        self._save_audio_settings()
    
    def _save_audio_settings(self):
        if not self.workflow_data_dir:
            return
        
        settings = {
            'master_volume': self.master_volume_slider.value(),
            'sfx_enabled': self.sfx_enabled_checkbox.isChecked(),
            'sfx_volume': self.sfx_volume_slider.value(),
            'voice_enabled': self.voice_enabled_checkbox.isChecked(),
            'voice_volume': self.voice_volume_slider.value(),
        }
        
        settings_dir = os.path.join(self.workflow_data_dir, "resources", "data files", "settings")
        os.makedirs(settings_dir, exist_ok=True)
        settings_file = os.path.join(settings_dir, "audio_settings.json")
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving audio settings: {e}")
    
    def _test_sfx(self):
        print("Testing SFX...")
    
    def _test_music(self):
        print("Testing Music...")
    
    def _test_voice(self):
        print("Testing Voice...")
    
    def _add_music_group(self):
        group_name, ok = QInputDialog.getText(self, "Add Music Group", "Enter group name:")
        if ok and group_name.strip():
            group_name = group_name.strip()
            if group_name not in self.music_groups:
                self.music_groups[group_name] = []
                self.group_priority_order.append(group_name)
                self._refresh_groups_list()
                self._save_music_data()
    
    def _remove_music_group(self):
        current_item = self.groups_list.currentItem()
        if current_item:
            group_name = current_item.text()
            if group_name in self.music_groups:
                reply = QMessageBox.question(
                    self, "Remove Group", 
                    f"Are you sure you want to remove the group '{group_name}' and all its music files?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    del self.music_groups[group_name]
                    if group_name in self.group_priority_order:
                        self.group_priority_order.remove(group_name)
                    self._refresh_groups_list()
                    self._refresh_music_files_list()
                    self._save_music_data()
    
    def _on_group_selected(self, item):
        self._refresh_music_files_list()
        if item:
            group_name = item.text()
            self.group_details_widget.setVisible(True)
            self._load_group_details(group_name)
        else:
            self.group_details_widget.setVisible(False)
        self._update_move_buttons_state()
    
    def _convert_mp3_to_ogg(self):
        input_file, _ = QFileDialog.getOpenFileName(
            self, "Select MP3 File", "", "MP3 Files (*.mp3)"
        )
        if input_file:
            if not self._check_ffmpeg_available():
                QMessageBox.warning(
                    self, "FFmpeg Not Found", 
                    "FFmpeg is required for MP3 to OGG conversion. Please install FFmpeg and ensure it's in your PATH."
                )
                return
            
            output_dir = os.path.join(self.workflow_data_dir, "resources", "audio", "music")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = os.path.splitext(os.path.basename(input_file))[0]
            output_file = os.path.join(output_dir, f"{filename}.ogg")
            
            self.conversion_progress.setVisible(True)
            self.conversion_progress.setValue(0)
            self.convert_mp3_button.setEnabled(False)
            
            self.ogg_converter = OGGConverterThread(input_file, output_file)
            self.ogg_converter.conversion_finished.connect(self._on_conversion_finished)
            self.ogg_converter.conversion_failed.connect(self._on_conversion_failed)
            self.ogg_converter.start()
    
    def _on_conversion_finished(self, input_file, output_file):
        self.conversion_progress.setVisible(False)
        self.convert_mp3_button.setEnabled(True)
        
        if self._validate_ogg_file(output_file):
            QMessageBox.information(
                self, "Conversion Complete", 
                f"Successfully converted {os.path.basename(input_file)} to OGG format."
            )
            self._refresh_music_files_list()
        else:
            QMessageBox.warning(
                self, "Conversion Issue", 
                f"File was converted but validation failed. The OGG file may be corrupted."
            )
    
    def _on_conversion_failed(self, input_file, error_msg):
        self.conversion_progress.setVisible(False)
        self.convert_mp3_button.setEnabled(True)
        QMessageBox.critical(
            self, "Conversion Failed", 
            f"Failed to convert {os.path.basename(input_file)}: {error_msg}"
        )
    
    def _add_music_file(self):
        current_group_item = self.groups_list.currentItem()
        if not current_group_item:
            QMessageBox.warning(self, "No Group Selected", "Please select a group first.")
            return
        
        group_name = current_group_item.text()
        music_dir = os.path.join(self.workflow_data_dir, "resources", "audio", "music")
        
        if not os.path.exists(music_dir):
            os.makedirs(music_dir, exist_ok=True)
        
        music_file, _ = QFileDialog.getOpenFileName(
            self, "Select Music File", music_dir, "OGG Files (*.ogg)"
        )
        
        if music_file:
            if music_file.endswith('.ogg'):
                filename = os.path.basename(music_file)
                display_name, ok = QInputDialog.getText(
                    self, "Music File Name", 
                    "Enter display name for this music file:",
                    text=os.path.splitext(filename)[0]
                )
                
                if ok and display_name.strip():
                    display_name = display_name.strip()
                    music_info = {
                        'filename': filename,
                        'display_name': display_name,
                        'group': group_name,
                        'filepath': music_file
                    }
                    
                    self.music_files[filename] = music_info
                    if group_name not in self.music_groups:
                        self.music_groups[group_name] = []
                    self.music_groups[group_name].append(filename)
                    
                    self._refresh_music_files_list()
                    self._save_music_data()
            else:
                QMessageBox.warning(
                    self, "Invalid Format", 
                    "Please select an OGG file. Use the 'Convert MP3 to OGG' button for MP3 files."
                )
    
    def _remove_music_file(self):
        current_item = self.music_files_list.currentItem()
        if current_item:
            filename = current_item.data(Qt.UserRole)
            if filename in self.music_files:
                music_info = self.music_files[filename]
                reply = QMessageBox.question(
                    self, "Remove Music File", 
                    f"Are you sure you want to remove '{music_info['display_name']}'?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    group_name = music_info['group']
                    if group_name in self.music_groups and filename in self.music_groups[group_name]:
                        self.music_groups[group_name].remove(filename)
                    
                    del self.music_files[filename]
                    self._refresh_music_files_list()
                    self._save_music_data()
    
    def _play_music_file(self, item):
        filename = item.data(Qt.UserRole)
        if filename in self.music_files:
            music_info = self.music_files[filename]
            filepath = music_info['filepath']
            
            self._stop_current_music()
            
            try:
                from core.music_manager import get_music_manager
                music_manager = get_music_manager()
                
                if self.main_ui and hasattr(self.main_ui, '_music_volume'):
                    music_manager.set_volume(self.main_ui._music_volume)
                
                success = music_manager.play_music(filepath, fade_in_ms=800, loop=False)
                if success:
                    self.current_music_player = music_manager
                    item.setBackground(QColor(0, 255, 0, 100))
                    item.setToolTip("Playing...")
                    
                    self.test_music_button.setEnabled(False)
                    self.stop_music_button.setEnabled(True)
                else:
                    print(f"Failed to play music: {filepath}")
                    
            except Exception as e:
                print(f"Error using global music manager: {e}")
                # Fallback to old method
                self.current_music_player = MusicPlayerThread(filepath)
                self.current_music_player.playback_finished.connect(self._on_music_playback_finished)
                self.current_music_player.start()
                
                item.setBackground(QColor(0, 255, 0, 100))
                item.setToolTip("Playing...")
                
                self.test_music_button.setEnabled(False)
                self.stop_music_button.setEnabled(True)
    
    def _on_music_playback_finished(self):
        for i in range(self.music_files_list.count()):
            item = self.music_files_list.item(i)
            if item.background() != QColor(0, 0, 0, 0):
                item.setBackground(QColor(0, 0, 0, 0))
                item.setToolTip("")
                break
        
        self.test_music_button.setEnabled(True)
        self.stop_music_button.setEnabled(False)
        self.current_music_player = None
    
    def _test_current_music(self):
        current_item = self.music_files_list.currentItem()
        if current_item:
            self._play_music_file(current_item)
        else:
            QMessageBox.information(self, "No Selection", "Please select a music file to test.")
    
    def _refresh_groups_list(self):
        self.groups_list.clear()
        
        # Get groups in priority order, then add any new groups not in the priority list
        ordered_groups = []
        for group_name in self.group_priority_order:
            if group_name in self.music_groups:
                ordered_groups.append(group_name)
        
        # Add any groups that aren't in the priority order yet
        for group_name in sorted(self.music_groups.keys()):
            if group_name not in ordered_groups:
                ordered_groups.append(group_name)
                self.group_priority_order.append(group_name)
        
        # Remove groups from priority order that no longer exist
        self.group_priority_order = [g for g in self.group_priority_order if g in self.music_groups]
        
        for group_name in ordered_groups:
            item = QListWidgetItem(group_name)
            self.groups_list.addItem(item)
            
        self._update_move_buttons_state()
    
    def _refresh_music_files_list(self):
        self.music_files_list.clear()
        current_group_item = self.groups_list.currentItem()
        
        if current_group_item:
            group_name = current_group_item.text()
            if group_name in self.music_groups:
                for filename in sorted(self.music_groups[group_name]):
                    if filename in self.music_files:
                        music_info = self.music_files[filename]
                        item = QListWidgetItem(music_info['display_name'])
                        item.setData(Qt.UserRole, filename)
                        item.setToolTip(f"File: {filename}")
                        self.music_files_list.addItem(item)
    
    def _save_music_data(self):
        if not self.workflow_data_dir:
            return
        
        music_data = {
            'groups': self.music_groups,
            'files': self.music_files,
            'conditions': self.music_conditions,
            'group_priority_order': self.group_priority_order
        }
        
        music_dir = os.path.join(self.workflow_data_dir, "resources", "data files", "settings")
        os.makedirs(music_dir, exist_ok=True)
        music_file = os.path.join(music_dir, "music_data.json")
        
        try:
            with open(music_file, 'w', encoding='utf-8') as f:
                json.dump(music_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving music data: {e}")
    
    def _load_music_data(self):
        if not self.workflow_data_dir:
            return
        
        music_file = os.path.join(
            self.workflow_data_dir, "resources", "data files", "settings", "music_data.json"
        )
        
        if os.path.exists(music_file):
            try:
                with open(music_file, 'r', encoding='utf-8') as f:
                    music_data = json.load(f)
                
                self.music_groups = music_data.get('groups', {})
                self.music_files = music_data.get('files', {})
                self.music_conditions = music_data.get('conditions', {})
                self.group_priority_order = music_data.get('group_priority_order', [])
                
                self._refresh_groups_list()
                self._refresh_music_files_list()
                

                
            except Exception as e:
                print(f"Error loading music data: {e}")
    
    def _check_ffmpeg_available(self):
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _validate_ogg_file(self, filepath):
        try:
            if not os.path.exists(filepath):
                return False
            
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                return False
            
            cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', filepath]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                try:
                    info = json.loads(result.stdout)
                    format_info = info.get('format', {})
                    duration = format_info.get('duration')
                    if duration and float(duration) > 0:
                        print(f"OGG file validated: {filepath}, duration: {duration}s, size: {file_size} bytes")
                        return True
                except:
                    pass
            
            print(f"OGG file validation failed: {filepath}")
            return False
            
        except Exception as e:
            print(f"Error validating OGG file: {e}")
            return False
    
    def _set_title_music(self):
        music_dir = os.path.join(self.workflow_data_dir, "resources", "audio", "music")
        if not os.path.exists(music_dir):
            QMessageBox.warning(self, "No Music Folder", "Music folder does not exist. Please add some music files first.")
            return
        
        ogg_files = []
        for file in os.listdir(music_dir):
            if file.lower().endswith('.ogg'):
                ogg_files.append(file)
        
        if not ogg_files:
            QMessageBox.warning(self, "No OGG Files", "No OGG music files found in the music folder.")
            return
        
        if len(ogg_files) == 1:
            selected_file = ogg_files[0]
        else:
            selected_file, ok = QInputDialog.getItem(
                self, "Select Title Music", 
                "Choose music file for title screen:",
                ogg_files, 0, False
            )
            if not ok:
                return
        
        self.title_music_file = selected_file
        self.title_music_label.setText(f"Title Music: {selected_file}")
        self._save_title_music_to_variables()
        QMessageBox.information(
            self, "Title Music Set", 
            f"'{selected_file}' is now set as title music."
        )

    def _clear_title_music(self):
        if getattr(self, 'title_music_file', None):
            self.title_music_file = None
            self.title_music_label.setText("No title music set")
            self._save_title_music_to_variables()
            QMessageBox.information(self, "Title Music Cleared", "Title music has been cleared.")
        else:
            QMessageBox.information(self, "No Title Music", "No title music is currently set.")

    def _get_variables_file(self):
        try:
            if self.tab_data:
                scm = self.tab_data.get('start_conditions_manager_widget')
                if scm and hasattr(scm, 'variables_file'):
                    return scm.variables_file
        except Exception:
            pass
        return None

    def _load_title_music_from_variables(self):
        vars_file = self._get_variables_file()
        if not vars_file or not os.path.exists(vars_file):
            self.title_music_file = None
            self.title_music_label.setText("No title music set")
            return
        try:
            with open(vars_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.title_music_file = data.get('title_music_file')
            if self.title_music_file:
                self.title_music_label.setText(f"Title Music: {self.title_music_file}")
            else:
                self.title_music_label.setText("No title music set")
        except Exception as e:
            print(f"Error loading title music from variables: {e}")
            self.title_music_file = None
            self.title_music_label.setText("No title music set")

    def _save_title_music_to_variables(self):
        vars_file = self._get_variables_file()
        if not vars_file:
            return
        try:
            if os.path.exists(vars_file):
                with open(vars_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                os.makedirs(os.path.dirname(vars_file), exist_ok=True)
                data = {}
            data['title_music_file'] = self.title_music_file
            with open(vars_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving title music to variables: {e}")

    def _set_intro_music(self):
        music_dir = os.path.join(self.workflow_data_dir, "resources", "audio", "music")
        if not os.path.exists(music_dir):
            QMessageBox.warning(self, "No Music Folder", "Music folder does not exist. Please add some music files first.")
            return
        
        ogg_files = []
        for file in os.listdir(music_dir):
            if file.lower().endswith('.ogg'):
                ogg_files.append(file)
        
        if not ogg_files:
            QMessageBox.warning(self, "No OGG Files", "No OGG music files found in the music folder.")
            return
        
        if len(ogg_files) == 1:
            selected_file = ogg_files[0]
        else:
            selected_file, ok = QInputDialog.getItem(
                self, "Select Intro Music", 
                "Choose music file for introduction sequence:",
                ogg_files, 0, False
            )
            if not ok:
                return
        
        self.intro_music_file = selected_file
        self.intro_music_label.setText(f"Intro Music: {selected_file}")
        self._save_intro_music_to_variables()
        QMessageBox.information(
            self, "Intro Music Set", 
            f"'{selected_file}' is now set as introduction music."
        )

    def _clear_intro_music(self):
        if getattr(self, 'intro_music_file', None):
            self.intro_music_file = None
            self.intro_music_label.setText("No intro music set")
            self._save_intro_music_to_variables()
            QMessageBox.information(self, "Intro Music Cleared", "Introduction music has been cleared.")
        else:
            QMessageBox.information(self, "No Intro Music", "No introduction music is currently set.")

    def _load_intro_music_from_variables(self):
        vars_file = self._get_variables_file()
        if not vars_file or not os.path.exists(vars_file):
            self.intro_music_file = None
            self.intro_music_label.setText("No intro music set")
            return
        try:
            with open(vars_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.intro_music_file = data.get('intro_music_file')
            if self.intro_music_file:
                self.intro_music_label.setText(f"Intro Music: {self.intro_music_file}")
            else:
                self.intro_music_label.setText("No intro music set")
        except Exception as e:
            print(f"Error loading intro music from variables: {e}")
            self.intro_music_file = None
            self.intro_music_label.setText("No intro music set")

    def _save_intro_music_to_variables(self):
        vars_file = self._get_variables_file()
        if not vars_file:
            return
        try:
            if os.path.exists(vars_file):
                with open(vars_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                os.makedirs(os.path.dirname(vars_file), exist_ok=True)
                data = {}
            data['intro_music_file'] = self.intro_music_file
            with open(vars_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving intro music to variables: {e}")



    def _load_group_details(self, group_name):
        # Clear existing condition rows
        while self.conditions_layout.count() > 0:
            item = self.conditions_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Load conditions for this group
        if group_name in self.music_conditions:
            for i, condition_data in enumerate(self.music_conditions[group_name]):
                self._create_condition_row_widget(group_name, i, condition_data)

    def _add_condition(self):
        current_item = self.groups_list.currentItem()
        if current_item:
            group_name = current_item.text()
            self._add_condition_row(group_name)

    def _add_condition_row(self, group_name):
        if group_name not in self.music_conditions:
            self.music_conditions[group_name] = []
        
        condition_data = {
            "scope": "Global",
            "variable": "",
            "operator": "==",
            "value": ""
        }
        
        self.music_conditions[group_name].append(condition_data)
        self._create_condition_row_widget(group_name, len(self.music_conditions[group_name]) - 1, condition_data)
        self._save_music_data()



    def _create_condition_row_widget(self, group_name, condition_index, condition_data):
        row_widget = QWidget()
        row_widget.setObjectName("ConditionRow")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)
        
        scope_group = QButtonGroup(row_widget)
        scope_global_radio = QRadioButton("Global")
        scope_global_radio.setObjectName("ConditionScopeGlobalRadio")
        scope_global_radio.setToolTip("Global variable")
        scope_global_radio.setChecked(condition_data.get("scope") == "Global")
        scope_character_radio = QRadioButton("Character")
        scope_character_radio.setObjectName("ConditionScopeCharacterRadio")
        scope_character_radio.setToolTip("Character variable")
        scope_player_radio = QRadioButton("Player")
        scope_player_radio.setObjectName("ConditionScopePlayerRadio")
        scope_player_radio.setToolTip("Player character variable")
        scope_setting_radio = QRadioButton("Setting")
        scope_setting_radio.setObjectName("ConditionScopeSettingRadio")
        scope_setting_radio.setToolTip("Setting variable")
        
        scope_group.addButton(scope_global_radio)
        scope_group.addButton(scope_character_radio)
        scope_group.addButton(scope_player_radio)
        scope_group.addButton(scope_setting_radio)
        
        row_layout.addWidget(scope_global_radio)
        row_layout.addWidget(scope_character_radio)
        row_layout.addWidget(scope_player_radio)
        row_layout.addWidget(scope_setting_radio)
        
        var_name_input = QLineEdit()
        var_name_input.setObjectName("ConditionVarNameInput")
        var_name_input.setPlaceholderText("Variable Name")
        var_name_input.setText(condition_data.get("variable", ""))
        var_name_input.textChanged.connect(lambda text: self._update_condition_data(group_name, condition_index, "variable", text))
        row_layout.addWidget(var_name_input, 2)
        
        operator_combo = QComboBox()
        operator_combo.setObjectName("ConditionOperatorCombo")
        operator_combo.addItems(["==", "!=", ">", "<", ">=", "<=", "exists", "not exists", "contains", "not contains"])
        operator_combo.setCurrentText(condition_data.get("operator", "=="))
        operator_combo.currentTextChanged.connect(lambda text: self._update_condition_data(group_name, condition_index, "operator", text))
        row_layout.addWidget(operator_combo, 1)
        
        value_input = QLineEdit()
        value_input.setObjectName("ConditionValueInput")
        value_input.setPlaceholderText("Value")
        value_input.setText(condition_data.get("value", ""))
        value_input.textChanged.connect(lambda text: self._update_condition_data(group_name, condition_index, "value", text))
        row_layout.addWidget(value_input, 2)
        
        remove_button = QPushButton("-")
        remove_button.setObjectName("RemoveConditionButton")
        remove_button.setFixedWidth(25)
        remove_button.clicked.connect(lambda: self._remove_condition_row(group_name, condition_index, row_widget))
        row_layout.addWidget(remove_button)
        
        def update_value_visibility():
            op = operator_combo.currentText()
            value_input.setVisible(op not in ["exists", "not exists"])
        
        operator_combo.currentTextChanged.connect(update_value_visibility)
        update_value_visibility()
        
        def update_scope():
            if scope_global_radio.isChecked():
                scope = "Global"
            elif scope_character_radio.isChecked():
                scope = "Character"
            elif scope_player_radio.isChecked():
                scope = "Player"
            elif scope_setting_radio.isChecked():
                scope = "Setting"
            else:
                scope = "Global"
            self._update_condition_data(group_name, condition_index, "scope", scope)
        
        scope_group.buttonClicked.connect(update_scope)
        
        self.conditions_layout.addWidget(row_widget)
        return row_widget

    def _update_condition_data(self, group_name, condition_index, field, value):
        if group_name in self.music_conditions and condition_index < len(self.music_conditions[group_name]):
            self.music_conditions[group_name][condition_index][field] = value
            self._save_music_data()

    def _remove_condition_row(self, group_name, condition_index, row_widget):
        if group_name in self.music_conditions and condition_index < len(self.music_conditions[group_name]):
            del self.music_conditions[group_name][condition_index]
            self.conditions_layout.removeWidget(row_widget)
            row_widget.deleteLater()
            self._save_music_data()
            # Reload the entire group details to fix the indices
            self._load_group_details(group_name)





    def _evaluate_conditions(self, conditions, tab_data):
        if not conditions:
            return True
        
        for condition in conditions:
            if not self._evaluate_single_condition(condition, tab_data):
                return False
        
        return True

    def _evaluate_single_condition(self, condition, tab_data):
        try:
            scope = condition.get('scope', 'Global')
            variable = condition.get('variable', '')
            operator = condition.get('operator', '==')
            value = condition.get('value', '')
            
            if not variable:
                return False
            
            actual_value = self._get_variable_value(scope, variable, tab_data)
            
            if operator == "exists":
                return actual_value is not None and actual_value != ""
            elif operator == "not exists":
                return actual_value is None or actual_value == ""
            elif operator == "contains":
                return str(actual_value).lower().find(str(value).lower()) >= 0
            elif operator == "not contains":
                return str(actual_value).lower().find(str(value).lower()) < 0
            elif operator == "==":
                return str(actual_value).lower() == str(value).lower()
            elif operator == "!=":
                return str(actual_value).lower() != str(value).lower()
            elif operator in [">", "<", ">=", "<="]:
                try:
                    actual_num = float(actual_value) if actual_value is not None else 0
                    target_num = float(value)
                    if operator == ">":
                        return actual_num > target_num
                    elif operator == "<":
                        return actual_num < target_num
                    elif operator == ">=":
                        return actual_num >= target_num
                    elif operator == "<=":
                        return actual_num <= target_num
                except (ValueError, TypeError):
                    return False
            
            return False
            
        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return False

    def _get_variable_value(self, scope, variable, tab_data):
        try:
            if scope == "Global":
                vars_file = self._get_variables_file()
                if vars_file and os.path.exists(vars_file):
                    with open(vars_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return data.get(variable)
            elif scope == "Character":
                if tab_data and 'context' in tab_data:
                    for msg in tab_data['context']:
                        if 'character' in msg and msg['character'] == variable:
                            return msg.get('content', '')
            elif scope == "Player":
                if tab_data and 'context' in tab_data:
                    for msg in tab_data['context']:
                        if 'role' in msg and msg['role'] == 'user':
                            return msg.get('content', '')
            elif scope == "Setting":
                vars_file = self._get_variables_file()
                if vars_file and os.path.exists(vars_file):
                    with open(vars_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return data.get(f"setting_{variable}")
            
            return None
            
        except Exception as e:
            print(f"Error getting variable value: {e}")
            return None

    def _update_move_buttons_state(self):
        current_item = self.groups_list.currentItem()
        if not current_item:
            self.move_group_up_button.setEnabled(False)
            self.move_group_down_button.setEnabled(False)
            return
        
        current_row = self.groups_list.row(current_item)
        self.move_group_up_button.setEnabled(current_row > 0)
        self.move_group_down_button.setEnabled(current_row < self.groups_list.count() - 1)

    def _move_group_up(self):
        current_item = self.groups_list.currentItem()
        if not current_item:
            return
        
        current_row = self.groups_list.row(current_item)
        if current_row > 0:
            group_name = current_item.text()
            
            # Update priority order
            current_index = self.group_priority_order.index(group_name)
            self.group_priority_order[current_index], self.group_priority_order[current_index - 1] = \
                self.group_priority_order[current_index - 1], self.group_priority_order[current_index]
            
            # Refresh and maintain selection by group name
            self._refresh_groups_list()
            self._select_group_by_name(group_name)
            self._save_music_data()

    def _move_group_down(self):
        current_item = self.groups_list.currentItem()
        if not current_item:
            return
        
        current_row = self.groups_list.row(current_item)
        if current_row < self.groups_list.count() - 1:
            group_name = current_item.text()
            
            # Update priority order
            current_index = self.group_priority_order.index(group_name)
            self.group_priority_order[current_index], self.group_priority_order[current_index + 1] = \
                self.group_priority_order[current_index + 1], self.group_priority_order[current_index]
            
            # Refresh and maintain selection by group name
            self._refresh_groups_list()
            self._select_group_by_name(group_name)
            self._save_music_data()

    def _select_group_by_name(self, group_name):
        """Find and select a group by name in the groups list"""
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            if item.text() == group_name:
                self.groups_list.setCurrentItem(item)
                # Trigger the selection event manually to update UI
                self._on_group_selected(item)
                break
