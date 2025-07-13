import os
import json
import re
from typing import List, Dict, Set, Optional
from collections import defaultdict

def load_keywords_for_workflow(workflow_data_dir: str) -> Dict[str, List[Dict]]:
    keywords_dict = defaultdict(list)
    keywords_base_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'keywords')
    if not os.path.exists(keywords_base_dir):
        return {}
    try:
        for category in os.listdir(keywords_base_dir):
            category_path = os.path.join(keywords_base_dir, category)
            if not os.path.isdir(category_path):
                continue
            for filename in os.listdir(category_path):
                if not filename.endswith('.json') or filename == '_order.json':
                    continue
                keyword_path = os.path.join(category_path, filename)
                try:
                    with open(keyword_path, 'r', encoding='utf-8') as f:
                        keyword_data = json.load(f)
                    keyword_name = keyword_data.get('name', filename[:-5])
                    entries = keyword_data.get('entries', [])
                    for entry in entries:
                        entry['_category'] = category
                        entry['_keyword_name'] = keyword_name
                        keywords_dict[keyword_name.lower()].append(entry)
                except Exception as e:
                    print(f"Error loading keyword file {keyword_path}: {e}")
    except Exception as e:
        print(f"Error scanning keywords directory: {e}")
    return dict(keywords_dict)

def extract_keywords_from_text(text: str, available_keywords: Set[str]) -> Set[str]:
    if not text:
        return set()
    found_keywords = set()
    text_lower = text.lower()
    for keyword in available_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            found_keywords.add(keyword)
    return found_keywords

def filter_keyword_entries(entries: List[Dict], character_name: str, setting_name: str, 
                         location_info: Dict[str, str], is_narrator: bool = False) -> Optional[Dict]:
    for entry in entries:
        if not _check_character_filter(entry, character_name, is_narrator):
            continue
        if not _check_setting_filter(entry, setting_name):
            continue
        if not _check_location_filters(entry, location_info):
            continue
        return entry
    return None

def _check_character_filter(entry: Dict, character_name: str, is_narrator: bool) -> bool:
    char_filter = entry.get('character', '').strip()
    if not char_filter:
        return True
    allowed_chars = [c.strip() for c in char_filter.split(',') if c.strip()]
    allowed_chars_lower = [c.lower() for c in allowed_chars]
    if 'any' in allowed_chars_lower:
        return True
    if is_narrator and 'narrator' in allowed_chars_lower:
        return True
    if character_name and character_name.lower() in allowed_chars_lower:
        return True
    return False

def _check_setting_filter(entry: Dict, setting_name: str) -> bool:
    setting_filter = entry.get('setting', '').strip()
    if not setting_filter:
        return True
    allowed_settings = [s.strip().lower() for s in setting_filter.split(',') if s.strip()]
    if setting_name and setting_name.lower() in allowed_settings:
        return True
    return False

def _check_location_filters(entry: Dict, location_info: Dict[str, str]) -> bool:
    world_filter = entry.get('world', '').strip()
    if world_filter:
        allowed_worlds = [w.strip().lower() for w in world_filter.split(',') if w.strip()]
        current_world = location_info.get('world', '').lower()
        if current_world not in allowed_worlds:
            return False
    region_filter = entry.get('region', '').strip()
    if region_filter:
        allowed_regions = [r.strip().lower() for r in region_filter.split(',') if r.strip()]
        current_region = location_info.get('region', '').lower()
        if current_region not in allowed_regions:
            return False
    location_filter = entry.get('location', '').strip()
    if location_filter:
        allowed_locations = [l.strip().lower() for l in location_filter.split(',') if l.strip()]
        current_location = location_info.get('location', '').lower()
        if current_location not in allowed_locations:
            return False
    return True

def build_keyword_context(scene_text: str, character_name: str, setting_name: str,
                         location_info: Dict[str, str], workflow_data_dir: str,
                         is_narrator: bool = False, full_context: List[Dict] = None, 
                         current_scene_number: int = 1) -> str:
    all_keywords = load_keywords_for_workflow(workflow_data_dir)
    if not all_keywords:
        return ""
    full_scene_text = ""
    if full_context and current_scene_number:
        full_scene_text = get_scene_text_for_keywords(full_context, current_scene_number)
    all_scene_keywords = extract_keywords_from_text(full_scene_text, set(all_keywords.keys()))
    current_turn_keywords = extract_keywords_from_text(scene_text, set(all_keywords.keys()))
    all_active_keywords = set()
    for keyword in all_scene_keywords:
        entries = all_keywords.get(keyword, [])
        if not entries:
            continue
        matching_entry = filter_keyword_entries(
            entries, character_name, setting_name, location_info, is_narrator
        )
        if matching_entry:
            scope = matching_entry.get('scope', 'mention').lower()
            if scope == 'conversation':
                all_active_keywords.add(keyword)
            elif scope == 'mention' and keyword in current_turn_keywords:
                all_active_keywords.add(keyword)
    if not all_active_keywords:
        return ""
    keyword_definitions = []
    for keyword in sorted(all_active_keywords):
        entries = all_keywords.get(keyword, [])
        if not entries:
            continue
        matching_entry = filter_keyword_entries(
            entries, character_name, setting_name, location_info, is_narrator
        )
        if matching_entry:
            context_output = matching_entry.get('context_output', '').strip()
            if context_output:
                keyword_definitions.append(f"{keyword.title()} - {context_output}")
    if keyword_definitions:
        definitions_text = ". ".join(keyword_definitions) + "."
        return f"(Important keyword definitions mentioned in the context: {definitions_text})"
    return ""

def get_scene_text_for_keywords(context: List[Dict], current_scene_number: int) -> str:
    scene_texts = []
    for msg in context:
        if msg.get('scene', 1) == current_scene_number and msg.get('role') != 'system':
            content = msg.get('content', '')
            if content:
                scene_texts.append(content)
    return ' '.join(scene_texts)

def inject_keywords_into_context(context_for_llm: List[Dict], original_context: List[Dict],
                               character_name: str, setting_name: str, 
                               location_info: Dict[str, str], workflow_data_dir: str,
                               current_scene_number: int, is_narrator: bool = False) -> List[Dict]:
    scene_text = ""
    for msg in reversed(original_context):
        if msg.get('role') == 'user' and msg.get('scene', 1) == current_scene_number:
            scene_text = msg.get('content', '')
            break
    keyword_context = build_keyword_context(
        scene_text, character_name, setting_name, location_info, 
        workflow_data_dir, is_narrator, original_context, current_scene_number
    )
    if keyword_context:
        last_system_idx = -1
        for i, msg in enumerate(context_for_llm):
            if msg.get('role') == 'system':
                last_system_idx = i
        insert_idx = last_system_idx + 1
        context_for_llm.insert(insert_idx, {
            "role": "user",
            "content": keyword_context
        })
    return context_for_llm

def get_location_info_for_keywords(workflow_data_dir: str, setting_file_path: str = None) -> Dict[str, str]:
    location_info = {
        'world': '',
        'region': '',
        'location': ''
    }
    if not setting_file_path:
        return location_info
    try:
        parts = os.path.normpath(setting_file_path).split(os.sep)
        if 'settings' in parts:
            idx = parts.index('settings')
            if len(parts) > idx + 1:
                location_info['world'] = parts[idx + 1]
            if len(parts) > idx + 2:
                location_info['region'] = parts[idx + 2]
            if len(parts) > idx + 3:
                location_info['location'] = parts[idx + 3]
    except Exception as e:
        print(f"Error extracting location info from path: {e}")
    return location_info 