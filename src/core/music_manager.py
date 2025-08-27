import pygame
import subprocess
import threading
import time
import os
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class GlobalMusicManager(QObject):
    music_started = pyqtSignal(str)
    music_stopped = pyqtSignal()
    music_faded_out = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._current_music_path = None
        self._current_ffplay_process = None
        self._current_pygame_music = None
        self._fade_timer = None
        self._fade_duration = 1500
        self._music_volume = 1.0
        self._is_fading = False
        self._lock = threading.Lock()
        
        # Initialize pygame mixer for potential fallback (non-OGG files only)
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            print("✓ Pygame mixer initialized (fallback for non-OGG files)")
        except Exception as e:
            print(f"⚠️  Pygame mixer initialization failed: {e}")
    
    def set_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        old_volume = self._music_volume
        self._music_volume = max(0.0, min(1.0, volume))
        
        playback_method = self.get_playback_method()
        print(f"Volume change: {old_volume:.2f} -> {self._music_volume:.2f} ({playback_method})")
        
        # Apply volume to currently playing music
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.set_volume(self._music_volume)
                print(f"✓ Applied volume {self._music_volume:.2f} to pygame music (instant, no restart)")
            else:
                print("✗ No pygame music currently playing")
        except Exception as e:
            print(f"Error setting pygame volume: {e}")
        
        # For ffplay (our primary method), restart with new volume
        if self._current_ffplay_process and self._current_ffplay_process.poll() is None:
            volume_diff = abs(old_volume - self._music_volume)
            if volume_diff > 0.05:  # Lower threshold for ffplay since it's our primary method
                print(f"Volume change detected ({volume_diff:.2f}), updating ffplay (seamless crossfade)...")
                self._restart_ffplay_with_new_volume()
            else:
                print(f"Volume change too small ({volume_diff:.2f}), skipping ffplay restart")
        else:
            print("No active ffplay process to restart")
    
    def play_music(self, music_path, fade_in_ms=1500, loop=True):
        """Play music with fade transition, stopping any current music"""
        if not os.path.exists(music_path):
            print(f"Music file not found: {music_path}")
            return False
        
        with self._lock:
            if self._is_fading:
                return False
            
            self._is_fading = True
            
            # Stop current music with fade out
            if self._current_music_path:
                self._fade_out_current_music()
                # Wait for fade out to complete
                time.sleep(self._fade_duration / 1000.0)
            
            # Start new music
            success = self._start_music(music_path, fade_in_ms, loop)
            if success:
                self._current_music_path = music_path
                self.music_started.emit(music_path)
            
            self._is_fading = False
            return success
    
    def _fade_out_current_music(self):
        """Fade out current music"""
        try:
            if self._current_ffplay_process:
                self._current_ffplay_process.terminate()
                self._current_ffplay_process.wait(timeout=2)
                self._current_ffplay_process = None
            
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(self._fade_duration)
                pygame.mixer.music.stop()
            
            self.music_faded_out.emit()
            
        except Exception as e:
            print(f"Error fading out music: {e}")
    
    def _start_music(self, music_path, fade_in_ms, loop):
        """Start music playback using ffplay as primary method (better OGG support)"""
        try:
            # Try ffplay first (excellent OGG support, better audio quality)
            if self._try_ffplay(music_path, loop):
                print(f"✓ Using ffplay for {os.path.basename(music_path)} (excellent OGG support)")
                return True
            
            # Only try pygame for non-OGG files as fallback
            if not music_path.lower().endswith('.ogg'):
                if self._try_pygame(music_path, fade_in_ms, loop):
                    print(f"✓ Using pygame fallback for {os.path.basename(music_path)} (non-OGG file)")
                    return True
            else:
                print(f"⚠️  Skipping pygame for OGG file: {os.path.basename(music_path)} (known compatibility issues)")
            
            return False
            
        except Exception as e:
            print(f"Error starting music: {e}")
            return False
    
    def _try_ffplay(self, music_path, loop):
        """Try to start music with ffplay"""
        try:
            if self._current_ffplay_process:
                self._current_ffplay_process.terminate()
                self._current_ffplay_process.wait(timeout=1)
                self._current_ffplay_process = None
            
            volume_filter = f'volume={self._music_volume:.2f}'
            
            if loop:
                cmd = ['ffplay', '-nodisp', '-loop', '-1', '-loglevel', 'error', 
                       '-af', volume_filter, music_path]
            else:
                cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'error', 
                       '-af', volume_filter, music_path]
            
            self._current_ffplay_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Start a thread to monitor when ffplay exits naturally
            def monitor_ffplay():
                try:
                    self._current_ffplay_process.wait()  # Wait for process to finish
                    # Only emit stopped signal if this is still our current process
                    if self._current_ffplay_process and self._current_ffplay_process.poll() is not None:
                        self.music_stopped.emit()
                except Exception:
                    pass
            
            import threading
            monitor_thread = threading.Thread(target=monitor_ffplay, daemon=True)
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            print(f"ffplay failed: {e}")
            return False
    
    def _try_pygame(self, music_path, fade_in_ms, loop):
        """Try to start music with pygame"""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self._music_volume)
            
            if loop:
                pygame.mixer.music.play(loops=-1, fade_ms=fade_in_ms)
            else:
                pygame.mixer.music.play(fade_ms=fade_in_ms)
            
            print(f"Started pygame music: {music_path}")
            return True
            
        except Exception as e:
            print(f"pygame failed: {e}")
            return False
    
    def stop_music(self, fade_out_ms=1500):
        """Stop current music with fade out"""
        with self._lock:
            if self._is_fading:
                return
            
            self._is_fading = True
            self._fade_out_current_music()
            
            # Wait for fade out to complete
            if fade_out_ms > 0:
                time.sleep(fade_out_ms / 1000.0)
            
            self._current_music_path = None
            self._is_fading = False
            self.music_stopped.emit()
    
    def pause_music(self):
        """Pause current music"""
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.pause()
        except Exception as e:
            print(f"Error pausing music: {e}")
    
    def unpause_music(self):
        """Unpause current music"""
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.unpause()
        except Exception as e:
            print(f"Error unpausing music: {e}")
    
    def is_playing(self):
        """Check if music is currently playing"""
        try:
            if self._current_ffplay_process and self._current_ffplay_process.poll() is None:
                return True
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                return True
            return False
        except:
            return False
    
    def get_current_music(self):
        """Get current music file path"""
        return self._current_music_path
    
    def get_playback_method(self):
        """Get the current playback method (pygame or ffplay)"""
        if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            return "pygame"
        elif self._current_ffplay_process and self._current_ffplay_process.poll() is None:
            return "ffplay"
        else:
            return "none"
    
    def get_volume_info(self):
        """Get current volume and playback method info"""
        return {
            'volume': self._music_volume,
            'playback_method': self.get_playback_method(),
            'current_music': self._current_music_path,
            'file_type': self._get_file_type(self._current_music_path) if self._current_music_path else None
        }
    
    def _get_file_type(self, file_path):
        """Get the file type/extension of a music file"""
        if not file_path:
            return None
        return os.path.splitext(file_path)[1].lower()
    
    def is_ogg_file(self, file_path):
        """Check if a file is an OGG file"""
        return file_path and file_path.lower().endswith('.ogg')
    
    def cleanup(self):
        """Clean up all music processes"""
        try:
            if self._current_ffplay_process:
                self._current_ffplay_process.terminate()
                self._current_ffplay_process.wait(timeout=2)
                self._current_ffplay_process = None
            
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                
        except Exception as e:
            print(f"Error cleaning up music manager: {e}")
    
    def _restart_ffplay_with_new_volume(self):
        """Restart ffplay process with new volume setting"""
        try:
            if not self._current_music_path:
                return
            
            # Store current music info
            current_path = self._current_music_path
            was_looping = True  # Assume looping for title music
            
            # Start new ffplay with new volume first (crossfade approach)
            volume_filter = f'volume={self._music_volume:.2f}'
            cmd = ['ffplay', '-nodisp', '-loop', '-1', '-loglevel', 'error', 
                   '-af', volume_filter, current_path]
            
            new_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Started new ffplay with volume {self._music_volume:.2f} (PID: {new_process.pid})")
            
            # Wait a moment for new process to start, then stop old one
            time.sleep(0.1)
            
            # Stop old ffplay
            if self._current_ffplay_process:
                self._current_ffplay_process.terminate()
                self._current_ffplay_process.wait(timeout=1)
                self._current_ffplay_process = None
            
            # Update to new process
            self._current_ffplay_process = new_process
            print(f"✓ Successfully switched to new ffplay process")
            
        except Exception as e:
            print(f"Error restarting ffplay with new volume: {e}")
            # If new process failed, keep old one
            if 'new_process' in locals():
                try:
                    new_process.terminate()
                except:
                    pass

# Global instance
_music_manager = None

def get_music_manager():
    """Get the global music manager instance"""
    global _music_manager
    if _music_manager is None:
        _music_manager = GlobalMusicManager()
    return _music_manager

def cleanup_music_manager():
    """Clean up the global music manager"""
    global _music_manager
    if _music_manager:
        _music_manager.cleanup()
        _music_manager = None
