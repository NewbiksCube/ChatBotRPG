import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QSlider, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QImage, QPolygonF, QPainterPath, QTransform
from PyQt5.QtCore import Qt, QPoint, QPointF, QRectF, QSizeF, QLineF

class MapCanvas(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.base_image = QImage(image_path)
        if self.base_image.isNull():
            print(f"Error: Could not load image at {image_path}")
            self.base_image = QImage(800, 600, QImage.Format_RGB32)
            self.base_image.fill(Qt.darkGray)
        
        self.pixmap = QPixmap.fromImage(self.base_image)
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self.last_mouse_pos = None
        self.pan_click_start_pos = None
        self.is_panning = False
        self.mode = 'pan' 

        self.zones = [] 
        self.current_path_points = [] # Centerline points for the current stroke
        self.is_drawing_zone = False
        self.selected_zone_index = None 
        self.vertex_distance_threshold = 5  
        self.brush_width = 40  

        self.setMinimumSize(600, 400)

    def set_brush_width(self, width):
        self.brush_width = max(5, int(width)) # Ensure minimum brush width
        self.update() # In case we add a brush cursor preview later

    def _create_octagon_poly(self, center_point, radius, num_vertices=8):
        polygon = QPolygonF()
        angle_step = 2 * math.pi / num_vertices
        start_angle_offset = 0 
        for i in range(num_vertices):
            angle = i * angle_step + start_angle_offset
            x = center_point.x() + radius * math.cos(angle)
            y = center_point.y() + radius * math.sin(angle)
            polygon.append(QPointF(x, y))
        return polygon

    def _generate_preview_stamps(self): # Generates list of individual octagon QPainterPaths for preview
        if not self.current_path_points:
            return []

        stamps = []
        brush_radius = self.brush_width / 2.0
        if brush_radius < 0.1: # Avoid issues with tiny or zero radius
            return []

        first_octagon_poly = self._create_octagon_poly(self.current_path_points[0], brush_radius)
        first_stamp_path = QPainterPath()
        first_stamp_path.addPolygon(first_octagon_poly)
        stamps.append(first_stamp_path)

        if len(self.current_path_points) == 1:
            return stamps # Only the first stamp if it's a single point so far

        for i in range(1, len(self.current_path_points)):
            p1 = self.current_path_points[i-1]
            p2 = self.current_path_points[i]
            segment_line = QLineF(p1, p2)
            segment_length = segment_line.length()

            num_stamps_for_segment = 1 
            # Ensure we stamp densely enough relative to brush size, but not excessively
            stamp_interval = brush_radius / 2.0 
            if stamp_interval > 0.01: # Avoid division by zero or extreme stamping
                num_stamps_for_segment = max(1, int(segment_length / stamp_interval))

            for j in range(1, num_stamps_for_segment + 1):
                alpha = float(j) / num_stamps_for_segment
                interpolated_x = p1.x() * (1.0 - alpha) + p2.x() * alpha
                interpolated_y = p1.y() * (1.0 - alpha) + p2.y() * alpha
                stamp_center = QPointF(interpolated_x, interpolated_y)
                
                octagon_poly_stamp = self._create_octagon_poly(stamp_center, brush_radius)
                stamp_path_segment = QPainterPath()
                stamp_path_segment.addPolygon(octagon_poly_stamp)
                stamps.append(stamp_path_segment)
        return stamps
    
    def _create_united_path_from_stamps(self, stamp_paths): # Unites a list of QPainterPath stamps
        if not stamp_paths:
            return QPainterPath()
        
        united_path = QPainterPath(stamp_paths[0]) # Start with the first stamp
        united_path.setFillRule(Qt.WindingFill)

        for i in range(1, len(stamp_paths)):
            united_path = united_path.united(stamp_paths[i])
        return united_path

    def _get_image_rect_on_canvas(self):
        scaled_width = self.base_image.width() * self.zoom_factor
        scaled_height = self.base_image.height() * self.zoom_factor
        return QRectF(self.pan_offset, QSizeF(scaled_width, scaled_height))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), Qt.lightGray)

        painter.save()
        painter.translate(self.pan_offset)
        painter.scale(self.zoom_factor, self.zoom_factor)
        if not self.base_image.isNull():
            painter.drawImage(QPointF(0,0), self.base_image, QRectF(self.base_image.rect()))
        painter.restore()

        painter.save()
        painter.translate(self.pan_offset)
        painter.scale(self.zoom_factor, self.zoom_factor)

        for i, zone_path in enumerate(self.zones):
            if not zone_path.isEmpty():
                painter.save() 
                pen_width_img_coords = 1 
                fill_color = QColor(0, 100, 200, 80)
                border_color = fill_color # Default border color is same as fill

                if i == self.selected_zone_index:
                    # Selected zone: border color is same as fill, but thicker pen
                    # border_color = QColor(255, 165, 0, 255) # This was the previous orange highlight
                    border_color = fill_color # Explicitly set to fill_color for selected as per request
                    pen_width_img_coords = 3 
                
                actual_pen_width = max(0.5, pen_width_img_coords / self.zoom_factor)
                current_pen = QPen(border_color, actual_pen_width)
                # Apply round cap/join for potentially thin lines, more noticeable on non-selected
                if i != self.selected_zone_index and pen_width_img_coords <=1:
                     current_pen.setCapStyle(Qt.RoundCap)
                     current_pen.setJoinStyle(Qt.RoundJoin)
                # Or apply to all for consistency if desired, even thicker selected border
                # current_pen.setCapStyle(Qt.RoundCap)
                # current_pen.setJoinStyle(Qt.RoundJoin)

                painter.setPen(current_pen)
                painter.setBrush(QBrush(fill_color))
                painter.drawPath(zone_path) 
                painter.restore() 

        if self.is_drawing_zone and self.current_path_points:
            preview_stamps = self._generate_preview_stamps() # Get list of individual octagon paths
            if preview_stamps:
                painter.save()
                pen_width_img_coords = 2 
                actual_pen_width = max(1.0, pen_width_img_coords / self.zoom_factor)
                # Preview border and fill remain distinct green
                preview_border_color = QColor(0, 255, 0, 200)
                preview_fill_color = QColor(0, 255, 0, 60)
                pen = QPen(preview_border_color, actual_pen_width, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(QBrush(preview_fill_color))
                for stamp_path in preview_stamps:
                    painter.drawPath(stamp_path) # Draw each stamp individually for preview
                painter.restore()
        
        # Draw brush cursor preview if in draw mode
        if self.mode == 'draw':
            current_mouse_canvas_pos = self.mapFromGlobal(self.cursor().pos())
            # Check if mouse is within the canvas widget bounds
            if self.rect().contains(current_mouse_canvas_pos):
                img_coords_at_mouse = self.canvasToImage(current_mouse_canvas_pos)
                brush_radius_img = self.brush_width / 2.0
                if brush_radius_img > 0:
                    cursor_octagon_poly = self._create_octagon_poly(img_coords_at_mouse, brush_radius_img)
                    painter.setPen(QPen(Qt.yellow, max(0.5, 1.0 / self.zoom_factor), Qt.DotLine))
                    painter.setBrush(Qt.NoBrush) # No fill for cursor preview
                    painter.drawPolygon(cursor_octagon_poly) # Draw in image-coordinate space (transformed by painter)
        painter.restore()

    def imageToCanvas(self, image_point):
        return image_point * self.zoom_factor + self.pan_offset

    def canvasToImage(self, canvas_point):
        if self.zoom_factor == 0: return QPointF()
        return (canvas_point - self.pan_offset) / self.zoom_factor

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        if self.mode == 'pan':
            if event.button() == Qt.LeftButton:
                self.pan_click_start_pos = event.pos()
        elif self.mode == 'draw':
            if event.button() == Qt.LeftButton:
                self.is_drawing_zone = True
                self.current_path_points = [] 
                img_coords = self.canvasToImage(self.last_mouse_pos)
                self.current_path_points.append(img_coords)
                self.update() 
            elif event.button() == Qt.RightButton: 
                self.is_drawing_zone = False
                self.current_path_points = []
                self.update()

    def mouseMoveEvent(self, event):
        current_pos = event.pos()
        # Update brush cursor irrespective of mode if mouse is over canvas
        if self.mode == 'draw' and self.rect().contains(current_pos):
            self.update() # Trigger repaint for brush cursor
            
        if self.mode == 'pan' and (event.buttons() & Qt.LeftButton):
            if self.pan_click_start_pos:
                if QLineF(self.pan_click_start_pos, current_pos).length() > QApplication.startDragDistance():
                    self.is_panning = True
                    self.pan_click_start_pos = None 
            
            if self.is_panning:
                delta = current_pos - self.last_mouse_pos
                self.pan_offset += delta
                self.update()

        elif self.mode == 'draw' and self.is_drawing_zone and (event.buttons() & Qt.LeftButton):
            img_coords = self.canvasToImage(current_pos)
            if self.current_path_points: 
                last_path_pt = self.current_path_points[-1]
                if QLineF(last_path_pt, img_coords).length() >= self.vertex_distance_threshold:
                    self.current_path_points.append(img_coords)
                    self.update() 
            else: 
                self.current_path_points.append(img_coords)
                self.update()
        self.last_mouse_pos = current_pos

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.mode == 'pan':
                if self.is_panning:
                    self.is_panning = False
                elif self.pan_click_start_pos: 
                    clicked_img_pos = self.canvasToImage(event.pos())
                    found_selection = False
                    for i in reversed(range(len(self.zones))):
                        zone_path = self.zones[i] 
                        if zone_path.contains(clicked_img_pos):
                            self.selected_zone_index = i
                            found_selection = True
                            break
                    if not found_selection:
                        self.selected_zone_index = None 
                    self.update()
                self.pan_click_start_pos = None 

            elif self.mode == 'draw' and self.is_drawing_zone:
                if self.current_path_points: 
                    stamps_for_final_zone = self._generate_preview_stamps() # Get all stamps for the drawn stroke
                    if stamps_for_final_zone:
                        newly_drawn_united_path = self._create_united_path_from_stamps(stamps_for_final_zone)
                        if not newly_drawn_united_path.isEmpty():
                            if self.selected_zone_index is not None and self.selected_zone_index < len(self.zones):
                                existing_path = self.zones[self.selected_zone_index] 
                                final_united_path = existing_path.united(newly_drawn_united_path)
                                # Simplify path to prevent excessive complexity after many unions
                                self.zones[self.selected_zone_index] = final_united_path.simplified() 
                            else:
                                self.zones.append(newly_drawn_united_path.simplified()) 
                                self.selected_zone_index = len(self.zones) -1 
                            
                self.is_drawing_zone = False 
                self.current_path_points = [] 
                self.update() 

    def wheelEvent(self, event):
        mouse_pos_before_zoom = self.canvasToImage(event.pos())
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_factor *= 1.15
        else:
            self.zoom_factor /= 1.15
        self.zoom_factor = max(0.05, min(self.zoom_factor, 20.0))
        mouse_pos_after_zoom = self.canvasToImage(event.pos())
        pan_adj = (mouse_pos_after_zoom - mouse_pos_before_zoom) * self.zoom_factor
        self.pan_offset += pan_adj
        self.update()

    def clear_all_zones(self):
        self.zones.clear()
        self.current_path_points = [] 
        self.is_drawing_zone = False
        self.selected_zone_index = None 
        self.update()

class ToolBar(QWidget):
    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8,8,8,8)
        layout.setSpacing(8)
        self.setFixedWidth(150) # Increased width for slider

        self.pan_btn = QPushButton("Pan/Select Zone")
        self.draw_btn = QPushButton("Draw/Add Zone")
        self.pan_btn.setCheckable(True)
        self.draw_btn.setCheckable(True)
        self.pan_btn.setChecked(True)

        self.brush_label = QLabel("Brush Width (px):")
        self.brush_slider = QSlider(Qt.Horizontal)
        self.brush_slider.setMinimum(10) # Min brush width
        self.brush_slider.setMaximum(150) # Max brush width
        self.brush_slider.setValue(self.canvas.brush_width) # Set initial value
        self.brush_slider.setTickPosition(QSlider.TicksBelow)
        self.brush_slider.setTickInterval(10)
        self.brush_slider.valueChanged.connect(self.canvas.set_brush_width)

        self.clear_all_btn = QPushButton("Clear All Zones")
        self.clear_all_btn.clicked.connect(self.canvas.clear_all_zones)

        layout.addWidget(self.pan_btn)
        layout.addWidget(self.draw_btn)
        layout.addSpacing(10)
        layout.addWidget(self.brush_label)
        layout.addWidget(self.brush_slider)
        layout.addSpacing(10)
        layout.addWidget(self.clear_all_btn)
        layout.addStretch(1)

        self.pan_btn.clicked.connect(self.set_pan_mode)
        self.draw_btn.clicked.connect(self.set_draw_mode)

    def set_pan_mode(self):
        self.canvas.mode = 'pan'
        self.pan_btn.setChecked(True)
        self.draw_btn.setChecked(False)
        if self.canvas.is_drawing_zone:
            self.canvas.is_drawing_zone = False
            self.canvas.current_path_points = []
            self.canvas.update()
        self.canvas.update() # To hide brush cursor if it was visible

    def set_draw_mode(self):
        self.canvas.mode = 'draw'
        self.pan_btn.setChecked(False)
        self.draw_btn.setChecked(True)
        self.canvas.update() # To show brush cursor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zone Editor - Adjustable Brush") 
        self.setGeometry(100, 100, 1000, 700)
        image_file = "worldmap.jpg" 
        self.canvas = MapCanvas(image_file)
        if self.canvas.base_image.isNull() or self.canvas.base_image.width() < 2:
            self.statusBar().showMessage(f"Failed to load '{image_file}'. Check file.", 10000)

        toolbar = ToolBar(self.canvas)
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5,5,5,5)
        main_layout.setSpacing(0)
        main_layout.addWidget(toolbar)
        main_layout.addWidget(self.canvas, 1) 
        self.setCentralWidget(central_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
