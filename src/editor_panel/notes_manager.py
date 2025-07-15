import os
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLabel, QHBoxLayout, 
                             QPushButton, QScrollArea, QFrame, QComboBox, QLineEdit,
                             QMessageBox, QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor

class NotesManagerWidget(QWidget):
    notes_saved = pyqtSignal(str)

    def __init__(self, theme_colors, tab_settings_file, parent=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.tab_settings_file = tab_settings_file
        self.setObjectName("NotesManagerContainer")
        self.world_field_instances = {}
        self.world_field_order = []
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.save_notes)
        self._notes_changed_since_last_save = False
        self.current_layout = "Notes"
        self._init_ui()
        self.load_notes()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(0)
        
        self.layout_buttons_container = QWidget()
        layout_buttons_layout = QHBoxLayout(self.layout_buttons_container)
        layout_buttons_layout.setContentsMargins(0, 0, 0, 0)
        layout_buttons_layout.setSpacing(5)
        
        self.world_button = QPushButton("World")
        self.system_button = QPushButton("System") 
        self.general_button = QPushButton("Notes")
        
        for button in [self.world_button, self.system_button, self.general_button]:
            button.setObjectName("NotesLayoutButton")
            button.setFont(QFont('Consolas', 10))
            button.setFixedHeight(25)
            button.setCheckable(True)
            layout_buttons_layout.addWidget(button)
        
        self.world_button.setChecked(True)
        self.current_layout = "World"
        
        self.world_button.clicked.connect(lambda: self.switch_layout("World"))
        self.system_button.clicked.connect(lambda: self.switch_layout("System"))
        self.general_button.clicked.connect(lambda: self.switch_layout("Notes"))
        
        layout.addWidget(self.layout_buttons_container)

        self.notes_editor = QTextEdit()
        self.notes_editor.setObjectName("NotesEditor")
        self.notes_editor.setFont(QFont('Consolas', 11))
        self.notes_editor.setPlaceholderText("Enter your development notes for this workflow here...")
        self.notes_editor.textChanged.connect(self._on_notes_changed)
        self.notes_editor.setOverwriteMode(False)
        self.notes_editor.setCursorWidth(4)

        self.world_scroll_area = QScrollArea()
        self.world_scroll_area.setWidgetResizable(True)
        self.world_scroll_area.setObjectName("WorldScrollArea")
        self.world_content_widget = QWidget()
        self.world_layout = QVBoxLayout(self.world_content_widget)
        self.world_layout.setContentsMargins(5, 5, 5, 5)
        self.world_layout.setSpacing(10)
        
        self.world_field_templates = {
            "core_concept": ("Core Concept", "World Name\n\nTagline or Theme (e.g. \"A world shrinking under the weight of its own magic\")\n\nGenre & Tone (grimdark, fairy tale, surreal, etc.)\n\nFoundational Premise (What makes this world unique?)\n\nWhat conflicts shape this world?\n\nWhat kind of stories does this world want to tell?"),
            "peoples_cultures": ("Peoples & Cultures", "Dominant peoples/races\n\nMinorities, subcultures, hybrids\n\nCultural values and taboos\n\nClass structures and social mobility\n\nGender roles and family structures\n\nImportant cultural rituals or practices\n\nOutsider perspectives / xenophobia / multiculturalism"),
            "biology_ecology": ("Biology & Ecology", "Biosphere (plants, beasts, weather, ecology)\n\nIntelligent species – how do they evolve/survive?\n\nUnique evolutionary adaptations\n\nDiseases, poisons, and afflictions\n\nSymbiotic or hostile species relations\n\nHow do people interact with nature?"),
            "civilization_infrastructure": ("Civilization & Infrastructure", "City design & architecture\n\nTransportation methods\n\nFood systems & agriculture\n\nTrade & travel routes\n\nCommunication methods (magical or mundane)\n\nWaste management & water\n\nWhat luxuries exist? Who has access?"),
            "power_government": ("Power & Government", "Forms of government (monarchy, republic, tribal council, etc.)\n\nWho holds real power?\n\nLaws and punishments\n\nSurveillance, propaganda, policing\n\nCivil rights, freedoms, and censorship\n\nRebellion and revolution: who resists?\n\nInternational relations & diplomacy"),
            "magic_science_technology": ("Magic, Science & Technology", "Sources of power (arcane, divine, scientific, natural)\n\nHow is magic accessed or restricted?\n\nCost, risk, or consequence of using magic\n\nMagical or technological artifacts\n\nOverlap between science and magic\n\nPublic trust in magic/science\n\nForbidden or lost knowledge"),
            "spirituality_myth": ("Spirituality & Myth", "Religions, cults, and philosophies\n\nPantheon(s), saints, spirits, or voids\n\nCreation myth and eschatology (end times)\n\nRituals, festivals, sacrifices\n\nRole of religious figures in society\n\nHeresy, orthodoxy, and religious wars"),
            "knowledge_education": ("Knowledge & Education", "How is knowledge preserved and passed down?\n\nWho has access to education?\n\nAre books, magic scrolls, or data crystals used?\n\nWhat taboos exist around knowledge?\n\nHow do people learn: apprenticeship, formal schools, oral lore?"),
            "daily_life": ("Daily Life", "Clothing, fashion, and materials\n\nFood, drink, and mealtime rituals\n\nRecreation, games, and sports\n\nArts (music, painting, theater, tattoos, etc.)\n\nSexuality, romance, and courtship\n\nCustoms around birth, coming-of-age, marriage, and death\n\nHow people greet each other, say goodbye, insult, curse"),
            "conflict_warfare": ("Conflict & Warfare", "Who fights and why?\n\nHow are armies organized?\n\nWeapons and armor (traditional or magical)\n\nBattlegrounds: where do wars take place?\n\nHow do people view war—honor or horror?\n\nSecret wars, shadow wars, or civil strife\n\nHeroes, mercenaries, or rebels"),
            "geography_environment": ("Geography & Environment", "Continents, regions, and biomes\n\nImportant landmarks and wonder-locations\n\nWhere do borders naturally occur? (mountains, rivers, Mist)\n\nHow does geography affect culture and survival?\n\nClimate patterns and natural disasters\n\nAre there hidden or shifting places (e.g. the Mist)?"),
            "history_time": ("History & Time", "Mythic history (what people believe happened)\n\nDocumented history (what actually happened)\n\nMajor historical events (wars, disasters, discoveries)\n\nCycles: Ages, Eras, or repeating calamities\n\nCalendars and timekeeping systems"),
            "mystery_unknown": ("Mystery & the Unknown", "What can't be explained?\n\nWhat secrets do people whisper about?\n\nWhat lies beyond the Mist, sea, sky, stars?\n\nAre the gods real or imagined?\n\nWho is hiding the truth, and why?"),
            "story_specific": ("Story-Specific Elements", "What part of the world will your story focus on?\n\nWho are the key factions in your narrative?\n\nWhat moral or theme do you want to explore?\n\nHow does the protagonist fit into this world?\n\nWhat questions about the world will your story ask (or answer)?")
        }
        
        self.world_fields_container = QWidget()
        self.world_fields_layout = QVBoxLayout(self.world_fields_container)
        self.world_fields_layout.setContentsMargins(0, 0, 0, 0)
        self.world_fields_layout.setSpacing(10)
        
        self.world_layout.addWidget(self.world_fields_container)
        self.world_scroll_area.setWidget(self.world_content_widget)
        
        self._setup_default_world_fields()

        self.system_scroll_area = QScrollArea()
        self.system_scroll_area.setWidgetResizable(True)
        self.system_scroll_area.setObjectName("SystemScrollArea")
        self.system_content_widget = QWidget()
        self.system_layout = QVBoxLayout(self.system_content_widget)
        self.system_layout.setContentsMargins(5, 5, 5, 5)
        self.system_layout.setSpacing(10)
        self.system_fields = {}
        
        system_sections = [
            ("combat_conflict", "1. Combat & Conflict Resolution", "How is combat resolved? (turn-based, real-time, narrative)\n\nWhat determines success/failure? (dice, cards, resource management)\n\nWhat are the stakes of combat? (death, injury, resources, reputation)\n\nHow do characters improve in combat?\n\nWhat role does equipment/gear play?\n\nAre there different types of combat? (melee, ranged, social, magical)\n\nHow do multiple characters interact in combat?"),
            ("survival_resources", "2. Survival & Resource Management", "Is there a food/drink system? How does it work?\n\nWhat other resources matter? (health, stamina, money, materials)\n\nHow do characters acquire and manage resources?\n\nWhat happens when resources run out?\n\nAre there crafting/gathering systems?\n\nHow do environmental factors affect survival?\n\nWhat role does time play in resource management?"),
            ("character_progression", "3. Character Progression & Development", "How do characters improve? (levels, skills, attributes, relationships)\n\nWhat drives character growth? (experience, training, story events)\n\nAre there classes, archetypes, or free-form development?\n\nHow do characters specialize or differentiate themselves?\n\nWhat are the limits to character growth?\n\nHow do characters change over time?\n\nWhat role do relationships play in development?"),
            ("social_interaction", "4. Social Interaction & Relationships", "How are social encounters resolved?\n\nWhat determines social success/failure?\n\nHow do relationships develop and change?\n\nAre there reputation or influence systems?\n\nHow do characters form alliances or rivalries?\n\nWhat role does communication play?\n\nHow do social dynamics affect gameplay?"),
            ("exploration_discovery", "5. Exploration & Discovery", "How do characters explore the world?\n\nWhat drives exploration? (curiosity, necessity, rewards)\n\nHow is information revealed to players?\n\nAre there hidden areas or secrets?\n\nHow do characters navigate and travel?\n\nWhat role does mapping or location tracking play?\n\nHow do characters interact with the environment?"),
            ("magic_technology", "6. Magic & Technology Systems", "How does magic/technology work in this world?\n\nWhat are the costs and consequences of using power?\n\nHow is power accessed or learned?\n\nAre there different schools or types of power?\n\nWhat limits or restrictions exist?\n\nHow do magic/tech interact with other systems?\n\nWhat role does innovation or discovery play?"),
            ("economy_trade", "7. Economy & Trade", "How does the economy function?\n\nWhat is valuable and why?\n\nHow do characters acquire wealth?\n\nAre there different currencies or trade systems?\n\nHow do supply and demand work?\n\nWhat role do merchants and markets play?\n\nHow does economic status affect gameplay?"),
            ("politics_influence", "8. Politics & Influence", "How do characters gain and use influence?\n\nWhat role do factions or organizations play?\n\nHow do political decisions affect the world?\n\nWhat determines political success or failure?\n\nHow do characters navigate power structures?\n\nWhat role does reputation or status play?\n\nHow do political changes affect other systems?"),
            ("time_advancement", "9. Time & Advancement", "How does time pass in the game?\n\nWhat happens during downtime?\n\nHow do long-term projects work?\n\nWhat role do seasons, cycles, or eras play?\n\nHow do characters age or change over time?\n\nWhat happens when characters are inactive?\n\nHow does time affect other systems?"),
            ("challenges_obstacles", "10. Challenges & Obstacles", "What types of challenges do characters face?\n\nHow are obstacles overcome?\n\nWhat role does preparation play?\n\nHow do characters deal with failure?\n\nAre there different difficulty levels?\n\nHow do challenges scale with character ability?\n\nWhat makes challenges meaningful?"),
            ("rewards_achievement", "11. Rewards & Achievement", "What motivates characters to act?\n\nWhat types of rewards exist? (tangible, intangible, story-based)\n\nHow do characters measure success?\n\nAre there achievement or milestone systems?\n\nWhat role does recognition play?\n\nHow do rewards affect character development?\n\nWhat makes achievements meaningful?"),
            ("narrative_storytelling", "12. Narrative & Storytelling", "How does the story unfold?\n\nWhat role do players have in storytelling?\n\nHow are story elements integrated with mechanics?\n\nWhat drives the narrative forward?\n\nHow do characters contribute to the story?\n\nWhat role do NPCs and world events play?\n\nHow do multiple storylines interact?"),
            ("balance_design", "13. Balance & Design Philosophy", "What are the core design principles?\n\nHow do you balance different playstyles?\n\nWhat makes choices meaningful?\n\nHow do you prevent dominant strategies?\n\nWhat role does randomness play?\n\nHow do you handle player skill vs character ability?\n\nWhat makes the system fun and engaging?"),
            ("implementation_technical", "14. Implementation & Technical Considerations", "How will this system be implemented?\n\nWhat technical challenges exist?\n\nHow will the system integrate with the framework?\n\nWhat tools or interfaces are needed?\n\nHow will the system be tested and refined?\n\nWhat data structures or algorithms are required?\n\nHow will the system scale and evolve?")
        ]
        
        for field_key, title, placeholder in system_sections:
            section_frame = QFrame()
            section_frame.setObjectName("SystemSectionFrame")
            section_layout = QVBoxLayout(section_frame)
            section_layout.setContentsMargins(10, 10, 10, 10)
            section_layout.setSpacing(5)
            
            title_label = QLabel(title)
            title_label.setObjectName("SystemSectionTitle")
            title_label.setFont(QFont('Consolas', 12, QFont.Bold))
            section_layout.addWidget(title_label)
            
            text_field = QTextEdit()
            text_field.setObjectName(f"SystemField_{field_key}")
            text_field.setFont(QFont('Consolas', 10))
            text_field.setPlaceholderText(placeholder)
            text_field.setMaximumHeight(200)
            text_field.setMinimumHeight(100)
            text_field.textChanged.connect(self._on_system_field_changed)
            text_field.setCursorWidth(4)
            section_layout.addWidget(text_field)
            
            self.system_fields[field_key] = text_field
            self.system_layout.addWidget(section_frame)
        
        self.system_scroll_area.setWidget(self.system_content_widget)
        
        self.editor_stack = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_stack)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.addWidget(self.notes_editor)
        self.editor_layout.addWidget(self.world_scroll_area)
        self.editor_layout.addWidget(self.system_scroll_area)
        
        self.notes_editor.setVisible(False)
        self.system_scroll_area.setVisible(False)
        
        layout.addWidget(self.editor_stack)
        self.setLayout(layout)
        self.setMinimumHeight(0)
        self.update_theme(self.theme_colors)

    def _setup_default_world_fields(self):
        default_fields = [
            "core_concept", "peoples_cultures", "biology_ecology", "civilization_infrastructure",
            "power_government", "magic_science_technology", "spirituality_myth", "knowledge_education",
            "daily_life", "conflict_warfare", "geography_environment", "history_time",
            "mystery_unknown", "story_specific"
        ]
        
        for field_key in default_fields:
            if field_key not in self.world_field_order:
                self.world_field_order.append(field_key)
                if field_key not in self.world_field_instances:
                    self.world_field_instances[field_key] = {}
                    self.add_field_instance(field_key, None)



    def add_field_instance(self, field_type, custom_name=None):
        if field_type not in self.world_field_instances:
            self.world_field_instances[field_type] = {}
        
        instances = self.world_field_instances[field_type]
        instance_id = len(instances)
        
        instance_data = {
            'custom_name': custom_name,
            'content': ''
        }
        
        instances[instance_id] = instance_data
        self.rebuild_world_ui()
        self._on_world_field_changed()

    def remove_field_instance(self, field_type, instance_id):
        if field_type in self.world_field_instances and instance_id in self.world_field_instances[field_type]:
            if len(self.world_field_instances[field_type]) > 1:
                del self.world_field_instances[field_type][instance_id]
                self.rebuild_world_ui()
                self._on_world_field_changed()

    def move_field_up(self, field_type):
        if field_type in self.world_field_order:
            current_index = self.world_field_order.index(field_type)
            if current_index > 0:
                self.world_field_order[current_index], self.world_field_order[current_index - 1] = \
                    self.world_field_order[current_index - 1], self.world_field_order[current_index]
                self.rebuild_world_ui()
                self._on_world_field_changed()

    def move_field_down(self, field_type):
        if field_type in self.world_field_order:
            current_index = self.world_field_order.index(field_type)
            if current_index < len(self.world_field_order) - 1:
                self.world_field_order[current_index], self.world_field_order[current_index + 1] = \
                    self.world_field_order[current_index + 1], self.world_field_order[current_index]
                self.rebuild_world_ui()
                self._on_world_field_changed()

    def move_instance_left(self, field_type, instance_id):
        if field_type in self.world_field_instances:
            instances = self.world_field_instances[field_type]
            instance_ids = sorted(instances.keys())
            
            if instance_id in instance_ids:
                current_index = instance_ids.index(instance_id)
                if current_index > 0:
                    left_id = instance_ids[current_index - 1]
                    instances[instance_id], instances[left_id] = instances[left_id], instances[instance_id]
                    self.rebuild_world_ui()
                    self._on_world_field_changed()

    def move_instance_right(self, field_type, instance_id):
        if field_type in self.world_field_instances:
            instances = self.world_field_instances[field_type]
            instance_ids = sorted(instances.keys())
            
            if instance_id in instance_ids:
                current_index = instance_ids.index(instance_id)
                if current_index < len(instance_ids) - 1:
                    right_id = instance_ids[current_index + 1]
                    instances[instance_id], instances[right_id] = instances[right_id], instances[instance_id]
                    self.rebuild_world_ui()
                    self._on_world_field_changed()

    def rebuild_world_ui(self):
        for i in reversed(range(self.world_fields_layout.count())):
            child = self.world_fields_layout.takeAt(i)
            if child.widget():
                child.widget().setParent(None)
        
        for field_type in self.world_field_order:
            if field_type in self.world_field_instances:
                self.create_field_section(field_type)

    def create_field_section(self, field_type):
        instances = self.world_field_instances[field_type]
        if not instances:
            return
        
        section_frame = QFrame()
        section_frame.setObjectName("WorldSectionFrame")
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(10, 10, 10, 10)
        section_layout.setSpacing(5)
        title_text = self.world_field_templates[field_type][0]
        title_label = QLabel(title_text)
        title_label.setObjectName("WorldSectionTitle")
        title_label.setFont(QFont('Consolas', 12, QFont.Bold))
        section_layout.addWidget(title_label)
        horizontal_scroll = QScrollArea()
        horizontal_scroll.setObjectName("HorizontalFieldScroll")
        horizontal_scroll.setWidgetResizable(True)
        horizontal_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        horizontal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        horizontal_scroll.setFixedHeight(250)
        horizontal_widget = QWidget()
        horizontal_layout = QHBoxLayout(horizontal_widget)
        horizontal_layout.setContentsMargins(5, 5, 5, 5)
        horizontal_layout.setSpacing(10)
        sorted_instances = sorted(instances.items(), key=lambda x: x[0])
        
        for instance_id, instance_data in sorted_instances:
            instance_frame = QFrame()
            instance_frame.setObjectName("FieldInstanceFrame")
            instance_frame.setMinimumWidth(320)
            instance_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            instance_frame.setFixedHeight(230)
            instance_layout = QVBoxLayout(instance_frame)
            instance_layout.setContentsMargins(8, 8, 8, 8)
            instance_layout.setSpacing(5)
            instance_header = QHBoxLayout()
            instance_header.setContentsMargins(0, 0, 0, 0)
            custom_name = instance_data.get('custom_name')
            if custom_name:
                name_label = QLabel(custom_name)
                name_label.setObjectName("InstanceNameLabel")
                name_label.setFont(QFont('Consolas', 9, QFont.Bold))
                instance_header.addWidget(name_label)
            instance_header.addStretch()
            button_layout = QHBoxLayout()
            button_layout.setSpacing(2)
            
            if len(instances) > 1:
                left_button = QPushButton("←")
                left_button.setObjectName("InstanceMoveButton")
                left_button.setFont(QFont('Consolas', 8))
                left_button.setFixedSize(18, 18)
                left_button.setToolTip("Move left")
                left_button.clicked.connect(lambda checked, ft=field_type, iid=instance_id: self.move_instance_left(ft, iid))
                button_layout.addWidget(left_button)
                right_button = QPushButton("→")
                right_button.setObjectName("InstanceMoveButton")
                right_button.setFont(QFont('Consolas', 8))
                right_button.setFixedSize(18, 18)
                right_button.setToolTip("Move right")
                right_button.clicked.connect(lambda checked, ft=field_type, iid=instance_id: self.move_instance_right(ft, iid))
                button_layout.addWidget(right_button)
            
            add_button = QPushButton("+")
            add_button.setObjectName("InstanceAddButton")
            add_button.setFont(QFont('Consolas', 8))
            add_button.setFixedSize(18, 18)
            add_button.setToolTip("Add instance")
            add_button.clicked.connect(lambda checked, ft=field_type: self.add_field_instance(ft))
            button_layout.addWidget(add_button)
            
            remove_button = QPushButton("×")
            remove_button.setObjectName("InstanceRemoveButton")
            remove_button.setFont(QFont('Consolas', 8))
            remove_button.setFixedSize(18, 18)
            remove_button.setToolTip("Remove instance")
            remove_button.clicked.connect(lambda checked, ft=field_type, iid=instance_id: self.remove_field_instance(ft, iid))
            remove_button.setEnabled(len(instances) > 1)
            button_layout.addWidget(remove_button)
            
            instance_header.addLayout(button_layout)
            instance_layout.addLayout(instance_header)
            
            text_field = QTextEdit()
            text_field.setObjectName(f"WorldField_{field_type}_{instance_id}")
            text_field.setFont(QFont('Consolas', 10))
            text_field.setPlaceholderText(self.world_field_templates[field_type][1])
            text_field.setPlainText(instance_data.get('content', ''))
            text_field.textChanged.connect(lambda ft=field_type, iid=instance_id: self.on_instance_text_changed(ft, iid))
            text_field.setCursorWidth(4)
            
            instance_layout.addWidget(text_field)
            horizontal_layout.addWidget(instance_frame)
        
        horizontal_scroll.setWidget(horizontal_widget)
        section_layout.addWidget(horizontal_scroll)
        
        self.world_fields_layout.addWidget(section_frame)

    def on_instance_text_changed(self, field_type, instance_id):
        sender = self.sender()
        if sender and field_type in self.world_field_instances and instance_id in self.world_field_instances[field_type]:
            self.world_field_instances[field_type][instance_id]['content'] = sender.toPlainText()
            self._on_world_field_changed()

    def _on_notes_changed(self):
        if self.current_layout == "Notes":
            self._notes_changed_since_last_save = True
            self._save_timer.start(1500)

    def _on_world_field_changed(self):
        if self.current_layout == "World":
            self._notes_changed_since_last_save = True
            self._save_timer.start(1500)

    def _on_system_field_changed(self):
        if self.current_layout == "System":
            self._notes_changed_since_last_save = True
            self._save_timer.start(1500)

    def save_notes(self):
        if self.tab_settings_file and self._notes_changed_since_last_save:
            try:
                tab_settings = {}
                if os.path.exists(self.tab_settings_file):
                    with open(self.tab_settings_file, 'r', encoding='utf-8') as f:
                        tab_settings = json.load(f)
                
                if not isinstance(tab_settings, dict):
                    tab_settings = {}
                
                if self.current_layout == "Notes":
                    notes_text = self.notes_editor.toPlainText()
                    tab_settings['dev_notes'] = notes_text
                elif self.current_layout == "World":
                    tab_settings['world_field_instances'] = self.world_field_instances
                    tab_settings['world_field_order'] = self.world_field_order
                elif self.current_layout == "System":
                    for field_key, text_field in self.system_fields.items():
                        tab_settings[f'system_{field_key}'] = text_field.toPlainText()
                
                with open(self.tab_settings_file, 'w', encoding='utf-8') as f:
                    json.dump(tab_settings, f, indent=2, ensure_ascii=False)
                
                self._notes_changed_since_last_save = False
                
                if self.current_layout == "Notes":
                    self.notes_saved.emit(self.notes_editor.toPlainText())
                    
            except Exception as e:
                print(f"Error saving notes to {self.tab_settings_file}: {e}")
        
        self._save_timer.stop()

    def load_notes(self):
        if self.tab_settings_file and os.path.exists(self.tab_settings_file):
            try:
                with open(self.tab_settings_file, 'r', encoding='utf-8') as f:
                    tab_settings = json.load(f)
                
                if isinstance(tab_settings, dict):
                    if 'dev_notes' in tab_settings:
                        notes = tab_settings['dev_notes']
                        if hasattr(self, 'notes_editor'):
                            self.notes_editor.blockSignals(True)
                            self.notes_editor.setPlainText(notes)
                            self.notes_editor.blockSignals(False)
                    
                    if 'world_field_instances' in tab_settings:
                        self.world_field_instances = tab_settings['world_field_instances']
                    
                    if 'world_field_order' in tab_settings:
                        self.world_field_order = tab_settings['world_field_order']
                    
                    if hasattr(self, 'world_fields_layout'):
                        self.rebuild_world_ui()
                    
                    for field_key, text_field in self.system_fields.items():
                        system_key = f'system_{field_key}'
                        if system_key in tab_settings:
                            text_field.blockSignals(True)
                            text_field.setPlainText(tab_settings[system_key])
                            text_field.blockSignals(False)
                
                self._notes_changed_since_last_save = False
                
            except Exception as e:
                print(f"Error loading notes from {self.tab_settings_file}: {e}")

    def update_theme(self, new_theme):
        self.theme_colors = new_theme.copy()
        base_color = self.theme_colors.get("base_color", "#FFFFFF")
        bg_color = self.theme_colors.get("bg_color", "#2A2A2A")
        darker_bg = self.theme_colors.get("darker_bg", "#1A1A1A")
        highlight = self.theme_colors.get("highlight", "#4A4A4A")
        
        editor_style = f"""
            QTextEdit {{
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 5px;
                font-family: Consolas;
                font-size: 10pt;
                selection-background-color: {highlight};
                selection-color: white;
            }}
            QTextEdit:focus {{
                border: 1px solid {base_color};
                outline: none;
            }}
        """
        
        self.notes_editor.setStyleSheet(editor_style)
        self.system_scroll_area.setStyleSheet(editor_style)
        
        for text_field in self.system_fields.values():
            text_field.setStyleSheet(editor_style)
        
        self.setStyleSheet(f"""
            QWidget#NotesManagerContainer {{
                background-color: {bg_color};
            }}
            QPushButton#NotesLayoutButton {{
                background-color: {bg_color};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 4px 12px;
                font: 10pt "Consolas";
            }}
            QPushButton#NotesLayoutButton:hover {{
                background-color: {highlight};
                color: white;
            }}
            QPushButton#NotesLayoutButton:checked {{
                background-color: {base_color};
                color: {bg_color};
            }}
            QFrame#WorldSectionFrame, QFrame#SystemSectionFrame {{
                background-color: {bg_color};
                border: 1px solid {base_color};
                border-radius: 3px;
            }}
            QFrame#FieldInstanceFrame {{
                background-color: {darker_bg};
                border: 1px solid {base_color};
                border-radius: 3px;
                margin: 2px;
            }}
            QLabel#WorldSectionTitle, QLabel#SystemSectionTitle {{
                color: {base_color};
                background-color: transparent;
                border: none;
                font: 12pt "Consolas";
            }}
            QLabel#InstanceNameLabel {{
                color: {base_color};
                background-color: transparent;
                border: none;
                font: 9pt "Consolas";
            }}
            QScrollArea#WorldScrollArea, QScrollArea#SystemScrollArea, QScrollArea#HorizontalFieldScroll {{
                background-color: {bg_color};
                border: none;
            }}
            QTextEdit[objectName^="WorldField_"] {{
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 3px;
                padding: 5px;
                font: 10pt "Consolas";
                selection-background-color: {highlight};
                selection-color: white;
            }}
            QTextEdit[objectName^="WorldField_"]:focus {{
                border: 1px solid {base_color};
                outline: none;
            }}
            QPushButton#InstanceAddButton, QPushButton#InstanceMoveButton {{
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 2px;
                font: 8pt "Consolas";
            }}
            QPushButton#InstanceAddButton:hover, QPushButton#InstanceMoveButton:hover {{
                background-color: {highlight};
                color: white;
            }}
            QPushButton#InstanceRemoveButton {{
                background-color: {darker_bg};
                color: {base_color};
                border: 1px solid {base_color};
                border-radius: 2px;
                font: 8pt "Consolas";
            }}
            QPushButton#InstanceRemoveButton:hover {{
                background-color: {highlight};
                color: white;
            }}
            QPushButton#InstanceRemoveButton:disabled {{
                background-color: {darker_bg};
                color: #666666;
                border: 1px solid #666666;
            }}
            QWidget {{
                background-color: {bg_color};
            }}
        """)

    def switch_layout(self, layout_name):
        self.world_button.setChecked(False)
        self.system_button.setChecked(False)
        self.general_button.setChecked(False)
        
        if layout_name == "World":
            self.world_button.setChecked(True)
        elif layout_name == "System":
            self.system_button.setChecked(True)
        elif layout_name == "Notes":
            self.general_button.setChecked(True)
        
        self.current_layout = layout_name
        
        self.notes_editor.setVisible(False)
        self.world_scroll_area.setVisible(False)
        self.system_scroll_area.setVisible(False)
        
        if layout_name == "World":
            self.world_scroll_area.setVisible(True)
        elif layout_name == "System":
            self.system_scroll_area.setVisible(True)
        elif layout_name == "Notes":
            self.notes_editor.setVisible(True)

    def force_save(self):
        self._notes_changed_since_last_save = True
        self.save_notes()
