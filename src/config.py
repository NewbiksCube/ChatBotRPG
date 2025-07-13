import os
import json

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "openrouter_api_key": "",
    "openrouter_base_url": "https://openrouter.ai/api/v1",
    "default_model": "google/gemini-2.5-flash-lite-preview-06-17",
    "default_cot_model": "google/gemini-2.5-flash-lite-preview-06-17",
    "default_utility_model": "google/gemini-2.5-flash-lite-preview-06-17",
    "default_temperature": 0.3,
    "default_max_tokens": 2048
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        for key, default_value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = default_value
        return config
    except Exception as e:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving configuration: {e}")

def get_openrouter_api_key():
    config = load_config()
    api_key = config.get("openrouter_api_key", "").strip()
    if not api_key:
        return None
    return api_key

def get_openrouter_base_url():
    config = load_config()
    return config.get("openrouter_base_url", "https://openrouter.ai/api/v1")

def get_default_model():
    config = load_config()
    return config.get("default_model", "google/gemini-2.5-flash-lite-preview-06-17")

def get_default_cot_model():
    config = load_config()
    return config.get("default_cot_model", "google/gemini-2.5-flash-lite-preview-06-17")

def get_default_utility_model():
    config = load_config()
    return config.get("default_utility_model", "google/gemini-2.5-flash-lite-preview-06-17")

def update_config(key, value):
    config = load_config()
    config[key] = value
    save_config(config)

def update_default_models(main_model=None, cot_model=None, utility_model=None):
    config = load_config()
    if main_model:
        config["default_model"] = main_model
    if cot_model:
        config["default_cot_model"] = cot_model
    if utility_model:
        config["default_utility_model"] = utility_model
    save_config(config)