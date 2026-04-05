import re
import time
import urllib.parse
from typing import Any, Optional

from curl_cffi import requests

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
_BASE = "https://mail.chatgpt.org.uk"


class _Client:
    def __init__(self):
        self.session = requests.Session(impersonate="chrome")
        self.session.headers.update({
            "User-Agent": _UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": f"{_BASE}/",
        })

    def _init_session(self):
        try:
            resp = self.session.get(_BASE, timeout=15)
            sid = self.session.cookies.get("gm_sid")
            if sid:
                self.session.headers.update({"Cookie": f"gm_sid={sid}"})
            m = re.search(r'(eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)', resp.text)
            if m:
                self.session.headers.update({"x-inbox-token": m.group(1)})
        except Exception:
            pass

    def generate_email(self) -> str:
        self._init_session()
        resp = self.session.get(f"{_BASE}/api/generate-email", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            self.session.headers.update({"x-inbox-token": data["auth"]["token"]})
            return data["data"]["email"]
        raise RuntimeError(f"临时邮箱生成失败: {resp.status_code}")

    def list_emails(self, email: str) -> list:
        encoded = urllib.parse.quote(email)
        resp = self.session.get(f"{_BASE}/api/emails?email={encoded}", timeout=15)
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("emails", [])
        return []


def create_temp_mailbox() -> tuple[str, "_Client"]:
    """返回 (email, client)，client 用于后续轮询。"""
    client = _Client()
    email = client.generate_email()
    return email, client


def poll_code(client: "_Client", email: str, stop_fn=None,
              timeout_sec: int = 180, poll: float = 6.0) -> Optional[str]:
    """轮询验证码，stop_fn() 返回 True 时提前退出。"""
    regex = r"(?<!\d)(\d{6})(?!\d)"
    start = time.monotonic()
    while time.monotonic() - start < timeout_sec:
        if stop_fn and stop_fn():
            return None
        try:
            for s in client.list_emails(email):
                m = re.search(regex, str(s.get("subject", "")))
                if m:
                    return m.group(1)
        except Exception:
            pass
        time.sleep(poll)
    return None
