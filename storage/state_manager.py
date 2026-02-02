import json
import os
from typing import Any, Dict, Optional


class StateManager:
    """状态管理器，用于持久化状态到JSON文件"""

    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> Dict:
        """加载状态文件"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                print(f"[WARN] Failed to load state file: {e}")
        return {}

    def _save(self):
        """保存状态到文件"""
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save state file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        return self.state.get(key, default)

    def set(self, key: str, value: Any):
        """设置状态值并保存"""
        self.state[key] = value
        self._save()

    def get_nested(self, *keys, default: Any = None) -> Any:
        """获取嵌套状态值"""
        current = self.state
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
            if current is None:
                return default
        return current

    def set_nested(self, *keys, value: Any):
        """设置嵌套状态值"""
        if len(keys) == 0:
            return

        current = self.state
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value
        self._save()

    def ensure_key(self, key: str, default: Any):
        """确保键存在，如果不存在则设置默认值"""
        if key not in self.state:
            self.state[key] = default
            self._save()
