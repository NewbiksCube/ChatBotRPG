import os
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt5.QtGui import QColor, QPainter, QImage, QPixmap, QPen, QBrush

VIRTUAL_CANVAS_WIDTH = 10000
VIRTUAL_CANVAS_HEIGHT = 10000

class WorldMapDisplay(QLabel):
    def __init__(self, *args, **kwargs):
        self.parent_editor = kwargs.pop('parent_editor', None)
        self.map_type = kwargs.pop('map_type', None)
        super().__init__(*args, **kwargs)
        self._original_image = None
        self._processed_image = None
        self._crt_pixmap = None
        self._tint_color = QColor("#CCCCCC")
        self._border_color = QColor("#CCCCCC")
        self._zoom = 1.0
        self._zoom_level = 0
        self._zoom_step_factor = 1.15
        self._zoom_baseline_multiplier = 1.0
        self._max_zoom_level_allowed = 20
        self._pan = [0, 0]
        self._dragging = False
        self._last_mouse_pos = None
        self._pulse_time = 0.0
        self._virtual_width = 10000
        self._virtual_height = 10000
        self._player_pos = None
        self._player_setting_name = None
        self._player_dot_radius = 6
        self._player_dot_color = QColor(255, 0, 0, 200)
        self.setAlignment(Qt.AlignCenter)
        self.setText("Map Not Loaded")
        self.setStyleSheet("color: #AAAAAA; background-color: #222222; font-style: italic;")
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_animate)
        self._pulse_timer.start(50)
        self._show_grid = False
        self._dragging_selection = False
        self._is_zooming_fit = False

    def _pulse_animate(self):
        self._pulse_time += 0.05
        if self._pulse_time > 2 * 3.14159:
            self._pulse_time -= 2 * 3.14159
        if self._player_pos is not None:
            self.update()

    def _apply_tint_to_image(self, original_image, tint_color):
        if original_image is None or original_image.isNull():
            return None
        grayscale_image = original_image.convertToFormat(QImage.Format_Grayscale8)
        effect_image = QImage(grayscale_image.size(), QImage.Format_ARGB32_Premultiplied)
        p_effect = QPainter(effect_image)
        p_effect.drawImage(0, 0, grayscale_image)
        p_effect.setCompositionMode(QPainter.CompositionMode_Multiply)
        p_effect.fillRect(effect_image.rect(), tint_color)
        p_effect.end()
        return effect_image

    def _update_display_image(self):
        if self._original_image and not self._original_image.isNull():
            self._processed_image = self._apply_tint_to_image(self._original_image, self._tint_color)
            if self._processed_image and not self._processed_image.isNull():
                self._crt_pixmap = QPixmap.fromImage(self._processed_image)
                self.clear()
                self.setStyleSheet("background-color: transparent;")
            else:
                self._processed_image = None
                self._crt_pixmap = None
                self.setText("Error Processing Map")
                self.setStyleSheet("color: #AAAAAA; background-color: #222222; font-style: italic;")
        else:
            self._original_image = None
            self._processed_image = None
            self._crt_pixmap = None
            self.setText("Map Not Loaded")
            self.setStyleSheet("color: #AAAAAA; background-color: #222222; font-style: italic;")
        self.update()

    def _min_zoom(self):
        if not self._original_image or self._original_image.isNull():
            return 0.1
        widget_width = self.width()
        widget_height = self.height()
        if widget_width == 0 or widget_height == 0:
            return 0.1
        img_width = self._original_image.width()
        img_height = self._original_image.height()
        if img_width == 0 or img_height == 0:
            return 0.1
        zoom_to_fit_width = widget_width / img_width
        zoom_to_fit_height = widget_height / img_height
        zoom_to_fit = min(zoom_to_fit_width, zoom_to_fit_height)
        min_sensible_zoom = 0.05 
        return max(min_sensible_zoom, zoom_to_fit * 0.5)

    def _clamp_pan(self):
        if not self._processed_image or self._processed_image.isNull() or self.width() == 0 or self.height() == 0: # Check processed_image
            self._pan = [0,0]
            return
        img_width_zoomed = self._processed_image.width() * self._zoom
        img_height_zoomed = self._processed_image.height() * self._zoom
        widget_width = self.width()
        widget_height = self.height()
        if img_width_zoomed < widget_width:
            self._pan[0] = (widget_width - img_width_zoomed) / 2
        else:
            self._pan[0] = max(widget_width - img_width_zoomed, min(0, self._pan[0]))
        if img_height_zoomed < widget_height:
            self._pan[1] = (widget_height - img_height_zoomed) / 2
        else:
            self._pan[1] = max(widget_height - img_height_zoomed, min(0, self._pan[1]))

    def setPixmap(self, pixmap, orig_image=None, preserve_view_state=False):
        try:
            if isinstance(orig_image, QImage) and not orig_image.isNull():
                self._original_image = orig_image.copy()
                if not preserve_view_state:
                    self._zoom = 1.0 * self._zoom_baseline_multiplier
                    self._zoom_level = 0
                    self._pan = [0, 0]
                self._update_display_image()
                return True
            else:
                self._original_image = None
                self._update_display_image()
                return False
        except Exception as e:
            self._original_image = None
            self._update_display_image()
            return False

    def setBorderColor(self, color_hex_str):
        self._border_color = QColor(color_hex_str)
        self.update()

    def set_tint_color(self, color_hex_str):
        new_tint_color = QColor(color_hex_str)
        if new_tint_color.isValid() and self._tint_color != new_tint_color:
            self._tint_color = new_tint_color
            self._update_display_image()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom_level = min(self._max_zoom_level_allowed, self._zoom_level + 1)
        elif delta < 0:
            self._zoom_level = max(-self._max_zoom_level_allowed, self._zoom_level - 1)
        old_zoom = self._zoom
        new_zoom_factor = math.pow(self._zoom_step_factor, self._zoom_level) * self._zoom_baseline_multiplier
        self._zoom = new_zoom_factor
        min_abs_zoom = self._min_zoom()
        if self._original_image and not self._original_image.isNull():
             self._zoom = max(min_abs_zoom, self._zoom)
        else:
             self._zoom = max(0.01, self._zoom)
        mouse_pos = event.pos()
        image_x_before_zoom = (mouse_pos.x() - self._pan[0]) / old_zoom 
        image_y_before_zoom = (mouse_pos.y() - self._pan[1]) / old_zoom
        self._pan[0] = mouse_pos.x() - (image_x_before_zoom * self._zoom)
        self._pan[1] = mouse_pos.y() - (image_y_before_zoom * self._zoom)
        self._clamp_pan()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.RightButton:
            if self._original_image and not self._original_image.isNull():
                self._zoom_level = 0
                self._zoom = self._min_zoom()
                self._pan = [0, 0]
                self._clamp_pan()
                self.update()

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta = event.pos() - self._last_mouse_pos
            self._pan[0] += delta.x()
            self._pan[1] += delta.y()
            self._last_mouse_pos = event.pos()
            self._clamp_pan()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(Qt.ArrowCursor)

    def resizeEvent(self, event):
        if self._original_image and not self._original_image.isNull():
            current_min_zoom = self._min_zoom()
            if abs(self._zoom - current_min_zoom) < 0.01:
                 self._zoom = current_min_zoom
            if not self._player_pos:
                self._clamp_pan() 
        else:
            pass
        self.update()

    def _get_image_rect(self):
        if not self._processed_image or self._processed_image.isNull():
            return QRectF()
        img_width_zoomed = self._processed_image.width() * self._zoom
        img_height_zoomed = self._processed_image.height() * self._zoom
        return QRectF(self._pan[0], self._pan[1], img_width_zoomed, img_height_zoomed)
    def _widget_to_image_coords(self, widget_pos):
        if self._zoom == 0: return QPointF(0,0)
        img_x = (widget_pos.x() - self._pan[0]) / self._zoom
        img_y = (widget_pos.y() - self._pan[1]) / self._zoom
        return QPointF(img_x, img_y)

    def _image_to_widget_coords(self, image_pos):
        if isinstance(image_pos, tuple) or isinstance(image_pos, list):
            widget_x = (image_pos[0] * self._zoom) + self._pan[0]
            widget_y = (image_pos[1] * self._zoom) + self._pan[1]
        else:
            widget_x = (image_pos.x() * self._zoom) + self._pan[0]
            widget_y = (image_pos.y() * self._zoom) + self._pan[1]
        return QPointF(widget_x, widget_y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        if self._crt_pixmap and not self._crt_pixmap.isNull():
            img_rect = self._get_image_rect()
            source_rect = QRectF(0, 0, self._crt_pixmap.width(), self._crt_pixmap.height())
            painter.drawPixmap(img_rect, self._crt_pixmap, source_rect)
            if self._border_color.isValid():
                painter.setPen(QPen(self._border_color, 1))
                painter.drawRect(img_rect)
        else:
            painter.setPen(QColor("#AAAAAA"))
            font = painter.font()
            font.setPointSize(12)
            font.setItalic(True)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, 
                            "Map Not Loaded" if not self.text() else self.text())
        if self._processed_image is not None and not self._processed_image.isNull():
            num_lines = int(self.height() / 2)
            painter.setPen(QColor(0, 0, 0, 20))
            for i in range(num_lines):
                y = i * 2 + (int(self._pulse_time * 5) % 2)
                painter.drawLine(0, y, self.width(), y)
        border_pen = QPen(self._border_color, 1)
        painter.setPen(border_pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def set_player_position(self, pos_img, setting_name=None, should_center=False):
        self._player_pos = pos_img
        self._player_setting_name = setting_name
        if should_center:
            QTimer.singleShot(100, self._center_on_player)
            QTimer.singleShot(300, self._center_on_player)
            QTimer.singleShot(600, self._center_on_player)
        self.update()
        
    def _center_on_player(self):
        if self._player_pos is None or self._original_image is None:
            return
        if self.width() <= 0 or self.height() <= 0:
            return
        try:
            self._zoom_level = 1
            self._zoom = math.pow(self._zoom_step_factor, self._zoom_level) * self._zoom_baseline_multiplier
            player_x = self._player_pos[0]
            player_y = self._player_pos[1]
            widget_center_x = self.width() / 2
            widget_center_y = self.height() / 2
            self._pan[0] = widget_center_x - (player_x * self._zoom)
            self._pan[1] = widget_center_y - (player_y * self._zoom)
            self.update()
        except Exception as e:
            pass

    def clear_player_position(self):
        self._player_pos = None
        self._player_setting_name = None
        self.update()

def create_world_map(parent=None, theme_settings=None):
    container = QWidget(parent)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0,0,0,0)
    map_display = WorldMapDisplay("Initializing Map...", parent_editor=None, map_type="world_map_mini")
    if theme_settings:
        base_color = theme_settings.get("base_color", "#CCCCCC")
        map_display.setBorderColor(base_color)
        map_display.set_tint_color(base_color)
    layout.addWidget(map_display)
    container.map_display = map_display
    return container

def load_map_from_file(map_widget, map_file_path):
    if not map_widget:
        return False
    if not hasattr(map_widget, 'map_display'):
        return False
    if not os.path.exists(map_file_path):
        map_widget.map_display.setPixmap(QPixmap(), orig_image=None)
        return False
    try:
        image = QImage(map_file_path)
        if image.isNull():
            map_widget.map_display.setPixmap(QPixmap(), orig_image=None)
            return False
        map_widget.map_display.setPixmap(QPixmap.fromImage(image), orig_image=image)
        return True
    except Exception as e:
        map_widget.map_display.setPixmap(QPixmap(), orig_image=None)
        return False

def set_map_image_from_qimage(map_widget, qimage, preserve_view_state=False):
    if not map_widget or not hasattr(map_widget, 'map_display'):
        return False
    if qimage is None or qimage.isNull():
        return map_widget.map_display.setPixmap(QPixmap(), orig_image=None, preserve_view_state=preserve_view_state)
    return map_widget.map_display.setPixmap(QPixmap.fromImage(qimage), orig_image=qimage, preserve_view_state=preserve_view_state)

def update_map_theme(map_widget, theme_settings):
    if not map_widget or not hasattr(map_widget, 'map_display'):
        return
    map_display = map_widget.map_display
    base_color = theme_settings.get('base_color', '#CCCCCC')
    border_color = theme_settings.get('accent_color', '#CCCCCC')
    map_display.setBorderColor(border_color)
    map_display.set_tint_color(base_color)

def update_player_position(map_widget, workflow_data_dir, should_center=False):
    if not map_widget:
        return
    map_display = None
    if isinstance(map_widget, WorldMapDisplay):
        map_display = map_widget
    elif hasattr(map_widget, 'map_display'):
        map_display = map_widget.map_display
    else:
        return
    if not workflow_data_dir or not os.path.exists(workflow_data_dir):
        return
    try:
        from core.utils import _get_player_current_setting_name
        import json
        current_setting = _get_player_current_setting_name(workflow_data_dir)
        if not current_setting or current_setting == "Unknown Setting":
            map_display.clear_player_position()
            return
        setting_file_path = None
        settings_dirs = [
            os.path.join(workflow_data_dir, 'game', 'settings'),
            os.path.join(workflow_data_dir, 'resources', 'data files', 'settings')
        ]
        for settings_dir in settings_dirs:
            if not os.path.exists(settings_dir):
                continue
            for root, dirs, files in os.walk(settings_dir):
                for file in files:
                    if file.endswith('_setting.json'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                setting_data = json.load(f)
                            if setting_data.get('name') == current_setting:
                                setting_file_path = file_path
                                break
                        except Exception as e:
                            continue
                if setting_file_path:
                    break
            if setting_file_path:
                break
        if not setting_file_path:
            map_display.clear_player_position()
            return
        
        try:
            with open(setting_file_path, 'r', encoding='utf-8') as f:
                setting_data = json.load(f)
            
            pos_x = setting_data.get('x')
            pos_y = setting_data.get('y')
            
            if pos_x is not None and pos_y is not None:
                map_display.set_player_position((float(pos_x), float(pos_y)), current_setting, should_center=should_center)
                return
        except Exception as e:
            pass
        
        map_display.clear_player_position()
    except Exception as e:
        map_display.clear_player_position()