import json
import os
from typing import List, Optional


class Settings:
    """配置管理类"""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            print(f"[WARN] Config file not found: {self.config_file}")
            return self._get_default_config()

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "dingtalk": {"webhook": "", "secret": ""},
            "lof": {
                "limit_pct": 9.9,
                "speed_window_minutes": 10.0,
                "speed_threshold_pct": 2.0,
                "limit_codes_file": "lof_limit_codes.txt",
                "speed_codes_file": "lof_speed_codes.txt",
            },
            "ai": {
                "provider": "qwen",
                "api_key": "",
                "api_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen-turbo",
                "enable_search": False,
            },
            "rss": {
                "feed_url": "",
                "check_interval_minutes": 5,
            },
            "timezone": "Asia/Shanghai",
        }

    def save_default_config(self):
        """保存默认配置到文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(
                    self._get_default_config(), f, ensure_ascii=False, indent=2
                )
            print(f"[INFO] Default config saved to: {self.config_file}")
        except Exception as e:
            print(f"[ERROR] Failed to save default config: {e}")

    # DingTalk配置
    @property
    def ding_webhook(self) -> str:
        return self.config.get("dingtalk", {}).get("webhook", "")

    @property
    def ding_secret(self) -> str:
        return self.config.get("dingtalk", {}).get("secret", "")

    # LOF配置
    @property
    def lof_limit_pct(self) -> float:
        return float(self.config.get("lof", {}).get("limit_pct", 9.9))

    @property
    def lof_speed_window_minutes(self) -> float:
        return float(self.config.get("lof", {}).get("speed_window_minutes", 10.0))

    @property
    def lof_speed_threshold_pct(self) -> float:
        return float(self.config.get("lof", {}).get("speed_threshold_pct", 2.0))

    @property
    def lof_limit_codes_file(self) -> str:
        return self.config.get("lof", {}).get(
            "limit_codes_file", "lof_limit_codes.txt"
        )

    @property
    def lof_speed_codes_file(self) -> str:
        return self.config.get("lof", {}).get("speed_codes_file", "lof_speed_codes.txt")

    # AI配置
    @property
    def ai_provider(self) -> str:
        return self.config.get("ai", {}).get("provider", "qwen")

    @property
    def ai_api_key(self) -> str:
        return self.config.get("ai", {}).get("api_key", "")

    @property
    def ai_api_base_url(self) -> str:
        return self.config.get("ai", {}).get(
            "api_base_url",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    @property
    def ai_model(self) -> str:
        return self.config.get("ai", {}).get("model", "qwen-turbo")

    @property
    def ai_enable_search(self) -> bool:
        return self.config.get("ai", {}).get("enable_search", False)

    # RSS配置
    @property
    def rss_feed_url(self) -> str:
        return self.config.get("rss", {}).get("feed_url", "")

    @property
    def rss_check_interval_minutes(self) -> int:
        return int(self.config.get("rss", {}).get("check_interval_minutes", 5))

    # 其他配置
    @property
    def timezone(self) -> str:
        return self.config.get("timezone", "Asia/Shanghai")


def parse_codes_from_file(file_path: str) -> List[str]:
    """
    从文件中解析代码列表

    Args:
        file_path: 文件路径

    Returns:
        代码列表
    """
    codes = []
    if not os.path.exists(file_path):
        print(f"[WARN] Codes file not found: {file_path}")
        return codes

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                code = line.split()[0].strip()
                if code:
                    codes.append(code.zfill(6))
    except Exception as e:
        print(f"[ERROR] Failed to parse codes file: {e}")

    # 去重
    seen = set()
    unique_codes = []
    for code in codes:
        if code not in seen:
            unique_codes.append(code)
            seen.add(code)

    return unique_codes
