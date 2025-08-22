import os
import json
import re
from PyQt5.QtWidgets import QApplication
from datetime import datetime
from core.make_inference import make_inference
from config import get_default_utility_model

print("=== generate_random_list.py MODULE LOADED ===")


DEFAULT_SYSTEM_PROMPT = """
You are an expert game development assistant helping create random generators for a single-player text adventure game. Your task is to analyze instructions and create or modify JSON generator files that follow a specific format.

A generator consists of one or more tables, each with a title and a list of items. Each item has a name and weight.
Format:
{
  "name": "Generator Name",
  "tables": [
    {
      "title": "Table Name",
      "items": [
        {"name": "Item Name", "weight": 1},
        {"name": "Another Item", "weight": 3}
      ]
    }
  ]
}

Each table represents a category of elements (like "Professions", "Personalities", etc). Items in the tables are weighted options, where higher weights make them more likely to be selected.

Remember to ensure valid JSON. Weights should be positive integers. Be creative but relevant to the instructions.
"""

def get_model_response(system_prompt, user_prompt, model_override=None):
    print(f"DEBUG: get_model_response called with user_prompt: '{user_prompt}'")
    print(f"DEBUG: user_prompt length: {len(user_prompt)} characters")
    try:
        QApplication.processEvents()
        url_type = model_override
        if not url_type:
            try:
                import os
                import json
                tab_settings_path = os.path.join(os.getcwd(), "tab_settings.json")
                if os.path.exists(tab_settings_path):
                    with open(tab_settings_path, "r", encoding='utf-8') as f:
                        settings = json.load(f)
                        url_type = settings.get('cot_model')
            except Exception as e:
                print(f"Could not load cot_model from settings: {e}")
        if not url_type:
            url_type = get_default_utility_model()
        context_to_send = [{"role": "system", "content": system_prompt},
                          {"role": "user", "content": user_prompt}]
        print(f"DEBUG: System prompt being sent: '{system_prompt}'")
        print(f"DEBUG: Full context being sent to API: {context_to_send}")
        print(f"DEBUG: Total context length: {sum(len(msg.get('content', '')) for msg in context_to_send)} characters")
        QApplication.processEvents()
        response = make_inference(
            context=context_to_send,
            user_message=user_prompt,
            character_name="Generator",
            url_type=url_type,
            max_tokens=4000,
            temperature=0.7,
            is_utility_call=True
        )
        QApplication.processEvents()
        return response
    except Exception as e:
        return f"ERROR: Failed to get response from AI: {e}"

def sanitize_filename(name):
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\.]', '', name.lower().replace(' ', '_'))
    return sanitized or 'untitled_generator'

def create_new_generator(instructions, use_resource=True, resource_folder=None, game_folder=None, generator_name=None):
    print(f"DEBUG: create_new_generator called with instructions: '{instructions}'")
    default_name = f"Generator {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if generator_name:
        print(f"Using user-provided generator name: {generator_name}")
        final_generator_name = generator_name
    else:
        name_match = re.search(r"generator for ([a-zA-Z0-9 ]+)", instructions, re.IGNORECASE)
        if name_match:
            potential_name = name_match.group(1).strip()
            if len(potential_name) > 3 and len(potential_name) < 30:
                final_generator_name = potential_name.title() + " Generator"
            else:
                final_generator_name = default_name
        else:
            final_generator_name = default_name
    user_prompt = f"""
    Create a random generator based on these instructions: "{instructions}"
    
    """
    print(f"DEBUG: Final user_prompt being sent to AI: '{user_prompt}'")
    if not generator_name:
        user_prompt += """
    First, create a SHORT, DISTINCTIVE NAME for this generator (max 3-4 words). The name should clearly indicate the purpose.
    Then, create multiple tables as needed with at least 10-15 varied items per table with appropriate weights.
    """
    else:
        user_prompt += f"""
    Name the generator: "{generator_name}"
    Create multiple tables as needed with at least 10-15 varied items per table with appropriate weights.
    """
    user_prompt += """
    Respond ONLY with the complete, valid JSON object.
    """
    try:
        ai_response = get_model_response(DEFAULT_SYSTEM_PROMPT, user_prompt)
        print(f"DEBUG: AI response received: '{ai_response}'")
        if ai_response.startswith("ERROR:"):
            return {"status": "error", "message": ai_response}
        try:
            json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", ai_response)
            if json_match:
                json_content = json_match.group(1)
            else:
                json_content = ai_response
            generator_data = json.loads(json_content)
            if "name" not in generator_data:
                generator_data["name"] = final_generator_name
            elif generator_name:
                generator_data["name"] = generator_name
            elif len(generator_data["name"]) > 50:
                generator_data["name"] = generator_data["name"][:50]
            if "tables" not in generator_data or not isinstance(generator_data["tables"], list):
                return {"status": "error", "message": "AI did not generate a valid generator structure with tables"}
            for table in generator_data["tables"]:
                if "title" not in table:
                    table["title"] = "Untitled Table"
                if "items" not in table or not isinstance(table["items"], list):
                    table["items"] = []
                for item in table["items"]:
                    if "name" not in item:
                        item["name"] = "Untitled Item"
                    if "weight" not in item or not isinstance(item["weight"], int):
                        item["weight"] = 1
                    if "generate" not in item:
                        item["generate"] = True
            target_folder = game_folder if not use_resource else resource_folder
            if not target_folder or not os.path.exists(target_folder):
                return {"status": "error", "message": f"Target folder does not exist: {target_folder}"}
            sanitized_name = sanitize_filename(generator_data["name"])
            filename = f"{sanitized_name}.json"
            file_path = os.path.join(target_folder, filename)
            if os.path.exists(file_path):
                base_name = sanitized_name
                counter = 1
                while os.path.exists(file_path):
                    sanitized_name = f"{base_name}_{counter}"
                    filename = f"{sanitized_name}.json"
                    file_path = os.path.join(target_folder, filename)
                    counter += 1
                generator_data["name"] = f"{generator_data['name']} {counter}"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(generator_data, f, indent=2, ensure_ascii=False)
            return {
                "status": "success",
                "message": f"Created new generator: {generator_data['name']}",
                "file_path": file_path,
                "generator_name": generator_data["name"],
                "tables_count": len(generator_data["tables"]),
                "items_count": sum(len(table.get("items", [])) for table in generator_data["tables"]),
                "result": f"Created new generator '{generator_data['name']}' with {len(generator_data['tables'])} tables and {sum(len(table.get('items', [])) for table in generator_data['tables'])} items."
            }
        except json.JSONDecodeError as e:
            return {"status": "error", "message": f"Failed to parse AI response as JSON: {e}", "ai_response": ai_response}
    except Exception as e:
        return {"status": "error", "message": f"Error creating new generator: {e}"}

def permutate_generator(generator_data, instructions, permutate_objects=False, permutate_weights=False):
    import copy
    permutated_data = copy.deepcopy(generator_data)
    if not permutate_objects and not permutate_weights:
        return permutated_data
    tables_info = []
    for i, table in enumerate(generator_data.get("tables", [])):
        items_info = []
        for item in table.get("items", []):
            items_info.append(f"{item.get('name', 'Unknown')} (weight: {item.get('weight', 1)})")
        tables_info.append(f"Table {i+1}: {table.get('title', f'Table {i+1}')}\nItems: {', '.join(items_info[:10])}{' [...]' if len(items_info) > 10 else ''}")
    tables_description = "\n\n".join(tables_info)
    user_prompt = f"""INSTRUCTIONS:
    I need to permutate a generator named "{generator_data.get('name', 'Unknown Generator')}" based on these instructions: "{instructions}"
    
    {'I need to modify the ITEMS in each table.' if permutate_objects else ''}
    {'I need to modify the WEIGHTS of existing items.' if permutate_weights else ''}
    Here are the current tables and items:
    {tables_description}
    Respond with ONLY the permutated generator in valid JSON format. 
    Maintain the same structure but {'modify items' if permutate_objects else ''} {'and' if permutate_objects and permutate_weights else ''} {'modify weights' if permutate_weights else ''}.
    Keep the same name and table titles unless the instructions explicitly ask to change them.
    """
    try:
        ai_response = get_model_response(DEFAULT_SYSTEM_PROMPT, user_prompt)
        if ai_response.startswith("ERROR:"):
            return permutated_data
        try:
            json_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", ai_response)
            if json_match:
                json_content = json_match.group(1)
            else:
                json_content = ai_response
            new_data = json.loads(json_content)
            if "name" not in new_data:
                new_data["name"] = permutated_data["name"]
            if "tables" not in new_data or not isinstance(new_data["tables"], list):
                return permutated_data
            if len(new_data["tables"]) < len(permutated_data.get("tables", [])):
                return permutated_data
            if permutate_weights and not permutate_objects:
                for i, (orig_table, new_table) in enumerate(zip(permutated_data.get("tables", []), new_data["tables"])):
                    if len(orig_table.get("items", [])) != len(new_table.get("items", [])):
                        print(f"Warning: Table {i+1} has a different number of items. Using original table structure.")
                        new_table["items"] = orig_table.get("items", [])
                        continue
                    for j, (orig_item, new_item) in enumerate(zip(orig_table.get("items", []), new_table.get("items", []))):
                        if orig_item.get("name") != new_item.get("name"):
                            new_item["name"] = orig_item.get("name", "Unknown")
                        if not isinstance(new_item.get("weight"), int) or new_item.get("weight") < 1:
                            new_item["weight"] = 1
                        new_item["generate"] = orig_item.get("generate", True)
            return new_data
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response as JSON: {e}")
            return permutated_data
    except Exception as e:
        print(f"Error permutating generator: {e}")
        return permutated_data

def generate_random_list(instructions, is_permutate=False, use_resource=True, permutate_objects=False, permutate_weights=False, generator_json_path=None, resource_folder=None, game_folder=None, model_override=None, generator_name=None):
    if not instructions.strip():
        return "Error: Instructions cannot be empty"
    if is_permutate and (not generator_json_path or not os.path.exists(generator_json_path)):
        print(f"WARNING: Could not find generator '{generator_name}' for permutation. Falling back to creating new generator.")
        is_permutate = False
    target_folder = game_folder if not use_resource else resource_folder
    if not target_folder or not os.path.exists(target_folder):
        return f"Error: Target folder does not exist: {target_folder}"
    try:
        if is_permutate:
            try:
                with open(generator_json_path, 'r', encoding='utf-8') as f:
                    generator_data = json.load(f)
            except Exception as e:
                return f"Error: Failed to load generator file: {e}"
            permutated_data = generator_data
            if permutate_objects or permutate_weights:
                permutated_data = permutate_generator(generator_data, instructions, permutate_objects=permutate_objects, permutate_weights=permutate_weights)
            if use_resource:
                target_folder = resource_folder
            else:
                target_folder = game_folder
            sanitized_name = sanitize_filename(permutated_data.get("name", "permutated_generator"))
            filename = f"{sanitized_name}.json"
            file_path = os.path.join(target_folder, filename)
            if os.path.normpath(file_path) == os.path.normpath(generator_json_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(permutated_data, f, indent=2, ensure_ascii=False)
                return f"Updated generator '{permutated_data.get('name')}' with permutated {'items' if permutate_objects else ''}{'and ' if permutate_objects and permutate_weights else ''}{'weights' if permutate_weights else ''}"
            else:
                if os.path.exists(file_path):
                    base_name = sanitized_name
                    counter = 1
                    while os.path.exists(file_path):
                        sanitized_name = f"{base_name}_{counter}"
                        filename = f"{sanitized_name}.json"
                        file_path = os.path.join(target_folder, filename)
                        counter += 1
                    permutated_data["name"] = f"{permutated_data.get('name')} {counter}"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(permutated_data, f, indent=2, ensure_ascii=False)
                return f"Created new generator '{permutated_data.get('name')}' with permutated {'items' if permutate_objects else ''}{'and ' if permutate_objects and permutate_weights else ''}{'weights' if permutate_weights else ''}"
        else:
            result = create_new_generator(instructions=instructions, use_resource=use_resource, resource_folder=resource_folder, game_folder=game_folder, generator_name=generator_name)
            if result["status"] == "success":
                return result["result"]
            else:
                return f"Error: {result['message']}"
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Unexpected error: {e}"

if __name__ == "__main__":
    result = generate_random_list("Create a generator for fantasy character occupations with appropriate weights", is_permutate=False, use_resource=True, permutate_objects=False, permutate_weights=False, generator_json_path="example.json", resource_folder="./resources/generators", game_folder="./game/generators")
    print(result)
