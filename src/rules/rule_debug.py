from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QSizePolicy, QHBoxLayout, QLabel, QFrame, QListWidgetItem, QTextEdit
from PyQt5.QtCore import Qt

class RuleDebugWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RuleDebugWidget")
        self._answers_by_rule_id = {}
        self.posts_list_widget = QListWidget()
        self.posts_list_widget.setObjectName("DebugPostsList")
        self.posts_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.posts_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.posts_list_widget.setFocusPolicy(Qt.StrongFocus)
        self.posts_list_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.posts_list_widget.setMinimumHeight(60)
        self.posts_list_widget.setMaximumHeight(140)
        self.rules_list_widget = QListWidget()
        self.rules_list_widget.setObjectName("DebugRulesList")
        self.rules_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.rules_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rules_list_widget.setFocusPolicy(Qt.NoFocus)
        self.rules_list_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(self.posts_list_widget, 0)
        left_layout.addWidget(self.rules_list_widget, 1)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(8)
        self.post_text_label = QLabel("")
        self.post_text_label.setObjectName("DebugPostLabel")
        self.post_text_label.setWordWrap(True)
        right_layout.addWidget(self.post_text_label)
        self.description_label = QLabel("")
        self.description_label.setObjectName("DebugDescriptionLabel")
        self.description_label.setWordWrap(True)
        right_layout.addWidget(self.description_label)
        self.conditions_title = QLabel("Conditions")
        self.conditions_title.setObjectName("DebugSectionTitle")
        self.conditions_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.actions_title = QLabel("Actions")
        self.actions_title.setObjectName("DebugSectionTitle")
        self.actions_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.conditions_container = QWidget()
        self.conditions_container.setObjectName("DebugConditionsContainer")
        self.conditions_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.conditions_layout = QVBoxLayout(self.conditions_container)
        self.conditions_layout.setContentsMargins(6, 6, 6, 6)
        self.conditions_layout.setSpacing(6)
        self.answer_box = QTextEdit()
        self.answer_box.setObjectName("DebugAnswerBox")
        self.answer_box.setReadOnly(True)
        self.answer_box.setVisible(False)
        self.tag_badge = QLabel("")
        self.tag_badge.setObjectName("DebugTagBadge")
        self.tag_badge.setVisible(False)
        answer_row = QHBoxLayout()
        answer_row.setContentsMargins(0, 0, 0, 0)
        answer_row.setSpacing(6)
        answer_row.addWidget(self.answer_box, 1)
        answer_row.addWidget(self.tag_badge, 0)
        self.conditions_layout.addLayout(answer_row)
        self.actions_container = QWidget()
        self.actions_container.setObjectName("DebugActionsContainer")
        self.actions_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.actions_layout = QVBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(6, 6, 6, 6)
        self.actions_layout.setSpacing(6)
        conditions_header = QHBoxLayout()
        conditions_header.setContentsMargins(0, 0, 0, 0)
        conditions_header.addWidget(self.conditions_title)
        actions_header = QHBoxLayout()
        actions_header.setContentsMargins(0, 0, 0, 0)
        actions_header.addWidget(self.actions_title)
        top_wrapper = QWidget()
        top_layout = QVBoxLayout(top_wrapper)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(4)
        top_layout.addLayout(conditions_header)
        line1 = QFrame()
        line1.setObjectName("DebugDivider")
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        top_layout.addWidget(line1)
        top_layout.addWidget(self.conditions_container, 1)
        bottom_wrapper = QWidget()
        bottom_layout = QVBoxLayout(bottom_wrapper)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(4)
        bottom_layout.addLayout(actions_header)
        line2 = QFrame()
        line2.setObjectName("DebugDivider")
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        bottom_layout.addWidget(line2)
        bottom_layout.addWidget(self.actions_container, 1)
        right_layout.addWidget(top_wrapper, 1)
        right_layout.addWidget(bottom_wrapper, 1)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        left_panel.setMinimumWidth(240)
        left_panel.setMaximumWidth(420)
        main_layout.addWidget(left_panel, 0)
        main_layout.addWidget(right_panel, 1)
        self.setLayout(main_layout)
        self.rules_list_widget.itemSelectionChanged.connect(self._on_rule_selection_changed)
        self.posts_list_widget.itemSelectionChanged.connect(self._on_post_selection_changed)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.posts_list_widget.hasFocus():
            self.posts_list_widget.clearSelection()
            for i in range(self.rules_list_widget.count()):
                self.rules_list_widget.item(i).setHidden(False)
            self.post_text_label.setText("")
            event.accept()
            return
        super().keyPressEvent(event)

    def _clear_layout(self, layout):
        if not layout:
            return
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def _rule_could_apply_to_post(self, rule, post_role, post_character_name):
        applies_to = rule.get('applies_to', 'Narrator')
        if post_role == 'user':
            return True
        if post_role == 'assistant':
            if post_character_name and post_character_name.strip().lower() != 'narrator':
                if applies_to != 'Character':
                    return False
                target_name = rule.get('character_name')
                if target_name and target_name.strip():
                    return target_name.strip().lower() == post_character_name.strip().lower()
                return True
            else:
                return applies_to != 'Character'
        return True

    def _on_post_selection_changed(self):
        item = self.posts_list_widget.currentItem()
        if not item:
            return
        post_data = item.data(Qt.UserRole) or {}
        full_text = post_data.get('full_text') or item.text()
        self.post_text_label.setText(full_text)
        post_role = post_data.get('role')
        post_character = post_data.get('character_name')
        current_item = self.rules_list_widget.currentItem()
        current_rule_id = current_item.data(Qt.UserRole).get('id') if current_item and isinstance(current_item.data(Qt.UserRole), dict) else None
        self.rules_list_widget.blockSignals(True)
        try:
            for i in range(self.rules_list_widget.count()):
                rule_item = self.rules_list_widget.item(i)
                rule = rule_item.data(Qt.UserRole)
                should_hide = isinstance(rule, dict) and not self._rule_could_apply_to_post(rule, post_role, post_character)
                if current_rule_id and isinstance(rule, dict) and rule.get('id') == current_rule_id:
                    should_hide = False
                rule_item.setHidden(should_hide)
        finally:
            self.rules_list_widget.blockSignals(False)

    def _on_rule_selection_changed(self):
        item = self.rules_list_widget.currentItem()
        if not item:
            return
        rule = item.data(Qt.UserRole)
        if not isinstance(rule, dict):
            return
        self._clear_layout(self.conditions_layout)
        self._clear_layout(self.actions_layout)
        self.answer_box.setParent(None)
        self.tag_badge.setParent(None)
        desc = rule.get('description', '') or ''
        self.description_label.setText(desc)
        question_text = rule.get('condition', '')
        if question_text:
            title = QLabel("Question:")
            title.setObjectName("DebugFieldLabel")
            value = QLabel(question_text)
            value.setObjectName("DebugFieldValue")
            value.setWordWrap(True)
            self.conditions_layout.addWidget(title)
            self.conditions_layout.addWidget(value)
        answer_row = QHBoxLayout()
        answer_row.setContentsMargins(0, 0, 0, 0)
        answer_row.setSpacing(6)
        answer_row.addWidget(self.answer_box, 1)
        answer_row.addWidget(self.tag_badge, 0)
        self.conditions_layout.addLayout(answer_row)
        self.answer_box.clear()
        self.tag_badge.clear()
        rid = rule.get('id')
        saved = self._answers_by_rule_id.get(rid)
        if saved and isinstance(saved, dict):
            txt = saved.get('text')
            if txt is None:
                txt = ""
            tag = saved.get('tag') or None
            display_text = txt if len(txt) > 0 else "[NO RESPONSE]"
            self.answer_box.setPlainText(display_text)
            self.answer_box.setVisible(True)
            if tag:
                self.tag_badge.setText(tag)
                self.tag_badge.setVisible(True)
            else:
                self.tag_badge.setVisible(False)
        else:
            self.answer_box.setPlainText("")
            self.answer_box.setVisible(True)
            self.tag_badge.setVisible(False)

    def on_rule_answer(self, rule, result_text, matched_tag=None):
        rid = rule.get('id') if isinstance(rule, dict) else None
        if not rid:
            return
        tag_text = matched_tag
        if not tag_text and isinstance(rule, dict):
            for pair in rule.get('tag_action_pairs', []) or []:
                tag = pair.get('tag', '').strip()
                if tag:
                    if result_text.strip().lower().startswith(tag.lower()) or result_text.strip().lower() == tag.lower():
                        tag_text = tag
                        break
        self._answers_by_rule_id[rid] = {'text': result_text, 'tag': tag_text}
        item = self.rules_list_widget.currentItem()
        current_rule = item.data(Qt.UserRole) if item else None
        if isinstance(current_rule, dict) and current_rule.get('id') == rid:
            if self.answer_box.parent() is None:
                answer_row = QHBoxLayout()
                answer_row.setContentsMargins(0, 0, 0, 0)
                answer_row.setSpacing(6)
                answer_row.addWidget(self.answer_box, 1)
                answer_row.addWidget(self.tag_badge, 0)
                self.conditions_layout.addLayout(answer_row)
            display_text = result_text if (result_text is not None and len(result_text) > 0) else "[NO RESPONSE]"
            self.answer_box.setPlainText(display_text)
            self.answer_box.setVisible(True)
            if tag_text:
                self.tag_badge.setText(tag_text)
                self.tag_badge.setVisible(True)
            else:
                self.tag_badge.clear()
                self.tag_badge.setVisible(False)

    def set_posts(self, posts):
        self.posts_list_widget.clear()
        if not posts:
            return
        for p in posts:
            if isinstance(p, dict):
                role = p.get('role')
                content = p.get('content', '')
                character_name = p.get('character_name')
                display = p.get('display')
                if not display:
                    prefix = "Player" if role == 'user' else (character_name if character_name else "Narrator")
                    label = content if isinstance(content, str) else str(content)
                    label = " ".join(label.split())
                    if len(label) > 80:
                        label = label[:77] + "..."
                    display = f"{prefix}: {label}"
                item = QListWidgetItem(display)
                item.setData(Qt.UserRole, {'role': role, 'character_name': character_name, 'full_text': f"{display.split(': ',1)[0]}: {content}"})
                self.posts_list_widget.addItem(item)
            else:
                item = QListWidgetItem(str(p))
                self.posts_list_widget.addItem(item)

    def append_post(self, role, content, character_name=None):
        prefix = "Player" if role == "user" else (character_name if character_name else "Narrator")
        label = content if isinstance(content, str) else str(content)
        label_compact = " ".join(label.split())
        display = f"{prefix}: {label_compact[:77] + '...' if len(label_compact) > 80 else label_compact}"
        item = QListWidgetItem(display)
        item.setData(Qt.UserRole, {'role': role, 'character_name': character_name, 'full_text': f"{prefix}: {label}"})
        self.posts_list_widget.addItem(item)
        self.posts_list_widget.scrollToBottom()

    def set_rules(self, rules):
        self.rules_list_widget.clear()
        if not rules:
            return
        for r in rules:
            if isinstance(r, dict):
                rule_id = r.get('id', 'unnamed')
                display_text = f"ID: {rule_id}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, r)
                self.rules_list_widget.addItem(item)
            else:
                item = QListWidgetItem(str(r))
                self.rules_list_widget.addItem(item)

    def get_posts_list_widget(self):
        return self.posts_list_widget

    def get_rules_list_widget(self):
        return self.rules_list_widget

    def get_conditions_container(self):
        return self.conditions_container

    def get_actions_container(self):
        return self.actions_container