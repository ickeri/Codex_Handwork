import re
import time
import urllib.parse
from typing import List, Dict, Any, Optional

from curl_cffi import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"


class GPTMailClient:
    def __init__(self, proxies: Any = None):
        self.session = requests.Session(proxies=proxies, impersonate="chrome")
        self.session.headers.update({
            "User-Agent": UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://mail.chatgpt.org.uk/"
        })
        self.base_url = "https://mail.chatgpt.org.uk"

    def _init_browser_session(self):
        try:
            resp = self.session.get(self.base_url, timeout=15)
            gm_sid = self.session.cookies.get("gm_sid")
            if gm_sid:
                self.session.headers.update({"Cookie": f"gm_sid={gm_sid}"})
            token_match = re.search(r'(eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)', resp.text)
            if token_match:
                self.session.headers.update({"x-inbox-token": token_match.group(1)})
        except Exception:
            pass

    def generate_email(self) -> str:
        self._init_browser_session()
        resp = self.session.get(f"{self.base_url}/api/generate-email", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            email = data['data']['email']
            self.session.headers.update({"x-inbox-token": data['auth']['token']})
            return email
        raise RuntimeError(f"GPTMail 生成失败: {resp.status_code}")

    def list_emails(self, email: str) -> List[Dict]:
        encoded_email = urllib.parse.quote(email)
        resp = self.session.get(f"{self.base_url}/api/emails?email={encoded_email}", timeout=15)
        if resp.status_code == 200:
            return resp.json().get('data', {}).get('emails', [])
        return []


def get_email_and_code_fetcher(proxies: Any = None):
    """
    返回 (email, fetch_code)
    fetch_code() 轮询邮箱直到收到 6 位验证码，超时返回 None
    """
    client = GPTMailClient(proxies)
    email = client.generate_email()

    def fetch_code(timeout_sec: int = 180, poll: float = 6.0) -> Optional[str]:
        regex = r"(?<!\d)(\d{6})(?!\d)"
        start = time.monotonic()
        attempt = 0
        while time.monotonic() - start < timeout_sec:
            attempt += 1
            try:
                summaries = client.list_emails(email)
                print(f"[otp] 轮询 #{attempt}, 收到 {len(summaries)} 封邮件, 目标: {email}")
                for s in summaries:
                    m = re.search(regex, str(s.get("subject", "")))
                    if m:
                        return m.group(1)
            except Exception:
                pass
            time.sleep(poll)
        return None

    return email, fetch_code


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="获取临时邮箱并等待验证码")
    parser.add_argument("--proxy", help="代理地址")
    parser.add_argument("--timeout", type=int, default=180, help="等待验证码超时(秒)")
    args = parser.parse_args()

    proxies = {"http": args.proxy, "https": args.proxy} if args.proxy else None

    print("正在生成临时邮箱...")
    email, fetch_code = get_email_and_code_fetcher(proxies)
    print(f"邮箱: {email}")

    print("等待验证码...")
    code = fetch_code(timeout_sec=args.timeout)
    if code:
        print(f"验证码: {code}")
    else:
        print("超时未收到验证码")
