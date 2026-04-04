import re
import time

import requests

from codex_handwork.settings import get_mail_request_config, get_settings

CODE_PATTERN = re.compile(r"\b(\d{4,8}|[A-Z]\d{5,6})\b")


def fetch_email_list() -> list[dict]:
    config = get_mail_request_config()
    response = requests.get(
        config["url"],
        params=config["params"],
        headers=config["headers"],
        timeout=config["request_timeout_seconds"],
    )
    response.raise_for_status()
    payload = response.json() or {}
    data = payload.get("data") or {}
    items = data.get("list") or []
    return [item for item in items if isinstance(item, dict)]


def extract_verification_code(subject: str | None) -> str | None:
    if not subject:
        return None
    match = CODE_PATTERN.search(subject)
    return match.group(1) if match else None


def find_code_by_email(target_email: str) -> str | None:
    for item in fetch_email_list():
        if item.get("toEmail") != target_email:
            continue
        return extract_verification_code(item.get("subject"))
    return None


def wait_for_code_by_email(target_email: str, interval: int | None = None, timeout: int | None = None) -> str:
    if interval is None:
        interval = get_settings()["gui"]["code_poll_interval_seconds"]
    start = time.time()
    while True:
        code = find_code_by_email(target_email)
        if code:
            return code
        if timeout is not None and time.time() - start >= timeout:
            raise TimeoutError(f"验证码等待超时: {target_email}")
        time.sleep(interval)


if __name__ == "__main__":
    while True:
        try:
            for item in fetch_email_list():
                email = item.get("toEmail")
                code = extract_verification_code(item.get("subject"))
                print(f"邮箱: {email}, 验证码: {code}")
                break
        except Exception as e:
            print(f"错误: {e}")
        time.sleep(get_settings()["gui"]["code_poll_interval_seconds"])
