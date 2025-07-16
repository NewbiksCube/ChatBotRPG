from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QRadioButton, QButtonGroup, QComboBox, QCompleter, QVBoxLayout, QHBoxLayout, QApplication, QMessageBox, QCheckBox, QStackedWidget, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.utils import is_valid_widget, _get_available_actors, _get_available_settings

def create_generate_setting_widget(parent=None):
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    instructions_label = QLabel("Instructions:")
    instructions_label.setObjectName("InstructionsLabel")
    instructions_editor = QTextEdit()
    instructions_editor.setObjectName("GenerateSettingInstructionsEditor")
    instructions_editor.setMaximumHeight(150)
    layout.addWidget(instructions_label)
    layout.addWidget(instructions_editor)
    return widget

def create_generate_random_list_widget(parent=None):
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    mode_layout = QHBoxLayout()
    mode_label = QLabel("Mode:")
    mode_label.setObjectName("GenRandomListModeLabel")
    mode_label.setFont(QFont('Consolas', 9))
    mode_new_radio = QRadioButton("New Random List")
    mode_new_radio.setObjectName("GenRandomListNewRadio")
    mode_new_radio.setFont(QFont('Consolas', 9))
    mode_new_radio.setChecked(True)
    mode_permutate_radio = QRadioButton("Permutate")
    mode_permutate_radio.setObjectName("GenRandomListPermutateRadio")
    mode_permutate_radio.setFont(QFont('Consolas', 9))
    mode_layout.addWidget(mode_label)
    mode_layout.addWidget(mode_new_radio)
    mode_layout.addWidget(mode_permutate_radio)
    mode_layout.addStretch(1)
    layout.addLayout(mode_layout)
    name_layout = QHBoxLayout()
    name_label = QLabel("Name:")
    name_label.setObjectName("GenRandomListNameLabel")
    name_label.setFont(QFont('Consolas', 9))
    name_input = QLineEdit()
    name_input.setObjectName("GenRandomListNameInput")
    name_input.setFont(QFont('Consolas', 9))
    name_input.setPlaceholderText("Enter generator name (required)")
    name_layout.addWidget(name_label)
    name_layout.addWidget(name_input)
    layout.addLayout(name_layout)
    instructions_label = QLabel("Instructions:")
    instructions_label.setObjectName("GenRandomListInstructionsLabel")
    instructions_label.setFont(QFont('Consolas', 9))
    instructions_input = QTextEdit()
    instructions_input.setObjectName("GenRandomListInstructionsInput")
    instructions_input.setFont(QFont('Consolas', 9))
    instructions_input.setPlaceholderText("Enter instructions for generating/permutating the random list")
    instructions_input.setMaximumHeight(100)
    layout.addWidget(instructions_label)
    layout.addWidget(instructions_input)
    permutate_options = QWidget()
    permutate_options.setObjectName("GenRandomListPermutateOptions")
    permutate_layout = QHBoxLayout(permutate_options)
    permutate_layout.setContentsMargins(0, 0, 0, 0)
    objects_checkbox = QCheckBox("Permutate Objects")
    objects_checkbox.setObjectName("GenRandomListObjectsCheckbox")
    objects_checkbox.setFont(QFont('Consolas', 9))
    objects_checkbox.setChecked(True)
    weights_checkbox = QCheckBox("Permutate Weights")
    weights_checkbox.setObjectName("GenRandomListWeightsCheckbox")
    weights_checkbox.setFont(QFont('Consolas', 9))
    weights_checkbox.setChecked(True)
    permutate_layout.addWidget(objects_checkbox)
    permutate_layout.addWidget(weights_checkbox)
    permutate_layout.addStretch(1)
    layout.addWidget(permutate_options)
    permutate_options.setVisible(False)
    model_layout = QHBoxLayout()
    model_label = QLabel("Model Override:")
    model_label.setObjectName("GenRandomListModelLabel")
    model_label.setFont(QFont('Consolas', 9))
    model_input = QLineEdit()
    model_input.setObjectName("GenRandomListModelInput")
    model_input.setFont(QFont('Consolas', 9))
    model_input.setPlaceholderText("Optional model override (e.g., anthropic/claude-3.5-sonnet)")
    model_layout.addWidget(model_label)
    model_layout.addWidget(model_input)
    layout.addLayout(model_layout)
    context_layout = QHBoxLayout()
    context_label = QLabel("Context:")
    context_label.setObjectName("GenRandomListContextLabel")
    context_label.setFont(QFont('Consolas', 9))
    context_no_context_radio = QRadioButton("No Context")
    context_no_context_radio.setObjectName("GenRandomListNoContextRadio")
    context_no_context_radio.setFont(QFont('Consolas', 9))
    context_no_context_radio.setChecked(True)
    context_last_exchange_radio = QRadioButton("Last Exchange")
    context_last_exchange_radio.setObjectName("GenRandomListLastExchangeRadio")
    context_last_exchange_radio.setFont(QFont('Consolas', 9))
    context_user_msg_radio = QRadioButton("User Message")
    context_user_msg_radio.setObjectName("GenRandomListUserMsgRadio")
    context_user_msg_radio.setFont(QFont('Consolas', 9))
    context_full_convo_radio = QRadioButton("Full Conversation")
    context_full_convo_radio.setObjectName("GenRandomListFullConvoRadio")
    context_full_convo_radio.setFont(QFont('Consolas', 9))
    context_group = QButtonGroup(widget)
    context_group.addButton(context_no_context_radio)
    context_group.addButton(context_last_exchange_radio)
    context_group.addButton(context_user_msg_radio)
    context_group.addButton(context_full_convo_radio)
    context_layout.addWidget(context_label)
    context_layout.addWidget(context_no_context_radio)
    context_layout.addWidget(context_last_exchange_radio)
    context_layout.addWidget(context_user_msg_radio)
    context_layout.addWidget(context_full_convo_radio)
    context_layout.addStretch(1)
    layout.addLayout(context_layout)
    variable_layout = QVBoxLayout()
    variable_header = QHBoxLayout()
    var_label = QLabel("Store Result in Variable (Optional):")
    var_label.setObjectName("GenRandomListVarLabel")
    var_label.setFont(QFont('Consolas', 9))
    variable_header.addWidget(var_label)
    variable_header.addStretch(1)
    var_name_layout = QHBoxLayout()
    var_name_label = QLabel("Variable Name:")
    var_name_label.setObjectName("GenRandomListVarNameLabel")
    var_name_label.setFont(QFont('Consolas', 9))
    var_name_input = QLineEdit()
    var_name_input.setObjectName("GenRandomListVarNameInput")
    var_name_input.setFont(QFont('Consolas', 9))
    var_name_input.setPlaceholderText("Enter variable name to store result (leave blank to skip)")
    var_name_layout.addWidget(var_name_label)
    var_name_layout.addWidget(var_name_input)
    scope_label = QLabel("Variable Scope:")
    scope_label.setObjectName("GenRandomListVarScopeLabel")
    scope_label.setFont(QFont('Consolas', 9))
    var_scope_global_radio = QRadioButton("Global")
    var_scope_global_radio.setObjectName("GenRandomListVarScopeGlobalRadio")
    var_scope_global_radio.setFont(QFont('Consolas', 9))
    var_scope_global_radio.setChecked(True)
    var_scope_player_radio = QRadioButton("Player")
    var_scope_player_radio.setObjectName("GenRandomListVarScopePlayerRadio")
    var_scope_player_radio.setFont(QFont('Consolas', 9))
    var_scope_character_radio = QRadioButton("Character")
    var_scope_character_radio.setObjectName("GenRandomListVarScopeCharacterRadio")
    var_scope_character_radio.setFont(QFont('Consolas', 9))
    var_scope_setting_radio = QRadioButton("Setting")
    var_scope_setting_radio.setObjectName("GenRandomListVarScopeSettingRadio")
    var_scope_setting_radio.setFont(QFont('Consolas', 9))
    var_scope_scene_chars_radio = QRadioButton("Scene Characters")
    var_scope_scene_chars_radio.setObjectName("GenRandomListVarScopeSceneCharsRadio")
    var_scope_scene_chars_radio.setFont(QFont('Consolas', 9))
    var_scope_layout = QHBoxLayout()
    var_scope_layout.addWidget(scope_label)
    var_scope_layout.addWidget(var_scope_global_radio)
    var_scope_layout.addWidget(var_scope_player_radio)
    var_scope_layout.addWidget(var_scope_character_radio)
    var_scope_layout.addWidget(var_scope_setting_radio)
    var_scope_layout.addWidget(var_scope_scene_chars_radio)
    var_scope_layout.addStretch(1)
    variable_layout.addLayout(variable_header)
    variable_layout.addLayout(var_name_layout)
    variable_layout.addLayout(var_scope_layout)
    layout.addLayout(variable_layout)
    def update_mode_ui():
        is_permutate = mode_permutate_radio.isChecked()
        permutate_options.setVisible(is_permutate)
    mode_new_radio.toggled.connect(update_mode_ui)
    mode_permutate_radio.toggled.connect(update_mode_ui)
    layout.addStretch(1)
    return widget

def create_pair_widget(tab_data):
    pair_widget = QWidget()
    pair_widget.setObjectName("PairWidget")
    pair_layout = QVBoxLayout(pair_widget)
    pair_header = QHBoxLayout()
    pair_label = QLabel(f"Pair #{len(tab_data['tag_action_pairs']) + 1}")
    pair_label.setObjectName("PairLabel")
    pair_label.setFont(QFont('Consolas', 10, QFont.Bold))
    pair_header.addWidget(pair_label)
    remove_button = QPushButton("Remove")
    remove_button.setObjectName("RemovePairButton")
    remove_button.setMaximumWidth(80)
    pair_header.addWidget(remove_button)
    pair_header.addStretch()
    pair_layout.addLayout(pair_header)
    try:
        remove_button.clicked.disconnect()
    except TypeError:
        pass
    tag_layout = QHBoxLayout()
    tag_label = QLabel("Tag:")
    tag_label.setObjectName("TagLabel")
    tag_label.setFont(QFont('Consolas', 10))
    tag_layout.addWidget(tag_label)
    tag_editor = QTextEdit()
    tag_editor.setObjectName("TagEditor")
    tag_editor.setFont(QFont('Consolas', 10))
    tag_editor.setPlaceholderText("[TAG]")
    tag_editor.setMaximumHeight(40)
    tag_layout.addWidget(tag_editor)
    pair_layout.addLayout(tag_layout)
    pair_actions_container = QWidget()
    pair_actions_container.setObjectName("PairActionsContainerWidget")
    pair_actions_layout = QVBoxLayout(pair_actions_container)
    pair_actions_layout.setContentsMargins(0, 0, 0, 0)
    pair_actions_layout.setSpacing(3)
    pair_action_rows = []

    def update_all_buttons():
        for i, r in enumerate(pair_action_rows):
            if is_valid_widget(r['add_btn']): r['add_btn'].setVisible(i == len(pair_action_rows)-1)
            if is_valid_widget(r['remove_btn']): r['remove_btn'].setVisible(len(pair_action_rows) > 1)
            if 'update_buttons' in r and callable(r['update_buttons']): r['update_buttons']()
        for i, row_data in enumerate(pair_action_rows):
            action_number_label = row_data.get('action_number_label')
            if action_number_label and is_valid_widget(action_number_label): action_number_label.setText(f"Action #{i + 1}")

    def create_pair_action_row(data=None, workflow_data_dir=None):
        row_widget = QWidget()
        main_v_layout = QVBoxLayout(row_widget)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(0)
        separator_container = QWidget()
        separator_layout = QHBoxLayout(separator_container)
        separator_layout.setContentsMargins(0, 0, 0, 0)
        separator_layout.setSpacing(5)
        action_number_label = QLabel("Action #1")
        action_number_label.setObjectName("ActionNumberLabel")
        action_number_label.setFont(QFont('Consolas', 9, QFont.Bold))
        theme_colors = tab_data.get('settings', {})
        base_color = theme_colors.get('base_color', '#00FF66')
        action_number_label.setStyleSheet(f"color: {base_color}; padding: 2px 0px;")
        separator_layout.addWidget(action_number_label)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"QFrame {{ background-color: {base_color}; border: none; }}")
        separator.setMaximumHeight(2)
        separator_layout.addWidget(separator, 1)
        main_v_layout.addWidget(separator_container)
        main_v_layout.addSpacing(3)
        top_h_layout = QHBoxLayout()
        top_h_layout.setContentsMargins(0, 0, 0, 0)
        top_h_layout.setSpacing(5)
        type_selector = QComboBox()
        type_selector.setObjectName("PairActionTypeSelector")
        type_selector.setFont(QFont('Consolas', 10))
        type_selector.addItems([
            "System Message", "Next Rule", "Switch Model", "Set Var",
            "Rewrite Post", "Generate Story", "Generate Setting",
            "Generate Character", "Generate Random List",
            "Text Tag", "New Scene", "Change Actor Location", "Force Narrator", "Set Screen Effect", "Skip Post", "Change Brightness", "Exit Rule Processing", "Game Over",
            "Post Visibility", "Add Item", "Remove Item", "Move Item", "Post Streaming"
        ])
        top_h_layout.addWidget(type_selector)
        value_editor = QTextEdit()
        value_editor.setObjectName("PairActionValueEditor")
        value_editor.setFont(QFont('Consolas', 10))
        value_editor.setMaximumHeight(40)
        value_editor.setPlaceholderText("Action value")
        top_h_layout.addWidget(value_editor)
        var_name_editor = QLineEdit()
        var_name_editor.setObjectName("PairActionVarNameEditor")
        var_name_editor.setFont(QFont('Consolas', 9))
        var_name_editor.setPlaceholderText("Var Name")
        var_name_editor.setMinimumWidth(70)
        var_value_editor = QLineEdit()
        var_value_editor.setObjectName("PairActionVarValueEditor")
        var_value_editor.setFont(QFont('Consolas', 9))
        var_value_editor.setPlaceholderText("Var Value")
        var_value_editor.setMinimumWidth(70)
        operation_selector = QComboBox()
        operation_selector.setObjectName("SetVarOperationSelector")
        operation_selector.setFont(QFont('Consolas', 8))
        operation_selector.addItems(["Set", "Increment", "Decrement", "Multiply", "Divide", "Generate", "From Random List", "From Var"])
        operation_selector.setMinimumWidth(60)
        operation_selector.setVisible(False)
        top_h_layout.addWidget(operation_selector)
        top_h_layout.addWidget(var_name_editor)
        top_h_layout.addWidget(var_value_editor)
        set_var_mode_widget = QWidget()
        set_var_mode_layout = QHBoxLayout(set_var_mode_widget)
        set_var_mode_layout.setContentsMargins(0, 0, 0, 0)
        set_var_mode_layout.setSpacing(3)
        set_var_mode_label = QLabel("Mode:")
        set_var_mode_label.setFont(QFont('Consolas', 9))
        set_var_prepend_radio = QRadioButton("Prepend")
        set_var_prepend_radio.setObjectName("SetVarPrependRadio")
        set_var_prepend_radio.setFont(QFont('Consolas', 9))
        set_var_replace_radio = QRadioButton("Replace")
        set_var_replace_radio.setObjectName("SetVarReplaceRadio")
        set_var_replace_radio.setFont(QFont('Consolas', 9))
        set_var_replace_radio.setChecked(True)
        set_var_append_radio = QRadioButton("Append")
        set_var_append_radio.setObjectName("SetVarAppendRadio")
        set_var_append_radio.setFont(QFont('Consolas', 9))
        set_var_delimiter_label = QLabel("Delimiter:")
        set_var_delimiter_label.setFont(QFont('Consolas', 9))
        set_var_delimiter_input = QLineEdit("/")
        set_var_delimiter_input.setObjectName("SetVarDelimiterInput")
        set_var_delimiter_input.setFont(QFont('Consolas', 9))
        set_var_delimiter_input.setMaximumWidth(50)
        set_var_delimiter_input.setToolTip("Optional delimiter to use when prepending or appending text")
        set_var_mode_group = QButtonGroup(set_var_mode_widget)
        set_var_mode_group.addButton(set_var_prepend_radio)
        set_var_mode_group.addButton(set_var_replace_radio)
        set_var_mode_group.addButton(set_var_append_radio)
        set_var_mode_layout.addWidget(set_var_mode_label)
        set_var_mode_layout.addWidget(set_var_prepend_radio)
        set_var_mode_layout.addWidget(set_var_replace_radio)
        set_var_mode_layout.addWidget(set_var_append_radio)
        set_var_mode_layout.addWidget(set_var_delimiter_input)
        set_var_mode_widget.setVisible(False)
        top_h_layout.addWidget(set_var_mode_widget)
        main_v_layout.addLayout(top_h_layout)
        random_list_widget = QWidget()
        random_list_widget.setObjectName("RandomListWidget")
        random_list_layout = QHBoxLayout(random_list_widget)
        random_list_layout.setContentsMargins(0, 0, 0, 0)
        random_list_layout.setSpacing(3)
        random_list_label = QLabel("Generator:")
        random_list_label.setFont(QFont('Consolas', 9))
        random_list_combo = QLineEdit()
        random_list_combo.setObjectName("VarRandomListGeneratorInput")
        random_list_combo.setFont(QFont('Consolas', 9))
        random_list_combo.setPlaceholderText("Enter generator name")
        random_list_layout.addWidget(random_list_label)
        random_list_layout.addWidget(random_list_combo)
        random_list_layout.addStretch(1)
        random_list_context_layout = QHBoxLayout()
        random_list_context_label = QLabel("Context:")
        random_list_context_label.setFont(QFont('Consolas', 9))
        random_list_no_context_radio = QRadioButton("No Context")
        random_list_no_context_radio.setObjectName("RandomListNoContextRadio")
        random_list_no_context_radio.setFont(QFont('Consolas', 9))
        random_list_no_context_radio.setChecked(True)
        random_list_last_exchange_radio = QRadioButton("Last Exchange")
        random_list_last_exchange_radio.setObjectName("RandomListLastExchangeRadio")
        random_list_last_exchange_radio.setFont(QFont('Consolas', 9))
        random_list_user_msg_radio = QRadioButton("User Message")
        random_list_user_msg_radio.setObjectName("RandomListUserMsgRadio")
        random_list_user_msg_radio.setFont(QFont('Consolas', 9))
        random_list_full_convo_radio = QRadioButton("Full Conversation")
        random_list_full_convo_radio.setObjectName("RandomListFullConvoRadio")
        random_list_full_convo_radio.setFont(QFont('Consolas', 9))
        random_list_context_group = QButtonGroup(random_list_widget)
        random_list_context_group.addButton(random_list_no_context_radio)
        random_list_context_group.addButton(random_list_last_exchange_radio)
        random_list_context_group.addButton(random_list_user_msg_radio)
        random_list_context_group.addButton(random_list_full_convo_radio)
        random_list_context_layout.addWidget(random_list_context_label)
        random_list_context_layout.addWidget(random_list_no_context_radio)
        random_list_context_layout.addWidget(random_list_last_exchange_radio)
        random_list_context_layout.addWidget(random_list_user_msg_radio)
        random_list_context_layout.addWidget(random_list_full_convo_radio)
        random_list_context_layout.addStretch(1)
        random_list_layout.addLayout(random_list_context_layout)
        random_list_widget.setVisible(False)
        from_var_widget = QWidget()
        from_var_widget.setObjectName("FromVarWidget")
        from_var_layout = QVBoxLayout(from_var_widget)
        from_var_layout.setContentsMargins(0, 0, 0, 0)
        from_var_layout.setSpacing(3)
        from_var_name_layout = QHBoxLayout()
        from_var_name_label = QLabel("Source Variable:")
        from_var_name_label.setFont(QFont('Consolas', 9))
        from_var_name_input = QLineEdit()
        from_var_name_input.setObjectName("FromVarNameInput")
        from_var_name_input.setFont(QFont('Consolas', 9))
        from_var_name_input.setPlaceholderText("Enter source variable name")
        from_var_name_layout.addWidget(from_var_name_label)
        from_var_name_layout.addWidget(from_var_name_input)
        from_var_layout.addLayout(from_var_name_layout)
        from_var_scope_layout = QHBoxLayout()
        from_var_scope_label = QLabel("Source Scope:")
        from_var_scope_label.setFont(QFont('Consolas', 9))
        from_var_scope_global_radio = QRadioButton("Global")
        from_var_scope_global_radio.setObjectName("FromVarScopeGlobalRadio")
        from_var_scope_global_radio.setFont(QFont('Consolas', 9))
        from_var_scope_global_radio.setChecked(True)
        from_var_scope_player_radio = QRadioButton("Player")
        from_var_scope_player_radio.setObjectName("FromVarScopePlayerRadio")
        from_var_scope_player_radio.setFont(QFont('Consolas', 9))
        from_var_scope_character_radio = QRadioButton("Character")
        from_var_scope_character_radio.setObjectName("FromVarScopeCharacterRadio")
        from_var_scope_character_radio.setFont(QFont('Consolas', 9))
        from_var_scope_scene_chars_radio = QRadioButton("Scene Characters")
        from_var_scope_scene_chars_radio.setObjectName("FromVarScopeSceneCharsRadio")
        from_var_scope_scene_chars_radio.setFont(QFont('Consolas', 9))
        from_var_scope_setting_radio = QRadioButton("Setting")
        from_var_scope_setting_radio.setObjectName("FromVarScopeSettingRadio")
        from_var_scope_setting_radio.setFont(QFont('Consolas', 9))
        from_var_scope_group = QButtonGroup(from_var_widget)
        from_var_scope_group.addButton(from_var_scope_global_radio)
        from_var_scope_group.addButton(from_var_scope_player_radio)
        from_var_scope_group.addButton(from_var_scope_character_radio)
        from_var_scope_group.addButton(from_var_scope_scene_chars_radio)
        from_var_scope_group.addButton(from_var_scope_setting_radio)
        from_var_scope_layout.addWidget(from_var_scope_label)
        from_var_scope_layout.addWidget(from_var_scope_global_radio)
        from_var_scope_layout.addWidget(from_var_scope_player_radio)
        from_var_scope_layout.addWidget(from_var_scope_character_radio)
        from_var_scope_layout.addWidget(from_var_scope_scene_chars_radio)
        from_var_scope_layout.addWidget(from_var_scope_setting_radio)
        from_var_scope_layout.addStretch(1)
        from_var_layout.addLayout(from_var_scope_layout)
        from_var_widget.setVisible(False)
        main_v_layout.addWidget(random_list_widget)
        main_v_layout.addWidget(from_var_widget)
        row_widget.setLayout(main_v_layout)
        action_var_scope_widget = QWidget()
        action_var_scope_layout = QHBoxLayout(action_var_scope_widget)
        action_var_scope_layout.setContentsMargins(5, 0, 0, 0)
        action_var_scope_layout.setSpacing(3)
        action_scope_label = QLabel("Scope:")
        action_scope_label.setObjectName("ActionScopeLabel")
        action_scope_label.setFont(QFont('Consolas', 9))
        action_scope_global_radio = QRadioButton("Global")
        action_scope_global_radio.setObjectName("ActionVarScopeGlobalRadio")
        action_scope_global_radio.setFont(QFont('Consolas', 9))
        action_scope_global_radio.setChecked(True)
        action_scope_player_radio = QRadioButton("Player")
        action_scope_player_radio.setObjectName("ActionVarScopePlayerRadio")
        action_scope_player_radio.setFont(QFont('Consolas', 9))
        action_scope_character_radio = QRadioButton("Character")
        action_scope_character_radio.setObjectName("ActionVarScopeCharacterRadio")
        action_scope_character_radio.setFont(QFont('Consolas', 9))
        action_scope_scene_chars_radio = QRadioButton("Scene Characters")
        action_scope_scene_chars_radio.setObjectName("ActionVarScopeSceneCharsRadio")
        action_scope_scene_chars_radio.setFont(QFont('Consolas', 9))
        action_scope_setting_radio = QRadioButton("Setting")
        action_scope_setting_radio.setObjectName("ActionVarScopeSettingRadio")
        action_scope_setting_radio.setFont(QFont('Consolas', 9))
        action_var_scope_group = QButtonGroup(action_var_scope_widget)
        action_var_scope_group.addButton(action_scope_global_radio)
        action_var_scope_group.addButton(action_scope_player_radio)
        action_var_scope_group.addButton(action_scope_character_radio)
        action_var_scope_group.addButton(action_scope_scene_chars_radio)
        action_var_scope_group.addButton(action_scope_setting_radio)
        action_var_scope_layout.addWidget(action_scope_label)
        action_var_scope_layout.addWidget(action_scope_global_radio)
        action_var_scope_layout.addWidget(action_scope_player_radio)
        action_var_scope_layout.addWidget(action_scope_character_radio)
        action_var_scope_layout.addWidget(action_scope_scene_chars_radio)
        action_var_scope_layout.addWidget(action_scope_setting_radio)
        action_var_scope_layout.addStretch()
        action_var_scope_widget.setVisible(False)
        main_v_layout.addWidget(action_var_scope_widget)
        switch_model_widget = QWidget()
        switch_model_layout = QHBoxLayout(switch_model_widget)
        switch_model_layout.setContentsMargins(5, 0, 0, 0)
        switch_model_layout.setSpacing(5)
        temp_label = QLabel("Temperature:")
        temp_label.setFont(QFont('Consolas', 9))
        temp_editor = QLineEdit()
        temp_editor.setObjectName("SwitchModelTempEditor")
        temp_editor.setFont(QFont('Consolas', 9))
        temp_editor.setPlaceholderText("0.7")
        temp_editor.setMaximumWidth(60)
        switch_model_layout.addWidget(temp_label)
        switch_model_layout.addWidget(temp_editor)
        switch_model_layout.addStretch()
        switch_model_widget.setVisible(False)
        top_h_layout.addWidget(switch_model_widget)
        text_tag_mode_widget = QWidget()
        text_tag_mode_layout = QHBoxLayout(text_tag_mode_widget)
        text_tag_mode_layout.setContentsMargins(0, 0, 0, 0)
        text_tag_mode_label = QLabel("Tag Mode:")
        text_tag_mode_label.setFont(QFont('Consolas', 9))
        tag_overwrite_radio = QRadioButton("Overwrite")
        tag_overwrite_radio.setObjectName("TagOverwriteRadio")
        tag_overwrite_radio.setFont(QFont('Consolas', 9))
        tag_overwrite_radio.setChecked(True)
        tag_append_radio = QRadioButton("Append")
        tag_append_radio.setObjectName("TagAppendRadio")
        tag_append_radio.setFont(QFont('Consolas', 9))
        tag_prepend_radio = QRadioButton("Prepend")
        tag_prepend_radio.setObjectName("TagPrependRadio")
        tag_prepend_radio.setFont(QFont('Consolas', 9))
        tag_mode_group = QButtonGroup(text_tag_mode_widget)
        tag_mode_group.addButton(tag_overwrite_radio)
        tag_mode_group.addButton(tag_append_radio)
        tag_mode_group.addButton(tag_prepend_radio)
        text_tag_mode_layout.addWidget(text_tag_mode_label)
        text_tag_mode_layout.addWidget(tag_overwrite_radio)
        text_tag_mode_layout.addWidget(tag_append_radio)
        text_tag_mode_layout.addWidget(tag_prepend_radio)
        text_tag_mode_layout.addStretch()
        text_tag_mode_widget.setVisible(False)
        top_h_layout.addWidget(text_tag_mode_widget)
        brightness_widget = QWidget()
        brightness_widget.setObjectName("BrightnessWidget")
        brightness_layout = QHBoxLayout(brightness_widget)
        brightness_layout.setContentsMargins(0, 0, 0, 0)
        brightness_layout.setSpacing(3)
        brightness_label = QLabel("Brightness:")
        brightness_label.setFont(QFont('Consolas', 9))
        brightness_input = QLineEdit()
        brightness_input.setObjectName("BrightnessInput")
        brightness_input.setFont(QFont('Consolas', 9))
        brightness_input.setPlaceholderText("0.0-2.0 (1.0=normal)")
        brightness_input.setMaximumWidth(120)
        brightness_input.setToolTip("Brightness factor: 0.0=black, 1.0=normal, 2.0=very bright")
        brightness_layout.addWidget(brightness_label)
        brightness_layout.addWidget(brightness_input)
        brightness_layout.addStretch()
        brightness_widget.setVisible(False)
        top_h_layout.addWidget(brightness_widget)
        post_visibility_widget = QWidget()
        post_visibility_widget.setObjectName("PostVisibilityWidget")
        post_visibility_layout = QVBoxLayout(post_visibility_widget)
        post_visibility_layout.setContentsMargins(0, 0, 0, 0)
        post_visibility_layout.setSpacing(3)
        
        applies_to_layout = QHBoxLayout()
        applies_to_label = QLabel("Applies to:")
        applies_to_label.setFont(QFont('Consolas', 9))
        current_post_radio = QRadioButton("Current Post")
        current_post_radio.setObjectName("PostVisibilityCurrentPostRadio")
        current_post_radio.setFont(QFont('Consolas', 9))
        current_post_radio.setChecked(True)
        player_post_radio = QRadioButton("Player Post")
        player_post_radio.setObjectName("PostVisibilityPlayerPostRadio")
        player_post_radio.setFont(QFont('Consolas', 9))
        applies_to_group = QButtonGroup(post_visibility_widget)
        applies_to_group.addButton(current_post_radio)
        applies_to_group.addButton(player_post_radio)
        applies_to_layout.addWidget(applies_to_label)
        applies_to_layout.addWidget(current_post_radio)
        applies_to_layout.addWidget(player_post_radio)
        applies_to_layout.addStretch()
        post_visibility_layout.addLayout(applies_to_layout)
        
        visibility_mode_layout = QHBoxLayout()
        visibility_mode_label = QLabel("Mode:")
        visibility_mode_label.setFont(QFont('Consolas', 9))
        visible_only_radio = QRadioButton("Visible Only To:")
        visible_only_radio.setObjectName("PostVisibilityVisibleOnlyRadio")
        visible_only_radio.setFont(QFont('Consolas', 9))
        visible_only_radio.setChecked(True)
        not_visible_radio = QRadioButton("Not Visible To:")
        not_visible_radio.setObjectName("PostVisibilityNotVisibleRadio")
        not_visible_radio.setFont(QFont('Consolas', 9))
        visibility_mode_group = QButtonGroup(post_visibility_widget)
        visibility_mode_group.addButton(visible_only_radio)
        visibility_mode_group.addButton(not_visible_radio)
        visibility_mode_layout.addWidget(visibility_mode_label)
        visibility_mode_layout.addWidget(visible_only_radio)
        visibility_mode_layout.addWidget(not_visible_radio)
        visibility_mode_layout.addStretch()
        post_visibility_layout.addLayout(visibility_mode_layout)
        
        condition_type_layout = QHBoxLayout()
        condition_type_label = QLabel("Condition Type:")
        condition_type_label.setFont(QFont('Consolas', 9))
        name_match_radio = QRadioButton("Name Match")
        name_match_radio.setObjectName("PostVisibilityNameMatchRadio")
        name_match_radio.setFont(QFont('Consolas', 9))
        name_match_radio.setChecked(True)
        variable_radio = QRadioButton("Variable")
        variable_radio.setObjectName("PostVisibilityVariableRadio")
        variable_radio.setFont(QFont('Consolas', 9))
        condition_type_group = QButtonGroup(post_visibility_widget)
        condition_type_group.addButton(name_match_radio)
        condition_type_group.addButton(variable_radio)
        condition_type_layout.addWidget(condition_type_label)
        condition_type_layout.addWidget(name_match_radio)
        condition_type_layout.addWidget(variable_radio)
        condition_type_layout.addStretch()
        post_visibility_layout.addLayout(condition_type_layout)
        
        conditions_container = QWidget()
        conditions_container.setObjectName("PostVisibilityConditionsContainer")
        conditions_layout = QVBoxLayout(conditions_container)
        conditions_layout.setContentsMargins(0, 0, 0, 0)
        conditions_layout.setSpacing(3)
        
        conditions_header = QHBoxLayout()
        conditions_label = QLabel("Conditions:")
        conditions_label.setFont(QFont('Consolas', 9, QFont.Bold))
        conditions_header.addWidget(conditions_label)
        add_condition_btn = QPushButton("+")
        add_condition_btn.setObjectName("PostVisibilityAddConditionButton")
        add_condition_btn.setMaximumWidth(30)
        add_condition_btn.setMaximumHeight(25)
        add_condition_btn.setFont(QFont('Consolas', 9))
        conditions_header.addWidget(add_condition_btn)
        conditions_header.addStretch()
        conditions_layout.addLayout(conditions_header)
        
        post_visibility_layout.addWidget(conditions_container)
        post_visibility_widget.setVisible(False)
        top_h_layout.addWidget(post_visibility_widget)
        game_over_widget = QWidget()
        game_over_widget.setObjectName("GameOverWidget")
        game_over_layout = QVBoxLayout(game_over_widget)
        game_over_layout.setContentsMargins(0, 0, 0, 0)
        game_over_layout.setSpacing(3)
        
        game_over_message_label = QLabel("Game Over Message:")
        game_over_message_label.setFont(QFont('Consolas', 9))
        game_over_layout.addWidget(game_over_message_label)
        
        game_over_message_input = QTextEdit()
        game_over_message_input.setObjectName("GameOverMessageInput")
        game_over_message_input.setFont(QFont('Consolas', 10))
        game_over_message_input.setMaximumHeight(80)
        game_over_message_input.setPlaceholderText("Enter the message the player will see when the game ends...")
        game_over_layout.addWidget(game_over_message_input)
        
        game_over_widget.setVisible(False)
        top_h_layout.addWidget(game_over_widget)
        
        add_item_widget = QWidget()
        add_item_widget.setObjectName("AddItemWidget")
        add_item_layout = QVBoxLayout(add_item_widget)
        add_item_layout.setContentsMargins(0, 0, 0, 0)
        add_item_layout.setSpacing(3)
        
        item_details_layout = QHBoxLayout()
        item_name_label = QLabel("Item Name:")
        item_name_label.setFont(QFont('Consolas', 9))
        item_name_input = QLineEdit()
        item_name_input.setObjectName("AddItemNameInput")
        item_name_input.setFont(QFont('Consolas', 9))
        item_name_input.setPlaceholderText("Enter item name")
        item_name_input.setMinimumWidth(150)
        
        quantity_label = QLabel("Quantity:")
        quantity_label.setFont(QFont('Consolas', 9))
        quantity_input = QLineEdit()
        quantity_input.setObjectName("AddItemQuantityInput")
        quantity_input.setFont(QFont('Consolas', 9))
        quantity_input.setPlaceholderText("1")
        quantity_input.setMaximumWidth(80)
        
        generate_checkbox = QCheckBox("Generate")
        generate_checkbox.setObjectName("AddItemGenerateCheckbox")
        generate_checkbox.setFont(QFont('Consolas', 9))
        generate_checkbox.setToolTip("Generate the item dynamically")
        
        item_details_layout.addWidget(item_name_label)
        item_details_layout.addWidget(item_name_input)
        item_details_layout.addWidget(quantity_label)
        item_details_layout.addWidget(quantity_input)
        item_details_layout.addWidget(generate_checkbox)
        item_details_layout.addStretch()
        add_item_layout.addLayout(item_details_layout)
        
        target_layout = QHBoxLayout()
        target_label = QLabel("Target:")
        target_label.setFont(QFont('Consolas', 9))
        target_setting_radio = QRadioButton("Setting")
        target_setting_radio.setObjectName("AddItemTargetSettingRadio")
        target_setting_radio.setFont(QFont('Consolas', 9))
        target_setting_radio.setChecked(True)
        target_character_radio = QRadioButton("Character")
        target_character_radio.setObjectName("AddItemTargetCharacterRadio")
        target_character_radio.setFont(QFont('Consolas', 9))
        target_group = QButtonGroup(add_item_widget)
        target_group.addButton(target_setting_radio)
        target_group.addButton(target_character_radio)
        
        target_name_label = QLabel("Target Name:")
        target_name_label.setFont(QFont('Consolas', 9))
        target_name_input = QLineEdit()
        target_name_input.setObjectName("AddItemTargetNameInput")
        target_name_input.setFont(QFont('Consolas', 9))
        target_name_input.setPlaceholderText("Leave blank for current")
        target_name_input.setMinimumWidth(150)
        
        target_layout.addWidget(target_label)
        target_layout.addWidget(target_setting_radio)
        target_layout.addWidget(target_character_radio)
        target_layout.addWidget(target_name_label)
        target_layout.addWidget(target_name_input)
        target_layout.addStretch()
        add_item_layout.addLayout(target_layout)
        
        add_item_widget.setVisible(False)
        top_h_layout.addWidget(add_item_widget)
        
        remove_item_widget = QWidget()
        remove_item_widget.setObjectName("RemoveItemWidget")
        remove_item_layout = QVBoxLayout(remove_item_widget)
        remove_item_layout.setContentsMargins(0, 0, 0, 0)
        remove_item_layout.setSpacing(3)
        
        remove_item_details_layout = QHBoxLayout()
        remove_item_name_label = QLabel("Item Name:")
        remove_item_name_label.setFont(QFont('Consolas', 9))
        remove_item_name_input = QLineEdit()
        remove_item_name_input.setObjectName("RemoveItemNameInput")
        remove_item_name_input.setFont(QFont('Consolas', 9))
        remove_item_name_input.setPlaceholderText("Enter item name")
        remove_item_name_input.setMinimumWidth(150)
        
        remove_quantity_label = QLabel("Quantity:")
        remove_quantity_label.setFont(QFont('Consolas', 9))
        remove_quantity_input = QLineEdit()
        remove_quantity_input.setObjectName("RemoveItemQuantityInput")
        remove_quantity_input.setFont(QFont('Consolas', 9))
        remove_quantity_input.setPlaceholderText("1")
        remove_quantity_input.setMaximumWidth(80)
        
        remove_item_details_layout.addWidget(remove_item_name_label)
        remove_item_details_layout.addWidget(remove_item_name_input)
        remove_item_details_layout.addWidget(remove_quantity_label)
        remove_item_details_layout.addWidget(remove_quantity_input)
        remove_item_details_layout.addStretch()
        remove_item_layout.addLayout(remove_item_details_layout)
        
        remove_target_layout = QHBoxLayout()
        remove_target_label = QLabel("Target:")
        remove_target_label.setFont(QFont('Consolas', 9))
        remove_target_setting_radio = QRadioButton("Setting")
        remove_target_setting_radio.setObjectName("RemoveItemTargetSettingRadio")
        remove_target_setting_radio.setFont(QFont('Consolas', 9))
        remove_target_setting_radio.setChecked(True)
        remove_target_character_radio = QRadioButton("Character")
        remove_target_character_radio.setObjectName("RemoveItemTargetCharacterRadio")
        remove_target_character_radio.setFont(QFont('Consolas', 9))
        remove_target_group = QButtonGroup(remove_item_widget)
        remove_target_group.addButton(remove_target_setting_radio)
        remove_target_group.addButton(remove_target_character_radio)
        
        remove_target_name_label = QLabel("Target Name:")
        remove_target_name_label.setFont(QFont('Consolas', 9))
        remove_target_name_input = QLineEdit()
        remove_target_name_input.setObjectName("RemoveItemTargetNameInput")
        remove_target_name_input.setFont(QFont('Consolas', 9))
        remove_target_name_input.setPlaceholderText("Leave blank for current")
        remove_target_name_input.setMinimumWidth(150)
        
        remove_target_layout.addWidget(remove_target_label)
        remove_target_layout.addWidget(remove_target_setting_radio)
        remove_target_layout.addWidget(remove_target_character_radio)
        remove_target_layout.addWidget(remove_target_name_label)
        remove_target_layout.addWidget(remove_target_name_input)
        remove_target_layout.addStretch()
        remove_item_layout.addLayout(remove_target_layout)
        
        remove_item_widget.setVisible(False)
        top_h_layout.addWidget(remove_item_widget)
        
        move_item_widget = QWidget()
        move_item_widget.setObjectName("MoveItemWidget")
        move_item_layout = QVBoxLayout(move_item_widget)
        move_item_layout.setContentsMargins(0, 0, 0, 0)
        move_item_layout.setSpacing(3)
        
        move_item_details_layout = QHBoxLayout()
        move_item_name_label = QLabel("Item Name:")
        move_item_name_label.setFont(QFont('Consolas', 9))
        move_item_name_input = QLineEdit()
        move_item_name_input.setObjectName("MoveItemNameInput")
        move_item_name_input.setFont(QFont('Consolas', 9))
        move_item_name_input.setPlaceholderText("Enter item name")
        move_item_name_input.setMinimumWidth(150)
        
        move_quantity_label = QLabel("Quantity:")
        move_quantity_label.setFont(QFont('Consolas', 9))
        move_quantity_input = QLineEdit()
        move_quantity_input.setObjectName("MoveItemQuantityInput")
        move_quantity_input.setFont(QFont('Consolas', 9))
        move_quantity_input.setPlaceholderText("1")
        move_quantity_input.setMaximumWidth(80)
        
        move_item_details_layout.addWidget(move_item_name_label)
        move_item_details_layout.addWidget(move_item_name_input)
        move_item_details_layout.addWidget(move_quantity_label)
        move_item_details_layout.addWidget(move_quantity_input)
        move_item_details_layout.addStretch()
        move_item_layout.addLayout(move_item_details_layout)
        
        move_from_layout = QHBoxLayout()
        move_from_label = QLabel("From:")
        move_from_label.setFont(QFont('Consolas', 9))
        move_from_setting_radio = QRadioButton("Setting")
        move_from_setting_radio.setObjectName("MoveItemFromSettingRadio")
        move_from_setting_radio.setFont(QFont('Consolas', 9))
        move_from_setting_radio.setChecked(True)
        move_from_character_radio = QRadioButton("Character")
        move_from_character_radio.setObjectName("MoveItemFromCharacterRadio")
        move_from_character_radio.setFont(QFont('Consolas', 9))
        move_from_group = QButtonGroup(move_item_widget)
        move_from_group.addButton(move_from_setting_radio)
        move_from_group.addButton(move_from_character_radio)
        
        move_from_name_label = QLabel("From Name:")
        move_from_name_label.setFont(QFont('Consolas', 9))
        move_from_name_input = QLineEdit()
        move_from_name_input.setObjectName("MoveItemFromNameInput")
        move_from_name_input.setFont(QFont('Consolas', 9))
        move_from_name_input.setPlaceholderText("Leave blank for current")
        move_from_name_input.setMinimumWidth(150)
        
        move_from_layout.addWidget(move_from_label)
        move_from_layout.addWidget(move_from_setting_radio)
        move_from_layout.addWidget(move_from_character_radio)
        move_from_layout.addWidget(move_from_name_label)
        move_from_layout.addWidget(move_from_name_input)
        move_from_layout.addStretch()
        move_item_layout.addLayout(move_from_layout)
        
        move_to_layout = QHBoxLayout()
        move_to_label = QLabel("To:")
        move_to_label.setFont(QFont('Consolas', 9))
        move_to_setting_radio = QRadioButton("Setting")
        move_to_setting_radio.setObjectName("MoveItemToSettingRadio")
        move_to_setting_radio.setFont(QFont('Consolas', 9))
        move_to_setting_radio.setChecked(True)
        move_to_character_radio = QRadioButton("Character")
        move_to_character_radio.setObjectName("MoveItemToCharacterRadio")
        move_to_character_radio.setFont(QFont('Consolas', 9))
        move_to_group = QButtonGroup(move_item_widget)
        move_to_group.addButton(move_to_setting_radio)
        move_to_group.addButton(move_to_character_radio)
        
        move_to_name_label = QLabel("To Name:")
        move_to_name_label.setFont(QFont('Consolas', 9))
        move_to_name_input = QLineEdit()
        move_to_name_input.setObjectName("MoveItemToNameInput")
        move_to_name_input.setFont(QFont('Consolas', 9))
        move_to_name_input.setPlaceholderText("Leave blank for current")
        move_to_name_input.setMinimumWidth(150)
        
        move_to_layout.addWidget(move_to_label)
        move_to_layout.addWidget(move_to_setting_radio)
        move_to_layout.addWidget(move_to_character_radio)
        move_to_layout.addWidget(move_to_name_label)
        move_to_layout.addWidget(move_to_name_input)
        move_to_layout.addStretch()
        move_item_layout.addLayout(move_to_layout)
        
        move_item_widget.setVisible(False)
        top_h_layout.addWidget(move_item_widget)
        position_container = QWidget()
        position_container.setObjectName("ActionPositionContainer")
        position_layout = QVBoxLayout(position_container)
        position_layout.setContentsMargins(2, 0, 2, 0)
        position_layout.setSpacing(2)
        add_to_widget = QWidget()
        add_to_layout = QHBoxLayout(add_to_widget)
        add_to_layout.setContentsMargins(0, 0, 0, 0)
        add_to_layout.setSpacing(3)
        add_to_label = QLabel("Add to:")
        add_to_label.setObjectName("ActionPositionLabel")
        add_to_label.setFont(QFont('Consolas', 9))
        add_to_layout.addWidget(add_to_label)
        add_to_group = QButtonGroup(add_to_widget)
        prepend_radio = QRadioButton("Prepend")
        prepend_radio.setObjectName("ActionPrependRadio")
        prepend_radio.setChecked(True)
        append_radio = QRadioButton("Append")
        append_radio.setObjectName("ActionAppendRadio")
        append_radio.setFont(QFont('Consolas', 9))
        replace_radio = QRadioButton("Replace")
        replace_radio.setObjectName("ActionReplaceRadio")
        replace_radio.setFont(QFont('Consolas', 9))
        add_to_group.addButton(prepend_radio)
        add_to_group.addButton(append_radio)
        add_to_group.addButton(replace_radio)
        add_to_layout.addWidget(prepend_radio)
        add_to_layout.addWidget(append_radio)
        add_to_layout.addWidget(replace_radio)
        position_layout.addWidget(add_to_widget)
        sys_pos_widget = QWidget()
        sys_pos_layout = QHBoxLayout(sys_pos_widget)
        sys_pos_layout.setContentsMargins(0, 0, 0, 0)
        sys_pos_layout.setSpacing(3)
        sys_pos_label = QLabel("Sys Msg Pos:")
        sys_pos_label.setObjectName("ActionSysMsgPosLabel")
        sys_pos_label.setFont(QFont('Consolas', 9))
        sys_pos_group = QButtonGroup(sys_pos_widget)
        first_radio = QRadioButton("First")
        first_radio.setObjectName("ActionFirstSysMsgRadio")
        first_radio.setFont(QFont('Consolas', 9))
        first_radio.setChecked(True)
        last_radio = QRadioButton("Last")
        last_radio.setObjectName("ActionLastSysMsgRadio")
        last_radio.setFont(QFont('Consolas', 9))
        sys_pos_group.addButton(first_radio)
        sys_pos_group.addButton(last_radio)
        sys_pos_layout.addWidget(first_radio)
        sys_pos_layout.addWidget(last_radio)
        position_layout.addWidget(add_to_widget)
        position_layout.addWidget(sys_pos_widget)
        top_h_layout.addWidget(position_container)
        position_container.setVisible(False)
        change_location_widget = QWidget()
        change_location_layout = QVBoxLayout(change_location_widget)
        change_location_layout.setContentsMargins(2, 0, 2, 0)
        change_location_layout.setSpacing(3)
        actor_select_layout = QHBoxLayout()
        actor_label = QLabel("Actor:")
        actor_label.setFont(QFont('Consolas', 9))
        actor_input = QLineEdit()
        actor_input.setObjectName("ChangeLocationActorInput")
        actor_input.setFont(QFont('Consolas', 9))
        actor_input.setMinimumWidth(120)
        actor_select_layout.addWidget(actor_label)
        actor_select_layout.addWidget(actor_input, 1)
        change_location_layout.addLayout(actor_select_layout)
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setFont(QFont('Consolas', 9))
        mode_adjacent_radio = QRadioButton("Determine (Adjacent)")
        mode_adjacent_radio.setObjectName("ChangeLocationAdjacentRadio")
        mode_adjacent_radio.setFont(QFont('Consolas', 9))
        mode_fast_travel_radio = QRadioButton("Determine (Fast Travel)")
        mode_fast_travel_radio.setObjectName("ChangeLocationFastTravelRadio")
        mode_fast_travel_radio.setFont(QFont('Consolas', 9))
        mode_setting_radio = QRadioButton("Setting")
        mode_setting_radio.setObjectName("ChangeLocationSettingRadio")
        mode_setting_radio.setFont(QFont('Consolas', 9))
        mode_setting_radio.setChecked(True)
        location_mode_group = QButtonGroup(change_location_widget)
        location_mode_group.addButton(mode_adjacent_radio)
        location_mode_group.addButton(mode_fast_travel_radio)
        location_mode_group.addButton(mode_setting_radio)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(mode_adjacent_radio)
        mode_layout.addWidget(mode_fast_travel_radio)
        mode_layout.addWidget(mode_setting_radio)
        mode_layout.addStretch()
        change_location_layout.addLayout(mode_layout)
        target_setting_layout = QHBoxLayout()
        target_setting_label = QLabel("Target Setting:")
        target_setting_label.setFont(QFont('Consolas', 9))
        target_setting_input = QLineEdit()
        target_setting_input.setObjectName("ChangeLocationTargetSettingInput")
        target_setting_input.setFont(QFont('Consolas', 9))
        target_setting_input.setMinimumWidth(150)
        target_setting_layout.addWidget(target_setting_label)
        target_setting_layout.addWidget(target_setting_input, 1)
        change_location_layout.addLayout(target_setting_layout)

        time_advancement_layout = QHBoxLayout()
        advance_time_checkbox = QCheckBox("Advance time based on travel distance")
        advance_time_checkbox.setObjectName("ChangeLocationAdvanceTimeCheckbox")
        advance_time_checkbox.setFont(QFont('Consolas', 9))
        advance_time_checkbox.setChecked(True)
        advance_time_checkbox.setToolTip("When enabled, game time will advance based on the path length and map scale settings")
        time_advancement_layout.addWidget(advance_time_checkbox)
        time_advancement_layout.addStretch()
        change_location_layout.addLayout(time_advancement_layout)
        
        change_location_widget.setVisible(False)
        top_h_layout.addWidget(change_location_widget)
        generate_setting_widget = create_generate_setting_widget(parent=row_widget)
        generate_setting_widget.setVisible(False)
        top_h_layout.addWidget(generate_setting_widget)
        generate_character_widget = QWidget(row_widget)
        generate_character_layout = QVBoxLayout(generate_character_widget)
        generate_character_layout.setContentsMargins(0, 0, 0, 0)
        generate_character_layout.setSpacing(3)
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setFont(QFont('Consolas', 9))
        create_new_radio = QRadioButton("Create New")
        create_new_radio.setObjectName("GenerateCharacterCreateNewRadio")
        create_new_radio.setFont(QFont('Consolas', 9))
        create_new_radio.setChecked(True)
        edit_existing_radio = QRadioButton("Edit Existing")
        edit_existing_radio.setObjectName("GenerateCharacterEditExistingRadio")
        edit_existing_radio.setFont(QFont('Consolas', 9))
        mode_group = QButtonGroup(generate_character_widget)
        mode_group.addButton(create_new_radio)
        mode_group.addButton(edit_existing_radio)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(create_new_radio)
        mode_layout.addWidget(edit_existing_radio)
        mode_layout.addStretch()
        generate_character_layout.addLayout(mode_layout)
        directory_layout = QHBoxLayout()
        directory_label = QLabel("Save To:")
        directory_label.setFont(QFont('Consolas', 9))
        game_dir_radio = QRadioButton("Game")
        game_dir_radio.setObjectName("GenerateCharacterGameDirRadio")
        game_dir_radio.setFont(QFont('Consolas', 9))
        game_dir_radio.setChecked(True)
        game_dir_radio.setToolTip("Save to /game/actors/ (session-specific)")
        resources_dir_radio = QRadioButton("Resources")
        resources_dir_radio.setObjectName("GenerateCharacterResourcesDirRadio")
        resources_dir_radio.setFont(QFont('Consolas', 9))
        resources_dir_radio.setToolTip("Save to /resources/data files/actors/ (available to all sessions)")
        directory_group = QButtonGroup(generate_character_widget)
        directory_group.addButton(game_dir_radio)
        directory_group.addButton(resources_dir_radio)
        directory_layout.addWidget(directory_label)
        directory_layout.addWidget(game_dir_radio)
        directory_layout.addWidget(resources_dir_radio)
        directory_layout.addStretch()
        generate_character_layout.addLayout(directory_layout)
        target_actor_layout = QHBoxLayout()
        target_actor_label = QLabel("Target Actor:")
        target_actor_label.setFont(QFont('Consolas', 9))
        target_actor_editor = QLineEdit()
        target_actor_editor.setObjectName("GenerateCharacterTargetActorEditor")
        target_actor_editor.setFont(QFont('Consolas', 10))
        target_actor_editor.setPlaceholderText("Name of actor to edit (for Edit Existing mode)")
        target_actor_editor.setEnabled(False)
        target_actor_layout.addWidget(target_actor_label)
        target_actor_layout.addWidget(target_actor_editor, 1)
        generate_character_layout.addLayout(target_actor_layout)
        fields_label = QLabel("Fields to Generate:")
        fields_label.setFont(QFont('Consolas', 9))
        generate_character_layout.addWidget(fields_label)
        fields_container = QWidget()
        fields_layout = QVBoxLayout(fields_container)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        fields_layout.setSpacing(2)
        fields_row1 = QHBoxLayout()
        name_checkbox = QCheckBox("Name")
        name_checkbox.setObjectName("GenerateCharacterNameCheckbox")
        name_checkbox.setFont(QFont('Consolas', 9))
        description_checkbox = QCheckBox("Description")
        description_checkbox.setObjectName("GenerateCharacterDescriptionCheckbox")
        description_checkbox.setFont(QFont('Consolas', 9))
        personality_checkbox = QCheckBox("Personality")
        personality_checkbox.setObjectName("GenerateCharacterPersonalityCheckbox")
        personality_checkbox.setFont(QFont('Consolas', 9))
        appearance_checkbox = QCheckBox("Appearance")
        appearance_checkbox.setObjectName("GenerateCharacterAppearanceCheckbox")
        appearance_checkbox.setFont(QFont('Consolas', 9))
        fields_row1.addWidget(name_checkbox)
        fields_row1.addWidget(description_checkbox)
        fields_row1.addWidget(personality_checkbox)
        fields_row1.addWidget(appearance_checkbox)
        fields_layout.addLayout(fields_row1)
        
        fields_row2 = QHBoxLayout()
        goals_checkbox = QCheckBox("Goals")
        goals_checkbox.setObjectName("GenerateCharacterGoalsCheckbox")
        goals_checkbox.setFont(QFont('Consolas', 9))
        story_checkbox = QCheckBox("Story")
        story_checkbox.setObjectName("GenerateCharacterStoryCheckbox")
        story_checkbox.setFont(QFont('Consolas', 9))
        abilities_checkbox = QCheckBox("Abilities")
        abilities_checkbox.setObjectName("GenerateCharacterAbilitiesCheckbox")
        abilities_checkbox.setFont(QFont('Consolas', 9))
        equipment_checkbox = QCheckBox("Equipment")
        equipment_checkbox.setObjectName("GenerateCharacterEquipmentCheckbox")
        equipment_checkbox.setFont(QFont('Consolas', 9))
        fields_row2.addWidget(goals_checkbox)
        fields_row2.addWidget(story_checkbox)
        fields_row2.addWidget(abilities_checkbox)
        fields_row2.addWidget(equipment_checkbox)
        fields_layout.addLayout(fields_row2)
        select_buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.setObjectName("GenerateCharacterSelectAllBtn")
        select_all_btn.setFont(QFont('Consolas', 8))
        select_all_btn.setMaximumHeight(20)
        select_none_btn = QPushButton("Select None")
        select_none_btn.setObjectName("GenerateCharacterSelectNoneBtn")
        select_none_btn.setFont(QFont('Consolas', 8))
        select_none_btn.setMaximumHeight(20)
        select_buttons_layout.addWidget(select_all_btn)
        select_buttons_layout.addWidget(select_none_btn)
        select_buttons_layout.addStretch()
        fields_layout.addLayout(select_buttons_layout)
        
        generate_character_layout.addWidget(fields_container)
        instructions_label = QLabel("Instructions:")
        instructions_label.setFont(QFont('Consolas', 9))
        instructions_editor = QTextEdit()
        instructions_editor.setObjectName("GenerateCharacterInstructionsEditor")
        instructions_editor.setFont(QFont('Consolas', 10))
        instructions_editor.setMaximumHeight(40)
        instructions_editor.setPlaceholderText("Describe the character to generate...")
        generate_character_layout.addWidget(instructions_label)
        generate_character_layout.addWidget(instructions_editor)
        options_layout = QHBoxLayout()
        attach_context_checkbox = QCheckBox("Attach Context")
        attach_context_checkbox.setObjectName("GenerateCharacterAttachContextCheckbox")
        attach_context_checkbox.setToolTip("If checked, the current conversation context will be prepended to the NPC generation instructions.")
        attach_context_checkbox.setFont(QFont('Consolas', 9))
        options_layout.addWidget(attach_context_checkbox)
        model_label = QLabel("Model:")
        model_label.setFont(QFont('Consolas', 9))
        model_editor = QLineEdit()
        model_editor.setObjectName("GenerateCharacterModelEditor")
        model_editor.setFont(QFont('Consolas', 10))
        model_editor.setPlaceholderText("Optional model override")
        model_editor.setMaximumWidth(200)
        options_layout.addWidget(model_label)
        options_layout.addWidget(model_editor)
        options_layout.addStretch()
        generate_character_layout.addLayout(options_layout)
        location_layout = QHBoxLayout()
        location_label = QLabel("Location:")
        location_label.setFont(QFont('Consolas', 9))
        location_editor = QLineEdit()
        location_editor.setObjectName("GenerateCharacterLocationEditor")
        location_editor.setFont(QFont('Consolas', 10))
        location_editor.setMinimumWidth(120)
        location_layout.addWidget(location_label)
        location_layout.addWidget(location_editor, 1)
        generate_character_layout.addLayout(location_layout)
        def update_target_actor_field():
            is_edit_mode = edit_existing_radio.isChecked()
            target_actor_editor.setEnabled(is_edit_mode)
            target_actor_label.setEnabled(is_edit_mode)
            if is_edit_mode:
                target_actor_editor.setStyleSheet("")
            else:
                target_actor_editor.setStyleSheet("color: gray;")
                target_actor_editor.clear()
        create_new_radio.toggled.connect(update_target_actor_field)
        edit_existing_radio.toggled.connect(update_target_actor_field)
        def select_all_fields():
            for checkbox in [name_checkbox, description_checkbox, personality_checkbox, appearance_checkbox,
                           goals_checkbox, story_checkbox, abilities_checkbox, equipment_checkbox]:
                checkbox.setChecked(True)
        def select_no_fields():
            for checkbox in [name_checkbox, description_checkbox, personality_checkbox, appearance_checkbox,
                           goals_checkbox, story_checkbox, abilities_checkbox, equipment_checkbox]:
                checkbox.setChecked(False)
        select_all_btn.clicked.connect(select_all_fields)
        select_none_btn.clicked.connect(select_no_fields)
        select_all_fields()
        generate_character_widget.setVisible(False)
        top_h_layout.addWidget(generate_character_widget)
        generate_random_list_widget = create_generate_random_list_widget(parent=row_widget)
        generate_random_list_widget.setVisible(False)
        top_h_layout.addWidget(generate_random_list_widget)
        force_narrator_widget = QWidget(row_widget)
        force_narrator_layout = QVBoxLayout(force_narrator_widget)
        force_narrator_layout.setContentsMargins(0, 0, 0, 0)
        force_narrator_layout.setSpacing(3)
        fn_order_layout = QHBoxLayout()
        fn_order_label = QLabel("Order:")
        fn_order_label.setFont(QFont('Consolas', 9))
        fn_order_first_radio = QRadioButton("First (Interrupt)")
        fn_order_first_radio.setObjectName("ForceNarratorOrderFirstRadio")
        fn_order_first_radio.setFont(QFont('Consolas', 9))
        fn_order_first_radio.setChecked(True)
        fn_order_last_radio = QRadioButton("Last (End of Turn)")
        fn_order_last_radio.setObjectName("ForceNarratorOrderLastRadio")
        fn_order_last_radio.setFont(QFont('Consolas', 9))
        fn_order_group = QButtonGroup(force_narrator_widget)
        fn_order_group.addButton(fn_order_first_radio)
        fn_order_group.addButton(fn_order_last_radio)
        fn_order_layout.addWidget(fn_order_label)
        fn_order_layout.addWidget(fn_order_first_radio)
        fn_order_layout.addWidget(fn_order_last_radio)
        fn_order_layout.addStretch()
        force_narrator_layout.addLayout(fn_order_layout)
        fn_sys_msg_label = QLabel("System Message Override:")
        fn_sys_msg_label.setFont(QFont('Consolas', 9))
        fn_sys_msg_editor = QTextEdit()
        fn_sys_msg_editor.setObjectName("ForceNarratorSysMsgEditor")
        fn_sys_msg_editor.setFont(QFont('Consolas', 10))
        fn_sys_msg_editor.setPlaceholderText("Optional system message for this forced narration.")
        fn_sys_msg_editor.setMaximumHeight(40)
        force_narrator_layout.addWidget(fn_sys_msg_label)
        force_narrator_layout.addWidget(fn_sys_msg_editor)
        force_narrator_widget.setVisible(False)
        top_h_layout.addWidget(force_narrator_widget)
        screen_effects_widget = QWidget(row_widget)
        screen_effects_layout = QVBoxLayout(screen_effects_widget)
        screen_effects_layout.setContentsMargins(0, 0, 0, 0)
        screen_effects_layout.setSpacing(5)
        effect_type_layout = QHBoxLayout()
        effect_type_label = QLabel("Effect Type:")
        effect_type_label.setFont(QFont('Consolas', 9))
        effect_type_combo = QComboBox()
        effect_type_combo.setObjectName("ScreenEffectTypeCombo")
        effect_type_combo.setFont(QFont('Consolas', 9))
        effect_type_combo.addItems(["Blur", "Flicker", "Static", "Darken/Brighten"])
        effect_type_layout.addWidget(effect_type_label)
        effect_type_layout.addWidget(effect_type_combo, 1)
        screen_effects_layout.addLayout(effect_type_layout)
        parameters_widget = QWidget()
        parameters_layout = QVBoxLayout(parameters_widget)
        parameters_layout.setContentsMargins(0, 0, 0, 0)
        parameters_layout.setSpacing(3)
        enable_layout = QHBoxLayout()
        enable_label = QLabel("Enabled:")
        enable_label.setFont(QFont('Consolas', 9))
        enable_combo = QComboBox()
        enable_combo.setObjectName("ScreenEffectEnabledCombo")
        enable_combo.setFont(QFont('Consolas', 9))
        enable_combo.addItems(["True", "False"])
        enable_layout.addWidget(enable_label)
        enable_layout.addWidget(enable_combo)
        enable_layout.addStretch()
        parameters_layout.addLayout(enable_layout)
        operation_layout = QHBoxLayout()
        operation_label = QLabel("Operation:")
        operation_label.setFont(QFont('Consolas', 9))
        effect_operation_combo = QComboBox()
        effect_operation_combo.setObjectName("ScreenEffectOperationCombo")
        effect_operation_combo.setFont(QFont('Consolas', 9))
        effect_operation_combo.addItems(["Set", "Increment", "Decrement"])
        operation_layout.addWidget(operation_label)
        operation_layout.addWidget(effect_operation_combo)
        operation_layout.addStretch()
        parameters_layout.addLayout(operation_layout)
        param_layout = QHBoxLayout()
        param_name_label = QLabel("Parameter:")
        param_name_label.setFont(QFont('Consolas', 9))
        param_name_combo = QComboBox()
        param_name_combo.setObjectName("ScreenEffectParamNameCombo")
        param_name_combo.setFont(QFont('Consolas', 9))
        param_layout.addWidget(param_name_label)
        param_layout.addWidget(param_name_combo, 1)
        parameters_layout.addLayout(param_layout)
        value_layout = QHBoxLayout()
        param_value_label = QLabel("Value:")
        param_value_label.setFont(QFont('Consolas', 9))
        param_value_input = QLineEdit()
        param_value_input.setObjectName("ScreenEffectParamValueInput")
        param_value_input.setFont(QFont('Consolas', 9))
        param_value_input.setPlaceholderText("Parameter value")
        value_layout.addWidget(param_value_label)
        value_layout.addWidget(param_value_input, 1)
        parameters_layout.addLayout(value_layout)
        flicker_color_layout = QHBoxLayout()
        flicker_color_label = QLabel("Color:")
        flicker_color_label.setFont(QFont('Consolas', 9))
        flicker_color_combo = QComboBox()
        flicker_color_combo.setObjectName("ScreenEffectFlickerColorCombo")
        flicker_color_combo.setFont(QFont('Consolas', 9))
        flicker_color_combo.addItems(["white", "black"])
        flicker_color_layout.addWidget(flicker_color_label)
        flicker_color_layout.addWidget(flicker_color_combo, 1)
        parameters_layout.addLayout(flicker_color_layout)
        flicker_color_label.setVisible(False)
        flicker_color_combo.setVisible(False)
        param_description = QLabel("Parameter description will appear here")
        param_description.setObjectName("ScreenEffectParamDescription")
        param_description.setFont(QFont('Consolas', 8))
        param_description.setWordWrap(True)
        param_description.setStyleSheet(f"color: {base_color};")
        parameters_layout.addWidget(param_description)
        screen_effects_layout.addWidget(parameters_widget)
        screen_effects_widget.setVisible(False)
        top_h_layout.addWidget(screen_effects_widget)
        def update_param_combo():
            effect_type = effect_type_combo.currentText()
            param_name_combo.clear()
            if effect_type == "Blur":
                param_name_combo.addItems(["radius", "animation_speed", "animate"])
            elif effect_type == "Flicker":
                param_name_combo.addItems(["intensity", "frequency", "color"])
            elif effect_type == "Static":
                param_name_combo.addItems(["intensity", "frequency", "dot_size"])
            elif effect_type == "Darken/Brighten":
                param_name_combo.addItems(["factor", "animation_speed", "animate"])
            update_flicker_color_visibility()
            update_param_description()
        def update_flicker_color_visibility():
            is_flicker_effect = effect_type_combo.currentText() == "Flicker"
            is_color_param = param_name_combo.currentText() == "color"
            
            if is_flicker_effect and is_color_param:
                param_value_input.setVisible(False)
                param_value_label.setVisible(False)
                flicker_color_label.setVisible(True)
                flicker_color_combo.setVisible(True)
            else:
                param_value_input.setVisible(True)
                param_value_label.setVisible(True)
                flicker_color_label.setVisible(False)
                flicker_color_combo.setVisible(False)
        def update_param_description():
            effect_type = effect_type_combo.currentText()
            param_name = param_name_combo.currentText()
            description = ""
            if effect_type == "Blur":
                if param_name == "radius":
                    description = "Blur radius (1-20, higher = more blur)"
                elif param_name == "animation_speed":
                    description = "Animation duration in milliseconds (1000-5000)"
                elif param_name == "animate":
                    description = "Whether blur should pulse/animate (true/false)"
            elif effect_type == "Flicker":
                if param_name == "intensity":
                    description = "Flicker strength (0.1-1.0)"
                elif param_name == "frequency":
                    description = "How often flicker occurs in milliseconds (100-2000)"
                elif param_name == "color":
                    description = "Color of flicker effect (select from dropdown)"
            elif effect_type == "Static":
                if param_name == "intensity":
                    description = "Static noise intensity (0.05-0.5)"
                elif param_name == "frequency":
                    description = "Update frequency in milliseconds (50-500)"
                elif param_name == "dot_size":
                    description = "Size of static dots (1-5)"
            elif effect_type == "Darken/Brighten":
                if param_name == "factor":
                    description = "Darkening factor (0.1-0.9) or brightening (1.1-2.0)"
                elif param_name == "animation_speed":
                    description = "Animation duration in milliseconds (1000-5000)"
                elif param_name == "animate":
                    description = "Whether effect should pulse/animate (true/false)"
            param_description.setText(description)
        effect_type_combo.currentIndexChanged.connect(update_param_combo)
        param_name_combo.currentIndexChanged.connect(update_flicker_color_visibility)
        param_name_combo.currentIndexChanged.connect(update_param_description)
        update_param_combo()
        update_flicker_color_visibility()
        generate_context_widget = QWidget()
        generate_context_layout = QVBoxLayout(generate_context_widget)
        generate_context_layout.setContentsMargins(0, 0, 0, 0)
        generate_context_layout.setSpacing(3)
        generate_mode_selector_layout = QHBoxLayout()
        generate_mode_label = QLabel("Generate Mode:")
        generate_mode_label.setFont(QFont('Consolas', 9))
        generate_mode_llm_radio = QRadioButton("LLM")
        generate_mode_llm_radio.setObjectName("GenerateModeLLMRadio")
        generate_mode_llm_radio.setFont(QFont('Consolas', 9))
        generate_mode_llm_radio.setChecked(True)
        generate_mode_random_radio = QRadioButton("Random")
        generate_mode_random_radio.setObjectName("GenerateModeRandomRadio")
        generate_mode_random_radio.setFont(QFont('Consolas', 9))
        generate_mode_group = QButtonGroup(generate_context_widget)
        generate_mode_group.addButton(generate_mode_llm_radio)
        generate_mode_group.addButton(generate_mode_random_radio)
        generate_mode_selector_layout.addWidget(generate_mode_label)
        generate_mode_selector_layout.addWidget(generate_mode_llm_radio)
        generate_mode_selector_layout.addWidget(generate_mode_random_radio)
        generate_mode_selector_layout.addStretch()
        generate_context_layout.addLayout(generate_mode_selector_layout)
        generate_mode_stack = QStackedWidget()
        generate_context_layout.addWidget(generate_mode_stack)
        llm_panel = QWidget()
        llm_panel_layout = QVBoxLayout(llm_panel)
        llm_panel_layout.setContentsMargins(0, 0, 0, 0)
        llm_panel_layout.setSpacing(3)
        generate_instructions_label = QLabel("Generation instructions:")
        generate_instructions_label.setObjectName("GenerateInstructionsLabel")
        llm_panel_layout.addWidget(generate_instructions_label)
        generate_instructions_input = QTextEdit()
        generate_instructions_input.setObjectName("GenerateInstructionsInput")
        generate_instructions_input.setMaximumHeight(60)
        generate_instructions_input.setPlaceholderText("Instructions for generating value")
        llm_panel_layout.addWidget(generate_instructions_input)
        generate_context_label = QLabel("Context:")
        generate_context_label.setObjectName("GenerateContextLabel")
        llm_panel_layout.addWidget(generate_context_label)
        generate_context_radios = QHBoxLayout()
        generate_last_exchange_radio = QRadioButton("Last Exchange")
        generate_last_exchange_radio.setObjectName("GenerateLastExchangeRadio")
        generate_last_exchange_radio.setChecked(True)
        generate_user_msg_radio = QRadioButton("User Message")
        generate_user_msg_radio.setObjectName("GenerateUserMsgRadio")
        generate_full_convo_radio = QRadioButton("Full Conversation")
        generate_full_convo_radio.setObjectName("GenerateFullConvoRadio")
        generate_context_group = QButtonGroup(llm_panel)
        generate_context_group.addButton(generate_last_exchange_radio)
        generate_context_group.addButton(generate_user_msg_radio)
        generate_context_group.addButton(generate_full_convo_radio)
        generate_context_radios.addWidget(generate_last_exchange_radio)
        generate_context_radios.addWidget(generate_user_msg_radio)
        generate_context_radios.addWidget(generate_full_convo_radio)
        llm_panel_layout.addLayout(generate_context_radios)
        generate_mode_stack.addWidget(llm_panel)
        random_panel = QWidget()
        random_panel_layout = QVBoxLayout(random_panel)
        random_panel_layout.setContentsMargins(0, 0, 0, 0)
        random_panel_layout.setSpacing(3)
        random_type_layout = QHBoxLayout()
        random_type_label = QLabel("Random Type:")
        random_type_label.setFont(QFont('Consolas', 9))
        random_type_combo = QComboBox()
        random_type_combo.setObjectName("RandomTypeCombo")
        random_type_combo.setFont(QFont('Consolas', 9))
        random_type_combo.addItems(["Number", "Setting", "Character"])
        random_type_layout.addWidget(random_type_label)
        random_type_layout.addWidget(random_type_combo)
        random_type_layout.addStretch()
        random_panel_layout.addLayout(random_type_layout)
        random_type_stack = QStackedWidget()
        random_panel_layout.addWidget(random_type_stack)

        number_panel = QWidget()
        number_layout = QHBoxLayout(number_panel)
        number_layout.setContentsMargins(0, 0, 0, 0)
        number_layout.setSpacing(5)
        min_label = QLabel("Min:")
        min_label.setFont(QFont('Consolas', 9))
        min_spin = QLineEdit()
        min_spin.setObjectName("RandomNumberMin")
        min_spin.setFont(QFont('Consolas', 9))
        min_spin.setPlaceholderText("-100 or [global,VarName]")
        max_label = QLabel("Max:")
        max_label.setFont(QFont('Consolas', 9))
        max_spin = QLineEdit()
        max_spin.setObjectName("RandomNumberMax")
        max_spin.setFont(QFont('Consolas', 9))
        max_spin.setPlaceholderText("100 or [setting,VarName]")
        number_layout.addWidget(min_label)
        number_layout.addWidget(min_spin)
        number_layout.addWidget(max_label)
        number_layout.addWidget(max_spin)
        number_layout.addStretch()
        random_type_stack.addWidget(number_panel)
        setting_panel = QWidget()
        setting_layout = QVBoxLayout(setting_panel)
        setting_layout.setContentsMargins(0, 0, 0, 0)
        setting_layout.setSpacing(3)
        setting_filter_label = QLabel("Setting Filters (format: var1=value1,var2=value2):")
        setting_filter_label.setFont(QFont('Consolas', 9))
        setting_filter_label.setWordWrap(True)
        setting_layout.addWidget(setting_filter_label)
        setting_filter_input = QLineEdit()
        setting_filter_input.setObjectName("SettingFilterInput")
        setting_filter_input.setFont(QFont('Consolas', 9))
        setting_filter_input.setPlaceholderText("e.g., castle=true,size=large")
        setting_layout.addWidget(setting_filter_input)
        random_type_stack.addWidget(setting_panel)
        character_panel = QWidget()
        character_layout = QVBoxLayout(character_panel)
        character_layout.setContentsMargins(0, 0, 0, 0)
        character_layout.setSpacing(3)
        character_filter_label = QLabel("Character Filters (format: var1=value1,var2=value2):")
        character_filter_label.setFont(QFont('Consolas', 9))
        character_filter_label.setWordWrap(True)
        character_layout.addWidget(character_filter_label)
        character_filter_input = QLineEdit()
        character_filter_input.setObjectName("CharacterFilterInput")
        character_filter_input.setFont(QFont('Consolas', 9))
        character_filter_input.setPlaceholderText("e.g., npc=true,faction=friendly")
        character_layout.addWidget(character_filter_input)
        random_type_stack.addWidget(character_panel)
        generate_mode_stack.addWidget(random_panel)

        def update_generate_mode():
            if generate_mode_llm_radio.isChecked():
                generate_mode_stack.setCurrentIndex(0)
            else:
                generate_mode_stack.setCurrentIndex(1)
        generate_mode_llm_radio.toggled.connect(update_generate_mode)
        generate_mode_random_radio.toggled.connect(update_generate_mode)
        update_generate_mode()
        def update_random_type():
            random_type = random_type_combo.currentText()
            if random_type == "Number":
                random_type_stack.setCurrentIndex(0)
            elif random_type == "Setting":
                random_type_stack.setCurrentIndex(1)
            elif random_type == "Character":
                random_type_stack.setCurrentIndex(2)
        random_type_combo.currentIndexChanged.connect(update_random_type)
        update_random_type()
        generate_context_widget.setVisible(False)
        main_v_layout.addWidget(generate_context_widget)
        temp_parent = row_widget
        current_tab_data = None
        while temp_parent is not None:
                if hasattr(temp_parent, 'property') and temp_parent.property("tab_data"):
                    current_tab_data = temp_parent.property("tab_data")
                    break
                temp_parent = temp_parent.parent()
        if current_tab_data and 'workflow_data_dir' in current_tab_data:
            workflow_dir = current_tab_data['workflow_data_dir']
            actor_names = _get_available_actors(workflow_dir)
            setting_names = _get_available_settings(workflow_dir)
            actor_input.clear()
            actor_input.addItems(actor_names)
            target_setting_input.clear()
            target_setting_input.addItems(setting_names)
            setting_completer = QCompleter(setting_names)
            setting_completer.setCaseSensitivity(Qt.CaseInsensitive)
            setting_completer.setFilterMode(Qt.MatchContains)
            target_setting_input.setCompleter(setting_completer)
        else:
            pass

        def create_post_visibility_condition_row():
            condition_widget = QWidget()
            condition_layout = QHBoxLayout(condition_widget)
            condition_layout.setContentsMargins(0, 0, 0, 0)
            condition_layout.setSpacing(3)
            
            condition_widget.setObjectName("PostVisibilityConditionRow")
            
            name_match_widget = QWidget()
            name_match_layout = QHBoxLayout(name_match_widget)
            name_match_layout.setContentsMargins(0, 0, 0, 0)
            name_match_layout.setSpacing(3)
            
            name_label = QLabel("Name:")
            name_label.setFont(QFont('Consolas', 9))
            name_input = QLineEdit()
            name_input.setObjectName("PostVisibilityNameInput")
            name_input.setFont(QFont('Consolas', 9))
            name_input.setPlaceholderText("Enter character name")
            name_input.setMinimumWidth(120)
            name_match_layout.addWidget(name_label)
            name_match_layout.addWidget(name_input)
            name_match_layout.addStretch()
            
            variable_widget = QWidget()
            variable_layout = QHBoxLayout(variable_widget)
            variable_layout.setContentsMargins(0, 0, 0, 0)
            variable_layout.setSpacing(3)
            
            var_name_label = QLabel("Variable:")
            var_name_label.setFont(QFont('Consolas', 9))
            var_name_input = QLineEdit()
            var_name_input.setObjectName("PostVisibilityVarNameInput")
            var_name_input.setFont(QFont('Consolas', 9))
            var_name_input.setPlaceholderText("Variable name")
            var_name_input.setMinimumWidth(100)
            
            operator_combo = QComboBox()
            operator_combo.setObjectName("PostVisibilityOperatorCombo")
            operator_combo.setFont(QFont('Consolas', 9))
            operator_combo.addItems(["equals", "not equals", "contains", "greater than", "less than", "greater than or equal", "less than or equal"])
            operator_combo.setMinimumWidth(120)
            
            var_value_label = QLabel("Value:")
            var_value_label.setFont(QFont('Consolas', 9))
            var_value_input = QLineEdit()
            var_value_input.setObjectName("PostVisibilityVarValueInput")
            var_value_input.setFont(QFont('Consolas', 9))
            var_value_input.setPlaceholderText("Value to compare")
            var_value_input.setMinimumWidth(100)
            
            variable_layout.addWidget(var_name_label)
            variable_layout.addWidget(var_name_input)
            variable_layout.addWidget(operator_combo)
            variable_layout.addWidget(var_value_label)
            variable_layout.addWidget(var_value_input)
            variable_layout.addStretch()
            
            remove_btn = QPushButton("−")
            remove_btn.setObjectName("PostVisibilityRemoveConditionButton")
            remove_btn.setMaximumWidth(25)
            remove_btn.setMaximumHeight(25)
            remove_btn.setFont(QFont('Consolas', 9))
            
            condition_layout.addWidget(name_match_widget)
            condition_layout.addWidget(variable_widget)
            condition_layout.addWidget(remove_btn)
            
            def update_condition_type():
                try:
                    is_name_match = name_match_radio.isChecked()
                    if name_match_widget and not name_match_widget.isHidden():
                        name_match_widget.setVisible(is_name_match)
                    if variable_widget and not variable_widget.isHidden():
                        variable_widget.setVisible(not is_name_match)
                except RuntimeError:
                    pass
            
            def remove_condition():
                try:
                    if conditions_layout.count() > 2:
                        conditions_layout.removeWidget(condition_widget)
                        condition_widget.deleteLater()
                except RuntimeError:
                    pass
            
            remove_btn.clicked.connect(remove_condition)
            
            # Set initial visibility based on current radio button state
            is_name_match = name_match_radio.isChecked()
            name_match_widget.setVisible(is_name_match)
            variable_widget.setVisible(not is_name_match)
            
            return {
                'widget': condition_widget,
                'name_match_widget': name_match_widget,
                'variable_widget': variable_widget,
                'name_input': name_input,
                'var_name_input': var_name_input,
                'operator_combo': operator_combo,
                'var_value_input': var_value_input,
                'remove_btn': remove_btn,
                'update_condition_type': update_condition_type
            }
        
        post_visibility_conditions = []
        
        def add_post_visibility_condition():
            condition_row = create_post_visibility_condition_row()
            post_visibility_conditions.append(condition_row)
            conditions_layout.addWidget(condition_row['widget'])
        
        def update_all_condition_types():
            for condition_row in post_visibility_conditions:
                try:
                    if 'update_condition_type' in condition_row:
                        condition_row['update_condition_type']()
                except RuntimeError:
                    pass
        
        name_match_radio.toggled.connect(update_all_condition_types)
        variable_radio.toggled.connect(update_all_condition_types)
        
        add_condition_btn.clicked.connect(add_post_visibility_condition)
        
        add_post_visibility_condition()
        
        def update_inputs():
            t = type_selector.currentText()
            is_sys_msg = (t == "System Message")
            is_set_var = (t == "Set Var")
            is_rewrite = (t == "Rewrite Post")
            is_generate_story = (t == "Generate Story")
            is_generate_setting = (t == "Generate Setting")
            is_generate_character = (t == "Generate Character")
            is_generate_random_list = (t == "Generate Random List")
            is_text_tag = (t == "Text Tag")
            is_switch_model = (t == "Switch Model")
            is_change_location = (t == "Change Actor Location")
            is_force_narrator = (t == "Force Narrator")
            is_screen_effect = (t == "Set Screen Effect")
            is_change_brightness = (t == "Change Brightness")
            is_exit_rule_processing = (t == "Exit Rule Processing")
            is_game_over = (t == "Game Over")
            is_post_visibility = (t == "Post Visibility")
            is_add_item = (t == "Add Item")
            is_remove_item = (t == "Remove Item")
            is_move_item = (t == "Move Item")
            is_generate_operation = False
            is_from_random_list = False
            if is_set_var and operation_selector:
                op_text = operation_selector.currentText() 
                is_generate_operation = (op_text == "Generate")
                is_from_random_list = (op_text == "From Random List")
                is_from_var = (op_text == "From Var")
                is_simple_set = (op_text == "Set")

            rule_applies_to_character = False
            parent = row_widget
            rules_manager_widget = None
            loop_count = 0
            max_loops = 10
            while parent is not None and loop_count < max_loops:
                 if parent.findChild(QLineEdit, "RuleIdEditor"):
                      rules_manager_widget = parent
                      break
                 parent = parent.parentWidget()
                 loop_count += 1

            value_editor_visible = not any([
                is_set_var, is_generate_setting, is_generate_story,
                is_generate_character, is_change_location, is_force_narrator,
                is_screen_effect, is_generate_random_list, is_change_brightness, is_exit_rule_processing, is_game_over, is_post_visibility,
                is_add_item, is_remove_item, is_move_item
            ])
            value_editor.setVisible(value_editor_visible)
            var_name_editor.setVisible(is_set_var)
            var_value_editor.setVisible(is_set_var and not (is_generate_operation or is_from_random_list or is_from_var))
            set_var_mode_widget.setVisible(is_set_var and (is_simple_set or is_from_random_list or is_generate_operation or is_from_var))
            text_tag_mode_widget.setVisible(is_text_tag)
            brightness_widget.setVisible(is_change_brightness)
            game_over_widget.setVisible(is_game_over)
            post_visibility_widget.setVisible(is_post_visibility)
            add_item_widget.setVisible(is_add_item)
            remove_item_widget.setVisible(is_remove_item)
            move_item_widget.setVisible(is_move_item)
            position_container.setVisible(is_sys_msg)
            switch_model_widget.setVisible(is_switch_model)
            generate_setting_widget.setVisible(is_generate_setting)
            generate_character_widget.setVisible(is_generate_character)
            generate_random_list_widget.setVisible(is_generate_random_list)
            change_location_widget.setVisible(is_change_location)
            target_setting_input.setVisible(is_change_location and mode_setting_radio.isChecked())
            target_setting_label.setVisible(is_change_location and mode_setting_radio.isChecked())
            operation_selector.setVisible(is_set_var)
            force_narrator_widget.setVisible(is_force_narrator)
            screen_effects_widget.setVisible(is_screen_effect)
            generate_context_widget.setVisible(is_set_var and is_generate_operation)
            random_list_widget.setVisible(is_set_var and is_from_random_list)
            from_var_widget.setVisible(is_set_var and is_from_var)
            should_show_action_scope = is_set_var
            if is_valid_widget(action_var_scope_widget):
                action_var_scope_widget.setVisible(should_show_action_scope)
                if is_valid_widget(row_widget) and is_valid_widget(row_widget.layout()):
                     row_widget.layout().activate()
                     row_widget.adjustSize()
            if value_editor_visible:
                if t == "System Message": value_editor.setPlaceholderText("System message text")
                elif t == "Next Rule": value_editor.setPlaceholderText("Rule ID")
                elif t == "Switch Model": value_editor.setPlaceholderText("Model name")
                elif is_rewrite: value_editor.setPlaceholderText("Rewrite instructions")
                elif is_text_tag: value_editor.setPlaceholderText("Tag text (displays centered)")
                else: value_editor.setPlaceholderText("Action value")
        type_selector.currentIndexChanged.connect(update_inputs)
        operation_selector.currentIndexChanged.connect(update_inputs)
        mode_setting_radio.toggled.connect(update_inputs)
        add_btn = QPushButton("+")
        add_btn.setObjectName("AddActionButton")
        add_btn.setMaximumWidth(30)
        add_btn.setMaximumHeight(30)
        remove_btn = QPushButton("−")
        remove_btn.setObjectName("RemoveActionButton")
        remove_btn.setMaximumWidth(30)
        remove_btn.setMaximumHeight(30)
        move_up_btn = QPushButton("↑")
        move_up_btn.setObjectName("MoveUpActionButton")
        move_up_btn.setMaximumWidth(30)
        move_up_btn.setToolTip("Move action up")
        move_down_btn = QPushButton("↓")
        move_down_btn.setObjectName("MoveDownActionButton")
        move_down_btn.setMaximumWidth(30)
        move_down_btn.setToolTip("Move action down")
        top_h_layout.addWidget(move_up_btn)
        top_h_layout.addWidget(move_down_btn)
        top_h_layout.addWidget(add_btn)
        top_h_layout.addWidget(remove_btn)

        def add_row():
            add_pair_action_row()
            update_all_buttons()

        def remove_row():
            if len(pair_action_rows) > 1:
                idx = -1
                for i, r_data in enumerate(pair_action_rows):
                    if r_data['widget'] is row_widget:
                        idx = i
                        break
                if idx != -1:
                    layout_idx = pair_actions_layout.indexOf(row_widget)
                    if layout_idx > 0:
                        spacer_widget = pair_actions_layout.itemAt(layout_idx - 1).widget()
                        if spacer_widget and spacer_widget.height() == 8:
                            pair_actions_layout.removeWidget(spacer_widget)
                            spacer_widget.deleteLater()
                    row = pair_action_rows.pop(idx)
                    if is_valid_widget(row['widget']) and is_valid_widget(pair_actions_layout):
                            pair_actions_layout.removeWidget(row['widget'])
                            row['widget'].deleteLater()
                            update_all_buttons()
        def move_row_up():
            current_idx = -1
            for i, r_data in enumerate(pair_action_rows):
                if r_data['widget'] is row_widget:
                    current_idx = i
                    break
            if current_idx > 0:
                pair_action_rows[current_idx], pair_action_rows[current_idx - 1] = \
                    pair_action_rows[current_idx - 1], pair_action_rows[current_idx]
                _rebuild_action_rows_layout()
                update_all_buttons()
        
        def move_row_down():
            current_idx = -1
            for i, r_data in enumerate(pair_action_rows):
                if r_data['widget'] is row_widget:
                    current_idx = i
                    break
            
            if current_idx >= 0 and current_idx < len(pair_action_rows) - 1:
                pair_action_rows[current_idx], pair_action_rows[current_idx + 1] = \
                    pair_action_rows[current_idx + 1], pair_action_rows[current_idx]
                _rebuild_action_rows_layout()
                update_all_buttons()
        
        def _rebuild_action_rows_layout():
            while pair_actions_layout.count():
                child = pair_actions_layout.takeAt(0)
                if child.widget():
                    child.widget().setParent(None)
            for i, row_data in enumerate(pair_action_rows):
                if i > 0:
                    spacer = QWidget()
                    spacer.setFixedHeight(8)
                    pair_actions_layout.addWidget(spacer)
                pair_actions_layout.addWidget(row_data['widget'])
        add_btn.clicked.connect(add_row)
        remove_btn.clicked.connect(remove_row)
        move_up_btn.clicked.connect(move_row_up)
        move_down_btn.clicked.connect(move_row_down)

        def update_action_numbers():
            for i, row_data in enumerate(pair_action_rows):
                action_number_label = row_data.get('action_number_label')
                if action_number_label and is_valid_widget(action_number_label):
                    action_number_label.setText(f"Action #{i + 1}")

        def update_buttons():
            remove_btn.setVisible(len(pair_action_rows) > 1 if pair_action_rows else False)
            is_last_row = bool(pair_action_rows and pair_action_rows[-1]['widget'] == row_widget)
            add_btn.setVisible(is_last_row)
            current_idx = -1
            for i, r_data in enumerate(pair_action_rows):
                if r_data['widget'] is row_widget:
                    current_idx = i
                    break
            move_up_btn.setVisible(current_idx > 0)
            move_down_btn.setVisible(current_idx >= 0 and current_idx < len(pair_action_rows) - 1)
            update_action_numbers()

        def populate_actor_setting_dropdowns(workflow_data_dir):
            if not workflow_data_dir:
                return
            try:
                actor_names = _get_available_actors(workflow_data_dir)
                setting_names = _get_available_settings(workflow_data_dir)
                current_actor = actor_input.currentText() if actor_input else ''
                current_setting = target_setting_input.currentText() if target_setting_input else ''
                if actor_input:
                    actor_input.clear()
                    actor_input.addItems(actor_names)
                    if current_actor:
                        idx = actor_input.findText(current_actor)
                        if idx >= 0:
                            actor_input.setCurrentIndex(idx)
                if target_setting_input:
                    target_setting_input.clear()
                    target_setting_input.addItems(setting_names)
                    if current_setting:
                        idx = target_setting_input.findText(current_setting)
                        if idx >= 0:
                            target_setting_input.setCurrentIndex(idx)
            except Exception as e:
                print(f"Error populating actor/setting dropdowns: {e}")

        row = {
            'widget': row_widget,
            'type_selector': type_selector,
            'value_editor': value_editor,
            'var_name_editor': var_name_editor,
            'var_value_editor': var_value_editor,
            'text_tag_mode_widget': text_tag_mode_widget,
            'tag_overwrite_radio': tag_overwrite_radio,
            'tag_append_radio': tag_append_radio,
            'tag_prepend_radio': tag_prepend_radio,
            'position_container': position_container,
            'prepend_radio': prepend_radio,
            'append_radio': append_radio,
            'replace_radio': replace_radio,
            'first_radio': first_radio,
            'last_radio': last_radio,
            'change_location_widget': change_location_widget,
            'actor_input': actor_input,
            'mode_adjacent_radio': mode_adjacent_radio,
            'mode_fast_travel_radio': mode_fast_travel_radio,
            'mode_setting_radio': mode_setting_radio,
            'target_setting_input': target_setting_input,
            'advance_time_checkbox': advance_time_checkbox,
            'add_btn': add_btn,
            'remove_btn': remove_btn,
            'move_up_btn': move_up_btn,
            'move_down_btn': move_down_btn,
            'update_buttons': update_buttons,
            'populate_actor_setting_dropdowns': populate_actor_setting_dropdowns,
            'action_var_scope_widget': action_var_scope_widget,
            'action_scope_global_radio': action_scope_global_radio,
            'action_scope_player_radio': action_scope_player_radio,
            'action_scope_character_radio': action_scope_character_radio,
            'action_scope_scene_chars_radio': action_scope_scene_chars_radio,
            'action_scope_setting_radio': action_scope_setting_radio,
            'generate_character_widget': generate_character_widget,
            'generate_character_instructions_editor': instructions_editor,
            'generate_character_location_editor': location_editor,
            'generate_character_attach_context_checkbox': attach_context_checkbox,
            'generate_random_list_widget': generate_random_list_widget,
            'operation_selector': operation_selector,
            'random_list_widget': random_list_widget,
            'random_list_combo': random_list_combo,
            'random_list_no_context_radio': random_list_no_context_radio,
            'random_list_last_exchange_radio': random_list_last_exchange_radio,
            'random_list_user_msg_radio': random_list_user_msg_radio,
            'random_list_full_convo_radio': random_list_full_convo_radio,
            'from_var_widget': from_var_widget,
            'from_var_name_input': from_var_name_input,
            'from_var_scope_global_radio': from_var_scope_global_radio,
            'from_var_scope_player_radio': from_var_scope_player_radio,
            'from_var_scope_character_radio': from_var_scope_character_radio,
            'from_var_scope_scene_chars_radio': from_var_scope_scene_chars_radio,
            'from_var_scope_setting_radio': from_var_scope_setting_radio,
            'set_var_mode_widget': set_var_mode_widget,
            'set_var_prepend_radio': set_var_prepend_radio,
            'set_var_replace_radio': set_var_replace_radio,
            'set_var_append_radio': set_var_append_radio,
            'set_var_delimiter_input': set_var_delimiter_input,
            'force_narrator_widget': force_narrator_widget,
            'fn_order_first_radio': fn_order_first_radio,
            'fn_order_last_radio': fn_order_last_radio,
            'fn_sys_msg_editor': fn_sys_msg_editor,
            'generate_context_widget': generate_context_widget,
            'generate_instructions_input': generate_instructions_input,
            'generate_last_exchange_radio': generate_last_exchange_radio,
            'generate_user_msg_radio': generate_user_msg_radio,
            'generate_full_convo_radio': generate_full_convo_radio,
            'switch_model_widget': switch_model_widget,
            'switch_model_temp_editor': temp_editor,
            'screen_effects_widget': screen_effects_widget,
            'effect_type_combo': effect_type_combo,
            'effect_operation_combo': effect_operation_combo,
            'param_name_combo': param_name_combo,
            'param_value_input': param_value_input,
            'param_description': param_description,
            'flicker_color_combo': flicker_color_combo,
            'generate_mode_llm_radio': generate_mode_llm_radio,
            'generate_mode_random_radio': generate_mode_random_radio,
            'random_type_combo': random_type_combo,
            'random_number_min_spin': min_spin,
            'random_number_max_spin': max_spin,
            'setting_filter_input': setting_filter_input,
            'character_filter_input': character_filter_input,
            'brightness_widget': brightness_widget,
            'brightness_input': brightness_input,
            'game_over_widget': game_over_widget,
            'game_over_message_input': game_over_message_input,
            'post_visibility_widget': post_visibility_widget,
            'current_post_radio': current_post_radio,
            'player_post_radio': player_post_radio,
            'visible_only_radio': visible_only_radio,
            'not_visible_radio': not_visible_radio,
            'name_match_radio': name_match_radio,
            'variable_radio': variable_radio,
            'post_visibility_conditions': post_visibility_conditions,
            'add_post_visibility_condition': add_post_visibility_condition,
            'add_item_widget': add_item_widget,
            'add_item_name_input': item_name_input,
            'add_item_quantity_input': quantity_input,
            'add_item_generate_checkbox': generate_checkbox,
            'add_item_target_setting_radio': target_setting_radio,
            'add_item_target_character_radio': target_character_radio,
            'add_item_target_name_input': target_name_input,
            'remove_item_widget': remove_item_widget,
            'remove_item_name_input': remove_item_name_input,
            'remove_item_quantity_input': remove_quantity_input,
            'remove_item_target_setting_radio': remove_target_setting_radio,
            'remove_item_target_character_radio': remove_target_character_radio,
            'remove_item_target_name_input': remove_target_name_input,
            'move_item_widget': move_item_widget,
            'move_item_name_input': move_item_name_input,
            'move_item_quantity_input': move_quantity_input,
            'move_item_from_setting_radio': move_from_setting_radio,
            'move_item_from_character_radio': move_from_character_radio,
            'move_item_from_name_input': move_from_name_input,
            'move_item_to_setting_radio': move_to_setting_radio,
            'move_item_to_character_radio': move_to_character_radio,
            'move_item_to_name_input': move_to_name_input,
            'action_number_label': action_number_label
        }
        temp_parent = row_widget
        current_tab_data = None
        while temp_parent is not None:
            if hasattr(temp_parent, 'property') and temp_parent.property("tab_data"):
                current_tab_data = temp_parent.property("tab_data")
                break
            temp_parent = temp_parent.parent()
        if current_tab_data and 'workflow_data_dir' in current_tab_data:
            row['populate_actor_setting_dropdowns'](current_tab_data['workflow_data_dir'])
        if data:
            print(f"    Populating action row with data: {data}")
            action_type = data.get('type')
            if action_type:
                idx = type_selector.findText(action_type, Qt.MatchFixedString)
                if idx >= 0:
                    type_selector.setCurrentIndex(idx)
                    update_inputs()
            populate_action_fields_sync(action_type, data, row_widget, row, update_inputs)
        else:
            update_inputs()
        update_buttons()
        return row

    def populate_action_fields_sync(action_type, data, row_widget, row, update_inputs):
        if not action_type:
            return
        type_selector = row.get('type_selector')
        value_editor = row.get('value_editor')
        var_name_editor = row.get('var_name_editor')
        var_value_editor = row.get('var_value_editor')
        operation_selector = row.get('operation_selector')
        if type_selector and is_valid_widget(type_selector):
            index = type_selector.findText(action_type)
            if index >= 0:
                type_selector.setCurrentIndex(index)
                update_inputs()
        if action_type == 'Set Var':
            update_inputs()
            if is_valid_widget(var_name_editor):
                var_name_editor.setText(data.get('var_name', ''))
            if is_valid_widget(var_value_editor):
                var_value_editor.setText(data.get('var_value', ''))
            scope = data.get('variable_scope', 'Global')
            scope_radios = [
                (row.get('action_scope_global_radio'), 'Global'),
                (row.get('action_scope_player_radio'), 'Player'),
                (row.get('action_scope_character_radio'), 'Character'),
                (row.get('action_scope_scene_chars_radio'), 'Scene Characters'),
                (row.get('action_scope_setting_radio'), 'Setting')
            ]
            for radio, scope_value in scope_radios:
                if radio and is_valid_widget(radio):
                    radio.setChecked(scope == scope_value)
            op_val = data.get('operation', 'set').lower()
            if is_valid_widget(operation_selector):
                op_mapping = {
                    'set': 0, 'increment': 1, 'decrement': 2, 'multiply': 3,
                    'divide': 4, 'generate': 5, 'from random list': 6, 'from var': 7
                }
                idx = op_mapping.get(op_val, 0)
                if op_val == 'from random list':
                    idx = operation_selector.findText('From Random List')
                operation_selector.setCurrentIndex(idx)
                set_var_mode = data.get('set_var_mode', 'replace')
                mode_radios = [
                    (row.get('set_var_prepend_radio'), 'prepend'),
                    (row.get('set_var_replace_radio'), 'replace'),
                    (row.get('set_var_append_radio'), 'append')
                ]
                for radio, mode_value in mode_radios:
                    if radio and is_valid_widget(radio):
                        radio.setChecked(set_var_mode == mode_value or (not set_var_mode and mode_value == 'replace'))
                delimiter_input = row.get('set_var_delimiter_input')
                if delimiter_input and is_valid_widget(delimiter_input):
                    delimiter_input.setText(data.get('set_var_delimiter', '/'))
                if op_val == 'generate':
                    populate_generate_operation(data, row)
                elif op_val == 'from random list':
                    populate_from_random_list(data, row)
                elif op_val == 'from var':
                    populate_from_var(data, row)
                update_inputs()

        elif action_type == 'System Message':
            value_to_set = data.get('value', '')
            if is_valid_widget(value_editor):
                value_editor.setPlainText(value_to_set)
            pos = data.get('position', 'prepend')
            position_radios = [
                (row.get('prepend_radio'), 'prepend'),
                (row.get('append_radio'), 'append'),
                (row.get('replace_radio'), 'replace')
            ]
            for radio, pos_value in position_radios:
                if radio and is_valid_widget(radio):
                    radio.setChecked(pos == pos_value)
            sys_pos = data.get('system_message_position', 'first')
            sys_pos_radios = [
                (row.get('first_radio'), 'first'),
                (row.get('last_radio'), 'last')
            ]
            for radio, sys_pos_value in sys_pos_radios:
                if radio and is_valid_widget(radio):
                    radio.setChecked(sys_pos == sys_pos_value)

        elif action_type in ['Next Rule', 'Switch Model', 'Rewrite Post']:
            if is_valid_widget(value_editor):
                value_editor.setPlainText(data.get('value', ''))
            if action_type == 'Switch Model':
                temp_editor = row.get('switch_model_temp_editor')
                if temp_editor and is_valid_widget(temp_editor):
                    temp_value = data.get('temperature', '')
                    temp_editor.setText(temp_value)

        elif action_type == 'Text Tag':
            if is_valid_widget(value_editor):
                value_editor.setPlainText(data.get('value', ''))
            tag_mode = data.get('tag_mode', 'overwrite')
            tag_mode_radios = [
                (row.get('tag_append_radio'), 'append'),
                (row.get('tag_prepend_radio'), 'prepend'),
                (row.get('tag_overwrite_radio'), 'overwrite')
            ]
            for radio, mode_value in tag_mode_radios:
                if radio and is_valid_widget(radio):
                    radio.setChecked(tag_mode == mode_value)

        elif action_type == 'Change Actor Location':
            populate_change_actor_location(data, row)

        elif action_type == 'Generate Character':
            populate_generate_character(data, row, row_widget)

        elif action_type == 'Generate Random List':
            populate_generate_random_list(data, row, row_widget)

        elif action_type == 'Force Narrator':
            populate_force_narrator(data, row)

        elif action_type == 'Set Screen Effect':
            populate_screen_effect(data, row)

        elif action_type == 'Change Brightness':
            brightness_input = row.get('brightness_input')
            if brightness_input and is_valid_widget(brightness_input):
                brightness_value = data.get('brightness', '1.0')
                brightness_input.setText(str(brightness_value))

        elif action_type == 'Game Over':
            game_over_message_input = row.get('game_over_message_input')
            if game_over_message_input and is_valid_widget(game_over_message_input):
                game_over_message = data.get('game_over_message', '')
                game_over_message_input.setPlainText(game_over_message)

        elif action_type == 'Post Visibility':
            populate_post_visibility(data, row)
            
        elif action_type == 'Add Item':
            populate_add_item(data, row)
            
        elif action_type == 'Remove Item':
            populate_remove_item(data, row)
            
        elif action_type == 'Move Item':
            populate_move_item(data, row)

    def populate_generate_operation(data, row):
        generate_instructions_input = row.get('generate_instructions_input')
        if generate_instructions_input and is_valid_widget(generate_instructions_input):
            generate_instructions_input.setPlainText(data.get('generate_instructions', ''))

        generate_context = data.get('generate_context', 'Last Exchange')
        context_radios = [
            (row.get('generate_last_exchange_radio'), 'Last Exchange'),
            (row.get('generate_user_msg_radio'), 'User Message'),
            (row.get('generate_full_convo_radio'), 'Full Conversation')
        ]
        for radio, context_value in context_radios:
            if radio and is_valid_widget(radio):
                radio.setChecked(generate_context == context_value)

        generate_mode = data.get('generate_mode', 'LLM')
        mode_radios = [
            (row.get('generate_mode_llm_radio'), 'LLM'),
            (row.get('generate_mode_random_radio'), 'Random')
        ]
        for radio, mode_value in mode_radios:
            if radio and is_valid_widget(radio):
                radio.setChecked(generate_mode == mode_value)

        if generate_mode == 'Random':
            populate_random_generation(data, row)

    def populate_random_generation(data, row):
        random_type = data.get('random_type', 'Number')
        random_type_combo = row.get('random_type_combo')
        if random_type_combo and is_valid_widget(random_type_combo):
            random_type_combo.setCurrentText(random_type)
        if random_type == 'Number':
            min_spin = row.get('random_number_min_spin')
            max_spin = row.get('random_number_max_spin')
            if min_spin and is_valid_widget(min_spin):
                min_spin.setText(str(data.get('random_number_min', '')))
            if max_spin and is_valid_widget(max_spin):
                max_spin.setText(str(data.get('random_number_max', '')))
        elif random_type == 'Setting':
            setting_filter_input = row.get('setting_filter_input')
            if setting_filter_input and is_valid_widget(setting_filter_input):
                filters = data.get('random_setting_filters', [])
                filter_str = ','.join(filters)
                setting_filter_input.setText(filter_str)
        elif random_type == 'Character':
            character_filter_input = row.get('character_filter_input')
            if character_filter_input and is_valid_widget(character_filter_input):
                filters = data.get('random_character_filters', [])
                filter_str = ','.join(filters)
                character_filter_input.setText(filter_str)

    def populate_from_random_list(data, row):
        random_list_combo = row.get('random_list_combo')
        if random_list_combo and is_valid_widget(random_list_combo):
            generator_name = data.get('random_list_generator', '')
            random_list_combo.setText(generator_name)
        random_list_context = data.get('random_list_context', 'No Context')
        context_radios = [
            (row.get('random_list_no_context_radio'), 'No Context'),
            (row.get('random_list_last_exchange_radio'), 'Last Exchange'),
            (row.get('random_list_user_msg_radio'), 'User Message'),
            (row.get('random_list_full_convo_radio'), 'Full Conversation')
        ]
        for radio, context_value in context_radios:
            if radio and is_valid_widget(radio):
                radio.setChecked(random_list_context == context_value)

    def populate_from_var(data, row):
        from_var_name_input = row.get('from_var_name_input')
        if from_var_name_input and is_valid_widget(from_var_name_input):
            source_var_name = data.get('from_var_name', '')
            from_var_name_input.setText(source_var_name)
        from_var_scope = data.get('from_var_scope', 'Global')
        scope_radios = [
            (row.get('from_var_scope_global_radio'), 'Global'),
            (row.get('from_var_scope_player_radio'), 'Player'),
            (row.get('from_var_scope_character_radio'), 'Character'),
            (row.get('from_var_scope_scene_chars_radio'), 'Scene Characters'),
            (row.get('from_var_scope_setting_radio'), 'Setting')
        ]
        for radio, scope_value in scope_radios:
            if radio and is_valid_widget(radio):
                radio.setChecked(from_var_scope == scope_value)

    def populate_change_actor_location(data, row):
        actor_name = data.get('actor_name', '')
        mode = data.get('location_mode', 'Setting')
        target_setting = data.get('target_setting', '')
        advance_time = data.get('advance_time', True)
        actor_input = row.get('actor_input')
        if actor_input and is_valid_widget(actor_input):
            actor_input.setText(actor_name)
        mode_radios = [
            (row.get('mode_adjacent_radio'), 'Adjacent'),
            (row.get('mode_fast_travel_radio'), 'Fast Travel'),
            (row.get('mode_setting_radio'), 'Setting')
        ]
        for radio, mode_value in mode_radios:
            if radio and is_valid_widget(radio):
                radio.setChecked(mode == mode_value)
        target_setting_input = row.get('target_setting_input')
        if target_setting_input and is_valid_widget(target_setting_input):
            target_setting_input.setText(target_setting)
        advance_time_checkbox = row.get('advance_time_checkbox')
        if advance_time_checkbox and is_valid_widget(advance_time_checkbox):
            advance_time_checkbox.setChecked(advance_time)

    def populate_generate_character(data, row, row_widget):
        generate_character_widget = row.get('generate_character_widget')
        if not generate_character_widget:
            return
        instructions_editor = generate_character_widget.findChild(QTextEdit, "GenerateCharacterInstructionsEditor")
        location_editor = generate_character_widget.findChild(QLineEdit, "GenerateCharacterLocationEditor")
        attach_context_checkbox = generate_character_widget.findChild(QCheckBox, "GenerateCharacterAttachContextCheckbox")
        if instructions_editor and is_valid_widget(instructions_editor):
            instructions_editor.setPlainText(data.get('instructions', ''))
        if location_editor and is_valid_widget(location_editor):
            location_editor.setText(data.get('location', ''))
        if attach_context_checkbox and is_valid_widget(attach_context_checkbox):
            attach_context_checkbox.setChecked(data.get('attach_context', False))
        saved_generation_mode = data.get('generation_mode', 'Create New')
        create_new_radio = generate_character_widget.findChild(QRadioButton, "GenerateCharacterCreateNewRadio")
        edit_existing_radio = generate_character_widget.findChild(QRadioButton, "GenerateCharacterEditExistingRadio")
        if create_new_radio and edit_existing_radio:
            if saved_generation_mode == 'Edit Existing':
                edit_existing_radio.setChecked(True)
            else:
                create_new_radio.setChecked(True)
        saved_target_directory = data.get('target_directory', 'Game')
        game_dir_radio = generate_character_widget.findChild(QRadioButton, "GenerateCharacterGameDirRadio")
        resources_dir_radio = generate_character_widget.findChild(QRadioButton, "GenerateCharacterResourcesDirRadio")
        if game_dir_radio and resources_dir_radio:
            if saved_target_directory == 'Resources':
                resources_dir_radio.setChecked(True)
            else:
                game_dir_radio.setChecked(True)
        target_actor_editor = generate_character_widget.findChild(QLineEdit, "GenerateCharacterTargetActorEditor")
        if target_actor_editor and is_valid_widget(target_actor_editor):
            target_actor_editor.setText(data.get('target_actor_name', ''))
        model_editor = generate_character_widget.findChild(QLineEdit, "GenerateCharacterModelEditor")
        if model_editor and is_valid_widget(model_editor):
            model_editor.setText(data.get('model_override', ''))
        saved_fields_to_generate = data.get('fields_to_generate', ['name', 'description', 'personality', 'appearance', 'goals', 'story', 'abilities', 'equipment'])
        field_checkboxes = [
            ("GenerateCharacterNameCheckbox", "name"),
            ("GenerateCharacterDescriptionCheckbox", "description"),
            ("GenerateCharacterPersonalityCheckbox", "personality"),
            ("GenerateCharacterAppearanceCheckbox", "appearance"),
            ("GenerateCharacterGoalsCheckbox", "goals"),
            ("GenerateCharacterStoryCheckbox", "story"),
            ("GenerateCharacterAbilitiesCheckbox", "abilities"),
            ("GenerateCharacterEquipmentCheckbox", "equipment")
        ]

        for checkbox_name, field_name in field_checkboxes:
            checkbox = generate_character_widget.findChild(QCheckBox, checkbox_name)
            if checkbox and is_valid_widget(checkbox):
                checkbox.setChecked(field_name in saved_fields_to_generate)

    def populate_generate_random_list(data, row, row_widget):
        gen_random_list_widget = row.get('generate_random_list_widget')
        if not gen_random_list_widget:
            return
        is_permutate = data.get('is_permutate', False)
        generator_name = data.get('generator_name', '')
        instructions = data.get('instructions', '')
        model_override = data.get('model_override', '')
        var_name = data.get('var_name', '')
        var_scope = data.get('var_scope', 'Global')
        context = data.get('generate_context', 'No Context')
        mode_new_radio = gen_random_list_widget.findChild(QRadioButton, "GenRandomListNewRadio")
        mode_permutate_radio = gen_random_list_widget.findChild(QRadioButton, "GenRandomListPermutateRadio")
        if mode_new_radio and mode_permutate_radio:
            if is_permutate:
                mode_permutate_radio.setChecked(True)
            else:
                mode_new_radio.setChecked(True)
        name_input = gen_random_list_widget.findChild(QLineEdit, "GenRandomListNameInput")
        if name_input and is_valid_widget(name_input):
            name_input.setText(generator_name)
        instructions_input = gen_random_list_widget.findChild(QTextEdit, "GenRandomListInstructionsInput")
        if instructions_input and is_valid_widget(instructions_input):
            instructions_input.setPlainText(instructions)
        if is_permutate:
            objects_checkbox = gen_random_list_widget.findChild(QCheckBox, "GenRandomListObjectsCheckbox")
            weights_checkbox = gen_random_list_widget.findChild(QCheckBox, "GenRandomListWeightsCheckbox")
            if objects_checkbox and is_valid_widget(objects_checkbox):
                objects_checkbox.setChecked(data.get('permutate_objects', False))
            if weights_checkbox and is_valid_widget(weights_checkbox):
                weights_checkbox.setChecked(data.get('permutate_weights', False))
        model_input = gen_random_list_widget.findChild(QLineEdit, "GenRandomListModelInput")
        if model_input and is_valid_widget(model_input):
            model_input.setText(model_override)
        var_name_input = gen_random_list_widget.findChild(QLineEdit, "GenRandomListVarNameInput")
        if var_name_input and is_valid_widget(var_name_input):
            var_name_input.setText(var_name)
        scope_radios = [
            ("GenRandomListVarScopeGlobalRadio", "Global"),
            ("GenRandomListVarScopePlayerRadio", "Player"),
            ("GenRandomListVarScopeCharacterRadio", "Character"),
            ("GenRandomListVarScopeSettingRadio", "Setting"),
            ("GenRandomListVarScopeSceneCharsRadio", "Scene Characters")
        ]
        for radio_name, scope_value in scope_radios:
            radio = gen_random_list_widget.findChild(QRadioButton, radio_name)
            if radio and is_valid_widget(radio):
                radio.setChecked(var_scope == scope_value)
        context_radios = [
            ("GenRandomListNoContextRadio", "No Context"),
            ("GenRandomListLastExchangeRadio", "Last Exchange"),
            ("GenRandomListUserMsgRadio", "User Message"),
            ("GenRandomListFullConvoRadio", "Full Conversation")
        ]
        for radio_name, context_value in context_radios:
            radio = gen_random_list_widget.findChild(QRadioButton, radio_name)
            if radio and is_valid_widget(radio):
                radio.setChecked(context == context_value)

    def populate_force_narrator(data, row):
        fn_order = data.get('force_narrator_order', 'First')
        fn_sys_msg = data.get('force_narrator_system_message', '')
        fn_order_first_radio = row.get('fn_order_first_radio')
        fn_order_last_radio = row.get('fn_order_last_radio')
        if fn_order_first_radio and is_valid_widget(fn_order_first_radio):
            fn_order_first_radio.setChecked(fn_order == 'First')
        if fn_order_last_radio and is_valid_widget(fn_order_last_radio):
            fn_order_last_radio.setChecked(fn_order == 'Last')
        fn_sys_msg_editor = row.get('fn_sys_msg_editor')
        if fn_sys_msg_editor and is_valid_widget(fn_sys_msg_editor):
            fn_sys_msg_editor.setPlainText(fn_sys_msg)

    def populate_post_visibility(data, row):
        applies_to = data.get('applies_to', 'Current Post')
        visibility_mode = data.get('visibility_mode', 'Visible Only To')
        condition_type = data.get('condition_type', 'Name Match')
        conditions = data.get('conditions', [])
        
        current_post_radio = row.get('current_post_radio')
        player_post_radio = row.get('player_post_radio')
        visible_only_radio = row.get('visible_only_radio')
        not_visible_radio = row.get('not_visible_radio')
        name_match_radio = row.get('name_match_radio')
        variable_radio = row.get('variable_radio')
        
        if current_post_radio and is_valid_widget(current_post_radio):
            current_post_radio.setChecked(applies_to == 'Current Post')
        if player_post_radio and is_valid_widget(player_post_radio):
            player_post_radio.setChecked(applies_to == 'Player Post')
        if visible_only_radio and is_valid_widget(visible_only_radio):
            visible_only_radio.setChecked(visibility_mode == 'Visible Only To')
        if not_visible_radio and is_valid_widget(not_visible_radio):
            not_visible_radio.setChecked(visibility_mode == 'Not Visible To')
        if name_match_radio and is_valid_widget(name_match_radio):
            name_match_radio.setChecked(condition_type == 'Name Match')
        if variable_radio and is_valid_widget(variable_radio):
            variable_radio.setChecked(condition_type == 'Variable')
        
        # Clear existing conditions first
        post_visibility_conditions = row.get('post_visibility_conditions', [])
        conditions_container = None
        
        # Find the conditions container
        post_visibility_widget = row.get('post_visibility_widget')
        if post_visibility_widget:
            conditions_container = post_visibility_widget.findChild(QWidget, "PostVisibilityConditionsContainer")
        
        # Clear existing conditions (except the header)
        if conditions_container and conditions_container.layout():
            # Remove all widgets except the header (first item)
            while conditions_container.layout().count() > 1:
                item = conditions_container.layout().takeAt(1)
                if item.widget():
                    item.widget().deleteLater()
        
        # Clear the post_visibility_conditions list
        post_visibility_conditions.clear()
        
        # Add conditions from data
        for condition_data in conditions:
            condition_type = condition_data.get('type', 'Name Match')
            
            # Create a new condition row
            condition_widget = QWidget()
            condition_layout = QHBoxLayout(condition_widget)
            condition_layout.setContentsMargins(0, 0, 0, 0)
            condition_layout.setSpacing(3)
            
            condition_widget.setObjectName("PostVisibilityConditionRow")
            
            name_match_widget = QWidget()
            name_match_layout = QHBoxLayout(name_match_widget)
            name_match_layout.setContentsMargins(0, 0, 0, 0)
            name_match_layout.setSpacing(3)
            
            name_label = QLabel("Name:")
            name_label.setFont(QFont('Consolas', 9))
            name_input = QLineEdit()
            name_input.setObjectName("PostVisibilityNameInput")
            name_input.setFont(QFont('Consolas', 9))
            name_input.setPlaceholderText("Enter character name")
            name_input.setMinimumWidth(120)
            name_match_layout.addWidget(name_label)
            name_match_layout.addWidget(name_input)
            name_match_layout.addStretch()
            
            variable_widget = QWidget()
            variable_layout = QHBoxLayout(variable_widget)
            variable_layout.setContentsMargins(0, 0, 0, 0)
            variable_layout.setSpacing(3)
            
            var_name_label = QLabel("Variable:")
            var_name_label.setFont(QFont('Consolas', 9))
            var_name_input = QLineEdit()
            var_name_input.setObjectName("PostVisibilityVarNameInput")
            var_name_input.setFont(QFont('Consolas', 9))
            var_name_input.setPlaceholderText("Variable name")
            var_name_input.setMinimumWidth(100)
            
            operator_combo = QComboBox()
            operator_combo.setObjectName("PostVisibilityOperatorCombo")
            operator_combo.setFont(QFont('Consolas', 9))
            operator_combo.addItems(["equals", "not equals", "contains", "greater than", "less than", "greater than or equal", "less than or equal"])
            operator_combo.setMinimumWidth(120)
            
            var_value_label = QLabel("Value:")
            var_value_label.setFont(QFont('Consolas', 9))
            var_value_input = QLineEdit()
            var_value_input.setObjectName("PostVisibilityVarValueInput")
            var_value_input.setFont(QFont('Consolas', 9))
            var_value_input.setPlaceholderText("Value to compare")
            var_value_input.setMinimumWidth(100)
            
            variable_layout.addWidget(var_name_label)
            variable_layout.addWidget(var_name_input)
            variable_layout.addWidget(operator_combo)
            variable_layout.addWidget(var_value_label)
            variable_layout.addWidget(var_value_input)
            variable_layout.addStretch()
            
            remove_btn = QPushButton("−")
            remove_btn.setObjectName("PostVisibilityRemoveConditionButton")
            remove_btn.setMaximumWidth(25)
            remove_btn.setMaximumHeight(25)
            remove_btn.setFont(QFont('Consolas', 9))
            
            condition_layout.addWidget(name_match_widget)
            condition_layout.addWidget(variable_widget)
            condition_layout.addWidget(remove_btn)
            
            # Set visibility based on condition type
            if condition_type == 'Name Match':
                name_match_widget.setVisible(True)
                variable_widget.setVisible(False)
                name_input.setText(condition_data.get('name', ''))
            elif condition_type == 'Variable':
                name_match_widget.setVisible(False)
                variable_widget.setVisible(True)
                var_name_input.setText(condition_data.get('variable_name', ''))
                operator = condition_data.get('operator', 'equals')
                
                # Convert backend operators to UI operators
                operator_mapping = {
                    '==': 'equals',
                    '!=': 'not equals',
                    'contains': 'contains',
                    '>': 'greater than',
                    '<': 'less than',
                    '>=': 'greater than or equal',
                    '<=': 'less than or equal'
                }
                ui_operator = operator_mapping.get(operator, 'equals')
                idx = operator_combo.findText(ui_operator)
                if idx >= 0:
                    operator_combo.setCurrentIndex(idx)
                var_value_input.setText(condition_data.get('value', ''))
            
            # Add remove functionality
            def remove_condition():
                try:
                    if conditions_container and conditions_container.layout():
                        conditions_container.layout().removeWidget(condition_widget)
                        condition_widget.deleteLater()
                except RuntimeError:
                    pass
            
            remove_btn.clicked.connect(remove_condition)
            
            # Add to container
            if conditions_container and conditions_container.layout():
                conditions_container.layout().addWidget(condition_widget)
                
                # Add to post_visibility_conditions list for tracking
                condition_row_data = {
                    'widget': condition_widget,
                    'name_match_widget': name_match_widget,
                    'variable_widget': variable_widget,
                    'name_input': name_input,
                    'var_name_input': var_name_input,
                    'operator_combo': operator_combo,
                    'var_value_input': var_value_input,
                    'remove_btn': remove_btn
                }
                post_visibility_conditions.append(condition_row_data)

    def populate_add_item(data, row):
        item_name = data.get('item_name', '')
        quantity = data.get('quantity', '1')
        target_type = data.get('target_type', 'Setting')
        target_name = data.get('target_name', '')
        generate = data.get('generate', False)
        
        item_name_input = row.get('add_item_name_input')
        if item_name_input and is_valid_widget(item_name_input):
            item_name_input.setText(item_name)
            
        quantity_input = row.get('add_item_quantity_input')
        if quantity_input and is_valid_widget(quantity_input):
            quantity_input.setText(quantity)
            
        generate_checkbox = row.get('add_item_generate_checkbox')
        if generate_checkbox and is_valid_widget(generate_checkbox):
            generate_checkbox.setChecked(generate)
            
        target_setting_radio = row.get('add_item_target_setting_radio')
        target_character_radio = row.get('add_item_target_character_radio')
        if target_setting_radio and target_character_radio:
            if target_type == 'Setting':
                target_setting_radio.setChecked(True)
            else:
                target_character_radio.setChecked(True)
                
        target_name_input = row.get('add_item_target_name_input')
        if target_name_input and is_valid_widget(target_name_input):
            target_name_input.setText(target_name)

    def populate_remove_item(data, row):
        item_name = data.get('item_name', '')
        quantity = data.get('quantity', '1')
        target_type = data.get('target_type', 'Setting')
        target_name = data.get('target_name', '')
        
        item_name_input = row.get('remove_item_name_input')
        if item_name_input and is_valid_widget(item_name_input):
            item_name_input.setText(item_name)
            
        quantity_input = row.get('remove_item_quantity_input')
        if quantity_input and is_valid_widget(quantity_input):
            quantity_input.setText(quantity)
            
        target_setting_radio = row.get('remove_item_target_setting_radio')
        target_character_radio = row.get('remove_item_target_character_radio')
        if target_setting_radio and target_character_radio:
            if target_type == 'Setting':
                target_setting_radio.setChecked(True)
            else:
                target_character_radio.setChecked(True)
                
        target_name_input = row.get('remove_item_target_name_input')
        if target_name_input and is_valid_widget(target_name_input):
            target_name_input.setText(target_name)

    def populate_move_item(data, row):
        item_name = data.get('item_name', '')
        quantity = data.get('quantity', '1')
        from_type = data.get('from_type', 'Setting')
        from_name = data.get('from_name', '')
        to_type = data.get('to_type', 'Setting')
        to_name = data.get('to_name', '')
        
        item_name_input = row.get('move_item_name_input')
        if item_name_input and is_valid_widget(item_name_input):
            item_name_input.setText(item_name)
            
        quantity_input = row.get('move_item_quantity_input')
        if quantity_input and is_valid_widget(quantity_input):
            quantity_input.setText(quantity)
            
        from_setting_radio = row.get('move_item_from_setting_radio')
        from_character_radio = row.get('move_item_from_character_radio')
        if from_setting_radio and from_character_radio:
            if from_type == 'Setting':
                from_setting_radio.setChecked(True)
            else:
                from_character_radio.setChecked(True)
                
        from_name_input = row.get('move_item_from_name_input')
        if from_name_input and is_valid_widget(from_name_input):
            from_name_input.setText(from_name)
            
        to_setting_radio = row.get('move_item_to_setting_radio')
        to_character_radio = row.get('move_item_to_character_radio')
        if to_setting_radio and to_character_radio:
            if to_type == 'Setting':
                to_setting_radio.setChecked(True)
            else:
                to_character_radio.setChecked(True)
                
        to_name_input = row.get('move_item_to_name_input')
        if to_name_input and is_valid_widget(to_name_input):
            to_name_input.setText(to_name)

    def populate_screen_effect(data, row):
        effect_type = data.get('effect_type', 'Blur')
        operation = data.get('operation', 'set')
        param_name = data.get('param_name', '')
        param_value = data.get('param_value', '')
        enabled = data.get('enabled', True)
        effect_type_combo = row.get('effect_type_combo')
        if effect_type_combo and is_valid_widget(effect_type_combo):
            idx = effect_type_combo.findText(effect_type)
            if idx >= 0:
                effect_type_combo.setCurrentIndex(idx)
        effect_operation_combo = row.get('effect_operation_combo')
        if effect_operation_combo and is_valid_widget(effect_operation_combo):
            operation_title_case = operation.capitalize()
            idx = effect_operation_combo.findText(operation_title_case)
            if idx >= 0:
                effect_operation_combo.setCurrentIndex(idx)
        param_name_combo = row.get('param_name_combo')
        if param_name_combo and is_valid_widget(param_name_combo):
            param_name_combo.setCurrentText(param_name)
        if effect_type == "Flicker" and param_name == "color":
            flicker_color_combo = row.get('flicker_color_combo')
            if flicker_color_combo and is_valid_widget(flicker_color_combo):
                flicker_color_combo.setCurrentText(param_value)
        else:
            param_value_input = row.get('param_value_input')
            if param_value_input and is_valid_widget(param_value_input):
                param_value_input.setText(param_value)
        enable_combo = row.get('enable_combo')
        if enable_combo and is_valid_widget(enable_combo):
            enable_combo.setCurrentText("True" if enabled else "False")

    def add_pair_action_row(data=None, workflow_data_dir=None):
        if pair_action_rows:
            spacer = QWidget()
            spacer.setFixedHeight(8)
            pair_actions_layout.addWidget(spacer)
        row = create_pair_action_row(data, workflow_data_dir)
        pair_action_rows.append(row)
        pair_actions_layout.addWidget(row['widget'])
        update_all_buttons()
        return row
    pair_layout.addWidget(pair_actions_container)
    def remove_pair(pair_data, tab_data):
        if len(tab_data['tag_action_pairs']) <= 1:
            QMessageBox.warning(None, "Cannot Remove", "At least one tag/action pair is required.")
            return
        pair_index = -1
        for i, pair in enumerate(tab_data['tag_action_pairs']):
            if pair is pair_data:
                pair_index = i
                break
        if pair_index == -1:
            widget_to_remove = pair_data.get('widget')
            for i, pair in enumerate(tab_data['tag_action_pairs']):
                if pair.get('widget') is widget_to_remove:
                    pair_index = i
                    break
        if pair_index == -1:
                return
        removed_pair = tab_data['tag_action_pairs'].pop(pair_index)
        widget = removed_pair.get('widget')
        if is_valid_widget(tab_data.get('pairs_layout')) and is_valid_widget(widget):
            tab_data['pairs_layout'].removeWidget(widget)
            widget.hide()
            widget.deleteLater()
        
        for i, pair in enumerate(tab_data['tag_action_pairs']):
            try:
                label_widget = pair.get('label')
                if is_valid_widget(label_widget):
                    label_widget.setText(f"Pair #{i + 1}")
            except (RuntimeError, Exception) as e:
                print(f"Error relabeling pair {i+1}: {e}")
        
        pairs_container = tab_data.get('pairs_container')
        if pairs_container and is_valid_widget(pairs_container):
            pairs_container.update()
        
        QApplication.processEvents()

    pair_data = {
        'widget': pair_widget,
        'tag_editor': tag_editor,
        'pair_action_rows': pair_action_rows,
        'label': pair_label,
        'add_pair_action_row': add_pair_action_row
    }
    remove_button.clicked.connect(lambda checked=False, p_data=pair_data, t_data=tab_data: remove_pair(p_data, t_data))
    return pair_data
