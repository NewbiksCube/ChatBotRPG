import json
import os
import re
import copy
import pygame
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton, QMessageBox, QRadioButton, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication

def is_valid_widget(widget):
    if not widget:
        return False
    try:
        widget.objectName()
        return True
    except (RuntimeError, Exception):
        return False
_layout_refs = []

def _add_rule(self, tab_index, rule_id_editor, condition_editor, tag_action_pairs_argument_ignored,
            prepend_radio, append_radio, replace_radio, is_last_exchange, trigger_selector, rules_list):
    if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
        print(f"Error: Invalid tab index: {tab_index}")
        return
    tab_data = self.tabs_data[tab_index]
    tab_content_widget = tab_data['widget']
    if not tab_content_widget:
        print("Error: Tab content widget not found")
        return
    new_rule_id = rule_id_editor.text().strip()
    if not new_rule_id:
        QMessageBox.warning(self, "Missing ID", "Rule ID is required.")
        return
    description_editor = tab_data.get('description_editor')
    description = description_editor.text().strip() if description_editor else ""
    add_update_button = None
    editing_index = -1
    for button in tab_content_widget.findChildren(QPushButton):
        if button.objectName().startswith("add_rule_button_"):
            add_update_button = button
            stored_index_prop = button.property("editing_rule_index")
            if stored_index_prop is not None:
                try:
                    editing_index = int(stored_index_prop)
                except (ValueError, TypeError):
                    print(f"Warning: Invalid editing_rule_index property found: {stored_index_prop}")
                    editing_index = -1
            break
    if not add_update_button:
        QMessageBox.critical(self, "Error", "Could not find the Add/Update Rule button.")
        return
    is_update_mode = editing_index >= 0
    rules = tab_data.get('thought_rules', [])
    conditions_container = tab_content_widget.findChild(QWidget, "ConditionsContainer")
    condition_rows_data = []
    if conditions_container:
        condition_widgets = []
        for i in range(conditions_container.layout().count()):
            widget = conditions_container.layout().itemAt(i).widget()
            if widget and widget.layout():
                condition_widgets.append(widget)
        for i, condition_widget in enumerate(condition_widgets):
            selector = condition_widget.findChild(QComboBox, "StartConditionSelector")
            if not selector:
                continue
            try:
                condition_type = selector.currentText()
                condition_data = {"type": condition_type}
                if condition_type in ["Setting", "Location", "Region", "World"]:
                    geography_editor = condition_widget.findChild(QLineEdit, "GeographyNameEditor")
                    if geography_editor:
                        try:
                            condition_data["geography_name"] = geography_editor.text().strip()
                        except RuntimeError:
                            pass
                elif condition_type == "Variable":
                    var_editor = condition_widget.findChild(QLineEdit, "ConditionVarNameEditor")
                    op_selector = condition_widget.findChild(QComboBox, "VariableCondOpSelector")
                    val_editor = condition_widget.findChild(QLineEdit, "ConditionVarValueEditor")
                    if var_editor and op_selector:
                        try:
                            var_name = var_editor.text().strip()
                            operator = op_selector.currentText()
                            value = None
                            if val_editor and operator not in ["exists", "not exists"]:
                                try:
                                    value = val_editor.text()
                                except RuntimeError:
                                    pass
                            if var_name:
                                condition_data["variable"] = var_name
                                condition_data["operator"] = operator
                                condition_data["value"] = value
                                scope_global_radio = condition_widget.findChild(QRadioButton, "ConditionVarScopeGlobalRadio")
                                scope_character_radio = condition_widget.findChild(QRadioButton, "ConditionVarScopeCharacterRadio")
                                scope_player_radio = condition_widget.findChild(QRadioButton, "ConditionVarScopePlayerRadio")
                                scope_setting_radio = condition_widget.findChild(QRadioButton, "ConditionVarScopeSettingRadio")
                                if scope_global_radio and scope_global_radio.isChecked():
                                    condition_data["variable_scope"] = "Global"
                                elif scope_character_radio and scope_character_radio.isChecked():
                                    condition_data["variable_scope"] = "Character"
                                elif scope_player_radio and scope_player_radio.isChecked():
                                    condition_data["variable_scope"] = "Player"
                                elif scope_setting_radio and scope_setting_radio.isChecked():
                                    condition_data["variable_scope"] = "Setting"
                                else:
                                    condition_data["variable_scope"] = "Global"
                        except RuntimeError:
                            pass   
                elif condition_type == "Scene Count":
                    op_selector = condition_widget.findChild(QComboBox, "SceneCondOpSelector")
                    value_spinner = condition_widget.findChild(QSpinBox, "ConditionSceneCountSpinner")
                    if op_selector and value_spinner:
                        try:
                            condition_data["operator"] = op_selector.currentText()
                            condition_data["value"] = value_spinner.value()
                        except RuntimeError:
                            pass
                elif condition_type == "Game Time":
                    op_selector = condition_widget.findChild(QComboBox, "GameTimeCondOpSelector")
                    type_selector = condition_widget.findChild(QComboBox, "GameTimeTypeSelector")
                    value_spinner = condition_widget.findChild(QSpinBox, "GameTimeValueSpinner")
                    if op_selector and type_selector and value_spinner:
                        try:
                            condition_data["operator"] = op_selector.currentText()
                            condition_data["time_type"] = type_selector.currentText()
                            condition_data["value"] = value_spinner.value()
                        except RuntimeError:
                            pass
                elif condition_type == "Post Dialogue":
                    post_player_radio = condition_widget.findChild(QRadioButton, "PostDialoguePlayerPostRadio")
                    post_current_radio = condition_widget.findChild(QRadioButton, "PostDialogueCurrentPostRadio")
                    operator_is_radio = condition_widget.findChild(QRadioButton, "PostDialogueIsRadio")
                    operator_not_radio = condition_widget.findChild(QRadioButton, "PostDialogueNotRadio")
                    dialogue_all_radio = condition_widget.findChild(QRadioButton, "PostDialogueAllRadio")
                    dialogue_some_radio = condition_widget.findChild(QRadioButton, "PostDialogueSomeRadio")
                    dialogue_none_radio = condition_widget.findChild(QRadioButton, "PostDialogueNoneRadio")
                    try:
                        if post_current_radio and post_current_radio.isChecked():
                            condition_data["post_type"] = "Current Post"
                        else:
                            condition_data["post_type"] = "Player Post"
                        
                        if operator_not_radio and operator_not_radio.isChecked():
                            condition_data["operator"] = "Not"
                        else:
                            condition_data["operator"] = "Is"
                        print(f"[DEBUG] Saving Post Dialogue operator: Is={operator_is_radio.isChecked() if operator_is_radio else 'None'}, Not={operator_not_radio.isChecked() if operator_not_radio else 'None'} -> '{condition_data['operator']}'")
                        
                        if dialogue_all_radio and dialogue_all_radio.isChecked():
                            condition_data["dialogue_amount"] = "All Dialogue"
                        elif dialogue_some_radio and dialogue_some_radio.isChecked():
                            condition_data["dialogue_amount"] = "Some Dialogue"
                        elif dialogue_none_radio and dialogue_none_radio.isChecked():
                            condition_data["dialogue_amount"] = "No Dialogue"
                        else:
                            condition_data["dialogue_amount"] = "All Dialogue"
                    except RuntimeError:
                        pass
                condition_rows_data.append(condition_data)
            except RuntimeError:
                pass
    condition = condition_editor.toPlainText().strip()
    model_editor = tab_content_widget.findChild(QLineEdit, "ModelEditor")
    model = ""
    if model_editor:
        try:
            model = model_editor.text().strip()
        except RuntimeError:
            print("Warning: model_editor has been deleted")
    pairs_container = tab_content_widget.findChild(QWidget, "PairsContainer")
    tag_action_pairs_data = []
    if pairs_container:
        try:
            if pairs_container and pairs_container.layout():
                pairs_layout = pairs_container.layout()
                for i in range(pairs_layout.count()):
                    item = pairs_layout.itemAt(i)
                    if item and item.widget() and item.widget().objectName() == "PairWidget":
                        pair_widget = item.widget()
                        try:
                            tag_editor = pair_widget.findChild(QTextEdit, "TagEditor")
                            if not tag_editor:
                                continue
                            actions = []
                            pair_actions_container = None
                            for j in range(pair_widget.layout().count()):
                                subitem = pair_widget.layout().itemAt(j)
                                if subitem and subitem.widget() and isinstance(subitem.widget(), QWidget):
                                    potential_container = subitem.widget()
                                    if potential_container.layout() and potential_container.findChild(QComboBox, "PairActionTypeSelector"):
                                        pair_actions_container = potential_container
                                        break
                            if pair_actions_container and pair_actions_container.layout():
                                layout = pair_actions_container.layout()
                                for k in range(layout.count()):
                                    action_row_item = layout.itemAt(k)
                                    if not action_row_item or not action_row_item.widget():
                                        continue
                                    action_row_widget = action_row_item.widget()
                                    type_selector = action_row_widget.findChild(QComboBox, "PairActionTypeSelector")
                                    if not type_selector:
                                        continue
                                    value_editor = action_row_widget.findChild(QTextEdit, "PairActionValueEditor")
                                    var_name_editor = action_row_widget.findChild(QLineEdit, "PairActionVarNameEditor")
                                    var_value_editor = action_row_widget.findChild(QLineEdit, "PairActionVarValueEditor")
                                    action_type = type_selector.currentText()
                                    action_obj = {"type": action_type}
                                    if action_type == "Change Actor Location":
                                        actor_input = action_row_widget.findChild(QLineEdit, "ChangeLocationActorInput")
                                        mode_adjacent_radio = action_row_widget.findChild(QRadioButton, "ChangeLocationAdjacentRadio")
                                        mode_fast_travel_radio = action_row_widget.findChild(QRadioButton, "ChangeLocationFastTravelRadio")
                                        mode_setting_radio = action_row_widget.findChild(QRadioButton, "ChangeLocationSettingRadio")
                                        target_setting_input = action_row_widget.findChild(QLineEdit, "ChangeLocationTargetSettingInput")
                                        advance_time_checkbox = action_row_widget.findChild(QCheckBox, "ChangeLocationAdvanceTimeCheckbox")
                                        
                                        if actor_input:
                                            action_obj["actor_name"] = actor_input.text()
                                        if mode_adjacent_radio and mode_adjacent_radio.isChecked():
                                            action_obj["location_mode"] = "Adjacent"
                                        elif mode_fast_travel_radio and mode_fast_travel_radio.isChecked():
                                            action_obj["location_mode"] = "Fast Travel"
                                        elif mode_setting_radio and mode_setting_radio.isChecked():
                                            action_obj["location_mode"] = "Setting"
                                            if target_setting_input:
                                                action_obj["target_setting"] = target_setting_input.text()
                                        else:
                                            action_obj["location_mode"] = "Setting"
                                            if target_setting_input:
                                                action_obj["target_setting"] = target_setting_input.text()
                                        if advance_time_checkbox:
                                            action_obj["advance_time"] = advance_time_checkbox.isChecked()
                                        else:
                                            action_obj["advance_time"] = True
                                        speed_multiplier_spinner = action_row_widget.findChild(QDoubleSpinBox, "ChangeLocationSpeedMultiplierSpinner")
                                        if speed_multiplier_spinner:
                                            action_obj["speed_multiplier"] = speed_multiplier_spinner.value()
                                        else:
                                            action_obj["speed_multiplier"] = 1.0
                                    elif action_type == "Set Var":
                                        if var_name_editor and var_value_editor:
                                            try:
                                                action_obj["var_name"] = var_name_editor.text().strip()
                                                action_obj["var_value"] = var_value_editor.text().strip()
                                                action_scope_global_radio = action_row_widget.findChild(QRadioButton, "ActionVarScopeGlobalRadio")
                                                action_scope_character_radio = action_row_widget.findChild(QRadioButton, "ActionVarScopeCharacterRadio")
                                                action_scope_scene_chars_radio = action_row_widget.findChild(QRadioButton, "ActionVarScopeSceneCharsRadio")
                                                action_scope_setting_radio = action_row_widget.findChild(QRadioButton, "ActionVarScopeSettingRadio")
                                                action_scope_player_radio = action_row_widget.findChild(QRadioButton, "ActionVarScopePlayerRadio")
                                                
                                                if action_scope_global_radio and action_scope_global_radio.isChecked():
                                                    action_obj["variable_scope"] = "Global"
                                                elif action_scope_scene_chars_radio and action_scope_scene_chars_radio.isChecked():
                                                    action_obj["variable_scope"] = "Scene Characters"
                                                elif action_scope_character_radio and action_scope_character_radio.isChecked():
                                                    action_obj["variable_scope"] = "Character"
                                                elif action_scope_player_radio and action_scope_player_radio.isChecked():
                                                    action_obj["variable_scope"] = "Player"
                                                elif action_scope_setting_radio and action_scope_setting_radio.isChecked():
                                                    action_obj["variable_scope"] = "Setting"
                                                else:
                                                    action_obj["variable_scope"] = "Global"
                                                operation_selector = action_row_widget.findChild(QComboBox, "SetVarOperationSelector")
                                                if operation_selector:
                                                    op_text = operation_selector.currentText().lower()
                                                    if op_text == "set":
                                                        action_obj["operation"] = "set"
                                                    elif op_text == "increment":
                                                        action_obj["operation"] = "increment"
                                                    elif op_text == "decrement":
                                                        action_obj["operation"] = "decrement"
                                                    elif op_text == "multiply":
                                                        action_obj["operation"] = "multiply"
                                                    elif op_text == "divide":
                                                        action_obj["operation"] = "divide"
                                                    elif op_text == "generate":
                                                        action_obj["operation"] = "generate"
                                                        generate_instructions_input = action_row_widget.findChild(QTextEdit, "GenerateInstructionsInput")
                                                        generate_user_msg_radio = action_row_widget.findChild(QRadioButton, "GenerateUserMsgRadio")
                                                        generate_full_convo_radio = action_row_widget.findChild(QRadioButton, "GenerateFullConvoRadio")
                                                        generate_mode_llm_radio = action_row_widget.findChild(QRadioButton, "GenerateModeLLMRadio")
                                                        current_generate_mode = "LLM"
                                                        if generate_mode_llm_radio and generate_mode_llm_radio.isChecked():
                                                            current_generate_mode = "LLM"
                                                        else:
                                                            current_generate_mode = "Random"
                                                        action_obj["generate_mode"] = current_generate_mode

                                                        if current_generate_mode == "LLM":
                                                            if generate_instructions_input:
                                                                action_obj["generate_instructions"] = generate_instructions_input.toPlainText().strip()
                                                            generate_context = "Last Exchange"
                                                            if generate_user_msg_radio and generate_user_msg_radio.isChecked():
                                                                generate_context = "User Message"
                                                            elif generate_full_convo_radio and generate_full_convo_radio.isChecked():
                                                                generate_context = "Full Conversation"
                                                            action_obj["generate_context"] = generate_context
                                                        elif current_generate_mode == "Random":
                                                            random_type_combo = action_row_widget.findChild(QComboBox, "RandomTypeCombo")
                                                            if random_type_combo:
                                                                random_type = random_type_combo.currentText()
                                                                action_obj["random_type"] = random_type

                                                                if random_type == "Number":
                                                                    min_spin = action_row_widget.findChild(QLineEdit, "RandomNumberMin")
                                                                    max_spin = action_row_widget.findChild(QLineEdit, "RandomNumberMax")
                                                                    if min_spin: action_obj["random_number_min"] = min_spin.text()
                                                                    if max_spin: action_obj["random_number_max"] = max_spin.text()
                                                                elif random_type == "Setting":
                                                                    setting_filter_input = action_row_widget.findChild(QLineEdit, "SettingFilterInput")
                                                                    if setting_filter_input:
                                                                        filter_text = setting_filter_input.text().strip()
                                                                        filters = []
                                                                        if filter_text:
                                                                            filters = [f.strip() for f in filter_text.split(',') if f.strip()]
                                                                        action_obj["random_setting_filters"] = filters
                                                                elif random_type == "Character":
                                                                    character_filter_input = action_row_widget.findChild(QLineEdit, "CharacterFilterInput")
                                                                    if character_filter_input:
                                                                        filter_text = character_filter_input.text().strip()
                                                                        filters = []
                                                                        if filter_text:
                                                                            filters = [f.strip() for f in filter_text.split(',') if f.strip()]
                                                                        action_obj["random_character_filters"] = filters
                                                    elif op_text == "from random list":
                                                        action_obj["operation"] = "from random list"
                                                        gen_input = action_row_widget.findChild(QLineEdit, "VarRandomListGeneratorInput")
                                                        if gen_input:
                                                            generator_name = gen_input.text().strip()
                                                            action_obj["random_list_generator"] = generator_name
                                                            line_edits = action_row_widget.findChildren(QLineEdit)
                                                            gen_input_by_placeholder = None
                                                            for i, le in enumerate(line_edits):
                                                                print(f"      {i+1}: {le.objectName() or 'no name'} - placeholder: {le.placeholderText()}")
                                                                if le.placeholderText() == "Enter generator name":
                                                                    gen_input_by_placeholder = le
                                                            
                                                            if gen_input_by_placeholder:
                                                                generator_name = gen_input_by_placeholder.text().strip()
                                                                action_obj["random_list_generator"] = generator_name
                                                            else:
                                                                action_obj["random_list_generator"] = ""
                                                        random_list_no_context_radio = action_row_widget.findChild(QRadioButton, "RandomListNoContextRadio")
                                                        random_list_last_exchange_radio = action_row_widget.findChild(QRadioButton, "RandomListLastExchangeRadio")
                                                        random_list_user_msg_radio = action_row_widget.findChild(QRadioButton, "RandomListUserMsgRadio")
                                                        random_list_full_convo_radio = action_row_widget.findChild(QRadioButton, "RandomListFullConvoRadio")
                                                        
                                                        random_list_context = "No Context"
                                                        if random_list_no_context_radio and random_list_no_context_radio.isChecked():
                                                            random_list_context = "No Context"
                                                        elif random_list_last_exchange_radio and random_list_last_exchange_radio.isChecked():
                                                            random_list_context = "Last Exchange"
                                                        elif random_list_user_msg_radio and random_list_user_msg_radio.isChecked():
                                                            random_list_context = "User Message"
                                                        elif random_list_full_convo_radio and random_list_full_convo_radio.isChecked():
                                                            random_list_context = "Full Conversation"
                                                        
                                                        action_obj["random_list_context"] = random_list_context
                                                    elif op_text == "from var":
                                                        action_obj["operation"] = "from var"
                                                        from_var_name_input = action_row_widget.findChild(QLineEdit, "FromVarNameInput")
                                                        if from_var_name_input:
                                                            source_var_name = from_var_name_input.text().strip()
                                                            action_obj["from_var_name"] = source_var_name
                                                        else:
                                                            action_obj["from_var_name"] = ""
                                                        from_var_scope_global_radio = action_row_widget.findChild(QRadioButton, "FromVarScopeGlobalRadio")
                                                        from_var_scope_player_radio = action_row_widget.findChild(QRadioButton, "FromVarScopePlayerRadio")
                                                        from_var_scope_character_radio = action_row_widget.findChild(QRadioButton, "FromVarScopeCharacterRadio")
                                                        from_var_scope_scene_chars_radio = action_row_widget.findChild(QRadioButton, "FromVarScopeSceneCharsRadio")
                                                        from_var_scope_setting_radio = action_row_widget.findChild(QRadioButton, "FromVarScopeSettingRadio")
                                                        
                                                        from_var_scope = "Global"
                                                        if from_var_scope_global_radio and from_var_scope_global_radio.isChecked():
                                                            from_var_scope = "Global"
                                                        elif from_var_scope_player_radio and from_var_scope_player_radio.isChecked():
                                                            from_var_scope = "Player"
                                                        elif from_var_scope_character_radio and from_var_scope_character_radio.isChecked():
                                                            from_var_scope = "Character"
                                                        elif from_var_scope_scene_chars_radio and from_var_scope_scene_chars_radio.isChecked():
                                                            from_var_scope = "Scene Characters"
                                                        elif from_var_scope_setting_radio and from_var_scope_setting_radio.isChecked():
                                                            from_var_scope = "Setting"
                                                        
                                                        action_obj["from_var_scope"] = from_var_scope
                                                    else:
                                                        action_obj["operation"] = "set"
                                                set_var_prepend_radio = action_row_widget.findChild(QRadioButton, "SetVarPrependRadio")
                                                set_var_replace_radio = action_row_widget.findChild(QRadioButton, "SetVarReplaceRadio")
                                                set_var_append_radio = action_row_widget.findChild(QRadioButton, "SetVarAppendRadio")
                                                set_var_delimiter_input = action_row_widget.findChild(QLineEdit, "SetVarDelimiterInput")
                                                
                                                if set_var_prepend_radio and set_var_prepend_radio.isChecked():
                                                    action_obj["set_var_mode"] = "prepend"
                                                elif set_var_append_radio and set_var_append_radio.isChecked():
                                                    action_obj["set_var_mode"] = "append"
                                                else:
                                                    action_obj["set_var_mode"] = "replace"
                                                if set_var_delimiter_input:
                                                    delimiter = set_var_delimiter_input.text()
                                                    if delimiter:
                                                        action_obj["set_var_delimiter"] = delimiter
                                            except RuntimeError:
                                                pass
                                    elif action_type == "Text Tag":
                                        if value_editor:
                                            try:
                                                action_obj["value"] = value_editor.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["value"] = ""
                                        tag_append_radio = action_row_widget.findChild(QRadioButton, "TagAppendRadio")
                                        tag_prepend_radio = action_row_widget.findChild(QRadioButton, "TagPrependRadio")
                                        if tag_append_radio and tag_append_radio.isChecked():
                                            action_obj["tag_mode"] = "append"
                                        elif tag_prepend_radio and tag_prepend_radio.isChecked():
                                            action_obj["tag_mode"] = "prepend"
                                        else:
                                            action_obj["tag_mode"] = "overwrite"
                                    elif action_type == "Delete Character":
                                        if value_editor:
                                            try:
                                                action_obj["target_character_name"] = value_editor.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["target_character_name"] = ""
                                        else:
                                            action_obj["target_character_name"] = ""
                                    elif action_type in ["Next Rule", "Switch Model", "Rewrite Post"]:
                                        if value_editor:
                                            try:
                                                action_obj["value"] = value_editor.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["value"] = ""
                                        if action_type == "Switch Model":
                                            temp_editor = action_row_widget.findChild(QLineEdit, "SwitchModelTempEditor")
                                            if temp_editor:
                                                try:
                                                    temp_value = temp_editor.text().strip()
                                                    if temp_value:
                                                        action_obj["temperature"] = temp_value
                                                except RuntimeError:
                                                    pass
                                    elif action_type == "Generate Character":
                                        instructions_editor = action_row_widget.findChild(QTextEdit, "GenerateCharacterInstructionsEditor")
                                        location_editor = action_row_widget.findChild(QLineEdit, "GenerateCharacterLocationEditor")
                                        attach_context_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterAttachContextCheckbox")
                                        create_new_radio = action_row_widget.findChild(QRadioButton, "GenerateCharacterCreateNewRadio")
                                        edit_existing_radio = action_row_widget.findChild(QRadioButton, "GenerateCharacterEditExistingRadio")
                                        game_dir_radio = action_row_widget.findChild(QRadioButton, "GenerateCharacterGameDirRadio")
                                        resources_dir_radio = action_row_widget.findChild(QRadioButton, "GenerateCharacterResourcesDirRadio")
                                        target_actor_editor = action_row_widget.findChild(QLineEdit, "GenerateCharacterTargetActorEditor")
                                        model_editor = action_row_widget.findChild(QLineEdit, "GenerateCharacterModelEditor")
                                        name_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterNameCheckbox")
                                        description_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterDescriptionCheckbox")
                                        personality_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterPersonalityCheckbox")
                                        appearance_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterAppearanceCheckbox")
                                        goals_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterGoalsCheckbox")
                                        story_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterStoryCheckbox")
                                        abilities_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterAbilitiesCheckbox")
                                        equipment_checkbox = action_row_widget.findChild(QCheckBox, "GenerateCharacterEquipmentCheckbox")
                                        
                                        if instructions_editor:
                                            try:
                                                action_obj["instructions"] = instructions_editor.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["instructions"] = ""
                                        if location_editor:
                                            try:
                                                action_obj["location"] = location_editor.text().strip()
                                            except RuntimeError:
                                                action_obj["location"] = ""
                                        if attach_context_checkbox:
                                            try:
                                                action_obj["attach_context"] = attach_context_checkbox.isChecked()
                                            except RuntimeError:
                                                action_obj["attach_context"] = False
                                        if edit_existing_radio and edit_existing_radio.isChecked():
                                            action_obj["generation_mode"] = "Edit Existing"
                                        else:
                                            action_obj["generation_mode"] = "Create New"
                                        if resources_dir_radio and resources_dir_radio.isChecked():
                                            action_obj["target_directory"] = "Resources"
                                        else:
                                            action_obj["target_directory"] = "Game"
                                        if target_actor_editor:
                                            try:
                                                action_obj["target_actor_name"] = target_actor_editor.text().strip()
                                            except RuntimeError:
                                                action_obj["target_actor_name"] = ""
                                        if model_editor:
                                            try:
                                                action_obj["model_override"] = model_editor.text().strip()
                                            except RuntimeError:
                                                action_obj["model_override"] = ""
                                        fields_to_generate = []
                                        field_checkboxes = [
                                            (name_checkbox, "name"),
                                            (description_checkbox, "description"),
                                            (personality_checkbox, "personality"),
                                            (appearance_checkbox, "appearance"),
                                            (goals_checkbox, "goals"),
                                            (story_checkbox, "story"),
                                            (abilities_checkbox, "abilities"),
                                            (equipment_checkbox, "equipment")
                                        ]
                                        
                                        for checkbox, field_name in field_checkboxes:
                                            if checkbox:
                                                try:
                                                    if checkbox.isChecked():
                                                        fields_to_generate.append(field_name)
                                                except RuntimeError:
                                                    pass
                                        
                                        action_obj["fields_to_generate"] = fields_to_generate
                                        if not fields_to_generate:
                                            action_obj["fields_to_generate"] = ["name", "description", "personality", "appearance", "goals", "story", "abilities", "equipment"]
                                    elif action_type == "Generate Random List":
                                        mode_new_radio = action_row_widget.findChild(QRadioButton, "GenRandomListNewRadio")
                                        mode_permutate_radio = action_row_widget.findChild(QRadioButton, "GenRandomListPermutateRadio")
                                        name_input = action_row_widget.findChild(QLineEdit, "GenRandomListNameInput")
                                        instructions_input = action_row_widget.findChild(QTextEdit, "GenRandomListInstructionsInput")
                                        objects_checkbox = action_row_widget.findChild(QCheckBox, "GenRandomListObjectsCheckbox")
                                        weights_checkbox = action_row_widget.findChild(QCheckBox, "GenRandomListWeightsCheckbox")
                                        model_input = action_row_widget.findChild(QLineEdit, "GenRandomListModelInput")
                                        var_name_input = action_row_widget.findChild(QLineEdit, "GenRandomListVarNameInput")
                                        var_scope_global_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarScopeGlobalRadio")
                                        var_scope_player_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarScopePlayerRadio")
                                        var_scope_character_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarScopeCharacterRadio")
                                        var_scope_setting_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarScopeSettingRadio")
                                        var_scope_scene_chars_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarScopeSceneCharsRadio")
                                        is_permutate = mode_permutate_radio.isChecked() if mode_permutate_radio else False
                                        generator_name = name_input.text().strip() if name_input else ""
                                        instructions = instructions_input.toPlainText().strip() if instructions_input else ""
                                        permutate_objects = objects_checkbox.isChecked() if objects_checkbox else False
                                        permutate_weights = weights_checkbox.isChecked() if weights_checkbox else False
                                        model_override = model_input.text().strip() if model_input else ""
                                        var_name = var_name_input.text().strip() if var_name_input else ""
                                        var_scope = "Global"
                                        if var_scope_global_radio and var_scope_global_radio.isChecked():
                                            var_scope = "Global"
                                        elif var_scope_player_radio and var_scope_player_radio.isChecked():
                                            var_scope = "Player"
                                        elif var_scope_character_radio and var_scope_character_radio.isChecked():
                                            var_scope = "Character"
                                        elif var_scope_setting_radio and var_scope_setting_radio.isChecked():
                                            var_scope = "Setting"
                                        elif var_scope_scene_chars_radio and var_scope_scene_chars_radio.isChecked():
                                            var_scope = "Scene Characters"
                                        context_no_context_radio = action_row_widget.findChild(QRadioButton, "GenRandomListNoContextRadio")
                                        context_last_exchange_radio = action_row_widget.findChild(QRadioButton, "GenRandomListLastExchangeRadio")
                                        context_user_msg_radio = action_row_widget.findChild(QRadioButton, "GenRandomListUserMsgRadio")
                                        context_full_convo_radio = action_row_widget.findChild(QRadioButton, "GenRandomListFullConvoRadio")
                                        context = "No Context"
                                        if context_no_context_radio and context_no_context_radio.isChecked():
                                            context = "No Context"
                                        elif context_last_exchange_radio and context_last_exchange_radio.isChecked():
                                            context = "Last Exchange"
                                        elif context_user_msg_radio and context_user_msg_radio.isChecked():
                                            context = "User Message"
                                        elif context_full_convo_radio and context_full_convo_radio.isChecked():
                                            context = "Full Conversation"
                                        action_obj["generator_name"] = generator_name
                                        action_obj["instructions"] = instructions
                                        action_obj["is_permutate"] = is_permutate
                                        action_obj["permutate_objects"] = permutate_objects if is_permutate else False
                                        action_obj["permutate_weights"] = permutate_weights if is_permutate else False
                                        action_obj["model_override"] = model_override if model_override else None
                                        action_obj["var_name"] = var_name
                                        action_obj["var_scope"] = var_scope
                                        action_obj["generate_context"] = context
                                        
                                        var_mode_prepend_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarModePrependRadio")
                                        var_mode_replace_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarModeReplaceRadio")
                                        var_mode_append_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarModeAppendRadio")
                                        var_mode_delimiter_input = action_row_widget.findChild(QLineEdit, "GenRandomListVarModeDelimiterInput")
                                        
                                        var_mode = "replace"
                                        if var_mode_prepend_radio and var_mode_prepend_radio.isChecked():
                                            var_mode = "prepend"
                                        elif var_mode_append_radio and var_mode_append_radio.isChecked():
                                            var_mode = "append"
                                        
                                        action_obj["var_mode"] = var_mode
                                        action_obj["var_delimiter"] = var_mode_delimiter_input.text().strip() if var_mode_delimiter_input else "/"
                                        
                                        var_format_comma_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarFormatCommaRadio")
                                        var_format_space_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarFormatSpaceRadio")
                                        var_format_custom_radio = action_row_widget.findChild(QRadioButton, "GenRandomListVarFormatCustomRadio")
                                        var_format_custom_input = action_row_widget.findChild(QLineEdit, "GenRandomListVarFormatCustomInput")
                                        
                                        var_format = "comma"
                                        if var_format_space_radio and var_format_space_radio.isChecked():
                                            var_format = "space"
                                        elif var_format_custom_radio and var_format_custom_radio.isChecked():
                                            var_format = "custom"
                                        
                                        action_obj["var_format"] = var_format
                                        action_obj["var_format_separator"] = var_format_custom_input.text().strip() if var_format_custom_input else " "
                                    elif action_type == "Force Narrator":
                                        fn_order_first_radio = action_row_widget.findChild(QRadioButton, "ForceNarratorOrderFirstRadio")
                                        fn_order_last_radio = action_row_widget.findChild(QRadioButton, "ForceNarratorOrderLastRadio")
                                        fn_sys_msg_editor = action_row_widget.findChild(QTextEdit, "ForceNarratorSysMsgEditor")
                                        if fn_order_first_radio and fn_order_last_radio:
                                            try:
                                                force_order = "First" if fn_order_first_radio.isChecked() else "Last"
                                                action_obj["force_narrator_order"] = force_order
                                            except RuntimeError:
                                                action_obj["force_narrator_order"] = "First"
                                                
                                        if fn_sys_msg_editor:
                                            try:
                                                action_obj["force_narrator_system_message"] = fn_sys_msg_editor.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["force_narrator_system_message"] = ""
                                    elif action_type == "Set Screen Effect":
                                        effect_type_combo = action_row_widget.findChild(QComboBox, "ScreenEffectTypeCombo")
                                        effect_operation_combo = action_row_widget.findChild(QComboBox, "ScreenEffectOperationCombo")
                                        param_name_combo = action_row_widget.findChild(QComboBox, "ScreenEffectParamNameCombo")
                                        param_value_input = action_row_widget.findChild(QLineEdit, "ScreenEffectParamValueInput")
                                        enable_combo = action_row_widget.findChild(QComboBox, "ScreenEffectEnabledCombo")
                                        if effect_type_combo and param_name_combo and param_value_input:
                                            try:
                                                action_obj["effect_type"] = effect_type_combo.currentText()
                                                action_obj["operation"] = effect_operation_combo.currentText().lower()
                                                param_name_text = param_name_combo.currentText()
                                                action_obj["param_name"] = param_name_text
                                                if action_obj["effect_type"] == "Flicker" and param_name_text == "color":
                                                    flicker_color_widget = action_row_widget.findChild(QComboBox, "ScreenEffectFlickerColorCombo")
                                                    if flicker_color_widget:
                                                        action_obj["param_value"] = flicker_color_widget.currentText()
                                                    else:
                                                        action_obj["param_value"] = param_value_input.text().strip()
                                                else:
                                                    action_obj["param_value"] = param_value_input.text().strip()
                                                action_obj["enabled"] = enable_combo.currentText() == "True"
                                                print(f"    [DEBUG] Set Screen Effect: type={action_obj['effect_type']}, "
                                                      f"operation={action_obj['operation']}, param={action_obj['param_name']}, "
                                                      f"value={action_obj['param_value']}, enabled={action_obj['enabled']}")
                                            except RuntimeError:
                                                pass
                                    elif action_type == "Change Brightness":
                                        brightness_input = action_row_widget.findChild(QLineEdit, "BrightnessInput")
                                        if brightness_input:
                                            try:
                                                brightness_value = brightness_input.text().strip()
                                                if brightness_value:
                                                    try:
                                                        float(brightness_value)
                                                        action_obj["brightness"] = brightness_value
                                                    except ValueError:
                                                        continue
                                                else:
                                                    action_obj["brightness"] = "1.0"
                                            except RuntimeError:
                                                action_obj["brightness"] = "1.0"
                                    elif action_type == "Skip Post":
                                        pass
                                    elif action_type == "Exit Rule Processing":
                                        pass
                                    elif action_type == "Game Over":
                                        game_over_message_input = action_row_widget.findChild(QTextEdit, "GameOverMessageInput")
                                        if game_over_message_input:
                                            try:
                                                action_obj["game_over_message"] = game_over_message_input.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["game_over_message"] = ""
                                        else:
                                            action_obj["game_over_message"] = ""
                                    elif action_type == "Move Item":
                                        move_item_name_input = action_row_widget.findChild(QLineEdit, "MoveItemNameInput")
                                        move_item_quantity_input = action_row_widget.findChild(QLineEdit, "MoveItemQuantityInput")
                                        move_item_from_setting_radio = action_row_widget.findChild(QRadioButton, "MoveItemFromSettingRadio")
                                        move_item_from_character_radio = action_row_widget.findChild(QRadioButton, "MoveItemFromCharacterRadio")
                                        move_item_from_name_input = action_row_widget.findChild(QLineEdit, "MoveItemFromNameInput")
                                        move_item_to_setting_radio = action_row_widget.findChild(QRadioButton, "MoveItemToSettingRadio")
                                        move_item_to_character_radio = action_row_widget.findChild(QRadioButton, "MoveItemToCharacterRadio")
                                        move_item_to_name_input = action_row_widget.findChild(QLineEdit, "MoveItemToNameInput")
                                        if move_item_name_input:
                                            try:
                                                action_obj["item_name"] = move_item_name_input.text().strip()
                                            except RuntimeError:
                                                action_obj["item_name"] = ""
                                        if move_item_quantity_input:
                                            try:
                                                action_obj["quantity"] = move_item_quantity_input.text().strip()
                                            except RuntimeError:
                                                action_obj["quantity"] = "1"
                                        else:
                                            action_obj["quantity"] = "1"
                                        from_type = "Setting"
                                        if move_item_from_setting_radio and move_item_from_character_radio:
                                            try:
                                                if move_item_from_character_radio.isChecked():
                                                    from_type = "Character"
                                            except RuntimeError:
                                                from_type = "Setting"
                                        action_obj["from_type"] = from_type
                                        if move_item_from_name_input:
                                            try:
                                                action_obj["from_name"] = move_item_from_name_input.text().strip()
                                            except RuntimeError:
                                                action_obj["from_name"] = ""
                                        else:
                                            action_obj["from_name"] = ""
                                        to_type = "Setting"
                                        if move_item_to_setting_radio and move_item_to_character_radio:
                                            try:
                                                if move_item_to_character_radio.isChecked():
                                                    to_type = "Character"
                                            except RuntimeError:
                                                to_type = "Setting"
                                        action_obj["to_type"] = to_type
                                        if move_item_to_name_input:
                                            try:
                                                action_obj["to_name"] = move_item_to_name_input.text().strip()
                                            except RuntimeError:
                                                action_obj["to_name"] = ""
                                        else:
                                            action_obj["to_name"] = ""
                                        
                                        move_item_from_container_checkbox = action_row_widget.findChild(QCheckBox, "MoveItemFromContainerCheckbox")
                                        move_item_from_item_name_input = action_row_widget.findChild(QLineEdit, "MoveItemFromItemNameInput")
                                        move_item_from_container_name_input = action_row_widget.findChild(QLineEdit, "MoveItemFromContainerNameInput")
                                        
                                        if move_item_from_container_checkbox and move_item_from_container_checkbox.isChecked():
                                            action_obj["from_container_enabled"] = True
                                            if move_item_from_item_name_input:
                                                try:
                                                    action_obj["from_item_name"] = move_item_from_item_name_input.text().strip()
                                                except RuntimeError:
                                                    action_obj["from_item_name"] = ""
                                            else:
                                                action_obj["from_item_name"] = ""
                                            if move_item_from_container_name_input:
                                                try:
                                                    action_obj["from_container_name"] = move_item_from_container_name_input.text().strip()
                                                except RuntimeError:
                                                    action_obj["from_container_name"] = ""
                                            else:
                                                action_obj["from_container_name"] = ""
                                        else:
                                            action_obj["from_container_enabled"] = False
                                            action_obj["from_item_name"] = ""
                                            action_obj["from_container_name"] = ""
                                        
                                        move_item_to_container_checkbox = action_row_widget.findChild(QCheckBox, "MoveItemToContainerCheckbox")
                                        move_item_to_item_name_input = action_row_widget.findChild(QLineEdit, "MoveItemToItemNameInput")
                                        move_item_to_container_name_input = action_row_widget.findChild(QLineEdit, "MoveItemToContainerNameInput")
                                        
                                        if move_item_to_container_checkbox and move_item_to_container_checkbox.isChecked():
                                            action_obj["to_container_enabled"] = True
                                            if move_item_to_item_name_input:
                                                try:
                                                    action_obj["to_item_name"] = move_item_to_item_name_input.text().strip()
                                                except RuntimeError:
                                                    action_obj["to_item_name"] = ""
                                            else:
                                                action_obj["to_item_name"] = ""
                                            if move_item_to_container_name_input:
                                                try:
                                                    action_obj["to_container_name"] = move_item_to_container_name_input.text().strip()
                                                except RuntimeError:
                                                    action_obj["to_container_name"] = ""
                                            else:
                                                action_obj["to_container_name"] = ""
                                        else:
                                            action_obj["to_container_enabled"] = False
                                            action_obj["to_item_name"] = ""
                                            action_obj["to_container_name"] = ""
                                    elif action_type == "Add Item":
                                        add_item_name_input = action_row_widget.findChild(QLineEdit, "AddItemNameInput")
                                        add_item_quantity_input = action_row_widget.findChild(QLineEdit, "AddItemQuantityInput")
                                        add_item_generate_checkbox = action_row_widget.findChild(QCheckBox, "AddItemGenerateCheckbox")
                                        add_item_owner_input = action_row_widget.findChild(QLineEdit, "AddItemOwnerInput")
                                        add_item_description_input = action_row_widget.findChild(QLineEdit, "AddItemDescriptionInput")
                                        add_item_description_generate_checkbox = action_row_widget.findChild(QCheckBox, "AddItemDescriptionGenerateCheckbox")
                                        add_item_location_input = action_row_widget.findChild(QLineEdit, "AddItemLocationInput")
                                        add_item_location_generate_checkbox = action_row_widget.findChild(QCheckBox, "AddItemLocationGenerateCheckbox")
                                        add_item_generate_instructions_editor = action_row_widget.findChild(QTextEdit, "AddItemGenerateInstructionsEditor")
                                        add_item_attach_scene_context_checkbox = action_row_widget.findChild(QCheckBox, "AddItemAttachSceneContextCheckbox")
                                        add_item_attach_location_desc_checkbox = action_row_widget.findChild(QCheckBox, "AddItemAttachLocationDescCheckbox")
                                        add_item_attach_character_desc_checkbox = action_row_widget.findChild(QCheckBox, "AddItemAttachCharacterDescCheckbox")
                                        add_item_target_setting_radio = action_row_widget.findChild(QRadioButton, "AddItemTargetSettingRadio")
                                        add_item_target_character_radio = action_row_widget.findChild(QRadioButton, "AddItemTargetCharacterRadio")
                                        add_item_target_name_input = action_row_widget.findChild(QLineEdit, "AddItemTargetNameInput")
                                        
                                        if add_item_name_input:
                                            try:
                                                action_obj["item_name"] = add_item_name_input.text().strip()
                                            except RuntimeError:
                                                action_obj["item_name"] = ""
                                        if add_item_quantity_input:
                                            try:
                                                action_obj["quantity"] = add_item_quantity_input.text().strip()
                                            except RuntimeError:
                                                action_obj["quantity"] = "1"
                                        else:
                                            action_obj["quantity"] = "1"
                                        
                                        if add_item_generate_checkbox:
                                            try:
                                                action_obj["generate"] = add_item_generate_checkbox.isChecked()
                                            except RuntimeError:
                                                action_obj["generate"] = False
                                        else:
                                            action_obj["generate"] = False
                                        
                                        if add_item_owner_input:
                                            try:
                                                action_obj["owner"] = add_item_owner_input.text().strip()
                                            except RuntimeError:
                                                action_obj["owner"] = ""
                                        else:
                                            action_obj["owner"] = ""
                                        
                                        if add_item_description_input:
                                            try:
                                                action_obj["description"] = add_item_description_input.text().strip()
                                            except RuntimeError:
                                                action_obj["description"] = ""
                                        else:
                                            action_obj["description"] = ""
                                        
                                        if add_item_location_input:
                                            try:
                                                action_obj["location"] = add_item_location_input.text().strip()
                                            except RuntimeError:
                                                action_obj["location"] = ""
                                        else:
                                            action_obj["location"] = ""
                                        
                                        if add_item_description_generate_checkbox:
                                            try:
                                                action_obj["generate_description"] = add_item_description_generate_checkbox.isChecked()
                                            except RuntimeError:
                                                action_obj["generate_description"] = False
                                        else:
                                            action_obj["generate_description"] = False
                                        
                                        if add_item_location_generate_checkbox:
                                            try:
                                                action_obj["generate_location"] = add_item_location_generate_checkbox.isChecked()
                                            except RuntimeError:
                                                action_obj["generate_location"] = False
                                        else:
                                            action_obj["generate_location"] = False
                                        
                                        if add_item_generate_instructions_editor:
                                            try:
                                                action_obj["generate_instructions"] = add_item_generate_instructions_editor.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["generate_instructions"] = ""
                                        else:
                                            action_obj["generate_instructions"] = ""
                                        
                                        if add_item_attach_scene_context_checkbox:
                                            try:
                                                action_obj["attach_scene_context"] = add_item_attach_scene_context_checkbox.isChecked()
                                            except RuntimeError:
                                                action_obj["attach_scene_context"] = False
                                        else:
                                            action_obj["attach_scene_context"] = False
                                        
                                        if add_item_attach_location_desc_checkbox:
                                            try:
                                                action_obj["attach_location_desc"] = add_item_attach_location_desc_checkbox.isChecked()
                                            except RuntimeError:
                                                action_obj["attach_location_desc"] = False
                                        else:
                                            action_obj["attach_location_desc"] = False
                                        
                                        if add_item_attach_character_desc_checkbox:
                                            try:
                                                action_obj["attach_character_desc"] = add_item_attach_character_desc_checkbox.isChecked()
                                            except RuntimeError:
                                                action_obj["attach_character_desc"] = False
                                        else:
                                            action_obj["attach_character_desc"] = False
                                        
                                        if add_item_target_setting_radio:
                                            try:
                                                if add_item_target_setting_radio.isChecked():
                                                    action_obj["target_type"] = "Setting"
                                                else:
                                                    action_obj["target_type"] = "Character"
                                            except RuntimeError:
                                                action_obj["target_type"] = "Setting"
                                        else:
                                            action_obj["target_type"] = "Setting"
                                        
                                        if add_item_target_name_input:
                                            try:
                                                action_obj["target_name"] = add_item_target_name_input.text().strip()
                                            except RuntimeError:
                                                action_obj["target_name"] = ""
                                        else:
                                            action_obj["target_name"] = ""
                                        
                                        add_item_target_container_checkbox = action_row_widget.findChild(QCheckBox, "AddItemTargetContainerCheckbox")
                                        add_item_target_item_name_input = action_row_widget.findChild(QLineEdit, "AddItemTargetItemNameInput")
                                        add_item_target_container_name_input = action_row_widget.findChild(QLineEdit, "AddItemTargetContainerNameInput")
                                        
                                        if add_item_target_container_checkbox and add_item_target_container_checkbox.isChecked():
                                            action_obj["target_container_enabled"] = True
                                            if add_item_target_item_name_input:
                                                try:
                                                    action_obj["target_item_name"] = add_item_target_item_name_input.text().strip()
                                                except RuntimeError:
                                                    action_obj["target_item_name"] = ""
                                            else:
                                                action_obj["target_item_name"] = ""
                                            if add_item_target_container_name_input:
                                                try:
                                                    action_obj["target_container_name"] = add_item_target_container_name_input.text().strip()
                                                except RuntimeError:
                                                    action_obj["target_container_name"] = ""
                                            else:
                                                action_obj["target_container_name"] = ""
                                        else:
                                            action_obj["target_container_enabled"] = False
                                            action_obj["target_item_name"] = ""
                                            action_obj["target_container_name"] = ""
                                    elif action_type == "Remove Item":
                                        remove_item_name_input = action_row_widget.findChild(QLineEdit, "RemoveItemNameInput")
                                        remove_item_quantity_input = action_row_widget.findChild(QLineEdit, "RemoveItemQuantityInput")
                                        remove_item_target_setting_radio = action_row_widget.findChild(QRadioButton, "RemoveItemTargetSettingRadio")
                                        remove_item_target_character_radio = action_row_widget.findChild(QRadioButton, "RemoveItemTargetCharacterRadio")
                                        remove_item_target_name_input = action_row_widget.findChild(QLineEdit, "RemoveItemTargetNameInput")
                                        
                                        if remove_item_name_input:
                                            try:
                                                action_obj["item_name"] = remove_item_name_input.text().strip()
                                            except RuntimeError:
                                                action_obj["item_name"] = ""
                                        if remove_item_quantity_input:
                                            try:
                                                action_obj["quantity"] = remove_item_quantity_input.text().strip()
                                            except RuntimeError:
                                                action_obj["quantity"] = "1"
                                        else:
                                            action_obj["quantity"] = "1"
                                        
                                        target_type = "Setting"
                                        if remove_item_target_setting_radio and remove_item_target_character_radio:
                                            try:
                                                if remove_item_target_character_radio.isChecked():
                                                    target_type = "Character"
                                            except RuntimeError:
                                                target_type = "Setting"
                                        action_obj["target_type"] = target_type
                                        
                                        if remove_item_target_name_input:
                                            try:
                                                action_obj["target_name"] = remove_item_target_name_input.text().strip()
                                            except RuntimeError:
                                                action_obj["target_name"] = ""
                                        else:
                                            action_obj["target_name"] = ""
                                        
                                        remove_item_target_container_checkbox = action_row_widget.findChild(QCheckBox, "RemoveItemTargetContainerCheckbox")
                                        remove_item_target_item_name_input = action_row_widget.findChild(QLineEdit, "RemoveItemTargetItemNameInput")
                                        remove_item_target_container_name_input = action_row_widget.findChild(QLineEdit, "RemoveItemTargetContainerNameInput")
                                        
                                        if remove_item_target_container_checkbox and remove_item_target_container_checkbox.isChecked():
                                            action_obj["target_container_enabled"] = True
                                            if remove_item_target_item_name_input:
                                                try:
                                                    action_obj["target_item_name"] = remove_item_target_item_name_input.text().strip()
                                                except RuntimeError:
                                                    action_obj["target_item_name"] = ""
                                            else:
                                                action_obj["target_item_name"] = ""
                                            if remove_item_target_container_name_input:
                                                try:
                                                    action_obj["target_container_name"] = remove_item_target_container_name_input.text().strip()
                                                except RuntimeError:
                                                    action_obj["target_container_name"] = ""
                                            else:
                                                action_obj["target_container_name"] = ""
                                        else:
                                            action_obj["target_container_enabled"] = False
                                            action_obj["target_item_name"] = ""
                                            action_obj["target_container_name"] = ""
                                        
                                        remove_item_consume_checkbox = action_row_widget.findChild(QCheckBox, "RemoveItemConsumeCheckbox")
                                        remove_item_consume_player_radio = action_row_widget.findChild(QRadioButton, "RemoveItemConsumePlayerRadio")
                                        remove_item_consume_setting_radio = action_row_widget.findChild(QRadioButton, "RemoveItemConsumeSettingRadio")
                                        remove_item_consume_character_radio = action_row_widget.findChild(QRadioButton, "RemoveItemConsumeCharacterRadio")
                                        remove_item_consume_scene_chars_radio = action_row_widget.findChild(QRadioButton, "RemoveItemConsumeSceneCharsRadio")
                                        
                                        if remove_item_consume_checkbox:
                                            try:
                                                action_obj["consume"] = remove_item_consume_checkbox.isChecked()
                                            except RuntimeError:
                                                action_obj["consume"] = False
                                        else:
                                            action_obj["consume"] = False
                                        
                                        if action_obj.get("consume", False):
                                            consume_scope = "Player"
                                            if remove_item_consume_setting_radio and remove_item_consume_setting_radio.isChecked():
                                                consume_scope = "Setting"
                                            elif remove_item_consume_character_radio and remove_item_consume_character_radio.isChecked():
                                                consume_scope = "Character"
                                            elif remove_item_consume_scene_chars_radio and remove_item_consume_scene_chars_radio.isChecked():
                                                consume_scope = "Scene Characters"
                                            action_obj["consume_scope"] = consume_scope
                                        else:
                                            action_obj["consume_scope"] = "Player"
                                    elif action_type == "Determine Items":
                                        determine_items_player_radio = action_row_widget.findChild(QRadioButton, "DetermineItemPlayerRadio")
                                        determine_items_character_radio = action_row_widget.findChild(QRadioButton, "DetermineItemCharacterRadio")
                                        determine_items_setting_radio = action_row_widget.findChild(QRadioButton, "DetermineItemSettingRadio")
                                        determine_items_single_item_radio = action_row_widget.findChild(QRadioButton, "DetermineItemsSingleItemRadio")
                                        determine_items_multiple_items_radio = action_row_widget.findChild(QRadioButton, "DetermineItemsMultipleItemsRadio")
                                        determine_items_owner_input = action_row_widget.findChild(QLineEdit, "DetermineItemOwnerInput")
                                        determine_items_description_input = action_row_widget.findChild(QLineEdit, "DetermineItemsDescriptionInput")
                                        determine_items_location_input = action_row_widget.findChild(QLineEdit, "DetermineItemsLocationInput")
                                        determine_items_text_input = action_row_widget.findChild(QTextEdit, "DetermineItemsTextInput")
                                        determine_items_full_convo_radio = action_row_widget.findChild(QRadioButton, "DetermineItemsFullConvoRadio")
                                        determine_items_user_msg_radio = action_row_widget.findChild(QRadioButton, "DetermineItemsUserMsgRadio")
                                        determine_items_llm_reply_radio = action_row_widget.findChild(QRadioButton, "DetermineItemsLlmReplyRadio")
                                        determine_items_convo_llm_radio = action_row_widget.findChild(QRadioButton, "DetermineItemsConvoLlmRadio")
                                        
                                        scope = "Player"
                                        if determine_items_character_radio and determine_items_character_radio.isChecked():
                                            scope = "Character"
                                        elif determine_items_setting_radio and determine_items_setting_radio.isChecked():
                                            scope = "Setting"
                                        action_obj["scope"] = scope
                                        
                                        return_type = "Single Item"
                                        if determine_items_multiple_items_radio and determine_items_multiple_items_radio.isChecked():
                                            return_type = "Multiple Items"
                                        action_obj["return_type"] = return_type
                                        
                                        if determine_items_owner_input:
                                            try:
                                                action_obj["owner"] = determine_items_owner_input.text().strip()
                                            except RuntimeError:
                                                action_obj["owner"] = ""
                                        else:
                                            action_obj["owner"] = ""
                                        
                                        if determine_items_description_input:
                                            try:
                                                action_obj["description"] = determine_items_description_input.text().strip()
                                            except RuntimeError:
                                                action_obj["description"] = ""
                                        else:
                                            action_obj["description"] = ""
                                        
                                        if determine_items_location_input:
                                            try:
                                                action_obj["location"] = determine_items_location_input.text().strip()
                                            except RuntimeError:
                                                action_obj["location"] = ""
                                        else:
                                            action_obj["location"] = ""
                                        
                                        if determine_items_text_input:
                                            try:
                                                action_obj["text"] = determine_items_text_input.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["text"] = ""
                                        else:
                                            action_obj["text"] = ""
                                        
                                        text_scope = "Full Conversation"
                                        if determine_items_user_msg_radio and determine_items_user_msg_radio.isChecked():
                                            text_scope = "User Message"
                                        elif determine_items_llm_reply_radio and determine_items_llm_reply_radio.isChecked():
                                            text_scope = "LLM Reply"
                                        elif determine_items_convo_llm_radio and determine_items_convo_llm_radio.isChecked():
                                            text_scope = "Conversation plus LLM Reply"
                                        action_obj["text_scope"] = text_scope
                                    elif action_type == "Post Visibility":
                                        current_post_radio = action_row_widget.findChild(QRadioButton, "PostVisibilityCurrentPostRadio")
                                        player_post_radio = action_row_widget.findChild(QRadioButton, "PostVisibilityPlayerPostRadio")
                                        visible_only_radio = action_row_widget.findChild(QRadioButton, "PostVisibilityVisibleOnlyRadio")
                                        not_visible_radio = action_row_widget.findChild(QRadioButton, "PostVisibilityNotVisibleRadio")
                                        name_match_radio = action_row_widget.findChild(QRadioButton, "PostVisibilityNameMatchRadio")
                                        variable_radio = action_row_widget.findChild(QRadioButton, "PostVisibilityVariableRadio")
                                        if current_post_radio and current_post_radio.isChecked():
                                            action_obj["applies_to"] = "Current Post"
                                        elif player_post_radio and player_post_radio.isChecked():
                                            action_obj["applies_to"] = "Player Post"
                                        else:
                                            action_obj["applies_to"] = "Current Post"
                                        if visible_only_radio and visible_only_radio.isChecked():
                                            action_obj["visibility_mode"] = "Visible Only To"
                                        elif not_visible_radio and not_visible_radio.isChecked():
                                            action_obj["visibility_mode"] = "Not Visible To"
                                        else:
                                            action_obj["visibility_mode"] = "Visible Only To"
                                        if name_match_radio and name_match_radio.isChecked():
                                            action_obj["condition_type"] = "Name Match"
                                        elif variable_radio and variable_radio.isChecked():
                                            action_obj["condition_type"] = "Variable"
                                        else:
                                            action_obj["condition_type"] = "Name Match"
                                        conditions = []
                                        conditions_container = action_row_widget.findChild(QWidget, "PostVisibilityConditionsContainer")
                                        if conditions_container and conditions_container.layout():
                                            for i in range(conditions_container.layout().count()):
                                                condition_widget = conditions_container.layout().itemAt(i).widget()
                                                if condition_widget and condition_widget.objectName() == "PostVisibilityConditionRow":
                                                    name_input = condition_widget.findChild(QLineEdit, "PostVisibilityNameInput")
                                                    if name_input and name_input.isVisible():
                                                        name_value = name_input.text().strip()
                                                        if name_value:
                                                            name_condition_data = {
                                                                "type": "Name Match",
                                                                "name": name_value
                                                            }
                                                            conditions.append(name_condition_data)
                                                    var_name_input = condition_widget.findChild(QLineEdit, "PostVisibilityVarNameInput")
                                                    operator_combo = condition_widget.findChild(QComboBox, "PostVisibilityOperatorCombo")
                                                    var_value_input = condition_widget.findChild(QLineEdit, "PostVisibilityVarValueInput")
                                                    
                                                    if var_name_input and var_name_input.isVisible():
                                                        var_name = var_name_input.text().strip()
                                                        operator = operator_combo.currentText() if operator_combo else "equals"
                                                        var_value = var_value_input.text().strip() if var_value_input else ""
                                                        var_scope = "Global"
                                                        var_scope_global_radio = condition_widget.findChild(QRadioButton, "PostVisibilityVarScopeGlobalRadio")
                                                        var_scope_player_radio = condition_widget.findChild(QRadioButton, "PostVisibilityVarScopePlayerRadio")
                                                        var_scope_character_radio = condition_widget.findChild(QRadioButton, "PostVisibilityVarScopeCharacterRadio")
                                                        var_scope_setting_radio = condition_widget.findChild(QRadioButton, "PostVisibilityVarScopeSettingRadio")
                                                        if var_scope_player_radio and var_scope_player_radio.isChecked():
                                                            var_scope = "Player"
                                                        elif var_scope_character_radio and var_scope_character_radio.isChecked():
                                                            var_scope = "Character"
                                                        elif var_scope_setting_radio and var_scope_setting_radio.isChecked():
                                                            var_scope = "Setting"
                                                        if var_name:
                                                            var_condition_data = {
                                                                "type": "Variable",
                                                                "variable_name": var_name,
                                                                "operator": operator,
                                                                "value": var_value,
                                                                "variable_scope": var_scope
                                                            }
                                                            conditions.append(var_condition_data)
                                        
                                        action_obj["conditions"] = conditions
                                    elif action_type == "New Scene":
                                        pass
                                    elif action_type == "System Message":
                                        if value_editor:
                                            try:
                                                action_obj["value"] = value_editor.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["value"] = ""
                                        action_prepend_radio = action_row_widget.findChild(QRadioButton, "ActionPrependRadio")
                                        action_append_radio = action_row_widget.findChild(QRadioButton, "ActionAppendRadio")
                                        action_replace_radio = action_row_widget.findChild(QRadioButton, "ActionReplaceRadio")
                                        
                                        if action_prepend_radio and action_prepend_radio.isChecked():
                                            action_obj["position"] = "prepend"
                                        elif action_append_radio and action_append_radio.isChecked():
                                            action_obj["position"] = "append"
                                        elif action_replace_radio and action_replace_radio.isChecked():
                                            action_obj["position"] = "replace"
                                        else:
                                            action_obj["position"] = "prepend"
                                        action_first_sysmsg_radio = action_row_widget.findChild(QRadioButton, "ActionFirstSysMsgRadio")
                                        action_last_sysmsg_radio = action_row_widget.findChild(QRadioButton, "ActionLastSysMsgRadio")
                                        
                                        if action_first_sysmsg_radio and action_first_sysmsg_radio.isChecked():
                                            action_obj["system_message_position"] = "first"
                                        elif action_last_sysmsg_radio and action_last_sysmsg_radio.isChecked():
                                            action_obj["system_message_position"] = "last"
                                        else:
                                            action_obj["system_message_position"] = "first"
                                    elif action_type == "Rewrite Post":
                                        if value_editor:
                                            try:
                                                action_obj["value"] = value_editor.toPlainText().strip()
                                            except RuntimeError:
                                                action_obj["value"] = ""
                                        rewrite_model_editor = action_row_widget.findChild(QLineEdit, "RewriteModelEditor")
                                        if rewrite_model_editor:
                                            try:
                                                action_obj["model_override"] = rewrite_model_editor.text().strip()
                                            except RuntimeError:
                                                action_obj["model_override"] = ""
                                        else:
                                            action_obj["model_override"] = ""
                                    elif action_type == "Advance Time":
                                        advance_time_input = action_row_widget.findChild(QLineEdit, "AdvanceTimeInput")
                                        if advance_time_input:
                                            try:
                                                action_obj["advance_amount"] = advance_time_input.text().strip()
                                            except RuntimeError:
                                                action_obj["advance_amount"] = ""
                                        else:
                                            action_obj["advance_amount"] = ""
                                    elif action_type == "Change Time Passage":
                                        passage_static_radio = action_row_widget.findChild(QRadioButton, "ChangeTimePassageStaticRadio")
                                        passage_realtime_radio = action_row_widget.findChild(QRadioButton, "ChangeTimePassageRealtimeRadio")
                                        multiplier_input = action_row_widget.findChild(QDoubleSpinBox, "ChangeTimePassageMultiplierInput")
                                        
                                        if passage_static_radio and passage_static_radio.isChecked():
                                            action_obj["passage_mode"] = "static"
                                        elif passage_realtime_radio and passage_realtime_radio.isChecked():
                                            action_obj["passage_mode"] = "realtime"
                                        else:
                                            action_obj["passage_mode"] = "static"
                                        
                                        if multiplier_input:
                                            try:
                                                action_obj["time_multiplier"] = multiplier_input.value()
                                            except RuntimeError:
                                                action_obj["time_multiplier"] = 1.0
                                        else:
                                            action_obj["time_multiplier"] = 1.0
                                    actions.append(action_obj)
                            try:
                                tag = tag_editor.toPlainText().strip()
                                tag_action_pairs_data.append({
                                    "tag": tag,
                                    "actions": actions,
                                    "next_rule": None,
                                    "switch_model": None,
                                    "set_variable": None
                                })
                            except RuntimeError:
                                pass
                        except RuntimeError:
                            continue
        except RuntimeError:
            print("Warning: Could not process pairs scroll area - it may have been deleted")
    if not tag_action_pairs_data:
        tag_action_pairs_data.append({
            "tag": "",
            "actions": [],
            "next_rule": None,
            "switch_model": None,
            "set_variable": None
        })
    position = "prepend"
    sysmsg_position = "first"
    try:
        if prepend_radio and prepend_radio.isChecked(): 
            position = "prepend"
        elif append_radio and append_radio.isChecked(): 
            position = "append"
        elif replace_radio and replace_radio.isChecked(): 
            position = "replace"
    except RuntimeError:
        pass
    first_sysmsg_radio = tab_content_widget.findChild(QRadioButton, "FirstSysMsgRadio")
    last_sysmsg_radio = tab_content_widget.findChild(QRadioButton, "LastSysMsgRadio")
    try:
        if first_sysmsg_radio and first_sysmsg_radio.isChecked(): 
            sysmsg_position = "first"
        elif last_sysmsg_radio and last_sysmsg_radio.isChecked(): 
            sysmsg_position = "last"
    except RuntimeError:
        pass
    last_exchange_radio = tab_content_widget.findChild(QRadioButton, "LastExchangeRadio")
    full_convo_radio = tab_content_widget.findChild(QRadioButton, "FullConversationRadio")
    user_message_radio = tab_content_widget.findChild(QRadioButton, "UserMessageRadio")
    llm_reply_radio = tab_content_widget.findChild(QRadioButton, "LLMReplyRadio")
    convo_llm_reply_radio = tab_content_widget.findChild(QRadioButton, "ConvoLLMReplyRadio")
    applies_to_character_radio = tab_content_widget.findChild(QRadioButton, "AppliesToCharacterRadio")
    scope = "user_message"
    try:
        if last_exchange_radio and last_exchange_radio.isChecked():
            scope = "last_exchange"
        elif full_convo_radio and full_convo_radio.isChecked():
            scope = "full_conversation"
        elif user_message_radio and user_message_radio.isChecked():
            scope = "user_message"
        elif llm_reply_radio and llm_reply_radio.isChecked():
            scope = "llm_reply"
        elif convo_llm_reply_radio and convo_llm_reply_radio.isChecked():
            scope = "convo_llm_reply"
    except RuntimeError:
        pass
    operator_combo = tab_content_widget.findChild(QComboBox, "ConditionsOperatorCombo")
    conditions_operator = "AND"
    try:
        if operator_combo:
            operator_text = operator_combo.currentText()
            if "OR" in operator_text:
                conditions_operator = "OR"
    except RuntimeError:
        print("Warning: operator_combo has been deleted, using default value 'AND'")
    applies_to = "Narrator"
    character_name = None
    try:
        applies_to_character_radio = tab_content_widget.findChild(QRadioButton, "AppliesToCharacterRadio")
        applies_to_end_of_round_radio = tab_content_widget.findChild(QRadioButton, "AppliesToEndOfRoundRadio")
        if applies_to_character_radio and applies_to_character_radio.isChecked():
            applies_to = "Character"
            if is_update_mode and 0 <= editing_index < len(rules):
                original_rule = rules[editing_index]
                character_name = original_rule.get('character_name', '')
            else:
                character_name_input = tab_content_widget.findChild(QLineEdit, "CharacterNameInput")
                if character_name_input:
                    character_name = character_name_input.text().strip()
                    if not character_name or character_name.isspace():
                        character_name = ""
        elif applies_to_end_of_round_radio and applies_to_end_of_round_radio.isChecked():
            applies_to = "End of Round"
    except RuntimeError:
        print("Warning: Could not find Applies To radio buttons, defaulting to Narrator.")
    new_rule = {
        "id": new_rule_id,
        "description": description,
        "conditions_operator": operator_combo.currentText().split(' ')[0].upper() if operator_combo else 'AND',
        "conditions": condition_rows_data,
        "condition": condition,
        "scope": scope,
        "applies_to": applies_to,
        "character_name": character_name,
        "model": model,
        "tag_action_pairs": tag_action_pairs_data
    }

    if is_update_mode:
        if 0 <= editing_index < len(rules):
            rules[editing_index] = new_rule
            if hasattr(self, 'update_rule_sound') and self.update_rule_sound:
                try:
                    self.update_rule_sound.play()
                except pygame.error as e:
                    print(f"Error playing update_rule_sound: {e}")
                    self.update_rule_sound = None
        else:
            QMessageBox.warning(self, "Error", f"Update mode active, but invalid rule index: {editing_index}")
            return
    else:
        if any(rule.get('id') == new_rule_id for rule in rules):
            QMessageBox.warning(self, "Duplicate ID", f"A rule with ID '{new_rule_id}' already exists. Please use a unique ID.")
            return
        rules.append(new_rule)
        if hasattr(self, 'add_rule_sound') and self.add_rule_sound:
            try:
                self.add_rule_sound.play()
            except pygame.error as e:
                print(f"Error playing add_rule_sound: {e}")
                self.add_rule_sound = None
    _save_thought_rules(self, tab_index)
    self._update_rules_display(rules, rules_list)
    if not is_update_mode:
        self._clear_rule_form(tab_index)
    add_update_button.setText("Add Rule")
    add_update_button.setProperty("editing_rule_index", None)

def _load_selected_rule(self, tab_index, rules_list):
    if self._is_loading_rule:
        return
    self._is_loading_rule = True
    app = QApplication.instance()
    main_window = None
    if app:
        for widget in app.topLevelWidgets():
            if hasattr(widget, 'windowTitle') and 'ChatBot' in widget.windowTitle():
                main_window = widget
                break
    if main_window:
        main_window.setUpdatesEnabled(False)
    try:
        if tab_index < 0 or tab_index >= len(self.tabs_data):
            print(f"Error: Invalid tab index {tab_index} for _load_selected_rule")
            return
        tab_rules = self.tab_widget.widget(tab_index)
        if not tab_rules:
            print(f"Error: Tab at index {tab_index} does not exist")
            return
        selected_items = rules_list.selectedItems()
        if not selected_items:
            print("No rule selected")
            return
        selected_item = selected_items[0]
        current_row_index = rules_list.row(selected_item)
        rule_data = selected_item.data(Qt.UserRole)
        if not rule_data:
            print("No rule data found in selected item")
            return
        rule_id = rule_data.get('id', 'unnamed')
        tab_data = self.tabs_data[tab_index]
        if not tab_data or not tab_data['widget']:
            print("Error: Tab content widget not found")
            return
        tab_content_widget = tab_data['widget']
        tab_content_widget.setUpdatesEnabled(False)
        try:
            widget_cache = {
                'rule_id_editor': tab_content_widget.findChild(QLineEdit, "RuleIdEditor"),
                'description_editor': tab_content_widget.findChild(QLineEdit, "RuleDescriptionEditor"),
                'condition_editor': tab_content_widget.findChild(QTextEdit, "ConditionEditor"),
                'model_editor': tab_content_widget.findChild(QLineEdit, "ModelEditor"),
                'last_exchange_radio': tab_content_widget.findChild(QRadioButton, "LastExchangeRadio"),
                'full_convo_radio': tab_content_widget.findChild(QRadioButton, "FullConversationRadio"),
                'user_message_radio': tab_content_widget.findChild(QRadioButton, "UserMessageRadio"),
                'llm_reply_radio': tab_content_widget.findChild(QRadioButton, "LLMReplyRadio"),
                'convo_llm_reply_radio': tab_content_widget.findChild(QRadioButton, "ConvoLLMReplyRadio"),
                'applies_to_narrator_radio': tab_content_widget.findChild(QRadioButton, "AppliesToNarratorRadio"),
                'applies_to_character_radio': tab_content_widget.findChild(QRadioButton, "AppliesToCharacterRadio"),
                'add_update_button': tab_content_widget.findChild(QPushButton, f"add_rule_button_{tab_index}"),
                'conditions_container': tab_content_widget.findChild(QWidget, "ConditionsContainer"),
                'operator_combo': tab_content_widget.findChild(QComboBox, "ConditionsOperatorCombo"),
                'pairs_container': tab_content_widget.findChild(QWidget, "PairsContainer")
            }
            if widget_cache['rule_id_editor']: 
                widget_cache['rule_id_editor'].setText(rule_id)
            if widget_cache['description_editor']: 
                widget_cache['description_editor'].setText(rule_data.get('description', ''))
            if widget_cache['condition_editor']: 
                widget_cache['condition_editor'].setPlainText(rule_data.get('condition', ''))
            if widget_cache['model_editor']: 
                widget_cache['model_editor'].setText(rule_data.get('model', ''))
            applies_to = rule_data.get('applies_to', 'Narrator')
            character_name = rule_data.get('character_name', '')
            if widget_cache['applies_to_narrator_radio'] and widget_cache['applies_to_character_radio']:
                widget_cache['applies_to_narrator_radio'].setChecked(applies_to == 'Narrator')
                widget_cache['applies_to_character_radio'].setChecked(applies_to == 'Character')
                applies_to_end_of_round_radio = tab_content_widget.findChild(QRadioButton, "AppliesToEndOfRoundRadio")
                if applies_to_end_of_round_radio:
                    applies_to_end_of_round_radio.setChecked(applies_to == 'End of Round')
                character_name_input = tab_content_widget.findChild(QLineEdit, "CharacterNameInput")
                if character_name_input:
                    character_name_input.setText(character_name if character_name else "")
            scope = rule_data.get('scope', 'user_message')
            scope_radios = [
                (widget_cache['last_exchange_radio'], 'last_exchange'),
                (widget_cache['full_convo_radio'], 'full_conversation'),
                (widget_cache['user_message_radio'], 'user_message'),
                (widget_cache['llm_reply_radio'], 'llm_reply'),
                (widget_cache['convo_llm_reply_radio'], 'convo_llm_reply')
            ]
            for radio, scope_value in scope_radios:
                if radio:
                    radio.setChecked(scope == scope_value)
            _load_conditions_optimized(self, widget_cache, rule_data, tab_data)
            _load_tag_action_pairs_optimized(self, widget_cache, rule_data, tab_data)
            if widget_cache['add_update_button'] and is_valid_widget(widget_cache['add_update_button']):
                widget_cache['add_update_button'].setText("Update ↑")
                widget_cache['add_update_button'].setProperty("editing_rule_index", current_row_index)
        finally:
            tab_content_widget.setUpdatesEnabled(True)
    finally:
        if main_window:
            main_window.setUpdatesEnabled(True)
        self._is_loading_rule = False

def _load_conditions_optimized(self, widget_cache, rule_data, tab_data):
    conditions_container = widget_cache['conditions_container']
    operator_combo = widget_cache['operator_combo']
    if not (conditions_container and is_valid_widget(conditions_container) and conditions_container.layout()):
        return
    layout = conditions_container.layout()
    while layout.count() > 0:
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()
    if 'condition_rows' in tab_data:
        tab_data['condition_rows'] = []
    else:
        tab_data['condition_rows'] = []
    saved_conditions = rule_data.get('conditions', [])
    conditions_operator = rule_data.get('conditions_operator', 'AND')
    if operator_combo and is_valid_widget(operator_combo):
        if conditions_operator == 'OR':
            operator_combo.setCurrentIndex(1)
        else:
            operator_combo.setCurrentIndex(0)
    add_condition_row_func = tab_data.get('add_condition_row')
    if add_condition_row_func:
        num_rows_to_create = max(1, len(saved_conditions))
        for i in range(num_rows_to_create):
            try:
                add_condition_row_func()
            except RuntimeError as e:
                print(f"Error creating condition row structure {i+1}: {e}")
    condition_row_widgets = []
    layout = conditions_container.layout()
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item and item.widget() and item.widget().findChild(QComboBox, "StartConditionSelector"):
            condition_row_widgets.append(item.widget())
    for i, row_widget in enumerate(condition_row_widgets):
        label = row_widget.findChild(QLabel, "ConditionLabel")
        if label:
            label.setText(f"Condition {i + 1}:")
        if i < len(saved_conditions):
            cond_data = saved_conditions[i]
            _populate_condition_row(self, row_widget, cond_data)
    condition_rows = tab_data.get('condition_rows', [])
    for i, r in enumerate(condition_rows):
        if is_valid_widget(r.get('add_btn')):
            r['add_btn'].setVisible(i == len(condition_rows)-1)
        if is_valid_widget(r.get('remove_btn')):
            r['remove_btn'].setVisible(len(condition_rows) > 1)

def _populate_condition_row(self, row_widget, cond_data):
    try:
        selector = row_widget.findChild(QComboBox, "StartConditionSelector")
        if selector:
            saved_type = cond_data.get('type', 'None')
            index_to_set = selector.findText(saved_type, Qt.MatchFixedString)
            if index_to_set >= 0:
                selector.setCurrentIndex(index_to_set)
            else:
                none_index = selector.findText("None")
                if none_index >= 0:
                    selector.setCurrentIndex(none_index)
        condition_type = selector.currentText() if selector else 'None'
        if condition_type in ['Setting', 'Location', 'Region', 'World']:
            geography_editor = row_widget.findChild(QLineEdit, "GeographyNameEditor")
            if geography_editor:
                geography_editor.setText(cond_data.get('geography_name', ''))
        elif condition_type == 'Variable':
            var_editor = row_widget.findChild(QLineEdit, "ConditionVarNameEditor")
            op_selector = row_widget.findChild(QComboBox, "VariableCondOpSelector")
            val_editor = row_widget.findChild(QLineEdit, "ConditionVarValueEditor")
            if var_editor:
                var_editor.setText(cond_data.get('variable', ''))
            if op_selector:
                op_index = op_selector.findText(cond_data.get('operator', '=='))
                op_selector.setCurrentIndex(op_index if op_index >= 0 else 0)
            if val_editor:
                val_editor.setText(cond_data.get('value', ''))
            scope = cond_data.get('variable_scope', 'Global')
            scope_radios = [
                (row_widget.findChild(QRadioButton, "ConditionVarScopeGlobalRadio"), 'Global'),
                (row_widget.findChild(QRadioButton, "ConditionVarScopeCharacterRadio"), 'Character'),
                (row_widget.findChild(QRadioButton, "ConditionVarScopePlayerRadio"), 'Player'),
                (row_widget.findChild(QRadioButton, "ConditionVarScopeSettingRadio"), 'Setting')
            ]
            for radio, scope_value in scope_radios:
                if radio:
                    radio.setChecked(scope == scope_value)
        elif condition_type == 'Scene Count':
            scene_op_selector = row_widget.findChild(QComboBox, "SceneCondOpSelector")
            scene_count_spinner = row_widget.findChild(QSpinBox, "ConditionSceneCountSpinner")
            if scene_op_selector:
                op_index = scene_op_selector.findText(cond_data.get('operator', '=='))
                scene_op_selector.setCurrentIndex(op_index if op_index >= 0 else 0)
            if scene_count_spinner:
                scene_count_spinner.setValue(cond_data.get('value', 1))
        elif condition_type == 'Game Time':
            game_time_op_selector = row_widget.findChild(QComboBox, "GameTimeCondOpSelector")
            game_time_type_selector = row_widget.findChild(QComboBox, "GameTimeTypeSelector")
            game_time_value_spinner = row_widget.findChild(QSpinBox, "GameTimeValueSpinner")
            if game_time_op_selector:
                op_index = game_time_op_selector.findText(cond_data.get('operator', 'Before'))
                game_time_op_selector.setCurrentIndex(op_index if op_index >= 0 else 0)
            if game_time_type_selector:
                type_index = game_time_type_selector.findText(cond_data.get('time_type', 'Minute'))
                game_time_type_selector.setCurrentIndex(type_index if type_index >= 0 else 0)
            if game_time_value_spinner:
                game_time_value_spinner.setValue(cond_data.get('value', 0))
        elif condition_type == 'Post Dialogue':
            post_player_radio = row_widget.findChild(QRadioButton, "PostDialoguePlayerPostRadio")
            post_current_radio = row_widget.findChild(QRadioButton, "PostDialogueCurrentPostRadio")
            operator_is_radio = row_widget.findChild(QRadioButton, "PostDialogueIsRadio")
            operator_not_radio = row_widget.findChild(QRadioButton, "PostDialogueNotRadio")
            dialogue_all_radio = row_widget.findChild(QRadioButton, "PostDialogueAllRadio")
            dialogue_some_radio = row_widget.findChild(QRadioButton, "PostDialogueSomeRadio")
            dialogue_none_radio = row_widget.findChild(QRadioButton, "PostDialogueNoneRadio")
            post_type = cond_data.get('post_type', 'Player Post')
            operator = cond_data.get('operator', 'Is')
            dialogue_amount = cond_data.get('dialogue_amount', 'All Dialogue')
            if post_player_radio and post_current_radio:
                post_player_radio.setChecked(post_type == 'Player Post')
                post_current_radio.setChecked(post_type == 'Current Post')
            if operator_is_radio and operator_not_radio:
                operator_is_radio.setChecked(operator == 'Is')
                operator_not_radio.setChecked(operator == 'Not')
            if dialogue_all_radio and dialogue_some_radio and dialogue_none_radio:
                dialogue_all_radio.setChecked(dialogue_amount == 'All Dialogue')
                dialogue_some_radio.setChecked(dialogue_amount == 'Some Dialogue')
                dialogue_none_radio.setChecked(dialogue_amount == 'No Dialogue')
        if selector:
            selector.currentIndexChanged.emit(selector.currentIndex())
        if 'op_selector' in locals() and op_selector:
            op_selector.currentIndexChanged.emit(op_selector.currentIndex())
    except Exception as e:
        print(f"Error populating condition row: {e}")

def _load_tag_action_pairs_optimized(self, widget_cache, rule_data, tab_data):
    pairs_container = tab_data.get('pairs_container') or widget_cache['pairs_container']
    if not is_valid_widget(pairs_container):
        QMessageBox.critical(self, "UI Error", "Failed to find the Tag/Action Pairs UI component. Please reload the tab.")
        return
    container_layout_tuple = (pairs_container, pairs_container.layout())
    pairs_container, main_layout = container_layout_tuple
    tab_data['pairs_container'] = pairs_container
    tab_data['pairs_layout'] = main_layout
    tab_data['tag_action_pairs'] = []
    if pairs_container is None or main_layout is None:
        QMessageBox.critical(self, "UI Error", "Failed to create the Tag/Action Pairs container. Please reload the tab.")
        return
    pairs_container.setUpdatesEnabled(False)
    
    try:
        add_new_pair_func = tab_data.get('add_new_pair')
        if not add_new_pair_func:
            QMessageBox.critical(self, "Internal Error", "Cannot load rule actions: add_new_pair function missing.")
            return
        saved_pairs = rule_data.get('tag_action_pairs', [])
        while main_layout.count() > 0:
            item = main_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        tab_data['tag_action_pairs'].clear()
        if not saved_pairs:
            pair_info = add_new_pair_func(tab_data, main_layout, False)
            if not pair_info or not pair_info.get('widget'):
                QMessageBox.critical(self, "Rule Load Error", "Failed to create default UI for Tag/Action Pairs.\nNo widget returned.")
        else:
            for pair_data_saved in saved_pairs:
                pair_info = add_new_pair_func(tab_data, main_layout, False)
                if not pair_info or not pair_info.get('widget'):
                    print(f"ERROR: Failed to create pair widget for data: {pair_data_saved}")
                    continue
                pair_widget = pair_info.get('widget')
                if len(tab_data['tag_action_pairs']) > 0:
                    pair_info_runtime = tab_data['tag_action_pairs'][-1]
                    try:
                        tag_editor = pair_widget.findChild(QTextEdit, "TagEditor")
                        if tag_editor and is_valid_widget(tag_editor):
                            tag_editor.setPlainText(pair_data_saved.get('tag', ''))
                        _load_pair_actions_optimized(self, pair_widget, pair_info_runtime, pair_data_saved, tab_data)
                    except Exception as e:
                        print(f"Error populating pair: {e}")
                else:
                    print(f"ERROR: No pair info runtime found for pair widget")
        if 'workflow_data_dir' in tab_data:
            _update_workflow_dropdowns(self, tab_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        QMessageBox.critical(self, "Rule Load Error", f"An unexpected error occurred while loading Tag/Action Pairs.\nError: {e}")
    finally:
        pairs_container.setUpdatesEnabled(True)
        pairs_container.update()

def _load_pair_actions_optimized(self, pair_widget, pair_info_runtime, pair_data_saved, tab_data):
    pair_actions_container = pair_widget.findChild(QWidget, "PairActionsContainerWidget")
    if not pair_actions_container:
        print(f"  Error: Could not find actions container widget")
        return
    add_pair_action_row_func = pair_info_runtime.get('add_pair_action_row')
    if not add_pair_action_row_func:
        print(f"  Error: Could not find add_pair_action_row function")
        return
    saved_actions = pair_data_saved.get('actions', [])
    container_layout = pair_actions_container.layout()
    while container_layout.count() > 0:
        item = container_layout.takeAt(0)
        if item and item.widget():
            item.widget().deleteLater()
    if 'pair_action_rows' in pair_info_runtime:
        pair_info_runtime['pair_action_rows'].clear()
    pair_actions_container.setUpdatesEnabled(False)
    pair_widget.setUpdatesEnabled(False)
    
    try:
        if saved_actions:
            print(f"  Loading {len(saved_actions)} actions...")
            for action_idx, action_data in enumerate(saved_actions):
                try:
                    action_row = add_pair_action_row_func(action_data, tab_data.get('workflow_data_dir'))
                except Exception as e:
                    print(f"    Error adding/populating action row {action_idx + 1}: {e}")
        try:
            add_btn = pair_actions_container.findChild(QPushButton, "AddActionButton")
            if not add_btn:
                add_pair_action_row_func(None, tab_data.get('workflow_data_dir'))
        except Exception as e:
            print(f"  Error ensuring add action button: {e}")
    finally:
        pair_actions_container.setUpdatesEnabled(True)
        pair_widget.setUpdatesEnabled(True)

def _update_workflow_dropdowns(self, tab_data):
    workflow_dir = tab_data['workflow_data_dir']
    pairs_container = tab_data.get('pairs_container')
    if pairs_container and pairs_container.layout():
        pairs_layout = pairs_container.layout()
        for i in range(pairs_layout.count()):
            pair_item = pairs_layout.itemAt(i)
            if pair_item and pair_item.widget():
                pair_widget = pair_item.widget()
                pair_info_runtime = None
                if 'tag_action_pairs' in tab_data and i < len(tab_data['tag_action_pairs']):
                    pair_info_runtime = tab_data['tag_action_pairs'][i]
                if not pair_info_runtime:
                    continue
                pair_action_rows = pair_info_runtime.get('pair_action_rows', [])
                for action_row_info in pair_action_rows:
                    if action_row_info['type_selector'].currentText() == 'Change Actor Location':
                        action_row_info['populate_actor_setting_dropdowns'](workflow_dir)

def _save_thought_rules(self, tab_index):
    if not (0 <= tab_index < len(self.tabs_data) and self.tabs_data[tab_index] is not None):
        print(f"Error: Cannot save thought rules for invalid tab index {tab_index}")
        return
    tab_data = self.tabs_data[tab_index]
    rules_dir = tab_data.get('rules_dir')
    if not rules_dir:
        print(f"Error saving rules: No rules_dir for tab {tab_index}")
        return
    rules_to_save = tab_data.get('thought_rules', [])
    existing_files = set(os.listdir(rules_dir)) if os.path.exists(rules_dir) else set()
    current_files = set()
    rule_ids_in_order = []
    for rule in rules_to_save:
        rule_id = rule.get('id')
        if not rule_id:
            print(f"Warning: Skipping rule with no ID: {rule}")
            continue
        rule_ids_in_order.append(rule_id)
        filename = f"{rule_id}_rule.json"
        filepath = os.path.join(rules_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rule, f, indent=2, ensure_ascii=False)
            current_files.add(filename)
        except Exception as e:
            print(f"Error saving rule '{rule_id}': {e}")
    order_filename = "_rules_order.json"
    order_filepath = os.path.join(rules_dir, order_filename)
    try:
        with open(order_filepath, 'w', encoding='utf-8') as f:
            json.dump(rule_ids_in_order, f, indent=2, ensure_ascii=False)
        print(f"Saved rule order to {order_filepath}")
        current_files.add(order_filename)
    except Exception as e:
        print(f"Error saving rule order: {e}")
    files_to_delete = existing_files - current_files
    for fname in files_to_delete:
        if fname.endswith('_rule.json') or fname == order_filename:
            if fname == order_filename and order_filename in current_files:
                 continue
            try:
                os.remove(os.path.join(rules_dir, fname))
                print(f"Deleted old file: {fname}")
            except Exception as e:
                print(f"Error deleting old file {fname}: {e}")

def _delete_selected_rule(main_ui, tab_index, rules_list):
    if not (0 <= tab_index < len(main_ui.tabs_data) and main_ui.tabs_data[tab_index] is not None):
        return
    selected_items = rules_list.selectedItems()
    if not selected_items:
        return
    selected_rule = selected_items[0].data(Qt.UserRole)
    tab_data = main_ui.tabs_data[tab_index]
    rules = tab_data.get('thought_rules', [])
    rule_index = -1
    selected_id = selected_rule.get('id')
    for i, rule in enumerate(rules):
        if selected_id and rule.get('id') == selected_id:
            rule_index = i
            break
        elif rule == selected_rule:
             rule_index = i
    if rule_index == -1:
        print(f"Warning: Could not find rule to delete (ID: {selected_id})")
        return
    del rules[rule_index]
    tab_data['thought_rules'] = rules
    main_ui._update_rules_display(rules, rules_list)
    _save_thought_rules(main_ui, tab_index)
    if hasattr(main_ui, 'delete_rule_sound') and main_ui.delete_rule_sound:
        try:
            main_ui.delete_rule_sound.play()
        except Exception:
            main_ui.delete_rule_sound = None

def _move_rule_up(main_ui, tab_index, rules_list):
    if not (0 <= tab_index < len(main_ui.tabs_data) and main_ui.tabs_data[tab_index] is not None):
        return
    selected_items = rules_list.selectedItems()
    if not selected_items:
        return
    current_row = rules_list.row(selected_items[0])
    if current_row <= 0:
        return
    tab_data = main_ui.tabs_data[tab_index]
    rules = tab_data.get('thought_rules', [])
    temp_rule = copy.deepcopy(rules[current_row])
    rules[current_row] = copy.deepcopy(rules[current_row - 1])
    rules[current_row - 1] = temp_rule
    tab_data['thought_rules'] = rules
    main_ui._update_rules_display(rules, rules_list)
    rules_list.setCurrentRow(current_row - 1)
    if hasattr(main_ui, '_save_rules_timer') and main_ui._save_rules_timer.isActive():
        main_ui._save_rules_timer.stop()
    if not hasattr(main_ui, '_save_rules_timer'):
        main_ui._save_rules_timer = QTimer(main_ui)
        main_ui._save_rules_timer.setSingleShot(True)
        main_ui._save_rules_timer.timeout.connect(lambda: _save_thought_rules(main_ui, tab_index))
    main_ui._save_rules_timer.start(1000)

def _move_rule_down(main_ui, tab_index, rules_list):
    if not (0 <= tab_index < len(main_ui.tabs_data) and main_ui.tabs_data[tab_index] is not None):
        return
    selected_items = rules_list.selectedItems()
    if not selected_items:
        return
    current_row = rules_list.row(selected_items[0])
    if current_row >= rules_list.count() - 1:
        return
    tab_data = main_ui.tabs_data[tab_index]
    rules = tab_data.get('thought_rules', [])
    temp_rule = copy.deepcopy(rules[current_row])
    rules[current_row] = copy.deepcopy(rules[current_row + 1])
    rules[current_row + 1] = temp_rule
    tab_data['thought_rules'] = rules
    main_ui._update_rules_display(rules, rules_list)
    rules_list.setCurrentRow(current_row + 1)
    if hasattr(main_ui, '_save_rules_timer') and main_ui._save_rules_timer.isActive():
        main_ui._save_rules_timer.stop()
    if not hasattr(main_ui, '_save_rules_timer'):
        main_ui._save_rules_timer = QTimer(main_ui)
        main_ui._save_rules_timer.setSingleShot(True)
        main_ui._save_rules_timer.timeout.connect(lambda: _save_thought_rules(main_ui, tab_index))
    main_ui._save_rules_timer.start(1000)

def _refresh_rules_from_json(main_ui, tab_index, rules_list):
    if not (0 <= tab_index < len(main_ui.tabs_data) and main_ui.tabs_data[tab_index] is not None):
        print(f"Error: Invalid tab index: {tab_index}")
        return
    from PyQt5.QtWidgets import QMessageBox
    tab_data = main_ui.tabs_data[tab_index]
    rules_dir = tab_data.get('rules_dir')
    if not rules_dir or not os.path.exists(rules_dir):
        QMessageBox.warning(main_ui, "Error", f"Rules directory not found: {rules_dir}")
        return
    try:
        loaded_rules = []
        order_filepath = os.path.join(rules_dir, "_rules_order.json")
        rule_files = {fname: os.path.join(rules_dir, fname)
                      for fname in os.listdir(rules_dir) if fname.endswith('_rule.json')}
        ordered_rule_ids = []
        if os.path.exists(order_filepath):
            try:
                with open(order_filepath, 'r', encoding='utf-8') as f:
                    ordered_rule_ids = json.load(f)
            except Exception as e:
                print(f"Error loading rule order file {order_filepath}: {e}. Falling back to directory scan.")
                ordered_rule_ids = []
        if ordered_rule_ids:
            loaded_rules_map = {}
            valid_ordered_ids = []
            for rule_id in ordered_rule_ids:
                filename = f"{rule_id}_rule.json"
                fpath = rule_files.get(filename)
                if fpath and os.path.exists(fpath):
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            rule = json.load(f)
                            rule.setdefault('scope', 'last_exchange')
                            loaded_rules_map[rule_id] = rule
                            valid_ordered_ids.append(rule_id)
                            print(f"  Refreshed rule: {rule_id}")
                    except Exception as e:
                        print(f"Error loading rule file {fpath}: {e}")
            loaded_rules = [loaded_rules_map[rule_id] for rule_id in valid_ordered_ids]
            found_rule_files = set(loaded_rules_map.keys())
            all_rule_ids_from_files = {fname.replace('_rule.json', '') for fname in rule_files.keys()}
            orphaned_rules = all_rule_ids_from_files - found_rule_files
            if orphaned_rules:
                for rule_id in sorted(list(orphaned_rules)):
                    filename = f"{rule_id}_rule.json"
                    fpath = rule_files.get(filename)
                    if fpath:
                        try:
                            with open(fpath, 'r', encoding='utf-8') as f:
                                rule = json.load(f)
                                rule.setdefault('scope', 'last_exchange')
                                loaded_rules.append(rule)
                                valid_ordered_ids.append(rule_id)
                        except Exception as e:
                            print(f"Error loading orphaned rule file {fpath}: {e}")
        else:
            rule_ids_loaded = []
            sorted_filenames = sorted(rule_files.keys())
            for fname in sorted_filenames:
                fpath = rule_files[fname]
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        rule = json.load(f)
                        rule.setdefault('scope', 'last_exchange')
                        loaded_rules.append(rule)
                        rule_id = rule.get('id')
                        if rule_id:
                            rule_ids_loaded.append(rule_id)
                        else:
                            fallback_id = fname.replace('_rule.json', '')
                            print(f"Warning: Rule in {fname} missing 'id'. Using filename '{fallback_id}' for ordering.")
                            rule_ids_loaded.append(fallback_id)
                except Exception as e:
                    print(f"Error loading rule from {fpath}: {e}")
        tab_data['thought_rules'] = loaded_rules
        main_ui._update_rules_display(loaded_rules, rules_list)
        if 'timer_rules_widget' in tab_data and tab_data['timer_rules_widget']:
            from rules.timer_rules_manager import _load_timer_rules
            timer_rules = _load_timer_rules(main_ui, tab_index)
            if timer_rules:
                tab_data['timer_rules_widget'].load_timer_rules(timer_rules)
        if hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
            try:
                main_ui.add_rule_sound.play()
            except Exception as e:
                print(f"Error playing refresh sound: {e}")
    except Exception as e:
        print(f"Error refreshing rules: {e}")
        QMessageBox.critical(main_ui, "Refresh Error", f"An error occurred while refreshing rules:\n{e}")

def _duplicate_selected_rule(main_ui, tab_index, rules_list):
    if not (0 <= tab_index < len(main_ui.tabs_data) and main_ui.tabs_data[tab_index] is not None):
        print(f"Error: Invalid tab index: {tab_index}")
        return
    selected_items = rules_list.selectedItems()
    if not selected_items:
        QMessageBox.information(main_ui, "No Rule Selected", "Please select a rule to duplicate.")
        return
    selected_item = selected_items[0]
    current_row = rules_list.row(selected_item)
    selected_rule_data = selected_item.data(Qt.UserRole)
    if not selected_rule_data:
        QMessageBox.warning(main_ui, "Error", "Could not retrieve data for the selected rule.")
        return
    tab_data = main_ui.tabs_data[tab_index]
    rules = tab_data.get('thought_rules', [])
    new_rule = copy.deepcopy(selected_rule_data)
    original_id = new_rule.get('id', "rule")
    new_id_base = original_id
    match = re.match(r"^(.*?)_copy(?:\d+)?$", original_id)
    if match:
        new_id_base = match.group(1)
    counter = 1
    new_rule_id = f"{new_id_base}_copy"
    while any(rule.get('id') == new_rule_id for rule in rules):
        counter += 1
        new_rule_id = f"{new_id_base}_copy{counter}"
    new_rule['id'] = new_rule_id
    if 'description' in new_rule and new_rule['description']:
        new_rule['description'] = f"{new_rule['description']} (Copy)"
    else:
        new_rule['description'] = f"Copy of {original_id}"
    insert_position = current_row
    rules.insert(insert_position, new_rule)
    _save_thought_rules(main_ui, tab_index)
    from PyQt5.QtWidgets import QListWidgetItem
    new_item = QListWidgetItem(f"{new_rule_id} - {new_rule.get('description', '')}")
    new_item.setData(Qt.UserRole, new_rule)
    rules_list.insertItem(insert_position, new_item)
    rules_list.setCurrentItem(new_item)
    
    if hasattr(main_ui, 'add_rule_sound') and main_ui.add_rule_sound:
        try:
            main_ui.add_rule_sound.play()
        except pygame.error as e:
            print(f"Error playing add_rule_sound (on duplicate): {e}")
            main_ui.add_rule_sound = None