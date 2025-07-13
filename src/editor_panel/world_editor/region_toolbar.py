from PyQt5.QtWidgets import QComboBox, QWidget, QMessageBox
import os
from PyQt5.QtGui import QImage, QPainter, QColor, QPen, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QRectF, QTimer, QPointF
import numpy as np
import time

def _set_region_edit_mode(self, map_type, checked):
    if map_type != 'world':
        return
    region_submode_widget = getattr(self, 'world_region_submode_widget', None)
    region_selector_label = getattr(self, 'world_region_selector_label', None)
    region_selector = getattr(self, 'world_region_selector', None)
    brush_size_label = getattr(self, 'world_brush_size_label', None)
    brush_size_slider = getattr(self, 'world_brush_size_slider', None)
    widgets_to_toggle = [
        region_submode_widget, region_selector_label, region_selector,
        brush_size_label, brush_size_slider
    ]
    if checked:
        setattr(self, '_show_region_fills', True)
        setattr(self, '_region_edit_mode_active', True)
        if hasattr(self, 'world_map_label') and self.world_map_label:
            setattr(self.world_map_label, '_show_region_fills', True)
            setattr(self.world_map_label, '_region_edit_mode_active', True)
        world_features_toolbar = getattr(self, 'world_features_toolbar', None)
        feature_submode_widget = getattr(self, 'world_feature_submode_widget', None)
        if feature_submode_widget:
            feature_submode_widget.setVisible(False)
        if world_features_toolbar:
            if hasattr(world_features_toolbar, 'feature_selector_label'):
                world_features_toolbar.feature_selector_label.setVisible(False)
            if hasattr(world_features_toolbar, 'feature_selector'):
                world_features_toolbar.feature_selector.setVisible(False)
            if hasattr(world_features_toolbar, 'brush_size_label'):
                world_features_toolbar.brush_size_label.setVisible(False)
            if hasattr(world_features_toolbar, 'brush_size_slider'):
                world_features_toolbar.brush_size_slider.setVisible(False)
            if hasattr(world_features_toolbar, 'set_feature_paint_mode'):
                world_features_toolbar.set_feature_paint_mode(False)
            else:
                feature_paint_btn = getattr(world_features_toolbar, 'feature_paint_btn', None)
                if feature_paint_btn and feature_paint_btn.isChecked():
                    feature_paint_btn.blockSignals(True)
                    feature_paint_btn.setChecked(False)
                    feature_paint_btn.blockSignals(False)
                    if hasattr(self, '_on_feature_paint_toggled'):
                        self._on_feature_paint_toggled('world', False)
        if hasattr(self, '_world_feature_paint'):
            self._world_feature_paint = False
        if hasattr(self, '_world_draw_mode') and getattr(self, '_world_draw_mode') == 'feature_paint':
            self._world_draw_mode = 'region_edit'
        if hasattr(self, '_set_path_details_mode'):
            self._set_path_details_mode('world', False)
        drawing_buttons = [
            getattr(self, 'world_draw_small_line_btn', None),
            getattr(self, 'world_draw_medium_line_btn', None),
            getattr(self, 'world_draw_big_line_btn', None),
            getattr(self, 'world_plot_setting_btn', None),
            getattr(self, 'world_plot_medium_location_btn', None),
            getattr(self, 'world_plot_large_location_btn', None)
        ]
        for btn in drawing_buttons:
            if btn and btn.isChecked():
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)
        self._set_draw_mode('world', 'none', False)
        self._world_draw_mode = 'region_edit'
        _init_region_masks(self)
        self._populate_region_selector()
        if hasattr(self, '_region_masks'):
            if not hasattr(self, '_region_border_cache'):
                self._region_border_cache = {}
            else:
                self._region_border_cache.clear()
            for region_name in self._region_masks.keys():
                update_region_border_cache(self, region_name)
        for widget in widgets_to_toggle:
            if widget:
                widget.setVisible(True)
        self._update_region_cursor_and_draw_mode()
        if hasattr(self, 'world_map_label') and self.world_map_label:
            QTimer.singleShot(50, self.world_map_label.update)
            QTimer.singleShot(200, self.world_map_label.update)
            QTimer.singleShot(500, self.world_map_label.update)
    else:
        setattr(self, '_region_edit_mode_active', False)
        if hasattr(self, 'world_map_label') and self.world_map_label:
            setattr(self.world_map_label, '_region_edit_mode_active', False)
        self._world_draw_mode = 'none'
        for widget in widgets_to_toggle:
            if widget:
                widget.setVisible(False)
        if hasattr(self, 'world_map_label') and self.world_map_label:
            if self.world_map_label._zoom_level > 0:
                self.world_map_label.setCursor(Qt.OpenHandCursor)
            else:
                self.world_map_label.setCursor(Qt.ArrowCursor)
    if hasattr(self, 'world_map_label') and self.world_map_label:
        self.world_map_label.update()

def _init_region_masks(self):
    if not hasattr(self, '_region_masks'):
        self._region_masks = {}
    if hasattr(self, 'world_map_label') and hasattr(self.world_map_label, '_crt_image') and self.world_map_label._crt_image:
        base_width = self.world_map_label._crt_image.width()
        base_height = self.world_map_label._crt_image.height()
    else:
        base_width = getattr(self.world_map_label, '_virtual_width', 1000) if hasattr(self, 'world_map_label') else 1000
        base_height = getattr(self.world_map_label, '_virtual_height', 1000) if hasattr(self, 'world_map_label') else 1000
    mask_scale = 1.0
    if max(base_width, base_height) < 2000:
        mask_scale = 2.0
    max_dimension = max(base_width, base_height)
    if max_dimension > 4000:
        mask_scale = 0.25
    if max_dimension > 6000:
        mask_scale = 0.125
    if max_dimension > 8000:
        mask_scale = 0.0625
    self._region_mask_scale = mask_scale
    mask_width = int(base_width * mask_scale)
    mask_height = int(base_height * mask_scale)
    mask_width = max(mask_width, 10)
    mask_height = max(mask_height, 10)
    if mask_width == 0 or mask_height == 0:
        return
    loaded_regions = set()
    if hasattr(self, 'workflow_data_dir') and self.current_world_name:
        world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
        region_resources_dir = os.path.join(world_dir, "resources", "regions")
        if not os.path.isdir(region_resources_dir):
            os.makedirs(region_resources_dir, exist_ok=True)
        elif os.path.isdir(region_resources_dir):
            mask_files = [f for f in os.listdir(region_resources_dir) if f.endswith('_region_mask.png')]
            from editor_panel.world_editor.world_editor_auto import sanitize_path_name
            for mask_file in mask_files:
                try:
                    sanitized_name_from_file = mask_file.replace('_region_mask.png', '')
                    region_folder_path = None
                    region_display_name = None
                    for folder_name in os.listdir(world_dir):
                        folder_path = os.path.join(world_dir, folder_name)
                        if os.path.isdir(folder_path):
                            if sanitize_path_name(folder_name).lower() == sanitized_name_from_file:
                                region_folder_path = folder_path
                                break
                    if region_folder_path:
                        json_file_name = f"{sanitized_name_from_file}_region.json"
                        json_path = os.path.join(region_folder_path, json_file_name)
                        if os.path.isfile(json_path):
                            region_data = self._load_json(json_path)
                            region_display_name = region_data.get('name')
                    if not region_display_name:
                        continue
                    else:
                        region_name = region_display_name
                    mask_path = os.path.join(region_resources_dir, mask_file)
                    from PyQt5.QtGui import QImage
                    loaded_mask = QImage(mask_path)
                    if not loaded_mask.isNull():
                        if loaded_mask.width() != mask_width or loaded_mask.height() != mask_height:
                            loaded_mask = loaded_mask.scaled(mask_width, mask_height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                        if loaded_mask.format() != QImage.Format_ARGB32:
                            loaded_mask = loaded_mask.convertToFormat(QImage.Format_ARGB32)
                        self._region_masks[region_name] = loaded_mask
                        loaded_regions.add(region_name)
                except Exception as e:
                    print(f"[ERROR] Failed to load region mask '{mask_file}': {str(e)}")
    valid_region_names = set(list(self._world_regions.keys()) + list(loaded_regions))
    for mask_region_name in list(self._region_masks.keys()):
        if mask_region_name not in valid_region_names:
            del self._region_masks[mask_region_name]
    for region_name in list(self._world_regions.keys()):
        if region_name in loaded_regions:
            continue
        existing_mask = self._region_masks.get(region_name)
        if existing_mask and not existing_mask.isNull() and \
            existing_mask.width() == mask_width and existing_mask.height() == mask_height:
            if existing_mask.format() != QImage.Format_ARGB32:
                self._region_masks[region_name] = existing_mask.convertToFormat(QImage.Format_ARGB32)
            continue
        else:
            mask = QImage(mask_width, mask_height, QImage.Format_ARGB32)
            mask.fill(QColor(0, 0, 0, 0))
            self._region_masks[region_name] = mask
            if self._world_regions.get(region_name):
                self._rebuild_region_mask_from_strokes(region_name)
                if hasattr(self, 'workflow_data_dir') and self.current_world_name:
                    world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
                    region_resources_dir = os.path.join(world_dir, "resources", "regions")
                    os.makedirs(region_resources_dir, exist_ok=True)
                    mask_filename = f"{region_name.replace(' ', '_').lower()}_region_mask.png"
                    mask_path = os.path.join(region_resources_dir, mask_filename)
                    self._region_masks[region_name].save(mask_path, "PNG")
    self._update_dots_region_assignments(update_files=True)
    if not hasattr(self, '_region_border_cache'):
        self._region_border_cache = {}
    for region_name in self._region_masks.keys():
        update_region_border_cache(self, region_name)

    if hasattr(self, '_world_draw_mode') and getattr(self, '_world_draw_mode') == 'region_edit':
        setattr(self, '_region_edit_mode_active', True)
        if hasattr(self, 'world_map_label') and self.world_map_label:
            setattr(self.world_map_label, '_region_edit_mode_active', True)
            setattr(self.world_map_label, '_show_region_fills', True)

def _populate_region_selector(self):
    if not self.current_world_name:
        return
    if not hasattr(self, 'world_region_selector') or self.world_region_selector is None:
        all_combos = self.findChildren(QComboBox)
        for combo in all_combos:
            if "RegionSelector" in combo.objectName():
                self.world_region_selector = combo
                break
        if self.world_region_selector is None:
            if hasattr(self, 'world_tab') and self.world_tab:
                world_toolbar = self.world_tab.findChild(QWidget, "WORLDToolbar")
                if world_toolbar:
                    region_selector = QComboBox(world_toolbar)
                    region_selector.setObjectName("WORLDToolbar_RegionSelector")
                    region_selector.currentIndexChanged.connect(self._on_region_selected)
                    world_toolbar_layout = world_toolbar.layout()
                    if world_toolbar_layout:
                        world_toolbar_layout.addWidget(region_selector)
                        self.world_region_selector = region_selector
    if not hasattr(self, 'world_region_selector') or self.world_region_selector is None:
        return
    self.world_region_selector.blockSignals(True)
    self.world_region_selector.clear()
    world_dir = os.path.join(self.workflow_data_dir, 'resources', 'data files', 'settings', self.current_world_name)
    regions = []
    if os.path.isdir(world_dir):
        for region_folder in os.listdir(world_dir):
            region_path = os.path.join(world_dir, region_folder)
            if os.path.isdir(region_path) and region_folder.lower() != 'resources':
                from editor_panel.world_editor.world_editor_auto import sanitize_path_name
                region_json = f"{sanitize_path_name(region_folder)}_region.json"
                region_json_path = os.path.join(region_path, region_json)
                if os.path.isfile(region_json_path):
                    try:
                        region_data = self._load_json(region_json_path)
                        display_name = region_data.get('name', region_folder.replace('_', ' ').title())
                        regions.append((display_name, region_folder))
                        print(f"Found region: {display_name} ({region_folder})")
                    except Exception as e:
                        print(f"Error loading region JSON {region_json_path}: {e}")
    else:
        print(f"World directory not found: {world_dir}")
    if not regions:
        self.world_region_selector.addItem("No regions available")
        self.world_region_selector.setEnabled(False)
        self._current_region_name = None
        print("No regions found to populate dropdown")
    else:
        self.world_region_selector.setEnabled(True)
        print("[DEBUG] Populating region selector with:")
        for display_name, folder_name in sorted(regions, key=lambda x: x[0]):
            self.world_region_selector.addItem(display_name)
            index = self.world_region_selector.count() - 1
            self.world_region_selector.setItemData(index, display_name, Qt.UserRole)
            print(f"  Index {index}: {display_name} -> {display_name}")
        try:
            self.world_region_selector.currentIndexChanged.disconnect()
        except Exception:
            pass
        self.world_region_selector.currentIndexChanged.connect(self._on_region_selected)
        if self._current_region_name:
            idx_found = False
            for i in range(self.world_region_selector.count()):
                if self.world_region_selector.itemData(i, Qt.UserRole) == self._current_region_name:
                    self.world_region_selector.setCurrentIndex(i)
                    idx_found = True
                    print(f"Selected previously selected region: {self._current_region_name}")
                    break
            if not idx_found and self.world_region_selector.count() > 0:
                self.world_region_selector.setCurrentIndex(0)
                self._current_region_name = self.world_region_selector.itemData(0, Qt.UserRole)
                print(f"Selected first region: {self._current_region_name}")
        elif self.world_region_selector.count() > 0:
            self.world_region_selector.setCurrentIndex(0)
            self._current_region_name = self.world_region_selector.itemData(0, Qt.UserRole)
            print(f"Selected first region by default: {self._current_region_name}")
    self.world_region_selector.blockSignals(False)
    if self._world_draw_mode == 'region_edit':
        self.world_region_selector.setVisible(True)
        if hasattr(self, 'world_region_selector_label') and self.world_region_selector_label:
            self.world_region_selector_label.setVisible(True)
        if hasattr(self, 'world_brush_size_label') and self.world_brush_size_label:
            self.world_brush_size_label.setVisible(True)
        if hasattr(self, 'world_brush_size_slider') and self.world_brush_size_slider:
            self.world_brush_size_slider.setVisible(True)

def _on_region_selected(self, index):
    if not hasattr(self, 'world_region_selector') or not self.world_region_selector or index < 0 or index >= self.world_region_selector.count():
        print("Invalid region selection")
        return
    data = self.world_region_selector.itemData(index, Qt.UserRole)
    if isinstance(data, str):
        self._current_region_name = data
        if not hasattr(self, '_world_regions'):
            self._world_regions = {}
        if self._current_region_name not in self._world_regions:
            self._world_regions[self._current_region_name] = []
        if not hasattr(self, '_region_masks'):
            self._region_masks = {}
        if self._current_region_name not in self._region_masks:
            width = 1000
            height = 1000
            if hasattr(self, 'world_map_label'):
                if hasattr(self.world_map_label, '_crt_image') and self.world_map_label._crt_image and not self.world_map_label._crt_image.isNull():
                    width = self.world_map_label._crt_image.width()
                    height = self.world_map_label._crt_image.height()
                elif hasattr(self.world_map_label, '_virtual_width'):
                    width = getattr(self.world_map_label, '_virtual_width', 1000)
                    height = getattr(self.world_map_label, '_virtual_height', 1000)
            mask_scale_factor = getattr(self, '_region_mask_scale', 1.0)
            scaled_width = int(width * mask_scale_factor)
            scaled_height = int(height * mask_scale_factor)
            scaled_width = max(1, scaled_width)
            scaled_height = max(1, scaled_height)
            mask_image = QImage(scaled_width, scaled_height, QImage.Format_ARGB32_Premultiplied)
            mask_image.fill(QColor(0, 0, 0, 0)) # transparent
            self._region_masks[self._current_region_name] = mask_image
        if self._current_region_name and self._current_region_name not in self._world_regions:
            self._world_regions[self._current_region_name] = []
        if hasattr(self, '_world_selected_item_type'):
            self._world_selected_item_type = 'region'
            self._world_selected_item_index = self._current_region_name
        if hasattr(self, 'world_map_label') and self.world_map_label:
            setattr(self.world_map_label, '_world_selected_item_type', 'region')
            setattr(self.world_map_label, '_world_selected_item_index', self._current_region_name)
            self.world_map_label.update()
        
def _on_brush_size_changed(self, value):
    self._region_brush_size = value
    
def _select_region_for_painting(self, region_name_to_select=None):
    self._populate_region_selector()
    if region_name_to_select and self.world_region_selector:
        found_idx = -1
        for i in range(self.world_region_selector.count()):
            if self.world_region_selector.itemData(i, Qt.UserRole) == region_name_to_select:
                found_idx = i
                break
        if found_idx != -1:
            self.world_region_selector.setCurrentIndex(found_idx)
            if hasattr(self, '_world_selected_item_type'):
                self._world_selected_item_type = 'region'
                self._world_selected_item_index = region_name_to_select
            if hasattr(self, 'world_map_label') and self.world_map_label:
                setattr(self.world_map_label, '_world_selected_item_type', 'region')
                setattr(self.world_map_label, '_world_selected_item_index', region_name_to_select)
                self.world_map_label.update()
    elif not self.world_region_selector:
        QMessageBox.warning(self, "Region Selection Error", "Region selector UI element not found.")
        if hasattr(self, 'world_region_edit_btn') and self.world_region_edit_btn:
            self.world_region_edit_btn.setChecked(False)

def paint_region_at(self, point, target_color=None, stroke_points=None, erase_mode=False):
    if not hasattr(self, '_region_masks'):
        self._region_masks = {}
    if not hasattr(self, '_region_fill_cache'):
        self._region_fill_cache = {}
    if not self._current_region_name:
        print("No region selected for painting")
        return point, []
    brush_size = getattr(self, '_region_brush_size', 5)
    mask_scale = getattr(self, '_region_mask_scale', 1.0)
    if self._current_region_name not in self._region_masks:
        img_w, img_h = 1000, 1000
        if hasattr(self, 'world_map_label'):
            if hasattr(self.world_map_label, '_crt_image') and self.world_map_label._crt_image:
                img_w = self.world_map_label._crt_image.width()
                img_h = self.world_map_label._crt_image.height()
            elif hasattr(self.world_map_label, '_virtual_width'):
                img_w = getattr(self.world_map_label, '_virtual_width', 1000)
                img_h = getattr(self.world_map_label, '_virtual_height', 1000)
        max_dimension = max(img_w, img_h)
        if max_dimension > 2000:
            mask_scale = min(mask_scale, 0.5)
        if max_dimension > 4000:
            mask_scale = min(mask_scale, 0.25)
        if max_dimension > 6000:
            mask_scale = min(mask_scale, 0.125)
        if max_dimension > 8000:
            mask_scale = min(mask_scale, 0.0625)
        if hasattr(self, '_region_mask_scale'):
            self._region_mask_scale = mask_scale
        mask_width = int(img_w * mask_scale)
        mask_height = int(img_h * mask_scale)
        mask_width = max(mask_width, 10)
        mask_height = max(mask_height, 10)
        mask = QImage(mask_width, mask_height, QImage.Format_ARGB32)
        mask.fill(QColor(0, 0, 0, 0))
        self._region_masks[self._current_region_name] = mask
    region_mask = self._region_masks[self._current_region_name]
    if self._current_region_name not in self._world_regions:
        self._world_regions[self._current_region_name] = []
    affected_regions = set()
    points_to_process = []
    if stroke_points:
        points_to_process = stroke_points
    else:
        points_to_process = [point]
    scaled_points = [(p[0] * mask_scale, p[1] * mask_scale) for p in points_to_process]
    scaled_brush_size = brush_size * mask_scale
    scaled_brush_size = max(1.0, scaled_brush_size)
    min_x_stroke, min_y_stroke, max_x_stroke, max_y_stroke = float('inf'), float('inf'), float('-inf'), float('-inf')
    if scaled_points:
        for x, y in scaled_points:
            min_x_stroke = min(min_x_stroke, x - scaled_brush_size/2)
            min_y_stroke = min(min_y_stroke, y - scaled_brush_size/2)
            max_x_stroke = max(max_x_stroke, x + scaled_brush_size/2)
            max_y_stroke = max(max_y_stroke, y + scaled_brush_size/2)
        stroke_margin = max(5, scaled_brush_size / 2)
        min_x_stroke = max(0, int(min_x_stroke - stroke_margin))
        min_y_stroke = max(0, int(min_y_stroke - stroke_margin))
        max_x_stroke = min(region_mask.width() - 1, int(max_x_stroke + stroke_margin))
        max_y_stroke = min(region_mask.height() - 1, int(max_y_stroke + stroke_margin))
        stroke_update_rect = (min_x_stroke, min_y_stroke, max_x_stroke, max_y_stroke)
    else:
        stroke_update_rect = None
    try:
        import numpy as np
        import cv2
        stroke_mask = np.zeros((region_mask.height(), region_mask.width()), dtype=np.uint8)
        if len(scaled_points) > 1:
            for i in range(len(scaled_points) - 1):
                x1 = int(scaled_points[i][0])
                y1 = int(scaled_points[i][1])
                x2 = int(scaled_points[i+1][0])
                y2 = int(scaled_points[i+1][1])
                pt1 = (x1, y1)
                pt2 = (x2, y2)
                cv2.line(stroke_mask, pt1, pt2, 255, int(scaled_brush_size))
            for x, y in scaled_points:
                cv2.circle(stroke_mask, (int(x), int(y)), int(scaled_brush_size/2), 255, -1)
        else:
            for x, y in scaled_points:
                cv2.circle(stroke_mask, (int(x), int(y)), int(scaled_brush_size/2), 255, -1)
        kernel = np.ones((3, 3), np.uint8)
        dilated_stroke = cv2.dilate(stroke_mask, kernel, iterations=1)
        if not erase_mode:
            for other_region_name, other_region_mask in self._region_masks.items():
                if other_region_name != self._current_region_name and \
                   other_region_mask.width() == region_mask.width() and \
                   other_region_mask.height() == region_mask.height():
                    other_bits = other_region_mask.bits()
                    other_bits.setsize(other_region_mask.byteCount())
                    other_array = np.frombuffer(other_bits, dtype=np.uint8).reshape((other_region_mask.height(), other_region_mask.width(), 4))
                    other_array[dilated_stroke > 0, 3] = 0
                    modified_mask = QImage(other_array.data, other_region_mask.width(), other_region_mask.height(), QImage.Format_ARGB32)
                    modified_mask.bits()
                    self._region_masks[other_region_name] = modified_mask
                    affected_regions.add(other_region_name)
    except (ImportError, Exception) as e:
        if not erase_mode:
            for other_region_name, other_region_mask in self._region_masks.items():
                if other_region_name != self._current_region_name:
                    clear_painter = QPainter(other_region_mask)
                    clear_painter.setRenderHint(QPainter.Antialiasing, True)
                    clear_painter.setCompositionMode(QPainter.CompositionMode_Clear)
                    clearance_margin = 1
                    clearing_brush_size = scaled_brush_size + clearance_margin
                    if len(scaled_points) > 1:
                        path = QPainterPath()
                        path.moveTo(scaled_points[0][0], scaled_points[0][1])
                        for i in range(1, len(scaled_points)):
                            path.lineTo(scaled_points[i][0], scaled_points[i][1])
                        clear_pen = QPen(Qt.black, clearing_brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                        clear_painter.setPen(clear_pen)
                        clear_painter.setBrush(Qt.NoBrush)
                        clear_painter.drawPath(path)
                    elif scaled_points:
                        x, y = scaled_points[0]
                        clear_painter.setPen(Qt.NoPen)
                        clear_painter.setBrush(QBrush(Qt.black))
                        clear_painter.drawEllipse(QRectF(
                            x - clearing_brush_size/2, 
                            y - clearing_brush_size/2, 
                            clearing_brush_size, 
                            clearing_brush_size
                        ))               
                    clear_painter.end()
                    affected_regions.add(other_region_name)
    if not erase_mode:
        for point in points_to_process:
            self._world_regions[self._current_region_name].append((point[0], point[1], brush_size))
    else:
        if hasattr(self, '_region_modified'):
            self._region_modified = True
        if not hasattr(self, '_was_erasing_region'):
            self._was_erasing_region = {}
        self._was_erasing_region[self._current_region_name] = True
    painter = QPainter(region_mask)
    painter.setRenderHint(QPainter.Antialiasing, True)
    if erase_mode:
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        brush_color = QColor(0, 0, 0, 255)
    else:
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        base_color_str = self.theme_colors.get("base_color", "#00A0A0")
        brush_color = QColor(base_color_str)
        brush_color.setAlpha(128)
    painter.setBrush(QBrush(brush_color))
    if len(scaled_points) > 1:
        path = QPainterPath()
        path.moveTo(scaled_points[0][0], scaled_points[0][1])
        for i in range(1, len(scaled_points)):
            path.lineTo(scaled_points[i][0], scaled_points[i][1])
        pen = QPen(brush_color, scaled_brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)
    elif scaled_points:
        x, y = scaled_points[0]
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(
            x - scaled_brush_size/2, 
            y - scaled_brush_size/2, 
            scaled_brush_size, 
            scaled_brush_size
        ))
    painter.end()
    affected_regions.add(self._current_region_name)
    for region_name_iter in affected_regions:
        if erase_mode and region_name_iter == self._current_region_name:
            update_region_border_cache(self, region_name_iter)
        else:
            current_iter_update_rect = stroke_update_rect if region_name_iter == self._current_region_name else None
            _update_region_border_cache_optimized(
                self, 
                region_name_iter, 
                current_iter_update_rect, 
                simplified_from_caller=True
            )
        if region_name_iter == self._current_region_name:
            setattr(self, f"_region_just_painted_ultra_{region_name_iter}", True)
            setattr(self, f"_region_painted_ultra_time_{region_name_iter}", time.time())
    setattr(self, f"_border_cache_updated_{self._current_region_name}", True)
    if points_to_process:
        return points_to_process[-1], list(affected_regions)
    return point, list(affected_regions)

def _update_region_border_cache_optimized(self, region_name, visible_area=None, simplified_from_caller=False):
    if not hasattr(self, '_region_masks') or region_name not in self._region_masks:
        if hasattr(self, '_region_border_cache'): self._region_border_cache[region_name] = []
        return
    mask_qimage = self._region_masks[region_name]
    w_full, h_full = mask_qimage.width(), mask_qimage.height()
    if mask_qimage.isNull() or w_full <= 1 or h_full <= 1:
        if hasattr(self, '_region_border_cache'): self._region_border_cache[region_name] = []
        return
    if not hasattr(self, '_region_border_cache'): self._region_border_cache = {}
    actual_ultra_mode = False
    actual_zoom_simplified_mode = False
    ultra_flag_key = f"_region_just_painted_ultra_{region_name}"
    ultra_time_key = f"_region_painted_ultra_time_{region_name}"
    if getattr(self, ultra_flag_key, False):
        if time.time() - getattr(self, ultra_time_key, 0) < 0.5:
            actual_ultra_mode = True
        else:
            setattr(self, ultra_flag_key, False)
    if not actual_ultra_mode and simplified_from_caller:
        actual_zoom_simplified_mode = True
    try:
        import cv2
        import numpy as np
        mask_bits = mask_qimage.bits()
        mask_bits.setsize(mask_qimage.byteCount())
        mask_array_rgba = np.frombuffer(mask_bits, dtype=np.uint8).reshape((h_full, w_full, 4))
        alpha_channel_full = mask_array_rgba[..., 3]
        _, binary_mask_full = cv2.threshold(alpha_channel_full, 10, 255, cv2.THRESH_BINARY)
        if not np.any(binary_mask_full > 0):
            self._region_border_cache[region_name] = []
            return
            
        process_binary_mask = binary_mask_full
        offset_x, offset_y = 0, 0
        if visible_area and len(visible_area) == 4:
            x1, y1, x2, y2 = map(int, visible_area)
            margin = 10
            x1 = max(0, x1 - margin); y1 = max(0, y1 - margin)
            x2 = min(w_full, x2 + margin); y2 = min(h_full, y2 + margin)
            if x1 < x2 and y1 < y2:
                process_binary_mask = binary_mask_full[y1:y2, x1:x2]
                offset_x, offset_y = x1, y1
                
        if not np.any(process_binary_mask):
            if not visible_area: self._region_border_cache[region_name] = []
            return
        kernel_size = 2
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        morph_iterations = 2
        processed = cv2.morphologyEx(process_binary_mask, cv2.MORPH_CLOSE, kernel, iterations=morph_iterations)
        if actual_ultra_mode:
            contour_finding_method = cv2.CHAIN_APPROX_SIMPLE
        else:
            contour_finding_method = cv2.CHAIN_APPROX_TC89_L1
        contours, hierarchy = cv2.findContours(processed, cv2.RETR_LIST, contour_finding_method)
        
        normalized_contours = []
        min_final_points = 3
        
        for contour_in_roi in contours:
            contour_full_coords = contour_in_roi + np.array([offset_x, offset_y]).reshape(1,1,2)
            arc_length = cv2.arcLength(contour_full_coords, True)
            min_arc_len = 5
            if arc_length < min_arc_len: continue
            current_approx = contour_full_coords
            if actual_ultra_mode:
                epsilon = 0.0001 * arc_length
                current_approx = cv2.approxPolyDP(current_approx, epsilon, True)
                if len(current_approx) > 60:
                    current_approx = cv2.approxPolyDP(current_approx, 0.0005 * arc_length, True)
            elif actual_zoom_simplified_mode:
                epsilon = 0.00005 * arc_length
                current_approx = cv2.approxPolyDP(current_approx, epsilon, True)
                if len(current_approx) > 100:
                    current_approx = cv2.approxPolyDP(current_approx, 0.0002 * arc_length, True)
            else:
                epsilon = 0.00002 * arc_length
                current_approx = cv2.approxPolyDP(current_approx, epsilon, True)
                if len(current_approx) > 250:
                    current_approx = cv2.approxPolyDP(current_approx, 0.00005 * arc_length, True)
            if len(current_approx) < min_final_points: continue
            norm_points = [(pt[0][0] / w_full, pt[0][1] / h_full) for pt in current_approx]
            normalized_contours.append(norm_points)
        self._region_border_cache[region_name] = normalized_contours
        if not actual_ultra_mode:
             setattr(self, f"_last_border_cache_time_{region_name}", time.time())
             
        total_points = sum(len(c) for c in normalized_contours)
        percent_of_mask = (total_points / (w_full * h_full) * 100) if w_full * h_full > 0 else 0
        mode_str = "ULTRA (Post-Paint)" if actual_ultra_mode else ("ZoomSimplified" if actual_zoom_simplified_mode else "Normal")
        
    except ImportError:
        update_region_border_cache(self, region_name, visible_area)
    except Exception as e:
        print(f"Error in _update_region_border_cache_optimized for '{region_name}': {e}")
        import traceback
        traceback.print_exc()
        update_region_border_cache(self, region_name, visible_area)

def mouseReleaseEvent(self, event):
    if self._painting_active and self._stroke_points:
        try:
            end_pt, cleared_regions = self.paint_region_at(event.pos(), stroke_points=self._stroke_points)
            region_processing_active = getattr(self, '_region_processing_active', False)
            if region_processing_active:
                self._painting_active = False
                self._stroke_points = []
                self.releaseMouse()
                return
            self._region_processing_active = True
            visible_mask_area = None
            if hasattr(self, 'world_map_label') and self.world_map_label:
                try:
                    visible_rect_img_coords = self.world_map_label._get_image_rect()
                    if visible_rect_img_coords:
                        mask_scale = getattr(self, '_region_mask_scale', 1.0)
                        visible_mask_area = (
                            int(visible_rect_img_coords.x() * mask_scale),
                            int(visible_rect_img_coords.y() * mask_scale),
                            int((visible_rect_img_coords.x() + visible_rect_img_coords.width()) * mask_scale),
                            int((visible_rect_img_coords.y() + visible_rect_img_coords.height()) * mask_scale)
                        )
                except Exception as e:
                    print(f"Error calculating visible mask area: {e}")
            user_zoom_factor = 1.0
            if hasattr(self, 'world_map_label'):
                user_zoom_factor = getattr(self.world_map_label, '_zoom_step_factor', 1.15) ** \
                                 getattr(self.world_map_label, '_zoom_level', 0)
            timer_delay = 100
            if user_zoom_factor < 0.25: timer_delay = 300
            elif user_zoom_factor < 0.5: timer_delay = 200
                
            def update_borders_timed():
                try:
                    current_region_name = self._current_region_name 
                    if not current_region_name: 
                        self._region_processing_active = False
                        return
                    region_names_to_update = list(self._region_masks.keys()) if hasattr(self, '_region_masks') else []
                    is_zoomed_out_simplified = user_zoom_factor < 0.25
                    for region_name in region_names_to_update:
                        _update_region_border_cache_optimized(
                            self.parent_editor,
                            region_name,
                            visible_mask_area, 
                            simplified_from_caller=is_zoomed_out_simplified
                        )
                    if hasattr(self, 'world_map_label') and self.world_map_label:
                        setattr(self.world_map_label, '_region_edit_mode_active', True)
                    if user_zoom_factor > 0.25 and hasattr(self, '_update_dots_region_assignments'):
                        self._update_dots_region_assignments(visible_mask_area, update_files=True)
                        if hasattr(self, '_dots_modified') and self._dots_modified:
                            if hasattr(self, '_save_world_map_data'):
                                QTimer.singleShot(300, self._save_world_map_data)
                            self._dots_modified = False
                except Exception as e:
                    print(f"Error in timed border processing: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    self._region_processing_active = False
                    if hasattr(self, 'world_map_label') and self.world_map_label:
                        self.world_map_label.update()
            QTimer.singleShot(timer_delay, update_borders_timed)
        except Exception as e:
            print(f"Error in mouse release: {e}")
            import traceback
            traceback.print_exc()
            self._region_processing_active = False
        if hasattr(self, 'world_map_label') and self.world_map_label:
            self.world_map_label.update()
        self.update()
    self._painting_active = False
    self._stroke_points = []
    self.releaseMouse()


def _render_region_borders(self, painter, visible_rect=None):
    if not self.parent_editor or not hasattr(self.parent_editor, '_region_border_cache'):
        return
    region_edit_active = getattr(self, '_region_edit_mode_active', False)
    if not region_edit_active and not getattr(self, '_show_region_fills', True) and not self._dragging and self.parent_editor._world_draw_mode != 'region_edit':
        return
    user_zoom_factor = self._zoom_step_factor ** self._zoom_level
    extremely_low_zoom = user_zoom_factor < 0.2
    low_zoom = user_zoom_factor < 0.5
    render_budget = 2000 if extremely_low_zoom else (5000 if low_zoom else 15000)
    rendered_point_count = 0
    border_cache = self.parent_editor._region_border_cache
    if not border_cache:
        return
    region_names = list(border_cache.keys())
    if not region_names:
        return
    selected_region = None
    if region_edit_active: 
        if hasattr(self, '_world_selected_item_type') and self._world_selected_item_type == 'region':
            selected_region = getattr(self, '_world_selected_item_index', None)
    prioritized_regions = []
    if selected_region and selected_region in region_names:
        prioritized_regions.append(selected_region)
        region_names.remove(selected_region)
    if not extremely_low_zoom:
        painter.setRenderHint(QPainter.Antialiasing, True)
    else:
        painter.setRenderHint(QPainter.Antialiasing, False)
    if extremely_low_zoom and visible_rect:
        if self._crt_image:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
        else:
            img_w, img_h = self._virtual_width, self._virtual_height
        for region_name in prioritized_regions + region_names:
            if region_name not in border_cache:
                continue
            contour_groups = border_cache[region_name]
            if not contour_groups:
                continue
            name_hash = sum(ord(c) for c in region_name) if region_name else 0
            hue = (name_hash % 360) / 360.0
            if region_name == selected_region:
                color = QColor.fromHsvF(hue, 0.7, 0.9, 0.5)
            else:
                color = QColor.fromHsvF(hue, 0.6, 0.8, 0.3)
            all_x, all_y = [], []
            for contour in contour_groups:
                for px, py in contour:
                    all_x.append(px * img_w)
                    all_y.append(py * img_h)
            if all_x and all_y:
                min_x, max_x = min(all_x), max(all_x)
                min_y, max_y = min(all_y), max(all_y)
                rect_tl = self._image_to_widget_coords((min_x, min_y))
                rect_br = self._image_to_widget_coords((max_x, max_y))
                if rect_tl and rect_br:
                    rect = QRectF(rect_tl.x(), rect_tl.y(), rect_br.x() - rect_tl.x(), rect_br.y() - rect_tl.y())
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(color))
                    painter.drawRect(rect)
                    center_x = (rect_tl.x() + rect_br.x()) / 2
                    center_y = (rect_tl.y() + rect_br.y()) / 2
                    painter.setPen(QPen(QColor.fromHsvF(hue, 0.9, 0.9), 2))
                    painter.drawEllipse(QPointF(center_x, center_y), 4, 4)
        return
    for region_name in prioritized_regions + region_names:
        if rendered_point_count >= render_budget:
            break
        if region_name not in border_cache:
            continue
        contour_groups = border_cache[region_name]
        if not contour_groups:
            continue
        if self._crt_image:
            img_w, img_h = self._crt_image.width(), self._crt_image.height()
        else:
            img_w, img_h = self._virtual_width, self._virtual_height
        name_hash = sum(ord(c) for c in region_name) if region_name else 0
        hue = (name_hash % 360) / 360.0
        region_path = QPainterPath()
        contour_added = False
        MAX_ABS_WIDGET_COORD = 500000.0
        for contour_points in contour_groups:
            if len(contour_points) < 3:
                continue
            skip_factor = 1
            if low_zoom:
                num_points = len(contour_points)
                if num_points > 1000: skip_factor = 15
                elif num_points > 500: skip_factor = 8
                elif num_points > 250: skip_factor = 5
                elif num_points > 100: skip_factor = 3
                else: skip_factor = 2
            num_points_to_use = len(contour_points) // skip_factor
            if rendered_point_count + num_points_to_use > render_budget:
                if not contour_added and len(contour_groups) == 1:
                    num_simplified_pts = min(max(30, int(render_budget * 0.1)), len(contour_points))
                    indices = np.linspace(0, len(contour_points)-1, num_simplified_pts, dtype=int)
                    simple_points = [contour_points[i] for i in indices]
                    first_point = True
                    for norm_x, norm_y in simple_points:
                        img_x = norm_x * img_w
                        img_y = norm_y * img_h
                        widget_pos = self._image_to_widget_coords((img_x, img_y))
                        if not widget_pos: continue
                        clamped_x = max(-MAX_ABS_WIDGET_COORD, min(widget_pos.x(), MAX_ABS_WIDGET_COORD))
                        clamped_y = max(-MAX_ABS_WIDGET_COORD, min(widget_pos.y(), MAX_ABS_WIDGET_COORD))
                        current_point_for_path = QPointF(clamped_x, clamped_y)
                        if first_point:
                            region_path.moveTo(current_point_for_path)
                            first_point = False
                        else:
                            region_path.lineTo(current_point_for_path)
                    if not first_point:
                        region_path.closeSubpath()
                        contour_added = True
                        rendered_point_count += len(simple_points)
                    continue
                else:
                    continue
            first_point = True
            points_used = 0
            num_non_prioritized_regions = len(region_names)
            if num_non_prioritized_regions == 0:
                point_limit_for_this_contour = render_budget * 2
            else:
                point_limit_for_this_contour = render_budget // num_non_prioritized_regions
            visible_margin = visible_rect.width() * 0.3 if visible_rect else 0
            for i in range(0, len(contour_points), skip_factor):
                if points_used >= point_limit_for_this_contour: break
                if i >= len(contour_points): break
                norm_x, norm_y = contour_points[i]
                img_x = norm_x * img_w
                img_y = norm_y * img_h
                if visible_rect:
                    if (img_x < visible_rect.x() - visible_margin or 
                        img_x > visible_rect.x() + visible_rect.width() + visible_margin or
                        img_y < visible_rect.y() - visible_margin or 
                        img_y > visible_rect.y() + visible_rect.height() + visible_margin):
                        continue
                widget_pos = self._image_to_widget_coords((img_x, img_y))
                if not widget_pos: continue
                clamped_x = max(-MAX_ABS_WIDGET_COORD, min(widget_pos.x(), MAX_ABS_WIDGET_COORD))
                clamped_y = max(-MAX_ABS_WIDGET_COORD, min(widget_pos.y(), MAX_ABS_WIDGET_COORD))
                current_point_for_path = QPointF(clamped_x, clamped_y)
                if first_point:
                    region_path.moveTo(current_point_for_path)
                    first_point = False
                else:
                    region_path.lineTo(current_point_for_path)
                points_used += 1
            if not first_point:
                region_path.closeSubpath()
                contour_added = True
                rendered_point_count += points_used
        if contour_added:
            painter.setBrush(Qt.NoBrush)
            ui_color_str = self.parent_editor.theme_colors.get("base_color", "#00A0A0")
            ui_color = QColor(ui_color_str)
            if region_name == selected_region:
                line_width = 3.5 if user_zoom_factor > 0.3 else 2.5
                highlight_color = QColor(ui_color.lighter(140))
                highlight_color.setAlpha(240)
                pen = QPen(highlight_color, line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            else:
                line_width = 2 if user_zoom_factor > 0.3 else 1.5
                normal_color = QColor(ui_color)
                normal_color.setAlpha(200)
                pen = QPen(normal_color, line_width, Qt.DotLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawPath(region_path)
            if contour_groups:
                all_x, all_y = [], []
                for contour in contour_groups:
                    for px, py in contour:
                        img_x = px * img_w
                        img_y = py * img_h
                        if visible_rect:
                            margin = visible_rect.width() * 0.3
                            if (img_x < visible_rect.x() - margin or 
                                img_x > visible_rect.x() + visible_rect.width() + margin or
                                img_y < visible_rect.y() - margin or 
                                img_y > visible_rect.y() + visible_rect.height() + margin):
                                continue
                        all_x.append(img_x)
                        all_y.append(img_y)
                if all_x and all_y:
                    centroid_x = sum(all_x) / len(all_x)
                    centroid_y = sum(all_y) / len(all_y)
                    widget_centroid = self._image_to_widget_coords((centroid_x, centroid_y))
                    if widget_centroid:
                        region_bbox_w = max(all_x) - min(all_x)
                        region_bbox_h = max(all_y) - min(all_y)
                        if region_bbox_w * user_zoom_factor > 40 and region_bbox_h * user_zoom_factor > 20:
                            if region_name == selected_region:
                                pass
                            label = str(region_name)
                            if '_' in label:
                                parts = label.split('_')
                                if len(parts) == 2 and parts[1].isdigit():
                                    label = f"{parts[0].capitalize()} {parts[1]}"
                                else:
                                    label = ' '.join(part.capitalize() for part in parts)
                            else:
                                label = label.capitalize()

def update_region_border_cache(self, region_name, visible_area=None):
    import numpy as np
    import cv2
    if not hasattr(self, '_region_masks') or region_name not in self._region_masks:
        self._region_border_cache[region_name] = []
        return
    mask_qimage = self._region_masks[region_name]
    w, h = mask_qimage.width(), mask_qimage.height()
    if w <= 1 or h <= 1 or mask_qimage.isNull():
        self._region_border_cache[region_name] = []
        return
    current_time = time.time()
    cache_time_key = f"_last_border_cache_time_{region_name}"
    last_cache_time = getattr(self, cache_time_key, 0)
    is_current_region = region_name == getattr(self, '_current_region_name', '')
    min_update_interval = 0.1 if is_current_region else 1.0
    if visible_area and current_time - last_cache_time < min_update_interval:
        return
    setattr(self, cache_time_key, current_time)
    try:
        if mask_qimage.format() != QImage.Format_ARGB32:
            mask_qimage = mask_qimage.convertToFormat(QImage.Format_ARGB32)
            self._region_masks[region_name] = mask_qimage
        expected_bytes = w * h * 4
        actual_bytes = mask_qimage.byteCount()
        if expected_bytes != actual_bytes:
            self._region_border_cache[region_name] = []
            return
        mask_bits = mask_qimage.bits()
        mask_bits.setsize(mask_qimage.byteCount())
        mask_array_rgba = np.frombuffer(mask_bits, dtype=np.uint8).reshape((h, w, 4))
        alpha_channel = mask_array_rgba[..., 3]
        _, current_binary = cv2.threshold(alpha_channel, 10, 255, cv2.THRESH_BINARY)
        if not np.any(current_binary > 0):
            self._region_border_cache[region_name] = []
            return
        if visible_area and len(visible_area) == 4:
            margin = 50
            x1 = max(0, visible_area[0] - margin)
            y1 = max(0, visible_area[1] - margin)
            x2 = min(w, visible_area[2] + margin)
            y2 = min(h, visible_area[3] + margin)
            if x1 < x2 and y1 < y2:
                roi_binary = current_binary[y1:y2, x1:x2]
                if np.any(roi_binary > 0):
                    kernel = np.ones((3, 3), np.uint8)
                    processed_roi = cv2.morphologyEx(roi_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
                    contours, hierarchy = cv2.findContours(processed_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
                    all_contours_points = []
                    min_contour_length = 5
                    for contour in contours:
                        if len(contour) < min_contour_length:
                            continue
                        adjusted_contour = contour.copy()
                        adjusted_contour[:, :, 0] += x1
                        adjusted_contour[:, :, 1] += y1
                        arc_length = cv2.arcLength(adjusted_contour, True)
                        epsilon = 0.00005 * arc_length
                        approx = cv2.approxPolyDP(adjusted_contour, epsilon, True)
                        contour_points = [(pt[0][0] / w, pt[0][1] / h) for pt in approx]
                        all_contours_points.append(contour_points)
                    if all_contours_points:
                        self._region_border_cache[region_name] = all_contours_points
                        return
                else:
                    self._region_border_cache[region_name] = []
                    return
        processed_mask = current_binary.copy()
        kernel = np.ones((3, 3), np.uint8)
        processed_mask = cv2.morphologyEx(processed_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, hierarchy = cv2.findContours(processed_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_L1)
        all_contours_points = []
        min_contour_length = 5
        max_points_per_contour = 500
        for contour in contours:
            if len(contour) < min_contour_length:
                continue
            arc_length = cv2.arcLength(contour, True)
            if arc_length < 10:
                continue
            epsilon = 0.00005 * arc_length
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) > max_points_per_contour:
                epsilon = 0.0001 * arc_length
                approx = cv2.approxPolyDP(contour, epsilon, True)
            contour_points = [(pt[0][0] / w, pt[0][1] / h) for pt in approx]
            all_contours_points.append(contour_points)
        self._region_border_cache[region_name] = all_contours_points
    except Exception as e:
        self._region_border_cache[region_name] = []