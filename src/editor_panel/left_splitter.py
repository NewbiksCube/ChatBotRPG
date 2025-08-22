from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QButtonGroup, QSizePolicy, QFrame, QSpacerItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from scribe.agent_chat import AgentPanel

class LeftSplitterWidget(QWidget):
    mode_changed = pyqtSignal(str)

    def __init__(self, theme_colors, parent=None, main_app=None):
        super().__init__(parent)
        self.theme_colors = theme_colors
        self.main_app = main_app
        self.setObjectName("LeftSplitterContainer")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        base_color = QColor(self.theme_colors['base_color'])
        if base_color.isValid():
            bright_color = base_color.lighter(130).name()
        else:
            bright_color = self.theme_colors['base_color']
        self.banner_label = QLabel("<span style='font-size:10pt; font-weight:bold;'>ChatBot RPG</span><br><span style='font-size:8pt;'>Construction Toolkit</span>")
        self.banner_label.setObjectName("BannerLabelLeft")
        self.banner_label.setAlignment(Qt.AlignCenter)
        self.banner_label.setTextFormat(Qt.RichText)
        self.banner_label.setStyleSheet(f"color: {bright_color}; letter-spacing: 1px; padding: 2px 0;")
        self.banner_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(self.banner_label)
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.live_game_button = QPushButton("LIVE GAME")
        self.live_game_button.setObjectName("LiveGameButtonLeft")
        self.live_game_button.setCheckable(True)
        self.live_game_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.live_game_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.live_game_button)
        self.live_game_button.setChecked(False)
        layout.addWidget(self.live_game_button)
        self.notes_button = QPushButton("WORLDBUILDING")
        self.notes_button.setObjectName("NotesManagerButtonLeft")
        self.notes_button.setCheckable(True)
        self.notes_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.notes_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.notes_button)
        layout.addWidget(self.notes_button)
        self.setting_manager_button = QPushButton("SETTINGS")
        self.setting_manager_button.setObjectName("SettingManagerButtonLeft")
        self.setting_manager_button.setCheckable(True)
        self.setting_manager_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.setting_manager_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.setting_manager_button)
        layout.addWidget(self.setting_manager_button)
        self.time_manager_button = QPushButton("TIME")
        self.time_manager_button.setObjectName("TimeManagerButtonLeft")
        self.time_manager_button.setCheckable(True)
        self.time_manager_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.time_manager_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.time_manager_button)
        layout.addWidget(self.time_manager_button)
        self.actor_manager_button = QPushButton("CHARACTERS")
        self.actor_manager_button.setObjectName("ActorManagerButtonLeft")
        self.actor_manager_button.setCheckable(True)
        self.actor_manager_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.actor_manager_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.actor_manager_button)
        layout.addWidget(self.actor_manager_button)
        self.rules_button = QPushButton("RULES")
        self.rules_button.setObjectName("RulesManagerButtonLeft")
        self.rules_button.setCheckable(True)
        self.rules_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.rules_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.rules_button)
        layout.addWidget(self.rules_button)
        self.keyword_manager_button = QPushButton("KEYWORDS")
        self.keyword_manager_button.setObjectName("KeywordManagerButtonLeft")
        self.keyword_manager_button.setCheckable(True)
        self.keyword_manager_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.keyword_manager_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.keyword_manager_button)
        layout.addWidget(self.keyword_manager_button)
        self.inventory_manager_button = QPushButton("INVENTORY")
        self.inventory_manager_button.setObjectName("InventoryManagerButtonLeft")
        self.inventory_manager_button.setCheckable(True)
        self.inventory_manager_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.inventory_manager_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.inventory_manager_button)
        layout.addWidget(self.inventory_manager_button)
        self.random_generators_button = QPushButton("LISTS")
        self.random_generators_button.setObjectName("RandomGeneratorsButtonLeft")
        self.random_generators_button.setCheckable(True)
        self.random_generators_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.random_generators_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.random_generators_button)
        layout.addWidget(self.random_generators_button)
        self.start_conditions_button = QPushButton("INTRO")
        self.start_conditions_button.setObjectName("StartConditionsButtonLeft")
        self.start_conditions_button.setCheckable(True)
        self.start_conditions_button.setFont(QFont('Consolas', 6, QFont.Bold))
        self.start_conditions_button.setFocusPolicy(Qt.NoFocus)
        self.button_group.addButton(self.start_conditions_button)
        self.start_conditions_button.setChecked(False)
        layout.addWidget(self.start_conditions_button)
        self.divider = QFrame()
        self.divider.setFrameShape(QFrame.HLine)
        self.divider.setFrameShadow(QFrame.Sunken)
        divider_color = self.theme_colors.get('base_color', '#00E5E5')
        self.divider.setStyleSheet(f"background-color: {divider_color}; height: 1px; border: none; margin: 5px 0 0 0;")
        layout.addWidget(self.divider)
        
        self.agent_panel = AgentPanel(parent=self.main_app, theme_colors=self.theme_colors)
        # Set the scribe label color to bright in the agent panel
        if hasattr(self.agent_panel, 'scribe_label'):
            self.agent_panel.scribe_label.setStyleSheet(f"font-size: 10pt; color: {bright_color}; padding: 2px; background-color: transparent;")
        layout.addWidget(self.agent_panel, 1)
        self.bottom_stretch = None
        self.setLayout(layout)
        self.update_splitter_layout()
        self.button_group.buttonClicked.connect(self._emit_mode_change)
        self.setMinimumHeight(0)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(240)

    def _emit_mode_change(self, button):
        self.mode_changed.emit(button.objectName())

    def update_theme(self, new_theme):
        self.theme_colors = new_theme.copy()
        base_color = QColor(self.theme_colors['base_color'])
        if base_color.isValid():
            bright_color = base_color.lighter(130).name()
        else:
            bright_color = self.theme_colors['base_color']
        self.banner_label.setStyleSheet(f"color: {bright_color}; letter-spacing: 1px; padding: 2px 0;")
        divider_color = self.theme_colors.get('base_color', '#00E5E5')
        self.divider.setStyleSheet(f"background-color: {divider_color}; height: 1px; border: none; margin: 5px 0 0 0;")
        if hasattr(self, 'agent_panel') and self.agent_panel and hasattr(self.agent_panel, 'scribe_label'):
            self.agent_panel.scribe_label.setStyleSheet(f"font-size: 10pt; color: {bright_color}; padding: 2px; background-color: transparent;")
        if hasattr(self, 'agent_panel') and self.agent_panel and hasattr(self.agent_panel, 'update_theme'):
            self.agent_panel.update_theme(self.theme_colors)

    def update_splitter_layout(self):
        layout = self.layout()
        if self.bottom_stretch:
            layout.removeItem(self.bottom_stretch)
            self.bottom_stretch = None
        if not self.agent_panel.isVisible():
            self.bottom_stretch = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
            layout.addItem(self.bottom_stretch)

    def set_agent_panel_visible(self, visible):
        self.agent_panel.setVisible(visible)
        self.update_splitter_layout()

    def sizeHint(self):
        return self.layout().sizeHint()

    def minimumSizeHint(self):
        return self.layout().minimumSize()
 