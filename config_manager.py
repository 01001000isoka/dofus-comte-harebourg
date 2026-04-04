import json
import os

CONFIG_FILE = "Comte_settings.json"

DEFAULT_CONFIG = {
    "scale": 1.080,
    "offset_x": 2,
    "offset_y": 16,
    "hotkey_90": "ctrl+2",
    "hotkey_180": "ctrl+3",
    "hotkey_270": "ctrl+1",
    "hotkey_360": "ctrl+4",
    "ping_target": "ctrl+left",
    "ping_player": "ctrl+right",
    "hotkey_reset": ""
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    except:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)