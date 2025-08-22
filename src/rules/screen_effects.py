from PyQt5.QtWidgets import QWidget, QGraphicsBlurEffect
from PyQt5.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QColor
import random
import os
import json

class BlurEffect(QWidget):
    def __init__(self, parent_widget_to_blur=None):
        super().__init__()
        self.parent_widget_to_blur = parent_widget_to_blur
        self._enabled = False
        self._max_blur = 10.0
        self._animation_speed = 2000
        self._animate = True
        self.blur_effect_instance = None
        self.anim = None

    def set_config(self, enabled, radius=5, animation_speed=2000, animate=True):
        if not self.parent_widget_to_blur:
            return
        self._enabled = enabled
        self._max_blur = float(max(1, min(20, radius)))
        self._animation_speed = animation_speed
        self._animate = animate
        if self.parent_widget_to_blur.graphicsEffect() == self.blur_effect_instance:
            self.parent_widget_to_blur.setGraphicsEffect(None)
        if self.anim and self.anim.state() == QPropertyAnimation.Running:
            self.anim.stop()
        self.blur_effect_instance = None
        self.anim = None
        if self._enabled:
            self.blur_effect_instance = QGraphicsBlurEffect(self)
            self.blur_effect_instance.setBlurRadius(0.0 if self._animate else self._max_blur)
            self.parent_widget_to_blur.setGraphicsEffect(self.blur_effect_instance)
            if self._animate:
                self.anim = QPropertyAnimation(self.blur_effect_instance, b"blurRadius")
                self.anim.setEasingCurve(QEasingCurve.InOutSine)
                self.start_animation()

    def start_animation(self):
        if not self.blur_effect_instance or not self._enabled or not self._animate:
            return
        if self.anim.state() == QPropertyAnimation.Running:
            self.anim.stop()
        try:
            self.anim.finished.disconnect()
        except Exception:
            pass
        self.anim.setDuration(self._animation_speed)
        self.anim.setStartValue(self.blur_effect_instance.blurRadius())
        self.anim.setEndValue(self._max_blur)
        self.anim.start()
        self.anim.finished.connect(self._reverse_animation)

    def _reverse_animation(self):
        if not self.blur_effect_instance or not self._enabled or not self._animate:
            if self.parent_widget_to_blur and self.parent_widget_to_blur.graphicsEffect() == self.blur_effect_instance:
                self.blur_effect_instance.setBlurRadius(0.0)
                self.parent_widget_to_blur.setGraphicsEffect(None)
            return
        if self.anim.state() == QPropertyAnimation.Running:
            self.anim.stop()
        try:
            self.anim.finished.disconnect()
        except Exception:
            pass
        self.anim.setStartValue(self.blur_effect_instance.blurRadius())
        self.anim.setEndValue(0.0)
        self.anim.start()
        self.anim.finished.connect(self.start_animation)

class FlickerEffect(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._enabled = False
        self._intensity = 0.3
        self._frequency = 500
        self._current_opacity = 0
        self._color_mode = "white"
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_flicker)
        self.hide()
    
    def set_config(self, enabled, intensity=0.3, frequency=500, color_mode="white"):
        self._enabled = enabled
        self._intensity = max(0, min(1, intensity))
        self._frequency = frequency
        self._color_mode = color_mode.lower()
        if enabled:
            self.show()
            self.timer.start(self._frequency)
        else:
            self.hide()
            self.timer.stop()
    
    def _update_flicker(self):
        if random.random() < 0.3:
            self._current_opacity = random.uniform(0, self._intensity)
            self.update()
            QTimer.singleShot(50, self._reset_flicker)
    
    def _reset_flicker(self):
        self._current_opacity = 0
        self.update()
    
    def paintEvent(self, event):
        if self._current_opacity > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            if self._color_mode == "black":
                color = QColor(0, 0, 0, int(self._current_opacity * 255))
            else:
                color = QColor(255, 255, 255, int(self._current_opacity * 255))
            painter.fillRect(self.rect(), color)
    def resizeEvent(self, event):
        if self.parent:
            self.setGeometry(0, 0, self.parent.width(), self.parent.height())
        super().resizeEvent(event)


class StaticNoiseEffect(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._enabled = False
        self._intensity = 0.2
        self._update_frequency = 100
        self._dot_size = 3
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._regenerate_noise)
        self._noise_pattern = []
        self.hide()
    
    def set_config(self, enabled, intensity=0.2, frequency=100, dot_size=3):
        self._enabled = enabled
        self._intensity = min(0.5, max(0.05, intensity))
        self._update_frequency = frequency
        self._dot_size = max(1, min(5, dot_size))
        if enabled:
            if self.parent:
                self.setGeometry(0, 0, self.parent.width(), self.parent.height())
                self.raise_()
            self._regenerate_noise()
            self.show()
            self.timer.start(self._update_frequency)
        else:
            self.hide()
            self.timer.stop()
    
    def _regenerate_noise(self):
        if not self.isVisible() or not self._enabled:
            return
        self._noise_pattern = []
        width = self.width()
        height = self.height()
        area = width * height
        if area == 0: max_dots = 0
        else: max_dots = int((area / 500) * self._intensity) 
        for _ in range(max_dots):
            x = random.randint(0, width)
            y = random.randint(0, height)
            self._noise_pattern.append((x, y))
        self.update()
    
    def paintEvent(self, event):
        if not self._enabled or not self._noise_pattern:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        for x, y in self._noise_pattern:
            if random.random() > 0.5:
                color = QColor(255, 255, 255, random.randint(100, 180))
            else:
                color = QColor(180, 180, 180, random.randint(100, 180))
                
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRect(x, y, self._dot_size, self._dot_size)
    
    def resizeEvent(self, event):
        if self.parent:
            self.setGeometry(0, 0, self.parent.width(), self.parent.height())
        super().resizeEvent(event)


class DarkenBrightenEffect(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._enabled = False
        self._factor = 1.0
        self._animate = False
        self._animation_speed = 2000
        self._current_factor = 1.0
        self.anim = QPropertyAnimation(self, b"current_factor")
        self.anim.setEasingCurve(QEasingCurve.InOutSine)
        self.hide()

    def set_config(self, enabled, factor=1.0, animate=False, animation_speed=2000):
        self._enabled = enabled
        self._factor = float(factor)
        self._animate = animate
        self._animation_speed = animation_speed
        if self.anim.state() == QPropertyAnimation.Running:
            self.anim.stop()
        try:
            self.anim.finished.disconnect()
        except Exception:
            pass
        if enabled:
            if self.parent:
                self.setGeometry(0, 0, self.parent.width(), self.parent.height())
                self.raise_()
            self.show()
            if animate:
                self.start_animation()
            else:
                self._current_factor = self._factor
                self.update()
        else:
            self.hide()

    def get_current_factor(self):
        return self._current_factor

    def set_current_factor(self, value):
        self._current_factor = value
        self.update()

    current_factor = pyqtProperty(float, get_current_factor, set_current_factor)

    def start_animation(self):
        if self.anim.state() == QPropertyAnimation.Running:
            self.anim.stop()
        try:
            self.anim.finished.disconnect()
        except Exception:
            pass
        self.anim.setDuration(self._animation_speed)
        self.anim.setStartValue(self._factor)
        self.anim.setEndValue(1.0)
        self.anim.start()
        self.anim.finished.connect(self._reverse_animation)

    def _reverse_animation(self):
        if self.anim.state() == QPropertyAnimation.Running:
            self.anim.stop()
        try:
            self.anim.finished.disconnect()
        except Exception:
            pass
        self.anim.setDuration(self._animation_speed)
        self.anim.setStartValue(self._current_factor)
        self.anim.setEndValue(self._factor)
        self.anim.start()
        self.anim.finished.connect(self.start_animation)

    def paintEvent(self, event):
        if not self._enabled or self._current_factor == 1.0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self._current_factor < 1.0:
            opacity = 1.0 - self._current_factor
            color = QColor(0, 0, 0, int(opacity * 255))
        else:
            opacity = min(self._current_factor - 1.0, 1.0)
            color = QColor(255, 255, 255, int(opacity * 255))
        painter.fillRect(self.rect(), color)

    def resizeEvent(self, event):
        if self.parent:
            self.setGeometry(0, 0, self.parent.width(), self.parent.height())
        super().resizeEvent(event)


def load_effects_from_gamestate(tab_data):
    if not tab_data:
        return None
    workflow_data_dir = tab_data.get('workflow_data_dir')
    if not workflow_data_dir:
        return None
    gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
    if not os.path.exists(gamestate_path):
        return None
    try:
        with open(gamestate_path, 'r', encoding='utf-8') as f:
            gamestate = json.load(f)
        effects_config = gamestate.get('effects', {})
        return effects_config
    except Exception as e:
        print(f"Error loading effects from gamestate: {e}")
        return None

def update_screen_effects(workflow_data_dir, blur_enabled=False, blur_radius=0, blur_speed=2000, animate_blur=True,
                         flicker_enabled=False, flicker_intensity=0, flicker_frequency=500,
                         flicker_color="white", static_enabled=False, static_intensity=0,
                         static_frequency=100, static_dot_size=3):
    if not workflow_data_dir:
        print("Error: No workflow data directory provided")
        return False
    gamestate_path = os.path.join(workflow_data_dir, 'game', 'gamestate.json')
    if not os.path.exists(os.path.dirname(gamestate_path)):
        os.makedirs(os.path.dirname(gamestate_path))
    gamestate = {}
    if os.path.exists(gamestate_path):
        try:
            with open(gamestate_path, 'r', encoding='utf-8') as f:
                gamestate = json.load(f)
        except Exception as e:
            print(f"Error loading gamestate.json: {e}")
    if 'timers' not in gamestate:
        gamestate['timers'] = {'active_timers': []}
    effects = gamestate.get('effects', {})
    effects['blur'] = {
        'enabled': blur_enabled,
        'radius': blur_radius,
        'animation_speed': blur_speed,
        'animate': animate_blur
    }
    effects['flicker'] = {
        'enabled': flicker_enabled,
        'intensity': flicker_intensity,
        'frequency': flicker_frequency,
        'color': flicker_color
    }
    effects['static'] = {
        'enabled': static_enabled,
        'intensity': static_intensity,
        'frequency': static_frequency,
        'dot_size': static_dot_size
    }
    gamestate['effects'] = effects
    try:
        with open(gamestate_path, 'w', encoding='utf-8') as f:
            json.dump(gamestate, f, indent=2)
        print(f"Updated screen effects in {gamestate_path}")
        return True
    except Exception as e:
        print(f"Error saving gamestate.json: {e}")
        return False 