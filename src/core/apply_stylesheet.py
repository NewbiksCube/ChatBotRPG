from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

def generate_and_apply_stylesheet(target_widget, theme_colors):
    base_color = theme_colors["base_color"]
    bg_value = int(80 * theme_colors["contrast"])
    bg_color = f"#{bg_value:02x}{bg_value:02x}{bg_value:02x}"
    darker_bg = f"#{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}{max(bg_value-10, 0):02x}"
    even_darker_bg = f"#{max(bg_value-20, 0):02x}{max(bg_value-20, 0):02x}{max(bg_value-20, 0):02x}"
    try:
        qcolor = QColor(base_color)
        if not qcolor.isValid(): raise ValueError("Invalid base color")
        r, g, b = qcolor.red(), qcolor.green(), qcolor.blue()
        highlight = f"rgba({r}, {g}, {b}, 0.6)"
        brighter = f"rgba({min(r+30, 255)}, {min(g+30, 255)}, {min(b+30, 255)}, 0.8)"
        input_text_color = qcolor.darker(170).name()
    except ValueError:
        print(f"Warning: Invalid base color '{base_color}'. Using fallbacks.")
        base_color = "#CCCCCC"
        highlight = "rgba(204, 204, 204, 0.6)"
        brighter = "rgba(234, 234, 234, 0.8)"
        input_text_color = "#999999"

    qss = f"""
    /* Default Radio Buttons Styling */
    QRadioButton {{
        color: {base_color};
        font: 9pt 'Consolas';
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* Main container with border */
    QWidget#MainContainer {{
        background-color: {even_darker_bg};
        border: 1px solid #404040;
        border-radius: 3px;
    }}
    
    /* Custom title bar */
    QWidget#TitleBar {{
        background-color: {darker_bg};
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
        border-bottom: 1px solid {base_color};
    }}
    
    QLabel#TitleLabel {{
        color: {base_color};
        font-weight: bold;
    }}
    
    QPushButton#CloseButton, QPushButton#MaximizeButton, QPushButton#MinimizeButton, QPushButton#OptionsButton {{
        background-color: transparent;
        color: {base_color};
        border: none;
        font-size: 16px;
        font-weight: bold;
        border-radius: 12px;
        text-align: center;
        padding: 0px;
        margin: 0px;
    }}
    
    QPushButton#CloseButton:hover {{
        color: {brighter};
        background-color: rgba({r}, {g}, {b}, 0.2);
    }}
    
    QPushButton#MaximizeButton:hover, QPushButton#MinimizeButton:hover, QPushButton#OptionsButton:hover {{
        color: {brighter};
        background-color: rgba({r}, {g}, {b}, 0.2);
    }}
    
    /* Content area */
    QWidget#ContentArea {{
        background-color: {bg_color}; 
        color: {base_color};
    }}
    
    /* Top Controls */
    QHBoxLayout {{ 
        spacing: 10px;
    }}
    
    QComboBox {{ 
        color: {base_color}; 
        background-color: {bg_color}; 
        border: 2px solid {base_color}; 
        padding: 5px; 
        min-width: 150px; 
        border-radius: 5px;
        font: 14pt "Consolas"; /* Default font */
    }}
    QComboBox::drop-down {{ 
        border: none; 
    }} 
    QComboBox::down-arrow {{ 
        image: none;
    }}
    QComboBox QAbstractItemView {{ 
        color: {base_color}; 
        background-color: {bg_color}; 
        selection-background-color: {highlight}; 
        selection-color: white;
    }}
    
    QComboBox#InventoryVarEffectTypeCombo, QComboBox#InventoryVarOperationCombo {{
        min-width: 92px !important;
        font: 9pt "Consolas" !important;
        padding: 4px 8px !important;
    }}
    
    QPushButton {{ 
        color: {base_color}; 
        background-color: {bg_color}; 
        border: 2px solid {base_color}; 
        padding: 5px; /* Default padding */
        font: 14pt "Consolas"; /* Default font */
        border-radius: 5px;
        min-height: 28px; /* Default min height */
    }}
    QPushButton:hover {{ 
        background-color: {highlight}; 
        color: white;
        border: 2px solid {brighter};
    }}
    QPushButton:checked {{ 
        background-color: {highlight}; 
        color: white;
    }}
    
    QLabel {{ /* Default Label */
        color: {base_color};
        font: 14pt "Consolas";
    }}

    QLabel#TemperatureLabel, QLabel#ThemeLabel, QLabel#ModelLabel, QLabel#PurposeLabel, QLabel#SystemContextHeader, QLabel#ThoughtToolHeader {{ 
        color: {base_color}; 
        font: 12pt "Consolas"; /* Slightly smaller */
    }}
    /* Reduce font size for Turn Counter Label */
    QLabel#TurnCounterLabel {{
        color: {base_color};
        font: 14pt "Consolas";
    }}
    /* CoT Specific Labels */
    QLabel#RuleIdLabel, QLabel#RuleDescriptionLabel, QLabel#StartConditionLabel, QLabel#ConditionLabel, QLabel#PairsHeader, QLabel#TagLabel, QLabel#ActionLabel, QLabel#NextRuleLabel, QLabel#PositionLabel, QLabel#ScopeLabel, QLabel#PairLabel, QLabel#SysMsgPositionLabel, QLabel#SwitchModelLabel, QLabel#SetVarLabel, 
    QLabel#VariableCondVarLabel, QLabel#VariableCondValLabel /* Added */ {{
        color: {base_color}; /* Ensure color is set */
        font: 10pt "Consolas"; /* Smaller */
        background-color: transparent; /* Ensure no background override */
    }}
    QLabel#PairsHeader {{
        font-weight: bold;
        margin-top: 5px;
        margin-bottom: 2px;
    }}
    QLabel#PairLabel {{
        font-weight: bold;
    }}

    /* NEW: Style for specific condition row labels */
    QLabel#ConditionTurnLabel, QLabel#ConditionVarLabel, QLabel#ConditionValLabel,
    QLabel#ConditionSceneCountLabel, QLabel#GeographyNameLabel /* Added */ {{
        color: {base_color};
        font: 9pt "Consolas"; /* Even smaller */
        background-color: transparent;
        padding-left: 3px; /* Align a bit */
    }}
    
    QDoubleSpinBox {{ 
        color: {base_color}; 
        background-color: {bg_color}; 
        border: 2px solid {base_color}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 14pt "Consolas";
        border-radius: 5px;
        background: transparent;
    }}
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ 
        background-color: {base_color}; 
        border: 1px solid {bg_color};
        width: 15px; /* Smaller buttons */
    }}
    QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {{
        width: 0px; height: 0px;
    }}
    
    QTextEdit#ModelInput, QTextEdit#PurposeEditor, QTextEdit#SystemContextEditor {{ 
        color: {base_color}; 
        background-color: {bg_color}; 
        border: 2px solid {base_color}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 11pt "Consolas"; 
        border-radius: 5px;
    }}
    /* CoT Specific TextEdits */
    QTextEdit#ConditionEditor, QTextEdit#TagEditor, QTextEdit#ActionEditor,
    QTextEdit#PairActionValueEditor /* NEW */
    {{
        color: {base_color}; 
        background-color: {darker_bg}; /* Match list bg */
        border: 1px solid {base_color}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas"; /* Smaller */
        border-radius: 3px;
        padding: 3px;
    }}
    
    /* Add specific styling for system message action editor to make it bigger */
    QTextEdit#PairActionValueEditor {{
        min-height: 60px; /* Set minimum height */
    }}
    
    /* CoT Specific QLineEdit */
    QLineEdit#RuleIdEditor, QLineEdit#RuleDescriptionEditor, QLineEdit#SwitchModelEditor, QLineEdit#ModelEditor,
    QLineEdit#VariableCondVarEditor, QLineEdit#VariableCondValEditor, /* Added trigger variable inputs */
    QLineEdit#SetVariableNameEditor, QLineEdit#SetVariableValueEditor, /* Added action variable inputs */
    QLineEdit#ConditionVarNameEditor, QLineEdit#ConditionVarValueEditor, /* NEW */
    QLineEdit#GeographyNameEditor, /* Added geography name editor */
    QLineEdit#PairActionVarNameEditor, QLineEdit#PairActionVarValueEditor /* NEW */
    {{
        color: {base_color};
        background-color: {darker_bg}; /* Match list bg */
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas"; /* Smaller */
        border-radius: 3px;
        padding: 3px;
    }}
    /* ADDED: Ensure all QLineEdits in CoT area get the background */
    QWidget#ThoughtToolContainer QLineEdit {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        color: {base_color}; /* Ensure text color */
    }}

    /* CoT Specific ComboBoxes */
    QComboBox#StartConditionSelector, QComboBox#NextRuleSelector, QComboBox#VariableCondOpSelector,
    QComboBox#SceneCondOpSelector /* Added */ {{
        color: {base_color}; 
        background-color: {darker_bg}; /* Match list bg */
        border: 1px solid {base_color}; 
        padding: 3px; 
        font: 9pt "Consolas"; /* Smaller */
        border-radius: 3px;
        min-width: 60px; /* Smaller min width */
    }}
    QComboBox#StartConditionSelector::drop-down, QComboBox#NextRuleSelector::drop-down, QComboBox#VariableCondOpSelector::drop-down,
    QComboBox#SceneCondOpSelector::drop-down /* Added */ {{ 
        border: none; 
    }} 
    QComboBox#StartConditionSelector::down-arrow, QComboBox#NextRuleSelector::down-arrow, QComboBox#VariableCondOpSelector::down-arrow,
    QComboBox#SceneCondOpSelector::down-arrow /* Added */ {{ 
        image: none;
    }}
    QComboBox#StartConditionSelector QAbstractItemView, QComboBox#NextRuleSelector QAbstractItemView, QComboBox#VariableCondOpSelector QAbstractItemView,
    QComboBox#SceneCondOpSelector QAbstractItemView /* Added */ {{ 
        color: {base_color}; 
        background-color: {darker_bg}; /* Match dropdown bg */
        border: 1px solid {base_color};
        selection-background-color: {highlight}; 
        selection-color: white;
    }}
    
    QTabWidget::pane {{ 
        border: 2px solid {base_color}; 
        border-radius: 5px;
        background-color: {bg_color}; /* Ensure pane has a background */
    }}
    QTabWidget::tab-bar {{ 
        alignment: center;
    }}
    QTabBar::tab {{ 
        color: {base_color};
        background: transparent; /* Unselected tabs darker */
        border: 1px solid {base_color};
        padding: 8px 15px; /* More generous padding for text */
        margin-right: 2px;
        font: 10pt "Consolas"; /* Standard readable font size */
        border-top-left-radius: 5px; /* Keep rounded corners */
        border-top-right-radius: 5px;
        border-bottom: none; /* Remove bottom border for unselected */
        min-width: 80px; /* Adequate minimum width for text */
    }}
    
    /* Specific styling for inventory tabs to allow variable width */
    QTabWidget#InventoryTabWidget QTabBar::tab {{
        min-width: 80px; /* Adequate minimum width for short tabs */
        max-width: 250px; /* Maximum width for long tabs */  
        padding: 8px 15px; /* Keep generous padding for readability */
    }}
    QTabBar::tab:selected {{ 
        background-color: {base_color}; /* Selected tab uses bright base color */
        color: #000000; /* Black text for contrast */
        border: 1px solid {base_color};
        border-bottom-color: {base_color}; /* Match background to blend edge */
        margin-bottom: -1px; /* Pull it up slightly */
        font-weight: bold; /* Make selected text bold */
    }}
    QTabBar::tab:!selected:hover {{ 
        background: {highlight}; 
        color: white;
        border: 1px solid {brighter};
        border-bottom: none; /* Ensure no bottom border on hover either */
    }}
    /* Remove margin between - and + tab buttons */
    QTabBar::tab:last-child, QTabBar::tab:only-one {{
        margin-right: 0;
    }}
    
    /* Style tab scroll buttons */
    QTabBar::scroller {{
        background-color: transparent;
        border: none;
        spacing: 2px;
    }}
    
    QTabBar QToolButton {{
        background-color: rgba(0, 0, 0, 0.7);
        border: 1px solid {base_color};
        border-radius: 3px;
        color: {base_color};
        padding: 4px;
        margin: 2px;
        min-width: 20px;
        min-height: 20px;
        max-width: 20px;
        max-height: 20px;
        width: 20px;
        height: 20px;
    }}
    
    QTabBar QToolButton:first {{
        background-color: rgba(0, 0, 0, 0.7);
        border: 1px solid {base_color};
        border-radius: 3px;
        color: {base_color};
        padding: 4px;
        margin: 2px;
        min-width: 20px;
        min-height: 20px;
        max-width: 20px;
        max-height: 20px;
        width: 20px;
        height: 20px;
    }}
    
    QTabBar QToolButton:last {{
        background-color: rgba(0, 0, 0, 0.7);
        border: 1px solid {base_color};
        border-radius: 3px;
        color: {base_color};
        padding: 4px;
        margin: 2px;
        min-width: 20px;
        min-height: 20px;
        max-width: 20px;
        max-height: 20px;
        width: 20px;
        height: 20px;
    }}
    
    QTabBar QToolButton:hover {{
        background-color: rgba(0, 0, 0, 0.8);
        border: 1px solid {brighter};
        color: white;
    }}
    
    QTabBar QToolButton:pressed {{
        background-color: {base_color};
        border: 1px solid {base_color};
        color: #000000;
    }}
    
    QTextEdit#InventoryReadableTextInput {{
        color: {base_color};
        background-color: {bg_color};
        border: 2px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
        padding: 4px;
    }}
    
    QTextEdit#InputField {{ 
        color: {base_color}; 
        background-color: {bg_color}; 
        border: 2px solid {base_color};
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 16pt "Consolas";
    }}
    
    QTextEdit#OutputField {{ 
        color: {base_color};
        background-color: {bg_color}; 
        border: none;
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 16pt "Consolas";
    }}
    
    QScrollBar:vertical {{ 
        background: {bg_color}; 
        width: 16px; 
        border: 1px solid {base_color}; 
        margin: 0px; 
    }}
    QScrollBar::handle:vertical {{ 
        background-color: {base_color}; 
        min-height: 20px; 
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none; 
        background: none; 
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    
    QScrollBar:horizontal {{ 
        background: {bg_color}; 
        height: 16px; 
        border: 1px solid {base_color}; 
        margin: 0px; 
    }}
    QScrollBar::handle:horizontal {{ 
        background-color: {base_color}; 
        min-width: 20px; 
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        border: none; 
        background: none; 
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}
    
    hr {{
        border: none;
        border-top: 1px solid {highlight}; /* Use highlight for hr */
        margin-top: 5px; /* Smaller margins */
        margin-bottom: 5px;
    }}
    
    QColorDialog {{
        background-color: {bg_color};
    }}
    
    /* Dialog style */
    QDialog {{
        background-color: {bg_color};
        color: {base_color};
        border-radius: 5px;
    }}
    
    QSlider::groove:horizontal {{
        border: 1px solid {base_color};
        height: 8px;
        background: transparent;
        margin: 2px 0;
        border-radius: 5px;
    }}
    
    QSlider::handle:horizontal {{
        background-color: {base_color};
        border: 1px solid {brighter};
        width: 18px;
        margin: -2px 0;
        border-radius: 5px;
    }}
    
    /* Splitter styling */
    QSplitter::handle {{
        background-color: {darker_bg};
        width: 2px; /* Thinner handle */
        height: 2px;
        border: 1px solid {base_color};
        margin: 0px;
    }}
    
    QSplitter::handle:hover {{
        background-color: {base_color};
    }}
    
    /* System context panel styling (already adjusted) */
    QWidget#SystemContextEditor {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        font: 11pt "Consolas"; 
        padding: 5px;
        border-radius: 3px;
    }}
    
    /* Specific styling for chain-of-thought tool components */
    /* Container for the whole CoT tool */
    QWidget#ThoughtToolContainer {{
        /* Optional: Add border or background if needed */
        background-color: {bg_color}; /* Match content area */
    }}

    QListWidget#RulesList {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        font: 8pt "Consolas"; /* Even Smaller font */
        padding: 3px;
        alternate-background-color: {bg_color};
        border-radius: 3px;
    }}
    
    
    QListWidget#RulesList::item:selected {{
        background-color: {highlight};
        color: white;
    }}
    
    QListWidget#RulesList::item:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* CoT Radio Buttons */
    QStackedWidget#CenterPanelStack QRadioButton#LastExchangeRadio, 
    QStackedWidget#CenterPanelStack QRadioButton#FullConversationRadio, 
    QStackedWidget#CenterPanelStack QRadioButton#UserMessageRadio, 
    QStackedWidget#CenterPanelStack QRadioButton#LLMReplyRadio,
    QStackedWidget#CenterPanelStack QRadioButton#AppliesToNarratorRadio, 
    QStackedWidget#CenterPanelStack QRadioButton#AppliesToCharacterRadio /* NEW */ {{
        color: {base_color}; /* Ensure color is set */
        font: 9pt "Consolas"; /* Smaller */
        spacing: 5px; /* Less spacing */
        background-color: transparent; /* Ensure no background override */
    }}
    QStackedWidget#CenterPanelStack QRadioButton#LastExchangeRadio::indicator, 
    QStackedWidget#CenterPanelStack QRadioButton#FullConversationRadio::indicator, 
    QStackedWidget#CenterPanelStack QRadioButton#UserMessageRadio::indicator, 
    QStackedWidget#CenterPanelStack QRadioButton#LLMReplyRadio::indicator,
    QStackedWidget#CenterPanelStack QRadioButton#AppliesToNarratorRadio::indicator, 
    QStackedWidget#CenterPanelStack QRadioButton#AppliesToCharacterRadio::indicator /* NEW */ {{
        width: 13px; /* Smaller */
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color}; /* Thinner border */
        background: {bg_color};
    }}
    QStackedWidget#CenterPanelStack QRadioButton#LastExchangeRadio::indicator:checked, 
    QStackedWidget#CenterPanelStack QRadioButton#FullConversationRadio::indicator:checked, 
    QStackedWidget#CenterPanelStack QRadioButton#UserMessageRadio::indicator:checked, 
    QStackedWidget#CenterPanelStack QRadioButton#LLMReplyRadio::indicator:checked,
    QStackedWidget#CenterPanelStack QRadioButton#AppliesToNarratorRadio::indicator:checked, 
    QStackedWidget#CenterPanelStack QRadioButton#AppliesToCharacterRadio::indicator:checked /* NEW */ {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QStackedWidget#CenterPanelStack QRadioButton#LastExchangeRadio::indicator:hover, 
    QStackedWidget#CenterPanelStack QRadioButton#FullConversationRadio::indicator:hover, 
    QStackedWidget#CenterPanelStack QRadioButton#UserMessageRadio::indicator:hover, 
    QStackedWidget#CenterPanelStack QRadioButton#LLMReplyRadio::indicator:hover,
    QStackedWidget#CenterPanelStack QRadioButton#AppliesToNarratorRadio::indicator:hover, 
    QStackedWidget#CenterPanelStack QRadioButton#AppliesToCharacterRadio::indicator:hover /* NEW */ {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    
    /* Additional radio buttons that need styling */
    QRadioButton#PrependRadio, QRadioButton#AppendRadio, QRadioButton#ReplaceRadio, 
    QRadioButton#FirstSysMsgRadio, QRadioButton#LastSysMsgRadio,
    /* NEW: Add Condition and Action Scope Radios */
    QRadioButton#ConditionVarScopeGlobalRadio, QRadioButton#ConditionVarScopeCharacterRadio,
    QRadioButton#ConditionVarScopePlayerRadio,
    QRadioButton#ConditionVarScopeSettingRadio,
    QRadioButton#ActionVarScopeGlobalRadio, QRadioButton#ActionVarScopeCharacterRadio, QRadioButton#ActionVarScopePlayerRadio, QRadioButton#ActionVarScopeSceneCharsRadio, QRadioButton#ActionVarScopeSettingRadio
    /* END NEW */
    {{
        color: {base_color}; /* Ensure color is set */
        font: 9pt "Consolas"; /* Smaller */
        spacing: 5px; /* Less spacing */
        background-color: transparent; /* Ensure no background override */
    }}
    QRadioButton#PrependRadio::indicator, QRadioButton#AppendRadio::indicator, QRadioButton#ReplaceRadio::indicator,
    QRadioButton#FirstSysMsgRadio::indicator, QRadioButton#LastSysMsgRadio::indicator,
    /* NEW: Add Condition and Action Scope Radio Indicators */
    QRadioButton#ConditionVarScopeGlobalRadio::indicator, QRadioButton#ConditionVarScopeCharacterRadio::indicator,
    QRadioButton#ConditionVarScopePlayerRadio::indicator,
    QRadioButton#ConditionVarScopeSettingRadio::indicator,
    QRadioButton#ActionVarScopeGlobalRadio::indicator, QRadioButton#ActionVarScopeCharacterRadio::indicator, QRadioButton#ActionVarScopePlayerRadio::indicator, QRadioButton#ActionVarScopeSceneCharsRadio::indicator, QRadioButton#ActionVarScopeSettingRadio::indicator
    /* END NEW */
    {{
        width: 13px; /* Smaller */
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color}; /* Thinner border */
        background: {bg_color};
    }}
    QRadioButton#PrependRadio::indicator:checked, QRadioButton#AppendRadio::indicator:checked, QRadioButton#ReplaceRadio::indicator:checked,
    QRadioButton#FirstSysMsgRadio::indicator:checked, QRadioButton#LastSysMsgRadio::indicator:checked,
    /* NEW: Add Condition and Action Scope Radio Checked Indicators */
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:checked, QRadioButton#ConditionVarScopeCharacterRadio::indicator:checked,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:checked,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:checked,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:checked, QRadioButton#ActionVarScopeCharacterRadio::indicator:checked, QRadioButton#ActionVarScopePlayerRadio::indicator:checked, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:checked, QRadioButton#ActionVarScopeSettingRadio::indicator:checked
    /* END NEW */
    {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#PrependRadio::indicator:hover, QRadioButton#AppendRadio::indicator:hover, QRadioButton#ReplaceRadio::indicator:hover,
    QRadioButton#FirstSysMsgRadio::indicator:hover, QRadioButton#LastSysMsgRadio::indicator:hover,
    /* NEW: Add Condition and Action Scope Radio Hover Indicators */
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:hover, QRadioButton#ConditionVarScopeCharacterRadio::indicator:hover,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:hover,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:hover,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:hover, QRadioButton#ActionVarScopeCharacterRadio::indicator:hover, QRadioButton#ActionVarScopePlayerRadio::indicator:hover, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:hover, QRadioButton#ActionVarScopeSettingRadio::indicator:hover
    /* END NEW */
    {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    
    /* Fix System Message Position label size */
    QLabel#SysMsgPositionLabel {{
        color: {base_color};
        font: 10pt "Consolas"; /* Match the PositionLabel size */
    }}
    
    /* CoT Buttons - General small style */
    QWidget#ThoughtToolContainer QPushButton {{
        font: 9pt "Consolas"; /* Smaller font */
        padding: 3px 6px; /* Reduced padding */
        min-height: 20px; /* Smaller height */
        border-radius: 3px;
        color: {base_color}; /* Ensure color */
        background-color: {bg_color}; /* Ensure background */
        border: 1px solid {base_color}; /* Ensure border */
    }}
    QWidget#ThoughtToolContainer QPushButton:hover {{
        background-color: {highlight}; 
        color: white;
        border: 1px solid {brighter};
    }}
        QWidget#ThoughtToolContainer QPushButton:checked {{
            background-color: {highlight}; 
            color: white;
            border: 1px solid {brighter};
        }}

    /* CoT Specific Buttons by Name */
    QPushButton#AddPairButton, QPushButton#RemovePairButton, QPushButton#SaveRulesButton, QPushButton#DeleteRuleButton, QPushButton#PrependButton, QPushButton#AppendButton {{
        font: 9pt "Consolas";
        padding: 3px 6px;
        min-height: 20px;
        border-radius: 3px;
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
    }}

    /* NEW: Style for Rule Manager Buttons */
    QPushButton#RuleManagerButton {{
        font: 8pt "Consolas"; /* Even smaller font */
        padding: 1px 4px; /* Reduced padding significantly */
        min-height: 20px; /* Changed to 20px */
        max-height: 20px; /* Changed to 20px */
        /* Inherits border, background, color, hover from general CoT buttons */
    }}
    /* END NEW */

    QPushButton#RemovePairButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
    }}
    QPushButton#RemovePairButton:hover {{
        background-color: {highlight};
        color: white;
        border: 1px solid {brighter};
    }}
    QPushButton#AddPairButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        font: 9pt "Consolas";
        padding: 3px 6px;
        min-height: 20px;
        border-radius: 3px;
    }}
    QPushButton#AddPairButton:hover {{
        background-color: {highlight};
        color: white;
        border: 1px solid {brighter};
    }}
    /* NEW: Style for Condition Add/Remove buttons */
    QPushButton#AddConditionButton, QPushButton#RemoveConditionButton {{
        font: 9pt "Consolas";
        min-height: 22px; /* Match the manager add/remove buttons */
        max-height: 22px;
        min-width: 22px;
        max-width: 22px;
        padding: 0px; /* Remove padding to keep it small */
        border: 1px solid {base_color}; /* Explicitly define border */
        /* Inherits background, color, hover from general CoT buttons */
    }}
    /* END NEW */

    /* CoT Buttons by Attribute (for dynamic names) */
    QPushButton[objectName^="add_rule_button_"] {{
        /* Inherits general small style */
        /* Add specific styling if needed, e.g., primary action color */
    }}
        QPushButton[objectName^="clear_rule_button_"] {{
            /* Inherits general small style */
            font: 8pt "Consolas"; /* Extra small */
        }}
    
    /* CoT Tag/Action Pair Styling */
    QWidget#PairWidget {{
        border: 1px solid rgba({r}, {g}, {b}, 0.2); /* Subtle border using base color */
        border-radius: 5px; 
        padding: 5px; /* Reduced padding */
        margin: 3px 0px; /* Reduced margin */
        background-color: rgba({r}, {g}, {b}, 0.05); /* Very subtle background tint */
    }}
    QScrollArea#UnifiedRuleScroll {{ 
            background-color: {darker_bg}; /* Set background for the scroll area */
            border: none; 
            border-radius: 3px;
    }}
    /* Style the viewport inside the scroll area */
    QScrollArea#UnifiedRuleScroll > QWidget > QWidget {{ 
            background-color: {darker_bg}; /* Match scroll area background */
    }}
    QWidget#PairsContainer {{ 
            background-color: transparent; /* Container inside viewport is transparent */
    }}
    QWidget#TagActionsContainer {{ 
            background-color: {darker_bg}; /* Set background for actions container */
            border-radius: 3px;
    }}

    /* ADDED: Styling for Turn Spinner */
    QSpinBox#TurnSpinner {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 1px 3px; /* Less vertical padding */
        min-width: 40px; /* Adjust width */
        max-width: 60px;
    }}
    QSpinBox#TurnSpinner::up-button, QSpinBox#TurnSpinner::down-button {{
        background-color: {base_color};
        border: 1px solid {bg_color};
        width: 12px; /* Smaller buttons */
        subcontrol-origin: border;
        subcontrol-position: right; /* Position buttons on the right */
        margin: 1px;
    }}
    QSpinBox#TurnSpinner::up-button {{
            subcontrol-position: top right; /* Place up button top right */
    }}
    QSpinBox#TurnSpinner::down-button {{
            subcontrol-position: bottom right; /* Place down button bottom right */
    }}
    QSpinBox#TurnSpinner::up-arrow, QSpinBox#TurnSpinner::down-arrow {{
        width: 0px; height: 0px; /* Hide default arrows */
    }}
    QLabel#TurnSpinnerLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        background-color: transparent;
        padding-left: 5px; /* Add some space before the spinner */
    }}
    /* --- END ADDED --- */

    /* Style for the tab-specific input field */
    ChatbotInputField {{ 
        color: {input_text_color}; /* Use the calculated darker color */
        background-color: {bg_color}; 
        border: 2px solid {base_color};
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 16pt "Consolas";
    }}

    /* ADDED: Styling for Condition Turn Spinner */
    QSpinBox#ConditionTurnSpinner {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 1px 3px; /* Less vertical padding */
        min-width: 40px; /* Adjust width */
        max-width: 60px;
    }}
    QSpinBox#ConditionTurnSpinner::up-button, QSpinBox#ConditionTurnSpinner::down-button {{
        background-color: {base_color};
        border: 1px solid {bg_color};
        width: 12px; /* Smaller buttons */
        subcontrol-origin: border;
        subcontrol-position: right; /* Position buttons on the right */
        margin: 1px;
    }}
    QSpinBox#ConditionTurnSpinner::up-button {{
            subcontrol-position: top right; /* Place up button top right */
    }}
    QSpinBox#ConditionTurnSpinner::down-button {{
            subcontrol-position: bottom right; /* Place down button bottom right */
    }}
    QSpinBox#ConditionTurnSpinner::up-arrow, QSpinBox#ConditionTurnSpinner::down-arrow {{
        width: 0px; height: 0px; /* Hide default arrows */
    }}
    /* Remove old #TurnSpinner specific styling if it exists (prevent duplication) */
    QSpinBox#TurnSpinner {{ /* Remove this block if found */
        /* ... old styles ... */
    }}
    QLabel#TurnSpinnerLabel {{ /* Remove this block if found */
        /* ... old styles ... */
    }}
    /* --- END ADDED/REMOVED --- */

    /* Style for the tab-specific input field */
    ChatbotInputField {{ 
        color: {input_text_color}; /* Use the calculated darker color */
        background-color: {bg_color}; 
        border: 2px solid {base_color};
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 16pt "Consolas";
    }}

    /* NEW: Target Pair Action Type Selector */
    QComboBox#PairActionTypeSelector {{
        color: {base_color}; 
        background-color: {darker_bg}; /* Match list bg */
        border: 1px solid {base_color}; 
        padding: 3px; 
        font: 9pt "Consolas"; /* Smaller */
        border-radius: 3px;
        min-width: 90px; /* Adjust as needed */
    }}
    QComboBox#PairActionTypeSelector::drop-down {{
        border: none;
    }}
    QComboBox#PairActionTypeSelector::down-arrow {{
        image: none;
    }}
    QComboBox#PairActionTypeSelector QAbstractItemView {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}
    /* End NEW */
    
    /* --- START ADDITION --- */
    /* Ensure action value widgets within a PairWidget are styled */
    QWidget#PairWidget QTextEdit {{ /* Target any QTextEdit within PairWidget */
        color: {base_color};
        background-color: {darker_bg}; /* Match list bg */
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas"; /* Smaller */
        border-radius: 3px;
        padding: 3px;
    }}
    QWidget#PairWidget QLineEdit {{ /* Target any QLineEdit within PairWidget */
        color: {base_color};
        background-color: {darker_bg}; /* Match list bg */
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas"; /* Smaller */
        border-radius: 3px;
        padding: 3px;
    }}
    
    /* Style the action position container and its radio buttons */
    QWidget#ActionPositionContainer {{
        background-color: rgba({r}, {g}, {b}, 0.05); /* Match the subtle tint of PairWidget */
        border-radius: 3px;
        margin: 2px 0px;
        padding: 3px;
        border: 1px solid rgba({r}, {g}, {b}, 0.1); /* Very subtle border */
    }}
    
    QLabel#ActionPositionLabel, QLabel#ActionSysMsgPosLabel {{
        color: {base_color};
        font: 9pt "Consolas";
        background-color: transparent;
    }}
    
    QRadioButton#ActionPrependRadio, QRadioButton#ActionAppendRadio, QRadioButton#ActionReplaceRadio,
    QRadioButton#ActionFirstSysMsgRadio, QRadioButton#ActionLastSysMsgRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    
    QRadioButton#ActionPrependRadio::indicator, QRadioButton#ActionAppendRadio::indicator, 
    QRadioButton#ActionReplaceRadio::indicator, QRadioButton#ActionFirstSysMsgRadio::indicator,
    QRadioButton#ActionLastSysMsgRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    
    QRadioButton#ActionPrependRadio::indicator:checked, QRadioButton#ActionAppendRadio::indicator:checked,
    QRadioButton#ActionReplaceRadio::indicator:checked, QRadioButton#ActionFirstSysMsgRadio::indicator:checked,
    QRadioButton#ActionLastSysMsgRadio::indicator:checked {{
        background-color: {highlight};
        border: 1px solid {brighter};
    }}
    
    QRadioButton#ActionPrependRadio::indicator:hover, QRadioButton#ActionAppendRadio::indicator:hover,
    QRadioButton#ActionReplaceRadio::indicator:hover, QRadioButton#ActionFirstSysMsgRadio::indicator:hover,
    QRadioButton#ActionLastSysMsgRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    
    /* Force Narrator Order Radio Buttons */
    QLabel#ForceNarratorOrderLabel {{
        color: {base_color};
        font: 9pt "Consolas";
        background-color: transparent;
    }}
    
    QRadioButton#ForceNarratorOrderFirstRadio, QRadioButton#ForceNarratorOrderLastRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    
    QRadioButton#ForceNarratorOrderFirstRadio::indicator, QRadioButton#ForceNarratorOrderLastRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    
    QRadioButton#ForceNarratorOrderFirstRadio::indicator:checked, QRadioButton#ForceNarratorOrderLastRadio::indicator:checked {{
        background-color: {highlight};
        border: 1px solid {brighter};
    }}
    
    QRadioButton#ForceNarratorOrderFirstRadio::indicator:hover, QRadioButton#ForceNarratorOrderLastRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END ADDITION --- */
    
    QTabWidget::pane {{
        border: 2px solid {base_color};
        border-radius: 5px;
    }}

    /* NEW: Target the specific Conditions Operator Combo */
    QComboBox#ConditionsOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg}; /* Match list bg */
        border: 1px solid {base_color};
        padding: 2px; /* Reduced padding */
        font: 9pt "Consolas"; /* Smaller */
        border-radius: 3px;
        min-width: 90px; /* Adjust width as needed */
    }}
    QComboBox#ConditionsOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#ConditionsOperatorCombo::down-arrow {{
        image: none;
    }}
    QComboBox#ConditionsOperatorCombo QAbstractItemView {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}
    /* END NEW */

    /* NEW: Target the specific Conditions Operator Label */
    QLabel#ConditionsOperatorLabel {{
        color: {base_color};
        font: 9pt "Consolas"; /* Smaller */
        background-color: transparent;
        padding: 0px 3px 0px 0px; /* Adjust padding if needed */
        margin-right: 5px; /* Add spacing */
    }}

    QLineEdit#RulesFilterInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
    }}
    
    /* Setting Manager Widget Styles */
    QWidget#SettingManagerContainer {{ 
        background-color: {bg_color}; 
    }}
    
    /* --- Connections Section Styling --- */
    QGroupBox#SettingConnectionsGroup {{
        border: 1px solid {base_color};
        border-radius: 5px;
        margin-top: 10px;
        margin-bottom: 5px;
        padding-top: 12px; /* space for the title */
        background-color: {darker_bg};
    }}
    QGroupBox#SettingConnectionsGroup:title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 4px;
        color: {base_color};
        font: bold 11pt "Consolas";
        background: transparent;
    }}
    QLabel#ConnectionLabel {{
        color: {base_color};
        font: bold 10pt "Consolas";
        margin-top: 2px;
        margin-bottom: 2px;
    }}
    
    QWidget#ConnectionListItem {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 4px;
        margin: 3px;
    }}
    
    QComboBox#SettingManagerDropdown {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 9pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    /* --- End Connections Section Styling --- */
    
    QLabel#SettingManagerLabel {{ 
        color: {base_color}; 
        font: 11pt "Consolas";
        margin-right: 10px;
    }}
    
    QListWidget#SettingManagerList {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        alternate-background-color: {bg_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
    }}
    
    QListWidget#SettingManagerList::item:selected {{
        background-color: {highlight};
        color: white;
    }}
    
    QListWidget#SettingManagerList::item:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* Setting Manager Table Style */
    QTableWidget#SettingManagerTable {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        alternate-background-color: {bg_color};
        border-radius: 3px;
        gridline-color: rgba({r}, {g}, {b}, 0.3);
        font: 10pt "Consolas";
        outline: none;
    }}
    QTableWidget#SettingManagerTable::item {{
        padding: 4px;
        border: none;
        outline: none;
    }}
    QTableWidget#SettingManagerTable::item:selected {{
        background-color: {highlight};
        color: white;
        outline: none;
    }}
    QTableWidget#SettingManagerTable::item:focus {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {highlight};
        outline: none;
    }}
    QHeaderView#SettingManagerTableHeader {{
        background-color: {bg_color};
        color: {base_color};
        border: 1px solid {base_color};
        font: 10pt "Consolas";
        font-weight: bold;
    }}
    QHeaderView#SettingManagerTableHeader::section {{
        background-color: {bg_color};
        color: {base_color};
        border: 1px solid {base_color};
        padding: 4px;
        font-weight: bold;
    }}
    QHeaderView#SettingManagerTableHeader::section:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* NEW: Setting Manager Name/Description Inputs */
    QLineEdit#SettingManagerNameInput, QTextEdit#SettingManagerDescInput {{
        color: {base_color};
        background-color: {darker_bg}; /* Match list background */
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#SettingManagerEditLabel {{ /* Existing label for edits */
        color: {base_color}; /* Change from #DDDDDD to base_color */
        font: 9pt "Consolas";
        margin-right: 5px; /* Add some space */
    }}
    /* END NEW */

    /* NEW: Actor Manager Item Labels and Inputs */
    QLabel#ActorManagerItemLabel {{
        color: {base_color};
        font: 9pt "Consolas"; /* Small font for item labels */
    }}
    QLineEdit#ActorManagerItemInput {{
        color: {base_color};
        background-color: {darker_bg}; /* Match other list/input backgrounds */
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match Name/Desc inputs */
        selection-background-color: {highlight};
        selection-color: white;
    }}
    /* END NEW */



    /* ADDED: Styling for Scene Count Spinner */
    QSpinBox#ConditionSceneCountSpinner {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 1px 3px; /* Less vertical padding */
        min-width: 40px; /* Adjust width */
        max-width: 60px;
    }}
    QSpinBox#ConditionSceneCountSpinner::up-button, QSpinBox#ConditionSceneCountSpinner::down-button {{
        background-color: {base_color};
        border: 1px solid {bg_color};
        width: 12px; /* Smaller buttons */
        subcontrol-origin: border;
        subcontrol-position: right; /* Position buttons on the right */
        margin: 1px;
    }}
    QSpinBox#ConditionSceneCountSpinner::up-button {{
            subcontrol-position: top right; /* Place up button top right */
    }}
    QSpinBox#ConditionSceneCountSpinner::down-button {{
            subcontrol-position: bottom right; /* Place down button bottom right */
    }}
    QSpinBox#ConditionSceneCountSpinner::up-arrow, QSpinBox#ConditionSceneCountSpinner::down-arrow {{
        width: 0px; height: 0px; /* Hide default arrows */
    }}
    /* END ADDED */

    /* ADDED: Styling for Game Time Value Spinner */
    QSpinBox#GameTimeValueSpinner {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 1px 3px; /* Less vertical padding */
        min-width: 40px; /* Adjust width */
        max-width: 60px;
    }}
    QSpinBox#GameTimeValueSpinner::up-button, QSpinBox#GameTimeValueSpinner::down-button {{
        background-color: {base_color};
        border: 1px solid {bg_color};
        width: 12px; /* Smaller buttons */
        subcontrol-origin: border;
        subcontrol-position: right; /* Position buttons on the right */
        margin: 1px;
    }}
    QSpinBox#GameTimeValueSpinner::up-button {{
            subcontrol-position: top right; /* Place up button top right */
    }}
    QSpinBox#GameTimeValueSpinner::down-button {{
            subcontrol-position: bottom right; /* Place down button bottom right */
    }}
    QSpinBox#GameTimeValueSpinner::up-arrow, QSpinBox#GameTimeValueSpinner::down-arrow {{
        width: 0px; height: 0px; /* Hide default arrows */
    }}
    /* END ADDED */

    /* ADDED: Horizontal Separator Style */
    QFrame#SettingManagerHSeparator {{
        border: none;
        border-top: 1px solid rgba({r}, {g}, {b}, 0.3); /* Use base color with low alpha */
        margin: 5px 0px; /* Add some vertical margin */
    }}
    /* END ADDED */

    QLineEdit#FilterInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 9pt "Consolas"; /* Slightly smaller font */
    }}

    /* Actor Manager List Style */
    QListWidget#ActorManagerList {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        alternate-background-color: {bg_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
    }}

    QListWidget#ActorManagerList::item:selected {{
        background-color: {highlight};
        color: white;
    }}

    QListWidget#ActorManagerList::item:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* Actor Manager: Relations Container (Main widget, might not be visible bg) */
    QWidget#RelationsContainer {{
        background-color: transparent; /* Make outer container transparent */
        border: none; /* No border on outer container */
    }}

    /* Actor Manager: Relations Scroll Area */
    QScrollArea#RelationsScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Actor Manager: Relations Scroll Area Content Widget */
    QScrollArea#RelationsScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Actor Manager: Variables Scroll Area */
    QScrollArea#VariablesScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Actor Manager: Variables Scroll Area Content Widget */
    QScrollArea#VariablesScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Time Manager: Main Scroll Area */
    QScrollArea#TimeManagerScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Time Manager: Main Scroll Area Content Widget */
    QScrollArea#TimeManagerScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Actor Manager: Inventory Container Border and Background */
    QWidget#InventoryContainer {{
        background-color: {darker_bg}; /* Use darker background like lists */
        border: none; /* Remove outer border to avoid nested borders */
        border-radius: 3px;
    }}

    /* NEW: Actor Manager Name/Description Inputs */
    QLineEdit#ActorManagerNameInput, QTextEdit#ActorManagerDescInput {{
        color: {base_color};
        background-color: {darker_bg}; /* Match list background */
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#ActorManagerEditLabel {{ /* Label for actor edits */
        color: {base_color};
        font: 9pt "Consolas";
        margin-right: 5px; /* Add some space */
    }}
    
    /* Character Name Input Styling for Rules Manager */
    QLineEdit#CharacterNameInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#CharacterNameLabel {{
        color: {base_color};
        font: 12pt "Consolas";
        background-color: transparent;
    }}
    /* END NEW */

    QCheckBox {{
        color: {base_color};
        font: 9pt 'Consolas';
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 3px;
        background: transparent;
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:unchecked {{
        background: transparent;
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:disabled {{
        background: #333;
        border: 1.5px solid #444;
    }}

    /* Style for Optional Model Override Input */
    QLineEdit#ModelOverrideInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerNameInput */
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Style for Additional Instructions Input */
    QTextEdit#AdditionalInstructionsInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerDescInput */
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Container for Holding/Wearing content - no border */
    QWidget#InventoryContentContainer {{
        border: none;
        background-color: transparent;
    }}

    /* Add border to Inventory scroll area */
    QScrollArea#InventoryScrollArea {{
        border: 1px solid {base_color};
        border-radius: 3px;
        background-color: {darker_bg};
        margin-top: 4px; /* Add some space below the Inventory: label */
    }}

    /* --- NEW: Change Actor Location Action Widgets --- */
    QWidget#ChangeLocationWidget {{ /* Container for the whole action */
        background-color: rgba({r}, {g}, {b}, 0.05); /* Subtle tint like PairWidget */
        border-radius: 3px;
        padding: 4px;
        margin-top: 2px;
        border: 1px solid rgba({r}, {g}, {b}, 0.1); /* Very subtle border */
    }}

    QComboBox#ChangeLocationActorSelector, QComboBox#ChangeLocationTargetSettingCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        padding: 3px;
        font: 9pt "Consolas";
        border-radius: 3px;
        min-width: 120px;
    }}
    QComboBox#ChangeLocationActorSelector::drop-down, QComboBox#ChangeLocationTargetSettingCombo::drop-down {{
        border: none;
    }}
    QComboBox#ChangeLocationActorSelector::down-arrow, QComboBox#ChangeLocationTargetSettingCombo::down-arrow {{
        image: none;
    }}
    QComboBox#ChangeLocationActorSelector QAbstractItemView, QComboBox#ChangeLocationTargetSettingCombo QAbstractItemView {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Style the completer popup for Target Setting */
    QComboBox QAbstractItemView#qt_scrollarea_viewport {{
        border: 1px solid {base_color};
        background-color: {darker_bg};
        color: {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QRadioButton#ChangeLocationAdjacentRadio, QRadioButton#ChangeLocationFastTravelRadio, QRadioButton#ChangeLocationSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator, QRadioButton#ChangeLocationFastTravelRadio::indicator, QRadioButton#ChangeLocationSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator:checked, QRadioButton#ChangeLocationFastTravelRadio::indicator:checked, QRadioButton#ChangeLocationSettingRadio::indicator:checked {{
        background-color: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator:hover, QRadioButton#ChangeLocationFastTravelRadio::indicator:hover, QRadioButton#ChangeLocationSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}
    /* --- END NEW --- */

    /* --- NEW: Style for Condition and Action Scope Radio Buttons --- */
    QRadioButton#ConditionVarScopeGlobalRadio, QRadioButton#ConditionVarScopeCharacterRadio,
    QRadioButton#ConditionVarScopePlayerRadio,
    QRadioButton#ConditionVarScopeSettingRadio,
    QRadioButton#ActionVarScopeGlobalRadio, QRadioButton#ActionVarScopeCharacterRadio, QRadioButton#ActionVarScopePlayerRadio, QRadioButton#ActionVarScopeSceneCharsRadio, QRadioButton#ActionVarScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator, QRadioButton#ConditionVarScopeCharacterRadio::indicator,
    QRadioButton#ConditionVarScopePlayerRadio::indicator,
    QRadioButton#ConditionVarScopeSettingRadio::indicator,
    QRadioButton#ActionVarScopeGlobalRadio::indicator, QRadioButton#ActionVarScopeCharacterRadio::indicator, QRadioButton#ActionVarScopePlayerRadio::indicator, QRadioButton#ActionVarScopeSceneCharsRadio::indicator, QRadioButton#ActionVarScopeSettingRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:checked, QRadioButton#ConditionVarScopeCharacterRadio::indicator:checked,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:checked,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:checked,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:checked, QRadioButton#ActionVarScopeCharacterRadio::indicator:checked, QRadioButton#ActionVarScopePlayerRadio::indicator:checked, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:checked, QRadioButton#ActionVarScopeSettingRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:hover, QRadioButton#ConditionVarScopeCharacterRadio::indicator:hover,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:hover,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:hover,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:hover, QRadioButton#ActionVarScopeCharacterRadio::indicator:hover, QRadioButton#ActionVarScopePlayerRadio::indicator:hover, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:hover, QRadioButton#ActionVarScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* --- NEW: Style for Text Tag Mode Radio Buttons --- */
    QRadioButton#TagOverwriteRadio, QRadioButton#TagAppendRadio, QRadioButton#TagPrependRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TagOverwriteRadio::indicator, QRadioButton#TagAppendRadio::indicator, QRadioButton#TagPrependRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#TagOverwriteRadio::indicator:checked, QRadioButton#TagAppendRadio::indicator:checked, QRadioButton#TagPrependRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#TagOverwriteRadio::indicator:hover, QRadioButton#TagAppendRadio::indicator:hover, QRadioButton#TagPrependRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* Additional radio buttons that need styling (Keep for others like Prepend/Append/Replace/First/Last) */
    QRadioButton#PrependRadio, QRadioButton#AppendRadio, QRadioButton#ReplaceRadio, 
    QRadioButton#FirstSysMsgRadio, QRadioButton#LastSysMsgRadio
    {{
        color: {base_color}; /* Ensure color is set */
        font: 9pt "Consolas"; /* Smaller */
        spacing: 5px; /* Less spacing */
        background-color: transparent; /* Ensure no background override */
    }}
    QRadioButton#PrependRadio::indicator, QRadioButton#AppendRadio::indicator, QRadioButton#ReplaceRadio::indicator,
    QRadioButton#FirstSysMsgRadio::indicator, QRadioButton#LastSysMsgRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#PrependRadio::indicator:checked, QRadioButton#AppendRadio::indicator:checked, QRadioButton#ReplaceRadio::indicator:checked,
    QRadioButton#FirstSysMsgRadio::indicator:checked, QRadioButton#LastSysMsgRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#PrependRadio::indicator:hover, QRadioButton#AppendRadio::indicator:hover, QRadioButton#ReplaceRadio::indicator:hover,
    QRadioButton#FirstSysMsgRadio::indicator:hover, QRadioButton#LastSysMsgRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* NEW: Actor Manager Variable Name/Value Inputs */
    QLineEdit#ActorManagerVarNameInput, QLineEdit#ActorManagerVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    /* Highlight for selected variable row */
    QWidget.VariableRowSelected {{
        background-color: {highlight};
        border-radius: 3px;
    }}

    /* --- Timer Rules Styling --- */
    QWidget#TimerRulesContainer {{
        background-color: {bg_color}; /* Ensure base container has background */
        color: {base_color};
    }}
    
    QLabel#TimerRulesTitle {{ /* Assuming this exists or might be added later */
        color: {base_color};
        font: bold 12pt "Consolas";
    }}
    
    QLabel#TimerRulesDescription {{ /* Assuming this exists or might be added later */
        color: {base_color};
        font: 10pt "Consolas";
    }}
    
    QWidget#TimerRulesListControls {{ /* Parent of Rule ID/Desc and filter/list */
        background-color: {bg_color};
    }}
    
    QLineEdit#TimerRulesFilterInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}
    
    QListWidget#TimerRulesList {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        border-radius: 3px;
        alternate-background-color: {bg_color};
        font: 9pt "Consolas";
    }}
    QListWidget#TimerRulesList::item:selected {{
        background-color: {highlight};
        color: white;
    }}
    QListWidget#TimerRulesList::item:hover {{
        background-color: {highlight};
        color: white; 
    }}
    
    QPushButton#TimerRuleAddButton, QPushButton#TimerRuleRemoveButton,
    QPushButton#TimerRuleMoveUpButton, QPushButton#TimerRuleMoveDownButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 2px;
    }}
    QPushButton#TimerRuleAddButton:hover, QPushButton#TimerRuleRemoveButton:hover,
    QPushButton#TimerRuleMoveUpButton:hover, QPushButton#TimerRuleMoveDownButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    
    /* Left and Right Panel Base Styling */
    QWidget#TimerRightPanelWidget,
    QWidget#TimerLeftPanelWidget {{
        background-color: {bg_color};
    }}
    QScrollArea#TimerRightPanelScroll,
    QScrollArea#TimerLeftPanelScroll {{
        background-color: transparent; 
        border: none;
    }}
    QScrollArea#TimerLeftPanelScroll > QWidget > QWidget {{ /* Viewport content of left scroll */
        background-color: {bg_color}; 
    }}
     QScrollArea#TimerRightPanelScroll > QWidget > QWidget {{ /* Viewport content of right scroll */
        background-color: {bg_color}; 
    }}

    /* Titles within Panels */
    QLabel#TimerConditionsTitleLabel {{
        color: {base_color};
        font: bold 11pt "Consolas"; 
        margin-bottom: 5px; 
    }}
    QLabel#TimerRuleActionsLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: bold; 
    }}

    /* Labels for specific inputs (Rule ID, Desc, Intervals, Var Conditions) */
    QLabel#TimerRuleIdLabel, QLabel#TimerRuleDescLabel, 
    QLabel#TimerRuleIntervalLabel,
    QLabel#TimerRuleGameTimeIntervalLabel,
    QLabel#TimerRuleGameMinutesLabel,
    QLabel#TimerRuleGameHoursLabel,
    QLabel#TimerRuleGameDaysLabel,
    QLabel#TimerRuleConditionVarNameLabel, 
    QLabel#TimerRuleConditionVarValueLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: normal; /* Explicitly normal */
    }}
    
    /* LineEdits for Rule ID, Description, and Variable Conditions */
    QLineEdit#TimerRuleIdInput, QLineEdit#TimerRuleDescInput,
    QLineEdit#TimerRuleConditionVarNameInput, QLineEdit#TimerRuleConditionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas"; /* Changed from 9pt for consistency */
    }}
    
    /* General SpinBox styling for fixed value inputs in Conditions Panel */
    QSpinBox#TimerRuleIntervalInput,
    QSpinBox#TimerRuleGameMinutesInput,
    QSpinBox#TimerRuleGameHoursInput,
    QSpinBox#TimerRuleGameDaysInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
    }}
    /* Buttons for these general spinboxes */
    QSpinBox#TimerRuleIntervalInput::up-button, QSpinBox#TimerRuleIntervalInput::down-button,
    QSpinBox#TimerRuleGameMinutesInput::up-button, QSpinBox#TimerRuleGameMinutesInput::down-button,
    QSpinBox#TimerRuleGameHoursInput::up-button, QSpinBox#TimerRuleGameHoursInput::down-button,
    QSpinBox#TimerRuleGameDaysInput::up-button, QSpinBox#TimerRuleGameDaysInput::down-button {{
        background-color: {base_color}; 
        border: 1px solid {bg_color};
        width: 12px;
        min-height: 10px;
        subcontrol-origin: border;
        margin: 1px;
    }}
    /* Arrows for these general spinboxes */
    QSpinBox#TimerRuleIntervalInput::up-arrow, QSpinBox#TimerRuleIntervalInput::down-arrow,
    QSpinBox#TimerRuleGameMinutesInput::up-arrow, QSpinBox#TimerRuleGameMinutesInput::down-arrow,
    QSpinBox#TimerRuleGameHoursInput::up-arrow, QSpinBox#TimerRuleGameHoursInput::down-arrow,
    QSpinBox#TimerRuleGameDaysInput::up-arrow, QSpinBox#TimerRuleGameDaysInput::down-arrow {{
        width: 0px; 
        height: 0px;
    }}

    /* Styling for Timer Rule Condition Radio Buttons */
    QRadioButton#TimerRuleConditionAlwaysRadio, QRadioButton#TimerRuleConditionVariableRadio {{
        color: {base_color};
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator, QRadioButton#TimerRuleConditionVariableRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator:checked, QRadioButton#TimerRuleConditionVariableRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator:hover, QRadioButton#TimerRuleConditionVariableRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* Styling for Timer Rule Random Interval Checkboxes */
    QCheckBox#TimerRuleIntervalRandomCheckbox,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox,
    QCheckBox#TimerRuleGameHoursRandomCheckbox,
    QCheckBox#TimerRuleGameDaysRandomCheckbox {{
        color: {base_color};
        font: 10pt "Consolas"; 
        spacing: 5px;
        background-color: transparent;
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 3px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator:checked {{
        background-color: {base_color};
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* Styling for Timer Rule Random Interval Min/Max SpinBoxes */
    QSpinBox#TimerRuleIntervalMinInput, QSpinBox#TimerRuleIntervalMaxInput,
    QSpinBox#TimerRuleGameMinutesMinInput, QSpinBox#TimerRuleGameMinutesMaxInput,
    QSpinBox#TimerRuleGameHoursMinInput, QSpinBox#TimerRuleGameHoursMaxInput,
    QSpinBox#TimerRuleGameDaysMinInput, QSpinBox#TimerRuleGameDaysMaxInput {{
        color: {base_color};
        background-color: {darker_bg}; 
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px 3px; 
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
        min-width: 60px; 
    }}
    /* Buttons for these Min/Max spinboxes */
    QSpinBox#TimerRuleIntervalMinInput::up-button, QSpinBox#TimerRuleIntervalMaxInput::up-button,
    QSpinBox#TimerRuleGameMinutesMinInput::up-button, QSpinBox#TimerRuleGameMinutesMaxInput::up-button,
    QSpinBox#TimerRuleGameHoursMinInput::up-button, QSpinBox#TimerRuleGameHoursMaxInput::up-button,
    QSpinBox#TimerRuleGameDaysMinInput::up-button, QSpinBox#TimerRuleGameDaysMaxInput::up-button,
    QSpinBox#TimerRuleIntervalMinInput::down-button, QSpinBox#TimerRuleIntervalMaxInput::down-button,
    QSpinBox#TimerRuleGameMinutesMinInput::down-button, QSpinBox#TimerRuleGameMinutesMaxInput::down-button,
    QSpinBox#TimerRuleGameHoursMinInput::down-button, QSpinBox#TimerRuleGameHoursMaxInput::down-button,
    QSpinBox#TimerRuleGameDaysMinInput::down-button, QSpinBox#TimerRuleGameDaysMaxInput::down-button {{
        background-color: {base_color};
        border: 1px solid {bg_color};
        width: 12px;
        min-height: 10px; 
        subcontrol-origin: border;
        margin: 1px;
    }}
    /* Arrows for these Min/Max spinboxes */
    QSpinBox#TimerRuleIntervalMinInput::up-arrow, QSpinBox#TimerRuleIntervalMaxInput::up-arrow,
    QSpinBox#TimerRuleGameMinutesMinInput::up-arrow, QSpinBox#TimerRuleGameMinutesMaxInput::up-arrow,
    QSpinBox#TimerRuleGameHoursMinInput::up-arrow, QSpinBox#TimerRuleGameHoursMaxInput::up-arrow,
    QSpinBox#TimerRuleGameDaysMinInput::up-arrow, QSpinBox#TimerRuleGameDaysMaxInput::up-arrow,
    QSpinBox#TimerRuleIntervalMinInput::down-arrow, QSpinBox#TimerRuleIntervalMaxInput::down-arrow,
    QSpinBox#TimerRuleGameMinutesMinInput::down-arrow, QSpinBox#TimerRuleGameMinutesMaxInput::down-arrow,
    QSpinBox#TimerRuleGameHoursMinInput::down-arrow, QSpinBox#TimerRuleGameHoursMaxInput::down-arrow,
    QSpinBox#TimerRuleGameDaysMinInput::down-arrow, QSpinBox#TimerRuleGameDaysMaxInput::down-arrow {{
        width: 0px; 
        height: 0px;
    }}
    
    /* Enable/Disable Checkbox */
    QCheckBox#TimerRuleEnableCheckbox {{
        color: {base_color};
        font: 10pt "Consolas";
        /* Standard checkbox indicator styling will be inherited if not overridden here */
    }}
    
    /* Actions Area */
    QWidget#TimerRuleActionsContainer {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
    }}
    QWidget#TimerRuleActionRow {{
        background-color: {darker_bg}; /* Ensure rows also have this if they are separate widgets */
    }}
    QComboBox#TimerRuleActionTypeCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 9pt "Consolas";
    }}
    QComboBox#TimerRuleActionTypeCombo::drop-down {{
        border: none;
    }}
    QComboBox#TimerRuleActionTypeCombo::down-arrow {{
        image: none;
    }}
    QLineEdit#TimerRuleActionValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}
    QPushButton#TimerRuleActionRemoveButton {{
        color: {base_color};
        background-color: {darker_bg}; /* Changed from bg_color to match other small buttons */
        border: 1px solid {base_color};
        border-radius: 2px; /* Consistent with other small buttons */
    }}
    QPushButton#TimerRuleActionRemoveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    
    /* Main Action Buttons (Add Action, Save Rule) */
    QPushButton#TimerRuleAddActionButton, QPushButton#TimerRuleSaveButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color}; /* Ensure consistent border */
        border-radius: 3px;
        padding: 5px; /* Default padding from general QPushButton */
        font: 10pt "Consolas"; /* Slightly smaller than general QPushButton if needed */
    }}
    QPushButton#TimerRuleAddActionButton:hover, QPushButton#TimerRuleSaveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    /* --- End Timer Rules Styling --- */

    /* --- Styling for Start After Label --- */
    QLabel#TimerRuleStartAfterLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        /* margin-right: 5px; */ /* Add if more space needed before radios */
    }}

    /* --- Styling for Timer Rule Start After Radio Buttons --- */
    QRadioButton#TimerRuleStartAfterPlayerRadio, QRadioButton#TimerRuleStartAfterCharacterRadio, QRadioButton#TimerRuleStartAfterSceneChangeRadio {{
        color: {base_color};
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px; /* For round radio buttons */
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator:checked, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator:checked, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator:hover, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator:hover, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* --- Styling for Timer Rule Variable Scope Radio Buttons (Global/Character) --- */
    QRadioButton#TimerRuleVarScopeGlobalRadio, QRadioButton#TimerRuleVarScopeCharacterRadio {{
        color: {base_color}; /* CORRECTED: Single braces */
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px; /* For round radio buttons */
        border: 1px solid {base_color}; /* CORRECTED: Single braces */
        background: transparent; /* CORRECTED: Single braces */
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator:checked, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator:checked {{
        background-color: {base_color}; /* CORRECTED: Single braces */
        border: 1px solid {base_color}; /* CORRECTED: Single braces */
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator:hover, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator:hover {{
        border: 1px solid {brighter}; /* CORRECTED: Single braces */
    }}

    /* --- Styling for Timer Rule Condition Variable Input Labels & LineEdits --- */
    QLabel#TimerRuleConditionVarNameLabel, QLabel#TimerRuleConditionVarValueLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: normal; /* Explicitly normal */
    }}
    QLineEdit#TimerRuleConditionVarNameInput, QLineEdit#TimerRuleConditionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas"; /* Changed from 9pt for consistency */
    }}

    /* --- Styling for MULTIPLE Variable Conditions Area --- */
    QWidget#VariableConditionsArea {{
        /* Optional: Add border/background to visually group */
        /* background-color: rgba(0,0,0, 0.1); */
        /* border: 1px dotted {base_color}; */
        /* border-radius: 3px; */
        margin-top: 5px; /* Add some space above this section */
    }}

    QLabel#TimerConditionsOperatorLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        margin-right: 5px;
    }}
    
    QComboBox#TimerConditionsOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 10pt "Consolas";
        min-width: 60px;
    }}
    QComboBox#TimerConditionsOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#TimerConditionsOperatorCombo::down-arrow {{
        image: none;
    }}

    /* Styling for widgets WITHIN each VariableConditionRow */
    QWidget#VariableConditionRow QLineEdit#ConditionVarNameInput,
    QWidget#VariableConditionRow QLineEdit#ConditionValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px; /* Slightly smaller padding */
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas"; /* Smaller font for rows */
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 80px; /* Adjust width */
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo::drop-down {{
        border: none;
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo::down-arrow {{
        image: none;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px; /* Less spacing */
        background-color: transparent;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator:checked,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator:checked,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator:hover,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator:hover,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}
    QWidget#VariableConditionRow QPushButton#RemoveVariableConditionButton {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 2px;
        min-width: 20px; /* Match size? */
        max-width: 20px;
        min-height: 20px;
        max-height: 20px;
        padding: 0px;
        font-size: 12pt; /* Adjust for '-' sign */
    }}
    QWidget#VariableConditionRow QPushButton#RemoveVariableConditionButton:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* Button to add new rows */
    QPushButton#AddVariableConditionButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        margin-top: 5px; /* Add space above button */
    }}
    QPushButton#AddVariableConditionButton:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* --- Styling for Inter-Row Operator Combo --- */
    QComboBox#ConditionRowOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 55px; /* Keep narrow */
        max-width: 55px;
    }}
    QComboBox#ConditionRowOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#ConditionRowOperatorCombo::down-arrow {{
        image: none;
    }}

    /* --- Styling for Set Var Action Specific Inputs --- */
    QLineEdit#TimerRuleActionVarNameInput,
    QLineEdit#TimerRuleActionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px; /* Smaller padding for dense row */
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}

    QComboBox#TimerRuleSetVarOperationSelector {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 65px; /* Adjust as needed */
    }}
    QComboBox#TimerRuleSetVarOperationSelector::drop-down {{
        border: none;
    }}
    QComboBox#TimerRuleSetVarOperationSelector::down-arrow {{
        image: none;
    }}

    QRadioButton#TimerRuleActionScopeGlobalRadio,
    QRadioButton#TimerRuleActionScopeCharacterRadio,
    QRadioButton#TimerRuleActionScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator:checked,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator:checked,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator:hover,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator:hover,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* NEW: Setting Manager Variable Name/Value Inputs - with more specific selector */
    QWidget#VariableRow QLineEdit#SettingManagerVarNameInput,
    QWidget#VariableRow QLineEdit#SettingManagerVarValueInput,
    QLineEdit#SettingManagerVarNameInput,
    QLineEdit#SettingManagerVarValueInput {{
        color: {base_color} !important;
        background-color: {darker_bg} !important;
        border: 1px solid {base_color} !important;
        border-radius: 3px !important;
        padding: 3px !important;
        font: 10pt "Consolas" !important;
        selection-background-color: {highlight} !important;
        selection-color: white !important;
    }}
    /* END NEW */

    QLineEdit#PathDetailsNameInput, QTextEdit#PathDetailsDescInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt 'Consolas';
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QWidget[styleClass="PathDetailsNameInput"], QWidget[styleClass="PathDetailsDescInput"] {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt 'Consolas';
        selection-background-color: {highlight};
        selection-color: white;
    }}
    
    /* World Editor Scale Inputs */
    QLineEdit#WORLDToolbar_ScaleNumberInput, QLineEdit#WORLDToolbar_ScaleTimeInput,
    QLineEdit#LOCATIONToolbar_ScaleNumberInput, QLineEdit#LOCATIONToolbar_ScaleTimeInput {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        border: 1px solid {base_color}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
        max-width: 40px;
        min-width: 35px;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown, QComboBox#LOCATIONToolbar_ScaleUnitDropdown {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        border: 1px solid {base_color}; 
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
        max-width: 70px;
        min-width: 65px;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown::drop-down, QComboBox#LOCATIONToolbar_ScaleUnitDropdown::drop-down {{
        border: none;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown::down-arrow, QComboBox#LOCATIONToolbar_ScaleUnitDropdown::down-arrow {{
        image: none;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown QAbstractItemView, QComboBox#LOCATIONToolbar_ScaleUnitDropdown QAbstractItemView {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas";
    }}
    /* --- Inventory Scroll Area Fix --- */
    QScrollArea#InventoryScrollArea {{
        background-color: {darker_bg};
    }}
    QScrollArea#InventoryScrollArea QWidget {{
        background-color: {darker_bg};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio, QRadioButton#TimerGenerateUserMsgRadio, QRadioButton#TimerGenerateFullConvoRadio,
    QRadioButton#GenerateLastExchangeRadio, QRadioButton#GenerateUserMsgRadio, QRadioButton#GenerateFullConvoRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator, QRadioButton#TimerGenerateUserMsgRadio::indicator, QRadioButton#TimerGenerateFullConvoRadio::indicator,
    QRadioButton#GenerateLastExchangeRadio::indicator, QRadioButton#GenerateUserMsgRadio::indicator, QRadioButton#GenerateFullConvoRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator:checked, QRadioButton#TimerGenerateUserMsgRadio::indicator:checked, QRadioButton#TimerGenerateFullConvoRadio::indicator:checked,
    QRadioButton#GenerateLastExchangeRadio::indicator:checked, QRadioButton#GenerateUserMsgRadio::indicator:checked, QRadioButton#GenerateFullConvoRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator:hover, QRadioButton#TimerGenerateUserMsgRadio::indicator:hover, QRadioButton#TimerGenerateFullConvoRadio::indicator:hover,
    QRadioButton#GenerateLastExchangeRadio::indicator:hover, QRadioButton#GenerateUserMsgRadio::indicator:hover, QRadioButton#GenerateFullConvoRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    
    QLabel#TimerGenerateContextLabel, QLabel#TimerGenerateInstructionsLabel,
    QLabel#GenerateContextLabel, QLabel#GenerateInstructionsLabel {{
        color: {base_color};
        font: 9pt "Consolas";
        background-color: transparent;
    }}
    
    QTextEdit#TimerGenerateInstructionsInput, QTextEdit#GenerateInstructionsInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        padding: 3px;
    }}
    
    QWidget#TimerGenerateContextWidget, QWidget#GenerateContextWidget {{
        background-color: {darker_bg};
        border-radius: 3px;
    }}

    /* --- NEW: Generate Mode Radio Buttons Styling --- */
    QRadioButton#GenerateModeLLMRadio, QRadioButton#GenerateModeRandomRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#GenerateModeLLMRadio::indicator, QRadioButton#GenerateModeRandomRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#GenerateModeLLMRadio::indicator:checked, QRadioButton#GenerateModeRandomRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#GenerateModeLLMRadio::indicator:hover, QRadioButton#GenerateModeRandomRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* --- NEW: Random Generate Panel Filter Styling --- */
    QLineEdit#SettingFilterInput, QLineEdit#CharacterFilterInput,
    QLineEdit#RandomNumberMin, QLineEdit#RandomNumberMax {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 9pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Remove old QListWidget styling that's no longer needed */
    
    /* Keep button styling for other buttons */
    QPushButton#AddSettingFilterBtn, QPushButton#RemoveSettingFilterBtn,
    QPushButton#AddCharacterFilterBtn, QPushButton#RemoveCharacterFilterBtn {{
        /* These will inherit from QWidget#ThoughtToolContainer QPushButton for general CoT button style */
        /* Add specific overrides if general CoT button style isn't quite right */
        font: 9pt "Consolas";
        padding: 4px 8px; /* Slightly more padding for clarity */
    }}
    /* --- END NEW --- */

    /* --- NEW: Setting Manager Extra Area Styling --- */
    QWidget#SettingExtraAreaContainer {{
        background-color: {bg_color}; /* Use general background color */
        /* border: 1px solid {base_color}; REMOVED BORDER */
        border-radius: 3px;
        padding: 5px; /* Add some padding */
    }}

    QScrollArea#SettingExtraAreaScroll {{
        background-color: transparent; /* Scroll area itself is transparent */
        border: none; /* No border on the scroll area */
    }}

    /* Viewport of the scroll area, if needed for specific styling */
    QScrollArea#SettingExtraAreaScroll > QWidget > QWidget {{
        background-color: {bg_color}; /* Match container background */
    }}

    QCheckBox#SettingExteriorCheckbox {{
        /* Inherits general QCheckBox styling for color, font, indicator */
        /* Add specific overrides here if needed, e.g., margin */
        margin-bottom: 5px; /* Add some space below the checkbox */
    }}
    /* --- END NEW --- */

    /* --- NEW: Generation Options Panel Styling --- */
    QWidget#GenerationOptionsContainer {{
        background-color: {bg_color}; /* Use general background color */
        /* border: 1px solid {base_color}; no border for seamless look */
        border-radius: 3px;
        padding: 5px; /* Internal padding */
    }}

    QCheckBox#DescGenCheckbox, QCheckBox#ConnGenCheckbox, QCheckBox#InvGenCheckbox {{
        /* Inherit general QCheckBox styling */
        /* Add specific margins if needed, e.g., margin-bottom: 3px; */
    }}

    QPushButton#GenerateButton {{
        /* Inherit general QPushButton styling */
        /* Add specific margins if needed, e.g., margin-top: 5px; */
    }}
    /* --- END NEW --- */

    /* --- NEW: Setting Manager Connections Scroll Area Styling --- */
    QScrollArea#ConnectionsScrollArea {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
    }}
    QScrollArea#ConnectionsScrollArea > QWidget > QWidget {{
        background-color: {darker_bg};
        border: none;
    }}
    /* --- END NEW --- */

    /* --- Setting Manager Path Styling --- */
    /* Path widgets use existing styling classes and are handled automatically */

    /* Inventory Manager List Style (within tabs) */
    QListWidget#InventoryListWidget_Tab {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        alternate-background-color: {bg_color}; /* Keep or remove based on preference */
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerList or adjust as needed */
    }}

    QListWidget#InventoryListWidget_Tab::item:selected {{
        background-color: {highlight};
        color: white;
    }}

    QListWidget#InventoryListWidget_Tab::item:hover {{
        background-color: {highlight};
        color: white; /* Match ActorManagerList hover or adjust */
    }}

    /* Inventory Manager Table Style (within tabs) */
    QTableWidget#InventoryTableWidget_Tab {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        gridline-color: {even_darker_bg}; /* Color for the grid lines */
        /* alternate-background-color: {bg_color}; */ /* For alternating row colors, enable if desired */
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
        border-radius: 3px;
        padding: 1px; /* Minimal padding for the table itself */
    }}

    QTableWidget#InventoryTableWidget_Tab::item {{
        border-bottom: 1px solid {even_darker_bg}; /* Separator for items */
        padding: 4px; /* Padding within each cell */
        color: {base_color};
    }}

    QTableWidget#InventoryTableWidget_Tab::item:selected {{
        background-color: {highlight};
        color: white; /* Text color for selected items */
    }}

    /* Style for the horizontal header of the inventory table */
    QHeaderView#InventoryTableWidget_Tab_HorizontalHeader::section {{
        background-color: {even_darker_bg};
        color: {base_color};
        padding: 4px;
        border-top: 1px solid {darker_bg};
        border-left: 1px solid {darker_bg};
        border-right: 1px solid {darker_bg};
        border-bottom: 1px solid {base_color}; /* Stronger bottom border for header */
        font-weight: bold;
    }}

    /* Style for the vertical header (if made visible) */
    QHeaderView#InventoryTableWidget_Tab_VerticalHeader::section {{
        background-color: {even_darker_bg};
        color: {base_color};
        padding: 4px;
        border-top: 1px solid {darker_bg};
        border-left: 1px solid {base_color}; /* Stronger left border for header */
        border-right: 1px solid {darker_bg};
        border-bottom: 1px solid {darker_bg};
    }}
    /* End of Inventory Manager Table Style */

    /* Actor Manager: Relations Container (Main widget, might not be visible bg) */
    QWidget#RelationsContainer {{
        background-color: transparent; /* Make outer container transparent */
        border: none; /* No border on outer container */
    }}

    /* Actor Manager: Relations Scroll Area */
    QScrollArea#RelationsScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Actor Manager: Relations Scroll Area Content Widget */
    QScrollArea#RelationsScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Actor Manager: Variables Scroll Area */
    QScrollArea#VariablesScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Actor Manager: Variables Scroll Area Content Widget */
    QScrollArea#VariablesScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Time Manager: Main Scroll Area */
    QScrollArea#TimeManagerScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Time Manager: Main Scroll Area Content Widget */
    QScrollArea#TimeManagerScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Actor Manager: Inventory Container Border and Background */
    QWidget#InventoryContainer {{
        background-color: {darker_bg}; /* Use darker background like lists */
        border: 1px solid {base_color}; /* Use theme base color for border */
        border-radius: 3px;
    }}

    /* NEW: Actor Manager Name/Description Inputs */
    QLineEdit#ActorManagerNameInput, QTextEdit#ActorManagerDescInput {{
        color: {base_color};
        background-color: {darker_bg}; /* Match list background */
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#ActorManagerEditLabel {{ /* Label for actor edits */
        color: {base_color};
        font: 9pt "Consolas";
        margin-right: 5px; /* Add some space */
    }}
    
    /* Character Name Input Styling for Rules Manager */
    QLineEdit#CharacterNameInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#CharacterNameLabel {{
        color: {base_color};
        font: 12pt "Consolas";
        background-color: transparent;
    }}
    /* END NEW */

    QCheckBox {{
        color: {base_color};
        font: 9pt 'Consolas';
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 3px;
        background: transparent;
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:unchecked {{
        background: transparent;
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:disabled {{
        background: #333;
        border: 1.5px solid #444;
    }}

    /* Style for Optional Model Override Input */
    QLineEdit#ModelOverrideInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerNameInput */
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Style for Additional Instructions Input */
    QTextEdit#AdditionalInstructionsInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerDescInput */
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Container for Holding/Wearing content with border */
    QWidget#InventoryContentContainer {{
        border: 1px solid {base_color}; /* Use theme base color for consistent border */
        border-radius: 3px;
        margin-top: 4px; /* Add some space below the Inventory: label */
    }}

    /* --- NEW: Change Actor Location Action Widgets --- */
    QWidget#ChangeLocationWidget {{ /* Container for the whole action */
        background-color: rgba({r}, {g}, {b}, 0.05); /* Subtle tint like PairWidget */
        border-radius: 3px;
        padding: 4px;
        margin-top: 2px;
        border: 1px solid rgba({r}, {g}, {b}, 0.1); /* Very subtle border */
    }}

    QComboBox#ChangeLocationActorSelector, QComboBox#ChangeLocationTargetSettingCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        padding: 3px;
        font: 9pt "Consolas";
        border-radius: 3px;
        min-width: 120px;
    }}
    QComboBox#ChangeLocationActorSelector::drop-down, QComboBox#ChangeLocationTargetSettingCombo::drop-down {{
        border: none;
    }}
    QComboBox#ChangeLocationActorSelector::down-arrow, QComboBox#ChangeLocationTargetSettingCombo::down-arrow {{
        image: none;
    }}
    QComboBox#ChangeLocationActorSelector QAbstractItemView, QComboBox#ChangeLocationTargetSettingCombo QAbstractItemView {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Style the completer popup for Target Setting */
    QComboBox QAbstractItemView#qt_scrollarea_viewport {{
        border: 1px solid {base_color};
        background-color: {darker_bg};
        color: {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QRadioButton#ChangeLocationAdjacentRadio, QRadioButton#ChangeLocationFastTravelRadio, QRadioButton#ChangeLocationSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator, QRadioButton#ChangeLocationFastTravelRadio::indicator, QRadioButton#ChangeLocationSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator:checked, QRadioButton#ChangeLocationFastTravelRadio::indicator:checked, QRadioButton#ChangeLocationSettingRadio::indicator:checked {{
        background-color: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator:hover, QRadioButton#ChangeLocationFastTravelRadio::indicator:hover, QRadioButton#ChangeLocationSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}
    /* --- END NEW --- */

    /* --- NEW: Style for Condition and Action Scope Radio Buttons --- */
    QRadioButton#ConditionVarScopeGlobalRadio, QRadioButton#ConditionVarScopeCharacterRadio,
    QRadioButton#ConditionVarScopePlayerRadio,
    QRadioButton#ConditionVarScopeSettingRadio,
    QRadioButton#ActionVarScopeGlobalRadio, QRadioButton#ActionVarScopeCharacterRadio, QRadioButton#ActionVarScopePlayerRadio, QRadioButton#ActionVarScopeSceneCharsRadio, QRadioButton#ActionVarScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator, QRadioButton#ConditionVarScopeCharacterRadio::indicator,
    QRadioButton#ConditionVarScopePlayerRadio::indicator,
    QRadioButton#ConditionVarScopeSettingRadio::indicator,
    QRadioButton#ActionVarScopeGlobalRadio::indicator, QRadioButton#ActionVarScopeCharacterRadio::indicator, QRadioButton#ActionVarScopePlayerRadio::indicator, QRadioButton#ActionVarScopeSceneCharsRadio::indicator, QRadioButton#ActionVarScopeSettingRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:checked, QRadioButton#ConditionVarScopeCharacterRadio::indicator:checked,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:checked,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:checked,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:checked, QRadioButton#ActionVarScopeCharacterRadio::indicator:checked, QRadioButton#ActionVarScopePlayerRadio::indicator:checked, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:checked, QRadioButton#ActionVarScopeSettingRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:hover, QRadioButton#ConditionVarScopeCharacterRadio::indicator:hover,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:hover,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:hover,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:hover, QRadioButton#ActionVarScopeCharacterRadio::indicator:hover, QRadioButton#ActionVarScopePlayerRadio::indicator:hover, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:hover, QRadioButton#ActionVarScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* --- NEW: Style for Text Tag Mode Radio Buttons --- */
    QRadioButton#TagOverwriteRadio, QRadioButton#TagAppendRadio, QRadioButton#TagPrependRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TagOverwriteRadio::indicator, QRadioButton#TagAppendRadio::indicator, QRadioButton#TagPrependRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#TagOverwriteRadio::indicator:checked, QRadioButton#TagAppendRadio::indicator:checked, QRadioButton#TagPrependRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#TagOverwriteRadio::indicator:hover, QRadioButton#TagAppendRadio::indicator:hover, QRadioButton#TagPrependRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* Additional radio buttons that need styling (Keep for others like Prepend/Append/Replace/First/Last) */
    QRadioButton#PrependRadio, QRadioButton#AppendRadio, QRadioButton#ReplaceRadio, 
    QRadioButton#FirstSysMsgRadio, QRadioButton#LastSysMsgRadio
    {{
        color: {base_color}; /* Ensure color is set */
        font: 9pt "Consolas"; /* Smaller */
        spacing: 5px; /* Less spacing */
        background-color: transparent; /* Ensure no background override */
    }}
    QRadioButton#PrependRadio::indicator, QRadioButton#AppendRadio::indicator, QRadioButton#ReplaceRadio::indicator,
    QRadioButton#FirstSysMsgRadio::indicator, QRadioButton#LastSysMsgRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#PrependRadio::indicator:checked, QRadioButton#AppendRadio::indicator:checked, QRadioButton#ReplaceRadio::indicator:checked,
    QRadioButton#FirstSysMsgRadio::indicator:checked, QRadioButton#LastSysMsgRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#PrependRadio::indicator:hover, QRadioButton#AppendRadio::indicator:hover, QRadioButton#ReplaceRadio::indicator:hover,
    QRadioButton#FirstSysMsgRadio::indicator:hover, QRadioButton#LastSysMsgRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* NEW: Actor Manager Variable Name/Value Inputs */
    QLineEdit#ActorManagerVarNameInput, QLineEdit#ActorManagerVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    /* Highlight for selected variable row */
    QWidget.VariableRowSelected {{
        background-color: {highlight};
        border-radius: 3px;
    }}

    /* --- Timer Rules Styling --- */
    QWidget#TimerRulesContainer {{
        background-color: {bg_color}; /* Ensure base container has background */
        color: {base_color};
    }}
    
    QLabel#TimerRulesTitle {{ /* Assuming this exists or might be added later */
        color: {base_color};
        font: bold 12pt "Consolas";
    }}
    
    QLabel#TimerRulesDescription {{ /* Assuming this exists or might be added later */
        color: {base_color};
        font: 10pt "Consolas";
    }}
    
    QWidget#TimerRulesListControls {{ /* Parent of Rule ID/Desc and filter/list */
        background-color: {bg_color};
    }}
    
    QLineEdit#TimerRulesFilterInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}
    
    QListWidget#TimerRulesList {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        border-radius: 3px;
        alternate-background-color: {bg_color};
        font: 9pt "Consolas";
    }}
    QListWidget#TimerRulesList::item:selected {{
        background-color: {highlight};
        color: white;
    }}
    QListWidget#TimerRulesList::item:hover {{
        background-color: {highlight};
        color: white; 
    }}
    
    QPushButton#TimerRuleAddButton, QPushButton#TimerRuleRemoveButton,
    QPushButton#TimerRuleMoveUpButton, QPushButton#TimerRuleMoveDownButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 2px;
    }}
    QPushButton#TimerRuleAddButton:hover, QPushButton#TimerRuleRemoveButton:hover,
    QPushButton#TimerRuleMoveUpButton:hover, QPushButton#TimerRuleMoveDownButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    
    /* Left and Right Panel Base Styling */
    QWidget#TimerRightPanelWidget,
    QWidget#TimerLeftPanelWidget {{
        background-color: {bg_color};
    }}
    QScrollArea#TimerRightPanelScroll,
    QScrollArea#TimerLeftPanelScroll {{
        background-color: transparent; 
        border: none;
    }}
    QScrollArea#TimerLeftPanelScroll > QWidget > QWidget {{ /* Viewport content of left scroll */
        background-color: {bg_color}; 
    }}
     QScrollArea#TimerRightPanelScroll > QWidget > QWidget {{ /* Viewport content of right scroll */
        background-color: {bg_color}; 
    }}

    /* Titles within Panels */
    QLabel#TimerConditionsTitleLabel {{
        color: {base_color};
        font: bold 11pt "Consolas"; 
        margin-bottom: 5px; 
    }}
    QLabel#TimerRuleActionsLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: bold; 
    }}

    /* Labels for specific inputs (Rule ID, Desc, Intervals, Var Conditions) */
    QLabel#TimerRuleIdLabel, QLabel#TimerRuleDescLabel, 
    QLabel#TimerRuleIntervalLabel,
    QLabel#TimerRuleGameTimeIntervalLabel,
    QLabel#TimerRuleGameMinutesLabel,
    QLabel#TimerRuleGameHoursLabel,
    QLabel#TimerRuleGameDaysLabel,
    QLabel#TimerRuleConditionVarNameLabel, 
    QLabel#TimerRuleConditionVarValueLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: normal; /* Explicitly normal */
    }}
    
    /* LineEdits for Rule ID, Description, and Variable Conditions */
    QLineEdit#TimerRuleIdInput, QLineEdit#TimerRuleDescInput,
    QLineEdit#TimerRuleConditionVarNameInput, QLineEdit#TimerRuleConditionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas"; /* Changed from 9pt for consistency */
    }}
    
    /* General SpinBox styling for fixed value inputs in Conditions Panel */
    QSpinBox#TimerRuleIntervalInput,
    QSpinBox#TimerRuleGameMinutesInput,
    QSpinBox#TimerRuleGameHoursInput,
    QSpinBox#TimerRuleGameDaysInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
    }}
    /* Buttons for these general spinboxes */
    QSpinBox#TimerRuleIntervalInput::up-button, QSpinBox#TimerRuleIntervalInput::down-button,
    QSpinBox#TimerRuleGameMinutesInput::up-button, QSpinBox#TimerRuleGameMinutesInput::down-button,
    QSpinBox#TimerRuleGameHoursInput::up-button, QSpinBox#TimerRuleGameHoursInput::down-button,
    QSpinBox#TimerRuleGameDaysInput::up-button, QSpinBox#TimerRuleGameDaysInput::down-button {{
        background-color: {base_color}; 
        border: 1px solid {bg_color};
        width: 12px;
        min-height: 10px;
        subcontrol-origin: border;
        margin: 1px;
    }}
    /* Arrows for these general spinboxes */
    QSpinBox#TimerRuleIntervalInput::up-arrow, QSpinBox#TimerRuleIntervalInput::down-arrow,
    QSpinBox#TimerRuleGameMinutesInput::up-arrow, QSpinBox#TimerRuleGameMinutesInput::down-arrow,
    QSpinBox#TimerRuleGameHoursInput::up-arrow, QSpinBox#TimerRuleGameHoursInput::down-arrow,
    QSpinBox#TimerRuleGameDaysInput::up-arrow, QSpinBox#TimerRuleGameDaysInput::down-arrow {{
        width: 0px; 
        height: 0px;
    }}

    /* Styling for Timer Rule Condition Radio Buttons */
    QRadioButton#TimerRuleConditionAlwaysRadio, QRadioButton#TimerRuleConditionVariableRadio {{
        color: {base_color};
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator, QRadioButton#TimerRuleConditionVariableRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator:checked, QRadioButton#TimerRuleConditionVariableRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator:hover, QRadioButton#TimerRuleConditionVariableRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* Styling for Timer Rule Random Interval Checkboxes */
    QCheckBox#TimerRuleIntervalRandomCheckbox,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox,
    QCheckBox#TimerRuleGameHoursRandomCheckbox,
    QCheckBox#TimerRuleGameDaysRandomCheckbox {{
        color: {base_color};
        font: 10pt "Consolas"; 
        spacing: 5px;
        background-color: transparent;
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 3px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator:checked {{
        background-color: {base_color};
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* Styling for Timer Rule Random Interval Min/Max SpinBoxes */
    QSpinBox#TimerRuleIntervalMinInput, QSpinBox#TimerRuleIntervalMaxInput,
    QSpinBox#TimerRuleGameMinutesMinInput, QSpinBox#TimerRuleGameMinutesMaxInput,
    QSpinBox#TimerRuleGameHoursMinInput, QSpinBox#TimerRuleGameHoursMaxInput,
    QSpinBox#TimerRuleGameDaysMinInput, QSpinBox#TimerRuleGameDaysMaxInput {{
        color: {base_color};
        background-color: {darker_bg}; 
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px 3px; 
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
        min-width: 60px; 
    }}
    /* Buttons for these Min/Max spinboxes */
    QSpinBox#TimerRuleIntervalMinInput::up-button, QSpinBox#TimerRuleIntervalMaxInput::up-button,
    QSpinBox#TimerRuleGameMinutesMinInput::up-button, QSpinBox#TimerRuleGameMinutesMaxInput::up-button,
    QSpinBox#TimerRuleGameHoursMinInput::up-button, QSpinBox#TimerRuleGameHoursMaxInput::up-button,
    QSpinBox#TimerRuleGameDaysMinInput::up-button, QSpinBox#TimerRuleGameDaysMaxInput::up-button,
    QSpinBox#TimerRuleIntervalMinInput::down-button, QSpinBox#TimerRuleIntervalMaxInput::down-button,
    QSpinBox#TimerRuleGameMinutesMinInput::down-button, QSpinBox#TimerRuleGameMinutesMaxInput::down-button,
    QSpinBox#TimerRuleGameHoursMinInput::down-button, QSpinBox#TimerRuleGameHoursMaxInput::down-button,
    QSpinBox#TimerRuleGameDaysMinInput::down-button, QSpinBox#TimerRuleGameDaysMaxInput::down-button {{
        background-color: {base_color};
        border: 1px solid {bg_color};
        width: 12px;
        min-height: 10px; 
        subcontrol-origin: border;
        margin: 1px;
    }}
    /* Arrows for these Min/Max spinboxes */
    QSpinBox#TimerRuleIntervalMinInput::up-arrow, QSpinBox#TimerRuleIntervalMaxInput::up-arrow,
    QSpinBox#TimerRuleGameMinutesMinInput::up-arrow, QSpinBox#TimerRuleGameMinutesMaxInput::up-arrow,
    QSpinBox#TimerRuleGameHoursMinInput::up-arrow, QSpinBox#TimerRuleGameHoursMaxInput::up-arrow,
    QSpinBox#TimerRuleGameDaysMinInput::up-arrow, QSpinBox#TimerRuleGameDaysMaxInput::up-arrow,
    QSpinBox#TimerRuleIntervalMinInput::down-arrow, QSpinBox#TimerRuleIntervalMaxInput::down-arrow,
    QSpinBox#TimerRuleGameMinutesMinInput::down-arrow, QSpinBox#TimerRuleGameMinutesMaxInput::down-arrow,
    QSpinBox#TimerRuleGameHoursMinInput::down-arrow, QSpinBox#TimerRuleGameHoursMaxInput::down-arrow,
    QSpinBox#TimerRuleGameDaysMinInput::down-arrow, QSpinBox#TimerRuleGameDaysMaxInput::down-arrow {{
        width: 0px; 
        height: 0px;
    }}
    
    /* Enable/Disable Checkbox */
    QCheckBox#TimerRuleEnableCheckbox {{
        color: {base_color};
        font: 10pt "Consolas";
        /* Standard checkbox indicator styling will be inherited if not overridden here */
    }}
    
    /* Actions Area */
    QWidget#TimerRuleActionsContainer {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
    }}
    QWidget#TimerRuleActionRow {{
        background-color: {darker_bg}; /* Ensure rows also have this if they are separate widgets */
    }}
    QComboBox#TimerRuleActionTypeCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 9pt "Consolas";
    }}
    QComboBox#TimerRuleActionTypeCombo::drop-down {{
        border: none;
    }}
    QComboBox#TimerRuleActionTypeCombo::down-arrow {{
        image: none;
    }}
    QLineEdit#TimerRuleActionValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}
    QPushButton#TimerRuleActionRemoveButton {{
        color: {base_color};
        background-color: {darker_bg}; /* Changed from bg_color to match other small buttons */
        border: 1px solid {base_color};
        border-radius: 2px; /* Consistent with other small buttons */
    }}
    QPushButton#TimerRuleActionRemoveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    
    /* Main Action Buttons (Add Action, Save Rule) */
    QPushButton#TimerRuleAddActionButton, QPushButton#TimerRuleSaveButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color}; /* Ensure consistent border */
        border-radius: 3px;
        padding: 5px; /* Default padding from general QPushButton */
        font: 10pt "Consolas"; /* Slightly smaller than general QPushButton if needed */
    }}
    QPushButton#TimerRuleAddActionButton:hover, QPushButton#TimerRuleSaveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    /* --- End Timer Rules Styling --- */

    /* --- Styling for Start After Label --- */
    QLabel#TimerRuleStartAfterLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        /* margin-right: 5px; */ /* Add if more space needed before radios */
    }}

    /* --- Styling for Timer Rule Start After Radio Buttons --- */
    QRadioButton#TimerRuleStartAfterPlayerRadio, QRadioButton#TimerRuleStartAfterCharacterRadio, QRadioButton#TimerRuleStartAfterSceneChangeRadio {{
        color: {base_color};
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px; /* For round radio buttons */
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator:checked, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator:checked, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator:hover, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator:hover, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* --- Styling for Timer Rule Variable Scope Radio Buttons (Global/Character) --- */
    QRadioButton#TimerRuleVarScopeGlobalRadio, QRadioButton#TimerRuleVarScopeCharacterRadio {{
        color: {base_color}; /* CORRECTED: Single braces */
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px; /* For round radio buttons */
        border: 1px solid {base_color}; /* CORRECTED: Single braces */
        background: transparent; /* CORRECTED: Single braces */
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator:checked, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator:checked {{
        background-color: {base_color}; /* CORRECTED: Single braces */
        border: 1px solid {base_color}; /* CORRECTED: Single braces */
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator:hover, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator:hover {{
        border: 1px solid {brighter}; /* CORRECTED: Single braces */
    }}

    /* --- Styling for Timer Rule Condition Variable Input Labels & LineEdits --- */
    QLabel#TimerRuleConditionVarNameLabel, QLabel#TimerRuleConditionVarValueLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: normal; /* Explicitly normal */
    }}
    QLineEdit#TimerRuleConditionVarNameInput, QLineEdit#TimerRuleConditionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas"; /* Changed from 9pt for consistency */
    }}

    /* --- Styling for MULTIPLE Variable Conditions Area --- */
    QWidget#VariableConditionsArea {{
        /* Optional: Add border/background to visually group */
        /* background-color: rgba(0,0,0, 0.1); */
        /* border: 1px dotted {base_color}; */
        /* border-radius: 3px; */
        margin-top: 5px; /* Add some space above this section */
    }}

    QLabel#TimerConditionsOperatorLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        margin-right: 5px;
    }}
    
    QComboBox#TimerConditionsOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 10pt "Consolas";
        min-width: 60px;
    }}
    QComboBox#TimerConditionsOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#TimerConditionsOperatorCombo::down-arrow {{
        image: none;
    }}

    /* Styling for widgets WITHIN each VariableConditionRow */
    QWidget#VariableConditionRow QLineEdit#ConditionVarNameInput,
    QWidget#VariableConditionRow QLineEdit#ConditionValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px; /* Slightly smaller padding */
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas"; /* Smaller font for rows */
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 80px; /* Adjust width */
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo::drop-down {{
        border: none;
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo::down-arrow {{
        image: none;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px; /* Less spacing */
        background-color: transparent;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator:checked,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator:checked,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator:hover,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator:hover,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}
    QWidget#VariableConditionRow QPushButton#RemoveVariableConditionButton {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 2px;
        min-width: 20px; /* Match size? */
        max-width: 20px;
        min-height: 20px;
        max-height: 20px;
        padding: 0px;
        font-size: 12pt; /* Adjust for '-' sign */
    }}
    QWidget#VariableConditionRow QPushButton#RemoveVariableConditionButton:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* Button to add new rows */
    QPushButton#AddVariableConditionButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        margin-top: 5px; /* Add space above button */
    }}
    QPushButton#AddVariableConditionButton:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* --- Styling for Inter-Row Operator Combo --- */
    QComboBox#ConditionRowOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 55px; /* Keep narrow */
        max-width: 55px;
    }}
    QComboBox#ConditionRowOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#ConditionRowOperatorCombo::down-arrow {{
        image: none;
    }}

    /* --- Styling for Set Var Action Specific Inputs --- */
    QLineEdit#TimerRuleActionVarNameInput,
    QLineEdit#TimerRuleActionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px; /* Smaller padding for dense row */
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}

    QComboBox#TimerRuleSetVarOperationSelector {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 65px; /* Adjust as needed */
    }}
    QComboBox#TimerRuleSetVarOperationSelector::drop-down {{
        border: none;
    }}
    QComboBox#TimerRuleSetVarOperationSelector::down-arrow {{
        image: none;
    }}

    QRadioButton#TimerRuleActionScopeGlobalRadio,
    QRadioButton#TimerRuleActionScopeCharacterRadio,
    QRadioButton#TimerRuleActionScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator:checked,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator:checked,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator:hover,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator:hover,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* NEW: Setting Manager Variable Name/Value Inputs - with more specific selector */
    QWidget#VariableRow QLineEdit#SettingManagerVarNameInput,
    QWidget#VariableRow QLineEdit#SettingManagerVarValueInput,
    QLineEdit#SettingManagerVarNameInput,
    QLineEdit#SettingManagerVarValueInput {{
        color: {base_color} !important;
        background-color: {darker_bg} !important;
        border: 1px solid {base_color} !important;
        border-radius: 3px !important;
        padding: 3px !important;
        font: 10pt "Consolas" !important;
        selection-background-color: {highlight} !important;
        selection-color: white !important;
    }}
    /* END NEW */

    QLineEdit#PathDetailsNameInput, QTextEdit#PathDetailsDescInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt 'Consolas';
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QWidget[styleClass="PathDetailsNameInput"], QWidget[styleClass="PathDetailsDescInput"] {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt 'Consolas';
        selection-background-color: {highlight};
        selection-color: white;
    }}
    
    /* World Editor Scale Inputs */
    QLineEdit#WORLDToolbar_ScaleNumberInput, QLineEdit#WORLDToolbar_ScaleTimeInput,
    QLineEdit#LOCATIONToolbar_ScaleNumberInput, QLineEdit#LOCATIONToolbar_ScaleTimeInput {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        border: 1px solid {base_color}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
        max-width: 40px;
        min-width: 35px;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown, QComboBox#LOCATIONToolbar_ScaleUnitDropdown {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        border: 1px solid {base_color}; 
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
        max-width: 70px;
        min-width: 65px;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown::drop-down, QComboBox#LOCATIONToolbar_ScaleUnitDropdown::drop-down {{
        border: none;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown::down-arrow, QComboBox#LOCATIONToolbar_ScaleUnitDropdown::down-arrow {{
        image: none;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown QAbstractItemView, QComboBox#LOCATIONToolbar_ScaleUnitDropdown QAbstractItemView {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas";
    }}
    /* --- Inventory Scroll Area Fix --- */
    QScrollArea#InventoryScrollArea {{
        background-color: {darker_bg};
    }}
    QScrollArea#InventoryScrollArea QWidget {{
        background-color: {darker_bg};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio, QRadioButton#TimerGenerateUserMsgRadio, QRadioButton#TimerGenerateFullConvoRadio,
    QRadioButton#GenerateLastExchangeRadio, QRadioButton#GenerateUserMsgRadio, QRadioButton#GenerateFullConvoRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator, QRadioButton#TimerGenerateUserMsgRadio::indicator, QRadioButton#TimerGenerateFullConvoRadio::indicator,
    QRadioButton#GenerateLastExchangeRadio::indicator, QRadioButton#GenerateUserMsgRadio::indicator, QRadioButton#GenerateFullConvoRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator:checked, QRadioButton#TimerGenerateUserMsgRadio::indicator:checked, QRadioButton#TimerGenerateFullConvoRadio::indicator:checked,
    QRadioButton#GenerateLastExchangeRadio::indicator:checked, QRadioButton#GenerateUserMsgRadio::indicator:checked, QRadioButton#GenerateFullConvoRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator:hover, QRadioButton#TimerGenerateUserMsgRadio::indicator:hover, QRadioButton#TimerGenerateFullConvoRadio::indicator:hover,
    QRadioButton#GenerateLastExchangeRadio::indicator:hover, QRadioButton#GenerateUserMsgRadio::indicator:hover, QRadioButton#GenerateFullConvoRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    
    QLabel#TimerGenerateContextLabel, QLabel#TimerGenerateInstructionsLabel,
    QLabel#GenerateContextLabel, QLabel#GenerateInstructionsLabel {{
        color: {base_color};
        font: 9pt "Consolas";
        background-color: transparent;
    }}
    
    QTextEdit#TimerGenerateInstructionsInput, QTextEdit#GenerateInstructionsInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        padding: 3px;
    }}
    
    QWidget#TimerGenerateContextWidget, QWidget#GenerateContextWidget {{
        background-color: {darker_bg};
        border-radius: 3px;
    }}

    /* --- NEW: Generate Mode Radio Buttons Styling --- */
    QRadioButton#GenerateModeLLMRadio, QRadioButton#GenerateModeRandomRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#GenerateModeLLMRadio::indicator, QRadioButton#GenerateModeRandomRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#GenerateModeLLMRadio::indicator:checked, QRadioButton#GenerateModeRandomRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#GenerateModeLLMRadio::indicator:hover, QRadioButton#GenerateModeRandomRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* --- NEW: Random Generate Panel Filter Styling --- */
    QLineEdit#SettingFilterInput, QLineEdit#CharacterFilterInput,
    QLineEdit#RandomNumberMin, QLineEdit#RandomNumberMax {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 9pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Remove old QListWidget styling that's no longer needed */
    
    /* Keep button styling for other buttons */
    QPushButton#AddSettingFilterBtn, QPushButton#RemoveSettingFilterBtn,
    QPushButton#AddCharacterFilterBtn, QPushButton#RemoveCharacterFilterBtn {{
        /* These will inherit from QWidget#ThoughtToolContainer QPushButton for general CoT button style */
        /* Add specific overrides if general CoT button style isn't quite right */
        font: 9pt "Consolas";
        padding: 4px 8px; /* Slightly more padding for clarity */
    }}
    /* --- END NEW --- */

    /* --- NEW: Setting Manager Extra Area Styling --- */
    QWidget#SettingExtraAreaContainer {{
        background-color: {bg_color}; /* Use general background color */
        /* border: 1px solid {base_color}; REMOVED BORDER */
        border-radius: 3px;
        padding: 5px; /* Add some padding */
    }}

    QScrollArea#SettingExtraAreaScroll {{
        background-color: transparent; /* Scroll area itself is transparent */
        border: none; /* No border on the scroll area */
    }}

    /* Viewport of the scroll area, if needed for specific styling */
    QScrollArea#SettingExtraAreaScroll > QWidget > QWidget {{
        background-color: {bg_color}; /* Match container background */
    }}

    QCheckBox#SettingExteriorCheckbox {{
        /* Inherits general QCheckBox styling for color, font, indicator */
        /* Add specific overrides here if needed, e.g., margin */
        margin-bottom: 5px; /* Add some space below the checkbox */
    }}
    /* --- END NEW --- */

    /* --- NEW: Generation Options Panel Styling --- */
    QWidget#GenerationOptionsContainer {{
        background-color: {bg_color}; /* Use general background color */
        /* border: 1px solid {base_color}; no border for seamless look */
        border-radius: 3px;
        padding: 5px; /* Internal padding */
    }}

    QCheckBox#DescGenCheckbox, QCheckBox#ConnGenCheckbox, QCheckBox#InvGenCheckbox {{
        /* Inherit general QCheckBox styling */
        /* Add specific margins if needed, e.g., margin-bottom: 3px; */
    }}

    QPushButton#GenerateButton {{
        /* Inherit general QPushButton styling */
        /* Add specific margins if needed, e.g., margin-top: 5px; */
    }}
    /* --- END NEW --- */

    /* --- NEW: Setting Manager Connections Scroll Area Styling --- */
    QScrollArea#ConnectionsScrollArea {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
    }}
    QScrollArea#ConnectionsScrollArea > QWidget > QWidget {{
        background-color: {darker_bg};
        border: none;
    }}
    /* --- END NEW --- */

    /* --- Setting Manager Path Styling --- */
    /* Path widgets use existing styling classes and are handled automatically */

    /* Inventory Manager List Style (within tabs) */
    QListWidget#InventoryListWidget_Tab {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        alternate-background-color: {bg_color}; /* Keep or remove based on preference */
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerList or adjust as needed */
    }}

    QListWidget#InventoryListWidget_Tab::item:selected {{
        background-color: {highlight};
        color: white;
    }}

    QListWidget#InventoryListWidget_Tab::item:hover {{
        background-color: {highlight};
        color: white; /* Match ActorManagerList hover or adjust */
    }}

    /* Inventory Manager Table Style (within tabs) */
    QTableWidget#InventoryTableWidget_Tab {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        gridline-color: {even_darker_bg}; /* Color for the grid lines */
        /* alternate-background-color: {bg_color}; */ /* For alternating row colors, enable if desired */
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
        border-radius: 3px;
        padding: 1px; /* Minimal padding for the table itself */
    }}

    QTableWidget#InventoryTableWidget_Tab::item {{
        border-bottom: 1px solid {even_darker_bg}; /* Separator for items */
        padding: 4px; /* Padding within each cell */
        color: {base_color};
    }}

    QTableWidget#InventoryTableWidget_Tab::item:selected {{
        background-color: {highlight};
        color: white; /* Text color for selected items */
    }}

    /* Style for the horizontal header of the inventory table */
    QHeaderView#InventoryTableWidget_Tab_HorizontalHeader::section {{
        background-color: {even_darker_bg};
        color: {base_color};
        padding: 4px;
        border-top: 1px solid {darker_bg};
        border-left: 1px solid {darker_bg};
        border-right: 1px solid {darker_bg};
        border-bottom: 1px solid {base_color}; /* Stronger bottom border for header */
        font-weight: bold;
    }}

    /* Style for the vertical header (if made visible) */
    QHeaderView#InventoryTableWidget_Tab_VerticalHeader::section {{
        background-color: {even_darker_bg};
        color: {base_color};
        padding: 4px;
        border-top: 1px solid {darker_bg};
        border-left: 1px solid {base_color}; /* Stronger left border for header */
        border-right: 1px solid {darker_bg};
        border-bottom: 1px solid {darker_bg};
    }}
    /* End of Inventory Manager Table Style */

    /* Actor Manager: Relations Container (Main widget, might not be visible bg) */
    QWidget#RelationsContainer {{
        background-color: transparent; /* Make outer container transparent */
        border: none; /* No border on outer container */
    }}

    /* Actor Manager: Relations Scroll Area */
    QScrollArea#RelationsScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Actor Manager: Relations Scroll Area Content Widget */
    QScrollArea#RelationsScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Actor Manager: Variables Scroll Area */
    QScrollArea#VariablesScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Actor Manager: Variables Scroll Area Content Widget */
    QScrollArea#VariablesScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Time Manager: Main Scroll Area */
    QScrollArea#TimeManagerScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Time Manager: Main Scroll Area Content Widget */
    QScrollArea#TimeManagerScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Actor Manager: Inventory Container Border and Background */
    QWidget#InventoryContainer {{
        background-color: {darker_bg}; /* Use darker background like lists */
        border: 1px solid {base_color}; /* Use theme base color for border */
        border-radius: 3px;
    }}

    /* NEW: Actor Manager Name/Description Inputs */
    QLineEdit#ActorManagerNameInput, QTextEdit#ActorManagerDescInput {{
        color: {base_color};
        background-color: {darker_bg}; /* Match list background */
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#ActorManagerEditLabel {{ /* Label for actor edits */
        color: {base_color};
        font: 9pt "Consolas";
        margin-right: 5px; /* Add some space */
    }}
    
    /* Character Name Input Styling for Rules Manager */
    QLineEdit#CharacterNameInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#CharacterNameLabel {{
        color: {base_color};
        font: 12pt "Consolas";
        background-color: transparent;
    }}
    /* END NEW */

    QCheckBox {{
        color: {base_color};
        font: 9pt 'Consolas';
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 3px;
        background: transparent;
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:unchecked {{
        background: transparent;
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:disabled {{
        background: #333;
        border: 1.5px solid #444;
    }}

    /* Style for Optional Model Override Input */
    QLineEdit#ModelOverrideInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerNameInput */
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Style for Additional Instructions Input */
    QTextEdit#AdditionalInstructionsInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerDescInput */
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Container for Holding/Wearing content with border */
    QWidget#InventoryContentContainer {{
        border: 1px solid {base_color}; /* Use theme base color for consistent border */
        border-radius: 3px;
        margin-top: 4px; /* Add some space below the Inventory: label */
    }}

    /* --- NEW: Change Actor Location Action Widgets --- */
    QWidget#ChangeLocationWidget {{ /* Container for the whole action */
        background-color: rgba({r}, {g}, {b}, 0.05); /* Subtle tint like PairWidget */
        border-radius: 3px;
        padding: 4px;
        margin-top: 2px;
        border: 1px solid rgba({r}, {g}, {b}, 0.1); /* Very subtle border */
    }}

    QComboBox#ChangeLocationActorSelector, QComboBox#ChangeLocationTargetSettingCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        padding: 3px;
        font: 9pt "Consolas";
        border-radius: 3px;
        min-width: 120px;
    }}
    QComboBox#ChangeLocationActorSelector::drop-down, QComboBox#ChangeLocationTargetSettingCombo::drop-down {{
        border: none;
    }}
    QComboBox#ChangeLocationActorSelector::down-arrow, QComboBox#ChangeLocationTargetSettingCombo::down-arrow {{
        image: none;
    }}
    QComboBox#ChangeLocationActorSelector QAbstractItemView, QComboBox#ChangeLocationTargetSettingCombo QAbstractItemView {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Style the completer popup for Target Setting */
    QComboBox QAbstractItemView#qt_scrollarea_viewport {{
        border: 1px solid {base_color};
        background-color: {darker_bg};
        color: {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QRadioButton#ChangeLocationAdjacentRadio, QRadioButton#ChangeLocationFastTravelRadio, QRadioButton#ChangeLocationSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator, QRadioButton#ChangeLocationFastTravelRadio::indicator, QRadioButton#ChangeLocationSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator:checked, QRadioButton#ChangeLocationFastTravelRadio::indicator:checked, QRadioButton#ChangeLocationSettingRadio::indicator:checked {{
        background-color: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator:hover, QRadioButton#ChangeLocationFastTravelRadio::indicator:hover, QRadioButton#ChangeLocationSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}
    /* --- END NEW --- */

    /* --- NEW: Style for Condition and Action Scope Radio Buttons --- */
    QRadioButton#ConditionVarScopeGlobalRadio, QRadioButton#ConditionVarScopeCharacterRadio,
    QRadioButton#ConditionVarScopePlayerRadio,
    QRadioButton#ConditionVarScopeSettingRadio,
    QRadioButton#ActionVarScopeGlobalRadio, QRadioButton#ActionVarScopeCharacterRadio, QRadioButton#ActionVarScopePlayerRadio, QRadioButton#ActionVarScopeSceneCharsRadio, QRadioButton#ActionVarScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator, QRadioButton#ConditionVarScopeCharacterRadio::indicator,
    QRadioButton#ConditionVarScopePlayerRadio::indicator,
    QRadioButton#ConditionVarScopeSettingRadio::indicator,
    QRadioButton#ActionVarScopeGlobalRadio::indicator, QRadioButton#ActionVarScopeCharacterRadio::indicator, QRadioButton#ActionVarScopePlayerRadio::indicator, QRadioButton#ActionVarScopeSceneCharsRadio::indicator, QRadioButton#ActionVarScopeSettingRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:checked, QRadioButton#ConditionVarScopeCharacterRadio::indicator:checked,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:checked,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:checked,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:checked, QRadioButton#ActionVarScopeCharacterRadio::indicator:checked, QRadioButton#ActionVarScopePlayerRadio::indicator:checked, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:checked, QRadioButton#ActionVarScopeSettingRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:hover, QRadioButton#ConditionVarScopeCharacterRadio::indicator:hover,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:hover,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:hover,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:hover, QRadioButton#ActionVarScopeCharacterRadio::indicator:hover, QRadioButton#ActionVarScopePlayerRadio::indicator:hover, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:hover, QRadioButton#ActionVarScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* --- NEW: Style for Text Tag Mode Radio Buttons --- */
    QRadioButton#TagOverwriteRadio, QRadioButton#TagAppendRadio, QRadioButton#TagPrependRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TagOverwriteRadio::indicator, QRadioButton#TagAppendRadio::indicator, QRadioButton#TagPrependRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#TagOverwriteRadio::indicator:checked, QRadioButton#TagAppendRadio::indicator:checked, QRadioButton#TagPrependRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#TagOverwriteRadio::indicator:hover, QRadioButton#TagAppendRadio::indicator:hover, QRadioButton#TagPrependRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* Additional radio buttons that need styling (Keep for others like Prepend/Append/Replace/First/Last) */
    QRadioButton#PrependRadio, QRadioButton#AppendRadio, QRadioButton#ReplaceRadio, 
    QRadioButton#FirstSysMsgRadio, QRadioButton#LastSysMsgRadio
    {{
        color: {base_color}; /* Ensure color is set */
        font: 9pt "Consolas"; /* Smaller */
        spacing: 5px; /* Less spacing */
        background-color: transparent; /* Ensure no background override */
    }}
    QRadioButton#PrependRadio::indicator, QRadioButton#AppendRadio::indicator, QRadioButton#ReplaceRadio::indicator,
    QRadioButton#FirstSysMsgRadio::indicator, QRadioButton#LastSysMsgRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#PrependRadio::indicator:checked, QRadioButton#AppendRadio::indicator:checked, QRadioButton#ReplaceRadio::indicator:checked,
    QRadioButton#FirstSysMsgRadio::indicator:checked, QRadioButton#LastSysMsgRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#PrependRadio::indicator:hover, QRadioButton#AppendRadio::indicator:hover, QRadioButton#ReplaceRadio::indicator:hover,
    QRadioButton#FirstSysMsgRadio::indicator:hover, QRadioButton#LastSysMsgRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* NEW: Actor Manager Variable Name/Value Inputs */
    QLineEdit#ActorManagerVarNameInput, QLineEdit#ActorManagerVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    /* Highlight for selected variable row */
    QWidget.VariableRowSelected {{
        background-color: {highlight};
        border-radius: 3px;
    }}

    /* --- Timer Rules Styling --- */
    QWidget#TimerRulesContainer {{
        background-color: {bg_color}; /* Ensure base container has background */
        color: {base_color};
    }}
    
    QLabel#TimerRulesTitle {{ /* Assuming this exists or might be added later */
        color: {base_color};
        font: bold 12pt "Consolas";
    }}
    
    QLabel#TimerRulesDescription {{ /* Assuming this exists or might be added later */
        color: {base_color};
        font: 10pt "Consolas";
    }}
    
    QWidget#TimerRulesListControls {{ /* Parent of Rule ID/Desc and filter/list */
        background-color: {bg_color};
    }}
    
    QLineEdit#TimerRulesFilterInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}
    
    QListWidget#TimerRulesList {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        border-radius: 3px;
        alternate-background-color: {bg_color};
        font: 9pt "Consolas";
    }}
    QListWidget#TimerRulesList::item:selected {{
        background-color: {highlight};
        color: white;
    }}
    QListWidget#TimerRulesList::item:hover {{
        background-color: {highlight};
        color: white; 
    }}
    
    QPushButton#TimerRuleAddButton, QPushButton#TimerRuleRemoveButton,
    QPushButton#TimerRuleMoveUpButton, QPushButton#TimerRuleMoveDownButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 2px;
    }}
    QPushButton#TimerRuleAddButton:hover, QPushButton#TimerRuleRemoveButton:hover,
    QPushButton#TimerRuleMoveUpButton:hover, QPushButton#TimerRuleMoveDownButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    
    /* Left and Right Panel Base Styling */
    QWidget#TimerRightPanelWidget,
    QWidget#TimerLeftPanelWidget {{
        background-color: {bg_color};
    }}
    QScrollArea#TimerRightPanelScroll,
    QScrollArea#TimerLeftPanelScroll {{
        background-color: transparent; 
        border: none;
    }}
    QScrollArea#TimerLeftPanelScroll > QWidget > QWidget {{ /* Viewport content of left scroll */
        background-color: {bg_color}; 
    }}
     QScrollArea#TimerRightPanelScroll > QWidget > QWidget {{ /* Viewport content of right scroll */
        background-color: {bg_color}; 
    }}

    /* Titles within Panels */
    QLabel#TimerConditionsTitleLabel {{
        color: {base_color};
        font: bold 11pt "Consolas"; 
        margin-bottom: 5px; 
    }}
    QLabel#TimerRuleActionsLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: bold; 
    }}

    /* Labels for specific inputs (Rule ID, Desc, Intervals, Var Conditions) */
    QLabel#TimerRuleIdLabel, QLabel#TimerRuleDescLabel, 
    QLabel#TimerRuleIntervalLabel,
    QLabel#TimerRuleGameTimeIntervalLabel,
    QLabel#TimerRuleGameMinutesLabel,
    QLabel#TimerRuleGameHoursLabel,
    QLabel#TimerRuleGameDaysLabel,
    QLabel#TimerRuleConditionVarNameLabel, 
    QLabel#TimerRuleConditionVarValueLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: normal; /* Explicitly normal */
    }}
    
    /* LineEdits for Rule ID, Description, and Variable Conditions */
    QLineEdit#TimerRuleIdInput, QLineEdit#TimerRuleDescInput,
    QLineEdit#TimerRuleConditionVarNameInput, QLineEdit#TimerRuleConditionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas"; /* Changed from 9pt for consistency */
    }}
    
    /* General SpinBox styling for fixed value inputs in Conditions Panel */
    QSpinBox#TimerRuleIntervalInput,
    QSpinBox#TimerRuleGameMinutesInput,
    QSpinBox#TimerRuleGameHoursInput,
    QSpinBox#TimerRuleGameDaysInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
    }}
    /* Buttons for these general spinboxes */
    QSpinBox#TimerRuleIntervalInput::up-button, QSpinBox#TimerRuleIntervalInput::down-button,
    QSpinBox#TimerRuleGameMinutesInput::up-button, QSpinBox#TimerRuleGameMinutesInput::down-button,
    QSpinBox#TimerRuleGameHoursInput::up-button, QSpinBox#TimerRuleGameHoursInput::down-button,
    QSpinBox#TimerRuleGameDaysInput::up-button, QSpinBox#TimerRuleGameDaysInput::down-button {{
        background-color: {base_color}; 
        border: 1px solid {bg_color};
        width: 12px;
        min-height: 10px;
        subcontrol-origin: border;
        margin: 1px;
    }}
    /* Arrows for these general spinboxes */
    QSpinBox#TimerRuleIntervalInput::up-arrow, QSpinBox#TimerRuleIntervalInput::down-arrow,
    QSpinBox#TimerRuleGameMinutesInput::up-arrow, QSpinBox#TimerRuleGameMinutesInput::down-arrow,
    QSpinBox#TimerRuleGameHoursInput::up-arrow, QSpinBox#TimerRuleGameHoursInput::down-arrow,
    QSpinBox#TimerRuleGameDaysInput::up-arrow, QSpinBox#TimerRuleGameDaysInput::down-arrow {{
        width: 0px; 
        height: 0px;
    }}

    /* Styling for Timer Rule Condition Radio Buttons */
    QRadioButton#TimerRuleConditionAlwaysRadio, QRadioButton#TimerRuleConditionVariableRadio {{
        color: {base_color};
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator, QRadioButton#TimerRuleConditionVariableRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator:checked, QRadioButton#TimerRuleConditionVariableRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator:hover, QRadioButton#TimerRuleConditionVariableRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* Styling for Timer Rule Random Interval Checkboxes */
    QCheckBox#TimerRuleIntervalRandomCheckbox,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox,
    QCheckBox#TimerRuleGameHoursRandomCheckbox,
    QCheckBox#TimerRuleGameDaysRandomCheckbox {{
        color: {base_color};
        font: 10pt "Consolas"; 
        spacing: 5px;
        background-color: transparent;
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 3px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator:checked {{
        background-color: {base_color};
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* Styling for Timer Rule Random Interval Min/Max SpinBoxes */
    QSpinBox#TimerRuleIntervalMinInput, QSpinBox#TimerRuleIntervalMaxInput,
    QSpinBox#TimerRuleGameMinutesMinInput, QSpinBox#TimerRuleGameMinutesMaxInput,
    QSpinBox#TimerRuleGameHoursMinInput, QSpinBox#TimerRuleGameHoursMaxInput,
    QSpinBox#TimerRuleGameDaysMinInput, QSpinBox#TimerRuleGameDaysMaxInput {{
        color: {base_color};
        background-color: {darker_bg}; 
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px 3px; 
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
        min-width: 60px; 
    }}
    /* Buttons for these Min/Max spinboxes */
    QSpinBox#TimerRuleIntervalMinInput::up-button, QSpinBox#TimerRuleIntervalMaxInput::up-button,
    QSpinBox#TimerRuleGameMinutesMinInput::up-button, QSpinBox#TimerRuleGameMinutesMaxInput::up-button,
    QSpinBox#TimerRuleGameHoursMinInput::up-button, QSpinBox#TimerRuleGameHoursMaxInput::up-button,
    QSpinBox#TimerRuleGameDaysMinInput::up-button, QSpinBox#TimerRuleGameDaysMaxInput::up-button,
    QSpinBox#TimerRuleIntervalMinInput::down-button, QSpinBox#TimerRuleIntervalMaxInput::down-button,
    QSpinBox#TimerRuleGameMinutesMinInput::down-button, QSpinBox#TimerRuleGameMinutesMaxInput::down-button,
    QSpinBox#TimerRuleGameHoursMinInput::down-button, QSpinBox#TimerRuleGameHoursMaxInput::down-button,
    QSpinBox#TimerRuleGameDaysMinInput::down-button, QSpinBox#TimerRuleGameDaysMaxInput::down-button {{
        background-color: {base_color};
        border: 1px solid {bg_color};
        width: 12px;
        min-height: 10px; 
        subcontrol-origin: border;
        margin: 1px;
    }}
    /* Arrows for these Min/Max spinboxes */
    QSpinBox#TimerRuleIntervalMinInput::up-arrow, QSpinBox#TimerRuleIntervalMaxInput::up-arrow,
    QSpinBox#TimerRuleGameMinutesMinInput::up-arrow, QSpinBox#TimerRuleGameMinutesMaxInput::up-arrow,
    QSpinBox#TimerRuleGameHoursMinInput::up-arrow, QSpinBox#TimerRuleGameHoursMaxInput::up-arrow,
    QSpinBox#TimerRuleGameDaysMinInput::up-arrow, QSpinBox#TimerRuleGameDaysMaxInput::up-arrow,
    QSpinBox#TimerRuleIntervalMinInput::down-arrow, QSpinBox#TimerRuleIntervalMaxInput::down-arrow,
    QSpinBox#TimerRuleGameMinutesMinInput::down-arrow, QSpinBox#TimerRuleGameMinutesMaxInput::down-arrow,
    QSpinBox#TimerRuleGameHoursMinInput::down-arrow, QSpinBox#TimerRuleGameHoursMaxInput::down-arrow,
    QSpinBox#TimerRuleGameDaysMinInput::down-arrow, QSpinBox#TimerRuleGameDaysMaxInput::down-arrow {{
        width: 0px; 
        height: 0px;
    }}
    
    /* Enable/Disable Checkbox */
    QCheckBox#TimerRuleEnableCheckbox {{
        color: {base_color};
        font: 10pt "Consolas";
        /* Standard checkbox indicator styling will be inherited if not overridden here */
    }}
    
    /* Actions Area */
    QWidget#TimerRuleActionsContainer {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
    }}
    QWidget#TimerRuleActionRow {{
        background-color: {darker_bg}; /* Ensure rows also have this if they are separate widgets */
    }}
    QComboBox#TimerRuleActionTypeCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 9pt "Consolas";
    }}
    QComboBox#TimerRuleActionTypeCombo::drop-down {{
        border: none;
    }}
    QComboBox#TimerRuleActionTypeCombo::down-arrow {{
        image: none;
    }}
    QLineEdit#TimerRuleActionValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}
    QPushButton#TimerRuleActionRemoveButton {{
        color: {base_color};
        background-color: {darker_bg}; /* Changed from bg_color to match other small buttons */
        border: 1px solid {base_color};
        border-radius: 2px; /* Consistent with other small buttons */
    }}
    QPushButton#TimerRuleActionRemoveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    
    /* Main Action Buttons (Add Action, Save Rule) */
    QPushButton#TimerRuleAddActionButton, QPushButton#TimerRuleSaveButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color}; /* Ensure consistent border */
        border-radius: 3px;
        padding: 5px; /* Default padding from general QPushButton */
        font: 10pt "Consolas"; /* Slightly smaller than general QPushButton if needed */
    }}
    QPushButton#TimerRuleAddActionButton:hover, QPushButton#TimerRuleSaveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    /* --- End Timer Rules Styling --- */

    /* --- Styling for Start After Label --- */
    QLabel#TimerRuleStartAfterLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        /* margin-right: 5px; */ /* Add if more space needed before radios */
    }}

    /* --- Styling for Timer Rule Start After Radio Buttons --- */
    QRadioButton#TimerRuleStartAfterPlayerRadio, QRadioButton#TimerRuleStartAfterCharacterRadio, QRadioButton#TimerRuleStartAfterSceneChangeRadio {{
        color: {base_color};
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px; /* For round radio buttons */
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator:checked, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator:checked, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator:hover, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator:hover, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* --- Styling for Timer Rule Variable Scope Radio Buttons (Global/Character) --- */
    QRadioButton#TimerRuleVarScopeGlobalRadio, QRadioButton#TimerRuleVarScopeCharacterRadio {{
        color: {base_color}; /* CORRECTED: Single braces */
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px; /* For round radio buttons */
        border: 1px solid {base_color}; /* CORRECTED: Single braces */
        background: transparent; /* CORRECTED: Single braces */
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator:checked, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator:checked {{
        background-color: {base_color}; /* CORRECTED: Single braces */
        border: 1px solid {base_color}; /* CORRECTED: Single braces */
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator:hover, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator:hover {{
        border: 1px solid {brighter}; /* CORRECTED: Single braces */
    }}

    /* --- Styling for Timer Rule Condition Variable Input Labels & LineEdits --- */
    QLabel#TimerRuleConditionVarNameLabel, QLabel#TimerRuleConditionVarValueLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: normal; /* Explicitly normal */
    }}
    QLineEdit#TimerRuleConditionVarNameInput, QLineEdit#TimerRuleConditionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas"; /* Changed from 9pt for consistency */
    }}

    /* --- Styling for MULTIPLE Variable Conditions Area --- */
    QWidget#VariableConditionsArea {{
        /* Optional: Add border/background to visually group */
        /* background-color: rgba(0,0,0, 0.1); */
        /* border: 1px dotted {base_color}; */
        /* border-radius: 3px; */
        margin-top: 5px; /* Add some space above this section */
    }}

    QLabel#TimerConditionsOperatorLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        margin-right: 5px;
    }}
    
    QComboBox#TimerConditionsOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 10pt "Consolas";
        min-width: 60px;
    }}
    QComboBox#TimerConditionsOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#TimerConditionsOperatorCombo::down-arrow {{
        image: none;
    }}

    /* Styling for widgets WITHIN each VariableConditionRow */
    QWidget#VariableConditionRow QLineEdit#ConditionVarNameInput,
    QWidget#VariableConditionRow QLineEdit#ConditionValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px; /* Slightly smaller padding */
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas"; /* Smaller font for rows */
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 80px; /* Adjust width */
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo::drop-down {{
        border: none;
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo::down-arrow {{
        image: none;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px; /* Less spacing */
        background-color: transparent;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator:checked,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator:checked,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator:hover,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator:hover,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}
    QWidget#VariableConditionRow QPushButton#RemoveVariableConditionButton {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 2px;
        min-width: 20px; /* Match size? */
        max-width: 20px;
        min-height: 20px;
        max-height: 20px;
        padding: 0px;
        font-size: 12pt; /* Adjust for '-' sign */
    }}
    QWidget#VariableConditionRow QPushButton#RemoveVariableConditionButton:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* Button to add new rows */
    QPushButton#AddVariableConditionButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        margin-top: 5px; /* Add space above button */
    }}
    QPushButton#AddVariableConditionButton:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* --- Styling for Inter-Row Operator Combo --- */
    QComboBox#ConditionRowOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 55px; /* Keep narrow */
        max-width: 55px;
    }}
    QComboBox#ConditionRowOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#ConditionRowOperatorCombo::down-arrow {{
        image: none;
    }}

    /* --- Styling for Set Var Action Specific Inputs --- */
    QLineEdit#TimerRuleActionVarNameInput,
    QLineEdit#TimerRuleActionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px; /* Smaller padding for dense row */
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}

    QComboBox#TimerRuleSetVarOperationSelector {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 65px; /* Adjust as needed */
    }}
    QComboBox#TimerRuleSetVarOperationSelector::drop-down {{
        border: none;
    }}
    QComboBox#TimerRuleSetVarOperationSelector::down-arrow {{
        image: none;
    }}

    QRadioButton#TimerRuleActionScopeGlobalRadio,
    QRadioButton#TimerRuleActionScopeCharacterRadio,
    QRadioButton#TimerRuleActionScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator:checked,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator:checked,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator:hover,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator:hover,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* NEW: Setting Manager Variable Name/Value Inputs - with more specific selector */
    QWidget#VariableRow QLineEdit#SettingManagerVarNameInput,
    QWidget#VariableRow QLineEdit#SettingManagerVarValueInput,
    QLineEdit#SettingManagerVarNameInput,
    QLineEdit#SettingManagerVarValueInput {{
        color: {base_color} !important;
        background-color: {darker_bg} !important;
        border: 1px solid {base_color} !important;
        border-radius: 3px !important;
        padding: 3px !important;
        font: 10pt "Consolas" !important;
        selection-background-color: {highlight} !important;
        selection-color: white !important;
    }}
    /* END NEW */

    QLineEdit#PathDetailsNameInput, QTextEdit#PathDetailsDescInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt 'Consolas';
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QWidget[styleClass="PathDetailsNameInput"], QWidget[styleClass="PathDetailsDescInput"] {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt 'Consolas';
        selection-background-color: {highlight};
        selection-color: white;
    }}
    
    /* World Editor Scale Inputs */
    QLineEdit#WORLDToolbar_ScaleNumberInput, QLineEdit#WORLDToolbar_ScaleTimeInput,
    QLineEdit#LOCATIONToolbar_ScaleNumberInput, QLineEdit#LOCATIONToolbar_ScaleTimeInput {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        border: 1px solid {base_color}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
        max-width: 40px;
        min-width: 35px;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown, QComboBox#LOCATIONToolbar_ScaleUnitDropdown {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        border: 1px solid {base_color}; 
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
        max-width: 70px;
        min-width: 65px;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown::drop-down, QComboBox#LOCATIONToolbar_ScaleUnitDropdown::drop-down {{
        border: none;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown::down-arrow, QComboBox#LOCATIONToolbar_ScaleUnitDropdown::down-arrow {{
        image: none;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown QAbstractItemView, QComboBox#LOCATIONToolbar_ScaleUnitDropdown QAbstractItemView {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas";
    }}
    /* --- Inventory Scroll Area Fix --- */
    QScrollArea#InventoryScrollArea {{
        background-color: {darker_bg};
    }}
    QScrollArea#InventoryScrollArea QWidget {{
        background-color: {darker_bg};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio, QRadioButton#TimerGenerateUserMsgRadio, QRadioButton#TimerGenerateFullConvoRadio,
    QRadioButton#GenerateLastExchangeRadio, QRadioButton#GenerateUserMsgRadio, QRadioButton#GenerateFullConvoRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator, QRadioButton#TimerGenerateUserMsgRadio::indicator, QRadioButton#TimerGenerateFullConvoRadio::indicator,
    QRadioButton#GenerateLastExchangeRadio::indicator, QRadioButton#GenerateUserMsgRadio::indicator, QRadioButton#GenerateFullConvoRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator:checked, QRadioButton#TimerGenerateUserMsgRadio::indicator:checked, QRadioButton#TimerGenerateFullConvoRadio::indicator:checked,
    QRadioButton#GenerateLastExchangeRadio::indicator:checked, QRadioButton#GenerateUserMsgRadio::indicator:checked, QRadioButton#GenerateFullConvoRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator:hover, QRadioButton#TimerGenerateUserMsgRadio::indicator:hover, QRadioButton#TimerGenerateFullConvoRadio::indicator:hover,
    QRadioButton#GenerateLastExchangeRadio::indicator:hover, QRadioButton#GenerateUserMsgRadio::indicator:hover, QRadioButton#GenerateFullConvoRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    
    QLabel#TimerGenerateContextLabel, QLabel#TimerGenerateInstructionsLabel,
    QLabel#GenerateContextLabel, QLabel#GenerateInstructionsLabel {{
        color: {base_color};
        font: 9pt "Consolas";
        background-color: transparent;
    }}
    
    QTextEdit#TimerGenerateInstructionsInput, QTextEdit#GenerateInstructionsInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        padding: 3px;
    }}
    
    QWidget#TimerGenerateContextWidget, QWidget#GenerateContextWidget {{
        background-color: {darker_bg};
        border-radius: 3px;
    }}

    /* --- NEW: Generate Mode Radio Buttons Styling --- */
    QRadioButton#GenerateModeLLMRadio, QRadioButton#GenerateModeRandomRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#GenerateModeLLMRadio::indicator, QRadioButton#GenerateModeRandomRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#GenerateModeLLMRadio::indicator:checked, QRadioButton#GenerateModeRandomRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#GenerateModeLLMRadio::indicator:hover, QRadioButton#GenerateModeRandomRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* --- NEW: Random Generate Panel Filter Styling --- */
    QLineEdit#SettingFilterInput, QLineEdit#CharacterFilterInput,
    QLineEdit#RandomNumberMin, QLineEdit#RandomNumberMax {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 9pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Remove old QListWidget styling that's no longer needed */
    
    /* Keep button styling for other buttons */
    QPushButton#AddSettingFilterBtn, QPushButton#RemoveSettingFilterBtn,
    QPushButton#AddCharacterFilterBtn, QPushButton#RemoveCharacterFilterBtn {{
        /* These will inherit from QWidget#ThoughtToolContainer QPushButton for general CoT button style */
        /* Add specific overrides if general CoT button style isn't quite right */
        font: 9pt "Consolas";
        padding: 4px 8px; /* Slightly more padding for clarity */
    }}
    /* --- END NEW --- */

    /* --- NEW: Setting Manager Extra Area Styling --- */
    QWidget#SettingExtraAreaContainer {{
        background-color: {bg_color}; /* Use general background color */
        /* border: 1px solid {base_color}; REMOVED BORDER */
        border-radius: 3px;
        padding: 5px; /* Add some padding */
    }}

    QScrollArea#SettingExtraAreaScroll {{
        background-color: transparent; /* Scroll area itself is transparent */
        border: none; /* No border on the scroll area */
    }}

    /* Viewport of the scroll area, if needed for specific styling */
    QScrollArea#SettingExtraAreaScroll > QWidget > QWidget {{
        background-color: {bg_color}; /* Match container background */
    }}

    QCheckBox#SettingExteriorCheckbox {{
        /* Inherits general QCheckBox styling for color, font, indicator */
        /* Add specific overrides here if needed, e.g., margin */
        margin-bottom: 5px; /* Add some space below the checkbox */
    }}
    /* --- END NEW --- */

    /* --- NEW: Generation Options Panel Styling --- */
    QWidget#GenerationOptionsContainer {{
        background-color: {bg_color}; /* Use general background color */
        /* border: 1px solid {base_color}; no border for seamless look */
        border-radius: 3px;
        padding: 5px; /* Internal padding */
    }}

    QCheckBox#DescGenCheckbox, QCheckBox#ConnGenCheckbox, QCheckBox#InvGenCheckbox {{
        /* Inherit general QCheckBox styling */
        /* Add specific margins if needed, e.g., margin-bottom: 3px; */
    }}

    QPushButton#GenerateButton {{
        /* Inherit general QPushButton styling */
        /* Add specific margins if needed, e.g., margin-top: 5px; */
    }}
    /* --- END NEW --- */

    /* --- NEW: Setting Manager Connections Scroll Area Styling --- */
    QScrollArea#ConnectionsScrollArea {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
    }}
    QScrollArea#ConnectionsScrollArea > QWidget > QWidget {{
        background-color: {darker_bg};
        border: none;
    }}
    /* --- END NEW --- */

    /* --- Setting Manager Path Styling --- */
    /* Path widgets use existing styling classes and are handled automatically */

    /* Inventory Manager List Style (within tabs) */
    QListWidget#InventoryListWidget_Tab {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
        alternate-background-color: {bg_color}; /* Keep or remove based on preference */
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerList or adjust as needed */
    }}

    QListWidget#InventoryListWidget_Tab::item:selected {{
        background-color: {highlight};
        color: white;
    }}

    QListWidget#InventoryListWidget_Tab::item:hover {{
        background-color: {highlight};
        color: white; /* Match ActorManagerList hover or adjust */
    }}

    /* Inventory Manager Table Style (within tabs) */
    QTableWidget#InventoryTableWidget_Tab {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        gridline-color: {even_darker_bg}; /* Color for the grid lines */
        /* alternate-background-color: {bg_color}; */ /* For alternating row colors, enable if desired */
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
        border-radius: 3px;
        padding: 1px; /* Minimal padding for the table itself */
    }}

    QTableWidget#InventoryTableWidget_Tab::item {{
        border-bottom: 1px solid {even_darker_bg}; /* Separator for items */
        padding: 4px; /* Padding within each cell */
        color: {base_color};
    }}

    QTableWidget#InventoryTableWidget_Tab::item:selected {{
        background-color: {highlight};
        color: white; /* Text color for selected items */
    }}

    /* Style for the horizontal header of the inventory table */
    QHeaderView#InventoryTableWidget_Tab_HorizontalHeader::section {{
        background-color: {even_darker_bg};
        color: {base_color};
        padding: 4px;
        border-top: 1px solid {darker_bg};
        border-left: 1px solid {darker_bg};
        border-right: 1px solid {darker_bg};
        border-bottom: 1px solid {base_color}; /* Stronger bottom border for header */
        font-weight: bold;
    }}

    /* Style for the vertical header (if made visible) */
    QHeaderView#InventoryTableWidget_Tab_VerticalHeader::section {{
        background-color: {even_darker_bg};
        color: {base_color};
        padding: 4px;
        border-top: 1px solid {darker_bg};
        border-left: 1px solid {base_color}; /* Stronger left border for header */
        border-right: 1px solid {darker_bg};
        border-bottom: 1px solid {darker_bg};
    }}
    /* End of Inventory Manager Table Style */

    /* Actor Manager: Relations Container (Main widget, might not be visible bg) */
    QWidget#RelationsContainer {{
        background-color: transparent; /* Make outer container transparent */
        border: none; /* No border on outer container */
    }}

    /* Actor Manager: Relations Scroll Area */
    QScrollArea#RelationsScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Actor Manager: Relations Scroll Area Content Widget */
    QScrollArea#RelationsScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Actor Manager: Variables Scroll Area */
    QScrollArea#VariablesScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Actor Manager: Variables Scroll Area Content Widget */
    QScrollArea#VariablesScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Time Manager: Main Scroll Area */
    QScrollArea#TimeManagerScrollArea {{
        background-color: {darker_bg}; /* Match list backgrounds */
        border: 1px solid {base_color}; /* Use theme border */
        border-radius: 3px;
    }}

    /* Time Manager: Main Scroll Area Content Widget */
    QScrollArea#TimeManagerScrollArea > QWidget > QWidget {{
        background-color: {darker_bg}; /* Ensure content widget matches scroll area bg */
        border: none;
    }}

    /* Actor Manager: Inventory Container Border and Background */
    QWidget#InventoryContainer {{
        background-color: {darker_bg}; /* Use darker background like lists */
        border: 1px solid {base_color}; /* Use theme base color for border */
        border-radius: 3px;
    }}

    /* NEW: Actor Manager Name/Description Inputs */
    QLineEdit#ActorManagerNameInput, QTextEdit#ActorManagerDescInput {{
        color: {base_color};
        background-color: {darker_bg}; /* Match list background */
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#ActorManagerEditLabel {{ /* Label for actor edits */
        color: {base_color};
        font: 9pt "Consolas";
        margin-right: 5px; /* Add some space */
    }}
    
    /* Character Name Input Styling for Rules Manager */
    QLineEdit#CharacterNameInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QLabel#CharacterNameLabel {{
        color: {base_color};
        font: 12pt "Consolas";
        background-color: transparent;
    }}
    /* END NEW */

    QCheckBox {{
        color: {base_color};
        font: 9pt 'Consolas';
        spacing: 6px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 3px;
        background: transparent;
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:unchecked {{
        background: transparent;
        border: 1px solid {base_color};
    }}
    QCheckBox::indicator:disabled {{
        background: #333;
        border: 1.5px solid #444;
    }}

    /* Style for Optional Model Override Input */
    QLineEdit#ModelOverrideInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerNameInput */
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Style for Additional Instructions Input */
    QTextEdit#AdditionalInstructionsInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas"; /* Match ActorManagerDescInput */
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Container for Holding/Wearing content with border */
    QWidget#InventoryContentContainer {{
        border: 1px solid {base_color}; /* Use theme base color for consistent border */
        border-radius: 3px;
        margin-top: 4px; /* Add some space below the Inventory: label */
    }}

    /* --- NEW: Change Actor Location Action Widgets --- */
    QWidget#ChangeLocationWidget {{ /* Container for the whole action */
        background-color: rgba({r}, {g}, {b}, 0.05); /* Subtle tint like PairWidget */
        border-radius: 3px;
        padding: 4px;
        margin-top: 2px;
        border: 1px solid rgba({r}, {g}, {b}, 0.1); /* Very subtle border */
    }}

    QComboBox#ChangeLocationActorSelector, QComboBox#ChangeLocationTargetSettingCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        padding: 3px;
        font: 9pt "Consolas";
        border-radius: 3px;
        min-width: 120px;
    }}
    QComboBox#ChangeLocationActorSelector::drop-down, QComboBox#ChangeLocationTargetSettingCombo::drop-down {{
        border: none;
    }}
    QComboBox#ChangeLocationActorSelector::down-arrow, QComboBox#ChangeLocationTargetSettingCombo::down-arrow {{
        image: none;
    }}
    QComboBox#ChangeLocationActorSelector QAbstractItemView, QComboBox#ChangeLocationTargetSettingCombo QAbstractItemView {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Style the completer popup for Target Setting */
    QComboBox QAbstractItemView#qt_scrollarea_viewport {{
        border: 1px solid {base_color};
        background-color: {darker_bg};
        color: {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QRadioButton#ChangeLocationAdjacentRadio, QRadioButton#ChangeLocationFastTravelRadio, QRadioButton#ChangeLocationSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator, QRadioButton#ChangeLocationFastTravelRadio::indicator, QRadioButton#ChangeLocationSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator:checked, QRadioButton#ChangeLocationFastTravelRadio::indicator:checked, QRadioButton#ChangeLocationSettingRadio::indicator:checked {{
        background-color: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#ChangeLocationAdjacentRadio::indicator:hover, QRadioButton#ChangeLocationFastTravelRadio::indicator:hover, QRadioButton#ChangeLocationSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}
    /* --- END NEW --- */

    /* --- NEW: Style for Condition and Action Scope Radio Buttons --- */
    QRadioButton#ConditionVarScopeGlobalRadio, QRadioButton#ConditionVarScopeCharacterRadio,
    QRadioButton#ConditionVarScopePlayerRadio,
    QRadioButton#ConditionVarScopeSettingRadio,
    QRadioButton#ActionVarScopeGlobalRadio, QRadioButton#ActionVarScopeCharacterRadio, QRadioButton#ActionVarScopePlayerRadio, QRadioButton#ActionVarScopeSceneCharsRadio, QRadioButton#ActionVarScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator, QRadioButton#ConditionVarScopeCharacterRadio::indicator,
    QRadioButton#ConditionVarScopePlayerRadio::indicator,
    QRadioButton#ConditionVarScopeSettingRadio::indicator,
    QRadioButton#ActionVarScopeGlobalRadio::indicator, QRadioButton#ActionVarScopeCharacterRadio::indicator, QRadioButton#ActionVarScopePlayerRadio::indicator, QRadioButton#ActionVarScopeSceneCharsRadio::indicator, QRadioButton#ActionVarScopeSettingRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:checked, QRadioButton#ConditionVarScopeCharacterRadio::indicator:checked,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:checked,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:checked,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:checked, QRadioButton#ActionVarScopeCharacterRadio::indicator:checked, QRadioButton#ActionVarScopePlayerRadio::indicator:checked, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:checked, QRadioButton#ActionVarScopeSettingRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#ConditionVarScopeGlobalRadio::indicator:hover, QRadioButton#ConditionVarScopeCharacterRadio::indicator:hover,
    QRadioButton#ConditionVarScopePlayerRadio::indicator:hover,
    QRadioButton#ConditionVarScopeSettingRadio::indicator:hover,
    QRadioButton#ActionVarScopeGlobalRadio::indicator:hover, QRadioButton#ActionVarScopeCharacterRadio::indicator:hover, QRadioButton#ActionVarScopePlayerRadio::indicator:hover, QRadioButton#ActionVarScopeSceneCharsRadio::indicator:hover, QRadioButton#ActionVarScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* --- NEW: Style for Text Tag Mode Radio Buttons --- */
    QRadioButton#TagOverwriteRadio, QRadioButton#TagAppendRadio, QRadioButton#TagPrependRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TagOverwriteRadio::indicator, QRadioButton#TagAppendRadio::indicator, QRadioButton#TagPrependRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#TagOverwriteRadio::indicator:checked, QRadioButton#TagAppendRadio::indicator:checked, QRadioButton#TagPrependRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#TagOverwriteRadio::indicator:hover, QRadioButton#TagAppendRadio::indicator:hover, QRadioButton#TagPrependRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* Additional radio buttons that need styling (Keep for others like Prepend/Append/Replace/First/Last) */
    QRadioButton#PrependRadio, QRadioButton#AppendRadio, QRadioButton#ReplaceRadio, 
    QRadioButton#FirstSysMsgRadio, QRadioButton#LastSysMsgRadio
    {{
        color: {base_color}; /* Ensure color is set */
        font: 9pt "Consolas"; /* Smaller */
        spacing: 5px; /* Less spacing */
        background-color: transparent; /* Ensure no background override */
    }}
    QRadioButton#PrependRadio::indicator, QRadioButton#AppendRadio::indicator, QRadioButton#ReplaceRadio::indicator,
    QRadioButton#FirstSysMsgRadio::indicator, QRadioButton#LastSysMsgRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#PrependRadio::indicator:checked, QRadioButton#AppendRadio::indicator:checked, QRadioButton#ReplaceRadio::indicator:checked,
    QRadioButton#FirstSysMsgRadio::indicator:checked, QRadioButton#LastSysMsgRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#PrependRadio::indicator:hover, QRadioButton#AppendRadio::indicator:hover, QRadioButton#ReplaceRadio::indicator:hover,
    QRadioButton#FirstSysMsgRadio::indicator:hover, QRadioButton#LastSysMsgRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* NEW: Actor Manager Variable Name/Value Inputs */
    QLineEdit#ActorManagerVarNameInput, QLineEdit#ActorManagerVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    /* Highlight for selected variable row */
    QWidget.VariableRowSelected {{
        background-color: {highlight};
        border-radius: 3px;
    }}

    /* --- Timer Rules Styling --- */
    QWidget#TimerRulesContainer {{
        background-color: {bg_color}; /* Ensure base container has background */
        color: {base_color};
    }}
    
    QLabel#TimerRulesTitle {{ /* Assuming this exists or might be added later */
        color: {base_color};
        font: bold 12pt "Consolas";
    }}
    
    QLabel#TimerRulesDescription {{ /* Assuming this exists or might be added later */
        color: {base_color};
        font: 10pt "Consolas";
    }}
    
    QWidget#TimerRulesListControls {{ /* Parent of Rule ID/Desc and filter/list */
        background-color: {bg_color};
    }}
    
    QLineEdit#TimerRulesFilterInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}
    
    QListWidget#TimerRulesList {{
        background-color: {darker_bg};
        color: {base_color};
        border: 1px solid {base_color};
        border-radius: 3px;
        alternate-background-color: {bg_color};
        font: 9pt "Consolas";
    }}
    QListWidget#TimerRulesList::item:selected {{
        background-color: {highlight};
        color: white;
    }}
    QListWidget#TimerRulesList::item:hover {{
        background-color: {highlight};
        color: white; 
    }}
    
    QPushButton#TimerRuleAddButton, QPushButton#TimerRuleRemoveButton,
    QPushButton#TimerRuleMoveUpButton, QPushButton#TimerRuleMoveDownButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 2px;
    }}
    QPushButton#TimerRuleAddButton:hover, QPushButton#TimerRuleRemoveButton:hover,
    QPushButton#TimerRuleMoveUpButton:hover, QPushButton#TimerRuleMoveDownButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    
    /* Left and Right Panel Base Styling */
    QWidget#TimerRightPanelWidget,
    QWidget#TimerLeftPanelWidget {{
        background-color: {bg_color};
    }}
    QScrollArea#TimerRightPanelScroll,
    QScrollArea#TimerLeftPanelScroll {{
        background-color: transparent; 
        border: none;
    }}
    QScrollArea#TimerLeftPanelScroll > QWidget > QWidget {{ /* Viewport content of left scroll */
        background-color: {bg_color}; 
    }}
     QScrollArea#TimerRightPanelScroll > QWidget > QWidget {{ /* Viewport content of right scroll */
        background-color: {bg_color}; 
    }}

    /* Titles within Panels */
    QLabel#TimerConditionsTitleLabel {{
        color: {base_color};
        font: bold 11pt "Consolas"; 
        margin-bottom: 5px; 
    }}
    QLabel#TimerRuleActionsLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: bold; 
    }}

    /* Labels for specific inputs (Rule ID, Desc, Intervals, Var Conditions) */
    QLabel#TimerRuleIdLabel, QLabel#TimerRuleDescLabel, 
    QLabel#TimerRuleIntervalLabel,
    QLabel#TimerRuleGameTimeIntervalLabel,
    QLabel#TimerRuleGameMinutesLabel,
    QLabel#TimerRuleGameHoursLabel,
    QLabel#TimerRuleGameDaysLabel,
    QLabel#TimerRuleConditionVarNameLabel, 
    QLabel#TimerRuleConditionVarValueLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: normal; /* Explicitly normal */
    }}
    
    /* LineEdits for Rule ID, Description, and Variable Conditions */
    QLineEdit#TimerRuleIdInput, QLineEdit#TimerRuleDescInput,
    QLineEdit#TimerRuleConditionVarNameInput, QLineEdit#TimerRuleConditionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas"; /* Changed from 9pt for consistency */
    }}
    
    /* General SpinBox styling for fixed value inputs in Conditions Panel */
    QSpinBox#TimerRuleIntervalInput,
    QSpinBox#TimerRuleGameMinutesInput,
    QSpinBox#TimerRuleGameHoursInput,
    QSpinBox#TimerRuleGameDaysInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
    }}
    /* Buttons for these general spinboxes */
    QSpinBox#TimerRuleIntervalInput::up-button, QSpinBox#TimerRuleIntervalInput::down-button,
    QSpinBox#TimerRuleGameMinutesInput::up-button, QSpinBox#TimerRuleGameMinutesInput::down-button,
    QSpinBox#TimerRuleGameHoursInput::up-button, QSpinBox#TimerRuleGameHoursInput::down-button,
    QSpinBox#TimerRuleGameDaysInput::up-button, QSpinBox#TimerRuleGameDaysInput::down-button {{
        background-color: {base_color}; 
        border: 1px solid {bg_color};
        width: 12px;
        min-height: 10px;
        subcontrol-origin: border;
        margin: 1px;
    }}
    /* Arrows for these general spinboxes */
    QSpinBox#TimerRuleIntervalInput::up-arrow, QSpinBox#TimerRuleIntervalInput::down-arrow,
    QSpinBox#TimerRuleGameMinutesInput::up-arrow, QSpinBox#TimerRuleGameMinutesInput::down-arrow,
    QSpinBox#TimerRuleGameHoursInput::up-arrow, QSpinBox#TimerRuleGameHoursInput::down-arrow,
    QSpinBox#TimerRuleGameDaysInput::up-arrow, QSpinBox#TimerRuleGameDaysInput::down-arrow {{
        width: 0px; 
        height: 0px;
    }}

    /* Styling for Timer Rule Condition Radio Buttons */
    QRadioButton#TimerRuleConditionAlwaysRadio, QRadioButton#TimerRuleConditionVariableRadio {{
        color: {base_color};
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator, QRadioButton#TimerRuleConditionVariableRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator:checked, QRadioButton#TimerRuleConditionVariableRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleConditionAlwaysRadio::indicator:hover, QRadioButton#TimerRuleConditionVariableRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* Styling for Timer Rule Random Interval Checkboxes */
    QCheckBox#TimerRuleIntervalRandomCheckbox,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox,
    QCheckBox#TimerRuleGameHoursRandomCheckbox,
    QCheckBox#TimerRuleGameDaysRandomCheckbox {{
        color: {base_color};
        font: 10pt "Consolas"; 
        spacing: 5px;
        background-color: transparent;
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 3px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator:checked,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator:checked {{
        background-color: {base_color};
    }}
    QCheckBox#TimerRuleIntervalRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameMinutesRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameHoursRandomCheckbox::indicator:hover,
    QCheckBox#TimerRuleGameDaysRandomCheckbox::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* Styling for Timer Rule Random Interval Min/Max SpinBoxes */
    QSpinBox#TimerRuleIntervalMinInput, QSpinBox#TimerRuleIntervalMaxInput,
    QSpinBox#TimerRuleGameMinutesMinInput, QSpinBox#TimerRuleGameMinutesMaxInput,
    QSpinBox#TimerRuleGameHoursMinInput, QSpinBox#TimerRuleGameHoursMaxInput,
    QSpinBox#TimerRuleGameDaysMinInput, QSpinBox#TimerRuleGameDaysMaxInput {{
        color: {base_color};
        background-color: {darker_bg}; 
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px 3px; 
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas";
        min-width: 60px; 
    }}
    /* Buttons for these Min/Max spinboxes */
    QSpinBox#TimerRuleIntervalMinInput::up-button, QSpinBox#TimerRuleIntervalMaxInput::up-button,
    QSpinBox#TimerRuleGameMinutesMinInput::up-button, QSpinBox#TimerRuleGameMinutesMaxInput::up-button,
    QSpinBox#TimerRuleGameHoursMinInput::up-button, QSpinBox#TimerRuleGameHoursMaxInput::up-button,
    QSpinBox#TimerRuleGameDaysMinInput::up-button, QSpinBox#TimerRuleGameDaysMaxInput::up-button,
    QSpinBox#TimerRuleIntervalMinInput::down-button, QSpinBox#TimerRuleIntervalMaxInput::down-button,
    QSpinBox#TimerRuleGameMinutesMinInput::down-button, QSpinBox#TimerRuleGameMinutesMaxInput::down-button,
    QSpinBox#TimerRuleGameHoursMinInput::down-button, QSpinBox#TimerRuleGameHoursMaxInput::down-button,
    QSpinBox#TimerRuleGameDaysMinInput::down-button, QSpinBox#TimerRuleGameDaysMaxInput::down-button {{
        background-color: {base_color};
        border: 1px solid {bg_color};
        width: 12px;
        min-height: 10px; 
        subcontrol-origin: border;
        margin: 1px;
    }}
    /* Arrows for these Min/Max spinboxes */
    QSpinBox#TimerRuleIntervalMinInput::up-arrow, QSpinBox#TimerRuleIntervalMaxInput::up-arrow,
    QSpinBox#TimerRuleGameMinutesMinInput::up-arrow, QSpinBox#TimerRuleGameMinutesMaxInput::up-arrow,
    QSpinBox#TimerRuleGameHoursMinInput::up-arrow, QSpinBox#TimerRuleGameHoursMaxInput::up-arrow,
    QSpinBox#TimerRuleGameDaysMinInput::up-arrow, QSpinBox#TimerRuleGameDaysMaxInput::up-arrow,
    QSpinBox#TimerRuleIntervalMinInput::down-arrow, QSpinBox#TimerRuleIntervalMaxInput::down-arrow,
    QSpinBox#TimerRuleGameMinutesMinInput::down-arrow, QSpinBox#TimerRuleGameMinutesMaxInput::down-arrow,
    QSpinBox#TimerRuleGameHoursMinInput::down-arrow, QSpinBox#TimerRuleGameHoursMaxInput::down-arrow,
    QSpinBox#TimerRuleGameDaysMinInput::down-arrow, QSpinBox#TimerRuleGameDaysMaxInput::down-arrow {{
        width: 0px; 
        height: 0px;
    }}
    
    /* Enable/Disable Checkbox */
    QCheckBox#TimerRuleEnableCheckbox {{
        color: {base_color};
        font: 10pt "Consolas";
        /* Standard checkbox indicator styling will be inherited if not overridden here */
    }}
    
    /* Actions Area */
    QWidget#TimerRuleActionsContainer {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
    }}
    QWidget#TimerRuleActionRow {{
        background-color: {darker_bg}; /* Ensure rows also have this if they are separate widgets */
    }}
    QComboBox#TimerRuleActionTypeCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 9pt "Consolas";
    }}
    QComboBox#TimerRuleActionTypeCombo::drop-down {{
        border: none;
    }}
    QComboBox#TimerRuleActionTypeCombo::down-arrow {{
        image: none;
    }}
    QLineEdit#TimerRuleActionValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}
    QPushButton#TimerRuleActionRemoveButton {{
        color: {base_color};
        background-color: {darker_bg}; /* Changed from bg_color to match other small buttons */
        border: 1px solid {base_color};
        border-radius: 2px; /* Consistent with other small buttons */
    }}
    QPushButton#TimerRuleActionRemoveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    
    /* Main Action Buttons (Add Action, Save Rule) */
    QPushButton#TimerRuleAddActionButton, QPushButton#TimerRuleSaveButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color}; /* Ensure consistent border */
        border-radius: 3px;
        padding: 5px; /* Default padding from general QPushButton */
        font: 10pt "Consolas"; /* Slightly smaller than general QPushButton if needed */
    }}
    QPushButton#TimerRuleAddActionButton:hover, QPushButton#TimerRuleSaveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    /* --- End Timer Rules Styling --- */

    /* --- Styling for Start After Label --- */
    QLabel#TimerRuleStartAfterLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        /* margin-right: 5px; */ /* Add if more space needed before radios */
    }}

    /* --- Styling for Timer Rule Start After Radio Buttons --- */
    QRadioButton#TimerRuleStartAfterPlayerRadio, QRadioButton#TimerRuleStartAfterCharacterRadio, QRadioButton#TimerRuleStartAfterSceneChangeRadio {{
        color: {base_color};
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px; /* For round radio buttons */
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator:checked, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator:checked, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleStartAfterPlayerRadio::indicator:hover, QRadioButton#TimerRuleStartAfterCharacterRadio::indicator:hover, QRadioButton#TimerRuleStartAfterSceneChangeRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* --- Styling for Timer Rule Variable Scope Radio Buttons (Global/Character) --- */
    QRadioButton#TimerRuleVarScopeGlobalRadio, QRadioButton#TimerRuleVarScopeCharacterRadio {{
        color: {base_color}; /* CORRECTED: Single braces */
        font: 10pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 8px; /* For round radio buttons */
        border: 1px solid {base_color}; /* CORRECTED: Single braces */
        background: transparent; /* CORRECTED: Single braces */
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator:checked, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator:checked {{
        background-color: {base_color}; /* CORRECTED: Single braces */
        border: 1px solid {base_color}; /* CORRECTED: Single braces */
    }}
    QRadioButton#TimerRuleVarScopeGlobalRadio::indicator:hover, QRadioButton#TimerRuleVarScopeCharacterRadio::indicator:hover {{
        border: 1px solid {brighter}; /* CORRECTED: Single braces */
    }}

    /* --- Styling for Timer Rule Condition Variable Input Labels & LineEdits --- */
    QLabel#TimerRuleConditionVarNameLabel, QLabel#TimerRuleConditionVarValueLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        font-weight: normal; /* Explicitly normal */
    }}
    QLineEdit#TimerRuleConditionVarNameInput, QLineEdit#TimerRuleConditionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 10pt "Consolas"; /* Changed from 9pt for consistency */
    }}

    /* --- Styling for MULTIPLE Variable Conditions Area --- */
    QWidget#VariableConditionsArea {{
        /* Optional: Add border/background to visually group */
        /* background-color: rgba(0,0,0, 0.1); */
        /* border: 1px dotted {base_color}; */
        /* border-radius: 3px; */
        margin-top: 5px; /* Add some space above this section */
    }}

    QLabel#TimerConditionsOperatorLabel {{
        color: {base_color};
        font: 10pt "Consolas";
        margin-right: 5px;
    }}
    
    QComboBox#TimerConditionsOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 10pt "Consolas";
        min-width: 60px;
    }}
    QComboBox#TimerConditionsOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#TimerConditionsOperatorCombo::down-arrow {{
        image: none;
    }}

    /* Styling for widgets WITHIN each VariableConditionRow */
    QWidget#VariableConditionRow QLineEdit#ConditionVarNameInput,
    QWidget#VariableConditionRow QLineEdit#ConditionValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px; /* Slightly smaller padding */
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas"; /* Smaller font for rows */
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 80px; /* Adjust width */
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo::drop-down {{
        border: none;
    }}
    QWidget#VariableConditionRow QComboBox#ConditionOperatorCombo::down-arrow {{
        image: none;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px; /* Less spacing */
        background-color: transparent;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator:checked,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator:checked,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QWidget#VariableConditionRow QRadioButton#ConditionScopeGlobalRadio::indicator:hover,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeCharacterRadio::indicator:hover,
    QWidget#VariableConditionRow QRadioButton#ConditionScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}
    QWidget#VariableConditionRow QPushButton#RemoveVariableConditionButton {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 2px;
        min-width: 20px; /* Match size? */
        max-width: 20px;
        min-height: 20px;
        max-height: 20px;
        padding: 0px;
        font-size: 12pt; /* Adjust for '-' sign */
    }}
    QWidget#VariableConditionRow QPushButton#RemoveVariableConditionButton:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* Button to add new rows */
    QPushButton#AddVariableConditionButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt "Consolas";
        margin-top: 5px; /* Add space above button */
    }}
    QPushButton#AddVariableConditionButton:hover {{
        background-color: {highlight};
        color: white;
    }}

    /* --- Styling for Inter-Row Operator Combo --- */
    QComboBox#ConditionRowOperatorCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 55px; /* Keep narrow */
        max-width: 55px;
    }}
    QComboBox#ConditionRowOperatorCombo::drop-down {{
        border: none;
    }}
    QComboBox#ConditionRowOperatorCombo::down-arrow {{
        image: none;
    }}

    /* --- Styling for Set Var Action Specific Inputs --- */
    QLineEdit#TimerRuleActionVarNameInput,
    QLineEdit#TimerRuleActionVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px; /* Smaller padding for dense row */
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
    }}

    QComboBox#TimerRuleSetVarOperationSelector {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 1px;
        font: 9pt "Consolas";
        min-width: 65px; /* Adjust as needed */
    }}
    QComboBox#TimerRuleSetVarOperationSelector::drop-down {{
        border: none;
    }}
    QComboBox#TimerRuleSetVarOperationSelector::down-arrow {{
        image: none;
    }}

    QRadioButton#TimerRuleActionScopeGlobalRadio,
    QRadioButton#TimerRuleActionScopeCharacterRadio,
    QRadioButton#TimerRuleActionScopeSettingRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: transparent;
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator:checked,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator:checked,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
    }}
    QRadioButton#TimerRuleActionScopeGlobalRadio::indicator:hover,
    QRadioButton#TimerRuleActionScopeCharacterRadio::indicator:hover,
    QRadioButton#TimerRuleActionScopeSettingRadio::indicator:hover {{
        border: 1px solid {brighter};
    }}

    /* NEW: Setting Manager Variable Name/Value Inputs - with more specific selector */
    QWidget#VariableRow QLineEdit#SettingManagerVarNameInput,
    QWidget#VariableRow QLineEdit#SettingManagerVarValueInput,
    QLineEdit#SettingManagerVarNameInput,
    QLineEdit#SettingManagerVarValueInput {{
        color: {base_color} !important;
        background-color: {darker_bg} !important;
        border: 1px solid {base_color} !important;
        border-radius: 3px !important;
        padding: 3px !important;
        font: 10pt "Consolas" !important;
        selection-background-color: {highlight} !important;
        selection-color: white !important;
    }}
    /* END NEW */

    QLineEdit#PathDetailsNameInput, QTextEdit#PathDetailsDescInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt 'Consolas';
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QWidget[styleClass="PathDetailsNameInput"], QWidget[styleClass="PathDetailsDescInput"] {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 10pt 'Consolas';
        selection-background-color: {highlight};
        selection-color: white;
    }}
    
    /* World Editor Scale Inputs */
    QLineEdit#WORLDToolbar_ScaleNumberInput, QLineEdit#WORLDToolbar_ScaleTimeInput,
    QLineEdit#LOCATIONToolbar_ScaleNumberInput, QLineEdit#LOCATIONToolbar_ScaleTimeInput {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        border: 1px solid {base_color}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
        max-width: 40px;
        min-width: 35px;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown, QComboBox#LOCATIONToolbar_ScaleUnitDropdown {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        border: 1px solid {base_color}; 
        font: 9pt "Consolas";
        border-radius: 3px;
        padding: 3px;
        max-width: 70px;
        min-width: 65px;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown::drop-down, QComboBox#LOCATIONToolbar_ScaleUnitDropdown::drop-down {{
        border: none;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown::down-arrow, QComboBox#LOCATIONToolbar_ScaleUnitDropdown::down-arrow {{
        image: none;
    }}
    
    QComboBox#WORLDToolbar_ScaleUnitDropdown QAbstractItemView, QComboBox#LOCATIONToolbar_ScaleUnitDropdown QAbstractItemView {{
        color: {base_color}; 
        background-color: {darker_bg}; 
        selection-background-color: {highlight}; 
        selection-color: white;
        font: 9pt "Consolas";
    }}
    /* --- Inventory Scroll Area Fix --- */
    QScrollArea#InventoryScrollArea {{
        background-color: {darker_bg};
    }}
    QScrollArea#InventoryScrollArea QWidget {{
        background-color: {darker_bg};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio, QRadioButton#TimerGenerateUserMsgRadio, QRadioButton#TimerGenerateFullConvoRadio,
    QRadioButton#GenerateLastExchangeRadio, QRadioButton#GenerateUserMsgRadio, QRadioButton#GenerateFullConvoRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 3px;
        background-color: transparent;
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator, QRadioButton#TimerGenerateUserMsgRadio::indicator, QRadioButton#TimerGenerateFullConvoRadio::indicator,
    QRadioButton#GenerateLastExchangeRadio::indicator, QRadioButton#GenerateUserMsgRadio::indicator, QRadioButton#GenerateFullConvoRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background-color: {bg_color};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator:checked, QRadioButton#TimerGenerateUserMsgRadio::indicator:checked, QRadioButton#TimerGenerateFullConvoRadio::indicator:checked,
    QRadioButton#GenerateLastExchangeRadio::indicator:checked, QRadioButton#GenerateUserMsgRadio::indicator:checked, QRadioButton#GenerateFullConvoRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    
    QRadioButton#TimerGenerateLastExchangeRadio::indicator:hover, QRadioButton#TimerGenerateUserMsgRadio::indicator:hover, QRadioButton#TimerGenerateFullConvoRadio::indicator:hover,
    QRadioButton#GenerateLastExchangeRadio::indicator:hover, QRadioButton#GenerateUserMsgRadio::indicator:hover, QRadioButton#GenerateFullConvoRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    
    QLabel#TimerGenerateContextLabel, QLabel#TimerGenerateInstructionsLabel,
    QLabel#GenerateContextLabel, QLabel#GenerateInstructionsLabel {{
        color: {base_color};
        font: 9pt "Consolas";
        background-color: transparent;
    }}
    
    QTextEdit#TimerGenerateInstructionsInput, QTextEdit#GenerateInstructionsInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        selection-background-color: {highlight};
        selection-color: white;
        font: 9pt "Consolas";
        padding: 3px;
    }}
    
    QWidget#TimerGenerateContextWidget, QWidget#GenerateContextWidget {{
        background-color: {darker_bg};
        border-radius: 3px;
    }}

    /* --- NEW: Generate Mode Radio Buttons Styling --- */
    QRadioButton#GenerateModeLLMRadio, QRadioButton#GenerateModeRandomRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 5px;
        background-color: transparent;
    }}
    QRadioButton#GenerateModeLLMRadio::indicator, QRadioButton#GenerateModeRandomRadio::indicator {{
        width: 13px;
        height: 13px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#GenerateModeLLMRadio::indicator:checked, QRadioButton#GenerateModeRandomRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#GenerateModeLLMRadio::indicator:hover, QRadioButton#GenerateModeRandomRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}
    /* --- END NEW --- */

    /* --- NEW: Random Generate Panel Filter Styling --- */
    QLineEdit#SettingFilterInput, QLineEdit#CharacterFilterInput,
    QLineEdit#RandomNumberMin, QLineEdit#RandomNumberMax {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 3px;
        font: 9pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}

    /* Remove old QListWidget styling that's no longer needed */
    
    /* Keep button styling for other buttons */
    QPushButton#AddSettingFilterBtn, QPushButton#RemoveSettingFilterBtn,
    QPushButton#AddCharacterFilterBtn, QPushButton#RemoveCharacterFilterBtn {{
        /* These will inherit from QWidget#ThoughtToolContainer QPushButton for general CoT button style */
        /* Add specific overrides if general CoT button style isn't quite right */
        font: 9pt "Consolas";
        padding: 4px 8px; /* Slightly more padding for clarity */
    }}
    /* --- END NEW --- */

    /* --- NEW: Setting Manager Extra Area Styling --- */
    QWidget#SettingExtraAreaContainer {{
        background-color: {bg_color}; /* Use general background color */
        /* border: 1px solid {base_color}; REMOVED BORDER */
        border-radius: 3px;
        padding: 5px; /* Add some padding */
    }}

    QScrollArea#SettingExtraAreaScroll {{
        background-color: transparent; /* Scroll area itself is transparent */
        border: none; /* No border on the scroll area */
    }}

    /* Viewport of the scroll area, if needed for specific styling */
    QScrollArea#SettingExtraAreaScroll > QWidget > QWidget {{
        background-color: {bg_color}; /* Match container background */
    }}

    QCheckBox#SettingExteriorCheckbox {{
        /* Inherits general QCheckBox styling for color, font, indicator */
        /* Add specific overrides here if needed, e.g., margin */
        margin-bottom: 5px; /* Add some space below the checkbox */
    }}
    /* --- END NEW --- */

    /* --- NEW: Generation Options Panel Styling --- */
    QWidget#GenerationOptionsContainer {{
        background-color: {bg_color}; /* Use general background color */
        /* border: 1px solid {base_color}; no border for seamless look */
        border-radius: 3px;
        padding: 5px; /* Internal padding */
    }}

    QCheckBox#DescGenCheckbox, QCheckBox#ConnGenCheckbox, QCheckBox#InvGenCheckbox {{
        /* Inherit general QCheckBox styling */
        /* Add specific margins if needed, e.g., margin-bottom: 3px; */
    }}

    QPushButton#GenerateButton {{
        /* Inherit general QPushButton styling */
        /* Add specific margins if needed, e.g., margin-top: 5px; */
    }}
    /* --- END NEW --- */

    /* --- NEW: Setting Manager Connections Scroll Area Styling --- */
    QScrollArea#ConnectionsScrollArea {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
    }}
    QScrollArea#ConnectionsScrollArea > QWidget > QWidget {{
        background-color: {darker_bg};
        border: none;
    }}
    /* --- END NEW --- */

    /* --- Setting Manager Path Styling --- */
    /* Path widgets use existing styling classes and are handled automatically */

    /* Action Reordering Buttons (Move Up/Down) */
    QPushButton#MoveUpActionButton, QPushButton#MoveDownActionButton {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 2px;
        min-width: 28px;
        max-width: 28px;
        min-height: 22px;
        max-height: 22px;
        padding: 0px;
        font: 12pt "Consolas";
        font-weight: bold;
    }}
    QPushButton#MoveUpActionButton:hover, QPushButton#MoveDownActionButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    QPushButton#MoveUpActionButton:disabled, QPushButton#MoveDownActionButton:disabled {{
        color: {darker_bg};
        background-color: transparent;
        border: 1px solid {darker_bg};
    }}
    
    /* Main Action Buttons (Add Action, Save Rule) */
    QPushButton#TimerRuleAddActionButton, QPushButton#TimerRuleSaveButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color}; /* Ensure consistent border */
        border-radius: 3px;
        padding: 5px; /* Default padding from general QPushButton */
        font: 10pt "Consolas"; /* Slightly smaller than general QPushButton if needed */
    }}
    QPushButton#TimerRuleAddActionButton:hover, QPushButton#TimerRuleSaveButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    /* --- End Timer Rules Styling --- */

    /* --- Left Splitter Button Styling --- */
    #LeftSplitterContainer QPushButton {{
        font: 10pt "Consolas"; /* Smaller font */
        font-weight: bold;
        text-transform: uppercase;
        padding: 2px; /* Reduced padding */
        min-height: 24px; /* Smaller height */
        max-height: 24px;
        border-radius: 2px;
        border: 1px solid transparent; /* Transparent border for normal state */
        background-color: transparent; /* Transparent background */
    }}
    #LeftSplitterContainer QPushButton:hover {{
        background-color: {highlight};
        border: 1px solid {base_color};
        color: white;
    }}
    #LeftSplitterContainer QPushButton:checked {{
        background-color: {base_color};
        border: 1px solid {base_color};
        color: white;
    }}
    #LeftSplitterContainer QPushButton:checked:hover {{
        background-color: {brighter};
        border: 1px solid {brighter};
        color: white;
    }}
    /* --- End Left Splitter Button Styling --- */

    /* --- Right Splitter Styling --- */
    QWidget#RightSplitterWidget {{
        background-color: {darker_bg};
        color: {base_color};
    }}
    /* --- End Right Splitter Styling --- */

    /* --- Character Sheet Styling --- */
    QWidget#CharacterSheetPage {{
        background-color: {bg_color};
        color: {base_color};
    }}
    
    QLabel#CharacterSheetHeader {{
        color: {base_color};
        font: bold 11pt "Consolas";
        padding: 4px;
        border-bottom: 1px solid {base_color};
        margin-bottom: 3px;
    }}
    
    QScrollArea#CharacterSheetScrollArea {{
        background-color: {bg_color};
        border: none;
    }}
    QScrollArea#CharacterSheetScrollArea > QWidget > QWidget {{
        background-color: {bg_color};
    }}
    
    QWidget#CharacterSheetContent {{
        background-color: {bg_color};
    }}
    
    QLabel#CharacterNameLabel {{
        color: {base_color};
        font: bold 12pt "Consolas";
        padding: 3px;
        margin-bottom: 2px;
    }}
    
    QLabel#CharacterStatusLabel {{
        color: {base_color};
        font: 9pt "Consolas";
        padding: 2px;
        margin-bottom: 4px;
    }}
    
    QFrame#CharacterSectionFrame {{
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        margin: 2px;
        padding: 3px;
    }}
    
    QLabel#CharacterSectionTitle {{
        color: {base_color};
        font: bold 9pt "Consolas";
        padding: 2px;
        margin-bottom: 3px;
        border-bottom: 1px solid rgba({r}, {g}, {b}, 0.3);
    }}
    
    QLabel#CharacterDescriptionLabel, QLabel#CharacterAppearanceLabel {{
        color: {base_color};
        font: 8pt "Consolas";
        padding: 3px;
        background-color: {bg_color};
        border: 1px solid rgba({r}, {g}, {b}, 0.2);
        border-radius: 2px;
        margin: 1px;
    }}
    
    QLabel#EquipmentSlotLabel {{
        color: {base_color};
        font: 7pt "Consolas";
        font-weight: bold;
        padding: 1px;
    }}
    
    QLabel#EquipmentItemLabel {{
        color: {base_color};
        font: 7pt "Consolas";
        padding: 2px;
        background-color: {bg_color};
        border: 1px solid rgba({r}, {g}, {b}, 0.2);
        border-radius: 2px;
        margin: 1px;
        min-height: 12px;
    }}
    
    QLabel#EquipmentItemLabel[equipped="true"] {{
        background-color: rgba(0, 150, 0, 0.2);
        border: 1px solid rgba(0, 200, 0, 0.5);
        color: #90EE90;
    }}
    
    QLabel#EquipmentItemLabel[equipped="false"] {{
        background-color: {darker_bg};
        border: 1px solid rgba({r}, {g}, {b}, 0.1);
        color: rgba({r}, {g}, {b}, 0.6);
    }}
    
    QLabel#HeldItemSlotLabel {{
        color: {base_color};
        font: bold 8pt "Consolas";
        padding: 2px;
    }}
    
    QLabel#HeldItemLabel {{
        color: {base_color};
        font: 8pt "Consolas";
        padding: 3px;
        background-color: {bg_color};
        border: 1px solid rgba({r}, {g}, {b}, 0.3);
        border-radius: 2px;
        margin: 1px;
        min-height: 16px;
    }}
    /* --- End Character Sheet Styling --- */

    /* Actor Manager Refresh Buttons */
    QPushButton#RefreshButton, QPushButton#LocationRefreshButton {{
        color: {base_color};
        background-color: {bg_color};
        border: 1px solid {base_color};
        border-radius: 15px;
        padding: 3px;
        font-weight: bold;
    }}
    QPushButton#RefreshButton:hover, QPushButton#LocationRefreshButton:hover {{
        background-color: {highlight};
        color: white;
    }}
    QPushButton#RefreshButton:pressed, QPushButton#LocationRefreshButton:pressed {{
        background-color: {base_color};
        color: {bg_color};
    }}

    /* Inventory Radio Buttons */
    QRadioButton#InventoryConsumableRadio, QRadioButton#InventoryWeaponRadio, QRadioButton#InventoryWearableRadio, QRadioButton#InventoryReadableRadio, QRadioButton#InventoryLiquidRadio {{
        color: {base_color};
        font: 9pt "Consolas";
        spacing: 4px;
        background-color: transparent;
    }}
    QRadioButton#InventoryConsumableRadio::indicator, QRadioButton#InventoryWeaponRadio::indicator, QRadioButton#InventoryWearableRadio::indicator, QRadioButton#InventoryReadableRadio::indicator, QRadioButton#InventoryLiquidRadio::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 6px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QRadioButton#InventoryConsumableRadio::indicator:checked, QRadioButton#InventoryWeaponRadio::indicator:checked, QRadioButton#InventoryWearableRadio::indicator:checked, QRadioButton#InventoryReadableRadio::indicator:checked, QRadioButton#InventoryLiquidRadio::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QRadioButton#InventoryConsumableRadio::indicator:hover, QRadioButton#InventoryWeaponRadio::indicator:hover, QRadioButton#InventoryWearableRadio::indicator:hover, QRadioButton#InventoryReadableRadio::indicator:hover, QRadioButton#InventoryLiquidRadio::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}

    /* Container Liquid Checkboxes */
    QCheckBox#InventoryContainerLiquidCheckbox {{
        color: {base_color};
        font: 8pt "Consolas";
        spacing: 4px;
        background-color: transparent;
    }}
    QCheckBox#InventoryContainerLiquidCheckbox::indicator {{
        width: 12px;
        height: 12px;
        border-radius: 2px;
        border: 1px solid {base_color};
        background: {bg_color};
    }}
    QCheckBox#InventoryContainerLiquidCheckbox::indicator:checked {{
        background: {highlight};
        border: 1px solid {brighter};
    }}
    QCheckBox#InventoryContainerLiquidCheckbox::indicator:hover {{
        border: 1px solid {brighter};
        background: transparent;
    }}

    /* Inventory Variable Actions Widgets */
    QLineEdit#InventoryVarNameInput, QLineEdit#InventoryVarValueInput {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 9pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}

    QComboBox#InventoryVarOperationCombo {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        border-radius: 3px;
        padding: 2px;
        font: 9pt "Consolas";
        selection-background-color: {highlight};
        selection-color: white;
    }}
    QComboBox#InventoryVarOperationCombo::drop-down {{
        border: none;
    }}
    QComboBox#InventoryVarOperationCombo::down-arrow {{
        image: none;
    }}
    QComboBox#InventoryVarOperationCombo QAbstractItemView {{
        color: {base_color};
        background-color: {darker_bg};
        border: 1px solid {base_color};
        selection-background-color: {highlight};
        selection-color: white;
    }}

    """
    try:
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)
            if hasattr(target_widget, 'color_btn'):
                target_widget.color_btn.setStyleSheet(
                    f"background-color: {base_color}; "
                    f"border: 2px solid {base_color};"
                )
                print("Updated color button style")
        else:
            print("Error: Could not get QApplication instance to apply stylesheet")
    except Exception as e:
        print(f"Error applying stylesheet: {e}")
