from PyQt5.QtWidgets import QLabel, QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPainter, QPixmap, QImage, QColor, QPen, QBrush, QPainterPath, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
from editor_panel.world_editor.region_toolbar import _render_region_borders
from editor_panel.world_editor.world_editor_select import select_item
import math
import numpy as np

def catmull_rom(points, steps=5):
    result = []
    n = len(points)
    if n < 4:
        return points
    for i in range(n - 3):
        p0, p1, p2, p3 = points[i:i+4]
        for t in [j/steps for j in range(steps)]:
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * ((2 * p1[0]) +
                       (-p0[0] + p2[0]) * t +
                       (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) +
                       (-p0[1] + p2[1]) * t +
                       (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
            result.append((x, y))
    return result

def mousePressEvent(self, event):
    event_handled = False
    if self.parent_editor is None:
        QLabel.mousePressEvent(self, event)
        return
    if not self.hasFocus():
        self.setFocus()
    current_draw_mode = self.parent_editor.get_draw_mode(self.map_type)
    if hasattr(self.parent_editor, '_path_details_mode') and self.parent_editor._path_details_mode.get(self.map_type, False):
        if event.button() == Qt.RightButton:
            if self.parent_editor._path_assign_mode.get(self.map_type, False):
                widgets = self.parent_editor._path_details_widgets.get(self.map_type, {})
                if widgets.get('assign_btn') and widgets['assign_btn'].isChecked():
                    widgets['assign_btn'].setChecked(False)
                    self.parent_editor._set_path_assign_mode(self.map_type, False)
                    self.update()
                    return
            return
        item_type, item_index = self._find_item_at_pos(event.pos())
        is_in_assign_mode = self.parent_editor._path_assign_mode.get(self.map_type, False)
        if is_in_assign_mode and item_type == 'line':
            if hasattr(self.parent_editor, 'on_path_clicked_for_details'):
                self.parent_editor.on_path_clicked_for_details(self.map_type, item_index)
            return
        if item_type == 'line':
            self.parent_editor._selected_path_index[self.map_type] = item_index
            if hasattr(self.parent_editor, 'on_path_clicked_for_details'):
                self.parent_editor.on_path_clicked_for_details(self.map_type, item_index)
            self.update()
            return
        elif not is_in_assign_mode:
            self.parent_editor._selected_path_index[self.map_type] = None
            widgets = self.parent_editor._path_details_widgets.get(self.map_type, {})
            if widgets.get('name_input'):
                widgets['name_input'].setText("")
                widgets['name_input'].setEnabled(False)
            if widgets.get('desc_input'):
                widgets['desc_input'].setPlainText("")
                widgets['desc_input'].setEnabled(False)
            self.update()
    if event.button() == Qt.RightButton:
        if current_draw_mode == 'feature_paint':
            feature_sub_mode = 'paint'
            toolbar_ref = None
            if self.map_type == 'world':
                feature_sub_mode = getattr(self.parent_editor, '_world_feature_sub_mode', 'paint')
                toolbar_ref = getattr(self.parent_editor, 'world_features_toolbar', None)
            elif self.map_type == 'location':
                feature_sub_mode = getattr(self.parent_editor, '_location_feature_sub_mode', 'paint')
                toolbar_ref = getattr(self.parent_editor, 'location_features_toolbar', None)
            if feature_sub_mode == 'paint':
                if self.map_type == 'world':
                    self.parent_editor._on_world_feature_select_submode()
                elif self.map_type == 'location':
                    self.parent_editor._on_location_feature_select_submode()
                event.accept()
                return
            elif feature_sub_mode == 'select':
                if toolbar_ref and hasattr(toolbar_ref, 'feature_paint_btn') and not toolbar_ref.feature_paint_btn.isChecked():
                    if self.map_type == 'world':
                        self.parent_editor._on_world_feature_paint_submode()
                    elif self.map_type == 'location':
                        self.parent_editor._on_location_feature_paint_submode()
                event.accept()
                return
        if current_draw_mode == 'region_edit' and self.map_type == 'world':
            world_region_sub_mode = getattr(self.parent_editor, '_world_region_sub_mode', 'paint')
            if world_region_sub_mode == 'paint':
                widget_pos = event.pos()
                image_coords = self._widget_to_image_coords(widget_pos)
                if image_coords:
                    if self._crt_image is None:
                        self._expand_virtual_canvas(image_coords[0], image_coords[1])
                    if hasattr(self.parent_editor, '_last_painted_position'):
                        self.parent_editor._last_painted_position = None
                    if hasattr(self.parent_editor, '_previous_ema_point'):
                        self.parent_editor._previous_ema_point = None
                    self._region_erase_stroke_points = [image_coords]
                    self._region_erase_affected_regions = set()
                    current_region_name = getattr(self.parent_editor, '_current_region_name', None)
                    if current_region_name and hasattr(self.parent_editor, 'paint_region_stroke'):
                        self.parent_editor.paint_region_stroke(
                            current_region_name,
                            [image_coords],
                            getattr(self.parent_editor, '_region_brush_size', 5),
                            erase_mode=True
                        )
                    self.update()
                    event.accept()
                    return
        if current_draw_mode != 'none':
            print(f"Right-click cancelling {self.map_type} draw mode: {current_draw_mode}")
            self.parent_editor.cancel_draw_mode(self.map_type)
            event.accept()
            return
        else:
            QLabel.mousePressEvent(self, event)
            return

    if event.button() == Qt.LeftButton:
        feature_sub_mode = None
        world_region_sub_mode = None
        if self.map_type == 'world':
            if current_draw_mode == 'feature_paint':
                feature_sub_mode = getattr(self.parent_editor, '_world_feature_sub_mode', 'paint')
            elif current_draw_mode == 'region_edit':
                world_region_sub_mode = getattr(self.parent_editor, '_world_region_sub_mode', 'paint')
        elif self.map_type == 'location':
            if current_draw_mode == 'feature_paint':
                feature_sub_mode = getattr(self.parent_editor, '_location_feature_sub_mode', 'paint')
        if current_draw_mode == 'feature_paint' and feature_sub_mode == 'paint':
            widget_pos = event.pos()
            image_coords = self._widget_to_image_coords(widget_pos)
            if image_coords:
                self._feature_paint_stroke = [image_coords]
                self._feature_paint_preview_pos = image_coords
                self.update()
                event.accept()
                return

        elif current_draw_mode == 'region_edit' and self.map_type == 'world' and world_region_sub_mode == 'paint':
            widget_pos = event.pos()
            image_coords = self._widget_to_image_coords(widget_pos)
            if image_coords:
                if self._crt_image is None:
                    self._expand_virtual_canvas(image_coords[0], image_coords[1])
                if hasattr(self.parent_editor, '_last_painted_position'):
                    self.parent_editor._last_painted_position = None
                if hasattr(self.parent_editor, '_previous_ema_point'):
                    self.parent_editor._previous_ema_point = None
                self._region_paint_stroke_points = [image_coords]
                self._region_paint_affected_regions = set()
                self._is_actively_painting = True
                self.update()
                event.accept()
                event_handled = True
            else:
                self._dragging = True
                self._dragging_selection = False
                self._last_mouse_pos = event.pos()
                self.setCursor(Qt.ClosedHandCursor)
                event.accept()
                event_handled = True
            if event_handled:
                return

        elif current_draw_mode == 'dot':
            widget_pos = event.pos()
            image_coords = self._widget_to_image_coords(widget_pos)
            if image_coords:
                if self._crt_image is None:
                    self._expand_virtual_canvas(image_coords[0], image_coords[1])
                if self.map_type == 'world':
                    self.parent_editor.add_world_dot(image_coords)
                elif self.map_type == 'location':
                    self.parent_editor.add_location_dot(image_coords)
                print(f"Plotted {self.map_type} dot -> {'virtual' if self._crt_image is None else 'image'}:{image_coords}")
            else:
                print("Dot plot ignored: Click outside content area.")
            event.accept()
            return

        elif current_draw_mode == 'line':
            item_type, item_index = self._find_item_at_pos(event.pos())
            if item_type == 'dot':
                dots_data_list = self.parent_editor.get_world_draw_data()[1] if self.map_type == 'world' else self.parent_editor.get_location_draw_data()[1]
                if 0 <= item_index < len(dots_data_list):
                    start_dot_data = dots_data_list[item_index]
                    p_img_x, p_img_y, *_ = start_dot_data
                    p_widget = self._image_to_widget_coords((p_img_x, p_img_y))
                    if not p_widget:
                        print(f"Error: Could not convert start dot position to widget coordinates.")
                        event.accept()
                        return
                    self._is_linking_dots = True
                    self._link_start_dot_index = item_index
                    self._link_start_dot_img_pos = (p_img_x, p_img_y)
                    self._link_start_dot_widget_pos = p_widget
                    self._link_preview_end_widget_pos = QPointF(p_widget)
                    self._link_path_widget = [p_widget]
                    self._link_path_image = [(p_img_x, p_img_y)]
                    self._link_visited_dot_indices = [item_index]
                    self._link_visited_dot_positions = [(p_img_x, p_img_y)]
                    self.setCursor(Qt.CrossCursor)
                    self._dragging = False
                    self.update()
                else:
                    print(f"Error: Invalid dot index {item_index}")
            else:
                print(f"Line drawing ignored: Must click on a dot to start linking.")
            event.accept()
            return
        is_selection_or_pan_mode = False
        if current_draw_mode in ['none', 'dot', 'line']:
            is_selection_or_pan_mode = True
        elif current_draw_mode == 'feature_paint' and feature_sub_mode == 'select':
            is_selection_or_pan_mode = True
        elif current_draw_mode == 'region_edit' and self.map_type == 'world' and world_region_sub_mode == 'select':
            is_selection_or_pan_mode = True
        if is_selection_or_pan_mode:
            item_type, item_index_or_name = self._find_item_at_pos(event.pos())
            if item_type is not None:
                select_item(self.parent_editor, self.map_type, item_type, item_index_or_name)
                if item_type == 'dot':
                    dots_list = self.parent_editor.get_world_draw_data()[1] if self.map_type == 'world' else self.parent_editor.get_location_draw_data()[1]
                    lines = self.parent_editor.get_world_draw_data()[0] if self.map_type == 'world' else self.parent_editor.get_location_draw_data()[0]
                    has_connected_paths = False
                    if 0 <= item_index_or_name < len(dots_list):
                        dot_pos = (dots_list[item_index_or_name][0], dots_list[item_index_or_name][1])
                        dot_hit_tolerance = 12.0
                        for line in lines:
                            if len(line) >= 2:
                                path_points = line[0]
                                if len(path_points) >= 2:
                                    start_point = path_points[0]
                                    end_point = path_points[-1]
                                    start_dist = ((start_point[0] - dot_pos[0])**2 + (start_point[1] - dot_pos[1])**2)**0.5
                                    end_dist = ((end_point[0] - dot_pos[0])**2 + (end_point[1] - dot_pos[1])**2)**0.5
                                    if start_dist <= dot_hit_tolerance or end_dist <= dot_hit_tolerance:
                                        has_connected_paths = True
                                        break
                    if not has_connected_paths:
                        self._dragging_selection = True
                        self._dragging = True
                        self._drag_start_widget_pos = event.pos()
                        self._last_mouse_pos = event.pos()
                        dots_list = self.parent_editor.get_world_draw_data()[1] if self.map_type == 'world' else self.parent_editor.get_location_draw_data()[1]
                        if 0 <= item_index_or_name < len(dots_list):
                            dot_data = dots_list[item_index_or_name]
                            self._selected_item_start_img_pos = (dot_data[0], dot_data[1])
                    else:
                        self._dragging_selection = False
                        can_pan = False
                        if self._crt_image is not None and self._zoom_level >= 0:
                            img_rect_base = self._get_image_rect()
                            if img_rect_base.width() > 0:
                                user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                                draw_w = img_rect_base.width() * user_zoom_factor
                                draw_h = img_rect_base.height() * user_zoom_factor
                                center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + self._pan[0]
                                center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + self._pan[1]
                                x_top_left = center_x - draw_w / 2.0
                                y_top_left = center_y - draw_h / 2.0
                                if QRectF(x_top_left, y_top_left, draw_w, draw_h).contains(event.pos()):
                                    can_pan = True
                        elif self._crt_image is None:
                            can_pan = True
                        if can_pan:
                            self._dragging = True
                            self._dragging_selection = False
                            self._last_mouse_pos = event.pos()
                            self.setCursor(Qt.ClosedHandCursor)
                            event.accept()
                            event_handled = True
                elif item_type == 'line':
                    self._dragging_selection = False
                    can_pan = False
                    if self._crt_image is not None and self._zoom_level >= 0:
                        img_rect_base = self._get_image_rect()
                        if img_rect_base.width() > 0:
                            user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                            draw_w = img_rect_base.width() * user_zoom_factor
                            draw_h = img_rect_base.height() * user_zoom_factor
                            center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + self._pan[0]
                            center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + self._pan[1]
                            x_top_left = center_x - draw_w / 2.0
                            y_top_left = center_y - draw_h / 2.0
                            if QRectF(x_top_left, y_top_left, draw_w, draw_h).contains(event.pos()):
                                can_pan = True
                    elif self._crt_image is None:
                        can_pan = True
                    if can_pan:
                        self._dragging = True
                        self._dragging_selection = False
                        self._last_mouse_pos = event.pos()
                        self.setCursor(Qt.ClosedHandCursor)
                        event.accept()
                        event_handled = True
                elif item_type == 'region':
                    self._dragging_selection = False
                    if hasattr(self.parent_editor, '_select_region_for_painting'):
                        self.parent_editor._select_region_for_painting(item_index_or_name)
                    can_pan = False
                    if self._crt_image is not None and self._zoom_level >= 0:
                        img_rect_base = self._get_image_rect()
                        if img_rect_base.width() > 0:
                            user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                            draw_w = img_rect_base.width() * user_zoom_factor
                            draw_h = img_rect_base.height() * user_zoom_factor
                            center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + self._pan[0]
                            center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + self._pan[1]
                            x_top_left = center_x - draw_w / 2.0
                            y_top_left = center_y - draw_h / 2.0
                            if QRectF(x_top_left, y_top_left, draw_w, draw_h).contains(event.pos()):
                                can_pan = True
                    elif self._crt_image is None:
                        can_pan = True
                    if can_pan:
                        self._dragging = True
                        self._dragging_selection = False
                        self._last_mouse_pos = event.pos()
                        self.setCursor(Qt.ClosedHandCursor)
                        event.accept()
                        event_handled = True
                if event_handled:
                    return
            else:
                can_pan = False
                if self._crt_image is not None and self._zoom_level >= 0:
                    img_rect_base = self._get_image_rect()
                    if img_rect_base.width() > 0:
                        user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                        draw_w = img_rect_base.width() * user_zoom_factor
                        draw_h = img_rect_base.height() * user_zoom_factor
                        center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + self._pan[0]
                        center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + self._pan[1]
                        x_top_left = center_x - draw_w / 2.0
                        y_top_left = center_y - draw_h / 2.0
                        if QRectF(x_top_left, y_top_left, draw_w, draw_h).contains(event.pos()):
                            can_pan = True
                elif self._crt_image is None:
                    can_pan = True
                if can_pan:
                    self._dragging = True
                    self._dragging_selection = False
                    self._last_mouse_pos = event.pos()
                    self.setCursor(Qt.ClosedHandCursor)
                    event.accept()
                    event_handled = True
                else:
                    self.parent_editor.clear_selection(self.map_type)
                    self.update()
                if event_handled:
                    return
    if not event.isAccepted():
        QLabel.mousePressEvent(self, event)

def mouseMoveEvent(self, event):
    if self.parent_editor is None:
        QLabel.mouseMoveEvent(self, event)
        return
    is_dragging = event.buttons() == Qt.LeftButton and getattr(self, '_dragging', False)
    item_type_hover, item_index_hover = self._find_item_at_pos(event.pos())
    new_hovered_line_index = -1
    new_hovered_dot_index = -1
    if item_type_hover == 'line':
        new_hovered_line_index = item_index_hover
    elif item_type_hover == 'dot':
        new_hovered_dot_index = item_index_hover
    if hasattr(self, '_hovered_line_index'):
        if self._hovered_line_index != new_hovered_line_index:
            self._hovered_line_index = new_hovered_line_index
            self.update()
    else:
        self._hovered_line_index = new_hovered_line_index
        if new_hovered_line_index != -1:
            self.update()
    if hasattr(self, '_hovered_dot_index'):
        if self._hovered_dot_index != new_hovered_dot_index:
            self._hovered_dot_index = new_hovered_dot_index
            self.update()
    else:
        self._hovered_dot_index = new_hovered_dot_index
        if new_hovered_dot_index != -1:
            self.update()

    if getattr(self, '_is_linking_dots', False):
        image_coords = self._widget_to_image_coords(event.pos())
        if image_coords:
            current_widget_pos = event.pos()
            path_mode = 'draw'
            if self.parent_editor and hasattr(self.parent_editor, 'get_path_mode'):
                path_mode = self.parent_editor.get_path_mode(self.map_type)
            self._link_preview_end_widget_pos = current_widget_pos
            if path_mode == 'draw':
                current_image_point = image_coords
                if not self._link_path_image:
                    self._link_path_widget.append(current_widget_pos)
                    self._link_path_image.append(current_image_point)
                elif current_image_point != self._link_path_image[-1]:
                    self._link_path_widget.append(current_widget_pos)
                    self._link_path_image.append(current_image_point)
            elif path_mode == 'line':
                if len(self._link_path_widget) == 1:
                    self._link_path_widget.append(current_widget_pos)
                    self._link_path_image.append(image_coords)
                elif len(self._link_path_widget) > 1:
                    self._link_path_widget[-1] = current_widget_pos
                    self._link_path_image[-1] = image_coords
    if hasattr(self.parent_editor, '_path_details_mode') and \
       self.parent_editor._path_details_mode.get(self.map_type, False) and \
       not self.parent_editor._path_assign_mode.get(self.map_type, False) and \
       item_type_hover == 'line':
        if hasattr(self.parent_editor, 'on_path_hover_for_details'):
            self.parent_editor.on_path_hover_for_details(self.map_type, item_index_hover)
    current_draw_mode = getattr(self.parent_editor, f"_{self.map_type}_draw_mode", 'none')
    feature_sub_mode = None
    world_region_sub_mode = None
    if self.map_type == 'world':
        if current_draw_mode == 'feature_paint':
            feature_sub_mode = getattr(self.parent_editor, '_world_feature_sub_mode', 'paint')
        elif current_draw_mode == 'region_edit':
            world_region_sub_mode = getattr(self.parent_editor, '_world_region_sub_mode', 'paint')
    elif self.map_type == 'location':
        if current_draw_mode == 'feature_paint':
            feature_sub_mode = getattr(self.parent_editor, '_location_feature_sub_mode', 'paint')
    if event.buttons() == Qt.LeftButton:
        if current_draw_mode == 'feature_paint' and feature_sub_mode == 'paint':
            image_coords = self._widget_to_image_coords(event.pos())
            if image_coords:
                if not hasattr(self, '_feature_paint_stroke') or self._feature_paint_stroke is None:
                    self._feature_paint_stroke = []
                self._feature_paint_stroke.append(image_coords)
                self._feature_paint_preview_pos = image_coords
            self.update()
            return
        elif current_draw_mode == 'region_edit' and self.map_type == 'world' and \
                world_region_sub_mode == 'paint' and \
                hasattr(self, '_region_paint_stroke_points') and self._region_paint_stroke_points:
            image_coords = self._widget_to_image_coords(event.pos())
            if image_coords:
                self._region_paint_stroke_points.append(image_coords)
                if hasattr(self.parent_editor, '_last_painted_position'):
                    self.parent_editor._last_painted_position = image_coords
            self.update()
            return
    elif event.buttons() == Qt.RightButton:
        if current_draw_mode == 'region_edit' and self.map_type == 'world' and \
                world_region_sub_mode == 'paint' and \
                hasattr(self, '_region_erase_stroke_points') and self._region_erase_stroke_points:
            image_coords = self._widget_to_image_coords(event.pos())
            if image_coords:
                self._region_erase_stroke_points.append(image_coords)
                current_region_name = getattr(self.parent_editor, '_current_region_name', None)
                if current_region_name and hasattr(self.parent_editor, 'paint_region_stroke'):
                    self.parent_editor.paint_region_stroke(
                        current_region_name,
                        [image_coords],
                        getattr(self.parent_editor, '_region_brush_size', 5),
                        erase_mode=True
                    )
            self.update()
            return
    elif getattr(self, '_is_linking_dots', False):
        image_coords = self._widget_to_image_coords(event.pos())
        if image_coords:
            current_widget_pos = event.pos()
            path_mode = 'draw'
            if self.parent_editor and hasattr(self.parent_editor, 'get_path_mode'):
                path_mode = self.parent_editor.get_path_mode(self.map_type)
            self._link_preview_end_widget_pos = current_widget_pos
            if path_mode == 'draw':
                current_image_point = image_coords
                if not self._link_path_image:
                    self._link_path_widget.append(current_widget_pos)
                    self._link_path_image.append(current_image_point)
                elif current_image_point != self._link_path_image[-1]:
                    self._link_path_widget.append(current_widget_pos)
                    self._link_path_image.append(current_image_point)
            elif path_mode == 'line':
                 if len(self._link_path_widget) == 1:
                     self._link_path_widget.append(current_widget_pos)
                     self._link_path_image.append(image_coords)
                 elif len(self._link_path_widget) > 1:
                     self._link_path_widget[-1] = current_widget_pos
                     self._link_path_image[-1] = image_coords
            dots_list = self.parent_editor.get_world_draw_data()[1] if self.map_type == 'world' else self.parent_editor.get_location_draw_data()[1]
            min_dist_sq_link = float('inf')
            closest_dot_idx_link = -1
            for i, (dot_x, dot_y, *_) in enumerate(dots_list):
                if i == self._link_start_dot_index:
                    continue
                if i in self._link_visited_dot_indices and len(self._link_visited_dot_indices) > 1 and i != self._link_visited_dot_indices[-1]:
                    is_multi_segment_path = any(
                        meta.get('start') == self._link_visited_dot_indices[j] and meta.get('end') == self._link_visited_dot_indices[j + 1]
                        for j in range(len(self._link_visited_dot_indices) - 1)
                        for _, meta in (self.parent_editor.get_world_draw_data()[0] if self.map_type == 'world' else self.parent_editor.get_location_draw_data()[0])
                        if isinstance(meta, dict)
                    )
                    if not is_multi_segment_path and len(self._link_visited_dot_indices) > 2:
                        pass
                dist_sq = (dot_x - image_coords[0]) ** 2 + (dot_y - image_coords[1]) ** 2
                if dist_sq < min_dist_sq_link:
                    min_dist_sq_link = dist_sq
                    closest_dot_idx_link = i
            snap_threshold_sq = 100
            current_hovered_dot = -1
            if min_dist_sq_link < snap_threshold_sq and closest_dot_idx_link != -1:
                current_hovered_dot = closest_dot_idx_link
            if self._hovered_dot_index != current_hovered_dot:
                self._hovered_dot_index = current_hovered_dot
        self.update()
    can_drag_item = False
    if current_draw_mode in ['none', 'dot', 'line'] or \
       (current_draw_mode == 'feature_paint' and feature_sub_mode == 'select') or \
       (current_draw_mode == 'region_edit' and world_region_sub_mode == 'select'):
        can_drag_item = True
    if can_drag_item and event.buttons() == Qt.LeftButton and \
            getattr(self, '_dragging', False) and getattr(self, '_dragging_selection', False) and getattr(self, '_last_mouse_pos', None):
        selected_type, selected_index = self.parent_editor.get_selected_item(self.map_type)
        if selected_type == 'dot':
            delta_widget_x = event.pos().x() - self._last_mouse_pos.x()
            delta_widget_y = event.pos().y() - self._last_mouse_pos.y()
            if delta_widget_x != 0 or delta_widget_y != 0:
                image_pos = self._widget_to_image_coords(event.pos())
                if image_pos:
                    if self.map_type == 'world':
                        self.parent_editor.update_world_dot_position(selected_index, image_pos)
                    else:
                        self.parent_editor.update_location_dot_position(selected_index, image_pos)
            self._last_mouse_pos = event.pos()
            self.update()
            return
    if current_draw_mode == 'feature_paint' and event.buttons() == Qt.RightButton:
        image_coords_erase = self._widget_to_image_coords(event.pos())
        if image_coords_erase and hasattr(self.parent_editor, 'erase_feature_at'):
            erase_radius = getattr(self.parent_editor, f"_{self.map_type}_feature_brush_size", 10)
            self.parent_editor.erase_feature_at(self.map_type, image_coords_erase, erase_radius)
        return
    if getattr(self, '_last_mouse_pos', None) != event.pos():
        self._last_mouse_pos = event.pos()
    if not event.isAccepted():
        QLabel.mouseMoveEvent(self, event)

def mouseReleaseEvent(self, event):
    if self.parent_editor is None:
        QLabel.mouseReleaseEvent(self, event)
        return

    current_draw_mode = self.parent_editor.get_draw_mode(self.map_type)
    event_handled = False
    feature_sub_mode = None
    world_region_sub_mode = None
    if self.map_type == 'world':
        if current_draw_mode == 'feature_paint':
            feature_sub_mode = getattr(self.parent_editor, '_world_feature_sub_mode', 'paint')
        elif current_draw_mode == 'region_edit':
            world_region_sub_mode = getattr(self.parent_editor, '_world_region_sub_mode', 'paint')
    elif self.map_type == 'location':
        if current_draw_mode == 'feature_paint':
            feature_sub_mode = getattr(self.parent_editor, '_location_feature_sub_mode', 'paint')

    if event.button() == Qt.LeftButton:
        if current_draw_mode == 'feature_paint' and feature_sub_mode == 'paint':
            if hasattr(self, '_feature_paint_stroke') and self._feature_paint_stroke:
                if hasattr(self.parent_editor, 'paint_feature_at'):
                    self.parent_editor.paint_feature_at(self.map_type, list(self._feature_paint_stroke))
                self._feature_paint_stroke = []
                self._feature_paint_preview_pos = None
                self.update()
            event_handled = True
        elif current_draw_mode == 'region_edit' and self.map_type == 'world' and world_region_sub_mode == 'paint':
            if hasattr(self, '_region_paint_stroke_points') and self._region_paint_stroke_points:
                current_region_name = getattr(self.parent_editor, '_current_region_name', None)
                if current_region_name and hasattr(self.parent_editor, 'finalize_region_paint_stroke'):
                    self.parent_editor.finalize_region_paint_stroke(
                        self.map_type,
                        current_region_name,
                        list(self._region_paint_stroke_points)
                    )
                self._region_paint_stroke_points = []
                self._is_actively_painting = False
                self.update()
                event_handled = True
            else:
                print(f"[WARN] Could not finalize region paint stroke. Region: {getattr(self.parent_editor, '_current_region_name', None)}, Method Exists: {hasattr(self.parent_editor, 'finalize_region_paint_stroke')}")
        elif current_draw_mode == 'line' and getattr(self, '_is_linking_dots', False):
            final_link_event_pos = event.pos()
            final_image_coords = self._widget_to_image_coords(final_link_event_pos)
            end_dot_index = -1
            if self._hovered_dot_index != -1 and self._hovered_dot_index != self._link_start_dot_index:
                end_dot_index = self._hovered_dot_index
            else:
                item_type_at_release, item_index_at_release = self._find_item_at_pos(final_link_event_pos)
                if item_type_at_release == 'dot' and item_index_at_release != self._link_start_dot_index:
                    end_dot_index = item_index_at_release
            actual_end_image_coords = final_image_coords
            if end_dot_index != -1:
                dots_data_list = self.parent_editor.get_world_draw_data()[1] if self.map_type == 'world' else self.parent_editor.get_location_draw_data()[1]
                if 0 <= end_dot_index < len(dots_data_list):
                    actual_end_image_coords = (dots_data_list[end_dot_index][0], dots_data_list[end_dot_index][1])

            if self._link_start_dot_index != -1 and end_dot_index != -1 and self._link_start_dot_index != end_dot_index:
                path_sub_mode = 'draw'
                if self.parent_editor and hasattr(self.parent_editor, 'get_path_mode'):
                    path_sub_mode = self.parent_editor.get_path_mode(self.map_type)
                path_to_add = []
                if path_sub_mode == 'line':
                    path_to_add = [self._link_start_dot_img_pos, actual_end_image_coords]
                else:
                    if len(self._link_path_image) > 1:
                        if len(self._link_path_image) >= 4:
                            path_smoothness = 5
                            if self.parent_editor and hasattr(self.parent_editor, 'get_path_smoothness'):
                                smoothness_percent = self.parent_editor.get_path_smoothness(self.map_type)
                                path_smoothness = max(1, int(smoothness_percent / 10))
                            smooth_points = catmull_rom(self._link_path_image, steps=path_smoothness)
                            path_to_add = smooth_points
                        else:
                            path_to_add = list(self._link_path_image)
                        if actual_end_image_coords and path_to_add:
                            path_to_add[-1] = actual_end_image_coords
                        if path_to_add:
                            path_to_add[0] = self._link_start_dot_img_pos
                    elif self._link_start_dot_img_pos and actual_end_image_coords:
                        path_to_add = [self._link_start_dot_img_pos, actual_end_image_coords]
                if path_to_add:
                    if self.map_type == 'world':
                        dots_list = self.parent_editor._world_dots
                    else:
                        dots_list = self.parent_editor._location_dots
                    current_start_index = self.parent_editor._find_dot_index_by_pos(dots_list, self._link_start_dot_img_pos)
                    current_end_index = self.parent_editor._find_dot_index_by_pos(dots_list, actual_end_image_coords)
                    if current_start_index is not None and current_end_index is not None:
                        if self.map_type == 'world':
                            self.parent_editor.add_world_line(current_start_index, current_end_index, path_to_add)
                        elif self.map_type == 'location':
                            self.parent_editor.add_location_line(current_start_index, current_end_index, path_to_add)
                    else:
                        print(f"Could not find current dot indices. Start pos: {self._link_start_dot_img_pos}, End pos: {actual_end_image_coords}")
                        if self.map_type == 'world':
                            self.parent_editor.add_world_line(self._link_start_dot_index, end_dot_index, path_to_add)
                        elif self.map_type == 'location':
                            self.parent_editor.add_location_line(self._link_start_dot_index, end_dot_index, path_to_add)
                else:
                    print(f"Line linking path_to_add was empty. Start: {self._link_start_dot_index}, End: {end_dot_index}")
            else:
                print(f"Line linking cancelled or invalid: start={self._link_start_dot_index}, end={end_dot_index}, hovered={self._hovered_dot_index}")
            self._is_linking_dots = False
            self._link_start_dot_index = -1
            self._link_start_dot_img_pos = None
            self._link_start_dot_widget_pos = None
            self._link_preview_end_widget_pos = None
            self._link_path_widget = []
            self._link_path_image = []
            self._link_visited_dot_indices = []
            self._link_visited_dot_positions = []
            self._hovered_dot_index = -1
            self.setCursor(Qt.ArrowCursor)
            self.update()
            event_handled = True
        if getattr(self, '_dragging', False):
            self._dragging = False
            if getattr(self, '_dragging_selection', False):
                self._dragging_selection = False
            if self.cursor().shape() == Qt.ClosedHandCursor:
                if current_draw_mode == 'line':
                    self.setCursor(Qt.CrossCursor)
                elif current_draw_mode == 'dot':
                    self.setCursor(Qt.PointingHandCursor)
                else:
                    self.setCursor(Qt.ArrowCursor)
            self.update()
            event_handled = True
        if not event_handled and \
           (current_draw_mode == 'none' or
            (current_draw_mode == 'feature_paint' and feature_sub_mode == 'select') or
            (current_draw_mode == 'region_edit' and self.map_type == 'world' and world_region_sub_mode == 'select')):
            pass

    elif event.button() == Qt.RightButton:
        if current_draw_mode == 'region_edit' and self.map_type == 'world' and world_region_sub_mode == 'paint':
            if hasattr(self, '_region_erase_stroke_points') and self._region_erase_stroke_points:
                current_region_name = getattr(self.parent_editor, '_current_region_name', None)
                brush_size = getattr(self.parent_editor, '_region_brush_size', 5)
                if current_region_name and hasattr(self.parent_editor, 'paint_region_stroke'):
                    self.parent_editor.paint_region_stroke(
                        current_region_name,
                        list(self._region_erase_stroke_points),
                        brush_size,
                        erase_mode=True
                    )
                    if hasattr(self.parent_editor, '_save_world_map_data'):
                        QTimer.singleShot(500, self.parent_editor._save_world_map_data)
                        print(f"Region erase stroke applied to '{current_region_name}'. Scheduled save.")
                elif not current_region_name:
                    print(f"[WARN] Region erase for map '{self.map_type}' skipped: No current region selected for painting/erasing.")
                else:
                    print(f"[ERROR] Region erase for map '{self.map_type}' failed: Parent editor is missing 'paint_region_stroke' method.")
                self._region_erase_stroke_points = []
                self.update()
                event_handled = True
        if current_draw_mode == 'feature_paint' and feature_sub_mode == 'paint':
            if (self.map_type == 'world' and self.parent_editor._world_feature_sub_mode == 'paint') or \
               (self.map_type == 'location' and self.parent_editor._location_feature_sub_mode == 'paint'):
                widget_pos = event.pos()
                image_coords = self._widget_to_image_coords(widget_pos)
                if image_coords and hasattr(self.parent_editor, 'erase_feature_at'):
                    erase_radius = getattr(self.parent_editor, f"_{self.map_type}_feature_brush_size", 10)
                    self.parent_editor.erase_feature_at(self.map_type, image_coords, erase_radius)
                    event_handled = True
                    self.update()
    if event_handled:
        event.accept()
        return
    QLabel.mouseReleaseEvent(self, event)

def paintEvent(self, event):
    radius = 18
    path = QPainterPath()
    path.addRoundedRect(QRectF(self.rect()), radius, radius)
    painter = QPainter(self)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    painter.setClipPath(path)
    self._hovered_line_index = -1
    if not hasattr(self, '_is_scrolling'):
        self._is_scrolling = False
    current_name_field = ""
    if self.parent_editor and hasattr(self.parent_editor, '_get_current_path_name'):
        current_name_field = self.parent_editor._get_current_path_name(self.map_type)
    cursor_pos = self.mapFromGlobal(self.cursor().pos())
    if self.rect().contains(cursor_pos) and not getattr(self, '_is_scrolling', False):
        if not QApplication.mouseButtons():
            item_type, item_index = self._find_item_at_pos(cursor_pos)
            if item_type == 'line':
                self._hovered_line_index = item_index
    
    if self._crt_image is not None:
        img_rect_base = self._get_image_rect()
        pan_x, pan_y = self._pan
        if img_rect_base.width() <= 0 or img_rect_base.height() <= 0:
            painter.fillRect(self.rect(), QColor(0,0,0))
        else:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
            user_zoom_factor = self._zoom_step_factor ** self._zoom_level
            draw_w = img_rect_base.width() * user_zoom_factor
            draw_h = img_rect_base.height() * user_zoom_factor
            center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + pan_x
            center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + pan_y
            x = center_x - draw_w / 2.0
            y = center_y - draw_h / 2.0
            vis_rect = QRectF(self.rect())
            img_draw_rect = QRectF(x, y, draw_w, draw_h)
            visible_img_area_in_widget = vis_rect.intersected(img_draw_rect)
            if not visible_img_area_in_widget.isEmpty() and draw_w > 1e-6 and draw_h > 1e-6:
                sx = max(0, (visible_img_area_in_widget.x() - x) / draw_w * img_w)
                sy = max(0, (visible_img_area_in_widget.y() - y) / draw_h * img_h)
                sw = min(img_w - sx, visible_img_area_in_widget.width() / draw_w * img_w)
                sh = min(img_h - sy, visible_img_area_in_widget.height() / draw_h * img_h)
                if sw > 0 and sh > 0:
                    source_rect = QRectF(sx, sy, sw, sh)
                    target_rect = visible_img_area_in_widget
                    target_intermediate_pixels = 2.0 * target_rect.width() * target_rect.height()
                    source_pixels = sw * sh
                    intermediate_scale = max(0.01, min(1, (target_intermediate_pixels / source_pixels) ** 0.5 if source_pixels > 0 else 1.0))
                    intermediate_w = int(sw * intermediate_scale)
                    intermediate_h = int(sh * intermediate_scale)
                    if intermediate_scale < 0.99 and intermediate_w > 0 and intermediate_h > 0:
                        cropped_original = self._crt_image.copy(int(source_rect.x()), int(source_rect.y()), int(source_rect.width()), int(source_rect.height()))
                        if not cropped_original.isNull():
                            intermediate_image = cropped_original.scaled(intermediate_w, intermediate_h, Qt.KeepAspectRatio, Qt.FastTransformation)
                        else:
                            intermediate_image = QImage()
                    else:
                        intermediate_image = self._crt_image.copy(int(source_rect.x()), int(source_rect.y()), int(source_rect.width()), int(source_rect.height()))
                    if not intermediate_image.isNull() and target_rect.width() > 0 and target_rect.height() > 0:
                        processed_img = intermediate_image.convertToFormat(QImage.Format_Grayscale8)
                        scaled_img = processed_img.scaled(int(target_rect.width()), int(target_rect.height()), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        effect_pixmap = QPixmap(scaled_img.size())
                        effect_pixmap.fill(Qt.transparent)
                        p_effect = QPainter(effect_pixmap)
                        px = (effect_pixmap.width() - scaled_img.width()) / 2
                        py = (effect_pixmap.height() - scaled_img.height()) / 2
                        p_effect.drawImage(int(px), int(py), scaled_img)
                        contrast_color = QColor(20, 20, 20, 120)
                        p_effect.setCompositionMode(QPainter.CompositionMode_Overlay)
                        p_effect.fillRect(effect_pixmap.rect(), contrast_color)
                        p_effect.setCompositionMode(QPainter.CompositionMode_SourceOver)
                        p_effect.fillRect(effect_pixmap.rect(), QColor(0, 0, 0, 120))
                        p_effect.setCompositionMode(QPainter.CompositionMode_Multiply)
                        p_effect.fillRect(effect_pixmap.rect(), QColor(self._border_color))
                        p_effect.end()
                        painter.drawPixmap(target_rect.topLeft().toPoint(), effect_pixmap)
                    else:
                            painter.fillRect(self.rect(), QColor(0,0,0))
                else:
                    painter.fillRect(self.rect(), QColor(0,0,0))
            else:
                painter.fillRect(self.rect(), QColor(0,0,0))
    else:
        bg_color_str = self.parent_editor.theme_colors.get("bg_color", "#2C2C2C") if self.parent_editor else "#2C2C2C"
        painter.fillRect(self.rect(), QColor(bg_color_str))
        self._draw_virtual_grid(painter)

    is_region_edit_active = False
    current_selected_region_name_for_fill = None
    if self.parent_editor and self.map_type == 'world':
        current_draw_mode = self.parent_editor.get_draw_mode('world')
        is_region_edit_active = (current_draw_mode == 'region_edit')
        if is_region_edit_active:
            current_selected_region_name_for_fill = getattr(self.parent_editor, '_current_region_name', None)
    visible_rect = None
    if self._crt_image is not None:
        img_rect_base = self._get_image_rect()
        user_zoom_factor = self._zoom_step_factor ** self._zoom_level
        draw_w = img_rect_base.width() * user_zoom_factor
        draw_h = img_rect_base.height() * user_zoom_factor
        center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + self._pan[0]
        center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + self._pan[1]
        x = center_x - draw_w / 2.0
        y = center_y - draw_h / 2.0
        vis_rect = QRectF(self.rect())
        img_draw_rect = QRectF(x, y, draw_w, draw_h)
        visible_widget_area = vis_rect.intersected(img_draw_rect)
        
        if not visible_widget_area.isEmpty() and draw_w > 1e-6 and draw_h > 1e-6:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
            img_x1 = (visible_widget_area.x() - x) / draw_w * img_w
            img_y1 = (visible_widget_area.y() - y) / draw_h * img_h
            img_x2 = img_x1 + (visible_widget_area.width() / draw_w * img_w)
            img_y2 = img_y1 + (visible_widget_area.height() / draw_h * img_h)
            visible_rect = QRectF(img_x1, img_y1, img_x2 - img_x1, img_y2 - img_y1)
        else:
            visible_rect = QRectF(x, y, draw_w, draw_h)
    else:
        img_rect_base = self._get_image_rect()
        if img_rect_base.width() > 0 and img_rect_base.height() > 0:
            scale = self._zoom_step_factor ** self._zoom_level
            visible_rect = QRectF(
                self._pan[0], self._pan[1], 
                self.width() / scale, self.height() / scale
            )
    if self.parent_editor and self.map_type == 'world' and hasattr(self.parent_editor, '_region_masks') and is_region_edit_active:
        _render_region_borders(self, painter, visible_rect)
        if current_selected_region_name_for_fill:
            if self._show_region_fills and hasattr(self.parent_editor, '_region_fill_cache'):
                cached_fill_image = self.parent_editor._region_fill_cache.get(current_selected_region_name_for_fill)
                if cached_fill_image and not cached_fill_image.isNull() and visible_rect:
                    mask_scale = getattr(self.parent_editor, '_region_mask_scale', 1.0)
                    mask_x = int(visible_rect.x() * mask_scale)
                    mask_y = int(visible_rect.y() * mask_scale)
                    mask_w = int(visible_rect.width() * mask_scale)
                    mask_h = int(visible_rect.height() * mask_scale)
                    mask_x = max(0, min(mask_x, cached_fill_image.width()))
                    mask_y = max(0, min(mask_y, cached_fill_image.height()))
                    mask_w = max(0, min(mask_w, cached_fill_image.width() - mask_x))
                    mask_h = max(0, min(mask_h, cached_fill_image.height() - mask_y))
                    if mask_w > 0 and mask_h > 0:
                        visible_fill = cached_fill_image.copy(mask_x, mask_y, mask_w, mask_h)
                        top_left_widget = self._image_to_widget_coords((visible_rect.x(), visible_rect.y()))
                        bottom_right_widget = self._image_to_widget_coords((visible_rect.x() + visible_rect.width(), visible_rect.y() + visible_rect.height()))
                        if top_left_widget and bottom_right_widget:
                            target_rect = QRectF(top_left_widget, bottom_right_widget)
                            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                            painter.setBrush(Qt.NoBrush)
                            painter.setPen(Qt.NoPen)
                            painter.drawImage(target_rect, visible_fill)

            highlight_target_rect = None
            if self._crt_image is not None:
                img_rect_base_highlight = self._get_image_rect()
                user_zoom_factor_highlight = self._zoom_step_factor ** self._zoom_level
                draw_w_highlight = img_rect_base_highlight.width() * user_zoom_factor_highlight
                draw_h_highlight = img_rect_base_highlight.height() * user_zoom_factor_highlight
                center_x_highlight = img_rect_base_highlight.x() + img_rect_base_highlight.width() / 2.0 + self._pan[0]
                center_y_highlight = img_rect_base_highlight.y() + img_rect_base_highlight.height() / 2.0 + self._pan[1]
                x_highlight = center_x_highlight - draw_w_highlight / 2.0
                y_highlight = center_y_highlight - draw_h_highlight / 2.0
                highlight_target_rect = QRectF(x_highlight, y_highlight, draw_w_highlight, draw_h_highlight)
            else:
                img_rect_base_highlight = self._get_image_rect()
                if img_rect_base_highlight.width() > 0 and img_rect_base_highlight.height() > 0:
                    scale_highlight = self._zoom_step_factor ** self._zoom_level
                    highlight_target_rect = QRectF(self._pan[0], self._pan[1], self.width() / scale_highlight, self.height() / scale_highlight)
                    highlight_target_rect = highlight_target_rect.intersected(img_rect_base_highlight)
            
            if highlight_target_rect and not highlight_target_rect.isEmpty():
                highlight_color = QColor(self.parent_editor.theme_colors.get("highlight_color", "#FFFF00"))
                pen = QPen(highlight_color, 2, Qt.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(highlight_target_rect.adjusted(-1, -1, 1, 1))

    if self.parent_editor:
        base_qcolor = QColor(self.parent_editor.theme_colors.get("base_color", "#00A0A0"))
        dark_draw_color = base_qcolor.darker(160)
        if not dark_draw_color.isValid(): dark_draw_color = QColor("#404040")
        selected_color = base_qcolor.lighter(130)
        if not selected_color.isValid(): selected_color = QColor("#FFFF80")
        selected_item_type, selected_item_index = self.parent_editor.get_selected_item(self.map_type)
        img_rect_base = self._get_image_rect()
        base_scale = 1.0
        user_zoom_factor = self._zoom_step_factor ** self._zoom_level
        if self._crt_image and img_rect_base.width() > 0 and self._crt_image.width() > 0:
            img_w = self._crt_image.width()
            base_scale = img_rect_base.width() / img_w
        elif not self._crt_image and img_rect_base.width() > 0 and self._virtual_width > 0:
                base_scale = img_rect_base.width() / self._virtual_width
        else:
                base_scale = 0
        final_scale = base_scale * user_zoom_factor
        BASE_LINE_WIDTH_IMAGE = 10.0
        MIN_WIDGET_LINE_WIDTH = 2.0
        MAX_WIDGET_LINE_WIDTH = 30.0
        current_widget_line_width = max(MIN_WIDGET_LINE_WIDTH, 
                                        min(MAX_WIDGET_LINE_WIDTH, 
                                            BASE_LINE_WIDTH_IMAGE * final_scale))
        selected_widget_line_width = max(MIN_WIDGET_LINE_WIDTH, 
                                            min(MAX_WIDGET_LINE_WIDTH * 1.2,
                                                BASE_LINE_WIDTH_IMAGE * final_scale * 1.25))
        temp_widget_line_width = max(MIN_WIDGET_LINE_WIDTH * 0.75,
                                        min(MAX_WIDGET_LINE_WIDTH * 0.75,
                                            BASE_LINE_WIDTH_IMAGE * final_scale * 0.75))
        dot_brush = QBrush(dark_draw_color)
        selected_dot_brush = QBrush(selected_color)
        preview_line_color = QColor(dark_draw_color)
        preview_line_color.setAlpha(255)
        preview_line_color = preview_line_color.lighter(140)
        preview_pen = QPen(preview_line_color, 2, Qt.DashLine)
        temp_line_pen = QPen(selected_color, temp_widget_line_width, Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
        line_params = {
            'small':  {'base_thickness': 1.0, 'alpha_zoomed_out': 0,  'alpha_zoomed_in': 45, 'fade_start_scale': 0.1, 'fade_end_scale': 2},
            'medium': {'base_thickness': 3.0, 'alpha_zoomed_out': 5, 'alpha_zoomed_in': 75, 'fade_start_scale': 0.1, 'fade_end_scale': 6},
            'big':    {'base_thickness': 6.0,'alpha_zoomed_out': 25, 'alpha_zoomed_in': 90,'fade_start_scale': 0.1, 'fade_end_scale': 8.0},
        }
        default_line_params = line_params['medium']
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.NoBrush)
        if self.map_type == 'world':
            lines, dots = self.parent_editor.get_world_draw_data()
        elif self.map_type == 'location':
            lines, dots = self.parent_editor.get_location_draw_data()
        else:
            lines, dots = [], []
        visible_rect = QRectF(self.rect()).adjusted(-50, -50, 50, 50)
        if not hasattr(self, '_cached_visible_rect') or self._cached_visible_rect != visible_rect:
            self._cached_visible_rect = visible_rect
            self._clear_coord_cache()
        for path_index, line_data in enumerate(lines):
            if isinstance(line_data, tuple) and len(line_data) == 2:
                path_points, meta = line_data
            else:
                path_points = line_data
                meta = None
            if len(path_points) < 2: continue
            if not self._is_line_visible(path_points, visible_rect):
                continue
            line_type = 'medium'
            line_name = ""
            if isinstance(meta, dict):
                line_type = meta.get('type', 'medium')
                line_name = meta.get('name', "")
            else:
                line_type = meta if meta else 'medium'
            params = line_params.get(line_type, default_line_params)
            base_image_thickness = params['base_thickness']
            alpha_zoomed_out = params['alpha_zoomed_out']
            alpha_zoomed_in = params['alpha_zoomed_in']
            fade_start_scale = params['fade_start_scale']
            fade_end_scale = params['fade_end_scale']
            current_dynamic_alpha = 0
            scale_range = fade_end_scale - fade_start_scale
            if final_scale <= fade_start_scale:
                current_dynamic_alpha = alpha_zoomed_out
            elif final_scale >= fade_end_scale:
                current_dynamic_alpha = alpha_zoomed_in
            elif scale_range > 1e-6:
                t = (final_scale - fade_start_scale) / scale_range
                current_dynamic_alpha = alpha_zoomed_out + t * (alpha_zoomed_in - alpha_zoomed_out)
            else:
                current_dynamic_alpha = (alpha_zoomed_out + alpha_zoomed_in) / 2
            current_dynamic_alpha = max(0, min(255, int(current_dynamic_alpha)))
            if current_dynamic_alpha <= 0:
                continue
            current_widget_line_width = max(MIN_WIDGET_LINE_WIDTH, 
                                            min(MAX_WIDGET_LINE_WIDTH, 
                                                base_image_thickness * final_scale))
            selected_widget_line_width = max(MIN_WIDGET_LINE_WIDTH, 
                                                min(MAX_WIDGET_LINE_WIDTH * 1.2, 
                                                    base_image_thickness * final_scale * 1.25))
            
            widget_points = self._batch_convert_coords(path_points)
            if not widget_points or any(p is None for p in widget_points):
                continue
                
            widget_path = QPainterPath()
            widget_path.moveTo(widget_points[0])
            for i in range(1, len(widget_points)):
                widget_path.lineTo(widget_points[i])
            
            is_selected = (selected_item_type == 'line' and path_index == selected_item_index)
            is_hovered = (path_index == self._hovered_line_index)
            is_same_name = (current_name_field and line_name == current_name_field)
            main_pen_color = selected_color if is_selected else dark_draw_color
            main_pen_width = selected_widget_line_width if is_selected else current_widget_line_width
            main_pen_alpha = 255
            if is_same_name and current_name_field and not is_selected:
                main_pen_color = main_pen_color.lighter(150)
                main_pen_alpha = 255
            if is_hovered:
                main_pen_width *= 1.15
                main_pen_color = main_pen_color.lighter(150)
            elif is_selected:
                main_pen_width *= 1.3
                main_pen_color = main_pen_color.lighter(150)
            main_pen_color.setAlpha(main_pen_alpha)
            pen_style = Qt.SolidLine
            if isinstance(meta, dict) and meta.get("instant", False):
                pen_style = Qt.DashLine
            main_pen = QPen(main_pen_color, main_pen_width, pen_style, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(main_pen)
            painter.drawPath(widget_path)
        connected_start_dot_idx = -1
        connected_end_dot_idx = -1
        if selected_item_type == 'line' and 0 <= selected_item_index < len(lines):
            line_data = lines[selected_item_index]
            if isinstance(line_data, tuple) and len(line_data) == 2:
                path_points, meta = line_data
                if isinstance(meta, dict):
                    if len(path_points) >= 2:
                        start_point = path_points[0]
                        end_point = path_points[-1]
                        min_start_dist = float('inf')
                        min_end_dist = float('inf')
                        start_dot_idx = -1
                        end_dot_idx = -1
                        dot_hit_tolerance = 12.0
                        for dot_idx, dot_data in enumerate(dots):
                            if isinstance(dot_data, (list, tuple)) and len(dot_data) >= 2:
                                dot_x, dot_y = dot_data[0], dot_data[1]
                                dot_point = (dot_x, dot_y)
                                start_dist = math.dist(start_point, dot_point)
                                if start_dist < min_start_dist and start_dist <= dot_hit_tolerance:
                                    min_start_dist = start_dist
                                    start_dot_idx = dot_idx
                                end_dist = math.dist(end_point, dot_point)
                                if end_dist < min_end_dist and end_dist <= dot_hit_tolerance:
                                    min_end_dist = end_dist
                                    end_dot_idx = dot_idx
                        connected_start_dot_idx = start_dot_idx
                        connected_end_dot_idx = end_dot_idx
                    else:
                        connected_start_dot_idx = meta.get('start', -1)
                        connected_end_dot_idx = meta.get('end', -1)
        dot_params = {
            'small': {'radius': 3.0, 'sel_radius': 3.4},
            'medium': {'radius': 10, 'sel_radius': 10},
            'big': {'radius': 22, 'sel_radius': 22},
        }
        default_dot_params = dot_params['small']
        img_rect_base = self._get_image_rect()
        pan_x, pan_y = self._pan[0], self._pan[1]
        user_zoom_factor = self._zoom_step_factor ** self._zoom_level
        if self._crt_image:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
        else:
            img_w, img_h = self._virtual_width, self._virtual_height
        base_scale_x = 0
        base_scale_y = 0
        if img_w > 0 and img_rect_base.width() > 0:
                base_scale_x = img_rect_base.width() / img_w
        if img_h > 0 and img_rect_base.height() > 0:
                base_scale_y = img_rect_base.height() / img_h
        base_scale = min(base_scale_x, base_scale_y) if base_scale_x > 0 and base_scale_y > 0 else max(base_scale_x, base_scale_y)
        final_scale = base_scale * user_zoom_factor
        min_widget_radius = 1.0
        dot_coords = []
        for dot_index, dot_data in enumerate(dots):
            dot_type = None
            linked_name = None
            if isinstance(dot_data, (list, tuple)):
                if len(dot_data) >= 6:
                    p_img_x, p_img_y, pulse_offset, dot_type, linked_name, region_name = dot_data[:6]
                elif len(dot_data) >= 5:
                    p_img_x, p_img_y, pulse_offset, dot_type, linked_name = dot_data[:5]
                elif len(dot_data) >= 4:
                    p_img_x, p_img_y, pulse_offset, dot_type = dot_data[:4]
                    linked_name = None
            else:
                print(f"Warning [paintEvent]: Skipping non-sequence dot data: {dot_data}")
                continue
            if dot_type is None:
                print(f"Warning [paintEvent]: dot_type not assigned for dot_data (len={len(dot_data) if isinstance(dot_data, (list, tuple)) else 'N/A'}): {dot_data}")
                continue
            p_img = (p_img_x, p_img_y)
            dot_coords.append((dot_index, p_img, dot_type, linked_name))
        if dot_coords:
            image_coords_list = [coord[1] for coord in dot_coords]
            widget_coords = self._batch_convert_coords(image_coords_list)
            for i, (dot_index, p_img, dot_type, linked_name) in enumerate(dot_coords):
                p_widget = widget_coords[i]
                if not p_widget or not visible_rect.contains(p_widget):
                    continue
                params = dot_params.get(dot_type, default_dot_params)
                is_selected = (selected_item_type == 'dot' and dot_index == selected_item_index)
                is_hovered = (dot_index == self._hovered_dot_index)
                should_appear_selected = is_selected or (selected_item_type == 'line' and (dot_index == connected_start_dot_idx or dot_index == connected_end_dot_idx))
                dot_alpha = 255
                if should_appear_selected and selected_item_type == 'line':
                    current_image_radius = params['sel_radius']
                    dot_alpha = 255
                elif should_appear_selected and selected_item_type == 'dot':
                    current_image_radius = params['sel_radius']
                    dot_alpha = 255
                else:
                    current_image_radius = params['radius']
                    dot_alpha = 255
                widget_radius = max(min_widget_radius, current_image_radius * final_scale)
                if is_hovered:
                    widget_radius *= 1.3
                base_brush = selected_dot_brush if should_appear_selected else dot_brush
                faded_color = QColor(base_brush.color())
                if should_appear_selected:
                    faded_color = faded_color.lighter(150)
                elif is_hovered:
                    faded_color = faded_color.lighter(150)
                else:
                    faded_color = faded_color.lighter(130)
                faded_color.setAlpha(dot_alpha)
                faded_brush = QBrush(faded_color)
                painter.setBrush(faded_brush)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(p_widget, widget_radius, widget_radius)
        if self._is_linking_dots and len(self._link_start_dot_img_pos) >= 1:
            painter.setPen(temp_line_pen)
            painter.setBrush(Qt.NoBrush)
            if len(self._link_start_dot_img_pos) == 1:
                painter.drawEllipse(self._link_start_dot_widget_pos, 2, 2)
            else:
                temp_path = QPainterPath()
                temp_path.moveTo(self._link_start_dot_widget_pos)
                for i in range(1, len(self._link_start_dot_img_pos)):
                    temp_path.lineTo(self._link_start_dot_widget_pos)
                painter.drawPath(temp_path)
        if self._is_linking_dots and len(self._link_path_widget) >= 1:
            current_line_type = 'medium'
            path_mode = 'draw'
            if self.parent_editor:
                if self.map_type == 'world':
                    current_line_type = self.parent_editor._world_line_type_mode
                    path_mode = self.parent_editor.get_path_mode('world')
                elif self.map_type == 'location':
                    current_line_type = self.parent_editor._location_line_type_mode
                    path_mode = self.parent_editor.get_path_mode('location')
            preview_params = line_params.get(current_line_type, default_line_params)
            preview_base_thickness = preview_params['base_thickness']
            calculated_preview_width = max(MIN_WIDGET_LINE_WIDTH, min(MAX_WIDGET_LINE_WIDTH, preview_base_thickness * final_scale * 0.9))
            preview_pen.setWidthF(calculated_preview_width)
            painter.setPen(preview_pen)
            painter.setBrush(Qt.NoBrush)
            preview_path = QPainterPath()
            preview_path.moveTo(self._link_path_widget[0])
            if path_mode == 'line':
                if len(self._link_path_widget) > 1:
                    preview_path.lineTo(self._link_path_widget[-1])
                else:
                    preview_path.lineTo(self._link_preview_end_widget_pos)
            else:
                if len(self._link_path_widget) > 1:
                    for i in range(1, len(self._link_path_widget)):
                        preview_path.lineTo(self._link_path_widget[i])
                    if len(self._link_path_widget) >= 4:
                        points = [(p.x(), p.y()) for p in self._link_path_widget]
                        path_smoothness = 5
                        if self.parent_editor and hasattr(self.parent_editor, 'get_path_smoothness'):
                            smoothness_percent = self.parent_editor.get_path_smoothness(self.map_type)
                            path_smoothness = max(1, int(smoothness_percent / 10))
                        smooth_points = catmull_rom(points, steps=path_smoothness)
                        smooth_preview_path = QPainterPath()
                        smooth_preview_path.moveTo(QPointF(smooth_points[0][0], smooth_points[0][1]))
                        for x, y in smooth_points[1:]:
                            smooth_preview_path.lineTo(QPointF(x, y))
                        if not smooth_preview_path.isEmpty():
                            preview_path = smooth_preview_path
            painter.drawPath(preview_path)
    if (
        hasattr(self, '_region_paint_stroke_points') and self._region_paint_stroke_points
        and self.parent_editor and self.map_type == 'world'
        and getattr(self.parent_editor, '_world_draw_mode', None) == 'region_edit'
        and getattr(self.parent_editor, '_world_region_sub_mode', None) == 'paint'
        and hasattr(self, '_is_actively_painting') and self._is_actively_painting
    ):
        stroke_points = self._region_paint_stroke_points
        brush_size = getattr(self.parent_editor, '_region_brush_size', 5)
        base_color_str = self.parent_editor.theme_colors.get("base_color", "#00A0A0")
        base_color = QColor(base_color_str)
        preview_color = base_color.lighter(130)
        preview_color.setAlpha(255)
        overlay_img = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        overlay_img.fill(Qt.transparent)
        overlay_painter = QPainter(overlay_img)
        overlay_painter.setRenderHint(QPainter.Antialiasing, True)
        overlay_painter.setPen(Qt.NoPen)
        overlay_painter.setBrush(preview_color)
        for i in range(len(stroke_points)):
            x, y = stroke_points[i]
            widget_pt = self._image_to_widget_coords((x, y))
            if widget_pt:
                if self._crt_image is not None:
                    img_w, img_h = self._crt_image.width(), self._crt_image.height()
                    img_rect_base = self._get_image_rect()
                    user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                    pixels_per_image_unit = (img_rect_base.width() * user_zoom_factor) / img_w
                    visual_brush_radius = (brush_size / 2) * pixels_per_image_unit
                else:
                    scale = self._zoom_step_factor ** self._zoom_level
                    visual_brush_radius = (brush_size / 2) * scale
                overlay_painter.drawEllipse(widget_pt, visual_brush_radius, visual_brush_radius)
        overlay_painter.end()
        painter.drawImage(0, 0, overlay_img)
    if (
        hasattr(self, '_region_erase_stroke_points') and self._region_erase_stroke_points
        and self.parent_editor and self.map_type == 'world'
        and getattr(self.parent_editor, '_world_draw_mode', None) == 'region_edit'
        and getattr(self.parent_editor, '_world_region_sub_mode', None) == 'paint'
    ):
        stroke_points = self._region_erase_stroke_points
        brush_size = getattr(self.parent_editor, '_region_brush_size', 5)
        preview_color = QColor(255, 80, 80, 160)
        overlay_img = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        overlay_img.fill(Qt.transparent)
        overlay_painter = QPainter(overlay_img)
        overlay_painter.setRenderHint(QPainter.Antialiasing, True)
        eraser_pen = QPen(QColor(255, 0, 0, 200), 1.5, Qt.DashLine)
        overlay_painter.setPen(eraser_pen)
        overlay_painter.setBrush(QBrush(preview_color))
        for i in range(len(stroke_points)):
            x, y = stroke_points[i]
            widget_pt = self._image_to_widget_coords((x, y))
            if widget_pt:
                if self._crt_image is not None:
                    img_w, img_h = self._crt_image.width(), self._crt_image.height()
                    img_rect_base = self._get_image_rect()
                    user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                    pixels_per_image_unit = (img_rect_base.width() * user_zoom_factor) / img_w
                    visual_brush_radius = (brush_size / 2) * pixels_per_image_unit
                else:
                    scale = self._zoom_step_factor ** self._zoom_level
                    visual_brush_radius = (brush_size / 2) * scale
                overlay_painter.drawEllipse(widget_pt, visual_brush_radius, visual_brush_radius)
                overlay_painter.setPen(QPen(QColor(255, 255, 255, 220), 1.5))
                overlay_painter.drawLine(QLineF(
                    widget_pt.x() - visual_brush_radius * 0.7, 
                    widget_pt.y() - visual_brush_radius * 0.7,
                    widget_pt.x() + visual_brush_radius * 0.7, 
                    widget_pt.y() + visual_brush_radius * 0.7
                ))
                overlay_painter.drawLine(QLineF(
                    widget_pt.x() + visual_brush_radius * 0.7, 
                    widget_pt.y() - visual_brush_radius * 0.7,
                    widget_pt.x() - visual_brush_radius * 0.7, 
                    widget_pt.y() + visual_brush_radius * 0.7
                ))
                overlay_painter.setPen(eraser_pen)
        overlay_painter.end()
        painter.drawImage(0, 0, overlay_img)
    if (
        self.parent_editor and self.map_type == 'world'
        and getattr(self.parent_editor, '_world_draw_mode', None) == 'region_edit'
        and hasattr(self.parent_editor, '_region_masks')
    ):
        painter.save()
        painter.setClipRect(self.rect(), Qt.ReplaceClip)
        region_masks = self.parent_editor._region_masks
        valid_regions = set()
        if hasattr(self.parent_editor, 'world_region_selector') and self.parent_editor.world_region_selector:
            for i in range(self.parent_editor.world_region_selector.count()):
                region_name = self.parent_editor.world_region_selector.itemText(i)
                if region_name != "No regions available":
                    valid_regions.add(region_name)
        if valid_regions:
            region_masks = {name: mask for name, mask in region_masks.items() if name in valid_regions}
        current_painting = None
        if hasattr(self, '_region_paint_stroke_points') and self._region_paint_stroke_points and \
           getattr(self.parent_editor, '_world_region_sub_mode', None) == 'paint':
            current_painting = getattr(self.parent_editor, '_current_region_name', None)
        mask_scale = getattr(self.parent_editor, '_region_mask_scale', 1.0)
        for region_name, mask in region_masks.items():
            if not mask or mask.isNull():
                continue
            if current_painting and region_name == current_painting:
                continue
            mask_h, mask_w = mask.height(), mask.width()
            mask_bits = mask.bits()
            mask_bits.setsize(mask.byteCount())
            arr = np.frombuffer(mask_bits, dtype=np.uint8).reshape((mask_h, mask_w, 4))
            alpha = arr[..., 3]
            ys, xs = np.nonzero(alpha > 127)
            if len(xs) == 0:
                continue
            cx = int(np.mean(xs)) / mask_scale
            cy = int(np.mean(ys)) / mask_scale
            widget_pt = self._image_to_widget_coords((cx, cy))
            if not widget_pt:
                continue
            visible_rect = QRectF(self.rect())
            region_size_px = len(xs)
            if self._zoom_level <= 0:
                min_visible_region_size = 300
                if region_size_px < min_visible_region_size:
                    continue
            if self._zoom_level > 0:
                if not visible_rect.contains(widget_pt):
                    nearest_x = max(visible_rect.left(), min(widget_pt.x(), visible_rect.right()))
                    nearest_y = max(visible_rect.top(), min(widget_pt.y(), visible_rect.bottom()))
                    nearest_point = QPointF(nearest_x, nearest_y)
                    distance = QLineF(widget_pt, nearest_point).length()
                    base_distance = 100
                    zoom_factor = 2 ** (self._zoom_level / 2)
                    max_distance = base_distance / zoom_factor
                    region_size_factor = min(1.0, region_size_px / 5000)
                    adjusted_distance = max_distance * (0.5 + 0.5 * region_size_factor)
                    if distance > adjusted_distance:
                        continue
            label = str(region_name).replace('_', ' ')
            font = QFont()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)
            fm = QFontMetrics(font)
            text_rect = fm.boundingRect(label)
            text_rect.adjust(-5, -2, 5, 2)
            text_rect.moveCenter(widget_pt.toPoint())
            if text_rect.left() < 10:
                text_rect.moveLeft(10)
            if text_rect.right() > self.width() - 10:
                text_rect.moveRight(self.width() - 10)
            if text_rect.top() < 10:
                text_rect.moveTop(10)
            if text_rect.bottom() > self.height() - 10:
                text_rect.moveBottom(self.height() - 10)
            text_color = QColor(self.parent_editor.theme_colors.get("base_color", "#00A0A0"))
            text_color = text_color.lighter(150)
            shadow_color = QColor(0, 0, 0, 180)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    shadow_rect = text_rect.translated(dx, dy)
                    painter.setPen(shadow_color)
                    painter.drawText(shadow_rect, Qt.AlignCenter, label)
            painter.setPen(text_color)
            painter.drawText(text_rect, Qt.AlignCenter, label)
        painter.restore()
    if self.parent_editor:
        is_feature_paint_mode_active = False
        if self.map_type == 'world':
            is_feature_paint_mode_active = getattr(self.parent_editor, '_world_feature_paint', False)
        elif self.map_type == 'location':
            is_feature_paint_mode_active = getattr(self.parent_editor, '_location_feature_paint', False)
        if is_feature_paint_mode_active:
            feature_masks = {}
            feature_border_cache = {}
            current_feature = None
            mask_scale = 0.5
            
            if self.map_type == 'world':
                if hasattr(self.parent_editor, '_feature_masks') and 'world' in self.parent_editor._feature_masks:
                    feature_masks = self.parent_editor._feature_masks['world']
                if hasattr(self.parent_editor, '_feature_border_cache') and 'world' in self.parent_editor._feature_border_cache:
                    feature_border_cache = self.parent_editor._feature_border_cache['world']
                current_feature = getattr(self.parent_editor, '_current_world_feature', None)
                mask_scale = getattr(self.parent_editor, '_feature_mask_scale', 0.5)
            elif self.map_type == 'location':
                if hasattr(self.parent_editor, '_feature_masks') and 'location' in self.parent_editor._feature_masks:
                    feature_masks = self.parent_editor._feature_masks['location']
                if hasattr(self.parent_editor, '_feature_border_cache') and 'location' in self.parent_editor._feature_border_cache:
                    feature_border_cache = self.parent_editor._feature_border_cache['location']
                current_feature = getattr(self.parent_editor, '_current_location_feature', None)
                mask_scale = getattr(self.parent_editor, '_feature_mask_scale', 0.5)
            
            map_viewport_rect = None
            if self._crt_image is not None:
                img_rect_base = self._get_image_rect()
                user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                draw_w = img_rect_base.width() * user_zoom_factor
                draw_h = img_rect_base.height() * user_zoom_factor
                center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + self._pan[0]
                center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + self._pan[1]
                x = center_x - draw_w / 2.0
                y = center_y - draw_h / 2.0
                map_viewport_rect = QRectF(x, y, draw_w, draw_h)
            else:
                img_rect_base = self._get_image_rect()
                if img_rect_base.width() > 0 and img_rect_base.height() > 0:
                    scale = self._zoom_step_factor ** self._zoom_level
                    map_viewport_rect = QRectF(
                        self._pan[0], self._pan[1], 
                        self.width() / scale, self.height() / scale
                    )

            for feature_name, mask in feature_masks.items():
                if mask and not mask.isNull():
                    target_rect = None 
                    if self._crt_image is not None:
                        img_rect_base = self._get_image_rect()
                        user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                        draw_w = img_rect_base.width() * user_zoom_factor
                        draw_h = img_rect_base.height() * user_zoom_factor
                        center_x = img_rect_base.x() + img_rect_base.width() / 2.0 + self._pan[0]
                        center_y = img_rect_base.y() + img_rect_base.height() / 2.0 + self._pan[1]
                        x = center_x - draw_w / 2.0
                        y = center_y - draw_h / 2.0
                        target_rect = QRectF(x, y, draw_w, draw_h)
                    else:
                        img_rect_base = self._get_image_rect()
                        if img_rect_base.width() > 0 and img_rect_base.height() > 0:
                            scale = self._zoom_step_factor ** self._zoom_level
                            mask_display_x = self._pan[0] 
                            mask_display_y = self._pan[1]
                            mask_display_width = mask.width() * scale / mask_scale
                            mask_display_height = mask.height() * scale / mask_scale
                            target_rect = QRectF(mask_display_x, mask_display_y, mask_display_width, mask_display_height)
                    if not target_rect: continue
                    base_color_str = self.parent_editor.theme_colors.get("base_color", "#00A0A0")
                    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    if feature_name == current_feature:
                        translucent_color = QColor(base_color_str)
                        translucent_color.setAlpha(128)
                        colored_img = QImage(mask.size(), QImage.Format_ARGB32)
                        colored_img.fill(translucent_color)
                        painter_mask = QPainter(colored_img)
                        painter_mask.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                        painter_mask.drawImage(0, 0, mask)
                        painter_mask.end()
                        painter.setBrush(Qt.NoBrush)
                        painter.setPen(Qt.NoPen)
                        painter.drawImage(target_rect, colored_img)
                    
                    if feature_name not in feature_border_cache or not feature_border_cache[feature_name]:
                        if self.map_type == 'world':
                            feature_border_cache = getattr(self.parent_editor, '_feature_border_cache', {}).get('world', {})
                        elif self.map_type == 'location':
                            feature_border_cache = getattr(self.parent_editor, '_feature_border_cache', {}).get('location', {})
                    list_of_contours = feature_border_cache.get(feature_name, [])
                    if list_of_contours:
                        painter.save()
                        border_color = QColor(base_color_str)
                        if feature_name == current_feature:
                            border_color = border_color.lighter(130)
                            border_color.setAlpha(240)
                            pen = QPen(border_color, 2.0)
                        else:
                            border_color.setAlpha(200)
                            pen = QPen(border_color, 1.5)
                        painter.setPen(pen)
                        painter.setBrush(Qt.NoBrush)
                        sample_rate = 1 if self._zoom_level >= 0 else max(1, int(3 / (self._zoom_level + 3)))
                        w_mask, h_mask = mask.width(), mask.height()
                        for contour_points in list_of_contours:
                            if not contour_points or len(contour_points) < 2:
                                continue
                            path = QPainterPath()
                            first_point = True
                            sampled_points = []
                            for i, point in enumerate(contour_points):
                                if i == 0 or i == len(contour_points) - 1 or i % sample_rate == 0:
                                    sampled_points.append(point)
                            if len(sampled_points) >= 4:
                                if sampled_points[0] != sampled_points[-1]:
                                    closed_points = [sampled_points[-2]] + sampled_points + [sampled_points[1]]
                                else:
                                    closed_points = [sampled_points[-2]] + sampled_points[:-1] + [sampled_points[0], sampled_points[1]]
                                spline_steps = 5
                                smooth_points = catmull_rom(closed_points, steps=spline_steps)
                                if smooth_points[0] != smooth_points[-1]:
                                    smooth_points.append(smooth_points[0])
                            else:
                                smooth_points = sampled_points
                            for i, (x_mask, y_mask) in enumerate(smooth_points):
                                fx = target_rect.left() + (x_mask / w_mask) * target_rect.width()
                                fy = target_rect.top() + (y_mask / h_mask) * target_rect.height()
                                if first_point:
                                    path.moveTo(fx, fy)
                                    first_point = False
                                else:
                                    path.lineTo(fx, fy)
                            if not path.isEmpty():
                                painter.drawPath(path)
                        painter.restore()
            for feature_name, mask in feature_masks.items():
                if not mask or mask.isNull():
                    continue
                mask_h, mask_w = mask.height(), mask.width()
                mask_bits = mask.bits()
                mask_bits.setsize(mask.byteCount())
                try:
                    arr = np.frombuffer(mask_bits, dtype=np.uint8).reshape((mask_h, mask_w, 4))
                    alpha = arr[..., 3]
                    ys, xs = np.nonzero(alpha > 127)
                    if len(xs) == 0:
                        continue
                    cx = int(np.mean(xs)) / mask_scale
                    cy = int(np.mean(ys)) / mask_scale
                    widget_pt = self._image_to_widget_coords((cx, cy))
                    if not widget_pt:
                        continue
                    visible_rect = QRectF(self.rect())
                    region_size_px = len(xs)
                    if self._zoom_level <= 0 and region_size_px < 300:
                        continue
                    if self._zoom_level > 0 and not visible_rect.contains(widget_pt):
                        nearest_x = max(visible_rect.left(), min(widget_pt.x(), visible_rect.right()))
                        nearest_y = max(visible_rect.top(), min(widget_pt.y(), visible_rect.bottom()))
                        nearest_point = QPointF(nearest_x, nearest_y)
                        distance = QLineF(widget_pt, nearest_point).length()
                        max_distance = 100 / (2 ** (self._zoom_level / 2))
                        if distance > max_distance:
                            continue
                    label = str(feature_name)
                    if '_' in label:
                        parts = label.split('_')
                        if len(parts) == 2 and parts[1].isdigit():
                            label = f"{parts[0].capitalize()} {parts[1]}"
                        else:
                            label = ' '.join(part.capitalize() for part in parts)
                    else:
                        label = label.capitalize()
                    font = QFont()
                    font.setPointSize(14)
                    font.setBold(True)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    text_rect = fm.boundingRect(label)
                    text_rect.adjust(-5, -2, 5, 2)
                    text_rect.moveCenter(widget_pt.toPoint())
                    if text_rect.left() < 10:
                        text_rect.moveLeft(10)
                    if text_rect.right() > self.width() - 10:
                        text_rect.moveRight(self.width() - 10)
                    if text_rect.top() < 10:
                        text_rect.moveTop(10)
                    if text_rect.bottom() > self.height() - 10:
                        text_rect.moveBottom(self.height() - 10)
                    text_color = QColor(self.parent_editor.theme_colors.get("base_color", "#00A0A0"))
                    text_color = text_color.lighter(150)
                    shadow_color = QColor(0, 0, 0, 180)
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            shadow_rect = text_rect.translated(dx, dy)
                            painter.setPen(shadow_color)
                            painter.drawText(shadow_rect, Qt.AlignCenter, label)
                    painter.setPen(text_color)
                    painter.drawText(text_rect, Qt.AlignCenter, label)
                except ImportError:
                    print("NumPy not available for feature label positioning")
                except Exception as e:
                    print(f"Error drawing feature name: {e}")
    if self.parent_editor:
        is_feature_paint_mode = False
        current_feature = None
        brush_size = 10
        feature_sub_mode = 'paint'
        
        if self.map_type == 'world':
            is_feature_paint_mode = getattr(self.parent_editor, '_world_feature_paint', False)
            current_feature = getattr(self.parent_editor, '_current_world_feature', None)
            brush_size = getattr(self.parent_editor, '_world_feature_brush_size', 10)
            feature_sub_mode = getattr(self.parent_editor, '_world_feature_sub_mode', 'paint')
        elif self.map_type == 'location':
            is_feature_paint_mode = getattr(self.parent_editor, '_location_feature_paint', False)
            current_feature = getattr(self.parent_editor, '_current_location_feature', None)
            brush_size = getattr(self.parent_editor, '_location_feature_brush_size', 10)
            feature_sub_mode = getattr(self.parent_editor, '_location_feature_sub_mode', 'paint')
        if is_feature_paint_mode and current_feature and feature_sub_mode == 'paint':
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            if self.rect().contains(cursor_pos):
                img_rect_base = self._get_image_rect()
                base_scale = 1.0
                user_zoom_factor = self._zoom_step_factor ** self._zoom_level
                if self._crt_image and img_rect_base.width() > 0 and self._crt_image.width() > 0:
                    img_w = self._crt_image.width()
                    base_scale = img_rect_base.width() / img_w
                elif not self._crt_image and img_rect_base.width() > 0 and self._virtual_width > 0:
                    base_scale = img_rect_base.width() / self._virtual_width
                final_scale = base_scale * user_zoom_factor
                widget_radius = max(1.0, brush_size * final_scale / 2.0)
                preview_color = QColor(self.parent_editor.theme_colors.get("base_color", "#00A0A0"))
                preview_color = preview_color.lighter(130)
                preview_color.setAlpha(255)
                painter.setBrush(QBrush(preview_color))
                preview_stroke_color = preview_color.lighter(120)
                preview_stroke_color.setAlpha(255)
                painter.setPen(QPen(preview_stroke_color, 1, Qt.DashLine))
                painter.drawEllipse(cursor_pos, widget_radius, widget_radius)

    if hasattr(self, '_feature_paint_stroke') and self._feature_paint_stroke and len(self._feature_paint_stroke) > 0:
        preview_stroke_color = QColor(self.parent_editor.theme_colors.get("base_color", "#00A0A0"))
        preview_stroke_color.setAlpha(80)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(preview_stroke_color))
        brush_size_img = 10
        if self.map_type == 'world':
            brush_size_img = getattr(self.parent_editor, '_world_feature_brush_size', 10)
        elif self.map_type == 'location':
            brush_size_img = getattr(self.parent_editor, '_location_feature_brush_size', 10)
        img_rect_base = self._get_image_rect()
        base_scale = 1.0
        user_zoom_factor = self._zoom_step_factor ** self._zoom_level
        if self._crt_image and img_rect_base.width() > 0 and self._crt_image.width() > 0:
            img_w = self._crt_image.width()
            base_scale = img_rect_base.width() / img_w
        elif not self._crt_image and img_rect_base.width() > 0 and self._virtual_width > 0:
            base_scale = img_rect_base.width() / self._virtual_width
        final_scale = base_scale * user_zoom_factor
        widget_radius = max(1.0, brush_size_img * final_scale / 2.0)
        if len(self._feature_paint_stroke) == 1:
            p_widget = self._image_to_widget_coords(self._feature_paint_stroke[0])
            if p_widget:
                painter.drawEllipse(p_widget, widget_radius, widget_radius)
        else:
            for i in range(len(self._feature_paint_stroke)):
                p_img = self._feature_paint_stroke[i]
                if isinstance(p_img, (list, tuple)) and len(p_img) >= 2:
                    p_widget = self._image_to_widget_coords(p_img)
                    if p_widget:
                        painter.drawEllipse(p_widget, widget_radius, widget_radius)
    painter.end()


def _find_item_at_pos(self, widget_pos):
    if not self.parent_editor:
        return None, -1
    if self._crt_image is not None and self._crt_image.width() > 0 and self._crt_image.height() > 0:
        has_image = True
        img_w, img_h = self._crt_image.width(), self._crt_image.height()
    else:
        has_image = False
        img_w, img_h = self._virtual_width, self._virtual_height
    dot_hit_tolerance = 12.0
    line_hit_tolerance = 8.0
    if self.map_type == 'world':
        lines, dots = self.parent_editor.get_world_draw_data()
    elif self.map_type == 'location':
        lines, dots = self.parent_editor.get_location_draw_data()
    else:
        return None, -1
    for index, dot_data in enumerate(dots):
        p_img_x, p_img_y, *_ = dot_data
        p_img = (p_img_x, p_img_y)
        p_widget = self._image_to_widget_coords(p_img)
        if p_widget:
            distance = QLineF(widget_pos, p_widget).length()
            if distance <= dot_hit_tolerance:
                return 'dot', index
    for path_index, line_data in enumerate(lines):
        if isinstance(line_data, tuple) and len(line_data) == 2:
            path_points, meta = line_data
        else:
            path_points = line_data
            meta = None
        if len(path_points) < 2: continue
        widget_points = [self._image_to_widget_coords(p) for p in path_points]
        for i in range(len(widget_points) - 1):
            p1_widget = widget_points[i]
            p2_widget = widget_points[i+1]
            if p1_widget and p2_widget:
                line = QLineF(p1_widget, p2_widget)
                line_len_sq = line.length() ** 2
                if line_len_sq < 1e-6:
                    distance = QLineF(widget_pos, p1_widget).length()
                else:
                    t = ((widget_pos.x() - p1_widget.x()) * line.dx() +
                         (widget_pos.y() - p1_widget.y()) * line.dy()) / line_len_sq
                    t = max(0.0, min(1.0, t))
                    projection = p1_widget + t * QPointF(line.dx(), line.dy())
                    distance = QLineF(widget_pos, projection).length()
                if distance <= line_hit_tolerance:
                    return 'line', path_index
    if self.map_type == 'world' and hasattr(self.parent_editor, '_region_masks'):
        if (not self.parent_editor._region_masks and 
            hasattr(self.parent_editor, '_world_regions') and 
            self.parent_editor._world_regions and
            hasattr(self.parent_editor, '_ensure_region_masks_exist')):
            self.parent_editor._ensure_region_masks_exist()
        
        mask_scale = getattr(self.parent_editor, '_region_mask_scale', 1.0)
        image_coords = self._widget_to_image_coords(widget_pos)
        if image_coords is not None and self.parent_editor._region_masks:
            for region_name in reversed(list(self.parent_editor._region_masks.keys())):
                mask = self.parent_editor._region_masks.get(region_name)
                if mask and not mask.isNull():
                    scaled_img_x = int(image_coords[0] * mask_scale)
                    scaled_img_y = int(image_coords[1] * mask_scale)
                    if 0 <= scaled_img_x < mask.width() and 0 <= scaled_img_y < mask.height():
                        pixel_color = mask.pixelColor(scaled_img_x, scaled_img_y)
                        if pixel_color.alpha() > 10:
                            return 'region', region_name
    return None, -1

def leaveEvent(self, event):
    if hasattr(self, '_hovered_line_index') and self._hovered_line_index != -1:
        self._hovered_line_index = -1
        self.update()
    if hasattr(self, '_hovered_dot_index') and self._hovered_dot_index != -1:
        self._hovered_dot_index = -1
        self.update()
    super().leaveEvent(event)

def keyPressEvent(self, event):
    if event.key() == Qt.Key_Delete:
        local_selected_type = getattr(self, f"_{self.map_type}_selected_item_type", None)
        local_selected_index = getattr(self, f"_{self.map_type}_selected_item_index", -1)
        parent_selected_type = None
        parent_selected_index = -1
        if self.parent_editor:
            parent_selected_type = getattr(self.parent_editor, f"_{self.map_type}_selected_item_type", None)
            parent_selected_index = getattr(self.parent_editor, f"_{self.map_type}_selected_item_index", -1)
        selected_type = local_selected_type if local_selected_type is not None else parent_selected_type
        selected_index = local_selected_index if local_selected_index >= 0 else parent_selected_index
        if selected_type is not None and hasattr(self.parent_editor, 'delete_selected_item'):
            self.parent_editor.delete_selected_item(self.map_type)
            return
    if not event.isAccepted():
        QLabel.keyPressEvent(self, event)
