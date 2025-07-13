import os
import json
import datetime

class AgentMemory:
    def __init__(self, notes_file):
        self.notes_file = notes_file
        self.notes = self._load_notes()

    def _load_notes(self):
        if not os.path.exists(self.notes_file):
            return []
        try:
            with open(self.notes_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Warning: Could not load or parse {self.notes_file}. Starting with empty notes.")
            if not os.path.exists(os.path.dirname(self.notes_file)) and os.path.dirname(self.notes_file):
                 os.makedirs(os.path.dirname(self.notes_file))
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                 json.dump([], f)
            return []
        except Exception as e:
            print(f"Unexpected error loading notes from {self.notes_file}: {e}")
            return []

    def _save_notes(self):
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, indent=2, ensure_ascii=False)
            print(f"Notes saved to {self.notes_file}")
        except Exception as e:
            print(f"Error saving notes to {self.notes_file}: {e}")

    def add_note(self, content, game_datetime=None):
        if not content or content.strip().lower() == 'none':
            print("Skipping empty or 'none' note.")
            return
        note = {
            "timestamp": game_datetime if game_datetime else datetime.datetime.now().isoformat(),
            "content": content.strip()
        }
        self.notes.append(note)
        self._save_notes()
        print(f"Agent saved note to {os.path.basename(self.notes_file)}: {content[:50]}...")

    def search_notes(self, query, max_results=3):
        if not query:
            return []
        query_words = set(query.lower().split())
        scored_notes = []
        for note in self.notes:
            note_words = set(note['content'].lower().split())
            common_words = query_words.intersection(note_words)
            if common_words:
                score = len(common_words)
                scored_notes.append((score, note))
        scored_notes.sort(key=lambda x: x[0], reverse=True)
        return [note for score, note in scored_notes[:max_results]]

    def format_notes_for_context(self, notes):
        if not notes:
            return ""
        formatted = "Relevant previous notes:\n"
        for note in notes:
            content_preview = note['content'][:150] + ('...' if len(note['content']) > 150 else '')
            formatted += f"- {content_preview} (Saved: {note['timestamp']})\n"
        return formatted.strip()

def get_npc_notes_from_character_file(character_file_path):
    try:
        if not os.path.exists(character_file_path):
            return None
        with open(character_file_path, 'r', encoding='utf-8') as f:
            character_data = json.load(f)
        notes = character_data.get('npc_notes', '')
        return notes if notes else None
    except Exception as e:
        print(f"[NPC NOTES] Error reading notes from {character_file_path}: {e}")
        return None

def add_npc_note_to_character_file(character_file_path, new_note, game_datetime=None, max_notes=150):
    try:
        if '/resources/data files/actors/' in character_file_path.replace('\\', '/'): return False
        if '/game/actors/' not in character_file_path.replace('\\', '/'): return False
        if not os.path.exists(character_file_path):
            character_filename = os.path.basename(character_file_path)
            workflow_data_dir = character_file_path.split('/game/actors/')[0].replace('\\', '/')
            template_path = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors', character_filename).replace('\\', '/')
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                if 'npc_notes' in template_data:
                    del template_data['npc_notes']
                os.makedirs(os.path.dirname(character_file_path), exist_ok=True)
                with open(character_file_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=2, ensure_ascii=False)
            else:
                return False
        with open(character_file_path, 'r', encoding='utf-8') as f:
            character_data = json.load(f)
        existing_notes_str = character_data.get('npc_notes', '')
        existing_notes = []
        if existing_notes_str:
            import re
            note_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (.+?)(?=\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]|$)'
            matches = re.findall(note_pattern, existing_notes_str, re.DOTALL)
            existing_notes = [(timestamp, content.strip()) for timestamp, content in matches]
        timestamp = game_datetime if game_datetime else datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_note_entry = (timestamp, new_note.strip())
        existing_notes.append(new_note_entry)
        if len(existing_notes) > max_notes:
            existing_notes = existing_notes[-max_notes:]
        notes_str = '\n'.join([f"[{timestamp}] {content}" for timestamp, content in existing_notes])
        character_data['npc_notes'] = notes_str
        with open(character_file_path, 'w', encoding='utf-8') as f:
            json.dump(character_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[NPC NOTES] Error adding note to {character_file_path}: {e}")
        return False

def format_npc_notes_for_context(notes_string, character_name):
    if not notes_string or not notes_string.strip():
        return None
    formatted = f"Your personal notes and memories as {character_name}:\n{notes_string.strip()}"
    return formatted 

def cleanup_template_files_from_npc_notes(workflow_data_dir):
    try:
        templates_dir = os.path.join(workflow_data_dir, 'resources', 'data files', 'actors')
        if not os.path.exists(templates_dir):
            return
        cleaned_count = 0
        for filename in os.listdir(templates_dir):
            if filename.lower().endswith('.json'):
                file_path = os.path.join(templates_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if 'npc_notes' in data:
                        print(f"[CLEANUP] Removing npc_notes from template: {filename}")
                        del data['npc_notes']
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        cleaned_count += 1
                except Exception as e:
                    print(f"[CLEANUP] Error processing {filename}: {e}")
        if cleaned_count > 0:
            print(f"[CLEANUP] Cleaned npc_notes from {cleaned_count} template file(s)")
        else:
            print(f"[CLEANUP] No template files contained npc_notes (good!)")
    except Exception as e:
        print(f"[CLEANUP] Error during template cleanup: {e}")
        import traceback
        traceback.print_exc() 