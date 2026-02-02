import base64
import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Optional

import requests


class DingTalkNotifier:
    """钉钉通知器"""

    def __init__(self, webhook: str, secret: str = ""):
        self.webhook = webhook
        self.secret = secret

    def _sign_webhook(self) -> str:
        """生成签名的webhook URL"""
        if not self.secret:
            return self.webhook

        ts_ms = str(round(time.time() * 1000))
        string_to_sign = f"{ts_ms}\n{self.secret}".encode("utf-8")
        sign = urllib.parse.quote_plus(
            base64.b64encode(
                hmac.new(
                    self.secret.encode("utf-8"),
                    string_to_sign,
                    digestmod=hashlib.sha256,
                ).digest()
            )
        )
        return f"{self.webhook}&timestamp={ts_ms}&sign={sign}"

    def send_text(self, content: str) -> bool:
        """
        发送文本消息

        Args:
            content: 消息内容

        Returns:
            bool: 发送是否成功
        """
        if not self.webhook:
            print("[WARN] DingTalk webhook not configured; alert skipped.")
            return False

        url = self._sign_webhook()
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {"msgtype": "text", "text": {"content": content}}

        try:
            resp = requests.post(
                url, headers=headers, data=json.dumps(payload), timeout=8
            )
            if resp.status_code != 200:
                print(f"[WARN] DingTalk error: {resp.status_code}, {resp.text}")
                return False
            result = resp.json()
            if result.get("errcode") != 0:
                print(f"[WARN] DingTalk API error: {result}")
                return False
            return True
        except Exception as exc:
            print(f"[ERR] DingTalk push failed: {exc}")
            return False

    def send_markdown(self, title: str, content: str) -> bool:
        """
        发送Markdown消息

        Args:
            title: 消息标题
            content: Markdown格式的消息内容

        Returns:
            bool: 发送是否成功
        """
        if not self.webhook:
            print("[WARN] DingTalk webhook not configured; alert skipped.")
            return False

        url = self._sign_webhook()
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": content},
        }

        try:
            resp = requests.post(
                url, headers=headers, data=json.dumps(payload), timeout=8
            )
            if resp.status_code != 200:
                print(f"[WARN] DingTalk error: {resp.status_code}, {resp.text}")
                return False
            result = resp.json()
            if result.get("errcode") != 0:
                print(f"[WARN] DingTalk API error: {result}")
                return False
            return True
        except Exception as exc:
            print(f"[ERR] DingTalk push failed: {exc}")
            return False