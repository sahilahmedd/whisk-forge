import json
import os
from pathlib import Path

class ConfigManager:
    _instance = None
    
    DEFAULT_CONFIG = {
        "window": {"width": 1360, "height": 900, "sidebar_width": 380},
        "theme": "light",
        "parallel_threads": 2,
        "last_output_path": str(Path.home() / "WhiskForge" / "output")
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.app_data_dir = Path(os.environ.get("APPDATA")) / "WhiskForge"
        self.app_data_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.app_data_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_file.exists():
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                config = self.DEFAULT_CONFIG.copy()
                self._recursive_update(config, user_config)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()

    def _recursive_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_nested(self, *keys):
        val = self.config
        for k in keys:
            val = val.get(k)
            if val is None:
                return None
        return val

    def set_nested(self, value, *keys):
        d = self.config
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        self.save_config()
